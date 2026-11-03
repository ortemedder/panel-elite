#!/usr/bin/env python3
# Parche v0.93: mercado de la estacion donde estas (o de EDSM), ajuste MERCADO, fotos de las naves,
# FPS en verde, transporte 5:20 / 6:00, foto de destino mas grande y faccion / reputacion del destino.
# Va con el sender v0.93. Fotos de naves: carpeta naves/ junto a panel.py.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def ship_photo" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.92b' not in s:
    sys.exit("Este parche es para la v0.92b")
shutil.copy(P, P + ".bak92b")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# 8. FPS en verde
rep('''    out.append((f"{PERF['fps']:.0f} FPS", DIM))''', '''    out.append((f"{PERF['fps']:.0f} FPS", GREEN))''')

# 9. transporte: 5:20 en estacion, 6:00 en planeta
rep('''    return (t.get("t0") or now) + TAXI_SECS - now''', '''    return (t.get("t0") or now) + (360 if t.get("planet") else 320) - now''')

# 10. foto del destino mas grande
rep('''    r = pygame.Rect(W - 132, H - 74, 124, 66)''', '''    r = pygame.Rect(W - 178, H - 102, 170, 96)''')
rep('''            tw_ = 136 if carrier_dest(d or {})[0] else 0''', '''            tw_ = 182 if carrier_dest(d or {})[0] else 0''')
rep('''    y, x, wd = TOP + 58, 8, W - 160''', '''    y, x, wd = TOP + 58, 8, W - 190''')
rep('''    put(surf, F["small"], f"datos: {src}" if src else "sin datos: no escaneado (o es una estación/señal)",
        (8, H - 16), DIM if src else ORANGE)''', '''    if src or not (d or {}).get("dstinfo"):
        put(surf, F["small"], f"datos: {src}" if src else "sin datos: no escaneado (o es una estación/señal)",
            (8, H - 16), DIM if src else ORANGE, W - 190)''')

# 4. ajuste MERCADO (SIEMPRE / CON CARGA / NUNCA) en AJUSTES > OPCIONES
rep('''             ("CERRAR JUEGO", cfg.get("killbtn", True))]
    for i, (name, on) in enumerate(items):
        r = grid(i, 4, 2)''', '''             ("CERRAR JUEGO", cfg.get("killbtn", True)), ("MERCADO", None)]
    for i, (name, on) in enumerate(items):
        r = grid(i, 4, 3)
        if name == "MERCADO":
            mk_ = cfg.get("mkt", "CON CARGA")
            draw_button(surf, r, name, mk_, F["btn"], filled=mk_ != "NUNCA", lit=flash.get((124, i), 0) > now)
            continue''')
rep('''        for i, k in enumerate(["auto", "alerts", "sound", "theme", "voice", "stream", "keys", "killbtn"]):
            if grid(i, 4, 2).collidepoint(x, y):''', '''        for i, k in enumerate(["auto", "alerts", "sound", "theme", "voice", "stream", "keys", "killbtn", "mkt"]):
            if grid(i, 4, 3).collidepoint(x, y):
                if k == "mkt":
                    tap_flash((124, i))
                    opts_ = ["CON CARGA", "SIEMPRE", "NUNCA"]
                    cfg["mkt"] = opts_[(opts_.index(cfg.get("mkt", "CON CARGA")) + 1) % 3]; save_cfg(); return''')
rep('''    if mode == "ATRACADO" and 4 in cells:''', '''    if 127 in cells and not mkt_show(d):
        cells[cells.index(127)] = 11                 # sin carga: SESION en lugar del MERCADO
    if mode == "ATRACADO" and 4 in cells:''')

# 5-7. fotos de naves
rep('''    surf.fill(BLACK)
    m_ = int(8 * k)
    y = m_
    put(surf, f1, (c.get("ship") or "?").upper(), (m_, y), ORANGE, w - 2 * m_); y += f1.get_height()''',
    '''    surf.fill(BLACK)
    ship_bg(surf, c, (d_sc_() or {}))
    m_ = int(8 * k)
    y = m_
    put(surf, f1, (c.get("ship") or "?").upper(), (m_, y), ORANGE, w - 2 * m_); y += f1.get_height()''')
