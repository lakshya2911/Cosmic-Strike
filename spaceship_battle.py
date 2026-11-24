import pygame
import random
import math

pygame.init()

# ----------------------------
# SCREEN
# ----------------------------
WIDTH = 1200
HEIGHT = 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Night Sky: Spaceship Battle")
clock = pygame.time.Clock()

ADD = pygame.BLEND_RGB_ADD

# ----------------------------
# COLORS
# ----------------------------
WHITE = (255, 255, 255)
BLACK = (5, 8, 20)
BLUE = (40, 150, 255)
CYAN = (70, 230, 255)
RED = (255, 70, 70)
ORANGE = (255, 150, 40)
PURPLE = (170, 80, 255)
GREEN = (70, 230, 120)

# ----------------------------
# FONTS
# ----------------------------
font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 64)
small_font = pygame.font.Font(None, 24)


# ============================================================
# HELPERS
# ============================================================
def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def make_glow(radius, color, strength=1.0):
    """Soft radial glow on a black surface. Blit it with BLEND_RGB_ADD."""
    surf = pygame.Surface((radius * 2, radius * 2))
    surf.fill((0, 0, 0))
    for r in range(radius, 0, -1):
        f = (1 - r / radius) ** 2 * strength
        c = tuple(min(255, int(v * f)) for v in color)
        pygame.draw.circle(surf, c, (radius, radius), r)
    return surf


def make_glow_ladder(radius, color, steps=8, strength=1.0):
    """Same glow at several brightness levels (used for fading effects)."""
    return [make_glow(radius, color, strength * (i + 1) / steps) for i in range(steps)]


