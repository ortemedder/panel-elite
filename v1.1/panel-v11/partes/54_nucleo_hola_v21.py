# Panel Elite v2.1 · parte 54: v2.1 — NÚCLEO y AUTODESCUBRIMIENTO (va con el sender v1.0b18)
#   - NÚCLEO (COMBATE a 1280x800): botón en la ficha del objetivo que pulsa «siguiente subsistema» hasta apuntar a la
#     planta de energía (máximo 15 pulsaciones; para si el objetivo cambia, si el juego no responde o si da la vuelta
#     entera sin encontrarla). Cada cambio de subsistema refresca también el escudo y el casco del objetivo.
#     CAMBIO AUTO > «COMBATE: APUNTAR AL NÚCLEO AL FIJAR» (apagado de fábrica): lo hace solo una vez por objetivo,
#     al terminar el escaneo. Las teclas salen por el mismo camino que los botones (teclado USB o red).
#   - AUTODESCUBRIMIENTO: el panel se anuncia en la red cada 5 s (UDP 5007, «ELITEPANEL-HOLA|versión|cmdr») y el
#     sender v1.0b18 lo encuentra solo, sin poner la IP a mano.

SENDER_OK = SENDER_REQ = "v1.0b18"

AUTO_LIST.append(("nucleo", "COMBATE: APUNTAR AL NÚCLEO AL FIJAR"))
EVL[162][4]["nucleo"] = False                                      # apagado de fábrica

# ---------------------------------------------------------------------------------------------------------------
# AUTODESCUBRIMIENTO: anuncio en la red
# ---------------------------------------------------------------------------------------------------------------
def hola_loop():
    while True:
        try:
            so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            so.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            msg = f"ELITEPANEL-HOLA|{PANEL_VER.split(' · ')[0]}|{cfg.get('cmdr', '')}".encode("utf-8")[:200]
            so.sendto(msg, ("255.255.255.255", 5007))
            so.close()
        except OSError:
            pass                                                   # sin red todavía: se reintenta
        time.sleep(5)

threading.Thread(target=hola_loop, daemon=True, name="hola").start()

# ---------------------------------------------------------------------------------------------------------------
# NÚCLEO: apuntar a la planta de energía
# ---------------------------------------------------------------------------------------------------------------
NUC = {"run": False, "msg": "", "auto_key": None}

def nuc_es_planta(t):
    raw = (t or {}).get("subraw") or ""
    if raw:
        return "powerplant" in raw
    nm = ((t or {}).get("subsys") or "").lower()
    return "power plant" in nm or "planta de energ" in nm or "núcleo" in nm

def _nuc_tecla():
    k = next((it[1] for it in COMBAT_BTNS if it[0] == "SUBSIST."), None)
    return k if k and k != SIN and key_ok(k) else None

def _nuc_tgt():
    with lock:
        d = state["data"]
    return (d or {}).get("target")

def _nuc_fin(titulo, sub, col):
    NUC.update(run=False, msg="")
    set_alert(titulo, sub, col, 2.5, kind="info")

def nuc_run(auto=False):
    try:
        t = _nuc_tgt()
        if not t:
            return _nuc_fin("NÚCLEO", "no hay objetivo fijado", ORANGE)
        if nuc_es_planta(t):
            return _nuc_fin("NÚCLEO APUNTADO", f"{t.get('subsys') or 'planta de energía'}", GREEN)
        k = _nuc_tecla()
        if not k:
            return _nuc_fin("SIN TECLA EN EL JUEGO", "«siguiente subsistema» (AJUSTES > OPCIONES > TECLAS)", ORANGE)
        quien = (t.get("stype"), t.get("pilot"))
        vistos, fallos = [], 0
        for n in range(1, 16):
            NUC["msg"] = f"BUSCANDO {n}/15"
            t0 = t.get("t")
            press_seq([k])
            fin = time.time() + 1.5
            while time.time() < fin:
                time.sleep(0.05)
                t = _nuc_tgt()
                if not t or (t.get("stype"), t.get("pilot")) != quien:
                    return _nuc_fin("NÚCLEO", "el objetivo ha cambiado", ORANGE)
                if t.get("t") != t0:
                    break
            else:
                fallos += 1
                if fallos >= 2:
                    return _nuc_fin("NÚCLEO", "el juego no responde (¿objetivo sin escanear?)", ORANGE)
                continue
            if nuc_es_planta(t):
                sh = t.get("subhealth")
                return _nuc_fin("NÚCLEO APUNTADO", (t.get("subsys") or "planta de energía") +
                                (f" {sh:.0f}%" if sh is not None else ""), GREEN)
            s_ = t.get("subraw") or t.get("subsys") or ""
            if s_ and vistos and s_ == vistos[0]:
                return _nuc_fin("NÚCLEO", "esta nave no deja apuntar a su planta", ORANGE)
            vistos.append(s_)
        _nuc_fin("NÚCLEO", "no lo he encontrado en 15 pulsaciones", ORANGE)
    except Exception as e:
        NUC.update(run=False, msg="")
        log_exc("núcleo", e)

def nuc_go(auto=False):
    if NUC["run"]:
        return
    NUC["run"] = True
    NUC["msg"] = "BUSCANDO"
    threading.Thread(target=nuc_run, args=(auto,), daemon=True, name="nucleo").start()

def nuc_auto(d):
    """Una vez por objetivo, con el escaneo terminado, si está activo en CAMBIO AUTO."""
    if not (cfg.get("auto", True) and (cfg.get("autoev") or {}).get("nucleo", False)):
        return
    t = (d or {}).get("target")
    if not t or t.get("scan", 0) < 3:
        return
    key = (t.get("stype"), t.get("pilot"))
    if key == NUC["auto_key"]:
        return
    NUC["auto_key"] = key
    if not nuc_es_planta(t):
        nuc_go(True)

_render_v21 = render

def render(surf):
    r_ = _render_v21(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d and time.time() - rx < 5:
            nuc_auto(d)
    except Exception as e:
        log_exc("núcleo auto", e)
    return r_

# botón en la ficha del objetivo de COMBATE (solo en el MENÚ a pantalla entera: en el cuadro del tablero no cabe)
LZ_ACC["nucleo"] = lambda acc, X, Y: nuc_go()

_lv_combate_v21 = lv_combate

def lv_combate(L, area, d, flags, now):
    _lv_combate_v21(L, area, d, flags, now)
    if area.h < 500 or not (d or {}).get("target"):
        return
    ch = int(area.h * 0.44)
    card = pygame.Rect(area.x + 6, area.y + 4, area.w - 12, ch - 8)
    pad = max(8, card.h // 30)
    hb = F["btn"].get_height()
    r = pygame.Rect(card.x + 2 * pad, card.bottom - pad - hb - 40, 300, hb + 36)
    t = d["target"]
    ok = nuc_es_planta(t)
    auto = (cfg.get("autoev") or {}).get("nucleo", False)
    sub = NUC["msg"] if NUC["run"] else ("APUNTADO" if ok else ("AUTO" if auto else "planta de energía"))
    lz_boton_v(L, r, "NÚCLEO", sub, F["btn"], filled=ok, lit=NUC["run"] and int(now * 3) % 2 == 0)
    lz_hit(r, "nucleo")

LZ_PANEL[6] = lv_combate
LZ_CELDA[6] = lambda L, d, flags, now: lv_combate(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now)
