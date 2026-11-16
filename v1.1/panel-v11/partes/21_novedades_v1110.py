# Panel Elite v1.1 · parte 21: novedades v1.1.10
#   PARADA DE EMERGENCIA (sender v1.0b14): aviso grande en rojo, voz y el robot se asusta.
#   BODEGA LLENA: el robot enseña unas cajas apiladas (las dibuja el panel) y luego pone su cara.
EV_LIST.append(("emergstop", "PARADA DE EMERGENCIA"))

_handle_note_v1110 = handle_note

def handle_note(kind, text):
    if kind == "emergstop":
        p = (str(text).split("|") + ["", ""])[:2]
        if ev_on("emergstop"):
            _xa_show("emergstop", col=RED, title="¡PARADA DE EMERGENCIA!",
                     big=(p[1] or ("ESTRELLA" if p[0] == "Star" else "PLANETA")).upper()[:30],
                     lines=["te has acercado demasiado rápido a la " + ("estrella" if p[0] == "Star" else "superficie"),
                            "FSD enfriándose: espera para volver a supercrucero"], secs=8)
        plog(f"Parada de emergencia: {p[1]} ({p[0]})")
        return
    return _handle_note_v1110(kind, text)

# --- BODEGA LLENA en el robot: foto de cajas apiladas ---
def cajas_jpg():
    import io, random as _rnd
    W_, H_ = 320, 240
    S_ = pygame.Surface((W_, H_)); S_.fill((8, 6, 4))
    for y in range(0, H_, 16):
        pygame.draw.line(S_, (22, 16, 8), (0, y), (W_, y))
    pygame.draw.rect(S_, (30, 22, 10), (0, H_ - 60, W_, 60))
    r_ = _rnd.Random(3)
    cw, ch = 58, 44
    for k in range(4):
        y = H_ - 52 - ch * (k + 1)
        x = (k % 2) * 29 - 10
        while x < W_:
            if not (k == 3 and r_.random() < 0.35):
                base = r_.choice([(255, 140, 0), (230, 120, 0), (200, 105, 0), (170, 90, 0)])
                osc = tuple(int(c * 0.55) for c in base)
                pygame.draw.rect(S_, base, (x, y, cw - 2, ch - 2))
                pygame.draw.rect(S_, osc, (x, y, cw - 2, ch - 2), 3)
                pygame.draw.line(S_, osc, (x, y), (x + cw - 2, y + ch - 2), 3)
                pygame.draw.line(S_, osc, (x + cw - 2, y), (x, y + ch - 2), 3)
                pygame.draw.rect(S_, (20, 14, 6), (x + cw // 2 - 10, y + 4, 18, 8))
            x += cw
    return jpg_bytes(S_)

_sc_foto_file_v1110 = sc_foto_file

def sc_foto_file(f):
    if f == "cajas":
        return "cajas"                                   # se dibuja, no es un archivo
    return _sc_foto_file_v1110(f)

_sc_foto_jpg_v1110 = sc_foto_jpg

def sc_foto_jpg(f):
    if f == "cajas":
        if "cajas" not in SC_FOTO["cache"]:
            SC_FOTO["cache"]["cajas"] = cajas_jpg()
        return SC_FOTO["cache"]["cajas"]
    return _sc_foto_jpg_v1110(f)

BODR = {"full": None}

def bodega_robot_watch(now):
    with lock:
        d, rx = state["data"], state["rx"]
    if not d or now - rx > 5 or not cfg.get("stackchan"):
        return
    h = hold_state(d)
    full = bool(h and h[0] >= h[1])
    if full and BODR["full"] is False and ev_on("bodegallena"):
        sc_foto("cajas", "BODEGA LLENA", f"{h[0]} / {h[1]} t", 7)
        sc_aviso("bodegallena", "alarm", "BODEGA LLENA", f"{h[0]} de {h[1]} t")   # la cara, al quitar la foto
    BODR["full"] = full

_render_v1110 = render

def render(surf):
    r_ = _render_v1110(surf)
    try:
        bodega_robot_watch(time.time())
    except Exception as e:
        log_exc("bodega robot", e)
    return r_
