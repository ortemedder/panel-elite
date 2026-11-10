#!/usr/bin/env python3
# Parche v1.0 beta 15 (desde la beta 14): reloj de lamas para el atraque (9:55) y la salida de la estacion (6 min),
# banda DENTRO DE LA ESTACION y cambio a EN VIVO al salir, tocar ALERTAS del radar abre la ficha, avisos de expansion
# y de control de sistemas, y COLONIZACION > AQUI con los datos de la estacion donde estas. Necesita el sender v1.0b11.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def draw_flip" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b14 ', s):
    sys.exit("Este parche es para la v1.0 beta 14")
shutil.copy(P, P + ".bak100b14")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# radar: guarda donde queda cada alerta para poder tocarla
rep('''        pygame.draw.rect(surf, RED if blink else (120, 0, 0), box, 2, border_radius=6)
        put(surf, F["small"], "ALERTAS", (X + 8, y + 3), RED)
        yy = y + 18
        for v in war[:4]:
''', '''        pygame.draw.rect(surf, RED if blink else (120, 0, 0), box, 2, border_radius=6)
        put(surf, F["small"], "ALERTAS", (X + 8, y + 3), RED)
        yy = y + 18
        for v in war[:4]:
            ALR.append((pygame.Rect(X, yy - 2, box.w, 30), v["sys"]))
''')
# COLONIZACION > AQUI: por clave interna y con los datos de la estacion donde estas
rep('''            sold = name.lower() in here and real > 0''', '''            sold = _hh(here, name, key) is not None and real > 0''')
rep('''        vis = [t for t in rows if t[5] > 0 and t[0].lower() in here]
        if not here and not mk.get("col"):
            put(surf, F["small"], "abre el mercado de esta estación para ver qué se vende", (W // 2, y + 40), DIM, W - 16, anchor="center")
        elif not vis:
            put(surf, F["btn"], "aquí no se vende nada de lo que falta", (W // 2, y + 40), RED, W - 16, anchor="center")
        put(surf, F["tiny"], f"EN {(mk.get('station') or 'ESTA ESTACIÓN').upper()}", (8, y), DIM, W - 16); y += 14
        for name, key, req, prov, inb, real in vis[:13]:
            r_ = here[name.lower()]''', '''        vis = [t for t in rows if t[5] > 0 and _hh(here, t[0], t[1]) is not None]
        src = COLHS.get("src")
        stn = (COLHS.get("st") or "ESTA ESTACIÓN").upper()
        if not src:
            put(surf, F["small"], "atraca y abre el mercado para ver qué se vende aquí", (W // 2, y + 40), DIM, W - 16, anchor="center")
        elif not vis:
            put(surf, F["btn"], "aquí no se vende nada de lo que falta", (W // 2, y + 40), RED, W - 16, anchor="center")
        lab = f"EN {stn}" + (" · datos del juego" if src == "juego" else
                             " · según EDSM" + (f", hace {_hace(now - COLHS['mt'])}" if COLHS.get("mt") else "") + " · abre el mercado para ver precios exactos" if src == "EDSM" else "")
        put(surf, F["tiny"], lab, (8, y), DIM if src != "EDSM" else BLUE, W - 16); y += 14
        for name, key, req, prov, inb, real in vis[:13]:
            r_ = _hh(here, name, key)''')

