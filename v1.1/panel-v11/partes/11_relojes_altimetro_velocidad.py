# Panel Elite v1.1 · parte 11: relojes altimetro velocidad (lineas 9814-10563 del panel entero)
# ---------- v1.0 beta 15 ----------
# --- reloj de lamas (como los paneles de aeropuerto): cada cifra en su tarjeta, la lama cae al cambiar ---
FLIPS, _FCC = {}, {}

def _flip_font(h):
    k = ("f", h)
    if k not in _FCC:
        _FCC[k] = pygame.font.Font(None, max(8, int(h * 1.32)))
    return _FCC[k]

def _flip_card(ch, w, h, col):
    k = (ch, w, h, col)
    if k not in _FCC:
        c = pygame.Surface((w, h), pygame.SRCALPHA)
        r = max(3, w // 7)
        h2 = h // 2
        pygame.draw.rect(c, (52, 52, 58), (0, 0, w, h2), border_top_left_radius=r, border_top_right_radius=r)
        pygame.draw.rect(c, (36, 36, 40), (0, h2, w, h - h2), border_bottom_left_radius=r, border_bottom_right_radius=r)
        pygame.draw.rect(c, (70, 70, 78), (2, 1, w - 4, max(1, h // 30)))          # brillo arriba
        g = _flip_font(h).render(ch, True, col)
        c.blit(g, ((w - g.get_width()) // 2, (h - g.get_height()) // 2 + int(h * 0.05)))
        pygame.draw.line(c, (0, 0, 0), (0, h2), (w, h2), max(1, h // 36))
        hw, hh = max(2, w // 16), max(3, h // 8)
        pygame.draw.rect(c, (12, 12, 12), (0, h2 - hh // 2, hw, hh))                # bisagras
        pygame.draw.rect(c, (12, 12, 12), (w - hw, h2 - hh // 2, hw, hh))
        _FCC[k] = c
    return _FCC[k]

def draw_flip_aero(surf, rect, text, col, now, key, dur=0.45):
    """Texto tipo M:SS en tarjetas de lamas. rect en coordenadas del panel (nitido tambien en la HDMI)."""
    real, rr = (surf.real, surf._r(rect)) if type(surf).__name__ == "ScaledSurf" else (surf, pygame.Rect(rect))
    nd = sum(1 for c in text if c != ":"); nc = len(text) - nd
    gap = max(2, rr.h // 14)
    cw = int((rr.w - gap * (len(text) - 1)) / (nd + 0.45 * nc))
    ch = min(rr.h, int(cw * 1.45))
    cw = int(ch / 1.45)
    total = cw * nd + int(cw * 0.45) * nc + gap * (len(text) - 1)
    x = rr.x + (rr.w - total) // 2
    y = rr.y + (rr.h - ch) // 2
    h2 = ch // 2
    for i, c_ in enumerate(text):
        if c_ == ":":
            w_ = int(cw * 0.45)
            for yy in (y + ch // 3, y + 2 * ch // 3):
                pygame.draw.circle(real, col, (x + w_ // 2, yy), max(2, cw // 9))
            x += w_ + gap; continue
        st = FLIPS.setdefault((key, i), {"v": c_, "old": c_, "t": 0})
        if st["v"] != c_:
            st.update(old=st["v"], v=c_, t=now)
        p = (now - st["t"]) / dur
        new, old = _flip_card(c_, cw, ch, col), _flip_card(st["old"], cw, ch, col)
        if p >= 1 or p < 0:
            real.blit(new, (x, y))
        else:
            real.blit(new, (x, y), (0, 0, cw, h2))                   # arriba ya la cifra nueva
            real.blit(old, (x, y + h2), (0, h2, cw, ch - h2))        # abajo aun la vieja
            if p < 0.5:                                               # la lama de arriba cae
                k = 1 - p / 0.5
                hh = max(1, int(h2 * k))
                part = pygame.transform.smoothscale(old.subsurface((0, 0, cw, h2)), (cw, hh))
                part.fill((int(255 - 90 * (1 - k)),) * 3 + (255,), special_flags=pygame.BLEND_RGBA_MULT)
                real.blit(part, (x, y + h2 - hh))
            else:                                                     # y se abre por abajo la nueva
                k = (p - 0.5) / 0.5
                k = min(1.0, k * 1.08) if k < 0.9 else 1.0 - (1.0 - k) * 0.4   # pequeno rebote
                hh = max(1, int((ch - h2) * k))
                part = pygame.transform.smoothscale(new.subsurface((0, h2, cw, ch - h2)), (cw, hh))
                real.blit(part, (x, y + h2))
            pygame.draw.line(real, (0, 0, 0), (x, y + h2), (x + cw, y + h2), max(1, ch // 36))
            TAP_EV.set()                                              # mientras gira: que se vea fluido
        x += cw + gap

# --- v1.1: reloj LCD de 7 segmentos (sin animacion: gasta mucha menos CPU) ---
# AJUSTES > PANTALLA > RELOJ. De entrada: AEROPUERTO en la Pi 4 y LCD en la Pi 3 (o cualquier otra mas lenta).
SEG7 = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
        "8": "abcdefg", "9": "abcdfg", "-": "g"}
_SEGC = {}
PIMODEL = {"m": None}

def pi_model():
    if PIMODEL["m"] is None:
        try:
            PIMODEL["m"] = open("/proc/device-tree/model").read().strip("\x00 \n")
        except OSError:
            PIMODEL["m"] = ""
    return PIMODEL["m"]

def clock_style():
    st = cfg.get("reloj")
    if st in ("AEROPUERTO", "LCD"):
        return st
    m = pi_model()
    return "AEROPUERTO" if not m or any(x in m for x in ("Pi 4", "Pi 5", "Pi 500", "Pi 400")) else "LCD"

def _seg_digit(ch, w, h, col):
    k = (ch, w, h, col)
    if k not in _SEGC:
        if len(_SEGC) > 120:
            _SEGC.clear()
        s_ = pygame.Surface((w, h), pygame.SRCALPHA)
        t = max(3, w // 6); m = t // 2 + 1
        ghost = (col[0] // 7, col[1] // 7, col[2] // 7)
        P = {"a": (m, 0, w - 2 * m, t), "g": (m, h // 2 - t // 2, w - 2 * m, t), "d": (m, h - t, w - 2 * m, t),
             "f": (0, m, t, h // 2 - m), "b": (w - t, m, t, h // 2 - m), "e": (0, h // 2 + 1, t, h // 2 - m - 1),
             "c": (w - t, h // 2 + 1, t, h // 2 - m - 1)}
        for n, rc in P.items():
            pygame.draw.rect(s_, col if n in SEG7.get(ch, "") else ghost, rc, border_radius=max(1, t // 2))
        _SEGC[k] = s_
    return _SEGC[k]

def draw_lcd(surf, rect, text, col):
    real, rr = (surf.real, surf._r(rect)) if type(surf).__name__ == "ScaledSurf" else (surf, pygame.Rect(rect))
    pygame.draw.rect(real, (14, 10, 4), rr, border_radius=max(3, rr.h // 12))
    h = int(rr.h * 0.74); w = int(h * 0.55); gap = max(3, w // 4)
    tot = sum(w if c != ":" else w // 3 for c in text) + gap * (len(text) - 1)
    if tot > rr.w - 8:                                   # que quepa
        k = (rr.w - 8) / tot; h = int(h * k); w = int(h * 0.55); gap = max(2, w // 4)
        tot = sum(w if c != ":" else w // 3 for c in text) + gap * (len(text) - 1)
    x = rr.centerx - tot // 2; y = rr.centery - h // 2
    for c in text:
        if c == ":":
            for yy in (y + h // 3, y + 2 * h // 3):
                pygame.draw.circle(real, col, (x + w // 6, yy), max(2, w // 8))
            x += w // 3 + gap; continue
        real.blit(_seg_digit(c, w, h, col), (x, y)); x += w + gap

def draw_flip(surf, rect, text, col, now, key, dur=0.45):
    if clock_style() == "LCD":
        draw_lcd(surf, rect, text, col)
    else:
        draw_flip_aero(surf, rect, text, col, now, key, dur)

def mmss(sec):
    sec = max(0, int(sec))
    return f"{min(99, sec // 60)}:{sec % 60:02d}"          # 10:00 en los puertos planetarios

def clock_col(sec, now):
    if sec < 60:
        return RED if int(now * 2) % 2 else (130, 0, 0)
    return (255, 215, 0) if sec < 120 else ORANGE

# --- reloj del atraque en ESTACION (y en ATRAQUE de la pantalla grande) ---
DOCK_SECS = 599

def dock_left(d, now):
    st = (d or {}).get("station") or {}
    if st.get("status") != "CONCEDIDO" or not st.get("gt"):
        return None
    return dock_secs(st) - (pc_now(d, now) - st["gt"])

PLANET_PORTS = ("CraterOutpost", "CraterPort", "OnFootSettlement", "SurfaceStation", "PlanetaryConstructionDepot")

def dock_secs(st):
    """En puertos planetarios el juego da un segundo mas: el reloj empieza en 10:00 (en estaciones, 9:59)."""
    t_ = str(st.get("type") or "")
    return DOCK_SECS + 1 if t_ in PLANET_PORTS or "Planetary" in t_ or "Surface" in t_ else DOCK_SECS

_view_station_b15 = VIEWS[8]

def view_station_b15(surf, d, flags, now):
    _view_station_b15(surf, d, flags, now)
    left = dock_left(d, now)
    if left is None:
        return
    r = pygame.Rect(250, 182, 222, 84)
    pygame.draw.rect(surf, BLACK, r.inflate(6, 18), border_radius=8)
    put(surf, F["tiny"], "TIEMPO PARA ATRACAR", (r.centerx, r.y - 4), DIM, anchor="center")
    draw_flip(surf, r.inflate(-6, -8).move(0, 4), mmss(left), clock_col(left, now), now, "dock")

VIEWS[8] = view_station_b15

# --- salida de la estacion: banda, reloj de 6 min y cambio a EN VIVO al salir ---
AUTO_LIST.append(("salida", "SALIDA DE LA ESTACIÓN > EN VIVO"))
EXIT_SECS = 300
EXW = {"out": None}

def exit_left(d, now):
    x = (d or {}).get("exitst") or {}
    if not x.get("t0") or x.get("out"):
        return None, x
    left = EXIT_SECS - (pc_now(d, now) - x["t0"])
    return (left if left > -60 else None), x

def draw_exit_band(surf, d, now):
    left, x = exit_left(d, now)
    if left is None:
        return
    r = pygame.Rect(0, H - 46, W, 46)
    pygame.draw.rect(surf, BLACK, r)
    pygame.draw.rect(surf, RED if left < 60 else ORANGE, r, 2, border_radius=6)
    put(surf, F["btn"], "DENTRO DE LA ESTACIÓN", (10, r.y + 5), ORANGE, W - 170)
    put(surf, F["small"], "sal por la ranura · " + (x.get("st") or ""), (10, r.y + 26), DIM, W - 170)
    draw_flip(surf, pygame.Rect(W - 150, r.y + 4, 142, 38), mmss(left), clock_col(left, now), now, "exit")





# --- radar: tocar un sistema de ALERTAS abre su ficha ---
ALR = []
_draw_fac_b15 = draw_fac_screen




# --- COLONIZACION > AQUI: lo que se vende en la estacion donde estas ---
COLHS = {"src": None}

def _hh(here, name, key):
    return here.get(("k", key)) if key and ("k", key) in here else here.get((name or "").lower())

def col_here(d):
    """{nombre o ("k", clave): [nombre, existencias, precio, falta, clave]} de la estacion donde estas atracado."""
    d = d or {}
    st = d.get("station") or {}
    COLHS.update(src=None, st=st.get("name"), mt=0)
    if not d.get("Flags", 0) & 1 or not st.get("mid"):
        return {}
    mid = str(st["mid"])
    mk = d.get("market") or {}
    out = {}
    if str(mk.get("mid")) == mid and mk.get("t"):                     # mercado del juego de esta estacion
        for r in mk.get("col") or []:
            out[(r[0] or "").lower()] = r
            if len(r) > 4 and r[4]:
                out[("k", r[4])] = r
        COLHS.update(src="juego", st=mk.get("station") or st.get("name"))
        return out
    B = d.get("colbuy") or {}
    if str(B.get("mid")) == mid and B.get("status") == "ok":           # si no, lo que dice EDSM
        for k, (stock, price) in (B.get("items") or {}).items():
            out[("k", k)] = [k, stock, price, 0, k]
        COLHS.update(src="EDSM", st=B.get("st") or st.get("name"), mt=B.get("mt") or 0)
    return out

# --- avisos de la faccion: expansion y control (se guardan para no perderlos al reiniciar) ---
EV_LIST.append(("facexp", "EXPANSIÓN DE TU FACCIÓN"))
EV_LIST.append(("facctrl", "CONTROL DE SISTEMAS"))
FST_F = os.path.join(PANEL_DIR, "faccion_estado.json")
try:
    FST = json.load(open(FST_F, encoding="utf-8"))
except Exception:
    FST = None

def fx_alert(k, title, big, lines, voz, col=RED):
    if not ev_on(k):
        return
    k0 = XA_K[0]
    try:
        XA_K[0] = k
        xa["a"] = dict(until=time.time() + 10, col=col, title=title, big=big, lines=lines)
        play("alarm" if col == RED else "ok")
        voice_say(voz)
    finally:
        XA_K[0] = k0

def fac_events(D, now):
    global FST
    SS = {n: v for n, v in (D.get("sistemas") or {}).items() if v.get("inf") and not v.get("fuera")}
    if not SS:
        return
    exp = {n: ("act" if "Expansion" in (v.get("activos") or []) else "pend" if "Expansion" in (v.get("pendientes") or []) else None)
           for n, v in SS.items()}
    ctl = {n: bool(v.get("ctrl")) for n, v in SS.items()}
    if FST is None:                                                  # primera vez: se apunta como esta, sin avisar
        fl = [n for n, e in exp.items() if e]
        FST = {"sis": sorted(SS), "exp": exp, "ctl": ctl, "fin": 0, "orig": "",
               "fe": "act" if any(e == "act" for e in exp.values()) else "pend" if fl else None}
    else:
        # la expansion es de toda la faccion: un aviso por cambio, con el sistema de origen (el de mas influencia)
        fl = [n for n, e in exp.items() if e]
        fe = "act" if any(e == "act" for e in exp.values()) else "pend" if fl else None
        fe0 = FST.get("fe")
        orig = max(fl, key=lambda n: SS[n]["inf"]) if fl else FST.get("orig", "")
        if fe == "pend" and fe0 is None:
            fx_alert("facexp", "EXPANSIÓN EN MARCHA", orig, ["la facción se expandirá desde aquí tras el tick"], f"expansión en marcha desde {orig}", BLUE)
        elif fe == "act" and fe0 != "act":
            fx_alert("facexp", "EXPANSIÓN ACTIVA", orig, ["buscando sistema nuevo cerca"], f"expansión activa desde {orig}", BLUE)
        elif fe is None and fe0 == "act":
            FST["fin"] = now                             # ha terminado: esperamos a ver si aparece un sistema nuevo
        FST["fe"] = fe
        if fl:
            FST["orig"] = orig
        nuevos = [n for n in SS if n not in FST["sis"]]
        for n in nuevos:
            if FST.get("fin") or FST.get("fe"):
                fx_alert("facexp", "¡EXPANSIÓN CONSEGUIDA!", n, [f"ahora estáis en {n}" + (f" (desde {FST['orig']})" if FST.get("orig") else "")],
                         f"expansión conseguida, ahora estáis en {n}", GREEN)
                FST["fin"] = 0
            else:
                fx_alert("facexp", "NUEVO SISTEMA", n, ["vuestra facción aparece en este sistema"], f"nuevo sistema, {n}", GREEN)
        if FST.get("fin") and now - FST["fin"] > 3 * 86400:
            fx_alert("facexp", "EXPANSIÓN SIN ÉXITO", FST.get("orig") or "", ["no ha aparecido ningún sistema nuevo en 3 días"], "la expansión no ha tenido éxito")
            FST["fin"] = 0
        for n, c in ctl.items():
            c0 = FST["ctl"].get(n)
            if c and c0 is False:
                fx_alert("facctrl", "¡TOMÁIS EL CONTROL!", n, [f"{SS[n]['inf']:.1f} % de influencia".replace(".", ",")], f"tomáis el control de {n}", GREEN)
            elif not c and c0:
                fx_alert("facctrl", "PERDÉIS EL CONTROL", n, [f"ahora controla {SS[n].get('ctrl_n') or SS[n].get('segunda') or 'otra facción'}"], f"perdéis el control de {n}")
        FST.update(sis=sorted(set(FST["sis"]) | set(SS)), exp=exp, ctl=ctl)
    try:
        json.dump(FST, open(FST_F, "w", encoding="utf-8"), ensure_ascii=False)
    except OSError:
        pass

FWS = {"t": 0}



# ---------- v1.0 beta 16 ----------
# --- memoria: pocas reservas de malloc y devolver lo libre (EMITIR copiaba 4 MB por fotograma en muchos hilos) ---
def _libc():
    import ctypes
    try:
        return ctypes.CDLL("libc.so.6")
    except OSError:
        return None

_LC = _libc()
try:
    if _LC is not None:
        _LC.mallopt(-8, 2)                              # M_ARENA_MAX = 2
except Exception:
    pass
IS_PI3 = False
try:
    IS_PI3 = "Pi 3" in open("/proc/device-tree/model").read()
except OSError:
    pass

def mem_rss_pct():
    try:
        rss = int(open("/proc/self/statm").read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
        tot = int(next(l for l in open("/proc/meminfo") if l.startswith("MemTotal")).split()[1]) * 1024
        return 100.0 * rss / tot
    except Exception:
        return 0.0

def mem_loop():
    warned = 0
    while True:
        time.sleep(30)
        try:
            if _LC is not None:
                _LC.malloc_trim(0)                      # devuelve al sistema la memoria libre
        except Exception:
            pass
        p = mem_rss_pct()
        if p > 60 and cfg.get("stream"):
            cfg["stream"] = False
            plog(f"EMITIR apagado: el panel usaba el {p:.0f} % de la RAM")
            set_alert("EMITIR APAGADO", f"el panel usaba el {p:.0f} % de la RAM · vuelve a encenderlo en AJUSTES", RED, 10)
        elif p > 75 and time.time() - warned > 600:
            warned = time.time()
            plog(f"Memoria del panel: {p:.0f} %")

threading.Thread(target=mem_loop, daemon=True, name="memoria").start()

# --- EMITIR: menos fotogramas en la Pi 3 y mas pequenos ---
_SNAP = {"t": 0}

def stream_snap(small):
    if not cfg.get("stream") or stream["clients"] <= 0:
        return
    now = time.time()
    if now - _SNAP["t"] < (0.2 if IS_PI3 else 0.1):     # 5 imagenes/s en la Pi 3, 10 en las demas
        return
    _SNAP["t"] = now
    with stream_lock:
        hi = panel_hi() if cfg.get("sharp") else None
        src = hi if hi is not None else small
        big = BIG["surf"] if BIG.get("fb") and BIG.get("surf") is not None else None
        if IS_PI3:
            sc = lambda S_: pygame.transform.scale(S_, (S_.get_width() * 3 // 4, S_.get_height() * 3 // 4)) if S_.get_width() > 800 else S_.copy()
            stream["small"] = sc(src)
            stream["big"] = sc(big) if big is not None else None
        else:
            stream["small"] = src.copy()
            stream["big"] = big.copy() if big is not None else None
        stream["seq"] += 1

# --- altimetro de cinta con velocidad vertical ---
MENU[137] = "ALTÍMETRO"
TABS[0].append((137, "ALTÍMETRO"))
ALTH = deque(maxlen=40)                                 # (hora, altura)

def alt_now(d):
    """Altura (m) si el juego la da y toca mostrarla; si no, None."""
    d = d or {}
    fl, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    alt = (d.get("live") or {}).get("alt")
    if alt is None or not fl & (1 << 21) or f2 & 1:     # sin coordenadas planetarias o a pie: nada
        return None
    if fl & (1 << 26) and not cfg.get("alt_srv", False):
        return None                                      # en el SRV solo si se ha activado
    return alt

def alt_vs():
    if len(ALTH) < 2:
        return None
    t1, a1 = ALTH[-1]
    old = [(t, a) for t, a in ALTH if t1 - t <= 3]
    t0, a0 = old[0]
    return (a1 - a0) / (t1 - t0) if t1 - t0 >= 0.5 else None

def alt_track(d, now):
    alt = alt_now(d)
    if alt is None:
        ALTH.clear(); return
    if not ALTH or ALTH[-1][1] != alt or now - ALTH[-1][0] > 1:
        ALTH.append((now, alt))


def view_alt(surf, d, flags, now):
    r = pygame.Rect(4, TOP + 2, W - 8, H - TOP - 6)
    draw_alt(surf, r, d, now)
    b = pygame.Rect(W - 112, H - 30, 106, 24)
    on = cfg.get("alt_srv", False)
    draw_button(surf, b, "SRV: " + ("SÍ" if on else "NO"), None, F["small"], filled=on, compact=True)
    ALT_SRV_R[0] = b

ALT_SRV_R = [pygame.Rect(0, 0, 0, 0)]
VIEWS[137] = view_alt

# pantalla grande: el altimetro sustituye a una de las 4 cuando hay altura
BIG_SETS["APROXIMACIÓN + ALTÍMETRO"] = [100, 72, 73, 137]
BIG_SETS["SUPERFICIE + ALTÍMETRO"] = [100, 73, 137, 150]
BIG_SETS["PUERTO PLANETARIO"] = [100, 8, 127, 137]







# ---------- v1.0 beta 17 ----------
BG_DOCK_DARK = 80                                        # brillo de la foto de fondo al atracar (antes 55)

# --- COMBATE por la musica: no al despegar ni dentro de la estacion; «Combat_Unknown» solo si hay pelea de verdad ---
CMB = {"att": 0}





# ---------- v1.0 beta 18 ----------
# --- arrastrar el dedo en la lista de SISTEMAS CONTROLADOS (radar) ---
DRAG = {"on": False, "p0": None, "last": None}
CTL_LIST = {"r": None, "off": 0, "max": 0, "seen": 0}
CTL_ROWS = []

def _to_panel(p):
    """Toque de la HDMI (0..1) a coordenadas del panel, si se esta viendo el panel."""
    if not hdmi_panel():
        return None
    bw, bh = BIG["w"] or 1024, BIG["h"] or 600
    sc = min(bw / W, bh / H)
    ox, oy = (bw - W * sc) / 2, (bh - H * sc) / 2
    return ((p[0] * bw - ox) / sc, (p[1] * bh - oy) / sc)

def drag_move(p0, p):
    a, b = _to_panel(p0) if p0 else None, _to_panel(p)
    if not a or not b:
        return
    r = CTL_LIST.get("r")
    radar_on = ui.get("view") == 77 or (ui.get("idle_on") and IDLE_MODE.get("m") == "fac")
    if not r or not radar_on or not r.collidepoint(a) or not CTL_LIST.get("max"):
        return
    if not DRAG["on"]:
        if abs(b[1] - a[1]) < 12:                       # menos de 12 px: todavia es un toque
            return
        DRAG.update(on=True, last=b[1], off0=CTL_LIST.get("off", 0), y0=a[1])
    CTL_LIST["off"] = int(max(0, min(CTL_LIST["max"], DRAG["off0"] - (b[1] - DRAG["y0"]))))
    CTL_LIST["seen"] = time.time()
    ui["idle_skip"] = ui.get("idle_skip", 0)
    TAP_EV.set()

def drag_end():
    DRAG.update(on=False)
    TAP_EV.set()



# --- ACTIVIDAD GALACTICA: fondo con brillo y nebulosa calida, vistas GALAXIA / COLONIA / SOL ---
ACT_MODE = ["gal"]
ACT_MODES = [("gal", "GALAXIA"), ("col", "COLONIA"), ("sol", "SOL")]
ACT_BTN = [pygame.Rect(236 + i * 58, 29, 54, 18) for i in range(3)]
_act_view_b18 = act_view
_GBG = {}

def act_view_b18(M, mode):
    if mode in ("col", "sol"):
        cx_, cz_, hw = (-9530, 19808, 1800) if mode == "col" else (0, 0, 350)
        X0, X1, Z0, Z1 = cx_ - hw, cx_ + hw, cz_ - hw * 0.87, cz_ + hw * 0.87
        sc = min(M.w / (X1 - X0), M.h / (Z1 - Z0))
        cx, cz = (X0 + X1) / 2, (Z0 + Z1) / 2
        return (lambda x, z: (M.centerx + (x - cx) * sc, M.centery - (z - cz) * sc)), sc
    return _act_view_b18(M, mode != "zona")

act_view = act_view_b18

def act_bg(surf, M, mode):
    real, rr = (surf.real, surf._r(M)) if type(surf).__name__ == "ScaledSurf" else (surf, pygame.Rect(M))
    key = (rr.w, rr.h, mode)
    if key not in _GBG:
        import random as _r
        bg = pygame.Surface(rr.size); bg.fill(BLACK)
        loc = pygame.Rect(0, 0, rr.w, rr.h)
        pt, sc = act_view_b18(loc, mode)
        if mode == "gal":
            neb = pygame.Surface(rr.size, pygame.SRCALPHA)
            rad = max(4, int(rr.w / 40))
            for x, z, b in gal_points()[::3]:
                px, py = pt(x, z)
                if 0 <= px < rr.w and 0 <= py < rr.h:
                    pygame.draw.circle(neb, (150, 80, 25, 9), (int(px), int(py)), rad)
            bg.blit(neb, (0, 0))
            cx, cy = pt(25, 25900)
            glow = pygame.Surface(rr.size, pygame.SRCALPHA)
            R = int(rr.w * 0.16)
            for k_ in range(R, 0, -max(1, R // 40)):
                pygame.draw.circle(glow, (255, 190, 120, int(70 * (1 - k_ / R) ** 1.6)), (int(cx), int(cy)), k_)
            bg.blit(glow, (0, 0))
            for x, z, b in gal_points():
                px, py = pt(x, z)
                if 0 <= px < rr.w and 0 <= py < rr.h:
                    bb = min(255, int(b * 2.0))
                    bg.fill((bb, int(bb * 0.75), int(bb * 0.55)), (int(px), int(py), 2, 2))
        else:                                            # de cerca: campo de estrellas y una neblina suave
            rnd = _r.Random(11 if mode == "col" else 7)
            glow = pygame.Surface(rr.size, pygame.SRCALPHA)
            for k_ in range(18):
                gx, gy, gr = rnd.randrange(rr.w), rnd.randrange(rr.h), rnd.randrange(rr.w // 8, rr.w // 3)
                pygame.draw.circle(glow, (150, 80, 25, 7) if mode == "col" else (120, 70, 30, 6), (gx, gy), gr)
            bg.blit(glow, (0, 0))
            for k_ in range(rr.w * rr.h // 900):
                b = rnd.randint(40, 170)
                bg.fill((b, int(b * 0.8), int(b * 0.65)), (rnd.randrange(rr.w), rnd.randrange(rr.h), 1 + (b > 150), 1 + (b > 150)))
        _GBG[key] = bg
    real.blit(_GBG[key], rr.topleft)

def draw_act_screen(surf, now):
    ACT["want"] = now
    surf.fill(BLACK)
    fixed = IDLEHOLD["m"] == "act" or ui.get("view") == 78
    mode = ACT_MODE[0] if fixed else ("gal", "sol", "col")[int(now // 10) % 3]   # en espera: 10 s cada vista
    put(surf, F["big"], "ACTIVIDAD GALÁCTICA", (10, 6), ORANGE)
    put(surf, F["small"], "en directo desde EDDN" if ACT["on"] else "conectando con EDDN…" if act_ok() else "falta python3-zmq en la Pi",
        (10, 32), DIM if act_ok() else RED, 220)
    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 56, 8), ORANGE, anchor="topright")
    for i, (k, lab) in enumerate(ACT_MODES):
        b = ACT_BTN[i]; sel = k == mode
        pygame.draw.rect(surf, ORANGE if sel else BLACK, b, border_radius=4)
        pygame.draw.rect(surf, ORANGE, b, 1, border_radius=4)
        put(surf, F["tiny"], lab, b.center, BLACK if sel else ORANGE, b.w - 4, anchor="center")
    pygame.draw.line(surf, ORANGE, (6, 50), (W - 6, 50), 1)
    M = pygame.Rect(6, 54, 300, 262)
    act_bg(surf, M, mode)
    pygame.draw.rect(surf, DIM, M, 1, border_radius=4)
    pt, sc = act_view_b18(M, mode)
    old = surf.get_clip(); surf.set_clip(M)
    marks = {"gal": (("SOL", 0, 0), ("COLONIA", -9530, 19808), ("SAG A*", 25, 25900)),
             "col": (("COLONIA", -9530, 19808),), "sol": (("SOL", 0, 0),)}[mode]
    for n, x, z in marks:
        px, py = pt(x, z); pygame.draw.circle(surf, DIM, (int(px), int(py)), 3, 1)
        put(surf, F["tiny"], n, (int(px) + 5, int(py) - 6), (200, 160, 110))
    if mode == "sol":                                    # vuestros sistemas en naranja
        used = []
        for n, v in sorted(((FACD["data"] or {}).get("sistemas") or {}).items(), key=lambda kv: -(kv[1].get("inf") or 0)):
            if v.get("pos") and None not in v["pos"] and not v.get("fuera") and v.get("inf"):
                px, py = pt(v["pos"][0], v["pos"][2])
                if not M.collidepoint(px, py):
                    continue
                pygame.draw.circle(surf, ORANGE if v.get("ctrl") else (120, 80, 30), (int(px), int(py)), 3, 0 if v.get("ctrl") else 1)
                if v.get("ctrl"):
                    nm = n if len(n) <= 14 else n[:13] + "…"
                    lr = pygame.Rect(int(px) + 5, int(py) - 6, tw_(F["tiny"], nm), 12)
                    if not M.contains(lr):
                        lr.right = int(px) - 5
                    if M.contains(lr) and not any(lr.colliderect(u) for u in used):
                        used.append(lr); put(surf, F["tiny"], nm, lr.topleft, (200, 140, 60))
    for x, z, t, mine in list(ACT["pings"]):
        age = now - t
        if age > 1.6 or age < 0:
            continue
        px, py = pt(x, z)
        if not M.collidepoint(px, py):
            continue
        col = ORANGE if mine else (90, 200, 255)
        f_ = max(0.0, 1 - age / 1.6)
        pygame.draw.circle(surf, tuple(int(c * f_) for c in col), (int(px), int(py)), int(2 + age * 10), 1)
        if age < 0.4:
            pygame.draw.circle(surf, col, (int(px), int(py)), 2)
    act_hit_draw(surf, M, pt, now)
    surf.set_clip(old)
    X, y = 314, 58
    j = list(ACT["jumps"])                               # copia: el hilo de EDDN sigue añadiendo mientras se dibuja
    pm = len(j) - bisect.bisect_left(j, now - 60)        # van en orden de llegada
    cm = sum(1 for t in list(ACT["uids"].values()) if now - t < 300)
    put(surf, F["small"], "SALTOS POR MINUTO", (X, y), DIM); y += 14
    put(surf, F["num"], str(pm), (W - 8, y), BLUE, anchor="topright"); y += 44
    put(surf, F["small"], "COMANDANTES (5 MIN)", (X, y), DIM); y += 14
    put(surf, F["big"], str(cm), (W - 8, y), WHITE, anchor="topright"); y += 30
    hoyk = time.strftime("%Y-%m-%d", time.gmtime())
    ent = sum(((v.get("trafico") or {}).get(hoyk, 0)) for v in ((FACD["data"] or {}).get("sistemas") or {}).values())
    put(surf, F["small"], "TUS SISTEMAS HOY", (X, y), DIM); put(surf, F["big"], str(ent), (W - 8, y + 10), ORANGE, anchor="topright")
    nv = ACT_DAY.get(hoyk, 0)
    put(surf, F["tiny"], f"comandantes · {nv} salto{'' if nv == 1 else 's'} visto{'' if nv == 1 else 's'}", (X, y + 40), DIM, W - X - 8); y += 54
    pygame.draw.line(surf, DIM, (X, y), (W - 6, y)); y += 4
    put(surf, F["small"], "ÚLTIMOS SALTOS", (X, y), DIM); y += 15
    for nm, mine, t in list(ACT["feed"])[:5]:
        put(surf, F["tiny"], nm, (X, y), ORANGE if mine else WHITE, 120)
        put(surf, F["tiny"], f"{max(0, int(now - t))} s", (W - 8, y), DIM, anchor="topright"); y += 13

# --- COMBATE: no al despegar (1 min tras cualquier despegue) ni «te atacan» al atracar ---
UNDK = {"t": 0, "dock": False}




# --- recompensas sin cobrar: boton BORRAR (en 11 DIA) ---
LEDB = {"r": None, "sure": 0}
_view11_b18 = VIEWS[11]

def view11_b18(surf, d, flags, now):
    _view11_b18(surf, d, flags, now)
    LEDB["r"] = None
    if ui.get("sesstab"):
        return
    led = ((d or {}).get("footcz") or {}).get("led") or {}
    if not led.get("cr"):
        return
    r = pygame.Rect(W - 104, H - 56, 98, 22)
    sure = time.time() < LEDB["sure"]
    draw_button(surf, r, "¿SEGURO?" if sure else "BORRAR", None, F["small"], filled=sure, compact=True)
    LEDB["r"] = r

VIEWS[11] = view11_b18

def led_clear():
    pc = pc_addr()
    if not pc:
        set_alert("NO SÉ LA IP DEL PC", "el sender no está enviando", RED, 3); return
    try:
        so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        so.sendto(b"ELITEPANEL-LEDGERCLR", (pc, 5006)); so.close()
        set_alert("RECOMPENSAS BORRADAS", "lo pendiente de cobrar vuelve a cero (sender v1.0b12)", GREEN, 4, kind="info")
    except OSError as e:
        set_alert("NO SE PUDO BORRAR", str(e)[:40], RED, 3)






# ---------- v1.0 beta 19 ----------
# --- voz: las abreviaturas, completas ---


# --- velocidad cerca de un planeta (con latitud, longitud y radio que manda el sender) ---
SPDH = deque(maxlen=40)                                  # (hora, lat, lon, alt)
SPD = {"gs": None, "vmax": {}}
SHIP_VMAX = {"sidewinder": 320, "eagle": 350, "hauler": 270, "adder": 300, "viper": 400, "cobra": 400, "vulture": 355,
             "asp": 340, "python": 300, "type-6": 300, "type6": 300, "type-7": 250, "type7": 250, "type-8": 260, "type8": 260,
             "type-9": 200, "type9": 200, "type-10": 220, "type10": 220, "anaconda": 250, "cutter": 320, "corvette": 260,
             "krait": 330, "mamba": 420, "fer-de-lance": 400, "ferdelance": 400, "chieftain": 330, "challenger": 300,
             "crusader": 300, "dolphin": 350, "orca": 380, "beluga": 290, "keelback": 300, "courier": 380, "clipper": 380,
             "diamondback": 340, "panther": 230, "mandalay": 330, "corsair": 330, "kestrel": 400, "python mk ii": 330}

def _geo(d):
    b = (d or {}).get("bio") or {}
    return b.get("lat"), b.get("lon"), b.get("R"), b.get("hdg")

def spd_track(d, now):
    lat, lon, R, hdg = _geo(d)
    alt = ((d or {}).get("live") or {}).get("alt")
    if lat is None or lon is None or not R:
        SPDH.clear(); SPD["gs"] = None; return
    if not SPDH or (SPDH[-1][1], SPDH[-1][2]) != (lat, lon) or now - SPDH[-1][0] > 1:
        SPDH.append((now, lat, lon, alt or 0))
    old = [p for p in SPDH if SPDH[-1][0] - p[0] <= 2.5]
    t0, a0, o0, h0 = old[0]
    t1, a1, o1, h1 = SPDH[-1]
    if t1 - t0 < 0.5:
        return
    p0, p1 = math.radians(a0), math.radians(a1)
    dl = math.radians(o1 - o0)
    c = math.sin((p1 - p0) / 2) ** 2 + math.cos(p0) * math.cos(p1) * math.sin(dl / 2) ** 2
    dist = 2 * (R + max(0, h1)) * math.asin(min(1.0, math.sqrt(c)))
    SPD["gs"] = dist / (t1 - t0)

def ship_vmax(d):
    sh = (((d or {}).get("live") or {}).get("ship") or {})
    n = (sh.get("ship") or "").lower()
    v = next((v for k, v in sorted(SHIP_VMAX.items(), key=lambda kv: -len(kv[0])) if k in n), 400)
    return max(200, int(math.ceil(v * 1.25 / 100.0)) * 100)

def in_srv(d):
    return bool((d or {}).get("Flags", 0) & (1 << 26))

def srv_name(d):
    t = ((d or {}).get("srvtype") or "SRV").upper()
    return "RHINO" if "RHINO" in t else t

def draw_arc(surf, cx, cy, R, v, vmax, step, bands, label, now, sub=None):
    a0, a1 = math.radians(150), math.radians(390)
    ang = lambda x: a0 + (a1 - a0) * min(1.0, max(0.0, x / vmax))
    pygame.draw.circle(surf, (14, 14, 16), (cx, cy), R + 3)
    for lo, hi, col in bands:
        n_ = 24
        for k in range(n_ + 1):
            x = lo + (hi - lo) * k / n_
            a = ang(x)
            pygame.draw.line(surf, col, (cx + (R - 2) * math.cos(a), cy + (R - 2) * math.sin(a)), (cx + (R - 6) * math.cos(a), cy + (R - 6) * math.sin(a)), 2)
    k = 0
    while k <= vmax + 1e-6:
        a = ang(k)
        pygame.draw.line(surf, WHITE, (cx + (R - 7) * math.cos(a), cy + (R - 7) * math.sin(a)), (cx + (R - 12) * math.cos(a), cy + (R - 12) * math.sin(a)), 1)
        put(surf, F["tiny"], str(int(k)), (int(cx + (R - 20) * math.cos(a)), int(cy + (R - 20) * math.sin(a))), WHITE, anchor="center")
        k += step
    put(surf, F["tiny"], label, (cx, cy - R // 3), DIM, anchor="center")
    if v is not None:
        a = ang(v)
        pygame.draw.line(surf, ORANGE, (cx, cy), (cx + (R - 9) * math.cos(a), cy + (R - 9) * math.sin(a)), 3)
        put(surf, F["big"], f"{v:.0f}", (cx, cy + R // 2), ORANGE, anchor="center")
    else:
        put(surf, F["small"], "—", (cx, cy + R // 2), DIM, anchor="center")
    pygame.draw.circle(surf, (60, 60, 60), (cx, cy), 4)
    put(surf, F["tiny"], "m/s" if sub is None else sub, (cx, cy + R // 2 + 14), DIM, anchor="center")

def draw_hdg_compass(surf, cx, cy, R, hdg):
    pygame.draw.circle(surf, (14, 14, 16), (cx, cy), R); pygame.draw.circle(surf, (80, 80, 86), (cx, cy), R, 1)
    for i, lab in enumerate("NESO"):
        a = math.radians(i * 90 - 90)
        put(surf, F["small"], lab, (int(cx + (R - 11) * math.cos(a)), int(cy + (R - 11) * math.sin(a))), RED if lab == "N" else WHITE, anchor="center")
    if hdg is not None:
        a = math.radians(hdg - 90)
        pygame.draw.line(surf, ORANGE, (cx, cy), (cx + (R - 20) * math.cos(a), cy + (R - 20) * math.sin(a)), 3)
        put(surf, F["tiny"], f"RUMBO {int(hdg) % 360:03d}°", (cx, cy + R + 8), DIM, anchor="center")



# --- aviso: bajando rapido cerca del suelo (solo en la nave) ---
EV_LIST.append(("suelo", "BAJANDO RÁPIDO CERCA DEL SUELO"))
SUELO = {"t": 0}

def suelo_watch(d, now):
    alt, vs = alt_now(d), alt_vs()
    fl = (d or {}).get("Flags", 0)
    if alt is None or vs is None or in_srv(d) or fl & 3 or fl & (1 << 29):
        return
    if (alt < 250 and vs < -35) or (alt < 60 and vs < -15):
        if now - SUELO["t"] > 12 and ev_on("suelo"):
            SUELO["t"] = now
            k0 = XA_K[0]
            try:
                XA_K[0] = "suelo"
                set_alert("BAJANDO RÁPIDO CERCA DEL SUELO", f"{alt:.0f} m · {vs:.0f} m/s", RED, 4)
                play("alarm")
                voice_say("cuidado, bajas rápido cerca del suelo")
            finally:
                XA_K[0] = k0

# --- caja negra: los ultimos 60 s de altura y velocidades, al LOG si te destruyen ---
CAJA = deque(maxlen=200)

def caja_track(d, now):
    alt = ((d or {}).get("live") or {}).get("alt")
    if alt is None or ((d or {}).get("bio") or {}).get("lat") is None:
        return
    if not CAJA or now - CAJA[-1][0] >= 0.5:
        CAJA.append((now, alt, alt_vs(), SPD.get("gs"), (d or {}).get("Flags", 0)))

def caja_dump(why):
    now = time.time()
    pts = [p for p in CAJA if now - p[0] <= 60]
    if not pts:
        plog(f"CAJA NEGRA ({why}): sin datos de altura en el último minuto"); return
    plog(f"CAJA NEGRA ({why}): últimos {now - pts[0][0]:.0f} s (segundos antes · altura · vertical · suelo)")
    sel = pts[::max(1, len(pts) // 30)] + [pts[-1]]
    for t, alt, vs, gs, fl in sel:
        plog(f"  -{now - t:4.1f} s · {alt:7.0f} m · " + (f"{vs:+5.0f}" if vs is not None else "   ? ") + " m/s · "
             + (f"{gs:5.0f}" if gs is not None else "   ? ") + " m/s" + (" · radio medio" if fl & (1 << 29) else ""))

# --- repetidos: avisos iguales seguidos una sola vez; en el LOG, una linea con ×N ---
REPN = {"k": None, "t": 0, "n": 0}


PLR = {"m": None, "t": 0, "n": 0}

def plog(*a, **k):
    msg = " ".join(str(x) for x in a)
    now = time.time()
    if msg == PLR["m"] and now - PLR["t"] < 5:
        PLR["n"] += 1; PLR["t"] = now; return
    if PLR["n"]:
        plog_base(f"  (repetido ×{PLR['n'] + 1})")
    PLR.update(m=msg, t=now, n=0)
    plog_base(*a, **k)

# pantalla grande: tambien en el SRV / Rhino (sustituye al MAPA)
BIG_SETS["SUPERFICIE + VELOCÍMETRO"] = [100, 73, 5, 137]


MENU[137] = "ALTÍMETRO Y VELOCIDAD"




# ---------- v1.0 beta 20: tras cargar la partida, 4 CUADROS ----------
LGB = {"t": 0}





