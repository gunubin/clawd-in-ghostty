# render-demo.py - clawd.glsl をヘッドレスの OpenGL で動かし、README のデモのコマを PNG に書き出す
#   uv run --with moderngl --with pillow --with numpy python tools/render-demo.py shaders/clawd.glsl /tmp/frames 18 20
#   ffmpeg -framerate 20 -i /tmp/frames/f%04d.png -vf "fps=15,scale=880:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" assets/demo.gif
#   tmux の画面は本物ではなく、ステータスバーの目印も含めて Pillow で描いた絵をシェーダーに渡している
import sys, os, math
import numpy as np
import moderngl
from PIL import Image, ImageDraw, ImageFont

SHADER, OUT = sys.argv[1], sys.argv[2]
DURATION = float(sys.argv[3]) if len(sys.argv) > 3 else 18.0
FPS = int(sys.argv[4]) if len(sys.argv) > 4 else 20
os.makedirs(OUT, exist_ok=True)

CW, CH, COLS, ROWS, PAD = 18, 38, 96, 26, 16
W, H = COLS * CW + 2 * PAD, ROWS * CH + 2 * PAD
FONT = ImageFont.truetype(os.environ.get('DEMO_FONT', os.path.expanduser('~/Library/Fonts/FiraCodeNerdFontMono-Regular.ttf')), 28)
BOLD = ImageFont.truetype(os.environ.get('DEMO_FONT_BOLD', os.path.expanduser('~/Library/Fonts/FiraCodeNerdFontMono-Bold.ttf')), 28)

# Catppuccin Mocha
BASE, MANTLE, CRUST = (30, 30, 46), (24, 24, 37), (17, 17, 27)
TEXT, SUB, OVER = (205, 214, 244), (166, 173, 200), (108, 112, 134)
LAV, MAUVE, BLUE, GREEN, PEACH, YELLOW, RED, TEAL, PINK = (180, 190, 254), (203, 166, 247), (137, 180, 250), (166, 227, 161), (250, 179, 135), (249, 226, 175), (243, 139, 168), (148, 226, 213), (245, 194, 231)
SURF = (69, 71, 90)

# pane の配置（マス目。0 行目はステータスバー）
PANES = {
    'A': (0, 1, 47, 12),   # 左上
    'B': (48, 1, 48, 12),  # 右上
    'C': (0, 14, 47, 12),  # 左下
    'D': (48, 14, 48, 12), # 右下（アクティブ）
}
ACTIVE = 'D'
TYPED = "add a dark mode toggle to settings"

def state_at(t):
    """各 pane の Claude の状態コードと、入力中か、git push 直後かを返す"""
    s = {}
    s['A'] = 1 if t < 11 else 4                      # 処理中 → 長引いて料理
    s['B'] = 2 if t < 7 else 1                       # 入力待ち → 処理中
    s['C'] = 1 if t < 2.5 else (3 if t < 6 else 1)   # 処理中 → 完了（紙吹雪）→ 処理中
    s['D'] = 5 if t < 7.5 else 1                     # 待機中に入力 → 処理中に入力（プレゼント）
    typing = t < 12.5
    pushed = 13.0 <= t < 17.0
    return s, typing, pushed

def typed_len(t):
    # 0.4 秒から 1 秒に 6 文字。打ち終わったら 7.5 秒で Enter し、また打ち始める
    if t < 7.5:
        return min(len(TYPED), max(0, int((t - 0.4) * 6)))
    return min(len(TYPED2), max(0, int((t - 7.8) * 6)))
TYPED2 = "also write tests for it"

def cell_color(v):
    return tuple(((v >> s) & 15) * 16 + 8 for s in (8, 4, 0))

def text(d, col, row, s, color, font=FONT):
    d.text((PAD + col * CW, PAD + row * CH + 4), s, font=font, fill=color)

def pane_text(d, name, lines):
    left, top, w, h = PANES[name]
    for i, (s, color) in enumerate(lines):
        if s:
            text(d, left + 1, top + i, s[: w - 2], color)

