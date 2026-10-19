# clawd-in-ghostty

Clawd, the Claude Code mascot, lives in the corner of every tmux pane where Claude is working.
A single Ghostty shader that makes tmux feel alive while you work with Claude Code.

<!-- TODO: demo GIF -->

## What it does

**Clawd in your panes**

- While Claude is working, Clawd walks, hops, waves and plays the official startup animations in the pane's top-left corner. Up to four panes at once.
- When Claude needs your permission or an answer, Clawd jumps with a `!`.
- When Claude finishes, Clawd celebrates with confetti.
- If a task runs over a minute, Clawd starts stirring a cooking pot.
- Very rarely, Clawd grows legs and turns into something else for a few seconds.

**You, as a little developer**

- Type in a pane where Claude is idle and a hoodie-wearing developer appears: running, sipping coffee, listening to music, typing on a laptop.
- Type while Claude is working and the developer tosses presents to Clawd, who catches them.

**tmux, but nicer**

- Inactive panes are blurred and dimmed, and the active pane casts a soft shadow.
- tmux popups get a modal-style backdrop, a shadow and a glowing edge.
- The screen edge glows while the prefix key is pressed, in copy mode, and while a pane is zoomed.
- The pane edge glows red when the last command failed.
- Fireworks go off after a successful `git push`.

## How it works

A Ghostty shader only sees pixels. It cannot ask tmux where the panes are.
So tmux paints that information as 21 colored cells at the right end of the status bar, and the shader reads them back and hides them.

```
Claude Code hooks ──> ~/.claude/pane-state.json
                              │
tmux status-right ──> scripts/pane-marker.sh ──> 21 colored cells
                                                       │
Ghostty ──> shaders/clawd.glsl reads the cells ──> draws everything
```

## Requirements

- macOS or Linux with [Ghostty](https://ghostty.org) 1.1 or later
- tmux 3.4 or later, with the status bar at the **top**
- [Claude Code](https://claude.com/claude-code)
- `jq`
- fish or zsh, only for the failed-command glow and the fireworks

## Install

```sh
git clone https://github.com/gunubin/clawd-in-ghostty.git
cd clawd-in-ghostty
./install.sh
```

`install.sh` links the repository to `~/.config/clawd-in-ghostty` and prints the remaining steps. It does not edit your config files.

1. **Ghostty.** Add to `~/.config/ghostty/config` and reload.

   ```
   custom-shader = ~/.config/clawd-in-ghostty/shaders/clawd.glsl
   custom-shader-animation = true
   ```

2. **tmux.** Add to the end of `~/.tmux.conf` and reload.

   ```
   source-file ~/.config/clawd-in-ghostty/tmux/clawd.tmux
   ```

   This moves the status bar to the top and appends the marker cells to `status-right`.

3. **Claude Code.** Merge the hooks in `claude/settings.example.json` into `~/.claude/settings.json`.

4. **Shell, optional.**

   ```sh
   # fish
   ln -s ~/.config/clawd-in-ghostty/shell/clawd.fish ~/.config/fish/conf.d/
   # zsh
   echo 'source ~/.config/clawd-in-ghostty/shell/clawd.zsh' >> ~/.zshrc
   ```

## Customize

- **Glow color.** Set `@clawd_color` in tmux. If you already set `@tab_color` per window, that is used instead.
- **Timing and sizes.** Constants at the top of `shaders/clawd.glsl`, such as `MASCOT_ACTION` and `DEV_ACTION`, control how often the characters change moves.
- **State file.** Set `CLAWD_STATE_FILE` to keep Claude's pane state somewhere other than `~/.claude/pane-state.json`.

## Troubleshooting

- **Nothing happens.** Make sure the status bar is at the top and `status-right` ends with the marker. A row of odd colored cells at the top right means tmux works but the shader is not loaded.
- **Clawd never appears.** Check that `~/.claude/pane-state.json` changes while Claude is working. If not, the hooks are not set up.
- **Colors look off on another display.** The marker survives small color shifts, but a custom color profile in Ghostty may break it.

## Credits

Clawd and the startup animations are from Claude Code by Anthropic. This is an unofficial fan project and is not affiliated with or endorsed by Anthropic. Claude and Clawd are trademarks of Anthropic.

The hoodie developer, the effects and the code are original and released under the MIT License.
