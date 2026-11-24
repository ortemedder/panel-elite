# Panel Elite v2.3 · parte 61: v2.3b1 — NAVEGACIÓN PLANETARIA (aproximación y superficie)
#   Cuando estás en un planeta (el juego da latitud y longitud) y el destino tiene coordenadas en ese planeta:
#   - ÓRBITA y PLANEO: el PLANETA como esfera (girada para verte a ti y al destino, con zoom solo), la ruta más corta,
#     tu nave con su rumbo y el destino. A la derecha RUMBO A SEGUIR, TU RUMBO, GIRA X°, DISTANCIA, LLEGAS EN,
#     ALTITUD, ÁNGULO AL DESTINO y lo recorrido.
#   - SUPERFICIE (vuelo bajo, aterrizado, SRV o a pie): FLECHA grande hacia el destino (arriba = delante de ti) y,
#     en el aro, marcas de los demás puntos (nave, muestras, recogidas). A la derecha DISTANCIA, GIRA, ALTITUD,
#     LLEGAS EN y un planeta pequeño.
#   - VARIOS PUNTOS: nave, muestras de exobiología y recogidas en el mapa; botón FLECHA: DESTINO / MÁS CERCANO.
#   - A menos de 500 m: aviso «HAS LLEGADO» (ALERTAS / SONIDO > HAS LLEGADO); a los 20 s vuelve el tablero de siempre
#     (y no vuelve hasta que te alejes más de 2 km).
#   - Destino: el que fijas en el juego (puerto o asentamiento con coordenadas conocidas) o el NAVP["manual"] (v2.3b2).
#   - Se quita en 12 AJUSTES > CAMBIO AUTO > PLANETA: ESFERA Y FLECHA. La exobiología, la minería y el combate mandan.
#   Sin cambios en el sender (v1.0b20).

CYAN = (47, 208, 255)
NP_LLEGA, NP_REARMA, NP_VER_LLEGADA = 500, 2000, 20

AUTO_LIST.append(("navpla", "PLANETA: ESFERA Y FLECHA AL DESTINO"))
EV_LIST.append(("llegada", "HAS LLEGADO (DESTINO EN EL PLANETA)"))

NAVP = {"manual": None, "modo": "dest", "avisado": None, "t_llega": 0.0, "d0": {}, "dist": [], "key": None}

# ---------------------------------------------------------------------------------------------------------------
# cuentas en la esfera
# ---------------------------------------------------------------------------------------------------------------
def np_vec(p):
    la, lo = math.radians(p[0]), math.radians(p[1])
    return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))

def np_ll(v):
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (math.degrees(math.asin(max(-1.0, min(1.0, v[2] / n)))), math.degrees(math.atan2(v[1], v[0])))

def np_sep(a, b):
    """Ángulo (radianes) entre dos puntos de la esfera."""
    va, vb = np_vec(a), np_vec(b)
    return math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(va, vb)))))

def np_slerp(a, b, t, om=None):
    om = np_sep(a, b) if om is None else om
    va, vb = np_vec(a), np_vec(b)
    if om < 1e-9:
        return a
    if abs(om - math.pi) < 1e-6:
        om -= 1e-6
    s = math.sin(om)
    k1, k2 = math.sin((1 - t) * om) / s, math.sin(t * om) / s
    return np_ll(tuple(k1 * x + k2 * y for x, y in zip(va, vb)))

def np_rumbo(a, b):
    p1, p2, dl = math.radians(a[0]), math.radians(b[0]), math.radians(b[1] - a[1])
    return math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                   math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360

def np_avanza(a, brg, om):
    """Punto a om radianes de a, con rumbo brg."""
    p1, l1, th = math.radians(a[0]), math.radians(a[1]), math.radians(brg)
    p2 = math.asin(math.sin(p1) * math.cos(om) + math.cos(p1) * math.sin(om) * math.cos(th))
    l2 = l1 + math.atan2(math.sin(th) * math.sin(om) * math.cos(p1), math.cos(om) - math.sin(p1) * math.sin(p2))
    return (math.degrees(p2), (math.degrees(l2) + 540) % 360 - 180)

