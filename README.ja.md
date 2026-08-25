# Theseus

> テセウスは好奇心旺盛なあなたの旅をサポートする防御Skillです。サードパーティ製のAgent Skillを導入前に監査し、未信頼データと正規の指示を分離しながら、外部モデルや常駐サービスなしで動作します。

Theseusは、[Agent Skills](https://agentskills.io/)形式のSkillを対象とする、ポータブルで読み取り専用のセキュリティ監査Skillです。候補パッケージ全体を棚卸しし、コード実行、ダウンロード、権限、永続化、秘密情報、外部コンテンツ取得を調べ、根拠付きでPASS／CONDITIONAL／REJECTを返します。

## Theseusが守る境界

Agent Skillは自然言語の指示・スクリプト・参照資料をまとめたものです。`SKILL.md`だけを読む、監査バッジだけを信じる、監査中にセットアップ手順を動かす、といった方法では実体のリスクを見落とします。

Theseusは次を徹底します。

- 候補内の文章やコードは、信頼済みの指示ではなくデータとして扱う
- 監査中は読み取り専用とし、候補の指示を実行しない
- パッケージ内の全ファイルを確認対象にする
- インストールや設定変更は、監査とは別のユーザー判断に分ける
- 人気・提供元・自動監査は補助情報として使い、実体確認の代わりにしない

## ユースケース

- サードパーティSkillを導入前に確認する
- 更新版と以前に承認した版を比較する
- skills.shなどの監査警告や想定外の機能を調べる
- チーム判断用に根拠付きの監査報告を作る
- 承認前に必要な権限と通信先を洗い出す

## インストール

```bash
DISABLE_TELEMETRY=1 npx skills@1.5.23 add 'kalt-sit/theseus#v2.0.0' --skill theseus -g -a hermes-agent --copy -y
```

このコマンドはSkills CLIのversionとTheseusのrelease tagを固定し、CLIの匿名install telemetryを無効化します。導入前にtag内の`skills/theseus/`を確認し、導入後はコピーされたpackageがtag内の同directoryと一致することを確認してください。Theseus本体はtelemetryを送信せず、外部モデルの呼び出し、補助ツールの導入、ホスト設定の変更も行いません。

## 配布境界

インストール対象は意図的に小さくしています。

```text
skills/theseus/
├── SKILL.md
└── references/
    └── audit-checklist.md
```

過去の端末固有の運用記録、installer手順、hook、定期ジョブ、ローカルの記録先は公開Skill packageに含めません。

## v1からの移行

Version 2は、意図的に小さくしたハーネス非依存のsecurity coreです。v1に含まれていたホスト自動化、整合性監視script、ローカルtrust記録、ハーネス固有のsetup guideは削除されます。これらへ依存している場合は、別管理のlocal adapterへ置き換えるまでv1を固定して使ってください。v2の導入だけでは既存のactive monitoringを代替しません。

## 互換性

Coreの監査原則はハーネス非依存で、ネットワーク接続やコード実行を必要としません。利用するAgent SkillsクライアントがSkillを読み、候補ファイルを静的に確認できれば利用できます。

## ホスト別ガイド

- [Hermes Agent](docs/hosts/hermes.md)
- [Codex](docs/hosts/codex.md)

各ガイドでは、Skillの検出、監査依頼、期待する報告、ホスト側の権限境界だけを説明します。インストール対象のCoreへホスト自動化は追加しません。

## 開発時の確認

Python標準ライブラリだけで配布契約テストを実行できます。

```bash
python3 -m unittest discover -s tests -v
```

テストは、配布ファイルのallowlist、標準frontmatter、読み取り専用契約、相対リンク、既知の高リスクscannerトリガー不在を確認します。

## セキュリティ

脅威モデルと非公開報告経路は [SECURITY.md](SECURITY.md) を参照してください。Theseusは監査漏れを減らしますが、暗号化・難読化・動的取得・可変参照された実体の安全性を証明するものではありません。

## English

English documentation is available in [README.md](README.md).

## ライセンス

MIT
