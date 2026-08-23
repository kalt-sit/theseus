# 認証形態の確認と保護フックの実動作検証

`theseus` スキル監査時・サードパーティ保護ツール導入後の検証で使う実践手順。
dcg (Destructive Command Guard) を題材にするが、手順自体は汎用。

## A. 認証・課金形態の確認（シークレットを漏らさない）

目的: Claude Code 等が「サブスク（OAuth）か / API 従量課金（ANTHROPIC_API_KEY）か」を判定する。
方針: **生トークン・キーは絶対に print しない。**

マスク出力スクリプトの形（Python 例）:
- JSON は読み、値は `型 + 長さ` のみ表示（文字列>40字は `<文字列 長さN マスク>`）
- サブスク/OAuth 指標キー名だけ検出: `oauthAccount`, `accessToken`, `subscriptionType`, `organizationId` 等
- 環境変数は `os.environ.get('ANTHROPIC_API_KEY','')` の「長さのみ」表示（prefix も出さない）
- rc ファイル内の定義は `grep -n KEY` して `=` 以降を `<マスク>` に置換

判定ロジック:
- `~/.claude.json` に `oauthAccount` キーあり ⇒ **サブスク（OAuth）認証** → 従量課金されない
- シェル環境に `ANTHROPIC_API_KEY` が設定済み ⇒ **API 従量課金** → `claude -p` でも同経路でトークン課金
- **`-p/--print` フラグは出力モードであり課金経路を変えない** — 普段の対話と同じ認証が適用される

> ユーザーが raw 認証ファイル出力をブロックした事例あり。マスク設計を提示してから実行せよ。

## B. 保護フックが本当に発動するか検証（Hermes 編・fail-open 罠）

`dcg doctor` / インストーラーの "settings updated" は **登録の有無**しか保証しない。
実際の遮断は別問題。以下の順で検証。

### 0. ⚠️ Hermes 固有の「初回使用同意ゲート」(最優先・原因の8割)

Hermes は `config.yaml` にフックを書いただけでは**発動しない**。
`~/.hermes/shell-hooks-allowlist.json` に `command` が allowlist 登録されていることが必須。
未登録だと `hermes hooks list` に `✗ not allowlisted` と出て、**フックはそもそも呼ばれず**（dcg は一切動かず、`rm -rf` がそのまま通る）。

確認と解決:
- 状態確認: `hermes hooks list` → `(timeout=30s, ✗ not allowlisted)` なら未登録
- 診断: `hermes hooks doctor` → `✗ not allowlisted — hook will NOT fire at runtime` が出る
- 登録（いずれか）:
  - 起動時自動承認: `hermes --accept-hooks`（または `--accept-hooks` 付きで chat/gateway 起動）
  - 直接作成: `~/.hermes/shell-hooks-allowlist.json` を以下の形で書く（監査済み安全な hook のみ）
    ```json
    {
      "approvals": [
        { "event": "pre_tool_call", "command": "<ABSOLUTE_PATH_TO_DCG>" }
      ]
    }
    ```
    > ⚠️ **allowlist の直接作成は特権操作。** ユーザー承認必須。また本ファイルは「deferred injection の永続化面」でもあり、SKILL.md §9 の通り外部データを引き金に変更してはならない。日次整合性チェック（E-3）の監視対象に含めること。
  - フォーマット根拠: `shell_hooks.py` の `_is_allowlisted` は `event` と `command` の完全一致を見る
- 登録後 `hermes hooks doctor` が `✓ allowlisted (approved ?)` / `All shell hooks look healthy.` になることを確認

> **これが「インストーラーが config を書いたのに何も守ってくれない」最大の理由。**
> dcg のようなツール導入後は、allowlist まで面倒見きれているか必ず `hermes hooks list` で確認せよ。

### 0b. ⚠️ 設定変更は「別プロセス」で効く — 同一セッション内テストは信頼できない

- Hermes は config / allowlist を**起動時に読み込み**、実行中セッションは再読み込みしない。
- したがって「config を直してから同じセッション内で `rm -rf` テスト」をしても、古い（未登録）状態のまま動き、**誤って「遮断されない」と判断する**。
- **検証は必ず別プロセスで行う**:
  - `hermes hooks test pre_tool_call --for-tool terminal --payload-file X.json`（新プロセス・現在の config を読む）
  - または新しい `hermes` セッションを起動してからテスト

### 1. Hermes は `~/.hermes/config.yaml` の直接編集を拒否する

- `patch` / `write_file` で config.yaml を書き換えようとすると
  `Refusing to write to Hermes config file ... Edit directly or use 'hermes config'` で弾かれる（保護機構）。