def np_giro(brg, hdg):
    """+ derecha, - izquierda (grados)."""
    return (brg - hdg + 540) % 360 - 180

def np_fmt(m):
    if m is None:
        return "-"
    if m >= 100000:
        return f"{fnum(m / 1000, 0)} km"
    if m >= 1000:
        return f"{m / 1000:.1f} km".replace(".", ",")
    return f"{m:.0f} m"

def np_tiempo(s):
    if s is None:
        return "-"
    s = int(s)
    if s >= 3600:
        return f"{s // 3600} h {s % 3600 // 60:02d} min"
    if s >= 60:
        return f"{s // 60} min {s % 60:02d} s"
    return f"{s} s"

# ---------------------------------------------------------------------------------------------------------------
# datos: dónde estás, destino y puntos
# ---------------------------------------------------------------------------------------------------------------
def np_yo(d):
    b = (d or {}).get("bio") or {}
    if b.get("lat") is None or b.get("lon") is None or not b.get("R"):
        return None
    return (b["lat"], b["lon"])

def np_destino(d):
    """{'name','lat','lon','src'} en el planeta donde estás, o None."""
    d = d or {}
    body = ((d.get("bio") or {}).get("body") or d.get("body") or "")
    m = NAVP.get("manual")
    if m and (not m.get("body") or not body or m["body"] == body):
        return m
    D = d.get("dest") or {}
    if D.get("lat") is not None and D.get("lon") is not None and (not D.get("sbody") or not body or D["sbody"] == body):
        return {"name": D.get("name") or "DESTINO", "lat": D["lat"], "lon": D["lon"], "src": "juego"}
    return None

NP_ITEMS = {"recharge": ("RECARGA", BLUE)}

def np_puntos(d):
    """Otros puntos del planeta: [(nombre, (lat, lon), color)]."""
    d = d or {}
    b = d.get("bio") or {}
    out = []
    if not d.get("Flags", 0) & (1 << 24):                  # fuera de la nave: la nave es un punto
        s_ = ship_pos(b)
        if s_:
            out.append(("NAVE", tuple(s_[:2]), GREEN))
    if (b.get("step") or 0) < 3:
        for i, p in enumerate(p_ for p_ in (b.get("pts") or []) if p_):
            out.append((f"MUESTRA {i + 1}", tuple(p[:2]), PURPLE))
    body = b.get("body") or d.get("body")
    if track.get("body") and body and track["body"] == body:
        n = 0
        for it in reversed(track.get("items") or []):
            nom, col = NP_ITEMS.get(it[0], ("RECOGIDA", AMBAR))
            out.append((nom, (it[1], it[2]), col))
            n += 1
            if n >= 6:
                break
    return out

def np_fase(d, dist):
    d = d or {}
    fl, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    if dist is not None and dist < NP_LLEGA:
        return "LLEGADA"
    if fl & (1 << 4):
        return "ÓRBITA"
    if f2 & (1 << 12):
        return "PLANEO"
    return "SUPERFICIE"

