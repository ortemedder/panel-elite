# Panel Elite v2.0 · parte 44: v2.0b7 — EXPLORACIÓN a 1280x800 (con PANTALLA v2)
#   7 EXPLORACIÓN (submenú), 71 EXPLORACIÓN, 72 SISTEMA (órbitas), 73 EXOBIOLOGÍA, 74 YACIMIENTOS, 75 DIARIO y
#   76 ALIENÍGENAS, en el MENÚ (LZ_PANEL) y, las que salen en el tablero (71, 72, 73, 74), como cuadros (LZ_CELDA).
#   El SISTEMA usa el mismo dibujo de órbitas (view_orrery) en el hueco del lienzo, con su columna de datos nueva.
#   Los botones tocan el centro de su botón de 480x320; tocar un cuerpo del SISTEMA lo marca (acción propia).

# ---------------------------------------------------------------------------------------------------------------
# acciones propias de los toques (además de «old»): LZ_ACC[nombre](acc, X, Y) en coordenadas del lienzo / celda
# ---------------------------------------------------------------------------------------------------------------
LZ_ACC = {}

def lz_panel_toque(X, Y):
    for r, acc in reversed(LZ["phits"]):
        if not r.collidepoint(X, Y):
            continue
        if acc[0] == "old":
            on_tap(int(acc[1]), int(acc[2]))
        elif acc[0] in LZ_ACC:
            LZ_ACC[acc[0]](acc, X, Y)
        else:
            continue
        TAP_EV.set()
        return True
    return False

def lz_celda_old(xn, yn):
    bw, bh = BIG.get("w") or LW, BIG.get("h") or LH
    X, Y = xn * bw, yn * bh
    for v, (sub, k, hits) in list(LZ["cel"].items()):
        if not sub.collidepoint(X, Y):
            continue
        lx, ly = (X - sub.x) / k, (Y - sub.y) / k
        for r, acc in reversed(hits):
            if not r.collidepoint(lx, ly):
                continue
            if acc[0] in LZ_ACC:
                HDMIF["t"] = time.time()
                LZ_ACC[acc[0]](acc, lx, ly)
                TAP_EV.set()
                return True
            if acc[0] == "old":
                HDMIF["t"] = time.time()
                v0 = ui["view"]
                ui["view"] = v
                try:
                    on_tap(int(acc[1]), int(acc[2]))
                finally:
                    if ui["view"] == v:
                        ui["view"] = v0
                    else:
                        lienzo_menu()
                TAP_EV.set()
                return True
        return False
    return False

# ---------------------------------------------------------------------------------------------------------------
# 7 EXPLORACIÓN (submenú)
# ---------------------------------------------------------------------------------------------------------------
def lv_sub7(L, area, d, flags, now):
    for i, (n, name) in enumerate([("1", "EXPLORACIÓN"), ("2", "SISTEMA"), ("3", "EXOBIO"), ("4", "YACIM."), ("5", "DIARIO"),
                                   ("6", "ALIEN")]):
        lz_boton_v(L, lz_grid(area, i, 3, 2), n, name, F["num"], lit=flash.get((7, i), 0) > now, viejo=grid(i, 3, 2))

