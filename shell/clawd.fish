# clawd.fish - コマンドが失敗したら pane に印（@cmd_failed）を付け、git push が成功したら時刻（@git_push_at）を残す
#   シェーダーが、印の付いた pane の縁を赤く光らせ、push の直後に花火を上げる
#   ~/.config/fish/conf.d/ にリンクするか、config.fish から source する
status is-interactive; or return

function __clawd_clear --on-event fish_preexec
    test -n "$TMUX"; or return
    tmux set-option -p -u -t $TMUX_PANE @cmd_failed 2>/dev/null
end

function __clawd_mark --on-event fish_postexec
    set -l code $status
    test -n "$TMUX"; or return
    if test $code -ne 0
        tmux set-option -p -t $TMUX_PANE @cmd_failed 1 2>/dev/null
        tmux refresh-client -S 2>/dev/null
    else if string match -qr '^\s*git\s+push\b' -- $argv[1]
        tmux set-option -g @git_push_at (date +%s) 2>/dev/null
        tmux refresh-client -S 2>/dev/null
    end
end