rep('''    put(surf, F["big"], (c.get("ship") or "?").upper(), (8, y), ORANGE, W // 2)
    put(surf, F["small"], " · ".join(x for x in (c.get("name"), c.get("ident")) if x), (W - 8, y + 6), DIM, W // 2 - 10, anchor="topright")
    y += 28''', '''    ph_ = ship_photo(surf, c, d or {}, pygame.Rect(W - 104, TOP + 2, 96, 54))
    put(surf, F["big"], (c.get("ship") or "?").upper(), (8, y), ORANGE, W // 2)
    put(surf, F["small"], " · ".join(x for x in (c.get("name"), c.get("ident")) if x), (W - (112 if ph_ else 8), y + 6), DIM,
        W // 2 - (110 if ph_ else 10), anchor="topright")
    y += 28''')
rep('''             ("CARGA", f"{c.get('cargo') or 0} t"), ("MASA", f"{c.get('mass') or 0:.0f} t"), ("VALOR", f"{crx(c.get('value') or 0)}")]
    stats = [x for x in stats if x[0] != "VALOR" or c.get("value")]
    cw = (W - 16) // len(stats)''', '''             ("CARGA", f"{c.get('cargo') or 0} t"), ("MASA", f"{c.get('mass') or 0:.0f} t"), ("VALOR", f"{crx(c.get('value') or 0)}")]
    stats = [x for x in stats if x[0] != "VALOR" or c.get("value")]
    cw = (W - (128 if ph_ else 16)) // len(stats)''')
rep('''        put(surf, F["btn"], (f.get("ship") or "?") + (f" «{nm}»" if nm and nm != f.get("ship") else ""), (8, y), ORANGE, W - 170)''',
    '''        ph_ = ship_photo(surf, f, d or {}, pygame.Rect(8, y + 1, 54, 30))
        x_ = 68 if ph_ else 8
        put(surf, F["btn"], (f.get("ship") or "?") + (f" «{nm}»" if nm and nm != f.get("ship") else ""), (x_, y), ORANGE, W - 170 - x_ + 8)''')
rep('''        put(surf, F["small"], sub, (8, y + 18), GREEN if f.get("here") else DIM, W - 16)''',
    '''        put(surf, F["small"], sub, (x_, y + 18), GREEN if f.get("here") else DIM, W - 8 - x_)''')

