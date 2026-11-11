# Panel Elite v1.1 · parte 10: radar colonizacion viajes (lineas 9047-9813 del panel entero)
# ---------- v1.0 beta 11 ----------
# --- tick del BGS de tu sistema principal (EDCAS; id64 de EDSM), cada 30 min ---
FTICK = {"sys": None, "addr": {}, "next": None, "win": 0, "last": None, "t": 0}

def ftick_loop():
    import urllib.request, urllib.parse, datetime
    def iso(x):
        try:
            return datetime.datetime.fromisoformat((x or "").replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": "PanelEliteRPi/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode() or "null")
    time.sleep(30)
    while True:
        try:
            D, S, gap = fac_rows()
            ctl = sorted([v for v in S if v.get("ctrl")], key=lambda v: -v["inf"])
            if ctl:
                n = ctl[0]["sys"]
                a = FTICK["addr"].get(n)
                if not a:
                    j = get("https://www.edsm.net/api-v1/system?" + urllib.parse.urlencode({"systemName": n, "showId": 1}))
                    a = (j or {}).get("id64")
                    if a:
                        FTICK["addr"][n] = a
                if a:
                    p = get(f"https://edservertick.de/api/v1/systems/{a}/tick-prediction")
                    FTICK.update(sys=n, next=iso((p or {}).get("next_tick")), win=(p or {}).get("window_minutes") or 0,
                                 last=iso((p or {}).get("last_tick")), t=time.time())
        except Exception as e:
            FTICK["err"] = str(e)[:50]
        time.sleep(1800)

threading.Thread(target=ftick_loop, daemon=True, name="tick-faccion").start()

def ftick_txt(now):
    n = FTICK.get("next")
    if not n:
        return None, DIM
    w = (FTICK.get("win") or 0) * 60
    hm = lambda s_: f"{int(s_ // 3600)} h {int(s_ % 3600 // 60):02d} min"
    if now < n - w:
        return "tick en " + hm(n - w - now), BLUE
    if now < n + w:
        return "TICK EN CURSO", GREEN
    return "tick: esperando", DIM

# --- radar: zoom, expansion y resumen ---
RZ = {"z": 1, "cx": 0.0, "cz": 0.0, "seen": 0}
RADAR_R = pygame.Rect(6, 56, 200, 200)
ZB = [pygame.Rect(RADAR_R.right - 42, RADAR_R.bottom - 20, 19, 17), pygame.Rect(RADAR_R.right - 21, RADAR_R.bottom - 20, 19, 17)]
RGEO = {}

def exp_target(D, v):
    """Destino probable de una expansion desde v: el sistema conocido mas cercano (< 30 al) donde no esta tu faccion."""
    if not v.get("pos") or None in v["pos"]:
        return None
    mine = {n for n, x in (D.get("sistemas") or {}).items() if x.get("inf") and not x.get("fuera")}
    cand = []
    for n, z in (D.get("zona") or {}).items():
        if n not in mine and z.get("pos") and None not in z["pos"]:
            cand.append((n, z["pos"]))
    for n, x in (D.get("sistemas") or {}).items():
        if x.get("fuera") and x.get("pos") and None not in x["pos"]:
            cand.append((n, x["pos"]))
    best = None
    for n, p in cand:
        dd = math.dist(p, v["pos"])
        if dd < 30 and (best is None or dd < best[0]):
            best = (dd, n, p)
    return best

def day_summary(S):
    hoyk = time.strftime("%Y-%m-%d", time.gmtime())
    cm = sum(((v.get("trafico") or {}).get(hoyk, 0)) for v in S)
    zc = sum(1 for v in S for z in (v.get("zc") or []) if time.time() - (z.get("t") or 0) < 86400)
    pn = sum(1 for v in S for x in (v.get("pn") or {}).values() if time.time() - (x.get("t") or 0) < 86400)
    return cm, zc, pn

