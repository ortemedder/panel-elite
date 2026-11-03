import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak45")
s = open(p, encoding="utf-8").read()
if "def decorate_big" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- estilo CABINA tambien en la pantalla grande ----------
def _bpat(w, h, ground):
    sf = pygame.Surface((w, h), pygame.SRCALPHA)
    if ground:
        for y in range(8, h, 20):
            for x in range(8, w, 20):
                sf.set_at((x, y), (255, 140, 0, 60))
    else:
        r = 22
        dx, dy = r * 1.732, r * 1.5
        for row in range(int(h / dy) + 2):
            for col in range(int(w / dx) + 2):
                cx = col * dx + (dx / 2 if row % 2 else 0)
                cy = row * dy
                pts = [(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]
                pygame.draw.polygon(sf, (255, 140, 0, 16), pts, 1)
    return sf

def _bscan(w, h):
    sf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 3):
        pygame.draw.line(sf, (0, 0, 0, 55), (0, y), (w, y))
    return sf

def _btint(w, h, col):
    sf = pygame.Surface((w, h), pygame.SRCALPHA)
    sf.fill((col[0], col[1], col[2], 22))
    return sf

def decorate_big(S):
    if not style["cab"]:
        return
    now = time.time()
    w, h = S.get_size()
    hh = 44
    with lock:
        d, rx = state["data"], state["rx"]
    online = d is not None and now - rx < 5
    if online and now - ui["start"] >= 3:
        flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
        ground = bool(f2 & 1 or flags & (1 << 26))
        S.blit(_cached(("bpat", ground, w, h), lambda: _bpat(w, h - hh, ground)), (0, hh))
        L = d.get("live") or {}
        hull = (L.get("ship") or {}).get("hull")
        danger = L.get("legal") in ("Wanted", "Hostile", "Warrant") or (hull is not None and hull < 0.3)
        tint = RED if danger else BLUE if flags & 1 else None
        if tint:
            S.blit(_cached(("btint", tuple(tint[:3]), w, h), lambda: _btint(w, h, tint)), (0, 0))
            _orig_rect(S, tint, (0, 0, w, h), 3)
        p_ = (now * 300) % (w + 300) - 150
        for x in range(0, w, 4):
            b = max(0.25, 1 - abs(x - p_) / 150)
            pygame.draw.line(S, tuple(int(c * b) for c in ORANGE[:3]), (x, hh - 2), (x + 3, hh - 2))
        pygame.draw.circle(S, GREEN if now - rx < 0.6 else DIM, (w - 6, 6), 4)
    S.blit(_cached(("bscan", w, h), lambda: _bscan(w, h)), (0, 0))
    band = _cached(("bband", w), lambda: pygame.Surface((w, 4), pygame.SRCALPHA))
    band.fill((255, 170, 60, 28))
    S.blit(band, (0, int((now * 60) % h)))

'''
rep("def render(surf):", SNIP + "def render(surf):")
rep("        render_big()\n", '        render_big()\n        decorate_big(BIG["surf"])\n')
rep('    ("0.44", "Esta lista de versiones"),\n]', '    ("0.44", "Esta lista de versiones"),\n    ("0.45", "Estilo CABINA también en la pantalla grande"),\n]')
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.45 · 29/10/2026 13:20"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
