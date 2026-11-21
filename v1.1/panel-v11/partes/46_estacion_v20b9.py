# Panel Elite v2.0 · parte 46: v2.0b9 — ESTACIÓN y MERCADO a 1280x800 (con PANTALLA v2)
#   8 ESTACIÓN (pidiendo atraque: plataforma, reloj de 10 min y altímetro en puertos planetarios; atracado: ficha de la
#   estación y sus facciones, alternando con POWERPLAY) y 127 MERCADO (tu bodega o lo mejor pagado, franjas de bodega
#   llena / entrega en tu depósito / no vendas, recuadro PARA TU COLONIA y la vista COLONIA del mercado), en el MENÚ,
#   en los cuadros del tablero y en ATRAQUE (una pantalla entera).

def lz_fondo_estacion(L, area, d, st, dark=95, label=True):
    """Foto de la estación o portanaves de fondo en area (como carrier_bg). Devuelve el rótulo dibujado o None."""
    if st.get("status") not in ("SOLICITADO", "CONCEDIDO", "ATRACADO"):
        return None
    k, lab, col = carrier_kind(d, st)
    if not k:
        return None
    rr = L._r(area).clip(L.real.get_rect())
    img = bg_img(k, rr.w, rr.h, dark)
    if img is not None:
        L.real.blit(img, rr.topleft)
    if label and st.get("status") != "ATRACADO" and not dock_alt_on(d):
        return lab, col
    return None

