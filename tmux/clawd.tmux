# clawd.tmux - clawd-in-ghostty の tmux 設定。~/.tmux.conf の最後で source する
#   source-file ~/.config/clawd-in-ghostty/tmux/clawd.tmux
#
# シェーダーは画面の一番上の行の右端から目印を読むので、ステータスバーは上に置く
set -g status-position top
# 目印（21 マス）を毎秒描き直す
set -g status-interval 1
set -g status-right-length 150

# 縁の光や popup の光に使う色。@tab_color があればそれを、なければラベンダーを使う
set -gq @clawd_color "#b4befe"

# ステータスバーの右端に、アクティブな pane・popup・モード・Claude の pane の位置を色のマスにして出す
set -ga status-right "#(~/.config/clawd-in-ghostty/scripts/pane-marker.sh #{client_cell_width} #{client_cell_height} #{client_width} #{client_height} #{pane_left} #{e|+:#{pane_top},1} #{pane_width} #{pane_height} '#{S:#{?#{&&:#{m:popup/*,#{session_name}},#{session_attached}},#{e|+:#{window_width},2},}}' '#{S:#{?#{&&:#{m:popup/*,#{session_name}},#{session_attached}},#{e|+:#{window_height},2},}}' '#{?@tab_color,#{E:@tab_color},#{@clawd_color}}' #{client_prefix} #{pane_in_mode} #{window_zoomed_flag} '#{@cmd_failed}' '#{@git_push_at}' #{window_id})"

# popup を開閉したら、すぐステータスバーを描き直す（popup の大きさをすぐ反映する）
set-hook -g client-attached[90] 'run-shell -b "tmux list-clients -F \"##{client_name}\" | while read -r c; do tmux refresh-client -S -t \"\$c\"; done"'
set-hook -g client-detached[90] 'run-shell -b "tmux list-clients -F \"##{client_name}\" | while read -r c; do tmux refresh-client -S -t \"\$c\"; done"'
