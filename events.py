"""Random events: the storm, the kraken and the golden crab.

An EventDirector sits on each island and, after a quiet spell, springs one of
the events that island allows. Only one runs at a time and the same one never
strikes twice running, so an island plays differently on every visit.

The director talks to the game through a handful of hooks (announce, toast,
award, hurt-detection via `hazard_hit`) and never reaches into its internals
beyond the player, the sand tiles and the pathfinding field.
"""
import math
import random

import pygame

import art
import scoring
from sprites import TILE_SIZE, Puddle, GoldenCrab

T = TILE_SIZE


def center(tile):
    return tile[0] * T + T / 2, tile[1] * T + T / 2


class Storm:
    kind = "storm"
    DURATION = 15.0
    banner = "A STORM BREWS!"
    sub = "Coins are worth double while it rages"
    color = (60, 84, 130)

    def __init__(self, game):
        self.game = game
        self.t = 0.0
        self.wind = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.flipped = False
        self.surge = []            # [Puddle, state_time]
        self.surged = False
        self.bolt = random.uniform(1.2, 2.5)
        game.audio.loop(2, "rain")

    @property
    def strength(self):
        return max(0.0, min(1.0, self.t / 1.5, (self.DURATION - self.t) / 1.5))

    def wind_vector(self):
        k = 48 * self.strength
        return self.wind[0] * k, self.wind[1] * k

    def update(self, dt):
        g = self.game
        self.t += dt
        if not self.flipped and self.t > self.DURATION / 2:
            self.flipped = True
            self.wind = random.choice([w for w in [(1, 0), (-1, 0), (0, 1), (0, -1)]
                                       if w != self.wind])
            g.toast("The wind swings round!")
        if not self.surged and self.t > 2.5:
            self.surged = True
            ptile = g.player_tile()
            spots = [s for s in g.sand_tiles
                     if max(abs(s[0] - ptile[0]), abs(s[1] - ptile[1])) >= 3
                     and s not in g.reserved_tiles]
            random.shuffle(spots)
            for tile in spots[:3 + g.level_number // 2]:
                self.surge.append([Puddle(*tile), 0.0])
            g.toast("The tide surges over the sand!")
        for entry in self.surge:
            entry[0].update(dt)
            entry[1] += dt
        self.bolt -= dt
        if self.bolt <= 0 and self.t < self.DURATION - 1.5:
            self.bolt = random.uniform(2.6, 5.0)
            g.flash = 1.0
            g.shake.kick(4)
            g.audio.play("thunder")
        return self.t >= self.DURATION

    def surge_ready(self, entry):
        return entry[1] > 1.4 and self.t < self.DURATION - 1.0

    def hazard_hit(self, player):
        for entry in self.surge:
            p = entry[0]
            if self.surge_ready(entry) and math.hypot(p.x - player.x, p.y - player.y) \
                    < p.radius + player.radius * 0.8:
                return "splash"
        return None

    def draw_under(self, surface, ox, oy):
        for entry in self.surge:
            p, age = entry
            if self.surge_ready(entry):
                p.draw(surface, ox, oy)
            else:
                # Seeping in (or draining away): a damp patch that warns first.
                k = min(1.0, age / 1.4) if self.t < self.DURATION - 1.0 else 0.5
                r = int(6 + 11 * k)
                c = (int(p.x + ox), int(p.y + oy))
                pygame.draw.ellipse(surface, (190, 156, 108), (c[0] - r, c[1] - r * 0.7, r * 2, r * 1.4))
                pygame.draw.ellipse(surface, (96, 150, 176), (c[0] - r, c[1] - r * 0.7, r * 2, r * 1.4), 2)

    def draw_over(self, surface, ox, oy):
        pass

    def end(self):
        self.game.audio.loop(2, None)
        self.game.toast("The storm blows itself out.")


class Kraken:
    kind = "kraken"
    DURATION = 12.0
    banner = "THE KRAKEN STIRS!"
    sub = "Watch the sand - stay off the dark holes"
    color = (110, 36, 90)

    WARN, UP, DOWN = 1.0, 1.1, 0.3

    def __init__(self, game):
        self.game = game
        self.t = 0.0
        self.spawn = 0.6
        self.arms = []             # [tile, age, seed]
        self.touched = False
        game.audio.play("kraken")
        game.shake.kick(5)

    def wind_vector(self):
        return 0, 0

    def update(self, dt):
        g = self.game
        self.t += dt
        self.spawn -= dt
        if self.spawn <= 0 and self.t < self.DURATION - 2.4:
            self.spawn = max(0.55, 1.0 - g.level_number * 0.06)
            ptile = g.player_tile()
            busy = {a[0] for a in self.arms}
            near = [s for s in g.walk_tiles
                    if max(abs(s[0] - ptile[0]), abs(s[1] - ptile[1])) <= 3 and s not in busy]
            if near:
                tile = ptile if (random.random() < 0.35 and ptile not in busy) \
                    else random.choice(near)
                self.arms.append([tile, 0.0, random.uniform(0, 6)])
        for arm in self.arms:
            before = arm[1]
            arm[1] += dt
            if before < self.WARN <= arm[1]:
                g.audio.play("tentacle")
                x, y = center(arm[0])
                g.particles.burst(x, y, (214, 180, 124), 8, 80, 0.4)
        self.arms = [a for a in self.arms if a[1] < self.WARN + self.UP + self.DOWN]
        return self.t >= self.DURATION and not self.arms

    def rise(self, age):
        if age < self.WARN:
            return 0.0
        if age < self.WARN + self.UP:
            return min(1.0, (age - self.WARN) / 0.15)
        return max(0.0, 1.0 - (age - self.WARN - self.UP) / self.DOWN)

    def hazard_hit(self, player):
        for tile, age, _ in self.arms:
            if self.WARN + 0.08 < age < self.WARN + self.UP:
                x, y = center(tile)
                if math.hypot(x - player.x, y - player.y) < 15 + player.radius * 0.8:
                    self.touched = True
                    return "hit"
        return None

    def draw_under(self, surface, ox, oy):
        for tile, age, seed in self.arms:
            if age < self.WARN:
                x, y = center(tile)
                k = age / self.WARN
                r = int(7 + 10 * k)
                c = (int(x + ox), int(y + oy + 8))
                pygame.draw.ellipse(surface, (40, 62, 76), (c[0] - r, c[1] - r // 2, r * 2, r))
                for i in range(3):       # bubbles
                    a = seed + i * 2.1 + age * 6
                    pygame.draw.circle(surface, (226, 236, 232),
                                       (int(c[0] + math.cos(a) * r * 0.5),
                                        int(c[1] + math.sin(a) * r * 0.25)), 2, 1)

    def draw_over(self, surface, ox, oy):
        for tile, age, seed in sorted(self.arms, key=lambda a: a[0][1]):
            if age >= self.WARN:
                x, y = center(tile)
                art.draw_tentacle(surface, int(x + ox), int(y + oy), self.rise(age),
                                  self.t, seed)

    def end(self):
        g = self.game
        if self.touched:
            g.toast("The kraken sinks back, satisfied.")
        else:
            g.award("events", scoring.KRAKEN_BONUS, "Outwitted the kraken!", sound="gold")


class GoldRush:
    kind = "gold"
    DURATION = 16.0
    banner = "A GOLDEN CRAB SCUTTLES ASHORE!"
    sub = "Catch it before it burrows away"
    color = (176, 122, 20)

    def __init__(self, game):
        self.game = game
        self.t = 0.0
        self.caught = False
        field = game.dist
        best = max(game.sand_tiles, key=lambda s: (field.get(s, 0), random.random()))
        self.crab = GoldenCrab(*best)
        game.audio.play("gold")

    def wind_vector(self):
        return 0, 0

    def update(self, dt):
        g = self.game
        self.t += dt
        self.crab.update_flee(dt, g.player, g.wall_rects, g.bounds, g.dist)
        if random.random() < dt * 14:
            g.particles.burst(self.crab.x, self.crab.y, art.GOLD_LIT, 1, 30, 0.5, 2, 0)
        if math.hypot(self.crab.x - g.player.x, self.crab.y - g.player.y) \
                < self.crab.radius + g.player.radius + 3:
            self.caught = True
            g.particles.burst(self.crab.x, self.crab.y, art.GOLD, 26, 170, 0.8, 4,
                              colors=[art.GOLD, art.GOLD_LIT, (255, 255, 230)])
            g.award("events", scoring.GOLD_CRAB_VALUE, "Golden crab!", sound="gold",
                    at=(self.crab.x, self.crab.y))
            return True
        return self.t >= self.DURATION

    def hazard_hit(self, player):
        return None

    def draw_under(self, surface, ox, oy):
        pass

    def draw_over(self, surface, ox, oy):
        left = self.DURATION - self.t
        if left > 2.5 or int(left * 8) % 2:
            self.crab.draw(surface, ox, oy)

    def end(self):
        if not self.caught:
            g = self.game
            g.particles.burst(self.crab.x, self.crab.y, (214, 180, 124), 14, 90, 0.5)
            g.toast("The golden crab burrows out of sight.")


EVENTS = {"storm": Storm, "kraken": Kraken, "gold": GoldRush}


class EventDirector:
    def __init__(self, game, pool):
        self.game = game
        self.pool = list(pool)
        self.active = None
        self.last = None
        self.timer = random.uniform(13, 20)
        self.count = 0

    @property
    def storm(self):
        return self.active is not None and self.active.kind == "storm"

    def storm_strength(self):
        return self.active.strength if self.storm else 0.0

    def wind_vector(self):
        return self.active.wind_vector() if self.active else (0, 0)

    def start(self, kind):
        self.stop()
        self.active = EVENTS[kind](self.game)
        self.last = kind
        self.count += 1
        self.game.announce(self.active.banner, self.active.sub, self.active.color)

    def stop(self):
        if self.active:
            self.active.end()
            self.active = None

    def update(self, dt):
        if self.active:
            if self.active.update(dt):
                self.stop()
                self.timer = random.uniform(18, 30)
            return
        if not self.pool:
            return
        self.timer -= dt
        if self.timer <= 0:
            choices = [k for k in self.pool if k != self.last] or self.pool
            # The first event on an island is the one listed first: islands
            # introduce the storm, the crab and the kraken in a sensible order.
            self.start(self.pool[0] if self.count == 0 else random.choice(choices))

    def hazard_hit(self, player):
        return self.active.hazard_hit(player) if self.active else None

    def draw_under(self, surface, ox, oy):
        if self.active:
            self.active.draw_under(surface, ox, oy)

    def draw_over(self, surface, ox, oy):
        if self.active:
            self.active.draw_over(surface, ox, oy)