def blit_glow(glow, cx, cy):
    screen.blit(
        glow,
        (int(cx) - glow.get_width() // 2, int(cy) - glow.get_height() // 2),
        special_flags=ADD,
    )


# ---- supersampled sprite drawing (gives smooth, anti-aliased edges) ----
SS = 4


def spoly(surf, color, pts, cx, cy):
    pygame.draw.polygon(
        surf, color, [(int((cx + x) * SS), int((cy + y) * SS)) for x, y in pts]
    )


def sellipse(surf, color, rect, cx, cy):
    x, y, w, h = rect
    pygame.draw.ellipse(
        surf,
        color,
        (int((cx + x) * SS), int((cy + y) * SS), int(w * SS), int(h * SS)),
    )


def srect(surf, color, rect, cx, cy, radius=0):
    x, y, w, h = rect
    pygame.draw.rect(
        surf,
        color,
        (int((cx + x) * SS), int((cy + y) * SS), int(w * SS), int(h * SS)),
        border_radius=int(radius * SS),
    )


def sline(surf, color, p1, p2, width, cx, cy):
    pygame.draw.line(
        surf,
        color,
        (int((cx + p1[0]) * SS), int((cy + p1[1]) * SS)),
        (int((cx + p2[0]) * SS), int((cy + p2[1]) * SS)),
        max(1, int(width * SS)),
    )


def scircle(surf, color, center, r, cx, cy):
    pygame.draw.circle(
        surf,
        color,
        (int((cx + center[0]) * SS), int((cy + center[1]) * SS)),
        max(1, int(r * SS)),
    )


def finish_sprite(big, w, h):
    return pygame.transform.smoothscale(big, (w, h)).convert_alpha()


# ============================================================
# BACKGROUND
# ============================================================
def build_moon():
    R = 55
    S = 3
    big = pygame.Surface((R * 2 * S, R * 2 * S), pygame.SRCALPHA)

    # Sphere shading: concentric discs drifting toward the light
    for i in range(R * S, 0, -1):
        t = i / (R * S)
        c = int(238 - 48 * t)
        cx = R * S - int((1 - t) * 12 * S)
        cy = R * S - int((1 - t) * 12 * S)
        pygame.draw.circle(big, (c, c, int(c * 0.93)), (cx, cy), i)

    # Craters
    for dx, dy, r in [(-15, -10, 9), (14, -18, 6), (10, 14, 11),
                      (-22, 18, 5), (-2, -30, 4), (25, 2, 5)]:
        crater = pygame.Surface((r * 2 * S, r * 2 * S), pygame.SRCALPHA)
        pygame.draw.circle(crater, (120, 120, 118, 95), (r * S, r * S), r * S)
        pygame.draw.circle(crater, (225, 225, 212, 60), (r * S + S, r * S + S), max(1, r * S - 2 * S))
        big.blit(crater, (R * S + dx * S - r * S, R * S + dy * S - r * S))

    return pygame.transform.smoothscale(big, (R * 2, R * 2)).convert_alpha()


def build_sky():
    sky = pygame.Surface((WIDTH, HEIGHT))

    # Vertical gradient: deep space -> violet horizon
    top = (3, 5, 18)
    mid = (12, 16, 48)
    bottom = (40, 34, 88)
    for y in range(HEIGHT):
        t = y / HEIGHT
        if t < 0.6:
            c = lerp_color(top, mid, t / 0.6)
        else:
            c = lerp_color(mid, bottom, (t - 0.6) / 0.4)
        pygame.draw.line(sky, c, (0, y), (WIDTH, y))

    # Nebula clouds (drawn small, then smooth-scaled up for a soft look)
    nw, nh = WIDTH // 5, HEIGHT // 5
    nebula = pygame.Surface((nw, nh))
    nebula.fill((0, 0, 0))
    palette = [(70, 20, 110), (20, 60, 130), (110, 30, 90), (20, 90, 110)]
    for _ in range(16):
        col = random.choice(palette)
        r = random.randint(25, 55)
        glow = make_glow(r, col, 0.45)
        cx = random.randint(0, nw)
        cy = random.randint(0, int(nh * 0.75))
        nebula.blit(glow, (cx - r, cy - r), special_flags=ADD)
    nebula = pygame.transform.smoothscale(nebula, (WIDTH, HEIGHT))
    sky.blit(nebula, (0, 0), special_flags=ADD)

    # Moon halo + moon
    moon_x, moon_y = 1050, 105
    halo = make_glow(170, (55, 62, 90), 0.9)
    sky.blit(halo, (moon_x - 170, moon_y - 170), special_flags=ADD)
    moon = build_moon()
    sky.blit(moon, (moon_x - 55, moon_y - 55))

    return sky.convert()


def make_ridge(base_y, amp, steps=7, rough=0.55):
    """Midpoint-displacement ridge line -> natural looking mountains."""
    n = 2 ** steps
    h = [0.0] * (n + 1)
    h[0] = random.uniform(-amp, amp)
    h[n] = random.uniform(-amp, amp)
    step = n
    scale = amp
    while step > 1:
        half = step // 2
        for i in range(half, n, step):
            h[i] = (h[i - half] + h[i + half]) / 2 + random.uniform(-scale, scale)
        scale *= rough
        step = half
    return [(i * WIDTH / n, base_y + h[i]) for i in range(n + 1)]


def draw_tree(surf, x, y, h, color):
    w = h * 0.32
    for k in range(3):
        ty = y - h + k * h * 0.25
        by = ty + h * 0.45
        half = w * (0.55 + 0.22 * k)
        pygame.draw.polygon(surf, color, [(x, ty), (x - half, by), (x + half, by)])


def build_mountains():
    layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # (base_y, amplitude, fill, rim light, fog alpha, fog colour)
    specs = [
        (HEIGHT - 190, 45, (34, 40, 86), (95, 108, 180), 110, (70, 78, 140)),
        (HEIGHT - 135, 38, (22, 28, 64), (70, 84, 155), 90, (55, 62, 120)),
        (HEIGHT - 80, 28, (11, 15, 36), (44, 55, 105), 0, None),
    ]

    for index, (base, amp, fill, rim, fog_a, fog_c) in enumerate(specs):
        pts = make_ridge(base, amp)
        poly = pts + [(WIDTH, HEIGHT), (0, HEIGHT)]
        pygame.draw.polygon(layer, fill, poly)
        pygame.draw.lines(layer, rim, False, pts, 2)

        # Pine trees on the nearest layer
        if index == 2:
            n = len(pts) - 1
            x = random.randint(0, 12)
            while x < WIDTH:
                ridge_y = pts[min(n, int(x / WIDTH * n))][1]
                draw_tree(layer, x, ridge_y + 3, random.randint(18, 36), fill)
                x += random.randint(8, 20)

        # Atmospheric haze between layers
        if fog_c:
            fog_h = 230
            fog = pygame.Surface((WIDTH, fog_h), pygame.SRCALPHA)
            for y in range(fog_h):
                a = int(fog_a * (y / fog_h) ** 1.6)
                pygame.draw.line(fog, (*fog_c, a), (0, y), (WIDTH, y))
            layer.blit(fog, (0, HEIGHT - fog_h))

    return layer.convert_alpha()


sky_bg = build_sky()
mountains_layer = build_mountains()

# Stars: bigger ones are "closer" -> move faster and twinkle with a glow
STAR_TINTS = [(255, 255, 255), (200, 220, 255), (255, 236, 205), (255, 215, 215)]
stars = []
for _ in range(220):
    layer_id = random.choices([0, 1, 2], weights=[6, 3, 1])[0]
    stars.append({
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(0, HEIGHT),
        "size": layer_id + 1,
        "speed": [0.2, 0.45, 0.8][layer_id],
        "phase": random.uniform(0, 6.28),
        "freq": random.uniform(1.5, 4.0),
        "color": random.choice(STAR_TINTS),
    })

star_glow_small = make_glow(6, (110, 120, 160), 0.8)
star_glow_big = make_glow(12, (150, 160, 210), 0.9)

shooting_stars = []


def update_shooting_stars():
    if random.random() < 0.004 and len(shooting_stars) < 2:
        ang = math.radians(random.uniform(20, 35))
        sp = random.uniform(14, 20)
        life = random.randint(28, 42)
        shooting_stars.append({
            "x": random.uniform(300, WIDTH),
            "y": random.uniform(0, 200),
            "dx": -math.cos(ang) * sp,
            "dy": math.sin(ang) * sp,
            "life": life,
            "max": life,
        })

    for s in shooting_stars[:]:
        s["x"] += s["dx"]
        s["y"] += s["dy"]
        s["life"] -= 1
        if s["life"] <= 0:
            shooting_stars.remove(s)


def draw_shooting_stars():
    for s in shooting_stars:
        f = s["life"] / s["max"]
        n = 12
        for i in range(n):
            k = (1 - i / n) * f
            c = int(255 * k)
            p1 = (s["x"] - s["dx"] * i * 0.45, s["y"] - s["dy"] * i * 0.45)
            p2 = (s["x"] - s["dx"] * (i + 1) * 0.45, s["y"] - s["dy"] * (i + 1) * 0.45)
            pygame.draw.line(screen, (c, c, min(255, c + 20)), p1, p2, 2 if i < 4 else 1)


def draw_stars(t):
    for s in stars:
        tw = 0.65 + 0.35 * math.sin(t * s["freq"] + s["phase"])
        col = tuple(int(c * tw) for c in s["color"])
        x, y = int(s["x"]), int(s["y"])

        if s["size"] == 1:
            pygame.draw.circle(screen, col, (x, y), 1)
        elif s["size"] == 2:
            pygame.draw.circle(screen, col, (x, y), 1)
            screen.blit(star_glow_small, (x - 6, y - 6), special_flags=ADD)
        else:
            pygame.draw.circle(screen, col, (x, y), 2)
            dim = tuple(int(c * 0.5) for c in col)
            pygame.draw.line(screen, dim, (x - 7, y), (x + 7, y))
            pygame.draw.line(screen, dim, (x, y - 7), (x, y + 7))
            screen.blit(star_glow_big, (x - 12, y - 12), special_flags=ADD)


def draw_background(t):
    screen.blit(sky_bg, (0, 0))
    draw_stars(t)
    draw_shooting_stars()
    screen.blit(mountains_layer, (0, 0))


# ============================================================
# SPRITES: PLAYER
# ============================================================
def build_player_sprite():
    W, H = 140, 96
    cx, cy = W // 2, H // 2
    big = pygame.Surface((W * SS, H * SS), pygame.SRCALPHA)

    for m in (1, -1):
        def M(pts, m=m):
            return [(x * m, y) for x, y in pts]

        # Wing: dark underside + lit top facet
        spoly(big, (26, 74, 150), M([(-12, -2), (-60, 30), (-56, 38), (-28, 32), (-10, 22)]), cx, cy)
        spoly(big, (70, 160, 255), M([(-12, -2), (-60, 30), (-34, 22), (-12, 10)]), cx, cy)
        sline(big, (190, 235, 255), (m * -12, -2), (m * -60, 30), 0.9, cx, cy)
        sline(big, CYAN, (m * -22, 14), (m * -44, 28), 1.2, cx, cy)
        # Navigation light
        light = (255, 70, 70) if m == 1 else (70, 255, 120)
        scircle(big, light, (m * -57, 34), 2.2, cx, cy)

    # Fuselage: lit left half, shadowed right half
    left = [(0, -40), (-10, -18), (-22, 22), (-28, 32), (-9, 24), (0, 36)]
    right = [(-x, y) for x, y in left]
    spoly(big, (200, 212, 230), left, cx, cy)
    spoly(big, (138, 152, 178), right, cx, cy)

    # Panel lines and trim
    sline(big, (95, 108, 135), (0, -40), (0, 34), 0.7, cx, cy)
    sline(big, (95, 108, 135), (-11, -12), (-15, 20), 0.6, cx, cy)
    sline(big, (95, 108, 135), (11, -12), (15, 20), 0.6, cx, cy)
    spoly(big, (60, 170, 230), [(0, 6), (-9, 18), (0, 14), (9, 18)], cx, cy)

    # Engine pods
    for ex in (-14, 4):
        srect(big, (55, 62, 80), (ex, 22, 10, 12), cx, cy, radius=2)
        srect(big, (90, 100, 125), (ex, 22, 10, 2), cx, cy)
        srect(big, (22, 25, 35), (ex + 1, 32, 8, 3), cx, cy)

    # Cockpit canopy
    sellipse(big, (20, 60, 95), (-6.5, -25, 13, 28), cx, cy)
    sellipse(big, (40, 150, 205), (-5, -23, 10, 24), cx, cy)
    sellipse(big, (200, 245, 255), (-3, -21, 3, 10), cx, cy)

    return pygame.transform.smoothscale(big, (W, H)).convert_alpha()


ship_sprite = build_player_sprite()
ship_halo = make_glow(85, (30, 70, 140), 0.35)
engine_glow = make_glow(26, (255, 140, 50), 0.9)
trail_glows = make_glow_ladder(8, (255, 150, 60), 8, 0.9)

# ============================================================
# SPRITES: ENEMIES
# ============================================================
ENEMY_PALETTES = {
    1: dict(  # standard raider
        body_l=(190, 72, 98), body_r=(125, 40, 62),
        wing_d=(92, 38, 168), wing_l=(160, 95, 250),
        eye=(255, 170, 50), eye_in=(255, 240, 160),
        accent=(255, 90, 90), flame=(255, 70, 50), flame_in=(255, 190, 80),
        eye_glow=(255, 140, 40),
    ),
    2: dict(  # armoured heavy (level 4+)
        body_l=(140, 155, 180), body_r=(88, 100, 126),
        wing_d=(66, 74, 98), wing_l=(120, 134, 164),
        eye=(70, 240, 150), eye_in=(215, 255, 232),
        accent=(255, 190, 60), flame=(255, 150, 40), flame_in=(255, 235, 150),
        eye_glow=(60, 255, 150),
    ),
}


def build_enemy_sprite(pal):
    W, H = 120, 96
    cx, cy = W // 2, H // 2
    big = pygame.Surface((W * SS, H * SS), pygame.SRCALPHA)

    for m in (1, -1):
        def M(pts, m=m):
            return [(x * m, y) for x, y in pts]

        # Swept wings with a lit leading facet
        spoly(big, pal["wing_d"], M([(-10, -6), (-50, -34), (-52, -14), (-40, 6), (-22, 20), (-10, 10)]), cx, cy)
        spoly(big, pal["wing_l"], M([(-10, -6), (-50, -34), (-52, -14), (-24, -2)]), cx, cy)
        sline(big, pal["accent"], (m * -14, -4), (m * -44, -26), 1.1, cx, cy)

        # Wing cannons
        srect(big, (50, 50, 62), (-17 if m == 1 else 13, 0, 4, 16), cx, cy)
        srect(big, pal["accent"], (-17 if m == 1 else 13, 14, 4, 3), cx, cy)

    # Body (nose points down)
    left = [(0, 32), (-12, 10), (-28, -14), (-10, -12), (0, -30)]
    right = [(-x, y) for x, y in left]
    spoly(big, pal["body_l"], left, cx, cy)
    spoly(big, pal["body_r"], right, cx, cy)
    sline(big, (40, 20, 35), (0, 32), (0, -30), 0.6, cx, cy)

    # Engine housing at the rear (top)
    srect(big, (45, 40, 58), (-9, -35, 18, 9), cx, cy, radius=2)
    srect(big, (20, 18, 28), (-6, -36, 12, 3), cx, cy)

    # Glowing eye with slit pupil
    sellipse(big, (35, 14, 25), (-9, -4, 18, 22), cx, cy)
    sellipse(big, pal["eye"], (-7, -2, 14, 18), cx, cy)
    sellipse(big, pal["eye_in"], (-4, 0, 6, 6), cx, cy)
    sellipse(big, (30, 10, 15), (-1.5, 3, 3, 10), cx, cy)

    return pygame.transform.smoothscale(big, (W, H)).convert_alpha()


def make_flash(sprite):
    flash = sprite.copy()
    flash.fill((110, 110, 110, 0), special_flags=ADD)
    return flash


enemy_sprites = {}
enemy_eye_glows = {}
for hp, pal in ENEMY_PALETTES.items():
    base = build_enemy_sprite(pal)
    enemy_sprites[hp] = (base, make_flash(base))
    enemy_eye_glows[hp] = make_glow_ladder(20, pal["eye_glow"], 8, 0.9)

enemy_engine_glow = make_glow(18, (255, 100, 60), 0.8)

# ============================================================
# LASERS / EFFECT GLOWS
# ============================================================
laser_glow = pygame.transform.smoothscale(make_glow(16, (40, 170, 255), 0.9), (30, 64))
enemy_laser_glow = pygame.transform.smoothscale(make_glow(16, (255, 60, 40), 0.9), (30, 62))
fire_glows = make_glow_ladder(12, (255, 140, 40), 8, 0.9)
BOOM_R = 40
boom_glows = make_glow_ladder(BOOM_R, (255, 150, 60), 8, 0.8)

# ----------------------------
# PLAYER
# ----------------------------
player = {
    "x": WIDTH // 2,
    "y": HEIGHT - 110,
    "speed": 7,
    "health": 150,
    "cooldown": 0,
    "tilt": 0.0
}

# ----------------------------
# GAME OBJECTS
# ----------------------------
lasers = []
enemy_lasers = []
enemies = []
particles = []
rings = []
trail = []

score = 0
level = 1
enemy_timer = 0
game_over = False


# ============================================================
# DRAW FUNCTIONS
# ============================================================
def draw_player(t):
    x = player["x"]
    y = player["y"]

    # Soft halo around the ship
    blit_glow(ship_halo, x, y)

    # Twin engine flames (flickering)
    for nx in (-9, 9):
        fx = x + nx
        fy = y + 32
        length = 22 + random.uniform(0, 7) + math.sin(t * 40) * 3
        pygame.draw.polygon(screen, (255, 110, 30),
                            [(fx - 5.5, fy), (fx, fy + length), (fx + 5.5, fy)])
        pygame.draw.polygon(screen, (255, 205, 90),
                            [(fx - 3.5, fy), (fx, fy + length * 0.68), (fx + 3.5, fy)])
        pygame.draw.polygon(screen, (210, 245, 255),
                            [(fx - 1.8, fy), (fx, fy + length * 0.38), (fx + 1.8, fy)])
        blit_glow(engine_glow, fx, fy + 8)

    # Ship sprite, banking when moving sideways
    angle = -player["tilt"]
    sprite = ship_sprite if abs(angle) < 0.5 else pygame.transform.rotozoom(ship_sprite, angle, 1)
    screen.blit(sprite, sprite.get_rect(center=(int(x), int(y))))

    # Blinking wing lights
    if int(t * 3) % 2 == 0:
        blit_glow(star_glow_small, x - 57, y + 34)
        blit_glow(star_glow_small, x + 57, y + 34)


def draw_enemy(enemy, t):
    key = enemy["max_health"]
    pal = ENEMY_PALETTES[key]
    normal, flash = enemy_sprites[key]

    x = enemy["x"] + math.sin(t * 2.2 + enemy["phase"]) * 3
    y = enemy["y"]

    # Engine flame (points up, enemy flies down)
    fx, fy = x, y - 30
    length = 14 + random.uniform(0, 7)
    pygame.draw.polygon(screen, pal["flame"], [(fx - 7, fy), (fx, fy - length), (fx + 7, fy)])
    pygame.draw.polygon(screen, pal["flame_in"], [(fx - 4, fy), (fx, fy - length * 0.62), (fx + 4, fy)])
    blit_glow(enemy_engine_glow, fx, fy - 6)

    sprite = flash if enemy["flash"] > 0 else normal
    screen.blit(sprite, (int(x) - 60, int(y) - 48))

    # Pulsing eye glow
    pulse = 0.6 + 0.4 * math.sin(t * 6 + enemy["phase"])
    idx = max(0, min(7, int(pulse * 8)))
    blit_glow(enemy_eye_glows[key][idx], x, y + 6)

    # Small health bar for armoured enemies once damaged
    if enemy["max_health"] > 1 and enemy["health"] < enemy["max_health"]:
        bw = 40
        pygame.draw.rect(screen, (40, 40, 55), (x - bw // 2, y - 52, bw, 5), border_radius=2)
        pygame.draw.rect(
            screen, GREEN,
            (x - bw // 2, y - 52, bw * enemy["health"] / enemy["max_health"], 5),
            border_radius=2
        )


def draw_laser(laser):
    x, y = int(laser["x"]), int(laser["y"])
    blit_glow(laser_glow, x, y + 11)
    pygame.draw.rect(screen, CYAN, (x - 3, y, 6, 22), border_radius=3)
    pygame.draw.rect(screen, WHITE, (x - 1, y + 2, 2, 18), border_radius=1)


def draw_enemy_laser(laser):
    x, y = int(laser["x"]), int(laser["y"])
    blit_glow(enemy_laser_glow, x, y + 10)
    pygame.draw.rect(screen, RED, (x - 3, y, 6, 20), border_radius=3)
    pygame.draw.rect(screen, (255, 210, 140), (x - 1, y + 2, 2, 16), border_radius=1)


def create_explosion(x, y, count=26, power=1.0, ring=True):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1, 5) * power
        life = random.randint(18, 40)

        particles.append({
            "x": x,
            "y": y,
            "dx": math.cos(angle) * speed,
            "dy": math.sin(angle) * speed,
            "life": life,
            "max": life,
            "size": random.randint(2, 5)
        })

    if ring:
        rings.append({"x": x, "y": y, "r": 6, "life": 14, "max": 14})


def draw_particles():
    for p in particles:
        frac = p["life"] / p["max"]
        idx = max(0, min(7, int(frac * 8)))
        px, py = int(p["x"]), int(p["y"])
        screen.blit(fire_glows[idx], (px - 12, py - 12), special_flags=ADD)
        col = lerp_color((255, 90, 30), (255, 245, 200), frac)
        pygame.draw.circle(screen, col, (px, py), max(1, int(p["size"] * frac)))


def draw_rings():
    for r in rings:
        frac = r["life"] / r["max"]
        idx = max(0, min(7, int(frac * 8)))
        rx, ry = int(r["x"]), int(r["y"])
        screen.blit(boom_glows[idx], (rx - BOOM_R, ry - BOOM_R), special_flags=ADD)
        col = (int(255 * frac), int(170 * frac), int(80 * frac))
        pygame.draw.circle(screen, col, (rx, ry), int(r["r"]), 2)


def draw_trail():
    for p in trail:
        frac = p["life"] / p["max"]
        idx = max(0, min(7, int(frac * 8)))
        screen.blit(trail_glows[idx], (int(p["x"]) - 8, int(p["y"]) - 8), special_flags=ADD)


def draw_hud():
    score_text = font.render(f"Score: {score}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, WHITE)
    health_text = font.render(f"Health: {player['health']}", True, WHITE)

    screen.blit(score_text, (25, 20))
    screen.blit(level_text, (25, 55))
    screen.blit(health_text, (25, 90))

    # Health bar (colour shifts green -> red as health drops)
    ratio = max(0, player["health"]) / 150
    bar_color = lerp_color((230, 70, 70), (70, 230, 120), min(1.0, ratio * 1.4))
    pygame.draw.rect(screen, (30, 34, 50), (148, 94, 334, 22), border_radius=11)
    if ratio > 0:
        pygame.draw.rect(screen, bar_color, (150, 96, 330 * ratio, 18), border_radius=9)
    pygame.draw.rect(screen, (120, 135, 170), (148, 94, 334, 22), 2, border_radius=11)


# ----------------------------
# SPAWN ENEMY
# ----------------------------
def spawn_enemy():
    hp = 1 if level < 4 else 2
    enemies.append({
        "x": random.randint(60, WIDTH - 60),
        "y": random.randint(-120, -40),
        "speed": random.uniform(1.0, 1.7) + level * 0.08,
        "health": hp,
        "max_health": hp,
        "flash": 0,
        "phase": random.uniform(0, 6.28),
        "shoot_timer": random.randint(100, 180)
    })


# ----------------------------
# RESET GAME
# ----------------------------
def reset_game():
    global score, level, game_over, enemy_timer

    player["x"] = WIDTH // 2
    player["y"] = HEIGHT - 110
    player["health"] = 150
    player["cooldown"] = 0
    player["tilt"] = 0.0

    lasers.clear()
    enemy_lasers.clear()
    enemies.clear()
    particles.clear()
    rings.clear()
    trail.clear()

    score = 0
    level = 1
    enemy_timer = 0
    game_over = False


# ----------------------------
# MAIN LOOP
# ----------------------------
running = True

while running:
    clock.tick(60)
    t = pygame.time.get_ticks() / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if game_over and event.key == pygame.K_r:
                reset_game()

    if not game_over:
        keys = pygame.key.get_pressed()

        go_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        go_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        # Movement
        if go_left:
            player["x"] -= player["speed"]

        if go_right:
            player["x"] += player["speed"]

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player["y"] -= player["speed"]

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            player["y"] += player["speed"]

        # Ship banking
        move_x = (1 if go_right else 0) - (1 if go_left else 0)
        player["tilt"] += (move_x * 14 - player["tilt"]) * 0.18

        # Keep player inside screen
        player["x"] = max(55, min(WIDTH - 55, player["x"]))
        player["y"] = max(80, min(HEIGHT - 70, player["y"]))

        # Engine trail particles
        for nx in (-9, 9):
            if random.random() < 0.8:
                life = random.randint(12, 20)
                trail.append({
                    "x": player["x"] + nx + random.uniform(-1.5, 1.5),
                    "y": player["y"] + 46,
                    "dy": random.uniform(2.0, 4.0),
                    "life": life,
                    "max": life
                })

        # Shoot
        if player["cooldown"] > 0:
            player["cooldown"] -= 1

        if keys[pygame.K_SPACE] and player["cooldown"] == 0:
            lasers.append({
                "x": player["x"],
                "y": player["y"] - 35
            })
            player["cooldown"] = 9

        # Spawn enemies
        enemy_timer += 1
        spawn_delay = max(55, 100 - level * 3)

        if enemy_timer >= spawn_delay:
            spawn_enemy()
            enemy_timer = 0

        # Move player lasers
        for laser in lasers[:]:
            laser["y"] -= 10

            if laser["y"] < -30:
                lasers.remove(laser)

        # Move enemies
        for enemy in enemies[:]:
            enemy["y"] += enemy["speed"]

            if enemy["flash"] > 0:
                enemy["flash"] -= 1

            # Enemy shooting
            enemy["shoot_timer"] -= 1

            if enemy["shoot_timer"] <= 0:
                enemy_lasers.append({
                    "x": enemy["x"],
                    "y": enemy["y"] + 25
                })
                enemy["shoot_timer"] = random.randint(80, 150)

            # Enemy reaches bottom
            if enemy["y"] > HEIGHT + 50:
                enemies.remove(enemy)
                player["health"] -= 5

        # Move enemy lasers
        for laser in enemy_lasers[:]:
            laser["y"] += 5

            if laser["y"] > HEIGHT:
                enemy_lasers.remove(laser)

        # Player laser vs enemies
        for laser in lasers[:]:
            laser_rect = pygame.Rect(
                laser["x"] - 3,
                laser["y"],
                6,
                22
            )

            hit = False

            for enemy in enemies[:]:
                enemy_rect = pygame.Rect(
                    enemy["x"] - 30,
                    enemy["y"] - 35,
                    60,
                    65
                )

                if laser_rect.colliderect(enemy_rect):
                    enemy["health"] -= 1
                    enemy["flash"] = 5
                    hit = True
                    create_explosion(laser["x"], laser["y"], count=6, power=0.5, ring=False)

                    if enemy["health"] <= 0:
                        create_explosion(enemy["x"], enemy["y"])
                        enemies.remove(enemy)
                        score += 10

                        level = score // 100 + 1

                    break

            if hit and laser in lasers:
                lasers.remove(laser)

        # Enemy laser vs player
        player_rect = pygame.Rect(
            player["x"] - 30,
            player["y"] - 35,
            60,
            70
        )

        for laser in enemy_lasers[:]:
            laser_rect = pygame.Rect(
                laser["x"] - 3,
                laser["y"],
                6,
                20
            )

            if laser_rect.colliderect(player_rect):
                player["health"] -= 5
                enemy_lasers.remove(laser)
                create_explosion(laser["x"], laser["y"], count=14, power=0.7)

        # Enemy collision with player
        for enemy in enemies[:]:
            distance = math.hypot(
                enemy["x"] - player["x"],
                enemy["y"] - player["y"]
            )

            if distance < 50:
                player["health"] -= 15
                create_explosion(enemy["x"], enemy["y"], power=1.2)
                enemies.remove(enemy)

        # Particles
        for particle in particles[:]:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["dx"] *= 0.96
            particle["dy"] *= 0.96
            particle["life"] -= 1

            if particle["life"] <= 0:
                particles.remove(particle)

        # Explosion shockwaves
        for r in rings[:]:
            r["r"] += 3.5
            r["life"] -= 1

            if r["life"] <= 0:
                rings.remove(r)

        # Engine trail
        for p in trail[:]:
            p["y"] += p["dy"]
            p["life"] -= 1

            if p["life"] <= 0:
                trail.remove(p)

        # Slow background movement
        for star in stars:
            star["y"] += star["speed"]

            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)

        update_shooting_stars()

        # Game over
        if player["health"] <= 0:
            game_over = True

    # ----------------------------
    # DRAW
    # ----------------------------
    draw_background(t)

    draw_trail()

    for laser in lasers:
        draw_laser(laser)

    for laser in enemy_lasers:
        draw_enemy_laser(laser)

    for enemy in enemies:
        draw_enemy(enemy, t)

    draw_player(t)
    draw_particles()
    draw_rings()
    draw_hud()

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        game_over_text = big_font.render("GAME OVER", True, RED)
        score_text = font.render(
            f"Final Score: {score}",
            True,
            WHITE
        )
        restart_text = font.render(
            "Press R to restart",
            True,
            WHITE
        )

        screen.blit(
            game_over_text,
            game_over_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 - 60)
            )
        )

        screen.blit(
            score_text,
            score_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 5)
            )
        )

        screen.blit(
            restart_text,
            restart_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 55)
            )
        )

    pygame.display.flip()

pygame.quit()