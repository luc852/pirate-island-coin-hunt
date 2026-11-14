"""Game entities and their (mostly hand-drawn, CC0-safe) visuals.

The gold coin sprite is a real Kenney.nl (CC0) asset loaded from
assets/images/. Everything else (pirate, monsters, puddles, walls, sand,
hearts) is drawn procedurally with soft rounded pygame shapes in a bright,
kid-friendly palette, per the project's asset fallback rule.
"""
import math
import random
import os
import pygame

TILE_SIZE = 40

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "images")

SAND = (237, 201, 138)
SAND_DARK = (223, 184, 115)
SAND_DAMP = (207, 169, 113)

# Crates keep the old three-part construction but are lit from a single
# direction now: warm top, cooler bottom, hard drop underneath.
WALL_TOP = (138, 102, 71)
WALL_BOTTOM = (110, 80, 55)
WALL_DROP = (78, 54, 37)
WALL_FACE_TOP = (156, 120, 86)
WALL_FACE_BOTTOM = (130, 96, 63)
WALL_HILIGHT = (255, 232, 200)

# Tide pools used to be drawn in almost exactly the sea's blue, so a hazard
# read as scenery. Much darker water, foam rim, damp sand lip.
POOL_RIM = (20, 80, 110)
POOL_FILL = (30, 110, 150)
POOL_FOAM = (243, 235, 218)
POOL_SHINE = (79, 160, 196)

HEART_FILL = (226, 75, 84)
HEART_SHADE = (168, 37, 48)
HEART_EMPTY = (217, 204, 194)
HEART_EMPTY_SHADE = (185, 169, 156)

SKIN = (255, 214, 170)
COAT = (196, 74, 58)
COAT_DARK = (158, 53, 39)
BANDANA = (200, 40, 40)
BANDANA_DARK = (168, 31, 31)
CREAM = (255, 246, 226)

MONSTER_COLORS = [
    (110, 201, 120),   # green
    (154, 110, 214),   # purple
    (240, 150, 70),    # orange
    (90, 170, 230),    # blue
    (230, 90, 90),     # red
]


def vertical_gradient(width, height, stops):
    """A vertical gradient surface. `stops` is [(pos 0..1, color), ...]."""
    surf = pygame.Surface((width, height))
    stops = sorted(stops)
    for y in range(height):
        t = y / max(1, height - 1)
        lo = stops[0]
        hi = stops[-1]
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                lo, hi = stops[i], stops[i + 1]
                break
        span = hi[0] - lo[0]
        k = 0.0 if span <= 0 else (t - lo[0]) / span
        col = tuple(round(lo[1][c] + (hi[1][c] - lo[1][c]) * k) for c in range(3))
        pygame.draw.line(surf, col, (0, y), (width, y))
    return surf


def _rounded_gradient(width, height, top, bottom, radius):
    """A vertical gradient clipped to a rounded rectangle."""
    grad = vertical_gradient(width, height, [(0.0, top), (1.0, bottom)]).convert_alpha()
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, width, height), border_radius=radius)
    # BLEND_RGBA_MIN keeps the gradient inside the mask and zeroes the alpha
    # outside it, which is how we get a rounded gradient without per-pixel work.
    grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return grad


_crate_tile = None


def crate_tile():
    """One pre-rendered crate, reused by every wall (built once, on demand)."""
    global _crate_tile
    if _crate_tile is None:
        t = TILE_SIZE
        surf = pygame.Surface((t, t + 4), pygame.SRCALPHA)
        pygame.draw.rect(surf, WALL_DROP, (0, 4, t, t), border_radius=11)
        surf.blit(_rounded_gradient(t, t, WALL_TOP, WALL_BOTTOM, 11), (0, 0))
        highlight = pygame.Surface((t, t), pygame.SRCALPHA)
        pygame.draw.rect(highlight, (*WALL_HILIGHT, 56), (0, 0, t, t), 2, border_radius=11)
        surf.blit(highlight, (0, 0))
        inner = _rounded_gradient(26, 26, WALL_FACE_TOP, WALL_FACE_BOTTOM, 8)
        pygame.draw.line(inner, (*WALL_HILIGHT, 70), (8, 1), (18, 1), 2)
        surf.blit(inner, (7, 7))
        _crate_tile = surf
    return _crate_tile


