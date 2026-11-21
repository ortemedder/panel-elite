# Panel Elite v1.1 · parte 32: novedades v1.1.16
#   COLONIZACIÓN y EDSM: los avisos que salen de EDSM dicen «según EDSM». Al abrir el mercado del juego, si EDSM decía
#     que había algo que no está, aviso CORRECCIÓN. Lo que sabe el panel por tus visitas (diario, 7 días) manda sobre EDSM:
#     esa estación ya no sale para esa mercancía en el aviso al atracar, AQUÍ, EN EL SISTEMA, «prueba en…» ni DÓNDE COMPRAR HOY.
#   ROBOT: «¿dónde compro / vendo…?» elige la mercancía por todas las palabras (antes «tejidos» cogía la primera que
#     empezara así: tejido de categoría militar -> tejidos conductivos).
#   PERMISOS: AJUSTES > PERMISOS (los tuyos, uno a uno; los de rango de la Federación y del Imperio y el de Shinrarta
#     se ponen solos). Marca SIN PERMISO en la RUTA, aviso PERMISO NECESARIO (ruta, ruta externa y destino), candado en
#     la ficha del sistema de la ruta, VENTAJAS CERCANAS de los sistemas con permiso que tienes y CUERPO CERRADO.
#   MERCANCÍAS RARAS: aviso al atracar en una estación que vende una (datos/mercancias_raras.csv).
#   ROBOT: cada aviso lleva su número (#NN, el de ALERTAS / SONIDO). Por voz: «quita este aviso» (ALERTAS) y
#     «silencia este aviso» (SONIDO).
#   Todo lo nuevo se quita uno a uno en ALERTAS.
EV_LIST.extend([("edsmmal", "COLONIA: CORRECCIÓN DE EDSM"), ("permruta", "PERMISO NECESARIO (RUTA Y DESTINO)"),
                ("permcerca", "PERMISOS: VENTAJAS CERCANAS"), ("permcuerpo", "CUERPO CERRADO (PERMISO)"),
                ("rara", "MERCANCÍA RARA AL ATRACAR")])

DATOS_DIR = os.path.join(PANEL_DIR, "datos")

# ===============================================================================================================
# 1) COLONIZACIÓN: lo que has visto en el mercado del juego manda sobre EDSM (7 días)
# ===============================================================================================================
EDSM7 = 7 * 86400
GMK = {}                                                  # mid -> (t del mercado, {claves con existencias}, cuándo se leyó)
EDSM_ORIG = {}                                            # mid -> claves que EDSM decía que había (sin filtrar)
EDSM_MAL = {"mkt": None, "t": 0.0}

def _gmk_set(mid, t, keys):
    GMK[str(mid)] = (t or 0, set(keys), time.time())

def game_stock(mid):
    """(t, {claves con existencias}) del mercado del juego de esa estación, si lo has abierto (diario o ahora)."""
    if not mid:
        return None
    mid = str(mid)
    g = GMK.get(mid)
    if g and time.time() - g[2] < 600:
        return g[:2]
    try:
        with DB["lock"]:
            rows = db().execute("SELECT clave, stock, t FROM mercado WHERE mid=?", (int(mid),)).fetchall()
    except Exception:
        rows = []
    if rows:
        _gmk_set(mid, max(r[2] or 0 for r in rows), [r[0] for r in rows if (r[1] or 0) > 0])
    else:
        GMK[mid] = (0, set(), time.time())
    return GMK[mid][:2]

def edsm_malo(mid, key):
    """True si has abierto el mercado de esa estación hace menos de 7 días y no tenía esa mercancía."""
    g = game_stock(mid)
    return bool(g and g[0] and time.time() - g[0] < EDSM7 and key not in g[1])