CODE = r'''
# ---------- v0.93 ----------
def d_sc_():
    with lock:
        return state["data"]

# --- fotos de naves (carpeta naves/, nave_<tipo interno>.jpg) ---
SHIP_ALIAS = {"sidewindermki": "sidewinder", "eaglemkii": "eagle", "imperialeagle": "empire_eagle", "vipermkiii": "viper",
    "cobramkiii": "cobramkiii", "vipermkiv": "viper_mkiv", "diamondbackscout": "diamondback", "cobramkiv": "cobramkiv",
    "type6transporter": "type6", "diamondbackexplorer": "diamondbackxl", "imperialcourier": "empire_courier",
    "keelback": "independant_trader", "aspscout": "asp_scout", "aspexplorer": "asp", "federaldropship": "federation_dropship",
    "type7transporter": "type7", "alliancechieftain": "typex", "federalassaultship": "federation_dropship_mkii",
    "imperialclipper": "empire_trader", "alliancecrusader": "typex_3", "alliancechallenger": "typex_2",
    "federalgunship": "federation_gunship", "kraitphantom": "krait_light", "kraitmkii": "krait_mkii", "ferdelance": "ferdelance",
    "type9heavy": "type9", "belugaliner": "belugaliner", "type10defender": "type9_military", "federalcorvette": "federation_corvette",
    "imperialcutter": "cutter", "cobramkv": "cobramkv", "pythonmkii": "python_nx", "type8transporter": "type8",
    "caspianexplorer": "explorer_nx", "pantherclippermkii": "panthermkii", "type11prospector": "lakonminer",
    "kestrelmkii": "kestrel", "lynxhighliner": "lynx", "anacondamkii": "anaconda_mkii"}
_SHIPDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "naves")
_SHIPF = {}

def _norm(t):
    return "".join(ch for ch in (t or "").lower() if ch.isalnum())

def ship_file(c, d):
    """Fichero de la foto: por tipo interno, por nombre o por el nombre que da el astillero."""
    if not os.path.isdir(_SHIPDIR):
        return None
    if not _SHIPF:
        for f in os.listdir(_SHIPDIR):
            if f.startswith("nave_") and f.endswith(".jpg"):
                _SHIPF[_norm(f[5:-4])] = os.path.join(_SHIPDIR, f)
    names = [c.get("type"), c.get("ship")]
    fl = [x for x in ((d.get("naves") or {}).get("fleet") or []) if str(x.get("id")) == str(c.get("id"))]
    if fl:
        names += [fl[0].get("type"), fl[0].get("ship")]
    for n in names:
        k = _norm(n)
        if k in _SHIPF:
            return _SHIPF[k]
        if k in SHIP_ALIAS and _norm(SHIP_ALIAS[k]) in _SHIPF:
            return _SHIPF[_norm(SHIP_ALIAS[k])]
    return None

def ship_img(path, w, h, dark):
    key = (path, w, h, dark)
    if key not in _BG:
        img = None
        try:
            src = pygame.image.load(path)
            sw, sh = src.get_size()
            sc = max(w / sw, h / sh)
            img = pygame.transform.smoothscale(src, (int(sw * sc) + 1, int(sh * sc) + 1))
            img = img.subsurface(pygame.Rect((img.get_width() - w) // 2, (img.get_height() - h) // 2, w, h)).copy()
            if dark < 255:
                img.fill((dark, dark, dark), special_flags=pygame.BLEND_MULT)
        except Exception as e:
            log_exc("foto nave", e)
        _BG[key] = img
    return _BG[key]

def ship_photo(surf, c, d, r):
    p = ship_file(c, d)
    if not p:
        return False
    if type(surf).__name__ == "ScaledSurf":
        real, rr = surf.real, surf._r(r)
    else:
        real, rr = surf, r
    img = ship_img(p, rr.w, rr.h, 235)
    if img is None:
        return False
    real.blit(img, rr.topleft)
    pygame.draw.rect(surf, DIM, r, 1, border_radius=3)
    return True

def ship_bg(surf, c, d):
    p = ship_file(c, d)
    if not p:
        return
    real = surf.real if type(surf).__name__ == "ScaledSurf" else surf
    img = ship_img(p, real.get_width(), real.get_height(), 70)
    if img is not None:
        real.blit(img, (0, 0))

# --- mercado: el de la estacion donde estas ---
def mkt_show(d):
    m = cfg.get("mkt", "CON CARGA")
    if m == "NUNCA":
        return False
    return m == "SIEMPRE" or any(c for _, c in ((d or {}).get("cargo") or []))

def market_pick(d, now):
    st = (d or {}).get("station") or {}
    m = (d or {}).get("market") or {}
    if st.get("status") != "ATRACADO" or not st.get("name"):
        return m
    here = st["name"]
    me = (d or {}).get("market_edsm") or {}
    if m.get("station") == here:
        cur = m
    elif me.get("station") == here and not me.get("none"):
        cur = me
    else:
        return {"missing": here, "edsm": me.get("station") == here}
    mp = (d or {}).get("market_prev") or {}
    stype = st.get("type") or ""
    if (stype == "FleetCarrier" or "squadron" in stype.lower()) and mp.get("station") and mp.get("station") != here \
            and mp.get("sys") and mp.get("sys") == (d or {}).get("system") and int(now / 10) % 2:
        return dict(mp, other=True)
    return cur

_vm0 = view_market

def view_market(surf, d, flags, now):
    m = market_pick(d, now)
    if m.get("missing"):
        put(surf, F["btn"], m["missing"].upper(), (W // 2, (H + TOP) // 2 - 22), ORANGE, W - 16, anchor="center")
        put(surf, F["btn"], "abre su mercado para ver los precios", (W // 2, (H + TOP) // 2 + 4), DIM, anchor="center")
        put(surf, F["small"], "EDSM no tiene sus precios" if m.get("edsm") else "consultando EDSM...",
            (W // 2, (H + TOP) // 2 + 28), DIM, anchor="center")
        return
    _vm0(surf, dict(d or {}, market=m), flags, now)
    tag = "EDSM" if m.get("src") == "EDSM" else ("OTRA ESTACIÓN DEL SISTEMA" if m.get("other") else "")
    if tag:
        put(surf, F["small"], tag, (W - 8, H - 16), BLUE, 260, anchor="topright")

VIEWS[127] = view_market

# --- faccion y reputacion de la estacion de destino ---
def rep_level(r):
    if r is None:
        return None, DIM
    for lim, txt, col in ((-90, "HOSTIL", RED), (-35, "POCO AMISTOSO", ORANGE), (4, "NEUTRAL", DIM),
                          (35, "CORDIAL", WHITE), (90, "AMISTOSO", GREEN)):
        if r < lim:
            return txt, col
    return "ALIADO", GREEN

def dest_faction(d):
    di = d.get("dstinfo") or {}
    fac = di.get("fac")
    if not fac:
        return None
    f = next((x for x in ((d.get("sysinfo") or {}).get("facs") or []) if x[0] == fac[:30]), None)
    return fac, (f[3] if f and len(f) > 3 else None), (f[2] if f and len(f) > 2 else "")

def draw_dest_faction(surf, d, now):
    r_ = dest_faction(d)
    if not r_:
        return
    fac, rep, state_ = r_
    lvl, col = rep_level(rep)
    y = TOP + 58 if carrier_dest(d)[0] not in ("fc", "sq") else H - 40
    put(surf, F["small"], "FACCIÓN", (8, y), DIM)
    put(surf, F["btn"], fac, (8, y + 14), WHITE, W - 196)
    bits = [x for x in (lvl, state_) if x]
    if bits:
        put(surf, F["btn"], "  ·  ".join(bits), (8, y + 36), col, W - 196)
    nm = (d.get("dest") or {}).get("name")
    if lvl == "HOSTIL" and nm and DSTH.get("name") != nm:
        DSTH["name"] = nm
        k0 = XA_K[0]
        try:
            XA_K[0] = "dsthostil"
            xa["a"] = dict(until=now + 6, col=RED, title="¡DESTINO HOSTIL!", big=nm.upper(), lines=[fac])
            play("alarm")
        finally:
            XA_K[0] = k0
DSTH = {"name": None}

_navx2 = view_navx

def view_navx(surf, d, flags, now):
    _navx2(surf, d, flags, now)
    if (d or {}).get("dest") and not (ui.get("navtab") == 2 and not NAVBIG[0]) and not nav_show_pol(d, now):
        draw_dest_faction(surf, d or {}, now)

VIEWS[3] = view_navx
EV_LIST.append(("dsthostil", "DESTINO HOSTIL"))

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")

rep('''# Enlace energético''', '''# Novedades v0.93
- MERCADO: solo el de la estación donde estás atracado; si no lo has abierto, sus precios de EDSM, o «abre su mercado». En un portanaves alterna cada 10 s con el último mercado de otra estación del sistema.
- AJUSTES > OPCIONES > MERCADO: CON CARGA (de fábrica: en la pantalla grande solo sale si llevas carga; si no, SESIÓN), SIEMPRE o NUNCA.
- Fotos de naves (carpeta naves/ junto a panel.py): de fondo en la ficha a pantalla completa, en pequeño en NAVE y en FLOTA.
- Transporte: 5:20 para subir en estación y 6:00 en un planeta. FPS en verde. Foto del destino más grande.
- NAVEGACIÓN: facción de la estación de destino y tu reputación (HOSTIL en rojo y aviso ¡DESTINO HOSTIL!).
# Enlace energético''')
rep('    ("0.92", "TE ESCANEAN, SALUDOS, mega nave 15:00, datos del portanaves y fotos en ruta y atracado"),\n',
    '    ("0.92", "TE ESCANEAN, SALUDOS, mega nave 15:00, datos del portanaves y fotos en ruta y atracado"),\n'
    '    ("0.93", "Mercado de la estación donde estás, fotos de naves, facción del destino, transporte 5:20 / 6:00"),\n')
s = re.sub(r'PANEL_VER = "v0\.92b[^"]*"', 'PANEL_VER = "v0.93 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.93  (copia en " + P + ".bak92b)")
