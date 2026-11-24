"""Monday 23 November 2026 in one picture.

A front page drawn entirely in code: no image files, no network, no
third party packages. Every pixel is produced here by a small canvas
class and a hand built 5x7 bitmap font, then packed into a PNG with
the standard library only.

Layout, top to bottom:
  masthead with the date and the count of the day
  lead scene: the tanker struck at the Hormuz blockade line
  orbit panel: BepiColombo circling Mercury
  six story cards: NHS screening, the Asia AI sell-off, the Riemann
  proof, the 2035 Women's World Cup hosts, the Thai-Cambodia
  ceasefire, and the Grok image lawsuits
  footer strip: four regions, eight stories, one date check

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 241, 222)
PAPER_DARK = (238, 229, 203)
INK = (26, 26, 34)
RED = (163, 22, 33)
BLUE = (29, 78, 137)
TEAL = (14, 110, 110)
GOLD = (176, 132, 32)
SEA = (38, 84, 124)
SKY = (214, 228, 238)
SUN = (232, 164, 62)
GREY = (110, 108, 100)
LIGHT_GREY = (200, 196, 182)


def _chunk(kind, payload):
    head = struct.pack(">I", len(payload)) + kind + payload
    tail = struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    return head + tail


def png_bytes(buf, w, h):
    """Encode an RGB bytearray as a PNG with no filtering."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += buf[y * stride:(y + 1) * stride]
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    out += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += _chunk(b"IEND", b"")
    return bytes(out)


