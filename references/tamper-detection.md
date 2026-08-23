# スキル自身のランタイム改ざん検出・復元（git ベース）

## 動機
theseus の SKILL.md / references/ は通常 600/644（owner 書込み可）。
プロンプトインジェクションでエージェントが自らのスキルファイルを上書きすると、
「防御が丸裸になる」唯一の経路が生まれる。
`chattr +i` は WSL2 で `Operation not permitted` となり使えないため、git で復元基点を作る。

## セットアップ（1回のみ）
```bash
cd ~/.hermes/skills/security/theseus
git init -q
git -c user.email=hermes@local -c user.name=Hermes add -A
git -c user.email=hermes@local -c user.name=Hermes commit -q -m "baseline: clean snapshot"
```
※ 他の重要スキル（SOUL.md / CLAUDE.md レイヤー含む）も同様に git 管理すると復元基点が強化される。

## 検出（いつでも実行）
```bash
cd ~/.hermes/skills/security/theseus
git status --short   # 空なら clean。何か出たら要調査
git diff --stat      # 変更されたファイルと行数
# 外部アンカー照合（攻撃者が .git を汚染してもディレクトリ外ピンは触れない）
PIN=$(cat ~/.claude/theseus-pin.txt)
[ "$(git rev-parse HEAD)" = "$PIN" ] && echo "HEAD OK (pinned)" || echo "HEAD MISMATCH — 改ざん疑い"
```

## 復元（ピン基準のみ — 重要）
攻撃者が汚染をコミットしていた場合、`git checkout -- .`（HEAD 相対）は**汚染状態への復元**になる。必ずピン値または bare ミラーを明示指定する:
```bash
cd ~/.hermes/skills/security/theseus
PIN=$(cat ~/.claude/theseus-pin.txt)
git fetch ~/.theseus-mirror.git   # ミラーから最新の検証済み状態を取得
git reset --hard "$PIN"           # または: git checkout "$PIN" -- .
# ミラー経由で完全復元する場合:
#   git fetch ~/.theseus-mirror.git master && git reset --hard FETCH_HEAD
```
意図的な改善を加えた場合は `chmod +w` → 編集 → `git add -A && git commit -m "理由"` → ピンファイル更新 → mirror へ push → `chmod -w` で新たな基点を作る（正規更新フロー）。

## シンボリックリンク共有の伝播リスクと運用条件
`.hermes` の theseus を `.agents/skills/theseus` や `.claude/skills/theseus` に
symlink で共有すると、`.hermes` 版が注入で書き換わった瞬間に全環境へ汚染が伝播する。
運用条件（全て満たすこと）:
- マスター（`.hermes` 版）を `chmod 0444 / 0555` で読み専用化し、書込には `chmod +w` が必要（tripwire）
- ピンファイル `~/.claude/theseus-pin.txt` による HEAD 照合を使用時に必ず実施
- 日次 cron で `git status --porcelain` 非空／HEAD≠ピンを検出し通知
条件を満たさない場合は symlink をやめ、`git archive HEAD` でのデプロイ・コピー方式に戻す。

## 検出の自動化（推奨）
Hermes の `no_agent` cronで、正常時は無音・異常時だけ通知する最小構成を利用できる。
監視スクリプト、初回ピン作成、cron登録、正常系・異常系テストは `cron-setup.md` を参照。
