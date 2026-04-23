"""
OLED Animation - Be My Baby
Python/Pygame version of the HTML OLED simulator.
Run: python oled_animation.py
"""

import pygame
import math
import random
import sys

# ── Constants ────────────────────────────────────────────────────────────────
OLED_W, OLED_H = 128, 64
SCALE = 6                        # each OLED pixel → 6×6 screen pixels (enlarged)
FPS = 60

WIN_W, WIN_H = 900, 600          # fixed windowed size (not fullscreen)

# Colors
BG         = (10, 10, 10)
PCB        = (26, 26, 26)
PCB_BORDER = (51, 51, 51)
SCREEN_BG  = (0, 0, 0)
OLED_BG    = (184, 212, 232)    # bluish-white glow
OLED_PIX   = (10, 21, 32)       # dark pixel color
PIN_COL    = (102, 102, 102)
TEXT_COL   = (68, 68, 68)
TEXT_SONG  = (102, 102, 102)

SLIDE_FRAMES = 20               # frames to complete a lyric slide transition

INTRO_DURATION = 480            # ~8 seconds at 60 fps

# Face positions
FACE_CX_INTRO, FACE_CY_INTRO = 26, 34   # face during intro (left side)
FACE_CX, FACE_CY = 26, 34               # face during lyrics phase

# ── Pixel buffer ─────────────────────────────────────────────────────────────
buf = [[0] * OLED_W for _ in range(OLED_H)]

def clear_buf():
    for y in range(OLED_H):
        for x in range(OLED_W):
            buf[y][x] = 0

def set_pixel(x, y, v=1):
    if 0 <= x < OLED_W and 0 <= y < OLED_H:
        buf[y][x] = v

# ── Pixel font (5×7) ─────────────────────────────────────────────────────────
FONT = {
    ' ': [0,0,0,0,0,0,0],
    'a': [0b01110,0b10001,0b11111,0b10001,0b10001,0,0],
    'b': [0b11110,0b10001,0b11110,0b10001,0b11110,0,0],
    'c': [0b01110,0b10001,0b10000,0b10001,0b01110,0,0],
    'd': [0b11110,0b10001,0b10001,0b10001,0b11110,0,0],
    'e': [0b11111,0b10000,0b11110,0b10000,0b11111,0,0],
    'f': [0b11111,0b10000,0b11110,0b10000,0b10000,0,0],
    'g': [0b01111,0b10000,0b10111,0b10001,0b01111,0,0],
    'h': [0b10001,0b10001,0b11111,0b10001,0b10001,0,0],
    'i': [0b11100,0b00100,0b00100,0b00100,0b11100,0,0],
    'j': [0b00001,0b00001,0b00001,0b10001,0b01110,0,0],
    'k': [0b10001,0b10010,0b11100,0b10010,0b10001,0,0],
    'l': [0b10000,0b10000,0b10000,0b10000,0b11111,0,0],
    'm': [0b10001,0b11011,0b10101,0b10001,0b10001,0,0],
    'n': [0b10001,0b11001,0b10101,0b10011,0b10001,0,0],
    'o': [0b01110,0b10001,0b10001,0b10001,0b01110,0,0],
    'p': [0b11110,0b10001,0b11110,0b10000,0b10000,0,0],
    'q': [0b01110,0b10001,0b10101,0b10010,0b01101,0,0],
    'r': [0b11110,0b10001,0b11110,0b10010,0b10001,0,0],
    's': [0b01111,0b10000,0b01110,0b00001,0b11110,0,0],
    't': [0b11111,0b00100,0b00100,0b00100,0b00100,0,0],
    'u': [0b10001,0b10001,0b10001,0b10001,0b01110,0,0],
    'v': [0b10001,0b10001,0b10001,0b01010,0b00100,0,0],
    'w': [0b10001,0b10001,0b10101,0b11011,0b10001,0,0],
    'x': [0b10001,0b01010,0b00100,0b01010,0b10001,0,0],
    'y': [0b10001,0b01010,0b00100,0b00100,0b00100,0,0],
    'z': [0b11111,0b00010,0b00100,0b01000,0b11111,0,0],
    '&': [0b01100,0b10010,0b01100,0b10010,0b01101,0,0],
    '!': [0b00100,0b00100,0b00100,0b00000,0b00100,0,0],
    "'": [0b00100,0b00100,0b00000,0b00000,0b00000,0,0],  # apostrophe
    '(': [0b00110,0b01000,0b01000,0b01000,0b00110,0,0],  # left paren
    ')': [0b01100,0b00010,0b00010,0b00010,0b01100,0,0],  # right paren
}

