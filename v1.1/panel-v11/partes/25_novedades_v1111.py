# Panel Elite v1.1 · parte 25: novedades v1.1.11
#   MERCADO: «NO LA VENDAS · ES PARA TU COLONIA» y «aquí pagan poco» en vez de «VENDIENDO TODO».
#   ALTÍMETRO: suelo según el tipo de cuerpo (helado, rocoso, con hielo, metálico...), cielo con atmósfera tenue,
#              plantas si hay señales biológicas, magma o géiseres según el vulcanismo, sombra de la nave y polvo.
#   El cuerpo sale del sender v1.0b15 (lo que escaneas) o, si no, de EDSM (guardado en la caché del panel).
#   ROBOT: aviso de vulcanismo al llegar a un planeta; «¿cuántas células me quedan?» (a pie y en la nave).
#   FSD: cuenta atrás estimada del enfriamiento (aprende cuánto tarda cada nave) y «FSD LISTO» con pitido.
#   CÉLULAS DE ESCUDO de la nave: contador aproximado (Loadout menos las que disparas con el botón ESCUDO del panel).

def _mezcla(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))

# ---------------------------------------------------------------------------------------------------------------
# MERCADO: el rótulo de abajo
# ---------------------------------------------------------------------------------------------------------------
def mkt_para_colonia(d):
    """Nombres de la carga que le faltan a tu construcción (si no estás atracado en ella)."""
    C = (d or {}).get("colonia") or {}
    if C.get("dock"):
        return []
    falta = {}
    for x in C.get("list") or []:
        if x.get("done") or x.get("fail"):
            continue
        for r in x.get("res") or []:
            if len(r) > 3 and r[1] - r[2] > 0:
                falta[r[3]] = r[0]
    ck = (d or {}).get("cargok") or {}
    return [falta[k] for k, n in ck.items() if n and k in falta]

_view127_v1111 = VIEWS[127]

def view127_v1111(surf, d, flags, now):
    _view127_v1111(surf, d, flags, now)
    m = (d or {}).get("market") or {}
    sell = m.get("sell") or []
    if not sell:
        return
    tot = sum(r[1] * r[2] for r in sell)
    medio = sum(r[1] * r[3] for r in sell if len(r) > 3 and r[3])
    col_ = mkt_para_colonia(d)
    if col_:
        txt, c_ = "NO LA VENDAS · ES PARA TU COLONIA", ORANGE
    elif medio and tot < medio * 0.95:
        txt, c_ = f"VENDIENDO TODO: {cr(tot)} cr ({100 * tot / medio - 100:+.0f} %: aquí pagan poco)", ORANGE
    else:
        return                                            # como siempre: verde
    pygame.draw.rect(surf, BLACK, (0, H - 38, W, 26))
    if col_ and int(now * 2) % 2:
        pygame.draw.rect(surf, (60, 30, 0), (4, H - 38, W - 8, 24), border_radius=4)
    put(surf, F["btn"], txt, (8, H - 36), c_, W - 16)

VIEWS[127] = view127_v1111

# ---------------------------------------------------------------------------------------------------------------
# EL CUERPO DONDE ESTÁS: sender v1.0b15 o EDSM (con caché)
# ---------------------------------------------------------------------------------------------------------------
CUERPO_EDSM = {}                                         # sistema -> {nombre de cuerpo: info} (o None mientras se busca)

