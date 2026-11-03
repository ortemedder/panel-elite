import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak13")
s = open(p, encoding="utf-8").read()
if "def decorate" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- estilo CABINA (decoracion, se cambia en SESION) ----------
STYLE_FILE = "/home/ortem/estilo.txt"

def style_load():
    try:
        return open(STYLE_FILE).read().strip() == "cabina"
    except OSError:
        return False

style = {"cab": style_load(), "view": None, "vt": 0.0, "cache": {}}
STYLE_BTN = pygame.Rect(W - 128, H - 36, 120, 32)
HOLO = (90, 200, 255)

def style_toggle():
    style["cab"] = not style["cab"]
    try:
        with open(STYLE_FILE, "w") as f:
            f.write("cabina" if style["cab"] else "clasico")
    except OSError:
        pass

_orig_rect = pygame.draw.rect

def _cab_rect(surf, col, rect, width=0, border_radius=0, *a, **k):
    """En modo CABINA los rectangulos redondeados pasan a esquinas cortadas."""
    if style["cab"] and border_radius and border_radius > 0:
        r = pygame.Rect(rect)
        c = max(3, min(10, r.h // 3, r.w // 3))
        pts = [(r.x + c, r.y), (r.right - 1, r.y), (r.right - 1, r.bottom - 1 - c),
               (r.right - 1 - c, r.bottom - 1), (r.x, r.bottom - 1), (r.x, r.y + c)]
        return pygame.draw.polygon(surf, col, pts, width)
    return _orig_rect(surf, col, rect, width, border_radius, *a, **k)

pygame.draw.rect = _cab_rect

def _cached(key, make):
    c = style["cache"]
    if key not in c:
        c[key] = make()
    return c[key]

def _scan():
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(0, H, 3):
        pygame.draw.line(s, (0, 0, 0, 55), (0, y), (W, y))
    return s

def _hexes():
    s = pygame.Surface((W, H - TOP), pygame.SRCALPHA)
    r = 16
    dx, dy = r * 1.732, r * 1.5
    for row in range(int((H - TOP) / dy) + 2):
        for col in range(int(W / dx) + 2):
            cx = col * dx + (dx / 2 if row % 2 else 0)
            cy = row * dy
            pts = [(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]
            pygame.draw.polygon(s, (255, 140, 0, 16), pts, 1)
    return s

def _dots():
    s = pygame.Surface((W, H - TOP), pygame.SRCALPHA)
    for y in range(8, H - TOP, 16):
        for x in range(8, W, 16):
            s.set_at((x, y), (255, 140, 0, 60))
    return s

def _tint(col):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((col[0], col[1], col[2], 22))
    return s

def _stars():
    import random
    rnd = random.Random(7)
    return [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(4, 25), rnd.randint(60, 200)) for _ in range(45)]

def decorate(surf):
    now = time.time()
    v = ui["view"]
    splash = now - ui["start"] < 3
    if v == 11 and not splash and not ui["idle_on"]:
        draw_button(surf, STYLE_BTN, "ESTILO", "CABINA" if style["cab"] else "CLÁSICO", F["small"], filled=style["cab"])
    if not style["cab"]:
        return
    with lock:
        d, rx = state["data"], state["rx"]
    online = d is not None and now - rx < 5
    if v != style["view"]:
        style["view"], style["vt"] = v, now
    if ui["idle_on"]:
        # 8: estrellas y marco holografico de la foto
        for x0, y0, sp, b in _cached("stars", _stars):
            x = (x0 + now * sp) % W
            if 130 < x < 450 and 60 < y0 < 280:
                continue
            surf.set_at((int(x), int(y0)), (b, b, b))
        r = pygame.Rect(0, 0, 112, 128); r.center = (70, 160)
        k = 0.5 + 0.5 * math.sin(now * 2)
        col = tuple(int(c * (0.4 + 0.6 * k)) for c in HOLO)
        for (x, y), (sx, sy) in (((r.left, r.top), (1, 1)), ((r.right, r.top), (-1, 1)),
                                 ((r.left, r.bottom), (1, -1)), ((r.right, r.bottom), (-1, -1))):
            pygame.draw.line(surf, col, (x, y), (x + 16 * sx, y), 2)
            pygame.draw.line(surf, col, (x, y), (x, y + 16 * sy), 2)
        yy = r.top + int((now * 40) % r.h)
        pygame.draw.line(surf, col, (r.left + 4, yy), (r.right - 4, yy), 1)
    elif not splash:
        if online:
            flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
            # 6: fondo tenue segun el modo
            ground = f2 & 1 or flags & (1 << 26)
            surf.blit(_cached("dots" if ground else "hex", _dots if ground else _hexes), (0, TOP))
            # 7: tinte segun la situacion
            L = d.get("live") or {}
            hull = (L.get("ship") or {}).get("hull")
            danger = L.get("legal") in ("Wanted", "Hostile", "Warrant") or (hull is not None and hull < 0.3)
            tint = RED if danger else BLUE if flags & 1 else None
            if tint:
                surf.blit(_cached(("tint", tuple(tint[:3])), lambda: _tint(tint)), (0, 0))
                _orig_rect(surf, tint, (0, 0, W, H), 2)
        # 3: barra superior con barrido y piloto de datos
        p = (now * 160) % (W + 200) - 100
        for x in range(0, W, 3):
            b = max(0.25, 1 - abs(x - p) / 90)
            pygame.draw.line(surf, tuple(int(c * b) for c in ORANGE[:3]), (x, TOP - 2), (x + 2, TOP - 2))
        fresh = online and now - rx < 0.6
        pygame.draw.circle(surf, GREEN if fresh else DIM, (W - 5, TOP - 8), 3)
        # 5: barrido al cambiar de pantalla
        dt = now - style["vt"]
        if dt < 0.35:
            x = int(W * dt / 0.35)
            _orig_rect(surf, BLACK, (x, TOP, W - x, H - TOP))
            pygame.draw.line(surf, ORANGE, (x, TOP), (x, H), 2)
    # 2: lineas de escaneo y franja que baja
    surf.blit(_cached("scan", _scan), (0, 0))
    yy = int((now * 35) % H)
    band = _cached("band", lambda: pygame.Surface((W, 3), pygame.SRCALPHA))
    band.fill((255, 170, 60, 28))
    surf.blit(band, (0, yy))

'''
rep("def render(surf):", SNIP + "def render(surf):")
rep("            render(surf)\n", "            render(surf)\n            decorate(surf)\n")
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.13 · 28/10/2026 18:38"', s, count=1)
if not n: print("NO ENCONTRADO: PANEL_VER"); ok = False
L = s.split("\n")
t = next((i for i, l in enumerate(L) if l.strip() == "elif v == 71:"), None)
if t is None:
    print("NO ENCONTRADO: toque"); ok = False
else:
    ind = L[t][:len(L[t]) - len(L[t].lstrip())]
    L[t:t] = [ind + "elif v == 11 and STYLE_BTN.collidepoint(x, y):", ind + "    style_toggle(); return"]
s = "\n".join(L)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
