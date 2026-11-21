# Panel Elite v2.0 · parte 38: v2.0b1 — BASE «Ajuste resoluciones de pantalla»
#   Plan completo en claude/plan_v2.md. Esta beta pone la base; las pantallas se pasan una a una en las siguientes.
#   - LIENZO de 1280x800: las pantallas nuevas se dibujarán en coordenadas de 1280x800 (LienzoSurf) y se escalan igual
#     en ancho y alto a la pantalla real (Ortem 1280x800 x1; KORZO 1024x600 x0,75 = 960x600 con franjas de 32 px).
#   - PUENTE: lo que aún es de 480x320 y ocupa toda la HDMI (espera, avisos, recogida, arranque) se dibuja NÍTIDO
#     (como NITIDEZ ALTA) en vez de ampliar una imagen pequeña.
#   - UN SOLO MODO en la HDMI: tablero automático; tocar la barra de arriba (o TAB / clic derecho / pulsación larga)
#     abre el MENÚ a pantalla entera, que vuelve solo al tablero a los 20 s sin tocar (el FIJO de antes, para todos).
#   - TOQUES: un solo camino para el dedo, el ratón y la web (EMITIR).
#   - EMITIR: una sola imagen (la de la HDMI); OPCIONES > EMITIR pasa por NO > 1280x800 > 960x600 > 640x400 (v2.0b5b).
#   - 12 AJUSTES > PANTALLA v2: NO deja todo como en la v1.1.20b.

LW, LH = 1280, 800
LZ = {"surf": {}, "lleno": False}

def lienzo_on():
    return bool(cfg.get("lienzo", True))

def lienzo_escala(bw=None, bh=None):
    """(escala, x0, y0) del lienzo de 1280x800 dentro de la pantalla real."""
    bw, bh = bw or BIG.get("w") or LW, bh or BIG.get("h") or LH
    s = min(bw / LW, bh / LH)
    return s, (bw - LW * s) / 2, (bh - LH * s) / 2

def lienzo_punto(xn, yn):
    """Toque en la HDMI (0..1) -> punto del lienzo de 1280x800 (o None si cae en las franjas)."""
    bw, bh = BIG.get("w") or LW, BIG.get("h") or LH
    s, ox, oy = lienzo_escala(bw, bh)
    X, Y = (xn * bw - ox) / s, (yn * bh - oy) / s
    return (X, Y) if 0 <= X < LW and 0 <= Y < LH else None

# ---------------------------------------------------------------------------------------------------------------
# superficie y letras del lienzo (para las pantallas que se vayan pasando a 1280x800)
# ---------------------------------------------------------------------------------------------------------------
LZ_LETRAS = (("big", 60), ("btn", 46), ("small", 34), ("num", 100), ("clock", 220), ("mono", 22), ("tiny", 28))

class LienzoSurf(ScaledSurf):
    """Se dibuja como si midiera 1280x800; por debajo escribe en la pantalla real a su escala."""
    def get_size(self):
        return (LW, LH)
    def get_width(self):
        return LW
    def get_height(self):
        return LH
    def get_rect(self, **k):
        r = pygame.Rect(0, 0, LW, LH)
        for a, v in k.items():
            setattr(r, a, v)
        return r
    def get_clip(self):
        return self.clip or pygame.Rect(0, 0, LW, LH)

def lienzo_letras(s):
    out = {}
    for k, base in LZ_LETRAS:
        size = max(6, int(round(base * s)))
        if ("lz", k, size) not in _HIF:
            mono = pygame.font.match_font("dejavusansmono") or pygame.font.match_font("monospace")
            _HIF[("lz", k, size)] = pygame.font.Font(mono if k == "mono" else None, size)
        out[k] = FontProxy(_HIF[("lz", k, size)], size / base)
    return out

