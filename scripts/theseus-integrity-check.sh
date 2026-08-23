#!/usr/bin/env bash
# Theseus Skill のGit状態と外部ピンを確認する。
# 正常時は何も出力せず、異常時だけcron通知用メッセージを出す。

set -u

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
THESEUS_REPO="${THESEUS_REPO:-$HERMES_HOME/skills/security/theseus}"
THESEUS_PIN="${THESEUS_PIN:-$HOME/.claude/theseus-pin.txt}"

issues=()

if ! command -v git >/dev/null 2>&1; then
  issues+=("git コマンドが見つかりません")
elif [ ! -d "$THESEUS_REPO/.git" ]; then
  issues+=("Theseus がGit管理されていません: $THESEUS_REPO")
else
  status="$(git -C "$THESEUS_REPO" status --porcelain 2>&1)"
  status_rc=$?
  if [ "$status_rc" -ne 0 ]; then
    issues+=("Git状態を取得できません: $status")
  elif [ -n "$status" ]; then
    issues+=("Theseus に未コミット変更があります: $status")
  fi

  head="$(git -C "$THESEUS_REPO" rev-parse HEAD 2>&1)"
  head_rc=$?
  if [ "$head_rc" -ne 0 ]; then
    issues+=("Theseus のHEADを取得できません: $head")
  elif [ ! -f "$THESEUS_PIN" ]; then
    issues+=("外部ピンがありません: $THESEUS_PIN")
  else
    pin="$(tr -d '\r\n' < "$THESEUS_PIN")"
    if [ -z "$pin" ]; then
      issues+=("外部ピンが空です: $THESEUS_PIN")
    elif [ "$head" != "$pin" ]; then
      issues+=("Theseus のHEADと外部ピンが一致しません: HEAD=$head PIN=$pin")
    fi
  fi
fi

if [ "${#issues[@]}" -gt 0 ]; then
  printf '【Theseus整合性アラート】\n'
  printf -- '- %s\n' "${issues[@]}"
fi
