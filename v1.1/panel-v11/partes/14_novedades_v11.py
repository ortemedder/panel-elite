# Panel Elite v1.1 · parte 14: novedades de la v1.1 (pasajeros, calculadora, tick de cada sistema...)
# Los avisos nuevos van al final de las listas para no cambiar los numeros de los de antes.
EV_LIST.append(("inicio", "ENCENDER / APAGAR"))
EV_LIST.append(("colventa", "COLONIA: NO VENDER LA CARGA"))
AUTO_LIST.append(("supercrucero", "SUPERCRUCERO > 4 CUADROS"))
EV_LIST.append(("paxin", "PASAJEROS A BORDO"))
EV_LIST.append(("paxaqui", "DESEMBARCO DE PASAJEROS"))
EV_LIST.append(("paxtiempo", "PASAJEROS: POCO TIEMPO"))
EV_LIST.append(("paxbuscado", "PASAJEROS BUSCADOS ESCANEADOS"))

import re as _re11


def _xa_show(key, **a):
    """Aviso grande (xa) con su clave de ALERTAS / SONIDO."""
    k0 = XA_K[0]
    try:
        XA_K[0] = key
        xa["a"] = dict(until=time.time() + a.pop("secs", 7), **a)
        play("alarm" if a.get("col") == RED else "ok")
    finally:
        XA_K[0] = k0


# ======================================================================================
# PASAJEROS (sender b13): pestaña en 4 CARGA/MISIÓN, cuadro en la pantalla grande, avisos
# ======================================================================================
PAX_ES = {"Tourist": "turistas", "AidWorker": "trabajadores humanitarios", "Refugee": "refugiados",
          "Criminal": "criminales", "Explorer": "exploradores", "Scientist": "científicos", "Celebrity": "celebridades",
          "Business": "ejecutivos", "Political": "políticos", "Soldier": "soldados", "Medical": "personal médico",
          "Police": "policías", "Prisoner": "presos", "Protester": "manifestantes", "Genocide": "pasajeros"}
MENU[210] = "PASAJEROS"
PARENT[210] = 4

def pax_list(d):
    return ((d or {}).get("pax") or {}).get("list") or []

def pax_label(p):
    """«turistas», «trabajadores humanitarios»... (del nombre de la mision del juego, o del tipo)."""
    nom = _re11.sub(r"^\d+\s+", "", p.get("nom") or "")
    nom = _re11.split(r"\s+busca", nom)[0].strip()
    return (nom or PAX_ES.get(p.get("tipo"), p.get("tipo") or "pasajeros")).lower()

