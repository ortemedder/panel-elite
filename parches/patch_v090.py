#!/usr/bin/env python3
# Parche v0.90: linea de saltos de la ruta, fondo de portanaves al atracar, portanaves de escuadron,
# MENU PRINCIPAL abajo, combate se anula al atracar, SESION TERMINADA 20 s, RECOLECTABLE y valor 0 oculto.
# Va con el sender v0.90. Las fotos fondo_portanaves.jpg y fondo_escuadron.jpg van junto a panel.py.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def draw_routeline" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.89' not in s:
    sys.exit("Este parche es para la v0.89")
shutil.copy(P, P + ".bak89")

def rep(old, new, n=1):
    global s
    if s.count(old) < n:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, n)

# 1. MENU PRINCIPAL en la franja de abajo (no tapa GALNET)
rep('''            put(surf, F["big"], "MENÚ PRINCIPAL", (W // 2, H - 44), GREEN, anchor="center")''',
    '''            pygame.draw.rect(surf, BLACK, (0, H - 18, W, 18))
            put(surf, F["btn"], "MENÚ PRINCIPAL", (W // 2, H - 9), NEON_G, anchor="center")''')

# 2. combate: se anula al pasar a atracado
rep('''def glow_watch(d):
    fl = d.get("Flags", 0)''', '''def glow_watch(d):
    fl = d.get("Flags", 0)
    dk = bool(fl & 1)
    if dk and GLOW.get("dk") is False:
        fight["t"] = 0.0                         # atracado (o reaparecido en estacion): fuera el modo combate
    GLOW["dk"] = dk''')

# 3. SESION TERMINADA: 20 s y se quita al tocar
rep('''            xa["a"] = dict(until=now + 90, col=(90, 200, 255), title="SESIÓN TERMINADA",''',
    '''            xa["a"] = dict(until=now + 20, col=(90, 200, 255), title="SESIÓN TERMINADA",''')
rep('''    if ui.get("shipcard") and time.time() < ui["shipcard"]:
        ui["shipcard"] = 0; return''', '''    if ui.get("shipcard") and time.time() < ui["shipcard"]:
        ui["shipcard"] = 0; return
    if xa.get("a") and xa["a"].get("title") == "SESIÓN TERMINADA" and time.time() < xa["a"]["until"]:
        xa["a"] = None; return''')

# 4. valor de la nave: oculto si viene a cero (Operations)
rep('''("VALOR", f"{crx(c.get('value') or 0)}")]''', '''("VALOR", f"{crx(c.get('value') or 0)}")]
    stats = [x for x in stats if x[0] != "VALOR" or c.get("value")]''')
rep('''("VALOR", f"{crx(c.get('value') or 0)} cr")]''', '''("VALOR", f"{crx(c.get('value') or 0)} cr")]
    stats = [x for x in stats if x[0] != "VALOR" or c.get("value")]''')

# 5. RECOLECTABLE en verde neon
rep('''    put(surf, F["btn"], "RECOGIBLE" if ok else "NO RECOGIBLE", (x, y), GREEN if ok else RED); y += 26''',
    '''    put(surf, F["btn"], "RECOLECTABLE" if ok else "NO RECOLECTABLE", (x, y), NEON_G if ok else RED); y += 26''')
rep('''no hay estrellas recogibles"''', '''no hay estrellas recolectables"''')
rep('''{'RECOGIBLE' if scoop else 'NO RECOGIBLE'}''', '''{'RECOLECTABLE' if scoop else 'NO RECOLECTABLE'}''')

# 6. linea de saltos en NAVEGACION (la lista de abajo pasa a 3 sistemas)
rep('''    y += 30
    pygame.draw.line(surf, DIM, (8, y - 4), (W - 8, y - 4))
    if route:''', '''    y += 30
    y = draw_routeline(surf, d or {}, y, time.time())
    pygame.draw.line(surf, DIM, (8, y - 4), (W - 8, y - 4))
    if route:''')
rep('''        for n, (name, c) in enumerate(route[:5]):''', '''        for n, (name, c) in enumerate(route[:3]):''')
rep('''f"RUTA  -  destino: {route[-1][0]}"''', '''f"RUTA  -  destino: {((d or {}).get('routeend') or route[-1])[0]}"''')

# 7. fondo de portanaves en el atraque
rep('''    pad, stype = st.get("pad"), st.get("type")
    cx, cy, rad = 118, (H + TOP) // 2 + 4, 108''', '''    pad, stype = st.get("pad"), st.get("type")
    carrier_bg(surf, d or {}, st)
    cx, cy, rad = 118, (H + TOP) // 2 + 4, 108''')

