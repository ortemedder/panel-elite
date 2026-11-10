#!/usr/bin/env python3
# Parche v1.0 beta 19 (desde la beta 18): voz con las abreviaturas completas, velocimetro cerca de los planetas
# (nave: reloj de arco junto al altimetro; SRV y Rhino: reloj, km/h y brujula), aviso BAJANDO RAPIDO CERCA DEL SUELO,
# caja negra al ser destruido y avisos repetidos agrupados. El sender no cambia (v1.0b12).
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def spd_track" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b18 ', s):
    sys.exit("Este parche es para la v1.0 beta 18")
shutil.copy(P, P + ".bak100b18")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

CODE = r'''
# ---------- v1.0 beta 19 ----------
# --- voz: las abreviaturas, completas ---
_voz_txt_b19 = voz_txt

def voz_txt(t):
    t = _voz_txt_b19(t)
    t = re.sub(r"#\d+", "", t)
    n_ = r"(\d+(?:[.,]\d+)?)\s*"
    for pat, rep_ in ((n_ + r"m/s\b", r"\1 metros por segundo"), (n_ + r"km\b", r"\1 kilómetros"), (n_ + r"ls\b", r"\1 segundos luz"),
                      (n_ + r"al\b", r"\1 años luz"), (n_ + r"t\b", r"\1 toneladas"), (n_ + r"M\b", r"\1 millones"), (n_ + r"k\b", r"\1 mil")):
        t = re.sub(pat, rep_, t)
    t = re.sub(r"\bZC\b", "zona de conflicto", t)
    return re.sub(r"\bcmdrs?\b", "comandantes", t, flags=re.I)

# --- velocidad cerca de un planeta (con latitud, longitud y radio que manda el sender) ---
SPDH = deque(maxlen=40)                                  # (hora, lat, lon, alt)
SPD = {"gs": None, "vmax": {}}
SHIP_VMAX = {"sidewinder": 320, "eagle": 350, "hauler": 270, "adder": 300, "viper": 400, "cobra": 400, "vulture": 355,
             "asp": 340, "python": 300, "type-6": 300, "type6": 300, "type-7": 250, "type7": 250, "type-8": 260, "type8": 260,
             "type-9": 200, "type9": 200, "type-10": 220, "type10": 220, "anaconda": 250, "cutter": 320, "corvette": 260,
             "krait": 330, "mamba": 420, "fer-de-lance": 400, "ferdelance": 400, "chieftain": 330, "challenger": 300,
             "crusader": 300, "dolphin": 350, "orca": 380, "beluga": 290, "keelback": 300, "courier": 380, "clipper": 380,
             "diamondback": 340, "panther": 230, "mandalay": 330, "corsair": 330, "kestrel": 400, "python mk ii": 330}

def _geo(d):
    b = (d or {}).get("bio") or {}
    return b.get("lat"), b.get("lon"), b.get("R"), b.get("hdg")

def spd_track(d, now):
    lat, lon, R, hdg = _geo(d)
    alt = ((d or {}).get("live") or {}).get("alt")
    if lat is None or lon is None or not R:
        SPDH.clear(); SPD["gs"] = None; return
    if not SPDH or (SPDH[-1][1], SPDH[-1][2]) != (lat, lon) or now - SPDH[-1][0] > 1:
        SPDH.append((now, lat, lon, alt or 0))
    old = [p for p in SPDH if SPDH[-1][0] - p[0] <= 2.5]
    t0, a0, o0, h0 = old[0]
    t1, a1, o1, h1 = SPDH[-1]
    if t1 - t0 < 0.5:
        return
    p0, p1 = math.radians(a0), math.radians(a1)
    dl = math.radians(o1 - o0)
    c = math.sin((p1 - p0) / 2) ** 2 + math.cos(p0) * math.cos(p1) * math.sin(dl / 2) ** 2
    dist = 2 * (R + max(0, h1)) * math.asin(min(1.0, math.sqrt(c)))
    SPD["gs"] = dist / (t1 - t0)

def ship_vmax(d):
    sh = (((d or {}).get("live") or {}).get("ship") or {})
    n = (sh.get("ship") or "").lower()
    v = next((v for k, v in sorted(SHIP_VMAX.items(), key=lambda kv: -len(kv[0])) if k in n), 400)
    return max(200, int(math.ceil(v * 1.25 / 100.0)) * 100)

def in_srv(d):
    return bool((d or {}).get("Flags", 0) & (1 << 26))

def srv_name(d):
    t = ((d or {}).get("srvtype") or "SRV").upper()
    return "RHINO" if "RHINO" in t else t

def draw_arc(surf, cx, cy, R, v, vmax, step, bands, label, now, sub=None):
    a0, a1 = math.radians(150), math.radians(390)
    ang = lambda x: a0 + (a1 - a0) * min(1.0, max(0.0, x / vmax))
    pygame.draw.circle(surf, (14, 14, 16), (cx, cy), R + 3)
    for lo, hi, col in bands:
        n_ = 24
        for k in range(n_ + 1):
            x = lo + (hi - lo) * k / n_
            a = ang(x)
            pygame.draw.line(surf, col, (cx + (R - 2) * math.cos(a), cy + (R - 2) * math.sin(a)), (cx + (R - 6) * math.cos(a), cy + (R - 6) * math.sin(a)), 2)
    k = 0
    while k <= vmax + 1e-6:
        a = ang(k)
        pygame.draw.line(surf, WHITE, (cx + (R - 7) * math.cos(a), cy + (R - 7) * math.sin(a)), (cx + (R - 12) * math.cos(a), cy + (R - 12) * math.sin(a)), 1)
        put(surf, F["tiny"], str(int(k)), (int(cx + (R - 20) * math.cos(a)), int(cy + (R - 20) * math.sin(a))), WHITE, anchor="center")
        k += step
    put(surf, F["tiny"], label, (cx, cy - R // 3), DIM, anchor="center")
    if v is not None:
        a = ang(v)
        pygame.draw.line(surf, ORANGE, (cx, cy), (cx + (R - 9) * math.cos(a), cy + (R - 9) * math.sin(a)), 3)
        put(surf, F["big"], f"{v:.0f}", (cx, cy + R // 2), ORANGE, anchor="center")
    else:
        put(surf, F["small"], "—", (cx, cy + R // 2), DIM, anchor="center")
    pygame.draw.circle(surf, (60, 60, 60), (cx, cy), 4)
    put(surf, F["tiny"], "m/s" if sub is None else sub, (cx, cy + R // 2 + 14), DIM, anchor="center")

def draw_hdg_compass(surf, cx, cy, R, hdg):
    pygame.draw.circle(surf, (14, 14, 16), (cx, cy), R); pygame.draw.circle(surf, (80, 80, 86), (cx, cy), R, 1)
    for i, lab in enumerate("NESO"):
        a = math.radians(i * 90 - 90)
        put(surf, F["small"], lab, (int(cx + (R - 11) * math.cos(a)), int(cy + (R - 11) * math.sin(a))), RED if lab == "N" else WHITE, anchor="center")
    if hdg is not None:
        a = math.radians(hdg - 90)
        pygame.draw.line(surf, ORANGE, (cx, cy), (cx + (R - 20) * math.cos(a), cy + (R - 20) * math.sin(a)), 3)
        put(surf, F["tiny"], f"RUMBO {int(hdg) % 360:03d}°", (cx, cy + R + 8), DIM, anchor="center")

_draw_alt_b19 = draw_alt

def draw_alt(surf, r, d, now, big=False):
    if in_srv(d):                                         # SRV / Rhino: reloj de 0-40 m/s, km/h y brujula
        gs = SPD.get("gs")
        vm = SPD["vmax"].setdefault(srv_name(d), 40)
        if gs and gs > vm * 0.95:
            vm = SPD["vmax"][srv_name(d)] = int(math.ceil(gs * 1.2 / 10.0)) * 10
        R_ = min(r.h // 2 - 8, r.w // 4)
        draw_arc(surf, r.x + r.w // 4 + 4, r.centery, R_, gs, vm, 5 if vm <= 50 else 10,
                 [(0, vm * 0.62, GREEN), (vm * 0.62, vm * 0.85, ORANGE), (vm * 0.85, vm, RED)], srv_name(d), now)
        if gs is not None:
            put(surf, F["btn"], f"{gs * 3.6:.0f} km/h", (r.x + r.w // 4 + 4, r.bottom - 12), WHITE, anchor="center")
        draw_hdg_compass(surf, r.x + 3 * r.w // 4, r.centery - 6, min(r.h // 2 - 22, r.w // 5), _geo(d)[3])
        return
    _draw_alt_b19(surf, r, d, now, big)
    if alt_now(d) is None:
        return
    gs, vs = SPD.get("gs"), alt_vs()
    vm = ship_vmax(d)
    tape_r = int(r.w * 0.52) + 8
    cx = r.x + tape_r + 80 + (r.w - tape_r - 80) // 2
    R_ = min((r.w - tape_r - 90) // 2, r.h // 2 - 22)
    if R_ < 30:
        return
    draw_arc(surf, cx, r.y + 18 + R_, R_, gs, vm, 100 if vm <= 600 else 200,
             [(0, 100, GREEN), (100, vm * 0.66, ORANGE), (vm * 0.66, vm, RED)], "SUELO", now)
    if gs is not None and vs is not None:
        put(surf, F["small"], f"total {math.hypot(gs, vs):.0f} m/s", (cx, r.y + 18 + 2 * R_ + 18), WHITE, anchor="center")

# --- aviso: bajando rapido cerca del suelo (solo en la nave) ---
EV_LIST.append(("suelo", "BAJANDO RÁPIDO CERCA DEL SUELO"))
SUELO = {"t": 0}

def suelo_watch(d, now):
    alt, vs = alt_now(d), alt_vs()
    fl = (d or {}).get("Flags", 0)
    if alt is None or vs is None or in_srv(d) or fl & 3 or fl & (1 << 29):
        return
    if (alt < 250 and vs < -35) or (alt < 60 and vs < -15):
        if now - SUELO["t"] > 12 and ev_on("suelo"):
            SUELO["t"] = now
            k0 = XA_K[0]
            try:
                XA_K[0] = "suelo"
                set_alert("BAJANDO RÁPIDO CERCA DEL SUELO", f"{alt:.0f} m · {vs:.0f} m/s", RED, 4)
                play("alarm")
                voice_say("cuidado, bajas rápido cerca del suelo")
            finally:
                XA_K[0] = k0

# --- caja negra: los ultimos 60 s de altura y velocidades, al LOG si te destruyen ---
CAJA = deque(maxlen=200)

def caja_track(d, now):
    alt = ((d or {}).get("live") or {}).get("alt")
    if alt is None or ((d or {}).get("bio") or {}).get("lat") is None:
        return
    if not CAJA or now - CAJA[-1][0] >= 0.5:
        CAJA.append((now, alt, alt_vs(), SPD.get("gs"), (d or {}).get("Flags", 0)))

def caja_dump(why):
    now = time.time()
    pts = [p for p in CAJA if now - p[0] <= 60]
    if not pts:
        plog(f"CAJA NEGRA ({why}): sin datos de altura en el último minuto"); return
    plog(f"CAJA NEGRA ({why}): últimos {now - pts[0][0]:.0f} s (segundos antes · altura · vertical · suelo)")
    sel = pts[::max(1, len(pts) // 30)] + [pts[-1]]
    for t, alt, vs, gs, fl in sel:
        plog(f"  -{now - t:4.1f} s · {alt:7.0f} m · " + (f"{vs:+5.0f}" if vs is not None else "   ? ") + " m/s · "
             + (f"{gs:5.0f}" if gs is not None else "   ? ") + " m/s" + (" · radio medio" if fl & (1 << 29) else ""))

# --- repetidos: avisos iguales seguidos una sola vez; en el LOG, una linea con ×N ---
REPN = {"k": None, "t": 0, "n": 0}
_handle_note_b19 = handle_note

def handle_note(kind, text):
    now = time.time()
    if kind == "died":
        try:
            caja_dump("nave destruida")
        except Exception as e:
            log_exc("caja negra", e)
    k = (kind, text)
    if REPN["k"] == k and now - REPN["t"] < 3:
        REPN["n"] += 1; REPN["t"] = now
        return
    if REPN["n"]:
        plog(f"  (lo anterior, {REPN['k'][0]}: repetido ×{REPN['n'] + 1})")
    REPN.update(k=k, t=now, n=0)
    _handle_note_b19(kind, text)

_plog_b19 = plog
PLR = {"m": None, "t": 0, "n": 0}

def plog(*a, **k):
    msg = " ".join(str(x) for x in a)
    now = time.time()
    if msg == PLR["m"] and now - PLR["t"] < 5:
        PLR["n"] += 1; PLR["t"] = now; return
    if PLR["n"]:
        _plog_b19(f"  (repetido ×{PLR['n'] + 1})")
    PLR.update(m=msg, t=now, n=0)
    _plog_b19(*a, **k)

# pantalla grande: tambien en el SRV / Rhino (sustituye al MAPA)
BIG_SETS["SUPERFICIE + VELOCÍMETRO"] = [100, 73, 5, 137]
_big_mode_b19 = big_mode

def big_mode(d, flags):
    m = _big_mode_b19(d, flags)
    if m == "SUPERFICIE" and flags & (1 << 26) and _geo(d)[0] is not None:
        return "SUPERFICIE + VELOCÍMETRO"
    return m

MENU[137] = "ALTÍMETRO Y VELOCIDAD"

_render_b19 = render

def render(surf):
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        now = time.time()
        if d is not None and now - rx < 5:
            spd_track(d, now); caja_track(d, now); suelo_watch(d, now)
        if PLR["n"] and now - PLR["t"] > 5:
            _plog_b19(f"  (repetido ×{PLR['n'] + 1})"); PLR["n"] = 0
        if REPN["n"] and now - REPN["t"] > 5:
            _plog_b19(f"  ({REPN['k'][0]}: repetido ×{REPN['n'] + 1})"); REPN["n"] = 0
    except Exception as e:
        log_exc("velocidad", e)
    return _render_b19(surf)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 18''', '''# Novedades v1.0 beta 19
- Voz: lee las abreviaturas completas (toneladas, millones, mil, segundos luz, años luz, metros por segundo, kilómetros, zona de conflicto, comandantes) y no lee los «#23».
- Velocímetro cerca de un planeta (calculado con la latitud y longitud, aproximado): en la nave, reloj de arco junto al altímetro (velocidad sobre el suelo y total; la escala según tu nave; verde lento, naranja normal, rojo rápido). En el SRV y el Rhino, reloj de 0-40 m/s (se amplía solo), km/h y brújula con el rumbo; en 4 CUADROS sustituye al MAPA.
- Aviso BAJANDO RÁPIDO CERCA DEL SUELO (por debajo de 250 m a más de 35 m/s, o de 60 m a más de 15 m/s). Se apaga en ALERTAS.
- Caja negra: si te destruyen, el LOG guarda los últimos 60 s de altura, velocidad vertical y sobre el suelo.
- Avisos repetidos seguidos (p. ej. 14 «te atacan» en un segundo): uno solo, y en el LOG una línea con ×N.
# Novedades v1.0 beta 18''')
rep('    ("1.0b18", ', '    ("1.0b19", "Voz con abreviaturas, velocímetro (nave, SRV y Rhino), aviso de suelo, caja negra, repetidos"),\n    ("1.0b18", ')
s = re.sub(r'PANEL_VER = "v1\.0b18 [^"]*"', 'PANEL_VER = "v1.0b19 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 19  (copia en " + P + ".bak100b18)")
