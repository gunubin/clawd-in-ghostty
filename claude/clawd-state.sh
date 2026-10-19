#!/bin/bash
# clawd-state.sh - Claude Code の hook。pane ごとの Claude の状態を JSON に記録する
#   scripts/pane-marker.sh がこのファイルを読み、シェーダーに Claude の pane の位置と状態を渡す
#   記録先は CLAWD_STATE_FILE（既定は ~/.claude/pane-state.json）
#
# 1 pane 1 行: { "%12": { "status": "working|waiting|done|idle", "ts": <最後に変わった時刻>, "since": <処理を始めた時刻> } }

[ -z "$TMUX" ] && exit 0
PANE_ID="$TMUX_PANE"
[[ "$PANE_ID" =~ ^%[0-9]+$ ]] || exit 0
command -v jq >/dev/null || exit 0

STATE_FILE="${CLAWD_STATE_FILE:-$HOME/.claude/pane-state.json}"
LOCK_DIR="$STATE_FILE.lock"
event=$(jq -r '.hook_event_name // ""' 2>/dev/null)

# mkdir を使ったロック（macOS の flock がなくても動く）
acquire_lock() {
    local i=0
    while ! mkdir "$LOCK_DIR" 2>/dev/null; do
        i=$((i + 1))
        [ $i -ge 20 ] && return 1
        sleep 0.1
    done
}
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT

# 状態ファイルに jq の式を当てて、置き換える
update() {
    mkdir -p "$(dirname "$STATE_FILE")"
    [ -f "$STATE_FILE" ] || echo '{}' > "$STATE_FILE"
    acquire_lock || return
    local tmp="$STATE_FILE.tmp.$$"
    if jq "$@" "$STATE_FILE" > "$tmp" 2>/dev/null; then
        mv "$tmp" "$STATE_FILE"
    else
        rm -f "$tmp"
    fi
}

case "$event" in
    SessionStart)
        # もうない pane の記録を消してから、この pane を待機中にする
        active=$(tmux list-panes -a -F '#{pane_id}' 2>/dev/null | tr '\n' ' ')
        update --arg id "$PANE_ID" --arg active "$active" '
            ($active | split(" ") | map(select(length > 0))) as $valid
            | with_entries(select(.key | IN($valid[])))
            | .[$id] = {"status": "idle", "ts": (now | floor)}'
        ;;
    UserPromptSubmit)
        update --arg id "$PANE_ID" '.[$id] = {"status": "working", "ts": (now | floor), "since": (now | floor)}'
        ;;
    PreToolUse | PostToolUse | Notification | Stop)
        case "$event" in
            Notification) status=waiting ;;  # settings.json の matcher で、許可と質問のときだけ呼ぶ
            Stop) status=done ;;
            *) status=working ;;
        esac
        update --arg id "$PANE_ID" --arg status "$status" \
            'if .[$id] then .[$id].status = $status | .[$id].ts = (now | floor) else . end'
        ;;
    SessionEnd)
        update --arg id "$PANE_ID" 'del(.[$id])'
        ;;
esac
exit 0
