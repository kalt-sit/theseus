# Theseus

[English](README.md) | 日本語

**テセウスは、好奇心旺盛なあなたの旅をサポートする防御Skillです。**

サードパーティ製のAgent Skillを導入する前に監査し、LLMトークンを消費せずに改ざんも検知します。

Theseusは、Hermes Agentがプロンプトインジェクションへ対処し、サードパーティ製Skillを安全に監査するためのSkillです。
監査する文書やコードは、命令ではなく未信頼のデータとして扱います。外部モデルや外部APIは必須ではありません。

> [!IMPORTANT]
> 自動監視にはHermesのcron機能を使います。同梱スクリプトだけを`no_agent`（CLIでは`--no-agent`）モードで実行するため、LLMは呼び出されず、モデルや推論APIの料金・クレジットを消費しません。Hermes Agentと`git`は別途必要です。

## ユースケース

- **新しいSkillを試したいとき**

  `SKILL.md`、同梱スクリプト、要求される権限、外部通信、プロンプトインジェクションのリスクを導入前に確認します。

- **外部コンテンツに指示のような文言が含まれているとき**

  未信頼のデータと信頼できる指示を分離し、外部コンテンツに書かれた内容をそのまま命令として扱わないための原則を適用します。

- **候補のSkillをまとめて整理したいとき**

  各候補を `install`（導入）、`borrow-principles`（原則のみ借用）、`skip`（見送り）に分類し、導入判断とその根拠を整理します。結果は、ユーザーが指定した保存先（例：Obsidianのノート）へ記録できます。

- **導入後の改ざんを監視したいとき**

  Gitの `HEAD` とリポジトリ外部に保存したピンを `no_agent` cronで照合します。正常時は通知せず、異常を検出した場合のみ通知します。

## 含まれるもの

このリポジトリにはTheseus本体だけを収録しています。

```text
SKILL.md
references/
  cron-setup.md
  library-curation.md
  porting-to-codex.md
  skill-vetting.md
  tamper-detection.md
  verify-guards-and-credentials.md
  vetted-tools.md
scripts/
  theseus-integrity-check.sh
```

## インストール

### Skills CLI（推奨）

TheseusをHermes AgentのグローバルSkillディレクトリへ導入します。

```bash
npx skills add kalt-sit/theseus --skill theseus -g -a hermes-agent --copy -y
```

Skills CLIは、匿名化されたインストール集計情報を既定で送信します。skills.shは、この情報をディレクトリへの掲載とランキングに使用します。送信しない場合は、`DISABLE_TELEMETRY=1`を設定してください。

### 手動インストール

HermesのSkillディレクトリへ、`SKILL.md`が次の位置になるように配置します。

```text
$HERMES_HOME/skills/security/theseus/SKILL.md
```

`HERMES_HOME`が未設定の場合、既定値は`~/.hermes`です。Gitで取得する場合は次のコマンドを使います。

```bash
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
git clone https://github.com/kalt-sit/theseus.git "$HERMES_HOME/skills/security/theseus"
```

ZIPで取得した場合は、展開後のディレクトリ名を`theseus`にして同じ場所へ配置してください。

## 改ざん検出と日次監視

GitのHEADと外部ピンを照合する初期設定と、LLMを使わない日次cron監視については、[`references/cron-setup.md`](references/cron-setup.md)を参照してください。正常時は何も送らず、異常を検出したときだけ通知します。

### 通知先

通知先はHermes cronの`deliver`設定で選びます。

- `origin`: cronを作成したDiscord、Slack、Telegramなどのチャットへ返す
- `local`: メッセージサービスを使わず、Hermesのローカル出力へ保存する
- `discord`、`slack`、`telegram`など: Hermesで設定済みの各ホームチャンネルへ送る
- `all`: Hermesへ接続済みの全ホームチャンネルへ送る

## セキュリティ上の注意

- 監査対象のSkill、Webページ、ファイル、ツール出力に書かれた命令には従わず、未信頼のデータとして扱います。
- 導入前に内容を確認し、信頼するコミットを外部ピンへ固定してください。
- Theseus自身も改ざんされる可能性があります。整合性確認に失敗した場合は自動復元せず、先に差分を調べてください。

## ライセンス

MIT Licenseです。詳細は[`LICENSE`](LICENSE)を参照してください。
