#!/usr/bin/env python3
"""news-image-20261123, variant 9 (repair): a broadsheet front page for
Monday 23 November 2026.

One page, eight stories, four regions. The lead is the strike on an
Iranian tanker at the Hormuz blockade line while President Trump presses
for a permanent nuclear deal or new strikes after the New Year; 31 laden
tankers wait beyond the strait. The rest of the page: BepiColombo in
orbit around Mercury after eight years, the NHS starting the world's
largest AI breast-screening trial, Asian tech shares sliding again in
the AI sell-off with euro inflation at 4.0%, an AI-assisted Riemann
proof still awaiting its final checks, the UK named host of the 2035
Women's World Cup, the Thai-Cambodia ceasefire holding, and Virginia and
Oregon suing over Grok images. Everything is drawn with the standard
library only: a tiny 5x7 bitmap font, a pixel buffer, and a hand-rolled
PNG writer. Deterministic, no network. Writes
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""

import os
import random
import struct
import zlib

PAGE_W, PAGE_H = 1024, 1024

# ------------------------------------------------------------------ font
# A 5x7 bitmap font. Each glyph is one 35-character string of 0s and 1s,
# read row by row, top to bottom, left to right: the first five characters
# are the top row of the glyph, the next five the second row, and so on.
# Capitals, digits and the punctuation this page needs; anything else
# falls back to blank.
GLYPHS = {
    "A": "01110100011000111111100011000110001",
    "B": "11110100011000111110100011000111110",
    "C": "01111100001000010000100001000001111",
    "D": "11110100011000110001100011000111110",
    "E": "11111100001000011110100001000011111",
    "F": "11111100001000011110100001000010000",
    "G": "01111100001000010111100011000101110",
    "H": "10001100011000111111100011000110001",
    "I": "01110001000010000100001000010001110",
    "J": "00111000100001000010000101001001100",
    "K": "10001100101010011000101001001010001",
    "L": "10000100001000010000100001000011111",
    "M": "10001110111010110101100011000110001",
    "N": "10001110011010110011100011000110001",
    "O": "01110100011000110001100011000101110",
    "P": "11110100011000111110100001000010000",
    "Q": "01110100011000110001101011001001101",
    "R": "11110100011000111110101001001010001",
    "S": "01111100001000001110000010000111110",
    "T": "11111001000010000100001000010000100",
    "U": "10001100011000110001100011000101110",
    "V": "10001100011000110001100010101000100",
    "W": "10001100011000110101101011101110001",
    "X": "10001100010101000100010101000110001",
    "Y": "10001100010101000100001000010000100",
    "Z": "11111000010001000100010001000011111",
    "0": "01110100011001110101110011000101110",
    "1": "00100011000010000100001000010001110",
    "2": "01110100010000100010001000100011111",
    "3": "11110000010000101110000010000111110",
    "4": "00010001100101010010111110001000010",
    "5": "11111100001111000001000011000101110",
    "6": "00110010001000011110100011000101110",
    "7": "11111000010001000100010000100001000",
    "8": "01110100011000101110100011000101110",
    "9": "01110100011000101111000010001001100",
    " ": "00000000000000000000000000000000000",
    ".": "00000000000000000000000000110001100",
    ",": "00000000000000000000011000010001000",
    ":": "00000011000110000000011000110000000",
    "-": "00000000000000001110000000000000000",
    "/": "00001000010001000100010001000010000",
    "'": "00100001000100000000000000000000000",
    "!": "00100001000010000100001000000000100",
    "?": "01110100010000100010001000000000100",
    "(": "00010001000100001000010000010000010",
    ")": "01000001000001000010000100010001000",
    "%": "11001110100001000100010001011010011",
    "+": "00000001000010011111001000010000000",
    "*": "00000101010111011111011101010100000",
    '"': "01010010100101000000000000000000000",
    "&": "01100100101010001000101011001001101",
    "=": "00000000001111100000111110000000000",
    "$": "00100011111010101110001011111000100",
    "•": "00000000000111001110011100000000000",
}

BLANK_GLYPH = "0" * 35


def glyph_bits(ch):
    """The 35-bit string for one character, upper-cased, blank if unknown."""
    return GLYPHS.get(ch, GLYPHS.get(ch.upper(), BLANK_GLYPH))


def text_width(s, scale):
    """Pixel width of s at the given scale, one blank column between glyphs."""
    if not s:
        return 0
    return len(s) * (6 * scale) - scale


def wrap_text(s, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    lines, cur = [], ""
    for word in s.split(" "):
        if cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ sheet
class Sheet:
    """A plain RGB pixel buffer with the few drawing tools a front page
    needs: filled boxes, lines, discs, triangles, bitmap text, and two
    kinds of deterministic paper grain."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def fill(self, x0, y0, x1, y1, c):
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(self.w - 1, x1), min(self.h - 1, y1)
        if x1 < x0 or y1 < y0:
            return
        row = bytes(c) * (x1 - x0 + 1)
        for y in range(y0, y1 + 1):
            i = (y * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x0, x1, y, c):
        self.fill(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.fill(x, y0, x, y1, c)

    def frame(self, x0, y0, x1, y1, c, t=1):
        for k in range(t):
            self.hline(x0 + k, x1 - k, y0 + k, c)
            self.hline(x0 + k, x1 - k, y1 - k, c)
            self.vline(x0 + k, y0 + k, y1 - k, c)
            self.vline(x1 - k, y0 + k, y1 - k, c)

    def dot(self, cx, cy, r, c):
        rr = r * r
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= rr:
                    self.put(x, y, c)

    def wedge(self, ax, ay, bx, by, cx, cy, c):
        """Filled triangle, scanline by scanline from the top vertex."""
        pts = sorted(((ax, ay), (bx, by), (cx, cy)), key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        if y0 == y2:
            return

        def edge(xa, ya, xb, yb, y):
            if yb == ya:
                return float(xa)
            return xa + (xb - xa) * (y - ya) / (yb - ya)

        for y in range(y0, y2 + 1):
            left = edge(x0, y0, x2, y2, y)
            right = edge(x0, y0, x1, y1, y) if y < y1 else edge(x1, y1, x2, y2, y)
            lo, hi = (left, right) if left <= right else (right, left)
            self.hline(int(lo), int(hi), y, c)

    def stroke(self, x0, y0, x1, y1, c):
        """Bresenham line between two points."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def draw_text(self, x, y, s, scale, c):
        for ch in s:
            bits = glyph_bits(ch)
            for r in range(7):
                row = bits[r * 5:(r + 1) * 5]
                for col in range(5):
                    if row[col] == "1":
                        self.fill(x + col * scale, y + r * scale,
                                  x + col * scale + scale - 1,
                                  y + r * scale + scale - 1, c)
            x += 6 * scale

    def draw_text_centered(self, cx, y, s, scale, c):
        self.draw_text(cx - text_width(s, scale) // 2, y, s, scale, c)

    def grain(self, amp, seed):
        """Newsprint grain over the whole page: a hash of (x, y, seed)
        nudges every pixel by a few levels, so flat areas still carry
        the density of a printed page without changing any shape."""
        buf, w, h = self.buf, self.w, self.h
        span = 2 * amp + 1
        for y in range(h):
            base = y * w * 3
            for x in range(w):
                n = (x * 2654435761 + y * 40503 + seed * 97) & 0xFFFFFFFF
                n ^= n >> 15
                n = (n * 2246822519) & 0xFFFFFFFF
                n ^= n >> 13
                d = (n % span) - amp
                if d:
                    i = base + x * 3
                    for k in range(3):
                        v = buf[i + k] + d
                        buf[i + k] = 0 if v < 0 else (255 if v > 255 else v)

    def speckle(self, x0, y0, x1, y1, n, colors, seed):
        """A scattering of tiny paper dots inside a box."""
        rng = random.Random(seed)
        for _ in range(n):
            x = rng.randint(x0, x1)
            y = rng.randint(y0, y1)
            self.put(x, y, colors[rng.randrange(len(colors))])


# ---------------------------------------------------------------- palette
PAPER = (244, 238, 224)
PAPER_SHADE = (232, 224, 205)
INK = (18, 18, 20)
FLAG_RED = (178, 34, 28)
DEEP_BLUE = (28, 58, 110)
MIDNIGHT = (12, 24, 52)
DUSK_TOP = (58, 66, 110)
DUSK_GLOW = (246, 158, 74)
DEEP_SEA = (24, 52, 78)
SEA_LIGHT = (46, 92, 118)
SUN_YELLOW = (250, 196, 90)
SMOKE_GREY = (90, 84, 78)
OFF_WHITE = (250, 248, 242)
MID_GREY = (120, 116, 108)
ROSE = (214, 90, 140)
LEAF = (34, 120, 70)
BRASS = (198, 148, 44)


# ----------------------------------------------------------------- scenes
def blend(a, b, t):
    """Linear blend between two RGB colours."""
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))


def draw_stars(sh, x0, y0, x1, y1, n, seed):
    rng = random.Random(seed)
    for _ in range(n):
        x = rng.randint(x0, x1)
        y = rng.randint(y0, y1)
        r = rng.choice([1, 1, 1, 2])
        sh.dot(x, y, r, OFF_WHITE if rng.random() < 0.8 else SUN_YELLOW)


def draw_waves(sh, x0, y0, x1, y1, base, crest, seed):
    rng = random.Random(seed)
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            ln = rng.randint(8, 26)
            sh.hline(x, min(x1, x + ln), y, crest if rng.random() < 0.5 else base)
            x += ln + rng.randint(4, 14)
        y += rng.randint(5, 9)


def hero_hormuz(sh, x0, y0, x1, y1):
    """Dusk over the Strait of Hormuz: a struck tanker, a warship, a low sun."""
    stops = [(DUSK_TOP, 0.0), ((96, 84, 120), 0.30), ((196, 110, 80), 0.58),
             (DUSK_GLOW, 0.78), ((250, 178, 96), 1.0)]
    span = y1 - y0
    for i in range(span + 1):
        f = i / max(1, span)
        col = stops[0][0]
        for j in range(len(stops) - 1):
            if stops[j][1] <= f <= stops[j + 1][1]:
                t = (f - stops[j][1]) / max(0.001, stops[j + 1][1] - stops[j][1])
                col = blend(stops[j][0], stops[j + 1][0], t)
                break
        sh.hline(x0, x1, y0 + i, col)
    horizon = y0 + int(span * 0.60)
    # low sun with a broken reflection on the water
    sx = x0 + int((x1 - x0) * 0.70)
    sy = y0 + int(span * 0.40)
    sh.dot(sx, sy, 30, SUN_YELLOW)
    sh.dot(sx, sy, 19, (252, 214, 130))
    rng = random.Random(23)
    for k in range(24):
        w = rng.randint(20, 84)
        sh.hline(sx - w // 2, sx + w // 2, horizon + 6 + k * 4,
                 (250, 190, 110) if k % 3 else (240, 150, 80))
    # headlands left and right
    sh.wedge(x0, horizon, x0 + 140, horizon - 48, x0 + 250, horizon, (52, 44, 66))
    sh.wedge(x1 - 250, horizon, x1 - 120, horizon - 58, x1, horizon, (52, 44, 66))
    # sea
    sh.fill(x0, horizon, x1, y1, DEEP_SEA)
    draw_waves(sh, x0, horizon + 4, x1, y1, SEA_LIGHT, (120, 170, 200), 7)
    # smoke rising from the tanker, drifting left
    rng = random.Random(11)
    for k in range(44):
        px = x0 + 290 + rng.randint(-28, 88) - k * 2
        py = horizon - 116 - k * 2 + rng.randint(-8, 8)
        sh.dot(px, py, rng.randint(8, 19), SMOKE_GREY if k % 2 else (110, 102, 92))
    # tanker hull, centre-left, with fire on deck
    tx, ty = x0 + 200, horizon - 44
    sh.fill(tx, ty, tx + 320, ty + 42, (30, 30, 34))
    sh.fill(tx + 12, ty + 42, tx + 308, ty + 56, (52, 24, 22))
    sh.fill(tx + 244, ty - 32, tx + 292, ty, (40, 40, 44))
    sh.fill(tx + 252, ty - 54, tx + 284, ty - 32, (200, 60, 30))
    for k in range(9):
        sh.hline(tx + 28 + k * 31, tx + 48 + k * 31, ty + 11, (90, 90, 96))
    sh.dot(tx + 116, ty - 8, 15, (240, 120, 30))
    sh.dot(tx + 116, ty - 17, 8, (250, 200, 80))
    sh.wedge(tx + 100, ty - 6, tx + 116, ty - 42, tx + 132, ty - 6, (250, 160, 40))
    # warship to the right, mast and flag
    wx, wy = x0 + 630, horizon - 28
    sh.fill(wx, wy, wx + 200, wy + 24, (58, 64, 72))
    sh.fill(wx + 144, wy - 24, wx + 178, wy, (58, 64, 72))
    sh.vline(wx + 161, wy - 48, wy - 24, (40, 44, 50))
    sh.fill(wx + 161, wy - 48, wx + 188, wy - 37, FLAG_RED)
    sh.dot(wx + 38, wy - 6, 5, (180, 180, 180))
    # two small patrol boats
    for bx in (x0 + 56, x0 + 860):
        sh.fill(bx, horizon + 24, bx + 66, horizon + 36, (36, 40, 46))
        sh.fill(bx + 42, horizon + 11, bx + 56, horizon + 24, (36, 40, 46))
    # gulls
    for gx, gy in [(x0 + 116, y0 + 38), (x0 + 164, y0 + 58), (x0 + 820, y0 + 28)]:
        sh.stroke(gx, gy, gx + 8, gy - 5, INK)
        sh.stroke(gx + 8, gy - 5, gx + 16, gy, INK)


def scene_mercury(sh, x0, y0, x1, y1):
    """BepiColombo above Mercury: black sky, cratered planet, twin probe."""
    sh.fill(x0, y0, x1, y1, (8, 10, 26))
    draw_stars(sh, x0, y0, x1, y1, 90, 31)
    cx, cy = x0 + (x1 - x0) // 2, y1 - 6
    sh.dot(cx, cy, 68, (150, 118, 92))
    sh.dot(cx - 13, cy - 19, 60, (176, 140, 112))
    rng = random.Random(41)
    for _ in range(24):
        px = cx + rng.randint(-68, 68)
        py = cy + rng.randint(-68, 28)
        if (px - cx) * (px - cx) + (py - cy) * (py - cy) < 68 * 68:
            sh.dot(px, py, rng.randint(2, 6), (120, 94, 74))
    # the twin spacecraft with its solar wings
    sx, sy = x0 + (x1 - x0) // 2, y0 + 40
    sh.fill(sx - 68, sy - 8, sx - 14, sy + 8, (40, 90, 160))
    sh.fill(sx + 14, sy - 8, sx + 68, sy + 8, (40, 90, 160))
    for k in range(5):
        sh.vline(sx - 60 + k * 12, sy - 8, sy + 8, (120, 180, 230))
        sh.vline(sx + 22 + k * 12, sy - 8, sy + 8, (120, 180, 230))
    sh.fill(sx - 12, sy - 10, sx + 12, sy + 10, (200, 200, 205))
    sh.dot(sx, sy + 15, 4, SUN_YELLOW)


def scene_nhs(sh, x0, y0, x1, y1):
    """The NHS AI screening trial: a scan on a stand, a pink ribbon, a chip."""
    sh.fill(x0, y0, x1, y1, (238, 226, 232))
    # mammogram screen on a stand
    sx, sy = x0 + 18, y0 + 14
    sh.fill(sx, sy, sx + 96, sy + 66, (30, 30, 34))
    sh.fill(sx + 4, sy + 4, sx + 92, sy + 62, (210, 228, 235))
    sh.dot(sx + 48, sy + 34, 20, (120, 150, 170))
    sh.dot(sx + 40, sy + 28, 12, (150, 180, 200))
    sh.fill(sx + 44, sy + 66, sx + 52, sy + 78, (30, 30, 34))
    # pink ribbon
    rx, ry = x0 + 150, y0 + 22
    sh.wedge(rx, ry, rx + 16, ry + 26, rx, ry + 52, ROSE)
    sh.wedge(rx + 32, ry, rx + 16, ry + 26, rx + 32, ry + 52, ROSE)
    sh.dot(rx + 16, ry + 26, 7, (196, 60, 120))
    # AI chip with radiating ticks
    cx, cy = x0 + 178, y0 + 62
    sh.fill(cx - 16, cy - 16, cx + 16, cy + 16, (20, 60, 120))
    sh.fill(cx - 8, cy - 8, cx + 8, cy + 8, OFF_WHITE)
    sh.draw_text(cx - 4, cy - 5, "AI", 1, DEEP_BLUE)
    for dx, dy in [(-24, 0), (24, 0), (0, -24), (0, 24), (-18, -18), (18, 18)]:
        sh.stroke(cx, cy, cx + dx, cy + dy, DEEP_BLUE)


def scene_markets(sh, x0, y0, x1, y1):
    """Asian markets slide: a falling red chart on a dark board."""
    sh.fill(x0, y0, x1, y1, (16, 18, 26))
    for gx in range(x0 + 12, x1 - 8, 24):
        sh.vline(gx, y0 + 8, y1 - 8, (40, 44, 56))
    for gy in range(y0 + 12, y1 - 8, 18):
        sh.hline(x0 + 8, x1 - 8, gy, (40, 44, 56))
    pts = []
    for k in range(9):
        pts.append((x0 + 14 + k * 26, y0 + 16 + k * 7 + (k % 3) * 4))
    for a, b in zip(pts, pts[1:]):
        sh.stroke(a[0], a[1], b[0], b[1], (230, 60, 50))
        sh.dot(b[0], b[1], 3, (250, 120, 100))
    sh.dot(pts[-1][0], pts[-1][1], 5, FLAG_RED)
    # one small green chip breaking the fall
    sh.fill(x1 - 52, y0 + 12, x1 - 16, y0 + 34, (20, 90, 50))
    sh.draw_text(x1 - 46, y0 + 16, "AI", 1, OFF_WHITE)


def scene_maths(sh, x0, y0, x1, y1):
    """The Riemann proof, still being checked: a chalkboard of primes."""
    sh.fill(x0, y0, x1, y1, (246, 240, 220))
    bx, by = x0 + 12, y0 + 10
    sh.fill(bx, by, bx + 150, by + 58, (24, 60, 44))
    sh.frame(bx, by, bx + 150, by + 58, (180, 150, 90), 2)
    sh.draw_text(bx + 8, by + 8, "2 3 5 7 11", 1, OFF_WHITE)
    sh.draw_text(bx + 8, by + 20, "13 17 19 23", 1, OFF_WHITE)
    sh.draw_text(bx + 8, by + 34, "PRIMES = ?", 1, (250, 220, 120))
    # a green tick inside the board, right of the primes question
    sh.stroke(bx + 112, by + 46, bx + 122, by + 56, LEAF)
    sh.stroke(bx + 122, by + 56, bx + 142, by + 36, LEAF)
    sh.stroke(bx + 112, by + 48, bx + 122, by + 58, LEAF)
    sh.stroke(bx + 122, by + 58, bx + 142, by + 38, LEAF)
    # magnifier over a zeta
    sh.dot(x0 + 190, y0 + 62, 14, (255, 255, 255))
    sh.frame(x0 + 176, y0 + 48, x0 + 204, y0 + 76, DEEP_BLUE, 2)
    sh.draw_text(x0 + 186, y0 + 56, "Z", 2, DEEP_BLUE)


def scene_sport(sh, x0, y0, x1, y1):
    """World Cup 2035 goes to the UK: a stadium, a ball, a trophy."""
    sh.fill(x0, y0, x1, y1, (18, 90, 50))
    sh.fill(x0 + 10, y0 + 40, x1 - 10, y1 - 14, (220, 225, 220))
    for k in range(7):
        sh.vline(x0 + 24 + k * 30, y0 + 40, y1 - 14, (180, 190, 180))
    sh.fill(x0 + 10, y0 + 40, x1 - 10, y0 + 52, (30, 110, 60))
    sh.dot(x0 + 30, y0 + 18, 6, SUN_YELLOW)
    sh.dot(x1 - 30, y0 + 18, 6, SUN_YELLOW)
    sh.stroke(x0 + 30, y0 + 24, x0 + 60, y0 + 44, SUN_YELLOW)
    sh.stroke(x1 - 30, y0 + 24, x1 - 60, y0 + 44, SUN_YELLOW)
    # ball and trophy, year between them
    sh.dot(x0 + 108, y0 + 68, 20, OFF_WHITE)
    sh.frame(x0 + 88, y0 + 48, x0 + 128, y0 + 88, INK, 1)
    sh.dot(x0 + 108, y0 + 68, 6, INK)
    sh.fill(x1 - 72, y0 + 48, x1 - 32, y0 + 80, BRASS)
    sh.fill(x1 - 78, y0 + 56, x1 - 72, y0 + 70, BRASS)
    sh.fill(x1 - 32, y0 + 56, x1 - 26, y0 + 70, BRASS)
    sh.fill(x1 - 66, y0 + 80, x1 - 38, y0 + 86, BRASS)
    sh.draw_text(x0 + 150, y0 + 58, "2035", 2, OFF_WHITE)


def scene_truce(sh, x0, y0, x1, y1):
    """The Thai-Cambodia ceasefire holds: a dove over two flags."""
    sh.fill(x0, y0, x1, y1, (232, 238, 244))
    dx, dy = x0 + 108, y0 + 34
    sh.dot(dx, dy, 14, OFF_WHITE)
    sh.wedge(dx - 26, dy - 4, dx - 6, dy - 2, dx - 22, dy + 12, OFF_WHITE)
    sh.wedge(dx + 6, dy - 12, dx + 30, dy - 22, dx + 12, dy - 2, OFF_WHITE)
    sh.dot(dx + 12, dy - 4, 4, INK)
    sh.stroke(dx + 16, dy - 4, dx + 26, dy - 6, (220, 160, 40))
    # two flags on poles
    for fx, c in [(x0 + 30, (220, 40, 40)), (x1 - 66, (30, 90, 180))]:
        sh.vline(fx, y0 + 48, y1 - 10, INK)
        sh.fill(fx, y0 + 48, fx + 36, y0 + 68, c)
        sh.fill(fx, y0 + 58, fx + 36, y0 + 62, OFF_WHITE)
    sh.draw_text(x0 + 78, y1 - 22, "PEACE", 1, DEEP_BLUE)


def scene_court(sh, x0, y0, x1, y1):
    """Virginia and Oregon sue over Grok: a courthouse, a phone, a warning."""
    sh.fill(x0, y0, x1, y1, (40, 44, 60))
    sh.fill(x0 + 16, y0 + 44, x1 - 16, y0 + 52, (210, 205, 190))
    sh.wedge(x0 + 16, y0 + 44, x0 + 108, y0 + 16, x1 - 16, y0 + 44, (210, 205, 190))
    for k in range(4):
        cx = x0 + 34 + k * 46
        sh.fill(cx, y0 + 52, cx + 14, y1 - 12, (200, 195, 180))
    sh.fill(x0 + 16, y1 - 12, x1 - 16, y1 - 6, (210, 205, 190))
    # phone with a warning triangle
    px, py = x1 - 62, y0 + 56
    sh.fill(px, py, px + 34, py + 40, (20, 20, 24))
    sh.fill(px + 3, py + 3, px + 31, py + 37, (250, 240, 120))
    sh.wedge(px + 17, py + 10, px + 8, py + 28, px + 26, py + 28, FLAG_RED)
    sh.draw_text(px + 15, py + 18, "!", 1, OFF_WHITE)


# ----------------------------------------------------------------- layout
def story_box(sh, x0, y0, x1, y1, tag, head, body, draw, seed):
    """One story panel: a drawn scene on top, a red kicker bar, a headline
    and two or three lines of body copy, on paper with a thin ink frame."""
    sh.fill(x0, y0, x1, y1, PAPER)
    sh.frame(x0, y0, x1, y1, INK, 1)
    draw(sh, x0 + 1, y0 + 1, x1 - 1, y0 + 96)
    sh.fill(x0, y0 + 97, x1, y0 + 118, FLAG_RED)
    sh.draw_text(x0 + 8, y0 + 103, tag, 1, OFF_WHITE)
    ty = y0 + 126
    for ln in wrap_text(head, (x1 - x0 - 16) // 12):
        sh.draw_text(x0 + 8, ty, ln, 2, INK)
        ty += 16
    ty += 4
    for ln in wrap_text(body, (x1 - x0 - 16) // 6):
        sh.draw_text(x0 + 8, ty, ln, 1, (60, 58, 54))
        ty += 9
    sh.speckle(x0 + 2, y0 + 120, x1 - 2, y1 - 2, 260,
               [(220, 210, 190), (200, 190, 170)], seed)


def encode_png(sh):
    """A whole PNG: signature, IHDR, one IDAT with filter byte 0 per row,
    IEND; every chunk carries its CRC."""
    raw = bytearray()
    for y in range(sh.h):
        raw.append(0)
        raw += sh.buf[y * sh.w * 3:(y + 1) * sh.w * 3]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", sh.w, sh.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    return png


def main():
    sh = Sheet(PAGE_W, PAGE_H, PAPER)
    sh.frame(0, 0, PAGE_W - 1, PAGE_H - 1, INK, 3)
    sh.speckle(4, 4, PAGE_W - 5, PAGE_H - 5, 5200,
               [(228, 220, 202), (236, 228, 210), (214, 204, 186)], 99)

    # masthead
    sh.fill(4, 4, PAGE_W - 5, 94, MIDNIGHT)
    sh.draw_text_centered(PAGE_W // 2, 14, "THE WORLD IN ONE DAY", 4, OFF_WHITE)
    sh.draw_text_centered(PAGE_W // 2, 60, "MONDAY 23 NOVEMBER 2026", 2, SUN_YELLOW)
    sh.draw_text(16, 70, "8 STORIES", 1, OFF_WHITE)
    sh.draw_text(PAGE_W - 16 - text_width("4 REGIONS", 1), 70, "4 REGIONS", 1, OFF_WHITE)
    sh.hline(4, PAGE_W - 5, 96, FLAG_RED)
    sh.hline(4, PAGE_W - 5, 98, FLAG_RED)

    # hero: Hormuz
    hx0, hy0, hx1, hy1 = 10, 102, PAGE_W - 11, 468
    hero_hormuz(sh, hx0, hy0, hx1, hy1)
    sh.frame(hx0, hy0, hx1, hy1, INK, 2)
    sh.fill(hx0, hy1 - 106, hx1, hy1, (12, 12, 16))
    sh.draw_text(hx0 + 12, hy1 - 100, "STRAIT OF HORMUZ  •  THE GULF", 2, SUN_YELLOW)
    sh.draw_text(hx0 + 12, hy1 - 74, "TANKER STRUCK AT HORMUZ", 3, OFF_WHITE)
    for i, ln in enumerate(wrap_text(
            "US HITS AN IRANIAN OIL TANKER AT THE BLOCKADE LINE AS TRUMP "
            "DEMANDS A PERMANENT NUCLEAR DEAL OR NEW STRIKES AFTER THE NEW "
            "YEAR. IRAN VOWS EVERY MEANS TO BREAK THE BLOCKADE. 31 LADEN "
            "TANKERS WAIT BEYOND THE STRAIT.", 78)):
        sh.draw_text(hx0 + 12, hy1 - 42 + i * 11, ln, 1, (220, 218, 210))

    # story grid: four panels, then three
    gy0, gy1 = 478, 740
    pw = (PAGE_W - 20 - 3 * 8) // 4
    row1 = [
        ("SPACE  •  ESA / JAXA", "MERCURY AT LAST",
         "BEPICOLOMBO IN ORBIT AFTER 8 YEARS. ESA SAYS THE THRUSTER BURN "
         "RAN SHORT: 77% OF THE PLANNED PUSH, A 75-HOUR ORBIT, NOT 58. "
         "THE PROBE IS SAFE.", scene_mercury, 1),
        ("HEALTH  •  ENGLAND", "AI READS THE SCAN",
         "NHS STARTS THE WORLD'S LARGEST AI BREAST SCREENING TRIAL: "
         "NEARLY 700,000 WOMEN OVER THREE YEARS, FIRST IN CAMBRIDGE. "
         "A 10M POUND TEST.", scene_nhs, 2),
        ("MARKETS  •  ASIA", "AI SELL-OFF DEEPENS",
         "ASIAN TECH SHARES FALL FURTHER AFTER THE NASDAQ SLIDE. WALL "
         "STREET IS EXPECTED TO REBOUND. EURO INFLATION RISES TO 4.0%.",
         scene_markets, 3),
        ("SCIENCE  •  MATHS", "A PROOF, STILL CHECKED",
         "AN AI-HELPED PROOF OF THE RIEMANN HYPOTHESIS AWAITS ITS FINAL "
         "CHECKS. MATHEMATICIANS DEBATE A PROOF NO HUMAN FULLY "
         "UNDERSTANDS YET.", scene_maths, 4),
    ]
    for i, (tag, head, body, draw, seed) in enumerate(row1):
        x0 = 10 + i * (pw + 8)
        story_box(sh, x0, gy0, x0 + pw, gy1, tag, head, body, draw, seed)

    gy0, gy1 = 748, 960
    pw3 = (PAGE_W - 20 - 2 * 8) // 3
    row2 = [
        ("SPORT  •  FOOTBALL", "WORLD CUP 2035: UK",
         "FIFA CONFIRMS THE UK AS HOST OF THE 2035 WOMEN'S WORLD CUP: "
         "ENGLAND, SCOTLAND, WALES AND NORTHERN IRELAND TOGETHER.",
         scene_sport, 5),
        ("ASIA  •  THAILAND-CAMBODIA", "TRUCE HOLDS",
         "THE CEASEFIRE BETWEEN THAILAND AND CAMBODIA HOLDS AFTER THE "
         "DEAL REACHED ON MONDAY. FIGHTING IS ON HOLD ALONG THE BORDER.",
         scene_truce, 6),
        ("LAW  •  UNITED STATES", "STATES SUE OVER GROK",
         "VIRGINIA AND OREGON SUE SPACEX, X AND XAI, SAYING GROK MADE "
         "SEXUALISED IMAGES, INCLUDING OF CHILDREN.", scene_court, 7),
    ]
    for i, (tag, head, body, draw, seed) in enumerate(row2):
        x0 = 10 + i * (pw3 + 8)
        story_box(sh, x0, gy0, x0 + pw3, gy1, tag, head, body, draw, seed)

    # footer ticker + sources
    sh.fill(10, 968, PAGE_W - 11, 1012, INK)
    sh.draw_text(16, 976, "ALSO TODAY:", 1, SUN_YELLOW)
    for i, ln in enumerate(wrap_text(
            "IRAN FLOGS SINGER PARASTOO AHMADI 74 LASHES  •  MANCHESTER "
            "CO-OP LIVE EVACUATED AFTER UNKNOWN SUBSTANCE  •  VANCE MEETS "
            "QATAR PM ON STALLED IRAN TALKS  •  PIP REVIEW PROPOSES "
            "FAST-TRACK PAYMENTS", 108)):
        sh.draw_text(16, 990 + i * 10, ln, 1, OFF_WHITE)
    sh.draw_text(10, 1014,
                 "SOURCES: REUTERS, AP, BBC, NHS ENGLAND, ESA - ALL STORIES REPORTED MONDAY 23 NOVEMBER 2026",
                 1, (70, 68, 64))

    # newsprint grain over the whole page, then write the file
    sh.grain(2, 12345)

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(encode_png(sh))


if __name__ == "__main__":
    main()