def np_calc(d, now):
    """Todo lo que hace falta para dibujar (o None si no hay destino en este planeta)."""
    d = d or {}
    yo, dst = np_yo(d), np_destino(d)
    if yo is None or dst is None:
        return None
    b = d.get("bio") or {}
    R = b["R"]
    dp = (dst["lat"], dst["lon"])
    dist = hav(yo, dp, R)
    pts = np_puntos(d)
    obj, onom = dp, dst["name"]
    if NAVP["modo"] == "cerca" and pts:
        cer = min(pts, key=lambda p: hav(yo, p[1], R))
        if hav(yo, cer[1], R) < dist:
            obj, onom = cer[1], cer[0]
    dobj = hav(yo, obj, R)
    hdg = b.get("hdg")
    brg = np_rumbo(yo, obj)
    alt = (d.get("live") or {}).get("alt")
    if alt is not None and (d.get("Flags2", 0) & 1 or d.get("Flags", 0) & (1 << 26)):
        alt = None                                           # a pie o en el SRV: la altura no sirve
    key = (dst["name"], round(dst["lat"], 4), round(dst["lon"], 4))
    if NAVP["key"] != key:
        NAVP.update(key=key, dist=[])
    NAVP["d0"][key] = max(NAVP["d0"].get(key, 0), dist)
    h_ = NAVP["dist"]
    if not h_ or now - h_[-1][0] >= 0.5:
        h_.append((now, dist))
        del h_[:-20]
    old = [p for p in h_ if now - p[0] <= 6]
    vel = None
    if len(old) >= 2 and old[-1][0] - old[0][0] >= 1.5:
        vel = (old[0][1] - old[-1][1]) / (old[-1][0] - old[0][0])
    eta = dist / vel if vel and vel > 2 else None
    if obj != dp:
        eta = None                                           # la flecha va a otro punto: el tiempo era al destino
    ang = -math.degrees(math.atan2(alt, max(1.0, dist))) if alt is not None else None
    return {"yo": yo, "dst": dst, "dp": dp, "R": R, "dist": dist, "obj": obj, "onom": onom, "dobj": dobj, "hdg": hdg,
            "brg": brg, "giro": np_giro(brg, hdg) if hdg is not None else None, "alt": alt, "vel": vel, "eta": eta,
            "ang": ang, "pts": pts, "fase": np_fase(d, dist), "d0": NAVP["d0"][key], "key": key,
            "body": b.get("body") or d.get("body") or ""}

def np_update(d, now):
    """Aviso HAS LLEGADO (una vez por destino; se rearma al alejarse 2 km)."""
    yo, dst = np_yo(d), np_destino(d)
    if yo is None or dst is None:
        return
    key = (dst["name"], round(dst["lat"], 4), round(dst["lon"], 4))
    dist = hav(yo, (dst["lat"], dst["lon"]), d["bio"]["R"])
    if NAVP["avisado"] == key and dist > NP_REARMA:
        NAVP["avisado"] = None
    if dist < NP_LLEGA and NAVP["avisado"] != key:
        NAVP.update(avisado=key, t_llega=now)
        plog(f"HAS LLEGADO: {dst['name']} ({dist:.0f} m)")
        if ev_on("llegada"):
            _xa_venta("llegada", "ok", col=GREEN, title="HAS LLEGADO", big=str(dst["name"]).upper()[:30],
                      lines=[f"a {np_fmt(dist)} del destino"], secs=6)

def nav_activa(d, flags, now, mode):
    d = d or {}
    if FIX["on"]:
        return FIX["kind"] == "nav" and np_calc(d, now) is not None
    if not auto_on("navpla") or not flags & (1 << 21):
        return False
    if not str(mode).startswith(("APROXIMACIÓN", "SUPERFICIE")):
        return False
    yo, dst = np_yo(d), np_destino(d)
    if yo is None or dst is None:
        return False
    key = (dst["name"], round(dst["lat"], 4), round(dst["lon"], 4))
    if NAVP["avisado"] == key and now - NAVP["t_llega"] > NP_VER_LLEGADA:
        return False                                     # ya llegaste: vuelve el tablero de siempre
    return True

# ---------------------------------------------------------------------------------------------------------------
# PLANETA (esfera)
# ---------------------------------------------------------------------------------------------------------------
NP_PASOS = (30, 15, 10, 5, 2, 1, 0.5, 0.25, 0.1, 0.05, 0.02, 0.01)

