"""配布Core外で代表fixtureを分類する回帰oracle。完全監査器やPASS判定器ではない。"""

from __future__ import annotations

import re
import unicodedata


MAX_INPUT_BYTES = 4096
COMBINING_MARK_BURST = 4
MAX_SEGMENTS = 64
MAX_CODEPOINTS_PER_SEGMENT = 256
MAX_TOTAL_CODEPOINTS = 1024
MAX_DECODE_DEPTH = 2
MAX_DECODED_BYTES = MAX_INPUT_BYTES
MAX_DECODE_EXPANSION_RATIO = 1


class InputBudgetExceeded(ValueError):
    """UTF-8入力が静的検査の上限を超えたことを表す。"""


class MalformedEncoding(ValueError):
    """encodingらしい入力が安全に復号できないことを表す。"""


class DecodeDepthExceeded(InputBudgetExceeded):
    """encodingが許可した復号深度内で解決しないことを表す。"""


_ZERO_WIDTH = {0x200B, 0x200C, 0x200D, *range(0x2060, 0x2065), 0xFEFF}
_BIDI_CONTROLS = {
    0x061C,
    0x200E,
    0x200F,
    *range(0x202A, 0x202F),
    *range(0x2066, 0x206A),
}
_ESCAPED_CODEPOINT = re.compile(
    r"\\(?:u\{([0-9A-Fa-f]{1,6})\}|u([0-9A-Fa-f]{4})|U([0-9A-Fa-f]{8}))"
)
_ESCAPE_PREFIX = re.compile(r"\\[uU]")
_PERCENT_BYTE_RUN = re.compile(r"(?:%[0-9A-Fa-f]{2})+")
_FINDING_ORDER = (
    "zero_width",
    "variation_selector",
    "unicode_tag",
    "bidi_control",
    "escaped_invisible",
    "percent_encoded_invisible",
    "multiply_encoded_invisible",
    "mixed_script",
    "normalization_difference",
    "combining_mark_burst",
    "whitespace_steganography",
)


def _is_variation_selector(codepoint: int) -> bool:
    return 0xFE00 <= codepoint <= 0xFE0F or 0xE0100 <= codepoint <= 0xE01EF


def _is_unicode_tag(codepoint: int) -> bool:
    return 0xE0000 <= codepoint <= 0xE007F


def _is_suspicious_invisible(codepoint: int) -> bool:
    return (
        codepoint in _ZERO_WIDTH
        or codepoint in _BIDI_CONTROLS
        or _is_variation_selector(codepoint)
        or _is_unicode_tag(codepoint)
    )


def _bounded_utf8_size(text: str, limit: int, label: str) -> int:
    total = 0
    for index, character in enumerate(text):
        codepoint = ord(character)
        if codepoint <= 0x7F:
            width = 1
        elif codepoint <= 0x7FF:
            width = 2
        elif 0xD800 <= codepoint <= 0xDFFF:
            raise ValueError(f"{label}に孤立surrogateを検出: index {index}")
        elif codepoint <= 0xFFFF:
            width = 3
        else:
            width = 4
        total += width
        if total > limit:
            raise InputBudgetExceeded(f"{label}が上限を超過: > {limit} bytes")
    return total


def _script_family(codepoint: int) -> str | None:
    if not unicodedata.category(chr(codepoint)).startswith("L"):
        return None
    if (
        0x0041 <= codepoint <= 0x005A
        or 0x0061 <= codepoint <= 0x007A
        or 0x00C0 <= codepoint <= 0x024F
        or 0x1E00 <= codepoint <= 0x1EFF
    ):
        return "latin"
    if 0x0370 <= codepoint <= 0x03FF or 0x1F00 <= codepoint <= 0x1FFF:
        return "greek"
    if 0x0400 <= codepoint <= 0x052F:
        return "cyrillic"
    return None


def _looks_like_whitespace_steganography(text: str) -> bool:
    whitespace_alphabet = {" ", "\t", "\u00A0"}
    used_characters = set(text)
    return (
        len(text) >= 8
        and len(text) % 8 == 0
        and used_characters.issubset(whitespace_alphabet)
        and len(used_characters) >= 2
    )


def _decode_percent_layer(text: str) -> tuple[str, bool, bool]:
    input_bytes = _bounded_utf8_size(text, MAX_DECODED_BYTES, "percent復号入力")
    changed = False
    introduced_invisible = False

    def replace_run(match: re.Match[str]) -> str:
        nonlocal changed, introduced_invisible
        encoded_bytes = bytes.fromhex(match.group().replace("%", ""))
        try:
            decoded = encoded_bytes.decode("utf-8")
        except UnicodeDecodeError as error:
            raise MalformedEncoding(
                f"percent encodingがUTF-8として不正: index {match.start()}"
            ) from error
        changed = True
        if any(_is_suspicious_invisible(ord(character)) for character in decoded):
            introduced_invisible = True
        return decoded

    decoded_text = _PERCENT_BYTE_RUN.sub(replace_run, text)
    output_bytes = _bounded_utf8_size(decoded_text, MAX_DECODED_BYTES, "percent復号出力")
    if output_bytes > input_bytes * MAX_DECODE_EXPANSION_RATIO:
        raise InputBudgetExceeded(
            f"percent復号の展開率が上限を超過: > {MAX_DECODE_EXPANSION_RATIO}"
        )
    return decoded_text, changed, introduced_invisible


