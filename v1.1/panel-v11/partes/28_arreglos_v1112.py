# Panel Elite v1.1 · parte 28: arreglos v1.1.12
#   HDMI 4 CUADROS FIJO: tocar un cuadro solo usa sus botones (no pasa a PANEL); el PANEL abierto a mano
#                        (TAB, clic derecho, pulsación larga) vuelve solo a 4 CUADROS a los 20 s sin tocar nada.
#   ALTÍMETRO: escala que deja ver el suelo hasta los 600 m (alt_span, la usa draw_alt_base de la parte 25).
#   Interdicción: no sale la PARADA DE EMERGENCIA (el sender la ve como salida sin destino).

# ---------------------------------------------------------------------------------------------------------------
# ALTÍMETRO: escala según la altura (el suelo queda en la mitad de abajo de la cinta hasta los 600 m)
# ---------------------------------------------------------------------------------------------------------------
def alt_span(alt):
    if alt <= 600:
        for s_ in (60, 150, 300, 600, 1200, 1500):
            if alt <= s_ * 0.4:
                return s_
        return 1500
    return 6000 if alt < 30000 else 60000


# ---------------------------------------------------------------------------------------------------------------
# HDMI 4 CUADROS FIJO
# ---------------------------------------------------------------------------------------------------------------
def _es_pi3():
    try:
        return "Pi 3" in open("/proc/device-tree/model").read()
    except OSError:
        return False

HDMIF = {"pi3": _es_pi3(), "t": time.time()}

def hdmi_fijo():
    """De fábrica: FIJO en la Pi 4 (Ortem); en la Pi 3 (KORZO, solo HDMI) normal."""
    return bool(cfg.get("hdmifijo", not HDMIF["pi3"]))

def hdmi_ciclo():
    """Botón de OPCIONES: PANEL > 4 CUADROS > 4 CUADROS FIJO > PANEL."""
    if hdmi_panel():
        cfg["hdmi"] = "tablero"; cfg["hdmifijo"] = False
    elif not hdmi_fijo():
        cfg["hdmifijo"] = True
    else:
        cfg["hdmi"] = "panel"
    HDMIF["t"] = time.time()
    save_cfg(); TAP_EV.set()
    plog("HDMI: " + ("PANEL" if hdmi_panel() else "4 CUADROS FIJO" if hdmi_fijo() else "4 CUADROS"))

_on_tap_v1112 = on_tap

def on_tap(x, y):
    HDMIF["t"] = time.time()
    if ui.get("view") == 1244 and grid(10, 4, 3).collidepoint(x, y):
        tap_flash((124, 10)); hdmi_ciclo(); return
    return _on_tap_v1112(x, y)

_hdmi_toggle_v1112 = hdmi_toggle

def hdmi_toggle():
    HDMIF["t"] = time.time()
    _hdmi_toggle_v1112()

_view_settings_v1112 = VIEWS[1244]

def view_settings_v1112(surf, d, flags, now):
    _view_settings_v1112(surf, d, flags, now)
    r = grid(10, 4, 3)
    pygame.draw.rect(surf, BLACK, r)
    draw_button(surf, r, "HDMI", "PANEL" if hdmi_panel() else "4 CUADROS FIJO" if hdmi_fijo() else "4 CUADROS",
                F["btn"] if not hdmi_fijo() or hdmi_panel() else F["small"], filled=True,
                lit=flash.get((124, 10), 0) > now)

VIEWS[1244] = view_settings_v1112

_big_tap_v1112 = big_tap

def big_tap(xn, yn):
    HDMIF["t"] = time.time()
    if hdmi_panel() or not hdmi_fijo():
        return _big_tap_v1112(xn, yn)
    # FIJO: solo los botones de dentro de los cuadros; nunca pasa a PANEL
    bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
    X, Y = xn * bw, yn * bh
    with lock:
        d_ = state["data"]
    try:
        if ops_on(d_) and mega_rect(bw, bh).collidepoint(X, Y):
            mega_tap(); return
    except Exception as e:
        log_exc("toque mega", e)
    for v, area, how in BIG.get("cellmap") or []:
        if not area.collidepoint(X, Y) or v not in VIEWS:
            continue
        px, py = cell_point(area, how, X, Y)
        if not (0 <= px < W and TOP <= py < H):
            break
        v0 = ui["view"]
        ui["view"] = v
        try:
            _on_tap_v1112(int(px), int(py))
        finally:
            ui["view"] = v0
        TAP_EV.set()
        break

def hdmi_vuelta(now):
    """PANEL abierto a mano con FIJO: a los 20 s sin tocar nada vuelve a 4 CUADROS."""
    if not hdmi_fijo() or not hdmi_panel() or BIG.get("fb") is None:
        return
    if now - max(HDMIF["t"], mouse.get("t") or 0) > 20:
        cfg["hdmi"] = "tablero"; save_cfg(); TAP_EV.set()
        plog("HDMI FIJO: 20 s sin tocar, vuelve a 4 CUADROS")


# ---------------------------------------------------------------------------------------------------------------
# INTERDICCIÓN: sin PARADA DE EMERGENCIA
# ---------------------------------------------------------------------------------------------------------------
INTD = {"t": 0.0}
_handle_note_v1112 = handle_note

def handle_note(kind, text):
    if kind == "interdicted":
        INTD["t"] = time.time()
    elif kind == "emergstop" and time.time() - INTD["t"] < 30:
        plog(f"Parada de emergencia ignorada: es una interdicción ({text})")
        return
    return _handle_note_v1112(kind, text)


_render_big_v1112 = render_big

def render_big():
    try:
        hdmi_vuelta(time.time())
    except Exception as e:
        log_exc("HDMI fijo", e)
    return _render_big_v1112()