def np_esfera(Z, r, c, pequena=False):
    yo, dp, R = c["yo"], c["dp"], c["R"]
    sep = np_sep(yo, dp)
    cen = np_slerp(yo, dp, 0.5, sep)
    la0, lo0 = math.radians(cen[0]), math.radians(cen[1])
    s0, c0 = math.sin(la0), math.cos(la0)
    base = min(r.w, r.h) / 2 - (6 if pequena else 14)
    if pequena:
        k = 1.0                                          # el planeta entero, para saber dónde estás
    else:
        k = 400.0 if sep < 1e-9 else max(1.0, min(400.0, 0.35 / max(1e-6, math.sin(sep / 2))))
    Rp = base * k
    cx, cy = r.centerx, r.centery

    def pr(p):
        la, dl = math.radians(p[0]), math.radians(p[1]) - lo0
        cl = math.cos(la)
        cc = s0 * math.sin(la) + c0 * cl * math.cos(dl)
        x = cl * math.sin(dl)
        y = c0 * math.sin(la) - s0 * cl * math.cos(dl)
        return (cx + x * Rp, cy - y * Rp), cc >= 0, (x, y)

    old = Z.get_clip()
    Z.set_clip(r)
    pygame.draw.circle(Z, (26, 18, 8), (cx, cy), int(Rp))
    pygame.draw.circle(Z, ORANGE, (cx, cy), int(Rp), 2)
    vista = math.degrees(min(math.pi / 2, (max(r.w, r.h) / 2) / Rp * 1.2))   # media vista en grados
    paso = next((p_ for p_ in NP_PASOS if vista / p_ >= (2 if pequena else 3)), NP_PASOS[-1])
    rej = (90, 58, 16)
    lat_a, lat_b = max(-90.0, cen[0] - vista), min(90.0, cen[0] + vista)
    if vista >= 60 or abs(cen[0]) + vista >= 80:
        lon_a, lon_b = -180.0, 180.0
    else:
        dlon = vista / max(0.05, math.cos(math.radians(abs(cen[0]) + vista)))
        lon_a, lon_b = cen[1] - dlon, cen[1] + dlon

    def linea(seq):
        tramo = []
        for p in seq:
            xy, vis, _ = pr(p)
            if vis:
                tramo.append(xy)
            else:
                if len(tramo) > 1:
                    pygame.draw.lines(Z, rej, False, tramo, 1)
                tramo = []
        if len(tramo) > 1:
            pygame.draw.lines(Z, rej, False, tramo, 1)

    n_ = 0
    lo = math.floor(lon_a / paso) * paso
    while lo <= lon_b and n_ < 40:
        linea([(lat_a + (lat_b - lat_a) * i / 24, lo) for i in range(25)])
        lo += paso; n_ += 1
    la = math.floor(lat_a / paso) * paso
    while la <= lat_b and n_ < 80:
        if -90 < la < 90:
            linea([(la, lon_a + (lon_b - lon_a) * i / 36) for i in range(37)])
        la += paso; n_ += 1
    # ruta más corta (a trazos)
    ruta = [pr(np_slerp(yo, dp, i / 48, sep)) for i in range(49)]
    for i in range(0, 48, 2):
        (a_, va, _), (b_, vb, _) = ruta[i], ruta[i + 1]
        if va and vb:
            pygame.draw.line(Z, CYAN, a_, b_, 2 if pequena else 3)
    # otros puntos
    if not pequena:
        for nom, p, col in c["pts"]:
            xy, vis, _ = pr(p)
            if vis and r.collidepoint(xy):
                pygame.draw.circle(Z, col, xy, 6)
    # destino (si queda detrás, en el borde y apagado)
    xy, vis, (x, y) = pr(dp)
    if not vis:
        n = math.hypot(x, y) or 1.0
        xy = (cx + x / n * Rp, cy - y / n * Rp)
    col = CYAN if vis else (20, 90, 110)
    pygame.draw.circle(Z, col, xy, 8 if pequena else 13, 3)
    pygame.draw.circle(Z, col, xy, 3 if pequena else 5)
    if not pequena:
        put(Z, F["small"], ("" if vis else "(detrás) ") + "DESTINO", (xy[0] + 18, xy[1] - 26), col, r.right - xy[0] - 24)
    # tú, con tu rumbo
    xy, vis, _ = pr(yo)
    if c["hdg"] is not None:
        xy2, _, _ = pr(np_avanza(yo, c["hdg"], max(1e-7, sep / 12)))
        a = math.atan2(xy2[0] - xy[0], -(xy2[1] - xy[1]))
    else:
        a = 0.0
    sz = 10 if pequena else 18

    def rot(da, rr):
        return (xy[0] + rr * math.sin(a + da), xy[1] - rr * math.cos(a + da))
    pygame.draw.polygon(Z, WHITE, [rot(0, sz), rot(2.5, sz * 0.8), rot(math.pi, sz * 0.25), rot(-2.5, sz * 0.8)])
    if not pequena:
        put(Z, F["small"], "TÚ", (xy[0] - 18, xy[1] + sz + 4), WHITE)
    Z.set_clip(old)
    if not pequena:
        nx = r.right - 24
        pygame.draw.line(Z, WHITE, (nx, r.y + 44), (nx, r.y + 20), 2)
        pygame.draw.polygon(Z, WHITE, [(nx, r.y + 12), (nx - 6, r.y + 22), (nx + 6, r.y + 22)])
        put(Z, F["tiny"], "N", (nx - 12, r.y + 14), WHITE, anchor="topright")
        put(Z, F["tiny"], "toca: ESFERA / FLECHA", (r.x + 10, r.y + 10), DIM)
        put(Z, F["tiny"], f"rejilla {str(paso).replace('.', ',')}°" + (f"  ·  zoom x{k:.0f}" if k >= 2 else ""),
            (r.x + 10, r.bottom - F["tiny"].get_height() - 6), DIM)

