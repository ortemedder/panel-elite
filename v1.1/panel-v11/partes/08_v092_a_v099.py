# Panel Elite v1.1 · parte 08: v092 a v099 (lineas 6574-8267 del panel entero)
# ---------- v0.92 ----------
SCAN_ES = {"Cargo": "BODEGA", "Crime": "DELITOS", "Cabin": "PASAJEROS", "Data": "DATOS", "Unknown": "DESCONOCIDO",
           "Tourist": "TURISTAS"}

# fotos: portanaves de operaciones y SurfaceStation solo en Operations
ST_BG.pop("SurfaceStation", None)
BG_FILES["op"] = "fondo_operaciones.jpg"


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
    y, x = TOP + 58, 8
    wd_ = lambda y_: W - 16 if y_ + 18 <= THUMB_TOP else W - 240   # a lo ancho si queda encima de la foto
    own = d.get("carrier") or {}
    if lab == "TU PORTANAVES" and own.get("callsign"):
        av = own.get("avail")
        up = 5e6 + sum(CREW_COST.get(c, 0) for c in own.get("crew") or [])
        if av is not None:
            wk = av / up if up else 99
            put(surf, F["small"], "SALDO DISPONIBLE", (x, y), DIM)
            put(surf, F["btn"], f"{crx(av)} cr", (x + 130, y - 3), ORANGE); y += 18
            put(surf, F["small"], f"gastos ~{crx(up)} cr/semana  ·  da para {wk:.0f} semanas".replace(".", ","),
                (x, y), RED if wk < 2 else ORANGE if wk < 4 else DIM, wd_(y)); y += 20
        if own.get("crew"):
            put(surf, F["small"], "SERVICIOS: " + ", ".join(CREW_ES.get(c, c) for c in own["crew"] if c in CREW_ES),
                (x, y), BLUE, wd_(y)); y += 18
        if own.get("access"):
            put(surf, F["small"], f"ATRAQUE: {ACCESS_ES.get(own['access'], own['access'].upper())}"
                + ("  ·  admite buscados" if own.get("notorious") else ""), (x, y), GREEN, wd_(y)); y += 18
        if own.get("jump"):
            put(surf, F["small"], f"SALTO: {own['jump']} al", (x, y), WHITE, wd_(y))
        return
    di = d.get("dstinfo") or {}
    sv = [SVC_ES.get(v.lower()) for v in di.get("services") or []]
    sv = [v for v in sv if v]
    if sv:
        put(surf, F["small"], "SERVICIOS (última vez): " + ", ".join(dict.fromkeys(sv)), (x, y), BLUE, wd_(y)); y += 18
    if di.get("denied"):
        put(surf, F["small"], f"TE DENEGARON EL ATRAQUE: {di['denied']}", (x, y), RED, wd_(y)); y += 18
    if not sv and not di.get("denied"):
        put(surf, F["small"], "sin datos: los verás al atracar una vez", (x, y), DIM, wd_(y))


def view_navx_navx1(surf, d, flags, now):
    view_navx_navx0(surf, d, flags, now)
    if (d or {}).get("dest") and not (ui.get("navtab") == 2 and not NAVBIG[0]) and not nav_show_pol(d, now):
        carrier_info(surf, d or {})

VIEWS[3] = view_navx_navx1

# SALUDOS (gestos a pie): teclas Gesto 1..8 de tus controles
EMOTES = ["SEÑALAR", "SALUDO INFORMAL", "DE ACUERDO", "EN DESACUERDO", "VAMOS", "ALTO", "APLAUSO", "SALUDO MILITAR"]
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

def pc_now(d, now=None):
    """Hora del PC (la del juego). Si el sender manda su reloj, se corrige el de la Pi."""
    now = time.time() if now is None else now
    pn = (d or {}).get("pcnow")
    return now + (pn - state["rx"]) if pn and state.get("rx") else now





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
    "kestrelmkii": "kestrel", "lynxhighliner": "lynx", "anacondamkii": "anaconda_mkii",
    "f63condor": "federation_fighter", "condor": "federation_fighter", "gu97": "empire_fighter",
    "taipan": "independent_fighter", "xg7trident": "gdn_hybrid_fighter_v1", "trident": "gdn_hybrid_fighter_v1",
    "xg8javelin": "gdn_hybrid_fighter_v2", "javelin": "gdn_hybrid_fighter_v2", "xg9lance": "gdn_hybrid_fighter_v3",
    "lance": "gdn_hybrid_fighter_v3"}
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


