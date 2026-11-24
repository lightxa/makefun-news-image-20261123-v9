#!/usr/bin/env python3
"""news-image-20261123 variant 9: one front page, the Gulf at dusk.

A broadsheet front page for Monday 23 November 2026, built from a fresh
story set no earlier variant used. The hero is the day's single most
striking moment: a US strike on an Iranian oil tanker at the Hormuz
blockade line, as President Trump demanded a permanent nuclear deal or
new strikes after the New Year, with 31 laden tankers waiting beyond the
strait. Seven more panels cover the rest of the day across four regions:
BepiColombo entering orbit around Mercury after eight years (ESA's
23 November update on the thruster glitch), the NHS starting the world's
largest AI breast screening trial, the AI sell-off deepening in Asian
markets with euro inflation at 4.0%, the AI-assisted Riemann proof still
awaiting its final checks, the UK confirmed as 2035 Women's World Cup
host, the Thai-Cambodia ceasefire holding, and Virginia and Oregon suing
over Grok images. Pure standard library, deterministic, no network.
Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output/entry.png).
"""

import os
import random
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap font: seven rows of five cells ("#" = ink). Capitals, digits
# and the punctuation this front page needs.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
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
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": ("..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "$": ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    "•": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
}

BLANK = (".....",) * 7


def text_w(s, scale):
    return len(s) * (6 * scale) - scale