def lienzo_dibuja(S, fn, *a):
    """Dibuja fn(lienzo, *a) en coordenadas de 1280x800 sobre la superficie real S. True si ha ido bien."""
    bw, bh = S.get_size()
    s, ox, oy = lienzo_escala(bw, bh)
    sub = S.subsurface(pygame.Rect(int(ox), int(oy), min(bw - int(ox), int(LW * s)), min(bh - int(oy), int(LH * s))))
    keep = dict(F)
    HI_IDS.clear(); HI_KEEP.clear()
    F.update(lienzo_letras(s))
    try:
        fn(LienzoSurf(sub, s, s), *a)
        return True
    except Exception as e:
        log_exc("lienzo", e)
        return False
    finally:
        F.clear(); F.update(keep)
        HI_IDS.clear(); HI_KEEP.clear()

# ---------------------------------------------------------------------------------------------------------------
# PUENTE: pantallas de 480x320 a pantalla entera, dibujadas nítidas a su tamaño real
# ---------------------------------------------------------------------------------------------------------------
def lienzo_viejo(S, fn, *a):
    bw, bh = S.get_size()
    k = min(bw / W, bh / H)
    size = (int(W * k), int(H * k))
    real = LZ["surf"].get(size)
    if real is None:
        real = LZ["surf"][size] = pygame.Surface(size)
    real.fill(BLACK)
    keep = dict(F)
    HI_IDS.clear(); HI_KEEP.clear()
    F.update(hi_fonts(k))
    HI_PASS[0] = True
    try:
        fn(ScaledSurf(real, k, k), *a)
    except Exception as e:
        log_exc("lienzo puente", e)
        return False
    finally:
        HI_PASS[0] = False
        F.clear(); F.update(keep)
        HI_IDS.clear(); HI_KEEP.clear()
    S.fill(BLACK)
    S.blit(real, ((bw - size[0]) // 2, (bh - size[1]) // 2))
    return True

def lienzo_viejo_punto(xn, yn):
    """Toque en la HDMI -> punto del panel viejo (480x320) cuando está a pantalla entera."""
    bw, bh = BIG.get("w") or LW, BIG.get("h") or LH
    k = min(bw / W, bh / H)
    px, py = (xn * bw - (bw - W * k) / 2) / k, (yn * bh - (bh - H * k) / 2) / k
    return (px, py) if 0 <= px < W and 0 <= py < H else None

_render_big_base_v20 = render_big_base

def render_big_base():
    LZ["lleno"] = False
    S = BIG.get("surf")
    if not lienzo_on() or S is None or hdmi_panel() or ui.get("bye"):
        return _render_big_base_v20()
    with lock:
        d, rx = state["data"], state["rx"]
    now = time.time()
    online = d is not None and now - rx < 5
    flags = (d or {}).get("Flags", 0) if online else 0
    # mismo orden que render_big_base: arranque > espera (sin datos) > aviso entero > menú del juego
    fn, a, rotulo = None, (), None
    if now - ui["start"] < 3:
        fn, a = draw_splash, (now,)
    elif not online:
        fn, a = draw_idle, (now,)
    elif ui.get("alert") and now < ui["alert"]["until"]:
        fn, a = draw_alert, (now,)
    elif xa.get("a") and now < xa["a"]["until"] and not kill_in_cell(xa["a"]):
        fn, a = draw_xa, (now,)
    elif flags & (1 << 11) or now < scoop["full_until"]:
        fn, a = draw_scoop, (d, flags, now)
    elif d.get("menu"):
        fn, a, rotulo = draw_idle, (now,), "MENÚ PRINCIPAL"
    if fn is None:
        return _render_big_base_v20()
    BIG["fast"] = False
    BIG["rects"] = []
    if not lienzo_viejo(S, fn, *a):
        return _render_big_base_v20()
    LZ["lleno"] = True
    if rotulo:
        if BIG["fonts"] is None:
            BIG["fonts"] = (pygame.font.Font(None, 40), pygame.font.Font(None, 26))
        put(S, BIG["fonts"][0], rotulo, (S.get_width() // 2, S.get_height() - 40), GREEN, anchor="center")

# ---------------------------------------------------------------------------------------------------------------
# UN SOLO MODO: tablero + MENÚ (vuelve solo a los 20 s)
# ---------------------------------------------------------------------------------------------------------------
_hdmi_fijo_v20 = hdmi_fijo

def hdmi_fijo():
    return True if lienzo_on() else _hdmi_fijo_v20()

def lienzo_menu():
    if hdmi_panel():
        return
    cfg["hdmi"] = "panel"; save_cfg()
    HDMIF["t"] = time.time()
    TAP_EV.set()

LZ_CAB = 44                                  # alto de la barra de arriba del tablero (render_big_base)

# ---------------------------------------------------------------------------------------------------------------
# TOQUES: dedo en la HDMI
# ---------------------------------------------------------------------------------------------------------------
_big_tap_v20 = big_tap

def big_tap(xn, yn):
    if not lienzo_on() or hdmi_panel():
        return _big_tap_v20(xn, yn)
    HDMIF["t"] = time.time()
    if LZ["lleno"]:
        p = lienzo_viejo_punto(xn, yn)
        alerta = ui.get("alert") and time.time() < ui["alert"]["until"]
        fin = xa.get("a") and xa["a"].get("title") in ("SESIÓN TERMINADA", "BATALLA TERMINADA") \
            and time.time() < xa["a"]["until"]
        if p and (ui.get("idle_on") or alerta or fin):
            espera, skip0 = ui.get("idle_on"), ui.get("idle_skip", 0)
            try:
                on_tap(int(p[0]), int(p[1]))
            except Exception as e:
                log_exc("toque HDMI", e)
            if espera and ui.get("idle_skip", 0) > skip0 and ui.get("view") in (0, 100):
                lienzo_menu()                # «toca la pantalla para abrir el menú»: en la HDMI, el MENÚ
            TAP_EV.set()
        elif not ui.get("idle_on"):
            lienzo_menu()                    # pantalla entera sin botones: abre el MENÚ
        return
    if yn * (BIG.get("h") or LH) < LZ_CAB:                 # (sin pantalla entera: siempre hay barra de arriba)
        lienzo_menu(); return                # barra de arriba del tablero: MENÚ
    return _big_tap_v20(xn, yn)

# ratón y teclado: fuera del MENÚ, el clic izquierdo abre el MENÚ (antes tocaba botones que no se veían)
_handle_input_v20 = handle_input

def handle_input(ev, ec):
    if lienzo_on() and not hdmi_panel() and BIG.get("fb") is not None \
            and ev.type == ec.EV_KEY and ev.value == 1 and ev.code == ec.BTN_LEFT:
        mouse["t"] = time.time()
        lienzo_menu(); return
    return _handle_input_v20(ev, ec)

# web (EMITIR): la imagen es la de la HDMI; el clic va por el mismo camino que el dedo
_remote_tap_v20 = remote_tap

def remote_tap(x, y, w, h, which):
    if not lienzo_on() or BIG.get("fb") is None:
        return _remote_tap_v20(x, y, w, h, which)
    if 0 <= x < w and 0 <= y < h:
        big_tap(x / max(1, w), y / max(1, h))

# ---------------------------------------------------------------------------------------------------------------
# EMITIR: una sola imagen, a 1280x800, 960x600 o 640x400
# ---------------------------------------------------------------------------------------------------------------
EMI_TAM = ["1280x800", "960x600", "640x400"]

def emitir_tam():
    if not IS_PI3 and not cfg.get("emitam_b5b"):          # v2.0b5b: en la Pi 4, 1280x800 (una vez, aunque hubiera 960x600)
        cfg["emitam_b5b"] = True
        if cfg.get("emitam") in (None, "960x600"):
            cfg["emitam"] = "1280x800"
        save_cfg()
    t = cfg.get("emitam") or ("640x400" if IS_PI3 else "1280x800")
    return t if t in EMI_TAM else "1280x800"

_stream_snap_v20 = stream_snap

def stream_snap(small):
    if not lienzo_on() or not cfg.get("stream") or stream["clients"] <= 0:
        return _stream_snap_v20(small)
    now = time.time()
    if now - _SNAP["t"] < (0.2 if IS_PI3 else 0.1):
        return
    _SNAP["t"] = now
    with stream_lock:
        src = BIG["surf"] if BIG.get("fb") and BIG.get("surf") is not None else (panel_hi() if cfg.get("sharp") else None) or small
        tw, th = (int(v) for v in emitir_tam().split("x"))
        sc = min(tw / src.get_width(), th / src.get_height(), 1.0)
        size = (max(1, int(src.get_width() * sc)), max(1, int(src.get_height() * sc)))
        if size == src.get_size():
            img = src.copy()
        elif IS_PI3:
            img = pygame.transform.scale(src, size)
        else:
            try:
                img = pygame.transform.smoothscale(src, size)
            except ValueError:
                img = pygame.transform.scale(src, size)
        stream["small"] = stream["big"] = img
        stream["seq"] += 1

# ---------------------------------------------------------------------------------------------------------------
# AJUSTES > OPCIONES > EMITIR: NO > 960x600 > 640x400 > 1280x800 > NO (con PANTALLA v2)
# ---------------------------------------------------------------------------------------------------------------
EMI_I = 5                                    # posición de EMITIR en OPCIONES (04 view_settings / 13 on_tap)

def emitir_ciclo():
    if not cfg.get("stream"):
        cfg["stream"] = True; cfg["emitam"] = "1280x800" if not IS_PI3 else "640x400"
        stream_start()
    else:
        orden = ["1280x800", "960x600", "640x400"] if not IS_PI3 else ["640x400", "960x600", "1280x800"]
        i = orden.index(emitir_tam()) if emitir_tam() in orden else 0
        if i + 1 < len(orden):
            cfg["emitam"] = orden[i + 1]
        else:
            cfg["stream"] = False
    plog("EMITIR: " + (emitir_tam() if cfg.get("stream") else "NO"))
    save_cfg(); TAP_EV.set()

_view_1244_v20 = VIEWS[1244]

def view_settings_v20(surf, d, flags, now):
    _view_1244_v20(surf, d, flags, now)
    if not lienzo_on():
        return
    r = grid(EMI_I, 4, 3)
    on = bool(cfg.get("stream"))
    pygame.draw.rect(surf, BLACK, r)
    sub = (stream["err"] or f"{emitir_tam()} · {my_ip()}") if on else "NO"
    draw_button(surf, r, "EMITIR", sub, F["btn"], filled=on, lit=flash.get((124, EMI_I), 0) > now)

VIEWS[1244] = view_settings_v20

# ---------------------------------------------------------------------------------------------------------------
# 12 AJUSTES: PANTALLA v2 (SÍ / NO)
# ---------------------------------------------------------------------------------------------------------------
SET12.append(("PANTALLA v2", "lienzo"))

def _lz_i():
    return next((i for i, it in enumerate(SET12) if it and it[1] == "lienzo"), None)

_view_sub12_v20 = view_sub12

def view_sub12(surf, d, flags, now):
    _view_sub12_v20(surf, d, flags, now)
    i = _lz_i()
    if i is None:
        return
    r = grid(i, 4, SET12_ROWS())
    pygame.draw.rect(surf, BLACK, r)
    draw_button(surf, r, "PANTALLA v2", "SÍ · 1280x800" if lienzo_on() else "NO · como v1.1",
                F["btn"] if F["btn"].size("PANTALLA v2")[0] < r.w - 10 else F["small"],
                filled=lienzo_on(), lit=flash.get((12, i), 0) > now)

VIEWS[12] = view_sub12

_tap_sub12_v20 = tap_sub12

def tap_sub12(x, y):
    i = _lz_i()
    if i is not None and grid(i, 4, SET12_ROWS()).collidepoint(x, y):
        tap_flash((12, i))
        cfg["lienzo"] = not lienzo_on()
        plog("PANTALLA v2: " + ("SÍ (lienzo 1280x800)" if cfg["lienzo"] else "NO (como la v1.1.20b)"))
        save_cfg(); TAP_EV.set()
        return
    return _tap_sub12_v20(x, y)

_on_tap_v20 = on_tap

def on_tap(x, y):
    if lienzo_on() and ui.get("view") == 1244 and not ui.get("idle_on") and grid(EMI_I, 4, 3).collidepoint(x, y):
        tap_flash((124, EMI_I)); emitir_ciclo(); return
    return _on_tap_v20(x, y)
