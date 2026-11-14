"""The pirate-world dressing: moods, obstacles, treasure props, parchment, type.

sprites.py still owns the actors (pirate, crabs, coins, tide pools). This file
is everything added to make the islands feel like places: the time of day, the
rocks and palms that replace the wall of identical crates, the buried-treasure
props, and the parchment-and-gold look of the screens. All of it is drawn with
pygame primitives; nothing is loaded from disk.
"""
import math
import random

import pygame

from sprites import TILE_SIZE, crate_tile, soft_shadow

T = TILE_SIZE

INK = (50, 40, 30)
PARCHMENT = (240, 222, 178)
PARCHMENT_LIT = (250, 238, 204)
PARCHMENT_EDGE = (150, 112, 62)
PARCHMENT_BURN = (112, 78, 40)
GOLD = (222, 168, 46)
GOLD_LIT = (255, 222, 110)
GOLD_DEEP = (150, 98, 12)
BLOOD = (160, 40, 36)

# Each island sits at a different hour. `tint` multiplies the baked island,
# `dark` is how black the unlit night gets (None = no lantern needed).
MOODS = {
    "dawn":   {"sea": [(0.0, (236, 168, 142)), (0.35, (112, 170, 192)), (1.0, (38, 104, 140))],
               "tint": (255, 238, 228), "glint": (255, 226, 205), "dark": None},
    "noon":   {"sea": [(0.0, (79, 168, 206)), (0.42, (61, 155, 196)), (1.0, (27, 99, 137))],
               "tint": (255, 255, 255), "glint": (224, 244, 252), "dark": None},
    "golden": {"sea": [(0.0, (248, 186, 104)), (0.4, (92, 160, 170)), (1.0, (30, 94, 124))],
               "tint": (255, 234, 198), "glint": (255, 228, 160), "dark": None},
    "dusk":   {"sea": [(0.0, (124, 82, 132)), (0.4, (62, 92, 142)), (1.0, (24, 50, 96))],
               "tint": (228, 200, 216), "glint": (232, 190, 214), "dark": None},
    "night":  {"sea": [(0.0, (20, 32, 66)), (1.0, (8, 14, 36))],
               "tint": (188, 198, 232), "glint": (150, 170, 220), "dark": (70, 80, 122),
               "glow": (255, 236, 190)},
    "cove":   {"sea": [(0.0, (18, 62, 62)), (1.0, (6, 24, 30))],
               "tint": (182, 226, 200), "glint": (130, 220, 190), "dark": (96, 132, 122),
               "glow": (214, 255, 226)},
    "title":  {"sea": [(0.0, (250, 176, 96)), (0.22, (226, 120, 96)), (0.45, (70, 110, 150)),
                       (1.0, (16, 44, 84))],
               "tint": (255, 255, 255), "glint": (255, 214, 160), "dark": None},
}


# ------------------------------------------------------------------- type
_text_cache = {}


def outlined(font, text, fill, outline=(40, 26, 14), width=2):
    """Text with a solid outline: the poster lettering used for every heading.
    Cached, since stamping the outline costs eight extra blits."""
    key = (id(font), text, fill, outline, width)
    surf = _text_cache.get(key)
    if surf is None:
        if len(_text_cache) > 400:
            _text_cache.clear()
        base = font.render(text, True, fill)
        edge = font.render(text, True, outline)
        surf = pygame.Surface((base.get_width() + width * 2, base.get_height() + width * 2 + 2),
                              pygame.SRCALPHA)
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                if dx or dy:
                    surf.blit(edge, (dx + width, dy + width))
        surf.blit(edge, (width, width + 2))        # a little drop below
        surf.blit(base, (width, width))
        _text_cache[key] = surf
    return surf