def draw_fac_screen_b11(surf, now):
    D, S, gap = fac_rows()
    if now - RZ["seen"] > 3:                            # no se estaba viendo: vuelve a x1
        RZ.update(z=1, cx=0.0, cz=0.0)
    RZ["seen"] = now
    surf.fill(BLACK)
    for x in range(0, W, 24):
        pygame.draw.line(surf, (14, 9, 3), (x, 0), (x, H))
    for y in range(0, H, 24):
        pygame.draw.line(surf, (14, 9, 3), (0, y), (W, y))
    blink = int(now * 2) % 2
    # cabecera: nombre, resumen con el ultimo piloto, hora y tick
    if not blit_logo(surf, pygame.Rect(4, 2, 46, 46)):
        shield(surf, 26, 24, ORANGE)
    put(surf, F["big"], (D.get("faccion") or "").upper(), (56, 6), ORANGE, W - 190)
    nctl = sum(1 for v in S if v.get("ctrl"))
    med = sum(v["inf"] for v in S) / len(S)
    tmax = max([v.get("t") or 0 for v in S] or [0])
    a_txt, a_col = fac_age(tmax)
    t1 = f"{nctl} de {len(S)} controlados · media {med:.1f} % · ".replace(".", ",", 1)
    x_ = put(surf, F["small"], t1, (56, 32), DIM, W - 120)
    put(surf, F["small"], "último piloto " + a_txt, (56 + x_, 32), a_col, W - 120 - x_)
    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 56, 6), ORANGE, anchor="topright")
    tk, tkc = ftick_txt(now)
    if tk:
        put(surf, F["tiny"], tk, (W - 56, 20), tkc, anchor="topright")
    pygame.draw.line(surf, ORANGE, (6, 50), (W - 6, 50), 1)
    # radar
    R = RADAR_R; c = R.center; rad = 96
    blit_logo(surf, pygame.Rect(c[0] - 85, c[1] - 85, 170, 170), dark=40)
    for k in (1, 2, 3):
        pygame.draw.circle(surf, (40, 26, 8), c, rad * k // 3, 1)
    pygame.draw.line(surf, (40, 26, 8), (c[0] - rad, c[1]), (c[0] + rad, c[1]))
    pygame.draw.line(surf, (40, 26, 8), (c[0], c[1] - rad), (c[0], c[1] + rad))
    ang = math.radians((now * 60) % 360)
    for k in range(28):
        a = ang - math.radians(k * 1.4)
        f_ = (1 - k / 28) * 0.5
        pygame.draw.line(surf, (int(255 * f_), int(140 * f_), 0), c, (c[0] + rad * math.cos(a), c[1] + rad * math.sin(a)), 2)
    ps = [v for v in S if v.get("pos") and None not in v["pos"]]
    used = []
    RADAR_PTS.clear()
    z = RZ["z"]
    if ps:
        ctl_ = [v for v in ps if v.get("ctrl")] or ps
        mx = sum(v["pos"][0] for v in ctl_) / len(ctl_); mz = sum(v["pos"][2] for v in ctl_) / len(ctl_)
        ext = sorted(max(abs(v["pos"][0] - mx), abs(v["pos"][2] - mz)) for v in ps)
        ext = (ext[int(len(ext) * 0.9)] if len(ext) > 3 else ext[-1]) or 1
        RGEO.update(mx=mx, mz=mz, ext=ext)

        def to_px(p, clamp=True):
            dx, dz = ((p[0] - mx) / ext - RZ["cx"]) * z, ((p[2] - mz) / ext - RZ["cz"]) * z
            d_ = math.hypot(dx, dz)
            if d_ > 1:
                if not clamp or z > 1:
                    return None
                dx, dz = dx / d_, dz / d_
            return int(c[0] + dx * rad * 0.88), int(c[1] - dz * rad * 0.88)

        for v in sorted(ps, key=lambda v: (fac_war(v), v.get("ctrl"))):
            p_ = to_px(v["pos"])
            if not p_:
                continue
            px, py = p_
            RADAR_PTS.append((px, py, v["sys"]))
            war = fac_war(v)
            r = 3 + int(v["inf"] / 18)
            hoy = traf(v)[0] or 0
            if hoy:                                     # halo de trafico: mas grande cuantos mas comandantes hoy
                hr = r + 3 + min(9, hoy * 2)
                pygame.draw.circle(surf, (20, 45, 70), (px, py), hr)
                pygame.draw.circle(surf, (50, 110, 160), (px, py), hr, 1)
            if v.get("ctrl"):
                for g in range(3):
                    pygame.draw.circle(surf, (90 - g * 25, 50 - g * 15, 0), (px, py), r + 6 - g * 2)
            pygame.draw.circle(surf, RED if war else ORANGE if v.get("ctrl") else (150, 150, 150), (px, py), r)
            if war and blink:
                pygame.draw.circle(surf, RED, (px, py), r + 6, 1)
            if now - (v.get("t") or 0) < 3600:          # recien visitado: anillo blanco que late
                k_ = (now * 1.5) % 1
                pygame.draw.circle(surf, tuple(int(255 * (1 - k_)) for _ in range(3)), (px, py), int(r + 3 + k_ * 10), 1)
            if v.get("ctrl") or war or z > 1:
                nm = v["sys"].upper()
                nm = nm if len(nm) <= 12 else nm[:11] + "…"
                tw = tw_(F["tiny"], nm)
                lr = pygame.Rect(px + r + 3, py - 7, tw, 12)
                if lr.right > R.right:
                    lr.right = px - r - 3
                if R.contains(lr) and not any(lr.colliderect(u) for u in used):
                    used.append(lr)
                    put(surf, F["tiny"], nm, lr.topleft, RED if war else (230, 170, 90) if v.get("ctrl") else (170, 170, 170))
    put(surf, F["tiny"], "MAPA" if z == 1 else f"MAPA x{z}", (R.x + 4, R.bottom - 14), DIM)
    for i, b in enumerate(ZB):
        pygame.draw.rect(surf, BLACK, b, border_radius=3)
        pygame.draw.rect(surf, ORANGE if (i == 0 and z < 8) or (i == 1 and z > 1) else DIM, b, 1, border_radius=3)
        put(surf, F["small"], "+" if i == 0 else "−", b.center, ORANGE if (i == 0 and z < 8) or (i == 1 and z > 1) else DIM, anchor="center")
    # alertas
    X, y = 214, 58
    war = [v for v in S if fac_war(v)] + [v for v in S if not fac_war(v) and inf_warn(v)]
    if war:
        box = pygame.Rect(X, y, W - X - 6, 18 + min(4, len(war)) * 30)
        pygame.draw.rect(surf, (30, 0, 0), box, border_radius=6)
        pygame.draw.rect(surf, RED if blink else (120, 0, 0), box, 2, border_radius=6)
        put(surf, F["small"], "ALERTAS", (X + 8, y + 3), RED)
        yy = y + 18
        for v in war[:4]:
            ALR.append((pygame.Rect(X, yy - 2, box.w, 30), v["sys"]))
            if not fac_war(v):
                t1_, t2_ = inf_warn(v)
                put(surf, F["small"], t1_ + " · " + v["sys"], (X + 8, yy), WHITE, box.w - 16)
                put(surf, F["tiny"], t2_, (X + 8, yy + 14), ORANGE, box.w - 16)
                yy += 30; continue
            cf = (v.get("conflictos") or [{}])[0]
            t = tipo_es(cf.get("tipo") or next((x for x in (v.get("activos") or []) + (v.get("pendientes") or []) if x in ("War", "CivilWar", "Election")), "war"))
            put(surf, F["small"], f"{t} · {v['sys']}", (X + 8, yy), WHITE, box.w - 16)
            put(surf, F["tiny"], f"contra {cf.get('contra') or '?'} · {cf.get('ganados') or 0}-{cf.get('perdidos') or 0} días", (X + 8, yy + 14), RED, box.w - 16)
            yy += 30
        y = box.bottom + 8
    put(surf, F["small"], "SISTEMAS CONTROLADOS", (X, y), DIM); y += 16
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
    first_ = int(off_ // 14)
    for v in ctl_[first_:first_ + vis_n]:
        if y + 14 > H - 44:
            break
        CTL_ROWS.append((pygame.Rect(X, y, W - X - 8, 14), v["sys"]))
        g = gap(v)
        put(surf, F["tiny"], v["sys"].upper(), (X, y), ORANGE, 110)
        bx = pygame.Rect(X + 112, y + 3, 90, 8); pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, ORANGE, (bx.x + 1, bx.y + 1, int(88 * min(100, v["inf"]) / 100), 6))
        put(surf, F["tiny"], f"{v['inf']:.0f}%", (W - 8, y), GREEN if g >= 5 else RED, anchor="topright")
        trend_arrow(surf, v, W - 44, y + 3)
        y += 14
    # resumen del dia
    cm, zc, pn = day_summary(S)
    put(surf, F["small"], f"HOY: {cm} comandante{'s' if cm != 1 else ''} · {zc} ZC · {pn} portanave{'s' if pn != 1 else ''}",
        (X, H - 40), WHITE if cm or zc or pn else DIM, W - X - 8)
    # cinta con los estados
    pygame.draw.line(surf, ORANGE, (6, H - 24), (W - 6, H - 24), 1)
    segs = []
    for v in S:
        parts = fac_parts(v)
        hoy, media, alto = traf(v)
        if alto:
            parts = parts + [(f"TRÁFICO ALTO {hoy} cmdr", RED)]
        if parts:
            segs.append((v["sys"].upper() + ": ", ORANGE))
            for i, (t, col) in enumerate(parts):
                segs.append(((", " if i else "") + t, col))
            segs.append(("     ·     ", DIM))
    if segs:
        total = sum(tw_(F["small"], t) for t, c in segs) or 1
        x0 = 8 - int((now * 40) % total)
        old = surf.get_clip(); surf.set_clip(pygame.Rect(0, H - 22, W, 22))
        x = x0
        while x < W:
            for t, col in segs:
                w_ = tw_(F["small"], t)
                if x + w_ > 0 and x < W:
                    put(surf, F["small"], t, (x, H - 20), col)
                x += w_
        surf.set_clip(old)
    else:
        put(surf, F["small"], "sin estados especiales en tus sistemas", (W // 2, H - 12), DIM, anchor="center")

draw_fac_screen = draw_fac_screen_b11

def radar_tap(x, y):
    """Toques en el radar: zoom + / -, y con zoom tocar una zona vacia la centra. True si lo ha usado."""
    for i, b in enumerate(ZB):
        if b.inflate(6, 6).collidepoint(x, y):
            if i == 0 and RZ["z"] < 8:
                RZ["z"] *= 2
            elif i == 1 and RZ["z"] > 1:
                RZ["z"] //= 2
                if RZ["z"] == 1:
                    RZ.update(cx=0.0, cz=0.0)
            TAP_EV.set(); return True
    c = RADAR_R.center
    if RZ["z"] > 1 and math.hypot(x - c[0], y - c[1]) < 96 and not radar_hit(x, y):
        k = 96 * 0.88 * RZ["z"]
        RZ["cx"] += (x - c[0]) / k
        RZ["cz"] -= (y - c[1]) / k
        TAP_EV.set(); return True
    return False

# --- VIAJES: boton + (acerca sobre el centro del mapa) ---
def vj_btn(i):
    return pygame.Rect(4 + i * 67, H - 28, 63, 25)


def view_viajes(surf, d, flags, now):
    view_viajes_base(surf, d, flags, now)
    Z = ui.get("vjzoom")
    draw_button(surf, vj_btn(6), "+", "", F["small"], compact=True, dim=bool(Z and Z[0] >= 64))

VIEWS[190] = view_viajes

def vj_plus():
    A, pt, sc = VJT.get("A"), VJT.get("pt"), VJT.get("sc")
    if not (A and sc):
        return
    c0 = pt(0, 0)
    wx, wz = (A.centerx - c0[0]) / sc, -(A.centery - c0[1]) / sc
    Z = ui.get("vjzoom")
    f_ = (Z[0] if Z else 1) * 2
    if f_ <= 64:
        ui["vjzoom"] = (f_, wx, wz)

# --- numero de aviso: esquina de cada aviso; tocarlo lleva a su linea en ALERTAS ---
class _XA(dict):
    def __setitem__(self, k, v):
        if k == "a" and isinstance(v, dict) and "ev" not in v and XA_K[0]:
            v["ev"] = XA_K[0]
        super().__setitem__(k, v)

xa = _XA(xa)
NUMB = {"r": None, "ev": None}

def ev_num(k):
    for i, (k_, _) in enumerate(EV_LIST):
        if k_ == k:
            return i + 1
    return None

def draw_num(surf, box, k):
    n = ev_num(k) if k else None
    if not n:
        return
    lab = f"#{n}"
    r = pygame.Rect(box.right - tw_(F["tiny"], lab) - 14, box.y + 5, tw_(F["tiny"], lab) + 8, 14)
    pygame.draw.rect(surf, BLACK, r, border_radius=3)
    pygame.draw.rect(surf, DIM, r, 1, border_radius=3)
    put(surf, F["tiny"], lab, r.center, DIM, anchor="center")
    NUMB.update(r=r.inflate(16, 12), ev=k, t=time.time())





def num_tap(x, y):
    r = NUMB.get("r")
    if not r or time.time() - NUMB.get("t", 0) > 0.6 or not r.collidepoint(x, y):
        return False
    n = ev_num(NUMB["ev"])
    ui["alert"] = None; xa["a"] = None
    ui["view"] = 161; ui["evpage"] = (n - 1) // EVPP; ui["idle_skip"] = time.time() + 60
    flash[(161, (n - 1) % EVPP)] = time.time() + 4      # su boton se ilumina unos segundos
    NUMB["r"] = None; TAP_EV.set()
    return True

# --- COLONIZACION: pestana COLONIA en CARGA/MISION (datos del sender v1.0b7) ---
MENU[135] = "COLONIZACIÓN"
TABS[1].append((135, "COLONIZACIÓN"))
AUTO_LIST.append(("colonia", "DEPÓSITO DE CONSTRUCCIÓN > COLONIA"))
COLA = {"dock": None, "pend": 0}
COL_HEAD = pygame.Rect(0, TOP, W, 34)
COL_ROWS = 13

def col_pick(d):
    C = (d or {}).get("colonia") or {}
    L = C.get("list") or []
    if not L:
        return C, L, None
    sel = ui.get("colsel")
    if sel is None:
        sel = next((i for i, x in enumerate(L) if x.get("mid") == C.get("dock")), 0)
    return C, L, sel % len(L)



_view_market_b11 = VIEWS[127]

def view_market_b11(surf, d, flags, now):
    _view_market_b11(surf, d, flags, now)
    mk = (d or {}).get("market") or {}
    L = mk.get("col") or []
    try:
        m_ = market_pick(d, now)
        if m_.get("missing") or m_.get("src") == "EDSM" or m_.get("other"):
            return                                       # se esta viendo otro mercado
    except Exception:
        pass
    if not L:
        return
    n = min(4, len(L))
    box = pygame.Rect(6, H - 44 - 18 - n * 14, W - 12, 18 + n * 14)
    pygame.draw.rect(surf, (0, 28, 8), box, border_radius=5)
    pygame.draw.rect(surf, GREEN, box, 1, border_radius=5)
    put(surf, F["small"], "PARA TU COLONIA (se vende aquí)" + (f"  +{len(L) - n} más en COLONIZACIÓN" if len(L) > n else ""), (box.x + 6, box.y + 2), GREEN, box.w - 12)
    yy = box.y + 18
    for name, stock, price, need in (r_[:4] for r_ in L[:n]):
        put(surf, F["tiny"], name, (box.x + 8, yy), GREEN, 170)
        put(surf, F["tiny"], f"hay {stock:,} t · {price:,} cr".replace(",", "."), (box.x + 190, yy), WHITE, 150)
        put(surf, F["tiny"], f"faltan {need:,} t".replace(",", "."), (box.right - 8, yy), ORANGE, anchor="topright")
        yy += 14

VIEWS[127] = view_market_b11

# --- render: abre COLONIA al atracar en un deposito ---


# --- toques ---



# ---------- v1.0 beta 12 ----------
# --- COLONIZACION: se abre sola (una vez por atraque) ---
COLB = {"done": set(), "t": None}

def col_auto(d, now):
    C = (d or {}).get("colonia") or {}
    L = C.get("list") or []
    fl = (d or {}).get("Flags", 0)
    docked = bool(fl & 1) or bool(fl & 2)                # atracado o posado
    if not docked:
        COLB["done"].clear()
    newest = max((x.get("t") or 0 for x in L), default=0)
    why = key = None
    if C.get("dock") and docked and C["dock"] not in COLB["done"]:
        why, key = "atracado en un depósito", C["dock"]
    elif COLB["t"] is not None and newest > COLB["t"] and docked and L and L[0].get("mid") not in COLB["done"]:
        why, key = "datos nuevos del depósito", L[0].get("mid")
    COLB["t"] = newest if COLB["t"] is None else max(COLB["t"], newest)
    if why:
        COLB["done"].add(key)
        if auto_on("colonia") and not ui.get("idle_on"):
            COLB["pend"] = (now + 3, why)                # b12b: despues de que se asiente el atraque
        else:
            plog("Colonización: no la abro (" + why + "; cambio auto apagado o en espera)")



# --- ficha del sistema: destino probable de la expansion ---
_ficha_b12 = VIEWS[194]

def ficha_b12(surf, d, flags, now):
    _ficha_b12(surf, d, flags, now)
    D, name, v = fs_get()
    if not v or "Expansion" not in (v.get("activos") or []) + (v.get("pendientes") or []):
        return
    bad = [st for st in (v.get("activos") or []) + (v.get("pendientes") or []) if st in TIPS and st not in ST_GOOD][:2]
    y = H - 44 + 15 + 13 * len(bad)
    if y > H - 14:
        return
    tg = exp_target(D or FACD["data"] or {}, v)
    txt = (f"EXPANSIÓN · destino probable: {tg[1]} (a {tg[0]:.1f} al)".replace(".", ",") if tg
           else "EXPANSIÓN · destino desconocido (ningún sistema conocido a menos de 30 al)")
    put(surf, F["tiny"], txt, (100, y), BLUE, W - 104)

VIEWS[194] = ficha_b12

# --- ALERTAS y SONIDO: numero pequeno en cada boton (el mismo #n que sale en el aviso) ---

def view_evlist(surf, d, flags, now):
    v = ui["view"]
    if v not in (161, 163):
        return view_evlist_base(surf, d, flags, now)
    L, st, pk = _evl(v)
    pages = (len(L) + EVPP - 1) // EVPP
    pg = ui.get(pk, 0) % pages
    on = cfg.get(st) or {}
    df = EVL[v][4]
    n = sum(1 for k, _ in L if on.get(k, df.get(k, True)))
    top = [("TODOS ON", None), ("TODOS OFF", None), (f"PÁG {pg + 1}/{pages}" if pages > 1 else f"{n} de {len(L)}", None)]
    for i, (t, _) in enumerate(top):
        draw_button(surf, grid(i, 3, 1, TOP, TOP + 40), t, None, F["btn"], lit=flash.get((v, 100 + i), 0) > now)
    for i, (k, name) in enumerate(L[pg * EVPP:(pg + 1) * EVPP]):
        r = grid(i, 2, 6, TOP + 38, H)
        lit = flash.get((v, i), 0) > now
        fill = on.get(k, df.get(k, True))
        if fill or lit:
            pygame.draw.rect(surf, WHITE if lit else ORANGE, r, border_radius=6)
        else:
            pygame.draw.rect(surf, ORANGE, r, 2, border_radius=6)
        col = BLACK if fill or lit else ORANGE
        lab = str(pg * EVPP + i + 1)
        put(surf, F["tiny"], lab, (r.x + 6, r.centery), col, anchor="midleft")
        x0 = r.x + 10 + tw_(F["tiny"], "00")
        put(surf, F["small"] if len(name) > 17 else F["btn"], name, ((x0 + r.right - 4) // 2, r.centery), col, r.right - 4 - x0, anchor="center")

VIEWS[161] = VIEWS[163] = view_evlist

# ---------- v1.0 beta 12b: COLONIZACION gana al cambio automatico de ESTACION ----------
COLB.setdefault("pend", None)
COLB.setdefault("hold", 0)







# ---------- v1.0 beta 12c: modo COLONIZACION en la pantalla grande (4 CUADROS) ----------
BIG_SETS["COLONIZACIÓN"] = [135, 100, 127, 8]


BIGCOL = {"m": None}

# ---------- v1.0 beta 13: COLONIZACION con bodega, filtros y EN EL SISTEMA ----------
EV_LIST.append(("colentrega", "COLONIA: CARGA POR ENTREGAR"))
COLF = [("todo", "TODO"), ("aqui", "AQUÍ"), ("sis", "EN EL SISTEMA")]
COLF_R = [pygame.Rect(W - 90 - 4 - 56 - 4 - 50, TOP + 2, 50, 18), pygame.Rect(W - 90 - 4 - 56, TOP + 2, 56, 18),
          pygame.Rect(W - 90, TOP + 2, 86, 18)]
COL_HEAD = pygame.Rect(0, TOP, COLF_R[0].x - 4, 22)
COLROWS = []                                             # (rect, nombre de estacion) en EN EL SISTEMA
MKBOX = {"r": None}

def col_rows(d, x):
    """Cada mercancia: (nombre, clave, pedido, entregado, en bodega util, falta de verdad)."""
    carg = {}
    for n, c in ((d or {}).get("cargo") or []):          # por nombre (sender antiguo): el depósito los corta a 26 letras
        carg[(n or "").lower()[:26]] = carg.get((n or "").lower()[:26], 0) + c
    ck = (d or {}).get("cargok")                         # v1.1 (sender b13): por nombre interno, vale para todos
    out = []
    for r in x.get("res") or []:
        name, req, prov = r[0], r[1], r[2]
        key = r[3] if len(r) > 3 else ""
        pend = max(0, req - prov)
        if not pend:
            continue
        have = ck.get(key, 0) if isinstance(ck, dict) and key else carg.get((name or "").lower()[:26], 0)
        inb = min(have, pend)
        out.append((name, key, req, prov, inb, pend - inb))
    out.sort(key=lambda t: (t[5] == 0, -t[5], -t[4]))
    return out


def col_sys_state(d, rows):
    S = (d or {}).get("colsys") or {}
    off = S.get("off") or {}
    hit = [t for t in rows if t[5] > 0 and off.get(t[1])]
    if not S or S.get("status", "").startswith("consultando") or not S.get("status"):
        return S, off, hit, DIM
    return S, off, hit, GREEN if hit else RED

def _hace(sec):
    return "?" if sec is None or sec < 0 else "ahora" if sec < 60 else f"{int(sec // 60)} min" if sec < 3600 else f"{sec / 3600:.0f} h" if sec < 172800 else f"{sec / 86400:.0f} días"

def view_colonia(surf, d, flags, now):
    C, L, i = col_pick(d)
    COLROWS.clear()
    if not L:
        if d and "colonia" not in d:
            put(surf, F["btn"], "actualiza el sender a la v1.0b9", (W // 2, H // 2 - 10), ORANGE, W - 16, anchor="center")
        else:
            put(surf, F["btn"], "sin construcciones", (W // 2, H // 2 - 12), DIM, anchor="center")
            put(surf, F["small"], "atraca en un depósito de construcción y abre su mercado", (W // 2, H // 2 + 12), DIM, W - 16, anchor="center")
        return
    x = L[i]
    rows = col_rows(d, x)
    here = col_here(d)
    S, off, hit, scol = col_sys_state(d, rows)
    f = ui.get("colf", "todo")
    # cabecera: nombre (tocar = otra construccion) y filtros
    y = TOP + 3
    nm = (x.get("st") or "CONSTRUCCIÓN").upper() + (" · " + x["sys"] if x.get("sys") else "")
    w_ = put(surf, F["btn"], nm, (8, y), ORANGE, COLF_R[0].x - 60)
    if len(L) > 1:
        put(surf, F["tiny"], f"{i + 1}/{len(L)} >", (14 + w_, y + 4), BLUE)
    for k, (fk, lab) in enumerate(COLF):
        r = COLF_R[k]
        sel = f == fk
        col = scol if fk == "sis" else ORANGE
        pygame.draw.rect(surf, col if sel else BLACK, r, border_radius=4)
        pygame.draw.rect(surf, col, r, 1, border_radius=4)
        put(surf, F["tiny"], lab, r.center, BLACK if sel else col, r.w - 4, anchor="center")
    y += 21
    # progreso
    bar = pygame.Rect(8, y, W - 16, 11)
    pygame.draw.rect(surf, DIM, bar, 1)
    pygame.draw.rect(surf, GREEN if x.get("done") else ORANGE, (bar.x + 1, bar.y + 1, int((bar.w - 2) * min(100, x.get("prog") or 0) / 100), bar.h - 2))
    st_ = "COMPLETADA" if x.get("done") else "FALLIDA" if x.get("fail") else f"{x.get('prog', 0):.1f} %".replace(".", ",")
    put(surf, F["tiny"], st_, bar.center, WHITE, anchor="center")
    y += 14
    falta = sum(t[5] for t in rows)
    bod = sum(t[4] for t in rows)
    cap = (d or {}).get("cargocap") or 0
    t_ = f"FALTAN {falta:,} t".replace(",", ".") + (f" · ~{-(-falta // cap)} viajes de {cap} t" if cap and falta else "")
    xx = put(surf, F["small"], t_, (8, y), WHITE if falta else GREEN, W - 16)
    if bod:
        put(surf, F["small"], f" · {bod:,} t en bodega por entregar".replace(",", "."), (8 + xx, y), BLUE, W - 24 - xx)
    y += 16
    cw = (W - 16) // 2
    if f == "todo":
        pages = max(1, (len(rows) + 25) // 26)
        pg = ui.get("colpg", 0) % pages
        vis = rows[pg * 26:(pg + 1) * 26]
        nrow = max(1, (len(vis) + 1) // 2)
        for k, (name, key, req, prov, inb, real) in enumerate(vis):
            cx, cy = 8 + (k // nrow) * (cw + 4), y + (k % nrow) * 14
            sold = _hh(here, name, key) is not None and real > 0
            col = BLUE if real == 0 else GREEN if sold else ORANGE
            put(surf, F["tiny"], ("• " if sold else "") + name, (cx, cy), col, 96)
            b = pygame.Rect(cx + 100, cy + 3, 40, 7)
            pygame.draw.rect(surf, DIM, b, 1)
            w1 = int(38 * prov / req) if req else 0
            w2 = int(38 * inb / req) if req else 0
            pygame.draw.rect(surf, ORANGE, (b.x + 1, b.y + 1, w1, 5))
            if w2:
                pygame.draw.rect(surf, BLUE, (b.x + 1 + w1, b.y + 1, min(w2, 38 - w1), 5))
            if real == 0:
                put(surf, F["tiny"], f"{inb:,} en bodega".replace(",", "."), (cx + cw - 4, cy), BLUE, anchor="topright")
            else:
                xr = put(surf, F["tiny"], f"{real:,}".replace(",", "."), (cx + cw - 4, cy), col, anchor="topright")
                if inb:
                    put(surf, F["tiny"], f"+{inb:,}".replace(",", "."), (cx + cw - 8 - tw_(F["tiny"], f"{real:,}".replace(",", ".")), cy), BLUE, anchor="topright")
        foot = f"pág {pg + 1}/{pages} · " if pages > 1 else ""
        put(surf, F["tiny"], foot + "verde = se vende aquí · azul = en tu bodega · naranja = falta", (8, H - 14), DIM, W - 16)
    elif f == "aqui":
        mk = (d or {}).get("market") or {}
        vis = [t for t in rows if t[5] > 0 and _hh(here, t[0], t[1]) is not None]
        src = COLHS.get("src")
        stn = (COLHS.get("st") or "ESTA ESTACIÓN").upper()
        if not src:
            put(surf, F["small"], "atraca y abre el mercado para ver qué se vende aquí", (W // 2, y + 40), DIM, W - 16, anchor="center")
        elif not vis:
            put(surf, F["btn"], "aquí no se vende nada de lo que falta", (W // 2, y + 40), RED, W - 16, anchor="center")
        lab = f"EN {stn}" + (" · datos del juego" if src == "juego" else
                             " · según EDSM" + (f", hace {_hace(now - COLHS['mt'])}" if COLHS.get("mt") else "") + " · abre el mercado para ver precios exactos" if src == "EDSM" else "")
        put(surf, F["tiny"], lab, (8, y), DIM if src != "EDSM" else BLUE, W - 16); y += 14
        for name, key, req, prov, inb, real in vis[:13]:
            r_ = _hh(here, name, key)
            put(surf, F["small"], name, (8, y), GREEN, 170)
            put(surf, F["small"], f"hay {r_[1]:,} t · {r_[2]:,} cr".replace(",", "."), (184, y), WHITE, 170)
            put(surf, F["small"], f"faltan {real:,} t".replace(",", "."), (W - 8, y), ORANGE, anchor="topright")
            y += 15
    else:
        st = S.get("status") or ""
        info = (f"{S.get('sys')}: " if S.get("sys") else "") + (
            f"{S.get('n', 0)} mercados en EDSM · consultado hace {_hace(now - (S.get('t') or now))}" if st == "ok" else st or "entra en un sistema con la construcción sin terminar")
        put(surf, F["tiny"], info, (8, y), DIM, W - 16); y += 14
        vis = [t for t in rows if t[5] > 0]
        if st == "ok" and not hit:
            put(surf, F["btn"], "en este sistema no se vende nada de lo que falta", (W // 2, y + 40), RED, W - 16, anchor="center")
        per = max(1, (H - 18 - y) // 28)                 # las que quepan sobre el pie
        pages = max(1, (len(hit) + per - 1) // per)
        pg = ui.get("colpg", 0) % pages
        for name, key, req, prov, inb, real in hit[pg * per:(pg + 1) * per]:
            o = next((q for q in off[key] if not q[5] or now - q[5] < 30 * 86400), off[key][0])   # mejor uno reciente
            stn, stock, price, dist, pad, mt, fc = o[0], o[1], o[2], o[3], o[4], o[5], o[6]
            put(surf, F["small"], name, (8, y), GREEN, 220)
            put(surf, F["small"], f"faltan {real:,} t".replace(",", "."), (W - 8, y), ORANGE, anchor="topright")
            line = (f"→ {stn}" + (" (PORTANAVES)" if fc else "") + f" · {stock:,} t · {price:,} cr · {dist:,} ls · pad {pad}".replace(",", ".")
                    + (f" · hace {_hace(now - mt)}" if mt else ""))
            old_ = bool(mt) and now - mt > 30 * 86400
            put(surf, F["tiny"], line.replace("→", ">") + (" · DATO ANTIGUO" if old_ else ""), (16, y + 14), DIM if old_ else WHITE, W - 24)
            COLROWS.append((pygame.Rect(0, y, W, 27), stn))
            y += 28
        put(surf, F["tiny"], (f"pág {pg + 1}/{pages} · " if pages > 1 else "") + "toca una fila: copia la estación al portapapeles del PC · abajo: página",
            (8, H - 14), DIM, W - 16)

VIEWS[135] = view_colonia

# --- MERCADO: recuadro verde con lo que falta de verdad (descontando la bodega); tocarlo abre COLONIZACION > AQUI ---
def view_market_b13(surf, d, flags, now):
    _view_market_b11(surf, d, flags, now)              # el MERCADO sin el recuadro de la b11
    MKBOX["r"] = None
    mk = (d or {}).get("market") or {}
    try:
        m_ = market_pick(d, now)
        if m_.get("missing") or m_.get("src") == "EDSM" or m_.get("other"):
            return
    except Exception:
        pass
    C, L, i = col_pick(d)
    if not L:
        return
    real = {t[0].lower(): t[5] for t in col_rows(d, L[i])}
    rows = [r for r in (mk.get("col") or []) if real.get((r[0] or "").lower(), 0) > 0]
    if not rows:
        return
    n = min(4, len(rows))
    box = pygame.Rect(6, H - 44 - 18 - n * 14, W - 12, 18 + n * 14)
    pygame.draw.rect(surf, (0, 28, 8), box, border_radius=5)
    pygame.draw.rect(surf, GREEN, box, 1, border_radius=5)
    put(surf, F["small"], "PARA TU COLONIA (se vende aquí)" + (f"  +{len(rows) - n} más" if len(rows) > n else "") + "  · toca: ver todo",
        (box.x + 6, box.y + 2), GREEN, box.w - 12)
    yy = box.y + 18
    for name, stock, price, need in (r_[:4] for r_ in rows[:n]):     # b16b: mercado, ahora con 5 datos
        put(surf, F["tiny"], name, (box.x + 8, yy), GREEN, 170)
        put(surf, F["tiny"], f"hay {stock:,} t · {price:,} cr".replace(",", "."), (box.x + 190, yy), WHITE, 150)
        put(surf, F["tiny"], f"faltan {real[name.lower()]:,} t".replace(",", "."), (box.right - 8, yy), ORANGE, anchor="topright")
        yy += 14
    MKBOX["r"] = box

VIEWS[127] = view_market_b13

# --- aviso: carga por entregar al atracar en el deposito ---


# --- toques ---



# ---------- v1.0 beta 14: aviso de compra para tu construccion ----------
EV_LIST.append(("colcompra", "COLONIA: ESTACIÓN SIN LO QUE TE FALTA"))
CBW = {"t": None, "mk": None}

def _col_need_keys(d):
    C, L, i = col_pick(d)
    if not L:
        return None, []
    x = next((y for y in L if not y.get("done") and not y.get("fail")), None)
    if not x:
        return None, []
    return x, [t for t in col_rows(d, x) if t[5] > 0]

def _col_alert(title, sub, col, voz=None):
    if not ev_on("colcompra"):
        return
    k0 = XA_K[0]
    try:
        XA_K[0] = "colcompra"
        set_alert(title, sub, col, 8, kind="info")
        play("alarm" if col == RED else "ok")
        if voz:
            voice_say(voz)
    finally:
        XA_K[0] = k0

def _col_alt(d, need, skip_mid=None):
    """Estacion del sistema (segun EDSM) que vende mas cosas de lo que falta: (nombre, [mercancias])."""
    off = ((d or {}).get("colsys") or {}).get("off") or {}
    cnt = {}
    for fresh in (True, False):                          # primero solo con datos de menos de 30 dias
        for name, key, req, prov, inb, real in need:
            for o in off.get(key) or []:
                if o[7] != skip_mid and (not fresh or not o[5] or time.time() - o[5] < 30 * 86400):
                    cnt.setdefault(o[0], []).append(name)
        if cnt:
            break
    if not cnt:
        return None
    st = max(cnt, key=lambda k: len(cnt[k]))
    return st, cnt[st]

def colbuy_watch(d, now):
    if not (d or {}).get("Flags", 0) & 1:
        CBW["warn"] = None                               # al despegar: el aviso de no vender vuelve a valer
    B = (d or {}).get("colbuy") or {}
    t = B.get("t")
    if CBW["t"] is None:
        CBW["t"] = t or 0                                # al arrancar no avisa de lo antiguo
    elif t and t != CBW["t"]:
        CBW["t"] = t
        if B.get("status") == "ok" and not B.get("dep"):
            x, need = _col_need_keys(d)
            if need:
                keys = set(B.get("keys") or [])
                have = [t_[0] for t_ in need if t_[1] in keys]
                if have:
                    _col_alert(f"AQUÍ HAY {len(have)} MATERIAL{'ES' if len(have) != 1 else ''} DE COLONIZACIÓN",
                               ", ".join(have[:3]) + ("…" if len(have) > 3 else "") + f" · {B.get('st')}", GREEN)
                else:
                    alt = _col_alt(d, need, B.get("mid"))
                    _col_alert("ESTA ESTACIÓN NO TIENE MATERIALES DE COLONIZACIÓN",
                               (f"prueba en {alt[0]} ({', '.join(alt[1][:3])})" if alt else f"{B.get('st')} · para tu construcción"),
                               RED, "esta estación no tiene materiales de colonización")
    # al abrir el mercado ya atracado: con los datos del juego
    mk = (d or {}).get("market") or {}
    key_ = (mk.get("mid"), mk.get("t"))
    if CBW["mk"] is None:
        CBW["mk"] = key_
    elif key_ != CBW["mk"] and mk.get("t") and (d or {}).get("Flags", 0) & 1:
        CBW["mk"] = key_
        C = (d or {}).get("colonia") or {}
        mids = {str(y.get("mid")) for y in C.get("list") or []}
        if str(mk.get("mid")) in mids or C.get("dock"):
            return                                       # es un deposito de construccion
        x, need = _col_need_keys(d)
        if need:
            here = col_here(d)
            if not any(_hh(here, t_[0], t_[1]) is not None for t_ in need):
                alt = _col_alt(d, need, str(mk.get("mid")))
                _col_alert("AQUÍ NO HAY MATERIALES DE COLONIZACIÓN",
                           (f"prueba en {alt[0]} ({', '.join(alt[1][:3])})" if alt else (mk.get("station") or "") + " · mercado del juego"), RED)
        col_nosell(d, mk)


# ---------- v1.1: no vender la carga de colonizacion fuera del deposito ----------

def _col_carried(d):
    """Lo que llevas en la bodega que le falta a tu construccion: [(nombre, clave, toneladas utiles)]."""
    C, L, i = col_pick(d)
    if not L:
        return []
    x = next((y for y in L if not y.get("done") and not y.get("fail")), None)
    return [(t[0], t[1], t[4]) for t in col_rows(d, x) if t[4] > 0] if x else []

def _col_red(title, sub, voz=None):
    if not ev_on("colventa"):
        return
    k0 = XA_K[0]
    try:
        XA_K[0] = "colventa"
        set_alert(title, sub, RED, 10, kind="info")
        play("alarm")
        if voz:
            voice_say(voz)
    finally:
        XA_K[0] = k0

def col_nosell(d, mk):
    """Al abrir el mercado fuera del deposito con carga que le falta a tu construccion (una vez por atraque)."""
    if CBW.get("warn") == mk.get("mid"):
        return
    car = _col_carried(d)
    if not car:
        return
    CBW["warn"] = mk.get("mid")
    tot = sum(c[2] for c in car)
    _col_red(f"NO LA VENDAS AQUÍ: LLEVAS {tot:,} t DE COLONIZACIÓN".replace(",", "."),
             ", ".join(c[0] for c in car[:3]) + ("…" if len(car) > 3 else "") + " · es para tu construcción",
             "no vendas la carga de colonización")

def col_sold(text):
    """Nota del sender (b13) al vender: si era material que le falta a tu construccion, aviso."""
    p = (text.split("|") + ["", "", "0", ""])[:4]
    key, name, n = p[0], p[1], int(p[2] or 0)
    with lock:
        d = state.get("data")
    C = (d or {}).get("colonia") or {}
    if not n or C.get("dock") or p[3] in {str(y.get("mid")) for y in C.get("list") or []}:
        return
    C_, L, i = col_pick(d)
    x = next((y for y in L or [] if not y.get("done") and not y.get("fail")), None)
    for r in (x or {}).get("res") or []:
        if len(r) > 3 and r[3] == key and r[1] - r[2] > 0:
            _col_red(f"HAS VENDIDO {n:,} t DE {name.upper()}".replace(",", "."),
                     f"le faltan {r[1] - r[2]:,} t a tu construcción".replace(",", "."))
            plog(f"Colonización: vendidas {n} t de {name}, que faltan en la construcción")
            return




