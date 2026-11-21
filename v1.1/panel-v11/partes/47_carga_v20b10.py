# Panel Elite v2.0 · parte 47: v2.0b10 — CARGA y NAVE a 1280x800 (con PANTALLA v2)
#   4 CARGA/MISIÓN (BODEGA, MISIONES, PASAJEROS), 210 PASAJEROS, 217 CABINA, 125 MATERIALES, 126 PORTANAVES,
#   135 COLONIZACIÓN (TODO, AQUÍ, EN EL SISTEMA), 170 NAVE y 171 FLOTA, en el MENÚ (LZ_PANEL) y, las que salen en el
#   tablero (4, 210 y la CABINA del cuadro 4), como cuadros (LZ_CELDA). Mismos datos y mismos toques que antes:
#   pestañas y filtros tocan el centro de su botón de 480x320 y el resto de la pantalla pasa de página.

def lz_pagina(L, area, pg, pages, y=None):
    """«pág 2/3 · toca para pasar» abajo en el centro."""
    if pages > 1:
        hs = F["small"].get_height()
        put(L, F["small"], f"pág {pg + 1}/{pages}  ·  toca para pasar", (area.centerx, y if y is not None else area.bottom - hs), DIM,
            anchor="midtop")

def lz_vacio(L, area, txt, sub=None):
    hb = F["btn"].get_height()
    put(L, F["btn"], txt, (area.centerx, area.centery - (hb // 2 if sub else 0)), DIM, area.w - 30, anchor="center")
    if sub:
        put(L, F["small"], sub, (area.centerx, area.centery + hb // 2 + 6), DIM, area.w - 30, anchor="center")

def lz_barra_h(L, r, pct, col, borde=DIM):
    pygame.draw.rect(L, borde, r, 2, border_radius=4)
    w = int((r.w - 6) * max(0.0, min(1.0, pct)))
    if w > 0:
        pygame.draw.rect(L, col, (r.x + 3, r.y + 3, w, r.h - 6), border_radius=2)

def _lz_hace(sec):
    """«ahora», «5 min», «3 h», «12 días» (el _hace de la parte 10; la parte 26 reusó el nombre y salía «hace hace 20766 días»)."""
    return "?" if sec is None or sec < 0 else "ahora" if sec < 60 else f"{int(sec // 60)} min" if sec < 3600 else \
        f"{sec / 3600:.0f} h" if sec < 172800 else f"{sec / 86400:.0f} días"

# ---------------------------------------------------------------------------------------------------------------
# 210 PASAJEROS (también la pestaña PASAJEROS de 4 CARGA/MISIÓN)
# ---------------------------------------------------------------------------------------------------------------
def lz_pax(L, area, d, now, page=0):
    Lp = pax_list(d)
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    if not Lp:
        return lz_vacio(L, area, "Sin pasajeros a bordo")
    tot = sum(p.get("n", 0) for p in Lp)
    y = area.y + 4
    put(L, F["small"], f"{tot} pasajero{'s' if tot != 1 else ''} en {len(Lp)} misi{'ones' if len(Lp) != 1 else 'ón'} · "
                       f"{cr(sum(p.get('cr', 0) for p in Lp))} cr", (x0, y), DIM, x1 - x0)
    y += hs + 10
    grande = area.h > 400
    fn = F["btn"] if grande else F["small"]
    fs = F["small"] if grande else F["tiny"]
    rh = fn.get_height() + fs.get_height() + (22 if grande else 10)
    pie = area.bottom - hs - 6
    per = max(1, (pie - y) // rh)
    pages = (len(Lp) + per - 1) // per
    pg = page % pages
    for p in Lp[pg * per:(pg + 1) * per]:
        crt = f"{cr(p.get('cr', 0))} cr"
        x = x0 + put(L, fn, f"{p.get('n', 0)} {pax_label(p).upper()}", (x0, y), ORANGE, x1 - x0 - tw_(fn, crt) - 200) + 16
        for t_, c_, on in (("VIP", BLUE, p.get("vip")), ("BUSCADOS", RED, p.get("wanted"))):
            if on:
                w_ = tw_(fs, t_) + 16
                r_ = pygame.Rect(x, y + (fn.get_height() - fs.get_height()) // 2 - 3, w_, fs.get_height() + 6)
                pygame.draw.rect(L, c_, r_, 2, border_radius=5)
                put(L, fs, t_, r_.center, c_, anchor="center")
                x += w_ + 10
        put(L, fn, crt, (x1, y), GREEN, anchor="topright")
        y2 = y + fn.get_height() + 4
        left = (p.get("exp") or 0) - now
        tt = fmt_time(left) if p.get("exp") else ""
        put(L, fs, f"→ {p.get('st') or '?'} · {p.get('sys') or '?'}".replace("→", ">"), (x0 + 8, y2), DIM, x1 - x0 - tw_(fs, tt) - 30)
        if tt:
            put(L, fs, tt, (x1, y2), RED if left < 1800 else DIM, anchor="topright")
        y += rh
        pygame.draw.line(L, (60, 35, 0), (x0, y - (12 if grande else 5)), (x1, y - (12 if grande else 5)), 1)
    lz_pagina(L, area, pg, pages, pie + 2)

def lv_pax(L, area, d, flags, now):
    lz_hit(area, "old", W // 2, TOP + 40)                  # tocar: página siguiente
    lz_pax(L, area, d, now, ui.get("page4", 0))

# ---------------------------------------------------------------------------------------------------------------
# 4 CARGA/MISIÓN
# ---------------------------------------------------------------------------------------------------------------
def lv_carga(L, area, d, flags, now):
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    cargo = (d or {}).get("cargo") or []
    miss = (d or {}).get("missions") or []
    used = sum(c for _, c in cargo)
    cap = (d or {}).get("cargocap")
    Lp = pax_list(d)
    tabs = [f"BODEGA {used}/{cap if cap is not None else '?'} t", f"MISIONES ({len(miss)})"]
    if Lp:
        tabs.append(f"PASAJEROS ({sum(p.get('n', 0) for p in Lp)})")
    elif ui["tab4"] == 2:
        ui["tab4"] = 1
    lz_hit(area, "old", W // 2, H - 12)                    # tocar debajo de las pestañas: página siguiente
    th = (hb + 22) if grande else (F["small"].get_height() + 16)
    tr = pygame.Rect(area.x + 8, area.y + 2, area.w - 16, th)
    for i, t in enumerate(tabs):
        r = lz_grid(tr, i, len(tabs), 1, gap=12 if grande else 8)
        r.y, r.h = tr.y, tr.h
        lz_boton_v(L, r, t, None, F["btn"] if grande else F["small"], filled=ui["tab4"] == i, viejo=tab_rect_n(i, len(tabs)))
    top = tr.bottom + (14 if grande else 8)
    cuerpo = pygame.Rect(area.x, top, area.w, area.bottom - top)
    if ui["tab4"] == 2:
        return lz_pax(L, cuerpo, d, now, ui["page4"])
    x0, x1 = area.x + 14, area.right - 14
    pie = area.bottom - hs - 6
    if ui["tab4"] == 0:
        if not cargo:
            return lz_vacio(L, cuerpo, "Bodega vacía")
        y = top
        if cap:
            pct = used / cap if cap else 0
            col = RED if used >= cap else ORANGE if pct >= 0.95 else BLUE
            libre = f"{max(0, cap - used):,} t libres".replace(",", ".")
            bh = 18 if grande else 12
            lz_barra_h(L, pygame.Rect(x0, y + 2, x1 - x0 - tw_(F["small"], libre) - 20, bh), pct, col)
            put(L, F["small"], libre, (x1, y + bh // 2 + 2), RED if used >= cap else DIM, anchor="midright")
            y += bh + (16 if grande else 8)
        fn = F["btn"] if grande else F["small"]
        rh = fn.get_height() + (14 if grande else 5)
        filas = max(1, (pie - y) // rh)
        cols = 2 if len(cargo) > filas else 1
        per = filas * cols
        pages = (len(cargo) + per - 1) // per
        pg = ui["page4"] % pages
        vis = cargo[pg * per:(pg + 1) * per]
        cw = (x1 - x0 - (30 if cols > 1 else 0)) // cols
        nf = -(-len(vis) // cols)
        for k, (name, cnt) in enumerate(vis):
            cx = x0 + (k // nf) * (cw + 30)
            cy = y + (k % nf) * rh
            put(L, fn, name, (cx, cy), ORANGE, cw - tw_(fn, f"{cnt} t") - 20)
            put(L, fn, f"{cnt} t", (cx + cw, cy), WHITE, anchor="topright")
            pygame.draw.line(L, (60, 35, 0), (cx, cy + rh - (7 if grande else 3)), (cx + cw, cy + rh - (7 if grande else 3)), 1)
        return lz_pagina(L, area, pg, pages, pie + 2)
    if not miss:
        return lz_vacio(L, cuerpo, "Sin misiones activas")
    fn = F["btn"] if grande else F["small"]
    fs = F["small"] if grande else F["tiny"]
    rh = fn.get_height() + fs.get_height() + (22 if grande else 8)
    per = max(1, (pie - top) // rh)
    pages = (len(miss) + per - 1) // per
    pg = ui["page4"] % pages
    y = top
    for name, dest, exp in miss[pg * per:(pg + 1) * per]:
        put(L, fn, name, (x0, y), ORANGE, x1 - x0)
        y2 = y + fn.get_height() + 4
        left = exp - time.time() if exp else 0
        tt = fmt_time(left) if exp else ""
        put(L, fs, f"> {dest or '?'}", (x0 + 8, y2), DIM, x1 - x0 - tw_(fs, tt) - 30)
        if tt:
            put(L, fs, tt, (x1, y2), RED if left < 3600 else DIM, anchor="topright")
        y += rh
        pygame.draw.line(L, (60, 35, 0), (x0, y - (12 if grande else 4)), (x1, y - (12 if grande else 4)), 1)
    lz_pagina(L, area, pg, pages, pie + 2)

# ---------------------------------------------------------------------------------------------------------------
# 217 CABINA DE PASAJEROS
# ---------------------------------------------------------------------------------------------------------------
def lv_cabina(L, area, d, flags, now):
    Lp, n, plazas, cl, nv, nw = pax_resumen(d)
    if not Lp:
        return lz_vacio(L, area, "Sin pasajeros a bordo")
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 4
    marcas = [t for t, on in (("VIP", nv > 0), ("BUSCADOS", nw > 0)) if on]
    mt = " · ".join(marcas)
    tit = f"{n} PASAJERO{'S' if n != 1 else ''}" + (f" · {n}/{plazas} PLAZAS" if plazas > n else "") + \
          (f" · {PAX_CLS[cl]}" if cl in PAX_CLS else "")
    ft = F["big"] if grande else F["btn"]
    put(L, ft, tit, (x0, y), ORANGE, x1 - x0 - (tw_(F["small"], mt) + 20 if mt else 0))
    if mt:
        put(L, F["small"], mt, (x1, y + (ft.get_height() - hs) // 2), RED if nw else BLUE, anchor="topright")
    y += ft.get_height() + (12 if grande else 6)
    fs = F["btn"] if grande else F["small"]
    rh = fs.get_height() + (10 if grande else 4)
    nl = min(len(Lp), 4 if grande else 3)
    hc = area.bottom - y - nl * rh - (rh if len(Lp) > nl else 0) - (14 if grande else 6)
    hc = max(60, min(hc, int(area.h * 0.55)))
    dibuja_cabina(L, pygame.Rect(x0, y, x1 - x0, hc), n, plazas, nv, nw)
    y += hc + (14 if grande else 6)
    for p in Lp[:nl]:
        left = (p.get("exp") or 0) - now
        der = f"{cr(p.get('cr', 0))} cr · " + (fmt_time(left) if p.get("exp") else "--")
        t_ = f"{p.get('n', 0)} {pax_label(p)} > {p.get('st') or p.get('sys') or '?'}"
        c_ = RED if p.get("wanted") else BLUE if p.get("vip") else WHITE
        put(L, fs, t_, (x0, y), c_, x1 - x0 - tw_(fs, der) - 24)
        put(L, fs, der, (x1, y), RED if p.get("exp") and left < 1800 else GREEN, anchor="topright")
        y += rh
    if len(Lp) > nl:
        put(L, F["small"] if grande else F["tiny"], f"+{len(Lp) - nl} misiones más en 4 CARGA/MISIÓN", (x0, y), DIM)

# ---------------------------------------------------------------------------------------------------------------
# 125 MATERIALES
# ---------------------------------------------------------------------------------------------------------------
def lv_mats(L, area, d, flags, now):
    lz_hit(area, "old", W // 2, TOP + 40)                  # tocar: página siguiente
    M = (d or {}).get("mats") or {}
    rows = M.get("list") or []
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 4
    put(L, F["small"], f"{M.get('n', 0)} materiales", (x0, y), DIM)
    put(L, F["small"], f"AL MÁXIMO: {M.get('full', 0)}", (x1, y), RED if M.get("full") else DIM, anchor="topright")
    y += hs + 12
    if not rows:
        return lz_vacio(L, pygame.Rect(area.x, y, area.w, area.bottom - y), "Sin datos (carga la partida)")
    pie = area.bottom - hs - 6
    fn = F["btn"] if grande else F["small"]
    rh = fn.get_height() + (16 if grande else 6)
    filas = max(1, (pie - y) // rh)
    cols = 2 if len(rows) > filas else 1
    per = filas * cols
    pages = (len(rows) + per - 1) // per
    pg = ui.get("page125", 0) % pages
    gap = 40
    cw = (x1 - x0 - (gap if cols > 1 else 0)) // cols
    vis = rows[pg * per:(pg + 1) * per]
    nf = -(-len(vis) // cols)
    for k, (name, c, mx) in enumerate(vis):
        cx, cy = x0 + (k // nf) * (cw + gap), y + (k % nf) * rh
        pct = c / mx if mx else 0
        col = RED if c >= mx else ORANGE if pct >= 0.9 else WHITE
        num = f"{c}/{mx}"
        wn = tw_(fn, "000/000") + 10
        wname = int(cw * 0.48)
        put(L, fn, name, (cx, cy), ORANGE, wname - 10)
        bx = pygame.Rect(cx + wname, cy + fn.get_height() // 2 - (9 if grande else 6), cw - wname - wn - 10, 18 if grande else 12)
        lz_barra_h(L, bx, pct, RED if c >= mx else BLUE)
        put(L, fn, num, (cx + cw, cy), col, anchor="topright")
    lz_pagina(L, area, pg, pages, pie + 2)

# ---------------------------------------------------------------------------------------------------------------
# 126 PORTANAVES
# ---------------------------------------------------------------------------------------------------------------
def lv_carrier(L, area, d, flags, now):
    c = (d or {}).get("carrier") or {}
    sq = (d or {}).get("sqcarrier") or {}
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    if not (c.get("name") or c.get("callsign")):
        lz_vacio(L, area, "Sin datos del portanaves", "abre su gestión en el juego una vez")
    else:
        rr = L._r(area).clip(L.real.get_rect())
        img = bg_img("fc", rr.w, rr.h, BG_DOCK_DARK)
        if img is not None:
            L.real.blit(img, rr.topleft)
        x0, x1 = area.x + 14, area.right - 14
        y = area.y + 6
        cs = c.get("callsign") or ""
        put(L, F["big"], (c.get("name") or "").upper(), (x0, y), ORANGE, x1 - x0 - tw_(F["btn"], cs) - 30)
        put(L, F["btn"], cs, (x1, y + (hg - hb) // 2), DIM, anchor="topright")
        y += hg + (16 if grande else 8)
        fl = F["small"]
        xv = x0 + tw_(fl, "TRITIO") + 30
        put(L, fl, "SISTEMA", (x0, y + (hb - hs) // 2), DIM)
        put(L, F["btn"], c.get("system") or "?", (xv, y), ORANGE, x1 - xv); y += hb + (14 if grande else 6)
        fuel = c.get("fuel")
        put(L, fl, "TRITIO", (x0, y + (hb - hs) // 2), DIM)
        ft = f"{fuel} t" if fuel is not None else "?"
        fcol = RED if fuel is not None and fuel < 135 else ORANGE
        bx = pygame.Rect(xv, y + hb // 2 - (12 if grande else 8), x1 - xv - tw_(F["btn"], "1000 t") - 24, 24 if grande else 16)
        lz_barra_h(L, bx, (fuel or 0) / 1000, RED if fuel is not None and fuel < 135 else GREEN)
        put(L, F["btn"], ft, (x1, y), fcol, anchor="topright"); y += hb + (14 if grande else 6)
        put(L, fl, "SALDO", (x0, y + (hg - hs) // 2), DIM)
        put(L, F["big"], f"{cr(c.get('balance'))} cr", (xv, y), ORANGE, x1 - xv); y += hg + (14 if grande else 6)
        pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 12 if grande else 6
        lim = area.bottom - ((hb + 20) if sq.get("system") else 4)
        dest, dep = c.get("dest"), c.get("depart")
        if dest and dep:
            left = dep - time.time()
            put(L, fl, "SALTO PROGRAMADO A", (x0, y), DIM); y += hs + 4
            put(L, F["big"], dest.upper(), (x0, y), BLUE, x1 - x0); y += hg + 8
            if left > 0:
                ch = min(lim - y, 240 if grande else 110)
                if ch >= 40:
                    w_ = min(x1 - x0, int(ch * 2.6))
                    r_ = pygame.Rect(area.centerx - w_ // 2, y, w_, ch)
                    pygame.draw.rect(L, BLACK, r_.inflate(8, 8), border_radius=10)
                    draw_flip(L, r_.inflate(-8, -8), mmss(left), ORANGE if left > 60 else RED, now, "fcjump")
            else:
                put(L, F["big"], "SALTANDO...", (area.centerx, y + 10), BLUE if int(now * 2) % 2 else WHITE, anchor="midtop")
        else:
            put(L, F["btn"], "Sin salto programado", (area.centerx, (y + lim) // 2), DIM, anchor="center")
    if sq.get("system"):
        x0, x1 = area.x + 14, area.right - 14
        yb = area.bottom - hb - 10
        pygame.draw.rect(L, BLACK, (area.x, yb - 6, area.w, hb + 16))
        pygame.draw.line(L, DIM, (x0, yb - 6), (x1, yb - 6), 2)
        put(L, F["small"], "PORTANAVES DE ESCUADRÓN", (x0, yb + (hb - hs) // 2), BLUE)
        put(L, F["btn"], sq["system"], (x1, yb), BLUE, x1 - x0 - tw_(F["small"], "PORTANAVES DE ESCUADRÓN") - 30, anchor="topright")

# ---------------------------------------------------------------------------------------------------------------
# 135 COLONIZACIÓN
# ---------------------------------------------------------------------------------------------------------------
def _lz_colir(acc, X, Y):
    tap_flash(("colir",))
    ir_send(acc[1])

LZ_ACC["colir"] = _lz_colir

def lv_colonia(L, area, d, flags, now):
    C, Lc, i = col_pick(d)
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    x0, x1 = area.x + 14, area.right - 14
    if not Lc:
        if d and "colonia" not in d:
            return lz_vacio(L, area, "actualiza el sender a la v1.0b9")
        return lz_vacio(L, area, "sin construcciones", "atraca en un depósito de construcción y abre su mercado")
    lz_hit(area, "old", W // 2, H - 8)                     # tocar el resto: página siguiente
    x = Lc[i]
    rows = col_rows(d, x)
    here = col_here(d)
    S, off, hit, scol = col_sys_state(d, rows)
    f = ui.get("colf", "todo")
    fs, ft = F["small"], F["tiny"]
    # cabecera: nombre (tocar = otra construcción) y filtros
    y = area.y + 4
    fh = F["small"]
    bw = [tw_(fh, lab) + (40 if grande else 24) for _, lab in COLF]
    bh = fh.get_height() + (18 if grande else 10)
    xb = x1 - sum(bw) - 10 * (len(bw) - 1)
    nm = (x.get("st") or "CONSTRUCCIÓN").upper() + (" · " + x["sys"] if x.get("sys") else "")
    fn_ = F["btn"] if grande else F["small"]
    cnt = f"{i + 1}/{len(Lc)} >" if len(Lc) > 1 else ""
    w_ = put(L, fn_, nm, (x0, y + (bh - fn_.get_height()) // 2), ORANGE, xb - x0 - tw_(fs, cnt) - 30)
    if cnt:
        put(L, fs, cnt, (x0 + w_ + 14, y + (bh - hs) // 2), BLUE)
    lz_hit(pygame.Rect(area.x, area.y, xb - 10 - area.x, bh + 8), "old", COL_HEAD.centerx, COL_HEAD.centery)
    xx = xb
    for k, (fk, lab) in enumerate(COLF):
        r = pygame.Rect(xx, y, bw[k], bh)
        sel = f == fk
        col = scol if fk == "sis" else ORANGE
        pygame.draw.rect(L, col if sel else BLACK, r, border_radius=8)
        pygame.draw.rect(L, col, r, 2, border_radius=8)
        put(L, fh, lab, r.center, BLACK if sel else col, r.w - 8, anchor="center")
        lz_hit(r.inflate(6, 10), "old", COLF_R[k].centerx, COLF_R[k].centery)
        xx += bw[k] + 10
    y += bh + (12 if grande else 6)
    # progreso
    bar = pygame.Rect(x0, y, x1 - x0, hs + 8)
    pygame.draw.rect(L, DIM, bar, 2, border_radius=4)
    pygame.draw.rect(L, GREEN if x.get("done") else ORANGE,
                     (bar.x + 3, bar.y + 3, int((bar.w - 6) * min(100, x.get("prog") or 0) / 100), bar.h - 6), border_radius=2)
    st_ = "COMPLETADA" if x.get("done") else "FALLIDA" if x.get("fail") else f"{x.get('prog', 0):.1f} %".replace(".", ",")
    put(L, fs, st_, bar.center, WHITE, anchor="center")
    y += bar.h + (10 if grande else 5)
    falta = sum(t[5] for t in rows)
    bod = sum(t[4] for t in rows)
    cap = (d or {}).get("cargocap") or 0
    t_ = f"FALTAN {falta:,} t".replace(",", ".") + (f" · ~{-(-falta // cap)} viajes de {cap} t" if cap and falta else "")
    xx = put(L, fn_, t_, (x0, y), WHITE if falta else GREEN, x1 - x0)
    if bod:
        put(L, fs, f"  ·  {bod:,} t en bodega por entregar".replace(",", "."), (x0 + xx, y + (fn_.get_height() - hs) // 2), BLUE,
            x1 - x0 - xx)
    y += fn_.get_height() + (12 if grande else 5)
    pie = area.bottom - (hs if grande else ft.get_height()) - 4
    fp = fs if grande else ft
    if f == "todo":
        fr = fs if grande else ft
        rh = fr.get_height() + (12 if grande else 3)
        filas = max(1, (pie - 6 - y) // rh)
        per = filas * 2
        pages = max(1, (len(rows) + per - 1) // per)
        pg = ui.get("colpg", 0) % pages
        vis = rows[pg * per:(pg + 1) * per]
        nrow = min(filas, max(1, (len(vis) + 1) // 2))
        gap = 30
        cw = (x1 - x0 - gap) // 2
        wn = int(cw * 0.42)
        wb = int(cw * 0.28)
        for k, (name, key, req, prov, inb, real) in enumerate(vis):
            cx, cy = x0 + (k // nrow) * (cw + gap), y + (k % nrow) * rh
            sold = _hh(here, name, key) is not None and real > 0
            col = BLUE if real == 0 else GREEN if sold else ORANGE
            put(L, fr, ("• " if sold else "") + name, (cx, cy), col, wn - 8)
            b = pygame.Rect(cx + wn, cy + fr.get_height() // 2 - (7 if grande else 4), wb, 14 if grande else 8)
            pygame.draw.rect(L, DIM, b, 1)
            iw = b.w - 2
            w1 = int(iw * prov / req) if req else 0
            w2 = int(iw * inb / req) if req else 0
            if w1:
                pygame.draw.rect(L, ORANGE, (b.x + 1, b.y + 1, w1, b.h - 2))
            if w2:
                pygame.draw.rect(L, BLUE, (b.x + 1 + w1, b.y + 1, min(w2, iw - w1), b.h - 2))
            if real == 0:
                put(L, fr, f"{inb:,} en bodega".replace(",", "."), (cx + cw, cy), BLUE, anchor="topright")
            else:
                rt = f"{real:,}".replace(",", ".")
                put(L, fr, rt, (cx + cw, cy), col, anchor="topright")
                if inb:
                    put(L, fr, f"+{inb:,}".replace(",", "."), (cx + cw - tw_(fr, rt) - 10, cy), BLUE, anchor="topright")
        foot = f"pág {pg + 1}/{pages} · " if pages > 1 else ""
        put(L, fp, foot + "verde = se vende aquí · azul = en tu bodega · naranja = falta", (x0, pie), DIM, x1 - x0)
    elif f == "aqui":
        vis = [t for t in rows if t[5] > 0 and _hh(here, t[0], t[1]) is not None]
        src = COLHS.get("src")
        stn = (COLHS.get("st") or "ESTA ESTACIÓN").upper()
        lab = f"EN {stn}" + (" · datos del juego" if src == "juego" else
                             " · según EDSM" + (f", hace {_lz_hace(now - COLHS['mt'])}" if COLHS.get("mt") else "") +
                             " · abre el mercado para ver precios exactos" if src == "EDSM" else "")
        put(L, fp, lab, (x0, y), DIM if src != "EDSM" else BLUE, x1 - x0); y += fp.get_height() + (8 if grande else 3)
        if not src:
            put(L, fs, "atraca y abre el mercado para ver qué se vende aquí", (area.centerx, (y + pie) // 2), DIM, x1 - x0, anchor="center")
        elif not vis:
            put(L, fn_, "aquí no se vende nada de lo que falta", (area.centerx, (y + pie) // 2), RED, x1 - x0, anchor="center")
        fr = F["btn"] if grande else F["small"]
        rh = fr.get_height() + (10 if grande else 3)
        w = x1 - x0
        for name, key, req, prov, inb, real in vis[:max(1, (pie - y) // rh)]:
            r_ = _hh(here, name, key)
            put(L, fr, name, (x0, y), GREEN, int(w * 0.36))
            put(L, fr, f"hay {r_[1]:,} t · {r_[2]:,} cr".replace(",", "."), (x0 + int(w * 0.38), y), WHITE, int(w * 0.38))
            put(L, fr, f"faltan {real:,} t".replace(",", "."), (x1, y), ORANGE, anchor="topright")
            y += rh
    else:
        st = S.get("status") or ""
        info = (f"{S.get('sys')}: " if S.get("sys") else "") + (
            f"{S.get('n', 0)} mercados en EDSM · consultado hace {_lz_hace(now - (S.get('t') or now))}" if st == "ok" else
            st or "entra en un sistema con la construcción sin terminar")
        put(L, fp, info, (x0, y), DIM, x1 - x0); y += fp.get_height() + (8 if grande else 3)
        if st == "ok" and not hit:
            put(L, fn_, "en este sistema no se vende nada de lo que falta", (area.centerx, (y + pie) // 2), RED, x1 - x0, anchor="center")
        f1 = F["btn"] if grande else F["small"]
        f2 = fs if grande else ft
        rh = f1.get_height() + f2.get_height() + (20 if grande else 6)
        per = max(1, (pie - y) // rh)
        pages = max(1, (len(hit) + per - 1) // per)
        pg = ui.get("colpg", 0) % pages
        for name, key, req, prov, inb, real in hit[pg * per:(pg + 1) * per]:
            o = next((q for q in off[key] if not q[5] or now - q[5] < 30 * 86400), off[key][0])
            stn, stock, price, dist, pad, mt, fc = o[0], o[1], o[2], o[3], o[4], o[5], o[6]
            fr_ = pygame.Rect(x0 - 6, y - 4, x1 - x0 + 12, rh - 6)
            pygame.draw.rect(L, (30, 18, 0), fr_, border_radius=6)
            ftx = f"faltan {real:,} t".replace(",", ".")
            put(L, f1, name, (x0, y), GREEN, x1 - x0 - tw_(f1, ftx) - 20)
            put(L, f1, ftx, (x1, y), ORANGE, anchor="topright")
            line = (f"> {stn}" + (" (PORTANAVES)" if fc else "") + f" · {stock:,} t · {price:,} cr · {dist:,} ls · pad {pad}".replace(",", ".")
                    + (f" · hace {_lz_hace(now - mt)}" if mt else ""))
            old_ = bool(mt) and now - mt > 30 * 86400
            put(L, f2, line + (" · DATO ANTIGUO" if old_ else ""), (x0 + 14, y + f1.get_height() + 4), DIM if old_ else WHITE, x1 - x0 - 14)
            lz_hit(fr_, "colir", stn)
            y += rh
        put(L, fp, (f"pág {pg + 1}/{pages} · " if pages > 1 else "") + "toca una fila: copia la estación al portapapeles del PC · abajo: página",
            (x0, pie), DIM, x1 - x0)

# ---------------------------------------------------------------------------------------------------------------
# 170 NAVE
# ---------------------------------------------------------------------------------------------------------------
LZ_SHIP_PER = 12

def lv_ship(L, area, d, flags, now):
    N = (d or {}).get("naves") or {}
    c = N.get("cur")
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    if not c:
        return lz_vacio(L, area, "Sin datos de la nave", "llegan al cargar la partida o al equiparla (sender v0.88)")
    lz_hit(area, "old", W // 2, TOP + 60)                  # tocar: página siguiente
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 4
    pw, ph = (330, 186) if grande else (180, 100)
    ph_ = ship_photo(L, c, d or {}, pygame.Rect(x1 - pw, y, pw, ph))
    xr = (x1 - pw - 20) if ph_ else x1
    put(L, F["big"], (c.get("ship") or "?").upper(), (x0, y), ORANGE, xr - x0)
    y += hg + 2
    put(L, F["small"], " · ".join(x for x in (c.get("name"), c.get("ident")) if x), (x0, y), DIM, xr - x0)
    y += hs + (16 if grande else 6)
    stats = [("SALTO", f"{c['jump']:.1f} al" if c.get("jump") else "-"), ("COMB.", f"{c.get('fuel') or 0:g} t"),
             ("CARGA", f"{c.get('cargo') or 0} t"), ("MASA", f"{c.get('mass') or 0:.0f} t"), ("VALOR", f"{crx(c.get('value') or 0)}")]
    stats = [s for s in stats if s[0] != "VALOR" or c.get("value")]
    cw = (xr - x0) // len(stats)
    fv = F["btn"]
    for i, (k, v) in enumerate(stats):
        put(L, F["small"] if grande else F["tiny"], k, (x0 + i * cw, y), DIM)
        put(L, fv, v.replace(".", ","), (x0 + i * cw, y + (hs if grande else F["tiny"].get_height()) + 2), WHITE, cw - 8)
    y += (hs if grande else F["tiny"].get_height()) + fv.get_height() + (14 if grande else 6)
    y = max(y, area.y + ph + 12) if ph_ else y
    fb = c.get("fbay")
    if fb:
        crew = (((d or {}).get("ops") or {}).get("crew") or {})
        fs_ = (N.get("veh") or {}).get("fighter") or "-"
        put(L, F["small"] if grande else F["tiny"], f"HANGAR DE CAZAS · caza {fs_}" + (f" · piloto {crew.get('name')}" if crew.get("name") else ""),
            (x0, y), BLUE, x1 - x0); y += (hs if grande else F["tiny"].get_height()) + (10 if grande else 4)
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8 if grande else 4
    mods = sorted(c.get("mods") or [], key=lambda m: m["h"] >= 80)          # dañados arriba
    pie = area.bottom - hs - 6
    fm = F["btn"] if grande else F["small"]
    fe = F["small"] if grande else F["tiny"]
    rh = fm.get_height() + (12 if grande else 3)
    filas = max(1, (pie - y) // rh)
    cols = 2 if len(mods) > filas else 1
    per = filas * cols
    pages = max(1, (len(mods) + per - 1) // per)
    pg = ui.get("shippage", 0) % pages
    gap = 30
    cwm = (x1 - x0 - (gap if cols > 1 else 0)) // cols
    vis = mods[pg * per:(pg + 1) * per]
    nf = -(-len(vis) // cols)
    for k, m in enumerate(vis):
        cx, cy = x0 + (k // nf) * (cwm + gap), y + (k % nf) * rh
        hp = f"{m['h']}%"
        put(L, fe, m.get("s") or "", (cx, cy + (fm.get_height() - fe.get_height()) // 2), DIM)
        xs = cx + tw_(fe, "6A") + 14
        wmax = cx + cwm - tw_(fm, "100%") - 14 - xs
        w_ = put(L, fm, m["n"], (xs, cy), RED if m["h"] < 80 else ORANGE, wmax)
        if m.get("e") and w_ + 20 < wmax:
            put(L, fe, m["e"], (xs + w_ + 12, cy + (fm.get_height() - fe.get_height()) // 2), BLUE, wmax - w_ - 12)
        put(L, fm, hp, (cx + cwm, cy), _mod_col(m["h"]), anchor="topright")
    put(L, F["small"], f"pág {pg + 1}/{pages}  ·  toca para pasar" if pages > 1 else f"{len(mods)} módulos",
        (x1, pie + 2), DIM, anchor="topright")

# ---------------------------------------------------------------------------------------------------------------
# 171 FLOTA
# ---------------------------------------------------------------------------------------------------------------
def lv_fleet(L, area, d, flags, now):
    N = (d or {}).get("naves") or {}
    hs, hb, hg = lz_alturas()
    grande = area.h > 400
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 4
    fs = F["small"] if grande else F["tiny"]
    for xf in N.get("xfer") or []:
        left = max(0, int(xf.get("arrive", now) - time.time()))
        t_ = f"EN CAMINO: {xf.get('ship', '?')} > {xf.get('to') or '?'}  ·  quedan " + \
             (f"{left // 3600} h {left % 3600 // 60} min" if left >= 3600 else f"{left // 60} min {left % 60} s")
        put(L, fs, t_, (x0, y), BLUE, x1 - x0); y += fs.get_height() + 6
    fl = N.get("fleet") or []
    if not fl:
        return lz_vacio(L, pygame.Rect(area.x, y, area.w, area.bottom - y), "Abre el astillero en una estación",
                        "y el panel guardará dónde están tus naves")
    lz_hit(area, "old", W // 2, TOP + 60)                  # tocar: página siguiente
    t = N.get("fleet_t")
    put(L, fs, f"{len(fl)} naves guardadas" + (f" · astillero del {time.strftime('%d/%m %H:%M', time.localtime(t))}" if t else ""),
        (x0, y), DIM, x1 - x0 - 380)
    fb = F["btn"] if grande else F["small"]
    cwn = tw_(fb, "000") + (40 if grande else 20)
    for j, lab in enumerate(("ARMAS", "CARGA", "SALTO")):
        put(L, fs, lab, (x1 - j * cwn, y), DIM, anchor="topright")
    y += fs.get_height() + 6
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8 if grande else 4
    pie = area.bottom - hs - 6
    pw, ph = (150, 84) if grande else (76, 42)
    rh = max(ph, fb.get_height() + fs.get_height() + 6) + (16 if grande else 6)
    per = max(1, (pie - y) // rh)
    pages = max(1, (len(fl) + per - 1) // per)
    pg = ui.get("shippage", 0) % pages
    fl = sorted(fl, key=lambda f: (not f.get("here"), f.get("transit", False), f.get("sys") or ""))
    for f in fl[pg * per:(pg + 1) * per]:
        nm = f.get("name") or ""
        if f.get("here"):
            pygame.draw.rect(L, (0, 30, 10), (x0 - 6, y - 4, x1 - x0 + 12, rh - 6), border_radius=6)
        ph_ = ship_photo(L, f, d or {}, pygame.Rect(x0, y, pw, ph))
        xt = x0 + pw + 16 if ph_ else x0
        xc = x1 - 3 * cwn
        put(L, fb, (f.get("ship") or "?") + (f" «{nm}»" if nm and nm != f.get("ship") else ""), (xt, y), ORANGE, xc - xt - 10)
        sub = "AQUÍ" if f.get("here") else ("en tránsito" if f.get("transit") else f.get("sys") or "?")
        if not f.get("here") and f.get("xtime"):
            sec = int(f["xtime"])
            sub += f"  ·  traer: {sec // 3600} h {sec % 3600 // 60} min · {crx(f.get('xprice') or 0)} cr"
        put(L, fs, sub, (xt, y + fb.get_height() + 4), GREEN if f.get("here") else DIM, x1 - xt)
        vals = [f"{f['jump']:.0f}" if f.get("jump") else "-", f"{f['cargo']}" if f.get("cargo") is not None else "-",
                f"{f['weapons']}" if f.get("weapons") is not None else "-"]
        for j, v in enumerate(reversed(vals)):
            put(L, fb, v, (x1 - j * cwn, y), WHITE, anchor="topright")
        y += rh
    lz_pagina(L, area, pg, pages, pie + 2)

# ---------------------------------------------------------------------------------------------------------------
# registro y CABINA en el cuadro 4 del tablero (como big_cell de la v1.1.17)
# ---------------------------------------------------------------------------------------------------------------
_big_cell_v20b10 = big_cell

def big_cell(S, cell, v, d, flags, now, r, font, how, extra=""):
    if v != 217 and 217 in LZ_CELDA and lienzo_on() and LZ.get("lleno") == "tablero":
        try:
            if pax_list(d) and ev_on("paxcabina") and not COLBIG.get("on"):
                bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
                ch = (bh - 44) // 2
                if r.x >= bw // 2 - 2 and r.y >= 44 + ch - 2:   # cuadro 4 (abajo a la derecha)
                    if now - BCM["t"] > 1:
                        BCM["t"], BCM["mode"] = now, big_mode(d, flags)
                    if BCM["mode"] not in ("COMBATE", "COMBATE A PIE", "ATRAQUE"):
                        v = 217
        except Exception as e:
            log_exc("cabina en el cuadro 4", e)
    return _big_cell_v20b10(S, cell, v, d, flags, now, r, font, how, extra)

# ---------------------------------------------------------------------------------------------------------------
# arreglo (desde la v2.0b5): las pestañas de la barra del MENÚ nuevo medían sus botones viejos con las letras del
# lienzo, así que a partir de la segunda pestaña el toque caía fuera (p. ej. FLOTA, MERCADO, MATERIALES...).
# Ahora el botón viejo se mide con las letras de 480x320, igual que al tocar.
# ---------------------------------------------------------------------------------------------------------------
_TAB480 = {}
_tab_rects_v20b10 = tab_rects

def tab_rects(v):
    if not LZ.get("tab480"):
        return _tab_rects_v20b10(v)
    if "f" not in _TAB480:
        _TAB480["f"] = pygame.font.Font(None, 18)            # F["small"] de load_fonts
    f0 = F.get("small")
    F["small"] = _TAB480["f"]
    try:
        return _tab_rects_v20b10(v)
    finally:
        F["small"] = f0

_lz_panel_barra_v20b10 = lz_panel_barra

def lz_panel_barra(L, v, d, flags, now, online):
    LZ["tab480"] = True
    try:
        return _lz_panel_barra_v20b10(L, v, d, flags, now, online)
    finally:
        LZ["tab480"] = False

_LZ_B10 = {4: lv_carga, 210: lv_pax, 217: lv_cabina, 125: lv_mats, 126: lv_carrier, 135: lv_colonia, 170: lv_ship, 171: lv_fleet}
LZ_PANEL.update(_LZ_B10)
for _v, _fn in _LZ_B10.items():
    LZ_CELDA[_v] = (lambda fn: (lambda L, d, flags, now: fn(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now)))(_fn)