# ---------------------------------------------------------------------------------------------------------------
# FLECHA (superficie)
# ---------------------------------------------------------------------------------------------------------------
def np_flecha(Z, r, c):
    cx, cy = r.centerx, r.centery + 10
    rad = int(min(r.w, r.h) / 2 - 46)
    pygame.draw.circle(Z, (26, 18, 8), (cx, cy), rad)
    pygame.draw.circle(Z, DIM, (cx, cy), rad, 2)
    pygame.draw.circle(Z, (60, 40, 12), (cx, cy), int(rad * 0.68), 1)
    put(Z, F["small"], "DELANTE", (cx, cy - rad - 6), DIM, anchor="midbottom")
    put(Z, F["small"], "DETRÁS", (cx, cy + rad + 4), DIM, anchor="midtop")
    put(Z, F["tiny"], "toca: ESFERA / FLECHA", (r.x + 10, r.y + 10), DIM)
    hdg = c["hdg"]
    if hdg is None:
        put(Z, F["btn"], "sin rumbo del juego", (cx, cy), DIM, anchor="center")
        return
    # marcas de los otros puntos en el aro
    for nom, p, col in c["pts"]:
        a = math.radians(np_giro(np_rumbo(c["yo"], p), hdg))
        x1, y1 = cx + (rad - 4) * math.sin(a), cy - (rad - 4) * math.cos(a)
        x2, y2 = cx + (rad + 14) * math.sin(a), cy - (rad + 14) * math.cos(a)
        pygame.draw.line(Z, col, (x1, y1), (x2, y2), 5)
        dm = hav(c["yo"], p, c["R"])
        tx, ty = cx + (rad + 22) * math.sin(a), cy - (rad + 22) * math.cos(a)
        anc = "midleft" if math.sin(a) > 0.3 else "midright" if math.sin(a) < -0.3 else "center"
        put(Z, F["tiny"], f"{nom} {np_fmt(dm)}", (tx, ty), col, 220, anchor=anc)
    a = math.radians(c["giro"])
    col = GREEN if c["fase"] == "LLEGADA" else CYAN
    L = rad * 0.92

    def pt(x, y):          # (x lateral, y hacia delante) en el sistema de la flecha
        return (cx + x * math.cos(a) + y * math.sin(a), cy + x * math.sin(a) - y * math.cos(a))
    w1, w2 = rad * 0.13, rad * 0.34
    pygame.draw.polygon(Z, col, [pt(0, L), pt(w2, L * 0.38), pt(w1, L * 0.46), pt(w1, -L * 0.62),
                                 pt(-w1, -L * 0.62), pt(-w1, L * 0.46), pt(-w2, L * 0.38)])
    pygame.draw.polygon(Z, WHITE, [(cx, cy - 16), (cx + 12, cy + 14), (cx, cy + 6), (cx - 12, cy + 14)])
    put(Z, F["small"], "TÚ", (cx, cy + 20), WHITE, anchor="midtop")