CODE = r'''
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

def draw_flip(surf, rect, text, col, now, key, dur=0.45):
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

def mmss(sec):
    sec = max(0, int(sec))
    return f"{min(9, sec // 60)}:{sec % 60:02d}"

def clock_col(sec, now):
    if sec < 60:
        return RED if int(now * 2) % 2 else (130, 0, 0)
    return (255, 215, 0) if sec < 120 else ORANGE

# --- reloj del atraque en ESTACION (y en ATRAQUE de la pantalla grande) ---
DOCK_SECS = 595

def dock_left(d, now):
    st = (d or {}).get("station") or {}
    if st.get("status") != "CONCEDIDO" or not st.get("gt"):
        return None
    return DOCK_SECS - (pc_now(d, now) - st["gt"])

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
EXIT_SECS = 360
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
    r = pygame.Rect(0, TOP, W, 46)
    pygame.draw.rect(surf, BLACK, r)
    pygame.draw.rect(surf, RED if left < 60 else ORANGE, r, 2, border_radius=6)
    put(surf, F["btn"], "DENTRO DE LA ESTACIÓN", (10, r.y + 5), ORANGE, W - 170)
    put(surf, F["small"], "sal por la ranura · " + (x.get("st") or ""), (10, r.y + 26), DIM, W - 170)
    draw_flip(surf, pygame.Rect(W - 150, r.y + 4, 142, 38), mmss(left), clock_col(left, now), now, "exit")

_render_b15 = render

def render(surf):
    r_ = _render_b15(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        now = time.time()
        if d is not None and now - rx < 5:
            x = d.get("exitst") or {}
            if x.get("out") and EXW["out"] != x["out"]:
                if EXW["out"] is not None and auto_on("salida") and not ui.get("idle_on") and now - rx < 5:
                    ui["view"] = 100
                    plog("Salida de la estación (" + str(x.get("why")) + "): EN VIVO")
                EXW["out"] = x["out"]
            elif EXW["out"] is None:
                EXW["out"] = x.get("out") or 0
            if not ui.get("idle_on"):
                draw_exit_band(surf, d, now)
    except Exception as e:
        log_exc("salida estación", e)
    return r_

_render_big_b15 = render_big

def render_big():
    _render_big_b15()
    try:
        S = BIG.get("surf")
        if S is None or hdmi_panel():
            return
        with lock:
            d = state["data"]
        now = time.time()
        left, x = exit_left(d, now)
        if left is None:
            return
        bw = BIG["w"]
        box = pygame.Rect(bw // 2 - 400, 54, 800, 150)
        pygame.draw.rect(S, BLACK, box, border_radius=12)
        pygame.draw.rect(S, RED if left < 60 else ORANGE, box, 3, border_radius=12)
        fb, fs = BIG.get("fonts") or (pygame.font.Font(None, 40), pygame.font.Font(None, 26))
        S.blit(fb.render("DENTRO DE LA ESTACIÓN", True, ORANGE), (box.x + 20, box.y + 18))
        S.blit(fs.render("sal por la ranura · " + (x.get("st") or ""), True, DIM), (box.x + 20, box.y + 60))
        draw_flip(S, pygame.Rect(box.right - 290, box.y + 16, 270, 118), mmss(left), clock_col(left, now), now, "exitbig")
    except Exception as e:
        log_exc("salida pantalla grande", e)

# --- radar: tocar un sistema de ALERTAS abre su ficha ---
ALR = []
_draw_fac_b15 = draw_fac_screen

def draw_fac_screen(surf, now):
    ALR.clear()
    _draw_fac_b15(surf, now)

_on_tap_b15 = on_tap

def on_tap(x, y):
    v = ui.get("view")
    if (v == 77 or (ui.get("idle_on") and IDLE_MODE["m"] == "fac")) and not FULL_BACK.inflate(10, 10).collidepoint(x, y) \
            and not hold_rect("fac").inflate(10, 10).collidepoint(x, y) and not (ui.get("alert") and time.time() < ui["alert"]["until"]):
        for r, n in ALR:
            if r.collidepoint(x, y):
                ui["idle_skip"] = time.time() + 60
                ui["facsys"] = n; ui["facback"] = 77; ui["view"] = 194; TAP_EV.set(); return
    _on_tap_b15(x, y)

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

_fac_watch_b15 = fac_watch
FWS = {"t": 0}

def fac_watch(now):
    _fac_watch_b15(now)
    D = FACD["data"]
    if D and (D.get("t") or 0) != FWS["t"]:                         # solo cuando llegan datos nuevos
        FWS["t"] = D.get("t") or 0
        try:
            fac_events(D, now)
        except Exception as e:
            log_exc("faccion expansion/control", e)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 14''', '''# Novedades v1.0 beta 15
- Reloj de lamas (como los paneles de aeropuerto, sin sonido): TIEMPO PARA ATRACAR desde 9:55 al concederte el atraque (en ESTACIÓN y en ATRAQUE de la pantalla grande). Naranja, amarillo por debajo de 2 min y rojo parpadeando en el último.
- Al despegar dentro de una estación con hangar (Coriolis, Dodecaedro, Orbis, Ocellus, Bernal, base de asteroide): banda DENTRO DE LA ESTACIÓN con la cuenta de 6 minutos (también en 4 CUADROS). Al salir por la ranura se quita y se abre EN VIVO (CAMBIO AUTO > SALIDA DE LA ESTACIÓN).
- Radar de la facción: tocar un sistema de ALERTAS abre su ficha (y VOLVER lleva al radar).
- Avisos de la facción: EXPANSIÓN EN MARCHA / ACTIVA, ¡EXPANSIÓN CONSEGUIDA! (cuando aparece un sistema nuevo) o SIN ÉXITO (3 días sin sistema nuevo), ¡TOMÁIS EL CONTROL! y PERDÉIS EL CONTROL. Se apagan en ALERTAS.
- COLONIZACIÓN > AQUÍ: usa la estación donde estás atracado (los datos del juego si has abierto su mercado; si no, EDSM, y lo dice) y compara las mercancías por su nombre interno.
- Necesita el sender v1.0b11.
# Novedades v1.0 beta 14''')
rep('    ("1.0b14", ', '    ("1.0b15", "Relojes de lamas (atraque y salida), salida de la estación, ALERTAS del radar, avisos de expansión y control, AQUÍ arreglado"),\n    ("1.0b14", ')
s = re.sub(r'PANEL_VER = "v1\.0b14 [^"]*"', 'PANEL_VER = "v1.0b15 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 15  (copia en " + P + ".bak100b14)")
