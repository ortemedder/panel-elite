# Panel Elite v2.2 · parte 59: v2.2b4 — EXOBIOLOGÍA en 2 CUADROS (a pie en un planeta con el traje Artemis,
#   con el muestreador genético en la mano o mientras muestreas con cualquier traje)
#   - MAPA a la izquierda: tú con tu rumbo, las muestras tomadas con su círculo de distancia mínima del género
#     (verde si ya estás fuera de todos: puedes muestrear; rojo si no), tu rastro y la nave. Tocar = zoom.
#     Botón NAVE AQUÍ.
#   - ESPECIE ACTUAL a la derecha: especie y variante, muestras n/3, «PUEDES TOMAR MUESTRA» o «ALÉJATE» con la
#     distancia a cada muestra, valor (x5 si es primer descubrimiento) y los géneros del planeta con su estado.
#   - REGISTRO abajo: muestras, análisis y señales; SESIÓN · SIN VENDER.
#   - Va con 12 AJUSTES > PANTALLA > MINERÍA / BIO. El combate a pie siempre manda.

BH = {"sig": None, "log": [], "n": 0, "cr": 0, "zoom": 1}

def _bh_log(tag, txt, col):
    BH["log"].insert(0, (time.time(), tag, txt, col))
    del BH["log"][12:]

def bh_update(d):
    b = (d or {}).get("bio") or {}
    sig = (b.get("species"), b.get("step"), b.get("body"), b.get("signals"))
    old = BH["sig"]
    BH["sig"] = sig
    if old is None or sig == old:
        return
    sp, st, body, sg = sig
    if body and sg and (body, sg) != (old[2], old[3]):
        _bh_log("SEÑALES BIO", f"{sg} en {body}", AMBAR)
    if sp and st != old[1] or sp != old[0]:
        if st and st >= 3:
            v = b.get("value") or 0
            v5 = v * (5 if b.get("bonus") else 1)
            BH["n"] += 1; BH["cr"] += v5
            _bh_log("ANALIZADO", f"{sp}" + (f" · +{cr(v5)} cr" if v5 else ""), GREEN)
        elif sp and st:
            _bh_log(f"MUESTRA {st}/3", sp + (f" · {b['variant']}" if b.get("variant") else ""), PURPLE)

def bio_activa(d, flags, now, mode):
    d = d or {}
    f2 = d.get("Flags2", 0)
    if not (f2 & 1 and f2 & (1 << 4)) or in_fight(d, now) or str(mode).startswith("COMBATE"):
        return False
    Lv = d.get("live") or {}
    b = d.get("bio") or {}
    arma = (Lv.get("weapon") or "").lower()
    return ("artemis" in suit_name_of(d).lower() or any(k in arma for k in ("muestr", "sampler", "genetic", "genét"))
            or (b.get("species") and 0 < (b.get("step") or 0) < 3))

# ---------------------------------------------------------------------------------------------------------------
# MAPA de muestreo: centrado en ti, escala según la distancia mínima del género
# ---------------------------------------------------------------------------------------------------------------
LZ_ACC["biozoom"] = lambda acc, X, Y: (tap_flash(("biozoom",)), BH.__setitem__("zoom", (BH["zoom"] + 1) % 3))

