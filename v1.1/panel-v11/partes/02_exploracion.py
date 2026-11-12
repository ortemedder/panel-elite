# Panel Elite v1.1 · parte 02: exploracion (lineas 726-1803 del panel entero)
# ---------- 7 exploracion ----------
def view_explo_base(surf, d, flags, now):
    ex = (d or {}).get("explo") or {}
    y = TOP + 6
    total, scanned = ex.get("total"), ex.get("scanned", 0)
    put(surf, F["small"], "CUERPOS ESCANEADOS", (8, y), DIM)
    put(surf, F["small"], "MAPEADOS", (W - 8, y), DIM, anchor="topright")
    if ex.get("edsm_n"):
        put(surf, F["small"], f"EDSM: {ex['edsm_n']} cuerpos", (150, y), BLUE)
    elif ex.get("edsm_st") == "bloqueado":
        put(surf, F["small"], "EDSM bloqueado", (165, y), RED)
    elif ex.get("edsm_st") == "error":
        put(surf, F["small"], "EDSM sin respuesta", (165, y), ORANGE)
    y += 14
    done = total is not None and scanned >= total
    put(surf, F["big"], f"{scanned} / {total if total is not None else '?'}", (8, y), GREEN if done else ORANGE)
    put(surf, F["big"], str(ex.get("mapped", 0)), (W - 8, y), ORANGE, anchor="topright")
    fss = ex.get("fss")
    bx = pygame.Rect(150, y + 6, 200, 14)
    pygame.draw.rect(surf, DIM, bx, 1)
    if fss is not None:
        pygame.draw.rect(surf, BLUE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * fss), bx.h - 4))
        put(surf, F["small"], f"FSS {fss * 100:.0f}%", (bx.centerx, bx.y + 1), WHITE, anchor="midtop")
    else:
        put(surf, F["small"], "SIN ESCANEO FSS", (bx.centerx, bx.y + 1), DIM, anchor="midtop")
    y += 30
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
    top = ex.get("top") or []
    sysname = ex.get("system") or ""
    if not top:
        msg = {"consultando": "Consultando EDSM...", "bloqueado": "EDSM bloqueado (¿fútbol?) · reintento cada 10 min"}.get(
            ex.get("edsm_st"), "Nada destacable escaneado aún")
        put(surf, F["btn"], msg, (W // 2, y + 60), DIM, anchor="center")
    per = 7
    pages = max(1, (len(top) + per - 1) // per)
    pg = ui.get("page71", 0) % pages
    if pages > 1:
        put(surf, F["small"], f"pág {pg + 1}/{pages}  (toca para pasar)", (W // 2, H - 34), DIM, anchor="center")
    for row in top[pg * per:(pg + 1) * per]:
        name, cls, dist, first, mapped, val = row[:6]
        src = row[6] if len(row) > 6 else None
        short = name[len(sysname):].strip() if name.startswith(sysname) else name
        put(surf, F["btn"], short or name, (8, y), ORANGE, 70)
        put(surf, F["small"], cls, (80, y + 4), ORANGE, 150)
        put(surf, F["small"], f"{dist:,} ls".replace(",", "."), (300, y + 4), DIM, anchor="topright")
        if src == "edsm":
            put(surf, F["small"], "EDSM", (342, y + 4), BLUE)
        else:
            put(surf, F["small"], "1º" if first else "", (318, y + 4), GREEN)
            put(surf, F["small"], "MAPEADO" if mapped else "SIN MAPEAR", (342, y + 4), BLUE if mapped else DIM)
        put(surf, F["small"], cr(val), (W - 8, y + 4), ORANGE, anchor="topright")
        y += 21
    pygame.draw.line(surf, DIM, (8, H - 24), (W - 8, H - 24))
    put(surf, F["btn"], f"DATOS SIN VENDER  ~ {cr(ex.get('unsold'))} cr", (8, H - 20), ORANGE)
    put(surf, F["small"], f"{ex.get('unsold_n', 0)} cuerpos", (W - 8, H - 16), DIM, anchor="topright")

# ---------- 8 estacion ----------
STARPORTS = {"Coriolis", "Orbis", "Ocellus", "Bernal", "AsteroidBase", "Dodec"}
ST_TYPE = {"Coriolis": "Estación Coriolis", "Orbis": "Estación Orbis", "Ocellus": "Estación Ocellus",
           "Bernal": "Estación Ocellus", "AsteroidBase": "Base asteroide", "Outpost": "Puesto avanzado",
           "FleetCarrier": "Portanaves", "CraterOutpost": "Puesto planetario", "CraterPort": "Puerto planetario",
           "OnFootSettlement": "Asentamiento", "Dodec": "Estación Dodec", "MegaShip": "Mega nave"}
SERVICES = [("refuel", "COMBUSTIBLE"), ("repair", "REPARAR"), ("rearm", "REARMAR"), ("commodities", "MERCADO"),
            ("shipyard", "ASTILLERO"), ("outfitting", "EQUIPAMIENTO"), ("blackmarket", "MERCADO NEGRO"),
            ("facilitator", "FACTORES INT."), ("materialtrader", "MATERIALES"), ("techBroker", "TECNOLOGÍA"),
            ("engineer", "INGENIERO"), ("vistagenomics", "VISTA GENOMICS"), ("searchrescue", "RESCATE"),
            ("missions", "MISIONES"), ("tuning", "PERSONALIZAR")]
STATUS_COL = {"CONCEDIDO": GREEN, "ATRACADO": BLUE, "DENEGADO": RED, "SOLICITADO": ORANGE}

# 45 plataformas en 3 bloques de 15; cada bloque ocupa 4 horas. (sector dentro del bloque, profundidad)
PAD_GRP = [(0, 0), (0, 0), (0, 2), (0, 2), (1, 0), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2),
           (3, 0), (3, 0), (3, 1), (3, 2), (3, 2)]
PAD_DEPTH = ["ENTRADA", "MEDIO", "FONDO"]

def pad_pos(pad):
    """(hora 1-12, profundidad 0 entrada / 1 medio / 2 fondo), mirando desde la ranura de entrada."""
    p = (int(pad) - 1) % 45
    sct, dep = PAD_GRP[p % 15]
    sct += (p // 15) * 4
    return (6 + sct) % 12 or 12, dep

def pad_clock(pad):
    return pad_pos(pad)[0]

def view_station(surf, d, flags, now):
    st = (d or {}).get("station") or {}
    if not st.get("status"):
        put(surf, F["big"], "Sin solicitud de atraque", (W // 2, (H + TOP) // 2), DIM, anchor="center")
        return
    pad, stype = st.get("pad"), st.get("type")
    carrier_bg(surf, d or {}, st)
    cx, cy, rad = 118, (H + TOP) // 2 + 4, 108
    x0 = 248
    if pad and stype in STARPORTS:
        import math
        hour, dep = pad_pos(pad)
        RR = (rad, rad * 0.75, rad * 0.54, rad * 0.34)
        for h in range(12):
            a0, a1 = math.radians(h * 30 - 105), math.radians(h * 30 - 75)
            angs = [a0 + (a1 - a0) * t / 6 for t in range(7)]
            for k in range(3):
                ro, ri = RR[k], RR[k + 1]
                pts = [(cx + ro * math.cos(a), cy + ro * math.sin(a)) for a in angs] + \
                      [(cx + ri * math.cos(a), cy + ri * math.sin(a)) for a in reversed(angs)]
                on = (h or 12) == hour and k == dep
                pygame.draw.polygon(surf, ORANGE if on else BLACK, pts)
                pygame.draw.polygon(surf, DIM, pts, 1)
        k_ = 0.6 + 0.4 * math.sin(now * 3)
        arc = pygame.Rect(cx - rad - 7, cy - rad - 7, 2 * rad + 14, 2 * rad + 14)
        pygame.draw.arc(surf, tuple(int(c * k_) for c in RED[:3]), arc, math.radians(145), math.radians(215), 7)
        pygame.draw.arc(surf, tuple(int(c * k_) for c in GREEN[:3]), arc, math.radians(-35), math.radians(35), 7)
        pygame.draw.rect(surf, BLACK, (cx - 30, cy - 9, 60, 18))
        pygame.draw.rect(surf, WHITE, (cx - 30, cy - 9, 60, 18), 2)
        put(surf, F["small"], "ENTRADA", (cx, cy), WHITE, anchor="center")
        pygame.draw.circle(surf, RED, (cx - 40, cy), 6)
        pygame.draw.circle(surf, GREEN, (cx + 40, cy), 6)
        put(surf, F["small"], "12", (cx, cy - rad - 1), DIM, anchor="midbottom")
        put(surf, F["small"], "6", (cx, cy + rad + 1), DIM, anchor="midtop")
    elif pad:
        put(surf, F["num"], str(pad), (cx, cy), ORANGE, anchor="center")
        put(surf, F["small"], "PLATAFORMA", (cx, cy - 34), DIM, anchor="center")
    else:
        x0 = 8
    y = TOP + 6
    put(surf, F["big"], (st.get("name") or "?").upper(), (x0, y), ORANGE, W - x0 - 8); y += 26
    put(surf, F["small"], ST_TYPE.get(stype, stype or ""), (x0, y), DIM, W - x0 - 8); y += 18
    status = st.get("status")
    put(surf, F["btn"], status, (x0, y), STATUS_COL.get(status, DIM)); y += 22
    if status == "DENEGADO" and st.get("reason"):
        put(surf, F["small"], st["reason"], (x0, y), RED, W - x0 - 8); y += 16
    if pad:
        put(surf, F["big"], f"PLATAFORMA {pad}", (x0, y), WHITE); y += 26
        if stype in STARPORTS:
            h_, d_ = pad_pos(pad)
            put(surf, F["btn"], f"a las {h_}  ·  {PAD_DEPTH[d_]}", (x0, y), ORANGE); y += 22
    if st.get("dist"):
        put(surf, F["small"], f"{st['dist']:,.0f} ls de la estrella".replace(",", "."), (x0, y), DIM); y += 16
    if st.get("faction"):
        put(surf, F["small"], st["faction"], (x0, y), DIM, W - x0 - 8); y += 18
    srv = set(st.get("services") or [])
    tags = [t for k, t in SERVICES if k in srv]
    tx = x0
    for t in tags:
        w_ = F["small"].size(t)[0] + 10
        if tx + w_ > W - 4:
            tx = x0; y += 18
        if y > H - 16: break
        pygame.draw.rect(surf, DIM, (tx, y, w_ - 4, 16), 1, border_radius=3)
        put(surf, F["small"], t, (tx + 3, y + 2), ORANGE)
        tx += w_

# ---------- 10 mineria ----------
def view_mining_base(surf, d, flags, now):
    m = (d or {}).get("mining") or {}
    last = m.get("last")
    y = TOP + 6
    if "rhino" in ((d or {}).get("srvtype") or "").lower():
        put(surf, F["small"], "BODEGA DEL RHINO", (8, y), DIM)
        put(surf, F["small"], "REFINADO (SESIÓN)", (318, y), DIM); y += 14
        yy = y
        inv, tot = (d or {}).get("srvinv") or [], (d or {}).get("srvcargo")
        put(surf, F["big"], f"{tot if tot is not None else '?'} t", (8, y), ORANGE); y += 30
        for name, n in inv[:8]:
            put(surf, F["small"], name, (8, y + 2), ORANGE, 220)
            put(surf, F["btn"], f"{n} t", (300, y), WHITE, anchor="topright"); y += 20
        if not inv:
            put(surf, F["small"], "vacía", (8, y), DIM)
        pygame.draw.line(surf, DIM, (310, yy - 14), (310, H - 30))
        ref = sorted((m.get("refined") or {}).items(), key=lambda kv: -kv[1])
        if not ref:
            put(surf, F["small"], "nada aún", (318, yy + 4), DIM)
        for name, n in ref[:8]:
            put(surf, F["small"], name, (318, yy + 2), ORANGE, 110)
            put(surf, F["btn"], f"{n}", (W - 8, yy), ORANGE, anchor="topright"); yy += 20
        pygame.draw.line(surf, DIM, (8, H - 26), (W - 8, H - 26))
        sf = ((d or {}).get("Fuel") or {}).get("FuelReservoir")
        put(surf, F["btn"], f"COMBUSTIBLE: {sf:.2f} t".replace(".", ",") if sf is not None else "COMBUSTIBLE: ?",
            (8, H - 22), RED if sf is not None and sf < 0.1 else ORANGE)
        zonas = sum(c for n, c in (((d or {}).get("rings") or {}).get("signals") or []) if "miner" in n.lower() or "mining" in n.lower())
        put(surf, F["small"], f"Zonas de minería en el planeta: {zonas}", (W - 8, H - 18), DIM, anchor="topright")
        return
    if last and last.get("motherlode"):
        blink = int(now * 2) % 2
        r = pygame.Rect(4, y - 2, W - 8, 30)
        pygame.draw.rect(surf, RED if blink else BLACK, r, border_radius=6)
        pygame.draw.rect(surf, RED, r, 2, border_radius=6)
        put(surf, F["big"], f"NÚCLEO: {last['motherlode'].upper()}", r.center, WHITE, anchor="center")
        y += 34
    put(surf, F["small"], "ÚLTIMO PROSPECTOR", (8, y), DIM)
    put(surf, F["small"], "REFINADO (SESIÓN)", (318, y), DIM); y += 14
    yy = y
    if not last:
        put(surf, F["btn"], "Lanza un prospector", (8, y + 4), DIM)
    else:
        put(surf, F["btn"], f"Contenido: {last.get('content') or '?'}", (8, y), ORANGE); y += 22
        if last.get("remaining") is not None:
            put(surf, F["small"], f"Restante {last['remaining']:.0f}%", (8, y), DIM); y += 16
        for name, pct in last.get("mats") or []:
            put(surf, F["small"], name, (8, y + 1), ORANGE, 120)
            bx = pygame.Rect(132, y, 140, 14)
            pygame.draw.rect(surf, DIM, bx, 1)
            pygame.draw.rect(surf, BLUE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(pct, 100) / 100), bx.h - 4))
            put(surf, F["small"], f"{pct:.1f}%", (bx.right + 34, y + 1), WHITE, anchor="topright")
            y += 19
    pygame.draw.line(surf, DIM, (310, yy - 14), (310, H - 30))
    ref = sorted((m.get("refined") or {}).items(), key=lambda kv: -kv[1])
    if not ref:
        put(surf, F["small"], "nada aún", (318, yy + 4), DIM)
    for name, n in ref[:8]:
        put(surf, F["small"], name, (318, yy + 2), ORANGE, 110)
        put(surf, F["btn"], f"{n} t", (W - 8, yy), ORANGE, anchor="topright"); yy += 20
    pygame.draw.line(surf, DIM, (8, H - 26), (W - 8, H - 26))
    lim = m.get("limpets")
    put(surf, F["btn"], f"LIMPETS: {lim if lim is not None else '?'}", (8, H - 22), RED if lim == 0 else ORANGE)
    put(surf, F["small"], f"Prospectores {m.get('prospectors', 0)}   ·   Recolectores {m.get('collectors', 0)}",
        (W - 8, H - 18), DIM, anchor="topright")

# ---------- 11 sesion ----------
def view_session(surf, d, flags, now):
    s_ = (d or {}).get("sess") or {}
    if not s_:
        put(surf, F["btn"], "Sin sesión (carga la partida)", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    e = s_.get("earn") or {}
    play_ = (s_.get("play") or 0) + (max(0, (s_.get("lastts") or s_["seg"]) - s_["seg"]) if s_.get("seg") else 0)
    left = [("HOY " + game_date(), dur(play_ if s_.get("day") else time.time() - (s_.get("start") or time.time()))),
            ("SALTOS", str(s_.get("jumps", 0))),
            ("AÑOS LUZ", f"{s_.get('ly', 0):,.0f}".replace(",", ".")), ("BAJAS  pie · nave", f"{s_.get('kfoot', 0)} · {s_.get('kills', 0) - s_.get('kfoot', 0)}"),
            ("MUERTES", str(s_.get("deaths", 0)))]
    right = [("RECOMPENSAS", e.get("bounty")), ("COMERCIO", e.get("trade")), ("EXPLORACIÓN", e.get("explo")),
             ("MISIONES", e.get("missions")), ("EXOBIOLOGÍA", e.get("bio"))]
    y = TOP + 6
    for (l1, v1), (l2, v2) in zip(left, right):
        put(surf, F["small"], l1, (8, y + 4), BLUE if l1.startswith("HOY") else DIM, 130)
        put(surf, F["big"], v1, (226, y), RED if l1 == "MUERTES" and v1 != "0" else ORANGE, 90, anchor="topright")
        put(surf, F["small"], l2, (246, y + 4), DIM)
        put(surf, F["big"], cr(v2), (W - 8, y), ORANGE, anchor="topright")
        y += 32
    pygame.draw.line(surf, DIM, (236, TOP + 4), (236, y - 4))
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 6
    bal, c0 = (d or {}).get("balance"), s_.get("credits0")
    if bal is not None:
        put(surf, F["small"], "SALDO", (8, y + 6), DIM)
        put(surf, F["big"], f"{bal:,.0f} cr".replace(",", "."), (60, y), ORANGE)
        if c0 is not None:
            diff = bal - c0
            put(surf, F["big"], ("+" if diff >= 0 else "") + cr(diff), (W - 8, y), GREEN if diff >= 0 else RED, anchor="topright")

# ---------- 12 submenu ----------

# ---------- 7.2 sistema en movimiento (planetario) ----------
SPEEDS = [(1, "TIEMPO REAL"), (60, "1 min / s"), (3600, "1 hora / s"), (86400, "1 día / s"),
          (864000, "10 días / s"), (8640000, "100 días / s"), (31536000, "1 año / s")]
orr = {"speed": 3, "paused": False, "t": None, "last": None, "focus": None, "sel": None, "sys": None,
       "scale": None, "hits": []}
OR_AREA = pygame.Rect(0, TOP, 332, H - TOP)
OR_X = 336                                   # columna derecha

def or_btn(name):
    w2 = (W - OR_X - 6) // 2
    return {"menos": pygame.Rect(OR_X, 176, w2, 32), "mas": pygame.Rect(OR_X + w2 + 4, 176, w2, 32),
            "pausa": pygame.Rect(OR_X, 226, W - OR_X - 4, 28), "zoom": pygame.Rect(OR_X, 258, W - OR_X - 4, 28),
            "ahora": pygame.Rect(OR_X, 290, W - OR_X - 4, 28)}[name]

STAR_COL = {"O": (150, 180, 255), "B": (170, 200, 255), "A": (230, 235, 255), "F": (255, 250, 215), "G": (255, 228, 110),
            "K": (255, 165, 70), "M": (255, 105, 70), "L": (220, 70, 60), "T": (170, 60, 90), "Y": (120, 50, 80),
            "N": (210, 225, 255), "H": (90, 90, 90), "D": (235, 240, 255)}
PLANET_COL = {"Earthlike body": (60, 190, 150), "Water world": (60, 120, 255), "Ammonia world": (190, 160, 90),
              "Icy body": (190, 220, 240), "Rocky body": (150, 130, 110), "Rocky ice body": (170, 170, 185),
              "Metal rich body": (205, 120, 60), "High metal content body": (180, 140, 100)}

def bcol(o):
    st = o.get("star")
    if st:
        return STAR_COL.get("H" if st.startswith("Super") else st[0], (240, 240, 240))
    pc = o.get("pc") or ""
    return (210, 170, 120) if "gas giant" in pc.lower() else PLANET_COL.get(pc, (160, 160, 160))

def bsize(o):
    if o.get("star"):
        return 4 if o["star"][0] in "DNH" else 8
    return 5 if "gas giant" in (o.get("pc") or "").lower() else (4 if o.get("r", 0) > 5000 else 3)

def kep(o, t=None, E=None):
    """Posicion (x, y) en metros respecto a su padre. Con E dibuja la orbita completa."""
    a, P = o.get("a"), o.get("P")
    if not a or not P:
        return 0.0, 0.0
    e = min(o.get("e", 0), 0.99)
    if E is None:
        M = math.radians(o.get("M", 0)) + 2 * math.pi * ((t - (o.get("t") or t)) / P)
        E = M
        for _ in range(8):
            E -= (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    xv, yv = a * (math.cos(E) - e), a * math.sqrt(1 - e * e) * math.sin(E)
    w, i, W_ = math.radians(o.get("w", 0)), math.radians(o.get("i", 0)), math.radians(o.get("W", 0))
    xw, yw = xv * math.cos(w) - yv * math.sin(w), xv * math.sin(w) + yv * math.cos(w)
    return (xw * math.cos(W_) - yw * math.cos(i) * math.sin(W_), xw * math.sin(W_) + yw * math.cos(i) * math.cos(W_))

_ORBC = {}

def orbit_pts(o):
    """Forma de la orbita (49 puntos respecto al padre): no cambia con el tiempo, se calcula una vez (v1.1.1)."""
    k = (o.get("id"), o.get("a"), o.get("e"), o.get("w"), o.get("i"), o.get("W"), o.get("P"))
    pts = _ORBC.get(k)
    if pts is None:
        if len(_ORBC) > 600:
            _ORBC.clear()
        pts = _ORBC[k] = [kep(o, E=j * 2 * math.pi / 48) for j in range(49)]
    return pts

def build_tree(orbits):
    nodes, parent, ntype = {}, {}, {}
    for o in orbits:
        if o.get("id") is None:
            continue
        nodes[o["id"]] = o
        chain = o.get("par") or []
        if chain:
            parent[o["id"]] = chain[0][1]
            for (k1, v1), (k2, v2) in zip(chain, chain[1:]):
                parent.setdefault(v1, v2)
            for k, v in chain:
                ntype.setdefault(v, k)
        ntype[o["id"]] = "Star" if o.get("star") else "Planet" if o.get("pc") else ntype.get(o["id"], "Null")
    ids = set(nodes) | set(parent) | set(parent.values())
    roots = [i for i in ids if i not in parent]
    root = 0 if 0 in roots else (min(roots) if roots else None)
    return nodes, parent, ntype, root, ids

def classify(F, tree):
    nodes, parent, ntype, root, ids = tree
    local, moons = [], {}
    for n in ids:
        if n == F:
            continue
        chain, p, ok = [], parent.get(n), False
        while p is not None:
            if p == F:
                ok = True; break
            chain.append(p); p = parent.get(p)
        if not ok:
            continue
        planets = [c for c in chain if ntype.get(c) == "Planet"]
        if planets:
            moons.setdefault(planets[-1], []).append(n)
        else:
            local.append(n)
    return local, moons

def view_orrery(surf, d, flags, now):
    orbits = (d or {}).get("orbits") or []
    system = ((d or {}).get("explo") or {}).get("system")
    if system != orr["sys"]:
        orr.update(sys=system, focus=None, sel=None, scale=None)
    if orr["t"] is None:
        orr["t"] = now
    if orr["last"] is not None and not orr["paused"]:
        orr["t"] += (now - orr["last"]) * SPEEDS[orr["speed"]][0]
    orr["last"] = now
    t = orr["t"]
    pygame.draw.line(surf, DIM, (OR_AREA.right + 1, TOP + 2), (OR_AREA.right + 1, H - 4))
    draw_or_side(surf, d, orbits)
    tree = build_tree(orbits)
    nodes, parent, ntype, root, ids = tree
    if root is None or not nodes:
        put(surf, F["btn"], "Escanea el sistema (FSS)", (OR_AREA.centerx, OR_AREA.centery - 10), DIM, anchor="center")
        put(surf, F["small"], "para ver sus órbitas", (OR_AREA.centerx, OR_AREA.centery + 12), DIM, anchor="center")
        orr["hits"] = []
        return
    F_ = orr["focus"] if orr["focus"] in ids else root
    memo = {}
    def apos(i):
        if i in memo: return memo[i]
        p = parent.get(i)
        bx, by = apos(p) if p is not None else (0.0, 0.0)
        ox, oy = kep(nodes[i], t) if i in nodes else (0.0, 0.0)
        memo[i] = (bx + ox, by + oy)
        return memo[i]
    local, moons = classify(F_, tree)
    fx, fy = apos(F_)
    cx, cy = OR_AREA.center
    rmax = min(OR_AREA.w, OR_AREA.h) / 2 - 14
    # escala logaritmica (fija mientras no cambie el foco o los cuerpos)
    key = (F_, len(nodes))
    if not orr["scale"] or orr["scale"][0] != key:
        ds = [math.hypot(*[a - b for a, b in zip(apos(n), (fx, fy))]) for n in local]
        ds += [nodes[n].get("a", 0) * (1 + nodes[n].get("e", 0)) for n in local if n in nodes and parent.get(n) == F_]
        ds = [x for x in ds if x > 0]
        dmax = max(ds) if ds else 1.0
        d0 = max(min(ds) * 0.4, dmax * 1e-5) if ds else 1.0
        orr["scale"] = (key, dmax, d0)
    _, dmax, d0 = orr["scale"]
    norm = math.log1p(dmax / d0)
    def scr(px, py):
        dx, dy = px - fx, py - fy
        dd = math.hypot(dx, dy)
        if dd <= 0:
            return cx, cy
        r = rmax * min(1.05, math.log1p(dd / d0) / norm)
        return cx + dx / dd * r * ORR_XS[0], cy - dy / dd * r
    surf.set_clip(OR_AREA)
    # orbitas
    for n in local:
        o = nodes.get(n)
        if not o or not o.get("a"):
            continue
        bx, by = apos(parent.get(n))
        pts = [scr(bx + x, by + y) for x, y in orbit_pts(o)]
        pygame.draw.lines(surf, (60, 40, 10) if ntype.get(n) == "Null" else DIM, False, pts, 1)
    # cuerpos
    hits = []
    me = (d or {}).get("body")
    def body(n, x, y, small=False):
        o = nodes.get(n)
        if not o or ntype.get(n) == "Null":
            return
        r = 2 if small else bsize(o)
        col = bcol(o)
        pygame.draw.circle(surf, col, (int(x), int(y)), r)
        if o.get("rings") and not small:
            pygame.draw.ellipse(surf, (200, 180, 140), (x - r - 4, y - 2, 2 * r + 8, 4), 1)
        if o.get("star") and o["star"][0] in "NH":
            pygame.draw.circle(surf, col, (int(x), int(y)), r + 3, 1)
        if n == orr["sel"]:
            pygame.draw.circle(surf, WHITE, (int(x), int(y)), r + 5, 1)
        if me and o.get("name") == me:
            pygame.draw.circle(surf, GREEN, (int(x), int(y)), r + 8, 1)
            put(surf, F["small"], "TÚ", (x + r + 8, y - 16), GREEN)
        if not small and len(local) < 30:
            nm = o.get("name", "")
            short = nm[len(system):].strip() if system and nm.startswith(system) else nm
            put(surf, F["small"], short or nm, (x + r + 3, y + 1), DIM, 60)
        hits.append((n, x, y))
    if ntype.get(F_) != "Null":
        body(F_, cx, cy)
    else:
        pygame.draw.line(surf, DIM, (cx - 4, cy), (cx + 4, cy)); pygame.draw.line(surf, DIM, (cx, cy - 4), (cx, cy + 4))
    for n in local:
        x, y = scr(*apos(n))
        body(n, x, y)
        ms = moons.get(n)
        if ms:
            ax, ay = apos(n)
            rel = [(m, apos(m)[0] - ax, apos(m)[1] - ay) for m in ms]
            dm = [math.hypot(dx, dy) for _, dx, dy in rel]
            mmax, mmin = max(dm + [1]), min([v for v in dm if v > 0] + [1])
            for (m, dx, dy), dd in zip(rel, dm):
                rr = 9 + 12 * math.log1p(dd / (mmin * 0.5)) / math.log1p(mmax / (mmin * 0.5)) if dd > 0 else 9
                pygame.draw.circle(surf, (50, 35, 10), (int(x), int(y)), int(rr), 1)
                body(m, x + dx / (dd or 1) * rr, y - dy / (dd or 1) * rr, small=True)
    surf.set_clip(None)
    orr["hits"] = hits
    # tiempo simulado
    off = (t - now) / 86400
    if abs(off) > 0.01 or orr["paused"]:
        put(surf, F["small"], ("PAUSA  " if orr["paused"] else "") + f"T{'+' if off >= 0 else ''}{off:,.1f} días".replace(",", "X").replace(".", ",").replace("X", "."),
            (6, H - 16), ORANGE)
    if F_ != root:
        put(surf, F["small"], "ZOOM", (6, TOP + 4), GREEN)

def draw_or_side(surf, d, orbits):
    o = next((x for x in orbits if x.get("id") == orr["sel"]), None)
    y = TOP + 4
    if not o or not o.get("name"):
        put(surf, F["small"], "Toca un cuerpo", (OR_X, y), DIM)
        put(surf, F["small"], "para ver sus datos", (OR_X, y + 14), DIM)
    else:
        system = ((d or {}).get("explo") or {}).get("system") or ""
        nm = o["name"]
        short = nm[len(system):].strip() if system and nm.startswith(system) else nm
        put(surf, F["btn"], short or nm, (OR_X, y), ORANGE, W - OR_X - 4); y += 20
        put(surf, F["small"], o.get("cls", ""), (OR_X, y), bcol(o), W - OR_X - 4); y += 15
        put(surf, F["small"], f"{o.get('dist', 0):,} ls".replace(",", "."), (OR_X, y), DIM); y += 14
        if o.get("P"):
            days = o["P"] / 86400
            put(surf, F["small"], f"Órbita: {days:,.1f} días".replace(",", "X").replace(".", ",").replace("X", "."), (OR_X, y), DIM); y += 14
        if o.get("r"):
            put(surf, F["small"], f"Radio: {o['r']:,} km".replace(",", "."), (OR_X, y), DIM); y += 14
        put(surf, F["small"], ("1º  " if o.get("first") else "") + ("MAPEADO" if o.get("mapped") else ""), (OR_X, y), GREEN); y += 14
        put(surf, F["small"], f"~ {cr(o.get('value'))} cr", (OR_X, y), ORANGE); y += 14
        if o.get("src") == "edsm":
            put(surf, F["small"], "Fuente: EDSM (pos. aprox.)", (OR_X, y), BLUE, W - OR_X - 4)
    now = time.time()
    for k, txt in (("menos", "-"), ("mas", "+")):
        draw_button(surf, or_btn(k), txt, None, F["big"], lit=flash.get((72, k), 0) > now)
    put(surf, F["small"], SPEEDS[orr["speed"]][1], (or_btn("menos").x + (W - OR_X) // 2 - 2, 214), ORANGE, anchor="midtop")
    draw_button(surf, or_btn("pausa"), "SEGUIR" if orr["paused"] else "PAUSA", None, F["btn"], filled=orr["paused"])
    zoomed = orr["focus"] is not None
    draw_button(surf, or_btn("zoom"), "SISTEMA" if zoomed else "ZOOM", None, F["btn"],
                dim=not zoomed and orr["sel"] is None, filled=zoomed)
    draw_button(surf, or_btn("ahora"), "AHORA", None, F["btn"], lit=flash.get((72, "ahora"), 0) > now)

def tap_orrery(x, y):
    if OR_AREA.collidepoint(x, y):
        best = min(orr["hits"], key=lambda h: (h[1] - x) ** 2 + (h[2] - y) ** 2, default=None)
        if best and (best[1] - x) ** 2 + (best[2] - y) ** 2 < 18 ** 2:
            orr["sel"] = best[0]
        return
    if or_btn("menos").collidepoint(x, y):
        tap_flash((72, "menos")); orr["speed"] = max(0, orr["speed"] - 1)
    elif or_btn("mas").collidepoint(x, y):
        tap_flash((72, "mas")); orr["speed"] = min(len(SPEEDS) - 1, orr["speed"] + 1)
    elif or_btn("pausa").collidepoint(x, y):
        orr["paused"] = not orr["paused"]
    elif or_btn("zoom").collidepoint(x, y):
        if orr["focus"] is not None:
            orr["focus"] = None
        elif orr["sel"] is not None:
            orr["focus"] = orr["sel"]
        orr["scale"] = None
    elif or_btn("ahora").collidepoint(x, y):
        tap_flash((72, "ahora")); orr["t"] = time.time()

# ---------- 7.3 xenobiologia ----------
def hav(a, b, R):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(min(1, h)))

SHIPOV = {"pos": None, "src": None, "cur": None}
NAVE_BTN = pygame.Rect(196, H - 58, 124, 36)          # EN VIVO
NAVE_BTN_BIO = pygame.Rect(196, H - 64, 124, 34)      # XENOBIOLOGIA: por encima de MUESTRAS SIN VENDER

def ship_pos(b):
    s_ = b.get("ship")
    if s_ != SHIPOV["src"]:              # el juego da una posicion nueva: manda la del juego
        SHIPOV["src"], SHIPOV["pos"] = s_, None
    return SHIPOV["pos"] or s_

def ship_here():
    if SHIPOV["cur"]:
        SHIPOV["pos"] = list(SHIPOV["cur"])
        tap_flash(("nave", 0))

def draw_compass(surf, d, b, btn=None):
    btn = btn or NAVE_BTN
    ship, lat, lon, R = ship_pos(b), b.get("lat"), b.get("lon"), b.get("R")
    out = bool((d or {}).get("Flags", 0) & (1 << 26)) or bool((d or {}).get("Flags2", 0) & 1)
    SHIPOV["cur"] = (lat, lon) if (out and lat is not None) else None
    if out and lat is not None and R:
        draw_button(surf, btn, "NAVE AQUÍ", None, F["btn"], lit=flash.get(("nave", 0), 0) > time.time())
    if not ship or lat is None or not R or not out:
        return
    y0 = H - 62
    pygame.draw.line(surf, DIM, (8, y0 - 4), (W - 8, y0 - 4))
    dist = hav(ship, (lat, lon), R)
    p1, p2, dl = math.radians(lat), math.radians(ship[0]), math.radians(ship[1] - lon)
    brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                  math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
    hdg = b.get("hdg")
    cx, cy, r = 32, y0 + 17, 17
    pygame.draw.circle(surf, DIM, (cx, cy), r, 1)
    if hdg is not None:
        a = math.radians(brg - hdg)
        pt = lambda k, da: (cx + r * k * math.sin(a + da), cy - r * k * math.cos(a + da))
        pygame.draw.polygon(surf, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
    txt = f"{dist / 1000:.1f} km".replace(".", ",") if dist >= 1000 else f"{dist:.0f} m"
    put(surf, F["small"], "NAVE", (60, y0 + 2), DIM)
    put(surf, F["big"], txt, (60, y0 + 14), GREEN)
    put(surf, F["btn"], f"rumbo {brg:.0f}°", (W - 8, y0 + 4), ORANGE, anchor="topright")
    if hdg is not None:
        put(surf, F["small"], f"vas a {hdg:.0f}°", (W - 8, y0 + 24), DIM, anchor="topright")

def view_bio(surf, d, flags, now):
    b = (d or {}).get("bio") or {}
    y = TOP + 6
    put(surf, F["small"], "CUERPO", (8, y), DIM)
    sig = b.get("signals")
    put(surf, F["small"], f"SEÑALES BIO: {sig if sig is not None else '?'}", (W - 8, y), DIM, anchor="topright"); y += 14
    put(surf, F["btn"], b.get("body") or "No estás en un planeta", (8, y), ORANGE if b.get("body") else DIM, W - 16); y += 22
    done = set(b.get("done") or [])
    gx = 8
    for g in b.get("genuses") or []:
        t = ("OK " if g in done else "") + g
        w_ = F["small"].size(t)[0] + 10
        if gx + w_ > W - 4: break
        pygame.draw.rect(surf, GREEN if g in done else DIM, (gx, y, w_ - 4, 16), 1, border_radius=3)
        put(surf, F["small"], t, (gx + 3, y + 2), GREEN if g in done else ORANGE)
        gx += w_
    y += 22
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 6
    if not b.get("species"):
        put(surf, F["btn"], "Sin muestreo en curso", (W // 2, y + 50), DIM, anchor="center")
    else:
        step = b.get("step", 0)
        put(surf, F["big"], b["species"].upper(), (8, y), GREEN if step >= 3 else ORANGE, W - 90)
        for k in range(3):
            pygame.draw.circle(surf, ORANGE, (W - 70 + k * 22, y + 12), 8, 0 if k < step else 1)
        y += 26
        put(surf, F["small"], b.get("variant") or "", (8, y), DIM, W - 220)
        val = b.get("value")
        if val:
            txt = ("" if b.get("exact") else "~") + cr(val) + " cr"
            if b.get("bonus"):
                txt += f"  x5 = {cr(val * 5)}"
            put(surf, F["btn"], txt, (W - 8, y - 3), GREEN if b.get("bonus") else ORANGE, 210, anchor="topright")
        y += 20
        pts, R = b.get("pts") or [], b.get("R")
        lat, lon, rng = b.get("lat"), b.get("lon"), b.get("range", 100)
        if step >= 3:
            put(surf, F["big"], "MUESTRA COMPLETA", (W // 2, y + 22), GREEN, anchor="center")
        elif pts and R and lat is not None:
            dist = min(hav(p, (lat, lon), R) for p in pts)
            ok = dist >= rng
            put(surf, F["num"], f"{dist:,.0f} m".replace(",", "."), (8, y), GREEN if ok else RED)
            put(surf, F["btn"], f"mín. {rng} m", (W - 8, y + 4), DIM, anchor="topright")
            put(surf, F["small"], "PUEDES MUESTREAR" if ok else "ALÉJATE", (W - 8, y + 26), GREEN if ok else RED, anchor="topright")
            bx = pygame.Rect(8, y + 44, W - 16, 12)
            pygame.draw.rect(surf, DIM, bx, 1)
            pygame.draw.rect(surf, GREEN if ok else RED, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(1, dist / rng)), bx.h - 4))
        else:
            put(surf, F["btn"], f"Distancia mínima del género: {rng} m", (8, y + 10), DIM)
    draw_compass(surf, d, b, NAVE_BTN_BIO)
    pygame.draw.line(surf, DIM, (8, H - 24), (W - 8, H - 24))
    put(surf, F["btn"], f"MUESTRAS SIN VENDER: {b.get('unsold', 0)}", (8, H - 20), ORANGE)
    if b.get("unsold_cr"):
        put(surf, F["btn"], f"~ {cr(b['unsold_cr'])} cr", (W - 8, H - 20), ORANGE, anchor="topright")

# ---------- 11 submenu / 11.2 en vivo ----------
def view_sub11(surf, d, flags, now):
    for i, (n, name) in enumerate([("1", "SESIÓN"), ("2", "EN VIVO")]):
        draw_button(surf, grid(i, 2, 1), n, name, F["num"], lit=flash.get((11, i), 0) > now)

def chips(surf, items, y, cols=4):
    cw = (W - 16) // cols
    for k, (txt, on, col) in enumerate(items):
        r = pygame.Rect(8 + (k % cols) * cw, y + (k // cols) * 24, cw - 4, 20)
        if on and glow(txt):
            col = WHITE
        if on:
            pygame.draw.rect(surf, col, r, border_radius=4)
            put(surf, F["small"], txt, r.center, BLACK, cw - 8, anchor="center")
        else:
            pygame.draw.rect(surf, DIM, r, 1, border_radius=4)
            put(surf, F["small"], txt, r.center, DIM, cw - 8, anchor="center")
    return y + ((len(items) + cols - 1) // cols) * 24

LEGAL = {"Clean": ("LIMPIO", None), "IllegalCargo": ("CARGA ILEGAL", "r"), "Speeding": ("EXCESO VELOCIDAD", "r"),
         "Wanted": ("BUSCADO", "r"), "Hostile": ("HOSTIL", "r"), "PassengerWanted": ("PASAJERO BUSCADO", "r"),
         "Warrant": ("ORDEN DE ARRESTO", "r"), "Allied": ("ALIADO", None), "Thargoid": ("THARGOIDE", "r")}

def pctv(v):
    return None if v is None else v * 100

def view_live(surf, d, flags, now):
    d = d or {}
    L, f2 = d.get("live") or {}, d.get("Flags2", 0)
    if f2 & 1:
        mode = "A PIE"
    elif flags & (1 << 26):
        mode = (d.get("srvtype") or "SRV").upper()
    elif flags & (1 << 25):
        mode = "CAZA"
    else:
        mode = "NAVE"
    y = TOP + 4
    if mode == "A PIE" and in_fight(d, now):
        return draw_fight_big(surf, d, now)
    put(surf, F["big"], mode, (8, y), GREEN)
    if mode == "A PIE" and in_fight(d, now):
        tw_ = F["big"].size(mode)[0]
        r_ = pygame.Rect(16 + tw_, y + 2, 112, 22)
        on_ = int(now * 2) % 2 == 0
        pygame.draw.rect(surf, RED, r_, 0 if on_ else 2, border_radius=4)
        put(surf, F["small"], "EN COMBATE", r_.center, BLACK if on_ else RED, anchor="center")
    if mode == "A PIE":
        s_ = L.get("suit") or {}
        put(surf, F["small"], " · ".join(x for x in (s_.get("name"), s_.get("loadout")) if x), (W - 8, y + 6), ORANGE, 300, anchor="topright")
        y += 30
        oxy, hp = pctv(L.get("oxy")), pctv(L.get("health"))
        half = (W - 24) // 2
        bar(surf, 8, y, half, "OXÍGENO", oxy, RED if oxy is not None and oxy < 25 else BLUE)
        bar(surf, 16 + half, y, half, "SALUD", hp, RED if hp is not None and hp < 30 else GREEN)
        y += 22
        t = L.get("temp")
        tcol = RED if f2 & ((1 << 9) | (1 << 11)) else BLUE if f2 & ((1 << 8) | (1 << 10)) else ORANGE
        put(surf, F["small"], "TEMPERATURA", (8, y + 4), DIM)
        put(surf, F["big"], f"{t - 273.15:.0f} °C" if t is not None else "?", (100, y), tcol)
        g = L.get("grav")
        put(surf, F["small"], "GRAVEDAD", (250, y + 4), DIM)
        put(surf, F["big"], f"{g:.2f} G".replace(".", ",") if g is not None else "-", (W - 8, y),
            RED if g and g > 2 else ORANGE, anchor="topright")
        y += 26
        put(surf, F["small"], "ARMA", (8, y + 4), DIM)
        put(surf, F["btn"], L.get("weapon") or "-", (60, y + 1), ORANGE, W - 70); y += 24
        act_ = [c_ for c_ in [("ESTACIÓN", f2 & (1 << 3), BLUE), ("PLANETA", f2 & (1 << 4), BLUE),
                              ("RESPIRABLE", f2 & (1 << 16), GREEN), ("POCO O2", f2 & (1 << 6), RED),
                              ("SALUD BAJA", f2 & (1 << 7), RED), ("FRÍO", f2 & ((1 << 8) | (1 << 10)), BLUE),
                              ("CALOR", f2 & ((1 << 9) | (1 << 11)), RED), ("PLANEO", f2 & (1 << 12), ORANGE)] if c_[1]]
        y = chips(surf, act_[:4], y) if act_ else y
        Z = d.get("footcz") or {}
        P = d.get("pack") or {}
        if Z.get("n"):
            led = Z.get("led") or {}
            zt = (Z.get("zone") or "ZONA DE COMBATE").upper() + (f"  ·  por {Z['side']}" if Z.get("side") else "")
            put(surf, F["small"], zt, (8, y + 2), BLUE, W - 16)
            put(surf, F["btn"], f"{Z['n']} BAJAS", (8, y + 18), GREEN)
            put(surf, F["btn"], f"{crx(led.get('cr', 0))} cr sin cobrar", (120, y + 18), ORANGE, 230)
            tf_ = ((d.get("career") or {}).get("foot"))
            rt_ = "  ·  ".join(t_ for t_ in ((f"{str(Z['rate']).replace('.', ',')} / min" if Z.get("rate") else ""),
                                             (f"total {fnum(tf_, 0)}" if tf_ is not None else "")) if t_)
            if rt_:
                put(surf, F["small"], rt_, (W - 8, y + 22), DIM, anchor="topright")
        if Z.get("n"):
            y += 40
        draw_cons_row(surf, d, 8, y + 2, F["btn"], 12)
        y += 4
        if not Z.get("n") and (P.get("n_items") or P.get("n_comp") or P.get("n_data")):
            put(surf, F["small"], f"Mochila: {P.get('n_items', 0)} objetos · {P.get('n_comp', 0)} componentes · {P.get('n_data', 0)} datos",
                (8, y + 22), DIM, W - 16)
        draw_compass(surf, d, d.get("bio") or {})
    elif flags & (1 << 26):
        put(surf, F["small"], d.get("body") or "", (W - 8, y + 6), ORANGE, 300, anchor="topright")
        y += 34
        y = chips(surf, [("FRENO MANO", flags & (1 << 12), RED), ("TORRETA", flags & (1 << 13), ORANGE),
                         ("TORR. RECOGIDA", flags & (1 << 14), DIM), ("ASIST. CONDUC.", flags & (1 << 15), GREEN),
                         ("LUCES", flags & (1 << 8), ORANGE), ("LUCES LARGAS", flags & (1 << 31), ORANGE),
                         ("CARGA", flags & (1 << 9), ORANGE), ("SOBRECALENT.", flags & (1 << 20), RED)], y)
        if d.get("srvcargo") is not None:
            put(surf, F["small"], "BODEGA DEL VEHÍCULO", (8, y + 8), DIM)
            put(surf, F["big"], f"{d['srvcargo']} t", (170, y + 2), ORANGE)
            inv = ", ".join(f"{n} {c}" for n, c in (d.get("srvinv") or [])[:4])
            if inv:
                put(surf, F["small"], inv, (240, y + 8), WHITE, W - 248)
        sf = (d.get("Fuel") or {}).get("FuelReservoir")
        put(surf, F["small"], "COMBUSTIBLE", (8, y + 40), DIM)
        put(surf, F["big"], f"{sf:.2f} t".replace(".", ",") if sf is not None else "?", (110, y + 34),
            RED if sf is not None and sf < 0.1 else ORANGE)
        sh = flags & 8
        put(surf, F["btn"], "ESCUDOS ACTIVOS" if sh else "SIN ESCUDOS", (W - 8, y + 36), BLUE if sh else RED, anchor="topright")
        sm = d.get("srvmats") or []
        if sm:
            put(surf, F["small"], "RECOGIDO: " + ", ".join(f"{n} {c}" + (" (MÁX)" if full else "") for n, c, full in sm[:5]),
                (8, y + 64), RED if any(x[2] for x in sm) else ORANGE, W - 16)
        draw_compass(surf, d, d.get("bio") or {})
    else:
        sh = L.get("ship") or {}
        nm = " · ".join(x for x in (sh.get("name"), sh.get("ident")) if x)
        put(surf, F["small"], (sh.get("ship") or "").upper(), (W - 8, y + 2), ORANGE, 300, anchor="topright")
        put(surf, F["small"], nm, (W - 8, y + 16), (70, 120, 230), 300, anchor="topright")
        y += 32
        hull = pctv(sh.get("hull"))
        half = (W - 24) // 2
        bar(surf, 8, y, half, "CASCO", hull, RED if hull is not None and hull < 30 else ORANGE)
        cg, cap = L.get("cargo"), d.get("cargocap")
        put(surf, F["small"], "CARGA", (16 + half, y + 1), DIM)
        put(surf, F["btn"], f"{cg:.0f} / {cap if cap is not None else '?'} t" if cg is not None else "-",
            (W - 8, y - 2), ORANGE, anchor="topright")
        y += 22
        lg, kind = LEGAL.get(L.get("legal"), (L.get("legal") or "-", None))
        put(surf, F["small"], "ESTADO", (8, y + 4), DIM)
        put(surf, F["btn"], lg, (64, y + 1), RED if kind else GREEN)
        alt = L.get("alt")
        if alt is not None and flags & (1 << 21):
            real = not flags & (1 << 29)
            lab, acol = "ALTITUD", ORANGE
            if real and 7 <= alt <= 40:
                lab, acol = "RHINO OK", GREEN
            elif real and alt < 7:
                lab, acol = "SUBE A 7 m", ORANGE
            elif real and alt <= 80:
                lab, acol = "BAJA A 40 m", ORANGE
            put(surf, F["small"], lab, (250, y + 4), acol if lab != "ALTITUD" else DIM)
            put(surf, F["btn"], f"{alt / 1000:.1f} km".replace(".", ",") if alt >= 1000 else f"{alt:.0f} m",
                (W - 8, y + 1), acol, anchor="topright")
        y += 26
        rh = sh.get("rhino")
        rcol = GREEN if rh == "A BORDO" else RED if rh == "SIN RHINO" else ORANGE
        chips(surf, ([(f"RHINO {rh}" if rh != "SIN RHINO" else rh, rh in ("A BORDO", "SIN RHINO", "FUERA"), rcol)] if rh else []) + veh_chips(d, rh) + [("ATRACADO", flags & 1, BLUE), ("ATERRIZADO", flags & 2, BLUE), ("TREN", flags & 4, ORANGE),
                     ("ESCUDOS", flags & 8, BLUE), ("SUPERCRUCERO", flags & 16, BLUE), ("FA OFF", flags & 32, RED),
                     ("ARMAS", flags & 64, RED), ("LUCES", flags & 256, ORANGE), ("RECOGEDOR", flags & 512, ORANGE),
                     ("SILENCIOSO", flags & 1024, BLUE), ("RECOG. COMB.", flags & 2048, ORANGE),
                     ("MASA BLOQ.", flags & (1 << 16), RED), ("FSD CARGANDO", flags & (1 << 17), BLUE),
                     ("FSD ENFRIANDO", flags & (1 << 18), DIM), ("SOBRECALENT.", flags & (1 << 20), RED),
                     ("VISIÓN NOCT.", flags & (1 << 28), GREEN)], y)

# ---------- 12.5 materiales / 12.6 portanaves / 12.7 mercado ----------
def pager(key, n, per):
    pages = max(1, (n + per - 1) // per)
    pg = ui.get(key, 0) % pages
    if pages > 1:
        put(surf_ref[0], F["small"], f"pág {pg + 1}/{pages}  (toca para pasar)", (W // 2, H - 9), DIM, anchor="center")
    return pg
surf_ref = [None]

def view_mats(surf, d, flags, now):
    surf_ref[0] = surf
    M = (d or {}).get("mats") or {}
    rows = M.get("list") or []
    y = TOP + 4
    put(surf, F["small"], f"{M.get('n', 0)} materiales", (8, y), DIM)
    put(surf, F["small"], f"AL MÁXIMO: {M.get('full', 0)}", (W - 8, y), RED if M.get("full") else DIM, anchor="topright")
    y += 16
    if not rows:
        put(surf, F["btn"], "Sin datos (carga la partida)", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    per = 10
    pg = pager("page125", len(rows), per)
    for name, c, mx in rows[pg * per:(pg + 1) * per]:
        pct = c / mx
        col = RED if c >= mx else ORANGE if pct >= 0.9 else DIM
        put(surf, F["small"], name, (8, y + 3), ORANGE, 200)
        bx = pygame.Rect(214, y + 3, 186, 12)
        pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, RED if c >= mx else BLUE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(1, pct)), bx.h - 4))
        put(surf, F["small"], f"{c}/{mx}", (W - 8, y + 3), col if c >= 0.9 * mx else WHITE, anchor="topright")
        y += 22

def view_carrier(surf, d, flags, now):
    c = (d or {}).get("carrier") or {}
    if not (c.get("name") or c.get("callsign")):
        put(surf, F["btn"], "Sin datos del portanaves", (W // 2, (H + TOP) // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], "abre su gestión en el juego una vez", (W // 2, (H + TOP) // 2 + 12), DIM, anchor="center")
        return
    y = TOP + 6
    put(surf, F["big"], (c.get("name") or "").upper(), (8, y), ORANGE, W - 140)
    put(surf, F["btn"], c.get("callsign") or "", (W - 8, y + 2), DIM, anchor="topright"); y += 30
    put(surf, F["small"], "SISTEMA", (8, y + 4), DIM)
    put(surf, F["btn"], c.get("system") or "?", (80, y + 1), ORANGE, W - 90); y += 28
    fuel = c.get("fuel")
    put(surf, F["small"], "TRITIO", (8, y + 1), DIM)
    bx = pygame.Rect(80, y, W - 170, 16)
    pygame.draw.rect(surf, DIM, bx, 1)
    if fuel is not None:
        pygame.draw.rect(surf, RED if fuel < 135 else GREEN, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(1, fuel / 1000)), bx.h - 4))
    put(surf, F["btn"], f"{fuel} t" if fuel is not None else "?", (W - 8, y - 2), RED if fuel is not None and fuel < 135 else ORANGE, anchor="topright")
    y += 28
    put(surf, F["small"], "SALDO", (8, y + 4), DIM)
    put(surf, F["big"], f"{cr(c.get('balance'))} cr", (80, y), ORANGE); y += 34
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 8
    dest, dep = c.get("dest"), c.get("depart")
    if dest and dep:
        left = dep - time.time()
        put(surf, F["small"], "SALTO PROGRAMADO A", (8, y), DIM)
        put(surf, F["big"], dest.upper(), (8, y + 14), BLUE, W - 16); y += 46
        if left > 0:
            put(surf, F["num"], f"{int(left) // 60:02d}:{int(left) % 60:02d}", (W // 2, y), ORANGE if left > 60 else RED, anchor="midtop")
        else:
            put(surf, F["big"], "SALTANDO...", (W // 2, y + 8), BLUE if int(now * 2) % 2 else WHITE, anchor="midtop")
    else:
        put(surf, F["btn"], "Sin salto programado", (W // 2, y + 30), DIM, anchor="center")

def view_market_base(surf, d, flags, now):
    surf_ref[0] = surf
    m = (d or {}).get("market") or {}
    if not m.get("station"):
        put(surf, F["btn"], "Abre el mercado en una estación", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    y = TOP + 4
    age = int((time.time() - (m.get("t") or time.time())) / 60)
    put(surf, F["btn"], m["station"].upper(), (8, y), ORANGE, W - 120)
    put(surf, F["small"], f"hace {age} min" if age else "ahora", (W - 8, y + 4), DIM, anchor="topright"); y += 22
    sell = m.get("sell") or []
    rows = sell if sell else m.get("best") or []
    put(surf, F["small"], "TU BODEGA AQUÍ" if sell else "BODEGA VACÍA · LO MEJOR PAGADO AQUÍ (vs media)", (8, y), DIM)
    if sell:
        put(surf, F["small"], "TOTAL", (W - 8, y), DIM, anchor="topright")
    y += 16
    per = 7 if sell else 9
    pg = pager("page127", len(rows), per)
    for r in rows[pg * per:(pg + 1) * per]:
        if sell:
            name, n, price, mean, dem = r
        else:
            name, price, mean = r; n = None
        diff = (price - mean) / mean * 100 if mean else 0
        put(surf, F["small"], name, (8, y + 3), ORANGE, 170)
        if n is not None:
            put(surf, F["small"], f"{n} t", (200, y + 3), WHITE, anchor="topright")
        put(surf, F["small"], f"{price:,} cr".replace(",", "."), (300, y + 3), WHITE, anchor="topright")
        put(surf, F["small"], f"{diff:+.0f}%", (350, y + 3), GREEN if diff >= 0 else RED, anchor="topright")
        if n is not None:
            put(surf, F["btn"], cr(n * price), (W - 8, y), GREEN if diff >= 0 else ORANGE, anchor="topright")
        y += 22
    if sell:
        tot = sum(r[1] * r[2] for r in sell)
        pygame.draw.line(surf, DIM, (8, H - 40), (W - 8, H - 40))
        put(surf, F["btn"], f"VENDIENDO TODO: {cr(tot)} cr", (8, H - 36), GREEN)

# ---------- 12.8 notas de viaje ----------
NOTES_FILE = os.path.join(PANEL_DIR, "notas.json")

def trip_load():
    try:
        with open(NOTES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []

trip = {"list": trip_load(), "sel": None, "page": 0, "d": None}

def trip_save():
    import os
    try:
        with open(NOTES_FILE + ".tmp", "w", encoding="utf-8") as f:
            json.dump(trip["list"], f, ensure_ascii=False, indent=1)
        os.replace(NOTES_FILE + ".tmp", NOTES_FILE)
    except OSError as e:
        print("notas:", e)

def trip_here(d):
    d = d or {}
    flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    b = d.get("bio") or {}
    st = d.get("station") or {}
    if b.get("species") and 0 < b.get("step", 0) < 3: tag = "EXOBIO"
    elif flags & 1: tag = "ESTACIÓN"
    elif f2 & 1: tag = "A PIE"
    elif flags & (1 << 26): tag = "SRV"
    elif flags & 2: tag = "ATERRIZADO"
    elif d.get("body"): tag = "PLANETA"
    else: tag = "ESPACIO"
    return {"sys": d.get("system"), "body": d.get("body"), "st": st.get("name") if flags & 1 else None,
            "lat": b.get("lat"), "lon": b.get("lon"), "R": b.get("R"), "pos": d.get("starpos"),
            "tag": tag, "t": time.time()}

def trip_label(n):
    sysname, body = n.get("sys") or "?", n.get("body") or ""
    if n.get("st"):
        return n["st"]
    if body and body != sysname:
        return body
    return sysname

def trip_dist(n, d):
    a, b = n.get("pos"), (d or {}).get("starpos")
    if not a or not b:
        return ""
    ly = math.dist(a, b)
    return "aquí" if ly < 0.01 else f"{ly:,.1f} al".replace(",", "X").replace(".", ",").replace("X", ".")

TRIP_SAVE = pygame.Rect(8, TOP + 2, 210, 34)
TRIP_PAGE = pygame.Rect(W - 118, TOP + 2, 110, 34)
TRIP_DEL = pygame.Rect(W - 130, H - 42, 122, 36)
TRIP_PER = 6
TAG_COL = {"EXOBIO": GREEN, "ESTACIÓN": BLUE, "A PIE": GREEN, "SRV": ORANGE, "ATERRIZADO": ORANGE,
           "PLANETA": ORANGE, "ESPACIO": DIM}

def trip_row(i):
    return pygame.Rect(8, TOP + 42 + i * 32, W - 16, 30)

def view_trip(surf, d, flags, now):
    trip["d"] = d
    L = trip["list"]
    draw_button(surf, TRIP_SAVE, "GUARDAR AQUÍ", None, F["btn"], filled=True, dim=not (d or {}).get("system"),
                lit=flash.get((128, "save"), 0) > now)
    pages = max(1, (len(L) + TRIP_PER - 1) // TRIP_PER)
    pg = trip["page"] % pages
    if pages > 1:
        draw_button(surf, TRIP_PAGE, f"PÁG {pg + 1}/{pages} >", None, F["small"])
    else:
        put(surf, F["small"], f"{len(L)} sitios", (W - 8, TOP + 12), DIM, anchor="topright")
    if not L:
        put(surf, F["btn"], "Aún no has guardado ningún sitio", (W // 2, (H + TOP) // 2 + 16), DIM, anchor="center")
        return
    for i, n in enumerate(L[pg * TRIP_PER:(pg + 1) * TRIP_PER]):
        r = trip_row(i)
        pygame.draw.rect(surf, DIM, r, 1, border_radius=4)
        put(surf, F["btn"], trip_label(n), (r.x + 6, r.y + 2), ORANGE, 290)
        tag = n.get("tag", "")
        put(surf, F["small"], tag, (r.right - 6, r.y + 3), TAG_COL.get(tag, DIM), anchor="topright")
        sub = f"{n.get('sys') or '?'}  ·  {time.strftime('%d/%m %H:%M', time.localtime(n.get('t', 0)))}"
        put(surf, F["small"], sub, (r.x + 6, r.y + 17), DIM, 330)
        put(surf, F["small"], trip_dist(n, d), (r.right - 6, r.y + 17), BLUE, anchor="topright")

def view_trip_detail(surf, d, flags, now):
    trip["d"] = d
    L, i = trip["list"], trip["sel"]
    if i is None or i >= len(L):
        ui["view"] = 128; return
    n = L[i]
    y = TOP + 4
    put(surf, F["big"], (n.get("sys") or "?").upper(), (8, y), ORANGE, W - 16); y += 28
    if n.get("st") or (n.get("body") and n.get("body") != n.get("sys")):
        put(surf, F["btn"], trip_label(n), (8, y), WHITE, W - 16); y += 22
    tag = n.get("tag", "")
    put(surf, F["small"], tag, (8, y), TAG_COL.get(tag, DIM))
    put(surf, F["small"], time.strftime("%d/%m/%Y %H:%M", time.localtime(n.get("t", 0))), (W - 8, y), DIM, anchor="topright"); y += 18
    if n.get("lat") is not None:
        put(surf, F["small"], f"lat {n['lat']:.4f}   lon {n['lon']:.4f}", (8, y), DIM); y += 18
    dist = trip_dist(n, d)
    if dist:
        put(surf, F["small"], "DISTANCIA", (8, y + 6), DIM)
        put(surf, F["big"], dist, (90, y), BLUE); y += 30
    b = (d or {}).get("bio") or {}
    here = (d or {}).get("body") and (d or {}).get("body") == n.get("body")
    if here and n.get("lat") is not None and b.get("lat") is not None and b.get("R"):
        p1, p2 = math.radians(b["lat"]), math.radians(n["lat"])
        dl = math.radians(n["lon"] - b["lon"])
        brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                      math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
        m = hav((b["lat"], b["lon"]), (n["lat"], n["lon"]), b["R"])
        cx, cy, r = 40, H - 40, 26
        pygame.draw.circle(surf, DIM, (cx, cy), r, 1)
        hdg = b.get("hdg")
        if hdg is not None:
            a = math.radians(brg - hdg)
            pt = lambda k, da: (cx + r * k * math.sin(a + da), cy - r * k * math.cos(a + da))
            pygame.draw.polygon(surf, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
        txt = f"{m / 1000:.1f} km".replace(".", ",") if m >= 1000 else f"{m:.0f} m"
        put(surf, F["small"], "DESTINO", (76, H - 64), DIM)
        put(surf, F["big"], txt, (76, H - 50), GREEN)
        put(surf, F["small"], f"rumbo {brg:.0f}°", (76, H - 22), ORANGE)
    c, until = ui["confirm"]
    sure = c == "trip_del" and time.time() < until
    draw_button(surf, TRIP_DEL, "¿SEGURO?" if sure else "BORRAR", None, F["btn"], filled=sure)

def tap_trip(x, y):
    v, d = ui["view"], trip["d"]
    L = trip["list"]
    if v == 128:
        if TRIP_SAVE.collidepoint(x, y):
            n = trip_here(d)
            if not n["sys"]:
                set_alert("SIN DATOS DEL JUEGO", secs=2); return
            L.insert(0, n); trip_save(); trip["page"] = 0
            tap_flash((128, "save"))
            set_alert("SITIO GUARDADO", trip_label(n), col=GREEN, secs=2, kind="ok")
            return
        pages = max(1, (len(L) + TRIP_PER - 1) // TRIP_PER)
        if pages > 1 and TRIP_PAGE.collidepoint(x, y):
            trip["page"] += 1; return
        pg = trip["page"] % pages
        for i in range(TRIP_PER):
            idx = pg * TRIP_PER + i
            if idx < len(L) and trip_row(i).collidepoint(x, y):
                trip["sel"] = idx; ui["view"] = 129; return
    elif v == 129 and TRIP_DEL.collidepoint(x, y):
        c, until = ui["confirm"]
        if c == "trip_del" and time.time() < until:
            ui["confirm"] = (None, 0)
            if trip["sel"] is not None and trip["sel"] < len(L):
                L.pop(trip["sel"]); trip_save()
            ui["view"] = 128
        else:
            ui["confirm"] = ("trip_del", time.time() + 3)

# ---------- 7.4 yacimientos: zonas de mineria del planeta (Rhino) y anillos ----------
RES_COL = {"PRÍSTINAS": GREEN, "MAYORES": GREEN, "COMUNES": ORANGE, "BAJAS": RED, "AGOTADAS": RED}

def view_rings(surf, d, flags, now):
    R = (d or {}).get("rings") or {}
    if not R.get("planet"):
        put(surf, F["btn"], "Acércate a un planeta", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    y = TOP + 4
    put(surf, F["big"], R["planet"].upper(), (8, y), ORANGE, W - 150)
    if R.get("reserve"):
        put(surf, F["small"], "RESERVAS", (W - 8, y), DIM, anchor="topright")
        put(surf, F["btn"], R["reserve"], (W - 8, y + 12), RES_COL.get(R["reserve"], ORANGE), anchor="topright")
    y += 34
    sig = R.get("signals") or []
    put(surf, F["small"], "SEÑALES DEL PLANETA", (8, y), DIM); y += 15
    if not sig:
        put(surf, F["small"], "sin datos: escanea el planeta (FSS) o mapéalo con la sonda (DSS)", (8, y), DIM, W - 16); y += 20
    else:
        x = 8
        for name, c in sig:
            low = name.lower()
            col = GREEN if ("bio" in low) else BLUE if ("geo" in low) else ORANGE
            txt = f"{name} x{c}"
            w_ = F["btn"].size(txt)[0] + 14
            if x + w_ > W - 6:
                x = 8; y += 24
            pygame.draw.rect(surf, col, (x, y, w_ - 4, 21), 1, border_radius=4)
            put(surf, F["btn"], txt, (x + 5, y + 2), col)
            x += w_
        y += 28
    rings = R.get("rings") or []
    if not rings:
        return
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
    here = R.get("here") or ""
    for name, cls, hs in rings:
        if y > H - 40:
            break
        inside = bool(here) and here.endswith(name)
        r = pygame.Rect(6, y, W - 12, 26 + 20 * max(1, (len(hs or []) + 1) // 2))
        pygame.draw.rect(surf, GREEN if inside else DIM, r, 1, border_radius=5)
        put(surf, F["btn"], name.upper(), (r.x + 8, r.y + 4), ORANGE, 110)
        put(surf, F["small"], cls, (r.x + 120, r.y + 8), BLUE, 160)
        if inside:
            put(surf, F["small"], "ESTÁS AQUÍ", (r.right - 8, r.y + 8), GREEN, anchor="topright")
        yy = r.y + 26
        if not hs:
            put(surf, F["small"], "sin sondear: usa la sonda de superficie en el anillo", (r.x + 8, yy + 2), DIM, r.w - 16)
        else:
            for k, (m, c) in enumerate(hs):
                put(surf, F["btn"], f"{m}  x{c}", (r.x + 8 + (k % 2) * (r.w // 2), yy + (k // 2) * 20),
                    GREEN if c >= 2 else WHITE, r.w // 2 - 12)
        y = r.bottom + 6

# ---------- 3 navegacion: ficha del destino dentro del sistema ----------
