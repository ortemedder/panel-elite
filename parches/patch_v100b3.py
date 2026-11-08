#!/usr/bin/env python3
# Parche v1.0 beta 3 (desde la beta 2):
#  - teclas por la red tambien si la Pi tiene teclado USB pero no esta enchufada al PC
#  - VIAJES: mapa de tus saltos (pestana en NAVEGACION y cuadro de la HDMI)
#  - COMBATE + CAZA: pantalla doble mientras el caza esta lanzado
#  - tick del BGS y cambios desde tu ultima visita (pantalla del sistema)
#  - LOG: cuantas veces ha reiniciado hoy el vigilante
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def view_viajes" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v1.0b2' not in s:
    sys.exit("Este parche es para la v1.0 beta 2")
shutil.copy(P, P + ".bak100b2")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('''    if not os.path.exists("/dev/hidg0"):
        pc = state.get("pc")
        if not pc:''', '''    if not hid_ok():
        pc = pc_addr()
        if not pc:''')
rep('''    cells = list(BIG_SETS[mode])\n''', '''    cells = list(BIG_SETS[mode])
    if mode == "COMBATE" and fighter_out(d) and 6 in cells:
        cells[cells.index(6)] = 191                  # caza lanzado: COMBATE + CAZA\n''')

CODE = r'''
# ---------- v1.0 beta 3 ----------
def hid_ok():
    """Teclado USB listo: existe /dev/hidg0 y el PC lo tiene conectado."""
    if not os.path.exists("/dev/hidg0"):
        return False
    st = []
    for f in glob.glob("/sys/class/udc/*/state"):
        try:
            st.append(open(f).read().strip())
        except OSError:
            pass
    return not st or "configured" in st

def pc_addr():
    try:
        pc = open(os.path.join(PANEL_DIR, "pc_ip.txt")).read().strip()
        if pc:
            return pc
    except OSError:
        pass
    return state.get("pc")

def fighter_out(d):
    return ((d or {}).get("fighter") or {}).get("state") == "out" and not (d or {}).get("Flags2", 0) & 1

# --- VIAJES ---
MENU[190] = "VIAJES"
PARENT[190] = 0
TABS[0].append((190, "VIAJES"))
BIG_SETS["VIAJE"] = [100, 3, 190, 72]
VJ_PER = [("7", "1 SEM"), ("30", "1 MES"), ("90", "3 MESES"), ("all", "TODO")]
GAL_C = (25.2, 25899.0)                              # Sagittarius A*

def vj_btn(i):
    return pygame.Rect(4 + i * 95, H - 28, 91, 25)

def _vj_view(nodes, cur, mode, M):
    """Zona visible: 'gal' = toda la galaxia; 'zona' = donde mas has estado alrededor de donde estas."""
    if mode == "gal":
        x0, x1, z0, z1 = -45000, 45000, -20000, 70000
    else:
        ref = next((n for n in nodes if n[0] and n[0] == cur), None) or max(nodes, key=lambda n: n[3])
        tot = sum(n[3] for n in nodes) or 1
        acc, sel = 0, []
        for n in sorted(nodes, key=lambda n: math.hypot(n[1] - ref[1], n[2] - ref[2])):
            sel.append(n); acc += n[3]
            if acc >= tot * 0.85 and len(sel) >= 2:
                break
        xs = [n[1] for n in sel]; zs = [n[2] for n in sel]
        x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
        sz = max(x1 - x0, z1 - z0, 20) * 0.55
        cx_, cz_ = (x0 + x1) / 2, (z0 + z1) / 2
        x0, x1, z0, z1 = cx_ - sz, cx_ + sz, cz_ - sz, cz_ + sz
    sc = min(M.w / max(1, x1 - x0), M.h / max(1, z1 - z0))
    cx_, cz_ = (x0 + x1) / 2, (z0 + z1) / 2
    return lambda x, z: (M.centerx + (x - cx_) * sc, M.centery - (z - cz_) * sc), sc

def view_viajes(surf, d, flags, now):
    V = (d or {}).get("viajes") or {}
    per = ui.get("vjp", "30"); zm = ui.get("vjz", "zona")
    for i, (k, lab) in enumerate(VJ_PER):
        draw_button(surf, vj_btn(i), lab, "", F["small"], filled=k == per, compact=True)
    draw_button(surf, vj_btn(4), "GALAXIA" if zm == "gal" else "ZONA", "", F["small"], filled=False, compact=True)
    D = V.get(per)
    M = pygame.Rect(4, TOP + 2, W - 8, H - TOP - 34)
    pygame.draw.rect(surf, DIM, M, 1, border_radius=4)
    if not D or not D.get("n"):
        put(surf, F["btn"], "sin saltos en este periodo" if V else "esperando datos del sender", M.center, DIM, anchor="center")
        return
    nodes, edges, cur = D["n"], D["e"], D.get("cur")
    pt, sc = _vj_view(nodes, cur, zm, M.inflate(-30, -36).move(0, -2))
    old_clip = surf.get_clip(); surf.set_clip(M)
    if zm == "gal":
        c = pt(*GAL_C)
        pygame.draw.circle(surf, (45, 30, 10), (int(c[0]), int(c[1])), max(2, int(45000 * sc)), 1)
        pygame.draw.circle(surf, (70, 45, 15), (int(c[0]), int(c[1])), max(2, int(4000 * sc)))
    P_ = [pt(n[1], n[2]) for n in nodes]
    mx = max([e[2] for e in edges] or [1])
    outs = []
    for i, j, c, h in sorted(edges, key=lambda e: e[2]):
        a, b = P_[i], P_[j]
        w = 1 + round(4 * (c - 1) / max(1, mx - 1))
        col = ORANGE if c > 1 else (150, 80, 0)
        cl = M.clipline(a, b)
        if not cl:
            continue
        pygame.draw.line(surf, col, cl[0], cl[1], w)
        ina, inb = M.collidepoint(a), M.collidepoint(b)
        if ina != inb:                               # sale del mapa: flecha y a donde va
            far, edge_pt = (nodes[j], cl[1]) if ina else (nodes[i], cl[0])
            outs.append((far, edge_pt, h))
        elif h >= 5 and math.dist(a, b) > 70:
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            put(surf, F["small"], f"{h} saltos", (mid[0] + 4, mid[1] - 14), DIM)
    for k, n in enumerate(nodes):
        x, y = P_[k]
        if M.collidepoint(x, y):
            r = 2 + min(3, n[3] // 2)
            pygame.draw.circle(surf, WHITE if n[4] else (160, 160, 160), (int(x), int(y)), r + (1 if n[4] else 0))
    used = []
    def label(txt, x, y, col):
        tw, th = F["small"].size(txt)
        for dx, dy in ((9, -th // 2), (-9 - tw, -th // 2), (-tw // 2, -th - 8), (-tw // 2, 8), (9, -th - 4), (9, 4), (-9 - tw, 4)):
            r = pygame.Rect(int(x + dx), int(y + dy), tw, th)
            if M.contains(r) and not any(r.colliderect(u) for u in used):
                used.append(r.inflate(4, 2)); pygame.draw.rect(surf, BLACK, r.inflate(4, 0))
                put(surf, F["small"], txt, r.topleft, col); return True
        return False
    ci = next((k for k, n in enumerate(nodes) if n[0] and n[0] == cur), None)
    if ci is not None and M.collidepoint(P_[ci]):
        x, y = P_[ci]
        pygame.draw.circle(surf, BLUE, (int(x), int(y)), 7 if int(now * 2) % 2 else 9, 2)
        label(cur.upper()[:20], x, y, BLUE)
    for k in sorted(range(len(nodes)), key=lambda k: -nodes[k][3])[:6]:
        n = nodes[k]
        if n[0] and k != ci and M.collidepoint(P_[k]):
            label(n[0].upper()[:18], *P_[k], WHITE)
    ref = nodes[ci] if ci is not None else max(nodes, key=lambda n: n[3])
    seen = set()
    for far, (ex, ey), h in sorted(outs, key=lambda o: -math.hypot(o[0][1] - ref[1], o[0][2] - ref[2])):
        key = far[0] or (round(far[1]), round(far[2]))
        if key in seen or len(seen) >= 4:
            continue
        seen.add(key)
        dist = math.hypot(far[1] - ref[1], far[2] - ref[2])
        pygame.draw.circle(surf, ORANGE, (int(ex), int(ey)), 4)
        label(f"» {(far[0] or 'destino').upper()[:14]} {dist:,.0f} al".replace(",", "."), ex, ey, ORANGE)
    surf.set_clip(old_clip)
    st_ = f"{D['j']} SALTOS · {D['ly']:,} al · {D['s']} SISTEMAS".replace(",", ".")
    r_ = pygame.Rect(M.x + 3, M.bottom - 17, F["small"].size(st_)[0] + 8, 15)
    pygame.draw.rect(surf, BLACK, r_)
    put(surf, F["small"], st_, (r_.x + 4, r_.y + 1), DIM)

VIEWS[190] = view_viajes

# --- COMBATE + CAZA ---
MENU[191] = "COMBATE + CAZA"
PARENT[191] = 0
CC_L = ["OBJETIVO", "SIGUIENTE", "SUBSIST.", "DISIPADOR", "CHAFF", "ESCUDO"]
CC_R = ["ATACAR", "ALTO FUEGO", "DEFENSIVO", "AGRESIVO", "SEGUIRME", "VOLVER"]
CC_TOP = TOP + 70

def cc_rect(side, k):
    bh = (H - CC_TOP - 4) // 3
    bw = (W // 2 - 12) // 2
    x0 = 4 if side == 0 else W // 2 + 6
    return pygame.Rect(x0 + (k % 2) * (bw + 4), CC_TOP + (k // 2) * bh, bw, bh - 4)

def view_cc(surf, d, flags, now):
    d = d or {}
    t = d.get("target") or {}
    card = pygame.Rect(4, TOP + 2, W - 8, 62)
    pygame.draw.rect(surf, DIM, card, 1, border_radius=6)
    if t:
        put(surf, F["btn"], (t.get("ship") or "?").upper(), (12, TOP + 6), ORANGE, 150)
        lg = t.get("legal") or ""
        bits = [x for x in (t.get("pilot"), "BUSCADO" if lg.lower() == "wanted" else "") if x]
        put(surf, F["small"], " · ".join(bits), (168, TOP + 9), RED if "BUSCADO" in bits else WHITE, 125)
        bar(surf, 12, TOP + 28, 200, "ESCUDO", t.get("shield"), BLUE)
        bar(surf, 12, TOP + 46, 200, "CASCO", t.get("hull"), ORANGE)
        if t.get("t"):
            ago = int(pc_now(d, now) - t["t"])
            put(surf, F["small"], f"hace {ago} s" if ago < 120 else f"hace {ago // 60} min", (220, TOP + 46), DIM)
    else:
        put(surf, F["btn"], "SIN OBJETIVO", (150, TOP + 24), DIM, anchor="center")
    pygame.draw.line(surf, DIM, (300, TOP + 8), (300, TOP + 58))
    f = d.get("fighter") or {}
    txt, col = FIGHTER_STATE.get(f.get("state"), ("SIN DATOS", DIM))
    put(surf, F["small"], "CAZA", (310, TOP + 8), DIM)
    put(surf, F["btn"], txt, (310, TOP + 22), col, W - 320)
    if f.get("pilot") and f.get("state") == "out":
        put(surf, F["small"], f"Piloto: {f['pilot']}", (310, TOP + 44), ORANGE, W - 320)
    cb = dict(COMBAT_BTNS)
    for k, lab in enumerate(CC_L):
        draw_button(surf, cc_rect(0, k), lab, (cb.get(lab) or "").upper(), F["btn"], lit=flash.get((191, k), 0) > now)
    pygame.draw.line(surf, ORANGE, (W // 2, CC_TOP), (W // 2, H - 6), 2)
    fb = {b[0]: (i, b) for i, b in enumerate(FIGHTER_BTNS)}
    for k, lab in enumerate(CC_R):
        i, b = fb.get(lab, (None, (lab, "", None)))
        draw_button(surf, cc_rect(1, k), lab, (b[1] or "").replace("KP", "NUM "), F["btn"],
                    filled=b[2] is not None and ui["orders"].get(b[2]) == i, lit=flash.get((191, 10 + k), 0) > now)

VIEWS[191] = view_cc
AUTO_VIEW["fighter"] = 191

_on_tap_b3 = on_tap

def on_tap(x, y):
    v = ui.get("view")
    if v == 190 and y >= H - 30:
        for i in range(5):
            if vj_btn(i).collidepoint(x, y):
                if i < 4:
                    ui["vjp"] = VJ_PER[i][0]
                else:
                    ui["vjz"] = "zona" if ui.get("vjz", "zona") == "gal" else "gal"
                TAP_EV.set(); return
    if v == 191:
        cb = dict(COMBAT_BTNS)
        for k, lab in enumerate(CC_L):
            if cc_rect(0, k).collidepoint(x, y) and cb.get(lab):
                tap_flash((191, k)); press_seq([cb[lab]]); return
        for k, lab in enumerate(CC_R):
            if cc_rect(1, k).collidepoint(x, y):
                for i, (txt, key, grp) in enumerate(FIGHTER_BTNS):
                    if txt == lab:
                        tap_flash((191, 10 + k)); press_seq([key])
                        if grp:
                            ui["orders"][grp] = i
                            if txt == "VOLVER":
                                ui["orders"].pop("a", None)
                return
    _on_tap_b3(x, y)

_big_mode_b3 = big_mode

def big_mode(d, flags):
    m = _big_mode_b3(d, flags)
    if fighter_out(d) and m not in ("COMBATE A PIE", "ATRAQUE"):
        return "COMBATE"                             # caza lanzado: no se quita el modo combate
    return m

_handle_note_b3 = handle_note

def handle_note(kind, text):
    _handle_note_b3(kind, text)
    if ui.get("view") in (6, 9) and fighter_out(state.get("data")) and kind in ("underattack", "fighter", "combatmusic"):
        ui["view"] = 191

# --- tick del BGS ---
EV_LIST.append(("bgstick", "TICK DEL BGS"))
BGT = {"last": None}

def bgs_lines(d, now):
    out = []
    tk = (d or {}).get("tick")
    if tk:
        ago = max(0, int(pc_now(d, now) - tk))
        out.append((f"ÚLTIMO TICK hace {ago // 3600} h {ago % 3600 // 60:02d} min ({time.strftime('%H:%M', time.localtime(tk))})", BLUE))
    b = (d or {}).get("bgsv") or {}
    if b.get("prev"):
        days = (pc_now(d, now) - b["prev"]) / 86400
        cuando = "hoy" if days < 1 else f"hace {days:.0f} día{'s' if days >= 1.5 else ''}"
        out.append(("BGS ACTUALIZADO desde tu última visita (" + cuando + ")" if b.get("chg") else
                    "BGS sin cambios desde tu última visita (" + cuando + ")", GREEN if b.get("chg") else DIM))
    return out

_view_pol_b3 = view_pol

def view_pol(surf, d, flags, now):
    _view_pol_b3(surf, d, flags, now)
    L = bgs_lines(d, now)
    y = H - 4 - 15 * len(L)
    if L:
        pygame.draw.rect(surf, BLACK, (0, y - 2, W, H - y + 2))
    for txt, col in L:
        put(surf, F["small"], txt, (8, y), col, W - 16); y += 15

def bgs_watch(d, now):
    tk = (d or {}).get("tick")
    if not tk:
        return
    if BGT["last"] is not None and tk > BGT["last"] and ev_on("bgstick"):
        k0 = XA_K[0]
        try:
            XA_K[0] = "bgstick"
            set_alert("TICK DEL BGS", "influencias y estados actualizados", BLUE, 6)
            play("ok")
        finally:
            XA_K[0] = k0
    BGT["last"] = tk

# --- LOG: reinicios del vigilante hoy ---
WDN = {"t": 0, "n": 0}

def wd_today():
    if time.time() - WDN["t"] > 60:
        WDN["t"] = time.time()
        hoy = time.strftime("%d/%m ")
        n = 0
        for f in (PANEL_LOG, PANEL_LOG + ".1"):
            try:
                with open(f, encoding="utf-8", errors="ignore") as fh:
                    n += sum(1 for l in fh if l.startswith(hoy) and "PANEL COLGADO" in l)
            except OSError:
                pass
        WDN["n"] = n
    return WDN["n"]

_view_log_b3 = VIEWS.get(121)

def view_log_b3(surf, d, flags, now):
    if _view_log_b3:
        _view_log_b3(surf, d, flags, now)
    n = wd_today()
    if n:
        t = f" el vigilante reinició el panel {n} {'vez' if n == 1 else 'veces'} hoy "
        r = pygame.Rect(0, 0, F["small"].size(t)[0] + 8, 18); r.topright = (W - 4, TOP + 2)
        pygame.draw.rect(surf, BLACK, r); pygame.draw.rect(surf, RED, r, 1, border_radius=3)
        put(surf, F["small"], t, r.center, RED, anchor="center")

if _view_log_b3:
    VIEWS[121] = view_log_b3

_render_b3 = render

def render(surf):
    try:
        with lock:
            d_ = state["data"]
        bgs_watch(d_, time.time())
    except Exception:
        pass
    return _render_b3(surf)

'''
# va al final, justo antes de main(), para envolver render despues de todo lo demas
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 3
- Teclas por la red: si la Pi no está enchufada al PC por USB, los botones mandan las teclas por wifi al sender (hace falta el sender v1.0b3).
- VIAJES (pestaña en NAVEGACIÓN y cuadro de la pantalla grande en VIAJE): mapa de tus saltos; la línea es más gruesa cuanto más repites la ruta. 1 SEM / 1 MES / 3 MESES / TODO y ZONA / GALAXIA. Los viajes largos van en una línea con el número de saltos; si se salen del mapa, flecha con el destino y la distancia.
- COMBATE + CAZA: sale al lanzar el caza. Objetivo arriba (escudo, casco y hace cuánto se escaneó), 6 teclas de combate y 6 órdenes al caza. Mientras el caza está fuera, la pantalla grande sigue en COMBATE.
- Pantalla del sistema: hora del último tick del BGS y si el BGS ha cambiado desde tu última visita. Aviso TICK DEL BGS.
- Merc Coin: el «+N» es lo ganado hoy.
- LOG: aviso si el vigilante ha reiniciado el panel hoy.
# Enlace energético''')
rep('    ("1.0b2", ', '    ("1.0b3", "VIAJES, COMBATE + CAZA, tick del BGS, teclas por red sin USB"),\n    ("1.0b2", ')
s = re.sub(r'PANEL_VER = "v1\.0b2[^"]*"', 'PANEL_VER = "v1.0b3 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 3  (copia en " + P + ".bak100b2)")
