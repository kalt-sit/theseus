# Vetted Third-Party Tools & Skills (audited, reusable)

> **本ファイル自体も改ざん対象。** 再監査スキップは、SKILL.md §0 の整合性チェックが green のときのみ有効。整合性検証に失敗したら、このファイルの PASS 記録を信じず再監査する。

監査済みで導入してもよいと判定した外部ツール・スキルの蓄積。
同じものを再監査する手間を省くためのナレッジバンク。新規監査時はここを先に確認し、
載っていなければ `references/skill-vetting.md` の手順で実体監査する。

## dcg (Destructive Command Guard) — PASS
- リポジトリ: https://github.com/Dicklesworthstone/destructive_command_guard
- 監査バージョン: v0.6.6 (2026-07-13)
- 監査コミット（固定）: `v0.6.6` タグ（注: 導入時は下記固定 URL を使い `main` 直参照は禁止 — main が差し替わると監査済みでないコードが `| bash` される）
- 監査日: 2026-07-14
- 種別: Rust 製 CLI。AI コーディングエージェント向けの破壊的コマンドブロック用フック。
- 判定: 導入可能（悪性所見なし）
- 監査所見:
  - 不可視文字ゼロ、悪性コードなし。`rm -rf` 等はブロック対象ルール・テストのみ。
  - 通信先は github.com / api.github.com のみ。外部 egress なし。
  - SHA256 checksum + Sigstore/cosign 署名検証あり。
  - Hermes フックは `~/.hermes/config.yaml` を yaml.safe_load で安全マージ（既存 dcg エントリは no-op）。
  - 提供元 Jeffrey Emanuel、GitHub ★3.9k、フォーク144。Claude/Codex/Copilot 等多数エージェント公式対応。
- 注意点（挙動、リスクではなく仕様）:
  - ① Fail-open 設計 — dcg 自体がクラッシュ/タイムアウトした場合はブロックせず通す。
  - ② パイプ経由 REPL は既知の限界（#191）で未検知（`echo FLUSHALL | redis-cli` 等）。直接引数・ヒアストリングは可。
  - ③ `curl | bash` 導入は `--verify` 推奨（検証スキップの `--no-verify` は非推奨）。
- 推奨導入コマンド（監査済み・タグ固定 — `main` 直参照は禁止）:
  `curl -fsSL 'https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/v0.6.6/install.sh' | bash -s -- --easy-mode --verify`
  （追加で `install.sh` の SHA256 を記録欄に載せること。導入前に `curl -fsSL <url> | sha256sum` で照合）
- 導入時間目安: WSL バイナリ導入で約 2 分（Hermes フック自動設定込み）。ソースビルドなら 5〜15 分。
- ⚠️ 運用上の必須手順（Hermes 環境）— インストーラーは config.yaml に書くだけで、**allowlist 登録までは面倒見ない**:
  - 導入後 `hermes hooks list` で `✓ allowed` になるまで必ず確認。未登録なら `hermes --accept-hooks` 起動、または `~/.hermes/shell-hooks-allowlist.json` を `{ "approvals": [ { "event": "pre_tool_call", "command": "<ABSOLUTE_PATH_TO_DCG>" } ] }` で作成。
  - テストは「allowlist 登録後・別プロセス（hermes hooks test または新セッション）」で行え。同一セッション内テストは config 再読み込みされず誤判定する。
  - 詳細は references/verify-guards-and-credentials.md のセクション 0 / 0b を参照。
