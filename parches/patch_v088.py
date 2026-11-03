#!/usr/bin/env python3
# Parche v0.88: fichas NAVE y FLOTA, pantalla completa al cambiar de nave, transferencias, modulos danados,
# caza y chips de SRV / caza en EN VIVO. Va con el sender v0.88.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def view_ship" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.87' not in s:
    sys.exit("Este parche es para la v0.87")
shutil.copy(P, P + ".bak87")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# --- avisos nuevos en ALERTAS
rep('''           ("thargmusic", "MÚSICA THARGOIDE")]''', '''           ("thargmusic", "MÚSICA THARGOIDE"), ("shipswap", "CAMBIO DE NAVE"), ("shipxfer", "TRANSFERENCIA NAVE"),
           ("shiparrived", "NAVE TRANSFERIDA"), ("moddmg", "MÓDULOS DAÑADOS")]''')

# --- toques: cerrar la ficha grande; nombre de la nave en EN VIVO -> NAVE
rep('''    if kill_tap(x, y):
        return''', '''    if kill_tap(x, y):
        return
    if ui.get("shipcard") and time.time() < ui["shipcard"]:
        ui["shipcard"] = 0; return''')
rep('''    elif (v == 100 and NAVE_BTN.collidepoint(x, y)) or (v == 73 and NAVE_BTN_BIO.collidepoint(x, y)):''',
    '''    elif v == 100 and SHIP_NAME_R.collidepoint(x, y) and not ((state.get("data") or {}).get("Flags2", 0) & 1):
        ui["view"] = 170; return
    elif v in (170, 171):
        ui["shippage"] = ui.get("shippage", 0) + 1; return
    elif (v == 100 and NAVE_BTN.collidepoint(x, y)) or (v == 73 and NAVE_BTN_BIO.collidepoint(x, y)):''')

# --- chips de SRV y caza en EN VIVO nave
rep('''        chips(surf, ([(f"RHINO {rh}" if rh != "SIN RHINO" else rh, rh in ("A BORDO", "SIN RHINO", "FUERA"), rcol)] if rh else []) + [''',
    '''        chips(surf, ([(f"RHINO {rh}" if rh != "SIN RHINO" else rh, rh in ("A BORDO", "SIN RHINO", "FUERA"), rcol)] if rh else []) + veh_chips(d, rh) + [''')

# --- pantalla completa al cambiar de nave (las dos pantallas)
rep('''    draw_hpcrit(surf, now)''', '''    draw_shipcard(surf, now)
    draw_hpcrit(surf, now)''')
rep('''        draw_kill_cell(time.time())''', '''        draw_kill_cell(time.time())
        draw_shipcard(BIG["surf"], time.time())''')

# --- avisos
rep('''        elif kind == "gravity" and len(p) >= 2:''', '''        elif kind == "shipswap":
            ui["shipcard"] = now + 15; ui["shippage"] = 0
        elif kind == "shipxfer" and len(p) >= 2:
            sec = int(p[1] or 0)
            xa["a"] = dict(until=now + 6, col=BLUE, title="TRANSFERENCIA EN CAMINO", big=p[0].upper(),
                           lines=[f"llega en {sec // 3600} h {sec % 3600 // 60} min" if sec >= 3600 else f"llega en {sec // 60} min"])
        elif kind == "shiparrived" and len(p) >= 2:
            xa["a"] = dict(until=now + 8, col=GREEN, title="NAVE TRANSFERIDA", big=f"TU {p[0].upper()} YA ESTÁ",
                           lines=[f"en {p[1]}" if p[1] else ""])
            play("ok")
        elif kind == "moddmg" and len(p) >= 2:
            xa["a"] = dict(until=now + 8, col=ORANGE, title="MÓDULOS DAÑADOS (< 80 %)", big=f"{p[0]} MÓDULO" + ("S" if p[0] != "1" else ""),
                           lines=[p[1], "repara en una estación"])
        elif kind == "gravity" and len(p) >= 2:''')

