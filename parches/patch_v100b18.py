#!/usr/bin/env python3
# Parche v1.0 beta 18 (desde la beta 17b): ACTIVIDAD GALACTICA con fondo nuevo y vistas GALAXIA / COLONIA / SOL,
# SISTEMAS CONTROLADOS con todos y desplazamiento con el dedo, COMBATE que no se abre al despegar ni al atracar,
# boton BORRAR de recompensas sin cobrar y fondo del atraque a 80. Necesita el sender v1.0b12.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def act_view_b18" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b17b', s):
    sys.exit("Este parche es para la v1.0 beta 17b")
shutil.copy(P, P + ".bak100b17b")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep("BG_DOCK_DARK = 75", "BG_DOCK_DARK = 80")
# tactil HDMI: arrastrar el dedo (para la lista de SISTEMAS CONTROLADOS)
rep('''                    if ev.value == 1:
                        t_down, pos = time.time(), None
                    elif t_down is not None:
                        dur = time.time() - t_down; t_down = None
                        if pos is None:
                            continue
                        if dur >= 1.2:''', '''                    if ev.value == 1:
                        t_down, pos = time.time(), None
                        DRAG.update(on=False, p0=None, last=None)
                    elif t_down is not None:
                        dur = time.time() - t_down; t_down = None
                        if pos is None:
                            continue
                        if DRAG.get("on"):                       # b18: era un arrastre, no un toque
                            drag_end(); continue
                        if dur >= 1.2:''')
rep('''                elif ev.type == ec.EV_SYN and t_down is not None and pos is None:
                    pos = ((rx - ax.min) / max(1, ax.max - ax.min), (ry - ay.min) / max(1, ay.max - ay.min))''',
    '''                elif ev.type == ec.EV_SYN and t_down is not None and pos is None:
                    pos = ((rx - ax.min) / max(1, ax.max - ax.min), (ry - ay.min) / max(1, ay.max - ay.min))
                elif ev.type == ec.EV_SYN and t_down is not None:
                    drag_move(pos, ((rx - ax.min) / max(1, ax.max - ax.min), (ry - ay.min) / max(1, ay.max - ay.min)))''')
# radar: SISTEMAS CONTROLADOS con todos, desplazables
rep('''    put(surf, F["small"], "SISTEMAS CONTROLADOS", (X, y), DIM); y += 16
    for v in sorted([v for v in S if v.get("ctrl")], key=lambda v: -v["inf"]):
        if y + 14 > H - 44:
            break
        g = gap(v)''', '''    put(surf, F["small"], "SISTEMAS CONTROLADOS", (X, y), DIM); y += 16
    CTL_LIST.update(r=pygame.Rect(X, y, W - X - 6, H - 44 - y))
    ctl_ = sorted([v for v in S if v.get("ctrl")], key=lambda v: -v["inf"])
    vis_n = max(1, (H - 44 - y) // 14)
    CTL_LIST["max"] = max(0, len(ctl_) - vis_n) * 14
    off_ = max(0, min(CTL_LIST.get("off", 0), CTL_LIST["max"]))
    CTL_LIST["off"] = off_
    if CTL_LIST["max"]:
        tr_ = pygame.Rect(W - 5, y, 3, vis_n * 14)
        pygame.draw.rect(surf, (40, 26, 8), tr_)
        hh_ = max(8, tr_.h * vis_n // len(ctl_))
        pygame.draw.rect(surf, ORANGE, (tr_.x, tr_.y + int((tr_.h - hh_) * off_ / CTL_LIST["max"]), 3, hh_))
    CTL_ROWS.clear()
    first_ = off_ // 14
    for v in ctl_[first_:first_ + vis_n]:
        if y + 14 > H - 44:
            break
        CTL_ROWS.append((pygame.Rect(X, y, W - X - 8, 14), v["sys"]))
        g = gap(v)''')