def edsm_filtra(d):
    m = d.get("mktall") or {}
    if m.get("mid") and m.get("t"):
        g = GMK.get(str(m["mid"]))
        if not g or g[0] != m["t"]:
            _gmk_set(m["mid"], m["t"], [it[0] for it in m.get("items") or [] if len(it) > 5 and (it[5] or 0) > 0])
    B = d.get("colbuy")
    if isinstance(B, dict) and B.get("status") == "ok" and B.get("mid"):
        B0 = B.get("_orig") or B                          # lo que mandó el sender (sin filtrar)
        mid = str(B0["mid"])
        keys = list(B0.get("keys") or [])
        if B0 is B:
            EDSM_ORIG[mid] = (B0.get("t"), set(keys))
        malas = [k for k in keys if edsm_malo(mid, k)]
        B = {k: v for k, v in B0.items() if k != "_orig"}
        B["_orig"] = B0
        if malas:
            B["keys"] = [k for k in keys if k not in malas]
            B["items"] = {k: v for k, v in (B0.get("items") or {}).items() if k not in malas}
            B["malas"] = malas
        d["colbuy"] = B
    C = d.get("colsys")
    if isinstance(C, dict) and C.get("off"):
        C0 = C.get("_orig") or C
        off = {}
        for k, rows in (C0.get("off") or {}).items():
            off[k] = [r for r in rows if not (len(r) > 7 and edsm_malo(r[7], k))]
        d["colsys"] = dict({k: v for k, v in C0.items() if k != "_orig"}, off=off, _orig=C0)
    return d

_mkt_recuenta_v1116 = mkt_recuenta

def mkt_recuenta(d):
    d = _mkt_recuenta_v1116(d)
    try:
        d = edsm_filtra(d)
    except Exception as e:
        log_exc("EDSM filtro", e)
    return d

def edsm_correccion_watch(d):
    """Al abrir el mercado del juego: si EDSM decía que aquí había algo de tu construcción que no hay, aviso."""
    m = d.get("mktall") or {}
    key_ = (m.get("mid"), m.get("t"))
    if EDSM_MAL["mkt"] is None:
        EDSM_MAL["mkt"] = key_; return
    if key_ == EDSM_MAL["mkt"] or not m.get("mid") or not d.get("Flags", 0) & 1:
        return
    EDSM_MAL["mkt"] = key_
    orig = EDSM_ORIG.get(str(m["mid"]))
    if not orig:
        return
    x, need = _col_need_keys(d)
    hay = {it[0] for it in m.get("items") or [] if len(it) > 5 and (it[5] or 0) > 0}
    mal = [t_[0] for t_ in need if t_[1] in orig[1] and t_[1] not in hay]
    if mal:
        plog(f"EDSM se equivocaba en {m.get('st')}: no hay {', '.join(mal)}")
        aviso_num("edsmmal", "CORRECCIÓN: EDSM SE EQUIVOCABA",
                  "aquí no hay " + ", ".join(mal[:3]) + ("…" if len(mal) > 3 else ""), ORANGE, 8, sonido="alarm")

# aviso al conceder el atraque: igual que antes, pero dice que es según EDSM
def colbuy_watch(d, now):
    if not (d or {}).get("Flags", 0) & 1:
        CBW["warn"] = None
    B = (d or {}).get("colbuy") or {}
    t = B.get("t")
    if CBW["t"] is None:
        CBW["t"] = t or 0
    elif t and t != CBW["t"]:
        CBW["t"] = t
        if B.get("status") == "ok" and not B.get("dep"):
            x, need = _col_need_keys(d)
            if need:
                keys = set(B.get("keys") or [])
                have = [t_[0] for t_ in need if t_[1] in keys]
                src = "según EDSM" if B.get("src") == "EDSM" else ""
                if have:
                    _col_alert(f"AQUÍ HAY {len(have)} MATERIAL{'ES' if len(have) != 1 else ''} DE COLONIZACIÓN",
                               ", ".join(have[:3]) + ("…" if len(have) > 3 else "") + f" · {B.get('st')}" + (f" · {src}" if src else ""),
                               GREEN)
                else:
                    alt = _col_alt(d, need, B.get("mid"))
                    _col_alert("ESTA ESTACIÓN NO TIENE MATERIALES DE COLONIZACIÓN",
                               (f"prueba en {alt[0]} ({', '.join(alt[1][:3])})" if alt else f"{B.get('st')} · para tu construcción")
                               + (f" · {src}" if src else ""),
                               RED, "esta estación no tiene materiales de colonización")
    mk = (d or {}).get("market") or {}
    key_ = (mk.get("mid"), mk.get("t"))
    if CBW["mk"] is None:
        CBW["mk"] = key_
    elif key_ != CBW["mk"] and mk.get("t") and (d or {}).get("Flags", 0) & 1:
        CBW["mk"] = key_
        C = (d or {}).get("colonia") or {}
        mids = {str(y.get("mid")) for y in C.get("list") or []}
        if str(mk.get("mid")) in mids or C.get("dock"):
            return
        x, need = _col_need_keys(d)
        if need:
            here = col_here(d)
            if not any(_hh(here, t_[0], t_[1]) is not None for t_ in need):
                alt = _col_alt(d, need, str(mk.get("mid")))
                _col_alert("AQUÍ NO HAY MATERIALES DE COLONIZACIÓN",
                           (f"prueba en {alt[0]} ({', '.join(alt[1][:3])})" if alt else (mk.get("station") or "") + " · mercado del juego"), RED)
        col_nosell(d, mk)

