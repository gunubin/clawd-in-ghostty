#!/bin/sh
# install.sh - このリポジトリを ~/.config/clawd-in-ghostty にリンクし、残りの手順を表示する
#   既存の設定ファイルは書き換えない
set -e
here=$(cd "$(dirname "$0")" && pwd)
dest="$HOME/.config/clawd-in-ghostty"
if [ -e "$dest" ] && [ "$(readlink "$dest")" != "$here" ]; then
    echo "$dest already exists and points elsewhere. Remove it first." >&2
    exit 1
fi
mkdir -p "$HOME/.config"
ln -sfn "$here" "$dest"
for cmd in tmux jq; do
    command -v "$cmd" >/dev/null || echo "warning: $cmd is not installed" >&2
done
cat <<MSG
Linked $dest -> $here

Next steps:
  1. Ghostty: add to ~/.config/ghostty/config
       custom-shader = $dest/shaders/clawd.glsl
       custom-shader-animation = true
  2. tmux: add to the end of ~/.tmux.conf, then reload
       source-file $dest/tmux/clawd.tmux
  3. Claude Code: merge the hooks in $dest/claude/settings.example.json
     into ~/.claude/settings.json
  4. Optional (failed-command glow and git push fireworks):
       fish: ln -s $dest/shell/clawd.fish ~/.config/fish/conf.d/
       zsh:  echo 'source $dest/shell/clawd.zsh' >> ~/.zshrc
MSG
