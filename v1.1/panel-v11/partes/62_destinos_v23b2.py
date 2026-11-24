# Panel Elite v2.3 · parte 62: v2.3b2 — DESTINOS EN EL PLANETA
#   - DESTINO RÁPIDO: el panel guarda las coordenadas de cada puerto o asentamiento planetario que conoce (cuando el
#     juego las da al acercarte, o al atracar en él) en sitios_planeta.json. La próxima vez que lo fijes en el juego,
#     la ESFERA y la FLECHA salen desde la órbita aunque el juego aún no haya dado sus coordenadas.
#   - 3 NAVEGACIÓN > pestaña PLANETA (182): destino actual, sitios conocidos de este planeta (tocar = ir), botones
#     A MANO, GUARDAR AQUÍ, QUITAR DESTINO y NOTAS.
#   - A MANO (183): teclado para escribir LATITUD y LONGITUD (puntos de Canonn, guardianes, quedadas). IR la pone de
#     destino y la guarda en NOTAS DE VIAJE (tus favoritos).
#   - FAVORITOS = NOTAS DE VIAJE: en el detalle de un sitio con coordenadas, botón IR AQUÍ.
#   - PUNTO AUTOMÁTICO: guarda solo dónde aterriza tu nave y dónde despliegas el SRV (salen como puntos en el mapa).

SITIOS_FILE = os.path.join(PANEL_DIR, "sitios_planeta.json")
NP_TECLA = {"lat": "", "lon": "", "campo": "lat", "err": ""}
NP_PREV = {"fl": None}
MENU.update({182: "PLANETA", 183: "COORDENADAS A MANO"})
TABS[0].append((182, "PLANETA"))
TAB_OF[183] = 182
PARENT.update({182: 0, 183: 182})

def _sitios_load():
    try:
        with open(SITIOS_FILE, encoding="utf-8") as fh:
            s_ = json.load(fh)
        return s_ if isinstance(s_, dict) else {}
    except (OSError, ValueError):
        return {}

SITIOS = _sitios_load()
SITIOS.setdefault("auto", {})

def _sitios_save():
    try:
        tmp = SITIOS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(SITIOS, fh, ensure_ascii=False)
        os.replace(tmp, SITIOS_FILE)
    except OSError as e:
        log_exc("sitios del planeta", e)

def _sitio_k(sys_, name):
    return f"{(sys_ or '').lower()}|{(name or '').lower()}"

def sitio_aprende(sys_, name, body, lat, lon):
    if not sys_ or not name or lat is None or lon is None:
        return
    k = _sitio_k(sys_, name)
    old = SITIOS.get(k)
    if old and abs(old["lat"] - lat) < 1e-4 and abs(old["lon"] - lon) < 1e-4 and old.get("body") == body:
        return
    SITIOS[k] = {"name": name, "sys": sys_, "body": body, "lat": round(lat, 5), "lon": round(lon, 5), "t": int(time.time())}
    plog(f"PLANETA: sitio guardado {name} ({body}) {lat:.4f} / {lon:.4f}")
    _sitios_save()

def sitios_del_cuerpo(sys_, body):
    out = [v for k, v in SITIOS.items() if k != "auto" and isinstance(v, dict) and v.get("body") == body
           and (v.get("sys") or "").lower() == (sys_ or "").lower()]
    return sorted(out, key=lambda v: v.get("name") or "")

# ---------------------------------------------------------------------------------------------------------------
# destino: el manual manda; si no, el del juego; si el juego no da coordenadas, las que ya conocemos
# ---------------------------------------------------------------------------------------------------------------
_np_destino_v23b2 = np_destino

def np_destino(d):
    r = _np_destino_v23b2(d)
    if r is not None:
        return r
    d = d or {}
    D = d.get("dest") or {}
    if not D.get("name"):
        return None
    s_ = SITIOS.get(_sitio_k(d.get("system"), D["name"]))
    body = ((d.get("bio") or {}).get("body") or d.get("body") or "")
    if s_ and (not body or not s_.get("body") or s_["body"] == body):
        return {"name": s_["name"], "lat": s_["lat"], "lon": s_["lon"], "src": "memoria", "body": s_.get("body")}
    return None

