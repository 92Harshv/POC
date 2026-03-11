"""
Road Rash Clone - A motorcycle racing game with combat
Built with Pygame
"""

import pygame
import sys
import math
import random
import os
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

# ─── Constants ────────────────────────────────────────────────────────────────

SCREEN_W, SCREEN_H = 1024, 768
TARGET_FPS = 60
TITLE = "Road Rash - Moto Brawler"

# Road parameters
ROAD_SEGMENTS = 150
SEGMENT_LENGTH = 200
CAMERA_DEPTH = 0.84
DRAW_DISTANCE = 100
FIELD_OF_VIEW = 100

# Colors
SKY_TOP    = (100, 149, 237)
SKY_BOT    = (150, 200, 255)
HILL_COLOR = (40, 120, 40)
GRASS_DARK = (16,  200,  16)
GRASS_LGT  = (0,   154,   0)
ROAD_DARK  = (105, 105, 105)
ROAD_LGT   = (117, 117, 117)
RUMBLE_D   = (187,  20,  20)
RUMBLE_L   = (220, 220, 220)
LANE_CLR   = (255, 255, 255)
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
RED        = (220,  30,  30)
YELLOW     = (255, 220,  0)
GREEN      = (30,  200,  30)
ORANGE     = (255, 140,  0)
PURPLE     = (150,  50, 200)
CYAN       = (0,   200, 200)
DARK_GREY  = (40,   40,  40)

# HUD
HUD_BG     = (0, 0, 0, 160)

# ─── Enums ────────────────────────────────────────────────────────────────────

class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    LEVEL_COMPLETE = "level_complete"
    VICTORY = "victory"

class AttackType(Enum):
    NONE = 0
    PUNCH_LEFT  = 1
    PUNCH_RIGHT = 2
    KICK_LEFT   = 3
    KICK_RIGHT  = 4

# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class Segment:
    index:    int
    p1:       dict = field(default_factory=dict)   # world/screen/clip coords
    p2:       dict = field(default_factory=dict)
    curve:    float = 0.0
    color:    dict = field(default_factory=dict)
    sprites:  list = field(default_factory=list)
    cars:     list = field(default_factory=list)

@dataclass
class Sprite:
    offset:  float   # -1 … +1  (road width fraction)
    scale:   float
    img_key: str
    clip:    Optional[float] = None

# ─── Utility helpers ──────────────────────────────────────────────────────────

def project(point, camera_x, camera_y, camera_z, camera_depth, width, height, road_width):
    """Project a 3-D world point onto the 2-D screen."""
    scale = camera_depth / (point["world"]["z"] - camera_z)
    sx = (1 + scale * (point["world"]["x"] - camera_x)) * width / 2
    sy = (1 - scale * (point["world"]["y"] - camera_y)) * height / 2
    sw = scale * road_width * width / 2
    point["screen"] = {"x": sx, "y": sy, "w": sw, "scale": scale}
    return point

def draw_polygon(surface, c1, c2, c3, c4, color):
    if color is None:
        return
    pygame.draw.polygon(surface, color, [c1, c2, c3, c4])

def draw_segment(surface, width, lanes,
                 x1, y1, w1,
                 x2, y2, w2,
                 fog, colors):
    r = 0.05  # rumble strip fraction
    l = 0.01  # lane marker fraction

    r1 = rumble_width(w1, lanes)
    r2 = rumble_width(w2, lanes)

    # grass
    pygame.draw.rect(surface, colors["grass"], (0, y2, width, y1 - y2))

    # road
    draw_polygon(surface, colors["road"],
                 (x1 - w1 - r1, y1), (x1 + w1 + r1, y1),
                 (x2 + w2 + r2, y2), (x2 - w2 - r2, y2))

    # rumble strips
    draw_polygon(surface, colors["rumble"],
                 (x1 - w1 - r1, y1), (x1 - w1, y1),
                 (x2 - w2, y2),      (x2 - w2 - r2, y2))
    draw_polygon(surface, colors["rumble"],
                 (x1 + w1 + r1, y1), (x1 + w1, y1),
                 (x2 + w2, y2),      (x2 + w2 + r2, y2))

    # lane dashes
    if colors.get("lane"):
        lw1 = lane_marker_width(w1, lanes)
        lw2 = lane_marker_width(w2, lanes)
        for lane_idx in range(1, lanes):
            ml1 = x1 - w1 + lane_idx * 2 * w1 / lanes
            ml2 = x2 - w2 + lane_idx * 2 * w2 / lanes
            draw_polygon(surface, colors["lane"],
                         (ml1 - lw1 / 2, y1), (ml1 + lw1 / 2, y1),
                         (ml2 + lw2 / 2, y2), (ml2 - lw2 / 2, y2))

def rumble_width(road_w, lanes):
    return road_w / max(6, 2 * lanes)

def lane_marker_width(road_w, lanes):
    return road_w / max(32, 8 * lanes)

def increase(start, inc, max_val):
    result = start + inc
    while result >= max_val:
        result -= max_val
    while result < 0:
        result += max_val
    return result

def limit(value, mn, mx):
    return max(mn, min(mx, value))

def overlap(x1, w1, x2, w2, percent=1.0):
    half = percent / 2
    min1 = x1 - w1 * half
    max1 = x1 + w1 * half
    min2 = x2 - w2 * half
    max2 = x2 + w2 * half
    return not (max1 < min2 or min1 > max2)

# ─── Road Generator ───────────────────────────────────────────────────────────

