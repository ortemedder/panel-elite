# Panel Elite v1.1 · parte 27: PORTAPAPELES y RUTA EXTERNA (v1.1.11)
#   Al llegar a cada sistema, el nombre del siguiente va al portapapeles del PC (Ctrl+V en el mapa galáctico):
#   el de la RUTA EXTERNA si hay una cargada, si no el siguiente salto de la ruta del juego. Se quita en CAMBIO AUTO.
#   RUTA EXTERNA: el CSV más nuevo de la carpeta rutas/ junto al sender (Spansh, neutrones...). Pestaña RUTA EXT.
#   en NAVEGACIÓN: paradas, la siguiente destacada, y botones COPIAR · ATRÁS · SALTAR · BORRAR. Avanza sola.
AUTO_LIST.append(("copiasig", "COPIAR SIGUIENTE SISTEMA AL LLEGAR"))
EV_LIST.append(("robruta", "ROBOT: SIGUIENTE PARADA DE LA RUTA EXTERNA"))
MENU[216] = "RUTA EXTERNA"
PARENT[216] = 3                                           # < vuelve a NAVEGACIÓN (en las pestañas no cabe)
RX_BTN = pygame.Rect(W - 112, TOP + 3, 104, 22)
RX_FILE = os.path.join(PANEL_DIR, "ruta_externa.json")
RX = {"st": None, "sys": None, "btn": {}, "borrar": 0.0}

def rx_estado():
    if RX["st"] is None:
        try:
            with open(RX_FILE, encoding="utf-8") as fh:
                RX["st"] = json.load(fh)
        except (OSError, ValueError):
            RX["st"] = {"key": None, "idx": 0, "borrada": False}
    return RX["st"]