# ---------------------------------------------------------------------------------------------------------------
# aprender y punto automático
# ---------------------------------------------------------------------------------------------------------------
_np_update_v23b2 = np_update

def np_update(d, now):
    d = d or {}
    try:
        fl = d.get("Flags", 0)
        b = d.get("bio") or {}
        body = b.get("body") or d.get("body")
        D = d.get("dest") or {}
        if D.get("lat") is not None and D.get("name"):
            sitio_aprende(d.get("system"), D["name"], D.get("sbody") or body, D["lat"], D["lon"])
        st = d.get("station") or {}
        if fl & 1 and fl & (1 << 21) and st.get("name") and b.get("lat") is not None:
            sitio_aprende(d.get("system"), st["name"], body, b["lat"], b["lon"])
        prev = NP_PREV["fl"]
        NP_PREV["fl"] = fl
        if prev is not None and body and b.get("lat") is not None and fl & (1 << 21):
            tag = None
            if fl & 2 and not prev & 2 and fl & (1 << 24):
                tag = "ATERRIZAJE"
            elif fl & (1 << 26) and not prev & (1 << 26):
                tag = "SRV"
            if tag:
                SITIOS["auto"][f"{(d.get('system') or '').lower()}|{body}|{tag}"] = [tag, round(b["lat"], 5), round(b["lon"], 5), int(now)]
                plog(f"PLANETA: punto {tag} en {body}")
                _sitios_save()
    except Exception as e:
        log_exc("planeta: sitios", e)
    return _np_update_v23b2(d, now)

NP_ITEMS.update({"ATERRIZAJE": ("ATERRIZAJE", GREEN), "SRV": ("SRV", BLUE)})
_np_puntos_v23b2 = np_puntos

def np_puntos(d):
    out = _np_puntos_v23b2(d)
    d = d or {}
    body = (d.get("bio") or {}).get("body") or d.get("body")
    pre = f"{(d.get('system') or '').lower()}|{body}|"
    for k, v in SITIOS["auto"].items():
        if k.startswith(pre):
            nom, col = NP_ITEMS.get(v[0], (v[0], DIM))
            if not any(n_ == "NAVE" and hav(p_, (v[1], v[2]), 1e6) < 1 for n_, p_, _ in out):
                out.append((nom, (v[1], v[2]), col))
    return out

def np_poner(name, lat, lon, body, src, sys_=None):
    NAVP.update(manual={"name": name, "lat": lat, "lon": lon, "body": body, "sys": sys_, "src": src},
                avisado=None, modo="dest")
    plog(f"PLANETA: destino {name} {lat:.4f} / {lon:.4f} ({body or 'cualquier planeta'})")
    TAP_EV.set()

def np_quitar():
    NAVP["manual"] = None
    plog("PLANETA: destino quitado")
    TAP_EV.set()

# ---------------------------------------------------------------------------------------------------------------
# 182 PLANETA (pestaña de NAVEGACIÓN)
# ---------------------------------------------------------------------------------------------------------------
NPB = {k: pygame.Rect(8 + i * 118, H - 42, 112, 36) for i, k in enumerate(("mano", "aqui", "quitar", "notas"))}
NP_FILAS = 4

def np_fila(i):
    return pygame.Rect(8, TOP + 64 + i * 37, W - 16, 34)

