# Panel Elite v2.0 · parte 40: v2.0b3 — TABLERO y AVISOS de la HDMI en el lienzo de 1280x800 (con PANTALLA v2)
#   - TABLERO: barra de arriba nueva (botón MENÚ a la vista, sistema, situación, combustible, fecha y hora) y el reparto
#     de los cuadros (4 CUADROS, MIXTO, GRANDE, COMBATE A PIE, ATRAQUE) calculado en el lienzo. Los cuadros siguen
#     dibujando cada pantalla nítida (NITIDEZ ALTA) hasta que les toque su beta.
#   - AVISOS a pantalla entera (aviso rojo/naranja, salto, y los avisos grandes «xa») dibujados a 1280x800.
#   - ATRAQUE (un solo cuadro) ya nítido y con sus botones.
#   - La lista PARA TU COLONIA (colonia en grande) se coloca en la mitad de abajo del tablero nuevo.

LZ_CABH = 96                                         # alto de la barra de arriba del tablero
_LZF = {}

def lz_real(r):
    """Rectángulo del lienzo -> rectángulo real de la HDMI."""
    s, ox, oy = lienzo_escala()
    r = pygame.Rect(r)
    return pygame.Rect(round(ox + r.x * s), round(oy + r.y * s), round(r.w * s), round(r.h * s))

def lz_fuente(n):
    """Letra «de verdad» (sin FontProxy) para los rótulos de los cuadros, a la escala de la HDMI."""
    s, _, _ = lienzo_escala()
    k = max(8, int(n * s))
    if k not in _LZF:
        _LZF[k] = pygame.font.Font(None, k)
    return _LZF[k]

# ---------------------------------------------------------------------------------------------------------------
# barra de arriba del tablero
# ---------------------------------------------------------------------------------------------------------------
def lz_tab_cabecera(L, d, flags, now, mode):
    LZ["hits"] = []
    lz_boton(L, (14, 12, 170, 70), "MENÚ", col=ORANGE, accion=("menu",), font=F["btn"])
    x0 = 206
    # v2.0b5b: el nombre entero (letra más pequeña si no cabe) y el combustible en la primera línea, a la derecha de su
    # barra; la segunda línea queda para la situación y el CONSUMO (CPU, MHz, temperatura, RAM, FPS)
    put_fit(L, ("big", "btn", "small"), (d.get("system") or "---").upper(), (x0, 8), ORANGE, 480)
    put(L, F["tiny"], mode, (x0, 62), GREEN, 480)
    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
    if flags & (1 << 26):
        fuel, cap = (d.get("Fuel") or {}).get("FuelReservoir"), None
    if fuel is not None:
        bx = pygame.Rect(700, 16, 190, 26)
        pygame.draw.rect(L, DIM, bx, 2, border_radius=4)
        if cap:
            pct = max(0.0, min(1.0, fuel / cap))
            pygame.draw.rect(L, RED if pct < 0.25 else ORANGE, (bx.x + 4, bx.y + 4, int((bx.w - 8) * pct), bx.h - 8))
        put(L, F["tiny"], f"FUEL {fuel:.1f} t", (bx.right + 12, 15), ORANGE, 170)
    put(L, F["big"], time.strftime("%H:%M"), (LW - 20, 8), ORANGE, anchor="topright")
    put(L, F["tiny"], game_date().upper(), (LW - 20, 60), BLUE, anchor="topright")
    pygame.draw.line(L, DIM, (0, LZ_CABH - 4), (LW, LZ_CABH - 4), 2)

# ---------------------------------------------------------------------------------------------------------------
# qué cuadros tocan (mismas reglas que render_big_base)
# ---------------------------------------------------------------------------------------------------------------
def lz_celdas(d, flags, now, mode):
    cells = list(BIG_SETS[mode])
    if mode == "COMBATE" and fighter_out(d) and 6 in cells:
        cells[cells.index(6)] = 191
    if 74 in cells and not ((d.get("rings") or {}).get("rings") or (d.get("rings") or {}).get("signals")):
        cells[cells.index(74)] = 128
    if 127 in cells and not mkt_show(d):
        cells[cells.index(127)] = 11
    if pax_list(d):
        if mode == "ATRACADO" and 4 in cells:
            cells[cells.index(4)] = 210
        elif mode == "VIAJE" and 190 in cells:
            cells[cells.index(190)] = 210
    if mode == "ATRACADO" and 4 in cells:
        cells[cells.index(4)] = atr_cell(d, now)
    if mega_dock(d) and 133 in cells:
        cells[cells.index(133)] = 61
    if mode != "COMBATE" and len(cells) >= 3 and 10 not in cells and mining_active(d, now) and not (d.get("Flags2", 0) & 1):
        cells[2] = 10
    if d.get("target") and mode != "COMBATE" and len(cells) >= 3:
        k_ = next((c for c in (71, 72) if c in cells), cells[2])
        cells[cells.index(k_)] = 177
    if mode == "SUPERFICIE" and flags & (1 << 26) and "rhino" in (d.get("srvtype") or "").lower():
        cells = [100, 74, 5, 10]
    return cells