# ===============================================================================================================
# 2) ROBOT: «¿dónde compro / vendo X?» con todas las palabras
# ===============================================================================================================
_MERC_FUERA = {"donde", "vendo", "venden", "compro", "comprar", "vender", "puedo", "mejor", "precio", "pagan", "cuanto",
               "barato", "barata", "mercado", "estacion", "los", "las", "del", "una", "uno", "que", "mas", "por", "con",
               "consigo", "de", "el", "la", "en", "me", "se", "lo", "le", "un"}

def _mercancia(t):
    """La mercancía del diario que más palabras de la pregunta tiene (si empatan, la que las tiene todas)."""
    pal = [w for w in re.findall(r"[a-z]+", t) if len(w) >= 3 and w not in _MERC_FUERA]
    if not pal:
        return None
    with DB["lock"]:
        noms = [r[0] for r in db().execute("SELECT DISTINCT nombre FROM mercado").fetchall()]
    mejor, punt = None, (0, 0, 0)
    for n in noms:
        nw = [w for w in re.findall(r"[a-z]+", _norm(n)) if len(w) >= 3 and w not in _MERC_FUERA]
        if not nw:
            continue
        # cada palabra de la pregunta cuenta si empieza igual que una del nombre (tejido / tejidos)
        hits = sum(1 for w in pal if any(x.startswith(w[:5]) or w.startswith(x[:5]) for x in nw))
        if not hits:
            continue
        todas = sum(1 for x in nw if any(x.startswith(w[:5]) or w.startswith(x[:5]) for w in pal))
        p = (hits, int(todas == len(nw)), -len(nw))
        if p > punt:
            mejor, punt = n, p
    return mejor

# ===============================================================================================================
# 3) PERMISOS
# ===============================================================================================================
try:
    PERM = json.load(open(os.path.join(DATOS_DIR, "permisos.json"), encoding="utf-8"))
except Exception as _e:
    PERM = {"sistemas": [], "regiones": [], "cuerpos": []}
    print("permisos.json:", _e)
PERM_SYS = {s["sistema"].lower(): s for s in PERM.get("sistemas") or []}
FED_R = ["none", "recruit", "cadet", "midshipman", "petty officer", "chief petty officer", "warrant officer", "ensign",
         "lieutenant", "lieutenant commander", "post commander", "post captain", "rear admiral", "vice admiral", "admiral"]
EMP_R = ["none", "outsider", "serf", "master", "squire", "knight", "lord", "baron", "viscount", "count", "earl", "marquis",
         "duke", "prince", "king"]
_ORDEN = {"rango": 0, "reputacion": 1, "accesible": 2, "raro": 3, "desconocido": 4, "bloqueado": 5}
def _perm_vale(x):
    return "portanaves" not in (x.get("requisito") or "").lower()       # Hyades YO-Q b5-1: solo para portanaves