def draw_pax(surf, d, top, now, page=0):
    L = pax_list(d)
    tot = sum(p.get("n", 0) for p in L)
    if not L:
        put(surf, F["btn"], "Sin pasajeros a bordo", (W // 2, (H + top) // 2), DIM, anchor="center"); return
    put(surf, F["small"], f"{tot} pasajero{'s' if tot != 1 else ''} en {len(L)} misi{'ones' if len(L) != 1 else 'ón'} · "
                          f"{cr(sum(p.get('cr', 0) for p in L))} cr", (8, top), DIM, W - 16)
    y = top + 18
    rh = 42
    per = max(1, (H - y - 16) // rh)
    pages = (len(L) + per - 1) // per
    pg = page % pages
    for p in L[pg * per:(pg + 1) * per]:
        x = put(surf, F["btn"], f"{p.get('n', 0)} {pax_label(p).upper()}", (10, y), ORANGE, W - 150) + 16
        if p.get("vip"):
            x += put(surf, F["small"], "VIP", (x, y + 3), BLUE) + 8
        if p.get("wanted"):
            put(surf, F["small"], "BUSCADOS", (x, y + 3), RED)
        put(surf, F["btn"], f"{cr(p.get('cr', 0))} cr", (W - 10, y), GREEN, anchor="topright")
        left = (p.get("exp") or 0) - now
        put(surf, F["small"], f"-> {p.get('st') or '?'} · {p.get('sys') or '?'}", (10, y + 20), DIM, W - 110)
        put(surf, F["small"], fmt_time(left) if p.get("exp") else "", (W - 10, y + 20),
            RED if p.get("exp") and left < 1800 else DIM, anchor="topright")
        y += rh
    if pages > 1:
        put(surf, F["small"], f"pág {pg + 1}/{pages}  (toca para pasar)", (W // 2, H - 10), DIM, anchor="center")

def view_pax(surf, d, flags, now):
    draw_pax(surf, d, TOP + 4, now, ui.get("page4", 0))

VIEWS[210] = view_pax

# 4 CARGA/MISIÓN: tercera pestaña PASAJEROS cuando llevas
def carga_ntabs(d=None):
    if d is None:
        with lock:
            d = state["data"]
    return 3 if pax_list(d) else 2

def tab_rect_n(i, n):
    return grid(i, n, 1, TOP, TOP + TAB_H)

def view_carga(surf, d, flags, now):
    cargo = (d or {}).get("cargo") or []
    miss = (d or {}).get("missions") or []
    used = sum(c for _, c in cargo)
    cap = (d or {}).get("cargocap")
    L = pax_list(d)
    tabs = [f"BODEGA {used}/{cap if cap is not None else '?'} t", f"MISIONES ({len(miss)})"]
    if L:
        tabs.append(f"PASAJEROS ({sum(p.get('n', 0) for p in L)})")
    elif ui["tab4"] == 2:
        ui["tab4"] = 1
    for i, t in enumerate(tabs):
        draw_button(surf, tab_rect_n(i, len(tabs)), t, None, F["btn"] if len(tabs) == 2 else F["small"], filled=ui["tab4"] == i)
    top = TOP + TAB_H + 4
    if ui["tab4"] == 2:
        draw_pax(surf, d, top, now, ui["page4"]); return
    if ui["tab4"] == 0:
        rows, rh = [(n, c) for n, c in cargo], 24
        if not rows:
            put(surf, F["btn"], "Bodega vacía", (W // 2, (H + top) // 2), DIM, anchor="center"); return
    else:
        rows, rh = miss, 42
        if not rows:
            put(surf, F["btn"], "Sin misiones activas", (W // 2, (H + top) // 2), DIM, anchor="center"); return
    per = max(1, (H - top - 18) // rh)
    pages = (len(rows) + per - 1) // per
    pg = ui["page4"] % pages
    y = top
    for row in rows[pg * per:(pg + 1) * per]:
        if ui["tab4"] == 0:
            name, cnt = row
            put(surf, F["btn"], name, (10, y), ORANGE, W - 90)
            put(surf, F["btn"], f"{cnt} t", (W - 10, y), ORANGE, anchor="topright")
        else:
            name, dest, exp = row
            put(surf, F["btn"], name, (10, y), ORANGE, W - 20)
            left = exp - time.time() if exp else 0
            put(surf, F["small"], f"-> {dest or '?'}", (10, y + 20), DIM, W - 110)
            put(surf, F["small"], fmt_time(left) if exp else "", (W - 10, y + 20),
                RED if exp and left < 3600 else DIM, anchor="topright")
        y += rh
    if pages > 1:
        put(surf, F["small"], f"pág {pg + 1}/{pages}  (toca para pasar)", (W // 2, H - 10), DIM, anchor="center")

VIEWS[4] = view_carga

# avisos
PXW = {"dk": None, "warned": set(), "scan": None}

def pax_note(kind, text):
    p = (text.split("|") + ["", "", "", ""])[:4]
    n, tipo, tot, st = int(p[0] or 0), p[1], int(p[2] or 0), p[3]
    _xa_show("paxin", col=BLUE, title="PASAJEROS A BORDO", big=f"+{n} {PAX_ES.get(tipo, tipo or 'pasajeros').upper()}",
             lines=[f"{tot} pasajeros a bordo", f"destino: {st}" if st else ""], secs=6)

def pax_watch(now):
    with lock:
        d, rx = state["data"], state["rx"]
    if not d or now - rx > 5:
        return
    L = pax_list(d)
    dk = bool(d.get("Flags", 0) & 1)
    if dk and PXW["dk"] is False and L:                  # al atracar: ¿alguno se baja aquí?
        stn = ((d.get("station") or {}).get("name") or "").lower()
        here = [p for p in L if stn and (p.get("st") or "").lower() == stn]
        if here:
            n = sum(p.get("n", 0) for p in here)
            _xa_show("paxaqui", col=GREEN, title="DESEMBARCO", big=f"{n} PASAJERO{'S' if n != 1 else ''} SE BAJAN AQUÍ",
                     lines=[", ".join(f"{p.get('n')} {pax_label(p)}" for p in here[:3]), "entrega la misión en el tablón"], secs=8)
    PXW["dk"] = dk
    for p in L:                                          # poco tiempo
        left = (p.get("exp") or 0) - now
        if p.get("exp") and 0 < left < 1200 and p.get("id") not in PXW["warned"]:
            PXW["warned"].add(p.get("id"))
            _xa_show("paxtiempo", col=RED, title=f"QUEDAN {int(left // 60)} MIN", big=f"{p.get('n')} {pax_label(p).upper()}",
                     lines=[f"a {p.get('st') or '?'} · {p.get('sys') or '?'}"], secs=8)
    a = xa.get("a")                                      # te escanean la cabina con pasajeros buscados
    if a and a.get("title") == "TE ESCANEAN" and a.get("big") == "PASAJEROS" and id(a) != PXW["scan"]:
        PXW["scan"] = id(a)
        if any(p.get("wanted") for p in L) and ev_on("paxbuscado"):
            a["col"] = RED
            a["lines"] = list(a.get("lines") or []) + ["¡LLEVAS PASAJEROS BUSCADOS!"]
            k0 = XA_K[0]
            try:
                XA_K[0] = "paxbuscado"; play("alarm")
            finally:
                XA_K[0] = k0

_render_v11 = render

def render(surf):
    r_ = _render_v11(surf)
    try:
        pax_watch(time.time())
    except Exception as e:
        log_exc("pasajeros", e)
    return r_

# RESUMEN DEL DÍA: pasajeros llevados hoy
_view11_v11 = VIEWS[11]

def view11_v11(surf, d, flags, now):
    _view11_v11(surf, d, flags, now)
    h_ = ((d or {}).get("pax") or {}).get("hoy") or {}
    if h_.get("n") and h_.get("day") == time.strftime("%Y-%m-%d", time.gmtime()):
        put(surf, F["tiny"], f"PASAJEROS HOY: {h_['n']} · {cr(h_.get('cr', 0))} cr", (W - 8, TOP + 2), BLUE, anchor="topright")

VIEWS[11] = view11_v11


# ======================================================================================
# CALCULADORA con cinta (12 AJUSTES > CALCULADORA)
# ======================================================================================
MENU[211] = "CALCULADORA"
PARENT[211] = 12
CALC = {"cur": "0", "acc": None, "op": None, "expr": "", "tape": [], "new": True}
CK = [["7", "8", "9", "÷"], ["4", "5", "6", "×"], ["1", "2", "3", "−"], ["0", ",", "=", "+"]]
C_DISP = pygame.Rect(8, TOP + 4, 298, 44)
C_CLR = pygame.Rect(312, TOP + 4, 76, 44)
C_DEL = pygame.Rect(394, TOP + 4, 78, 44)
C_TAPE = pygame.Rect(312, TOP + 54, 160, H - TOP - 58)

def c_key(i, j):
    return pygame.Rect(8 + j * 76, TOP + 54 + i * 52, 70, 46)

def c_fmt(x):
    if x is None:
        return "Error"
    if abs(x) >= 1e15:
        return f"{x:.4g}".replace(".", ",")
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}".replace(",", ".")
    s = f"{x:,.4f}".rstrip("0").rstrip(".")
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def c_entry(s):
    neg = s.startswith("-")
    s = s.lstrip("-")
    ent, _, dec = s.partition(",")
    ent = f"{int(ent or '0'):,}".replace(",", ".")
    return ("-" if neg else "") + ent + ("," + dec if "," in s else "")

def c_val(s):
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return 0.0

def c_apply(a, op, b):
    if op == "+": return a + b
    if op == "−": return a - b
    if op == "×": return a * b
    if op == "÷": return None if b == 0 else a / b
    return b

def c_press(k):
    C = CALC
    if k in "0123456789":
        if C["new"] or C["cur"] in ("0", "Error"):
            C["cur"] = k; C["new"] = False
        elif len(C["cur"].replace(",", "")) < 15:
            C["cur"] += k
    elif k == ",":
        if C["new"] or C["cur"] == "Error":
            C["cur"] = "0,"; C["new"] = False
        elif "," not in C["cur"]:
            C["cur"] += ","
    elif k in "÷×−+":
        b = c_val(C["cur"])
        if C["op"] and not C["new"]:
            r = c_apply(C["acc"], C["op"], b)
            C["acc"] = r if r is not None else 0.0
            C["expr"] += f" {c_entry(C['cur'])} {k}"
        else:
            if C["acc"] is None or not C["op"]:
                C["acc"] = b
                C["expr"] = f"{c_entry(C['cur'])} {k}"
            else:
                C["expr"] = C["expr"][:-1] + k
        C["op"] = k; C["new"] = True
        C["cur"] = c_fmt(C["acc"]).replace(".", "") if C["acc"] is not None else "0"
    elif k == "=":
        if C["op"]:
            b = c_val(C["cur"])
            r = c_apply(C["acc"], C["op"], b)
            expr = f"{C['expr']} {c_entry(C['cur'])}"
            C["tape"].append((expr, c_fmt(r)))
            del C["tape"][:-20]
            C["cur"] = "Error" if r is None else c_fmt(r).replace(".", "")
            C.update(acc=None, op=None, expr="", new=True)

def c_cur_txt():
    return CALC["cur"] if CALC["cur"] == "Error" else c_entry(CALC["cur"])

def view_calc(surf, d, flags, now):
    pygame.draw.rect(surf, (20, 12, 0), C_DISP, border_radius=6)
    if CALC["expr"]:
        put(surf, F["tiny"], CALC["expr"], (C_DISP.right - 6, C_DISP.y + 2), DIM, C_DISP.w - 12, anchor="topright")
    put(surf, F["big"], c_cur_txt(), (C_DISP.right - 6, C_DISP.y + 16), ORANGE, C_DISP.w - 12, anchor="topright")
    draw_button(surf, C_CLR, "C", None, F["btn"], lit=flash.get((211, "c"), 0) > now)
    draw_button(surf, C_DEL, "BORRA", None, F["btn"], lit=flash.get((211, "b"), 0) > now)
    for i, row in enumerate(CK):
        for j, k in enumerate(row):
            draw_button(surf, c_key(i, j), k, None, F["big"], filled=k == "=", lit=flash.get((211, k), 0) > now)
    pygame.draw.rect(surf, DIM, C_TAPE, 1, border_radius=6)
    put(surf, F["tiny"], "CINTA · toca para recuperar", (C_TAPE.x + 6, C_TAPE.y + 3), DIM, C_TAPE.w - 10)
    y = C_TAPE.y + 18
    for expr, res in list(reversed(CALC["tape"]))[:6]:
        put(surf, F["tiny"], expr, (C_TAPE.x + 6, y), DIM, C_TAPE.w - 12)
        put(surf, F["small"], "= " + res, (C_TAPE.right - 6, y + 12), ORANGE, C_TAPE.w - 12, anchor="topright")
        y += 32

def tap_calc(x, y):
    if C_CLR.collidepoint(x, y):
        tap_flash((211, "c")); CALC.update(cur="0", acc=None, op=None, expr="", new=True); return
    if C_DEL.collidepoint(x, y):
        tap_flash((211, "b"))
        if not CALC["new"] and CALC["cur"] != "Error":
            CALC["cur"] = CALC["cur"][:-1] or "0"
        return
    for i, row in enumerate(CK):
        for j, k in enumerate(row):
            if c_key(i, j).collidepoint(x, y):
                tap_flash((211, k)); c_press(k); return
    if C_TAPE.collidepoint(x, y):
        k = int((y - C_TAPE.y - 18) // 32)
        T = list(reversed(CALC["tape"]))
        if 0 <= k < len(T) and T[k][1] != "Error":
            CALC["cur"] = T[k][1].replace(".", ""); CALC["new"] = False

VIEWS[211] = view_calc
SET12.append(("CALCULAR", 211))


# ======================================================================================
# TICK DE CADA SISTEMA (escucha del pueblo v4: tick_ult, tick_marg, tick_prox, tick_disp, tick_n)
# ======================================================================================
def sys_tick_txt(v, now):
    if not v:
        return None, DIM
    ult, prox = v.get("tick_ult"), v.get("tick_prox")
    if not ult and not prox:
        return ("tick sin medir" if "tk" in v else None), DIM
    hm = lambda t: time.strftime("%H:%M", time.localtime(t))
    parts = []
    if ult:
        parts.append(f"tick {hm(ult)}" + (f" (±{v['tick_marg']}m)" if v.get("tick_marg") else ""))
    col = DIM
    if prox:
        while prox < now - 3 * 3600:                     # previsión pasada: el siguiente día
            prox += 86400
        parts.append(f"próx. ~{hm(prox)}" + (f" (±{v['tick_disp']}m)" if v.get("tick_disp") else ""))
        if 0 <= prox - now < 3600:
            col = BLUE
    return " · ".join(parts), col

_fs_head_v11 = fs_head

def fs_head(surf, d, v, name):
    y = _fs_head_v11(surf, d, v, name)
    txt, col = sys_tick_txt(v, time.time())
    if txt:
        put(surf, F["tiny"], txt, (W - 8, y - 15), col, 240, anchor="topright")
    return y

def tick_soon(v, now):
    p = (v or {}).get("tick_prox")
    if not p:
        return False
    while p < now - 3 * 3600:
        p += 86400
    return 0 <= p - now < 3600

_dfs_v11 = draw_fac_screen

def draw_fac_screen(surf, now):
    r_ = _dfs_v11(surf, now)
    try:
        S = ((FACD["data"] or {}).get("sistemas") or {})
        for px, py, nm in RADAR_PTS:                     # reloj azul en los que tienen el tick en la próxima hora
            if tick_soon(S.get(nm), now):
                cx, cy = px - 9, py - 9
                pygame.draw.circle(surf, BLACK, (cx, cy), 6)
                pygame.draw.circle(surf, BLUE, (cx, cy), 6, 1)
                pygame.draw.line(surf, BLUE, (cx, cy), (cx, cy - 4))
                pygame.draw.line(surf, BLUE, (cx, cy), (cx + 3, cy))
    except Exception as e:
        log_exc("tick en el radar", e)
    return r_

_ficha_v11 = VIEWS[194]

def ficha_v11(surf, d, flags, now):
    _ficha_v11(surf, d, flags, now)
    D, name, v = fs_get()
    txt, col = sys_tick_txt(v, now)
    if not v or not txt:
        return
    y = TOP + 3 + 21                                     # la linea de «datos hace … · EDDN»
    a_txt, _ = fac_age(v.get("t"))
    x = 8 + F["small"].size(f"datos {a_txt} · {v.get('src') or '?'}")[0] + 12
    S_ = v.get("sis") or {}
    right = W - 8 - (F["small"].size(f"POBLACIÓN {fnum_pob(S_.get('pob'))}")[0] + 10 if S_ else 0)
    if right - x > 60:
        put(surf, F["tiny"], txt, (x, y + 2), col, right - x)

VIEWS[194] = ficha_v11


# --- v1.1.1: _orig_rect (rectangulo sin las esquinas de CABINA) tambien en el panel nitido de la HDMI ---
# (antes fallaba con «argument 1 must be pygame.surface.Surface, not ScaledSurf» al cambiar de pantalla en CABINA)
_orig_rect_raw = _orig_rect

def _orig_rect(surf, col, rect, width=0, *a, **k):
    if isinstance(surf, ScaledSurf):
        return _orig_rect_raw(surf.real, col, surf._r(rect), _hw(surf, width) if width else 0, *a, **k)
    return _orig_rect_raw(surf, col, rect, width, *a, **k)


# ======================================================================================
# v1.1.1 · RUTA: lista desplazable con marcas, hora y combustible de llegada, ficha de cada salto, avisos
# ======================================================================================
EV_LIST.append(("rutapeligro", "RUTA: ENANA BLANCA / NEUTRONES"))
EV_LIST.append(("rutafin", "RUTA: QUEDAN 2 SALTOS"))
EV_LIST.append(("rutacdsn", "RUTA: SISTEMA CDSN EN GUERRA"))
MENU[212] = "SISTEMA DE LA RUTA"
PARENT[212] = 3
RUT = {"off": 0, "rows": [], "up": None, "dn": None, "r": None, "max": 0, "key": None}
REDSM = {}                                               # nombre -> datos de EDSM (o {} si no lo conoce)
REDSM_Q = []

def _redsm_loop():
    import urllib.request, urllib.parse
    while True:
        if not REDSM_Q:
            time.sleep(2); continue
        n = REDSM_Q.pop(0)
        if n in REDSM:
            continue
        try:
            url = "https://www.edsm.net/api-v1/system?" + urllib.parse.urlencode(
                {"systemName": n, "showInformation": 1, "showPrimaryStar": 1, "showCoordinates": 1})
            req = urllib.request.Request(url, headers={"User-Agent": "PanelEliteRPi/1.1"})
            with urllib.request.urlopen(req, timeout=15) as r_:
                j = json.loads(r_.read().decode() or "[]")
            REDSM[n] = j if isinstance(j, dict) else {}
        except Exception:
            REDSM[n] = None                              # sin respuesta (se puede reintentar)
            time.sleep(10)
        time.sleep(2)                                    # sin prisa: EDSM pide no saturar

threading.Thread(target=_redsm_loop, daemon=True, name="edsm-ruta").start()

def redsm_want(n):
    if n and n not in REDSM and n not in REDSM_Q:
        REDSM_Q.append(n)

def route_marks(name, cls):
    """[(texto, color)] para un salto de la ruta."""
    k = star_kind(cls)
    out = [("NEUTRONES", RED)] if k == "neu" else [("ENANA BLANCA", RED)] if k == "wd" else []
    v = ((FACD["data"] or {}).get("sistemas") or {}).get(name)
    if v and not v.get("fuera"):
        st_ = (v.get("activos") or []) + (v.get("pendientes") or [])
        bad = "RETIRADA" if "Retreat" in st_ else "ELECCIONES" if "Election" in st_ else "GUERRA" if fac_war(v) else None
        out.append(("CDSN", ORANGE))
        if bad:
            out.append((bad, RED))
    else:
        info = (REDSM.get(name) or {}).get("information") or {}
        seg = (info.get("security") or "").lower()
        if "anarchy" in seg or "anarqu" in seg:
            out.append(("ANARQUÍA", RED))
        elif seg.startswith("low") or "baja" in seg:
            out.append(("SEG. BAJA", RED))
    return out

def route_arrival(d, now):
    """(texto hora y combustible de llegada, color)"""
    RI = (d or {}).get("routeinfo") or {}
    route = (d or {}).get("route") or []
    total = (d or {}).get("routen") or len(route)
    bits, col = [], BLUE
    if RI.get("eta"):
        e = RI["eta"]
        bits.append(f"ETA {e // 3600}h {e % 3600 // 60:02d}m" if e >= 3600 else f"ETA {e // 60} min")
        bits.append("llegas " + time.strftime("%H:%M", time.localtime(now + e)))
    fj, fm = (d or {}).get("fuelj"), ((d or {}).get("Fuel") or {}).get("FuelMain")
    if fj and fm is not None and total:
        left = fm - fj * total
        if left >= 0:
            bits.append(f"~{left:.0f} t")
        else:
            bits.append("hay que repostar"); col = RED
    if RI.get("neutron"):
        bits.append(f"neutrón a {RI['neutron']}")
    return "  ·  ".join(bits), col

def view_nav(surf, d, flags, now):
    nav = (d or {}).get("nav") or {}
    route = (d or {}).get("route") or []
    y = TOP + 6
    tgt = nav.get("target")
    if not tgt and not route:
        put(surf, F["big"], "Sin ruta trazada", (W // 2, (H + TOP) // 2), DIM, anchor="center")
        return
    put(surf, F["small"], "SIGUIENTE SALTO", (8, y), DIM); y += 16
    put(surf, F["big"], (tgt or route[0][0]).upper(), (8, y), ORANGE, W - 16); y += 30
    cls = nav.get("star") or (route[0][1] if route else "")
    ok = star_ok(cls)
    x = 8 + put(surf, F["btn"], f"Estrella {cls or '?'}   ", (8, y), ORANGE)
    put(surf, F["btn"], "RECOLECTABLE" if ok else "NO RECOLECTABLE", (x, y), NEON_G if ok else RED); y += 26
    jumps = nav.get("jumps")
    last = nav.get("last")
    put(surf, F["btn"], f"Saltos restantes: {jumps if jumps is not None else len(route)}", (8, y))
    if last:
        put(surf, F["btn"], f"Último salto: {last:.1f} al", (W - 8, y), ORANGE, anchor="topright")
    y += 30
    y = draw_routeline(surf, d or {}, y, time.time())
    pygame.draw.line(surf, DIM, (8, y - 4), (W - 8, y - 4))
    RUT.update(rows=[], up=None, dn=None, r=None)
    if not route:
        return
    put(surf, F["small"], f"RUTA  -  {((d or {}).get('routeend') or route[-1])[0]}", (8, y), DIM, W - 250)
    txt, col = route_arrival(d, now)
    if txt:
        put(surf, F["small"], txt, (W - 8, y), col, 240, anchor="topright")
    y += 18
    S_ = (d or {}).get("sysinfo") or {}
    bottom = H - 26 if any(S_.get(k) for k in ("gov", "alleg", "sec", "fstate")) else H - 4    # sitio de la linea de política
    rh = 22
    nvis = max(1, (bottom - y) // rh)
    key = tuple(r[0] for r in route[:2])
    if key != RUT["key"]:
        RUT.update(key=key, off=0)                       # ruta nueva o un salto hecho: arriba del todo
    RUT["max"] = max(0, len(route) - nvis)
    RUT["off"] = max(0, min(RUT["off"], RUT["max"]))
    tw_ = 182 if carrier_dest(d or {})[0] else 0
    sb = 22 if RUT["max"] else 0
    RUT["r"] = pygame.Rect(0, y, W, nvis * rh)
    for n in range(RUT["off"], min(len(route), RUT["off"] + nvis)):
        name, c = route[n]
        redsm_want(name)
        colr = ORANGE if star_ok(c) else RED
        marks = route_marks(name, c)
        mw = sum(F["tiny"].size(t)[0] + 8 for t, _ in marks)
        put(surf, F["btn"], f"{n + 1}. {name}", (8, y), colr, W - 70 - tw_ - sb - mw)
        xm = W - 30 - tw_ - sb - mw
        for t, cc in marks:
            xm += put(surf, F["tiny"], t, (xm, y + 5), cc) + 8
        put(surf, F["btn"], c or "?", (W - 8 - tw_ - sb, y), colr, anchor="topright")
        RUT["rows"].append((pygame.Rect(0, y, W - sb - tw_, rh), name, c))
        y += rh
    if RUT["max"]:                                       # flechas para subir y bajar (también se arrastra)
        x0 = W - 18 - tw_
        top_, bot_ = RUT["r"].y, RUT["r"].bottom
        RUT["up"] = pygame.Rect(x0 - 6, top_, 22, 20)
        RUT["dn"] = pygame.Rect(x0 - 6, bot_ - 20, 22, 20)
        cu = ORANGE if RUT["off"] > 0 else DIM
        cd = ORANGE if RUT["off"] < RUT["max"] else DIM
        pygame.draw.polygon(surf, cu, [(x0, top_ + 14), (x0 + 10, top_ + 14), (x0 + 5, top_ + 4)])
        pygame.draw.polygon(surf, cd, [(x0, bot_ - 14), (x0 + 10, bot_ - 14), (x0 + 5, bot_ - 4)])
        put(surf, F["tiny"], f"{RUT['off'] + 1}-{min(len(route), RUT['off'] + nvis)}/{len(route)}",
            (x0 + 5, (top_ + bot_) // 2 - 6), DIM, anchor="midtop")

def route_tap(x, y):
    if RUT["up"] and RUT["up"].inflate(10, 6).collidepoint(x, y):
        RUT["off"] = max(0, RUT["off"] - 3); return True
    if RUT["dn"] and RUT["dn"].inflate(10, 6).collidepoint(x, y):
        RUT["off"] = min(RUT["max"], RUT["off"] + 3); return True
    for r, name, c in RUT["rows"]:
        if r.collidepoint(x, y):
            tap_flash(("rsys",)); ui["rsys"] = (name, c); redsm_want(name); ui["view"] = 212
            return True
    return False

def view_rsys(surf, d, flags, now):
    name, c = ui.get("rsys") or ("?", "")
    y = TOP + 4
    put(surf, F["big"], name.upper(), (8, y), ORANGE, W - 110); y += 30
    k = star_kind(c)
    kt = {"ok": ("RECOLECTABLE", GREEN), "no": ("NO RECOLECTABLE", RED), "neu": ("ESTRELLA DE NEUTRONES · ¡cuidado con los chorros!", RED),
          "wd": ("ENANA BLANCA · ¡cuidado con los chorros!", RED), "?": ("", DIM)}[k]
    x = 8 + put(surf, F["btn"], f"Estrella {c or '?'}   ", (8, y), ORANGE)
    put(surf, F["btn"], kt[0], (x, y), kt[1], W - x - 8); y += 26
    v = ((FACD["data"] or {}).get("sistemas") or {}).get(name)
    if v and not v.get("fuera"):
        put(surf, F["btn"], f"CABALLEROS DE SION · {v.get('inf', 0):.1f} %".replace(".", ",") + (" · CONTROLA" if v.get("ctrl") else ""),
            (8, y), ORANGE, W - 16); y += 22
        st_ = ", ".join(ES_ST.get(s_, s_) for s_ in (v.get("activos") or []) + (v.get("pendientes") or []))
        if st_:
            put(surf, F["small"], st_, (8, y), RED if fac_war(v) else GREEN, W - 16); y += 18
    J = REDSM.get(name)
    pygame.draw.line(surf, DIM, (8, y + 2), (W - 8, y + 2)); y += 8
    if J is None and name in REDSM:
        put(surf, F["small"], "EDSM no responde (se reintentará)", (8, y), DIM)
    elif name not in REDSM:
        put(surf, F["small"], "consultando EDSM…", (8, y), DIM)
    elif not J:
        put(surf, F["btn"], "EDSM NO LO CONOCE", (8, y), GREEN); y += 22
        put(surf, F["small"], "puede que nadie lo haya subido: ¡posible primer descubrimiento!", (8, y), GREEN, W - 16)
    else:
        info = J.get("information") or {}
        ps = J.get("primaryStar") or {}
        rows = [("CONTROLA", info.get("faction")), ("GOBIERNO", info.get("government")), ("ALIANZA", info.get("allegiance")),
                ("SEGURIDAD", info.get("security")), ("ECONOMÍA", info.get("economy")),
                ("POBLACIÓN", f"{info['population']:,}".replace(",", ".") if info.get("population") else "deshabitado"),
                ("ESTRELLA", (ps.get("type") or "") + (" · recolectable" if ps.get("isScoopable") else ""))]
        for lab, val in rows:
            if val:
                put(surf, F["small"], lab, (8, y + 2), DIM)
                put(surf, F["btn"], str(val), (110, y), WHITE, W - 120); y += 21
    draw_button(surf, IR_R, "IR >", None, F["small"], lit=flash.get(("rir",), 0) > now, compact=True)
    draw_button(surf, BACK_R, "< VOLVER", None, F["small"], compact=True)

def tap_rsys(x, y):
    name = (ui.get("rsys") or ("",))[0]
    if IR_R.collidepoint(x, y) and name:
        tap_flash(("rir",)); ir_send(name); return
    if BACK_R.collidepoint(x, y) or y > TOP:
        ui["view"] = 3

VIEWS[212] = view_rsys

RW = {"dang": None, "fin": None, "sys": None}

def route_watch(now):
    with lock:
        d, rx = state["data"], state["rx"]
    if not d or now - rx > 5:
        return
    route = d.get("route") or []
    nxt = route[0] if route else None
    if RW["dang"] is None:
        RW.update(dang=nxt, fin=(d.get("routen") or 0, (d.get("routeend") or [""])[0]), sys=d.get("system")); return
    if nxt and nxt != RW["dang"] and star_kind(nxt[1]) in ("neu", "wd"):
        _xa_show("rutapeligro", col=RED, title="PRÓXIMO SALTO",
                 big="ESTRELLA DE NEUTRONES" if star_kind(nxt[1]) == "neu" else "ENANA BLANCA",
                 lines=[nxt[0], "al llegar, aléjate de los chorros"], secs=7)
    RW["dang"] = nxt
    fin = (d.get("routen") or len(route), (d.get("routeend") or [""])[0])
    if fin[0] == 2 and RW["fin"] != fin and RW["fin"][0] != 2:
        _xa_show("rutafin", col=BLUE, title="QUEDAN 2 SALTOS", big=(fin[1] or "").upper(), lines=["prepárate para llegar"], secs=6)
    RW["fin"] = fin
    sy = d.get("system")
    if sy and sy != RW["sys"]:
        v = ((FACD["data"] or {}).get("sistemas") or {}).get(sy)
        if v and not v.get("fuera"):
            st_ = (v.get("activos") or []) + (v.get("pendientes") or [])
            bad = "RETIRADA" if "Retreat" in st_ else "ELECCIONES" if "Election" in st_ else "GUERRA" if fac_war(v) else None
            if bad:
                cf = (v.get("conflictos") or [{}])[0]
                _xa_show("rutacdsn", col=RED, title=f"SISTEMA CDSN · {bad}", big=sy.upper(),
                         lines=[f"contra {cf.get('contra')} · {cf.get('ganados') or 0}-{cf.get('perdidos') or 0} días" if cf.get("contra") else
                                f"influencia {v.get('inf', 0):.1f} %".replace(".", ",")], secs=8)
    RW["sys"] = sy

_on_tap_v111 = on_tap

def on_tap(x, y):
    v = ui.get("view")
    if v == 3 and route_tap(x, y):
        TAP_EV.set(); return
    if v == 212:
        tap_rsys(x, y); TAP_EV.set(); return
    return _on_tap_v111(x, y)

_drag_move_v111 = drag_move

def drag_move(p0, p):
    a, b = _to_panel(p0) if p0 else None, _to_panel(p)
    lists = {3: RUT, 213: BGS}
    L = lists.get(ui.get("view"))
    if a and b and L and L.get("r") and L["r"].collidepoint(a) and L.get("max"):
        if not DRAG["on"]:
            if abs(b[1] - a[1]) < 12:
                return
            DRAG.update(on=True, last=b[1], off0=L.get("off", 0), y0=a[1])
        L["off"] = int(max(0, min(L["max"], DRAG["off0"] - (b[1] - DRAG["y0"]) / L.get("rh", 22))))
        TAP_EV.set()
        return
    return _drag_move_v111(p0, p)


# ======================================================================================
# v1.1.1 · FACCIÓN: reglas de alerta como la web, histórico de influencia, tick de respaldo, pestaña BGS
# ======================================================================================
def inf_warn(v):
    """(titulo, detalle) con las mismas reglas que la web cdsn-web (las guerras y elecciones van aparte, en fac_war)."""
    if not v.get("inf") or v.get("fuera"):
        return None
    st_ = (v.get("activos") or []) + (v.get("pendientes") or [])
    if "Retreat" in st_:
        return "RETIRADA", f"influencia {v['inf']:.1f} %".replace(".", ",")
    g = v["inf"] - (v.get("segunda_inf") or 0)
    if v.get("ctrl") and g < 5:
        return "VENTAJA BAJA", f"solo {g:.1f} sobre {v.get('segunda') or 'otra facción'}".replace(".", ",")
    if v.get("prev") is not None and v["prev"] - v["inf"] >= 3:
        return "BAJADA", f"{v['inf'] - v['prev']:.1f} desde ayer".replace(".", ",")
    return None

def _trend(v):
    h = v.get("hinf") or []
    if len(h) >= 2:
        return h[-1][1] - h[-2][1]
    return v["inf"] - v["prev"] if v.get("prev") is not None else 0

def trend_arrow(surf, v, x_, y_):
    t_ = _trend(v)
    if abs(t_) < 0.1:
        return
    up = t_ > 0
    pygame.draw.polygon(surf, GREEN if up else RED,
                        [(x_, y_ + 5), (x_ + 8, y_ + 5), (x_ + 4, y_)] if up else [(x_, y_), (x_ + 8, y_), (x_ + 4, y_ + 5)])

def tick_next(now):
    """Próximo tick como la web: el del sistema mejor medido (±3 h como mucho) o el de la galaxia + 24 h."""
    D = FACD["data"] or {}
    best = None
    for v in (D.get("sistemas") or {}).values():
        p = v.get("tick_prox")
        if not p or v.get("fuera") or v.get("tick_disp") is None or v["tick_disp"] > 180:
            continue
        while p < now - 1800:
            p += 86400
        if best is None or p < best[0]:
            best = (p, v["tick_disp"])
    if best:
        return best
    tg = D.get("tick_global")
    if tg:
        p = tg + 86400
        while p < now - 1800:
            p += 86400
        return p, None
    return None

_ftick_txt_v111 = ftick_txt

def ftick_txt(now):
    if FTICK.get("next") and now - (FTICK.get("t") or 0) < 3 * 3600:
        return _ftick_txt_v111(now)                      # EDCAS (edservertick) responde: como siempre
    tn = tick_next(now)                                  # si no, el del escucha del pueblo
    if not tn:
        return _ftick_txt_v111(now)
    p, w = tn
    w = (w or 30) * 60
    hm = lambda s_: f"{int(s_ // 3600)} h {int(s_ % 3600 // 60):02d} min"
    if now < p - w:
        return "tick en " + hm(p - w - now), BLUE
    if now < p + w:
        return "TICK EN CURSO", GREEN
    return "tick: esperando", DIM

# --- ficha del sistema: pestaña INFLUENCIA con la grafica del historico (hinf) ---
MENU[214] = "SISTEMA DE LA FACCIÓN"
PARENT[214] = 192
for _g in TABS:
    if any(t == 194 for t, _ in _g):
        _g.append((214, "INFLUENCIA"))

def draw_hinf(surf, r, h, now):
    """Grafica en escalones como la de la web (cada punto se mantiene hasta el siguiente cambio)."""
    pygame.draw.rect(surf, (15, 10, 4), r, border_radius=6)
    pygame.draw.rect(surf, DIM, r, 1, border_radius=6)
    if not h or len(h) < 2:
        put(surf, F["small"], "histórico: aprendiendo… (lo guarda el escucha v5)", r.center, DIM, r.w - 16, anchor="center"); return
    t0, t1 = h[0][0], max(h[-1][0] + 3600, now)
    vals = [p[1] for p in h]
    mn, mx = min(vals), max(vals)
    if mx - mn < 2:
        m = (mx + mn) / 2; mn, mx = m - 1, m + 1
    mn -= .5; mx += .5
    X = lambda t: r.x + 34 + (t - t0) / max(1, t1 - t0) * (r.w - 42)
    Y = lambda v: r.y + 6 + (1 - (v - mn) / (mx - mn)) * (r.h - 22)
    pts = []
    for i, (t, v) in enumerate(h):
        xn = X(h[i + 1][0]) if i + 1 < len(h) else r.right - 6
        pts += [(X(t), Y(v)), (xn, Y(v))]
    pygame.draw.lines(surf, ORANGE, False, pts, 2)
    for t, v in h:
        pygame.draw.circle(surf, ORANGE, (int(X(t)), int(Y(v))), 2)
    f = lambda t: time.strftime("%d/%m", time.localtime(t))
    put(surf, F["tiny"], f"{mx:.1f}".replace(".", ","), (r.x + 3, r.y + 3), DIM)
    put(surf, F["tiny"], f"{mn:.1f}".replace(".", ","), (r.x + 3, r.bottom - 26), DIM)
    put(surf, F["tiny"], f(t0), (r.x + 34, r.bottom - 13), DIM)
    put(surf, F["tiny"], f(t1), (r.right - 6, r.bottom - 13), DIM, anchor="topright")

def view_facinf(surf, d, flags, now):
    D, name, v = fs_get()
    if not v:
        put(surf, F["btn"], "sin datos", (W // 2, H // 2), DIM, anchor="center"); return
    y = fs_head(surf, d, v, name)
    h = [list(p) for p in v.get("hinf") or []]
    draw_hinf(surf, pygame.Rect(6, y, W - 12, 120), h, now)
    y += 126
    put(surf, F["small"], "ÚLTIMOS CAMBIOS", (8, y), DIM); y += 16
    for i in range(len(h) - 1, max(0, len(h) - 5) - 1, -1):
        t, val = h[i]
        dv = val - h[i - 1][1] if i > 0 else None
        put(surf, F["small"], time.strftime("%d/%m %H:%M", time.localtime(t)), (8, y), DIM)
        put(surf, F["small"], f"{val:.1f} %".replace(".", ","), (130, y), ORANGE)
        if dv is not None:
            put(surf, F["small"], f"{dv:+.1f}".replace(".", ","), (200, y), GREEN if dv > 0 else RED)
        y += 15
        if y > H - 46:
            break
    draw_button(surf, BACK_R, "< VOLVER", None, F["small"], compact=True)
    ir_draw(surf, now)

VIEWS[214] = view_facinf

def facinf_tap(x, y):
    if BACK_R.collidepoint(x, y):
        ui["view"] = ui.get("facback", 192)
    elif IR_R.inflate(6, 6).collidepoint(x, y):
        D, name, vv = fs_get()
        if name:
            tap_flash(("ir", 0)); ir_send(name)


# --- pestaña BGS: la web cdsn-web en el panel ---
MENU[213] = "BGS"
PARENT[213] = 0
for _g in TABS:
    if any(t == 193 for t, _ in _g):
        _g.append((213, "BGS"))
BGS = {"off": 0, "max": 0, "r": None, "rh": 17, "orden": "inf", "asc": False, "solo": None, "rows": [], "heads": [], "btn": []}
BGS_COLS = [("sys", "SISTEMA", 118, "l"), ("inf", "INFL.", 40, "r"), ("d", "AYER", 34, "r"), ("vent", "VENT.", 36, "r"),
            ("est", "ESTADOS", 74, "l"), ("conf", "ALERTA", 78, "l"), ("traf", "VIS.", 26, "r"),
            ("pob", "POBL.", 44, "r"), ("pp", "POWERPLAY", 66, "l"), ("t", "DATO", 32, "r"), ("tick", "TICK", 34, "r")]

_BGSF = {}

def _bgs_full():
    """Dibujando a la resolucion real de una HDMI grande (NITIDEZ ALTA): letra mas pequeña y las 11 columnas."""
    f = F.get("tiny")
    return bool(HI_PASS[0]) and isinstance(f, FontProxy) and f.f >= 1.9

def _bgs_font():
    if not _bgs_full():
        return F["tiny"]
    sc = F["tiny"].f
    size = max(8, int(round(10.5 * sc)))
    if size not in _BGSF:
        _BGSF[size] = pygame.font.Font(None, size)
    return FontProxy(_BGSF[size], size / 10.5)

def _bgs_cols():
    """En la HDMI con NITIDEZ ALTA caben las 11 columnas; si no, sin población, Powerplay y dato."""
    full = _bgs_full()
    return [c for c in BGS_COLS if full or c[0] not in ("pob", "pp", "t")]

def bgs_rows(now):
    D = FACD["data"] or {}
    hoy = time.strftime("%Y-%m-%d", time.gmtime())
    out = []
    for s in (D.get("sistemas") or {}).values():
        if s.get("fuera") or s.get("inf") is None:
            continue
        cf = (s.get("conflictos") or [{}])[0]
        war = fac_war(s)
        w_ = inf_warn(s)
        niv, al = (2, ("ELECC." if (cf.get("tipo") or "").lower() == "election" else "GUERRA") + (f" {cf.get('ganados') or 0}-{cf.get('perdidos') or 0}" if cf else "")) if war else \
                  (2 if w_[0] in ("RETIRADA", "VENTAJA BAJA") else 1, w_[0]) if w_ else \
                  (1, "EXPANSIÓN") if "Expansion" in (s.get("pendientes") or []) else (0, "")
        p = s.get("tick_prox") or 0
        while p and p < now - 1800:
            p += 86400
        out.append({"s": s, "sys": s["sys"], "inf": s["inf"], "d": (s["inf"] - s["prev"]) if s.get("prev") is not None else None,
                    "vent": s["inf"] - (s.get("segunda_inf") or 0), "niv": niv, "conf": al,
                    "est": ", ".join([ES_ST.get(x, x) for x in s.get("activos") or []] + [ES_ST.get(x, x) + " (p)" for x in s.get("pendientes") or []]),
                    "traf": (s.get("trafico") or {}).get(hoy, 0), "pob": (s.get("sis") or {}).get("pob") or 0,
                    "pp": (s.get("pp") or {}).get("pot") or "", "t": s.get("t") or 0, "tick": p})
    return out

def view_bgs(surf, d, flags, now):
    R = bgs_rows(now)
    tot, ctl = len(R), sum(1 for r in R if r["s"].get("ctrl"))
    al, traf = sum(1 for r in R if r["niv"]), sum(r["traf"] for r in R)
    tn = tick_next(now)
    cards = [("SISTEMAS", str(tot), WHITE), ("CONTROL.", str(ctl), ORANGE), ("ALERTAS", str(al), RED if al else GREEN),
             ("TRÁFICO HOY", str(traf), BLUE), ("PRÓX. TICK", "~" + time.strftime("%H:%M", time.localtime(tn[0])) if tn else "—", MERC)]
    cw = (W - 12) // len(cards)
    for i, (a, b, c) in enumerate(cards):
        r = pygame.Rect(6 + i * cw, TOP + 2, cw - 4, 30)
        pygame.draw.rect(surf, (26, 18, 8), r, border_radius=5)
        put(surf, F["tiny"], a, (r.x + 5, r.y + 2), GREEN)
        put(surf, F["btn"], b, (r.right - 5, r.y + 10), c, anchor="topright")
    y = TOP + 36
    BGS["btn"] = []
    for i, (k, lab) in enumerate((("ctrl", "solo controlados"), ("al", "solo alertas"))):
        r = pygame.Rect(6 + i * 110, y, 104, 16)
        on = BGS["solo"] == k
        pygame.draw.rect(surf, ORANGE if on else BLACK, r, border_radius=4)
        pygame.draw.rect(surf, ORANGE if on else DIM, r, 1, border_radius=4)
        put(surf, F["tiny"], lab, r.center, BLACK if on else DIM, anchor="center")
        BGS["btn"].append((r, k))
    if BGS["solo"] == "ctrl":
        R = [r for r in R if r["s"].get("ctrl")]
    elif BGS["solo"] == "al":
        R = [r for r in R if r["niv"]]
    put(surf, F["tiny"], f"{len(R)} de {tot} · toca una cabecera para ordenar", (W - 6, y + 2), DIM, anchor="topright")
    y += 20
    cols = _bgs_cols()
    f = _bgs_font()
    BGS["rh"] = 12 if _bgs_full() else 17
    k = BGS["orden"]
    def _key(r):
        val = r["niv"] if k == "conf" else r[k]
        if k in ("sys", "est", "pp"):
            return str(val).lower()
        return val if val is not None else -1e9
    R.sort(key=_key, reverse=not BGS["asc"])
    sc = (W - 12) / sum(c[2] for c in cols)
    xs, x = [], 6
    BGS["heads"] = []
    for c in cols:
        w = c[2] * sc
        xs.append((x, w))
        on = c[0] == k
        put(surf, f, c[1], (x + (w - 2 if c[3] == "r" else 2), y),
            ORANGE if on else GREEN, int(w), anchor="topright" if c[3] == "r" else "topleft")
        BGS["heads"].append((pygame.Rect(int(x), y - 2, int(w), 16), c[0]))
        x += w
    y += 14
    pygame.draw.line(surf, DIM, (6, y), (W - 6, y)); y += 2
    rh = BGS["rh"]
    nvis = max(1, (H - y - 4) // rh)
    BGS["max"] = max(0, len(R) - nvis)
    BGS["off"] = max(0, min(BGS["off"], BGS["max"]))
    BGS["r"] = pygame.Rect(0, y, W, nvis * rh)
    BGS["rows"] = []
    for r in R[BGS["off"]:BGS["off"] + nvis]:
        s = r["s"]
        if r["niv"]:
            pygame.draw.line(surf, RED if r["niv"] == 2 else YELLOW, (2, y + 1), (2, y + rh - 3), 3)
        if s.get("ctrl"):                                # cuadrado = controlado (como en la web)
            pygame.draw.rect(surf, ORANGE, (int(xs[0][0]) + 2, y + rh // 2 - 3, 5, 5))
        vals = {"sys": ("   " + s["sys"], ORANGE if s.get("ctrl") else WHITE),
                "inf": (f"{r['inf']:.1f}".replace(".", ","), WHITE),
                "d": ("—" if r["d"] is None else f"{r['d']:+.1f}".replace(".", ","), GREEN if (r["d"] or 0) > 0 else RED if (r["d"] or 0) < 0 else DIM),
                "vent": (f"{r['vent']:.1f}".replace(".", ","), RED if r["vent"] < 5 else WHITE if r["vent"] < 15 else GREEN),
                "est": (r["est"] or "—", DIM), "conf": (r["conf"], RED if r["niv"] == 2 else YELLOW),
                "traf": (str(r["traf"] or "—"), BLUE), "pob": (fnum_pob(r["pob"]) if r["pob"] else "—", DIM),
                "pp": (r["pp"] or "—", DIM), "t": (_hace(now - r["t"]) if r["t"] else "—", DIM),
                "tick": ("~" + time.strftime("%H:%M", time.localtime(r["tick"])) if r["tick"] else "—", MERC)}
        for (x, w), c in zip(xs, cols):
            t_, col = vals[c[0]]
            put(surf, f, t_, (x + (w - 2 if c[3] == "r" else 2), y + 2), col, int(w) - 3,
                anchor="topright" if c[3] == "r" else "topleft")
        BGS["rows"].append((pygame.Rect(0, y, W, rh), s["sys"]))
        y += rh
    if BGS["max"]:
        put(surf, F["tiny"], f"{BGS['off'] + 1}-{min(len(R), BGS['off'] + nvis)} de {len(R)} · arrastra", (W - 6, H - 12), DIM, anchor="topright")

def tap_bgs(x, y):
    for r, k in BGS["btn"]:
        if r.collidepoint(x, y):
            BGS["solo"] = None if BGS["solo"] == k else k; BGS["off"] = 0; return
    for r, k in BGS["heads"]:
        if r.collidepoint(x, y):
            if BGS["orden"] == k:
                BGS["asc"] = not BGS["asc"]
            else:
                BGS["orden"], BGS["asc"] = k, k == "sys"
            return
    for r, n in BGS["rows"]:
        if r.collidepoint(x, y):
            ui["facsys"] = n; ui["facback"] = 213; ui["view"] = 194; return

VIEWS[213] = view_bgs

_on_tap_v111b = on_tap

def on_tap(x, y):
    v = ui.get("view")
    if v == 213 and y > TOP:
        tap_bgs(x, y); TAP_EV.set(); return
    if v == 214 and y > TOP:
        facinf_tap(x, y); TAP_EV.set(); return
    return _on_tap_v111b(x, y)


# ======================================================================================
# v1.1.1 · COLONIZACIÓN: «dónde comprar hoy», MERCADO en la ventana 3 y aviso con los datos del juego
# ======================================================================================
COMPRAS_FILE = os.path.join(PANEL_DIR, "compras_hoy.json")
COMPRAS = {"day": None, "list": [], "t": 0, "rows": [], "line": None}

def _compras_load():
    try:
        with open(COMPRAS_FILE, encoding="utf-8") as f_:
            COMPRAS.update(json.load(f_))
    except (OSError, ValueError):
        pass

def _compras_day():
    hoy = time.strftime("%Y-%m-%d")
    if COMPRAS.get("day") != hoy:
        COMPRAS.update(day=hoy, list=[])
    return COMPRAS["list"]

def compras_add(st, sy, items):
    L = _compras_day()
    e = next((x for x in L if x["st"] == st and x["sys"] == sy), None)
    if e and set(e["items"]) == set(items):
        return
    if e:
        L.remove(e)
    L.append({"st": st, "sys": sy, "items": items[:8], "t": time.time()})
    del L[:-12]
    try:
        with open(COMPRAS_FILE + ".tmp", "w", encoding="utf-8") as f_:
            json.dump({"day": COMPRAS["day"], "list": L}, f_, ensure_ascii=False)
        os.replace(COMPRAS_FILE + ".tmp", COMPRAS_FILE)
    except OSError:
        pass
    plog(f"Colonización: {st} ({sy}) vende {', '.join(items[:5])}")

_compras_load()

def col_sells_here(d):
    """Construcción pendiente y la estación donde estás atracado vende algo de lo que le falta: [nombres]."""
    if not (d or {}).get("Flags", 0) & 1 or ((d or {}).get("colonia") or {}).get("dock"):
        return []
    x, need = _col_need_keys(d)
    if not need:
        return []
    here = col_here(d)
    return [t[0] for t in need if _hh(here, t[0], t[1]) is not None]

_mkt_show_v111 = mkt_show

def mkt_show(d):
    if _mkt_show_v111(d):
        return True
    try:
        return cfg.get("mkt", "CON CARGA") != "NUNCA" and bool(col_sells_here(d))
    except Exception:
        return False

def col_hoy_watch(now):
    if now - COMPRAS["t"] < 3:
        return
    COMPRAS["t"] = now
    with lock:
        d, rx = state["data"], state["rx"]
    if not d or now - rx > 5:
        return
    if not d.get("Flags", 0) & 1:
        CBW["okmid"] = None
        return
    have = col_sells_here(d)
    if not have:
        return
    st = (d.get("station") or {})
    compras_add(st.get("name") or "?", d.get("system") or "?", have)
    mid = st.get("mid")
    B = d.get("colbuy") or {}
    edsm_ok = str(B.get("mid")) == str(mid) and B.get("status") == "ok"
    if CBW.get("okmid") != mid and not edsm_ok and COLHS.get("src") == "juego":
        CBW["okmid"] = mid                               # EDSM no avisó: aviso con los datos del mercado del juego
        _col_alert(f"AQUÍ HAY {len(have)} MATERIAL{'ES' if len(have) != 1 else ''} DE COLONIZACIÓN",
                   ", ".join(have[:3]) + ("…" if len(have) > 3 else "") + f" · {st.get('name') or ''}", GREEN)
    elif edsm_ok:
        CBW["okmid"] = mid

# RESUMEN DEL DÍA: línea «DÓNDE COMPRAR HOY» y su lista (tocando la línea)
_view11_v111 = VIEWS[11]

def view11_v111(surf, d, flags, now):
    L = _compras_day()
    COMPRAS["line"] = None
    if ui.get("sesstab") == 2:
        put(surf, F["btn"], "DÓNDE COMPRAR HOY · materiales de colonización", (8, TOP + 4), GREEN, W - 16)
        y = TOP + 28
        COMPRAS["rows"] = []
        if not L:
            put(surf, F["small"], "todavía ninguna estación hoy", (8, y), DIM)
        for e in sorted(L, key=lambda e: -e["t"])[:7]:
            put(surf, F["btn"], f"{e['st']}", (8, y), ORANGE, W - 70)
            put(surf, F["small"], time.strftime("%H:%M", time.localtime(e["t"])), (W - 8, y + 2), DIM, anchor="topright")
            put(surf, F["small"], f"{e['sys']} · " + ", ".join(e["items"]), (8, y + 19), GREEN, W - 16)
            COMPRAS["rows"].append((pygame.Rect(0, y, W, 36), e["sys"]))
            y += 38
        put(surf, F["tiny"], "toca una estación para copiar su sistema en el PC · toca fuera para volver", (W // 2, H - 10), DIM, W - 16, anchor="center")
        return
    _view11_v111(surf, d, flags, now)
    if L and not ui.get("sesstab"):
        r = pygame.Rect(8, 270, W - 120, 18)
        pygame.draw.rect(surf, BLACK, r)
        put(surf, F["small"], f"DÓNDE COMPRAR HOY ({len(L)}): " + ", ".join(e["st"] for e in L[-3:]) + "  >", (r.x, r.y + 1), GREEN, r.w)
        COMPRAS["line"] = r

VIEWS[11] = view11_v111

_on_tap_v111c = on_tap

def on_tap(x, y):
    if ui.get("view") == 11 and y > TOP:
        if ui.get("sesstab") == 2:
            for r, sy in COMPRAS.get("rows") or []:
                if r.collidepoint(x, y):
                    ir_send(sy); TAP_EV.set(); return
            ui["sesstab"] = 0; TAP_EV.set(); return
        if COMPRAS.get("line") and COMPRAS["line"].inflate(0, 6).collidepoint(x, y) and not (LEDB.get("r") and LEDB["r"].collidepoint(x, y)):
            ui["sesstab"] = 2; TAP_EV.set(); return
    return _on_tap_v111c(x, y)

_render_v111 = render

def render(surf):
    r_ = _render_v111(surf)
    now = time.time()
    for fn, nm in ((route_watch, "ruta"), (col_hoy_watch, "colonia hoy")):
        try:
            fn(now)
        except Exception as e:
            log_exc(nm, e)
    return r_