# ---------------------------------------------------------------------------------------------------------------
# 71 EXPLORACIÓN
# ---------------------------------------------------------------------------------------------------------------
def lv_explo(L, area, d, flags, now):
    ex = (d or {}).get("explo") or {}
    hs, hb, hg = F["small"].get_height(), F["btn"].get_height(), F["big"].get_height()
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 6
    total, scanned = ex.get("total"), ex.get("scanned", 0)
    put(L, F["small"], "CUERPOS ESCANEADOS", (x0, y), DIM)
    put(L, F["small"], "MAPEADOS", (x1, y), DIM, anchor="topright")
    xe = area.x + int(area.w * 0.36)
    if ex.get("edsm_n"):
        put(L, F["small"], f"EDSM: {ex['edsm_n']} cuerpos", (xe, y), BLUE)
    elif ex.get("edsm_st") == "bloqueado":
        put(L, F["small"], "EDSM bloqueado", (xe, y), RED)
    elif ex.get("edsm_st") == "error":
        put(L, F["small"], "EDSM sin respuesta", (xe, y), ORANGE)
    y += hs + 2
    done = total is not None and scanned >= total
    put(L, F["big"], f"{scanned} / {total if total is not None else '?'}", (x0, y), GREEN if done else ORANGE)
    put(L, F["big"], str(ex.get("mapped", 0)), (x1, y), ORANGE, anchor="topright")
    fss = ex.get("fss")
    bx = pygame.Rect(xe, y + (hg - hs - 6) // 2, int(area.w * 0.40), hs + 6)
    pygame.draw.rect(L, DIM, bx, 2)
    if fss is not None:
        pygame.draw.rect(L, BLUE, (bx.x + 3, bx.y + 3, int((bx.w - 6) * fss), bx.h - 6))
        put(L, F["small"], f"FSS {fss * 100:.0f}%", bx.center, WHITE, anchor="center")
    else:
        put(L, F["small"], "SIN ESCANEO FSS", bx.center, DIM, anchor="center")
    y += hg + 8
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8
    top = ex.get("top") or []
    sysname = ex.get("system") or ""
    pie = area.bottom - hb - 10
    if not top:
        msg = {"consultando": "Consultando EDSM...", "bloqueado": "EDSM bloqueado (¿fútbol?) · reintento cada 10 min"}.get(
            ex.get("edsm_st"), "Nada destacable escaneado aún")
        put(L, F["btn"], msg, (area.centerx, (y + pie) // 2), DIM, area.w - 40, anchor="center")
    rh = hb + 6
    per = max(1, (pie - 10 - hs - y) // rh)
    pages = max(1, (len(top) + per - 1) // per)
    pg = ui.get("page71", 0) % pages
    if pages > 1:
        put(L, F["small"], f"pág {pg + 1}/{pages}  (toca para pasar)", (area.centerx, pie - 14 - hs), DIM, anchor="midtop")
    c_cls, c_dist, c_est, c_val = x0 + int(area.w * 0.17), x0 + int(area.w * 0.62), x0 + int(area.w * 0.66), x1
    for row in top[pg * per:(pg + 1) * per]:
        name, cls, dist, first, mapped, val = row[:6]
        src = row[6] if len(row) > 6 else None
        short = name[len(sysname):].strip() if name.startswith(sysname) else name
        put(L, F["btn"], short or name, (x0, y), ORANGE, c_cls - x0 - 8)
        put(L, F["small"], cls, (c_cls, y + 4), ORANGE, c_dist - c_cls - 130)
        put(L, F["small"], f"{dist:,} ls".replace(",", "."), (c_dist, y + 4), DIM, anchor="topright")
        if src == "edsm":
            put(L, F["small"], "EDSM", (c_est + 40, y + 4), BLUE)
        else:
            put(L, F["small"], "1º" if first else "", (c_est, y + 4), GREEN)
            put(L, F["small"], "MAPEADO" if mapped else "SIN MAPEAR", (c_est + 40, y + 4), BLUE if mapped else DIM)
        put(L, F["small"], cr(val), (c_val, y + 4), ORANGE, anchor="topright")
        y += rh
    pygame.draw.line(L, DIM, (x0, pie - 6), (x1, pie - 6), 2)
    put(L, F["btn"], f"DATOS SIN VENDER  ~ {cr(ex.get('unsold'))} cr", (x0, pie), ORANGE)
    put(L, F["small"], f"{ex.get('unsold_n', 0)} cuerpos", (x1, pie + 4), DIM, anchor="topright")
    lz_hit(area, "old", W // 2, (TOP + H) // 2)                # tocar pasa de página (como antes)

# ---------------------------------------------------------------------------------------------------------------
# 72 SISTEMA (órbitas)
# ---------------------------------------------------------------------------------------------------------------
def lz_orbitas(L, mapa, d, flags, now, lateral):
    """Dibuja las órbitas (view_orrery) dentro de mapa (coordenadas del lienzo o la celda). Se dibujan en una
    superficie propia con origen en la esquina del mapa: así los textos sueltos de view_orrery (ZOOM, T+…) caen dentro."""
    global OR_AREA, draw_or_side
    mapa = pygame.Rect(mapa)
    rr = L._r(mapa).clip(L.real.get_rect())
    if rr.w < 10 or rr.h < 10:
        return
    S = ScaledSurf(L.real.subsurface(rr), L.sx, L.sy)
    keep = (OR_AREA, draw_or_side, orr.get("hits"), orr.get("scale"))
    OR_AREA = pygame.Rect(0, 0, mapa.w, mapa.h)
    draw_or_side = lateral
    ORR_XS[0] = (mapa.w / 2 - 14) / max(1, mapa.h / 2 - 14)
    orr["scale"] = None
    try:
        view_orrery(S, d, flags, now)
        LZ["orhits"] = [(n, x + mapa.x, y + mapa.y) for n, x, y in (orr.get("hits") or [])]
    finally:
        OR_AREA, draw_or_side, orr["hits"], orr["scale"] = keep
        ORR_XS[0] = 1.0
    BIG["fast"] = True                                          # las órbitas se mueven
    lz_hit(mapa, "orsel")

def _lz_or_sel(acc, X, Y):
    best = min(LZ.get("orhits") or [], key=lambda h: (h[1] - X) ** 2 + (h[2] - Y) ** 2, default=None)
    if best and (best[1] - X) ** 2 + (best[2] - Y) ** 2 < 40 ** 2:
        orr["sel"] = best[0]

LZ_ACC["orsel"] = _lz_or_sel

def lz_or_cuerpo(L, d, orbits, box, sel=True):
    """Ficha del cuerpo marcado (o del destino / el más valioso sin mapear en el tablero)."""
    d = d or {}
    if sel:
        o = next((x for x in orbits if x.get("id") == orr["sel"]), None)
    else:
        want = [((d.get("dest") or {}).get("name")), d.get("body")]
        o = next((x for w_ in want if w_ for x in orbits if x.get("name") == w_), None)
        if o is None:
            cand = [x for x in orbits if x.get("name") and not x.get("mapped")]
            o = max(cand, key=lambda x: x.get("value") or 0, default=None)
    hs = F["small"].get_height()
    x, y = box.x + 12, box.y + 8
    if not o or not o.get("name"):
        if sel:
            put(L, F["small"], "Toca un cuerpo", (x, y), DIM)
            put(L, F["small"], "para ver sus datos", (x, y + hs + 2), DIM)
        return False
    system = (d.get("explo") or {}).get("system") or ""
    nm = o["name"]
    short = nm[len(system):].strip() if system and nm.startswith(system) else nm
    w = box.w - 24
    put(L, F["btn"], short or nm, (x, y), ORANGE, w); y += F["btn"].get_height() + 2
    put(L, F["small"], o.get("cls", ""), (x, y), bcol(o), w); y += hs + 2
    put(L, F["small"], f"{o.get('dist', 0):,} ls".replace(",", "."), (x, y), DIM)
    put(L, F["small"], ("1º " if o.get("first") else "") + ("MAPEADO" if o.get("mapped") else ""), (box.right - 12, y), GREEN, anchor="topright")
    y += hs + 2
    if sel and o.get("P"):
        days = o["P"] / 86400
        put(L, F["small"], f"Órbita: {days:,.1f} días".replace(",", "X").replace(".", ",").replace("X", "."), (x, y), DIM, w); y += hs + 2
    if sel and o.get("r"):
        put(L, F["small"], f"Radio: {o['r']:,} km".replace(",", "."), (x, y), DIM, w); y += hs + 2
    put(L, F["small"], f"~ {cr(o.get('value'))} cr", (x, y), ORANGE, w); y += hs + 2
    if sel and o.get("src") == "edsm":
        put(L, F["small"], "Fuente: EDSM (pos. aprox.)", (x, y), BLUE, w)
    return True

def lv_sistema(L, area, d, flags, now):
    """SISTEMA en el MENÚ: órbitas a la izquierda y columna de datos y botones a la derecha."""
    xr = area.x + int(area.w * 0.66)
    mapa = pygame.Rect(area.x + 4, area.y + 4, xr - area.x - 12, area.h - 8)
    lado = pygame.Rect(xr + 4, area.y + 4, area.right - xr - 10, area.h - 8)
    orbits = (d or {}).get("orbits") or []
    lz_orbitas(L, mapa, d, flags, now, lambda s, d_, o_: None)
    pygame.draw.line(L, DIM, (xr, area.y + 4), (xr, area.bottom - 4), 2)
    hb = F["btn"].get_height() + 22
    zb = pygame.Rect(lado.x, lado.bottom - 4 * hb - 3 * 10, lado.w, 4 * hb + 3 * 10)
    lz_or_cuerpo(L, d, orbits, pygame.Rect(lado.x, lado.y, lado.w, zb.y - lado.y - 10))
    w2 = (lado.w - 10) // 2
    rm = pygame.Rect(zb.x, zb.y, w2, hb); rp = pygame.Rect(zb.x + w2 + 10, zb.y, w2, hb)
    lz_boton_v(L, rm, "−", None, F["big"], lit=flash.get((72, "menos"), 0) > now, viejo=or_btn("menos"))
    lz_boton_v(L, rp, "+", None, F["big"], lit=flash.get((72, "mas"), 0) > now, viejo=or_btn("mas"))
    put(L, F["small"], SPEEDS[orr["speed"]][1], (lado.centerx, zb.y - 6), ORANGE, lado.w, anchor="midbottom")
    y = zb.y + hb + 10
    lz_boton_v(L, (lado.x, y, lado.w, hb), "SEGUIR" if orr["paused"] else "PAUSA", None, F["btn"], filled=orr["paused"], viejo=or_btn("pausa"))
    y += hb + 10
    zoomed = orr["focus"] is not None
    lz_boton_v(L, (lado.x, y, lado.w, hb), "SISTEMA" if zoomed else "ZOOM", None, F["btn"], dim=not zoomed and orr["sel"] is None,
               filled=zoomed, viejo=or_btn("zoom"))
    y += hb + 10
    lz_boton_v(L, (lado.x, y, lado.w, hb), "AHORA", None, F["btn"], lit=flash.get((72, "ahora"), 0) > now, viejo=or_btn("ahora"))

def lc_sistema(L, d, flags, now):
    """SISTEMA en el tablero: órbitas en todo el cuadro y la ficha del destino arriba a la derecha."""
    area = pygame.Rect(0, 0, CW0, CH0)
    orbits = (d or {}).get("orbits") or []
    lz_orbitas(L, area, d, flags, now, lambda s, d_, o_: None)
    box = pygame.Rect(CW0 - 250, 4, 246, 4 * F["small"].get_height() + F["btn"].get_height() + 22)
    pygame.draw.rect(L, BLACK, box)
    if lz_or_cuerpo(L, d, orbits, box, sel=False):
        pygame.draw.rect(L, DIM, box, 2, border_radius=6)
    else:
        pygame.draw.rect(L, BLACK, box)
    put(L, F["small"], SPEEDS[orr["speed"]][1] + ("  ·  PAUSA" if orr["paused"] else ""), (CW0 - 8, CH0 - 6), DIM, anchor="bottomright")

# ---------------------------------------------------------------------------------------------------------------
# 73 EXOBIOLOGÍA
# ---------------------------------------------------------------------------------------------------------------
def lv_bio(L, area, d, flags, now):
    b = (d or {}).get("bio") or {}
    hs, hb, hg = F["small"].get_height(), F["btn"].get_height(), F["big"].get_height()
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 6
    put(L, F["small"], "CUERPO", (x0, y), DIM)
    sig = b.get("signals")
    put(L, F["small"], f"SEÑALES BIO: {sig if sig is not None else '?'}", (x1, y), DIM, anchor="topright"); y += hs + 2
    put(L, F["btn"], b.get("body") or "No estás en un planeta", (x0, y), ORANGE if b.get("body") else DIM, x1 - x0); y += hb + 6
    done = set(b.get("done") or [])
    gx = x0
    for g in b.get("genuses") or []:
        t = ("OK " if g in done else "") + g
        w_ = tw_(F["small"], t) + 22
        if gx + w_ > x1:
            break
        pygame.draw.rect(L, GREEN if g in done else DIM, (gx, y, w_ - 8, hs + 8), 2, border_radius=5)
        put(L, F["small"], t, (gx + 7, y + 4), GREEN if g in done else ORANGE)
        gx += w_
    y += hs + 16
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 10
    pie = area.bottom - hb - 10
    brujula_y = pie - 10 - 64
    if not b.get("species"):
        put(L, F["btn"], "Sin muestreo en curso", (area.centerx, (y + brujula_y) // 2), DIM, anchor="center")
    else:
        step = b.get("step", 0)
        put(L, F["big"], b["species"].upper(), (x0, y), GREEN if step >= 3 else ORANGE, area.w - 200)
        for k in range(3):
            pygame.draw.circle(L, ORANGE, (x1 - 110 + k * 46, y + hg // 2), 16, 0 if k < step else 3)
        y += hg + 4
        put(L, F["small"], b.get("variant") or "", (x0, y), DIM, area.w * 0.45)
        val = b.get("value")
        if val:
            txt = ("" if b.get("exact") else "~") + cr(val) + " cr"
            if b.get("bonus"):
                txt += f"  x5 = {cr(val * 5)}"
            put(L, F["btn"], txt, (x1, y - 4), GREEN if b.get("bonus") else ORANGE, area.w * 0.5, anchor="topright")
        y += hs + 10
        pts, R = b.get("pts") or [], b.get("R")
        lat, lon, rng = b.get("lat"), b.get("lon"), b.get("range", 100)
        if step >= 3:
            put(L, F["big"], "MUESTRA COMPLETA", (area.centerx, y + hg), GREEN, anchor="center")
        elif pts and R and lat is not None:
            dist = min(hav(p, (lat, lon), R) for p in pts)
            ok = dist >= rng
            put(L, F["num"], f"{dist:,.0f} m".replace(",", "."), (x0, y), GREEN if ok else RED)
            put(L, F["btn"], f"mín. {rng} m", (x1, y + 6), DIM, anchor="topright")
            put(L, F["small"], "PUEDES MUESTREAR" if ok else "ALÉJATE", (x1, y + hb + 10), GREEN if ok else RED, anchor="topright")
            yb = y + F["num"].get_height() + 6
            bx = pygame.Rect(x0, yb, x1 - x0, max(12, hs // 2 + 6))
            pygame.draw.rect(L, DIM, bx, 2)
            pygame.draw.rect(L, GREEN if ok else RED, (bx.x + 3, bx.y + 3, int((bx.w - 6) * min(1, dist / rng)), bx.h - 6))
        else:
            put(L, F["btn"], f"Distancia mínima del género: {rng} m", (x0, y + 10), DIM, x1 - x0)
    lz_brujula_area(L, d, b, pygame.Rect(area.x, brujula_y, area.w, 64))
    pygame.draw.line(L, DIM, (x0, pie - 6), (x1, pie - 6), 2)
    put(L, F["btn"], f"MUESTRAS SIN VENDER: {b.get('unsold', 0)}", (x0, pie), ORANGE)
    if b.get("unsold_cr"):
        put(L, F["btn"], f"~ {cr(b['unsold_cr'])} cr", (x1, pie), ORANGE, anchor="topright")

def lz_brujula_area(L, d, b, r):
    """Como lc_brujula (EN VIVO), en la franja r: brújula a la nave y NAVE AQUÍ."""
    ship, lat, lon, R = ship_pos(b), b.get("lat"), b.get("lon"), b.get("R")
    out = bool((d or {}).get("Flags", 0) & (1 << 26)) or bool((d or {}).get("Flags2", 0) & 1)
    SHIPOV["cur"] = (lat, lon) if (out and lat is not None) else None
    if out and lat is not None and R:
        bt = pygame.Rect(r.x + int(r.w * 0.40), r.y + 8, int(r.w * 0.25), r.h - 16)
        lit = flash.get(("nave", 0), 0) > time.time()
        pygame.draw.rect(L, WHITE if lit else ORANGE, bt, 0 if lit else 2, border_radius=6)
        put(L, F["small"], "NAVE AQUÍ", bt.center, BLACK if lit else ORANGE, bt.w - 10, anchor="center")
        lz_hit(bt, "naveaqui")
    if not ship or lat is None or not R or not out:
        return
    pygame.draw.line(L, DIM, (r.x + 8, r.y), (r.right - 8, r.y), 1)
    dist = hav(ship, (lat, lon), R)
    p1, p2, dl = math.radians(lat), math.radians(ship[0]), math.radians(ship[1] - lon)
    brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                  math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
    hdg = b.get("hdg")
    cx, cy, rr = r.x + 34, r.y + r.h // 2, r.h // 2 - 8
    pygame.draw.circle(L, DIM, (cx, cy), rr, 2)
    if hdg is not None:
        a = math.radians(brg - hdg)
        pt = lambda k, da: (cx + rr * k * math.sin(a + da), cy - rr * k * math.cos(a + da))
        pygame.draw.polygon(L, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
    txt = f"{dist / 1000:.1f} km".replace(".", ",") if dist >= 1000 else f"{dist:.0f} m"
    put(L, F["tiny"], "NAVE", (r.x + 72, r.y + 6), DIM)
    put(L, F["big"], txt, (r.x + 72, r.y + r.h - F["big"].get_height() - 2), GREEN, int(r.w * 0.30))
    put(L, F["btn"], f"rumbo {brg:.0f}°", (r.right - 10, r.y + 6), ORANGE, anchor="topright")
    if hdg is not None:
        put(L, F["small"], f"vas a {hdg:.0f}°", (r.right - 10, r.bottom - F["small"].get_height() - 4), DIM, anchor="topright")

def _lz_nave_aqui(acc, X, Y):
    ship_here()

LZ_ACC["naveaqui"] = _lz_nave_aqui

# ---------------------------------------------------------------------------------------------------------------
# 74 YACIMIENTOS
# ---------------------------------------------------------------------------------------------------------------
def lv_rings(L, area, d, flags, now):
    R = (d or {}).get("rings") or {}
    hs, hb, hg = F["small"].get_height(), F["btn"].get_height(), F["big"].get_height()
    x0, x1 = area.x + 14, area.right - 14
    if not R.get("planet"):
        put(L, F["btn"], "Acércate a un planeta", area.center, DIM, anchor="center"); return
    y = area.y + 6
    put(L, F["big"], R["planet"].upper(), (x0, y), ORANGE, area.w * 0.7)
    if R.get("reserve"):
        put(L, F["small"], "RESERVAS", (x1, y), DIM, anchor="topright")
        put(L, F["btn"], R["reserve"], (x1, y + hs), RES_COL.get(R["reserve"], ORANGE), anchor="topright")
    y += hg + 8
    sig = R.get("signals") or []
    put(L, F["small"], "SEÑALES DEL PLANETA", (x0, y), DIM); y += hs + 4
    if not sig:
        put(L, F["small"], "sin datos: escanea el planeta (FSS) o mapéalo con la sonda (DSS)", (x0, y), DIM, x1 - x0); y += hs + 8
    else:
        x = x0
        for name, c in sig:
            low = name.lower()
            col = GREEN if ("bio" in low) else BLUE if ("geo" in low) else ORANGE
            txt = f"{name} x{c}"
            w_ = tw_(F["btn"], txt) + 30
            if x + w_ > x1:
                x = x0; y += hb + 14
            pygame.draw.rect(L, col, (x, y, w_ - 10, hb + 8), 2, border_radius=6)
            put(L, F["btn"], txt, (x + 10, y + 4), col)
            x += w_
        y += hb + 20
    rings = R.get("rings") or []
    if not rings:
        return
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8
    here = R.get("here") or ""
    for name, cls, hs_ in rings:
        if y > area.bottom - hb - 30:
            break
        inside = bool(here) and here.endswith(name)
        r = pygame.Rect(area.x + 10, y, area.w - 20, hb + 16 + (hb + 6) * max(1, (len(hs_ or []) + 1) // 2))
        r.h = min(r.h, area.bottom - 4 - y)
        pygame.draw.rect(L, GREEN if inside else DIM, r, 2, border_radius=8)
        put(L, F["btn"], name.upper(), (r.x + 14, r.y + 6), ORANGE, r.w * 0.3)
        put(L, F["small"], cls, (r.x + 14 + int(r.w * 0.32), r.y + 10), BLUE, r.w * 0.4)
        if inside:
            put(L, F["small"], "ESTÁS AQUÍ", (r.right - 14, r.y + 10), GREEN, anchor="topright")
        yy = r.y + hb + 12
        if not hs_:
            put(L, F["small"], "sin sondear: usa la sonda de superficie en el anillo", (r.x + 14, yy + 2), DIM, r.w - 28)
        else:
            for k, (m, c) in enumerate(hs_):
                if yy + (k // 2) * (hb + 6) > r.bottom - hb:
                    break
                put(L, F["btn"], f"{m}  x{c}", (r.x + 14 + (k % 2) * (r.w // 2), yy + (k // 2) * (hb + 6)),
                    GREEN if c >= 2 else WHITE, r.w // 2 - 24)
        y = r.bottom + 10

# ---------------------------------------------------------------------------------------------------------------
# 75 DIARIO DE EXPLORACIÓN
# ---------------------------------------------------------------------------------------------------------------
def lv_diary(L, area, d, flags, now):
    X = (d or {}).get("exdiary") or {}
    hs, hb, hg = F["small"].get_height(), F["btn"].get_height(), F["big"].get_height()
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 6
    secs = int(now - (X.get("start") or now))
    put(L, F["small"], f"SESIÓN DE EXPLORACIÓN · {secs // 3600}h {secs % 3600 // 60:02d}m", (x0, y), DIM); y += hs + 10
    rows = [("SISTEMAS VISITADOS", X.get("systems", 0), WHITE), ("AÑOS LUZ", X.get("ly", 0), WHITE),
            ("CUERPOS ESCANEADOS", X.get("scanned", 0), WHITE), ("1º DESCUBRIMIENTOS", X.get("first", 0), GREEN),
            ("CUERPOS MAPEADOS", X.get("mapped", 0), WHITE), ("1º MAPEADOS", X.get("first_mapped", 0), GREEN),
            ("MUESTRAS BIO", X.get("bio", 0), WHITE), ("SEÑALES VISITADAS", X.get("signals", 0), WHITE)]
    half = area.w // 2
    for k, (lab, val, col) in enumerate(rows):
        xa = x0 if k % 2 == 0 else area.x + half + 14
        put(L, F["small"], lab, (xa, y + (hg - hs) // 2), DIM)
        put(L, F["big"], f"{val:,}".replace(",", "."), (xa + half - 40, y), col, anchor="topright")
        if k % 2 == 1:
            y += hg + 10
    y += 10
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 14
    tot = (X.get("unsold") or 0) + (X.get("unsold_bio") or 0)
    put(L, F["small"], "SIN VENDER (exploración + bio)", (x0, y + (hg - hs) // 2), DIM)
    put(L, F["big"], f"{cr(tot)} cr", (x1, y), RED if tot >= 50e6 else ORANGE, anchor="topright"); y += hg + 10
    if X.get("dsol") is not None:
        put(L, F["small"], "DISTANCIA A SOL", (x0, y + 4), DIM)
        put(L, F["btn"], f"{X['dsol']:,.0f} al".replace(",", "."), (x1, y), BLUE, anchor="topright"); y += hb + 8
    if X.get("dst") is not None:
        put(L, F["small"], f"A LA ÚLTIMA ESTACIÓN ({X.get('stname') or '?'})", (x0, y + 4), DIM, area.w * 0.7)
        put(L, F["btn"], f"{X['dst']:,.0f} al".replace(",", "."), (x1, y), BLUE, anchor="topright")

# ---------------------------------------------------------------------------------------------------------------
# 76 ALIENÍGENAS
# ---------------------------------------------------------------------------------------------------------------
def lv_alien(L, area, d, flags, now):
    A = (d or {}).get("alien") or {}
    hs, hb, hg = F["small"].get_height(), F["btn"].get_height(), F["big"].get_height()
    x0, x1 = area.x + 14, area.right - 14
    tab = ui.get("alientab", 0)
    for i, t in enumerate(("THARGOIDES", "GUARDIANES")):
        r = pygame.Rect(area.x + 8 + i * (area.w // 2), area.y + 4, area.w // 2 - 16, hb + 16)
        on = tab == i
        pygame.draw.rect(L, (TGCOL if i == 0 else BLUE) if on else DIM, r, 0 if on else 2, border_radius=8)
        put(L, F["btn"], t, r.center, BLACK if on else DIM, anchor="center")
        lz_hit(r, "old", W // 2, (TOP + H) // 2)              # cualquier toque cambia de pestaña (como antes)
    y = area.y + hb + 34
    if tab == 0:
        w = A.get("tgwar")
        if w:
            put(L, F["small"], "GUERRA EN EL SISTEMA", (x0, y + (hg - hs) // 2), DIM)
            put(L, F["big"], w["state"], (x0 + int(area.w * 0.36), y), RED if w["state"] in ("INVASIÓN", "CONTROLADO", "BASTIÓN") else ORANGE)
            y += hg + 6
            pr = w.get("progress")
            if pr is not None:
                bx = pygame.Rect(x0, y, x1 - x0 - 150, hs + 4)
                pygame.draw.rect(L, DIM, bx, 2)
                pygame.draw.rect(L, TGCOL, (bx.x + 3, bx.y + 3, int((bx.w - 6) * max(0, min(1, pr))), bx.h - 6))
                put(L, F["btn"], f"{pr * 100:.0f}%", (x1, y - 4), WHITE, anchor="topright"); y += hs + 14
            extra = " · ".join(x for x in (f"puertos restantes {w['ports']}" if w.get("ports") else "", str(w.get("time") or "")) if x)
            if extra:
                put(L, F["small"], extra, (x0, y), DIM, x1 - x0); y += hs + 8
        else:
            put(L, F["btn"], "Sistema sin guerra thargoide", (x0, y), GREEN); y += hb + 10
        put(L, F["small"], "DERRIBOS THARGOIDES (sesión)", (x0, y + 4), DIM)
        put(L, F["btn"], f"{A.get('tgk', 0)}  ·  {cr(A.get('tgb', 0))} cr", (x1, y), TGCOL, anchor="topright"); y += hb + 10
        rows = A.get("tg") or []
        title, col = "MATERIALES THARGOIDES", TGCOL
    else:
        bp = A.get("bp") or {}
        put(L, F["small"], "PLANOS GUARDIANES", (x0, y), DIM); y += hs + 4
        for k, (lab, key) in enumerate((("MÓDULO", "module"), ("ARMA", "weapon"), ("NAVE", "vessel"))):
            xa = x0 + k * (area.w // 3)
            put(L, F["small"], lab, (xa, y + (hg - hs) // 2), DIM)
            put(L, F["big"], str(bp.get(key, 0)), (xa + area.w // 3 - 60, y), BLUE, anchor="topright")
        y += hg + 8
        rows = A.get("gd") or []
        title, col = "MATERIALES Y DATOS GUARDIANES", BLUE
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8
    put(L, F["small"], title, (x0, y), DIM); y += hs + 6
    if not rows:
        put(L, F["small"], "ninguno", (x0, y), DIM)
    half = area.w // 2
    for k, (n, c) in enumerate(rows):
        cx, cy = (x0 if k % 2 == 0 else area.x + half + 14), y + (k // 2) * (hs + 6)
        if cy > area.bottom - hs - 4:
            break
        put(L, F["small"], n, (cx, cy), WHITE, half - 110)
        put(L, F["small"], str(c), (cx + half - 40, cy), col, anchor="topright")

LZ_PANEL.update({7: lv_sub7, 71: lv_explo, 72: lv_sistema, 73: lv_bio, 74: lv_rings, 75: lv_diary, 76: lv_alien})
for _v, _fn in ((71, lv_explo), (73, lv_bio), (74, lv_rings), (75, lv_diary), (76, lv_alien)):
    LZ_CELDA[_v] = (lambda fn: (lambda L, d, flags, now: fn(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now)))(_fn)
LZ_CELDA[72] = lc_sistema