def lz_nombre_estacion(L, name, x, y, w):
    """Nombre entero: grande; si no cabe, mediano; si tampoco, en dos líneas."""
    hs, hb, hg = lz_alturas()
    if tw_(F["big"], name) <= w:
        put(L, F["big"], name, (x, y), ORANGE); return y + hg + 2
    if tw_(F["btn"], name) <= w:
        put(L, F["btn"], name, (x, y + (hg - hb) // 2), ORANGE); return y + hg + 2
    for f_ in ("btn", "small"):
        Ls = _partir(F[f_], name, w)
        if len(Ls) <= 2 and all(tw_(F[f_], l_) <= w for l_ in Ls):
            lh = F[f_].get_height() + 2
            for i, l_ in enumerate(Ls):
                put(L, F[f_], l_, (x, y + i * lh), ORANGE)
            return y + 2 * lh + 4
    Ls = _partir(F["small"], name, w)
    put(L, F["small"], Ls[0], (x, y), ORANGE, w)
    put(L, F["small"], " ".join(Ls[1:]), (x, y + hs + 2), ORANGE, w)
    return y + 2 * hs + 6

def lz_faccion_estacion(L, fac, x, y, w, font=None):
    """Facción dueña: la tuya en verde, con el escudo y «TU FACCIÓN». Devuelve la y de debajo."""
    font = font or F["btn"]
    fh = font.get_height()
    if not fac:
        put(L, font, "?", (x, y), ORANGE); return y + fh + 4
    if not es_mi_fac(fac):
        put(L, font, fac, (x, y), ORANGE, w); return y + fh + 4
    lg = fh + 4
    lx = x + lg + 10 if blit_logo(L, pygame.Rect(x, y - 2, lg, lg)) else x
    tw = put(L, font, fac, (lx, y), GREEN, w - (lx - x))
    if lx + tw + tw_(F["small"], "TU FACCIÓN") + 20 <= x + w:
        put(L, F["small"], "TU FACCIÓN", (lx + tw + 16, y + (fh - F["small"].get_height()) // 2), GREEN)
    return y + fh + 6

def lz_facciones(L, x0, x1, y, ylim, facs, destacada, grande=True):
    """Lista de facciones con su barra de influencia, estado y reputación."""
    hs, hb, hg = lz_alturas()
    fn = F["btn"] if grande else F["small"]
    fh = fn.get_height()
    rh = fh + (8 if grande else 4)
    w = x1 - x0
    cb, wb = x0 + int(w * 0.36), int(w * 0.24)
    for name, infl, st_, rep in facs:
        if y + rh > ylim:
            break
        put(L, fn, name, (x0, y), ORANGE if name == destacada else WHITE, cb - x0 - 12)
        bx = pygame.Rect(cb, y + fh // 2 - 8, wb, 16)
        pygame.draw.rect(L, DIM, bx, 2)
        pygame.draw.rect(L, BLUE, (bx.x + 3, bx.y + 3, int((bx.w - 6) * min(100, infl) / 100), bx.h - 6))
        put(L, F["small"], f"{infl:.0f}%", (bx.right + 80, y + (fh - hs) // 2), WHITE, anchor="topright")
        put(L, F["small"], st_ or "", (bx.right + 96, y + (fh - hs) // 2), RED if st_ in ("GUERRA", "GUERRA CIVIL", "BLOQUEO") else DIM,
            x1 - bx.right - 96 - 70)
        if rep is not None:
            put(L, F["small"], f"{rep:+.0f}", (x1, y + (fh - hs) // 2), GREEN if rep >= 35 else RED if rep <= -35 else ORANGE, anchor="topright")
        y += rh
    return y

def lz_servicios(L, st, x0, x1, y, font=None):
    srv = set(st.get("services") or [])
    return lz_chips(L, [(t, ORANGE) for k, t in SERVICES if k in srv], x0, x1, y, font or F["small"], gap=8, pad=8)

# ---------------------------------------------------------------------------------------------------------------
# 8 ESTACIÓN atracado: ficha de la estación
# ---------------------------------------------------------------------------------------------------------------
def lz_estacion_ficha(L, area, d, st):
    lz_fondo_estacion(L, area, d or {}, st, dark=BG_DOCK_DARK, label=False)
    S = (d or {}).get("sysinfo") or {}
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 4
    y = lz_nombre_estacion(L, (st.get("name") or "?").upper(), x0, y, x1 - x0)
    tipo = ST_TYPE.get(st.get("type"), st.get("type") or "")
    xa_ = x0 + put(L, F["small"], tipo, (x0, y), DIM, (x1 - x0) // 2) + 24
    put(L, F["small"], "ATRACADO", (xa_, y), BLUE)
    if st.get("dist"):
        put(L, F["small"], f"{st['dist']:,.0f} ls de la estrella".replace(",", "."), (x1, y), DIM, anchor="topright")
    y += hs + 8
    fac = st.get("faction") or S.get("st_faction")
    xv = x0 + tw_(F["small"], "FACCIÓN") + 20
    fn = F["btn"] if grande else F["small"]
    put(L, F["small"], "FACCIÓN", (x0, y + (fn.get_height() - hs) // 2), DIM)
    fst = S.get("st_fstate")
    wst = tw_(F["small"], fst) + 20 if fst else 0
    y2 = lz_faccion_estacion(L, fac, xv, y, x1 - xv - wst, fn)
    if fst:
        put(L, F["small"], fst, (x1, y + (fn.get_height() - hs) // 2), RED if fst in ("GUERRA", "GUERRA CIVIL", "BLOQUEO", "DISTURBIOS") else GREEN,
            anchor="topright")
    y = y2
    gv = " · ".join(x for x in (S.get("st_gov"), S.get("st_alleg"), st.get("economy")) if x)
    if gv:
        put(L, F["small"], gv, (xv, y), WHITE, x1 - xv); y += hs + 8
    y = lz_servicios(L, st, x0, x1, y, F["small"])
    facs = S.get("facs") or []
    if facs and y < area.bottom - 3 * hs:
        pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 6
        put(L, F["small"], "FACCIONES DEL SISTEMA", (x0, y), DIM); y += hs + 4
        lz_facciones(L, x0, x1, y, area.bottom - 4, facs, fac, grande)

# ---------------------------------------------------------------------------------------------------------------
# 8 ESTACIÓN pidiendo atraque: plataforma, reloj y altímetro
# ---------------------------------------------------------------------------------------------------------------
def lz_plataforma(L, cx, cy, rad, pad, now):
    """Esquema de la estación (12 sectores x 3 profundidades) con tu plataforma encendida y la ranura de entrada."""
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
            pygame.draw.polygon(L, ORANGE if on else BLACK, pts)
            pygame.draw.polygon(L, DIM, pts, 2)
    k_ = 0.6 + 0.4 * math.sin(now * 3)
    g = max(8, rad // 15)
    arc = pygame.Rect(cx - rad - g, cy - rad - g, 2 * (rad + g), 2 * (rad + g))
    pygame.draw.arc(L, tuple(int(c * k_) for c in RED[:3]), arc, math.radians(145), math.radians(215), g)
    pygame.draw.arc(L, tuple(int(c * k_) for c in GREEN[:3]), arc, math.radians(-35), math.radians(35), g)
    hs = F["small"].get_height()
    bw = tw_(F["small"], "ENTRADA") + 20
    pygame.draw.rect(L, BLACK, (cx - bw // 2, cy - hs // 2 - 4, bw, hs + 8))
    pygame.draw.rect(L, WHITE, (cx - bw // 2, cy - hs // 2 - 4, bw, hs + 8), 2)
    put(L, F["small"], "ENTRADA", (cx, cy), WHITE, anchor="center")
    pygame.draw.circle(L, RED, (cx - bw // 2 - 18, cy), max(5, rad // 18))
    pygame.draw.circle(L, GREEN, (cx + bw // 2 + 18, cy), max(5, rad // 18))
    put(L, F["small"], "12", (cx, cy - rad - g - 2), DIM, anchor="midbottom")
    put(L, F["small"], "6", (cx, cy + rad + g + 2), DIM, anchor="midtop")

def lz_estacion_atraque(L, area, d, flags, now, st):
    d = d or {}
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    pad, stype = st.get("pad"), st.get("type")
    rot = lz_fondo_estacion(L, area, d, st)
    alt = False
    try:
        alt = dock_alt_on(d)
    except Exception:
        pass
    colw = int(area.w * 0.46)
    col = pygame.Rect(area.x + 6, area.y + 4, colw, area.h - 8)
    x0 = col.right + 18 if (pad or alt) else area.x + 14
    x1 = area.right - 14
    if alt:                                                   # puerto planetario: ALTÍMETRO en la columna
        pygame.draw.rect(L, BLACK, col, border_radius=8)
        pygame.draw.rect(L, DIM, col, 2, border_radius=8)
        draw_alt(L, col.inflate(-8, -8), d, now)
        gs, vs = SPD.get("gs"), alt_vs()
        if gs is not None or vs is not None:
            tot = math.hypot(gs or 0, vs or 0)
            put(L, F["tiny"], "VEL.", (col.right - 50, col.y + 8), DIM, anchor="midtop")
            put(L, F["btn"], f"{tot:.0f}", (col.right - 50, col.y + 8 + F["tiny"].get_height()), WHITE, anchor="midtop")
        try:
            k, lab, c_ = carrier_kind(d, st)
            if k and lab:
                rot = (lab, c_)
        except Exception:
            pass
    elif pad and stype in STARPORTS:
        rad = min(col.w, col.h) // 2 - (28 if grande else 18)
        lz_plataforma(L, col.centerx, col.centery, rad, pad, now)
    elif pad:
        put(L, F["small"], "PLATAFORMA", (col.centerx, col.centery - F["num"].get_height() // 2 - 6), DIM, anchor="midbottom")
        put(L, F["num"], str(pad), col.center, ORANGE, anchor="center")
    y = area.y + 4
    y = lz_nombre_estacion(L, (st.get("name") or "?").upper(), x0, y, x1 - x0)
    if not st_label_shown(d, st):
        put(L, F["small"], ST_TYPE.get(stype, stype or ""), (x0, y), DIM, x1 - x0); y += hs + 4
    status = st.get("status")
    put(L, F["big"] if grande else F["btn"], status, (x0, y), STATUS_COL.get(status, DIM))
    y += (hg if grande else hb) + 4
    if status == "DENEGADO" and st.get("reason"):
        put(L, F["small"], st["reason"], (x0, y), RED, x1 - x0); y += hs + 4
    if pad:
        put(L, F["big"], f"PLATAFORMA {pad}", (x0, y), WHITE, x1 - x0); y += hg + 2
        if stype in STARPORTS:
            h_, d_ = pad_pos(pad)
            put(L, F["btn"], f"a las {h_}  ·  {PAD_DEPTH[d_]}", (x0, y), ORANGE, x1 - x0); y += hb + 6
    if st.get("faction"):
        y = lz_faccion_estacion(L, st["faction"], x0, y, x1 - x0, F["small"])
    left = dock_left(d, now)
    ylim = area.bottom - 4
    if rot:                                                   # rótulo del tipo abajo a la derecha (como antes)
        ylim -= hg + 8
    if left is not None:                                      # reloj de 10 minutos para atracar
        ch = int(min(220, area.h * 0.30))
        cr_ = pygame.Rect(x0, ylim - ch, x1 - x0, ch)
        pygame.draw.rect(L, BLACK, cr_.inflate(8, 8), border_radius=10)
        put(L, F["tiny"], "TIEMPO PARA ATRACAR", (cr_.centerx, cr_.y - 4), DIM, anchor="midbottom")
        draw_flip(L, cr_.inflate(-8, -8), mmss(left), clock_col(left, now), now, "dock")
        ylim = cr_.y - F["tiny"].get_height() - 10
    if st.get("dist") and y + hs <= ylim:
        put(L, F["small"], f"{st['dist']:,.0f} ls de la estrella".replace(",", "."), (x0, y), DIM); y += hs + 6
    if y + hs + 8 <= ylim:
        srv = set(st.get("services") or [])
        tags = [(t, ORANGE) for k, t in SERVICES if k in srv]
        if tags:
            lz_chips(L, tags, x0, x1, y, F["small"] if grande else F["tiny"], gap=6, pad=6)
    if rot:
        lab, c_ = rot
        pygame.draw.rect(L, BLACK, (x0 - 6, area.bottom - hg - 10, x1 - x0 + 12, hg + 8))
        put(L, F["big"], lab, (x1, area.bottom - hg - 6), c_, x1 - x0, anchor="topright")

def lv_estacion(L, area, d, flags, now):
    st = (d or {}).get("station") or {}
    key = (st.get("name"), st.get("status"))
    if not st.get("status"):
        put(L, F["big"], "Sin solicitud de atraque", area.center, DIM, anchor="center"); return
    if st.get("status") == "ATRACADO":
        if stdock["key"] != key:
            stdock.update(key=key, t=now)
        if now - stdock["t"] >= 15:
            S = (d or {}).get("sysinfo") or {}
            if (S.get("pp") or S.get("pp_conf") or S.get("powers")) and (now - stdock["t"] - 15) % 15 >= 10:
                return lz_pp(L, area, d, now)
            return lz_estacion_ficha(L, area, d, st)
    else:
        stdock["key"] = None
    lz_estacion_atraque(L, area, d, flags, now, st)

# ---------------------------------------------------------------------------------------------------------------
# 127 MERCADO
# ---------------------------------------------------------------------------------------------------------------
def lz_banda(L, r, txt, col, txtcol):
    pygame.draw.rect(L, col, r, border_radius=8)
    put(L, F["btn"], txt, r.center, txtcol, r.w - 16, anchor="center")

def lz_mercado_bandas(L, area, d, now):
    """Franja de arriba: ENTREGA AQUÍ (tu depósito) o BODEGA LLENA / CASI LLENA. Devuelve su alto."""
    hb = F["btn"].get_height()
    r = pygame.Rect(area.x + 6, area.y + 2, area.w - 12, hb + 10)
    if (d or {}).get("Flags", 0) & 1 and ((d or {}).get("colonia") or {}).get("dock"):
        car = _col_carried(d)
        if car:
            on = int(now * 2) % 2
            tot = sum(c[2] for c in car)
            lz_banda(L, r, f"ENTREGA AQUÍ LOS MATERIALES · {tot:,} t".replace(",", "."), GREEN if on else (20, 90, 40), BLACK if on else WHITE)
            TAP_EV.set()
            return r.h + 8
    h = hold_state(d)
    if h:
        used, cap = h
        if used >= cap:
            c_ = RED if int(now * 2) % 2 else (110, 0, 0)
            lz_banda(L, r, f"BODEGA LLENA · {used:,} / {cap:,} t".replace(",", "."), c_, BLACK if c_ == RED else WHITE)
            TAP_EV.set()
            return r.h + 8
        if used >= cap * 0.95:
            lz_banda(L, r, f"BODEGA CASI LLENA · QUEDAN {cap - used:,} t".replace(",", "."), ORANGE, BLACK)
            return r.h + 8
    return 0

def lz_marca(L, area, txt, y):
    w = tw_(F["small"], txt) + 30
    r = pygame.Rect(area.right - 8 - w, y, w, F["small"].get_height() + 10)
    pygame.draw.rect(L, BLACK, r, border_radius=6)
    pygame.draw.rect(L, GREEN, r, 2, border_radius=6)
    put(L, F["small"], txt, r.center, GREEN, anchor="center")
    return r

def lz_mkcol(L, area, d, now):
    """El MERCADO en modo COLONIA: lo que te falta para tu construcción y que se vende aquí."""
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 4
    lz_marca(L, area, "‹ MERCADO", y)
    put(L, F["btn"], "PARA TU COLONIA · SE VENDE AQUÍ", (x0, y), GREEN, area.w - 300)
    y += hb + 10
    try:
        rows = col_big_rows(d, now)
    except Exception:
        rows = []
    pie = area.bottom - hs - 6
    if rows:
        w = x1 - x0
        cols = (x0, x0 + int(w * 0.46), x0 + int(w * 0.63), x0 + int(w * 0.82))
        for x_, t_ in zip(cols, ("MATERIAL", "FALTA", "PRECIO", "HAY")):
            put(L, F["small"], t_, (x_, y), DIM)
        y += hs + 4
        pygame.draw.line(L, (0, 90, 30), (x0, y), (x1, y), 2); y += 6
        fn = F["btn"] if area.h > 400 else F["small"]
        rh = fn.get_height() + 6
        caben = max(1, (pie - 6 - y) // rh)
        for name, stock, price, falta in rows[:caben]:
            put(L, fn, name, (cols[0], y), GREEN, cols[1] - cols[0] - 10)
            put(L, fn, f"{falta:,} t".replace(",", "."), (cols[1], y), ORANGE)
            put(L, fn, f"{price:,}".replace(",", "."), (cols[2], y), WHITE)
            put(L, fn, f"{stock:,} t".replace(",", "."), (cols[3], y), WHITE if stock >= falta else ORANGE)
            y += rh
        if len(rows) > caben:
            put(L, F["small"], f"+{len(rows) - caben} más en COLONIZACIÓN", (x0, y), DIM)
    else:
        put(L, F["btn"], "Aquí no venden nada de lo que te falta", (x0, y), ORANGE, x1 - x0); y += hb + 8
        m_ = {}
        try:
            m_ = market_pick(d, now)
        except Exception:
            pass
        if m_.get("missing") or m_.get("src") == "EDSM" or m_.get("other"):
            put(L, F["small"], "abre el mercado en el juego para comprobarlo", (x0, y), DIM, x1 - x0); y += hs + 6
        x, need = _col_need_keys(d)
        alt = _col_alt(d, need, str(((d or {}).get("station") or {}).get("mid"))) if need else None
        if alt:
            put(L, F["small"], f"prueba en {alt[0]}: {', '.join(alt[1][:3])}", (x0, y), GREEN, x1 - x0); y += hs + 8
        y += 6
        put(L, F["small"], "TE FALTA", (x0, y), DIM); y += hs + 4
        fn = F["btn"] if area.h > 400 else F["small"]
        rh = fn.get_height() + 4
        for name, falta in col_falta(d)[:max(1, (pie - 6 - y) // rh)]:
            put(L, fn, name, (x0, y), ORANGE, (x1 - x0) // 2)
            put(L, fn, f"{falta:,} t".replace(",", "."), (x1, y), ORANGE, anchor="topright")
            y += rh
    car = _col_carried(d)
    if car:
        put(L, F["small"], f"llevas {sum(c[2] for c in car):,} t para la construcción".replace(",", "."), (x0, pie), BLUE)
    put(L, F["small"], "toca: MERCADO", (x1, pie), DIM, anchor="topright")

def lv_mercado(L, area, d, flags, now):
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    x0, x1 = area.x + 14, area.right - 14
    lz_hit(area, "old", W // 2, TOP + 30)                   # tocar: COLONIA <-> MERCADO o página siguiente (como antes)
    if mkcol_on(d):
        return lz_mkcol(L, area, d, now)
    m = market_pick(d, now)
    if m.get("missing"):
        cy = area.centery
        put(L, F["big"], m["missing"].upper(), (area.centerx, cy - hg), ORANGE, area.w - 30, anchor="center")
        put(L, F["btn"], "abre su mercado para ver los precios", (area.centerx, cy + 4), DIM, anchor="center")
        put(L, F["small"], "EDSM no tiene sus precios" if m.get("edsm") else "consultando EDSM...", (area.centerx, cy + hb + 10), DIM,
            anchor="center")
        return
    if not m.get("station"):
        put(L, F["btn"], "Abre el mercado en una estación", area.center, DIM, anchor="center"); return
    otro = m.get("src") == "EDSM" or m.get("other")
    y = area.y + 2 + lz_mercado_bandas(L, area, d, now)
    falta = col_falta(d)
    marca = None
    if falta:
        marca = lz_marca(L, area, "COLONIA ›", y)
    age = int((time.time() - (m.get("t") or time.time())) / 60)
    xr = (marca.x - 16) if marca else x1
    edad = f"hace {age} min" if age else "ahora"
    put(L, F["btn"], m["station"].upper(), (x0, y), ORANGE, xr - x0 - tw_(F["small"], edad) - 20)
    put(L, F["small"], edad, (xr, y + (hb - hs) // 2), DIM, anchor="topright")
    y += hb + 6
    sell = m.get("sell") or []
    rows = sell if sell else m.get("best") or []
    put(L, F["small"], "TU BODEGA AQUÍ" if sell else "BODEGA VACÍA · LO MEJOR PAGADO AQUÍ (vs media)", (x0, y), DIM, x1 - x0 - 120)
    if sell:
        put(L, F["small"], "TOTAL", (x1, y), DIM, anchor="topright")
    y += hs + 4
    # abajo: total / no vendas, y encima el recuadro PARA TU COLONIA
    pie = area.bottom - hb - 6
    if sell:
        tot = sum(r[1] * r[2] for r in sell)
        medio = sum(r[1] * r[3] for r in sell if len(r) > 3 and r[3])
        col_ = mkt_para_colonia(d)
        pygame.draw.line(L, DIM, (x0, pie - 6), (x1, pie - 6), 2)
        if col_:
            if int(now * 2) % 2:
                pygame.draw.rect(L, (60, 30, 0), (x0 - 6, pie - 2, x1 - x0 + 12, hb + 6), border_radius=6)
            put_fit(L, ("btn", "small"), "NO VENDAS AQUÍ LOS MATERIALES DE COLONIZACIÓN", (x0, pie), ORANGE, x1 - x0)
        elif medio and tot < medio * 0.95:
            put_fit(L, ("btn", "small"), f"VENDIENDO TODO: {cr(tot)} cr ({100 * tot / medio - 100:+.0f} %: aquí pagan poco)", (x0, pie), ORANGE,
                    x1 - x0)
        else:
            put(L, F["btn"], f"VENDIENDO TODO: {cr(tot)} cr", (x0, pie), GREEN)
        ylim = pie - 14
    else:
        ylim = area.bottom - 4
    if otro:
        tag = "EDSM" if m.get("src") == "EDSM" else "OTRA ESTACIÓN DEL SISTEMA"
        put(L, F["small"], tag, (x1, ylim - hs), BLUE, anchor="topright")
        ylim -= hs + 6
    if not otro and falta:                                   # recuadro PARA TU COLONIA (lo que falta de verdad)
        C, Lc, i = col_pick(d)
        if Lc:
            real = {t[0].lower(): t[5] for t in col_rows(d, Lc[i])}
            crow = [r for r in ((d or {}).get("market") or {}).get("col") or [] if real.get((r[0] or "").lower(), 0) > 0]
            if crow:
                n = min(4 if grande else 2, len(crow))
                fr = F["small"]
                bh = hs + 12 + n * (hs + 4)
                box = pygame.Rect(x0 - 6, ylim - bh, x1 - x0 + 12, bh)
                pygame.draw.rect(L, (0, 28, 8), box, border_radius=8)
                pygame.draw.rect(L, GREEN, box, 2, border_radius=8)
                put(L, fr, "PARA TU COLONIA (se vende aquí)" + (f"  +{len(crow) - n} más" if len(crow) > n else "") + "  · toca: ver todo",
                    (box.x + 10, box.y + 4), GREEN, box.w - 20)
                yy = box.y + hs + 8
                for name, stock, price, need in (r_[:4] for r_ in crow[:n]):
                    put(L, fr, name, (box.x + 14, yy), GREEN, int(box.w * 0.38))
                    put(L, fr, f"hay {stock:,} t · {price:,} cr".replace(",", "."), (box.x + int(box.w * 0.42), yy), WHITE, int(box.w * 0.36))
                    put(L, fr, f"faltan {real[name.lower()]:,} t".replace(",", "."), (box.right - 12, yy), ORANGE, anchor="topright")
                    yy += hs + 4
                ylim = box.y - 8
    # la tabla
    fn = F["btn"] if grande else F["small"]
    rh = fn.get_height() + (8 if grande else 3)
    per = max(1, (ylim - y) // rh)
    pages = max(1, (len(rows) + per - 1) // per)
    pg = ui.get("page127", 0) % pages
    w = x1 - x0
    c_t, c_p, c_d = x0 + int(w * 0.50), x0 + int(w * 0.68), x0 + int(w * 0.78)
    for r in rows[pg * per:(pg + 1) * per]:
        if sell:
            name, n, price, mean, dem = r
        else:
            name, price, mean = r; n = None
        diff = (price - mean) / mean * 100 if mean else 0
        put(L, fn, name, (x0, y), ORANGE, c_t - x0 - 140)
        if n is not None:
            put(L, fn, f"{n} t", (c_t, y), WHITE, anchor="topright")
        put(L, fn, f"{price:,} cr".replace(",", "."), (c_p, y), WHITE, anchor="topright")
        put(L, fn, f"{diff:+.0f}%", (c_d, y), GREEN if diff >= 0 else RED, anchor="topright")
        if n is not None:
            put(L, fn, cr(n * price), (x1, y), GREEN if diff >= 0 else ORANGE, anchor="topright")
        y += rh
    if pages > 1:
        put(L, F["small"], f"pág {pg + 1}/{pages}  (toca para pasar)", (area.centerx, ylim - hs), DIM, anchor="midtop")

# ---------------------------------------------------------------------------------------------------------------
# ATRAQUE (un solo cuadro en el tablero): la ESTACIÓN nueva a pantalla entera
# ---------------------------------------------------------------------------------------------------------------
_hi_cell_v20b9 = hi_cell

def hi_cell(S, fn, d, flags, now, area, how):
    if lienzo_on() and LZ.get("lleno") == "tablero" and fn is VIEWS.get(8) and 8 in LZ_PANEL \
            and area == lz_real((8, LZ_CABH + 6, LW - 16, LH - LZ_CABH - 12)):
        r = pygame.Rect(8, LZ_CABH + 6, LW - 16, LH - LZ_CABH - 12)
        def _dib(L):
            hits0 = LZ["hits"]
            try:
                LZ_PANEL[8](L, r, d, flags, now)
            finally:
                LZ["hits"] = hits0
        if lienzo_dibuja(S, _dib):
            return True
    return _hi_cell_v20b9(S, fn, d, flags, now, area, how)

LZ_PANEL.update({8: lv_estacion, 127: lv_mercado})
for _v, _fn in ((8, lv_estacion), (127, lv_mercado)):
    LZ_CELDA[_v] = (lambda fn: (lambda L, d, flags, now: fn(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now)))(_fn)
