#!/usr/bin/env python3
# Parche v0.89: transporte reservado / a bordo, totales de carrera (bajas a pie, bonos, recompensas),
# destello blanco de LUCES y VISION NOCTURNA y ficha de nave ya en la pantalla de carga. Va con el sender v0.89.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def draw_taxi" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.88' not in s:
    sys.exit("Este parche es para la v0.88")
shutil.copy(P, P + ".bak88")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# ---------- 1. ficha de nave tambien en la pantalla de carga / menu ----------
rep('''            put(surf, F["big"], "MENÚ PRINCIPAL", (W // 2, H - 44), GREEN, anchor="center")
        return''', '''            put(surf, F["big"], "MENÚ PRINCIPAL", (W // 2, H - 44), GREEN, anchor="center")
        draw_shipcard(surf, now)
        return''')

# ---------- 2. totales de carrera en los avisos ----------
rep('''            xa["a"] = dict(until=now + 3, col=col, title=f"{name} nº {num}" if num else name,''',
    '''            tot_ = p[7] if len(p) > 7 and p[7].isdigit() else ""
            if tot_:
                lab_ = "total" if veh == "F" else "bonos" if p[2] in ("B", "T") else "recompensas"
                name = (f"{name} nº {num}" if num else name) + f" · {lab_} {fnum(int(tot_), 0)}"
                num = ""
            xa["a"] = dict(until=now + 3, col=col, title=f"{name} nº {num}" if num else name,''')

# RANGOS: filas algo mas juntas y la carrera abajo
rep('''        put(surf, F["small"], f"{p_ or 0}%", (W - 6, y + 3), WHITE, anchor="topright")
        y += 35''', '''        put(surf, F["small"], f"{p_ or 0}%", (W - 6, y + 3), WHITE, anchor="topright")
        y += 31
    car_ = (d or {}).get("career") or {}
    if any(car_.get(k) is not None for k in ("foot", "bonds", "bounties")):
        pygame.draw.line(surf, DIM, (8, H - 26), (W - 8, H - 26))
        x_ = 8
        for k, lab, col in (("foot", "bajas a pie", GREEN), ("bonds", "bonos nave", BLUE), ("bounties", "recompensas", ORANGE)):
            if car_.get(k) is None:
                continue
            x_ += put(surf, F["btn"], fnum(car_[k], 0), (x_, H - 22), col)
            x_ += put(surf, F["small"], " " + lab, (x_, H - 18), DIM) + 14''')

# EN VIVO a pie: total de bajas junto al ritmo
rep('''            if Z.get("rate"):
                put(surf, F["small"], f"{str(Z['rate']).replace('.', ',')} / min", (W - 8, y + 22), DIM, anchor="topright")''',
    '''            tf_ = ((d.get("career") or {}).get("foot"))
            rt_ = "  ·  ".join(t_ for t_ in ((f"{str(Z['rate']).replace('.', ',')} / min" if Z.get("rate") else ""),
                                             (f"total {fnum(tf_, 0)}" if tf_ is not None else "")) if t_)
            if rt_:
                put(surf, F["small"], rt_, (W - 8, y + 22), DIM, anchor="topright")''')
# EN COMBATE a pie (grande)
rep('''    put(surf, F["small"], "BAJAS", (12 + F["num"].size(str(Z.get("n") or 0))[0], y + 26), GREEN)''',
    '''    put(surf, F["small"], "BAJAS", (12 + F["num"].size(str(Z.get("n") or 0))[0], y + 26), GREEN)
    tf_ = (d.get("career") or {}).get("foot")
    if tf_ is not None:
        put(surf, F["small"], f"total {fnum(tf_, 0)}", (12 + F["num"].size(str(Z.get("n") or 0))[0], y + 8), DIM)''')
# REGISTRO DE COMBATE (nave): bonos y recompensas de carrera
rep('''        put(surf, F["big"], "ACTIVOS" if flags & 8 else "SIN ESCUDOS", (80, y), BLUE if flags & 8 else DIM)
    y += 32''', '''        put(surf, F["big"], "ACTIVOS" if flags & 8 else "SIN ESCUDOS", (80, y), BLUE if flags & 8 else DIM)
    car_ = (d or {}).get("career") or {}
    if car_.get("bonds") is not None:
        put(surf, F["small"], f"bonos {fnum(car_['bonds'], 0)}", (W - 8, y), BLUE, anchor="topright")
    if car_.get("bounties") is not None:
        put(surf, F["small"], f"recompensas {fnum(car_['bounties'], 0)}", (W - 8, y + 15), ORANGE, anchor="topright")
    y += 32''')

# ---------- 3. transporte en EN VIVO ----------
rep('''def view_live_v071(surf, d, flags, now):
    view_live(surf, d, flags, now)''', '''def view_live_v071(surf, d, flags, now):
    if draw_taxi(surf, d or {}, now):
        return
    view_live(surf, d, flags, now)''')
rep('''    # avisos de peligro a pie y combustible del vehiculo''', '''    taxi_watch(d, now)
    # avisos de peligro a pie y combustible del vehiculo''')