def b2_mapa(Z, d, flags, now):
    d = d or {}
    b = d.get("bio") or {}
    rng = b.get("range") or 100
    esc_m = rng * (1.25, 2.5, 5.0)[BH["zoom"] % 3]          # metros del centro al borde corto
    a = c2_marco(Z, f"MAPA · {fmt_m(round(esc_m * 2))}", (b.get("body") or "").upper() or None)
    r = pygame.Rect(a.x - 14, a.y - 10, a.w + 28, a.h + 20)
    lat, lon, R = b.get("lat"), b.get("lon"), b.get("R")
    if lat is None or not R:
        put(Z, F["btn"], "Sin posición en el planeta", r.center, DIM, r.w - 20, anchor="center")
        return
    k = math.cos(math.radians(lat))
    def xy(p):
        return (R * math.radians(p[1] - lon) * k, R * math.radians(p[0] - lat))
    sc = min(r.w, r.h) / 2 / esc_m
    cx, cy = r.centerx, r.centery
    def scr(p):
        return (int(cx + p[0] * sc), int(cy - p[1] * sc))
    old = Z.get_clip()
    Z.set_clip(r)
    gc = tuple(max(18, c // 3) for c in DIM[:3])
    step = next((s_ for s_ in MAP_STEPS if esc_m * 2 / s_ <= 8), MAP_STEPS[-1])
    g = 0
    while g * sc <= r.w:
        for sgn in (1, -1):
            pygame.draw.line(Z, gc, (cx + sgn * g * sc, r.y), (cx + sgn * g * sc, r.bottom))
            pygame.draw.line(Z, gc, (r.x, cy + sgn * g * sc), (r.right, cy + sgn * g * sc))
        g += step
    trail = [scr(xy(p)) if p is not None else None for p in track["pts"][-400:]]
    for i in range(1, len(trail)):
        if trail[i - 1] and trail[i]:
            pygame.draw.line(Z, (120, 60, 0), trail[i - 1], trail[i], 2)
    pts = [p for p in (b.get("pts") or []) if p]
    step_ = b.get("step") or 0
    lejos = True
    dists = []
    for i, p in enumerate(pts if step_ < 3 else []):
        dm = hav(p, (lat, lon), R)
        dists.append(dm)
        dentro = dm < rng
        lejos = lejos and not dentro
        x, y = scr(xy(p))
        pygame.draw.circle(Z, (150, 40, 30) if dentro else (40, 110, 50), (x, y), max(4, int(rng * sc)), 2)
        pygame.draw.circle(Z, PURPLE, (x, y), 9)
        put(Z, F["tiny"], f"MUESTRA {i + 1}", (x + 14, y - 12), PURPLE)
    ship = ship_pos(b)
    if ship:
        x, y = scr(xy(ship))
        pygame.draw.polygon(Z, GREEN, [(x, y - 14), (x + 12, y + 10), (x - 12, y + 10)], 2)
        put(Z, F["tiny"], "NAVE", (x + 16, y - 8), GREEN)
    hdg = math.radians(b.get("hdg") or 0)
    def rot(a_, rr):
        return (cx + rr * math.sin(hdg + a_), cy - rr * math.cos(hdg + a_))
    pygame.draw.polygon(Z, AMBAR, [rot(0, 22), rot(2.5, 14), rot(math.pi, 4), rot(-2.5, 14)])
    ok = bool(pts) and lejos and step_ < 3
    pygame.draw.circle(Z, GREEN if ok or not pts else RED, (cx, cy), 30, 3)
    Z.set_clip(old)
    pygame.draw.rect(Z, DIM, r, 1)
    put(Z, F["tiny"], f"círculo = {rng} m (mínimo del género)  ·  toca para el zoom", (r.x + 8, r.y + 6), DIM, r.w - 60)
    nx = r.right - 16
    pygame.draw.line(Z, WHITE, (nx, r.y + 30), (nx, r.y + 12), 2)
    pygame.draw.polygon(Z, WHITE, [(nx, r.y + 6), (nx - 5, r.y + 14), (nx + 5, r.y + 14)])
    put(Z, F["tiny"], "N", (nx - 10, r.y + 8), WHITE, anchor="topright")
    if ship:
        put(Z, F["tiny"], f"nave a {fmt_m(round(hav((lat, lon), ship, R)))}", (r.x + 8, r.bottom - F["tiny"].get_height() - 6), GREEN)
    lz_hit(r, "biozoom")
    rb = pygame.Rect(r.right - 190, r.bottom - 54, 182, 46)
    pygame.draw.rect(Z, GREEN, rb, border_radius=8)
    put(Z, F["small"], "NAVE AQUÍ", rb.center, BLACK, anchor="center")
    lz_hit(rb, "naveaqui")

# ---------------------------------------------------------------------------------------------------------------
# ESPECIE ACTUAL
# ---------------------------------------------------------------------------------------------------------------
def b2_especie(Z, d, flags, now):
    d = d or {}
    b = d.get("bio") or {}
    Lv = d.get("live") or {}
    a = c2_marco(Z, "ESPECIE ACTUAL", suit_name_of(d).upper() or None)
    x, w = a.x, a.w
    y = a.y - 4
    sp = b.get("species")
    step = b.get("step") or 0
    hs = F["small"].get_height()
    if not sp:
        put(Z, F["btn"], "Sin muestreo en curso", (x, y + 6), DIM, w)
        y += F["btn"].get_height() + 14
    else:
        put_fit(Z, ("btn", "small"), sp.upper(), (x, y), GREEN if step >= 3 else PURPLE, w)
        y += F["btn"].get_height() + 2
        put(Z, F["tiny"], b.get("variant") or "", (x, y), DIM, w * 0.6)
        if b.get("bonus"):
            put(Z, F["tiny"], "PRIMER DESCUBRIMIENTO", (x + w, y), AMBAR, anchor="topright")
        y += F["tiny"].get_height() + 8
        put(Z, F["small"], "MUESTRAS", (x, y + 4), DIM)
        for k_ in range(3):
            rr = pygame.Rect(x + 140 + k_ * 62, y, 54, hs + 6)
            pygame.draw.rect(Z, PURPLE if k_ < step else (40, 25, 10), rr, border_radius=6)
            pygame.draw.rect(Z, DIM, rr, 1, border_radius=6)
        put(Z, F["btn"], f"{min(step, 3)} / 3", (x + w, y - 2), GREEN if step >= 3 else PURPLE, anchor="topright")
        y += hs + 16
        pts, R, lat, lon = b.get("pts") or [], b.get("R"), b.get("lat"), b.get("lon")
        rng = b.get("range") or 100
        rb = pygame.Rect(x, y, w, hs * 2 + 18)
        if step >= 3:
            pygame.draw.rect(Z, (10, 50, 20), rb, border_radius=8)
            pygame.draw.rect(Z, GREEN, rb, 2, border_radius=8)
            put(Z, F["btn"], "ESPECIE ANALIZADA", rb.center, GREEN, anchor="center")
        elif pts and R and lat is not None:
            ds = [hav(p, (lat, lon), R) for p in pts if p]
            ok = min(ds) >= rng
            pygame.draw.rect(Z, (10, 50, 20) if ok else (60, 12, 8), rb, border_radius=8)
            pygame.draw.rect(Z, GREEN if ok else RED, rb, 2, border_radius=8)
            put(Z, F["small"], "PUEDES TOMAR MUESTRA" if ok else "ALÉJATE", (rb.x + 12, rb.y + 6), GREEN if ok else RED)
            put(Z, F["tiny"], " · ".join(f"a {fmt_m(round(v))} de la {i + 1}" for i, v in enumerate(ds)) + f"  (mín. {rng} m)",
                (rb.x + 12, rb.y + hs + 10), WHITE, rb.w - 24)
        else:
            pygame.draw.rect(Z, DIM, rb, 2, border_radius=8)
            put(Z, F["small"], f"distancia mínima del género: {rng} m", (rb.x + 12, rb.centery), DIM, rb.w - 24, anchor="midleft")
        y = rb.bottom + 12
        val = b.get("value")
        if val:
            put(Z, F["small"], "VALOR", (x, y + 4), DIM)
            txt = ("" if b.get("exact") else "~ ") + cr(val) + " cr" + (f"  ·  x5 = {cr(val * 5)}" if b.get("bonus") else "")
            put(Z, F["btn"], txt, (x + w, y), GREEN, w - 110, anchor="topright")
            y += F["btn"].get_height() + 6
    pygame.draw.line(Z, DIM, (x, y), (x + w, y), 1)
    y += 6
    sig = b.get("signals")
    put(Z, F["tiny"], f"EN ESTE PLANETA · {sig if sig is not None else '?'} SEÑALES BIO", (x, y), DIM)
    y += F["tiny"].get_height() + 4
    done = set(b.get("done") or [])
    gens = list(b.get("genuses") or [])
    if b.get("genus") and b["genus"] not in gens and sp:
        gens.append(b["genus"])
    pie = a.bottom - F["tiny"].get_height() - 4
    if not gens:
        put(Z, F["small"], "sin datos: escanea el planeta (DSS)", (x, y), DIM, w)
    for g in gens:
        if y + hs > pie - 4:
            break
        if g in done:
            est, col = "ANALIZADO", GREEN
        elif g == b.get("genus") and sp and step < 3:
            est, col = f"{step}/3", PURPLE
        else:
            est, col = "PENDIENTE", DIM
        put(Z, F["small"], g, (x, y), WHITE, w * 0.6)
        put(Z, F["small"], est, (x + w, y), col, anchor="topright")
        y += hs + 4
    hp, oxy, t = pctv(Lv.get("health")), pctv(Lv.get("oxy")), Lv.get("temp")
    bits = [f"Salud {hp:.0f} %" if hp is not None else "", f"O₂ {oxy:.0f} %".replace("₂", "2") if oxy is not None else "",
            f"{t - 273.15:.0f} °C" if t is not None else ""]
    put(Z, F["tiny"], "  ·  ".join(x_ for x_ in bits if x_), (x, pie), RED if hp is not None and hp < 30 else DIM, w)

def b2_registro(Z, d, flags, now):
    b = (d or {}).get("bio") or {}
    bits = [f"SESIÓN {BH['n']} especies" + (f" · {cr(BH['cr'])} cr" if BH["cr"] else "")]
    if b.get("unsold") is not None:
        bits.append(f"SIN VENDER {b.get('unsold', 0)}" + (f" ({cr(b['unsold_cr'])} cr)" if b.get("unsold_cr") else ""))
    a = c2_marco(Z, "REGISTRO", "  ·  ".join(bits), dcol=WHITE)
    x, w = a.x, a.w
    y = a.y - 12
    lh = (a.bottom + 8 - y) // 3
    if not BH["log"]:
        put(Z, F["small"], "aún nada en esta sesión", (x, y + 4), DIM)
    for t_, tag, txt, col in BH["log"][:3]:
        put(Z, F["tiny"], time.strftime("%H:%M", time.localtime(t_)), (x, y + 3), DIM)
        put(Z, F["small"], tag, (x + 90, y), col)
        put(Z, F["small"], txt, (x + 330, y), WHITE, w - 340)
        y += lh
    lz_hit((0, 0, Z.get_width(), Z.get_height()), "vista", 61)

# ---------------------------------------------------------------------------------------------------------------
# enganche en el tablero
# ---------------------------------------------------------------------------------------------------------------
_lz_tablero_v22b4 = lz_tablero

def lz_tablero(S, d, flags, now):
    try:
        bh_update(d)
    except Exception as e:
        log_exc("historial de exobiología", e)
    mode = big_mode(d, flags)
    if not (mina2_on() and cfg.get("bigmode", "4") == "4" and bio_activa(d, flags, now, mode)):
        return _lz_tablero_v22b4(S, d, flags, now)
    if not lienzo_dibuja(S, lz_tab_cabecera, d, flags, now, "EXOBIOLOGÍA"):
        return _lz_tablero_v22b4(S, d, flags, now)
    if cfg.get("perf"):
        pr = lz_real((700, 64, 10, 10))
        perf_draw(S, pr.x, pr.y)
    LZ["colr"] = None
    BIG["cellmap"] = []
    BIG["fast"] = True
    zonas = ((b2_mapa, 73, P2_L), (b2_especie, 5, P2_R), (b2_registro, 61, C2_B))
    ok = all([lz_zona(S, fn, v, rc, d, flags, now) for fn, v, rc in zonas])
    BIG["rects"] = [(v, lz_real(rc)) for _, v, rc in zonas]
    if not ok:
        S.fill(BLACK)
        LZ["cel"] = {}
        return _lz_tablero_v22b4(S, d, flags, now)
    return True
