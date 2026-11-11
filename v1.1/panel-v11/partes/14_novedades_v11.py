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