def view_planeta(surf, d, flags, now):
    d = d or {}
    b = d.get("bio") or {}
    body = b.get("body") or d.get("body") or ""
    yo = np_yo(d)
    dst = np_destino(d)
    y = TOP + 2
    put(surf, F["small"], "DESTINO EN EL PLANETA", (8, y), DIM)
    put(surf, F["small"], (body or "fuera de un planeta").upper(), (W - 8, y), ORANGE if yo else DIM, 250, anchor="topright")
    y += 16
    if dst:
        put(surf, F["btn"], str(dst["name"]), (8, y), NEON, W - 150)
        src = {"juego": "DEL JUEGO", "memoria": "CONOCIDO", "mano": "A MANO", "fav": "NOTAS"}.get(dst.get("src"), "")
        if yo:
            dm = hav(yo, (dst["lat"], dst["lon"]), b["R"])
            put(surf, F["btn"], np_fmt(dm), (W - 8, y), GREEN, anchor="topright")
        y += 22
        put(surf, F["small"], f"{src}  ·  {dst['lat']:.4f} / {dst['lon']:.4f}".replace(".", ","), (8, y), DIM, W - 16)
    else:
        put(surf, F["btn"], "sin destino", (8, y), DIM)
        y += 22
        put(surf, F["small"], "fija un puerto en el juego, toca un sitio o escribe coordenadas", (8, y), DIM, W - 16)
    sit = sitios_del_cuerpo(d.get("system"), body) if body else []
    notas = [n for n in trip["list"] if n.get("lat") is not None and n.get("body") == body and body]
    filas = [(s_["name"], s_["lat"], s_["lon"], "CONOCIDO") for s_ in sit] + \
            [(trip_label(n), n["lat"], n["lon"], "NOTA") for n in notas]
    ui["np_filas"] = filas[:NP_FILAS]
    for i, (nom, la, lo, tag) in enumerate(filas[:NP_FILAS]):
        r = np_fila(i)
        on = dst is not None and abs(dst["lat"] - la) < 1e-4 and abs(dst["lon"] - lo) < 1e-4
        lit = flash.get((182, i), 0) > now
        pygame.draw.rect(surf, ORANGE if on or lit else DIM, r, 2 if on else 1, border_radius=6)
        put(surf, F["btn"], nom, (r.x + 8, r.y + 7), ORANGE if on else WHITE, r.w - 170)
        txt = np_fmt(hav(yo, (la, lo), b["R"])) if yo else tag
        put(surf, F["small"], txt, (r.right - 8, r.y + 10), BLUE if yo else DIM, anchor="topright")
    if not filas and body:
        put(surf, F["small"], "aún no conozco sitios en este planeta", (8, np_fila(0).y + 8), DIM)
    for k, t in (("mano", "A MANO"), ("aqui", "GUARDAR AQUÍ"), ("quitar", "QUITAR"), ("notas", "NOTAS")):
        dim_ = (k == "aqui" and not yo) or (k == "quitar" and not NAVP.get("manual"))
        draw_button(surf, NPB[k], t, None, F["small"], lit=flash.get((182, k), 0) > now, dim=dim_)

def tap_planeta(x, y):
    with lock:
        d = state["data"] or {}
    for k, r in NPB.items():
        if not r.collidepoint(x, y):
            continue
        tap_flash((182, k))
        if k == "mano":
            NP_TECLA.update(lat="", lon="", campo="lat", err="")
            ui["view"] = 183
        elif k == "aqui":
            n = trip_here(d)
            if n.get("lat") is None:
                set_alert("SIN COORDENADAS", "el juego no da tu posición aquí", secs=2)
                return
            n["tag"] = "PLANETA"
            trip["list"].insert(0, n); trip_save()
            set_alert("SITIO GUARDADO", f"{n['lat']:.4f} / {n['lon']:.4f}  ·  en NOTAS", col=GREEN, secs=2, kind="ok")
        elif k == "quitar":
            np_quitar()
        elif k == "notas":
            ui["view"] = 128
        return
    for i, f_ in enumerate(ui.get("np_filas") or []):
        if np_fila(i).collidepoint(x, y):
            tap_flash((182, i))
            nom, la, lo, tag = f_
            body = ((d.get("bio") or {}).get("body") or d.get("body"))
            if NAVP.get("manual") and abs(NAVP["manual"]["lat"] - la) < 1e-4 and abs(NAVP["manual"]["lon"] - lo) < 1e-4:
                np_quitar()
            else:
                np_poner(nom, la, lo, body, "fav" if tag == "NOTA" else "memoria", d.get("system"))
            return