def _edsm_cuerpos(sistema):
    def bg():
        datos = None
        try:
            datos = cache_get("edsm_bodies:" + sistema, 30 * 86400) if "cache_get" in globals() else None
            if datos is None:
                import urllib.request as _u, urllib.parse as _p
                req = _u.Request("https://www.edsm.net/api-system-v1/bodies?" + _p.urlencode({"systemName": sistema}),
                                 headers={"User-Agent": "PanelEliteRPi/1.1"})
                with _u.urlopen(req, timeout=15) as r_:
                    j = json.loads(r_.read().decode() or "{}")
                datos = {}
                for b in (j.get("bodies") or []) if isinstance(j, dict) else []:
                    if b.get("type") != "Planet":
                        continue
                    at, vo = b.get("atmosphereType") or "", b.get("volcanismType") or ""
                    datos[b.get("name")] = {"cls": b.get("subType") or "", "land": bool(b.get("isLandable")),
                                            "atm": "" if at.lower().startswith("no atmosphere") else at,
                                            "volc": "" if vo.lower().startswith("no volcanism") else vo}
                if "cache_put" in globals():
                    cache_put("edsm_bodies:" + sistema, datos)
        except Exception as e:
            plog(f"EDSM cuerpos {sistema}: {str(e)[:80]}")
        CUERPO_EDSM[sistema] = datos or {}
    CUERPO_EDSM[sistema] = None
    threading.Thread(target=bg, daemon=True).start()

def cuerpo_info(d):
    """{'name','cls','atm','volc','land','bio','geo'} del cuerpo donde estás (lo que se sepa)."""
    d = d or {}
    c = dict(d.get("cuerpo") or {})
    name = c.get("name") or d.get("body")
    if not name:
        return None
    c["name"] = name
    if not c.get("cls"):
        sy = d.get("system")
        if sy and sy not in CUERPO_EDSM:
            _edsm_cuerpos(sy)
        e = (CUERPO_EDSM.get(sy) or {}).get(name) if sy else None
        if e:
            for k, v in e.items():
                c.setdefault(k, v)
    if c.get("bio") is None:
        b = d.get("bio") or {}
        if b.get("body") == name and b.get("signals") is not None:
            c["bio"] = b["signals"]
    return c

def _tipo(cls):
    c = (cls or "").lower()
    if "icy" in c:
        return "helado"
    if "rocky ice" in c:
        return "hielo"
    if "high metal" in c:
        return "hmc"
    if "metal" in c:
        return "metal"
    return "rocoso"

SUELO_COL = {"rocoso": ((92, 88, 84), (60, 57, 54), (130, 126, 120)),
             "helado": ((170, 195, 215), (120, 150, 175), (225, 238, 248)),
             "hielo": ((100, 98, 100), (64, 62, 64), (200, 210, 220)),
             "hmc": ((125, 82, 52), (82, 52, 32), (165, 115, 78)),
             "metal": ((72, 72, 80), (45, 45, 52), (160, 160, 175))}

def _cielo_col(atm):
    a = (atm or "").lower()
    for k_, c_ in (("ammonia", (80, 140, 80)), ("methane", (80, 110, 160)), ("nitrogen", (90, 100, 150)),
                   ("carbon", (160, 110, 70)), ("sulphur", (165, 150, 60)), ("argon", (130, 95, 150)),
                   ("neon", (150, 90, 130)), ("water", (90, 130, 175)), ("oxygen", (110, 150, 200)),
                   ("helium", (150, 150, 170)), ("silicate", (150, 120, 90))):
        if k_ in a:
            return c_
    return (140, 110, 80)

def _h(i):                                               # pseudoaleatorio fijo (sin random por fotograma)
    return ((i * 2654435761) % 4294967296) / 4294967296.0