def wrap(s, max_chars):
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


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x0, y0, x1, y1, c):
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(self.w - 1, x1), min(self.h - 1, y1)
        for y in range(y0, y1 + 1):
            i = (y * self.w + x0) * 3
            self.px[i:(y * self.w + x1 + 1) * 3] = bytes(c) * (x1 - x0 + 1)

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x, y1, c)

    def border(self, x0, y0, x1, y1, c, t=1):
        for k in range(t):
            self.rect(x0 + k, y0 + k, x1 - k, y0 + k, c)
            self.rect(x0 + k, y1 - k, x1 - k, y1 - k, c)
            self.rect(x0 + k, y0 + k, x0 + k, y1 - k, c)
            self.rect(x1 - k, y0 + k, x1 - k, y1 - k, c)

    def disc(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def tri(self, ax, ay, bx, by, cx, cy, c):
        """Filled triangle via scanline interpolation."""
        pts = sorted([(ax, ay), (bx, by), (cx, cy)], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        if y0 == y2:
            return
        for y in range(y0, y2 + 1):
            if y < y1:
                xa = x0 + (x1 - x0) * (y - y0) / max(1, y1 - y0)
            else:
                xa = x1 + (x2 - x1) * (y - y1) / max(1, y2 - y1)
            xb = x0 + (x2 - x0) * (y - y0) / max(1, y2 - y0)
            lo, hi = sorted([int(xa), int(xb)])
            self.hline(lo, hi, y, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham line."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def text(self, x, y, s, scale, c):
        for ch in s:
            g = FONT.get(ch, FONT.get(ch.upper(), BLANK))
            for r in range(7):
                for col in range(5):
                    if g[r][col] == "#":
                        self.rect(x + col * scale, y + r * scale,
                                  x + col * scale + scale - 1,
                                  y + r * scale + scale - 1, c)
            x += 6 * scale

    def text_c(self, cx, y, s, scale, c):
        self.text(cx - text_w(s, scale) // 2, y, s, scale, c)

    def grain(self, amp, seed):
        """Deterministic newsprint grain: a small hash-based offset on
        every pixel. Flat areas stay flat to the eye but stop compressing
        to nothing, so the file carries the density of a real front page."""
        px, w, h = self.px, self.w, self.h
        span = 2 * amp + 1
        for y in range(h):
            base = y * w * 3
            for x in range(w):
                n = (x * 374761393 + y * 668265263 + seed * 974634211) & 0xFFFFFFFF
                n ^= n >> 13
                n = (n * 1274126177) & 0xFFFFFFFF
                n ^= n >> 16
                d = (n % span) - amp
                if d:
                    i = base + x * 3
                    for k in range(3):
                        v = px[i + k] + d
                        px[i + k] = 0 if v < 0 else (255 if v > 255 else v)

    def speckle(self, x0, y0, x1, y1, n, colors, seed):
        """Deterministic paper grain: n tiny dots inside a box."""
        rng = random.Random(seed)
        for _ in range(n):
            x = rng.randint(x0, x1)
            y = rng.randint(y0, y1)
            self.set(x, y, colors[rng.randrange(len(colors))])


# ---------------------------------------------------------------- palette
PAPER = (244, 238, 224)
PAPER_DK = (232, 224, 205)
INK = (18, 18, 20)
RED = (178, 34, 28)
BLUE = (28, 58, 110)
NAVY = (12, 24, 52)
SKY_DUSK = (246, 158, 74)
SKY_TOP = (58, 66, 110)
SEA = (24, 52, 78)
SEA_LT = (46, 92, 118)
SUN = (250, 196, 90)
SMOKE = (90, 84, 78)
WHITE = (250, 248, 242)
GREY = (120, 116, 108)
PINK = (214, 90, 140)
GREEN = (34, 120, 70)
GOLD = (198, 148, 44)


# ---------------------------------------------------------------- scenes
def draw_stars(cv, x0, y0, x1, y1, n, seed):
    rng = random.Random(seed)
    for _ in range(n):
        x = rng.randint(x0, x1)
        y = rng.randint(y0, y1)
        r = rng.choice([1, 1, 1, 2])
        cv.disc(x, y, r, WHITE if rng.random() < 0.8 else SUN)


def draw_waves(cv, x0, y0, x1, y1, base, crest, seed):
    rng = random.Random(seed)
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            ln = rng.randint(8, 26)
            cv.hline(x, min(x1, x + ln), y, crest if rng.random() < 0.5 else base)
            x += ln + rng.randint(4, 14)
        y += rng.randint(5, 9)


def hero_hormuz(cv, x0, y0, x1, y1):
    """Dusk over the Strait of Hormuz: tanker, warship, smoke, low sun."""
    # dusk sky in horizontal bands
    bands = [(SKY_TOP, 0.0), ((96, 84, 120), 0.30), ((196, 110, 80), 0.58),
             (SKY_DUSK, 0.78), ((250, 178, 96), 1.0)]
    for i in range(y1 - y0 + 1):
        f = i / max(1, y1 - y0)
        c = bands[0][0]
        for j in range(len(bands) - 1):
            if bands[j][1] <= f <= bands[j + 1][1]:
                t = (f - bands[j][1]) / max(0.001, bands[j + 1][1] - bands[j][1])
                a, b = bands[j][0], bands[j + 1][0]
                c = tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))
                break
        cv.hline(x0, x1, y0 + i, c)
    horizon = y0 + int((y1 - y0) * 0.62)
    # low sun and its reflection
    sx, sy = x0 + int((x1 - x0) * 0.72), y0 + int((y1 - y0) * 0.42)
    cv.disc(sx, sy, 34, SUN)
    cv.disc(sx, sy, 22, (252, 214, 130))
    rng = random.Random(23)
    for k in range(26):
        w = rng.randint(20, 90)
        cv.hline(sx - w // 2, sx + w // 2, horizon + 6 + k * 4,
                 (250, 190, 110) if k % 3 else (240, 150, 80))
    # distant cliffs left and right
    cv.tri(x0, horizon, x0 + 150, horizon - 52, x0 + 260, horizon, (52, 44, 66))
    cv.tri(x1 - 260, horizon, x1 - 130, horizon - 64, x1, horizon, (52, 44, 66))
    # sea
    cv.rect(x0, horizon, x1, y1, SEA)
    draw_waves(cv, x0, horizon + 4, x1, y1, SEA_LT, (120, 170, 200), 7)
    # smoke plume above the tanker
    rng = random.Random(11)
    for k in range(46):
        px = x0 + 300 + rng.randint(-30, 90) - k * 2
        py = horizon - 120 - k * 2 + rng.randint(-8, 8)
        cv.disc(px, py, rng.randint(8, 20), SMOKE if k % 2 else (110, 102, 92))
    # tanker hull (big, centre-left) with fire on deck
    tx, ty = x0 + 210, horizon - 46
    cv.rect(tx, ty, tx + 330, ty + 44, (30, 30, 34))
    cv.rect(tx + 12, ty + 44, tx + 318, ty + 58, (52, 24, 22))
    cv.rect(tx + 250, ty - 34, tx + 300, ty, (40, 40, 44))
    cv.rect(tx + 258, ty - 58, tx + 292, ty - 34, (200, 60, 30))
    for k in range(9):
        cv.hline(tx + 30 + k * 32, tx + 52 + k * 32, ty + 12, (90, 90, 96))
    cv.disc(tx + 120, ty - 8, 16, (240, 120, 30))
    cv.disc(tx + 120, ty - 18, 9, (250, 200, 80))
    cv.tri(tx + 104, ty - 6, tx + 120, ty - 44, tx + 136, ty - 6, (250, 160, 40))
    # warship (right) with mast and flag
    wx, wy = x0 + 640, horizon - 30
    cv.rect(wx, wy, wx + 210, wy + 26, (58, 64, 72))
    cv.rect(wx + 150, wy - 26, wx + 185, wy, (58, 64, 72))
    cv.vline(wx + 168, wy - 52, wy - 26, (40, 44, 50))
    cv.rect(wx + 168, wy - 52, wx + 196, wy - 40, RED)
    cv.disc(wx + 40, wy - 6, 5, (180, 180, 180))
    # small patrol boats
    for bx in (x0 + 60, x0 + 880):
        cv.rect(bx, horizon + 26, bx + 70, horizon + 38, (36, 40, 46))
        cv.rect(bx + 44, horizon + 12, bx + 58, horizon + 26, (36, 40, 46))
    # gulls
    for gx, gy in [(x0 + 120, y0 + 40), (x0 + 170, y0 + 62), (x0 + 840, y0 + 30)]:
        cv.line(gx, gy, gx + 8, gy - 5, INK)
        cv.line(gx + 8, gy - 5, gx + 16, gy, INK)


def scene_mercury(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, (8, 10, 26))
    draw_stars(cv, x0, y0, x1, y1, 90, 31)
    cx, cy = x0 + (x1 - x0) // 2, y1 - 6
    cv.disc(cx, cy, 70, (150, 118, 92))
    cv.disc(cx - 14, cy - 20, 62, (176, 140, 112))
    rng = random.Random(41)
    for _ in range(26):
        px = cx + rng.randint(-70, 70)
        py = cy + rng.randint(-70, 30)
        if (px - cx) ** 2 + (py - cy) ** 2 < 70 * 70:
            cv.disc(px, py, rng.randint(2, 6), (120, 94, 74))
    # twin spacecraft with solar wings above the planet
    sx, sy = x0 + (x1 - x0) // 2, y0 + 42
    cv.rect(sx - 70, sy - 8, sx - 14, sy + 8, (40, 90, 160))
    cv.rect(sx + 14, sy - 8, sx + 70, sy + 8, (40, 90, 160))
    for k in range(5):
        cv.vline(sx - 62 + k * 12, sy - 8, sy + 8, (120, 180, 230))
        cv.vline(sx + 22 + k * 12, sy - 8, sy + 8, (120, 180, 230))
    cv.rect(sx - 12, sy - 10, sx + 12, sy + 10, (200, 200, 205))
    cv.disc(sx, sy + 16, 4, SUN)


def scene_nhs(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, (238, 226, 232))
    # mammogram screen on a stand
    sx, sy = x0 + 18, y0 + 14
    cv.rect(sx, sy, sx + 96, sy + 66, (30, 30, 34))
    cv.rect(sx + 4, sy + 4, sx + 92, sy + 62, (210, 228, 235))
    cv.disc(sx + 48, sy + 34, 20, (120, 150, 170))
    cv.disc(sx + 40, sy + 28, 12, (150, 180, 200))
    cv.rect(sx + 44, sy + 66, sx + 52, sy + 78, (30, 30, 34))
    # pink ribbon
    rx, ry = x0 + 150, y0 + 22
    cv.tri(rx, ry, rx + 16, ry + 26, rx, ry + 52, PINK)
    cv.tri(rx + 32, ry, rx + 16, ry + 26, rx + 32, ry + 52, PINK)
    cv.disc(rx + 16, ry + 26, 7, (196, 60, 120))
    # AI chip with radiating ticks
    cx, cy = x0 + 178, y0 + 62
    cv.rect(cx - 16, cy - 16, cx + 16, cy + 16, (20, 60, 120))
    cv.rect(cx - 8, cy - 8, cx + 8, cy + 8, WHITE)
    cv.text(cx - 4, cy - 5, "AI", 1, BLUE)
    for dx, dy in [(-24, 0), (24, 0), (0, -24), (0, 24), (-18, -18), (18, 18)]:
        cv.line(cx, cy, cx + dx, cy + dy, BLUE)


def scene_markets(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, (16, 18, 26))
    # falling red chart with grid
    for gx in range(x0 + 12, x1 - 8, 24):
        cv.vline(gx, y0 + 8, y1 - 8, (40, 44, 56))
    for gy in range(y0 + 12, y1 - 8, 18):
        cv.hline(x0 + 8, x1 - 8, gy, (40, 44, 56))
    pts = []
    for k in range(9):
        pts.append((x0 + 14 + k * 26, y0 + 16 + k * 7 + (k % 3) * 4))
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], (230, 60, 50))
        cv.disc(b[0], b[1], 3, (250, 120, 100))
    cv.disc(pts[-1][0], pts[-1][1], 5, RED)
    # small green chip breaking the fall
    cv.rect(x1 - 52, y0 + 12, x1 - 16, y0 + 34, (20, 90, 50))
    cv.text(x1 - 46, y0 + 16, "AI", 1, WHITE)