class Canvas:
    """A plain RGB pixel buffer with shape helpers."""

    def __init__(self, w, h, base):
        self.w = w
        self.h = h
        self.buf = bytearray(base * (w * h))

    def px(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = colour[0]
            self.buf[i + 1] = colour[1]
            self.buf[i + 2] = colour[2]

    def rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = colour[0]
                self.buf[i + 1] = colour[1]
                self.buf[i + 2] = colour[2]

    def hline(self, x, y, length, colour, thick=1):
        for t in range(thick):
            self.rect(x, y + t, length, 1, colour)

    def vline(self, x, y, length, colour, thick=1):
        for t in range(thick):
            self.rect(x + t, y, 1, length, colour)

    def line(self, x0, y0, x1, y1, colour, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.rect(x, y, thick, thick, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.px(xx, yy, colour)

    def ring(self, cx, cy, r, colour, thick=2):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - thick <= d <= r + thick:
                    self.px(xx, yy, colour)

    def ellipse(self, cx, cy, rx, ry, colour):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                v = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
                if v <= 1.0:
                    self.px(xx, yy, colour)

    def triangle(self, ax, ay, bx, by, cx, cy, colour):
        lo_y = min(ay, by, cy)
        hi_y = max(ay, by, cy)
        for yy in range(lo_y, hi_y + 1):
            xs = []
            for (px0, py0, px1, py1) in (
                (ax, ay, bx, by),
                (bx, by, cx, cy),
                (cx, cy, ax, ay),
            ):
                if py0 == py1:
                    continue
                if (yy - py0) * (yy - py1) <= 0 and py0 != py1:
                    t = (yy - py0) / (py1 - py0)
                    xs.append(px0 + t * (px1 - px0))
            if len(xs) >= 2:
                for xx in range(int(min(xs)), int(max(xs)) + 1):
                    self.px(xx, yy, colour)

    def frame(self, x, y, w, h, colour, thick=3):
        self.hline(x, y, w, colour, thick)
        self.hline(x, y + h - thick, w, colour, thick)
        self.vline(x, y, h, colour, thick)
        self.vline(x + w - thick, y, h, colour, thick)


class Lcg:
    """Tiny deterministic generator for paper grain and stipple."""

    def __init__(self, seed):
        self.state = seed & 0x7FFFFFFF

    def next(self):
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return self.state

    def below(self, n):
        return self.next() % n


GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#..##", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
}


def glyph_width(ch):
    return 5


def text_width(text, scale):
    step = 6 * scale
    if not text:
        return 0
    return len(text) * step - scale


def draw_glyph(cv, ch, x, y, scale, colour):
    rows = GLYPHS.get(ch.upper(), GLYPHS["?"])
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            if cell == "#":
                cv.rect(x + c * scale, y + r * scale, scale, scale, colour)


def draw_text(cv, text, x, y, scale, colour):
    cx = x
    for ch in text:
        if ch == " ":
            cx += 6 * scale
            continue
        draw_glyph(cv, ch, cx, y, scale, colour)
        cx += 6 * scale
    return cx


def centre_text(cv, text, cx, y, scale, colour):
    w = text_width(text, scale)
    draw_text(cv, text, cx - w // 2, y, scale, colour)
    return w


def wrap_words(text, max_w, scale):
    """Split text into lines that fit max_w pixels at the given scale."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, text, x, y, max_w, scale, colour, leading=4):
    lines = wrap_words(text, max_w, scale)
    yy = y
    for line in lines:
        draw_text(cv, line, x, yy, scale, colour)
        yy += 7 * scale + leading
    return yy


def draw_kicker(cv, text, x, y, scale, fg, bg):
    pad = 4 * scale
    w = text_width(text, scale) + pad * 2
    h = 7 * scale + pad
    cv.rect(x, y, w, h, bg)
    draw_text(cv, text, x + pad, y + pad // 2, scale, fg)
    return w


def grain(cv):
    """Speckle the paper so the sheet reads as newsprint, not flat colour."""
    rng = Lcg(20261123)
    for _ in range(9000):
        x = rng.below(W)
        y = rng.below(H)
        tone = rng.below(3)
        if tone == 0:
            cv.px(x, y, (232, 223, 196))
        elif tone == 1:
            cv.px(x, y, (240, 233, 210))
        else:
            cv.px(x, y, (226, 216, 188))


def newsprint(cv):
    """Halftone the bare paper: near-identical tones picked by a hash.

    Real newsprint is never one flat colour. The variation is tiny
    (a few levels either way) so the page still reads as cream, but
    the picture carries the texture of a printed sheet instead of
    compressing down to a sketch.
    """
    tones = (
        (247, 241, 222),
        (243, 236, 214),
        (250, 245, 229),
        (240, 232, 208),
    )
    darks = (
        (238, 229, 203),
        (234, 224, 196),
        (242, 234, 210),
        (230, 220, 190),
    )
    buf = cv.buf
    rng = Lcg(20261123)
    for yy in range(cv.h):
        row = yy * cv.w * 3
        for xx in range(cv.w):
            i = row + xx * 3
            r = buf[i]
            g = buf[i + 1]
            b = buf[i + 2]
            if r == 247 and g == 241 and b == 222:
                t = tones[(rng.next() >> 16) & 3]
                buf[i] = t[0]
                buf[i + 1] = t[1]
                buf[i + 2] = t[2]
            elif r == 238 and g == 229 and b == 203:
                t = darks[(rng.next() >> 16) & 3]
                buf[i] = t[0]
                buf[i + 1] = t[1]
                buf[i + 2] = t[2]


def sky_bands(cv, x, y, w, h):
    """Horizontal dusk bands, light at the top, deeper toward the sea."""
    steps = 14
    for i in range(steps):
        t = i / max(1, steps - 1)
        r = int(226 - 62 * t)
        g = int(232 - 96 * t)
        b = int(238 - 84 * t)
        cv.rect(x, y + i * h // steps, w, h // steps + 1, (r, g, b))


def masthead(cv):
    cv.rect(0, 0, W, H, PAPER)
    grain(cv)
    cv.rect(24, 18, 976, 4, INK)
    centre_text(cv, "THE WORLD IN ONE DAY", W // 2, 34, 6, INK)
    cv.rect(24, 108, 976, 2, RED)
    centre_text(
        cv, "MONDAY 23 NOVEMBER 2026", W // 2, 122, 3, RED
    )
    centre_text(
        cv, "8 STORIES  *  4 REGIONS  *  ONE PAGE", W // 2, 152, 2, INK
    )
    cv.rect(24, 182, 976, 4, INK)


def hormuz_scene(cv, x, y, w, h):
    """Dusk over the strait: a tanker, a warship, the blockade line."""
    sky_bands(cv, x, y, w, 108)
    cv.disc(x + w - 110, y + 42, 26, SUN)
    cv.ring(x + w - 110, y + 42, 33, GOLD, 2)
    cv.rect(x, y + 108, w, h - 108, SEA)
    for i in range(6):
        yy = y + 122 + i * 10
        xx = (i * 137) % w
        cv.hline(x + xx, yy, 80 - i * 6, (88, 138, 172), 2)
    # blockade line: dashed red across the water
    for xx in range(x + 8, x + w - 8, 26):
        cv.rect(xx, y + 106, 16, 3, RED)
    draw_text(cv, "BLOCKADE LINE", x + 12, y + 90, 1, (255, 255, 255))
    # tanker hull, low and long
    cv.rect(x + 30, y + 140, 280, 30, (52, 52, 60))
    cv.rect(x + 30, y + 134, 280, 8, (120, 40, 44))
    cv.rect(x + 270, y + 122, 40, 14, (52, 52, 60))
    cv.rect(x + 278, y + 108, 7, 16, (52, 52, 60))
    cv.rect(x + 292, y + 108, 7, 16, (52, 52, 60))
    # smoke rising from the strike
    cv.disc(x + 160, y + 118, 12, (70, 70, 78))
    cv.disc(x + 178, y + 102, 15, (90, 90, 98))
    cv.disc(x + 196, y + 88, 10, (112, 112, 120))
    cv.disc(x + 150, y + 122, 7, (232, 120, 40))
    cv.disc(x + 168, y + 130, 6, (240, 160, 60))
    # warship silhouette on the right
    cv.rect(x + 420, y + 150, 140, 22, (30, 34, 40))
    cv.triangle(
        x + 560, y + 150, x + 588, y + 158, x + 560, y + 164, (30, 34, 40)
    )
    cv.rect(x + 455, y + 136, 36, 14, (30, 34, 40))
    cv.rect(x + 468, y + 124, 5, 12, (30, 34, 40))
    cv.rect(x + 420, y + 172, 140, 5, (120, 40, 44))
    # wake lines behind the warship
    cv.hline(x + 380, y + 178, 50, (200, 220, 235), 2)
    cv.hline(x + 360, y + 186, 60, (200, 220, 235), 2)
    cv.frame(x, y, w, h, INK, 3)


def lead_block(cv):
    x, y = 24, 196
    w, h = 620, 340
    hormuz_scene(cv, x, y, w, 190)
    draw_kicker(cv, "LEAD  *  MIDDLE EAST", x, y + 200, 2, PAPER, RED)
    draw_text(cv, "TANKER STRUCK AT", x + 4, y + 240, 3, INK)
    draw_text(cv, "HORMUZ BLOCKADE LINE", x + 4, y + 270, 3, INK)
    draw_para(
        cv,
        "A strike hits an Iranian tanker at the strait chokepoint as the blockade holds.",
        x + 4, y + 302, w - 8, 1, INK, leading=3,
    )
    cv.frame(x, y, w, h, INK, 3)


def orbit_panel(cv):
    x, y, w, h = 660, 196, 340, 340
    cv.rect(x, y, w, 184, (16, 20, 34))
    rng = Lcg(777)
    for _ in range(70):
        sx = x + 8 + rng.below(w - 16)
        sy = y + 8 + rng.below(168)
        cv.rect(sx, sy, 2, 2, (220, 224, 235))
    # Mercury, cratered
    cv.disc(x + 200, y + 96, 56, (188, 164, 138))
    cv.disc(x + 182, y + 78, 10, (160, 136, 112))
    cv.disc(x + 216, y + 112, 13, (160, 136, 112))
    cv.disc(x + 206, y + 66, 7, (172, 148, 122))
    cv.disc(x + 176, y + 108, 6, (172, 148, 122))
    # orbit ring around it
    cv.ring(x + 200, y + 96, 78, (240, 240, 245), 1)
    # spacecraft riding the ring, top left
    cv.rect(x + 108, y + 30, 26, 14, (220, 224, 230))
    cv.rect(x + 84, y + 33, 22, 8, (120, 150, 200))
    cv.rect(x + 136, y + 33, 22, 8, (120, 150, 200))
    cv.rect(x + 118, y + 44, 6, 10, GOLD)
    draw_kicker(cv, "SPACE", x + 12, y + 196, 2, PAPER, BLUE)
    draw_text(cv, "BEPICOLOMBO", x + 12, y + 232, 3, INK)
    draw_text(cv, "IN ORBIT AROUND", x + 12, y + 262, 2, INK)
    draw_text(cv, "MERCURY", x + 12, y + 288, 3, INK)
    draw_para(
        cv,
        "The joint mission settles into orbit around Mercury, the closest planet to the Sun.",
        x + 12, y + 318 - 4, w - 24, 1, INK, leading=3,
    )
    cv.frame(x, y, w, h, INK, 3)


def icon_nhs(cv, x, y):
    cv.rect(x, y, 52, 52, (214, 232, 240))
    cv.rect(x + 20, y + 10, 12, 32, BLUE)
    cv.rect(x + 10, y + 20, 32, 12, BLUE)
    cv.rect(x + 58, y + 8, 46, 36, PAPER)
    cv.frame(x + 58, y + 8, 46, 36, INK, 2)
    cv.line(x + 62, y + 36, x + 74, y + 20, TEAL, 2)
    cv.line(x + 74, y + 20, x + 84, y + 30, TEAL, 2)
    cv.line(x + 84, y + 30, x + 100, y + 14, TEAL, 2)


def icon_chart(cv, x, y):
    cv.rect(x, y, 104, 52, (240, 226, 222))
    cv.line(x + 8, y + 12, x + 30, y + 20, RED, 3)
    cv.line(x + 30, y + 20, x + 52, y + 18, RED, 3)
    cv.line(x + 52, y + 18, x + 74, y + 34, RED, 3)
    cv.line(x + 74, y + 34, x + 96, y + 44, RED, 3)
    cv.triangle(x + 88, y + 44, x + 100, y + 44, x + 96, y + 52, RED)


def icon_proof(cv, x, y):
    cv.rect(x, y, 104, 52, (232, 238, 232))
    px = x + 8
    py = y + 40
    for step in range(0, 88, 4):
        t = step / 88.0
        yy = int(py - 26 * (1 - t) * (1 - t) - 6 * t)
        cv.rect(px + step, yy, 4, 3, TEAL)
    cv.ring(x + 88, y + 14, 9, GOLD, 2)
    draw_text(cv, "?", x + 85, y + 8, 1, GOLD)


def icon_cup(cv, x, y):
    cv.rect(x, y, 104, 52, (244, 236, 210))
    cv.rect(x + 42, y + 6, 20, 18, GOLD)
    cv.rect(x + 36, y + 6, 6, 12, GOLD)
    cv.rect(x + 62, y + 6, 6, 12, GOLD)
    cv.rect(x + 49, y + 24, 6, 12, GOLD)
    cv.rect(x + 38, y + 36, 28, 6, GOLD)
    cv.disc(x + 52, y + 15, 4, (255, 240, 180))


def icon_branch(cv, x, y):
    cv.rect(x, y, 104, 52, (232, 238, 226))
    cv.line(x + 10, y + 44, x + 96, y + 10, TEAL, 3)
    for lx, ly in ((28, 36), (46, 28), (64, 20), (82, 12)):
        cv.ellipse(x + lx, y + ly, 10, 5, TEAL)
        cv.ellipse(x + lx + 4, y + ly + 10, 10, 5, TEAL)


def icon_scales(cv, x, y):
    cv.rect(x, y, 104, 52, (238, 232, 224))
    cv.vline(x + 52, y + 8, 36, INK, 3)
    cv.hline(x + 22, y + 10, 60, INK, 3)
    cv.line(x + 22, y + 10, x + 30, y + 30, INK, 2)
    cv.line(x + 22, y + 10, x + 14, y + 30, INK, 2)
    cv.line(x + 82, y + 10, x + 90, y + 30, INK, 2)
    cv.line(x + 82, y + 10, x + 74, y + 30, INK, 2)
    cv.triangle(x + 8, y + 30, x + 36, y + 30, x + 22, y + 42, BLUE)
    cv.triangle(x + 68, y + 30, x + 96, y + 30, x + 82, y + 42, BLUE)
    cv.rect(x + 44, y + 44, 16, 4, INK)


CARDS = [
    ("HEALTH  *  UK", "AI READS BREAST SCREENS IN NHS TRIAL",
     "Trial tests AI help for breast screening across NHS clinics.",
     icon_nhs),
    ("MARKETS  *  ASIA", "ASIAN TECH SHARES SLIDE IN AI SELL-OFF",
     "Tech shares fall across Asia as investors cool on AI stocks.",
     icon_chart),
    ("SCIENCE  *  MATHS", "AI-ASSISTED RIEMANN PROOF AWAITS CHECKS",
     "A machine-assisted proof nears final checks by mathematicians.",
     icon_proof),
    ("SPORT  *  UK", "UK TO HOST 2035 WOMEN'S WORLD CUP",
     "The UK is named host of the 2035 finals.",
     icon_cup),
    ("ASIA  *  PEACE", "THAI-CAMBODIA CEASEFIRE HOLDS",
     "The ceasefire along the Thai-Cambodia border holds for another day.",
     icon_branch),
    ("TECH  *  USA", "VIRGINIA AND OREGON SUE OVER GROK IMAGES",
     "Two US states sue over non-consensual AI images made with Grok.",
     icon_scales),
]


def card(cv, x, y, w, h, tag, headline, body, icon):
    cv.rect(x, y, w, h, PAPER_DARK)
    icon(cv, x + 12, y + 10)
    draw_kicker(cv, tag, x + 12, y + 72, 1, PAPER, INK)
    lines = wrap_words(headline, w - 24, 2)
    yy = y + 100
    for line in lines:
        draw_text(cv, line, x + 12, yy, 2, INK)
        yy += 7 * 2 + 3
    draw_para(cv, body, x + 12, yy + 4, w - 24, 1, INK, leading=3)
    cv.hline(x + 12, y + h - 26, w - 24, LIGHT_GREY, 1)
    draw_text(cv, "23 NOV 2026", x + 12, y + h - 20, 1, GREY)
    cv.frame(x, y, w, h, INK, 2)


def cards_row(cv):
    xs = (24, 355, 686)
    ys = (552, 760)
    for row, yy in enumerate(ys):
        for col, xx in enumerate(xs):
            tag, head, body, icon = CARDS[row * 3 + col]
            card(cv, xx, yy, 314, 196, tag, head, body, icon)


def footer(cv):
    y = 964
    cv.rect(24, y, 976, 2, INK)
    centre_text(
        cv,
        "MIDDLE EAST 1  *  SPACE 1  *  UK 2  *  ASIA 2  *  MATHS 1  *  USA 1",
        W // 2, y + 8, 1, INK,
    )
    centre_text(
        cv,
        "ALL EIGHT STORIES REPORTED ON MONDAY 23 NOVEMBER 2026",
        W // 2, y + 22, 1, GREY,
    )


def build():
    cv = Canvas(W, H, PAPER)
    masthead(cv)
    lead_block(cv)
    orbit_panel(cv)
    cards_row(cv)
    footer(cv)
    newsprint(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    data = png_bytes(cv.buf, W, H)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(data), W, H))


if __name__ == "__main__":
    main()
