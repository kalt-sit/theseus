# skill置き場（Notes/Skills Install Log.md）のキュレーション手順

Obsidian の skill置き場を正直な状態に保つワークフロー：未導入候補を監査し、結果を Notes/Skills Install Log.md に記録し、install / borrow-principles / skip を決める。リスト全体の処遇を決めるのがこの手順、個別スキルの深掘りは skill-vetting.md（両者はセットで使う）。

## 0. Source of truth
- Vault: `$OBSIDIAN_VAULT_PATH/Notes/Skills Install Log.md`（未設定ならユーザーにVaultの場所を確認し、絶対パスをハードコードしない）。※実ファイル名は複数形「Skills Install Log.md」。ユーザーは「Skill Install Log」「Skills.md」等と呼ぶことがあるが、実体はこの複数形ファイル。
- 監査基準と重み順（Security Audits ＞ 実体読取 ＞ 提供元 ＞ installs）は SKILL.md 原則6 を参照。
- スキルの導入先: `~/.hermes/skills/`（一部は `~/.agents/skills/` へのシンボリックリンク）。
- **theseus スキルのみ例外**: `~/.hermes/skills/security/theseus` がマスター。他環境（`.agents` / `.claude`）への共有は symlink または `git archive` デプロイ・コピー。編集はマスターのみ（SKILL.md §0・§8）。

## 1. 発動タイミング
- 「未導入skillを監査」「skill置き場を整理」「導入見送りって書いた？」等の依頼時、または find-skills で候補が出た後。
- 定期タスク向き：AgentReach で話題のスキルを1日最大3件収集 → Notes/Skills Install Log.md に追加 → 監査。

## 2. 候補ごとの監査
1. skill-vetting.md の手順で実体を確認（SKILL.md・references を読む。実行コード・通信・data-egress・注入の有無）。
2. skills.sh でメタデータ（installs / Security Audits / ★）を確認。
3. 分類する：
   - **install** — 監査クリア＋ローカル完結
   - **borrow-principles** — 安全だが価値の発揮に有料外部APIが必要（§5）
   - **skip** — 基準未達、またはコストをかけたくない

## 3. 一括マーキングのルール（重要・ユーザー指定）
リストを監査したときは、deep-dive した1件だけでなく**全件**をマーキングする。
- 軽量マークで十分：`導入 : 未` → `導入 : 未 監査済み` を対象全件に。個別の詳細プロースは focused な件のみでよい。

## 4. 見送り理由の記録（重要・ユーザー指定の定型文）
有料外部API / data-egress を理由に見送る場合、次の定型文を明記する：
```
導入見送り理由 : 外部API（<Name>）の呼び出しが必要で、利用に応じてお金がかかるため。ローカルHTML案件ではコストを避けるため見送り、無料で完結する範囲（原則借用）のみ活用。
```
focused な件のエントリに書き、別途サマリーセクションを書いた場合はそちらにも書く（2箇所）。

## 5. Borrow-principles パターン（有料APIスキルは導入より原則借用）
安全だが価値の発揮に有料外部APIが必要なスキルは、導入せず**原則を読んで既存ローカルスキルへ統合**する。
- 実例（touchstone）: hallmark（"Powered by Together AI"）→ 本体は入れず、STRUCTURAL VARIETY / PRE-EMIT SELF-CRITIQUE / 8-STATE MANDATE 等の原則のみ `design-taste-frontend` へ統合。すべて無料・ローカル・外部送信なし。
- マーキング：`導入 : 未（監査済・<日付>）→ 本体は導入せず、原則のみ <統合先skill> へ統合` ＋ §4 の見送り理由。

## 6. Pitfalls
- **Source-of-truth のファイル名が実 Vault と食い違ったら、メモリ / ad-hoc 検索で逃げず本ファイルを直す。** 2026-07-19 実例：本ファイルが `Notes/Skills Install Log.md` とハードコードされていたためエージェントが誤った名前を探し回り、実体は `Skills Install Log.md`（複数形）だった。ユーザー指示「正しい名前を覚える（メモリ）」ではなく「スキル文書の参照を正しい名前に直す」が根本解。読み取り専用の場合はユーザーに `chmod u+w <file>` と `chmod u+w <dir>` を依頼してから編集（theseus は `.hermes` マスターのみ編集可・配布コピーは symlink/デプロイ）。一般化：サードパーティ導入時の「記録先」「設定項目名」等、スキル文書に書かれた参照が実態と違う場合はその場しのぎせず文書を修正する。
- **Notes/Skills Install Log.md への patch（部分置換）は失敗しやすい。** `---` や `導入 : 未` が十数回繰り返されるためアンカーが一意にならない。ファイル全体を読み、全体を書き戻す方式にする。部分パッチでループしない。
- **シンボリックリンクのスキルは実体側を編集する。** `readlink -f` でリンク先（`~/.agents/skills/...`）を確認してから編集し、リンク経由で反映を確認。
  - **例外: theseus スキル自身。** theseus は `~/.hermes/skills/security/theseus` をマスターとし、`~/.agents/skills/theseus`・`~/.claude/skills/theseus` は symlink またはデプロイ・コピーで配布される。編集は**マスター（`.hermes`）でのみ**行い、配布コピー側での編集は禁止（SKILL.md §0・§8 の運用条件）。theseus を監査・更新する際は必ずマスターを直接開くこと。
- **監査結果を捏造しない。** 実際に読んだものだけを根拠にする。取得がブロックされたら「未確認」と明示してユーザーに確認し、"Pass" と断定しない。
- **2つのスキルレジストリは独立。** `~/.hermes/skills/`（Hermes）と `~/.agents/skills/`（.agent）は別ストアで、片方への追加はもう片方に反映されない。.agent へ手動登録するにはフォルダごと `~/.agents/skills/<name>/` にコピー（SKILL.md ＋ references/）。手動配置はロックファイル不要（ディレクトリスキャンで発見される）。`find ~/.agents/skills -name SKILL.md` で確認。
- **成果物の上書き禁止の慣例。** refine 系タスクでは元ファイルを上書きせず新ファイルに書く。ただし SKILL.md の編集はその例外（in-place 可）。
- **`npx skills add … -g -y` の "Failed to install 1 / PromptScript does not support global skill installation" は既知の偽エラー。** 実体は `~/.agents/skills/<name>/` に置かれ、Hermes へシンボリックリンクされる。偽エラーで導入失敗と早合点せず、`find ~/.agents/skills -name SKILL.md | grep -i <name>` で実体を確認する。
- **マーケティング名 ≠ リポジトリ / スキル名。** 例：インフォグラフィックの「Kill AI Slop」= リポジトリ `hardikpandya/stop-slop`（スキル名 `stop-slop`）。インフォグラフィック・ブログ等の「表示名」は監査・導入時の管理キーにせず、リポジトリURLとスキル名で管理する。

## 7. Output（完了条件）
- Notes/Skills Install Log.md が更新されている：全件マーキング＋見送り理由＋（あれば）borrow-principles の統合記録。
- チャットに短いサマリー：基準の判定結果、何をマークしたか、何を借用/見送りにしたか、およびその理由。
