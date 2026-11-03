#!/usr/bin/env python3
# Parche v0.92: escaneos y drones sin modo combate, TE ESCANEAN, foto de la estacion atracado y en la ruta,
# SALUDOS a pie, portanaves de operaciones, mega nave 15:00, escudos de a pie al embarcar y datos del portanaves.
# Va con el sender v0.92. Nueva foto: fondo_operaciones.jpg junto a panel.py.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def view_emotes" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.91' not in s:
    sys.exit("Este parche es para la v0.91")
shutil.copy(P, P + ".bak91")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# 1. armas desplegadas por escaner (modo analisis) o justo tras escanear / lanzar drones: no es combate
rep('''    if d.get("target") or flags & 64:
        return "COMBATE"''', '''    if d.get("target") or (flags & 64 and not flags & (1 << 27) and time.time() - (d.get("scan_t") or 0) > 20):
        return "COMBATE"''')
# 5. escaneado fuera de la zona de no disparar: modo combate
rep('''            if kind in FIGHT_KINDS and not (kind == "hull" and star_kind(d.get("curstar")) in ("neu", "wd")):''',
    '''            if (kind in FIGHT_KINDS and not (kind == "hull" and star_kind(d.get("curstar")) in ("neu", "wd"))) or \\
                    (kind == "scanned" and (text or "").split("|")[3:4] == ["0"]):''')
# 4. aviso TE ESCANEAN
rep('''        elif kind == "shipswap":''', '''        elif kind == "scanned" and len(p) >= 4:
            bad = p[2] == "1"
            xa["a"] = dict(until=now + 5, col=RED if bad else ORANGE, title="TE ESCANEAN",
                           big=SCAN_ES.get(p[0], p[0].upper()),
                           lines=[x for x in ((f"probablemente {p[1]}" if p[1] else ""),
                                              ("¡LLEVAS CARGA ILEGAL O ROBADA!" if bad else "")) if x])
            if bad:
                play("alarm")
        elif kind == "shipswap":''')
rep('''("moddmg", "MÓDULOS DAÑADOS")]''', '''("moddmg", "MÓDULOS DAÑADOS"),
           ("scanned", "TE ESCANEAN"), ("opmega", "MEGA NAVE 15 MIN")]''')
# 2. foto de la estacion tambien atracado (mas oscura)
rep('''def view_station_info(surf, d, st):
    S = (d or {}).get("sysinfo") or {}''', '''def view_station_info(surf, d, st):
    carrier_bg(surf, d or {}, st, dark=55, label=False)
    S = (d or {}).get("sysinfo") or {}''')
# 6. SALUDOS: tocar el titulo A PIE del menu 5
rep('''        put(surf, F["small"], label + ("  (ACTIVO)" if act else ""), (cx, TOP + 9), GREEN if act else DIM, anchor="center")''',
    '''        put(surf, F["small"], label + ("  (ACTIVO)" if act else "") + ("   ·   SALUDOS >" if label == "A PIE" else ""),
            (cx, TOP + 9), GREEN if act else (ORANGE if label == "A PIE" else DIM), anchor="center")''')
rep('''    elif v == 5:
        for i, b in enumerate(SRV_BTNS + PIE_BTNS):''', '''    elif v == 51:
        for i in range(len(EMOTES)):
            if grid(i, 4, 2).collidepoint(x, y):
                tap_flash((51, i))
                k = emote_key(i)
                if k:
                    press_seq([k])
                return
    elif v == 5:
        if y < SEC_TOP and x > W // 2:
            ui["view"] = 51; return
        for i, b in enumerate(SRV_BTNS + PIE_BTNS):''')
# 8. mega nave: en las dos pantallas
rep('''    draw_shipcard(surf, now)
    draw_hpcrit(surf, now)''', '''    draw_shipcard(surf, now)
    draw_mega(surf, d if online else None, now)
    draw_hpcrit(surf, now)''')
rep('''        draw_shipcard(BIG["surf"], time.time())''', '''        draw_shipcard(BIG["surf"], time.time())
        with lock:
            dm_ = state["data"]
        draw_mega(BIG["surf"], dm_, time.time())''')