# ---------------------------------------------------------------------------------------------------------------
# cuadros
# ---------------------------------------------------------------------------------------------------------------
def np_izq(Z, d, flags, now):
    c = np_calc(d, now)
    if c is None:
        a = c2_marco(Z, "PLANETA")
        put(Z, F["btn"], "sin destino en este planeta", a.center, DIM, anchor="center")
        return
    esfera = c["fase"] in ("ÓRBITA", "PLANEO")
    fz = NAVP.get("forzar")
    if fz and fz[0] == c["fase"]:
        esfera = fz[1]
    NAVP["esfera"] = (c["fase"], esfera)
    a = c2_marco(Z, "PLANETA" if esfera else "DIRECCIÓN", c["body"].upper() or None)
    r = pygame.Rect(a.x - 14, a.y - 10, a.w + 28, a.h + 20)
    if esfera:
        np_esfera(Z, r, c)
    else:
        np_flecha(Z, r, c)
    lz_hit(r, "npvista")

def _np_dato(Z, x, y, etq, val, col=WHITE, f="btn"):
    put(Z, F["tiny"], etq, (x, y), DIM)
    y += F["tiny"].get_height() + 2
    put(Z, F[f], val, (x, y), col)
    return y + F[f].get_height() + 10

def np_dch(Z, d, flags, now):
    c = np_calc(d, now)
    if c is None:
        c2_marco(Z, "DESTINO")
        return
    fuente = {"juego": "FIJADO EN EL JUEGO", "mano": "A MANO", "fav": "FAVORITO"}.get(c["dst"].get("src"), "")
    a = c2_marco(Z, "DESTINO", fuente or None)
    x, w = a.x, a.w
    y = a.y - 6
    put_fit(Z, ("btn", "small"), str(c["dst"]["name"]), (x, y), CYAN, w)
    y += F["btn"].get_height() + 10
    giro = c["giro"]
    if giro is None:
        gtxt, gcol = "sin rumbo", DIM
    elif abs(giro) < 5:
        gtxt, gcol = "BIEN ENCARADO", GREEN
    else:
        gtxt, gcol = f"GIRA {abs(giro):.0f}° {'DCHA' if giro > 0 else 'IZDA'}", GREEN if abs(giro) < 20 else AMBAR
    if c["onom"] != c["dst"]["name"]:
        put(Z, F["tiny"], f"FLECHA AL MÁS CERCANO: {c['onom']}", (x, y), AMBAR, w)
        y += F["tiny"].get_height() + 12
    if c["fase"] in ("ÓRBITA", "PLANEO"):
        put(Z, F["tiny"], "RUMBO A SEGUIR", (x, y), DIM)
        y += F["tiny"].get_height()
        put(Z, F["num"], f"{c['brg']:.0f}°", (x, y), ORANGE)
        if c["hdg"] is not None:
            put(Z, F["tiny"], f"TU RUMBO {c['hdg']:.0f}°", (x + w, y + 6), DIM, anchor="topright")
        put(Z, F["small"], gtxt, (x + w, y + F["tiny"].get_height() + 12), gcol, w * 0.62, anchor="topright")
        y += F["num"].get_height() + 8
        y = _np_dato(Z, x, y, "DISTANCIA", np_fmt(c["dist"]), WHITE, "big")
        put(Z, F["tiny"], "LLEGAS EN", (x + w, y - F["big"].get_height() - F["tiny"].get_height() - 12), DIM, anchor="topright")
        put(Z, F["small"], np_tiempo(c["eta"]), (x + w, y - F["small"].get_height() - 14), WHITE, anchor="topright")
        put(Z, F["tiny"], "ALTITUD", (x, y), DIM)
        put(Z, F["tiny"], "ÁNGULO AL DESTINO", (x + w * 0.5, y), DIM)
        y += F["tiny"].get_height() + 2
        put(Z, F["btn"], np_fmt(c["alt"]) if c["alt"] is not None else "-", (x, y), WHITE)
        put(Z, F["btn"], f"{c['ang']:.0f}°" if c["ang"] is not None else "-", (x + w * 0.5, y), GREEN)
        y += F["btn"].get_height() + 14
    else:
        y = _np_dato(Z, x, y, "DISTANCIA", np_fmt(c["dobj"]), GREEN if c["fase"] == "LLEGADA" else WHITE, "num")
        put(Z, F["small"], "HAS LLEGADO" if c["fase"] == "LLEGADA" else gtxt,
            (x, y - 6), GREEN if c["fase"] == "LLEGADA" else gcol, w)
        y += F["small"].get_height() + 10
        put(Z, F["tiny"], "ALTITUD", (x, y), DIM)
        put(Z, F["tiny"], "LLEGAS EN", (x + w * 0.5, y), DIM)
        y += F["tiny"].get_height() + 2
        put(Z, F["btn"], np_fmt(c["alt"]) if c["alt"] is not None else "-", (x, y), WHITE)
        put(Z, F["btn"], np_tiempo(c["eta"]), (x + w * 0.5, y), WHITE)
        y += F["btn"].get_height() + 14
    # recorrido
    if c["d0"] > 0 and c["fase"] != "LLEGADA":
        pct = max(0.0, min(1.0, 1 - c["dist"] / c["d0"]))
        rb = pygame.Rect(x, y, w, 14)
        pygame.draw.rect(Z, (42, 26, 8), rb, border_radius=3)
        pygame.draw.rect(Z, ORANGE, (rb.x, rb.y, int(rb.w * pct), rb.h), border_radius=3)
        put(Z, F["tiny"], f"recorrido {pct * 100:.0f} %", (x, rb.bottom + 4), DIM)
        y = rb.bottom + F["tiny"].get_height() + 10
    # abajo: botón FLECHA y planeta pequeño en superficie
    bh = 58
    rb = pygame.Rect(x, a.bottom - bh + 6, int(w * 0.6), bh)
    if c["pts"]:
        cerca = NAVP["modo"] == "cerca"
        pygame.draw.rect(Z, AMBAR if cerca else (40, 28, 8), rb, border_radius=8)
        pygame.draw.rect(Z, AMBAR, rb, 2, border_radius=8)
        put(Z, F["tiny"], "FLECHA", (rb.centerx, rb.y + 4), BLACK if cerca else DIM, anchor="midtop")
        put(Z, F["small"], "MÁS CERCANO" if cerca else "DESTINO", (rb.centerx, rb.bottom - 6),
            BLACK if cerca else AMBAR, rb.w - 10, anchor="midbottom")
        lz_hit(rb, "npmodo")
    if c["fase"] not in ("ÓRBITA", "PLANEO"):
        mr = pygame.Rect(x + w - 120, a.bottom - 120 + 6, 120, 120)
        if mr.y > y:
            np_esfera(Z, mr, c, pequena=True)