def draw_suelo(surf, tape, gy, alt, d, now):
    info = cuerpo_info(d) or {}
    base, osc, luz = SUELO_COL[_tipo(info.get("cls"))]
    fondo = (14, 14, 16)
    gh = tape.bottom - gy
    gs = SPD.get("gs") or 0
    scroll = (now * min(400.0, gs) * 0.25) % 100000      # el suelo pasa con la velocidad horizontal
    # cielo con atmósfera tenue: degradado sobre el horizonte
    if info.get("atm"):
        cc = _cielo_col(info.get("atmt") or info.get("atm"))
        alto = min(60, gy - tape.y)
        for i in range(0, alto, 3):
            pygame.draw.rect(surf, _mezcla(cc, fondo, i / max(1, alto)), (tape.x, gy - i - 3, tape.w, 3))
    pygame.draw.rect(surf, base, (tape.x, gy, tape.w, gh))
    # horizonte irregular
    pts = []
    paso = 8
    off = int(scroll // paso)
    fx = scroll % paso
    for i in range(0, tape.w + 2 * paso, paso):
        pts.append((tape.x + i - fx, gy + int(_h(off + i // paso) * 7) - 4))
    pygame.draw.polygon(surf, base, [(tape.x, tape.bottom)] + pts + [(tape.right + paso, tape.bottom)])
    pygame.draw.lines(surf, luz, False, pts, 2)
    tipo = _tipo(info.get("cls"))
    # rocas y cráteres (pasan con la velocidad)
    if gh > 14:
        anc = tape.w + 40
        for k in range(9):
            x = tape.x + (k * 61 + 13 - scroll * 0.9) % anc - 20
            y = gy + 10 + int(_h(k + 77) * max(4, gh - 18))
            rr = 4 + int(_h(k + 5) * 8)
            if k % 3 == 0:
                pygame.draw.ellipse(surf, osc, (x - rr, y - rr // 2, 2 * rr, rr))
                pygame.draw.arc(surf, luz, (x - rr, y - rr // 2, 2 * rr, rr), 3.4, 6.0, 1)
            else:
                pygame.draw.polygon(surf, osc, [(x - rr, y + 3), (x - rr // 2, y - rr // 2), (x + rr // 3, y - rr // 1.5), (x + rr, y + 3)])
            if tipo == "hielo" and k % 2:
                pygame.draw.circle(surf, (225, 232, 240), (int(x + rr), int(y + 2)), 2)
            if tipo == "metal" and int(now * 3 + k) % 5 == 0:
                pygame.draw.circle(surf, (235, 235, 255), (int(x), int(y - 1)), 1)
    # vulcanismo: magma (grietas que brillan) o géiseres (chorros que suben y se deshacen)
    vo = (info.get("volc") or "").lower()
    if "magma" in vo and gh > 8:
        brillo = (0.5 + 0.5 * math.sin(now * 2.2))
        cm = _mezcla((170, 40, 10), (255, 170, 50), brillo)
        for k in range(3):
            x0 = tape.x + (k * 97 + 30 - scroll * 0.9) % (tape.w + 60) - 30
            y0 = gy + 6 + int(_h(k + 31) * max(2, gh - 10))
            pygame.draw.lines(surf, cm, False, [(x0, y0), (x0 + 9, y0 + 3), (x0 + 15, y0 + 1), (x0 + 24, y0 + 5)], 2)
    if "geyser" in vo:
        for k in range(2):
            fase = (now / 4.0 + k * 0.5) % 1.0               # un chorro cada 4 s más o menos
            if fase > 0.6:
                continue
            x0 = tape.x + 25 + int(_h(k + 3) * (tape.w - 50))
            cg = (205, 225, 240) if "water" in vo or "ammonia" in vo or "methane" in vo or "nitrogen" in vo else (190, 185, 170)
            for j in range(8):
                hy = fase / 0.6 * 70 * (j + 1) / 8
                yy = gy - hy
                if yy < tape.y:
                    break
                pygame.draw.circle(surf, _mezcla(cg, fondo, fase / 0.6 * 0.8 + j * 0.03), (int(x0 + math.sin(j + now) * 2), int(yy)), 2 + j // 2)
    # plantas verdes si hay señales biológicas
    if (info.get("bio") or 0) > 0:
        for k in range(5):
            x = tape.x + (k * 47 + 20 - scroll * 0.9) % (tape.w + 30) - 15
            y = gy + 2 + int(_h(k + 11) * 4)
            v = (60, 170 + int(_h(k) * 50), 70)
            pygame.draw.line(surf, v, (x, y), (x, y - 9), 2)
            pygame.draw.line(surf, v, (x, y - 5), (x - 5, y - 9), 2)
            pygame.draw.line(surf, v, (x, y - 6), (x + 5, y - 11), 2)
    # sombra de la nave: más pequeña, oscura y nítida cuanto más cerca
    k_ = max(0.0, min(1.0, 1 - alt / 40.0))
    sw = int(tape.w * (0.42 - 0.24 * k_))
    sh = max(4, int(sw * 0.16))
    cx = tape.centerx
    for i, f_ in ((3, 0.25), (2, 0.4), (1, 0.6), (0, 0.35 + 0.45 * k_)):
        bw = sw + int(i * 8 * (1 - k_))
        pygame.draw.ellipse(surf, _mezcla(base, (10, 8, 6), f_), (cx - bw // 2, gy + 4 + sh // 2 - (sh + i * 2) // 2, bw, sh + i * 2))
    # polvo por debajo de 15 m
    if alt < 15 and gh > 2:
        n = int(30 * (1 - alt / 15)) + 6
        for i in range(n):
            lado = -1 if i % 2 else 1
            t_ = (now * 1.6 + _h(i + 300)) % 1.0
            dx = (sw * 0.35 + t_ * 70) * lado
            up = math.sin(t_ * math.pi) * 14 * (1 - alt / 15)
            c_ = _mezcla(luz, base, t_)
            pygame.draw.circle(surf, c_, (int(cx + dx), int(gy - up)), 1 + i % 2)
    if gh > 18 and info.get("cls"):
        rot = {"helado": "HELADO", "hielo": "ROCOSO CON HIELO", "hmc": "ALTO EN METALES",
               "metal": "RICO EN METALES", "rocoso": "ROCOSO"}[tipo] + ("  ·  ATMÓSFERA" if info.get("atm") else "")
        if F["tiny"].size(rot)[0] > tape.w - 12:         # cinta estrecha (atraque): sin «· ATMÓSFERA»
            rot = rot.split("  ·  ")[0]
        rot = fit(F["tiny"], rot, tape.w - 12)
        tw, th = F["tiny"].size(rot)                     # v1.1.13: caja oscura detrás para que se lea
        cj = pygame.Rect(tape.right - tw - 10, tape.bottom - th - 6, tw + 8, th + 4)
        pygame.draw.rect(surf, (10, 10, 12), cj, border_radius=3)
        put(surf, F["tiny"], rot, (cj.right - 4, cj.y + 2), WHITE, anchor="topright")

def draw_alt_base(surf, r, d, now, big=False):
    """Igual que antes, pero el suelo marrón ahora es el del cuerpo (draw_suelo)."""
    alt = alt_now(d)
    if alt is None:
        put(surf, F["btn"], "sin altura", (r.centerx, r.centery - 10), DIM, anchor="center")
        put(surf, F["small"], "aparece cerca de un planeta", (r.centerx, r.centery + 12), DIM, r.w - 10, anchor="center")
        return
    fl = (d or {}).get("Flags", 0)
    vs = alt_vs()
    tape = pygame.Rect(r.x + 8, r.y + 18, int(r.w * 0.52), r.h - 26)
    pygame.draw.rect(surf, (14, 14, 16), tape); pygame.draw.rect(surf, (80, 80, 86), tape, 1)
    span = alt_span(alt)                                 # v1.1.12: el suelo se ve hasta los 600 m (parte 28)
    step = span // 6
    ppm = tape.h / span
    mid = tape.centery
    old = surf.get_clip(); surf.set_clip(tape)
    gy = mid + alt * ppm
    if gy < tape.bottom:
        try:
            draw_suelo(surf, tape, int(gy), alt, d, now)
        except Exception as e:
            log_exc("suelo", e)
            pygame.draw.rect(surf, (60, 35, 10), (tape.x, int(gy), tape.w, tape.bottom - int(gy)))
    m0 = int((alt - span) // (step / 5)) * (step / 5)
    k = 0
    m = m0
    while m < alt + span and k < 200:
        yy = mid - (m - alt) * ppm
        if m >= 0 and abs(round(m / step) * step - m) < 1e-6:
            pygame.draw.line(surf, WHITE, (tape.x, yy), (tape.x + 12, yy), 2)
            put(surf, F["small"], f"{int(m):,}".replace(",", "."), (tape.x + 16, int(yy) - 8), WHITE)
        elif m >= 0:
            pygame.draw.line(surf, (150, 150, 150), (tape.x, yy), (tape.x + 6, yy), 1)
        m += step / 5; k += 1
    surf.set_clip(old)
    put(surf, F["tiny"], "ALT" + (" (radio medio)" if fl & (1 << 29) else ""), (tape.x, r.y + 3), DIM)
    txt = f"{alt:,.0f} m".replace(",", ".") if alt < 100000 else f"{alt / 1000:,.0f} km".replace(",", ".")
    box = pygame.Rect(tape.x + tape.w * 2 // 5, mid - 15, tape.w * 3 // 5 + 26, 30)
    pts = [(box.x, mid), (box.x + 10, box.y), (box.right, box.y), (box.right, box.bottom), (box.x + 10, box.bottom)]
    pygame.draw.polygon(surf, BLACK, pts); pygame.draw.polygon(surf, ORANGE, pts, 2)
    put(surf, F["big"], txt, (box.centerx + 5, mid), ORANGE, box.w - 14, anchor="center")
    vsr = pygame.Rect(tape.right + 40, tape.y + 14, 28, tape.h - 44)
    pygame.draw.rect(surf, (14, 14, 16), vsr)
    pygame.draw.line(surf, DIM, (vsr.x, vsr.centery), (vsr.right, vsr.centery), 1)
    put(surf, F["tiny"], "VERT.", (vsr.centerx, vsr.y - 12), DIM, anchor="center")
    if vs is not None:
        lim = 200 if alt > 2000 else 50
        h_ = int(min(1.0, abs(vs) / lim) * (vsr.h // 2 - 2))
        col = BLUE if vs < 0 else GREEN
        if vs < 0:
            pygame.draw.rect(surf, col, (vsr.x + 4, vsr.centery, vsr.w - 8, h_))
        else:
            pygame.draw.rect(surf, col, (vsr.x + 4, vsr.centery - h_, vsr.w - 8, h_))
        warn = vs < -30 and alt < 300
        put(surf, F["btn"], f"{vs:+.0f}", (vsr.centerx, vsr.bottom + 12), RED if warn and int(now * 2) % 2 else col, anchor="center")
        put(surf, F["tiny"], "m/s", (vsr.centerx, vsr.bottom + 28), DIM, anchor="center")

# ---------------------------------------------------------------------------------------------------------------
# VULCANISMO: aviso al robot al llegar a un planeta con volcanes
# ---------------------------------------------------------------------------------------------------------------
EV_LIST.append(("robvolc", "ROBOT: VULCANISMO AL LLEGAR A UN PLANETA"))
VOLC_SUST = [("silicate vapour", "vapor de silicato"), ("carbon dioxide", "dióxido de carbono"), ("water", "agua"),
             ("ammonia", "amoníaco"), ("methane", "metano"), ("nitrogen", "nitrógeno"), ("silicate", "silicato"),
             ("iron", "hierro"), ("rocky", "roca")]

def volc_es(v):
    """«minor silicate vapour geysers volcanism» -> «géiseres de vapor de silicato (menores)»."""
    t = (v or "").lower()
    sust = next((es for en, es in VOLC_SUST if en in t), "")
    if "geyser" in t:
        txt = "géiseres" + (f" de {sust}" if sust else "")
        fuerza = " (menores)" if "minor" in t else " (mayores)" if "major" in t else ""
    elif "magma" in t:
        txt = "magma" + (f" de {sust}" if sust else "")
        fuerza = " (menor)" if "minor" in t else " (mayor)" if "major" in t else ""
    else:
        return t.replace("volcanism", "").strip()
    return txt + fuerza

VOLCW = {"body": None}

def volc_watch(d):
    b = (d or {}).get("body")
    if not b or b == VOLCW["body"] or not (d.get("Flags", 0) & (1 << 21)):
        if not b:
            VOLCW["body"] = None
        return
    info = cuerpo_info(d) or {}
    if not info.get("cls") and not info.get("volc"):
        return                                            # aún no se sabe (EDSM buscando): se mira luego
    VOLCW["body"] = b
    if info.get("volc") and cfg.get("stackchan") and ev_on("robvolc"):
        sc_aviso("robvolc", "ok", "VULCANISMO", f"{b}: {volc_es(info['volc'])}")

# ---------------------------------------------------------------------------------------------------------------
# FSD ENFRIÁNDOSE: cuenta atrás estimada (aprende por nave; las paradas de emergencia aparte)
# ---------------------------------------------------------------------------------------------------------------
EV_LIST.append(("fsdlisto", "FSD LISTO (tras enfriarse)"))
FSDT_FILE = os.path.join(PANEL_DIR, "fsd_tiempos.json")
FSDC = {"t0": None, "emerg": False, "ship": None, "left": None, "est": None, "tab": None, "emerg_t": 0.0}

def _fsd_tab():
    if FSDC["tab"] is None:
        try:
            with open(FSDT_FILE, encoding="utf-8") as fh:
                FSDC["tab"] = json.load(fh)
        except (OSError, ValueError):
            FSDC["tab"] = {}
    return FSDC["tab"]

def _fsd_clave(d):
    sh = ((d.get("live") or {}).get("ship")) or {}
    return (sh.get("ident") or sh.get("name") or sh.get("ship") or "nave") + ("|emerg" if FSDC["emerg"] else "")

def fsd_watch(d, now):
    on = bool(d.get("Flags", 0) & (1 << 18))
    if on and FSDC["t0"] is None:
        FSDC.update(t0=now, emerg=now - FSDC["emerg_t"] < 10)
        L = _fsd_tab().get(_fsd_clave(d)) or []
        FSDC["est"] = sum(L) / len(L) if L else None
    elif not on and FSDC["t0"] is not None:
        dur = now - FSDC["t0"]
        if 2 < dur < 300:
            tab = _fsd_tab()
            L = (tab.get(_fsd_clave(d)) or [])[-4:] + [round(dur, 1)]
            tab[_fsd_clave(d)] = L
            try:
                with open(FSDT_FILE + ".tmp", "w", encoding="utf-8") as fh:
                    json.dump(tab, fh)
                os.replace(FSDT_FILE + ".tmp", FSDT_FILE)
            except OSError:
                pass
            if dur > 4:                                  # v1.1.13: mensaje (ALERTAS) y pitido (SONIDO) por separado
                if ev_on("fsdlisto"):
                    set_alert("FSD LISTO", "ya puedes saltar o entrar en supercrucero", GREEN, 2)
                if snd_on("fsdlisto"):
                    play("ok")
        FSDC.update(t0=None, est=None)
    if FSDC["t0"] is not None:
        el = now - FSDC["t0"]
        FSDC["left"] = max(0.0, FSDC["est"] - el) if FSDC["est"] else None
    else:
        FSDC["left"] = None

def draw_fsd_banda(surf, now):
    if FSDC["t0"] is None:
        return
    el = now - FSDC["t0"]
    r = pygame.Rect(8, H - 34, W - 16, 26)
    pygame.draw.rect(surf, BLACK, r)
    pygame.draw.rect(surf, BLUE, r, 1, border_radius=4)
    if FSDC["est"]:
        k = min(1.0, el / FSDC["est"])
        pygame.draw.rect(surf, (20, 50, 90), (r.x + 1, r.y + 1, int((r.w - 2) * k), r.h - 2), border_radius=4)
        txt = f"FSD LISTO EN ≈ {FSDC['left']:.0f} s" if FSDC["left"] > 0.5 else "FSD CASI LISTO…"
    else:
        txt = f"FSD ENFRIÁNDOSE · {el:.0f} s (aprendiendo cuánto tarda esta nave)"
    put(surf, F["btn"], txt, (r.centerx, r.centery), WHITE, r.w - 10, anchor="center")

_handle_note_v1111 = handle_note

def handle_note(kind, text):
    if kind == "emergstop":
        FSDC["emerg_t"] = time.time()
    return _handle_note_v1111(kind, text)

# ---------------------------------------------------------------------------------------------------------------
# CÉLULAS DE ESCUDO DE LA NAVE: contador aproximado
# ---------------------------------------------------------------------------------------------------------------
SCBC = {"usadas": 0, "ref": None}

def scb_aprox(d):
    """(células que quedan aprox., máximo) o None si la nave no lleva banco de células."""
    s = (d or {}).get("scb") or {}
    if s.get("n") is None:
        return None
    ref = (s.get("tlo"), s.get("tref"))
    if ref != SCBC["ref"]:                                # Loadout nuevo o recarga: se empieza a contar de nuevo
        SCBC.update(ref=ref, usadas=0)
    base = s.get("max") if s.get("tref", 0) > s.get("tlo", 0) else s.get("n")
    return max(0, (base or 0) - SCBC["usadas"]), s.get("max") or s.get("n") or 0

_press_seq_v1111 = press_seq

def press_seq(keys):
    try:
        k_esc = next((it[1] for it in BUTTONS + COMBAT_BTNS if it[0] == "ESCUDO"), None)
        with lock:
            d = state.get("data") or {}
        if k_esc and keys and keys[0] == k_esc and not (d.get("Flags2", 0) & 1):
            SCBC["usadas"] += 1
    except Exception:
        pass
    return _press_seq_v1111(keys)

_view_live_v1111 = VIEWS[100]

def view_live_v1111(surf, d, flags, now):
    _view_live_v1111(surf, d, flags, now)
    if (d or {}).get("Flags2", 0) & 1:
        return
    sc = scb_aprox(d)
    if sc:
        n, mx = sc
        put(surf, F["small"], f"CÉLULAS DE ESCUDO ≈ {n}" + (f" / {mx}" if mx else ""), (8, H - 56),
            RED if n <= 1 else BLUE)
    draw_fsd_banda(surf, now)

VIEWS[100] = view_live_v1111

# ---------------------------------------------------------------------------------------------------------------
# ROBOT: la cuenta atrás del FSD y «¿cuántas células me quedan?»
# ---------------------------------------------------------------------------------------------------------------
_sc_send_v1111 = sc_send

def sc_send(obj):
    if obj.get("t") == "hola":
        l_ = FSDC.get("left")
        obj = dict(obj, fsdc=int(l_) if l_ is not None and l_ > 0 else (-1 if FSDC["t0"] is None else 0))
    return _sc_send_v1111(obj)

def r_celulas(d, now, t):
    if (d or {}).get("Flags2", 0) & 1:                    # a pie
        c = cons_count(d)
        return f"Llevas {c.get('cell', 0)} células de energía y {c.get('med', 0)} botiquines"
    sc = scb_aprox(d)
    if not sc:
        return "Esta nave no lleva banco de células de escudo"
    return f"Te quedan unas {sc[0]} células de escudo" + (f" de {sc[1]}" if sc[1] else "") + \
           ". Es aproximado: solo cuento las que disparas desde el panel"

PREG_V1110.insert(0, (lambda t: _hay(t, "celula") and _hay(t, "queda", "tengo", "cuanta", "llevo", "me quedan"), r_celulas))

# ---------------------------------------------------------------------------------------------------------------
# vigilantes (una vez por fotograma, baratos)
# ---------------------------------------------------------------------------------------------------------------
_render_v1111 = render

def render(surf):
    r_ = _render_v1111(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        now = time.time()
        if d and now - rx < 5:
            fsd_watch(d, now)
            volc_watch(d)
    except Exception as e:
        log_exc("v1.1.11 vigilantes", e)
    return r_
