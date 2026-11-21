# Panel Elite v2.0 · parte 42: v2.0b5 — MENÚ y BOTONERAS a 1280x800 (con PANTALLA v2)
#   - El MENÚ de la HDMI (modo PANEL) dibuja a 1280x800 de verdad las pantallas que ya tienen versión nueva (LZ_PANEL):
#     barra de arriba nueva (< MENÚ, título, pestañas, combustible, engranaje) y la pantalla debajo.
#     Las que aún no la tienen se ven como antes (nítidas, 1200x800).
#   - Pantallas nuevas: 0 MENÚ PRINCIPAL (también con ICONOS), 1 MANDOS, 2 PIPS, 5 SRV / RHINO / A PIE, 51 SALUDOS, 9 CAZA.
#     PIPS y SRV / RHINO / A PIE también como cuadros del tablero.
#   - Cada botón nuevo hace exactamente lo mismo que el de antes: el toque se pasa al centro de su botón de 480x320.
#   - Ratón (KORZO): en el MENÚ nuevo la flecha se dibuja a 1280x800 y el clic va al botón que señala.

LZ_TOP = 108                                           # alto de la barra de arriba del MENÚ
LZ_PANEL = {}
LZ.update(phits=[], pv=None)

def lz_grid(area, i, cols, rows, gap=12):
    cw, ch = area.w / cols, area.h / rows
    c, r = i % cols, i // cols
    return pygame.Rect(int(area.x + c * cw + gap / 2), int(area.y + r * ch + gap / 2), int(cw - gap), int(ch - gap))

