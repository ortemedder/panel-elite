# Panel Elite v1.1 · parte 37: arreglos v1.1.20b — toques en la HDMI
#   1) Pantalla de espera en la HDMI (4 CUADROS / 4 CUADROS FIJO): la espera se dibuja a pantalla completa, pero el
#      toque se repartía con el mapa de los 4 cuadros de antes (ya no visibles). Ahora el toque se pasa a la posición
#      del panel (como en modo PANEL) y va por todos los botones: pestañas CDSN, V 1/2, GALAXIA / COLONIA / SOL...
#      También vale para quitar un aviso grande que tapa toda la HDMI.
#   2) Sin cuadros en pantalla, el mapa viejo de cuadros se olvida (no desvía más toques).
#   3) (en la parte 28) 4 CUADROS FIJO: los toques dentro de los cuadros usan ya todos los botones (v1.1.16 en adelante).

_big_tap_v1120b = big_tap

def _hdmi_pantalla_entera():
    """La HDMI enseña una pantalla entera del panel (espera o aviso) en vez de los 4 cuadros."""
    if hdmi_panel() or BIG.get("rects"):
        return False
    alerta = ui.get("alert") and time.time() < ui["alert"]["until"]
    return bool(ui.get("idle_on") or alerta)

def big_tap(xn, yn):
    if not hdmi_panel() and not BIG.get("rects"):
        BIG["cellmap"] = []                               # sin cuadros a la vista: nada de mapas viejos
    try:
        entera = _hdmi_pantalla_entera()
    except Exception:
        entera = False
    if entera and hdmi_fijo():                            # sin FIJO, tocar la espera abre PANEL, como siempre
        HDMIF["t"] = time.time()
        bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
        sc = min(bw / W, bh / H)
        ox, oy = (bw - W * sc) / 2, (bh - H * sc) / 2      # como big_blit: centrado y a escala
        px, py = (xn * bw - ox) / sc, (yn * bh - oy) / sc
        if 0 <= px < W and 0 <= py < H:
            try:
                on_tap(int(px), int(py))
            except Exception as e:
                log_exc("toque espera HDMI", e)
            TAP_EV.set()
        return
    return _big_tap_v1120b(xn, yn)