PERM_LIST = [s["sistema"] for s in sorted((x for x in PERM.get("sistemas") or [] if _perm_vale(x)),
                                           key=lambda x: (_ORDEN.get(x.get("tipo"), 9), x["sistema"]))]
PERMPP = 12
MENU[1246] = "PERMISOS"
PARENT[1246] = 12
SET12.append(("PERMISOS", 1246))

def _perm_init():
    """La primera vez: ORTEM ED DER con sus 30 permisos (datos/permisos_ortem.json); los demás, a mano."""
    if cfg.get("permini"):
        return
    cm = (cfg.get("cmdr") or "").upper()
    if not cm:
        return
    if cm == "ORTEM ED DER":
        try:
            mios = json.load(open(os.path.join(DATOS_DIR, "permisos_ortem.json"), encoding="utf-8")).get("permisos") or []
            cfg["perm"] = {s: True for s in mios}
        except Exception as e:
            log_exc("permisos de ORTEM", e)
            return
    cfg["permini"] = True
    save_cfg()

def perm_auto(sistema, d=None):
    """True si el permiso viene solo (rango de la Federación o del Imperio, Elite para Shinrarta, HIP 22460)."""
    s = PERM_SYS.get((sistema or "").lower())
    if not s:
        return False
    if s.get("tipo") == "accesible":
        return True
    if d is None:
        d = state.get("data") or {}                       # sin cerrojo: se llama también mientras se dibuja
    rk = ((d or {}).get("ranks") or {}).get("rank") or {}
    req = (s.get("requisito") or "").lower()
    if s["sistema"] == "Shinrarta Dezhra":
        return any((rk.get(k) or 0) >= 8 for k in ("Combat", "Trade", "Explore", "Soldier", "Exobiologist"))
    if s.get("tipo") == "rango" and ":" in req:
        nom = req.split(":", 1)[1].strip()
        for tabla, k in ((FED_R, "Federation"), (EMP_R, "Empire")):
            if ("federal" in req) == (k == "Federation") and nom in tabla and rk.get(k) is not None:
                return rk[k] >= tabla.index(nom)
    return False

def perm_tengo(sistema, d=None):
    return bool((cfg.get("perm") or {}).get(sistema)) or perm_auto(sistema, d)

def perm_falta(nombre, d=None):
    """El sistema necesita permiso y no lo tienes: el dato de permisos.json; si no está, None."""
    s = PERM_SYS.get((nombre or "").lower())
    if s and _perm_vale(s) and not perm_tengo(s["sistema"], d):
        return s
    return None

def perm_region(nombre):
    """Región cerrada por el nombre del sector (aproximado)."""
    n = (nombre or "").lower()
    for r in PERM.get("regiones") or []:
        if r.get("tipo") != "bloqueado":
            continue
        base = r["region"].lower().split(" (")[0]
        if n.startswith(base + " ") or (base in ("bleia", "praei") and re.match(base + r"\d\b", n)):
            return r
    return None

def perm_como(s):
    if s.get("mision_estacion"):
        return f"misión en {s['mision_estacion']} ({s.get('mision_sistema') or ''})".replace(" ()", "")
    req = s.get("requisito") or "?"
    return "sin forma conocida de conseguirlo" if req.lower().startswith("desconocido") else req