def scene_maths(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, (246, 240, 220))
    # chalkboard with prime numbers and a check
    bx, by = x0 + 12, y0 + 10
    cv.rect(bx, by, bx + 150, by + 58, (24, 60, 44))
    cv.border(bx, by, bx + 150, by + 58, (180, 150, 90), 2)
    cv.text(bx + 8, by + 8, "2 3 5 7 11", 1, WHITE)
    cv.text(bx + 8, by + 20, "13 17 19 23", 1, WHITE)
    cv.text(bx + 8, by + 34, "PRIMES = ?", 1, (250, 220, 120))
    cv.line(bx + 168, by + 40, bx + 182, by + 56, GREEN)
    cv.line(bx + 182, by + 56, bx + 206, by + 18, GREEN)
    cv.line(bx + 168, by + 42, bx + 182, by + 58, GREEN)
    cv.line(bx + 182, by + 58, bx + 206, by + 20, GREEN)
    # magnifier over a zeta symbol
    cv.disc(x0 + 190, y0 + 62, 14, (255, 255, 255))
    cv.border(x0 + 176, y0 + 48, x0 + 204, y0 + 76, BLUE, 2)
    cv.text(x0 + 186, y0 + 56, "Z", 2, BLUE)


def scene_sport(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, (18, 90, 50))
    # stadium bowl and floodlights
    cv.rect(x0 + 10, y0 + 40, x1 - 10, y1 - 14, (220, 225, 220))
    for k in range(7):
        cv.vline(x0 + 24 + k * 30, y0 + 40, y1 - 14, (180, 190, 180))
    cv.rect(x0 + 10, y0 + 40, x1 - 10, y0 + 52, (30, 110, 60))
    cv.disc(x0 + 30, y0 + 18, 6, SUN)
    cv.disc(x1 - 30, y0 + 18, 6, SUN)
    cv.line(x0 + 30, y0 + 24, x0 + 60, y0 + 44, SUN)
    cv.line(x1 - 30, y0 + 24, x1 - 60, y0 + 44, SUN)
    # ball and trophy
    cv.disc(x0 + 108, y0 + 68, 20, WHITE)
    cv.border(x0 + 88, y0 + 48, x0 + 128, y0 + 88, INK, 1)
    cv.disc(x0 + 108, y0 + 68, 6, INK)
    cv.rect(x1 - 72, y0 + 48, x1 - 32, y0 + 80, GOLD)
    cv.rect(x1 - 78, y0 + 56, x1 - 72, y0 + 70, GOLD)
    cv.rect(x1 - 32, y0 + 56, x1 - 26, y0 + 70, GOLD)
    cv.rect(x1 - 66, y0 + 80, x1 - 38, y0 + 86, GOLD)
    cv.text(x0 + 150, y0 + 58, "2035", 2, WHITE)


