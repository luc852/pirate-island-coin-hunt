"""Transient effects: particles, floating score text, the living sea, rain.

Everything is drawn straight onto an opaque surface with plain shapes. Alpha
compositing is the expensive thing in the WebAssembly build, so the only alpha
here is on small pre-rendered text.
"""
import math
import random

import pygame

MAX_PARTICLES = 220


class Particles:
    def __init__(self):
        self.items = []     # [x, y, vx, vy, life, max_life, radius, color, gravity]
        self.texts = []     # [surface, x, y, life, max_life]

    def clear(self):
        self.items.clear()
        self.texts.clear()

    def burst(self, x, y, color, count=10, speed=90, life=0.5, radius=3, gravity=160,
              colors=None):
        for _ in range(count):
            if len(self.items) >= MAX_PARTICLES:
                break
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(0.3, 1.0) * speed
            col = random.choice(colors) if colors else color
            self.items.append([x, y, math.cos(a) * v, math.sin(a) * v - speed * 0.3,
                               life * random.uniform(0.6, 1.0), life,
                               random.uniform(0.6, 1.0) * radius, col, gravity])

    def puff(self, x, y, color=(214, 180, 124)):
        if len(self.items) < MAX_PARTICLES:
            self.items.append([x + random.uniform(-4, 4), y, random.uniform(-12, 12),
                               random.uniform(-18, -6), 0.35, 0.35, 3, color, 0])

    def text(self, surface, x, y, life=0.9):
        self.texts.append([surface, x, y, life, life])

    def update(self, dt):
        for p in self.items:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += p[8] * dt
            p[4] -= dt
        self.items = [p for p in self.items if p[4] > 0]
        for t in self.texts:
            t[2] -= 34 * dt
            t[3] -= dt
        self.texts = [t for t in self.texts if t[3] > 0]

    def draw(self, surface, ox, oy):
        for x, y, _, _, life, max_life, radius, color, _ in self.items:
            r = max(1, int(radius * (life / max_life) + 0.5))
            pygame.draw.circle(surface, color, (int(x + ox), int(y + oy)), r)
        for surf, x, y, life, max_life in self.texts:
            k = life / max_life
            if k < 0.35:
                surf.set_alpha(int(255 * k / 0.35))
            else:
                surf.set_alpha(255)
            pop = 1.0 - k
            dy = -6 * math.sin(min(1.0, pop * 5) * math.pi / 2)
            surface.blit(surf, surf.get_rect(center=(int(x + ox), int(y + oy + dy))))


class Sea:
    """Wave glints sliding over the baked gradient, and gulls overhead."""

    def __init__(self, width, height, count=46, seed=3):
        self.w, self.h = width, height
        rnd = random.Random(seed)
        self.glints = [[rnd.uniform(0, width), rnd.uniform(0, height),
                        rnd.uniform(10, 26), rnd.uniform(6, 16), rnd.uniform(0, 6.28)]
                       for _ in range(count)]
        self.gulls = []
        self.gull_timer = rnd.uniform(3, 7)
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        for g in self.glints:
            g[0] += g[3] * dt
            if g[0] > self.w + 30:
                g[0] = -30
        self.gull_timer -= dt
        if self.gull_timer <= 0:
            self.gull_timer = random.uniform(7, 15)
            left = random.random() < 0.5
            self.gulls.append([-30 if left else self.w + 30, random.uniform(90, self.h - 120),
                               (1 if left else -1) * random.uniform(70, 110),
                               random.uniform(-10, 10), random.uniform(0, 6)])
        for g in self.gulls:
            g[0] += g[2] * dt
            g[1] += g[3] * dt
        self.gulls = [g for g in self.gulls if -60 < g[0] < self.w + 60]

    def draw_glints(self, surface, color, top=0):
        for x, y, length, _, phase in self.glints:
            if y < top:
                continue
            k = 0.5 + 0.5 * math.sin(self.t * 1.3 + phase)
            if k < 0.25:
                continue
            half = length * k / 2
            yy = y + math.sin(self.t * 0.9 + phase) * 3
            pygame.draw.line(surface, color, (x - half, yy), (x + half, yy), 2 if k > 0.7 else 1)

    def draw_gulls(self, surface, color=(250, 250, 246), shade=(60, 60, 70)):
        for x, y, vx, _, phase in self.gulls:
            flap = math.sin(self.t * 9 + phase) * 6
            for col, dy in ((shade, 2), (color, 0)):
                pygame.draw.lines(surface, col, False,
                                  [(x - 11, y - flap + dy), (x - 4, y - 2 + dy), (x, y + 1 + dy),
                                   (x + 4, y - 2 + dy), (x + 11, y - flap + dy)], 2)


class Rain:
    def __init__(self, width, height, count=70):
        self.w, self.h = width, height
        self.drops = [[random.uniform(0, width), random.uniform(0, height),
                       random.uniform(520, 760)] for _ in range(count)]

    def update(self, dt, wind):
        for d in self.drops:
            d[1] += d[2] * dt
            d[0] += wind * 3.2 * dt
            if d[1] > self.h:
                d[1] = random.uniform(-40, 0)
                d[0] = random.uniform(-40, self.w + 40)

    def draw(self, surface, wind, strength=1.0):
        n = int(len(self.drops) * strength)
        lean = wind * 0.05
        for x, y, _ in self.drops[:n]:
            pygame.draw.line(surface, (190, 208, 228), (x, y), (x - lean, y - 13), 1)


class Shake:
    def __init__(self):
        self.amount = 0.0

    def kick(self, amount):
        self.amount = max(self.amount, amount)

    def update(self, dt):
        self.amount = max(0.0, self.amount - 28 * dt)

    def offset(self):
        if self.amount <= 0.3:
            return 0, 0
        return (int(random.uniform(-1, 1) * self.amount),
                int(random.uniform(-1, 1) * self.amount))
