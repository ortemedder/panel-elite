# Panel Elite v1.1 · parte 29: novedades v1.1.13
#   ATRAQUE en puertos planetarios: el ALTÍMETRO (el mismo del cuadro 4, con el suelo del planeta) en la columna
#   izquierda de ESTACIÓN mientras esperas para atracar. Se quita en CAMBIO AUTO.
#   Nombre de la estación entero (letra más pequeña o dos líneas) y sin el tipo repetido.
#   Facción dueña de la estación: en verde y con el escudo si es la tuya, y aviso al atracar (ALERTAS).
#   (en la parte 25: FSD LISTO separado en ALERTAS y SONIDO, y rótulo del suelo legible)
AUTO_LIST.append(("dockalt", "ALTÍMETRO EN EL ATRAQUE PLANETARIO"))
EV_LIST.append(("estfac", "ESTACIÓN DE TU FACCIÓN"))

# ---------------------------------------------------------------------------------------------------------------
# tu facción (la de faccion.json; si aún no ha llegado, Caballeros de Sion)
# ---------------------------------------------------------------------------------------------------------------
def mi_fac():
    return ((FACD.get("data") or {}).get("faccion") or "Caballeros de Sion").strip()

def es_mi_fac(name):
    return bool(name) and name.strip().lower() == mi_fac().lower()

def fac_put(surf, fac, x, y, w):
    """Facción de la estación en ESTACIÓN; la tuya, en verde, con el escudo y «TU FACCIÓN»."""
    if not es_mi_fac(fac):
        put(surf, F["small"], fac, (x, y), DIM, w)
        return y + 18
    lx = x + 20 if blit_logo(surf, pygame.Rect(x, y, 17, 17)) else x
    tw = put(surf, F["small"], fac, (lx, y + 1), GREEN, w - (lx - x))
    if lx + tw + 90 <= x + w:
        put(surf, F["tiny"], "· TU FACCIÓN", (lx + tw + 6, y + 3), GREEN)
    return y + 19

# ---------------------------------------------------------------------------------------------------------------
# nombre de la estación entero: letra grande, si no cabe más pequeña, y si tampoco en dos líneas
# ---------------------------------------------------------------------------------------------------------------
def _partir(font, name, w):
    pal, L = name.split(), []
    for p_ in pal:
        if L and font.size(L[-1] + " " + p_)[0] <= w:
            L[-1] += " " + p_
        else:
            L.append(p_)
    return L

def st_name_put(surf, name, x, y, w):
    """Nombre entero: grande; si no cabe, mediana; luego en dos líneas mediana o pequeña."""
    if F["big"].size(name)[0] <= w:
        put(surf, F["big"], name, (x, y), ORANGE); return y + 26
    if F["btn"].size(name)[0] <= w:
        put(surf, F["btn"], name, (x, y + 3), ORANGE); return y + 26
    for f_, lh in (("btn", 21), ("small", 17)):
        L = _partir(F[f_], name, w)
        if len(L) <= 2 and all(F[f_].size(l_)[0] <= w for l_ in L):
            for i, l_ in enumerate(L):
                put(surf, F[f_], l_, (x, y + i * lh), ORANGE)
            return y + 2 * lh + 3
    L = _partir(F["small"], name, w)
    put(surf, F["small"], L[0], (x, y), ORANGE, w)
    put(surf, F["small"], " ".join(L[1:]), (x, y + 17), ORANGE, w)
    return y + 37

def st_label_shown(d, st):
    """True si la foto de fondo ya pone abajo el tipo de estación (DEPÓSITO PLANETARIO...)."""
    if st.get("status") not in ("SOLICITADO", "CONCEDIDO"):
        return False
    try:
        k, lab, col = carrier_kind(d, st)
    except Exception:
        return False
    t = ST_TYPE.get(st.get("type"), st.get("type") or "")
    return bool(k) and bool(t) and lab.upper() == t.upper()

# ---------------------------------------------------------------------------------------------------------------
# ALTÍMETRO en el atraque planetario
# ---------------------------------------------------------------------------------------------------------------
def dock_alt_on(d):
    d = d or {}
    st = d.get("station") or {}
    return (auto_on("dockalt") and st.get("status") in ("SOLICITADO", "CONCEDIDO") and bool(st.get("pad"))
            and st.get("type") not in STARPORTS and not d.get("Flags", 0) & 3 and alt_now(d) is not None)

def draw_dock_alt(surf, d, now):
    r = pygame.Rect(2, TOP + 2, 244, H - TOP - 4)
    pygame.draw.rect(surf, BLACK, r, border_radius=6)
    pygame.draw.rect(surf, DIM, r, 1, border_radius=6)
    draw_alt(surf, r.inflate(-4, -4), d, now)
    st = (d or {}).get("station") or {}
    try:                                                  # el rótulo del tipo, más pequeño, sin pisar el altímetro
        k, lab, col = carrier_kind(d or {}, st)
        if k and lab:
            put(surf, F["btn"], lab, (W - 8, H - 26), col, W - r.right - 14, anchor="topright")
    except Exception:
        pass
    gs, vs = SPD.get("gs"), alt_vs()                      # el reloj de velocidad no cabe: en cifras
    if gs is not None or vs is not None:
        tot = math.hypot(gs or 0, vs or 0)
        x = r.right - 22
        put(surf, F["tiny"], "VEL.", (x, r.y + 4), DIM, anchor="midtop")
        put(surf, F["btn"], f"{tot:.0f}", (x, r.y + 18), WHITE, anchor="midtop")

_view8_v1113 = VIEWS[8]

def view8_v1113(surf, d, flags, now):
    _view8_v1113(surf, d, flags, now)
    try:
        if dock_alt_on(d):
            draw_dock_alt(surf, d, now)
    except Exception as e:
        log_exc("altímetro del atraque", e)

VIEWS[8] = view8_v1113

# ---------------------------------------------------------------------------------------------------------------
# aviso al atracar en una estación de tu facción (una vez por atraque)
# ---------------------------------------------------------------------------------------------------------------
ESTFAC = {"key": None}

def estfac_watch(d):
    st = d.get("station") or {}
    if st.get("status") != "ATRACADO":
        ESTFAC["key"] = None
        return
    key = (st.get("name"), st.get("mid"))
    if ESTFAC["key"] == key:
        return
    fac = st.get("faction") or (d.get("sysinfo") or {}).get("st_faction")
    if not fac:
        return                                           # aún no ha llegado: se mira en el siguiente dibujo
    ESTFAC["key"] = key
    if es_mi_fac(fac) and ev_on("estfac"):
        k0 = XA_K[0]
        try:
            XA_K[0] = "estfac"
            set_alert("ESTACIÓN DE TU FACCIÓN", fac.upper(), GREEN, 5, kind="info")
            play("ok")
        finally:
            XA_K[0] = k0

_render_v1113 = render

def render(surf):
    r_ = _render_v1113(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d and time.time() - rx < 5:
            estfac_watch(d)
    except Exception as e:
        log_exc("estación de tu facción", e)
    return r_