def frame_image(t):
    states, typing, pushed = state_at(t)
    img = Image.new('RGB', (COLS * CW, ROWS * CH), BASE)
    d = ImageDraw.Draw(img, 'RGB')
    global PAD
    pad, PAD = PAD, 0

    # ステータスバー（上）
    d.rectangle([0, 0, COLS * CW, CH], fill=BASE)
    d.rectangle([0, 0, 16 * CW, CH], fill=LAV)
    text(d, 1, 0, " 1: clawd-demo", CRUST, BOLD)
    text(d, 17, 0, " 2: notes", PINK)
    text(d, COLS - 21 - 8, 0, "󰅐 20:14", BLUE)

    # pane の枠
    for name, (l, tp, w, h) in PANES.items():
        if l > 0:
            for r in range(tp, tp + h):
                text(d, l - 1, r, "│", LAV if name == ACTIVE else SURF)
        if tp > 1:
            for c in range(l, l + w):
                text(d, c, tp - 1, "─", LAV if name == ACTIVE else SURF)

    blank = [("", TEXT)] * 4
    # 左上: 処理中
    pane_text(d, 'A', blank + [
        ("> refactor the auth middleware", SUB),
        ("", TEXT),
        ("● Read src/auth/middleware.ts", TEXT),
        ("● Update src/auth/session.ts", TEXT),
        ("  └ +42 -17", GREEN),
        ("", TEXT),
        ("* Simmering… (esc to interrupt)" if states['A'] == 4 else "* Refactoring… (esc to interrupt)", PEACH),
    ])
    # 右上: 入力待ち → 処理中
    if states['B'] == 2:
        pane_text(d, 'B', blank + [
            ("> bump the deps and run the tests", SUB),
            ("", TEXT),
            ("Bash: pnpm test", TEXT),
            ("Do you want to proceed?", YELLOW),
            ("❯ 1. Yes", BLUE),
            ("  2. No, and tell Claude what to do", SUB),
        ])
    else:
        pane_text(d, 'B', blank + [
            ("> bump the deps and run the tests", SUB),
            ("", TEXT),
            ("● Bash(pnpm test)", TEXT),
            ("  └ 128 passed", GREEN),
            ("", TEXT),
            ("* Updating lockfile… (esc to interrupt)", PEACH),
        ])
    # 左下: 処理中 → 完了 → 処理中
    if states['C'] == 3 or (6 <= t < 7):
        pane_text(d, 'C', blank + [
            ("> fix the flaky upload test", SUB),
            ("", TEXT),
            ("● The test raced the file watcher.", TEXT),
            ("  Added an explicit await. 3/3 green.", TEXT),
            ("", TEXT),
            ("> ", TEXT),
        ])
    else:
        pane_text(d, 'C', blank + [
            ("> fix the flaky upload test" if t < 6 else "> now the download test too", SUB),
            ("", TEXT),
            ("● Read tests/upload.test.ts" if t < 6 else "● Read tests/download.test.ts", TEXT),
            ("", TEXT),
            ("* Investigating… (esc to interrupt)", PEACH),
        ])
    # 右下: アクティブ。入力中
    n = typed_len(t)
    if t < 7.5:
        lines = blank + [
            ("● Ready.", TEXT), ("", TEXT),
            ("> " + TYPED[:n], TEXT),
        ]
        cursor = (PANES['D'][0] + 1 + 2 + n, PANES["D"][1] + 6)
    else:
        lines = blank + [
            ("> " + TYPED, SUB), ("", TEXT),
            ("* Adding dark mode… (esc to interrupt)", PEACH), ("", TEXT),
            ("> " + TYPED2[:n], TEXT),
        ]
        cursor = (PANES['D'][0] + 1 + 2 + n, PANES["D"][1] + 8)
    if t >= 13.0:
        lines = blank + [
            ("> " + TYPED, SUB), ("", TEXT),
            ("● Bash(git push)", TEXT),
            ("  └ main -> main", GREEN), ("", TEXT),
            ("* Wrapping up… (esc to interrupt)", PEACH),
        ]
        cursor = (PANES['D'][0] + 1, PANES['D'][1] + 11)
    pane_text(d, 'D', lines)
    cx, cy = cursor
    d.rectangle([cx * CW, cy * CH + 4, cx * CW + CW - 1, cy * CH + CH - 4], fill=TEXT)

    # ステータスバー右端の目印 21 マス（pane-marker.sh と同じ詰め方）
    l, tp, w, h = PANES[ACTIVE]
    flags = 0
    claude = 16 if pushed else 0
    order = ['A', 'B', 'C', 'D']
    slots = [(PANES[n][0], PANES[n][1], states[n]) for n in order if states[n] > 0][:4]
    slots += [(0, 0, 0)] * (4 - len(slots))
    cells = []
    for pl, pt, code in reversed(slots):
        cells += [cell_color(pt + code * 512), cell_color(pl)]
    cells += [cell_color(claude), cell_color(flags), LAV, cell_color(0), cell_color(0), cell_color(2730),
              cell_color(h), cell_color(w), cell_color(tp), cell_color(l), cell_color(ROWS), cell_color(COLS),
              cell_color(CW * 64 + CH)]
    x0 = (COLS - len(cells)) * CW
    for i, c in enumerate(cells):
        d.rectangle([x0 + i * CW, 0, x0 + (i + 1) * CW - 1, CH - 1], fill=c)

    PAD = pad
    # 余白は端のマスの色を伸ばす（Ghostty の window-padding-color = extend と同じ）
    arr = np.pad(np.asarray(img), ((PAD, PAD), (PAD, PAD), (0, 0)), mode='edge')
    cursor_px = (PAD + cx * CW, PAD + cy * CH, CW, CH)
    return arr, cursor_px, typing, n