class Road:
    def __init__(self, level=1):
        self.segments: List[Segment] = []
        self.length    = 0
        self.lanes     = 3
        self.road_w    = 2000  # arbitrary "world" units
        self.level     = level
        self._build(level)

    # Color alternating every RUMBLE_LENGTH segments
    RUMBLE = 10

    def _build(self, level):
        curves = {1: 0.5, 2: 1.0, 3: 1.5}
        max_curve = curves.get(level, 1.0)

        self._add_straight(10)
        self._add_curve(50, max_curve * 2)
        self._add_straight(30)
        self._add_hill(40, 400)
        self._add_curve(30, -max_curve)
        self._add_straight(20)
        self._add_curve(50, max_curve * 1.5)
        self._add_straight(15)
        self._add_hill(30, -300)
        self._add_curve(40, -max_curve * 2)
        self._add_straight(25)
        self._add_curve(60, max_curve)
        self._add_straight(20)
        self._start_and_finish()
        self.length = len(self.segments) * SEGMENT_LENGTH

    def _add_segment(self, curve=0.0, y=0.0):
        n = len(self.segments)
        use_dark = (n // self.RUMBLE) % 2 == 0
        colors = {
            "grass":  GRASS_DARK if use_dark else GRASS_LGT,
            "road":   ROAD_DARK  if use_dark else ROAD_LGT,
            "rumble": RUMBLE_D   if use_dark else RUMBLE_L,
            "lane":   LANE_CLR   if use_dark else None,
        }
        last_y = self.segments[-1]["p2"]["world"]["y"] if self.segments else 0
        seg = {
            "index": n,
            "p1": {"world": {"x": 0, "y": last_y,   "z": n       * SEGMENT_LENGTH}},
            "p2": {"world": {"x": 0, "y": last_y + y, "z": (n + 1) * SEGMENT_LENGTH}},
            "curve":   curve,
            "colors":  colors,
            "sprites": [],
            "cars":    [],
        }
        self.segments.append(seg)

    def _add_straight(self, count=25):
        for _ in range(count):
            self._add_segment()

    def _add_curve(self, count=25, curve=2.0):
        for i in range(count):
            self._add_segment(curve=curve)

    def _add_hill(self, count=25, height=200):
        for i in range(count):
            y = height * math.sin(math.pi * i / count)
            self._add_segment(y=y)

    def _start_and_finish(self):
        # Color first and last 10 segments distinctively
        for seg in self.segments[:10]:
            seg["colors"]["road"]  = (200, 200, 200)
        for seg in self.segments[-10:]:
            seg["colors"]["road"]  = (200, 200, 200)
        # Decorate with roadside sprites
        self._add_sprites()

    def _add_sprites(self):
        tree_positions = [1.2, -1.3, 1.5, -1.6]
        for i in range(0, len(self.segments), random.randint(4, 8)):
            offset = random.choice(tree_positions)
            self.segments[i]["sprites"].append({"offset": offset, "key": "tree"})

    def find_segment(self, z):
        return self.segments[int(z / SEGMENT_LENGTH) % len(self.segments)]

    def get(self, index):
        return self.segments[index % len(self.segments)]


# ─── Sprite / Image renderer ──────────────────────────────────────────────────

class SpriteRenderer:
    """Draws procedurally generated sprites (no external image files needed)."""

    def __init__(self, surface_cache={}):
        self._cache = surface_cache

    def get(self, key, width=64, height=64) -> pygame.Surface:
        if key not in self._cache:
            self._cache[key] = self._make(key, width, height)
        return self._cache[key]

    def _make(self, key: str, w: int, h: int) -> pygame.Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        if key == "tree":
            # Trunk
            tw, th = w // 6, h // 3
            tx = (w - tw) // 2
            pygame.draw.rect(surf, (101, 67, 33), (tx, h - th, tw, th))
            # Foliage (3 circles)
            cr = w // 3
            pygame.draw.circle(surf, (34, 139, 34), (w // 2, h - th - cr), cr)
            pygame.draw.circle(surf, (34, 139, 34), (w // 2 - cr // 2, h - th - int(cr * 1.3)), int(cr * 0.9))
            pygame.draw.circle(surf, (34, 139, 34), (w // 2 + cr // 2, h - th - int(cr * 1.3)), int(cr * 0.9))
            pygame.draw.circle(surf, (50, 180, 50), (w // 2, h - th - int(cr * 1.5)), int(cr * 0.7))

        elif key.startswith("bike_"):
            color_map = {
                "bike_player": (255, 60,  0),
                "bike_red":    (220, 20,  60),
                "bike_blue":   (30,  100, 255),
                "bike_green":  (30,  200, 30),
                "bike_yellow": (255, 200,  0),
                "bike_purple": (180,  60, 220),
            }
            body_color = color_map.get(key, (150, 150, 150))
            self._draw_bike(surf, w, h, body_color)

        elif key == "crash_bike":
            self._draw_crash(surf, w, h)

        return surf

    def _draw_bike(self, surf, w, h, color):
        # Wheels
        wr = w // 8
        pygame.draw.circle(surf, (30, 30, 30),  (w // 4,         h - wr), wr)
        pygame.draw.circle(surf, (30, 30, 30),  (3 * w // 4,     h - wr), wr)
        pygame.draw.circle(surf, (80, 80, 80),  (w // 4,         h - wr), wr - 2)
        pygame.draw.circle(surf, (80, 80, 80),  (3 * w // 4,     h - wr), wr - 2)
        # Body
        bh = h // 3
        by = h - wr * 2 - bh
        pygame.draw.rect(surf, color, (w // 5, by, 3 * w // 5, bh))
        # Rider
        rw, rh = w // 4, h // 3
        rx = (w - rw) // 2
        ry = by - rh
        pygame.draw.rect(surf, (50, 50, 50), (rx, ry, rw, rh))
        # Helmet
        pygame.draw.ellipse(surf, (40, 40, 40), (rx, ry - rh // 2, rw, rh // 2 + 4))
        pygame.draw.ellipse(surf, (200, 200, 200), (rx + rw // 4, ry - rh // 2 + 4, rw // 2, rh // 4))

    def _draw_crash(self, surf, w, h):
        # Sparks
        for _ in range(20):
            x = random.randint(0, w)
            y = random.randint(0, h)
            r = random.randint(2, 5)
            c = random.choice([(255, 200, 0), (255, 100, 0), (255, 255, 255)])
            pygame.draw.circle(surf, c, (x, y), r)
        # Bike parts
        pygame.draw.line(surf, (150, 150, 150), (5, h - 5), (w - 10, h // 2), 4)
        pygame.draw.circle(surf, (30, 30, 30), (w // 3, h - 8), 8)
        pygame.draw.circle(surf, (30, 30, 30), (2 * w // 3, h - 8), 8)

# ─── Enemy Racer ──────────────────────────────────────────────────────────────

ENEMY_NAMES = ["Snake", "Dagger", "Blade", "Hawk", "Viper", "Storm", "Blaze", "Razor"]

class EnemyRacer:
    BIKE_KEYS = ["bike_red", "bike_blue", "bike_green", "bike_yellow", "bike_purple"]

    def __init__(self, road: Road, sprite_r: SpriteRenderer, z_start: float, name: str = ""):
        self.road      = road
        self.sprite_r  = sprite_r
        self.name      = name or random.choice(ENEMY_NAMES)
        self.bike_key  = random.choice(self.BIKE_KEYS)
        self.z         = z_start
        self.x         = random.uniform(-0.6, 0.6)
        self.speed     = random.uniform(140, 180)  # world units / second
        self.max_speed = random.uniform(150, 220)
        self.health    = 100
        self.stun_time = 0.0
        self.knocked   = False
        self.knocked_timer = 0.0
        self.percent   = 0.0  # race completion 0-1
        self.finished  = False
        self.crash_timer = 0.0

    @property
    def alive(self):
        return self.health > 0 and not self.knocked

    def update(self, dt, player_z, road_length):
        if self.knocked:
            self.knocked_timer -= dt
            if self.knocked_timer <= 0:
                self.knocked = False
                self.health  = max(1, self.health)
            return

        if self.crash_timer > 0:
            self.crash_timer -= dt
            self.speed = max(0, self.speed - 80 * dt)
            return

        if self.stun_time > 0:
            self.stun_time -= dt
            self.speed = max(30, self.speed - 60 * dt)
        else:
            # Rubber-band AI
            diff = player_z - self.z
            if diff > 500:
                target_speed = self.max_speed * 1.15
            elif diff < -500:
                target_speed = self.max_speed * 0.85
            else:
                target_speed = self.max_speed

            # Gentle steering
            seg = self.road.find_segment(self.z)
            self.x -= seg["curve"] * 0.003
            self.x += random.uniform(-0.005, 0.005)
            self.x  = limit(self.x, -0.9, 0.9)

            accel = 60 if self.speed < target_speed else -40
            self.speed = limit(self.speed + accel * dt, 30, self.max_speed * 1.2)

        self.z = increase(self.z, self.speed * dt, road_length)
        self.percent = self.z / road_length

    def take_hit(self, damage: int):
        self.health -= damage
        self.stun_time = 0.8
        if self.health <= 0:
            self.knocked = True
            self.knocked_timer = 3.0
            self.health = 0

    def sprite_key(self):
        if self.crash_timer > 0 or self.knocked:
            return "crash_bike"
        return self.bike_key

# ─── Player ───────────────────────────────────────────────────────────────────

class Player:
    MAX_SPEED   = 250.0   # world units / second
    ACCEL       = 120.0
    BRAKE_FORCE = 200.0
    STEER_SPEED = 1.8
    OFFROAD_SLOW = 0.4

    def __init__(self, road: Road):
        self.road        = road
        self.z           = 0.0
        self.x           = 0.0
        self.speed       = 0.0
        self.health      = 100
        self.max_health  = 100
        self.cash        = 0
        self.position    = 0    # race position
        self.percent     = 0.0  # 0-1 completion
        self.finished    = False
        self.finish_time = None

        self.attack        = AttackType.NONE
        self.attack_timer  = 0.0
        self.attack_cd     = 0.0
        self.stun_time     = 0.0
        self.invincible    = 0.0
        self.combo         = 0
        self.combo_timer   = 0.0

        self.off_road    = False
        self.skid_timer  = 0.0
        self.nitro       = 3
        self.nitro_timer = 0.0

    def accelerate(self, dt):
        self.speed = min(self.speed + self.ACCEL * dt, self.MAX_SPEED)

    def brake(self, dt):
        self.speed = max(0, self.speed - self.BRAKE_FORCE * dt)

    def steer_left(self, dt):
        self.x -= self.STEER_SPEED * dt * (self.speed / self.MAX_SPEED + 0.3)

    def steer_right(self, dt):
        self.x += self.STEER_SPEED * dt * (self.speed / self.MAX_SPEED + 0.3)

    def use_nitro(self):
        if self.nitro > 0 and self.nitro_timer <= 0:
            self.nitro -= 1
            self.nitro_timer = 2.0
            self.speed = min(self.speed + 80, self.MAX_SPEED * 1.3)

    def do_attack(self, attack_type: AttackType):
        if self.attack_cd <= 0 and self.stun_time <= 0:
            self.attack       = attack_type
            self.attack_timer = 0.35
            self.attack_cd    = 0.5

    def take_damage(self, dmg: int):
        if self.invincible > 0:
            return
        self.health   -= dmg
        self.invincible = 0.8
        self.stun_time  = 0.4
        if self.health < 0:
            self.health = 0

    def update(self, dt, road_length):
        if self.stun_time > 0:
            self.stun_time -= dt
            self.speed = max(0, self.speed - 100 * dt)

        if self.attack_timer > 0:
            self.attack_timer -= dt
        else:
            self.attack = AttackType.NONE

        if self.attack_cd > 0:
            self.attack_cd -= dt

        if self.invincible > 0:
            self.invincible -= dt

        if self.nitro_timer > 0:
            self.nitro_timer -= dt

        if self.combo_timer > 0:
            self.combo_timer -= dt
        else:
            self.combo = 0

        seg = self.road.find_segment(self.z)
        self.x -= seg["curve"] * (self.speed / self.MAX_SPEED) * 0.05

        self.off_road = abs(self.x) > 1.0
        if self.off_road:
            self.speed = max(0, self.speed - self.OFFROAD_SLOW * self.speed * dt * 3)
            self.x = limit(self.x, -2.0, 2.0)

        self.z = increase(self.z, self.speed * dt, road_length)
        self.percent = self.z / road_length

    def is_attacking_left(self):
        return self.attack in (AttackType.PUNCH_LEFT, AttackType.KICK_LEFT)

    def is_attacking_right(self):
        return self.attack in (AttackType.PUNCH_RIGHT, AttackType.KICK_RIGHT)

    def attack_damage(self):
        base = 15 if self.attack in (AttackType.PUNCH_LEFT, AttackType.PUNCH_RIGHT) else 25
        if self.combo >= 3:
            base = int(base * 1.5)
        return base

# ─── Camera ───────────────────────────────────────────────────────────────────

class Camera:
    HEIGHT = 1000
    DEPTH  = CAMERA_DEPTH

    def __init__(self):
        self.x = 0.0
        self.y = self.HEIGHT
        self.z = 0.0
        self.depth = self.DEPTH

    def follow(self, player: Player, road: Road):
        self.x = player.x * road.road_w
        seg = road.find_segment(player.z)
        self.y = self.HEIGHT + seg["p1"]["world"]["y"]
        self.z = player.z - (SCREEN_H / self.depth * 0.5) * SEGMENT_LENGTH

# ─── HUD ──────────────────────────────────────────────────────────────────────

class HUD:
    def __init__(self, font_large, font_med, font_small):
        self.font_l = font_large
        self.font_m = font_med
        self.font_s = font_small

    def draw(self, surface, player: Player, level: int, enemies: List[EnemyRacer],
             race_time: float, total_racers: int):
        w, h = surface.get_size()

        # Speed bar
        self._bar(surface, 20, h - 80, 220, 28,
                  player.speed / (player.MAX_SPEED * 1.3),
                  (255, 80, 0), "SPEED", f"{int(player.speed * 0.05)} mph")

        # Health bar
        hp_ratio = player.health / player.max_health
        bar_color = GREEN if hp_ratio > 0.5 else (YELLOW if hp_ratio > 0.25 else RED)
        self._bar(surface, 20, h - 46, 220, 24,
                  hp_ratio, bar_color, "HEALTH", f"{player.health}")

        # Nitro
        for i in range(3):
            col = CYAN if i < player.nitro else DARK_GREY
            pygame.draw.rect(surface, col, (255 + i * 26, h - 70, 22, 16))
            pygame.draw.rect(surface, WHITE, (255 + i * 26, h - 70, 22, 16), 1)
        self._label(surface, self.font_s, "NITRO", 255, h - 82)

        # Position
        pos_text = f"POS: {player.position + 1}/{total_racers}"
        self._label(surface, self.font_m, pos_text, w // 2 - 60, 10)

        # Timer
        mins = int(race_time) // 60
        secs = int(race_time) % 60
        ms   = int((race_time - int(race_time)) * 100)
        time_str = f"TIME  {mins:02d}:{secs:02d}.{ms:02d}"
        self._label(surface, self.font_m, time_str, w - 230, 10)

        # Level
        self._label(surface, self.font_s, f"LEVEL {level}", w - 100, 40)

        # Cash
        self._label(surface, self.font_m, f"${player.cash}", 20, 10)

        # Combo
        if player.combo >= 2:
            c_surf = self.font_l.render(f"x{player.combo} COMBO!", True, YELLOW)
            surface.blit(c_surf, (w // 2 - c_surf.get_width() // 2, h // 2 - 80))

        # Attack flash
        if player.attack != AttackType.NONE:
            side = "LEFT" if player.is_attacking_left() else "RIGHT"
            kind = "PUNCH" if player.attack in (AttackType.PUNCH_LEFT, AttackType.PUNCH_RIGHT) else "KICK"
            atk_surf = self.font_m.render(f"{kind} {side}!", True, ORANGE)
            surface.blit(atk_surf, (w // 2 - atk_surf.get_width() // 2, h // 2 - 40))

        # Nitro flash
        if player.nitro_timer > 0:
            n_surf = self.font_l.render("NITRO BOOST!", True, CYAN)
            surface.blit(n_surf, (w // 2 - n_surf.get_width() // 2, h // 2 - 120))

    def _bar(self, surface, x, y, w, h, ratio, color, label, value):
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 130))
        surface.blit(bg, (x, y))
        fill_w = int((w - 4) * max(0, min(ratio, 1)))
        if fill_w > 0:
            pygame.draw.rect(surface, color, (x + 2, y + 2, fill_w, h - 4))
        pygame.draw.rect(surface, WHITE, (x, y, w, h), 1)
        lbl = self.font_s.render(label, True, WHITE)
        surface.blit(lbl, (x + 4, y + h // 2 - lbl.get_height() // 2))
        val = self.font_s.render(value, True, WHITE)
        surface.blit(val, (x + w - val.get_width() - 4, y + h // 2 - val.get_height() // 2))

    def _label(self, surface, font, text, x, y, color=WHITE):
        surf = font.render(text, True, color)
        # shadow
        shadow = font.render(text, True, BLACK)
        surface.blit(shadow, (x + 1, y + 1))
        surface.blit(surf, (x, y))


# ─── Particle system ──────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, vx, vy, color, life):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.life  = life
        self.max_life = life
        self.r = random.randint(2, 5)

class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []

    def emit(self, x, y, count=10, colors=None, speed=3.0):
        if colors is None:
            colors = [(255, 200, 0), (255, 100, 0)]
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            spd   = random.uniform(0.5, speed)
            vx    = math.cos(angle) * spd
            vy    = math.sin(angle) * spd
            life  = random.uniform(0.3, 0.8)
            self.particles.append(Particle(x, y, vx, vy, random.choice(colors), life))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.x  += p.vx * 60 * dt
            p.y  += p.vy * 60 * dt
            p.vy += 2 * dt
            p.life -= dt

    def draw(self, surface):
        for p in self.particles:
            alpha = int(255 * p.life / p.max_life)
            color = (*p.color[:3], alpha) if len(p.color) == 3 else p.color
            s = pygame.Surface((p.r * 2, p.r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (p.r, p.r), p.r)
            surface.blit(s, (int(p.x) - p.r, int(p.y) - p.r))

# ─── Renderer ─────────────────────────────────────────────────────────────────

class Renderer3D:
    def __init__(self, surface: pygame.Surface, road: Road, sprite_r: SpriteRenderer):
        self.surface  = surface
        self.road     = road
        self.sprite_r = sprite_r
        self.w        = surface.get_width()
        self.h        = surface.get_height()

    def draw(self, camera: Camera, player: Player, enemies: List[EnemyRacer], particles: ParticleSystem):
        self._draw_sky()
        self._draw_road_and_sprites(camera, player, enemies)
        self._draw_player(player)
        particles.draw(self.surface)

    def _draw_sky(self):
        for y in range(self.h // 2):
            ratio = y / (self.h // 2)
            r = int(SKY_TOP[0] * (1 - ratio) + SKY_BOT[0] * ratio)
            g = int(SKY_TOP[1] * (1 - ratio) + SKY_BOT[1] * ratio)
            b = int(SKY_TOP[2] * (1 - ratio) + SKY_BOT[2] * ratio)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (self.w, y))
        # Hills
        hill_pts = []
        for x in range(0, self.w + 20, 20):
            y_val = int((self.h // 2) + 30 * math.sin(x * 0.01) - 20)
            hill_pts.append((x, y_val))
        hill_pts.append((self.w, self.h // 2))
        hill_pts.append((0, self.h // 2))
        pygame.draw.polygon(self.surface, HILL_COLOR, hill_pts)

    def _project_segs(self, camera: Camera):
        start_pos  = int(camera.z / SEGMENT_LENGTH)
        cam_x      = camera.x
        cam_y      = camera.y
        cam_z      = camera.z
        road       = self.road
        depth      = camera.depth
        x_offset   = 0.0
        max_y      = self.h

        projected = []
        for n in range(DRAW_DISTANCE):
            idx  = (start_pos + n) % len(road.segments)
            seg  = road.segments[idx]

            # Project p1 and p2
            cam_seg_z = cam_z - (len(road.segments) * SEGMENT_LENGTH if idx < start_pos else 0)

            scale1 = depth / (seg["p1"]["world"]["z"] - cam_seg_z + 1e-6)
            scale2 = depth / (seg["p2"]["world"]["z"] - cam_seg_z + 1e-6)

            sx1 = (1 + scale1 * (seg["p1"]["world"]["x"] * road.road_w - cam_x)) * self.w / 2
            sy1 = (1 - scale1 * (seg["p1"]["world"]["y"] - cam_y)) * self.h / 2
            sw1 = scale1 * road.road_w * self.w / 2

            sx2 = (1 + scale2 * (seg["p2"]["world"]["x"] * road.road_w - cam_x)) * self.w / 2
            sy2 = (1 - scale2 * (seg["p2"]["world"]["y"] - cam_y)) * self.h / 2
            sw2 = scale2 * road.road_w * self.w / 2

            x_offset += seg["curve"]

            # clip to horizon
            if sy2 >= max_y:
                continue
            if sy1 < sy2:
                max_y = sy1

            projected.append({
                "seg": seg,
                "x1": sx1 + x_offset, "y1": sy1, "w1": sw1,
                "x2": sx2 + x_offset, "y2": sy2, "w2": sw2,
                "scale": scale2,
            })
        return list(reversed(projected))

    def _draw_road_and_sprites(self, camera: Camera, player: Player, enemies: List[EnemyRacer]):
        segs = self._project_segs(camera)
        for proj in segs:
            seg = proj["seg"]
            draw_segment(
                self.surface, self.w, self.road.lanes,
                proj["x1"], proj["y1"], proj["w1"],
                proj["x2"], proj["y2"], proj["w2"],
                0, seg["colors"]
            )

        # Draw sprites (back to front already reversed)
        for proj in segs:
            seg = proj["seg"]
            scale = proj["scale"]
            screen_y = proj["y2"]
            screen_x_center = proj["x2"]
            sw = proj["w2"]

            # Roadside objects
            for sprite in seg["sprites"]:
                spr_img = self.sprite_r.get(sprite["key"], 64, 96)
                spr_w = int(spr_img.get_width() * scale * 2)
                spr_h = int(spr_img.get_height() * scale * 2)
                if spr_w < 2 or spr_h < 2:
                    continue
                off_x = screen_x_center + sprite["offset"] * sw * 1.5
                draw_x = int(off_x - spr_w // 2)
                draw_y = int(screen_y - spr_h)
                self.surface.blit(pygame.transform.scale(spr_img, (spr_w, spr_h)), (draw_x, draw_y))

            # Enemy bikes on this segment
            for enemy in seg.get("cars", []):
                bike_img = self.sprite_r.get(enemy.sprite_key(), 80, 60)
                b_w = int(bike_img.get_width() * scale * 3)
                b_h = int(bike_img.get_height() * scale * 3)
                if b_w < 4 or b_h < 4:
                    continue
                off_x = screen_x_center + enemy.x * sw
                draw_x = int(off_x - b_w // 2)
                draw_y = int(screen_y - b_h)
                # Blink when stunned
                if enemy.stun_time > 0 and int(enemy.stun_time * 10) % 2 == 0:
                    tinted = bike_img.copy()
                    tinted.fill((255, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
                    self.surface.blit(pygame.transform.scale(tinted, (b_w, b_h)), (draw_x, draw_y))
                else:
                    self.surface.blit(pygame.transform.scale(bike_img, (b_w, b_h)), (draw_x, draw_y))

                # Health bar above enemy
                if enemy.health < 100 and not enemy.knocked:
                    hb_w = b_w
                    hb_h = 5
                    hb_x = draw_x
                    hb_y = draw_y - 8
                    pygame.draw.rect(self.surface, RED,   (hb_x, hb_y, hb_w, hb_h))
                    pygame.draw.rect(self.surface, GREEN, (hb_x, hb_y, int(hb_w * enemy.health / 100), hb_h))

                # Name tag
                name_s = pygame.font.SysFont("Arial", max(8, int(12 * scale * 3))).render(
                    enemy.name, True, WHITE)
                self.surface.blit(name_s, (draw_x + b_w // 2 - name_s.get_width() // 2, draw_y - 20))

    def _draw_player(self, player: Player):
        w, h = self.w, self.h
        # Blink when invincible
        if player.invincible > 0 and int(player.invincible * 10) % 2 == 0:
            return

        bike_img = self.sprite_r.get("bike_player", 120, 90)
        bw = bike_img.get_width()
        bh = bike_img.get_height()

        lean = int(player.x * 10)
        rotated = pygame.transform.rotate(bike_img, -lean)

        # Center-bottom
        bx = w // 2 - rotated.get_width() // 2 + int(player.x * 30)
        by = h - rotated.get_height() - 20
        self.surface.blit(rotated, (bx, by))

        # Attack arm
        if player.attack != AttackType.NONE:
            arm_color = ORANGE if player.attack in (AttackType.PUNCH_LEFT, AttackType.PUNCH_RIGHT) else RED
            cx = bx + bw // 2
            cy = by + bh // 3
            if player.is_attacking_left():
                pygame.draw.line(self.surface, arm_color, (cx, cy), (cx - 60, cy - 10), 5)
                pygame.draw.circle(self.surface, arm_color, (cx - 60, cy - 10), 10)
            elif player.is_attacking_right():
                pygame.draw.line(self.surface, arm_color, (cx, cy), (cx + 60, cy - 10), 5)
                pygame.draw.circle(self.surface, arm_color, (cx + 60, cy - 10), 10)


# ─── Menu ─────────────────────────────────────────────────────────────────────

class Menu:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.font_xl = fonts["xl"]
        self.font_l  = fonts["l"]
        self.font_m  = fonts["m"]
        self.font_s  = fonts["s"]
        self.selected = 0
        self.options  = ["RACE", "CONTROLS", "QUIT"]
        self.show_controls = False
        self.bg_offset = 0.0

    def update(self, dt):
        self.bg_offset = (self.bg_offset + 40 * dt) % SCREEN_H

    def handle_event(self, event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if self.show_controls:
                self.show_controls = False
                return None
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = self.options[self.selected]
                if choice == "RACE":
                    return "start"
                elif choice == "CONTROLS":
                    self.show_controls = True
                elif choice == "QUIT":
                    return "quit"
        return None

    def draw(self):
        w, h = self.screen.get_size()

        # Animated road background
        self.screen.fill((20, 20, 40))
        for i in range(0, h, 40):
            y = (i + int(self.bg_offset)) % h
            pygame.draw.line(self.screen, (40, 40, 70), (0, y), (w, y), 1)
        for i in range(0, w, 80):
            pygame.draw.line(self.screen, (40, 40, 70), (i, 0), (i, h), 1)

        # Title glow
        for offset in range(4, 0, -1):
            glow = self.font_xl.render(TITLE, True, (min(255, offset * 60), 0, offset * 20))
            self.screen.blit(glow, (w // 2 - glow.get_width() // 2 + offset, h // 4 + offset))

        title_surf = self.font_xl.render(TITLE, True, (255, 80, 0))
        self.screen.blit(title_surf, (w // 2 - title_surf.get_width() // 2, h // 4))

        sub = self.font_m.render("Motorcycle Racing with Combat", True, (200, 200, 255))
        self.screen.blit(sub, (w // 2 - sub.get_width() // 2, h // 4 + 70))

        if self.show_controls:
            self._draw_controls(w, h)
            return

        # Menu options
        for i, opt in enumerate(self.options):
            color = YELLOW if i == self.selected else WHITE
            if i == self.selected:
                # selection box
                ts = self.font_l.render(f"> {opt} <", True, color)
            else:
                ts = self.font_l.render(opt, True, color)
            self.screen.blit(ts, (w // 2 - ts.get_width() // 2, h // 2 + i * 60))

        hint = self.font_s.render("UP/DOWN: Select   ENTER/SPACE: Confirm", True, (150, 150, 150))
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h - 40))

    def _draw_controls(self, w, h):
        panel = pygame.Surface((600, 420), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 200))
        self.screen.blit(panel, (w // 2 - 300, h // 2 - 220))

        title = self.font_l.render("CONTROLS", True, YELLOW)
        self.screen.blit(title, (w // 2 - title.get_width() // 2, h // 2 - 210))

        controls = [
            ("ACCELERATE",   "↑ / W"),
            ("BRAKE / REVERSE", "↓ / S"),
            ("STEER LEFT",   "← / A"),
            ("STEER RIGHT",  "→ / D"),
            ("PUNCH LEFT",   "Z"),
            ("PUNCH RIGHT",  "X"),
            ("KICK LEFT",    "Q"),
            ("KICK RIGHT",   "E"),
            ("NITRO BOOST",  "SHIFT"),
            ("PAUSE",        "P / ESC"),
        ]
        for j, (action, key) in enumerate(controls):
            a_surf = self.font_s.render(action, True, (200, 200, 200))
            k_surf = self.font_s.render(key,    True, CYAN)
            row_y  = h // 2 - 160 + j * 34
            self.screen.blit(a_surf, (w // 2 - 280, row_y))
            self.screen.blit(k_surf, (w // 2 + 80,  row_y))

        hint = self.font_s.render("Press any key to return", True, (150, 150, 150))
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, h // 2 + 190))


# ─── Game Over / Level Complete screens ──────────────────────────────────────

def draw_overlay_screen(surface, fonts, title, subtitle, details, color=RED):
    w, h = surface.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))

    t = fonts["xl"].render(title, True, color)
    surface.blit(t, (w // 2 - t.get_width() // 2, h // 3))

    s = fonts["l"].render(subtitle, True, WHITE)
    surface.blit(s, (w // 2 - s.get_width() // 2, h // 3 + 80))

    for i, d in enumerate(details):
        ds = fonts["m"].render(d, True, (200, 200, 200))
        surface.blit(ds, (w // 2 - ds.get_width() // 2, h // 2 + i * 36))

    hint = fonts["s"].render("ENTER: Continue   ESC: Menu", True, (150, 150, 150))
    surface.blit(hint, (w // 2 - hint.get_width() // 2, h - 50))


# ─── Main Game ────────────────────────────────────────────────────────────────

class RoadRashGame:
    LEVELS = 3
    ENEMIES_PER_LEVEL = [5, 7, 9]

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.DOUBLEBUF)
        self.clock  = pygame.time.Clock()

        self.fonts = {
            "xl": pygame.font.SysFont("Impact",  64),
            "l":  pygame.font.SysFont("Impact",  40),
            "m":  pygame.font.SysFont("Arial",   24),
            "s":  pygame.font.SysFont("Arial",   16),
        }

        self.state       = GameState.MENU
        self.menu        = Menu(self.screen, self.fonts)
        self.total_cash  = 0
        self.current_level = 1

        self.road      = None
        self.camera    = None
        self.player    = None
        self.enemies: List[EnemyRacer] = []
        self.renderer  = None
        self.hud       = None
        self.particles = ParticleSystem()
        self.sprite_r  = SpriteRenderer()
        self.race_time = 0.0

    # ── Level setup ─────────────────────────────────────────────────────────

    def _start_level(self, level: int):
        self.current_level = level
        self.road      = Road(level)
        self.camera    = Camera()
        self.player    = Player(self.road)
        self.particles = ParticleSystem()
        self.renderer  = Renderer3D(self.screen, self.road, self.sprite_r)
        self.hud       = HUD(self.fonts["l"], self.fonts["m"], self.fonts["s"])
        self.race_time = 0.0

        n_enemies = self.ENEMIES_PER_LEVEL[min(level - 1, len(self.ENEMIES_PER_LEVEL) - 1)]
        self.enemies = []
        names = random.sample(ENEMY_NAMES * 2, n_enemies)
        for i in range(n_enemies):
            z_start = (i + 1) * random.uniform(600, 1200)
            e = EnemyRacer(self.road, self.sprite_r, z_start, names[i])
            self.enemies.append(e)

        self.state = GameState.PLAYING

    # ── Update ──────────────────────────────────────────────────────────────

    def _update(self, dt: float):
        keys = pygame.key.get_pressed()
        player = self.player
        road   = self.road

        if player.stun_time <= 0:
            if keys[pygame.K_UP]   or keys[pygame.K_w]:  player.accelerate(dt)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:  player.brake(dt)
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:  player.steer_left(dt)
            if keys[pygame.K_RIGHT]or keys[pygame.K_d]:  player.steer_right(dt)
        else:
            player.speed = max(0, player.speed - 80 * dt)

        player.update(dt, road.length)
        self.race_time += dt

        # Place enemies in their road segments
        for seg in road.segments:
            seg["cars"] = []
        for enemy in self.enemies:
            enemy.update(dt, player.z, road.length)
            seg_idx = int(enemy.z / SEGMENT_LENGTH) % len(road.segments)
            road.segments[seg_idx]["cars"].append(enemy)

        self.camera.follow(player, road)
        self.particles.update(dt)

        # Combat hit detection
        self._check_combat(dt)

        # Update race positions
        self._update_positions()

        # Check finish
        if player.percent >= 1.0 and not player.finished:
            player.finished = True
            player.finish_time = self.race_time
            beaten = sum(1 for e in self.enemies if e.percent < player.percent)
            prize  = max(0, (len(self.enemies) + 1 - player.position) * 500)
            player.cash += prize
            self.total_cash += prize

            if player.position == 0:
                if self.current_level < self.LEVELS:
                    self.state = GameState.LEVEL_COMPLETE
                else:
                    self.state = GameState.VICTORY
            else:
                self.state = GameState.LEVEL_COMPLETE

        if player.health <= 0:
            self.state = GameState.GAME_OVER

    def _check_combat(self, dt):
        player = self.player
        if player.attack == AttackType.NONE:
            return

        pw, ph = SCREEN_W, SCREEN_H
        player_screen_x = pw // 2 + int(player.x * 200)
        player_screen_y = ph - 80
        hit_range_z = 400.0

        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dz = abs(enemy.z - player.z)
            if dz > hit_range_z:
                continue

            # Left/right check
            dx = enemy.x - player.x
            hitting_left  = player.is_attacking_left()  and dx < -0.05
            hitting_right = player.is_attacking_right() and dx >  0.05
            if not (hitting_left or hitting_right):
                continue

            if abs(dx) > 0.6:
                continue

            dmg = player.attack_damage()
            enemy.take_hit(dmg)
            player.combo      += 1
            player.combo_timer = 1.5

            # Sparks
            ex = player_screen_x + int(dx * 200)
            self.particles.emit(ex, player_screen_y - 40, 15,
                                [(255,200,0),(255,100,0),(255,255,200)], 4.0)

            if enemy.knocked:
                player.cash += 200 + player.combo * 50

        # Enemy attacks player
        for enemy in self.enemies:
            if not enemy.alive or enemy.stun_time > 0:
                continue
            dz = abs(enemy.z - player.z)
            dx = abs(enemy.x - player.x)
            if dz < 300 and dx < 0.3 and random.random() < 0.003:
                player.take_damage(random.randint(8, 18))
                self.particles.emit(pw // 2, ph - 100, 10, [RED, ORANGE], 3.0)

    def _update_positions(self):
        all_racers = [(self.player.percent, "player")] + \
                     [(e.percent, e) for e in self.enemies]
        all_racers.sort(key=lambda x: -x[0])
        for i, (pct, who) in enumerate(all_racers):
            if who == "player":
                self.player.position = i

    # ── Draw ────────────────────────────────────────────────────────────────

    def _draw(self):
        self.renderer.draw(self.camera, self.player, self.enemies, self.particles)
        self.hud.draw(self.screen, self.player, self.current_level,
                      self.enemies, self.race_time, len(self.enemies) + 1)

        if self.state == GameState.PAUSED:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.screen.blit(overlay, (0, 0))
            p = self.fonts["xl"].render("PAUSED", True, YELLOW)
            self.screen.blit(p, (SCREEN_W // 2 - p.get_width() // 2, SCREEN_H // 2 - 40))
            h = self.fonts["m"].render("P / ESC to resume", True, WHITE)
            self.screen.blit(h, (SCREEN_W // 2 - h.get_width() // 2, SCREEN_H // 2 + 30))

    # ── Main loop ───────────────────────────────────────────────────────────

    def run(self):
        while True:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            dt = min(dt, 0.05)  # cap

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if self.state == GameState.MENU:
                    result = self.menu.handle_event(event)
                    if result == "start":
                        self._start_level(1)
                    elif result == "quit":
                        pygame.quit(); sys.exit()

                elif self.state == GameState.PLAYING:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_p, pygame.K_ESCAPE):
                            self.state = GameState.PAUSED
                        elif event.key == pygame.K_z:
                            self.player.do_attack(AttackType.PUNCH_LEFT)
                        elif event.key == pygame.K_x:
                            self.player.do_attack(AttackType.PUNCH_RIGHT)
                        elif event.key == pygame.K_q:
                            self.player.do_attack(AttackType.KICK_LEFT)
                        elif event.key == pygame.K_e:
                            self.player.do_attack(AttackType.KICK_RIGHT)
                        elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                            self.player.use_nitro()

                elif self.state == GameState.PAUSED:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_p, pygame.K_ESCAPE):
                            self.state = GameState.PLAYING

                elif self.state in (GameState.GAME_OVER, GameState.LEVEL_COMPLETE, GameState.VICTORY):
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            if self.state == GameState.LEVEL_COMPLETE and self.current_level < self.LEVELS:
                                self._start_level(self.current_level + 1)
                            else:
                                self.state = GameState.MENU
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MENU

            # ── State updates ────────────────────────────────────────────
            if self.state == GameState.MENU:
                self.menu.update(dt)
                self.menu.draw()

            elif self.state == GameState.PLAYING:
                self._update(dt)
                self._draw()

            elif self.state == GameState.PAUSED:
                self._draw()

            elif self.state == GameState.GAME_OVER:
                self._draw()
                draw_overlay_screen(
                    self.screen, self.fonts,
                    "WIPED OUT!", "You crashed and burned.",
                    [f"Race Time: {int(self.race_time // 60):02d}:{int(self.race_time % 60):02d}",
                     f"Position: {self.player.position + 1}/{len(self.enemies) + 1}",
                     f"Cash Earned: ${self.player.cash}"],
                    RED
                )

            elif self.state == GameState.LEVEL_COMPLETE:
                self._draw()
                if self.player.position == 0:
                    title, sub = "1ST PLACE!", "Level Complete - Well Ridden!"
                    col = YELLOW
                else:
                    title = f"LEVEL {self.current_level} DONE"
                    sub   = f"You finished #{self.player.position + 1}"
                    col   = GREEN
                draw_overlay_screen(
                    self.screen, self.fonts, title, sub,
                    [f"Time: {int(self.race_time//60):02d}:{int(self.race_time%60):02d}",
                     f"Position: {self.player.position+1}/{len(self.enemies)+1}",
                     f"Level Cash: ${self.player.cash}",
                     f"Total Cash: ${self.total_cash}",
                     "" if self.current_level >= self.LEVELS else f"Next: Level {self.current_level + 1}"],
                    col
                )

            elif self.state == GameState.VICTORY:
                self._draw()
                draw_overlay_screen(
                    self.screen, self.fonts,
                    "CHAMPION!", "You conquered all 3 levels!",
                    [f"Total Cash: ${self.total_cash}",
                     "You are the Road Rash King!"],
                    YELLOW
                )

            pygame.display.flip()


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    game = RoadRashGame()
    game.run()

if __name__ == "__main__":
    main()