def view_market(surf, d, flags, now):
    m = market_pick(d, now)
    if m.get("missing"):
        put(surf, F["btn"], m["missing"].upper(), (W // 2, (H + TOP) // 2 - 22), ORANGE, W - 16, anchor="center")
        put(surf, F["btn"], "abre su mercado para ver los precios", (W // 2, (H + TOP) // 2 + 4), DIM, anchor="center")
        put(surf, F["small"], "EDSM no tiene sus precios" if m.get("edsm") else "consultando EDSM...",
            (W // 2, (H + TOP) // 2 + 28), DIM, anchor="center")
        return
    view_market_base(surf, dict(d or {}, market=m), flags, now)
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
    y = TOP + 80 if carrier_dest(d)[0] not in ("fc", "sq") else H - 40
    put(surf, F["small"], "FACCIÓN", (8, y), DIM)
    put(surf, F["btn"], fac, (8, y + 14), WHITE, W - 16 if y + 34 <= THUMB_TOP else W - 246)
    bits = [x for x in (lvl, state_) if x]
    if bits:
        put(surf, F["btn"], "  ·  ".join(bits), (8, y + 36), col, W - 16 if y + 56 <= THUMB_TOP else W - 246)
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


def view_navx_navx2(surf, d, flags, now):
    view_navx_navx1(surf, d, flags, now)
    if (d or {}).get("dest") and not (ui.get("navtab") == 2 and not NAVBIG[0]) and not nav_show_pol(d, now):
        draw_dest_faction(surf, d or {}, now)

VIEWS[3] = view_navx_navx2
EV_LIST.append(("dsthostil", "DESTINO HOSTIL"))


# ---------- v0.94: BATALLA TERMINADA (el juego no apunta la victoria: se deduce) ----------
BAT = {"on": False}

def battle_note(kind, text, d):
    p = (text or "").split("|")
    now = time.time()
    if kind == "kill" and len(p) > 3 and p[3] == "F":
        if not BAT.get("on"):
            Z = (d or {}).get("footcz") or {}
            BAT.clear()
            BAT.update(on=True, t0=now, k=0, cr=0, med=0, cell=0, gren=0, zone=Z.get("zone") or "", side=Z.get("side") or "")
        BAT["k"] += 1
        BAT["cr"] += float(p[1] or 0)
        BAT["last"] = now
    elif not BAT.get("on"):
        return
    elif kind == "usecons" and p:
        BAT["med" if p[0] == "healthpack" else "cell"] += 1
    elif kind == "thrown":
        BAT["gren"] += 1
    elif kind in ("taxi", "dropship"):
        battle_end(now, delay=7)                     # despues del aviso del transporte

def battle_watch(d, now):
    if BATP.get("a") and now >= BATP["at"]:
        k0 = XA_K[0]
        try:
            XA_K[0] = "battle"
            xa["a"] = dict(BATP["a"], until=now + 15)
            play("ok")
        finally:
            XA_K[0] = k0
        BATP["a"] = None
    if not BAT.get("on"):
        return
    Z = (d or {}).get("footcz") or {}
    if Z.get("zone"):
        BAT["zone"] = Z["zone"]
    if Z.get("side"):
        BAT["side"] = Z["side"]
    if not ((d or {}).get("Flags2", 0) & 1) or now - max(BAT.get("last", 0), fight["t"]) > 120:
        battle_end(now)

BATP = {"a": None, "at": 0}

def battle_end(now, delay=0):
    B = dict(BAT)
    BAT.clear(); BAT["on"] = False
    if B.get("k", 0) < 3:
        return                                       # dos bajas sueltas no son una batalla
    mins = max(1, round(((B.get("last") or now) - B["t0"]) / 60))
    cons = "  ·  ".join(x for x in ((f"botiquines {B['med']}" if B["med"] else ""), (f"células {B['cell']}" if B["cell"] else ""),
                                    (f"granadas {B['gren']}" if B["gren"] else "")) if x)
    BATP["a"] = dict(col=GREEN, title="BATALLA TERMINADA", big=(B.get("zone") or "ZONA DE COMBATE").upper(),
                     lines=[f"{B['k']} bajas  ·  +{crx(B['cr'])} cr sin cobrar",
                            f"duración {mins} min  ·  {B['k'] / mins:.1f} bajas/min".replace(".", ","),
                            cons, f"por {B['side']}" if B.get("side") else ""])
    BATP["at"] = now + delay

EV_LIST.append(("battle", "BATALLA TERMINADA"))


# ---------- v0.95 ----------
def mega_dock(d):
    st = (d or {}).get("station") or {}
    nm = ((st.get("name") or "") + " " + (st.get("sraw") or "")).lower()
    return bool((d or {}).get("mega")) or (st.get("status") == "ATRACADO" and
                                         (st.get("type") == "MegaShip" or "megaship" in nm or "investig" in nm))




# ---------- v0.96 ----------
import threading as _thr
PANEL_PERF_V = {}
TAP_EV = _thr.Event()


def perf_view(v, dt):
    a = PANEL_PERF_V.setdefault(v, [0, 0.0, 0.0])
    a[0] += 1; a[1] += dt; a[2] = max(a[2], dt)
    t0 = PANEL_PERF_V.setdefault("_t", time.time())
    if time.time() - t0 > 300:
        top = sorted(((k, x) for k, x in PANEL_PERF_V.items() if k != "_t"), key=lambda kv: -kv[1][1] / max(1, kv[1][0]))[:5]
        plog("TIEMPOS (5 min): " + "  ".join(f"{MENU.get(k, k)} {x[1] / max(1, x[0]) * 1000:.0f} ms (máx {x[2] * 1000:.0f})" for k, x in top)
             + f"  ·  CPU {PERF.get('cpu') or 0:.0f}%  ·  {PERF.get('mhz') or 0:.0f} MHz  ·  RAM {PERF.get('ram') or 0:.0f}%  ·  {PERF.get('fps') or 0:.0f} FPS")
        PANEL_PERF_V.clear(); PANEL_PERF_V["_t"] = time.time()

# 1. version del sender
VERW = {"done": False}
SENDER_REQ = "v1.0b13"                                   # sender que va con este panel (la v1.1 usa el b13)

def ver_check(d):
    sv = (d or {}).get("sver")
    if VERW["done"] or not d or "Flags" not in d:
        return
    VERW["done"] = True
    if sv != SENDER_REQ:
        k0 = XA_K[0]
        try:
            XA_K[0] = "keys"
            xa["a"] = dict(until=time.time() + 10, col=ORANGE, title="VERSIONES DISTINTAS", big=f"sender {sv or 'antiguo'} · necesita {SENDER_REQ}",
                           lines=[f"pon en el PC el elite_sender.py {SENDER_REQ} (va con el panel {PANEL_VER.split(' · ')[0]})"])
        finally:
            XA_K[0] = k0


def view_changelog(surf, d, flags, now):
    view_changelog_base(surf, d, flags, now)
    sv = (d or {}).get("sver")
    pygame.draw.rect(surf, BLACK, (0, H - 18, W, 18))
    put(surf, F["small"], f"panel {PANEL_VER.split(' · ')[0]}  ·  sender {sv or 'antiguo (sin versión)'}", (8, H - 16),
        GREEN if sv == SENDER_REQ else ORANGE, W - 16)

VIEWS[1245] = view_changelog

# 3. aviso de dinero sin cobrar (una vez al arrancar)
UNC = {"done": False}

def uncl_watch(d, now):
    if UNC["done"] or not d:
        return
    led = ((d.get("footcz") or {}).get("led") or {})
    t0 = d.get("uncl_t0")
    if not t0 or not led.get("cr"):
        return
    UNC["done"] = True
    days = int((now - t0) // 86400)
    if days >= 2 or led["cr"] >= 50e6:
        k0 = XA_K[0]
        try:
            XA_K[0] = "redeem"
            xa["a"] = dict(until=now + 8, col=ORANGE, title="SIN COBRAR", big=f"{crx(led['cr'])} cr",
                           lines=[f"desde hace {days} días" if days else "", "si te destruyen la nave, se pierden"])
        finally:
            XA_K[0] = k0

# 7. mineria por hora

def view_mining_vmin0(surf, d, flags, now):
    view_mining_base(surf, d, flags, now)
    m = (d or {}).get("mining") or {}
    tons = sum((m.get("refined") or {}).values())
    if tons and m.get("t0") and m.get("t1") and m["t1"] > m["t0"]:
        h = (m["t1"] - m["t0"]) / 3600
        rate = tons / h if h > 0.02 else None
        prices = {r[0].lower(): r[1] for r in (((d or {}).get("market") or {}).get("best") or [])}
        prices.update({r[0].lower(): r[2] for r in (((d or {}).get("market") or {}).get("sell") or [])})
        val = sum(n * prices.get(k.lower(), 0) for k, n in (m.get("refined") or {}).items())
        put(surf, F["small"], f"{rate:.0f} t/h".replace(".", ",") + (f"  ·  ~{crx(val / h)} cr/h" if val and h > 0.02 else "")
            if rate else f"{tons} t refinadas", (W - 8, H - 42), GREEN, W - 236, anchor="topright")

VIEWS[10] = view_mining_vmin0

def mining_cargo_bar(surf, d, now):
    """Barra de la bodega en MINERIA: naranja desde el 90 %, roja parpadeando llena."""
    cap = (d or {}).get("cargocap")
    used = sum(c for _, c in ((d or {}).get("cargo") or []))
    if not cap:
        return
    pct = min(1.0, used / cap)
    full = used >= cap
    col = RED if full else ORANGE if pct >= 0.9 else BLUE
    r = pygame.Rect(8, H - 44, 220, 16)
    pygame.draw.rect(surf, BLACK, r.inflate(4, 4))
    pygame.draw.rect(surf, DIM, r, 1)
    if not full or int(now * 3) % 2 == 0:
        pygame.draw.rect(surf, col, (r.x + 2, r.y + 2, int((r.w - 4) * pct), r.h - 4))
    txt = "¡BODEGA LLENA!" if full else (f"BODEGA {pct * 100:.0f} %" + (f"  ·  {used}/{cap} t" if pct < 0.9 else "  ·  casi llena"))
    put(surf, F["small"], txt, r.center, WHITE if full or pct >= 0.9 else WHITE, r.w - 8, anchor="center")


def view_mining(surf, d, flags, now):
    view_mining_vmin0(surf, d, flags, now)
    if "rhino" not in ((d or {}).get("srvtype") or "").lower():
        mining_cargo_bar(surf, d, now)

VIEWS[10] = view_mining

MINE = {"sig": None, "t": 0.0}

def mining_active(d, now):
    """Se esta minando: prospector, recolector, roca prospectada o tonelada refinada en los ultimos 10 min."""
    m = (d or {}).get("mining") or {}
    sig = (m.get("prospectors"), m.get("collectors"), m.get("t1"), str(m.get("last"))[:200])
    if MINE["sig"] is None:
        MINE["sig"] = sig
    elif sig != MINE["sig"]:
        MINE["sig"] = sig; MINE["t"] = now
    return now - MINE["t"] < 600

# 8. Powerplay: meritos de la semana y corte



# ---------- v0.97: ingenieros ----------
_ENGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingenieros")
_ENG = {"data": None}
ENG_PROG = {"Known": "conocido", "Invited": "invitado", "Acquainted": "le conoces", "Unlocked": "desbloqueado", "Barred": "vetado"}

def eng_table():
    if _ENG["data"] is None:
        try:
            import json as _j
            with open(os.path.join(_ENGDIR, "ingenieros.json"), encoding="utf-8") as f:
                _ENG["data"] = {k: dict(v, key=k) for k, v in _j.load(f).items()}
        except Exception as e:
            log_exc("ingenieros.json", e)
            _ENG["data"] = {}
    return _ENG["data"]

def eng_at(system):
    sy = (system or "").lower()
    return next((v for v in eng_table().values() if v.get("system", "").lower() == sy), None) if sy else None

def eng_here(d):
    return eng_at((d or {}).get("system"))

def eng_status(e, d):
    p = ((d or {}).get("engprog") or {}).get(e["name"].lower())
    if not p:
        return "no le conoces", DIM
    prog, rank = p
    if prog == "Unlocked":
        return (f"rango {rank}" if rank is not None else "desbloqueado"), GREEN
    return ENG_PROG.get(prog, prog.lower() or "?"), ORANGE

def eng_where(e):
    pl = e.get("planet") or ""
    body = pl if pl and not pl[:1].isdigit() and len(pl.split()[0]) > 2 else f"{e['system']} {pl}".strip()
    return f"{e['base']}  ·  {body}  ·  {e.get('region', '')}".strip(" ·")

ENGW = {"sys": None}

def eng_watch(d, now):
    sy = (d or {}).get("system")
    if not sy or sy == ENGW["sys"]:
        return
    first = ENGW["sys"] is None
    ENGW["sys"] = sy
    e = eng_at(sy)
    if not e or first:
        return
    st, _ = eng_status(e, d)
    k0 = XA_K[0]
    try:
        XA_K[0] = "engsys"
        xa["a"] = dict(until=now + 8, col=BLUE, title="INGENIERO EN EL SISTEMA", big=e["name"].upper(),
                       lines=[st, eng_where(e)])
        play("ok")
    finally:
        XA_K[0] = k0

def eng_card(surf, d, r):
    """Ficha del ingeniero: cara, nombre y rango, donde esta y lo que mejora."""
    e = eng_here(d)
    if not e:
        return False
    pygame.draw.rect(surf, BLACK, r)
    pygame.draw.rect(surf, BLUE, r, 1, border_radius=6)
    ph = pygame.Rect(r.x + 6, r.y + 6, int((r.h - 12) * 240 / 210), r.h - 12)
    real, rr = (surf.real, surf._r(ph)) if type(surf).__name__ == "ScaledSurf" else (surf, ph)
    img = ship_img(os.path.join(_ENGDIR, f"ing_{e['key']}.jpg"), rr.w, rr.h, 255)
    if img is not None:
        real.blit(img, rr.topleft)
    x = ph.right + 8
    wd = r.right - x - 6
    st, col = eng_status(e, d)
    narrow_ = r.w < W - 100                         # ficha estrecha: el rango baja a la segunda linea
    put(surf, F["btn"], e["name"].upper(), (x, r.y + 4), BLUE, wd if narrow_ else wd - F["small"].size(st)[0] - 12)
    if not narrow_:
        put(surf, F["small"], st, (r.right - 8, r.y + 7), col, 110, anchor="topright")
    put(surf, F["small"], (st + "  ·  " if narrow_ else "") + eng_where(e), (x, r.y + 26), col if narrow_ else ORANGE, wd)
    mods = sorted(e.get("mods") or [], key=lambda m: -int(m[1]) if m[:1] == "G" and m[1:2].isdigit() else 0)
    y = r.y + 44
    line = ""
    for m in mods:
        t = (line + "  ·  " if line else "") + m
        if F["small"].size(t)[0] > wd:
            put(surf, F["small"], line, (x, y), WHITE, wd); y += 15; line = m
            if y > r.bottom - 16:
                break
        else:
            line = t
    if line and y <= r.bottom - 16:
        put(surf, F["small"], line, (x, y), WHITE, wd)
    return True


def view_explo(surf, d, flags, now):
    view_explo_base(surf, d, flags, now)
    eng_card(surf, d or {}, pygame.Rect(4, H - 112, W - 8, 108))

VIEWS[71] = view_explo


# ---------- v0.97b: la ficha del ingeniero pasa a NAVEGACION ----------
view_explo = view_explo_base
VIEWS[71] = view_explo_base

def view_navx(surf, d, flags, now):
    view_navx_navx2(surf, d, flags, now)
    if not (ui.get("navtab") == 2 and not NAVBIG[0]) and not nav_show_pol(d, now) and eng_here(d):
        th = carrier_dest(d or {})[0]                 # foto de su base (destino marcado) a la derecha
        eng_card(surf, d or {}, pygame.Rect(4, H - 112, W - (240 if th else 8), 108))

VIEWS[3] = view_navx


def eng_by_base(name):
    n = (name or "").strip().lower()
    return next((v for v in eng_table().values() if v.get("base", "").lower() == n), None) if n else None


# ---------- v0.98: tactil de la pantalla HDMI ----------
def is_touch2(d):
    n = (d.name or "")
    if "ADS7846" in n or "touch" in n.lower() or "触控" in n or "qdtech" in n.lower() or "ilitek" in n.lower():
        return True
    try:
        from evdev import ecodes as ec_
        caps = d.capabilities()
        abs_ = [a[0] if isinstance(a, tuple) else a for a in caps.get(ec_.EV_ABS, [])]
        return ec_.ABS_X in abs_ and ec_.ABS_Y in abs_ and ec_.EV_REL not in caps
    except Exception:
        return False

BIGTAP_N = [0]


def touch_loop2():
    """Segundo tactil (el de la HDMI) cuando tambien esta la pantalla pequena."""
    try:
        from evdev import InputDevice, list_devices, ecodes as ec
    except ImportError:
        return
    while True:
        try:
            devs_ = [InputDevice(p) for p in list_devices()]
        except Exception:
            time.sleep(5); continue
        dev = next((d for d in devs_ if "ADS7846" not in d.name and is_touch2(d)), None)
        if not dev:
            time.sleep(5); continue
        print("Tactil HDMI:", dev.name)
        try:
            ax, ay = dev.absinfo(ec.ABS_X), dev.absinfo(ec.ABS_Y)
            rx = ry = 0; t_down = None; pos = None
            for ev in dev.read_loop():
                if ev.type == ec.EV_ABS:
                    if ev.code == ec.ABS_X: rx = ev.value
                    elif ev.code == ec.ABS_Y: ry = ev.value
                elif ev.type == ec.EV_KEY and ev.code in (ec.BTN_TOUCH, ec.BTN_LEFT):
                    if ev.value == 1:
                        t_down, pos = time.time(), None
                        DRAG.update(on=False, p0=None, last=None)
                    elif t_down is not None:
                        dur = time.time() - t_down; t_down = None
                        if pos is None:
                            continue
                        if DRAG.get("on"):                       # b18: era un arrastre, no un toque
                            drag_end(); continue
                        if dur >= 1.2:
                            hdmi_toggle(); TAP_EV.set()          # pulsacion larga: PANEL <-> 4 CUADROS
                        else:
                            big_tap(*pos)
                elif ev.type == ec.EV_SYN and t_down is not None and pos is None:
                    pos = ((rx - ax.min) / max(1, ax.max - ax.min), (ry - ay.min) / max(1, ay.max - ay.min))
                elif ev.type == ec.EV_SYN and t_down is not None:
                    drag_move(pos, ((rx - ax.min) / max(1, ax.max - ax.min), (ry - ay.min) / max(1, ay.max - ay.min)))
        except OSError:
            time.sleep(2)                                # desconectado: se vuelve a buscar
        except Exception as e:
            log_exc("tactil HDMI", e); time.sleep(5)


# ---------- v0.99: voz con Piper y combate solo con armas fuera ----------
def hp_out(d, flags):
    """Armas sacadas de verdad (no el escaner en modo analisis ni justo despues de escanear o lanzar drones)."""
    return bool(flags & 64) and not flags & (1 << 27) and pc_now(d) - ((d or {}).get("scan_t") or 0) > 20

PIPER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "piper")
PIPER_BIN = os.path.join(PIPER_DIR, "piper", "piper")
PIPER_MODEL = os.path.join(PIPER_DIR, "es.onnx")
PIPER_PRE = ["TE ATACAN", "ESCUDOS CAÍDOS", "ESCUDOS ARRIBA", "Voz de la nave activada"]

def piper_ok():
    return os.path.exists(PIPER_BIN) and os.path.exists(PIPER_MODEL)

def _piper_wav(t, low=False):
    d = os.path.join(PIPER_DIR, "cache")
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, hashlib.md5(t.encode("utf-8")).hexdigest()[:16] + ".wav")
    if not os.path.exists(f):
        cmd = (["nice", "-n", "19"] if low else []) + [PIPER_BIN, "--model", PIPER_MODEL, "--output_file", f + ".tmp"]
        subprocess.run(cmd, input=t.encode("utf-8"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        os.replace(f + ".tmp", f)
    return f

def _piper_play(t):
    try:
        f = _piper_wav(t)
        voice["proc"] = subprocess.Popen(["aplay", "-q", f], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log_exc("voz piper", e)
    finally:
        voice["busy"] = False

def _piper_pre():
    time.sleep(30)                                   # tras el arranque, sin prisa
    for t in PIPER_PRE:
        try:
            _piper_wav(t, low=True)
        except Exception:
            pass





if piper_ok():
    threading.Thread(target=_piper_pre, daemon=True).start()


# ---------- v0.99b: ficha del objetivo en la pantalla grande ----------
def view_target(surf, d, flags, now):
    view_combat(surf, d, flags, now)
    pygame.draw.rect(surf, BLACK, (0, CARD6, W, H - CARD6))
    t = (d or {}).get("target") or {}
    r = pygame.Rect(W // 2 - 122, CARD6 + 6, 244, H - CARD6 - 12)
    if not (cfg.get("cmdrpics", True) and ship_photo(surf, {"type": t.get("stype"), "ship": t.get("ship")}, {}, r)):
        put(surf, F["small"], "sin foto de esta nave", r.center, DIM, anchor="center")

VIEWS[177] = view_target
MENU[177] = "OBJETIVO"


# ---------- v0.99d: depositos de construccion ----------
ST_BG.update({"SpaceConstructionDepot": "deposito_espacial", "PlanetaryConstructionDepot": "deposito_planetario"})
BG_FILES.update({"deposito_espacial": "fondo_deposito_espacial.jpg", "deposito_planetario": "fondo_deposito_planetario.jpg"})
ST_TYPE.update({"SpaceConstructionDepot": "Depósito de construcción", "PlanetaryConstructionDepot": "Depósito planetario"})


# ---------- v0.99j: cronometro de la mega nave a mano ----------
MEGA = {"t0": None}

def ops_on(d):
    return bool(((d or {}).get("ops") or {}).get("on"))

def mega_left(d, now):
    if not ops_on(d):
        MEGA["t0"] = None
        return None
    t0 = MEGA["t0"]
    if t0 and t0 + MEGA_SECS - now < -30:
        MEGA["t0"] = t0 = None                        # acabado: vuelve a 15:00 en espera
    return False if not t0 else t0 + MEGA_SECS - now   # False = en espera de que lo toques

def mega_tap(now=None):
    MEGA["t0"] = time.time() if now is None else now
    xa.pop("mega60", None)
    play("ok")
    TAP_EV.set()

def mega_rect(w, h):
    k = h / H
    return pygame.Rect(w - int(140 * k), h - int(52 * k), int(132 * k), int(46 * k))

def mega_watch(d, now):
    left = mega_left(d, now)
    if not left:
        return
    k0 = XA_K[0]
    try:
        XA_K[0] = "opmega"
        key = MEGA["t0"]
        if 0 < left <= 60 and xa.get("mega60") != key:
            xa["mega60"] = key
            xa["a"] = dict(until=now + 6, col=RED, title="MEGA NAVE", big="¡QUEDA 1 MINUTO!", lines=["despega ya"])
            play("alarm")
    finally:
        XA_K[0] = k0

def draw_mega(surf, d, now):
    left = mega_left(d, now)
    if left is None:
        return
    w, h = surf.get_size()
    k = h / H
    key = round(k, 2)
    if key not in _MGF:
        _MGF[key] = (pygame.font.Font(None, int(40 * k)), pygame.font.Font(None, int(18 * k)))
    f1, f2 = _MGF[key] if type(surf).__name__ != "ScaledSurf" else (F["big"], F["small"])
    r = mega_rect(w, h)
    if left is False:
        col, txt, lab = DIM, "15:00", "MEGA NAVE · TOCA"
    else:
        col = GREEN if left > 300 else ORANGE if left > 60 else (RED if int(now * 3) % 2 == 0 else WHITE)
        l_ = max(0, int(left)); txt, lab = f"{l_ // 60}:{l_ % 60:02d}", "MEGA NAVE"
    pygame.draw.rect(surf, BLACK, r, border_radius=6)
    pygame.draw.rect(surf, col, r, 2, border_radius=6)
    put(surf, f2, lab, (r.centerx, r.y + int(10 * k)), DIM, anchor="center")
    put(surf, f1, txt, (r.centerx, r.y + int(30 * k)), col, anchor="center")






# ---------- v0.99k: vigilante del bucle principal ----------
WD = {"t": time.time(), "on": False}
WD_SECS = 45

def wd_dump(why):
    import sys, traceback as tb_
    names = {t.ident: t.name for t in threading.enumerate()}
    out = [f"PANEL COLGADO ({why}): reinicio. Donde estaba cada hilo:"]
    for tid, fr in sys._current_frames().items():
        st = tb_.extract_stack(fr)[-4:]
        out.append(f"  [{names.get(tid, tid)}] " + " <- ".join(f"{x.name}:{x.lineno}" for x in reversed(st)))
        out.append("      " + ((st[-1].line or "") if st else ""))
    plog("\n".join(out))

def watchdog_loop():
    while True:
        time.sleep(5)
        if WD["on"] and time.time() - WD["t"] > WD_SECS:
            try:
                wd_dump(f"{time.time() - WD['t']:.0f} s sin dibujar")
            finally:
                os._exit(3)                              # systemd lo arranca otra vez




# ---------- v1.0 beta 1 ----------
# voz: "cr" son creditos



# avatar de Inara: se baja una vez y se guarda en avatares/ junto a panel.py
AV_DIR = os.path.join(PANEL_DIR, "avatares")
_AV = {}

def _av_file(url):
    ext = os.path.splitext(url.split("?")[0])[1].lower()
    return os.path.join(AV_DIR, hashlib.md5(url.encode()).hexdigest()[:16] + (ext if ext in (".jpg", ".jpeg", ".png", ".gif") else ".jpg"))

def _av_get(url):
    try:
        import urllib.request
        os.makedirs(AV_DIR, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "PanelEliteRPi/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read(2_000_000)
        f = _av_file(url)
        with open(f + ".tmp", "wb") as o:
            o.write(data)
        os.replace(f + ".tmp", f)
        _AV.pop(("st", url), None)
    except Exception as e:
        _AV[("st", url)] = time.time()                      # fallo: se reintenta en 1 hora
        log_exc("avatar", e)

def avatar_photo(surf, url, r):
    if not url or not cfg.get("cmdrpics", True) or not url.startswith("http"):
        return False
    real, rr = (surf.real, surf._r(r)) if type(surf).__name__ == "ScaledSurf" else (surf, r)
    key = (url, rr.w, rr.h)
    img = _AV.get(key)
    if img is None:
        f = _av_file(url)
        if not os.path.exists(f):
            st = _AV.get(("st", url))
            if st is None or (st != "pend" and time.time() - st > 3600):
                _AV[("st", url)] = "pend"
                threading.Thread(target=_av_get, args=(url,), daemon=True).start()
            return False
        try:
            src = pygame.image.load(f)
            sw, sh = src.get_size()
            sc = min(rr.w / sw, rr.h / sh)
            im = pygame.transform.smoothscale(src, (max(1, int(sw * sc)), max(1, int(sh * sc))))
            img = pygame.Surface(rr.size); img.fill(BLACK)
            img.blit(im, ((rr.w - im.get_width()) // 2, (rr.h - im.get_height()) // 2))
        except Exception as e:
            log_exc("avatar", e); img = False
        _AV[key] = img
    if not img:
        return False
    real.blit(img, rr.topleft)
    pygame.draw.rect(surf, DIM, r, 1, border_radius=3)
    return True

# RAM % y MHz junto a CPU y temperatura
PERF_MAXMHZ = [None]

def _rd(p):
    try:
        with open(p) as f:
            return f.read()
    except OSError:
        return ""


def perf_parts():
    c, t, ram, mhz = PERF["cpu"], PERF["temp"], PERF.get("ram"), PERF.get("mhz")
    out = []
    if c is not None:
        out.append((f"CPU {c:.0f} %", GREEN if c < 30 else ORANGE if c < 60 else RED))
    if mhz:
        out.append((f"{mhz:.0f} MHz", ORANGE if power.get("cap") else GREEN))
    if t is not None:
        out.append((f"{t:.0f} °C", GREEN if t < 70 else ORANGE if t < 80 else RED))
    if ram is not None:
        out.append((f"RAM {ram:.0f} %", GREEN if ram < 70 else ORANGE if ram < 85 else RED))
    out.append((f"{PERF['fps']:.0f} FPS", GREEN))
    return out

# salud de la Pi: reloj sin sincronizar y poco espacio en la tarjeta SD
def salud_loop():
    time.sleep(60)                                       # tras el arranque, que le de tiempo a coger la hora
    avisado = {"ntp": 0, "sd": 0}
    while True:
        try:
            r = subprocess.run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
                               capture_output=True, text=True, timeout=5).stdout.strip()
            if r == "no" and time.time() - avisado["ntp"] > 6 * 3600:
                avisado["ntp"] = time.time()
                plog("AVISO: el reloj de la Pi no está sincronizado con internet")
                set_alert("RELOJ SIN SINCRONIZAR", "la Pi no tiene la hora de internet", ORANGE, 8)
        except Exception:
            pass
        try:
            du = shutil.disk_usage(PANEL_DIR)
            if du.free / du.total < 0.10 and time.time() - avisado["sd"] > 6 * 3600:
                avisado["sd"] = time.time()
                plog(f"AVISO: poco espacio en la tarjeta SD ({du.free / 1e9:.1f} GB libres)")
                set_alert("POCO ESPACIO EN LA SD", f"quedan {du.free / 1e9:.1f} GB ({100 * du.free / du.total:.0f} %)", ORANGE, 8)
        except Exception:
            pass
        time.sleep(1800)

threading.Thread(target=salud_loop, daemon=True, name="salud").start()


# ---------- v1.0 beta 2: botones de los cuadros (4 CUADROS) ----------


def cell_point(area, how, X, Y):
    # punto de la pantalla grande -> punto del panel (480x320) dentro de ese cuadro
    if how == "fill":
        return (X - area.x) * W / area.w, TOP + (Y - area.y) * (H - TOP) / area.h
    sc = min(area.w / W, area.h / (H - TOP))
    cw, ch = W * sc, (H - TOP) * sc
    x0 = area.centerx - cw / 2
    y0 = area.y if how == "top" else area.centery - ch / 2
    return (X - x0) / sc, TOP + (Y - y0) / sc





def load_fonts():
    pygame.font.init()
    mono = pygame.font.match_font("dejavusansmono") or pygame.font.match_font("monospace")
    F.update(big=pygame.font.Font(None, 30), btn=pygame.font.Font(None, 24), small=pygame.font.Font(None, 18),
             num=pygame.font.Font(None, 48), mono=pygame.font.Font(mono, 11), clock=pygame.font.Font(None, 110),
             tiny=pygame.font.Font(None, 15))

def main():
    T0 = time.time()
    load_cfg()
    ev_migrate()
    make_sounds()
    play_inicio()
    load_fonts()
    surf = pygame.Surface((W, H))
    dev, bpp, stride = find_fb()
    SMALL["null"] = dev == "/dev/null"
    print("Framebuffer", dev, bpp, "bpp")
    print(f"Panel {PANEL_VER.split(' · ')[0]} listo en {time.time() - T0:.1f} s")
    if cfg.get("stream"):
        stream_start()
    threading.Thread(target=udp_loop, daemon=True).start()
    threading.Thread(target=touch_loop, daemon=True).start()
    threading.Thread(target=touch_loop2, daemon=True).start()
    threading.Thread(target=mouse_loop, daemon=True).start()
    threading.Thread(target=obs_loop, daemon=True).start()
    last = None
    with open(dev, 'r+b', buffering=0) as fb:
        while True:
            if ui.get("bye"):
                draw_bye(surf)
            else:
                render(surf)
                decorate(surf)
                if not SMALL.get("null"):
                    draw_borders(surf)
                rhino_banner(surf)
            draw_pointer(surf)
            PANEL_SURF[0] = surf
            BIG["n"] += 1
            if big_go(surf):
                big_frame()
                stream_snap(surf)
            data = to_fb_bytes(surf, bpp, stride)
            if data != last:
                fb.seek(0); fb.write(data); last = data
            TAP_EV.wait(0.1); TAP_EV.clear()

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







# --- tick del BGS ---
EV_LIST.append(("bgstick", "TICK DEL BGS"))
BGT = {"last": None}




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




# ---------- v1.0 beta 4 ----------
def tw_(font, text):                                    # v1.0b6b: FontProxy ya mide en pixeles del panel
    return font.size(str(text))[0]

def put_fit(surf, names, text, pos, col, maxw, anchor="topleft"):
    """La letra mas grande de la lista con la que el texto cabe entero."""
    for n in names:
        if tw_(F[n], text) <= maxw:
            return put(surf, F[n], text, pos, col, anchor=anchor)
    return put(surf, F[names[-1]], text, pos, col, maxw, anchor=anchor)

def put_wrap(surf, text, pos, col, maxw, maxlines=2):
    """Texto en F['btn'] partido en lineas (si no cabe en maxlines, en F['small']). Devuelve el alto usado."""
    for f_, lh in ((F["btn"], 24), (F["small"], 17)):
        L = wrap_lines(f_, str(text), maxw)
        if len(L) <= maxlines or f_ is F["small"]:
            x, y = pos
            for t in L[:maxlines]:
                put(surf, f_, t, (x, y), col, maxw, anchor="midtop")
                y += lh
            return lh * min(len(L), maxlines)

# --- pestanas de combate ---
TABS.append([(6, "COMBATE"), (191, "COMBATE + CAZA"), (9, "CAZA")])

# --- VIAJES con zoom ---
VJT = {}


def view_viajes_base(surf, d, flags, now):
    V = (d or {}).get("viajes") or {}
    per = ui.get("vjp", "30"); zm = ui.get("vjz", "zona"); Z = ui.get("vjzoom")
    for i, (k, lab) in enumerate(VJ_PER):
        draw_button(surf, vj_btn(i), lab, "", F["small"], filled=k == per, compact=True)
    draw_button(surf, vj_btn(4), "GALAXIA" if zm == "gal" else "ZONA", "", F["small"], compact=True)
    draw_button(surf, vj_btn(5), f"−  x{Z[0]}" if Z else "−", "", F["small"], compact=True, dim=not Z)
    D = V.get(per)
    M = pygame.Rect(4, TOP + 2, W - 8, H - TOP - 34)
    pygame.draw.rect(surf, DIM, M, 1, border_radius=4)
    if not D or not D.get("n"):
        put(surf, F["btn"], "sin saltos en este periodo" if V else "esperando datos del sender", M.center, DIM, anchor="center")
        return
    nodes, edges, cur = D["n"], D["e"], D.get("cur")
    A = M.inflate(-30, -36).move(0, -2)
    pt0, sc0 = _vj_view(nodes, cur, zm, A)
    if Z:
        f_, wx, wz = Z
        sc = sc0 * f_
        pt = lambda x, z: (A.centerx + (x - wx) * sc, A.centery - (z - wz) * sc)
    else:
        pt, sc = pt0, sc0
    VJT.update(A=A, pt=pt, sc=sc)
    old_clip = surf.get_clip(); surf.set_clip(M)
    if zm == "gal":
        c = pt(*GAL_C)
        pygame.draw.circle(surf, (45, 30, 10), (int(c[0]), int(c[1])), max(2, min(4000, int(45000 * sc))), 1)
        pygame.draw.circle(surf, (70, 45, 15), (int(c[0]), int(c[1])), max(2, min(2000, int(4000 * sc))))
    P_ = [pt(n[1], n[2]) for n in nodes]
    mx = max([e[2] for e in edges] or [1])
    outs = []
    for i, j, c, h in sorted(edges, key=lambda e: e[2]):
        a, b = P_[i], P_[j]
        w = 1 + round(4 * (c - 1) / max(1, mx - 1))
        cl = M.clipline(a, b)
        if not cl:
            continue
        pygame.draw.line(surf, ORANGE if c > 1 else (150, 80, 0), cl[0], cl[1], w)
        ina, inb = M.collidepoint(a), M.collidepoint(b)
        if ina != inb:
            outs.append((nodes[j], cl[1], h) if ina else (nodes[i], cl[0], h))
        elif h >= 5 and math.dist(a, b) > 70:
            put(surf, F["small"], f"{h} saltos", ((a[0] + b[0]) / 2 + 4, (a[1] + b[1]) / 2 - 14), DIM)
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
                put(surf, F["small"], txt, r.topleft, col); return
    ci = next((k for k, n in enumerate(nodes) if n[0] and n[0] == cur), None)
    if ci is not None and M.collidepoint(P_[ci]):
        x, y = P_[ci]
        pygame.draw.circle(surf, BLUE, (int(x), int(y)), 7 if int(now * 2) % 2 else 9, 2)
        label(cur.upper()[:20], x, y, BLUE)
    nlab = 6 if not Z else 16                            # con zoom caben mas nombres
    for k in sorted(range(len(nodes)), key=lambda k: -nodes[k][3])[:nlab]:
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
    st_ = f"{D['j']} SALTOS · {D['ly']:,} al · {D['s']} SISTEMAS".replace(",", ".") + ("" if Z else "  ·  toca para ampliar")
    r_ = pygame.Rect(M.x + 3, M.bottom - 17, tw_(F["small"], st_) + 8, 15)
    pygame.draw.rect(surf, BLACK, r_)
    put(surf, F["small"], st_, (r_.x + 4, r_.y + 1), DIM)

VIEWS[190] = view_viajes_base

# --- tick del BGS por sistema (EDCAS) ---
ETA = {"key": None}

def _hm(sec):
    sec = max(0, int(sec))
    return f"{sec // 3600} h {sec % 3600 // 60:02d} min"

def bgs_lines(d, now):
    out = []
    E = (d or {}).get("etick") or {}
    pn = pc_now(d, now)
    if E.get("next") and E.get("sys") == (d or {}).get("system"):
        w = (E.get("win") or 0) * 60
        if pn < E["next"] - w:
            out.append((f"PRÓXIMO TICK en {_hm(E['next'] - w - pn)} (± {E.get('win')} min) · datos: EDCAS", BLUE))
        elif pn < E["next"] + w:
            out.append((f"TICK EN CURSO · la ventana acaba en {_hm(E['next'] + w - pn)} · datos: EDCAS", GREEN))
        else:
            out.append(("tick previsto ya pasado · esperando datos nuevos de EDCAS", DIM))
        if E.get("last"):
            out.append((f"ÚLTIMO TICK {time.strftime('%d/%m %H:%M', time.localtime(E['last']))} (hace {_hm(pn - E['last'])})", DIM))
    else:
        tk = (d or {}).get("tick")
        if tk:
            out.append((f"ÚLTIMO TICK (general) hace {_hm(pn - tk)} ({time.strftime('%H:%M', time.localtime(tk))})", BLUE))
    b = (d or {}).get("bgsv") or {}
    if b.get("prev"):
        days = (pn - b["prev"]) / 86400
        cuando = "hoy" if days < 1 else f"hace {days:.0f} día{'s' if days >= 1.5 else ''}"
        out.append(("BGS ACTUALIZADO desde tu última visita (" + cuando + ")" if b.get("chg") else
                    "BGS sin cambios desde tu última visita (" + cuando + ")", GREEN if b.get("chg") else DIM))
    return out

def tick_graph(surf, d, r):
    """Hora del tick (UTC) de los ultimos dias en este sistema."""
    E = (d or {}).get("etick") or {}
    H_ = E.get("hist") or []
    if len(H_) < 2 or E.get("sys") != (d or {}).get("system"):
        return False
    pygame.draw.rect(surf, BLACK, r); pygame.draw.rect(surf, DIM, r, 1, border_radius=3)
    pts = []
    for k, t in enumerate(H_):
        g = time.gmtime(t); hh = g.tm_hour + g.tm_min / 60
        pts.append((r.x + 4 + k * (r.w - 8) / max(1, len(H_) - 1), r.bottom - 4 - hh / 24 * (r.h - 8)))
    pygame.draw.lines(surf, ORANGE, False, pts, 1)
    for p_ in pts:
        pygame.draw.circle(surf, ORANGE, (int(p_[0]), int(p_[1])), 2)
    put(surf, F["small"], "hora del tick (UTC)", (r.x, r.y - 14), DIM)
    return True

_view_pol_b4 = view_pol_base

def view_pol(surf, d, flags, now):
    _view_pol_b4(surf, d, flags, now)
    L = bgs_lines(d, now)
    g = tick_graph(surf, d, pygame.Rect(W - 128, H - 8 - 15 * max(1, len(L)) - 40, 122, 36)) if L else False
    y = H - 4 - 15 * len(L)
    if L:
        pygame.draw.rect(surf, BLACK, (0, y - 2, W, H - y + 2))
    for txt, col in L:
        put(surf, F["small"], txt, (8, y), col, W - 16); y += 15

def etick_watch(d, now):
    E = (d or {}).get("etick") or {}
    if not E.get("next") or E.get("sys") != (d or {}).get("system"):
        return
    w = (E.get("win") or 0) * 60
    pn = pc_now(d, now)
    key = (E["sys"], E["next"])
    if E["next"] - w <= pn < E["next"] + w and ETA["key"] != key and ev_on("bgstick"):
        ETA["key"] = key
        k0 = XA_K[0]
        try:
            XA_K[0] = "bgstick"
            set_alert("TICK DEL BGS", f"empieza la ventana en {E['sys']} (± {E.get('win')} min)", BLUE, 6)
            play("ok")
        finally:
            XA_K[0] = k0

# --- MI FACCION (datos de GitHub) ---
FAC_URL = "https://raw.githubusercontent.com/ortemedder/cdsn-datos/main/faccion.json"
FAC_CACHE = os.path.join(PANEL_DIR, "faccion_cache.json")
FACD = {"data": None, "t": 0, "err": ""}
ES_ST = {"Expansion": "Expansión", "War": "Guerra", "CivilWar": "Guerra civil", "Election": "Elecciones", "Retreat": "Retirada",
         "Boom": "Auge", "Bust": "Crisis", "Famine": "Hambruna", "Outbreak": "Epidemia", "Lockdown": "Confinamiento",
         "CivilUnrest": "Disturbios", "PirateAttack": "Ataque pirata", "Drought": "Sequía", "Blight": "Plaga",
         "InfrastructureFailure": "Fallo infraestr.", "NaturalDisaster": "Desastre", "TerroristAttack": "Atentado",
         "CivilLiberty": "Libertad civil", "Investment": "Inversión", "PublicHoliday": "Festividad"}

def fac_loop():
    try:
        with open(FAC_CACHE, encoding="utf-8") as f:
            FACD.update(data=json.load(f))
    except (OSError, ValueError):
        pass
    url = FAC_URL
    try:
        u_ = open(os.path.join(PANEL_DIR, "faccion_url.txt")).read().strip()
        url = u_ or url
    except OSError:
        pass
    while True:
        try:
            import urllib.request
            req = urllib.request.Request(url + "?t=" + str(int(time.time() // 300)), headers={"User-Agent": "PanelEliteRPi/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                j = json.loads(r.read().decode("utf-8"))
            FACD.update(data=j, t=time.time(), err="")
            with open(FAC_CACHE + ".tmp", "w", encoding="utf-8") as f:
                json.dump(j, f)
            os.replace(FAC_CACHE + ".tmp", FAC_CACHE)
        except Exception as e:
            FACD["err"] = str(e)[:60]
        time.sleep(600)

threading.Thread(target=fac_loop, daemon=True, name="faccion").start()



FAC_PER = 6
MENU[192] = MENU[193] = "MI FACCIÓN"
PARENT[192] = PARENT[193] = 0
TABS[3].append((192, "FACCIÓN"))
TABS.append([(165, "ESCUADRÓN"), (193, "FACCIÓN")])

def view_fac_base(surf, d, flags, now):
    D, S, gap = fac_rows()
    y = TOP + 3
    if not S:
        put(surf, F["btn"], "sin datos de la facción", (W // 2, H // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], FACD["err"] or "descargando…", (W // 2, H // 2 + 14), DIM, W - 16, anchor="center")
        return
    pages = (len(S) + FAC_PER - 1) // FAC_PER
    pg = ui.get("facpg", 0) % pages
    put(surf, F["btn"], (D.get("faccion") or "").upper(), (8, y), ORANGE, 230)
    put(surf, F["small"], f"{sum(1 for v in S if v.get('ctrl'))} controlados · {len(S)} sistemas", (W - 8, y + 4), DIM, anchor="topright")
    y += 22
    for v in S[pg * FAC_PER:(pg + 1) * FAC_PER]:
        g = gap(v)
        pygame.draw.line(surf, (40, 28, 10), (6, y - 1), (W - 6, y - 1))
        col = ORANGE if v.get("ctrl") else WHITE
        if v.get("ctrl"):
            pygame.draw.polygon(surf, ORANGE, [(8, y + 4), (14, y + 4), (11, y + 9)])
        put(surf, F["small"], v["sys"].upper(), (18, y + 1), col, 170)
        st = fac_states(v)
        put(surf, F["small"], ", ".join(st) or "sin estados", (18, y + 15), RED if v.get("conflictos") or "Retreat" in " ".join(st) else BLUE if st else DIM, 170)
        bx = pygame.Rect(194, y + 5, 110, 12); pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, ORANGE if v.get("ctrl") else (170, 170, 170), (bx.x + 1, bx.y + 1, int((bx.w - 2) * min(100, v["inf"]) / 100), bx.h - 2))
        tx = bx.x + int(bx.w * min(100, v.get("segunda_inf") or 0) / 100); pygame.draw.line(surf, RED, (tx, bx.y - 2), (tx, bx.bottom + 1), 2)
        put(surf, F["btn"], f"{v['inf']:.1f}%".replace(".", ","), (310, y + 2), col)
        if v.get("prev") is not None and abs(v["inf"] - v["prev"]) >= 0.1:
            tr = v["inf"] - v["prev"]; c_ = GREEN if tr > 0 else RED; x_, y_ = 312, y + 21
            pygame.draw.polygon(surf, c_, [(x_, y_ + 5), (x_ + 8, y_ + 5), (x_ + 4, y_)] if tr > 0 else [(x_, y_), (x_ + 8, y_), (x_ + 4, y_ + 5)])
            put(surf, F["small"], f"{abs(tr):.1f}".replace(".", ","), (x_ + 11, y_ - 3), c_)
        put(surf, F["btn"], (f"+{g:.1f}" if g >= 0 else f"{g:.1f}").replace(".", ","), (W - 60, y + 2),
            GREEN if g >= 5 else ORANGE if g >= 0 else DIM, anchor="topright")
        age = (time.time() - (v.get("t") or 0)) / 3600
        put(surf, F["small"], f"{age:.0f} h" if age < 48 else f"{age / 24:.0f} d", (W - 8, y + 5), DIM, anchor="topright")
        y += 32
    put(surf, F["small"], (f"pág {pg + 1}/{pages} · toca para pasar  ·  " if pages > 1 else "") + "raya roja = 2ª facción · +N = ventaja",
        (8, H - 14), DIM, W - 16)

VIEWS[192] = VIEWS[193] = view_fac_base

def fac_summary(maxn=3):
    D, S, gap = fac_rows()
    if not S:
        return None, []
    head = f"{(D.get('faccion') or '').upper()} · {sum(1 for v in S if v.get('ctrl'))} controlados · {len(S)} sistemas"
    return head, S








# ---------- v1.0 beta 5 ----------
# --- menu: 9 = FACCION ---
_menu_b5 = VIEWS[0]

def flag_icon(surf, col, cx, cy):
    pygame.draw.line(surf, col, (cx - 12, cy - 16), (cx - 12, cy + 18), 3)
    pygame.draw.polygon(surf, col, [(cx - 11, cy - 16), (cx + 14, cy - 10), (cx - 11, cy - 2)])
    pygame.draw.circle(surf, col, (cx + 6, cy + 10), 6, 2)

def view_menu_b5(surf, d, flags, now):
    keep = MENU.get(9)
    MENU[9] = "FACCIÓN"
    try:
        _menu_b5(surf, d, flags, now)
    finally:
        MENU[9] = keep
    if ICONS_ON[0]:
        r = grid(8)
        draw_button(surf, r, "", None, F["small"], lit=flash.get((0, 8), 0) > now)
        flag_icon(surf, ORANGE, r.centerx, r.y + int(r.h * 0.38))
        put(surf, F["small"], "9 FACCIÓN", (r.centerx, r.bottom - 18), ORANGE, r.w - 8, anchor="midtop")

VIEWS[0] = view_menu_b5

# --- traducciones ---
def _clean(v):
    v = str(v or "")
    if v.startswith("$"):
        v = v.split("_", 1)[-1].rstrip(";")
        for p_ in ("SECURITY_", "security_"):
            v = v.replace(p_, "")
    return v

TR_ = {"high": "Alta", "medium": "Media", "low": "Baja", "anarchy": "Anarquía", "lawless": "Sin ley",
       "Industrial": "Industrial", "Extraction": "Extracción", "Refinery": "Refinería", "Agri": "Agrícola", "Agriculture": "Agrícola",
       "HighTech": "Alta tecnología", "High Tech": "Alta tecnología", "Military": "Militar", "Tourism": "Turismo",
       "Service": "Servicios", "Colony": "Colonia", "Terraforming": "Terraformación", "Prison": "Prisión", "None": "—",
       "Democracy": "Democracia", "Corporate": "Corporativo", "Dictatorship": "Dictadura", "Feudal": "Feudal",
       "Patronage": "Mecenazgo", "Communism": "Comunismo", "Cooperative": "Cooperativa", "Confederacy": "Confederación",
       "Theocracy": "Teocracia", "PrisonColony": "Colonia penal", "Prison colony": "Colonia penal", "Anarchy": "Anarquía",
       "Federation": "Federación", "Empire": "Imperio", "Alliance": "Alianza", "Independent": "Independiente",
       "Fortified": "Fortificado", "Stronghold": "Bastión", "Exploited": "Explotado", "Unoccupied": "Sin ocupar",
       "Contested": "En disputa", "Controlled": "Controlado", "InPrepareRadius": "En preparación", "Prepared": "Preparado"}

def tr_(v):
    c = _clean(v)
    return TR_.get(c, TR_.get(c.lower(), c))

def fnum_pob(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "?"
    return f"{n / 1e9:.1f} mil M".replace(".", ",") if n >= 1e9 else f"{n / 1e6:.1f} M".replace(".", ",") if n >= 1e6 else f"{n:,}".replace(",", ".")

def fac_age(t):
    if not t:
        return "sin fecha", DIM
    a = time.time() - t
    if a < 3600:
        txt = f"hace {int(a // 60)} min"
    elif a < 86400:
        txt = f"hace {a / 3600:.0f} h"
    else:
        txt = f"hace {a / 86400:.0f} d"
    return txt, (MERC if a < 86400 else ORANGE)

# --- pantalla de espera: titulo bien tapado y letra pequena ---
def idle_crawl(surf, now, box=None, waiting=True):
    idle_crawl_base(surf, now, box, waiting)
    head, S = fac_summary()
    if not S or int(now // 20) % 2 == 0:
        return
    box = box or IDLE_BOX
    badge = tw_(F["small"], "ESPERANDO A ELITE DANGEROUS") + 30
    cover = pygame.Rect(box.x + 4, box.y + 2, box.w - 8 - badge, 18)
    pygame.draw.rect(surf, BLACK, cover)
    D = FACD["data"] or {}
    tmax = max([v.get("t") or 0 for v in S] or [0])
    a_txt, a_col = fac_age(tmax)
    nctl = sum(1 for v in S if v.get("ctrl"))
    x = put(surf, F["tiny"], (D.get("faccion") or "").upper(), (box.x + 8, box.y + 6), ORANGE)
    put(surf, F["tiny"], f" · {nctl} contr. · {a_txt}", (box.x + 8 + x, box.y + 6), a_col, max(20, cover.w - x - 8))
    area = pygame.Rect(box.x + 8, box.y + 24, box.w - 16, box.h - 28)
    pygame.draw.rect(surf, BLACK, area)
    D, S, gap = fac_rows()
    y = area.y + 1
    for v in S:
        if y + 14 > area.bottom:
            break
        g = gap(v)
        alarm = v.get("ctrl") and (g < 5 or v.get("conflictos") or "Retreat" in (v.get("pendientes") or []) + (v.get("activos") or []))
        col = RED if alarm else ORANGE if v.get("ctrl") else WHITE
        put(surf, F["tiny"], ("» " if v.get("ctrl") else "   ") + v["sys"].upper(), (area.x, y), col, area.w * 0.40)
        put(surf, F["tiny"], f"{v['inf']:.1f} %  ({'+' if g >= 0 else ''}{g:.1f})".replace(".", ","), (area.x + area.w * 0.41, y), col)
        put(surf, F["tiny"], ", ".join(fac_states(v)), (area.x + area.w * 0.60, y), RED if alarm else BLUE, area.w * 0.40)
        y += 14

# --- FACCION: hora de actualizacion, filas que se tocan y paginas ---
FROWS = []
MENU[194] = "SISTEMA DE LA FACCIÓN"
PARENT[194] = 192

def fac_pg_btn(k):
    return pygame.Rect(W - 96 + k * 46, H - 26, 42, 23)

def view_fac_2(surf, d, flags, now):
    FROWS.clear()
    D, S, gap = fac_rows()
    y = TOP + 3
    if not S:
        put(surf, F["btn"], "sin datos de la facción", (W // 2, H // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], FACD["err"] or "descargando…", (W // 2, H // 2 + 14), DIM, W - 16, anchor="center")
        return
    pages = (len(S) + FAC_PER - 1) // FAC_PER
    pg = ui.get("facpg", 0) % pages
    x = put(surf, F["btn"], (D.get("faccion") or "").upper(), (8, y), ORANGE, 210)
    a_txt, a_col = fac_age(max([v.get("t") or 0 for v in S] or [0]))
    tmax = max([v.get("t") or 0 for v in S] or [0])
    put(surf, F["small"], f"act. {time.strftime('%H:%M', time.localtime(tmax))} ({a_txt})" if tmax else "sin fecha",
        (8 + x + 10, y + 4), a_col, W - x - 120)
    put(surf, F["small"], f"{sum(1 for v in S if v.get('ctrl'))} contr. · {len(S)} sist.", (W - 8, y + 4), DIM, anchor="topright")
    y += 22
    for v in S[pg * FAC_PER:(pg + 1) * FAC_PER]:
        FROWS.append((pygame.Rect(0, y - 1, W, 32), v["sys"]))
        g = gap(v)
        pygame.draw.line(surf, (40, 28, 10), (6, y - 1), (W - 6, y - 1))
        col = ORANGE if v.get("ctrl") else WHITE
        if v.get("ctrl"):
            pygame.draw.polygon(surf, ORANGE, [(8, y + 4), (14, y + 4), (11, y + 9)])
        put(surf, F["small"], v["sys"].upper(), (18, y + 1), col, 170)
        st = fac_states(v)
        put(surf, F["small"], ", ".join(st) or "sin estados", (18, y + 15),
            RED if v.get("conflictos") or "Retreat" in " ".join(st) else BLUE if st else DIM, 170)
        bx = pygame.Rect(194, y + 5, 110, 12); pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, ORANGE if v.get("ctrl") else (170, 170, 170), (bx.x + 1, bx.y + 1, int((bx.w - 2) * min(100, v["inf"]) / 100), bx.h - 2))
        tx = bx.x + int(bx.w * min(100, v.get("segunda_inf") or 0) / 100); pygame.draw.line(surf, RED, (tx, bx.y - 2), (tx, bx.bottom + 1), 2)
        put(surf, F["btn"], f"{v['inf']:.1f}%".replace(".", ","), (310, y + 2), col)
        if v.get("prev") is not None and abs(v["inf"] - v["prev"]) >= 0.1:
            tr = v["inf"] - v["prev"]; c_ = GREEN if tr > 0 else RED; x_, y_ = 312, y + 21
            pygame.draw.polygon(surf, c_, [(x_, y_ + 5), (x_ + 8, y_ + 5), (x_ + 4, y_)] if tr > 0 else [(x_, y_), (x_ + 8, y_), (x_ + 4, y_ + 5)])
            put(surf, F["small"], f"{abs(tr):.1f}".replace(".", ","), (x_ + 11, y_ - 3), c_)
        put(surf, F["btn"], (f"+{g:.1f}" if g >= 0 else f"{g:.1f}").replace(".", ","), (W - 60, y + 2),
            GREEN if g >= 5 else ORANGE if g >= 0 else DIM, anchor="topright")
        put(surf, F["small"], fac_age(v.get("t"))[0].replace("hace ", ""), (W - 8, y + 5), DIM, anchor="topright")
        y += 32
    put(surf, F["small"], (f"pág {pg + 1}/{pages} · " if pages > 1 else "") + "toca un sistema para ver su ficha",
        (8, H - 20), DIM, W - 110)
    if pages > 1:
        for k, t in enumerate(("<", ">")):
            draw_button(surf, fac_pg_btn(k), t, "", F["btn"], compact=True)

VIEWS[192] = VIEWS[193] = view_fac_2

def view_facsys(surf, d, flags, now):
    D = FACD["data"] or {}
    name = ui.get("facsys")
    v = (D.get("sistemas") or {}).get(name)
    if not v:
        put(surf, F["btn"], "sin datos de este sistema", (W // 2, H // 2), DIM, anchor="center"); return
    me = D.get("faccion")
    y = TOP + 3
    put(surf, F["btn"], name.upper(), (8, y), ORANGE, 260)
    pos, here = v.get("pos"), (d or {}).get("starpos")
    if pos and here and None not in pos:
        dist = math.dist(pos, here)
        put(surf, F["btn"], "AQUÍ" if dist < 0.01 else f"a {dist:,.1f} al".replace(",", "X").replace(".", ",").replace("X", "."),
            (W - 8, y), BLUE, anchor="topright")
    y += 21
    a_txt, a_col = fac_age(v.get("t"))
    put(surf, F["small"], f"datos {a_txt} · {v.get('src') or '?'}", (8, y), a_col)
    S_ = v.get("sis") or {}
    if S_:
        put(surf, F["small"], f"POBLACIÓN {fnum_pob(S_.get('pob'))}", (W - 8, y), DIM, anchor="topright")
    y += 16
    put(surf, F["small"], "CONTROLA", (8, y + 2), DIM)
    put(surf, F["btn"], v.get("ctrl_n") or ("tu facción" if v.get("ctrl") else "?"), (88, y - 1), ORANGE if v.get("ctrl") else WHITE, W - 96)
    y += 21
    if S_:
        eco = tr_(S_.get("eco")) + (f" / {tr_(S_.get('eco2'))}" if S_.get("eco2") and tr_(S_.get("eco2")) != "—" else "")
        put(surf, F["small"], f"SEGURIDAD {tr_(S_.get('seg'))}  ·  ECONOMÍA {eco}  ·  {tr_(S_.get('gov'))}, {tr_(S_.get('alg'))}",
            (8, y), WHITE, W - 16)
        y += 16
    pp = v.get("pp") or {}
    if pp.get("pot"):
        put(surf, F["small"], "POWERPLAY", (8, y + 1), DIM)
        x = 86 + put(surf, F["small"], f"{pp['pot']} · {tr_(pp.get('est'))}", (86, y + 1), BLUE, 240)
        if pp.get("prog") is not None:
            bx = pygame.Rect(x + 8, y + 3, 90, 10); pygame.draw.rect(surf, DIM, bx, 1)
            pr = max(0.0, min(1.0, float(pp["prog"])))
            pygame.draw.rect(surf, BLUE, (bx.x + 1, bx.y + 1, int((bx.w - 2) * pr), bx.h - 2))
            put(surf, F["small"], f"{pr * 100:.0f} %", (bx.right + 4, y + 1), BLUE)
        y += 16
    elif pp.get("pots"):
        put(surf, F["small"], "POWERPLAY  en disputa: " + ", ".join(pp["pots"]), (8, y + 1), BLUE, W - 16); y += 16
    elif pp:
        put(surf, F["small"], "POWERPLAY  sin potencia", (8, y + 1), DIM); y += 16
    pygame.draw.line(surf, DIM, (6, y + 1), (W - 6, y + 1)); y += 4
    T = sorted(v.get("todas") or [], key=lambda f: -(f.get("inf") or 0))
    if not T:
        put(surf, F["small"], "las demás facciones llegarán con el próximo dato de este sistema", (8, y + 4), DIM, W - 16)
    for f in T:
        if y + 15 > H - 30:
            put(surf, F["tiny"], f"… y {len(T) - T.index(f)} más", (8, y), DIM); break
        mine = f.get("n") == me
        col = ORANGE if mine else WHITE
        ctl = f.get("n") == v.get("ctrl_n")
        put(surf, F["tiny"], ("» " if ctl else "   ") + (f.get("n") or "?"), (8, y), col, 170)
        bx = pygame.Rect(182, y + 2, 80, 9); pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, ORANGE if mine else (150, 150, 150), (bx.x + 1, bx.y + 1, int((bx.w - 2) * min(100, f.get("inf") or 0) / 100), bx.h - 2))
        put(surf, F["tiny"], f"{f.get('inf') or 0:.1f}%".replace(".", ","), (268, y), col)
        st = [ES_ST.get(a, a) for a in f.get("act") or []] + [ES_ST.get(a, a) + " (p)" for a in f.get("pend") or []]
        put(surf, F["tiny"], ", ".join(st) or tr_(f.get("gov")), (312, y), BLUE if st else DIM, W - 318)
        y += 14
    for c in v.get("conflictos") or []:
        put(surf, F["small"], f"{'ELECCIONES' if (c.get('tipo') or '').lower() == 'election' else 'GUERRA'} contra {c.get('contra')}: "
                              f"{c.get('ganados') or 0}-{c.get('perdidos') or 0} días", (8, H - 44), RED, W - 110)
    draw_button(surf, pygame.Rect(4, H - 26, 90, 23), "< VOLVER", "", F["small"], compact=True)

VIEWS[194] = view_facsys