def draw_char(ch, ox, oy):
    g = FONT.get(ch.lower(), FONT[' '])
    for row in range(7):
        bits = g[row] if row < len(g) else 0
        for col in range(5):
            if bits & (1 << (4 - col)):
                set_pixel(ox + col, oy + row)

def text_width(text):
    """Return pixel width of a string (each char = 6px including gap)."""
    return len(text) * 6 - 1  # last char has no trailing gap

def draw_text(text, x, y):
    cx = x
    for ch in text:
        draw_char(ch, cx, y)
        cx += 6

# ── Text word-wrap for the OLED text zone (x > 54, width ~70px) ──────────────
TEXT_ZONE_X   = 55   # where text starts
TEXT_ZONE_W   = OLED_W - TEXT_ZONE_X - 2   # ~71 pixels wide
CHARS_PER_ROW = TEXT_ZONE_W // 6           # ~11 chars

def wrap_lyric(text):
    """Wrap a lyric string into lines fitting the text zone width."""
    words = text.split()
    lines = []
    current = ''
    for word in words:
        candidate = (current + ' ' + word).strip()
        if len(candidate) * 6 <= TEXT_ZONE_W:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

# ── Drawing helpers ───────────────────────────────────────────────────────────
def draw_circle(cx, cy, r):
    for angle in range(360):
        rad = math.radians(angle)
        x = round(cx + r * math.cos(rad))
        y = round(cy + r * math.sin(rad))
        set_pixel(x, y)

def fill_circle(cx, cy, r):
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            if dx*dx + dy*dy <= r*r:
                set_pixel(cx+dx, cy+dy)

