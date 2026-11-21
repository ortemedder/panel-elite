# Panel Elite v1.1 · parte 36: novedades v1.1.20 — LATIDO para la OLED
#   Cada 5 s, solo si cambia (y como mucho cada 30 s si no cambia), el panel escribe en la carpeta personal
#   (la de encima de panel-v11, valga el usuario que valga: ortem, elite...) el fichero .panel_latido con
#   una línea:  <epoch último paquete del PC (0 = ninguno)> <epoch ahora> <epoch arranque del panel>
#   oled_stats.py lo lee: panel vivo y más de 2 min sin datos del PC -> LEDs POLICÍA y «SIN DATOS PC».
#   AJUSTES > LATIDO OLED: AUTO (de fábrica: solo si existe ~/oled_stats.py), SÍ o NO.
#   Si está apagado borra el fichero, así la OLED no confunde un latido viejo con un panel colgado.

LATIDO_F = os.path.join(os.path.dirname(PANEL_DIR), ".panel_latido")
LATIDO_OLED = os.path.join(os.path.dirname(PANEL_DIR), "oled_stats.py")
LATIDO = {"t0": time.time(), "rx": None, "w": 0.0, "hay": None, "hay_t": 0.0}

def latido_hay_oled(now=None):
    now = now or time.time()
    if LATIDO["hay"] is None or now - LATIDO["hay_t"] > 300:
        LATIDO["hay"] = os.path.exists(LATIDO_OLED); LATIDO["hay_t"] = now
    return LATIDO["hay"]

def latido_on():
    m = cfg.get("latido", "AUTO")
    return latido_hay_oled() if m == "AUTO" else m == "SÍ"

def latido_loop():
    while True:
        time.sleep(5)
        try:
            now = time.time()
            if not latido_on():
                if LATIDO["w"]:
                    try:
                        os.remove(LATIDO_F)
                    except OSError:
                        pass
                    LATIDO["w"] = 0.0; LATIDO["rx"] = None
                continue
            rx = int(state.get("rx") or 0)
            if rx == LATIDO["rx"] and now - LATIDO["w"] < 30:
                continue
            with open(LATIDO_F + ".tmp", "w") as f:
                f.write(f"{rx} {int(now)} {int(LATIDO['t0'])}\n")
            os.replace(LATIDO_F + ".tmp", LATIDO_F)
            LATIDO["rx"], LATIDO["w"] = rx, now
        except Exception:
            pass                                          # sin permiso o sin disco: nada, ni en el log

threading.Thread(target=latido_loop, daemon=True, name="latido").start()

# ---------------------------------------------------------------------------------------------------------------
# 12 AJUSTES: botón LATIDO OLED (AUTO / SÍ / NO)
# ---------------------------------------------------------------------------------------------------------------
SET12.append(("LATIDO OLED", "latido"))

def _latido_i():
    return next((i for i, it in enumerate(SET12) if it and it[1] == "latido"), None)

_view_sub12_v1120 = view_sub12

def view_sub12(surf, d, flags, now):
    _view_sub12_v1120(surf, d, flags, now)
    i = _latido_i()
    if i is None:
        return
    r = grid(i, 4, SET12_ROWS())
    pygame.draw.rect(surf, BLACK, r)
    m = cfg.get("latido", "AUTO")
    on = latido_on()
    sub = (f"AUTO · {'SÍ' if on else 'NO'}" if m == "AUTO" else m)
    draw_button(surf, r, "LATIDO OLED", sub, F["btn"] if F["btn"].size("LATIDO OLED")[0] < r.w - 10 else F["small"],
                filled=on, lit=flash.get((12, i), 0) > now)

VIEWS[12] = view_sub12

_tap_sub12_v1120 = tap_sub12

def tap_sub12(x, y):
    i = _latido_i()
    if i is not None and grid(i, 4, SET12_ROWS()).collidepoint(x, y):
        tap_flash((12, i))
        orden = ["AUTO", "SÍ", "NO"]
        m = cfg.get("latido", "AUTO")
        cfg["latido"] = orden[(orden.index(m) + 1) % 3 if m in orden else 0]
        save_cfg(); TAP_EV.set()
        plog(f"LATIDO OLED: {cfg['latido']} ({'activo' if latido_on() else 'apagado'})")
        return
    return _tap_sub12_v1120(x, y)