CODE = r'''
# ---------- v0.88: NAVE, FLOTA y cambio de nave ----------
SHIP_NAME_R = pygame.Rect(W - 260, TOP, 260, 34)
SHIP_PER = 8

def veh_chips(d, rh):
    v = ((d or {}).get("naves") or {}).get("veh") or {}
    out = []
    if v.get("srvcap") and not rh and v.get("srv"):
        n = max(0, v["srvcap"] - (v.get("srvlost") or 0))
        st = v["srv"]
        lab = f"SRV A BORDO {n}/{v['srvcap']}" if st == "A BORDO" else ("SIN SRV" if n == 0 else f"SRV {st}")
        out.append((lab, True, GREEN if st == "A BORDO" and n else RED if n == 0 else ORANGE))
    if v.get("fighter"):
        f = v["fighter"]
        out.append((f"CAZA {f}", True, GREEN if f == "LISTO" else RED if f == "RECONSTRUYENDO" else ORANGE))
    return out

def _mod_col(h):
    return RED if h < 80 else ORANGE if h < 95 else GREEN

def view_ship(surf, d, flags, now):
    N = (d or {}).get("naves") or {}
    c = N.get("cur")
    if not c:
        put(surf, F["btn"], "Sin datos de la nave", (W // 2, (H + TOP) // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], "llegan al cargar la partida o al equiparla (sender v0.88)", (W // 2, (H + TOP) // 2 + 12), DIM, anchor="center")
        return
    y = TOP + 4
    put(surf, F["big"], (c.get("ship") or "?").upper(), (8, y), ORANGE, W // 2)
    put(surf, F["small"], " · ".join(x for x in (c.get("name"), c.get("ident")) if x), (W - 8, y + 6), DIM, W // 2 - 10, anchor="topright")
    y += 28
    stats = [("SALTO", f"{c['jump']:.1f} al" if c.get("jump") else "-"), ("COMB.", f"{c.get('fuel') or 0:g} t"),
             ("CARGA", f"{c.get('cargo') or 0} t"), ("MASA", f"{c.get('mass') or 0:.0f} t"), ("VALOR", f"{crx(c.get('value') or 0)}")]
    cw = (W - 16) // len(stats)
    for i, (k, v) in enumerate(stats):
        put(surf, F["small"], k, (8 + i * cw, y), DIM)
        put(surf, F["btn"], v.replace(".", ","), (8 + i * cw, y + 12), WHITE, cw - 4)
    y += 36
    fb = c.get("fbay")
    if fb:
        crew = ((d.get("ops") or {}).get("crew") or {})
        fs = (N.get("veh") or {}).get("fighter") or "-"
        put(surf, F["small"], f"HANGAR DE CAZAS · caza {fs}" + (f" · piloto {crew.get('name')}" if crew.get("name") else ""),
            (8, y), BLUE, W - 16); y += 16
    mods = sorted(c.get("mods") or [], key=lambda m: m["h"] >= 80)          # danados arriba
    pages = max(1, (len(mods) + SHIP_PER - 1) // SHIP_PER)
    pg = ui.get("shippage", 0) % pages
    for m in mods[pg * SHIP_PER:(pg + 1) * SHIP_PER]:
        put(surf, F["small"], m.get("s") or "", (8, y + 1), DIM)
        w_ = put(surf, F["btn"], m["n"], (34, y - 2), RED if m["h"] < 80 else ORANGE, 220)
        if m.get("e"):
            put(surf, F["small"], m["e"], (40 + max(w_, 0), y + 1), BLUE, W - 100 - w_)
        put(surf, F["small"], f"{m['h']}%", (W - 8, y + 1), _mod_col(m["h"]), anchor="topright")
        y += 20
    put(surf, F["small"], f"pág {pg + 1}/{pages}  ·  toca para pasar" if pages > 1 else f"{len(mods)} módulos",
        (W - 8, H - 16), DIM, anchor="topright")

def view_fleet(surf, d, flags, now):
    N = (d or {}).get("naves") or {}
    y = TOP + 4
    for x in N.get("xfer") or []:
        left = max(0, int(x.get("arrive", now) - time.time()))
        put(surf, F["small"], f"EN CAMINO: {x.get('ship', '?')} > {x.get('to') or '?'}  ·  quedan "
                              f"{left // 3600} h {left % 3600 // 60} min" if left >= 3600 else
                              f"EN CAMINO: {x.get('ship', '?')} > {x.get('to') or '?'}  ·  quedan {left // 60} min {left % 60} s",
            (8, y), BLUE, W - 16); y += 16
    fl = N.get("fleet") or []
    if not fl:
        put(surf, F["btn"], "Abre el astillero en una estación", (W // 2, (H + TOP) // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], "y el panel guardará dónde están tus naves", (W // 2, (H + TOP) // 2 + 12), DIM, anchor="center")
        return
    t = N.get("fleet_t")
    put(surf, F["small"], f"{len(fl)} naves guardadas" + (f" · astillero del {time.strftime('%d/%m %H:%M', time.localtime(t))}" if t else ""),
        (8, y), DIM, W - 16); y += 16
    put(surf, F["small"], "SALTO  CARGA  ARMAS", (W - 8, y), DIM, anchor="topright"); y += 14
    per = 6
    pages = max(1, (len(fl) + per - 1) // per)
    pg = ui.get("shippage", 0) % pages
    fl = sorted(fl, key=lambda f: (not f.get("here"), f.get("transit", False), f.get("sys") or ""))
    for f in fl[pg * per:(pg + 1) * per]:
        nm = f.get("name") or ""
        put(surf, F["btn"], (f.get("ship") or "?") + (f" «{nm}»" if nm and nm != f.get("ship") else ""), (8, y), ORANGE, W - 170)
        sub = "AQUÍ" if f.get("here") else ("en tránsito" if f.get("transit") else f.get("sys") or "?")
        if not f.get("here") and f.get("xtime"):
            sec = int(f["xtime"])
            sub += f"  ·  traer: {sec // 3600} h {sec % 3600 // 60} min · {crx(f.get('xprice') or 0)} cr"
        put(surf, F["small"], sub, (8, y + 18), GREEN if f.get("here") else DIM, W - 16)
        cols = [f"{f['jump']:.0f}" if f.get("jump") else "-", f"{f['cargo']}" if f.get("cargo") is not None else "-",
                f"{f['weapons']}" if f.get("weapons") is not None else "-"]
        put(surf, F["btn"], "   ".join(cols), (W - 8, y), WHITE, 160, anchor="topright")
        y += 34
    if pages > 1:
        put(surf, F["small"], f"pág {pg + 1}/{pages}  ·  toca", (W - 8, H - 16), DIM, anchor="topright")

VIEWS[170] = view_ship
VIEWS[171] = view_fleet
MENU[170] = "NAVE"
MENU[171] = "FLOTA"
PARENT[170] = 100
PARENT[171] = 100
TABS.append([(170, "NAVE"), (171, "FLOTA")])
_SCF = {}

def draw_shipcard(surf, now):
    """Al cambiar de nave: todos sus datos a pantalla completa sobre fondo negro (15 s o hasta tocar)."""
    if not ui.get("shipcard") or now > ui["shipcard"]:
        return
    with lock:
        c = ((state["data"] or {}).get("naves") or {}).get("cur")
    if not c:
        return
    w, h = surf.get_size()
    k = h / 320
    key = round(k, 2)
    if key not in _SCF:
        _SCF[key] = [pygame.font.Font(None, int(n * k)) for n in (52, 26, 20, 16)]
    f1, f2, f3, f4 = _SCF[key] if type(surf).__name__ != "ScaledSurf" else (F["num"], F["big"], F["btn"], F["small"])
    surf.fill(BLACK)
    m_ = int(8 * k)
    y = m_
    put(surf, f1, (c.get("ship") or "?").upper(), (m_, y), ORANGE, w - 2 * m_); y += f1.get_height()
    put(surf, f2, " · ".join(x for x in (c.get("name"), c.get("ident")) if x), (m_, y), WHITE, w - 2 * m_); y += f2.get_height() + int(4 * k)
    stats = [("SALTO", f"{c['jump']:.1f} al" if c.get("jump") else "-"), ("COMBUSTIBLE", f"{c.get('fuel') or 0:g} t"),
             ("CARGA", f"{c.get('cargo') or 0} t"), ("MASA", f"{c.get('mass') or 0:.0f} t"), ("VALOR", f"{crx(c.get('value') or 0)} cr")]
    cw = (w - 2 * m_) // len(stats)
    for i, (a, b) in enumerate(stats):
        put(surf, f4, a, (m_ + i * cw, y), DIM)
        put(surf, f2, b.replace(".", ","), (m_ + i * cw, y + f4.get_height()), GREEN, cw - 4)
    y += f4.get_height() + f2.get_height() + int(6 * k)
    pygame.draw.line(surf, DIM, (m_, y), (w - m_, y)); y += int(4 * k)
    mods = c.get("mods") or []
    col_w = (w - 3 * m_) // 2
    lh = f3.get_height() + 1
    rows = max(1, (h - y - f4.get_height() - m_) // lh)
    for i, md in enumerate(mods[:rows * 2]):
        x = m_ + (i // rows) * (col_w + m_)
        yy = y + (i % rows) * lh
        tw = put(surf, f3, f"{md.get('s') or ''} {md['n']}".strip(), (x, yy), RED if md["h"] < 80 else ORANGE, int(col_w * 0.55))
        if md.get("e"):
            put(surf, f4, md["e"], (x + tw + int(6 * k), yy + int(3 * k)), BLUE, col_w - tw - int(50 * k))
        put(surf, f4, f"{md['h']}%", (x + col_w, yy + int(3 * k)), _mod_col(md["h"]), anchor="topright")
    put(surf, f4, "NAVE NUEVA  ·  toca para cerrar", (w - m_, h - m_ - f4.get_height()), DIM, anchor="topright")

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")

rep('''# Enlace energético''', '''# Naves (v0.88, con el sender v0.88)
- Toca el nombre de la nave en EN VIVO: pestañas NAVE (salto, combustible, carga, masa, valor y todos los módulos con su ingeniería y salud; los dañados arriba en rojo) y FLOTA (dónde está cada nave, traer: tiempo y precio, y salto, carga y armas para comparar).
- Al cambiar de nave salen todos sus datos a pantalla completa 15 segundos (toca para cerrar).
- Avisos: transferencia en camino, NAVE TRANSFERIDA al llegar y módulos por debajo del 80 %.
- En EN VIVO nave: SRV A BORDO 2/2, SRV FUERA, CAZA LISTO, CAZA RECONSTRUYENDO...
- El sender guarda tus naves en naves.json (junto a elite_sender.py); la FLOTA se actualiza al abrir el astillero.
# Enlace energético''')
rep('    ("0.87", "Objetivos CERRADOS, bajas en un cuadro, combate de nave manda, Inara del CMDR fijado, EDSM y arreglos"),\n',
    '    ("0.87", "Objetivos CERRADOS, bajas en un cuadro, combate de nave manda, Inara del CMDR fijado, EDSM y arreglos"),\n'
    '    ("0.88", "Fichas NAVE y FLOTA, nave nueva a pantalla completa, transferencias, módulos dañados, SRV y caza"),\n')
s = re.sub(r'PANEL_VER = "v0\.87[^"]*"', 'PANEL_VER = "v0.88 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.88  (copia en " + P + ".bak87)")