def lz_boton_v(L, r, txt, sub, font, filled=False, lit=False, dim=False, viejo=None):
    """Botón como draw_button, a la escala del lienzo; viejo = su rectángulo de 480x320 (el toque va a su centro)."""
    r = pygame.Rect(r)
    br = max(6, r.h // 10)
    if filled or lit:
        pygame.draw.rect(L, WHITE if lit else ORANGE, r, border_radius=br)
        col = BLACK
    else:
        pygame.draw.rect(L, DIM if dim else ORANGE, r, 3, border_radius=br)
        col = DIM if dim else ORANGE
    fs = F["small"]
    if sub:
        hb, hs = font.get_height(), fs.get_height()
        y0 = r.centery - (hb + hs + 4) // 2
        put(L, font, txt, (r.centerx, y0 + hb // 2), col, r.w - 14, "center")
        put(L, fs, sub, (r.centerx, y0 + hb + 4 + hs // 2), col, r.w - 14, "center")
    else:
        put(L, font, txt, r.center, col, r.w - 14, "center")
    if viejo is not None:
        lz_hit(r, "old", viejo.centerx, viejo.centery)

def lz_icono_viejo(L, dib, cx, cy, k):
    """Dibuja un icono de 480x320 (dib(surf, cx, cy) en sus unidades) centrado en (cx, cy) del lienzo, k veces mayor."""
    half = 30
    box = pygame.Rect(cx - half * k, cy - half * k, 2 * half * k, 2 * half * k)
    rr = L._r(box).clip(L.real.get_rect())
    if rr.w < 4 or rr.h < 4:
        return
    sub = L.real.subsurface(rr)
    s_ = k * L.sx
    dib(ScaledSurf(sub, s_, s_), half, half)

# ---------------------------------------------------------------------------------------------------------------
# pantallas: botoneras
# ---------------------------------------------------------------------------------------------------------------
def lv_menu(L, area, d, flags, now):
    keep = MENU.get(9)
    MENU[9] = "FACCIÓN"
    try:
        for i in range(12):
            name = MENU.get(i + 1)
            r = lz_grid(area, i, 4, 3)
            lit = flash.get((0, i), 0) > now
            if ICONS_ON[0]:
                lz_boton_v(L, r, "", None, F["small"], lit=lit, dim=name is None, viejo=grid(i))
                col = BLACK if lit else DIM if name is None else ORANGE
                k = r.h / 90
                if i == 8:
                    lz_icono_viejo(L, lambda s, x, y: flag_icon(s, col, x, y), r.centerx, r.y + int(r.h * 0.40), k)
                else:
                    lz_icono_viejo(L, lambda s, x, y, i=i: menu_icon(s, i, col, x, y), r.centerx, r.y + int(r.h * 0.40), k)
                put(L, F["small"], f"{i + 1} {name or 'vacío'}", (r.centerx, r.bottom - 14), col, r.w - 14, anchor="midbottom")
            else:
                lz_boton_v(L, r, str(i + 1), name or "vacío", F["num"], lit=lit, dim=name is None, viejo=grid(i))
    finally:
        MENU[9] = keep

def lv_mandos(L, area, d, flags, now):
    for i, (txt, key, bit) in enumerate(BUTTONS):
        lz_boton_v(L, lz_grid(area, i, 4, 3), txt, key.upper(), F["btn"],
                   filled=bit is not None and bool(flags & (1 << bit)), lit=flash.get((1, i), 0) > now or glow(txt), viejo=grid(i))

def lv_pips(L, area, d, flags, now):
    pips = (d or {}).get("Pips") or [0, 0, 0]
    hp = int(area.h * 0.76)
    arriba = pygame.Rect(area.x, area.y, area.w, hp)
    abajo = pygame.Rect(area.x, area.y + hp, area.w, area.h - hp)
    for i, (name, key) in enumerate(PIP_COLS):
        r = lz_grid(arriba, i, 3, 1)
        lit = flash.get((2, i), 0) > now
        pygame.draw.rect(L, WHITE if lit else ORANGE, r, 3, border_radius=10)
        put(L, F["btn"], name, (r.centerx, r.y + 10), ORANGE, r.w - 10, anchor="midtop")
        val = pips[i] if i < len(pips) else 0
        top = r.y + 10 + F["btn"].get_height() + 8
        bot = r.bottom - F["small"].get_height() - 16
        gap = 8
        bh = max(6, (bot - top - 3 * gap) // 4)
        bw = r.w - 50
        for p in range(4):
            br = pygame.Rect(r.x + 25, bot - (p + 1) * bh - p * gap, bw, bh)
            fill = max(0, min(2, val - p * 2))
            pygame.draw.rect(L, DIM, br, 2)
            if fill:
                pygame.draw.rect(L, BLUE, (br.x + 3, br.y + 3, (br.w - 6) * fill // 2, br.h - 6))
        put(L, F["small"], f"{val / 2:g} / 4   [{key.upper()}]", (r.centerx, r.bottom - 8), ORANGE, r.w - 10, anchor="midbottom")
        lz_hit(r, "old", pip_rect(i).centerx, pip_rect(i).centery)
    for i, (name, ks) in enumerate(PIP_PRESETS):
        lz_boton_v(L, lz_grid(abajo, i, 4, 1), name, ks[0].upper() if len(ks) == 1 else None, F["btn"],
                   lit=flash.get((2, 10 + i), 0) > now, viejo=preset_rect(i))

def lv_srv(L, area, d, flags, now):
    flags2 = (d or {}).get("Flags2", 0)
    in_srv, on_foot = bool(flags & (1 << 26)), bool(flags2 & 1)
    th = F["small"].get_height() + 14
    mid = area.centerx
    for label, cx, act in ((("RHINO" if "rhino" in ((d or {}).get("srvtype") or "").lower() else "SRV"), area.x + area.w // 4, in_srv),
                           ("A PIE", area.x + 3 * area.w // 4, on_foot)):
        put(L, F["small"], label + ("  (ACTIVO)" if act else "") + ("   ·   SALUDOS >" if label == "A PIE" else ""),
            (cx, area.y + th // 2), GREEN if act else (ORANGE if label == "A PIE" else DIM), area.w // 2 - 20, anchor="center")
    lz_hit((mid, area.y, area.w // 2, th), "old", 3 * W // 4, TOP + 9)
    pygame.draw.line(L, DIM, (mid, area.y + 4), (mid, area.bottom - 4), 2)
    zona = pygame.Rect(area.x, area.y + th, area.w, area.h - th)
    for i, (txt, key, bit) in enumerate(SRV_BTNS + PIE_BTNS):
        dim = (i < 6 and on_foot) or (i >= 6 and in_srv)
        idx = i % 2 + (2 if i >= 6 else 0) + 4 * ((i % 6) // 2)
        lz_boton_v(L, lz_grid(zona, idx, 4, 3), txt, key.upper(), F["btn"], dim=dim,
                   filled=bit is not None and in_srv and i < 6 and bool(flags & (1 << bit)),
                   lit=flash.get((5, i), 0) > now or glow(txt), viejo=m5_rect(i))

def lv_saludos(L, area, d, flags, now):
    for i, name in enumerate(EMOTES):
        k = emote_key(i)
        r = lz_grid(area, i, 4, 2)
        lz_boton_v(L, r, name, k or SIN, F["btn"] if tw_(F["btn"], name) < r.w - 20 else F["small"],
                   lit=flash.get((51, i), 0) > now, dim=k is None, viejo=grid(i, 4, 2))

def lv_caza(L, area, d, flags, now):
    f = (d or {}).get("fighter") or {}
    ch = int(area.h * 0.30)
    card = pygame.Rect(area.x + 8, area.y + 4, area.w - 16, ch - 8)
    pygame.draw.rect(L, DIM, card, 2, border_radius=10)
    txt, col = FIGHTER_STATE.get(f.get("state"), ("SIN DATOS DEL CAZA", DIM))
    if flags & (1 << 25):
        txt, col = "PILOTANDO EL CAZA", BLUE
    y = card.y + 8
    put(L, F["small"], "CAZA", (card.x + 16, y), DIM); y += F["small"].get_height() + 2
    put(L, F["big"], txt, (card.x + 16, y), col, card.w - 32); y += F["big"].get_height() + 2
    who = f.get("pilot")
    if who and f.get("state") == "out":
        put(L, F["small"], f"Piloto: {who}", (card.x + 16, y), ORANGE, card.w - 32)
    orders = ui["orders"]
    zona = pygame.Rect(area.x, area.y + ch, area.w, area.h - ch)
    for i, (t_, key, grp) in enumerate(FIGHTER_BTNS):
        lz_boton_v(L, lz_grid(zona, i, 4, 2), t_, key.replace("KP", "NUM "), F["btn"],
                   filled=grp is not None and orders.get(grp) == i, lit=flash.get((9, i), 0) > now, viejo=c9_rect(i))

LZ_PANEL.update({0: lv_menu, 1: lv_mandos, 2: lv_pips, 5: lv_srv, 51: lv_saludos, 9: lv_caza})

# en el tablero: PIPS y SRV / RHINO / A PIE con el diseño nuevo (el toque, con la vista del cuadro)
LZ_CELDA[2] = lambda L, d, flags, now: lv_pips(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now)
LZ_CELDA[5] = lambda L, d, flags, now: lv_srv(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now)

# ---------------------------------------------------------------------------------------------------------------
# barra de arriba del MENÚ
# ---------------------------------------------------------------------------------------------------------------
def lz_panel_barra(L, v, d, flags, now, online):
    rb = pygame.Rect(12, 10, 230, LZ_TOP - 22)
    pygame.draw.rect(L, ORANGE, rb, 3, border_radius=10)
    put(L, F["btn"], "MENÚ" if v == 100 else "< INICIO" if v == 0 else "< MENÚ", rb.center, ORANGE, rb.w - 10, anchor="center")
    lz_hit(rb, "old", BACK.centerx, BACK.centery)
    x0 = rb.right + 20
    title = ("MENÚ PRINCIPAL" if (d or {}).get("menu") else ((d or {}).get("system") or "---").upper()) if online else "SIN DATOS"
    alerta = next((t for b, t in ALERTS if flags & (1 << b)), None) if online else None
    g = tab_group(v)[0]
    if alerta and g:
        put(L, F["big"], alerta, (x0, 4), RED, 640)
    else:
        put(L, F["big"], title, (x0, 4), (GREEN if (d or {}).get("menu") else ORANGE) if online else DIM, 640)
    # engranaje
    gr = pygame.Rect(LW - 110, 8, 96, LZ_TOP - 18)
    on = v in (12, 121, 122, 1244, 1245)
    col = WHITE if flash.get(("gear",), 0) > now else ORANGE
    if on:
        pygame.draw.rect(L, ORANGE, gr, 3, border_radius=10)
    cx, cy = gr.center
    rot = now * 40
    for a in range(8):
        r_ = math.radians(a * 45 + rot)
        pygame.draw.line(L, col, (cx + 24 * math.cos(r_), cy + 24 * math.sin(r_)), (cx + 37 * math.cos(r_), cy + 37 * math.sin(r_)), 12)
    pygame.draw.circle(L, col, (cx, cy), 28)
    pygame.draw.circle(L, BLACK, (cx, cy), 11)
    lz_hit(gr, "old", GEAR.centerx, GEAR.centery)
    if power["now"] and int(now * 2) % 2 == 0:
        draw_bolt(L, gr.x - 44, 30, RED, 2.2)
    fuel = ((d or {}).get("Fuel") or {}).get("FuelMain")
    cap = (d or {}).get("fuelcap")
    if online and fuel is not None:
        pct = max(0.0, min(1.0, fuel / cap)) if cap else None
        bx = pygame.Rect(LW - 400, 14, 260, 26)
        pygame.draw.rect(L, DIM, bx, 2, border_radius=4)
        if pct is not None:
            pygame.draw.rect(L, RED if pct < 0.25 else ORANGE, (bx.x + 4, bx.y + 4, int((bx.w - 8) * pct), bx.h - 8))
        put(L, F["tiny"], f"FUEL {fuel:.1f} t", (bx.x, 48), ORANGE)
    mode = (d or {}).get("mode") if online else None
    if mode and not g:
        put(L, F["tiny"], f"MODO: {mode}", (LW - 400, 76), RED, 260)
    if g:
        x = x0
        for t, name, r_old, act in tab_rects(v):
            w_ = tw_(F["small"], name) + 36
            r = pygame.Rect(x, 62, w_, 40)
            new = t == 130 and galnet["new"]
            c_ = GREEN if new else ORANGE
            if act:
                pygame.draw.rect(L, c_, r, border_radius=8)
                put(L, F["small"], name, r.center, BLACK, anchor="center")
            else:
                pygame.draw.rect(L, c_ if new else DIM, r, 2, border_radius=8)
                put(L, F["small"], name, r.center, c_, anchor="center")
            lz_hit(r.inflate(4, 10), "old", r_old.centerx, r_old.centery)
            x += w_ + 8
    elif alerta:
        put(L, F["small"], alerta, (x0, 66), RED, 620)
    elif v:
        put(L, F["small"], MENU.get(v, f"MENU {v}"), (x0, 66), DIM, 620)
    pygame.draw.line(L, DIM, (0, LZ_TOP - 4), (LW, LZ_TOP - 4), 2)

def lz_flecha(L):
    """Flecha del ratón (KORZO) en el MENÚ nuevo."""
    if time.time() - mouse["t"] > 10:
        return
    x, y = mouse["x"] * LW / W, mouse["y"] * LH / H
    pts = [(x, y), (x, y + 40), (x + 10, y + 30), (x + 20, y + 48), (x + 28, y + 43), (x + 18, y + 27), (x + 30, y + 27)]
    pygame.draw.polygon(L, WHITE, pts)
    pygame.draw.polygon(L, BLACK, pts, 2)

def lz_panel_dibuja(L, v, d, flags, now, online):
    LZ["hits"] = []
    L.fill(BLACK)
    lz_panel_barra(L, v, d, flags, now, online)
    LZ_PANEL[v](L, pygame.Rect(0, LZ_TOP + 4, LW, LH - LZ_TOP - 8), d, flags, now)
    LZ["phits"] = LZ["hits"]
    lz_flecha(L)

_render_big_panel_v20b5 = render_big_panel

def render_big_panel(S):
    LZ["pv"] = None
    v = ui.get("view")
    if not lienzo_on() or v not in LZ_PANEL or ui.get("idle_on") or ui.get("bye"):
        return _render_big_panel_v20b5(S)
    now = time.time()
    if (ui.get("alert") and now < ui["alert"]["until"]) or (xa.get("a") and now < xa["a"]["until"]) \
            or (ui.get("shipcard") and now < ui["shipcard"]):
        return _render_big_panel_v20b5(S)                    # avisos encima del MENÚ: como antes
    with lock:
        d, rx = state["data"], state["rx"]
    online = d is not None and now - rx < 5
    flags = (d or {}).get("Flags", 0) if online else 0
    S.fill(BLACK)
    if not lienzo_dibuja(S, lz_panel_dibuja, v, d if online else None, flags, now, online):
        return _render_big_panel_v20b5(S)
    LZ["pv"] = v
    if cfg.get("perf"):
        perf_side(S)
    return True

# el MENÚ también se redibuja cuando gira el engranaje o se mueve la flecha (big_go compara la pantalla pequeña)
_big_go_base_v20b5 = big_go_base

def big_go_base(surf):
    r = _big_go_base_v20b5(surf)
    if not r and lienzo_on() and hdmi_panel() and LZ.get("pv") is not None and time.time() - BIG.get("plast2", 0) > 0.5:
        BIG["plast2"] = time.time()
        return True
    return r

# ---------------------------------------------------------------------------------------------------------------
# toques: dedo y web (big_tap), ratón (handle_input)
# ---------------------------------------------------------------------------------------------------------------
def lz_panel_toque(X, Y):
    for r, acc in reversed(LZ["phits"]):
        if r.collidepoint(X, Y) and acc[0] == "old":
            on_tap(int(acc[1]), int(acc[2]))
            TAP_EV.set()
            return True
    return False

def lz_celda_old(xn, yn):
    """Toque en un cuadro nuevo del tablero cuyo botón es de los de 480x320: como en 4 CUADROS FIJO."""
    bw, bh = BIG.get("w") or LW, BIG.get("h") or LH
    X, Y = xn * bw, yn * bh
    for v, (sub, k, hits) in list(LZ["cel"].items()):
        if not sub.collidepoint(X, Y):
            continue
        lx, ly = (X - sub.x) / k, (Y - sub.y) / k
        for r, acc in reversed(hits):
            if r.collidepoint(lx, ly) and acc[0] == "old":
                HDMIF["t"] = time.time()
                v0 = ui["view"]
                ui["view"] = v
                try:
                    on_tap(int(acc[1]), int(acc[2]))
                finally:
                    if ui["view"] == v:
                        ui["view"] = v0
                    else:                                    # ha cambiado de pantalla (p. ej. SALUDOS): al MENÚ
                        lienzo_menu()
                TAP_EV.set()
                return True
        return False
    return False

_big_tap_v20b5 = big_tap

def big_tap(xn, yn):
    if lienzo_on():
        if hdmi_panel() and LZ.get("pv") is not None:
            HDMIF["t"] = time.time()
            p = lienzo_punto(xn, yn)
            if p:
                lz_panel_toque(*p)
            return
        if not hdmi_panel() and LZ.get("lleno") == "tablero" and LZ["cel"] and lz_celda_old(xn, yn):
            return
    return _big_tap_v20b5(xn, yn)

_handle_input_v20b5 = handle_input

def handle_input(ev, ec):
    if lienzo_on() and hdmi_panel() and LZ.get("pv") is not None and ev.type == ec.EV_KEY and ev.value == 1 \
            and ev.code == ec.BTN_LEFT:
        mouse["t"] = time.time()
        HDMIF["t"] = time.time()
        lz_panel_toque(mouse["x"] * LW / W, mouse["y"] * LH / H)
        return
    return _handle_input_v20b5(ev, ec)