_shadow_cache = {}


def soft_shadow(width, height, alpha=64):
    """Cached translucent blob. pygame.draw ignores alpha on an opaque surface,
    so contact shadows have to be composited from their own surface."""
    key = (width, height, alpha)
    surf = _shadow_cache.get(key)
    if surf is None:
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (46, 28, 14, alpha), (0, 0, width, height))
        _shadow_cache[key] = surf
    return surf


def load_coin_frames():
    frames = []
    for name in ("coin_01.png", "coin_02.png"):
        path = os.path.join(ASSETS_DIR, name)
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (int(TILE_SIZE * 0.7), int(TILE_SIZE * 0.7)))
        frames.append(img)
    return frames


class Wall:
    def __init__(self, col, row):
        self.rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def draw(self, surface, ox, oy):
        surface.blit(crate_tile(), (self.rect.x + ox, self.rect.y + oy))


ISLAND_RADIUS = 20


def draw_sand_background(width, height, cols, rows, ox, oy, seed=0):
    """The island: a rounded landmass with a damp shoreline, not a hard rectangle."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(surf, SAND, (0, 0, width, height), border_radius=ISLAND_RADIUS)

    rnd = random.Random(seed)
    for _ in range((cols * rows) // 3):
        x = rnd.randint(0, width - 1)
        y = rnd.randint(0, height - 1)
        r = rnd.randint(2, 4)
        pygame.draw.circle(surf, SAND_DARK, (x, y), r)

    # Sand darkens toward the waterline. Concentric outlines with falling alpha
    # stand in for an inset shadow; pygame.draw ignores alpha, so it is composited
    # from its own surface.
    damp = pygame.Surface((width, height), pygame.SRCALPHA)
    for i in range(14):
        a = int(74 * (1 - i / 14))
        pygame.draw.rect(damp, (*SAND_DAMP, a), (i, i, width - 2 * i, height - 2 * i),
                         1, border_radius=max(1, ISLAND_RADIUS - i))
    surf.blit(damp, (0, 0))

    # Trim speckles and damp band back to the rounded silhouette.
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, width, height), border_radius=ISLAND_RADIUS)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return surf


def draw_shoreline(surface, rect):
    """Foam where the sea meets the island."""
    foam = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(foam, (255, 255, 255, 38), rect.inflate(22, 22), border_radius=ISLAND_RADIUS + 11)
    pygame.draw.rect(foam, (255, 255, 255, 86), rect.inflate(10, 10), border_radius=ISLAND_RADIUS + 5)
    surface.blit(foam, (0, 0))


class Coin:
    def __init__(self, col, row, frames):
        self.col, self.row = col, row
        self.x = col * TILE_SIZE + TILE_SIZE / 2
        self.y = row * TILE_SIZE + TILE_SIZE / 2
        self.frames = frames
        self.anim_t = random.random() * 10
        self.collected = False
        self.radius = TILE_SIZE * 0.3

    def update(self, dt):
        self.anim_t += dt

    def draw(self, surface, ox, oy):
        if self.collected:
            return
        bob = math.sin(self.anim_t * 4) * 3
        frame = self.frames[int(self.anim_t * 3) % len(self.frames)]
        rect = frame.get_rect(center=(self.x + ox, self.y + oy + bob))
        surface.blit(frame, rect)


class Puddle:
    def __init__(self, col, row):
        self.col, self.row = col, row
        self.x = col * TILE_SIZE + TILE_SIZE / 2
        self.y = row * TILE_SIZE + TILE_SIZE / 2
        self.radius = TILE_SIZE * 0.38
        self.t = random.random() * 10

    def update(self, dt):
        self.t += dt

    def draw(self, surface, ox, oy):
        cx, cy = int(self.x + ox), int(self.y + oy)

        def oval(color, rx, ry, dx=0, dy=0):
            pygame.draw.ellipse(surface, color, (cx - rx + dx, cy - ry + dy, rx * 2, ry * 2))

        oval(SAND_DAMP, 17, 12, dy=1)      # damp lip, so it reads as a hole in the beach
        oval(POOL_FOAM, 16, 11)
        oval(POOL_RIM, 14, 9)
        oval(POOL_FILL, 12, 7, dy=1)
        oval(POOL_SHINE, 4, 2, dx=-4, dy=-3)

        ripple_r = (math.sin(self.t * 2) * 0.5 + 0.5) * 3 + 5
        ripple = pygame.Rect(0, 0, int(ripple_r * 2), int(ripple_r * 1.3))
        ripple.center = (cx + 2, cy + 1)
        pygame.draw.ellipse(surface, (74, 148, 184), ripple, 1)


# How far sideways we look for the opening the player is trying to turn into.
TURN_ASSIST_REACH = TILE_SIZE * 0.6
# Sideways slide speed while lining up for a turn, relative to walking speed.
TURN_ASSIST_SPEED = 1.6


class Player:
    def __init__(self, col, row):
        self.x = col * TILE_SIZE + TILE_SIZE / 2
        self.y = row * TILE_SIZE + TILE_SIZE / 2
        self.radius = TILE_SIZE * 0.34
        self.speed = 190
        self.facing = (0, 1)
        self.invincible_t = 0.0
        self.walk_t = 0.0
        self.moving = False

    @property
    def rect_hitbox(self):
        r = self.radius
        return pygame.Rect(self.x - r, self.y - r, r * 2, r * 2)

    def _is_free(self, x, y, wall_rects, bounds):
        r = self.radius
        hitbox = pygame.Rect(x - r, y - r, r * 2, r * 2)
        return bounds.contains(hitbox) and not any(hitbox.colliderect(w) for w in wall_rects)

    def _step(self, dx, dy, wall_rects, bounds):
        """Move one axis if the destination is clear. Returns True if we moved."""
        if dx == 0 and dy == 0:
            return False
        if self._is_free(self.x + dx, self.y + dy, wall_rects, bounds):
            self.x += dx
            self.y += dy
            return True
        return False

    def try_move(self, dx, dy, wall_rects, bounds):
        self._step(dx, 0, wall_rects, bounds)
        self._step(0, dy, wall_rects, bounds)

    def _turn_assist(self, dirx, diry, step, wall_rects, bounds):
        """Ease sideways into a nearby opening when a turn is blocked.

        Standing a few pixels off-lane shouldn't stop the player from turning
        down a corridor, so when the requested direction is blocked we look at
        the lane centres within reach, pick the nearest one the turn actually
        opens up from, and slide toward it. Returns True if we slid.
        """
        horizontal = dirx != 0
        pos = self.y if horizontal else self.x
        base = math.floor(pos / TILE_SIZE)
        lanes = sorted(((base + off + 0.5) * TILE_SIZE for off in (-1, 0, 1)),
                       key=lambda c: abs(c - pos))
        probe = max(step, 4.0)
        for lane in lanes:
            offset = lane - pos
            if abs(offset) < 0.5 or abs(offset) > TURN_ASSIST_REACH:
                continue
            slide = math.copysign(min(step * TURN_ASSIST_SPEED, abs(offset)), offset)
            if horizontal:
                ahead = (self.x + dirx * probe, lane)
                nudged = (self.x, self.y + slide)
            else:
                ahead = (lane, self.y + diry * probe)
                nudged = (self.x + slide, self.y)
            if not self._is_free(*ahead, wall_rects, bounds):
                continue
            if not self._is_free(*nudged, wall_rects, bounds):
                continue
            self.x, self.y = nudged
            return True
        return False

    def update(self, dt, keys, wall_rects, bounds):
        dx = dy = 0
        if keys["left"]:
            dx -= 1
        if keys["right"]:
            dx += 1
        if keys["up"]:
            dy -= 1
        if keys["down"]:
            dy += 1
        self.moving = dx != 0 or dy != 0
        if dx or dy:
            length = math.hypot(dx, dy)
            ndx, ndy = dx / length, dy / length
            self.facing = (ndx, ndy)
            step = self.speed * dt

            # A blocked turn gets first claim on this frame: we slide into the
            # opening instead of advancing, so the turn lands immediately.
            assisted = None
            if dy and not self._is_free(self.x, self.y + ndy * step, wall_rects, bounds):
                if self._turn_assist(0, dy, step, wall_rects, bounds):
                    assisted = "x"
            if assisted is None and dx and not self._is_free(self.x + ndx * step, self.y,
                                                             wall_rects, bounds):
                if self._turn_assist(dx, 0, step, wall_rects, bounds):
                    assisted = "y"

            if assisted != "x":
                self._step(ndx * step, 0, wall_rects, bounds)
            if assisted != "y":
                self._step(0, ndy * step, wall_rects, bounds)
            self.walk_t += dt
        if self.invincible_t > 0:
            self.invincible_t = max(0.0, self.invincible_t - dt)

    def push(self, dx, dy, wall_rects, bounds):
        """Shoved by something other than the player's own feet (the wind)."""
        self._step(dx, 0, wall_rects, bounds)
        self._step(0, dy, wall_rects, bounds)

    def start_invincibility(self, duration=1.6):
        self.invincible_t = duration

    @property
    def is_invincible(self):
        return self.invincible_t > 0

    def draw(self, surface, ox, oy):
        if self.is_invincible and int(self.invincible_t * 10) % 2 == 0:
            return  # flicker while invincible
        cx, cy = int(self.x + ox), int(self.y + oy)
        bob = int(math.sin(self.walk_t * 10) * 1.5) if self.moving else 0
        fx, fy = self.facing

        shadow = soft_shadow(26, 8)
        surface.blit(shadow, shadow.get_rect(center=(cx, cy + 15)))

        body_y = cy + 6 + bob
        head_y = cy - 4 + bob
        band_y = cy - 8 + bob     # a cap on the skull, so the face keeps its room

        def silhouette(grow, color):
            pygame.draw.circle(surface, color, (cx, body_y), 10 + grow)
            pygame.draw.circle(surface, color, (cx, head_y), 10 + grow)
            pygame.draw.circle(surface, color, (cx, band_y), 10 + grow,
                               draw_top_left=True, draw_top_right=True)
            pygame.draw.polygon(surface, color, [
                (cx + 8, band_y - grow), (cx + 15 + grow, band_y - 4),
                (cx + 14, band_y + 4 + grow)])

        # Traced outline rather than a fixed ring: dark reads on sand, cream
        # reads on crates, so he pops against either.
        silhouette(4, (46, 28, 14))
        silhouette(2, CREAM)

        pygame.draw.circle(surface, COAT_DARK, (cx, body_y + 2), 10)
        pygame.draw.circle(surface, COAT, (cx, body_y), 10)

        pygame.draw.circle(surface, SKIN, (cx, head_y), 10)
        pygame.draw.polygon(surface, BANDANA, [
            (cx + 8, band_y), (cx + 15, band_y - 4), (cx + 14, band_y + 4)])
        pygame.draw.circle(surface, BANDANA, (cx, band_y), 10,
                           draw_top_left=True, draw_top_right=True)
        pygame.draw.line(surface, BANDANA_DARK, (cx - 10, band_y), (cx + 10, band_y), 2)

        # Eyepatch: the piece that makes his outline unmistakable.
        ex, ey = int(fx * 1.5), int(fy * 1.5)
        pygame.draw.line(surface, (36, 24, 20), (cx - 9, band_y + 1), (cx - 2, cy - 2), 1)
        pygame.draw.circle(surface, (36, 24, 20), (cx - 4, cy - 1), 3)
        pygame.draw.circle(surface, (36, 24, 20), (cx + 4 + ex, cy - 1 + ey), 2)
        pygame.draw.arc(surface, (120, 80, 55), (cx - 4, cy, 9, 6),
                        math.pi * 1.15, math.pi * 1.85, 2)


