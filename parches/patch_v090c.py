#!/usr/bin/env python3
# Parche v0.90c: el chorro de neutrones / enana blanca ya no activa el modo combate y
# miniatura del portanaves en la ruta (cuadro 2 de la pantalla grande y 3 NAVEGACION) si el destino es uno.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def route_thumb" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.90b' not in s:
    sys.exit("Este parche es para la v0.90b")
shutil.copy(P, P + ".bak90b")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# 1. danos en el casco junto a una estrella de neutrones o enana blanca: no es combate
rep('''            if kind in FIGHT_KINDS:
                fight["t"] = time.time()''', '''            if kind in FIGHT_KINDS and not (kind == "hull" and star_kind(d.get("curstar")) in ("neu", "wd")):
                fight["t"] = time.time()''')

# 2. lista de la ruta mas estrecha si hay miniatura
rep('''            put(surf, F["btn"], f"{n + 1}. {name}", (8, y), col, W - 90)
            put(surf, F["btn"], c or "?", (W - 8, y), col, anchor="topright")''',
    '''            tw_ = 136 if carrier_dest(d or {})[0] else 0
            put(surf, F["btn"], f"{n + 1}. {name}", (8, y), col, W - 90 - tw_)
            put(surf, F["btn"], c or "?", (W - 8 - tw_, y), col, anchor="topright")''')

CODE = r'''
# ---------- v0.90c: miniatura del portanaves de destino ----------
import re as _re
CALLSIGN = _re.compile(r"\b[A-Z0-9]{3}-[A-Z0-9]{3}\b")

def carrier_dest(d):
    """(tipo de foto, rotulo) si el destino es un portanaves: por el destino marcado o por el sistema final de la ruta."""
    own, sq = d.get("carrier") or {}, d.get("sqcarrier") or {}
    D = d.get("dest") or {}
    nm = (D.get("name") or "").upper()
    if nm and CALLSIGN.search(nm):
        if own.get("callsign") and own["callsign"].upper() in nm:
            return "fc", "TU PORTANAVES"
        if sq.get("system") and sq["system"] == d.get("system"):
            return "sq", "PORTANAVES DE ESCUADRÓN"
        return "fc", "PORTANAVES"
    end = d.get("routeend") or ((d.get("route") or [None])[-1])
    if d.get("route") and end:
        if own.get("system") and end[0] == own["system"]:
            return "fc", "TU PORTANAVES"
        if sq.get("system") and end[0] == sq["system"]:
            return "sq", "PORTANAVES DE ESCUADRÓN"
    return None, ""

def bg_img(k, w, h, dark=95):
    key = (k, w, h, dark)
    if key not in _BG:
        img = None
        try:
            src = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), BG_FILES[k]))
            sw, sh = src.get_size()
            sc = max(w / sw, h / sh)
            img = pygame.transform.smoothscale(src, (int(sw * sc) + 1, int(sh * sc) + 1))
            img = img.subsurface(pygame.Rect((img.get_width() - w) // 2, (img.get_height() - h) // 2, w, h)).copy()
            if dark < 255:
                img.fill((dark, dark, dark), special_flags=pygame.BLEND_MULT)
        except Exception as e:
            log_exc("foto " + k, e)
        _BG[key] = img
    return _BG[key]

def route_thumb(surf, d):
    k, label = carrier_dest(d)
    if not k:
        return
    r = pygame.Rect(W - 132, H - 74, 124, 66)
    if type(surf).__name__ == "ScaledSurf":
        real, rr = surf.real, surf._r(r)
    else:
        real, rr = surf, r
    img = bg_img(k, rr.w, rr.h, 230)
    if img is not None:
        real.blit(img, rr.topleft)
    pygame.draw.rect(surf, BLUE if k == "sq" else ORANGE, r, 2, border_radius=4)
    pygame.draw.rect(surf, BLACK, (r.x + 2, r.bottom - 16, r.w - 4, 14))
    put(surf, F["small"], label.replace("PORTANAVES DE ESCUADRÓN", "ESCUADRÓN"), (r.centerx, r.bottom - 9),
        BLUE if k == "sq" else ORANGE, r.w - 6, anchor="center")

_navx0 = view_navx

def view_navx(surf, d, flags, now):
    _navx0(surf, d, flags, now)
    if not (ui.get("navtab") == 2 and not NAVBIG[0]) and not nav_show_pol(d, now):
        route_thumb(surf, d or {})

VIEWS[3] = view_navx

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")

rep('''# Enlace energético''', '''# Novedades v0.90c
- El daño del chorro de una estrella de neutrones o enana blanca ya no pone la pantalla en COMBATE.
- Si el destino es un portanaves (marcado en el mapa o la ruta acaba en el sistema del tuyo o del de escuadrón), sale su foto en pequeño en NAVEGACIÓN y en el cuadro 2 de la pantalla grande.
# Enlace energético''')
rep('    ("0.90", "Línea de saltos, fondos de portanaves, portanaves de escuadrón y arreglos"),\n',
    '    ("0.90", "Línea de saltos, fondos de portanaves, portanaves de escuadrón y arreglos"),\n'
    '    ("0.90c", "Neutrones sin modo combate y foto del portanaves en la ruta"),\n')
s = re.sub(r'PANEL_VER = "v0\.90b[^"]*"', 'PANEL_VER = "v0.90c · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.90c  (copia en " + P + ".bak90b)")