# ---------- 4. destello de LUCES y VISION NOCTURNA ----------
rep('''def chips(surf, items, y, cols=4):
    cw = (W - 16) // cols
    for k, (txt, on, col) in enumerate(items):
        r = pygame.Rect(8 + (k % cols) * cw, y + (k // cols) * 24, cw - 4, 20)
        if on:''', '''def chips(surf, items, y, cols=4):
    cw = (W - 16) // cols
    for k, (txt, on, col) in enumerate(items):
        r = pygame.Rect(8 + (k % cols) * cw, y + (k // cols) * 24, cw - 4, 20)
        if on and glow(txt):
            col = WHITE
        if on:''')
rep('''                    filled=bit is not None and bool(flags & (1 << bit)), lit=flash.get((1, i), 0) > now)''',
    '''                    filled=bit is not None and bool(flags & (1 << bit)), lit=flash.get((1, i), 0) > now or glow(txt))''')
rep('''                    filled=bit is not None and in_srv and i < 6 and bool(flags & (1 << bit)),
                    lit=flash.get((5, i), 0) > now)''', '''                    filled=bit is not None and in_srv and i < 6 and bool(flags & (1 << bit)),
                    lit=flash.get((5, i), 0) > now or glow(txt))''')
rep('''            if m5_rect(i).collidepoint(x, y):
                tap_flash((5, i)); press_seq([b[1]]); return''', '''            if m5_rect(i).collidepoint(x, y):
                tap_flash((5, i)); press_seq([b[1]])
                if i >= 6 and b[0] in GLOW_LBL:            # a pie el juego no dice si estan encendidas
                    GLOW[GLOW_LBL[b[0]]] = time.time()
                return''')
rep('''    if online and not HI_PASS[0]:
        binds_check(d)''', '''    if online and not HI_PASS[0]:
        glow_watch(d)
        binds_check(d)''')

