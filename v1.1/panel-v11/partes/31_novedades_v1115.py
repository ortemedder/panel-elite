# Panel Elite v1.1 · parte 31: novedades v1.1.15
#   MERCADO PARA TU COLONIA en grande: atracado en una estación que vende lo que le falta a tu construcción,
#   en la HDMI (4 CUADROS) los cuadros 3 y 4 se juntan en uno ancho con la lista en letra grande, dibujada a la
#   resolución real. Un toque vuelve a los 4 cuadros (hasta la siguiente estación). Se quita en CAMBIO AUTO.
#   TEMPERATURA NORMAL: aviso verde al acabar el sobrecalentamiento, con número; mensaje en ALERTAS y pitido en
#   SONIDO por separado.
#   (en la parte 25: FSD LISTO con su número en el aviso)
AUTO_LIST.append(("colbig", "MERCADO: LISTA GRANDE PARA TU COLONIA (HDMI)"))
EV_LIST.append(("tempok", "TEMPERATURA NORMAL"))

def aviso_num(k, titulo, sub, col, secs, sonido="ok"):
    """Aviso con su número (#NN): el mensaje se quita en ALERTAS y el pitido en SONIDO, cada uno por su lado."""
    if ev_on(k):
        k0 = XA_K[0]
        try:
            XA_K[0] = k
            set_alert(titulo, sub, col, secs)
        finally:
            XA_K[0] = k0
    if snd_on(k):
        play(sonido)                                      # sin XA_K: quitar el mensaje no quita el pitido

# ---------------------------------------------------------------------------------------------------------------
# TEMPERATURA NORMAL (bit 20 de Flags: sobrecalentamiento)
# ---------------------------------------------------------------------------------------------------------------
HEAT = {"on": None}

def heat_watch(d):
    fl = d.get("Flags", 0)
    on = bool(fl & (1 << 20))
    if HEAT["on"] and not on and not fl & 1:              # se acaba de enfriar (y no estás atracado)
        aviso_num("tempok", "TEMPERATURA NORMAL", "la nave se ha enfriado", GREEN, 3)
    HEAT["on"] = on

# ---------------------------------------------------------------------------------------------------------------
# MERCADO PARA TU COLONIA en la HDMI
# ---------------------------------------------------------------------------------------------------------------
COLBIG = {"on": False, "off": None, "r": None, "grid": False}

def col_big_rows(d, now):
    """[(material, existencias, precio, lo que falta de verdad)] que vende la estación donde estás atracado."""
    d = d or {}
    if not d.get("Flags", 0) & 1:
        return []
    m_ = market_pick(d, now)
    if m_.get("missing") or m_.get("src") == "EDSM" or m_.get("other"):
        return []
    C, L, i = col_pick(d)
    if not L:
        return []
    real = {t[0].lower(): t[5] for t in col_rows(d, L[i])}
    out = []
    for r_ in (d.get("market") or {}).get("col") or []:
        falta = real.get((r_[0] or "").lower(), 0)
        if falta > 0:
            out.append((r_[0], r_[1], r_[2], falta))
    return out

def _col_key(d):
    st = (d or {}).get("station") or {}
    return (st.get("name"), st.get("mid"))

def col_big_on(d, now):
    if cfg.get("bigmode", "4") != "4" or hdmi_panel() or not auto_on("colbig") or (d or {}).get("menu"):
        return False
    if COLBIG["off"] is not None and COLBIG["off"] == _col_key(d):
        return False                                      # lo has quitado tocando: hasta la siguiente estación
    try:
        return bool(col_big_rows(d, now))
    except Exception:
        return False

def _cb_font(n):
    k = ("cbf", n)
    if k not in BIG:
        BIG[k] = pygame.font.Font(None, n)
    return BIG[k]

def draw_col_big(S, d, now):
    bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
    hh = 44
    ch = (bh - hh) // 2
    r = pygame.Rect(0, hh + ch, bw, bh - hh - ch)
    COLBIG["r"] = r
    pygame.draw.rect(S, BLACK, r)
    pygame.draw.rect(S, (0, 24, 8), r.inflate(-8, -8), border_radius=8)
    pygame.draw.rect(S, GREEN, r.inflate(-8, -8), 2, border_radius=8)
    rows = col_big_rows(d, now)
    ft, fr, fh = _cb_font(34), _cb_font(32), _cb_font(22)
    x0 = r.x + 20
    y = r.y + 12
    S.blit(ft.render("PARA TU COLONIA · SE VENDE AQUÍ", True, GREEN), (x0, y))
    tip = fh.render("toca para volver a los 4 cuadros", True, DIM)
    S.blit(tip, (r.right - 20 - tip.get_width(), y + 8))
    y += 36
    cols = (x0, x0 + int(r.w * 0.46), x0 + int(r.w * 0.64), x0 + int(r.w * 0.80))
    for x, t in zip(cols, ("MATERIAL", "FALTA", "PRECIO", "EXISTENCIAS")):
        S.blit(fh.render(t, True, DIM), (x, y))
    y += 22
    pygame.draw.line(S, (0, 90, 30), (x0, y), (r.right - 20, y), 1)
    y += 4
    lh = 31
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

# los cuadros 3 y 4 no se dibujan mientras está la lista (no gastan CPU ni reciben toques)
_big_cell_v1115 = big_cell

def big_cell(S, cell, v, d, flags, now, r, font, how, extra=""):
    if COLBIG["on"]:
        ch = ((BIG.get("h") or 600) - 44) // 2
        if r.y == 44 and r.h == ch:
            COLBIG["grid"] = True                         # se están dibujando los 4 cuadros
        if r.y >= 44 + ch:
            return None
    return _big_cell_v1115(S, cell, v, d, flags, now, r, font, how, extra)

_render_big_v1115 = render_big

def render_big():
    try:
        with lock:
            d = state["data"]
        now = time.time()
        if COLBIG["off"] is not None and COLBIG["off"] != _col_key(d):
            COLBIG["off"] = None                          # otra estación: vuelve a salir
        COLBIG["on"] = bool(d) and BIG.get("surf") is not None and col_big_on(d, now)
    except Exception as e:
        COLBIG["on"] = False
        log_exc("colonia en grande", e)
    COLBIG["grid"] = False
    r_ = _render_big_v1115()
    if COLBIG["on"] and COLBIG["grid"]:                   # solo encima de los 4 cuadros de verdad
        try:
            S = BIG.get("surf")
            if S is not None and not hdmi_panel():
                draw_col_big(S, d, now)
        except Exception as e:
            log_exc("colonia en grande (dibujo)", e)
    else:
        COLBIG["r"] = None
    return r_

_big_tap_v1115 = big_tap

def big_tap(xn, yn):
    r = COLBIG.get("r")
    if COLBIG["on"] and COLBIG["grid"] and r is not None and not hdmi_panel():
        bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
        if r.collidepoint(xn * bw, yn * bh):
            with lock:
                d = state["data"]
            COLBIG["off"] = _col_key(d); COLBIG["on"] = False; COLBIG["r"] = None
            plog("Colonia en grande: quitada hasta la siguiente estación")
            TAP_EV.set()
            return
    return _big_tap_v1115(xn, yn)

_render_v1115 = render

def render(surf):
    r_ = _render_v1115(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d and time.time() - rx < 5:
            heat_watch(d)
    except Exception as e:
        log_exc("temperatura normal", e)
    return r_