- 正規の変更手段は `hermes config set <dotted.key> <value>`:
  - 例: `hermes config set hooks.pre_tool_call.0.command "<ABSOLUTE_PATH_TO_DCG>"`
  - ネスト・配列はドット記法（`hooks.pre_tool_call.0.command`）。確認は `hermes config show` または直接 read_file。

### 2. フック `command` は「単一実行ファイル」のみ — パイプは拒否される

- `command: tee /tmp/x.json | <ABSOLUTE_PATH_TO_DCG>` のような**パイプ形式は `hermes hooks doctor` で `✗ script missing or not executable` と弾かれる**。
- ペイロード採取等で前処理が必要な場合は、**ラッパースクリプト**を作り、`command` にその絶対パスを指定する（スクリプトには `chmod +x` と shebang 必須）:
  ```sh
  #!/bin/sh
  # <ABSOLUTE_PATH_TO_DCG>-hermes-capture
  tee /tmp/hermes-hook-payload.json | <ABSOLUTE_PATH_TO_DCG> "$@"
  ```

### 3. 実ペイロードの採取（最初に、スキーマ不一致を見抜く）

フック `command` を一時的に上記ラッパー（`tee` 採取）に差し替え、allowlist もラッパーのパスで更新。
エージェント経由で**無害な** `echo hello` を実行し、`/tmp/hermes-hook-payload.json` に Hermes が実際に送った JSON を保存。
（手作り JSON でテストするとスキーマ不一致を見逃す — 実物と照合こそが決め手）

dcg の Hermes 期待入力（src/hook.rs より、実際に Hermes が送る形と一致を確認済み）:
```json
{"hook_event_name":"pre_tool_call","tool_name":"terminal","tool_input":{"command":"echo hello"},"session_id":"...","cwd":"<HOME_DIRECTORY>"}
```
- **`command` は `tool_input.command` のネスト構造**。Hermes はこの正しい形を送る。
- 採取ペイロードの `tool_input.command` を `rm -rf /tmp/theseus-dcg-test-victim` に書き換え、**オフライン**で `cat payload.json | <ABSOLUTE_PATH_TO_DCG>` に通す。
  - `{"decision":"block",...}` が返ればルールエンジン＋スキーマ解釈は正常。遮断されない原因は「フックが呼ばれていない（allowlist 未登録等）」に絞れる。
  - 何も出ず exit=0 なら dcg がパース失敗で fail-open（この場合はラッパーで `env DCG_FAIL_CLOSED=1` を足し、パース失敗時に全ブロック＝気づける故障にする）。

> **注意（過去の誤結論）**: かつて「スキーマ不一致×fail-open が原因、修正は `dcg hook` + `DCG_FAIL_CLOSED=1`」とされたが、
> 実際には Hermes は正しい `tool_input.command` を送っており、真因は **allowlist 未登録（0）** だった。
> `dcg hook` への書き換えが必須かは未証明 — まず allowlist 登録（0）と別プロセス検証（0b）を済ませよ。

### 4. 安全な実弾テスト（隔離）

- 負のテスト: `mkdir ~/dcg-test-victim` → エージェント経由で `rm -rf ~/dcg-test-victim` → **ブロックされて dir が残る**ことを確認
- 正のテスト: `ls` 等が通ること（fail-closed ですべてブロックされていないか確認 — これを飛ばすとエージェントが実質使用不能に）
- 本物のホーム/プロジェクトは絶対に触らない。犠牲 dir は `~` 直下の明確なダミィ名にとどめる
- **実弾テストは必ず「allowlist 登録後・別プロセス（新セッション or `hermes hooks test`）」で行う**（0・0b を参照）

### 5. ルールエンジン単体の健全性確認
`dcg explain "rm -rf /tmp/theseus-dcg-test-victim"` → `Decision: DENY (core.filesystem:rm-rf-root-home)` ならエンジンは正常。
遮断されない原因は「入力パース層／発動層（手前）」にあると特定できる。

### 6. Hermes フック診断コマンド一覧
- `hermes hooks list` — 登録一覧＋`✓ allowed` / `✗ not allowlisted` ステータス
- `hermes hooks doctor` — exec bit / allowlist / JSON 妥当性 / 空ペイロードでの合成実行タイミング
- `hermes hooks test <event> --for-tool terminal [--payload-file X.json]` — 新プロセスでフックを発火。
  `parsed: <none — hook contributed nothing to the dispatcher>` と出たら、フックは呼ばれたが block 出力を返さなかった（スキーマ不一致か、ルールが引っかからなかったか）。
- `hermes config set <k> <v>` / `hermes config show` — config 変更・確認（直接編集は不可）