CODE = r'''
# ---------- v0.89: transporte, carrera y destello de luces ----------
GLOW = {"luz": 0.0, "nv": 0.0, "prev": None}
GLOW_LBL = {"LUCES": "luz", "LINTERNA": "luz", "FAROS": "luz", "LUCES LARGAS": "luz",
            "VISIÓN NOC": "nv", "VISIÓN NOCT.": "nv"}

def glow_watch(d):
    fl = d.get("Flags", 0)
    st = (bool(fl & (1 << 8) or fl & (1 << 31)), bool(fl & (1 << 28)))
    pv = GLOW["prev"]
    if pv is not None:
        if st[0] and not pv[0]:
            GLOW["luz"] = time.time()
        if st[1] and not pv[1]:
            GLOW["nv"] = time.time()
    GLOW["prev"] = st

def glow(txt):
    """Al encender: 4 destellos blancos en menos de 1 s y luego su color."""
    k = GLOW_LBL.get(txt)
    if not k:
        return False
    el = time.time() - GLOW[k]
    return el < 0.9 and int(el * 9) % 2 == 0

TAXI_SECS = 300            # tiempo para subir al transporte reservado
TAXI_LOST = 60             # el aviso de perdido se ve 1 minuto

def taxi_left(t, now):
    return (t.get("t0") or now) + TAXI_SECS - now

def taxi_watch(d, now):
    t = (d or {}).get("taxi") or {}
    k0 = XA_K[0]
    try:
        XA_K[0] = "taxi"
        if t.get("st") != "booked":
            return
        left = taxi_left(t, now)
        key = t.get("t0")
        if 0 < left <= 60 and xa.get("taxi60") != key:
            xa["taxi60"] = key
            xa["a"] = dict(until=now + 6, col=RED, title=t.get("kind") or "TRANSPORTE", big="¡SUBE A LA LANZADERA!",
                           lines=["queda 1 minuto"])
            play("alarm")
        elif -TAXI_LOST < left <= 0 and xa.get("taxilost") != key:
            xa["taxilost"] = key
            xa["a"] = dict(until=now + 6, col=RED, title=t.get("kind") or "TRANSPORTE", big="TRANSPORTE PERDIDO",
                           lines=["se acabó el tiempo para subir"])
    finally:
        XA_K[0] = k0

FSTATE_ES = {"War": "EN GUERRA", "CivilWar": "EN GUERRA CIVIL", "Boom": "AUGE", "Bust": "QUIEBRA",
             "Election": "ELECCIONES", "Expansion": "EXPANSIÓN", "Lockdown": "CONFINAMIENTO", "Outbreak": "EPIDEMIA",
             "CivilUnrest": "DISTURBIOS", "Famine": "HAMBRUNA", "Retreat": "RETIRADA", "Investment": "INVERSIÓN",
             "PirateAttack": "ATAQUE PIRATA", "Terrorism": "TERRORISMO", "Blight": "PLAGA", "Drought": "SEQUÍA"}

def draw_taxi(surf, d, now):
    """Transporte reservado (cuenta atras para subir) o a bordo (fase, altitud, gravedad y zona)."""
    t = d.get("taxi") or {}
    st = t.get("st")
    if st not in ("booked", "aboard"):
        return False
    if st == "booked" and taxi_left(t, now) <= -TAXI_LOST:
        return False
    w_, h_ = surf.get_size()
    military = "MILITAR" in (t.get("kind") or "")
    kind = ("RETIRADA · " if t.get("retreat") else "") + (t.get("kind") or "TRANSPORTE")
    dest = t.get("loc") or t.get("sys") or ""
    y = TOP + 4
    put(surf, F["small"], kind, (8, y), BLUE if not military else ORANGE, W - 16); y += 18
    if st == "booked":
        left = taxi_left(t, now)
        if left <= 0:
            on_ = int(now * 3) % 2 == 0
            put(surf, F["big"], "TRANSPORTE PERDIDO", (W // 2, y + 30), RED if on_ else ORANGE, anchor="center")
            put(surf, F["small"], "se acabó el tiempo para subir", (W // 2, y + 58), DIM, anchor="center")
            return True
        put(surf, F["big"], "TRANSPORTE RESERVADO", (8, y), GREEN); y += 30
        col = GREEN if left > 120 else ORANGE if left > 60 else (RED if int(now * 4) % 2 == 0 else BLACK)
        m_, s_ = int(left) // 60, int(left) % 60
        put(surf, F["num"], f"{m_}:{s_:02d}", (W // 2, y + 26), col, anchor="center"); y += 58
        put(surf, F["btn"], "para subir" if left > 60 else "¡SUBE YA!", (W // 2, y), DIM if left > 60 else RED, anchor="center"); y += 26
        if dest:
            put(surf, F["small"], "DESTINO", (8, y + 4), DIM)
            put(surf, F["btn"], dest.upper(), (80, y), ORANGE, W - 88); y += 24
        if t.get("cost"):
            put(surf, F["small"], f"coste {cr(t['cost'])} cr", (8, y), DIM)
        return True
    put(surf, F["big"], "A BORDO", (8, y), GREEN)
    ph = t.get("phase") or ""
    put(surf, F["big"], ph, (W - 8, y), BLUE, W // 2, anchor="topright"); y += 32
    if dest:
        put(surf, F["small"], "DESTINO", (8, y + 4), DIM)
        put(surf, F["btn"], dest.upper(), (80, y), ORANGE, W - 88); y += 26
    L = d.get("live") or {}
    alt, g = L.get("alt"), L.get("grav")
    if alt is not None or g is not None:
        if alt is not None:
            put(surf, F["small"], "ALTITUD", (8, y + 4), DIM)
            put(surf, F["btn"], f"{alt / 1000:.1f} km".replace(".", ",") if alt >= 1000 else f"{alt:.0f} m", (80, y), ORANGE)
        if g is not None:
            put(surf, F["small"], "GRAVEDAD", (250, y + 4), DIM)
            put(surf, F["btn"], f"{g:.2f} G".replace(".", ","), (W - 8, y), RED if g > 2 else ORANGE, anchor="topright")
        y += 26
    if military and (t.get("zone") or t.get("fac")):
        pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 6
        put(surf, F["small"], "ZONA DE COMBATE", (8, y), DIM); y += 16
        put(surf, F["btn"], (t.get("zone") or "").upper(), (8, y), RED, W - 16); y += 24
        fst = FSTATE_ES.get(t.get("fstate") or "", t.get("fstate") or "")
        put(surf, F["small"], "  ·  ".join(x for x in (t.get("fac"), fst) if x), (8, y), ORANGE, W - 16)
    return True

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")

rep('''# Enlace energético''', '''# Novedades v0.89
- Transporte: al reservar la lanzadera o el transporte militar, EN VIVO muestra TRANSPORTE RESERVADO con 5:00 para subir (verde; naranja con menos de 2 min; rojo parpadeando en el último). Al minuto: «¡SUBE A LA LANZADERA!»; si se acaba, TRANSPORTE PERDIDO.
- A bordo: fase (embarque, despegue, supercrucero, aproximación, llegada), altitud y gravedad; en el transporte militar, la zona de combate, la facción y su estado.
- Totales de carrera (de las estadísticas del juego más lo de la partida): en RANGOS abajo; «total» de bajas a pie en EN VIVO y EN COMBATE; bonos y recompensas en el REGISTRO DE COMBATE; y en los avisos «BAJA nº X · total N», «DERRIBO nº X · bonos N».
- LUCES y VISIÓN NOCTURNA destellan en blanco al encenderlas y luego cogen su color.
- Operations: la ficha de la nave sale ya en la pantalla de carga y se refresca al llegar el equipamiento.
# Enlace energético''')
rep('    ("0.88", "Fichas NAVE y FLOTA, nave nueva a pantalla completa, transferencias, módulos dañados, SRV y caza"),\n',
    '    ("0.88", "Fichas NAVE y FLOTA, nave nueva a pantalla completa, transferencias, módulos dañados, SRV y caza"),\n'
    '    ("0.89", "Transporte reservado y a bordo, totales de carrera, destello de luces, nave en la carga de Operations"),\n')
s = re.sub(r'PANEL_VER = "v0\.88[^"]*"', 'PANEL_VER = "v0.89 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.89  (copia en " + P + ".bak88)")