def draw_line(x0, y0, x1, y1):
    dx = abs(x1-x0); dy = abs(y1-y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        set_pixel(x0, y0)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x0 += sx
        if e2 <  dx: err += dx; y0 += sy

# ── Pookie face ───────────────────────────────────────────────────────────────
def draw_face(cx, cy, eye_state, mouth_curve):
    draw_circle(cx, cy, 19)
    draw_circle(cx, cy, 18)

    eye_y  = cy - 5
    eye_lx = cx - 7
    eye_rx = cx + 7
    mouth_y = cy + 7

    # EYES
    if eye_state == 'blink':
        # closed eyes for blink transition
        for dx in range(-3, 4):
            set_pixel(eye_lx + dx, eye_y)
            set_pixel(eye_rx + dx, eye_y)

    elif eye_state == 'open':
        fill_circle(eye_lx, eye_y, 3)
        fill_circle(eye_rx, eye_y, 3)
        set_pixel(eye_lx+1, eye_y-1, 0)
        set_pixel(eye_rx+1, eye_y-1, 0)

    elif eye_state == 'uwu':
        for dx in range(-3, 4):
            dy = round(dx*dx*0.18)
            set_pixel(eye_lx+dx, eye_y+dy)
            set_pixel(eye_rx+dx, eye_y+dy)
        for dx in range(-2, 3):
            dy = round(dx*dx*0.18)
            set_pixel(eye_lx+dx, eye_y+dy+1)
            set_pixel(eye_rx+dx, eye_y+dy+1)

    elif eye_state == 'heart':
        def draw_heart(hx, hy):
            set_pixel(hx-1,hy-1); set_pixel(hx,hy-1)
            set_pixel(hx-2,hy);   set_pixel(hx-1,hy)
            set_pixel(hx,hy);     set_pixel(hx+1,hy)
            set_pixel(hx-1,hy+1); set_pixel(hx,hy+1)
            set_pixel(hx,hy+2)
        draw_heart(eye_lx, eye_y-1)
        draw_heart(eye_rx, eye_y-1)

    elif eye_state == 'wink':
        fill_circle(eye_rx, eye_y, 3)
        set_pixel(eye_rx+1, eye_y-1, 0)
        draw_line(eye_lx-2, eye_y+1, eye_lx+2, eye_y-1)
        draw_line(eye_lx-2, eye_y+2, eye_lx+2, eye_y)

    elif eye_state == 'sparkle':
        def draw_star(sx, sy):
            for d in range(1, 3):
                set_pixel(sx, sy-d); set_pixel(sx, sy+d)
                set_pixel(sx-d, sy); set_pixel(sx+d, sy)
            set_pixel(sx-1,sy-1); set_pixel(sx+1,sy-1)
            set_pixel(sx-1,sy+1); set_pixel(sx+1,sy+1)
        draw_star(eye_lx, eye_y)
        draw_star(eye_rx, eye_y)

    elif eye_state == 'teary':
        fill_circle(eye_lx, eye_y, 3)
        fill_circle(eye_rx, eye_y, 3)
        set_pixel(eye_lx+1, eye_y-1, 0)
        set_pixel(eye_rx+1, eye_y-1, 0)
        set_pixel(eye_lx-2, eye_y+4)
        set_pixel(eye_lx-2, eye_y+5)
        set_pixel(eye_rx+2, eye_y+4)
        set_pixel(eye_rx+2, eye_y+5)

    elif eye_state == 'dizzy':
        draw_line(eye_lx-2, eye_y-2, eye_lx+2, eye_y+2)
        draw_line(eye_lx+2, eye_y-2, eye_lx-2, eye_y+2)
        draw_line(eye_rx-2, eye_y-2, eye_rx+2, eye_y+2)
        draw_line(eye_rx+2, eye_y-2, eye_rx-2, eye_y+2)

    else:
        fill_circle(eye_lx, eye_y, 2)
        fill_circle(eye_rx, eye_y, 2)

    # MOUTH (skip mouth during blink so face stays cute)
    if eye_state == 'blink':
        mouth_curve = 'smile'

    if mouth_curve == 'bigsmile':
        for dx in range(-6, 7):
            dy = round(dx*dx*0.1)
            set_pixel(cx+dx, mouth_y+dy)
            set_pixel(cx+dx, mouth_y+dy+1)

    elif mouth_curve == 'smile':
        for dx in range(-5, 6):
            dy = round(dx*dx*0.08)
            set_pixel(cx+dx, mouth_y+dy)

    elif mouth_curve == 'neutral':
        for dx in range(-4, 5):
            set_pixel(cx+dx, mouth_y)

    elif mouth_curve == 'open':
        for dx in range(-4, 5):
            set_pixel(cx+dx, mouth_y)
            set_pixel(cx+dx, mouth_y+3)
        for dy in range(4):
            set_pixel(cx-4, mouth_y+dy)
            set_pixel(cx+4, mouth_y+dy)

    elif mouth_curve == 'kiss':
        fill_circle(cx, mouth_y+1, 2)
        set_pixel(cx, mouth_y-1)

    elif mouth_curve == 'cat':
        draw_line(cx-4, mouth_y+1, cx-2, mouth_y)
        draw_line(cx-2, mouth_y,   cx,   mouth_y+2)
        draw_line(cx,   mouth_y+2, cx+2, mouth_y)
        draw_line(cx+2, mouth_y,   cx+4, mouth_y+1)

    elif mouth_curve == 'singing':
        for dx in range(-3, 4):
            set_pixel(cx+dx, mouth_y)
            set_pixel(cx+dx, mouth_y+4)
        for dy in range(1, 4):
            set_pixel(cx-3, mouth_y+dy)
            set_pixel(cx+3, mouth_y+dy)

    # Rosy cheeks
    set_pixel(cx-13, cy+2); set_pixel(cx-14, cy+2); set_pixel(cx-13, cy+3)
    set_pixel(cx+13, cy+2); set_pixel(cx+14, cy+2); set_pixel(cx+13, cy+3)

# ── Music note (♪) drawn with set_pixel ──────────────────────────────────────
def draw_music_note(nx, ny, size=1):
    """Draw a ♪ music note centered at (nx, ny) using pixels."""
    # Note head (filled oval approximation)
    for dy in range(-2, 3):
        for dx in range(-3, 4):
            if dx*dx*0.25 + dy*dy*0.7 <= 4:
                set_pixel(nx + dx, ny + dy)
    # Stem (vertical line going up from right side of head)
    stem_x = nx + 3
    for sy in range(-10, 0):
        set_pixel(stem_x, ny + sy)
    # Flag (two curved lines at top of stem)
    set_pixel(stem_x,   ny - 10)
    set_pixel(stem_x+1, ny - 9)
    set_pixel(stem_x+2, ny - 8)
    set_pixel(stem_x+3, ny - 7)
    set_pixel(stem_x+3, ny - 6)
    set_pixel(stem_x,   ny - 8)
    set_pixel(stem_x+1, ny - 7)
    set_pixel(stem_x+2, ny - 6)
    set_pixel(stem_x+3, ny - 5)
    set_pixel(stem_x+3, ny - 4)

def draw_double_note(nx, ny):
    """Draw ♫ — two eighth notes beamed together."""
    # Left note head
    head1_x, head1_y = nx - 5, ny + 2
    for dy in range(-2, 3):
        for dx in range(-3, 4):
            if dx*dx*0.25 + dy*dy*0.7 <= 4:
                set_pixel(head1_x + dx, head1_y + dy)
    # Right note head
    head2_x, head2_y = nx + 8, ny + 4
    for dy in range(-2, 3):
        for dx in range(-3, 4):
            if dx*dx*0.25 + dy*dy*0.7 <= 4:
                set_pixel(head2_x + dx, head2_y + dy)
    # Left stem
    for sy in range(-10, 0):
        set_pixel(head1_x + 3, head1_y + sy)
    # Right stem
    for sy in range(-8, 0):
        set_pixel(head2_x + 3, head2_y + sy)
    # Beam connecting tops
    beam_y1 = head1_y - 10
    beam_y2 = head2_y - 8
    for bx in range(0, head2_x - head1_x + 4):
        t = bx / (head2_x - head1_x + 3)
        by = round(beam_y1 + t * (beam_y2 - beam_y1))
        set_pixel(head1_x + 3 + bx, by)
        set_pixel(head1_x + 3 + bx, by + 1)

# ── Tiny heart shape (3×3) for background hearts ─────────────────────────────
def draw_tiny_heart(hx, hy):
    set_pixel(hx-1, hy);  set_pixel(hx+1, hy)
    set_pixel(hx-1, hy+1); set_pixel(hx, hy+1); set_pixel(hx+1, hy+1)
    set_pixel(hx,   hy+2)

# ── Background animation state ────────────────────────────────────────────────
# Hearts: each = [x (float), y (float), wobble_phase]
NUM_HEARTS = 5
hearts = []

def init_hearts():
    global hearts
    hearts = []
    for _ in range(NUM_HEARTS):
        x = random.randint(50, OLED_W - 5)   # right half only (avoid face)
        y = random.randint(0, OLED_H - 1)
        phase = random.uniform(0, math.pi * 2)
        hearts.append([float(x), float(y), phase])

# Stars: each = [x, y, timer, period, on]
NUM_STARS = 8

def make_star():
    x = random.randint(50, OLED_W - 3)
    y = random.randint(3, OLED_H - 3)
    period = random.randint(20, 60)
    timer = random.randint(0, period)
    on = random.choice([True, False])
    return [x, y, timer, period, on]

stars = []

def init_stars():
    global stars
    stars = [make_star() for _ in range(NUM_STARS)]

def init_bg():
    init_hearts()
    init_stars()

def draw_background(tick):
    """Draw floating hearts, twinkling stars, heartbeat dot — before face/text."""
    global hearts

    # ── Floating hearts ──────────────────────────────────────────────────────
    for h in hearts:
        h[1] -= 0.25       # drift upward
        h[2] += 0.08       # wobble phase
        h[0] += math.sin(h[2]) * 0.4   # gentle horizontal sway

        # Clamp x to right zone
        if h[0] < 51: h[0] = 51.0
        if h[0] > OLED_W - 4: h[0] = float(OLED_W - 4)

        # Respawn when off the top
        if h[1] < -3:
            h[0] = float(random.randint(51, OLED_W - 5))
            h[1] = float(OLED_H + 2)
            h[2] = random.uniform(0, math.pi * 2)

        hx = round(h[0]); hy = round(h[1])
        draw_tiny_heart(hx, hy)

    # ── Twinkling stars ───────────────────────────────────────────────────────
    for s in stars:
        s[2] += 1
        if s[2] >= s[3]:
            s[2] = 0
            s[4] = not s[4]   # toggle on/off
        if s[4]:
            sx, sy = s[0], s[1]
            set_pixel(sx, sy)
            # tiny + shape on alternate beats for sparkle
            if (tick // 30) % 2 == 0:
                set_pixel(sx-1, sy); set_pixel(sx+1, sy)
                set_pixel(sx, sy-1); set_pixel(sx, sy+1)

    # ── Heartbeat dot (bottom-right corner) ──────────────────────────────────
    # Period ~50 ticks → ~1.2 BPM multiplied to 72 BPM
    # Two quick beats per cycle of 100 ticks (simulating lub-dub)
    beat_t = tick % 100
    if beat_t < 6 or (15 <= beat_t < 21):
        r = 2
    else:
        r = 1
    hb_x, hb_y = OLED_W - 6, OLED_H - 6
    fill_circle(hb_x, hb_y, r)

# ── Intro screen ──────────────────────────────────────────────────────────────
NOTE_CX, NOTE_CY = 95, 28               # music note center (right side of display)

def draw_intro(tick):
    """Animated intro: pookie face + animated music note for first 8 seconds."""
    clear_buf()

    # Background (hearts on right, stars anywhere right of face)
    draw_background(tick)

    # Alternate between single and double note with a slow pulse (~every 40 ticks)
    phase = (tick // 40) % 2
    # Gentle vertical bounce for the music note (±2 px, period ~60 ticks)
    bounce = round(2 * math.sin(tick * 2 * math.pi / 60))

    if phase == 0:
        draw_music_note(NOTE_CX, NOTE_CY + bounce)
    else:
        draw_double_note(NOTE_CX - 3, NOTE_CY + bounce)

    # Face alternates eye states for a lively intro
    eye_phase = (tick // 80) % 3
    eye_states = ['open', 'sparkle', 'heart']
    draw_face(FACE_CX_INTRO, FACE_CY_INTRO, eye_states[eye_phase], 'bigsmile')

    # "be my baby" text
    label_x = 55
    label_y = 10
    draw_text('be my', label_x, label_y)
    draw_text('baby', label_x + 3, label_y + 10)

    # Small repeating note dots below—decorative
    pulse = (tick // 15) % 3
    for i in range(3):
        dot_x = 58 + i * 14
        dot_y = 52
        if i <= pulse:
            fill_circle(dot_x, dot_y, 2)
        else:
            draw_circle(dot_x, dot_y, 2)

# ── Lyrics list with exact timestamps (seconds from launch) ──────────────────
LYRICS = [
    ( 8, "the night we met"),
    (10, "i needed you so"),
    (15, "and if i had the chance"),
    (19, "id never let you go so"),
    (23, "wont you say you love me"),
    (26, "ill make you so proud of me"),
    (30, "well make em turn their heads"),
    (33, "every place we go"),
    (35, "so wont you please"),
    (39, "be my little baby"),
    (43, "say youll be my darling"),
    (46, "be my baby now"),
    (50, "whoa oh oh oh"),
]

# Pre-wrap all lyrics
LYRIC_LINES = [wrap_lyric(l[1]) for l in LYRICS]

# ── Face cycling state ────────────────────────────────────────────────────────
EYE_STATES   = ['open', 'uwu', 'heart', 'wink', 'sparkle', 'teary', 'dizzy']
MOUTH_STATES = ['bigsmile', 'smile', 'neutral', 'open', 'kiss', 'cat', 'singing']
FACE_CYCLE_TICKS = FPS * 3   # change face every 3 seconds
BLINK_DURATION = 4            # frames of closed-eye blink during transition

def make_face_sequence():
    """Generate a randomized sequence of (eye, mouth) pairs."""
    eyes = EYE_STATES[:]
    mouths = MOUTH_STATES[:]
    random.shuffle(eyes)
    random.shuffle(mouths)
    # Cycle mouths if more eyes than mouths (or vice versa)
    pairs = [(eyes[i], mouths[i % len(mouths)]) for i in range(len(eyes))]
    # For extra variety, re-shuffle mouths for the next round
    return pairs

# ── Draw lyric lines (wrapped) at a given x offset ───────────────────────────
def draw_lyric_lines(lines, text_x, tick):
    """Draw wrapped lyric lines vertically centered in the text zone."""
    n = len(lines)
    # Vertical center: OLED center is 32, leave room for face at y≈7–50 area
    start_y = 32 - (n * 9) // 2
    for i, line in enumerate(lines):
        draw_text(line, text_x, start_y + i * 9)

# ── Render lyric scene (face + optional background + text) ───────────────────
def draw_lyric_scene(eye, mouth, old_lines, new_lines, trans_t, global_tick):
    """Draw a complete lyric frame.

    trans_t: 0..SLIDE_FRAMES during transition, -1 when stable.
    old_lines/new_lines: wrapped line lists.
    """
    clear_buf()

    # Background first
    draw_background(global_tick)

    # Face (blink at start of transition for a brief flash)
    effective_eye = eye
    if trans_t >= 0 and trans_t < BLINK_DURATION:
        effective_eye = 'blink'
    draw_face(FACE_CX, FACE_CY, effective_eye, mouth)

    # Lyric text
    if trans_t < 0:
        # Stable: draw current lyric at rest position
        draw_lyric_lines(new_lines, TEXT_ZONE_X, global_tick)
    else:
        # Slide transition: progress 0→1 over SLIDE_FRAMES
        progress = trans_t / SLIDE_FRAMES
        # Ease in-out for smoothness
        t = progress * progress * (3 - 2 * progress)
        old_x = round(TEXT_ZONE_X - t * OLED_W)    # old slides left (exits)
        new_x = round(TEXT_ZONE_X + (1 - t) * OLED_W)  # new slides in from right

        if old_lines:
            draw_lyric_lines(old_lines, old_x, global_tick)
        draw_lyric_lines(new_lines, new_x, global_tick)

# ── Render buf → pygame surface ───────────────────────────────────────────────
def render(screen, oled_rect, show_grid, actual_w, actual_h, dyn_scale):
    """Draw everything. All positions are relative to oled_rect / actual screen
    dimensions so the layout is correct on any screen size."""
    cx = actual_w // 2   # horizontal center of screen

    # ── PCB panel (sized to wrap the OLED with comfortable margins) ────────────
    PAD_H      = max(14, dyn_scale * 5)   # horizontal padding each side
    PAD_TOP    = max(32, dyn_scale * 7)   # room for pin row above OLED
    PAD_BOTTOM = max(52, dyn_scale * 9)   # room for song info + hint below
    pcb_rect = pygame.Rect(
        oled_rect.left  - PAD_H,
        oled_rect.top   - PAD_TOP,
        oled_rect.width + PAD_H * 2,
        oled_rect.height + PAD_TOP + PAD_BOTTOM,
    )
    pygame.draw.rect(screen, PCB, pcb_rect, border_radius=8)
    pygame.draw.rect(screen, PCB_BORDER, pcb_rect, 2, border_radius=8)

    # ── Mounting holes at PCB corners ─────────────────────────────────────────
    ho = 9   # hole inset
    HOLE_COL_RING = (110, 130, 90)   # bright PCB-gold-green
    for pos in [
        (pcb_rect.left + ho,  pcb_rect.top    + ho),
        (pcb_rect.right - ho, pcb_rect.top    + ho),
        (pcb_rect.left + ho,  pcb_rect.bottom - ho),
        (pcb_rect.right - ho, pcb_rect.bottom - ho),
    ]:
        pygame.draw.circle(screen, BG, pos, 5)
        pygame.draw.circle(screen, HOLE_COL_RING, pos, 5, 1)

    # ── PCB trace lines (decorative) ──────────────────────────────────────────
    TR = (38, 50, 35)   # subtle dark-green trace color
    bx, by, bw, bh = pcb_rect
    # horizontal trace along top edge (under pin row)
    trace_y = oled_rect.top - PAD_TOP // 2
    pygame.draw.line(screen, TR, (bx + ho + 8, trace_y), (bx + bw - ho - 8, trace_y), 1)
    # short vertical stubs up from bezel corners
    bezel_top = oled_rect.top - 6
    for tx in (oled_rect.left + 6, oled_rect.right - 6):
        pygame.draw.line(screen, TR, (tx, trace_y), (tx, bezel_top), 1)
    # horizontal trace below OLED
    trace_y2 = oled_rect.bottom + PAD_BOTTOM // 3
    pygame.draw.line(screen, TR, (bx + ho + 8, trace_y2), (bx + bw - ho - 8, trace_y2), 1)

    # ── Pin header row above OLED ─────────────────────────────────────────────
    pin_font = pygame.font.SysFont('monospace', max(7, dyn_scale + 3))
    pins = ['GND', 'VCC', 'SCL', 'SDA']
    n_pins = len(pins)
    PIN_RING = (180, 160, 60)   # bright gold solder pad ring
    # Distribute pins evenly across the OLED width
    pin_spacing = oled_rect.width // (n_pins + 1)
    pin_dot_y = oled_rect.top - max(16, dyn_scale * 3)
    for i, p in enumerate(pins):
        px = oled_rect.left + pin_spacing * (i + 1)
        # solder pad
        pygame.draw.circle(screen, (200, 185, 80), (px, pin_dot_y), 4)
        pygame.draw.circle(screen, PIN_RING, (px, pin_dot_y), 4, 1)
        # trace down to bezel
        pygame.draw.line(screen, TR, (px, pin_dot_y + 4), (px, bezel_top), 1)
        lbl = pin_font.render(p, True, (150, 150, 150))
        screen.blit(lbl, (px - lbl.get_width() // 2, pin_dot_y - lbl.get_height() - 1))

    # ── Screen bezel ──────────────────────────────────────────────────────────
    bezel = oled_rect.inflate(10, 10)
    pygame.draw.rect(screen, SCREEN_BG, bezel, border_radius=4)

    # ── OLED surface ──────────────────────────────────────────────────────────
    oled_surf = pygame.Surface((OLED_W * dyn_scale, OLED_H * dyn_scale))
    oled_surf.fill(OLED_BG)

    for y in range(OLED_H):
        for x in range(OLED_W):
            if buf[y][x]:
                pygame.draw.rect(oled_surf, OLED_PIX,
                                 (x * dyn_scale, y * dyn_scale, dyn_scale, dyn_scale))

    # scanlines
    scan_surf = pygame.Surface((OLED_W * dyn_scale, OLED_H * dyn_scale), pygame.SRCALPHA)
    for y in range(0, OLED_H * dyn_scale, 2):
        pygame.draw.line(scan_surf, (0, 0, 0, 15), (0, y), (OLED_W * dyn_scale, y))
    oled_surf.blit(scan_surf, (0, 0))

    # pixel grid
    if show_grid:
        grid_surf = pygame.Surface((OLED_W * dyn_scale, OLED_H * dyn_scale), pygame.SRCALPHA)
        for gx in range(0, OLED_W * dyn_scale, dyn_scale):
            pygame.draw.line(grid_surf, (0, 0, 0, 40), (gx, 0), (gx, OLED_H * dyn_scale))
        for gy in range(0, OLED_H * dyn_scale, dyn_scale):
            pygame.draw.line(grid_surf, (0, 0, 0, 40), (0, gy), (OLED_W * dyn_scale, gy))
        oled_surf.blit(grid_surf, (0, 0))

    screen.blit(oled_surf, oled_rect.topleft)

    # ── Song info — below OLED, inside PCB panel ──────────────────────────────
    info_font = pygame.font.SysFont('monospace', 11)
    note_lbl = info_font.render('\u266a  Be My Baby', True, TEXT_SONG)
    info_y = oled_rect.bottom + max(8, PAD_BOTTOM // 5)
    screen.blit(note_lbl, (cx - note_lbl.get_width() // 2, info_y))

    # ── SSD1306 chip label ────────────────────────────────────────────────────
    chip_font = pygame.font.SysFont('monospace', max(7, dyn_scale + 2))
    chip_lbl = chip_font.render('SSD1306', True, (75, 85, 70))
    chip_y = pcb_rect.bottom - chip_lbl.get_height() - 5
    screen.blit(chip_lbl, (cx - chip_lbl.get_width() // 2, chip_y))

    # ── Controls hint — below PCB panel, never overlapping OLED ──────────────
    hint_font = pygame.font.SysFont('monospace', max(8, dyn_scale + 2))
    hint = hint_font.render('[G] GRID    [P] PAUSE    [Q] QUIT', True, (60, 60, 60))
    # Place just below PCB, or at least 4px from bottom of screen
    hint_y = min(pcb_rect.bottom + 6, actual_h - hint.get_height() - 4)
    screen.blit(hint, (cx - hint.get_width() // 2, hint_y))


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    random.seed()

    # Windowed mode at fixed 900×600
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption('OLED Animation \u2014 Be My Baby')
    clock = pygame.time.Clock()

    # Read the actual surface size — on HiDPI / phone screens the OS may
    # deliver a different resolution than requested, so always use the real
    # dimensions for centering rather than the WIN_W/WIN_H constants.
    actual_w, actual_h = screen.get_size()

    # Dynamic scale: largest integer scale that lets the OLED fit comfortably
    # with room reserved for the pin row above and UI text below.
    UI_RESERVE_V = 120   # vertical px reserved for pins above + text below
    UI_RESERVE_H = 40    # horizontal px reserved (padding each side)
    max_scale_w = max(1, (actual_w - UI_RESERVE_H) // OLED_W)
    max_scale_h = max(1, (actual_h - UI_RESERVE_V) // OLED_H)
    dyn_scale   = max(1, min(SCALE, max_scale_w, max_scale_h))

    oled_pw = OLED_W * dyn_scale
    oled_ph = OLED_H * dyn_scale
    # Center OLED perfectly — the PCB panel will be built around it in render()
    oled_x = (actual_w - oled_pw) // 2
    oled_y = (actual_h - oled_ph) // 2
    oled_rect = pygame.Rect(oled_x, oled_y, oled_pw, oled_ph)

    show_grid = False
    paused    = False

    # ── Global tick (counts every frame when not paused, includes intro) ──────
    global_tick = 0

    # ── Intro state ───────────────────────────────────────────────────────────
    intro_active = True

    # ── Init background systems ───────────────────────────────────────────────
    init_bg()

    # ── Lyric state ───────────────────────────────────────────────────────────
    lyric_idx  = -1        # currently displayed lyric index (-1 = none yet)
    old_lines  = []        # lines of previous lyric (for slide-out)
    cur_lines  = []        # lines of current lyric (for slide-in / stable)
    trans_t    = -1        # -1 = stable; 0..SLIDE_FRAMES = animating

    # ── Face state ────────────────────────────────────────────────────────────
    face_pairs   = make_face_sequence()
    face_pair_idx = 0
    face_tick    = 0       # counts ticks since last face change
    cur_eye, cur_mouth = face_pairs[face_pair_idx]

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_g:
                    show_grid = not show_grid
                if event.key == pygame.K_p:
                    paused = not paused

        if not paused:

            # ── Intro phase ──────────────────────────────────────────────────
            if intro_active:
                draw_intro(global_tick)
                global_tick += 1
                if global_tick >= INTRO_DURATION:
                    intro_active = False
                    # global_tick keeps counting — lyrics trigger at
                    # second * FPS regardless of intro offset.

            # ── Lyrics phase ─────────────────────────────────────────────────
            else:
                # --- Face cycling (independent timer) ---
                face_tick += 1
                if face_tick >= FACE_CYCLE_TICKS:
                    face_tick = 0
                    face_pair_idx = (face_pair_idx + 1) % len(face_pairs)
                    if face_pair_idx == 0:
                        # Reshuffle when we've cycled through all pairs
                        face_pairs = make_face_sequence()
                    cur_eye, cur_mouth = face_pairs[face_pair_idx]

                # --- Lyric triggering ---
                # Find which lyric should be active right now
                elapsed_sec = global_tick / FPS
                new_idx = -1
                for i, (ts, _) in enumerate(LYRICS):
                    if elapsed_sec >= ts:
                        new_idx = i

                if new_idx != lyric_idx:
                    # New lyric triggered — start transition
                    old_lines = cur_lines[:]
                    if new_idx >= 0:
                        cur_lines = LYRIC_LINES[new_idx]
                    else:
                        cur_lines = []
                    lyric_idx = new_idx
                    trans_t = 0   # begin slide transition

                # --- Advance transition ---
                if trans_t >= 0:
                    trans_t += 1
                    if trans_t >= SLIDE_FRAMES:
                        trans_t = -1   # transition complete — stable

                # --- Draw ---
                draw_lyric_scene(cur_eye, cur_mouth,
                                 old_lines, cur_lines,
                                 trans_t, global_tick)

                global_tick += 1

        # ── Blit to screen ────────────────────────────────────────────────────
        screen.fill(BG)
        render(screen, oled_rect, show_grid, actual_w, actual_h, dyn_scale)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == '__main__':
    main()
