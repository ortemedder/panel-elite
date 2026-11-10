#!/usr/bin/env python3
# Parche v1.0 beta 11 (desde la beta 10c): radar de la faccion (ultimo piloto, cuenta atras del tick, halo de trafico,
# recien visitados, resumen del dia, expansion con destino probable, zoom), pestana COLONIA en CARGA/MISION
# (necesita el sender v1.0b7), boton + en VIAJES y numero de aviso para ir a su linea en ALERTAS.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def draw_fac_screen_b11" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b10c', s):
    sys.exit("Este parche es para la v1.0 beta 10c")
shutil.copy(P, P + ".bak100b10c")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

CODE = r'''
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

        # expansiones: linea roja parpadeante hacia el destino probable
        for v in ps:
            if "Expansion" in (v.get("activos") or []) + (v.get("pendientes") or []):
                o = to_px(v["pos"])
                if not o:
                    continue
                tg = exp_target(D, v)
                if tg:
                    dd, tn, tp = tg
                    t_ = to_px(tp)
                    if t_ and blink:
                        pygame.draw.line(surf, RED, o, t_, 2)
                    if t_:
                        pygame.draw.circle(surf, RED if blink else (110, 0, 0), t_, 7, 2)
                        lab = "PROBABLE " + (tn.upper() if len(tn) <= 12 else tn.upper()[:11] + "…")
                        lr = pygame.Rect(t_[0] + 9, t_[1] - 6, tw_(F["tiny"], lab), 12)
                        if lr.right > R.right:
                            lr.right = t_[0] - 9
                        lr.x = max(2, lr.x)
                        if blink:
                            put(surf, F["tiny"], lab, lr.topleft, RED); used.append(lr)
                else:
                    pygame.draw.circle(surf, RED if blink else (110, 0, 0), o, 14, 1)
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
    put(surf, F["tiny"], "MAPA DE LA FACCIÓN" if z == 1 else f"MAPA x{z}", (R.x + 4, R.bottom - 14), DIM)
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
    for v in sorted([v for v in S if v.get("ctrl")], key=lambda v: -v["inf"]):
        if y + 14 > H - 44:
            break
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

_view_viajes_b11 = view_viajes

def view_viajes(surf, d, flags, now):
    _view_viajes_b11(surf, d, flags, now)
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

_draw_alert_b11 = draw_alert

def draw_alert(surf, now):
    _draw_alert_b11(surf, now)
    a = ui.get("alert")
    if a:
        draw_num(surf, pygame.Rect(30, 105, W - 60, 110), a.get("ev"))

_draw_xa_b11 = draw_xa

def draw_xa(surf, now):
    a = xa.get("a")
    _draw_xa_b11(surf, now)
    if a and xa.get("a") is a and now <= a.get("until", 0):
        draw_num(surf, pygame.Rect(24, 64, W - 48, 196), a.get("ev"))

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
TABS[1].append((135, "COLONIA"))
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

def view_colonia(surf, d, flags, now):
    C, L, i = col_pick(d)
    if not L:
        if d and "colonia" not in d:
            put(surf, F["btn"], "actualiza el sender a la v1.0b7", (W // 2, H // 2 - 10), ORANGE, W - 16, anchor="center")
        else:
            put(surf, F["btn"], "sin construcciones", (W // 2, H // 2 - 12), DIM, anchor="center")
            put(surf, F["small"], "atraca en un depósito de construcción y abre su mercado", (W // 2, H // 2 + 12), DIM, W - 16, anchor="center")
        return
    x = L[i]
    y = TOP + 3
    nm = (x.get("st") or "CONSTRUCCIÓN").upper() + (" · " + x["sys"] if x.get("sys") else "")
    put(surf, F["btn"], nm, (8, y), ORANGE, W - 90)
    if len(L) > 1:
        put(surf, F["small"], f"{i + 1}/{len(L)}  >", (W - 8, y + 3), BLUE, anchor="topright")
    elif x.get("mid") == C.get("dock"):
        put(surf, F["small"], "ATRACADO", (W - 8, y + 3), GREEN, anchor="topright")
    y += 20
    bar = pygame.Rect(8, y, W - 16, 12)
    pygame.draw.rect(surf, DIM, bar, 1)
    pygame.draw.rect(surf, GREEN if x.get("done") else ORANGE, (bar.x + 1, bar.y + 1, int((bar.w - 2) * min(100, x.get("prog") or 0) / 100), bar.h - 2))
    st_ = "COMPLETADA" if x.get("done") else "FALLIDA" if x.get("fail") else f"{x.get('prog', 0):.1f} %".replace(".", ",")
    put(surf, F["tiny"], st_, bar.center, WHITE, anchor="center")
    y += 16
    res = x.get("res") or []
    falta = sum(max(0, r[1] - r[2]) for r in res)
    cap = (d or {}).get("cargocap") or 0
    carg = {(n or "").lower(): c for n, c in ((d or {}).get("cargo") or [])}
    util = sum(min(carg.get((r[0] or "").lower(), 0), max(0, r[1] - r[2])) for r in res)
    mk = (d or {}).get("market") or {}
    here = {(r[0] or "").lower(): r[1] for r in (mk.get("col") or [])}
    t_ = f"FALTAN {falta:,} t".replace(",", ".") + (f" · ~{-(-falta // cap)} viajes de {cap} t" if cap and falta else "")
    xx = put(surf, F["small"], t_, (8, y), WHITE if falta else GREEN, W - 16)
    if util:
        put(surf, F["small"], f" · llevas {util:,} t útiles".replace(",", "."), (8 + xx, y), GREEN, W - 24 - xx)
    y += 16
    pend = [r for r in res if r[1] - r[2] > 0]
    hechas = len(res) - len(pend)
    pages = max(1, (len(pend) + 2 * COL_ROWS - 1) // (2 * COL_ROWS))
    pg = ui.get("colpg", 0) % pages
    cw = (W - 16) // 2
    vis = pend[pg * 2 * COL_ROWS:(pg + 1) * 2 * COL_ROWS]
    rows = max(1, (len(vis) + 1) // 2)                  # las dos columnas, repartidas
    for k, r in enumerate(vis):
        cx, cy = 8 + (k // rows) * (cw + 4), y + (k % rows) * 14
        name, req, prov = r[0], r[1], r[2]
        sold = name.lower() in here
        inb = carg.get(name.lower(), 0)
        col = GREEN if sold else WHITE if inb else ORANGE
        put(surf, F["tiny"], ("• " if sold else "") + name, (cx, cy), col, cw - 96)
        b = pygame.Rect(cx + cw - 92, cy + 3, 40, 7)
        pygame.draw.rect(surf, DIM, b, 1)
        pygame.draw.rect(surf, ORANGE, (b.x + 1, b.y + 1, int(38 * prov / req) if req else 0, 5))
        put(surf, F["tiny"], f"{req - prov:,}".replace(",", "."), (cx + cw - 4, cy), col, anchor="topright")
    foot = f"{hechas} de {len(res)} completas" + (f" · pág {pg + 1}/{pages}" if pages > 1 else "") + " · verde = se vende aquí · blanco = en tu bodega"
    put(surf, F["tiny"], foot, (8, H - 14), DIM, W - 16)

VIEWS[135] = view_colonia

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
    put(surf, F["small"], "PARA TU COLONIA (se vende aquí)" + (f"  +{len(L) - n} más en COLONIA" if len(L) > n else ""), (box.x + 6, box.y + 2), GREEN, box.w - 12)
    yy = box.y + 18
    for name, stock, price, need in L[:n]:
        put(surf, F["tiny"], name, (box.x + 8, yy), GREEN, 170)
        put(surf, F["tiny"], f"hay {stock:,} t · {price:,} cr".replace(",", "."), (box.x + 190, yy), WHITE, 150)
        put(surf, F["tiny"], f"faltan {need:,} t".replace(",", "."), (box.right - 8, yy), ORANGE, anchor="topright")
        yy += 14

VIEWS[127] = view_market_b11

# --- render: abre COLONIA al atracar en un deposito ---
_render_b11 = render

def render(surf):
    r_ = _render_b11(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        now = time.time()
        if d is not None and now - rx < 5:
            dk = ((d or {}).get("colonia") or {}).get("dock")
            if dk != COLA["dock"]:
                COLA["dock"] = dk
                COLA["pend"] = now + 2 if dk else 0
            if COLA["pend"] and now > COLA["pend"]:
                COLA["pend"] = 0
                if auto_on("colonia") and not ui.get("idle_on"):
                    ui["view"] = 135; ui["colsel"] = None; ui["colpg"] = 0
    except Exception as e:
        log_exc("colonia auto", e)
    return r_

# --- toques ---
_on_tap_b11 = on_tap

def on_tap(x, y):
    if num_tap(x, y):
        return
    v = ui.get("view")
    if v == 190 and vj_btn(6).collidepoint(x, y):
        vj_plus(); TAP_EV.set(); return
    if v == 135 and y > TOP:
        if COL_HEAD.collidepoint(x, y):
            C, L, i = col_pick(state.get("data"))
            if L:
                ui["colsel"] = (i + 1) % len(L); ui["colpg"] = 0
        else:
            ui["colpg"] = ui.get("colpg", 0) + 1
        TAP_EV.set(); return
    if (v == 77 or (ui.get("idle_on") and IDLE_MODE["m"] == "fac")) and not FULL_BACK.inflate(10, 10).collidepoint(x, y) \
            and not hold_rect("fac").inflate(10, 10).collidepoint(x, y):
        if radar_tap(x, y):
            return
    _on_tap_b11(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 11
- Radar de la facción: «último piloto hace…» (cuándo entró alguien con EDMC en uno de tus sistemas), cuenta atrás del tick de tu sistema principal (EDCAS), halo azul según los comandantes de hoy, anillo blanco que late en los visitados la última hora, línea HOY con comandantes, zonas de conflicto y portanaves, y las EXPANSIONES con una línea roja parpadeante hacia el destino PROBABLE (el sistema conocido más cercano donde no estáis).
- Radar con zoom: botones + y − (hasta x8). Con zoom salen todos los nombres y tocar una zona vacía la centra. Vuelve a x1 cuando deja de verse.
- COLONIA (pestaña de CARGA/MISIÓN): progreso de tu construcción y lo que falta de cada mercancía (en verde lo que se vende en el mercado donde estás, en blanco lo que llevas). Tocar arriba cambia de construcción; tocar la lista pasa de página. Se abre sola al atracar en un depósito (CAMBIO AUTO). Necesita el sender v1.0b7.
- MERCADO: recuadro verde PARA TU COLONIA con lo que se vende allí y le falta a tu construcción.
- VIAJES: botón + para acercar sobre el centro.
- Avisos: número pequeño en la esquina (#23). Tocarlo lleva a su línea en ALERTAS para apagarlo o encenderlo.
# Enlace energético''')
rep('    ("1.0b10c", ', '    ("1.0b11", "Radar con tick, tráfico, expansión y zoom; COLONIA; + en VIAJES; número de aviso"),\n    ("1.0b10c", ')
s = re.sub(r'PANEL_VER = "v1\.0b10c[^"]*"', 'PANEL_VER = "v1.0b11 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 11  (copia en " + P + ".bak100b10c)")