def np_abajo(Z, d, flags, now):
    c = np_calc(d, now)
    a = c2_marco(Z, "NAVEGACIÓN PLANETARIA")
    if c is None:
        return
    x, w = a.x, a.w
    y = a.y - 12
    fases = ("ÓRBITA", "PLANEO", "SUPERFICIE", "LLEGADA")
    cw = (w - 3 * 10) // 4
    ch = F["small"].get_height() + 8
    for i, f_ in enumerate(fases):
        rr = pygame.Rect(x + i * (cw + 10), y, cw, ch)
        on = f_ == c["fase"]
        pygame.draw.rect(Z, (GREEN if f_ == "LLEGADA" else ORANGE) if on else (42, 26, 8), rr, border_radius=5)
        put(Z, F["small"], f_, rr.center, BLACK if on else DIM, rr.w - 8, anchor="center")
    y += ch + 8
    yo, dp = c["yo"], c["dp"]
    txt = f"TÚ {yo[0]:.4f} / {yo[1]:.4f}".replace(".", ",")
    put(Z, F["tiny"], txt, (x, y), WHITE)
    put(Z, F["tiny"], f"DESTINO {dp[0]:.4f} / {dp[1]:.4f}".replace(".", ","), (x + w * 0.36, y), CYAN)
    if c["pts"]:
        put(Z, F["tiny"], f"{len(c['pts'])} PUNTOS MÁS EN EL MAPA", (x + w, y), AMBAR, anchor="topright")