CODE = r'''
# ---------- v0.90: linea de ruta, fondos de portanaves y portanaves de escuadron ----------
NEON_G = (57, 255, 20)

def star_kind(c):
    c = c or ""
    if c == "N":
        return "neu"
    if c.startswith("D"):
        return "wd"
    if not c:
        return "?"
    return "ok" if star_ok(c) else "no"

def draw_routeline(surf, d, y, now):
    """Circulos de la ruta: amarillo recolectable, rojo no, azul parpadeando neutrones, blanco parpadeando enana blanca."""
    route = d.get("route") or []
    if not route:
        return y
    total = d.get("routen") or len(route)
    end = d.get("routeend") or route[-1]
    nodes = [[d.get("system") or "?", d.get("curstar")]] + [list(r) for r in route[:9]]
    gap = total > 9
    if gap:
        nodes = nodes[:9] + [list(end)]
    on = int(now * 3) % 2 == 0
    x0, x1, cy = 20, W - 20, y + 12
    n = len(nodes)
    step = (x1 - x0) / max(1, n - 1)
    xs = [int(x0 + i * step) for i in range(n)] if n > 1 else [x0]
    for i in range(n - 1):
        if gap and i == n - 2:
            for k in range(xs[i] + 8, xs[i + 1] - 6, 6):
                pygame.draw.line(surf, DIM, (k, cy), (k + 2, cy), 2)
        else:
            pygame.draw.line(surf, DIM, (xs[i], cy), (xs[i + 1], cy), 2)
    for i, (name, c) in enumerate(nodes):
        k = star_kind(c)
        col = {"ok": YELLOW, "no": RED, "neu": BLUE if on else DIM, "wd": WHITE if on else DIM, "?": DIM}[k]
        r = 9 if i == 0 else 7 if i < n - 1 or not gap else 8
        pygame.draw.circle(surf, col, (xs[i], cy), r)
        if i == 0:
            pygame.draw.circle(surf, ORANGE, (xs[i], cy), r + 4, 2)
        if i == n - 1:
            pygame.draw.circle(surf, GREEN, (xs[i], cy), r + 4, 2)
    y += 28
    nxt = route[0][0] if route else ""
    put(surf, F["small"], f"{(d.get('system') or '?')}  >  {nxt}", (8, y), ORANGE, W - 150)
    put(surf, F["small"], f"quedan {total}" + (f" · {end[0]}" if end and total > 1 else ""), (W - 8, y), DIM, 140, anchor="topright")
    return y + 22

_BG = {}
BG_FILES = {"fc": "fondo_portanaves.jpg", "sq": "fondo_escuadron.jpg"}

def carrier_kind(d, st):
    stype = (st.get("type") or "")
    mid = st.get("mid")
    sq, own = d.get("sqcarrier") or {}, d.get("carrier") or {}
    if "squadron" in stype.lower() or (mid and mid == sq.get("id")):
        return "sq", "PORTANAVES DE ESCUADRÓN", BLUE
    if stype == "FleetCarrier":
        return "fc", ("TU PORTANAVES" if mid and mid == own.get("id") else "PORTANAVES"), ORANGE
    return None, "", None

def carrier_bg(surf, d, st):
    """Al pedir atraque en un portanaves: su foto de fondo (oscurecida) y el rotulo."""
    if st.get("status") not in ("SOLICITADO", "CONCEDIDO"):
        return
    k, label, col = carrier_kind(d, st)
    if not k:
        return
    real = surf.real if type(surf).__name__ == "ScaledSurf" else surf
    w, h = real.get_size()
    top = int(TOP * h / H)
    key = (k, w, h)
    if key not in _BG:
        img = None
        try:
            src = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), BG_FILES[k])).convert()
            sw, sh = src.get_size()
            sc = max(w / sw, (h - top) / sh)
            img = pygame.transform.smoothscale(src, (int(sw * sc) + 1, int(sh * sc) + 1))
            img = img.subsurface(pygame.Rect((img.get_width() - w) // 2, (img.get_height() - (h - top)) // 2, w, h - top)).copy()
            img.fill((95, 95, 95), special_flags=pygame.BLEND_MULT)
        except Exception as e:
            log_exc("fondo portanaves", e)
        _BG[key] = img
    if _BG[key] is not None:
        real.blit(_BG[key], (0, top))
    put(surf, F["big"], label, (8, H - 30), col, W - 16)

def view_carrier90(surf, d, flags, now):
    view_carrier(surf, d, flags, now)
    sq = (d or {}).get("sqcarrier") or {}
    if sq.get("system"):
        pygame.draw.rect(surf, BLACK, (0, H - 24, W, 24))
        pygame.draw.line(surf, DIM, (8, H - 24), (W - 8, H - 24))
        put(surf, F["small"], "PORTANAVES DE ESCUADRÓN", (8, H - 18), BLUE)
        put(surf, F["btn"], sq["system"], (W - 8, H - 21), BLUE, W - 200, anchor="topright")

VIEWS[126] = view_carrier90

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")

rep('''# Enlace energético''', '''# Novedades v0.90
- NAVEGACIÓN: línea de saltos con hasta 10 estrellas (amarillo recolectable, rojo no, azul parpadeando neutrones, blanco parpadeando enana blanca), con la actual → la siguiente y los saltos que quedan. Avanza con cada salto.
- Atraque en un portanaves: su foto de fondo (fondo_portanaves.jpg o fondo_escuadron.jpg junto a panel.py) y el rótulo TU PORTANAVES / PORTANAVES DE ESCUADRÓN / PORTANAVES.
- PORTANAVES: tu portanaves ya no sale en el sistema del de escuadrón; abajo, el sistema del PORTANAVES DE ESCUADRÓN.
- MENÚ PRINCIPAL abajo en la pantalla de inicio; al atracar se quita el modo combate; SESIÓN TERMINADA 20 s (toca para quitarla); RECOLECTABLE en verde neón; la ficha de nave no enseña valor 0.
# Enlace energético''')
rep('    ("0.89", "Transporte reservado y a bordo, totales de carrera, destello de luces, nave en la carga de Operations"),\n',
    '    ("0.89", "Transporte reservado y a bordo, totales de carrera, destello de luces, nave en la carga de Operations"),\n'
    '    ("0.90", "Línea de saltos, fondos de portanaves, portanaves de escuadrón y arreglos"),\n')
s = re.sub(r'PANEL_VER = "v0\.89[^"]*"', 'PANEL_VER = "v0.90 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.90  (copia en " + P + ".bak89)")