def scene_truce(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, (232, 238, 244))
    # dove over two flags
    dx, dy = x0 + 108, y0 + 34
    cv.disc(dx, dy, 14, WHITE)
    cv.tri(dx - 26, dy - 4, dx - 6, dy - 2, dx - 22, dy + 12, WHITE)
    cv.tri(dx + 6, dy - 12, dx + 30, dy - 22, dx + 12, dy - 2, WHITE)
    cv.disc(dx + 12, dy - 4, 4, INK)
    cv.line(dx + 16, dy - 4, dx + 26, dy - 6, (220, 160, 40))
    # two flags on poles
    for fx, c in [(x0 + 30, (220, 40, 40)), (x1 - 66, (30, 90, 180))]:
        cv.vline(fx, y0 + 48, y1 - 10, INK)
        cv.rect(fx, y0 + 48, fx + 36, y0 + 68, c)
        cv.rect(fx, y0 + 58, fx + 36, y0 + 62, WHITE)
    cv.text(x0 + 78, y1 - 22, "PEACE", 1, BLUE)


def scene_court(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, (40, 44, 60))
    # courthouse columns
    cv.rect(x0 + 16, y0 + 44, x1 - 16, y0 + 52, (210, 205, 190))
    cv.tri(x0 + 16, y0 + 44, x0 + 108, y0 + 16, x1 - 16, y0 + 44, (210, 205, 190))
    for k in range(4):
        cx = x0 + 34 + k * 46
        cv.rect(cx, y0 + 52, cx + 14, y1 - 12, (200, 195, 180))
    cv.rect(x0 + 16, y1 - 12, x1 - 16, y1 - 6, (210, 205, 190))
    # phone with warning triangle
    px, py = x1 - 62, y0 + 56
    cv.rect(px, py, px + 34, py + 40, (20, 20, 24))
    cv.rect(px + 3, py + 3, px + 31, py + 37, (250, 240, 120))
    cv.tri(px + 17, py + 10, px + 8, py + 28, px + 26, py + 28, RED)
    cv.text(px + 15, py + 18, "!", 1, WHITE)