CODE = r'''
# ---------- v1.0 beta 18 ----------
# --- arrastrar el dedo en la lista de SISTEMAS CONTROLADOS (radar) ---
DRAG = {"on": False, "p0": None, "last": None}
CTL_LIST = {"r": None, "off": 0, "max": 0, "seen": 0}
CTL_ROWS = []

def _to_panel(p):
    """Toque de la HDMI (0..1) a coordenadas del panel, si se esta viendo el panel."""
    if not hdmi_panel():
        return None
    bw, bh = BIG["w"] or 1024, BIG["h"] or 600
    sc = min(bw / W, bh / H)
    ox, oy = (bw - W * sc) / 2, (bh - H * sc) / 2
    return ((p[0] * bw - ox) / sc, (p[1] * bh - oy) / sc)

def drag_move(p0, p):
    a, b = _to_panel(p0) if p0 else None, _to_panel(p)
    if not a or not b:
        return
    r = CTL_LIST.get("r")
    radar_on = ui.get("view") == 77 or (ui.get("idle_on") and IDLE_MODE.get("m") == "fac")
    if not r or not radar_on or not r.collidepoint(a) or not CTL_LIST.get("max"):
        return
    if not DRAG["on"]:
        if abs(b[1] - a[1]) < 12:                       # menos de 12 px: todavia es un toque
            return
        DRAG.update(on=True, last=b[1], off0=CTL_LIST.get("off", 0), y0=a[1])
    CTL_LIST["off"] = max(0, min(CTL_LIST["max"], DRAG["off0"] - (b[1] - DRAG["y0"])))
    CTL_LIST["seen"] = time.time()
    ui["idle_skip"] = ui.get("idle_skip", 0)
    TAP_EV.set()

def drag_end():
    DRAG.update(on=False)
    TAP_EV.set()

_draw_fac_b18 = draw_fac_screen

def draw_fac_screen(surf, now):
    if now - CTL_LIST.get("seen", 0) > 30 and ui.get("view") != 77:
        CTL_LIST["off"] = 0                              # en la espera vuelve arriba
    _draw_fac_b18(surf, now)

# --- ACTIVIDAD GALACTICA: fondo con brillo y nebulosa calida, vistas GALAXIA / COLONIA / SOL ---
ACT_MODE = ["gal"]
ACT_MODES = [("gal", "GALAXIA"), ("col", "COLONIA"), ("sol", "SOL")]
ACT_BTN = [pygame.Rect(236 + i * 58, 29, 54, 18) for i in range(3)]
_act_view_b18 = act_view
_GBG = {}

def act_view_b18(M, mode):
    if mode in ("col", "sol"):
        cx_, cz_, hw = (-9530, 19808, 1800) if mode == "col" else (0, 0, 350)
        X0, X1, Z0, Z1 = cx_ - hw, cx_ + hw, cz_ - hw * 0.87, cz_ + hw * 0.87
        sc = min(M.w / (X1 - X0), M.h / (Z1 - Z0))
        cx, cz = (X0 + X1) / 2, (Z0 + Z1) / 2
        return (lambda x, z: (M.centerx + (x - cx) * sc, M.centery - (z - cz) * sc)), sc
    return _act_view_b18(M, mode != "zona")

act_view = act_view_b18

def act_bg(surf, M, mode):
    real, rr = (surf.real, surf._r(M)) if type(surf).__name__ == "ScaledSurf" else (surf, pygame.Rect(M))
    key = (rr.w, rr.h, mode)
    if key not in _GBG:
        import random as _r
        bg = pygame.Surface(rr.size); bg.fill(BLACK)
        loc = pygame.Rect(0, 0, rr.w, rr.h)
        pt, sc = act_view_b18(loc, mode)
        if mode == "gal":
            neb = pygame.Surface(rr.size, pygame.SRCALPHA)
            rad = max(4, int(rr.w / 40))
            for x, z, b in gal_points()[::3]:
                px, py = pt(x, z)
                if 0 <= px < rr.w and 0 <= py < rr.h:
                    pygame.draw.circle(neb, (150, 80, 25, 9), (int(px), int(py)), rad)
            bg.blit(neb, (0, 0))
            cx, cy = pt(25, 25900)
            glow = pygame.Surface(rr.size, pygame.SRCALPHA)
            R = int(rr.w * 0.16)
            for k_ in range(R, 0, -max(1, R // 40)):
                pygame.draw.circle(glow, (255, 190, 120, int(70 * (1 - k_ / R) ** 1.6)), (int(cx), int(cy)), k_)
            bg.blit(glow, (0, 0))
            for x, z, b in gal_points():
                px, py = pt(x, z)
                if 0 <= px < rr.w and 0 <= py < rr.h:
                    bb = min(255, int(b * 2.0))
                    bg.fill((bb, int(bb * 0.75), int(bb * 0.55)), (int(px), int(py), 2, 2))
        else:                                            # de cerca: campo de estrellas y una neblina suave
            rnd = _r.Random(11 if mode == "col" else 7)
            glow = pygame.Surface(rr.size, pygame.SRCALPHA)
            for k_ in range(18):
                gx, gy, gr = rnd.randrange(rr.w), rnd.randrange(rr.h), rnd.randrange(rr.w // 8, rr.w // 3)
                pygame.draw.circle(glow, (150, 80, 25, 7) if mode == "col" else (120, 70, 30, 6), (gx, gy), gr)
            bg.blit(glow, (0, 0))
            for k_ in range(rr.w * rr.h // 900):
                b = rnd.randint(40, 170)
                bg.fill((b, int(b * 0.8), int(b * 0.65)), (rnd.randrange(rr.w), rnd.randrange(rr.h), 1 + (b > 150), 1 + (b > 150)))
        _GBG[key] = bg
    real.blit(_GBG[key], rr.topleft)

def draw_act_screen(surf, now):
    ACT["want"] = now
    surf.fill(BLACK)
    fixed = IDLEHOLD["m"] == "act" or ui.get("view") == 78
    mode = ACT_MODE[0] if fixed else ("gal", "sol", "col")[int(now // 10) % 3]   # en espera: 10 s cada vista
    put(surf, F["big"], "ACTIVIDAD GALÁCTICA", (10, 6), ORANGE)
    put(surf, F["small"], "en directo desde EDDN" if ACT["on"] else "conectando con EDDN…" if act_ok() else "falta python3-zmq en la Pi",
        (10, 32), DIM if act_ok() else RED, 220)
    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 56, 8), ORANGE, anchor="topright")
    for i, (k, lab) in enumerate(ACT_MODES):
        b = ACT_BTN[i]; sel = k == mode
        pygame.draw.rect(surf, ORANGE if sel else BLACK, b, border_radius=4)
        pygame.draw.rect(surf, ORANGE, b, 1, border_radius=4)
        put(surf, F["tiny"], lab, b.center, BLACK if sel else ORANGE, b.w - 4, anchor="center")
    pygame.draw.line(surf, ORANGE, (6, 50), (W - 6, 50), 1)
    M = pygame.Rect(6, 54, 300, 262)
    act_bg(surf, M, mode)
    pygame.draw.rect(surf, DIM, M, 1, border_radius=4)
    pt, sc = act_view_b18(M, mode)
    old = surf.get_clip(); surf.set_clip(M)
    marks = {"gal": (("SOL", 0, 0), ("COLONIA", -9530, 19808), ("SAG A*", 25, 25900)),
             "col": (("COLONIA", -9530, 19808),), "sol": (("SOL", 0, 0),)}[mode]
    for n, x, z in marks:
        px, py = pt(x, z); pygame.draw.circle(surf, DIM, (int(px), int(py)), 3, 1)
        put(surf, F["tiny"], n, (int(px) + 5, int(py) - 6), (200, 160, 110))
    if mode == "sol":                                    # vuestros sistemas en naranja
        used = []
        for n, v in sorted(((FACD["data"] or {}).get("sistemas") or {}).items(), key=lambda kv: -(kv[1].get("inf") or 0)):
            if v.get("pos") and None not in v["pos"] and not v.get("fuera") and v.get("inf"):
                px, py = pt(v["pos"][0], v["pos"][2])
                if not M.collidepoint(px, py):
                    continue
                pygame.draw.circle(surf, ORANGE if v.get("ctrl") else (120, 80, 30), (int(px), int(py)), 3, 0 if v.get("ctrl") else 1)
                if v.get("ctrl"):
                    nm = n if len(n) <= 14 else n[:13] + "…"
                    lr = pygame.Rect(int(px) + 5, int(py) - 6, tw_(F["tiny"], nm), 12)
                    if not M.contains(lr):
                        lr.right = int(px) - 5
                    if M.contains(lr) and not any(lr.colliderect(u) for u in used):
                        used.append(lr); put(surf, F["tiny"], nm, lr.topleft, (200, 140, 60))
    for x, z, t, mine in list(ACT["pings"]):
        age = now - t
        if age > 1.6 or age < 0:
            continue
        px, py = pt(x, z)
        if not M.collidepoint(px, py):
            continue
        col = ORANGE if mine else (90, 200, 255)
        f_ = max(0.0, 1 - age / 1.6)
        pygame.draw.circle(surf, tuple(int(c * f_) for c in col), (int(px), int(py)), int(2 + age * 10), 1)
        if age < 0.4:
            pygame.draw.circle(surf, col, (int(px), int(py)), 2)
    act_hit_draw(surf, M, pt, now)
    surf.set_clip(old)
    X, y = 314, 58
    j = ACT["jumps"]
    pm = sum(1 for t in j if now - t < 60)
    cm = sum(1 for t in ACT["uids"].values() if now - t < 300)
    put(surf, F["small"], "SALTOS POR MINUTO", (X, y), DIM); y += 14
    put(surf, F["num"], str(pm), (W - 8, y), BLUE, anchor="topright"); y += 44
    put(surf, F["small"], "COMANDANTES (5 MIN)", (X, y), DIM); y += 14
    put(surf, F["big"], str(cm), (W - 8, y), WHITE, anchor="topright"); y += 30
    hoyk = time.strftime("%Y-%m-%d", time.gmtime())
    ent = sum(((v.get("trafico") or {}).get(hoyk, 0)) for v in ((FACD["data"] or {}).get("sistemas") or {}).values())
    put(surf, F["small"], "TUS SISTEMAS HOY", (X, y), DIM); put(surf, F["big"], str(ent), (W - 8, y + 10), ORANGE, anchor="topright")
    nv = ACT_DAY.get(hoyk, 0)
    put(surf, F["tiny"], f"comandantes · {nv} salto{'' if nv == 1 else 's'} visto{'' if nv == 1 else 's'}", (X, y + 40), DIM, W - X - 8); y += 54
    pygame.draw.line(surf, DIM, (X, y), (W - 6, y)); y += 4
    put(surf, F["small"], "ÚLTIMOS SALTOS", (X, y), DIM); y += 15
    for nm, mine, t in list(ACT["feed"])[:5]:
        put(surf, F["tiny"], nm, (X, y), ORANGE if mine else WHITE, 120)
        put(surf, F["tiny"], f"{max(0, int(now - t))} s", (W - 8, y), DIM, anchor="topright"); y += 13

# --- COMBATE: no al despegar (1 min tras cualquier despegue) ni «te atacan» al atracar ---
UNDK = {"t": 0, "dock": False}
_combat_ok_b18 = combat_music_ok

def combat_music_ok(text):
    if time.time() - UNDK["t"] < 60:
        return False, "recién despegado"
    return _combat_ok_b18(text)

_handle_note_b18 = handle_note

def handle_note(kind, text):
    if kind == "underattack":
        d = state.get("data") or {}
        st = (d.get("station") or {}).get("status")
        if d.get("Flags", 0) & 3 or st in ("SOLICITADO", "CONCEDIDO", "ATRACADO") or time.time() - UNDK["t"] < 60:
            v0 = ui.get("view")
            _handle_note_b18(kind, text)                 # el aviso sale igual
            if ui.get("view") != v0:
                ui["view"] = v0
                plog("Te atacan al atracar o despegar: aviso sin cambiar a COMBATE")
            return
    _handle_note_b18(kind, text)

# --- recompensas sin cobrar: boton BORRAR (en 11 DIA) ---
LEDB = {"r": None, "sure": 0}
_view11_b18 = VIEWS[11]

def view11_b18(surf, d, flags, now):
    _view11_b18(surf, d, flags, now)
    LEDB["r"] = None
    if ui.get("sesstab"):
        return
    led = ((d or {}).get("footcz") or {}).get("led") or {}
    if not led.get("cr"):
        return
    r = pygame.Rect(W - 104, H - 56, 98, 22)
    sure = time.time() < LEDB["sure"]
    draw_button(surf, r, "¿SEGURO?" if sure else "BORRAR", None, F["small"], filled=sure, compact=True)
    LEDB["r"] = r

VIEWS[11] = view11_b18

def led_clear():
    pc = pc_addr()
    if not pc:
        set_alert("NO SÉ LA IP DEL PC", "el sender no está enviando", RED, 3); return
    try:
        so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        so.sendto(b"ELITEPANEL-LEDGERCLR", (pc, 5006)); so.close()
        set_alert("RECOMPENSAS BORRADAS", "lo pendiente de cobrar vuelve a cero (sender v1.0b12)", GREEN, 4, kind="info")
    except OSError as e:
        set_alert("NO SE PUDO BORRAR", str(e)[:40], RED, 3)

_render_b18 = render

def render(surf):
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d is not None and time.time() - rx < 5:
            dk = bool(d.get("Flags", 0) & 3)
            if UNDK["dock"] and not dk:
                UNDK["t"] = time.time()                  # acaba de despegar
            UNDK["dock"] = dk
    except Exception:
        pass
    return _render_b18(surf)

_on_tap_b18 = on_tap

def on_tap(x, y):
    if DRAG.get("on"):
        return
    v = ui.get("view")
    if v == 11 and LEDB.get("r") and LEDB["r"].collidepoint(x, y):
        if time.time() < LEDB["sure"]:
            LEDB["sure"] = 0; led_clear()
        else:
            LEDB["sure"] = time.time() + 3
        TAP_EV.set(); return
    act_vis = v == 78 or (ui.get("idle_on") and IDLE_MODE.get("m") == "act")
    if act_vis and not (ui.get("alert") and time.time() < ui["alert"]["until"]):
        for i, b in enumerate(ACT_BTN):
            if b.inflate(4, 8).collidepoint(x, y):
                ACT_MODE[0] = ACT_MODES[i][0]
                if ui.get("idle_on"):
                    IDLEHOLD["m"] = "act"                # en la espera: se queda fija en esa vista
                TAP_EV.set(); return
        if ACT_MAP.collidepoint(x, y) and (v == 78 or IDLEHOLD["m"] == "act"):
            k = [m for m, _ in ACT_MODES].index(ACT_MODE[0]) if ACT_MODE[0] in [m for m, _ in ACT_MODES] else 0
            ACT_MODE[0] = ACT_MODES[(k + 1) % 3][0]; TAP_EV.set(); return
    radar_vis = v == 77 or (ui.get("idle_on") and IDLE_MODE.get("m") == "fac")
    if radar_vis:
        for r, n in CTL_ROWS:
            if r.collidepoint(x, y):
                ui["idle_skip"] = time.time() + 60
                ui["facsys"] = n; ui["facback"] = 77; ui["view"] = 194; TAP_EV.set(); return
    _on_tap_b18(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 17b''', '''# Novedades v1.0 beta 18
- ACTIVIDAD GALÁCTICA: fondo nuevo (estrellas más brillantes, neblina naranja en los brazos y núcleo iluminado) y tres botones arriba: GALAXIA, COLONIA y SOL (vuestros sistemas salen en SOL). En la espera rota entre las tres; tocar un botón la deja fija.
- Radar de la facción: SISTEMAS CONTROLADOS con todos; con el dedo se sube y baja por la lista (barrita a la derecha). Tocar un sistema abre su ficha.
- COMBATE no se abre por la música en el minuto siguiente a cualquier despegue, y «te atacan» al atracar o despegar avisa sin cambiar de pantalla.
- 11 DÍA: botón BORRAR (dos toques) para poner a cero lo sin cobrar si se ha quedado mal (sender v1.0b12).
- Fotos de fondo del atraque a 80.
# Novedades v1.0 beta 17b''')
rep('    ("1.0b17b", ', '    ("1.0b18", "ACTIVIDAD con fondo nuevo y GALAXIA/COLONIA/SOL, controlados con el dedo, COMBATE al despegar, BORRAR recompensas"),\n    ("1.0b17b", ')
s = re.sub(r'PANEL_VER = "v1\.0b17b[^"]*"', 'PANEL_VER = "v1.0b18 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 18  (copia en " + P + ".bak100b17b)")
