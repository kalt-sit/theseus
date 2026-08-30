from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADVERSARIAL_ROOT = ROOT / "tests" / "adversarial"
FIXTURE_MANIFEST = ADVERSARIAL_ROOT / "fixtures.json"
REFERENCE_SCANNER = ADVERSARIAL_ROOT / "reference_scanner.py"


class AdversarialFixtureContractTests(unittest.TestCase):
    def load_reference_scanner(self):
        self.assertTrue(REFERENCE_SCANNER.is_file(), "reference scannerが存在すること")
        spec = importlib.util.spec_from_file_location(
            "theseus_reference_scanner", REFERENCE_SCANNER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_fixture_corpus_declares_independent_safe_origin(self) -> None:
        self.assertTrue(FIXTURE_MANIFEST.is_file(), "fixture manifestが存在すること")
        raw = FIXTURE_MANIFEST.read_text(encoding="utf-8")
        manifest = json.loads(raw)
        metadata = manifest["_meta"]

        self.assertEqual(metadata["schema_version"], 1)
        self.assertEqual(metadata["origin"], "independently-authored")
        self.assertEqual(metadata["coverage"], "representative-not-exhaustive")
        self.assertEqual(metadata["payload_policy"], "harmless-markers-only")
        self.assertFalse(metadata["copied_from_third_party"])
        self.assertLessEqual(metadata["max_utf8_bytes_per_fixture"], 256)
        self.assertTrue(raw.isascii(), "manifest自体へ不可視Unicodeを直書きしないこと")

    def test_fixture_corpus_covers_the_registered_regression_cases(self) -> None:
        manifest = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
        fixtures = manifest["fixtures"]
        ids = [fixture["id"] for fixture in fixtures]
        required_ids = {
            "clean_ascii_control",
            "zero_width_insertion",
            "variation_selector_pair",
            "unicode_tag_sequence",
            "bidi_isolate",
            "mixed_script_homoglyph",
            "combining_mark_burst",
            "whitespace_bit_pattern",
            "escaped_zero_width",
            "percent_encoded_zero_width",
            "multiply_percent_encoded_zero_width",
            "normalization_difference",
            "nbsp_whitespace_pattern",
            "additional_default_ignorable",
        }

        self.assertEqual(set(ids), required_ids)
        self.assertEqual(len(ids), len(set(ids)), "fixture idは一意であること")
        for fixture in fixtures:
            self.assertTrue(fixture["segments"])
            self.assertIsInstance(fixture["expected_findings"], list)

    def test_fixture_corpus_uses_only_reviewed_harmless_segments(self) -> None:
        manifest = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
        expected_segments = {
            "clean_ascii_control": [{"text": "SAFE-FIXTURE-01"}],
            "zero_width_insertion": [
                {"text": "SA"},
                {"codepoints": ["200B"]},
                {"text": "FE-FIXTURE-01"},
            ],
            "variation_selector_pair": [
                {"text": "SAFE"},
                {"codepoints": ["FE0E", "FE0F"]},
                {"text": "-FIXTURE-01"},
            ],
            "unicode_tag_sequence": [
                {"text": "SAFE-FIXTURE-01"},
                {
                    "codepoints": ["E0073", "E0061", "E0066", "E0065", "E007F"]
                },
            ],
            "bidi_isolate": [
                {"text": "SAFE"},
                {"codepoints": ["2066"]},
                {"text": "-FIXTURE-01"},
                {"codepoints": ["2069"]},
            ],
            "mixed_script_homoglyph": [
                {"text": "S"},
                {"codepoints": ["0410"]},
                {"text": "FE-FIXTURE-01"},
            ],
            "combining_mark_burst": [
                {"text": "S"},
                {
                    "codepoints": ["0301", "0300", "0302", "0303", "0308", "0307"]
                },
                {"text": "AFE-FIXTURE-01"},
            ],
            "whitespace_bit_pattern": [
                {
                    "codepoints": [
                        "0020",
                        "0009",
                        "0020",
                        "0009",
                        "0020",
                        "0020",
                        "0009",
                        "0009",
                    ]
                }
            ],
            "escaped_zero_width": [{"text": r"SAFE-FIXTURE-01\u200B"}],
            "percent_encoded_zero_width": [
                {"text": "SAFE-FIXTURE-01%E2%80%8B"}
            ],
            "multiply_percent_encoded_zero_width": [
                {"text": "SAFE-FIXTURE-01%25E2%2580%258B"}
            ],
            "normalization_difference": [
                {"text": "SAFE-FIXTURE-01-e"},
                {"codepoints": ["0301"]},
            ],
            "nbsp_whitespace_pattern": [
                {
                    "codepoints": [
                        "0020",
                        "00A0",
                        "0020",
                        "00A0",
                        "0020",
                        "0020",
                        "00A0",
                        "00A0",
                    ]
                }
            ],
            "additional_default_ignorable": [
                {"text": "SAFE"},
                {"codepoints": ["2063"]},
                {"text": "-FIXTURE-01"},
            ],
        }
        actual_segments = {
            fixture["id"]: fixture["segments"] for fixture in manifest["fixtures"]
        }

        self.assertEqual(actual_segments, expected_segments)

    def test_reference_scanner_reports_direct_unicode_controls(self) -> None:
        scanner = self.load_reference_scanner()
        cases = {
            "SAFE-FIXTURE-01": [],
            "SA" + chr(0x200B) + "FE": ["zero_width"],
            "SAFE" + chr(0xFE0E) + chr(0xFE0F): ["variation_selector"],
            "SAFE" + chr(0xE0061) + chr(0xE007F): ["unicode_tag"],
            "SAFE" + chr(0x2066) + "X" + chr(0x2069): ["bidi_control"],
        }

        for text, expected in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(scanner.scan_text(text), expected)

    def test_reference_scanner_reports_mixed_scripts(self) -> None:
        scanner = self.load_reference_scanner()
        text = "S" + chr(0x0410) + "FE-FIXTURE-01"

        self.assertEqual(scanner.scan_text(text), ["mixed_script"])
        non_letter_in_latin_block = chr(0x00D7) + chr(0x0410)
        self.assertEqual(scanner.scan_text(non_letter_in_latin_block), [])

    def test_reference_scanner_reports_combining_mark_bursts(self) -> None:
        scanner = self.load_reference_scanner()
        marks = "".join(
            chr(codepoint)
            for codepoint in (0x0301, 0x0300, 0x0302, 0x0303, 0x0308, 0x0307)
        )

        self.assertEqual(
            scanner.scan_text("S" + marks + "AFE-FIXTURE-01"),
            ["normalization_difference", "combining_mark_burst"],
        )

    def test_reference_scanner_reports_whitespace_bit_patterns(self) -> None:
        scanner = self.load_reference_scanner()

        self.assertEqual(
            scanner.scan_text(" \t \t  \t\t"),
            ["whitespace_steganography"],
        )
        self.assertEqual(scanner.scan_text("SAFE FIXTURE"), [])

    def test_reference_scanner_reports_nbsp_whitespace_patterns(self) -> None:
        scanner = self.load_reference_scanner()
        pattern = "".join(
            chr(codepoint)
            for codepoint in (0x0020, 0x00A0, 0x0020, 0x00A0, 0x0020, 0x0020, 0x00A0, 0x00A0)
        )

        self.assertEqual(scanner.scan_text(pattern), ["whitespace_steganography"])

    def test_reference_scanner_reports_normalization_differences(self) -> None:
        scanner = self.load_reference_scanner()
        decomposed = "SAFE-FIXTURE-e" + chr(0x0301)

        self.assertEqual(scanner.scan_text(decomposed), ["normalization_difference"])

    def test_reference_scanner_reports_additional_default_ignorable_example(self) -> None:
        scanner = self.load_reference_scanner()

        self.assertEqual(
            scanner.scan_text("SAFE" + chr(0x2063) + "-FIXTURE-01"),
            ["zero_width"],
        )

    def test_reference_scanner_reports_escaped_invisible_codepoints(self) -> None:
        scanner = self.load_reference_scanner()

        self.assertEqual(
            scanner.scan_text(r"SAFE-FIXTURE-01\u200B"),
            ["escaped_invisible"],
        )
        self.assertEqual(
            scanner.scan_text(r"SAFE-FIXTURE-01\u{E007F}"),
            ["escaped_invisible"],
        )
        for malformed_escape in (r"SAFE\u{110000}", r"SAFE\uD800", r"SAFE\u{ZZ}"):
            with self.subTest(text=malformed_escape):
                with self.assertRaises(scanner.MalformedEncoding):
                    scanner.scan_text(malformed_escape)

    def test_reference_scanner_reports_percent_encoded_invisible_codepoints(self) -> None:
        scanner = self.load_reference_scanner()

        self.assertEqual(
            scanner.scan_text("SAFE-FIXTURE-01%E2%80%8B"),
            ["percent_encoded_invisible"],
        )
        for benign in ("SAFE%", "SAFE%GG", "SAFE%41"):
            with self.subTest(text=benign):
                self.assertEqual(scanner.scan_text(benign), [])
        for malformed_encoding in ("SAFE%E2%80", "SAFE%FF", "SAFE%C0%AF"):
            with self.subTest(text=malformed_encoding):
                with self.assertRaises(scanner.MalformedEncoding):
                    scanner.scan_text(malformed_encoding)

    def test_reference_scanner_bounds_multiply_encoded_percent_sequences(self) -> None:
        scanner = self.load_reference_scanner()

        self.assertEqual(scanner.MAX_DECODE_DEPTH, 2)
        self.assertEqual(scanner.MAX_DECODE_EXPANSION_RATIO, 1)
        self.assertEqual(
            scanner.scan_text("SAFE-FIXTURE-01%25E2%2580%258B"),
            ["multiply_encoded_invisible"],
        )
        with self.assertRaises(scanner.DecodeDepthExceeded):
            scanner.scan_text("SAFE-FIXTURE-01%2525E2%252580%25258B")

    def test_reference_scanner_enforces_the_utf8_input_budget(self) -> None:
        scanner = self.load_reference_scanner()

        self.assertEqual(scanner.scan_text("A" * scanner.MAX_INPUT_BYTES), [])
        with self.assertRaises(scanner.InputBudgetExceeded):
            scanner.scan_text("A" * (scanner.MAX_INPUT_BYTES + 1))

        multibyte_character = chr(0x00E9)
        exact_multibyte_input = multibyte_character * (
            scanner.MAX_INPUT_BYTES // len(multibyte_character.encode("utf-8"))
        )
        self.assertEqual(scanner.scan_text(exact_multibyte_input), [])
        with self.assertRaises(scanner.InputBudgetExceeded):
            scanner.scan_text(exact_multibyte_input + multibyte_character)
        with self.assertRaises(ValueError):
            scanner.scan_text(chr(0xD800))

    def test_fixture_manifest_is_an_immutable_executable_oracle(self) -> None:
        scanner = self.load_reference_scanner()
        manifest = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
        maximum_bytes = manifest["_meta"]["max_utf8_bytes_per_fixture"]

        for fixture in manifest["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                segments_before = json.dumps(fixture["segments"], sort_keys=True)
                text = scanner.render_segments(fixture["segments"])
                self.assertEqual(
                    json.dumps(fixture["segments"], sort_keys=True),
                    segments_before,
                    "render処理がfixture定義を書き換えないこと",
                )
                self.assertLessEqual(len(text.encode("utf-8")), maximum_bytes)
                self.assertEqual(
                    scanner.scan_text(text),
                    fixture["expected_findings"],
                )

    def test_fixture_renderer_rejects_ambiguous_or_unsafe_segments(self) -> None:
        scanner = self.load_reference_scanner()
        invalid_segments = (
            [{}],
            [{"text": "SAFE", "codepoints": ["200B"]}],
            [{"text": "SAFE", "extra": "value"}],
            [{"codepoints": []}],
            [{"codepoints": ["not-hex"]}],
            [{"codepoints": ["D800"]}],
            [{"codepoints": ["110000"]}],
        )

        for segments in invalid_segments:
            with self.subTest(segments=segments):
                with self.assertRaises(ValueError):
                    scanner.render_segments(segments)

        with self.assertRaises(scanner.InputBudgetExceeded):
            scanner.render_segments([{"text": "A" * (scanner.MAX_INPUT_BYTES + 1)}])
        with self.assertRaises(scanner.InputBudgetExceeded):
            scanner.render_segments(
                [{"text": ""}] * (scanner.MAX_SEGMENTS + 1)
            )
        with self.assertRaises(scanner.InputBudgetExceeded):
            scanner.render_segments(
                [
                    {
                        "codepoints": ["0020"]
                        * (scanner.MAX_CODEPOINTS_PER_SEGMENT + 1)
                    }
                ]
            )
        with self.assertRaises(scanner.InputBudgetExceeded):
            scanner.render_segments(
                [
                    {"codepoints": ["0020"] * scanner.MAX_CODEPOINTS_PER_SEGMENT}
                ]
                * (
                    scanner.MAX_TOTAL_CODEPOINTS
                    // scanner.MAX_CODEPOINTS_PER_SEGMENT
                    + 1
                )
            )

    def test_fixture_corpus_contains_no_external_or_executable_material(self) -> None:
        raw = FIXTURE_MANIFEST.read_text(encoding="utf-8").lower()
        forbidden_tokens = (
            "http://",
            "https://",
            "#!/",
            "subprocess",
            "os.system",
            "eval(",
            "exec(",
            "curl ",
            "wget ",
            "powershell",
        )

        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, raw)


if __name__ == "__main__":
    unittest.main()
