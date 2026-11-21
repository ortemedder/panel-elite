# Panel Elite v2.0 · parte 45: v2.0b8 — NAVEGACIÓN a 1280x800 (con PANTALLA v2)
#   3 NAVEGACIÓN (caras RUTA/DESTINO, SISTEMA y POWERPLAY, ahora con sus botones arriba y RUTA EXT.), 212 sistema de la
#   ruta, 216 RUTA EXTERNA y 190 VIAJES, en el MENÚ (LZ_PANEL) y, NAVEGACIÓN y VIAJES, como cuadros del tablero (LZ_CELDA).
#   Las listas y el mapa de VIAJES guardan su estado propio (el panel viejo de 480x320 sigue dibujándose por debajo).

LZ["rut"] = {"p": {"off": 0, "key": None, "max": 0, "nvis": 1}, "c": {"off": 0, "key": None, "max": 0, "nvis": 1}}
LZ["vj"] = {}

def lz_alturas():
    return F["small"].get_height(), F["btn"].get_height(), F["big"].get_height()

def lz_chips(L, items, x0, x1, y, font, gap=10, pad=10):
    """Etiquetas con borde, en filas; devuelve la y de debajo."""
    items = [(t, c) for t, c in items if t]
    if not items:
        return y
    h = font.get_height() + 8
    x = x0
    for t, col in items:
        w_ = tw_(font, t) + 2 * pad
        if x + w_ > x1 and x > x0:
            x = x0; y += h + 8
        pygame.draw.rect(L, col, (x, y, min(w_, x1 - x), h), 2, border_radius=6)
        put(L, font, t, (x + pad, y + 4), col, x1 - x - 2 * pad)
        x += w_ + gap
    return y + h + 10

