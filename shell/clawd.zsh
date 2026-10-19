# clawd.zsh - コマンドが失敗したら pane に印（@cmd_failed）を付け、git push が成功したら時刻（@git_push_at）を残す
#   シェーダーが、印の付いた pane の縁を赤く光らせ、push の直後に花火を上げる
#   ~/.zshrc から source する
[[ -o interactive ]] || return
autoload -Uz add-zsh-hook

__clawd_preexec() {
    __clawd_cmd=$1
    [[ -n $TMUX ]] && tmux set-option -p -u -t "$TMUX_PANE" @cmd_failed 2>/dev/null
}

__clawd_precmd() {
    local code=$?
    [[ -n $TMUX && -n $__clawd_cmd ]] || return
    if (( code != 0 )); then
        tmux set-option -p -t "$TMUX_PANE" @cmd_failed 1 2>/dev/null
        tmux refresh-client -S 2>/dev/null
    elif [[ $__clawd_cmd =~ '^[[:space:]]*git[[:space:]]+push([[:space:]]|$)' ]]; then
        tmux set-option -g @git_push_at "$(date +%s)" 2>/dev/null
        tmux refresh-client -S 2>/dev/null
    fi
    __clawd_cmd=
}

add-zsh-hook preexec __clawd_preexec
add-zsh-hook precmd __clawd_precmd