def view_perm(surf, d, flags, now):
    _perm_init()
    pages = max(1, (len(PERM_LIST) + PERMPP - 1) // PERMPP)
    pg = ui.get("permpage", 0) % pages
    n = sum(1 for s in PERM_LIST if perm_tengo(s, d))
    top = [("TODOS ON", None), ("TODOS OFF", None), (f"PÁG {pg + 1}/{pages} · {n} TUYOS", None)]
    for i, (t, _) in enumerate(top):
        draw_button(surf, grid(i, 3, 1, TOP, TOP + 40), t, None, F["btn"] if i < 2 else F["small"],
                    lit=flash.get((1246, 100 + i), 0) > now)
    for i, s in enumerate(PERM_LIST[pg * PERMPP:(pg + 1) * PERMPP]):
        r = grid(i, 2, 6, TOP + 38, H)
        auto = perm_auto(s, d)
        tengo = auto or bool((cfg.get("perm") or {}).get(s))
        lit = flash.get((1246, i), 0) > now
        if tengo or lit:
            pygame.draw.rect(surf, WHITE if lit else ORANGE, r, border_radius=6)
        else:
            pygame.draw.rect(surf, ORANGE, r, 2, border_radius=6)
        col = BLACK if tengo or lit else ORANGE
        tipo = (PERM_SYS.get(s.lower()) or {}).get("tipo") or ""
        tag = "AUTO" if auto else {"rango": "RANGO", "reputacion": "REP.", "raro": "RARO", "accesible": "TODOS"}.get(tipo, "")
        if tag:
            put(surf, F["tiny"], tag, (r.right - 5, r.centery), col, anchor="midright")
        x1 = r.right - 8 - (tw_(F["tiny"], tag) if tag else 0)
        put(surf, F["small"] if len(s) > 14 else F["btn"], s.upper(), ((r.x + 4 + x1) // 2, r.centery), col, x1 - r.x - 8,
            anchor="center")

def tap_perm(x, y):
    _perm_init()
    pages = max(1, (len(PERM_LIST) + PERMPP - 1) // PERMPP)
    pg = ui.get("permpage", 0) % pages
    on = cfg.setdefault("perm", {})
    for i in range(3):
        if grid(i, 3, 1, TOP, TOP + 40).collidepoint(x, y):
            tap_flash((1246, 100 + i))
            if i < 2:
                for s in PERM_LIST:
                    on[s] = i == 0
                cfg["permini"] = True
                save_cfg()
            else:
                ui["permpage"] = pg + 1
            return
    for i, s in enumerate(PERM_LIST[pg * PERMPP:(pg + 1) * PERMPP]):
        if grid(i, 2, 6, TOP + 38, H).collidepoint(x, y):
            tap_flash((1246, i))
            if perm_auto(s):
                set_alert("LO TIENES POR RANGO", s, GREEN, 2, kind="info")
            else:
                on[s] = not on.get(s, False)
                cfg["permini"] = True
                save_cfg()
            return

VIEWS[1246] = view_perm

# RUTA: marca SIN PERMISO en la lista
_route_marks_v1116 = route_marks

def route_marks(name, cls):
    out = _route_marks_v1116(name, cls)
    try:
        if perm_falta(name) or perm_region(name):
            out = [("SIN PERMISO", RED)] + out
    except Exception:
        pass
    return out

# ficha del sistema de la ruta: candado con el permiso (el resto como antes)
_view_rsys_v1116 = view_rsys

def view_rsys(surf, d, flags, now):
    name = (ui.get("rsys") or ("?", ""))[0]
    s = PERM_SYS.get((name or "").lower())
    rg = None if s else perm_region(name)
    if not s and not rg:
        return _view_rsys_v1116(surf, d, flags, now)
    _view_rsys_v1116(surf, d, flags, now)
    if s:
        ok = perm_tengo(s["sistema"], d)
        txt = (f"PERMISO: LO TIENES" if ok else "PERMISO: TE FALTA") + f" · {s.get('titular') or ''}"
        sub = perm_como(s) if not ok else (s.get("ventajas") or "")
    else:
        ok, txt, sub = False, f"ZONA CERRADA: {rg['region'].upper()}", "no se conoce forma de conseguir el permiso"
    r = pygame.Rect(100, H - 46, W - 104, 42)
    pygame.draw.rect(surf, BLACK, r, border_radius=5)
    pygame.draw.rect(surf, GREEN if ok else RED, r, 2, border_radius=5)
    put(surf, F["small"], txt, (r.x + 6, r.y + 4), GREEN if ok else RED, r.w - 12)
    if sub:
        put(surf, F["tiny"], sub, (r.x + 6, r.y + 24), WHITE, r.w - 12)

VIEWS[212] = view_rsys

# avisos: PERMISO NECESARIO (ruta, ruta externa, destino), VENTAJAS CERCANAS, CUERPO CERRADO
PW = {"t": 0.0, "dichos": {}, "sys": None, "cerca": {}, "cuerpo": {}, "coords": False, "rkey": None}
PERM_CUERPOS = {(c.get("cuerpo") or "").lower(): c for c in PERM.get("cuerpos") or []}
PERM_CUERPOS.update({"luna": PERM_CUERPOS.get("moon"), "tritón": PERM_CUERPOS.get("triton")})
PERM_CUERPOS = {k: v for k, v in PERM_CUERPOS.items() if v}

def _perm_nombres(d):
    out = []
    for r in d.get("route") or []:
        if r and r[0]:
            out.append(r[0])
    end = d.get("routeend")
    if end and end[0]:
        out.append(end[0])
    for p in ((d.get("rutaext") or {}).get("p") or []) if isinstance(d.get("rutaext"), dict) else []:
        if p and p[0]:
            out.append(p[0])
    tg = (d.get("nav") or {}).get("target")
    if tg:
        out.append(tg)
    return out

def perm_watch(d, now):
    if now - PW["t"] < 1:
        return
    PW["t"] = now
    _perm_init()
    # 1) PERMISO NECESARIO
    if ev_on("permruta"):
        for n in _perm_nombres(d):
            s = perm_falta(n, d)
            rg = None if s else perm_region(n)
            if not (s or rg) or now - PW["dichos"].get(n, 0) < 1800:
                continue
            PW["dichos"][n] = now
            if s:
                _xa_show("permruta", col=RED, title="PERMISO NECESARIO", big=n.upper(),
                         lines=[perm_como(s), "sin él no podrás saltar a este sistema"], secs=8)
            else:
                _xa_show("permruta", col=RED, title="ZONA CERRADA", big=n.upper(),
                         lines=[rg["region"], "no se conoce forma de conseguir el permiso"], secs=8)
            break
    # 2) VENTAJAS CERCANAS (de los sistemas con permiso que tienes)
    if ev_on("permcerca"):
        if not PW["coords"] and now - START_T > 90:
            PW["coords"] = True
            for s in PERM.get("sistemas") or []:
                if s.get("ventajas"):
                    redsm_want(s["sistema"])
        sy, pos = d.get("system"), d.get("starpos")
        if sy and sy != PW["sys"] and pos and len(pos) == 3:
            PW["sys"] = sy
            for s in PERM.get("sistemas") or []:
                if not s.get("ventajas") or s["sistema"] == sy or not perm_tengo(s["sistema"], d):
                    continue
                c = (REDSM.get(s["sistema"]) or {}).get("coords") or {}
                if c.get("x") is None:
                    continue
                dist = math.dist(pos, (c["x"], c["y"], c["z"]))
                if dist <= 15 and now - PW["cerca"].get(s["sistema"], 0) > 86400:
                    PW["cerca"][s["sistema"]] = now
                    aviso_num("permcerca", f"CERCA: {s['sistema'].upper()} · {dist:.0f} AL".replace(".", ","), s["ventajas"], BLUE, 8)
                    break
    # 3) CUERPO CERRADO (la Luna, Tritón, Diso 5 C, Lave 2)
    if ev_on("permcuerpo"):
        nm = ((d.get("dest") or {}).get("name") or "").lower()
        c = PERM_CUERPOS.get(nm)
        if c and (c.get("sistema") or "").lower() == (d.get("system") or "").lower() and now - PW["cuerpo"].get(nm, 0) > 600:
            PW["cuerpo"][nm] = now
            _xa_show("permcuerpo", col=RED, title="CUERPO CERRADO", big=c["cuerpo"].upper(),
                     lines=[f"permiso de {c.get('titular')}", "no se puede aterrizar: no se conoce cómo conseguirlo"], secs=7)

START_T = time.time()

# ===============================================================================================================
# 4) MERCANCÍAS RARAS: aviso al atracar donde venden una
# ===============================================================================================================
RARAS = {}
try:
    import csv as _csv
    for _r in _csv.DictReader(open(os.path.join(DATOS_DIR, "mercancias_raras.csv"), encoding="utf-8")):
        RARAS.setdefault(((_r.get("estacion") or "").lower(), (_r.get("sistema") or "").lower()), []).append(_r.get("mercancia"))
except Exception as _e:
    print("mercancias_raras.csv:", _e)
RARA_W = {"mid": None}

def rara_watch(d):
    st = d.get("station") or {}
    if not d.get("Flags", 0) & 1:
        RARA_W["mid"] = None; return
    mid = st.get("mid")
    if not mid or mid == RARA_W["mid"]:
        return
    RARA_W["mid"] = mid
    L = RARAS.get(((st.get("name") or "").lower(), (d.get("system") or "").lower()))
    if L:
        aviso_num("rara", "MERCANCÍA RARA AQUÍ", ", ".join(L) + " · se paga mejor a más de 150 al", BLUE, 8)

# ===============================================================================================================
# 5) ROBOT: cada aviso con su número; «quita este aviso» y «silencia este aviso»
# ===============================================================================================================
ROB_ULT = {"ev": None, "t": 0.0, "tit": ""}

_sc_aviso_v1116 = sc_aviso

def sc_aviso(ev, kind, titulo, dato):
    n = ev_num(ev) if ev else None
    if n:
        ROB_ULT.update(ev=ev, t=time.time(), tit=titulo or "")
        titulo = f"#{n} {titulo or ''}"
    return _sc_aviso_v1116(ev, kind, titulo, dato)

def _ev_nombre(k):
    return next((n for k_, n in EV_LIST if k_ == k), k)

def r_quita_aviso(d, now, t):
    ev, cuando = ROB_ULT["ev"], ROB_ULT["t"]
    nb = NUMB.get("ev") if NUMB.get("t") and now - NUMB["t"] < 600 else None     # o el último de la pantalla
    if nb and (not ev or NUMB["t"] > cuando):
        ev, cuando = nb, NUMB["t"]
    if not ev or now - cuando > 600:
        return "No tengo ningún aviso reciente con número para quitar"
    silencia = _hay(t, "silencia", "silencio", "callar", "calla")
    store, master = ("snd", "sound") if silencia else ("ev", "alerts")
    cfg.setdefault(store, {})[ev] = False
    cfg[master] = True
    save_cfg()
    plog(f"Por voz: {'silenciado' if silencia else 'quitado'} el aviso #{ev_num(ev)} {_ev_nombre(ev)}")
    return (f"Silenciado el aviso {ev_num(ev)}, {_ev_nombre(ev)}. El mensaje sigue; el pitido se vuelve a poner en SONIDO"
            if silencia else f"Quitado el aviso {ev_num(ev)}, {_ev_nombre(ev)}. Se vuelve a poner en ALERTAS")

PREG_V1110.insert(0, (lambda t: _hay(t, "quita", "quitar", "silencia", "silenciar") and _hay(t, "aviso", "mensaje", "alerta"),
                      r_quita_aviso))

# ===============================================================================================================
# todo lo de arriba se mira una vez por segundo desde el dibujo
# ===============================================================================================================
_render_v1116 = render
W1116 = {"t": 0.0}

def render(surf):
    r_ = _render_v1116(surf)
    now = time.time()
    if now - W1116["t"] >= 1:
        W1116["t"] = now
        try:
            with lock:
                d, rx = state["data"], state["rx"]
            if d and now - rx < 5:
                for fn in (edsm_correccion_watch, rara_watch):
                    try:
                        fn(d)
                    except Exception as e:
                        log_exc(fn.__name__, e)
                perm_watch(d, now)
        except Exception as e:
            log_exc("v1.1.16", e)
    return r_

_on_tap_v1116 = on_tap

def on_tap(x, y):
    if ui.get("view") == 1246 and y > TOP and not ui.get("idle_on"):
        tap_perm(x, y); TAP_EV.set(); return
    return _on_tap_v1116(x, y)