rep('''    taxi_watch(d, now)''', '''    taxi_watch(d, now)
    mega_watch(d, now)''')
# 9. al embarcar: fuera la alerta de escudos de a pie
rep('''    dk = bool(fl & 1)''', '''    foot = bool(d.get("Flags2", 0) & 1)
    if GLOW.get("foot") and not foot and ui.get("alert") and "ESCUDO" in (ui["alert"].get("text") or ""):
        ui["alert"] = None
    GLOW["foot"] = foot
    dk = bool(fl & 1)''')

CODE = r'''
# ---------- v0.92 ----------
SCAN_ES = {"Cargo": "BODEGA", "Crime": "DELITOS", "Cabin": "PASAJEROS", "Data": "DATOS", "Unknown": "DESCONOCIDO",
           "Tourist": "TURISTAS"}

# fotos: portanaves de operaciones y SurfaceStation solo en Operations
ST_BG.pop("SurfaceStation", None)
BG_FILES["op"] = "fondo_operaciones.jpg"

def carrier_kind(d, st):
    stype = (st.get("type") or "")
    mid = st.get("mid")
    sq, own = d.get("sqcarrier") or {}, d.get("carrier") or {}
    if stype == "SurfaceStation" or (st.get("name") or "").startswith("$Operations"):
        return ("op", "PORTANAVES DE OPERACIONES", BLUE) if (d.get("ops") or {}).get("on") or \
            (st.get("name") or "").startswith("$Operations") else (None, "", None)
    if "squadron" in stype.lower() or (mid and mid == sq.get("id")):
        return "sq", "PORTANAVES DE ESCUADRÓN", BLUE
    if stype == "FleetCarrier":
        return "fc", ("TU PORTANAVES" if mid and mid == own.get("id") else "PORTANAVES"), ORANGE
    if stype in ST_BG:
        return ST_BG[stype], ST_TYPE.get(stype, stype).upper(), ORANGE
    return None, "", None

def carrier_bg(surf, d, st, dark=95, label=True):
    """Foto de fondo: pidiendo atraque (con rotulo) o atracado (mas oscura, sin rotulo)."""
    if st.get("status") not in ("SOLICITADO", "CONCEDIDO", "ATRACADO"):
        return
    k, lab, col = carrier_kind(d, st)
    if not k:
        return
    real = surf.real if type(surf).__name__ == "ScaledSurf" else surf
    w, h = real.get_size()
    top = int(TOP * h / H)
    img = bg_img(k, w, h - top, dark)
    if img is not None:
        real.blit(img, (0, top))
    if label and st.get("status") != "ATRACADO":
        put(surf, F["big"], lab, (W - 8, H - 30), col, W - 16 if k == "op" else W // 2 + 20, anchor="topright")

# miniatura en la ruta: portanaves y ahora tambien estaciones (tipo de EDSM o recordado)
_cd0 = carrier_dest

def carrier_dest(d):
    k, lab = _cd0(d)
    if k:
        return k, lab
    D = d.get("dest") or {}
    di = d.get("dstinfo") or {}
    t = di.get("type")
    if D.get("name") and t:
        if t == "FleetCarrier":
            return "fc", "PORTANAVES"
        if "squadron" in t.lower():
            return "sq", "ESCUADRÓN"
        if t in ST_BG:
            return ST_BG[t], ST_TYPE.get(t, t).upper()
    return None, ""

CREW_ES = {"Refuel": "COMBUSTIBLE", "Repair": "REPARAR", "Rearm": "REARMAR", "Commodities": "MERCADO",
           "BlackMarket": "MERCADO NEGRO", "Shipyard": "ASTILLERO", "Outfitting": "EQUIPAMIENTO",
           "Exploration": "CARTOGRAFÍA", "VoucherRedemption": "CANJE", "VistaGenomics": "VISTA GENOMICS",
           "PioneerSupplies": "PIONEER", "Bartender": "BAR", "CarrierFuel": "TRITIO"}
CREW_COST = {"Refuel": 1.5e6, "Repair": 1.5e6, "Rearm": 1.5e6, "Shipyard": 6.5e6, "Outfitting": 5e6,
             "BlackMarket": 2e6, "Exploration": 1.85e6, "VoucherRedemption": 1.85e6, "VistaGenomics": 1.5e6,
             "PioneerSupplies": 5e6, "Bartender": 1.75e6}
ACCESS_ES = {"all": "TODOS", "none": "NADIE", "friends": "AMIGOS", "squadron": "ESCUADRÓN",
             "squadronfriends": "ESCUADRÓN Y AMIGOS"}
SVC_ES = dict((k.lower(), v) for k, v in CREW_ES.items())
SVC_ES.update({k.lower(): v for k, v in SERVICES})

def carrier_info(surf, d):
    """Pantalla de destino con un portanaves marcado: sus datos en el hueco libre."""
    k, lab = carrier_dest(d)
    if k not in ("fc", "sq"):
        return
    y, x, wd = TOP + 58, 8, W - 160
    own = d.get("carrier") or {}
    if lab == "TU PORTANAVES" and own.get("callsign"):
        av = own.get("avail")
        up = 5e6 + sum(CREW_COST.get(c, 0) for c in own.get("crew") or [])
        if av is not None:
            wk = av / up if up else 99
            put(surf, F["small"], "SALDO DISPONIBLE", (x, y), DIM)
            put(surf, F["btn"], f"{crx(av)} cr", (x + 130, y - 3), ORANGE); y += 18
            put(surf, F["small"], f"gastos ~{crx(up)} cr/semana  ·  da para {wk:.0f} semanas".replace(".", ","),
                (x, y), RED if wk < 2 else ORANGE if wk < 4 else DIM, wd); y += 20
        if own.get("crew"):
            put(surf, F["small"], "SERVICIOS: " + ", ".join(CREW_ES.get(c, c) for c in own["crew"] if c in CREW_ES),
                (x, y), BLUE, wd); y += 18
        if own.get("access"):
            put(surf, F["small"], f"ATRAQUE: {ACCESS_ES.get(own['access'], own['access'].upper())}"
                + ("  ·  admite buscados" if own.get("notorious") else ""), (x, y), GREEN, wd); y += 18
        if own.get("jump"):
            put(surf, F["small"], f"SALTO: {own['jump']} al", (x, y), WHITE, wd)
        return
    di = d.get("dstinfo") or {}
    sv = [SVC_ES.get(v.lower()) for v in di.get("services") or []]
    sv = [v for v in sv if v]
    if sv:
        put(surf, F["small"], "SERVICIOS (última vez): " + ", ".join(dict.fromkeys(sv)), (x, y), BLUE, wd); y += 18
    if di.get("denied"):
        put(surf, F["small"], f"TE DENEGARON EL ATRAQUE: {di['denied']}", (x, y), RED, wd); y += 18
    if not sv and not di.get("denied"):
        put(surf, F["small"], "sin datos: los verás al atracar una vez", (x, y), DIM, wd)

_navx1 = view_navx

def view_navx(surf, d, flags, now):
    _navx1(surf, d, flags, now)
    if (d or {}).get("dest") and not (ui.get("navtab") == 2 and not NAVBIG[0]) and not nav_show_pol(d, now):
        carrier_info(surf, d or {})

VIEWS[3] = view_navx

# SALUDOS (gestos a pie): teclas Gesto 1..8 de tus controles
EMOTES = ["SALUDAR", "SEÑALAR", "SÍ", "NO", "ADELANTE", "ALTO", "SALUDO MILITAR", "GRACIAS"]
MENU[51] = "SALUDOS"
PARENT[51] = 5

def emote_key(i):
    with lock:
        keys = (((state["data"] or {}).get("binds") or {}).get("keys")) or {}
    k = keys.get(f"HumanoidEmoteSlot{i + 1}")
    return k if k and key_ok(k) else None

def view_emotes(surf, d, flags, now):
    for i, name in enumerate(EMOTES):
        k = emote_key(i)
        draw_button(surf, grid(i, 4, 2), name, k or SIN, F["btn"] if F["btn"].size(name)[0] < W // 4 - 14 else F["small"],
                    lit=flash.get((51, i), 0) > now, dim=k is None)

VIEWS[51] = view_emotes

# mega nave de Operations: 15 minutos desde que atracas
MEGA_SECS = 15 * 60
_MGF = {}

def mega_left(d, now):
    t0 = (d or {}).get("mega")
    return None if not t0 else t0 + MEGA_SECS - now

def mega_watch(d, now):
    left = mega_left(d, now)
    if left is None:
        return
    k0 = XA_K[0]
    try:
        XA_K[0] = "opmega"
        key = (d or {}).get("mega")
        if 0 < left <= 60 and xa.get("mega60") != key:
            xa["mega60"] = key
            xa["a"] = dict(until=now + 6, col=RED, title="MEGA NAVE", big="¡QUEDA 1 MINUTO!", lines=["despega ya"])
            play("alarm")
    finally:
        XA_K[0] = k0

def draw_mega(surf, d, now):
    left = mega_left(d, now)
    if left is None or left < -30:
        return
    w, h = surf.get_size()
    k = h / H
    key = round(k, 2)
    if key not in _MGF:
        _MGF[key] = (pygame.font.Font(None, int(40 * k)), pygame.font.Font(None, int(18 * k)))
    f1, f2 = _MGF[key] if type(surf).__name__ != "ScaledSurf" else (F["big"], F["small"])
    r = pygame.Rect(w - int(140 * k), h - int(52 * k), int(132 * k), int(46 * k))
    col = GREEN if left > 300 else ORANGE if left > 60 else (RED if int(now * 3) % 2 == 0 else WHITE)
    pygame.draw.rect(surf, BLACK, r, border_radius=6)
    pygame.draw.rect(surf, col, r, 2, border_radius=6)
    put(surf, f2, "MEGA NAVE", (r.centerx, r.y + int(10 * k)), DIM, anchor="center")
    l_ = max(0, int(left))
    put(surf, f1, f"{l_ // 60}:{l_ % 60:02d}", (r.centerx, r.y + int(30 * k)), col, anchor="center")

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")

rep('''# Enlace energético''', '''# Novedades v0.92
- El escáner del sistema, el de superficie y lanzar drones ya no ponen la pantalla en COMBATE.
- Aviso TE ESCANEAN (bodega, delitos, pasajeros...) con quien tengas fijado; en rojo si llevas carga ilegal o robada. Fuera de la zona de no disparar de una estación también activa el modo combate.
- La foto de la estación sale también atracado (más oscura) y en pequeño en la ruta al marcar una estación como destino (tipo sacado de EDSM o de donde ya has estado: estaciones.json junto al sender).
- 5 A PIE: toca «SALUDOS >» arriba a la derecha: los 8 gestos (asígnales tecla en el juego: Gesto 1 a 8).
- Operations: el portanaves de operaciones con su foto (fondo_operaciones.jpg); al atracar en la mega nave, cuenta atrás de 15:00 abajo a la derecha (aviso al último minuto).
- Al embarcar se quita la alerta de escudos de a pie.
- Destino a un portanaves: el tuyo con saldo, gastos aproximados y semanas, servicios, atraque y salto; los de otros, sus servicios de la última vez y si te denegaron el atraque.
# Enlace energético''')
rep('    ("0.91", "Fotos de fondo de cada tipo de estación al pedir atraque"),\n',
    '    ("0.91", "Fotos de fondo de cada tipo de estación al pedir atraque"),\n'
    '    ("0.92", "TE ESCANEAN, SALUDOS, mega nave 15:00, datos del portanaves y fotos en ruta y atracado"),\n')
s = re.sub(r'PANEL_VER = "v0\.91[^"]*"', 'PANEL_VER = "v0.92 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.92  (copia en " + P + ".bak91)")