def lz_flecha_btn(L, r, arriba, on):
    col = ORANGE if on else DIM
    pygame.draw.rect(L, col, r, 3, border_radius=8)
    cx, cy, s = r.centerx, r.centery, min(r.w, r.h) // 4
    pts = [(cx - s, cy + s // 2), (cx + s, cy + s // 2), (cx, cy - s)] if arriba else \
          [(cx - s, cy - s // 2), (cx + s, cy - s // 2), (cx, cy + s)]
    pygame.draw.polygon(L, col, pts)

def lz_foto_destino(L, r, k, label):
    """Foto del destino (portanaves, estación...) con su nombre abajo."""
    rr = L._r(r)
    img = bg_img(k, rr.w, rr.h, 230)
    if img is not None:
        L.real.blit(img, rr.topleft)
    col = BLUE if k == "sq" else ORANGE
    hs = F["small"].get_height()
    pygame.draw.rect(L, BLACK, (r.x + 3, r.bottom - hs - 7, r.w - 6, hs + 4))
    pygame.draw.rect(L, col, r, 3, border_radius=6)
    put(L, F["small"], label.replace("PORTANAVES DE ESCUADRÓN", "ESCUADRÓN"), (r.centerx, r.bottom - hs // 2 - 5), col, r.w - 12,
        anchor="center")

def lz_ing(L, d, r):
    """Ficha del ingeniero del sistema: cara, nombre, rango, dónde está y lo que mejora."""
    e = eng_here(d)
    if not e:
        return False
    hs, hb, hg = lz_alturas()
    pygame.draw.rect(L, BLACK, r)
    pygame.draw.rect(L, BLUE, r, 2, border_radius=8)
    ph = pygame.Rect(r.x + 8, r.y + 8, int((r.h - 16) * 240 / 210), r.h - 16)
    rr = L._r(ph)
    img = ship_img(os.path.join(_ENGDIR, f"ing_{e['key']}.jpg"), rr.w, rr.h, 255)
    if img is not None:
        L.real.blit(img, rr.topleft)
    x = ph.right + 14
    wd = r.right - x - 12
    st, col = eng_status(e, d)
    put(L, F["btn"], e["name"].upper(), (x, r.y + 6), BLUE, wd - tw_(F["small"], st) - 20)
    put(L, F["small"], st, (r.right - 12, r.y + 6 + (hb - hs) // 2), col, anchor="topright")
    y = r.y + 10 + hb
    put(L, F["small"], eng_where(e), (x, y), ORANGE, wd); y += hs + 6
    mods = sorted(e.get("mods") or [], key=lambda m: -int(m[1]) if m[:1] == "G" and m[1:2].isdigit() else 0)
    line = ""
    for m in mods:
        t = (line + "  ·  " if line else "") + m
        if tw_(F["small"], t) > wd and line:
            if y + hs > r.bottom - 6:
                return True
            put(L, F["small"], line, (x, y), WHITE, wd); y += hs + 4; line = m
        else:
            line = t
    if line and y + hs <= r.bottom - 6:
        put(L, F["small"], line, (x, y), WHITE, wd)
    return True

def lz_franja_pol(L, area, d):
    """Línea de política abajo (gobierno · alianza · seguridad · estado). Devuelve la y de arriba."""
    S = (d or {}).get("sysinfo") or {}
    t = " · ".join(p for p in (S.get("gov"), S.get("alleg"), S.get("sec"), S.get("fstate")) if p)
    if not t:
        return area.bottom
    hs = F["small"].get_height()
    sec = (S.get("sec") or "").lower()
    col = GREEN if "alta" in sec or "high" in sec else ORANGE if "media" in sec or "medium" in sec else RED
    y = area.bottom - hs - 6
    pygame.draw.line(L, DIM, (area.x + 14, y - 6), (area.right - 14, y - 6), 2)
    put(L, F["small"], t, (area.x + 14, y), col, area.w - 28)
    return y - 10

# ---------------------------------------------------------------------------------------------------------------
# cara SISTEMA (política y facciones)
# ---------------------------------------------------------------------------------------------------------------
def lz_tick_graf(L, d, r):
    E = (d or {}).get("etick") or {}
    H_ = E.get("hist") or []
    if len(H_) < 2 or E.get("sys") != (d or {}).get("system"):
        return False
    pygame.draw.rect(L, BLACK, r)
    pygame.draw.rect(L, DIM, r, 2, border_radius=5)
    pts = []
    for k, t in enumerate(H_):
        g = time.gmtime(t); hh = g.tm_hour + g.tm_min / 60
        pts.append((r.x + 8 + k * (r.w - 16) / max(1, len(H_) - 1), r.bottom - 8 - hh / 24 * (r.h - 16)))
    pygame.draw.lines(L, ORANGE, False, pts, 2)
    for p_ in pts:
        pygame.draw.circle(L, ORANGE, (int(p_[0]), int(p_[1])), 4)
    put(L, F["tiny"], "hora del tick (UTC)", (r.x, r.y - F["tiny"].get_height() - 2), DIM)
    return True

def lz_pol(L, area, d, now):
    S = (d or {}).get("sysinfo") or {}
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    if not S.get("faction") and not S.get("gov"):
        put(L, F["btn"], "Sin datos del sistema", area.center, DIM, anchor="center"); return
    sec = (S.get("sec") or "").lower()
    seccol = GREEN if "alta" in sec or "high" in sec else ORANGE if "media" in sec or "medium" in sec else RED
    pop = S.get("pop")
    popt = ((f"{pop / 1e9:.1f} mil M" if pop >= 1e9 else f"{pop / 1e6:.1f} M" if pop >= 1e6 else f"{pop:,}".replace(",", ".")).replace(".", ",", 1 if pop >= 1e6 else 0)
            + " hab.") if pop else ""
    y = lz_chips(L, [(S.get("gov"), ORANGE), (S.get("alleg"), BLUE), (S.get("sec"), seccol), (S.get("econ"), WHITE), (popt, DIM)],
                 x0, x1, area.y + 6, F["small"])
    xv = x0 + int(area.w * 0.17)
    put(L, F["small"], "CONTROLA", (x0, y + (hb - hs) // 2), DIM)
    fst = S.get("fstate")
    put(L, F["btn"], S.get("faction") or "?", (xv, y), ORANGE, x1 - xv - (tw_(F["small"], fst) + 20 if fst else 0))
    if fst:
        put(L, F["small"], fst, (x1, y + (hb - hs) // 2), RED if fst in ("GUERRA", "GUERRA CIVIL", "BLOQUEO", "DISTURBIOS", "ATAQUE PIRATA") else GREEN,
            anchor="topright")
    y += hb + 6
    put(L, F["small"], "POWERPLAY", (x0, y + (hb - hs) // 2), DIM)
    if S.get("pp"):
        pst = S.get("ppstate") or ""
        put(L, F["btn"], S["pp"], (xv, y), BLUE, x1 - xv - tw_(F["small"], pst) - 20)
        put(L, F["small"], pst, (x1, y + (hb - hs) // 2), BLUE, anchor="topright")
    else:
        rivals = list(S.get("powers") or [])
        put(L, F["small"], ("en disputa: " + ", ".join(rivals)) if rivals else "sin potencia", (xv, y + (hb - hs) // 2), DIM, x1 - xv)
    y += hb + 8
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8
    # abajo: tick y BGS, y encima la estación con la gráfica del tick
    lines = bgs_lines(d, now)
    yb = area.bottom - 4 - len(lines) * (hs + 4)
    for k, (txt, col) in enumerate(lines):
        put(L, F["small"], txt, (x0, yb + k * (hs + 4)), col, x1 - x0)
    gh = 0
    if lines:
        gr = pygame.Rect(x1 - 300, yb - 8 - 90, 300, 90) if area.h > 400 else pygame.Rect(x1 - 200, yb - 6 - 56, 200, 56)
        if lz_tick_graf(L, d, gr):
            gh = gr.h + 8
    yst = yb - 6 - max(hs, gh)
    if S.get("st_name"):
        t = f"{S['st_name']} · {S.get('st_faction') or '?'} · {S.get('st_gov') or ''}"
        put(L, F["small"], t, (x0, yb - 6 - hs), ORANGE, x1 - x0 - (310 if gh else 0))
        yst = min(yst, yb - 12 - hs)
    # facciones
    rh = max(hs, hb) + 8 if area.h > 400 else hs + 8
    fn = F["btn"] if area.h > 400 else F["small"]
    cb, wb = x0 + int(area.w * 0.36), int(area.w * 0.24)
    for name, infl, st_, rep in (S.get("facs") or [])[:8]:
        if y + rh > yst:
            break
        put(L, fn, name, (x0, y), ORANGE if name == S.get("faction") else WHITE, cb - x0 - 12)
        fh = fn.get_height()
        bx = pygame.Rect(cb, y + fh // 2 - 8, wb, 16)
        pygame.draw.rect(L, DIM, bx, 2)
        pygame.draw.rect(L, BLUE, (bx.x + 3, bx.y + 3, int((bx.w - 6) * min(100, infl) / 100), bx.h - 6))
        put(L, F["small"], f"{infl:.0f}%", (bx.right + 80, y + (fh - hs) // 2), WHITE, anchor="topright")
        put(L, F["small"], st_ or "", (bx.right + 96, y + (fh - hs) // 2), RED if st_ in ("GUERRA", "GUERRA CIVIL", "BLOQUEO") else DIM,
            x1 - bx.right - 96 - 70)
        if rep is not None:
            put(L, F["small"], f"{rep:+.0f}", (x1, y + (fh - hs) // 2), GREEN if rep >= 35 else RED if rep <= -35 else ORANGE, anchor="topright")
        y += rh

# ---------------------------------------------------------------------------------------------------------------
# cara POWERPLAY
# ---------------------------------------------------------------------------------------------------------------
def lz_pp(L, area, d, now):
    S = (d or {}).get("sysinfo") or {}
    me = (d or {}).get("ppme") or {}
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 6
    put(L, F["small"], "POWERPLAY DEL SISTEMA", (x0, y), DIM)
    if S.get("ppstate"):
        put(L, F["small"], S["ppstate"], (x1, y), BLUE, anchor="topright")
    y += hs + 4
    pp, mine = S.get("pp"), me.get("power")
    if pp:
        put(L, F["big"], pp.upper(), (x0, y), BLUE, area.w - 300)
        if mine:
            put(L, F["btn"], "TU POTENCIA" if pp == mine else "RIVAL", (x1, y + (hg - hb) // 2), GREEN if pp == mine else RED, anchor="topright")
        y += hg + 10
        prog = S.get("pp_prog")
        if prog is not None:
            put(L, F["small"], "CONTROL", (x0, y + (hb - hs) // 2), DIM)
            bx = pygame.Rect(x0 + int(area.w * 0.15), y + hb // 2 - 12, int(area.w * 0.62), 24)
            pygame.draw.rect(L, DIM, bx, 2)
            pygame.draw.rect(L, BLUE, (bx.x + 3, bx.y + 3, int((bx.w - 6) * max(0, min(1, prog))), bx.h - 6))
            put(L, F["btn"], f"{prog * 100:.0f}%", (x1, y), WHITE, anchor="topright")
            y += hb + 12
        ri, un = S.get("pp_reinf"), S.get("pp_under")
        if ri is not None or un is not None:
            ri, un = ri or 0, un or 0
            tot = max(1, ri + un)
            xm = area.x + area.w // 2
            put(L, F["small"], "REFUERZO", (x0, y + (hb - hs) // 2), DIM)
            put(L, F["btn"], f"{ri:,}".replace(",", "."), (xm - 30, y), GREEN, anchor="topright")
            put(L, F["small"], "SABOTAJE", (xm + 10, y + (hb - hs) // 2), DIM)
            put(L, F["btn"], f"{un:,}".replace(",", "."), (x1, y), RED, anchor="topright")
            y += hb + 6
            bx = pygame.Rect(x0, y, x1 - x0, 14)
            pygame.draw.rect(L, RED, bx)
            pygame.draw.rect(L, GREEN, (bx.x, bx.y, int(bx.w * ri / tot), bx.h))
            y += 26
    else:
        put(L, F["big"], "SIN POTENCIA", (x0, y), DIM); y += hg + 10
    # abajo: semana, tu potencia y méritos
    yb = area.bottom - 4
    w = (d or {}).get("ppweek") or {}
    if w.get("end"):
        left = max(0, int(w["end"] - time.time()))
        yb -= hs
        put(L, F["small"], f"ESTA SEMANA: {fnum(w.get('merits', 0), 0)} méritos  ·  corte en {left // 86400} d {left % 86400 // 3600} h",
            (x0, yb), BLUE, x1 - x0)
        yb -= 8
    r2 = yb - hb
    r1 = r2 - hb - 6
    pygame.draw.line(L, DIM, (x0, r1 - 8), (x1, r1 - 8), 2)
    if mine:
        put(L, F["small"], "TU POTENCIA", (x0, r1 + (hb - hs) // 2), DIM)
        put(L, F["btn"], mine, (x0 + int(area.w * 0.17), r1), GREEN if pp == mine else ORANGE, int(area.w * 0.5))
        put(L, F["small"], f"RANGO {me.get('rank', '?')}", (x1, r1 + (hb - hs) // 2), WHITE, anchor="topright")
        m = me.get("merits")
        put(L, F["btn"], f"Méritos: {m:,}".replace(",", ".") if m is not None else "Méritos: ?", (x0, r2), ORANGE)
        if me.get("session"):
            put(L, F["small"], f"+{me['session']:,} en esta sesión".replace(",", "."), (x1, r2 + (hb - hs) // 2), GREEN, anchor="topright")
    else:
        put(L, F["small"], "No estás alineado con ninguna potencia", (x0, r2), DIM)
    # conquistas (en el hueco que quede)
    conf = S.get("pp_conf") or []
    if conf:
        put(L, F["small"], "CONQUISTA EN CURSO (100% = toma el control)", (x0, y), DIM); y += hs + 6
        for power, cp in conf[:4]:
            if y + hb > r1 - 12:
                break
            col = GREEN if power == mine else ORANGE
            put(L, F["btn"], power, (x0, y), col, int(area.w * 0.3))
            bx = pygame.Rect(x0 + int(area.w * 0.33), y + hb // 2 - 9, int(area.w * 0.5), 18)
            pygame.draw.rect(L, DIM, bx, 2)
            pygame.draw.rect(L, col, (bx.x + 3, bx.y + 3, int((bx.w - 6) * max(0, min(1, cp))), bx.h - 6))
            put(L, F["btn"], f"{cp * 100:.0f}%", (x1, y), WHITE, anchor="topright")
            y += hb + 6
    elif S.get("powers") and not pp:
        put(L, F["small"], "presentes: " + ", ".join(S["powers"]), (x0, y), DIM, x1 - x0)

# ---------------------------------------------------------------------------------------------------------------
# cara RUTA (sin destino en el sistema)
# ---------------------------------------------------------------------------------------------------------------
def lz_ruta_linea(L, d, y, now, x0, x1):
    """Círculos de la ruta (amarillo recolectable, rojo no, azul neutrones, blanco enana blanca) y el combustible."""
    route = d.get("route") or []
    if not route:
        return y
    hs = F["small"].get_height()
    total = d.get("routen") or len(route)
    end = d.get("routeend") or route[-1]
    nodes = [[d.get("system") or "?", d.get("curstar")]] + [list(r) for r in route[:11]]
    gap = total > 11
    if gap:
        nodes = nodes[:11] + [list(end)]
    on = int(now * 3) % 2 == 0
    cy, n = y + 22, len(nodes)
    a, b = x0 + 20, x1 - 20
    step = (b - a) / max(1, n - 1)
    xs = [int(a + i * step) for i in range(n)] if n > 1 else [a]
    for i in range(n - 1):
        if gap and i == n - 2:
            for k in range(xs[i] + 16, xs[i + 1] - 12, 12):
                pygame.draw.line(L, DIM, (k, cy), (k + 5, cy), 3)
        else:
            pygame.draw.line(L, DIM, (xs[i], cy), (xs[i + 1], cy), 3)
    for i, (name, c) in enumerate(nodes):
        k = star_kind(c)
        col = {"ok": YELLOW, "no": RED, "neu": BLUE if on else DIM, "wd": WHITE if on else DIM, "?": DIM}[k]
        r = 15 if i == 0 else 11 if i < n - 1 or not gap else 13
        pygame.draw.circle(L, col, (xs[i], cy), r)
        if i == 0:
            pygame.draw.circle(L, ORANGE, (xs[i], cy), r + 6, 3)
        if i == n - 1:
            pygame.draw.circle(L, GREEN, (xs[i], cy), r + 6, 3)
    y = cy + 30
    nxt = route[0][0] if route else ""
    eg_ = eng_at((end or [""])[0]) if end else None
    der = f"quedan {total}" + (f" · {end[0]}" if end and total > 1 else "") + (f" · ING. {eg_['name']}" if eg_ else "")
    wd = tw_(F["small"], der)
    put(L, F["small"], f"{(d.get('system') or '?')}  >  {nxt}", (x0, y), ORANGE, x1 - x0 - min(wd, (x1 - x0) // 2) - 20)
    put(L, F["small"], der, (x1, y), BLUE if eg_ else DIM, (x1 - x0) // 2, anchor="topright")
    y += hs + 4
    fj_, fm_ = d.get("fuelj"), (d.get("Fuel") or {}).get("FuelMain")
    if fj_ and fm_ is not None:
        n_ = int(fm_ / fj_) if fj_ > 0 else 0
        put(L, F["small"], f"combustible para ~{n_} saltos" + ("  ·  ¡recoge en la ruta!" if n_ < min(total, 6) else ""),
            (x0, y), RED if n_ < 3 else ORANGE if n_ < min(total, 6) else GREEN, x1 - x0)
        y += hs + 4
    return y + 8

def lz_ruta(L, area, d, flags, now, foto, ylim):
    d = d or {}
    nav, route = d.get("nav") or {}, d.get("route") or []
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    xr = (foto.x - 16) if foto else x1
    y = area.y + 4
    tgt = nav.get("target")
    if not tgt and not route:
        put(L, F["big"], "Sin ruta trazada", area.center, DIM, anchor="center"); return
    put(L, F["small"], "SIGUIENTE SALTO", (x0, y), DIM); y += hs + 2
    put(L, F["big"], (tgt or route[0][0]).upper(), (x0, y), ORANGE, xr - x0); y += hg + 4
    cls = nav.get("star") or (route[0][1] if route else "")
    ok = star_ok(cls)
    x = x0 + put(L, F["btn"], f"Estrella {cls or '?'}   ", (x0, y), ORANGE)
    put(L, F["btn"], "RECOLECTABLE" if ok else "NO RECOLECTABLE", (x, y), NEON_G if ok else RED, xr - x); y += hb + 4
    jumps, last = nav.get("jumps"), nav.get("last")
    put(L, F["btn"], f"Saltos restantes: {jumps if jumps is not None else len(route)}", (x0, y), ORANGE, (xr - x0) // 2)
    if last:
        put(L, F["btn"], f"Último salto: {last:.1f} al".replace(".", ","), (xr, y), ORANGE, anchor="topright")
    y += hb + 6
    if foto:
        y = max(y, foto.bottom + 6)
    y = lz_ruta_linea(L, d, y, now, x0, x1)
    if not route:
        return
    pygame.draw.line(L, DIM, (x0, y - 6), (x1, y - 6), 2)
    txt, col = route_arrival(d, now)
    put(L, F["small"], f"RUTA  -  {(d.get('routeend') or route[-1])[0]}", (x0, y), DIM, (x1 - x0) // 2 - 20)
    if txt:
        put(L, F["small"], txt, (x1, y), col, (x1 - x0) // 2, anchor="topright")
    y += hs + 6
    fn = F["btn"] if area.h > 400 else F["small"]
    rh = fn.get_height() + (8 if area.h > 400 else 4)
    celda = area.h < 400
    R = LZ["rut"]["c" if celda else "p"]
    nvis = max(1, (ylim - y) // rh)
    key = tuple(r[0] for r in route[:2])
    if key != R["key"]:
        R.update(key=key, off=0)                                 # ruta nueva o un salto hecho: arriba del todo
    R["max"] = max(0, len(route) - nvis)
    R["off"] = 0 if celda else max(0, min(R["off"], R["max"]))       # en el cuadro, sin flechas: siempre los primeros
    R["nvis"] = nvis
    sb = 90 if R["max"] and not celda else 0
    for n in range(R["off"], min(len(route), R["off"] + nvis)):
        name, c = route[n]
        redsm_want(name)
        colr = ORANGE if star_ok(c) else RED
        marks = route_marks(name, c)
        mw = sum(tw_(F["tiny"], t) + 22 for t, _ in marks)
        cw_ = tw_(fn, c or "?") + 20
        put(L, fn, f"{n + 1}. {name}", (x0, y), colr, x1 - sb - x0 - cw_ - mw - 16)
        xm = x1 - sb - cw_ - mw
        for t, cc in marks:
            pygame.draw.rect(L, cc, (xm, y + (fn.get_height() - F["tiny"].get_height()) // 2 - 3, tw_(F["tiny"], t) + 12,
                                     F["tiny"].get_height() + 6), 1, border_radius=4)
            put(L, F["tiny"], t, (xm + 6, y + (fn.get_height() - F["tiny"].get_height()) // 2), cc)
            xm += tw_(F["tiny"], t) + 22
        put(L, fn, c or "?", (x1 - sb, y), colr, anchor="topright")
        lz_hit(pygame.Rect(area.x, y - 2, x1 - sb - area.x, rh), "rsys", name, c)
        y += rh
    if R["max"] and not celda:                                   # flechas para subir y bajar
        top_ = y - (min(len(route), R["off"] + nvis) - R["off"]) * rh
        hh = min(80, (y - top_ - 50) // 2)
        ru = pygame.Rect(x1 - 76, top_, 76, hh)
        rd = pygame.Rect(x1 - 76, y - hh - 4, 76, hh)
        lz_flecha_btn(L, ru, True, R["off"] > 0)
        lz_flecha_btn(L, rd, False, R["off"] < R["max"])
        put(L, F["tiny"], f"{R['off'] + 1}-{min(len(route), R['off'] + nvis)}/{len(route)}", (ru.centerx, (ru.bottom + rd.y) // 2),
            DIM, 90, anchor="center")
        lz_hit(ru, "rutoff", -nvis + 1)
        lz_hit(rd, "rutoff", nvis - 1)

def _lz_rutoff(acc, X, Y):
    R = LZ["rut"]["p"]
    R["off"] = max(0, min(R["max"], R["off"] + (acc[1] or 1)))

def _lz_rsys(acc, X, Y):
    tap_flash(("rsys",)); ui["rsys"] = (acc[1], acc[2]); redsm_want(acc[1]); ui["view"] = 212

LZ_ACC["rutoff"] = _lz_rutoff
LZ_ACC["rsys"] = _lz_rsys

# ---------------------------------------------------------------------------------------------------------------
# cara DESTINO (cuerpo, estación o portanaves marcado en el sistema)
# ---------------------------------------------------------------------------------------------------------------
def lz_portanaves_info(L, d, x0, y, wd, ylim):
    """Datos del portanaves o de la estación de destino (como carrier_info)."""
    hs, hb, hg = lz_alturas()
    k, lab = carrier_dest(d)
    if k not in ("fc", "sq"):
        return y
    own = d.get("carrier") or {}
    lines = []
    if lab == "TU PORTANAVES" and own.get("callsign"):
        av = own.get("avail")
        up = 5e6 + sum(CREW_COST.get(c, 0) for c in own.get("crew") or [])
        if av is not None:
            wk = av / up if up else 99
            if y + hb <= ylim:
                put(L, F["small"], "SALDO DISPONIBLE", (x0, y + (hb - hs) // 2), DIM)
                put(L, F["btn"], f"{crx(av)} cr", (x0 + 260, y), ORANGE); y += hb + 2
            lines.append((f"gastos ~{crx(up)} cr/semana  ·  da para {wk:.0f} semanas".replace(".", ","), RED if wk < 2 else ORANGE if wk < 4 else DIM))
        if own.get("crew"):
            lines.append(("SERVICIOS: " + ", ".join(CREW_ES.get(c, c) for c in own["crew"] if c in CREW_ES), BLUE))
        if own.get("access"):
            lines.append((f"ATRAQUE: {ACCESS_ES.get(own['access'], own['access'].upper())}" + ("  ·  admite buscados" if own.get("notorious") else ""), GREEN))
        if own.get("jump"):
            lines.append((f"SALTO: {own['jump']} al", WHITE))
    else:
        di = d.get("dstinfo") or {}
        sv = [v for v in (SVC_ES.get(v.lower()) for v in di.get("services") or []) if v]
        if sv:
            lines.append(("SERVICIOS (última vez): " + ", ".join(dict.fromkeys(sv)), BLUE))
        if di.get("denied"):
            lines.append((f"TE DENEGARON EL ATRAQUE: {di['denied']}", RED))
        if not sv and not di.get("denied"):
            lines.append(("sin datos: los verás al atracar una vez", DIM))
    for t, c in lines:
        if y + hs > ylim:
            break
        put(L, F["small"], t, (x0, y), c, wd(y)); y += hs + 4
    return y + 4

def lz_faccion_destino(L, d, x0, y, wd, ylim, now):
    r_ = dest_faction(d)
    if not r_:
        return y
    fac, rep, state_ = r_
    lvl, col = rep_level(rep)
    nm = (d.get("dest") or {}).get("name")
    if lvl == "HOSTIL" and nm and DSTH.get("name") != nm:            # el mismo aviso que la pantalla de 480x320
        DSTH["name"] = nm
        k0 = XA_K[0]
        try:
            XA_K[0] = "dsthostil"
            xa["a"] = dict(until=now + 6, col=RED, title="¡DESTINO HOSTIL!", big=nm.upper(), lines=[fac])
            play("alarm")
        finally:
            XA_K[0] = k0
    hs, hb, hg = lz_alturas()
    if y + hs + hb > ylim:
        return y
    put(L, F["small"], "FACCIÓN", (x0, y), DIM); y += hs + 2
    bits = [x for x in (lvl, state_) if x]
    t2 = "  ·  ".join(bits)
    put(L, F["btn"], fac, (x0, y), WHITE, wd(y) - (tw_(F["btn"], t2) + 30 if bits else 0))
    if bits:
        put(L, F["btn"], t2, (x0 + wd(y), y), col, anchor="topright")
    return y + hb + 8

def lz_destino(L, area, d, flags, now, foto, ylim):
    d = d or {}
    D = d.get("dest") or {}
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    wd = lambda y_: ((foto.x - 16) if foto and y_ < foto.bottom + 4 else x1) - x0
    y = area.y + 4
    arrived = d.get("body") == D["name"]
    put(L, F["small"], "DESTINO EN EL SISTEMA", (x0, y), DIM)
    if arrived:
        put(L, F["btn"], "HAS LLEGADO", (x0 + wd(y), y - 4), GREEN, anchor="topright")
    elif flags & 16:
        put(L, F["btn"], "EN RUTA", (x0 + wd(y), y - 4), BLUE if int(now * 2) % 2 else WHITE, anchor="topright")
    y += hs + 2
    put(L, F["big"], D["name"].upper(), (x0, y), ORANGE, wd(y)); y += hg + 4
    if D.get("cls") or D.get("dist") is not None:
        dt = f"{D['dist']:,} ls".replace(",", ".") if D.get("dist") is not None else ""
        if D.get("cls"):
            put(L, F["btn"], D["cls"], (x0, y), BLUE, wd(y) - tw_(F["btn"], dt) - 20)
        if dt:
            put(L, F["btn"], dt, (x0 + wd(y), y), WHITE, anchor="topright")
        y += hb + 6
    tags = []
    if D.get("land") is not None:
        tags.append(("ATERRIZABLE", GREEN) if D["land"] else ("NO ATERRIZABLE", DIM))
    g = D.get("g")
    if g is not None:
        tags.append((f"{g:.2f} G".replace(".", ","), RED if g >= 2 else ORANGE if g >= 1.5 else WHITE))
    if D.get("rings"):
        tags.append(("ANILLOS", BLUE))
    if D.get("tf"):
        tags.append(("TERRAFORMABLE", GREEN))
    if D.get("first"):
        tags.append(("1º DESCUBRIMIENTO", GREEN))
    if D.get("mapped"):
        tags.append(("MAPEADO", BLUE))
    for name, c in D.get("signals") or []:
        low = name.lower()
        tags.append((f"{name} x{c}", GREEN if "bio" in low else BLUE if "geo" in low else ORANGE))
    if tags:
        y = lz_chips(L, tags, x0, x0 + wd(y), y, F["small"] if area.h < 400 else F["btn"], gap=8)
    if D.get("value") and y + hg <= ylim:
        put(L, F["small"], "VALOR DE DATOS", (x0, y + (hg - hs) // 2), DIM)
        put(L, F["big"], f"~ {cr(D['value'])} cr", (x0 + tw_(F["small"], "VALOR DE DATOS") + 24, y), ORANGE, wd(y) - 260)
        y += hg + 6
    # abajo: fuente de los datos y brújula al destino en la superficie
    src = D.get("src")
    yb = ylim
    if src or not d.get("dstinfo"):
        yb -= hs
        put(L, F["small"], f"datos: {src}" if src else "sin datos: no escaneado (o es una estación/señal)", (x0, yb), DIM if src else ORANGE,
            x1 - x0)
        yb -= 8
    b = d.get("bio") or {}
    if D.get("lat") is not None and b.get("lat") is not None and b.get("R") and d.get("body") == D.get("sbody"):
        p1, p2 = math.radians(b["lat"]), math.radians(D["lat"])
        dl = math.radians(D["lon"] - b["lon"])
        brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                      math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
        m = hav((b["lat"], b["lon"]), (D["lat"], D["lon"]), b["R"])
        rr = min(40, (hs + hg) // 2 + 4)
        cy = yb - rr - 4
        cx = x0 + rr + 4
        pygame.draw.circle(L, DIM, (cx, cy), rr, 2)
        hdg = b.get("hdg")
        if hdg is not None:
            a = math.radians(brg - hdg)
            pt = lambda k, da: (cx + rr * k * math.sin(a + da), cy - rr * k * math.cos(a + da))
            pygame.draw.polygon(L, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
        txt = f"{m / 1000:.1f} km".replace(".", ",") if m >= 1000 else f"{m:.0f} m"
        put(L, F["small"], "DISTANCIA AL DESTINO", (cx + rr + 20, cy - rr), DIM)
        put(L, F["big"], txt, (cx + rr + 20, cy - rr + hs), GREEN)
        put(L, F["btn"], f"rumbo {brg:.0f}°", (x1, cy - hb // 2), ORANGE, anchor="topright")
        yb = cy - rr - 10
    y = lz_portanaves_info(L, d, x0, y, wd, yb)
    lz_faccion_destino(L, d, x0, y, wd, yb, now)

def lz_navx(L, area, d, flags, now, celda=False):
    """Cara RUTA/DESTINO: con foto del destino arriba a la derecha y la ficha del ingeniero abajo si lo hay."""
    d = d or {}
    D = d.get("dest") or {}
    nav = d.get("nav") or {}
    if not (D and D.get("name")) and not nav.get("target") and not d.get("route"):
        return lz_pol(L, area, d, now)
    k, label = carrier_dest(d)
    foto = None
    if k:
        fw, fh = (220, 124) if celda else (380, 214)
        foto = pygame.Rect(area.right - 10 - fw, area.y + 4, fw, fh)
        lz_foto_destino(L, foto, k, label)
    ylim = area.bottom - 4
    if eng_here(d):
        ch = 100 if celda else 160
        lz_ing(L, d, pygame.Rect(area.x + 8, area.bottom - ch - 4, area.w - 16, ch))
        ylim = area.bottom - ch - 12
    if D and D.get("name"):
        lz_destino(L, area, d, flags, now, foto, ylim)
    else:
        if ylim == area.bottom - 4:
            ylim = lz_franja_pol(L, area, d)
        lz_ruta(L, area, d, flags, now, foto, ylim)

# ---------------------------------------------------------------------------------------------------------------
# 3 NAVEGACIÓN en el MENÚ: botones de cara arriba (RUTA/DESTINO · SISTEMA · POWERPLAY) y RUTA EXT.
# ---------------------------------------------------------------------------------------------------------------
def lv_nav(L, area, d, flags, now):
    hs, hb, hg = lz_alturas()
    cara = 2 if ui.get("navtab") == 2 else 1 if nav_show_pol(d, now) else 0
    lz_hit(area, "navcic")                                    # tocar el contenido cambia de cara (como antes)
    bh = hb + 18
    D = (d or {}).get("dest") or {}
    names = ("DESTINO" if D.get("name") else "RUTA", "SISTEMA", "POWERPLAY")
    bw = 230
    for i, n in enumerate(names):
        r = pygame.Rect(area.x + 10 + i * (bw + 12), area.y + 4, bw, bh)
        lz_boton_v(L, r, n, None, F["btn"], filled=cara == i, lit=flash.get(("navcara", i), 0) > now)
        lz_hit(r, "navcara", i)
    P_, i_ = rx_ruta(d)
    lab = f"RUTA EXT. {min(i_ + 1, len(P_))}/{len(P_)}" if P_ else "RUTA EXT."
    lz_boton_v(L, pygame.Rect(area.right - 10 - 300, area.y + 4, 300, bh), lab, None, F["btn"],
               lit=bool(P_) or flash.get(("rxb",), 0) > now, viejo=RX_BTN)
    sub = pygame.Rect(area.x, area.y + bh + 14, area.w, area.h - bh - 14)
    pygame.draw.line(L, DIM, (area.x + 10, sub.y - 6), (area.right - 10, sub.y - 6), 2)
    if cara == 2:
        lz_pp(L, sub, d, now)
    elif cara == 1:
        lz_pol(L, sub, d, now)
    else:
        lz_navx(L, sub, d, flags, now)

def _lz_navcic(acc, X, Y):
    cur = ui.get("navtab") or (1 if time.time() < pol["until"] else 0)
    ui["navtab"] = (cur + 1) % 3
    pol["until"] = 0

def _lz_navcara(acc, X, Y):
    tap_flash(("navcara", acc[1]))
    ui["navtab"] = acc[1]
    pol["until"] = 0

LZ_ACC["navcic"] = _lz_navcic
LZ_ACC["navcara"] = _lz_navcara

def lc_nav(L, d, flags, now):
    """NAVEGACIÓN en el tablero: 10 s el sistema al llegar, 5 s el powerplay (si hay) y luego ruta o destino."""
    area = pygame.Rect(0, 0, CW0, CH0)
    nav_show_pol(d, now)
    S = (d or {}).get("sysinfo") or {}
    el = now - pol.get("t0", 0)
    if el < 10:
        return lz_pol(L, area, d, now)
    if el < 15 and (S.get("pp") or S.get("pp_conf") or S.get("powers")):
        return lz_pp(L, area, d, now)
    NAVBIG[0] = True
    try:
        lz_navx(L, area, d, flags, now, celda=True)
    finally:
        NAVBIG[0] = False

# ---------------------------------------------------------------------------------------------------------------
# 212 sistema de la ruta (ficha de EDSM)
# ---------------------------------------------------------------------------------------------------------------
def lv_rsys(L, area, d, flags, now):
    name, c = ui.get("rsys") or ("?", "")
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    lz_hit(area, "old", BACK_R.centerx, BACK_R.centery)       # tocar fuera de IR vuelve a NAVEGACIÓN (como antes)
    bh = hb + 18
    rir = pygame.Rect(x1 - 200, area.y + 4, 200, bh)
    rbk = pygame.Rect(rir.x - 16 - 250, area.y + 4, 250, bh)
    lz_boton_v(L, rbk, "< VOLVER", None, F["btn"], viejo=BACK_R)
    lz_boton_v(L, rir, "IR >", None, F["btn"], lit=flash.get(("rir",), 0) > now, viejo=IR_R)
    y = area.y + 6
    put(L, F["big"], name.upper(), (x0, y), ORANGE, rbk.x - x0 - 16); y += max(hg, bh) + 8
    kt = {"ok": ("RECOLECTABLE", GREEN), "no": ("NO RECOLECTABLE", RED), "neu": ("ESTRELLA DE NEUTRONES · ¡cuidado con los chorros!", RED),
          "wd": ("ENANA BLANCA · ¡cuidado con los chorros!", RED), "?": ("", DIM)}[star_kind(c)]
    x = x0 + put(L, F["btn"], f"Estrella {c or '?'}   ", (x0, y), ORANGE)
    put(L, F["btn"], kt[0], (x, y), kt[1], x1 - x); y += hb + 8
    v = ((FACD["data"] or {}).get("sistemas") or {}).get(name)
    if v and not v.get("fuera"):
        put(L, F["btn"], f"CABALLEROS DE SION · {v.get('inf', 0):.1f} %".replace(".", ",") + (" · CONTROLA" if v.get("ctrl") else ""),
            (x0, y), ORANGE, x1 - x0); y += hb + 4
        st_ = ", ".join(ES_ST.get(s_, s_) for s_ in (v.get("activos") or []) + (v.get("pendientes") or []))
        if st_:
            put(L, F["small"], st_, (x0, y), RED if fac_war(v) else GREEN, x1 - x0); y += hs + 6
    pygame.draw.line(L, DIM, (x0, y + 2), (x1, y + 2), 2); y += 12
    # permiso (abajo)
    s = PERM_SYS.get((name or "").lower())
    rg = None if s else perm_region(name)
    ylim = area.bottom - 4
    if s or rg:
        if s:
            ok = perm_tengo(s["sistema"], d)
            txt = ("PERMISO: LO TIENES" if ok else "PERMISO: TE FALTA") + f" · {s.get('titular') or ''}"
            sub = perm_como(s) if not ok else (s.get("ventajas") or "")
        else:
            ok, txt, sub = False, f"ZONA CERRADA: {rg['region'].upper()}", "no se conoce forma de conseguir el permiso"
        r = pygame.Rect(x0 - 4, area.bottom - hb - hs - 22, x1 - x0 + 8, hb + hs + 18)
        pygame.draw.rect(L, BLACK, r, border_radius=8)
        pygame.draw.rect(L, GREEN if ok else RED, r, 3, border_radius=8)
        put(L, F["btn"], txt, (r.x + 12, r.y + 6), GREEN if ok else RED, r.w - 24)
        if sub:
            put(L, F["small"], sub, (r.x + 12, r.y + 10 + hb), WHITE, r.w - 24)
        ylim = r.y - 8
    J = REDSM.get(name)
    if J is None and name in REDSM:
        put(L, F["btn"], "EDSM no responde (se reintentará)", (x0, y), DIM)
    elif name not in REDSM:
        put(L, F["btn"], "consultando EDSM…", (x0, y), DIM)
    elif not J:
        put(L, F["btn"], "EDSM NO LO CONOCE", (x0, y), GREEN); y += hb + 4
        put(L, F["small"], "puede que nadie lo haya subido: ¡posible primer descubrimiento!", (x0, y), GREEN, x1 - x0)
    else:
        info = J.get("information") or {}
        ps = J.get("primaryStar") or {}
        rows = [("CONTROLA", info.get("faction")), ("GOBIERNO", info.get("government")), ("ALIANZA", info.get("allegiance")),
                ("SEGURIDAD", info.get("security")), ("ECONOMÍA", info.get("economy")),
                ("POBLACIÓN", f"{info['population']:,}".replace(",", ".") if info.get("population") else "deshabitado"),
                ("ESTRELLA", (ps.get("type") or "") + (" · recolectable" if ps.get("isScoopable") else ""))]
        xv = x0 + int(area.w * 0.18)
        for lab, val in rows:
            if not val:
                continue
            if y + hb > ylim:
                break
            put(L, F["small"], lab, (x0, y + (hb - hs) // 2), DIM)
            put(L, F["btn"], str(val), (xv, y), WHITE, x1 - xv); y += hb + 6

# ---------------------------------------------------------------------------------------------------------------
# 216 RUTA EXTERNA
# ---------------------------------------------------------------------------------------------------------------
def lv_rutaext(L, area, d, flags, now):
    P_, i = rx_ruta(d)
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 6
    if not P_:
        route = (d or {}).get("route") or []
        put(L, F["btn"], "Sin ruta externa", (x0, y), ORANGE); y += hb + 10
        for t_ in ("Descarga la ruta en CSV (Spansh, neutrones...) y déjala en la carpeta rutas\\ junto a elite_sender.py.",
                   "Se carga sola la más nueva y avanza al llegar a cada parada."):
            put(L, F["small"], t_, (x0, y), DIM, x1 - x0); y += hs + 6
        if route:
            y += 20
            put(L, F["small"], "SIGUIENTE SALTO DE LA RUTA DEL JUEGO", (x0, y), DIM); y += hs + 4
            put(L, F["big"], route[0][0].upper(), (x0, y), ORANGE, x1 - x0 - 260)
            b = pygame.Rect(x1 - 240, y - 4, 240, hg + 8)
            lz_boton_v(L, b, "COPIAR", None, F["btn"], lit=flash.get(("rxc",), 0) > now)
            lz_hit(b, "rxacc", "copiar_juego", route[0][0])
        return
    r = (d or {}).get("rutaext") or {}
    put(L, F["small"], f"{r.get('f', '')} · parada {min(i + 1, len(P_))} de {len(P_)}", (x0, y), DIM, x1 - x0); y += hs + 8
    bh = hb + 26
    yb = area.bottom - bh - 6
    rh = hb + 10
    nvis = max(1, (yb - 10 - y) // rh)
    ini = max(0, min(i - 2, len(P_) - nvis))
    for k in range(ini, min(len(P_), ini + nvis)):
        nom, neu = P_[k][0], P_[k][1]
        if k < i:
            c_, pre = DIM, "· "
        elif k == i:
            c_, pre = ORANGE, "> "
            pygame.draw.rect(L, (40, 25, 0), (x0 - 8, y - 4, x1 - x0 + 16, rh), border_radius=6)
        else:
            c_, pre = WHITE, "   "
        put(L, F["big"] if k == i and area.h > 400 else F["btn"], f"{pre}{k + 1}. {nom}", (x0, y + (0 if k == i else 0)), c_, x1 - x0 - 180)
        if neu:
            put(L, F["small"], "NEUTRÓN", (x1, y + (hb - hs) // 2), BLUE, anchor="topright")
        y += rh
    bw = (x1 - x0 - 3 * 14) // 4
    for n_, (lab, key) in enumerate((("COPIAR", "copiar"), ("< ATRÁS", "atras"), ("SALTAR >", "saltar"),
                                     ("¿SEGURO?" if now - RX["borrar"] < 3 else "BORRAR", "borrar"))):
        b = pygame.Rect(x0 + n_ * (bw + 14), yb, bw, bh)
        lz_boton_v(L, b, lab, None, F["btn"], lit=flash.get(("rx", key), 0) > now)
        lz_hit(b, "rxacc", key, None)

def _lz_rxacc(acc, X, Y):
    """Los botones de la RUTA EXTERNA (lo mismo que su on_tap)."""
    key, extra = acc[1], acc[2]
    with lock:
        d = state.get("data") or {}
    P_, i = rx_ruta(d)
    st = rx_estado()
    if key == "copiar_juego":
        tap_flash(("rxc",)); rx_copia(extra)
    elif key == "copiar" and P_ and i < len(P_):
        tap_flash(("rx", key)); rx_copia(P_[i][0])
    elif key == "atras" and P_:
        tap_flash(("rx", key)); st["idx"] = max(0, i - 1); rx_guarda()
    elif key == "saltar" and P_:
        tap_flash(("rx", key)); st["idx"] = min(len(P_), i + 1); rx_guarda()
        if st["idx"] < len(P_) and auto_on("copiasig"):
            rx_copia(P_[st["idx"]][0])
    elif key == "borrar":
        if time.time() - RX["borrar"] < 3:
            st["borrada"] = True; rx_guarda(); RX["borrar"] = 0
            set_alert("RUTA EXTERNA BORRADA", "deja otro CSV en rutas\\ para cargar una nueva", ORANGE, 3)
        else:
            RX["borrar"] = time.time()

LZ_ACC["rxacc"] = _lz_rxacc

# ---------------------------------------------------------------------------------------------------------------
# 190 VIAJES (mapa de tus saltos)
# ---------------------------------------------------------------------------------------------------------------
def lz_viajes(L, area, d, flags, now, celda=False):
    V = (d or {}).get("viajes") or {}
    hs, hb, hg = lz_alturas()
    per = ui.get("vjp", "30"); zm = ui.get("vjz", "zona"); Z = ui.get("vjzoom")
    key = "c" if celda else "p"
    LZ["vj"][key] = None
    bh = (hs + 18) if celda else (hb + 22)
    yb = area.bottom - bh - 4
    gap = 8
    bw = (area.w - 16 - 6 * gap) // 7
    labs = [(lab, k == per, False) for k, lab in VJ_PER] + [("GALAXIA" if zm == "gal" else "ZONA", False, False),
            (f"−  x{Z[0]}" if Z else "−", False, not Z), ("+", False, bool(Z and Z[0] >= 64))]
    fb = F["tiny"] if celda else F["btn"]
    for i, (lab, fil, dim) in enumerate(labs):
        r = pygame.Rect(area.x + 8 + i * (bw + gap), yb, bw, bh)
        if i < 6:
            lz_boton_v(L, r, lab, None, fb, filled=fil, dim=dim, viejo=vj_btn(i))
        else:
            lz_boton_v(L, r, lab, None, fb, dim=dim, lit=flash.get(("vjmas",), 0) > now)
            lz_hit(r, "vjmas", key)
    M = pygame.Rect(area.x + 6, area.y + 4, area.w - 12, yb - 10 - area.y - 4)
    pygame.draw.rect(L, DIM, M, 2, border_radius=6)
    D = V.get(per)
    if not D or not D.get("n"):
        put(L, F["btn"], "sin saltos en este periodo" if V else "esperando datos del sender", M.center, DIM, anchor="center")
        return
    nodes, edges, cur = D["n"], D["e"], D.get("cur")
    A = M.inflate(-50, -60).move(0, -4)
    pt0, sc0 = _vj_view(nodes, cur, zm, A)
    if Z:
        f_, wx, wz = Z
        sc = sc0 * f_
        pt = lambda x, z: (A.centerx + (x - wx) * sc, A.centery - (z - wz) * sc)
    else:
        pt, sc = pt0, sc0
    LZ["vj"][key] = (A, pt, sc)
    lz_hit(M, "vjmapa", key)
    k_ = 2 if not celda else 1
    if zm == "gal":
        c = pt(*GAL_C)
        rr1 = max(2, min(4000, int(45000 * sc)))
        if M.collidepoint(c) or rr1 < 3000:
            pygame.draw.circle(L, (45, 30, 10), (int(c[0]), int(c[1])), rr1, 2)
        pygame.draw.circle(L, (70, 45, 15), (int(c[0]), int(c[1])), max(3, min(2000, int(4000 * sc))))
    P_ = [pt(n[1], n[2]) for n in nodes]
    mx = max([e[2] for e in edges] or [1])
    outs = []
    for i, j, c, h in sorted(edges, key=lambda e: e[2]):
        a, b = P_[i], P_[j]
        w = k_ + round(4 * k_ * (c - 1) / max(1, mx - 1))
        cl = M.clipline(a, b)
        if not cl:
            continue
        pygame.draw.line(L, ORANGE if c > 1 else (150, 80, 0), cl[0], cl[1], w)
        ina, inb = M.collidepoint(a), M.collidepoint(b)
        if ina != inb:
            outs.append((nodes[j], cl[1], h) if ina else (nodes[i], cl[0], h))
        elif h >= 5 and math.dist(a, b) > 150:
            put(L, F["small"], f"{h} saltos", ((a[0] + b[0]) / 2 + 8, (a[1] + b[1]) / 2 - hs - 4), DIM)
    for k, n in enumerate(nodes):
        x, y = P_[k]
        if M.collidepoint(x, y):
            r = (2 + min(3, n[3] // 2)) * k_
            pygame.draw.circle(L, WHITE if n[4] else (160, 160, 160), (int(x), int(y)), r + (k_ if n[4] else 0))
    used = []
    def label(txt, x, y, col):
        tw, th = tw_(F["small"], txt), hs
        for dx, dy in ((16, -th // 2), (-16 - tw, -th // 2), (-tw // 2, -th - 14), (-tw // 2, 14), (16, -th - 8), (16, 8), (-16 - tw, 8)):
            r = pygame.Rect(int(x + dx), int(y + dy), tw, th)
            if M.contains(r) and not any(r.colliderect(u) for u in used):
                used.append(r.inflate(8, 4)); pygame.draw.rect(L, BLACK, r.inflate(8, 0))
                put(L, F["small"], txt, r.topleft, col); return
    ci = next((k for k, n in enumerate(nodes) if n[0] and n[0] == cur), None)
    if ci is not None and M.collidepoint(P_[ci]):
        x, y = P_[ci]
        pygame.draw.circle(L, BLUE, (int(x), int(y)), (7 if int(now * 2) % 2 else 9) * k_, 3)
        label(cur.upper()[:22], x, y, BLUE)
    nlab = (8 if not Z else 20) if not celda else (5 if not Z else 12)
    for k in sorted(range(len(nodes)), key=lambda k: -nodes[k][3])[:nlab]:
        n = nodes[k]
        if n[0] and k != ci and M.collidepoint(P_[k]):
            label(n[0].upper()[:20], *P_[k], WHITE)
    ref = nodes[ci] if ci is not None else max(nodes, key=lambda n: n[3])
    seen = set()
    for far, (ex, ey), h in sorted(outs, key=lambda o: -math.hypot(o[0][1] - ref[1], o[0][2] - ref[2])):
        kk = far[0] or (round(far[1]), round(far[2]))
        if kk in seen or len(seen) >= 4:
            continue
        seen.add(kk)
        dist = math.hypot(far[1] - ref[1], far[2] - ref[2])
        pygame.draw.circle(L, ORANGE, (int(ex), int(ey)), 4 * k_)
        label(f"» {(far[0] or 'destino').upper()[:16]} {dist:,.0f} al".replace(",", "."), ex, ey, ORANGE)
    st_ = f"{D['j']} SALTOS · {D['ly']:,} al · {D['s']} SISTEMAS".replace(",", ".") + ("" if Z else "  ·  toca para ampliar")
    r_ = pygame.Rect(M.x + 4, M.bottom - hs - 6, tw_(F["small"], st_) + 14, hs + 4)
    pygame.draw.rect(L, BLACK, r_)
    put(L, F["small"], st_, (r_.x + 7, r_.y + 2), DIM)

def _lz_vjzoom(key, X=None, Y=None):
    g = LZ["vj"].get(key)
    if not g:
        return
    A, pt, sc = g
    c0 = pt(0, 0)
    if X is None:
        X, Y = A.centerx, A.centery
    wx, wz = (X - c0[0]) / sc, -(Y - c0[1]) / sc
    Z = ui.get("vjzoom")
    f_ = (Z[0] if Z else 1) * 2
    if f_ <= 64:
        ui["vjzoom"] = (f_, wx, wz)

LZ_ACC["vjmas"] = lambda acc, X, Y: (tap_flash(("vjmas",)), _lz_vjzoom(acc[1]))
LZ_ACC["vjmapa"] = lambda acc, X, Y: _lz_vjzoom(acc[1], X, Y)

def lv_viajes(L, area, d, flags, now):
    lz_viajes(L, area, d, flags, now)

# ---------------------------------------------------------------------------------------------------------------
# toques en los cuadros con acciones propias: si cambian de vista, se abre el MENÚ
# ---------------------------------------------------------------------------------------------------------------
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
                v0 = ui["view"]
                LZ_ACC[acc[0]](acc, lx, ly)
                if ui["view"] != v0:
                    lienzo_menu()
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

LZ_PANEL.update({3: lv_nav, 212: lv_rsys, 216: lv_rutaext, 190: lv_viajes})
LZ_CELDA[3] = lc_nav
LZ_CELDA[190] = lambda L, d, flags, now: lz_viajes(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now, celda=True)
