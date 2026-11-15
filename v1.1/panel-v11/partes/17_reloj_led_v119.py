# Panel Elite v1.1 · parte 17: novedades v1.1.9 (reloj LED rojo, EMITIR suelta la memoria)
#   Los relojes de ATRACAR (aterrizaje) y SALIDA (despegue) en rojo vivo, como los relojes LED antiguos.
#   El último minuto parpadea entre rojo vivo y rojo apagado (igual que antes).

LED_RED = (255, 28, 18)
LED_DIM = (110, 6, 0)

def clock_col(sec, now):
    if sec < 60:
        return LED_RED if int(now * 2) % 2 else LED_DIM
    return LED_RED

# --- EMITIR: si nadie mira (o se apaga), se sueltan las imágenes guardadas ---
_stream_snap_v119 = stream_snap

def stream_snap(small):
    if not cfg.get("stream") or stream["clients"] <= 0:
        if stream["small"] is not None or stream["big"] is not None or stream["jpg"]:
            with stream_lock:
                stream["small"] = stream["big"] = None
                stream["jpg"] = {}
        return
    _stream_snap_v119(small)

# --- ROBOT: contento al vender en el mercado ---
#   Varias ventas seguidas (menos de 3 s entre una y otra) se juntan en un solo aviso.
#   No salta si vendes material que le falta a tu construcción (ahí ya va el aviso rojo).
EV_LIST.append(("venta", "ROBOT: VENTA EN EL MERCADO"))
VENTA = {"n": 0, "tipos": [], "t": 0.0, "red": False}
_col_red_v119 = _col_red

def _col_red(*a, **k):
    VENTA["red"] = True
    return _col_red_v119(*a, **k)

def _venta_envia(t0):
    time.sleep(3)
    if VENTA["t"] != t0 or not VENTA["n"]:
        return                                        # ha llegado otra venta: espera a esa
    n, tipos = VENTA["n"], VENTA["tipos"]
    VENTA.update(n=0, tipos=[])
    dato = f"{n:,} t de {tipos[0]}".replace(",", ".") if len(tipos) == 1 else \
           f"{n:,} t de {len(tipos)} mercancías".replace(",", ".")
    if cfg.get("stackchan") and ev_on("venta"):
        sc_aviso("venta", "ok", "VENDIDO", dato)

_handle_note_v119 = handle_note

def handle_note(kind, text):
    if kind != "mktsell":
        return _handle_note_v119(kind, text)
    VENTA["red"] = False
    _handle_note_v119(kind, text)
    if VENTA["red"]:
        return
    p = (str(text).split("|") + ["", "", "0", ""])[:4]
    try:
        n = int(p[2] or 0)
    except ValueError:
        n = 0
    if n <= 0:
        return
    VENTA["n"] += n
    if p[1] and p[1] not in VENTA["tipos"]:
        VENTA["tipos"].append(p[1])
    VENTA["t"] = t0 = time.time()
    threading.Thread(target=_venta_envia, args=(t0,), daemon=True).start()

# --- MAPAS del juego: el panel enseña lo que te sirve y vuelve al cerrarlos ---
#   mapa galáctico (GuiFocus 6) -> NAVEGACIÓN (la ruta)
#   mapa del sistema (GuiFocus 7) -> ficha del sistema donde estás (tu facción y EDSM)
#   Al cerrar el mapa vuelve a la pantalla de antes, salvo que hayas cambiado tú de pantalla.
#   ROBOT: mientras el mapa está abierto, cara de duda y mirando a los lados.
AUTO_LIST.append(("galmap", "MAPA GALÁCTICO > NAVEGACIÓN"))
AUTO_LIST.append(("sysmap", "MAPA DEL SISTEMA > FICHA DEL SISTEMA"))
MAPA = {"prev": None, "puesta": None, "sc": ""}

def _mapa_cambia(d, old, gui):
    if gui == old:
        return
    if gui in (6, 7):
        dest = None
        if gui == 6 and auto_on("galmap"):
            dest = 3
        elif gui == 7 and auto_on("sysmap") and d.get("system"):
            ui["rsys"] = (d["system"], "")
            redsm_want(d["system"]); dest = 212
        if dest is not None and not ui.get("idle_on"):
            if MAPA["puesta"] is None or ui.get("view") != MAPA["puesta"]:
                MAPA["prev"] = ui.get("view")             # la de antes de abrir el primer mapa
            ui["view"] = dest; MAPA["puesta"] = dest; TAP_EV.set()
    elif old in (6, 7):                                   # mapa cerrado
        if MAPA["puesta"] is not None and ui.get("view") == MAPA["puesta"] and MAPA["prev"] is not None:
            ui["view"] = MAPA["prev"]; TAP_EV.set()
        MAPA.update(prev=None, puesta=None)

_process_notes_v119 = process_notes

def process_notes(d):
    old = ui.get("gui", 0)
    r_ = _process_notes_v119(d)
    try:
        gui = (d or {}).get("gui", 0)
        _mapa_cambia(d or {}, old, gui)
        m = "gal" if gui == 6 else "sis" if gui == 7 else ""
        if m != MAPA["sc"]:
            MAPA["sc"] = m
            if cfg.get("stackchan"):
                sc_send({"t": "mapa", "mapa": m})
    except Exception as e:
        log_exc("mapas", e)
    return r_

_sc_send_v119 = sc_send

def sc_send(obj):
    if obj.get("t") == "hola":
        obj = dict(obj, mapa=MAPA["sc"])
    return _sc_send_v119(obj)