def lz_tablero(S, d, flags, now):
    cell = BIG["cell"]
    mode = big_mode(d, flags)
    if not lienzo_dibuja(S, lz_tab_cabecera, d, flags, now, mode):
        return False
    if cfg.get("perf"):                                       # CONSUMO (AJUSTES > PANTALLA): CPU, RAM... en la barra
        pr = lz_real((700, 64, 10, 10))
        perf_draw(S, pr.x, pr.y)
    cells = lz_celdas(d, flags, now, mode)
    fbig, fsm = lz_fuente(40), lz_fuente(30)
    top, alto = LZ_CABH, LH - LZ_CABH
    LZ["colr"] = None
    if len(cells) == 1:                                       # ATRAQUE: una pantalla entera, nítida y con botones
        v = cells[0]
        area = lz_real((8, top + 6, LW - 16, alto - 12))
        fn = VIEWS.get(v)
        if fn is None or not hi_cell(S, fn, d, flags, now, area, "fit"):
            cell.fill(BLACK)
            try:
                fn and fn(cell, d, flags, now)
            except Exception as e:
                put(cell, F["small"], f"error: {e}"[:60], (8, TOP + 8), RED)
            big_blit(S, cell.subsurface((0, TOP, W, H - TOP)), area)
        BIG["cellmap"] = [(v, area, "fit")]
        BIG["rects"] = [(v, area)]
        return True
    bm = cfg.get("bigmode", "4")
    cw, ch = LW // 2, alto // 2
    if bm == "GRANDE":
        k = int(now // BIG_ROT) % len(cells)
        r = lz_real((0, top, LW, alto))
        big_cell(S, cell, cells[k], d, flags, now, r, fbig, "fit", f"  {k + 1}/{len(cells)}")
        pct = (now % BIG_ROT) / BIG_ROT
        b = lz_real((LW - 300, top + 22, 260, 12))
        pygame.draw.rect(S, DIM, b, 1)
        pygame.draw.rect(S, ORANGE, (b.x + 1, b.y + 1, int((b.w - 2) * pct), b.h - 2))
        return True
    if bm == "MIXTO":
        main = cells[1] if len(cells) > 1 else cells[0]
        rest = [c for c in cells if c != main][:3]
        bwl = LW * 2 // 3
        big_cell(S, cell, main, d, flags, now, lz_real((0, top, bwl, alto)), fbig, "top")
        if rest:
            h3 = alto // len(rest)
            for k, v in enumerate(rest):
                big_cell(S, cell, v, d, flags, now, lz_real((bwl, top + k * h3, LW - bwl, h3)), fsm, "fill")
        return True
    if len(cells) == 3 and cells[2] == 150:
        big_cell(S, cell, cells[0], d, flags, now, lz_real((0, top, cw, ch)), fsm, "fill")
        big_cell(S, cell, cells[1], d, flags, now, lz_real((0, top + ch, cw, ch)), fsm, "fill")
        big_cell(S, cell, 150, d, flags, now, lz_real((cw, top, cw, alto)), fsm, "fill")
        return True
    if len(cells) == 2:
        for i, v in enumerate(cells):
            big_cell(S, cell, v, d, flags, now, lz_real((i * cw, top, cw, alto)), fbig, "fit")
        return True
    if COLBIG.get("on"):                                      # PARA TU COLONIA: abajo, en lugar de los cuadros 3 y 4
        COLBIG["grid"] = True
        LZ["colr"] = lz_real((0, top + ch, LW, alto - ch))
        cells = cells[:2]
    for i, v in enumerate(cells):
        big_cell(S, cell, v, d, flags, now, lz_real(((i % 2) * cw, top + (i // 2) * ch, cw, ch)), fsm, "fill")
    return True

# los cuadros de abajo no se dibujan mientras está la lista de la colonia (big_cell de la parte 31 mira su geometría
# antigua; con el tablero nuevo ya no se le pasan)
_draw_col_big_v20b3 = draw_col_big

def draw_col_big(S, d, now):
    r = LZ.get("colr")
    if not (lienzo_on() and LZ.get("lleno") == "tablero" and r):
        return _draw_col_big_v20b3(S, d, now)
    # mismo dibujo que la parte 31, en el hueco del tablero nuevo
    COLBIG["r"] = r
    pygame.draw.rect(S, BLACK, r)
    pygame.draw.rect(S, (0, 24, 8), r.inflate(-8, -8), border_radius=8)
    pygame.draw.rect(S, GREEN, r.inflate(-8, -8), 2, border_radius=8)
    rows = col_big_rows(d, now)
    s, _, _ = lienzo_escala()
    ft, fr, fh = _cb_font(int(34 * s)), _cb_font(int(32 * s)), _cb_font(int(22 * s))
    x0 = r.x + 20
    y = r.y + 12
    S.blit(ft.render("PARA TU COLONIA · SE VENDE AQUÍ", True, GREEN), (x0, y))
    tip = fh.render("toca para volver a los 4 cuadros", True, DIM)
    S.blit(tip, (r.right - 20 - tip.get_width(), y + 8))
    y += int(36 * s)
    cols = (x0, x0 + int(r.w * 0.46), x0 + int(r.w * 0.64), x0 + int(r.w * 0.80))
    for x, t in zip(cols, ("MATERIAL", "FALTA", "PRECIO", "EXISTENCIAS")):
        S.blit(fh.render(t, True, DIM), (x, y))
    y += int(22 * s)
    pygame.draw.line(S, (0, 90, 30), (x0, y), (r.right - 20, y), 1)
    y += 4
    lh = int(31 * s)
    caben = max(1, (r.bottom - 14 - y) // lh)
    if len(rows) > caben:
        caben -= 1
    for name, stock, price, falta in rows[:caben]:
        fit_w = cols[1] - cols[0] - 12
        nm = name
        while nm and fr.size(nm)[0] > fit_w:
            nm = nm[:-1]
        if nm != name:
            nm = nm[:-2] + "..."
        S.blit(fr.render(nm, True, GREEN), (cols[0], y))
        S.blit(fr.render(f"{falta:,} t".replace(",", "."), True, ORANGE), (cols[1], y))
        S.blit(fr.render(f"{price:,} cr".replace(",", "."), True, WHITE), (cols[2], y))
        S.blit(fr.render(f"{stock:,} t".replace(",", "."), True, WHITE if stock >= falta else ORANGE), (cols[3], y))
        y += lh
    if len(rows) > caben:
        S.blit(fh.render(f"+{len(rows) - caben} más en COLONIZACIÓN", True, DIM), (cols[0], y + 4))

# ---------------------------------------------------------------------------------------------------------------
# AVISOS a pantalla entera
# ---------------------------------------------------------------------------------------------------------------
def lz_lineas_centro(L, text, cx, y, col, maxw, maxlines):
    for f_, lh in ((F["btn"], 58), (F["small"], 44)):
        ls = wrap_lines(f_, str(text), maxw)
        if len(ls) <= maxlines or f_ is F["small"]:
            for t in ls[:maxlines]:
                put(L, f_, t, (cx, y), col, maxw, anchor="midtop")
                y += lh
            return lh * min(len(ls), maxlines)

def lz_marco(L, col, on):
    for k in range(4 if on else 2):
        pygame.draw.rect(L, col, (k * 8, k * 8, LW - k * 16, LH - k * 16), 4)

def lz_num(L, box, k):
    n = ev_num(k) if k else None
    if not n:
        return
    lab = f"#{n}"
    r = pygame.Rect(box.right - tw_(F["tiny"], lab) - 36, box.y + 12, tw_(F["tiny"], lab) + 20, 40)
    pygame.draw.rect(L, BLACK, r, border_radius=6)
    pygame.draw.rect(L, DIM, r, 2, border_radius=6)
    put(L, F["tiny"], lab, r.center, DIM, anchor="center")

def lz_aviso(L, now):
    LZ["hits"] = []
    a = ui["alert"]
    col = a["col"]
    on = int(now * 3) % 2 == 0 or a["kind"] != "red"
    L.fill(BLACK)
    lz_marco(L, col, on)
    box = pygame.Rect(80, 250, LW - 160, 300)
    pygame.draw.rect(L, BLACK, box)
    pygame.draw.rect(L, col, box, 6, border_radius=20)
    if a["kind"] == "jump":
        for j in range(14):
            yy = box.y + 20 + ((j * 57 + int(now * 400)) % (box.h - 40))
            pygame.draw.line(L, (40, 70, 130), (box.x + 24, yy), (box.x + 24 + (j * 93) % 300, yy), 2)
            pygame.draw.line(L, (40, 70, 130), (box.right - 24 - (j * 131) % 300, yy), (box.right - 24, yy), 2)
    sub = a.get("sub") or ""
    two_ = bool(sub) and len(wrap_lines(F["btn"], sub, box.w - 60)) > 1
    put_fit(L, ("clock", "num", "big", "btn") if len(a["text"]) <= 16 else ("num", "big", "btn"), a["text"],
            (box.centerx, box.centery - (70 if two_ else 40 if sub else 0)), col if on else WHITE, box.w - 60, anchor="center")
    if sub:
        lz_lineas_centro(L, sub, box.centerx, box.centery + (10 if two_ else 40), WHITE, box.w - 60, 2)
    lz_num(L, box, a.get("ev"))

def lz_xa(L, now):
    LZ["hits"] = []
    a = xa["a"]
    col = a["col"]
    on = int(now * 3) % 2 == 0 or col != RED
    L.fill(BLACK)
    lz_marco(L, col, on)
    box = pygame.Rect(60, 150, LW - 120, 520)
    pygame.draw.rect(L, BLACK, box)
    dim = tuple(int(c) // 3 for c in col[:3])
    for j in range(12):
        yy = box.y + 24 + (j * 43) % (box.h - 48)
        ln = (j * 103 + int(now * 400)) % 260
        pygame.draw.line(L, dim, (box.x + 20, yy), (box.x + 20 + ln, yy), 2)
        pygame.draw.line(L, dim, (box.right - 20 - ln, yy), (box.right - 20, yy), 2)
    pygame.draw.rect(L, col, box, 6, border_radius=20)
    cx, y = box.centerx, box.y + 36
    put_fit(L, ("big", "btn", "small"), a["title"], (cx, y), col if on else WHITE, box.w - 60, anchor="midtop"); y += 84
    put_fit(L, ("clock", "num", "big", "btn"), a["big"], (cx, y), WHITE, box.w - 60, anchor="midtop")
    y += 170 if tw_(F["clock"], a["big"]) <= box.w - 60 else 120
    for ln_ in [l for l in a["lines"] if l][:3]:
        t_, c2 = ln_ if isinstance(ln_, tuple) else (ln_, col)
        y += lz_lineas_centro(L, t_, cx, y, c2, box.w - 60, max(1, (box.bottom - 16 - y) // 58))
    lz_num(L, box, a.get("ev"))

# ---------------------------------------------------------------------------------------------------------------
# enganche en el dibujo de la HDMI
# ---------------------------------------------------------------------------------------------------------------
_render_big_base_v20b3 = render_big_base

def render_big_base():
    S = BIG.get("surf")
    if not lienzo_on() or S is None or hdmi_panel() or ui.get("bye"):
        return _render_big_base_v20b3()
    with lock:
        d, rx = state["data"], state["rx"]
    now = time.time()
    online = d is not None and now - rx < 5
    if now - ui["start"] < 3 or not online:
        return _render_big_base_v20b3()                       # arranque (puente) y espera (v2.0b2)
    flags = d.get("Flags", 0)
    try:
        if ui.get("alert") and now < ui["alert"]["until"]:
            S.fill(BLACK)
            if lienzo_dibuja(S, lz_aviso, now):
                BIG["rects"] = []; BIG["fast"] = True; LZ["lleno"] = "aviso"
                return
        elif xa.get("a") and now < xa["a"]["until"] and not kill_in_cell(xa["a"]):
            S.fill(BLACK)
            if lienzo_dibuja(S, lz_xa, now):
                BIG["rects"] = []; BIG["fast"] = True; LZ["lleno"] = "aviso"
                return
        elif flags & (1 << 11) or now < scoop["full_until"] or d.get("menu"):
            return _render_big_base_v20b3()                   # recogida de combustible (puente) y menú del juego
        else:
            S.fill(BLACK)
            BIG["fast"] = False
            BIG["rects"] = []
            LZ["lleno"] = "tablero"
            if lz_tablero(S, d, flags, now):
                return
    except Exception as e:
        log_exc("tablero v2", e)
    LZ["lleno"] = False
    return _render_big_base_v20b3()

_big_tap_v20b3 = big_tap

def big_tap(xn, yn):
    if not lienzo_on() or hdmi_panel():
        return _big_tap_v20b3(xn, yn)
    ll = LZ.get("lleno")
    if ll == "aviso":
        HDMIF["t"] = time.time()
        now = time.time()
        if ui.get("alert") and now < ui["alert"]["until"]:
            ui["alert"] = None                                # tocar quita el aviso (como en el panel)
        elif xa.get("a") and xa["a"].get("title") in ("SESIÓN TERMINADA", "BATALLA TERMINADA") and now < xa["a"]["until"]:
            xa["a"] = None
        else:
            lienzo_menu()
        TAP_EV.set()
        return
    if ll == "tablero":
        HDMIF["t"] = time.time()
        p = lienzo_punto(xn, yn)
        if p and p[1] < LZ_CABH:                              # barra de arriba (y su botón MENÚ): el MENÚ
            lienzo_menu(); TAP_EV.set(); return
        return _big_tap_v20(xn, yn)                           # los cuadros: como siempre (botones de cada cuadro)
    return _big_tap_v20b3(xn, yn)