# ---------------------------------------------------------------------------------------------------------------
# toques
# ---------------------------------------------------------------------------------------------------------------
def _np_modo(acc, X, Y):
    tap_flash(("npmodo",))
    NAVP["modo"] = "dest" if NAVP["modo"] == "cerca" else "cerca"
    plog("PLANETA: FLECHA " + ("AL MÁS CERCANO" if NAVP["modo"] == "cerca" else "AL DESTINO"))
    TAP_EV.set()

LZ_ACC["npmodo"] = _np_modo
def _np_vista(acc, X, Y):
    tap_flash(("npvista",))
    f_, esf = NAVP.get("esfera") or (None, True)
    NAVP["forzar"] = (f_, not esf)                       # hasta que cambie la fase
    TAP_EV.set()

LZ_ACC["npvista"] = _np_vista

# ---------------------------------------------------------------------------------------------------------------
# FIJAR PANTALLA: también vale para el planeta
# ---------------------------------------------------------------------------------------------------------------
_fix_tipo_v23b1 = fix_tipo

def fix_tipo(d, flags, now):
    k, mode, nom = _fix_tipo_v23b1(d, flags, now)
    if k == "modo" and _nav_real(d, flags, now, mode):
        return "nav", mode, "PLANETA"
    return k, mode, nom

def _nav_real(d, flags, now, mode):
    on, FIX["on"] = FIX["on"], False
    try:
        return nav_activa(d, flags, now, mode)
    finally:
        FIX["on"] = on

# ---------------------------------------------------------------------------------------------------------------
# enganche en el tablero (el combate, la exobiología y la minería van antes)
# ---------------------------------------------------------------------------------------------------------------
_lz_tablero_v23b1 = lz_tablero

def lz_tablero(S, d, flags, now):
    try:
        np_update(d or {}, now)
    except Exception as e:
        log_exc("planeta: llegada", e)
    if cfg.get("bigmode", "4") != "4":
        return _lz_tablero_v23b1(S, d, flags, now)
    mode = big_mode(d, flags)
    if str(mode).startswith("COMBATE"):
        return _lz_tablero_v23b1(S, d, flags, now)
    if mina2_on() and (bio_activa(d, flags, now, mode) or mina_asteroides(d, flags, now, mode)
                       or mina_planeta(d, flags, now, mode)):
        return _lz_tablero_v23b1(S, d, flags, now)
    try:
        act = nav_activa(d, flags, now, mode)
    except Exception as e:
        log_exc("planeta", e)
        act = False
    if not act:
        return _lz_tablero_v23b1(S, d, flags, now)
    if not lienzo_dibuja(S, lz_tab_cabecera, d, flags, now, "PLANETA"):
        return _lz_tablero_v23b1(S, d, flags, now)
    if cfg.get("perf"):
        pr = lz_real((700, 64, 10, 10))
        perf_draw(S, pr.x, pr.y)
    LZ["colr"] = None
    BIG["cellmap"] = []
    zonas = ((np_izq, 3, P2_L), (np_dch, 1001, P2_R), (np_abajo, 1002, C2_B))
    ok = all([lz_zona(S, fn, v, rc, d, flags, now) for fn, v, rc in zonas])
    BIG["rects"] = [(3, lz_real(rc)) for _, _, rc in zonas]
    if not ok:
        S.fill(BLACK)
        LZ["cel"] = {}
        return _lz_tablero_v23b1(S, d, flags, now)
    return True