def _percent_encoding_finding(text: str) -> str | None:
    current = text
    finding_depth: int | None = None
    for depth in range(1, MAX_DECODE_DEPTH + 1):
        current, changed, introduced_invisible = _decode_percent_layer(current)
        if not changed:
            break
        if introduced_invisible and finding_depth is None:
            finding_depth = depth
    if _PERCENT_BYTE_RUN.search(current):
        raise DecodeDepthExceeded(f"percent encodingが深度{MAX_DECODE_DEPTH}で未解決")
    if finding_depth == 1:
        return "percent_encoded_invisible"
    if finding_depth is not None:
        return "multiply_encoded_invisible"
    return None


def _contains_escaped_invisible(text: str) -> bool:
    matches = list(_ESCAPED_CODEPOINT.finditer(text))
    valid_starts = {match.start() for match in matches}
    for prefix in _ESCAPE_PREFIX.finditer(text):
        if prefix.start() not in valid_starts:
            raise MalformedEncoding(f"Unicode escapeが不正: index {prefix.start()}")

    found = False
    for match in matches:
        codepoint = int(next(group for group in match.groups() if group is not None), 16)
        if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
            raise MalformedEncoding(f"Unicode scalar値が不正: index {match.start()}")
        if _is_suspicious_invisible(codepoint):
            found = True
    return found


def render_segments(segments: list[dict[str, object]]) -> str:
    """ASCII manifestのsegmentを検証し、元データを変更せず文字列化する。"""
    if not isinstance(segments, list):
        raise TypeError("segmentsはlistであること")
    if len(segments) > MAX_SEGMENTS:
        raise InputBudgetExceeded(f"segment数が上限を超過: > {MAX_SEGMENTS}")

    rendered_parts: list[str] = []
    rendered_bytes = 0
    total_codepoints = 0
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ValueError(f"segment[{index}]はobjectであること")
        if len(segment) != 1:
            raise ValueError(
                f"segment[{index}]はtextまたはcodepointsの一方だけを持つこと"
            )
        keys = set(segment)
        if keys == {"text"}:
            text = segment["text"]
            if not isinstance(text, str):
                raise ValueError(f"segment[{index}].textはstrであること")
            if len(text) > MAX_INPUT_BYTES:
                raise InputBudgetExceeded(
                    f"segment[{index}].textが文字数上限を超過: > {MAX_INPUT_BYTES}"
                )
            rendered = text
        elif keys == {"codepoints"}:
            codepoints = segment["codepoints"]
            if not isinstance(codepoints, list) or not codepoints:
                raise ValueError(f"segment[{index}].codepointsは空でないlistであること")
            if len(codepoints) > MAX_CODEPOINTS_PER_SEGMENT:
                raise InputBudgetExceeded(
                    f"segment[{index}].codepointsが上限を超過: "
                    f"> {MAX_CODEPOINTS_PER_SEGMENT}"
                )
            total_codepoints += len(codepoints)
            if total_codepoints > MAX_TOTAL_CODEPOINTS:
                raise InputBudgetExceeded(
                    f"codepoint総数が上限を超過: > {MAX_TOTAL_CODEPOINTS}"
                )
            characters: list[str] = []
            for encoded in codepoints:
                if (
                    not isinstance(encoded, str)
                    or len(encoded) > 6
                    or not re.fullmatch(r"[0-9A-Fa-f]{1,6}", encoded)
                ):
                    raise ValueError(f"segment[{index}]のcodepointはASCII hexであること")
                codepoint = int(encoded, 16)
                if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
                    raise ValueError(f"segment[{index}]のcodepointがUnicode範囲外")
                characters.append(chr(codepoint))
            rendered = "".join(characters)
        else:
            raise ValueError(
                f"segment[{index}]はtextまたはcodepointsの一方だけを持つこと"
            )

        rendered_bytes += _bounded_utf8_size(
            rendered,
            MAX_INPUT_BYTES - rendered_bytes,
            "fixture出力",
        )
        rendered_parts.append(rendered)

    return "".join(rendered_parts)


def scan_text(text: str) -> list[str]:
    """文字列を変更せず、検出したUnicode系リスクの種別だけを返す。"""
    if not isinstance(text, str):
        raise TypeError("textはstrであること")
    if len(text) > MAX_INPUT_BYTES:
        raise InputBudgetExceeded(f"文字数が上限を超過: > {MAX_INPUT_BYTES}")
    _bounded_utf8_size(text, MAX_INPUT_BYTES, "UTF-8入力")

    findings: set[str] = set()
    script_families: set[str] = set()
    combining_run = 0
    maximum_combining_run = 0
    for character in text:
        codepoint = ord(character)
        if unicodedata.combining(character):
            combining_run += 1
            maximum_combining_run = max(maximum_combining_run, combining_run)
        else:
            combining_run = 0
        script_family = _script_family(codepoint)
        if script_family:
            script_families.add(script_family)
        if codepoint in _ZERO_WIDTH:
            findings.add("zero_width")
        if _is_variation_selector(codepoint):
            findings.add("variation_selector")
        if _is_unicode_tag(codepoint):
            findings.add("unicode_tag")
        if codepoint in _BIDI_CONTROLS:
            findings.add("bidi_control")

    if "latin" in script_families and script_families.intersection({"greek", "cyrillic"}):
        findings.add("mixed_script")
    if unicodedata.normalize("NFC", text) != text:
        findings.add("normalization_difference")
    if maximum_combining_run >= COMBINING_MARK_BURST:
        findings.add("combining_mark_burst")
    if _looks_like_whitespace_steganography(text):
        findings.add("whitespace_steganography")
    if _contains_escaped_invisible(text):
        findings.add("escaped_invisible")
    percent_finding = _percent_encoding_finding(text)
    if percent_finding:
        findings.add(percent_finding)

    return [name for name in _FINDING_ORDER if name in findings]
