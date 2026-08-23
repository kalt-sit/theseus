# Theseusの日次cron監視 — 最小導入ガイド

このガイドは、Theseus Skill のGit作業ツリーと外部ピンを定期照合し、異常時だけ通知する最小構成を示す。Hermesの `no_agent` cronを使うため、正常時のLLM呼び出しと通知は発生しない。

## 前提

- Theseusディレクトリ一式（`SKILL.md`、`references/`、`scripts/`）を受け取っている。
- 内容を人が確認し、信頼できる配布元から受け取ったと判断している。
- `git` とHermes Agentが利用できる。

既定の配置先は `$HERMES_HOME/skills/security/theseus`。`HERMES_HOME` が未設定なら `~/.hermes` を使う。

## 1. 信頼する版をGitと外部ピンで固定する

内容を確認してから、受け取った版を初期基準としてコミットする。

```bash
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
THESEUS="$HERMES_HOME/skills/security/theseus"

if ! git -C "$THESEUS" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$THESEUS" init -q
  git -C "$THESEUS" add -A
  git -C "$THESEUS" -c user.name="Hermes" -c user.email="hermes@local" \
    commit -q -m "baseline: trusted theseus skill"
fi

mkdir -p "$HOME/.claude"
git -C "$THESEUS" rev-parse HEAD | \
  tee "$HOME/.claude/theseus-pin.txt" >/dev/null
chmod 444 "$HOME/.claude/theseus-pin.txt"
```

確認結果が一致し、Git状態が空なら基準作成は完了。

```bash
git -C "$THESEUS" rev-parse HEAD
tr -d '\r\n' < "$HOME/.claude/theseus-pin.txt"; printf '\n'
git -C "$THESEUS" status --porcelain
```

## 2. 監視スクリプトを配置する

Hermes cronが実行できる場所へ同梱スクリプトをコピーする。

```bash
mkdir -p "$HERMES_HOME/scripts"
cp "$THESEUS/scripts/theseus-integrity-check.sh" \
  "$HERMES_HOME/scripts/theseus-integrity-check.sh"
chmod 755 "$HERMES_HOME/scripts/theseus-integrity-check.sh"
```

正常系では標準出力が空になる。

```bash
output="$("$HERMES_HOME/scripts/theseus-integrity-check.sh")"
[ -z "$output" ] && echo "PASS: 正常時は無音" || printf '%s\n' "$output"
```

外部ピンを一時的に `/dev/null` として実行すれば、実ファイルを変更せず異常通知を確認できる。

```bash
THESEUS_PIN=/dev/null "$HERMES_HOME/scripts/theseus-integrity-check.sh"
```

## 3. 通知先を選び、日次cronを登録する

Theseusは通知サービスへ直接接続しない。監視スクリプトの出力を、Hermes cronの `deliver` で指定した場所へ渡す。

| 利用方法 | `deliver` の値 | 補足 |
|---|---|---|
| Discord・Slack・Telegramなど、そのcronを作ったチャットへ返す | `origin` | メッセージ上でHermesに作成を頼む場合に便利 |
| 外部サービスを使わずローカルへ保存 | `local` | CLI利用者や、メッセージサービス未接続の利用者向け |
| Discordのホームチャンネル | `discord` | DiscordがHermesへ設定済みであること |
| Slackのホームチャンネル | `slack` | SlackがHermesへ設定済みであること |
| Telegramのホームチャンネル | `telegram` | TelegramがHermesへ設定済みであること |
| 接続済みの全ホームチャンネル | `all` | 実行時点で接続済みのサービスへ配信 |

CLIから登録する場合は、最初に通知先を選ぶ。次は外部サービスを使わない例。

```bash
DELIVERY_TARGET="local"

hermes cron create "0 9 * * *" \
  --no-agent \
  --script theseus-integrity-check.sh \
  --deliver "$DELIVERY_TARGET" \
  --name theseus-integrity-daily
```

Discordなら `DELIVERY_TARGET="discord"`、Slackなら `DELIVERY_TARGET="slack"` に変更する。Hermesとのメッセージ上で作成する場合は、「この監視スクリプトを毎日9時に、異常時だけこのチャットへ通知して」のように頼めば `origin` を使える。

`--no-agent` は、スクリプト自体をcronジョブとして実行するHermesの機能。スクリプトの標準出力が空なら通知なし、異常メッセージがあればそのまま配信される。LLM、モデル、推論APIは呼び出されない。スクリプト失敗やタイムアウトはHermes側のエラー通知になる。

> [!NOTE]
> `discord`、`slack`、`telegram` などへ通知するには、対象サービスが先にHermesへ接続・設定されている必要がある。接続していないサービスをTheseusが自動設定することはない。

## 4. 登録確認

```bash
hermes cron list
hermes cron run theseus-integrity-daily
```

`theseus-integrity-daily` が有効で、手動実行後の状態が `ok` なら導入完了。正常時にメッセージが届かないのは仕様。

## 更新時

Theseusを正規に更新した場合だけ、新しいコミットのHEADで外部ピンを更新する。意図しない差分やHEAD不一致を見つけた場合は自動復元せず、`references/tamper-detection.md` に従って調査する。

## 範囲

この最小構成が監視するのはTheseusディレクトリの未コミット変更と、HEAD・外部ピンの不一致だけ。SOUL.md、Hermes設定、allowlistなどの追加監視は必要になってから別ジョブとして足す。