# ---------------------------------------------------------------------------------------------------------------
# 183 COORDENADAS A MANO (teclado)
# ---------------------------------------------------------------------------------------------------------------
NP_KEYS = [["7", "8", "9", "BORRA"], ["4", "5", "6", "-"], ["1", "2", "3", ","], ["0", "SIG."]]
NP_CAMPO = {"lat": pygame.Rect(8, TOP + 22, 222, 44), "lon": pygame.Rect(8, TOP + 92, 222, 44)}
NP_OK = pygame.Rect(8, H - 46, 150, 40)
NP_NO = pygame.Rect(166, H - 46, 64, 40)

def np_tecla_r(f, c):
    x0, y0, kw, kh = 240, TOP + 2, 58, (H - TOP - 6) // 4
    w_ = kw * 2 - 4 if (f == 3 and c == 1) else kw - 4
    x = x0 + c * kw + (kw if (f == 3 and c == 1) else 0)
    return pygame.Rect(x, y0 + f * kh, w_, kh - 4)

def _np_num(t, lim):
    t = t.replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        return None
    return v if -lim <= v <= lim else None

def view_teclado(surf, d, flags, now):
    for k, etq in (("lat", "LATITUD (-90 a 90)"), ("lon", "LONGITUD (-180 a 180)")):
        r = NP_CAMPO[k]
        put(surf, F["small"], etq, (r.x, r.y - 16), DIM)
        on = NP_TECLA["campo"] == k
        pygame.draw.rect(surf, ORANGE if on else DIM, r, 3 if on else 1, border_radius=6)
        txt = NP_TECLA[k] + ("_" if on and int(now * 2) % 2 else "")
        put(surf, F["big"], txt or " ", (r.x + 10, r.y + 8), WHITE, r.w - 20)
    body = ((d or {}).get("bio") or {}).get("body") or (d or {}).get("body")
    put(surf, F["small"], f"en {body}" if body else "valdrá en el planeta donde estés", (8, TOP + 142), DIM, 222)
    if NP_TECLA["err"]:
        put(surf, F["small"], NP_TECLA["err"], (8, TOP + 160), RED, 222)
    for f, fila in enumerate(NP_KEYS):
        for c, k in enumerate(fila):
            r = np_tecla_r(f, c)
            draw_button(surf, r, k, None, F["btn"] if len(k) == 1 else F["small"], lit=flash.get((183, k), 0) > now)
    draw_button(surf, NP_OK, "IR", None, F["btn"], filled=True, lit=flash.get((183, "ok"), 0) > now)
    draw_button(surf, NP_NO, "X", None, F["btn"], lit=flash.get((183, "no"), 0) > now)

def tap_teclado(x, y):
    T = NP_TECLA
    for k, r in NP_CAMPO.items():
        if r.collidepoint(x, y):
            T["campo"] = k; return
    for f, fila in enumerate(NP_KEYS):
        for c, k in enumerate(fila):
            if not np_tecla_r(f, c).collidepoint(x, y):
                continue
            tap_flash((183, k)); T["err"] = ""
            cur = T[T["campo"]]
            if k == "BORRA":
                T[T["campo"]] = cur[:-1]
            elif k == "SIG.":
                T["campo"] = "lon" if T["campo"] == "lat" else "lat"
            elif k == "-":
                T[T["campo"]] = cur[1:] if cur.startswith("-") else "-" + cur
            elif k == ",":
                if "," not in cur:
                    T[T["campo"]] = (cur or "0") + ","
            elif len(cur) < 10:
                T[T["campo"]] = cur + k
            return
    if NP_NO.collidepoint(x, y):
        tap_flash((183, "no")); ui["view"] = 182; return
    if NP_OK.collidepoint(x, y):
        tap_flash((183, "ok"))
        la, lo = _np_num(T["lat"], 90), _np_num(T["lon"], 180)
        if la is None:
            T.update(err="latitud no válida", campo="lat"); return
        if lo is None:
            T.update(err="longitud no válida", campo="lon"); return
        with lock:
            d = state["data"] or {}
        b = d.get("bio") or {}
        body = b.get("body") or d.get("body") if d.get("Flags", 0) & (1 << 21) else None
        nom = f"COORDENADAS {la:.4f} / {lo:.4f}".replace(".", ",")
        np_poner(nom, la, lo, body, "mano", d.get("system"))
        trip["list"].insert(0, {"sys": d.get("system"), "body": body, "st": None, "lat": la, "lon": lo,
                                "R": b.get("R"), "pos": d.get("starpos"), "tag": "A MANO", "t": time.time()})
        trip_save()
        set_alert("DESTINO PUESTO", nom, col=GREEN, secs=2, kind="ok")
        ui["view"] = 182