# Ghostty はシェーダーに Display P3 の色で渡す。sRGB の絵を P3 にして渡し、出てきた色を sRGB に戻す
M = np.array([[1.2249401, -0.2249404, 0.0], [-0.0420569, 1.0420571, 0.0], [-0.0196376, -0.0786361, 1.0982735]])
def to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
def srgb_to_p3(a):
    return np.clip(np.round(to_srgb(to_lin(a / 255.0) @ np.linalg.inv(M).T) * 255), 0, 255).astype(np.uint8)
def p3_to_srgb(a):
    return np.clip(np.round(to_srgb(to_lin(a / 255.0) @ M.T) * 255), 0, 255).astype(np.uint8)

ctx = moderngl.create_standalone_context(require=330)
header = '''#version 330 core
uniform sampler2D iChannel0;
uniform vec3 iResolution;
uniform float iTime;
uniform float iTimeDelta;
uniform int iFrame;
uniform vec4 iMouse;
uniform vec4 iCurrentCursor;
uniform vec4 iPreviousCursor;
uniform vec4 iCurrentCursorColor;
uniform vec4 iPreviousCursorColor;
uniform float iTimeCursorChange;
'''
footer = '''
out vec4 outColor;
void main() {
    vec4 c;
    mainImage(c, vec2(gl_FragCoord.x, iResolution.y - gl_FragCoord.y));
    outColor = vec4(c.rgb, 1.0);
}
'''
prog = ctx.program(
    vertex_shader='#version 330 core\nin vec2 pos; void main(){ gl_Position = vec4(pos, 0.0, 1.0); }',
    fragment_shader=header + open(SHADER).read() + footer)
vbo = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype='f4').tobytes())
vao = ctx.simple_vertex_array(prog, vbo, 'pos')
fbo = ctx.simple_framebuffer((W, H), components=4)
fbo.use()
tex = ctx.texture((W, H), 3)
tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
tex.repeat_x = tex.repeat_y = False

def set_u(name, value):
    if name in prog:
        prog[name].value = value

set_u('iResolution', (W, H, 1.0))
last_cursor, cursor_change, prev_cursor = None, 0.0, (0, 0, CW, CH)
frames = int(DURATION * FPS)
for i in range(frames):
    t = i / FPS
    arr, cur, typing, n = frame_image(t)
    if cur != last_cursor:
        if last_cursor is not None:
            prev_cursor = last_cursor
        cursor_change = t
        last_cursor = cur
    tex.write(np.ascontiguousarray(srgb_to_p3(arr)).tobytes())
    tex.use(0)
    set_u('iChannel0', 0)
    # シェーダーの時刻は少し進めておく（起動直後の特別扱いを避ける）
    set_u('iTime', t + 100.0)
    set_u('iTimeDelta', 1.0 / FPS)
    set_u('iFrame', i)
    set_u('iCurrentCursor', tuple(float(v) for v in cur))
    set_u('iPreviousCursor', tuple(float(v) for v in prev_cursor))
    set_u('iCurrentCursorColor', (0.8, 0.84, 0.96, 1.0))
    set_u('iPreviousCursorColor', (0.8, 0.84, 0.96, 1.0))
    set_u('iTimeCursorChange', cursor_change + 100.0)
    fbo.clear(0, 0, 0, 1)
    vao.render(moderngl.TRIANGLE_STRIP)
    data = np.frombuffer(fbo.read(components=3), dtype=np.uint8).reshape(H, W, 3)[::-1]
    Image.fromarray(p3_to_srgb(data)).save(os.path.join(OUT, f'f{i:04d}.png'))
print(f'{frames} frames, {W}x{H}')