def rx_guarda():
    try:
        with open(RX_FILE + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(RX["st"], fh)
        os.replace(RX_FILE + ".tmp", RX_FILE)
    except OSError:
        pass

def rx_ruta(d):
    """(paradas, índice de la siguiente) de la ruta externa activa, o (None, 0)."""
    r = (d or {}).get("rutaext") or {}
    P_ = r.get("p") or []
    if not P_:
        return None, 0
    st = rx_estado()
    key = f"{r.get('f')}|{r.get('m')}"
    if st.get("key") != key:                              # ruta nueva: se empieza por el principio
        st.update(key=key, idx=0, borrada=False)
        sy = ((d or {}).get("system") or "").lower()
        if sy and P_[0][0].lower() == sy:
            st["idx"] = 1
        rx_guarda()
        if auto_on("copiasig") and st["idx"] < len(P_):
            rx_copia(P_[st["idx"]][0], f"RUTA EXTERNA: {len(P_)} paradas")
    if st.get("borrada"):
        return None, 0
    return P_, min(st.get("idx", 0), len(P_))

def rx_copia(nombre, titulo=None):
    ir_send(nombre)
    if titulo:
        set_alert(titulo, f"copiado {nombre} · Ctrl+V en el mapa galáctico", GREEN, 4, kind="info")

def rx_watch(d):
    sy = (d or {}).get("system")
    if not sy or sy == RX["sys"]:
        return
    primera = RX["sys"] is None
    RX["sys"] = sy
    if primera:
        rx_ruta(d)
        return
    P_, i = rx_ruta(d)
    if P_:
        nombres = [p[0].lower() for p in P_]
        if sy.lower() in nombres[i:]:
            j = nombres.index(sy.lower(), i)
            rx_estado()["idx"] = i = j + 1
            rx_guarda()
            if i >= len(P_):
                set_alert("RUTA EXTERNA TERMINADA", sy, GREEN, 5)
                if cfg.get("stackchan") and ev_on("robruta"):
                    sc_aviso("robllegada", "ok", "HEMOS LLEGADO!", f"fin de la ruta: {sy}")
                return
            if auto_on("copiasig"):
                rx_copia(P_[i][0], f"PARADA {i} DE {len(P_)} · SIGUIENTE")
            if cfg.get("stackchan") and ev_on("robruta"):
                sc_aviso("robruta", "ok", "SIGUIENTE PARADA", f"{P_[i][0]}, quedan {len(P_) - i}")
        return
    route = (d or {}).get("route") or []
    if route and auto_on("copiasig"):
        rx_copia(route[0][0], "SIGUIENTE SALTO")

def view_rutaext(surf, d, flags, now):
    P_, i = rx_ruta(d)
    y = TOP + 4
    RX["btn"] = {}
    if not P_:
        route = (d or {}).get("route") or []
        put(surf, F["btn"], "Sin ruta externa", (8, y), ORANGE); y += 26
        for t_ in ("Descarga la ruta en CSV (Spansh, neutrones...) y déjala",
                   "en la carpeta rutas\\ junto a elite_sender.py (sender v1.0b15).",
                   "Se carga sola la más nueva y avanza al llegar a cada parada."):
            put(surf, F["small"], t_, (8, y), DIM, W - 16); y += 17
        if route:
            y += 10
            put(surf, F["small"], "SIGUIENTE SALTO DE LA RUTA DEL JUEGO", (8, y), DIM); y += 16
            put(surf, F["big"], route[0][0].upper(), (8, y), ORANGE, W - 150)
            b = pygame.Rect(W - 136, y - 2, 128, 30)
            draw_button(surf, b, "COPIAR", None, F["small"], lit=flash.get(("rxc",), 0) > now, compact=True)
            RX["btn"]["copiar_juego"] = (b, route[0][0])
        return
    r = (d or {}).get("rutaext") or {}
    put(surf, F["small"], f"{r.get('f', '')} · parada {min(i + 1, len(P_))} de {len(P_)}", (8, y), DIM, W - 16); y += 18
    ini = max(0, i - 2)
    for k in range(ini, min(len(P_), ini + 7)):
        nom, neu = P_[k][0], P_[k][1]
        if k < i:
            c_, pre = DIM, "· "
        elif k == i:
            c_, pre = ORANGE, "> "
            pygame.draw.rect(surf, (40, 25, 0), (4, y - 1, W - 8, 21), border_radius=3)
        else:
            c_, pre = WHITE, "   "
        put(surf, F["btn"] if k == i else F["small"], f"{pre}{k + 1}. {nom}", (8, y + (0 if k == i else 2)), c_, W - 60)
        if neu:
            put(surf, F["small"], "NEUTRÓN", (W - 8, y + 2), BLUE, anchor="topright")
        y += 21
    bw = (W - 16 - 18) // 4
    for n_, (lab, key) in enumerate((("COPIAR", "copiar"), ("< ATRÁS", "atras"), ("SALTAR >", "saltar"),
                                     ("¿SEGURO?" if now - RX["borrar"] < 3 else "BORRAR", "borrar"))):
        b = pygame.Rect(8 + n_ * (bw + 6), H - 40, bw, 34)
        draw_button(surf, b, lab, None, F["small"], lit=flash.get(("rx", key), 0) > now, compact=True)
        RX["btn"][key] = (b, None)

VIEWS[216] = view_rutaext

_view3_v1111 = VIEWS[3]

def view3_v1111(surf, d, flags, now):
    _view3_v1111(surf, d, flags, now)
    P_, i = rx_ruta(d)
    lab = f"RUTA EXT. {min(i + 1, len(P_))}/{len(P_)}" if P_ else "RUTA EXT."
    draw_button(surf, RX_BTN, lab, None, F["tiny"], lit=bool(P_) or flash.get(("rxb",), 0) > now, compact=True)

VIEWS[3] = view3_v1111

_on_tap_v1111 = on_tap

def on_tap(x, y):
    if ui.get("view") == 3 and RX_BTN.inflate(6, 6).collidepoint(x, y) and not ui.get("idle_on"):
        tap_flash(("rxb",)); ui["view"] = 216; TAP_EV.set(); return
    if ui.get("view") == 216 and y > TOP and not ui.get("idle_on"):
        with lock:
            d = state.get("data") or {}
        P_, i = rx_ruta(d)
        for key, (b, extra) in RX["btn"].items():
            if b.collidepoint(x, y):
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
                TAP_EV.set()
                return
        return
    return _on_tap_v1111(x, y)

# el robot: copiloto de la ruta externa
_rob_cop_v1111 = rob_cop

def rob_cop(d):
    P_, i = rx_ruta(d)
    if P_ and i < len(P_) and ev_on("robcop") and not (d.get("Flags", 0) & 1):
        return f"ruta ext. {i + 1}/{len(P_)}\nsig: {P_[i][0]}"
    return _rob_cop_v1111(d)

_render_v1111c = render

def render(surf):
    r_ = _render_v1111c(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d and time.time() - rx < 5:
            rx_watch(d)
    except Exception as e:
        log_exc("ruta externa", e)
    return r_