VIEWS[182] = view_planeta
VIEWS[183] = view_teclado

# ---------------------------------------------------------------------------------------------------------------
# NOTAS DE VIAJE (detalle 129): IR AQUÍ
# ---------------------------------------------------------------------------------------------------------------
NP_IR = pygame.Rect(W - 262, H - 42, 124, 36)
_view_trip_detail_v23b2 = view_trip_detail

def view_trip_detail(surf, d, flags, now):
    _view_trip_detail_v23b2(surf, d, flags, now)
    L, i = trip["list"], trip["sel"]
    if i is None or i >= len(L) or L[i].get("lat") is None:
        return
    n = L[i]
    m = NAVP.get("manual")
    on = bool(m and abs(m["lat"] - n["lat"]) < 1e-6 and abs(m["lon"] - n["lon"]) < 1e-6)
    draw_button(surf, NP_IR, "QUITAR" if on else "IR AQUÍ", None, F["btn"], filled=on,
                lit=flash.get((129, "ir"), 0) > now)

VIEWS[129] = view_trip_detail

_on_tap_v23b2 = on_tap

def on_tap(x, y):
    v = ui.get("view")
    if not ui.get("idle_on"):
        if v == 182 and y >= TOP:
            tap_planeta(x, y)
            return
        elif v == 183:
            if y >= TOP:
                tap_teclado(x, y)
                return
        elif v == 129 and NP_IR.collidepoint(x, y):
            L, i = trip["list"], trip["sel"]
            if i is not None and i < len(L) and L[i].get("lat") is not None:
                n = L[i]
                tap_flash((129, "ir"))
                m = NAVP.get("manual")
                if m and abs(m["lat"] - n["lat"]) < 1e-6 and abs(m["lon"] - n["lon"]) < 1e-6:
                    np_quitar()
                else:
                    np_poner(trip_label(n), n["lat"], n["lon"], n.get("body"), "fav", n.get("sys"))
                    set_alert("DESTINO PUESTO", trip_label(n), col=GREEN, secs=2, kind="ok")
                return
    return _on_tap_v23b2(x, y)

# en el MENÚ nuevo (1280x800): con el adaptador, como AJUSTES
LZ_PANEL[182] = lz_adaptada(182)
LZ_PANEL[183] = lz_adaptada(183)

_lv_trip_detail_v23b2 = LZ_PANEL[129]

def lv_trip_detail(L, area, d, flags, now):
    _lv_trip_detail_v23b2(L, area, d, flags, now)
    Lt, i = trip["list"], trip["sel"]
    if i is None or i >= len(Lt) or Lt[i].get("lat") is None:
        return
    n = Lt[i]
    m = NAVP.get("manual")
    on = bool(m and abs(m["lat"] - n["lat"]) < 1e-6 and abs(m["lon"] - n["lon"]) < 1e-6)
    hb = F["btn"].get_height()
    x1 = area.right - 14
    rb = pygame.Rect(x1 - 620, area.bottom - hb - 30, 300, hb + 24)
    lz_boton_v(L, rb, "QUITAR DESTINO" if on else "IR AQUÍ", None, F["btn"], filled=on, viejo=NP_IR)

LZ_PANEL[129] = lv_trip_detail