class Monster:
    def __init__(self, col, row, color, speed, mode):
        self.x = col * TILE_SIZE + TILE_SIZE / 2
        self.y = row * TILE_SIZE + TILE_SIZE / 2
        self.radius = TILE_SIZE * 0.32
        self.color = color
        self.base_speed = speed
        self.mode = mode  # 'wander' | 'mix' | 'chase'
        self.dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.dir_timer = random.uniform(0.5, 1.5)
        self.chase_timer = random.uniform(2.0, 4.0)
        self.chasing = False
        self.bob_t = random.random() * 10

    def _blocked(self, nx, ny, wall_rects, bounds):
        r = self.radius
        hitbox = pygame.Rect(nx - r, ny - r, r * 2, r * 2)
        if not bounds.contains(hitbox):
            return True
        return any(hitbox.colliderect(w) for w in wall_rects)

    def _try_axis_move(self, dx, dy, wall_rects, bounds):
        moved = False
        if dx != 0:
            nx = self.x + dx
            if not self._blocked(nx, self.y, wall_rects, bounds):
                self.x = nx
                moved = True
        if dy != 0:
            ny = self.y + dy
            if not self._blocked(self.x, ny, wall_rects, bounds):
                self.y = ny
                moved = True
        return moved

    def _seek(self, tx, ty, step, wall_rects, bounds):
        """Walk toward a point, each axis on its own so corners slide."""
        dx = max(-step, min(step, tx - self.x))
        dy = max(-step, min(step, ty - self.y))
        return self._try_axis_move(dx, dy, wall_rects, bounds)

    def _next_tile(self, dist, toward=True):
        """The neighbouring tile one step nearer the player (or one step
        further, for something running away), read off the distance field."""
        tile = (int(self.x // TILE_SIZE), int(self.y // TILE_SIZE))
        here = dist.get(tile)
        if here is None:
            return None
        best, best_d = None, here
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (tile[0] + ox, tile[1] + oy)
            d = dist.get(n)
            if d is None:
                continue
            if (d < best_d) if toward else (d > best_d):
                best, best_d = n, d
        return best

    def update(self, dt, player, wall_rects, bounds, dist=None):
        self.bob_t += dt

        if self.mode == "chase":
            self.chasing = True
        elif self.mode == "mix":
            self.chase_timer -= dt
            if self.chase_timer <= 0:
                self.chasing = not self.chasing
                self.chase_timer = random.uniform(2.5, 4.5) if self.chasing else random.uniform(2.0, 3.5)
        else:
            self.chasing = False

        speed = self.base_speed * (0.55 if (self.mode == "mix" and self.chasing) else 1.0)

        if self.chasing:
            # Follow the maze rather than the compass. The old straight-line
            # chase pressed crabs into the nearest wall and left them there.
            nxt = self._next_tile(dist) if dist else None
            if nxt is not None:
                tx = nxt[0] * TILE_SIZE + TILE_SIZE / 2
                ty = nxt[1] * TILE_SIZE + TILE_SIZE / 2
            else:
                tx, ty = player.x, player.y
            moved = self._seek(tx, ty, speed * dt, wall_rects, bounds)
            if not moved:
                # fall back to wander-style random step to get unstuck
                self.dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                self._try_axis_move(self.dir[0] * speed * dt, self.dir[1] * speed * dt, wall_rects, bounds)
        else:
            self.dir_timer -= dt
            if self.dir_timer <= 0:
                self.dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                self.dir_timer = random.uniform(0.6, 1.8)
            moved = self._try_axis_move(self.dir[0] * speed * dt, self.dir[1] * speed * dt, wall_rects, bounds)
            if not moved:
                self.dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                self.dir_timer = random.uniform(0.3, 0.9)

    def draw(self, surface, ox, oy):
        """A crab. The old blob shared the player's round outline, which is why
        the two blurred together at speed; claws and eye stalks break it up."""
        cx, cy = int(self.x + ox), int(self.y + oy)
        bob = int(math.sin(self.bob_t * 6) * 2)
        dark = tuple(max(0, c - 40) for c in self.color)
        light = tuple(min(255, c + 34) for c in self.color)

        shadow = soft_shadow(26, 7)
        surface.blit(shadow, shadow.get_rect(center=(cx, cy + 12)))

        for side in (-1, 1):
            pygame.draw.line(surface, dark, (cx + side * 10, cy + 4 + bob),
                             (cx + side * 16, cy + 8 + bob), 2)
            pygame.draw.line(surface, dark, (cx + side * 10, cy + 7 + bob),
                             (cx + side * 14, cy + 12 + bob), 2)
            claw = (cx + side * 11, cy - 1 + bob)
            pygame.draw.circle(surface, light, claw, 5)
            pygame.draw.circle(surface, dark, claw, 5, 1)
            pygame.draw.line(surface, dark, claw,
                             (claw[0] + side * 5, claw[1] - 2), 2)

        pygame.draw.ellipse(surface, dark, (cx - 11, cy - 5 + bob, 22, 18))
        pygame.draw.ellipse(surface, self.color, (cx - 11, cy - 7 + bob, 22, 18))
        pygame.draw.arc(surface, light, (cx - 9, cy - 8 + bob, 18, 12),
                        math.pi * 0.15, math.pi * 0.85, 2)

        for side in (-1, 1):
            sx = cx + side * 5
            pygame.draw.line(surface, dark, (sx, cy - 6 + bob), (sx, cy - 10 + bob), 2)
            pygame.draw.circle(surface, (255, 255, 255), (sx, cy - 12 + bob), 4)
            pygame.draw.circle(surface, (20, 20, 20), (sx, cy - 12 + bob), 2)


class GoldenCrab(Monster):
    """Harmless, valuable, and it runs. Catching it is the point."""

    def __init__(self, col, row):
        super().__init__(col, row, (236, 186, 52), 150, "flee")

    def update_flee(self, dt, player, wall_rects, bounds, dist):
        self.bob_t += dt
        step = self.base_speed * dt
        near = math.hypot(player.x - self.x, player.y - self.y) < TILE_SIZE * 7
        nxt = self._next_tile(dist, toward=False) if near else None
        if nxt is not None:
            self._seek(nxt[0] * TILE_SIZE + TILE_SIZE / 2,
                       nxt[1] * TILE_SIZE + TILE_SIZE / 2, step, wall_rects, bounds)
            return
        # Nowhere further to run, or not yet spooked: amble.
        self.dir_timer -= dt
        if self.dir_timer <= 0:
            self.dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            self.dir_timer = random.uniform(0.4, 1.0)
        if not self._try_axis_move(self.dir[0] * step * 0.5, self.dir[1] * step * 0.5,
                                   wall_rects, bounds):
            self.dir_timer = 0


def _heart_points(cx, cy, size, steps=30):
    """The classic parametric heart. The old shape was two circles over a
    down-pointing triangle, which left flat shoulders and a hard V."""
    s = size / 32.0
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        hx = 16 * math.sin(t) ** 3
        hy = (13 * math.cos(t) - 5 * math.cos(2 * t)
              - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + hx * s, cy - hy * s))
    return pts


def draw_heart(surface, x, y, size, filled=True):
    fill = HEART_FILL if filled else HEART_EMPTY
    shade = HEART_SHADE if filled else HEART_EMPTY_SHADE
    pygame.draw.polygon(surface, shade, _heart_points(x, y + size * 0.06, size))
    pygame.draw.polygon(surface, fill, _heart_points(x, y, size))
    if filled:
        shine = pygame.Rect(0, 0, max(2, int(size * 0.2)), max(2, int(size * 0.14)))
        shine.center = (int(x - size * 0.2), int(y - size * 0.18))
        pygame.draw.ellipse(surface, (255, 226, 228), shine)


def draw_pirate_avatar(surface, cx, cy, r, bandana=BANDANA, tint=None):
    """Small crew portrait. Used by the HUD; the title screen will want it too."""
    pygame.draw.circle(surface, tint if tint is not None else CREAM, (cx, cy), r)
    body_r = int(r * 0.70)
    head_r = int(r * 0.55)
    pygame.draw.circle(surface, COAT, (cx, cy + int(r * 0.28)), body_r)
    pygame.draw.circle(surface, SKIN, (cx, cy - int(r * 0.16)), head_r)
    pygame.draw.circle(surface, bandana, (cx, cy - int(r * 0.28)), head_r,
                       draw_top_left=True, draw_top_right=True)
    eye_dx = max(1, int(r * 0.2))
    eye_y = cy - int(r * 0.05)
    for side in (-1, 1):
        pygame.draw.circle(surface, (36, 24, 20), (cx + side * eye_dx, eye_y), max(1, int(r * 0.13)))