def gold_title(font, text):
    """The big title: gold letters lit from above, each set slightly askew
    like a hand-painted tavern sign."""
    rnd = random.Random(text)
    letters = []
    for ch in text:
        if ch == " ":
            letters.append(None)
            continue
        base = font.render(ch, True, (255, 255, 255))
        w, h = base.get_size()
        grad = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            k = y / max(1, h - 1)
            col = tuple(int(GOLD_LIT[i] + (GOLD_DEEP[i] - GOLD_LIT[i]) * k ** 1.4) for i in range(3))
            pygame.draw.line(grad, col, (0, y), (w, y))
        grad.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        edge = font.render(ch, True, (46, 24, 10))
        tile = pygame.Surface((w + 8, h + 10), pygame.SRCALPHA)
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx * dx + dy * dy <= 10:
                    tile.blit(edge, (4 + dx, 4 + dy))
        tile.blit(edge, (4, 8))
        tile.blit(grad, (4, 4))
        tile = pygame.transform.rotate(tile, rnd.uniform(-4, 4))
        letters.append((tile, rnd.randint(-3, 3)))
    space = font.size(" ")[0]
    width = sum(space if l is None else l[0].get_width() - 9 for l in letters) + 12
    height = max(l[0].get_height() for l in letters if l) + 8
    out = pygame.Surface((width, height), pygame.SRCALPHA)
    x = 2
    for l in letters:
        if l is None:
            x += space
            continue
        out.blit(l[0], (x, 4 + l[1] + (height - 8 - l[0].get_height()) // 2))
        x += l[0].get_width() - 9
    return out


def wrap(font, text, width):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if font.size(trial)[0] <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


# -------------------------------------------------------------- parchment
_parchment_cache = {}


def parchment(width, height, seed=0):
    """A sheet of old paper: ragged edge, scorched rim, a few stains."""
    key = (width, height, seed)
    surf = _parchment_cache.get(key)
    if surf is not None:
        return surf
    rnd = random.Random(seed * 977 + width)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)

    def ragged(inset, wobble):
        pts = []
        step = 14
        for x in range(inset, width - inset, step):
            pts.append((x, inset + rnd.uniform(0, wobble)))
        for y in range(inset, height - inset, step):
            pts.append((width - inset - rnd.uniform(0, wobble), y))
        for x in range(width - inset, inset, -step):
            pts.append((x, height - inset - rnd.uniform(0, wobble)))
        for y in range(height - inset, inset, -step):
            pts.append((inset + rnd.uniform(0, wobble), y))
        return pts

    pygame.draw.polygon(surf, PARCHMENT_BURN, ragged(0, 4))
    pygame.draw.polygon(surf, PARCHMENT_EDGE, ragged(2, 4))
    pygame.draw.polygon(surf, PARCHMENT, ragged(5, 4))
    inner = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(inner, (*PARCHMENT_LIT, 150), (18, 16, width - 36, height - 32),
                     border_radius=30)
    for _ in range(max(3, width * height // 22000)):
        r = rnd.randint(8, 26)
        pygame.draw.circle(inner, (176, 138, 84, rnd.randint(14, 34)),
                           (rnd.randint(20, width - 20), rnd.randint(20, height - 20)), r)
    for _ in range(width * height // 900):
        pygame.draw.circle(inner, (150, 116, 70, 40),
                           (rnd.randint(12, width - 12), rnd.randint(12, height - 12)), 1)
    surf.blit(inner, (0, 0))
    _parchment_cache[key] = surf
    return surf


def ribbon(surface, font, text, cx, cy, fill=BLOOD, ink=(255, 240, 210), pad=26, alpha=255):
    """A swallow-tailed banner, for announcements."""
    label = outlined(font, text, ink, (60, 14, 12), 1)
    w, h = label.get_width() + pad * 2, label.get_height() + 12
    surf = pygame.Surface((w + 44, h + 12), pygame.SRCALPHA)
    dark = tuple(max(0, c - 55) for c in fill)
    for side in (0, 1):
        x0 = 0 if side == 0 else w + 44
        x1 = 30 if side == 0 else w + 14
        notch = 12 if side == 0 else w + 32
        pygame.draw.polygon(surf, dark, [(x0, 10), (x1, 10), (x1, h + 10), (x0, h + 10),
                                         (notch, h // 2 + 10)])
    pygame.draw.rect(surf, fill, (22, 0, w, h), border_radius=5)
    pygame.draw.rect(surf, dark, (22, 0, w, h), 2, border_radius=5)
    pygame.draw.line(surf, tuple(min(255, c + 45) for c in fill), (28, 4), (w + 16, 4), 1)
    surf.blit(label, label.get_rect(center=(22 + w // 2, h // 2 + 1)))
    if alpha < 255:
        surf.set_alpha(alpha)
    surface.blit(surf, surf.get_rect(center=(cx, cy)))


def skull_and_bones(surface, cx, cy, s=1.0, bone=(244, 236, 214), ink=(40, 28, 20)):
    r = int(16 * s)
    for sx, sy in ((-1, -1), (1, -1)):
        a = (cx + sx * int(26 * s), cy + int(4 * s) + sy * int(-14 * s))
        b = (cx - sx * int(26 * s), cy + int(4 * s) - sy * int(-14 * s) + int(8 * s))
        pygame.draw.line(surface, ink, a, b, int(9 * s))
        pygame.draw.line(surface, bone, a, b, int(5 * s))
        for p in (a, b):
            pygame.draw.circle(surface, ink, p, int(6 * s))
            pygame.draw.circle(surface, bone, p, int(4 * s))
    pygame.draw.circle(surface, ink, (cx, cy - int(4 * s)), r + 2)
    pygame.draw.rect(surface, ink, (cx - int(10 * s) - 2, cy, int(20 * s) + 4, int(14 * s) + 2),
                     border_radius=4)
    pygame.draw.circle(surface, bone, (cx, cy - int(4 * s)), r)
    pygame.draw.rect(surface, bone, (cx - int(10 * s), cy, int(20 * s), int(14 * s)),
                     border_radius=3)
    for side in (-1, 1):
        pygame.draw.circle(surface, ink, (cx + side * int(6 * s), cy - int(4 * s)), int(4.5 * s))
    pygame.draw.polygon(surface, ink, [(cx, cy + int(2 * s)), (cx - int(3 * s), cy + int(7 * s)),
                                       (cx + int(3 * s), cy + int(7 * s))])
    for i in (-1, 0, 1):
        x = cx + i * int(5 * s)
        pygame.draw.line(surface, ink, (x, cy + int(9 * s)), (x, cy + int(14 * s)), 1)


# -------------------------------------------------------------- obstacles
_tiles = {}


def obstacle_tile(kind):
    """Pre-rendered obstacle, one per kind. Tiles are T wide and a little
    taller so each can cast a drop underneath."""
    surf = _tiles.get(kind)
    if surf is not None:
        return surf
    if kind == "crate":
        surf = crate_tile()
    else:
        surf = pygame.Surface((T, T + 4), pygame.SRCALPHA)
        rnd = random.Random(kind)
        if kind.startswith("rock") or kind == "palm":
            pts, n = [], 9
            for i in range(n):
                a = 2 * math.pi * i / n
                rr = T * 0.5 - rnd.uniform(1, 6)
                pts.append((T / 2 + math.cos(a) * rr, T / 2 + math.sin(a) * rr * 0.94))
            pygame.draw.polygon(surf, (62, 56, 54), [(x, y + 4) for x, y in pts])
            pygame.draw.polygon(surf, (128, 120, 112), pts)
            hi = [(T / 2 + (x - T / 2) * 0.72 - 3, T / 2 + (y - T / 2) * 0.72 - 4) for x, y in pts]
            pygame.draw.polygon(surf, (156, 148, 136), hi)
            for _ in range(3):
                x, y = rnd.randint(9, T - 12), rnd.randint(9, T - 12)
                pygame.draw.line(surf, (98, 92, 88), (x, y),
                                 (x + rnd.randint(-6, 6), y + rnd.randint(3, 8)), 1)
            pygame.draw.polygon(surf, (70, 62, 58), pts, 2)
            if kind == "palm":
                c = (T // 2, T // 2 - 1)
                pygame.draw.circle(surf, (96, 66, 40), c, 5)
                for i in range(7):
                    a = 2 * math.pi * i / 7 + 0.3
                    tip = (c[0] + math.cos(a) * 19, c[1] + math.sin(a) * 18)
                    mid = (c[0] + math.cos(a + 0.35) * 10, c[1] + math.sin(a + 0.35) * 10)
                    mid2 = (c[0] + math.cos(a - 0.35) * 10, c[1] + math.sin(a - 0.35) * 10)
                    pygame.draw.polygon(surf, (30, 92, 52), [c, mid, tip, mid2])
                    pygame.draw.polygon(surf, (58, 142, 74), [c, mid, tip])
                    pygame.draw.line(surf, (24, 70, 42), c, tip, 1)
                pygame.draw.circle(surf, (120, 84, 50), c, 3)
        elif kind == "barrel":
            pygame.draw.ellipse(surf, (60, 40, 26), (3, 7, T - 6, T - 6))
            pygame.draw.ellipse(surf, (140, 96, 58), (3, 3, T - 6, T - 6))
            pygame.draw.ellipse(surf, (92, 62, 38), (3, 3, T - 6, T - 6), 3)
            pygame.draw.ellipse(surf, (166, 120, 76), (9, 9, T - 18, T - 18))
            for i in range(-2, 3):
                x = T // 2 + i * 5
                pygame.draw.line(surf, (128, 88, 52), (x, 11), (x, T - 11), 1)
            pygame.draw.ellipse(surf, (70, 70, 76), (6, 6, T - 12, T - 12), 2)
            pygame.draw.circle(surf, (60, 40, 26), (T // 2, T // 2), 3)
    _tiles[kind] = surf
    return surf


def pick_obstacle(col, row, cols, rows, rnd):
    """Rocks and the odd palm ring the island; the cargo sits inland."""
    edge = col in (0, cols - 1) or row in (0, rows - 1)
    roll = rnd.random()
    if edge:
        return "palm" if roll < 0.2 else ("rock1" if roll < 0.6 else "rock2")
    if roll < 0.62:
        return "crate"
    return "barrel" if roll < 0.86 else ("rock1" if roll < 0.95 else "palm")


# ------------------------------------------------------------- landmarks
def draw_landmark(surface, kind, cx, cy):
    """Flat decals lying on the sand: they are clues, not obstacles."""
    sh = soft_shadow(30, 12, 50)
    surface.blit(sh, sh.get_rect(center=(cx, cy + 9)))
    if kind == "anchor":
        iron, dark = (92, 96, 108), (54, 52, 60)
        for col, w in ((dark, 6), (iron, 3)):
            pygame.draw.line(surface, col, (cx, cy - 10), (cx, cy + 11), w)
            pygame.draw.line(surface, col, (cx - 7, cy - 5), (cx + 7, cy - 5), w)
            pygame.draw.arc(surface, col, (cx - 12, cy - 6, 24, 19), math.pi, 2 * math.pi, w)
        pygame.draw.circle(surface, dark, (cx, cy - 12), 5, 3)
        pygame.draw.circle(surface, (168, 96, 60), (cx + 4, cy + 3), 2)
    elif kind == "skull":
        skull_and_bones(surface, cx, cy - 1, 0.55, bone=(246, 240, 224), ink=(70, 56, 44))
    elif kind == "starfish":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = 13 if i % 2 == 0 else 5.5
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        pygame.draw.polygon(surface, (120, 30, 30), [(x, y + 2) for x, y in pts])
        pygame.draw.polygon(surface, (224, 72, 60), pts)
        pygame.draw.polygon(surface, (150, 36, 34), pts, 2)
        for i in range(5):
            a = -math.pi / 2 + i * 2 * math.pi / 5
            pygame.draw.circle(surface, (255, 190, 160),
                               (int(cx + math.cos(a) * 6), int(cy + math.sin(a) * 6)), 1)
    else:  # wheel
        wood, dark = (150, 104, 60), (84, 54, 30)
        for i in range(8):
            a = i * math.pi / 4
            if i in (2, 3):
                continue                       # broken: two spokes missing
            end = (cx + math.cos(a) * 14, cy + math.sin(a) * 14)
            pygame.draw.line(surface, dark, (cx, cy), end, 4)
            pygame.draw.line(surface, wood, (cx, cy), end, 2)
        pygame.draw.arc(surface, dark, (cx - 11, cy - 11, 22, 22), 0.9 * math.pi, 2.45 * math.pi, 5)
        pygame.draw.arc(surface, wood, (cx - 10, cy - 10, 20, 20), 0.9 * math.pi, 2.45 * math.pi, 3)
        pygame.draw.circle(surface, dark, (cx, cy), 4)
        pygame.draw.circle(surface, (196, 150, 70), (cx, cy), 2)


def draw_hole(surface, cx, cy):
    pygame.draw.ellipse(surface, (196, 158, 100), (cx - 15, cy - 9, 30, 21))
    pygame.draw.ellipse(surface, (120, 86, 50), (cx - 12, cy - 7, 24, 16))
    pygame.draw.ellipse(surface, (84, 58, 34), (cx - 10, cy - 4, 20, 12))
    for dx, dy in ((-15, 6), (13, 7), (-4, 10)):
        pygame.draw.circle(surface, (212, 176, 118), (cx + dx, cy + dy), 4)


def draw_bottle(surface, cx, cy, t):
    bob = math.sin(t * 2.4) * 2
    sh = soft_shadow(24, 8, 60)
    surface.blit(sh, sh.get_rect(center=(cx, cy + 11)))
    body = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.rect(body, (40, 104, 84), (6, 9, 18, 13), border_radius=6)
    pygame.draw.rect(body, (86, 170, 140), (7, 10, 16, 11), border_radius=5)
    pygame.draw.rect(body, (40, 104, 84), (22, 12, 6, 7), border_radius=2)
    pygame.draw.rect(body, (150, 104, 60), (27, 13, 3, 5))
    pygame.draw.rect(body, (250, 240, 210), (10, 12, 9, 7), border_radius=2)   # the note
    pygame.draw.line(body, (200, 240, 226), (9, 11), (19, 11), 1)
    body = pygame.transform.rotate(body, 24 + math.sin(t * 1.3) * 5)
    surface.blit(body, body.get_rect(center=(cx, cy + bob)))
    if (t * 0.8) % 1.0 < 0.25:
        k = ((t * 0.8) % 1.0) / 0.25
        r = int(2 + 5 * math.sin(k * math.pi))
        x, y = cx - 6, int(cy - 7 + bob)
        pygame.draw.line(surface, (255, 255, 255), (x - r, y), (x + r, y), 1)
        pygame.draw.line(surface, (255, 255, 255), (x, y - r), (x, y + r), 1)


def draw_chest(surface, cx, cy, opened=1.0):
    """`opened` runs 0..1 as the lid swings up."""
    sh = soft_shadow(34, 10, 80)
    surface.blit(sh, sh.get_rect(center=(cx, cy + 13)))
    wood, dark, band = (140, 86, 44), (84, 48, 24), (226, 178, 60)
    box = pygame.Rect(cx - 14, cy - 2, 28, 15)
    lid_h = int(9 - 5 * opened)
    lid = pygame.Rect(cx - 14, cy - 2 - lid_h - int(7 * opened), 28, lid_h + 2)
    if opened > 0.3:
        pygame.draw.rect(surface, (60, 34, 16), (cx - 13, cy - 9, 26, 9))
        for i, dx in enumerate((-8, -3, 2, 7, -5, 4)):
            pygame.draw.circle(surface, GOLD_LIT if i % 2 else GOLD,
                               (cx + dx, cy - 4 - (i % 3)), 3)
    pygame.draw.rect(surface, dark, box.move(0, 2), border_radius=3)
    pygame.draw.rect(surface, wood, box, border_radius=3)
    pygame.draw.rect(surface, dark, box, 2, border_radius=3)
    pygame.draw.rect(surface, wood, lid, border_radius=4)
    pygame.draw.rect(surface, dark, lid, 2, border_radius=4)
    for dx in (-8, 8):
        pygame.draw.line(surface, band, (cx + dx, box.y), (cx + dx, box.bottom - 1), 2)
    pygame.draw.rect(surface, band, (cx - 3, cy, 6, 6), border_radius=1)
    pygame.draw.circle(surface, dark, (cx, cy + 3), 1)


def draw_crown(surface, cx, cy, t):
    bob = int(math.sin(t * 2.5) * 3)
    y = cy + bob
    glow = pygame.Surface((60, 60), pygame.SRCALPHA)
    a = int(50 + 30 * math.sin(t * 3))
    pygame.draw.circle(glow, (255, 230, 140, a), (30, 30), 26)
    pygame.draw.circle(glow, (255, 240, 180, a), (30, 30), 16)
    surface.blit(glow, (cx - 30, y - 30))
    pts = [(cx - 13, y + 8), (cx - 14, y - 7), (cx - 7, y), (cx, y - 11),
           (cx + 7, y), (cx + 14, y - 7), (cx + 13, y + 8)]
    pygame.draw.polygon(surface, GOLD_DEEP, [(x, yy + 2) for x, yy in pts])
    pygame.draw.polygon(surface, GOLD_LIT, pts)
    pygame.draw.polygon(surface, (110, 70, 8), pts, 2)
    pygame.draw.rect(surface, GOLD, (cx - 13, y + 3, 26, 5))
    for dx, col in ((-7, (210, 50, 60)), (0, (70, 190, 220)), (7, (90, 200, 110))):
        pygame.draw.circle(surface, col, (cx + dx, y + 5), 2)


RUNE_COLORS = {"sun": (240, 170, 50), "moon": (190, 204, 236),
               "star": (120, 220, 230), "skull": (226, 220, 200)}


def draw_rune_glyph(surface, rune, cx, cy, col, s=1.0):
    if rune == "sun":
        pygame.draw.circle(surface, col, (cx, cy), int(5 * s))
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(surface, col,
                             (cx + math.cos(a) * 7 * s, cy + math.sin(a) * 7 * s),
                             (cx + math.cos(a) * 11 * s, cy + math.sin(a) * 11 * s), 2)
    elif rune == "moon":
        pts = []
        for i in range(13):
            a = math.pi / 2 + i * math.pi / 12
            pts.append((cx + 3 * s + math.cos(a) * 10 * s, cy + math.sin(a) * 10 * s))
        for i in range(13):
            a = 3 * math.pi / 2 - i * math.pi / 12
            pts.append((cx + 3 * s + math.cos(a) * 5 * s, cy + math.sin(a) * 10 * s))
        pygame.draw.polygon(surface, col, pts)
    elif rune == "star":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = (11 if i % 2 == 0 else 4.5) * s
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        pygame.draw.polygon(surface, col, pts)
    else:
        pygame.draw.circle(surface, col, (cx, cy - int(2 * s)), int(8 * s))
        pygame.draw.rect(surface, col, (cx - int(5 * s), cy + int(2 * s), int(10 * s), int(7 * s)),
                         border_radius=2)
        for side in (-1, 1):
            pygame.draw.circle(surface, (30, 30, 34), (cx + side * int(3 * s), cy - int(2 * s)),
                               max(1, int(2 * s)))
        pygame.draw.line(surface, (30, 30, 34), (cx, cy + int(4 * s)), (cx, cy + int(8 * s)), 1)


def draw_rune_plate(surface, rune, cx, cy, state, t):
    """state: 'idle', 'lit' (correctly trodden) or 'bad' (flashing a mistake)."""
    stone, dark = (88, 96, 100), (44, 50, 54)
    pygame.draw.rect(surface, dark, (cx - 16, cy - 13, 32, 30), border_radius=7)
    pygame.draw.rect(surface, stone, (cx - 16, cy - 16, 32, 30), border_radius=7)
    pygame.draw.rect(surface, (120, 128, 130), (cx - 16, cy - 16, 32, 30), 2, border_radius=7)
    if state == "lit":
        col = RUNE_COLORS[rune]
        glow = pygame.Surface((56, 56), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, int(70 + 40 * math.sin(t * 5))), (28, 28), 24)
        surface.blit(glow, (cx - 28, cy - 29))
    elif state == "bad":
        col = (230, 60, 50)
    else:
        col = tuple(int(c * 0.55 + 30) for c in RUNE_COLORS[rune])
    draw_rune_glyph(surface, rune, cx, cy - 1, col)


def draw_vault_door(surface, x, y, t):
    pygame.draw.rect(surface, (30, 34, 40), (x, y + 4, T, T), border_radius=6)
    pygame.draw.rect(surface, (74, 82, 92), (x, y, T, T), border_radius=6)
    pygame.draw.rect(surface, (112, 122, 130), (x, y, T, T), 3, border_radius=6)
    for i in (1, 2, 3):
        pygame.draw.line(surface, (52, 58, 66), (x + i * 10, y + 4), (x + i * 10, y + T - 5), 2)
    col = (int(170 + 60 * math.sin(t * 3)), 210, 190)
    draw_rune_glyph(surface, "skull", x + T // 2, y + T // 2, col, 0.9)


def draw_tentacle(surface, cx, cy, rise, t, seed=0.0):
    """`rise` 0..1: how far out of the sand it has come."""
    hole = pygame.Rect(0, 0, 34, 16)
    hole.center = (cx, cy + 8)
    pygame.draw.ellipse(surface, (24, 46, 60), hole)
    pygame.draw.ellipse(surface, (236, 232, 214), hole, 2)
    if rise <= 0.02:
        return
    segs = 9
    length = 54 * rise
    prev = (cx, cy + 8)
    for i in range(1, segs + 1):
        k = i / segs
        sway = math.sin(t * 5 + seed + k * 3.2) * 10 * k
        p = (cx + sway, cy + 8 - length * k)
        w = int(13 * (1 - k * 0.72))
        pygame.draw.line(surface, (70, 22, 60), prev, p, w + 4)
        pygame.draw.line(surface, (156, 60, 110), prev, p, w)
        pygame.draw.circle(surface, (156, 60, 110), (int(p[0]), int(p[1])), w // 2)
        if i % 2 == 0 and w > 5:
            pygame.draw.circle(surface, (238, 186, 204), (int(p[0]) + 2, int(p[1])), 2)
        prev = p


def draw_fragment(surface, cx, cy, index, found, size=9):
    """One of the five torn pieces of the old map, as a HUD pip."""
    rnd = random.Random(index * 31 + 5)
    pts = [(cx - size + rnd.randint(0, 2), cy - size + rnd.randint(0, 3)),
           (cx + size - rnd.randint(0, 3), cy - size + rnd.randint(0, 2)),
           (cx + size - rnd.randint(0, 2), cy + size - rnd.randint(0, 3)),
           (cx + rnd.randint(-2, 2), cy + size - rnd.randint(0, 2)),
           (cx - size + rnd.randint(0, 3), cy + size - rnd.randint(0, 2))]
    if found:
        pygame.draw.polygon(surface, PARCHMENT_LIT, pts)
        pygame.draw.polygon(surface, PARCHMENT_BURN, pts, 2)
        a = rnd.uniform(0, 3)
        pygame.draw.line(surface, BLOOD, (cx - 3, cy - 3), (cx + 3, cy + 3), 2) if index == 4 else \
            pygame.draw.line(surface, (140, 100, 60),
                             (cx - 4 * math.cos(a), cy - 4 * math.sin(a)),
                             (cx + 4 * math.cos(a), cy + 4 * math.sin(a)), 1)
        if index == 4:
            pygame.draw.line(surface, BLOOD, (cx + 3, cy - 3), (cx - 3, cy + 3), 2)
    else:
        pygame.draw.polygon(surface, (196, 168, 116), pts)
        pygame.draw.polygon(surface, (160, 132, 90), pts, 1)


def draw_shovel(surface, cx, cy, lit=True):
    wood = (140, 96, 56) if lit else (176, 152, 116)
    iron = (120, 126, 138) if lit else (180, 168, 146)
    pygame.draw.line(surface, wood, (cx + 6, cy - 9), (cx - 3, cy + 2), 3)
    pygame.draw.line(surface, wood, (cx + 3, cy - 11), (cx + 9, cy - 7), 3)
    pygame.draw.polygon(surface, iron, [(cx - 1, cy), (cx - 5, cy + 4), (cx - 8, cy + 11),
                                        (cx - 1, cy + 8), (cx + 1, cy + 3)])


def lantern_light(like, dark, glow=(255, 236, 190), radius=150, size=(1800, 1100)):
    """A sheet of night with a pool of lantern light at its centre.

    Blitted with BLEND_RGB_MULT and slid about so the pool follows the pirate:
    one blit a frame, where a per-pixel alpha overlay would cost far more in
    WebAssembly."""
    # Built in the exact pixel format of the surface it will be multiplied
    # into. In the browser a resize can change the default format, and a
    # special-flag blit between two formats swaps red and blue: moonlight
    # came out pink.
    surf = pygame.Surface(size, 0, like)
    surf.fill(dark)
    cx, cy = size[0] // 2, size[1] // 2
    steps = 40
    for i in range(steps):
        k = i / (steps - 1)
        r = int(radius * (1 - k * 0.92))
        e = k ** 1.15
        col = tuple(int(dark[c] + (glow[c] - dark[c]) * e) for c in range(3))
        pygame.draw.circle(surf, col, (cx, cy), r)
    return surf