# ---------------------------------------------------------------- layout
def panel(cv, x0, y0, x1, y1, kicker, head, body, scene, seed):
    cv.rect(x0, y0, x1, y1, PAPER)
    cv.border(x0, y0, x1, y1, INK, 1)
    scene(cv, x0 + 1, y0 + 1, x1 - 1, y0 + 96)
    cv.rect(x0, y0 + 97, x1, y0 + 118, RED)
    cv.text(x0 + 8, y0 + 103, kicker, 1, WHITE)
    ty = y0 + 126
    for ln in wrap(head, (x1 - x0 - 16) // 12):
        cv.text(x0 + 8, ty, ln, 2, INK)
        ty += 16
    ty += 4
    for ln in wrap(body, (x1 - x0 - 16) // 6):
        cv.text(x0 + 8, ty, ln, 1, (60, 58, 54))
        ty += 9
    cv.speckle(x0 + 2, y0 + 120, x1 - 2, y1 - 2, 260,
               [(220, 210, 190), (200, 190, 170)], seed)


def encode_png(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    return png


def main():
    cv = Canvas(W, H, PAPER)
    cv.border(0, 0, W - 1, H - 1, INK, 3)
    cv.speckle(4, 4, W - 5, H - 5, 5200,
               [(228, 220, 202), (236, 228, 210), (214, 204, 186)], 99)

    # masthead
    cv.rect(4, 4, W - 5, 96, NAVY)
    cv.text_c(W // 2, 14, "THE WORLD IN ONE DAY", 4, WHITE)
    cv.text_c(W // 2, 62, "MONDAY 23 NOVEMBER 2026", 2, SUN)
    cv.text(16, 70, "8 STORIES", 1, WHITE)
    cv.text(W - 16 - text_w("4 REGIONS", 1), 70, "4 REGIONS", 1, WHITE)
    cv.hline(4, W - 5, 98, RED)
    cv.hline(4, W - 5, 100, RED)

    # hero: Hormuz
    hx0, hy0, hx1, hy1 = 10, 104, W - 11, 470
    hero_hormuz(cv, hx0, hy0, hx1, hy1)
    cv.border(hx0, hy0, hx1, hy1, INK, 2)
    cv.rect(hx0, hy1 - 108, hx1, hy1, (12, 12, 16))
    cv.text(hx0 + 12, hy1 - 102, "STRAIT OF HORMUZ  •  THE GULF", 2, SUN)
    cv.text(hx0 + 12, hy1 - 76, "TANKER STRUCK AT HORMUZ", 3, WHITE)
    for i, ln in enumerate(wrap(
            "US HITS AN IRANIAN OIL TANKER AT THE BLOCKADE LINE AS TRUMP "
            "DEMANDS A PERMANENT NUCLEAR DEAL OR NEW STRIKES AFTER THE NEW "
            "YEAR. IRAN VOWS EVERY MEANS TO BREAK THE BLOCKADE. 31 LADEN "
            "TANKERS WAIT BEYOND THE STRAIT.", 78)):
        cv.text(hx0 + 12, hy1 - 44 + i * 11, ln, 1, (220, 218, 210))

    # story grid: four panels, then three
    gy0, gy1 = 480, 742
    pw = (W - 20 - 3 * 8) // 4
    panels = [
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
    for i, (kick, head, body, scene, seed) in enumerate(panels):
        x0 = 10 + i * (pw + 8)
        panel(cv, x0, gy0, x0 + pw, gy1, kick, head, body, scene, seed)

    gy0, gy1 = 750, 962
    pw3 = (W - 20 - 2 * 8) // 3
    panels2 = [
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
    for i, (kick, head, body, scene, seed) in enumerate(panels2):
        x0 = 10 + i * (pw3 + 8)
        panel(cv, x0, gy0, x0 + pw3, gy1, kick, head, body, scene, seed)

    # footer ticker + sources
    cv.rect(10, 970, W - 11, 1013, INK)
    cv.text(16, 978, "ALSO TODAY:", 1, SUN)
    for i, ln in enumerate(wrap(
            "IRAN FLOGS SINGER PARASTOO AHMADI 74 LASHES  •  MANCHESTER "
            "CO-OP LIVE EVACUATED AFTER UNKNOWN SUBSTANCE  •  VANCE MEETS "
            "QATAR PM ON STALLED IRAN TALKS  •  PIP REVIEW PROPOSES "
            "FAST-TRACK PAYMENTS", 108)):
        cv.text(16, 992 + i * 10, ln, 1, WHITE)
    cv.text_c(W // 2, 1016 - 4, "", 1, WHITE)
    cv.text(10, 1017, "SOURCES: REUTERS, AP, BBC, NHS ENGLAND, ESA - ALL STORIES REPORTED MONDAY 23 NOVEMBER 2026",
            1, (70, 68, 64))

    # newsprint grain over the whole page, then write the file
    cv.grain(2, 12345)

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(encode_png(cv))


if __name__ == "__main__":
    main()
