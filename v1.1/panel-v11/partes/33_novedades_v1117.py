# Panel Elite v1.1 · parte 33: novedades v1.1.17
#   MERCADO <-> PARA TU COLONIA: si te falta material de tu construcción, un toque en MERCADO (panel o cuadro de la
#     HDMI) enseña lo que vende esta estación para tu colonia; otro toque vuelve al MERCADO. Marca «COLONIA ›».
#   Avisos de colonia: «NO VENDAS AQUÍ LOS MATERIALES QUE LLEVAS DE COLONIZACIÓN» y, cuando ya lo llevas todo,
#     «TODOS LOS MATERIALES COMPRADOS · ENTRÉGALOS EN DESTINO» (con su número, pitido, voz y robot).
#   PASAJEROS: cabina dibujada en el cuadro 4 de la HDMI mientras los llevas y en la pantalla del robot al embarcar
#     y desembarcar.
#   LLEGADA AL SISTEMA con su propia línea (y número) en ALERTAS.
#   INGENIEROS: aviso al desbloquear uno o subir de rango.
#   ROBOT: «¿cómo consigo el permiso de X?», mercancías raras, «¿qué versiones tienes?», órdenes por voz (los
#     arriesgados piden «sí»), duérmete / despierta, repite, calla; oído siempre listo en la Pi 4, lista de palabras
#     de Vosk, frases fijas guardadas; se duerme si llevas 15 min parado; cara de fuego con sobrecalentamiento,
#     cara marrón con la bodega llena y doble toque en la cabeza para quitar el último aviso (robot v1.1.17).
EV_LIST.extend([("arrsys", "LLEGADA AL SISTEMA"), ("coltodo", "COLONIA: TODO COMPRADO"),
                ("paxcabina", "PASAJEROS: CABINA (HDMI Y ROBOT)"), ("engunlock", "INGENIERO DESBLOQUEADO / RANGO"),
                ("robcmd", "ROBOT: ÓRDENES POR VOZ"), ("robparado", "ROBOT: DORMIR SI ESTÁS PARADO 15 MIN"),
                ("robvosk", "ROBOT: OÍDO SIEMPRE LISTO (PI 4)")])
for _i, (_k, _n) in enumerate(EV_LIST):
    if _k == "arrive":
        EV_LIST[_i] = ("arrive", "LLEGADA A ESTACIÓN / SEÑAL")

def _v1117_migra():
    """Quien tenía apagado «LLEGADA / SEÑAL» tiene también apagada la llegada al sistema (eran el mismo)."""
    for st in ("ev", "snd"):
        m = cfg.get(st) or {}
        if "arrsys" not in m and m.get("arrive") is False:
            cfg.setdefault(st, {})["arrsys"] = False
try:
    _v1117_migra()
except Exception as _e:
    print("migración v1.1.17:", _e)

SENDER_OK, ROBOT_OK = "v1.0b16", "v1.1.17"
SENDER_REQ = SENDER_OK                                   # el aviso VERSIONES DISTINTAS pide ya el b16

# arreglo: los avisos grandes (LLEGADA, SEÑAL, INTERDICCIÓN...) no hacían caso de ALERTAS desde la v1.0b10
def _xa_set(self, k, v):
    if k == "a" and v is not None and XA_K[0] and not ev_on(XA_K[0]):
        return
    if k == "a" and isinstance(v, dict) and "ev" not in v and XA_K[0]:
        v["ev"] = XA_K[0]
    dict.__setitem__(self, k, v)

_XA.__setitem__ = _xa_set

# ===============================================================================================================
# 1) COLONIZACIÓN
# ===============================================================================================================
MKC = {"st": None}

def col_activa(d):
    C, L, i = col_pick(d)
    if not L:
        return C, None
    return C, next((y for y in L if not y.get("done") and not y.get("fail")), None)

def col_falta(d):
    """Lo que falta de verdad de tu construcción (descontada la bodega): [(nombre, falta)]."""
    C, x = col_activa(d)
    if not x:
        return []
    return [(t[0], t[5]) for t in col_rows(d, x) if t[5] > 0]

def mkcol_on(d):
    st = ((d or {}).get("station") or {}).get("mid")
    if st != MKC["st"]:
        MKC["st"] = st
        ui["mkcol"] = False                                # otra estación: vuelve el MERCADO
    return bool(ui.get("mkcol")) and bool(col_falta(d))

def draw_mkcol(surf, d, now):
    y = TOP + 4
    put(surf, F["btn"], "PARA TU COLONIA · SE VENDE AQUÍ", (8, y), GREEN, W - 110)
    y += 26
    try:
        rows = col_big_rows(d, now)
    except Exception:
        rows = []
    if rows:
        cols = (8, 230, 300, 390)
        for x_, t_ in zip(cols, ("MATERIAL", "FALTA", "PRECIO", "HAY")):
            put(surf, F["tiny"], t_, (x_, y), DIM)
        y += 15
        pygame.draw.line(surf, (0, 90, 30), (6, y), (W - 6, y), 1)
        y += 3
        caben = max(1, (H - 22 - y) // 19)
        for name, stock, price, falta in rows[:caben]:
            put(surf, F["small"], name, (cols[0], y), GREEN, cols[1] - cols[0] - 6)
            put(surf, F["small"], f"{falta:,} t".replace(",", "."), (cols[1], y), ORANGE)
            put(surf, F["small"], f"{price:,}".replace(",", "."), (cols[2], y), WHITE)
            put(surf, F["small"], f"{stock:,} t".replace(",", "."), (cols[3], y), WHITE if stock >= falta else ORANGE)
            y += 19
        if len(rows) > caben:
            put(surf, F["tiny"], f"+{len(rows) - caben} más en COLONIZACIÓN", (8, y), DIM)
    else:
        put(surf, F["btn"], "Aquí no venden nada de lo que te falta", (8, y), ORANGE, W - 16); y += 24
        m_ = {}
        try:
            m_ = market_pick(d, now)
        except Exception:
            pass
        if m_.get("missing") or m_.get("src") == "EDSM" or m_.get("other"):
            put(surf, F["small"], "abre el mercado en el juego para comprobarlo", (8, y), DIM, W - 16); y += 18
        x, need = _col_need_keys(d)
        alt = _col_alt(d, need, str(((d or {}).get("station") or {}).get("mid"))) if need else None
        if alt:
            put(surf, F["small"], f"prueba en {alt[0]}: {', '.join(alt[1][:3])}", (8, y), GREEN, W - 16); y += 20
        y += 4
        put(surf, F["tiny"], "TE FALTA", (8, y), DIM); y += 15
        for name, falta in col_falta(d)[:max(1, (H - 22 - y) // 17)]:
            put(surf, F["small"], name, (8, y), ORANGE, 300)
            put(surf, F["small"], f"{falta:,} t".replace(",", "."), (W - 10, y), ORANGE, anchor="topright")
            y += 17
    car = _col_carried(d)
    if car:
        put(surf, F["tiny"], f"llevas {sum(c[2] for c in car):,} t para la construcción".replace(",", "."), (8, H - 16), BLUE)
    put(surf, F["tiny"], "toca: MERCADO", (W - 8, H - 16), DIM, anchor="topright")

def _marca_col(surf, txt):
    r = pygame.Rect(W - 98, TOP + 2, 94, 18)
    pygame.draw.rect(surf, BLACK, r, border_radius=4)
    pygame.draw.rect(surf, GREEN, r, 1, border_radius=4)
    put(surf, F["tiny"], txt, r.center, GREEN, anchor="center")

def _banda_no_vendas(surf, d, now):
    """La franja de abajo del MERCADO (v1.1.11) con el texto nuevo."""
    m = (d or {}).get("market") or {}
    sell = m.get("sell") or []
    if not sell:
        return
    tot = sum(r[1] * r[2] for r in sell)
    medio = sum(r[1] * r[3] for r in sell if len(r) > 3 and r[3])
    col_ = mkt_para_colonia(d)
    if col_:
        txt, c_ = "NO VENDAS AQUÍ LOS MATERIALES DE COLONIZACIÓN", ORANGE
    elif medio and tot < medio * 0.95:
        txt, c_ = f"VENDIENDO TODO: {cr(tot)} cr ({100 * tot / medio - 100:+.0f} %: aquí pagan poco)", ORANGE
    else:
        return
    pygame.draw.rect(surf, BLACK, (0, H - 38, W, 26))
    if col_ and int(now * 2) % 2:
        pygame.draw.rect(surf, (60, 30, 0), (4, H - 38, W - 8, 24), border_radius=4)
    put_fit(surf, ("btn", "small"), txt, (8, H - 36), c_, W - 16)

def view127_v1117(surf, d, flags, now):
    if mkcol_on(d):
        draw_mkcol(surf, d, now)
        _marca_col(surf, "‹ MERCADO")
        return
    _view127_v1111(surf, d, flags, now)                   # el MERCADO de siempre (sin la franja de la v1.1.11)
    _banda_no_vendas(surf, d, now)
    if col_falta(d):
        _marca_col(surf, "COLONIA ›")

VIEWS[127] = view127_v1117

def col_nosell(d, mk):
    """Al abrir el mercado fuera del depósito con carga que le falta a tu construcción (una vez por atraque)."""
    if CBW.get("warn") == mk.get("mid"):
        return
    car = _col_carried(d)
    if not car:
        return
    CBW["warn"] = mk.get("mid")
    tot = sum(c[2] for c in car)
    _col_red("NO VENDAS AQUÍ LOS MATERIALES QUE LLEVAS DE COLONIZACIÓN",
             f"{tot:,} t: ".replace(",", ".") + ", ".join(c[0] for c in car[:3]) + ("…" if len(car) > 3 else ""),
             "no vendas aquí los materiales que llevas de colonización")

COLT = {"k": None}

def col_todo_watch(d):
    C, x = col_activa(d)
    if not x:
        COLT["k"] = None; return
    rows = col_rows(d, x)
    listo = bool(rows) and all(t[5] == 0 for t in rows) and any(t[4] > 0 for t in rows)
    if not listo:
        COLT["k"] = None; return                           # vuelve a faltar algo (o ya lo has entregado): se rearma
    if C.get("dock") == x.get("mid"):
        return                                             # ya estás en el depósito: allí sale ENTREGA AQUÍ
    k = (x.get("mid"), sum(t[4] for t in rows))
    if COLT["k"] is None:
        COLT["k"] = k
        aviso_num("coltodo", "TODOS LOS MATERIALES COMPRADOS", "entrégalos en destino: " + (x.get("st") or x.get("sys") or "tu construcción"),
                  GREEN, 8)

# ===============================================================================================================
# 2) PASAJEROS: cabina dibujada (cuadro 4 de la HDMI y robot)
# ===============================================================================================================
MENU[217] = "PASAJEROS"
PARENT[217] = 4
PAX_SEATS = {(1, 2): 2, (1, 3): 4, (1, 4): 8, (1, 5): 16, (1, 6): 32, (2, 3): 3, (2, 4): 6, (2, 5): 10, (2, 6): 16,
             (3, 4): 3, (3, 5): 6, (3, 6): 12, (4, 5): 4, (4, 6): 8}
PAX_CLS = {1: "ECONÓMICA", 2: "BUSINESS", 3: "PRIMERA", 4: "LUJO"}

def pax_cabinas(d):
    """[(clase 1-4, plazas)] de las cabinas de la nave actual (de la ficha NAVE)."""
    c = ((d or {}).get("naves") or {}).get("cur") or {}
    out = []
    for m in c.get("mods") or []:
        if "pasajeros" not in (m.get("n") or "").lower():
            continue
        s = (m.get("s") or "").strip()
        if len(s) >= 2 and s[0].isdigit() and s[1] in "ABCD":
            cl, sz = "ABCD".index(s[1]) + 1, int(s[0])
            out.append((cl, PAX_SEATS.get((cl, sz), sz)))
    return out

def pax_resumen(d):
    L = pax_list(d)
    n = sum(p.get("n", 0) for p in L)
    cab = pax_cabinas(d)
    plazas = max(n, sum(p for _, p in cab))
    cl = max((c for c, _ in cab), default=0)
    nv = sum(p.get("n", 0) for p in L if p.get("vip") and not p.get("wanted"))
    nw = sum(p.get("n", 0) for p in L if p.get("wanted"))
    return L, n, plazas, cl, nv, nw

def dibuja_cabina(S, r, n, plazas, nv=0, nw=0, col=None):
    """Cabina vista desde arriba: filas de asientos; ocupados en naranja, VIP en azul y buscados en rojo."""
    col = col or ORANGE
    pygame.draw.rect(S, (20, 12, 4), r, border_radius=max(6, r.h // 6))
    pygame.draw.rect(S, col, r, 2, border_radius=max(6, r.h // 6))
    plazas = max(1, min(plazas, 40))
    n = min(n, plazas)
    colores = [RED] * min(nw, n) + [BLUE] * min(nv, max(0, n - nw)) + [col] * max(0, n - nw - nv)
    filas = 2 if plazas <= 8 else 4
    porfila = (plazas + filas - 1) // filas
    pasillo = r.h // (6 if filas == 2 else 8)
    alto = (r.h - 16 - pasillo) // filas
    paso = (r.w - 24) / max(1, porfila)
    ancho = max(6, min(int(paso * 0.62), int(alto * 1.3)))
    k = 0
    for f in range(filas):
        yy = r.y + 8 + f * alto + (pasillo if f >= filas // 2 else 0)
        for c in range(porfila):
            if k >= plazas:
                break
            cx = int(r.x + 12 + paso * c + paso / 2)
            seat = pygame.Rect(cx - ancho // 2, yy + 2, ancho, alto - 4)
            if k < n:
                pygame.draw.rect(S, colores[k], seat, 0, border_radius=max(2, seat.w // 4))
                pygame.draw.rect(S, BLACK, (seat.x + 3, seat.bottom - max(3, seat.h // 4), seat.w - 6, 2))
                pygame.draw.circle(S, BLACK, (seat.centerx, seat.y + seat.h // 3), max(2, min(seat.w, seat.h) // 4))
            else:
                pygame.draw.rect(S, (90, 50, 0), seat, 1, border_radius=max(2, seat.w // 4))
            k += 1
    for i in range(6):                                     # ventanillas
        wx = r.x + 14 + i * (r.w - 28) // 6
        pygame.draw.line(S, (90, 160, 255), (wx, r.y + 3), (wx + max(4, r.w // 30), r.y + 3), 2)
        pygame.draw.line(S, (90, 160, 255), (wx, r.bottom - 4), (wx + max(4, r.w // 30), r.bottom - 4), 2)

def view_cabina(surf, d, flags, now):
    L, n, plazas, cl, nv, nw = pax_resumen(d)
    vip, wanted = nv > 0, nw > 0
    if not L:
        put(surf, F["btn"], "Sin pasajeros a bordo", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    y = TOP + 4
    tit = f"{n} PASAJERO{'S' if n != 1 else ''}" + (f" · {n}/{plazas} PLAZAS" if plazas > n else "") + \
          (f" · {PAX_CLS[cl]}" if cl in PAX_CLS else "")
    put(surf, F["btn"], tit, (8, y), ORANGE, W - 16)
    y += 24
    dibuja_cabina(surf, pygame.Rect(8, y, W - 16, 112), n, plazas, nv, nw)
    y += 118
    for p in L[:3]:
        left = (p.get("exp") or 0) - now
        t_ = f"{p.get('n', 0)} {pax_label(p)} -> {p.get('st') or p.get('sys') or '?'}"
        c_ = RED if p.get("wanted") else BLUE if p.get("vip") else WHITE
        put(surf, F["small"], t_, (8, y), c_, W - 150)
        put(surf, F["small"], f"{cr(p.get('cr', 0))} cr · " + (fmt_time(left) if p.get("exp") else "--"),
            (W - 8, y), RED if p.get("exp") and left < 1800 else GREEN, anchor="topright")
        y += 18
    if len(L) > 3:
        put(surf, F["tiny"], f"+{len(L) - 3} misiones más en 4 CARGA/MISIÓN", (8, y), DIM)
    marcas = [t for t, on in (("VIP", vip), ("BUSCADOS", wanted)) if on]
    if marcas:
        put(surf, F["small"], " · ".join(marcas), (W - 8, TOP + 6), RED if wanted else BLUE, anchor="topright")

VIEWS[217] = view_cabina

_big_cell_v1117 = big_cell
BCM = {"t": 0.0, "mode": ""}

def big_cell(S, cell, v, d, flags, now, r, font, how, extra=""):
    try:
        if pax_list(d) and ev_on("paxcabina") and not COLBIG.get("on"):
            bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
            ch = (bh - 44) // 2
            if r.x >= bw // 2 - 2 and r.y >= 44 + ch - 2:   # cuadro 4 (abajo a la derecha)
                if now - BCM["t"] > 1:
                    BCM["t"], BCM["mode"] = now, big_mode(d, flags)
                if BCM["mode"] not in ("COMBATE", "COMBATE A PIE", "ATRAQUE"):
                    v = 217
    except Exception as e:
        log_exc("cabina en el cuadro 4", e)
    return _big_cell_v1117(S, cell, v, d, flags, now, r, font, how, extra)

# robot: la cabina en su pantalla al embarcar y desembarcar
PAXR = {"n": None}

def cabina_jpg(spec):
    try:
        n, plazas, cl, nv, nw = (int(x) for x in spec.split(":")[1:6])
    except ValueError:
        n, plazas, cl, nv, nw = 1, 1, 0, 0, 0
    S_ = pygame.Surface((320, 240)); S_.fill(BLACK)
    dibuja_cabina(S_, pygame.Rect(10, 30, 300, 150), n, plazas, nv, nw)
    f_ = pygame.font.Font(None, 26)
    S_.blit(f_.render(f"{n}/{plazas} " + PAX_CLS.get(cl, "PASAJEROS"), True, ORANGE), (12, 6))
    return jpg_bytes(S_)

_sc_foto_file_v1117 = sc_foto_file

def sc_foto_file(f):
    if f.startswith("cabina:"):
        return f
    return _sc_foto_file_v1117(f)

_sc_foto_jpg_v1117 = sc_foto_jpg

def sc_foto_jpg(f):
    if f.startswith("cabina:"):
        if f not in SC_FOTO["cache"]:
            if len(SC_FOTO["cache"]) > 20:
                SC_FOTO["cache"].clear()
            SC_FOTO["cache"][f] = cabina_jpg(f)
        return SC_FOTO["cache"][f]
    return _sc_foto_jpg_v1117(f)

def pax_robot_watch(d):
    L, n, plazas, cl, nv, nw = pax_resumen(d)
    old, PAXR["n"] = PAXR["n"], n
    if old is None or n == old or not cfg.get("stackchan") or not ev_on("paxcabina"):
        return
    spec = f"cabina:{n}:{max(plazas, 1)}:{cl}:{nv}:{nw}"
    if n > old:
        sc_foto(spec, "PASAJEROS A BORDO", f"suben {n - old} · {n} a bordo", 6)
    else:
        sc_foto(spec, "DESEMBARCO", f"bajan {old - n}" + (f" · quedan {n}" if n else " · cabina vacía"), 6)

# ===============================================================================================================
# 3) INGENIEROS: desbloqueado o sube de rango
# ===============================================================================================================
INGW = {"p": None}

def ing_watch(d):
    P = (d or {}).get("engprog")
    if not isinstance(P, dict) or not P:
        return
    old, INGW["p"] = INGW["p"], {k: list(v) if isinstance(v, (list, tuple)) else v for k, v in P.items()}
    if old is None:
        return
    for k, v in P.items():
        o = old.get(k)
        prog, rank = (v[0], v[1]) if isinstance(v, (list, tuple)) and len(v) > 1 else (v, None)
        oprog, orank = (o[0], o[1]) if isinstance(o, (list, tuple)) and len(o) > 1 else (o, None)
        nombre = k.title()
        if prog == "Unlocked" and oprog != "Unlocked":
            aviso_num("engunlock", "INGENIERO DESBLOQUEADO", nombre + (f" · rango {rank}" if rank else ""), GREEN, 8)
            return
        if rank and orank and rank > orank:
            aviso_num("engunlock", f"INGENIERO: RANGO {rank}", nombre, GREEN, 6)
            return

# ===============================================================================================================
# 4) ROBOT: hola con sobrecalentamiento, bodega llena y «parado 15 min»
# ===============================================================================================================
ROBM = {"zzz": False, "sig": None, "t": time.time()}

def parado_watch(d, now):
    sig = (d.get("system"), d.get("Flags"), d.get("Flags2"), d.get("gui"), max([n[0] for n in d.get("notes") or []] or [0]),
           round(((d.get("Fuel") or {}).get("FuelMain") or 0), 1), ui.get("view"))
    if sig != ROBM["sig"]:
        ROBM["sig"], ROBM["t"] = sig, now
        if ROBM["zzz"]:
            ROBM["zzz"] = False                            # cualquier cosa lo despierta

def _robot_quieto(now):
    return ROBM["zzz"] or (ev_on("robparado") and now - ROBM["t"] > 900)

_sc_send_v1117 = sc_send

def sc_send(obj):
    if obj.get("t") == "hola":
        try:
            d = state.get("data") or {}
            h = hold_state(d)
            obj = dict(obj, calor=bool(d.get("Flags", 0) & (1 << 20)), llena=bool(h and h[1] and h[0] >= h[1]))
            if _robot_quieto(time.time()):
                obj["zzz"] = True
        except Exception as e:
            log_exc("robot hola", e)
    return _sc_send_v1117(obj)

# ===============================================================================================================
# 5) ROBOT: preguntas nuevas y órdenes por voz
# ===============================================================================================================
def _palabras_en(t, nombre):
    n = _norm(nombre)
    return re.search(r"\b" + re.escape(n) + r"\b", t) is not None

def r_permiso(d, now, t):
    cand = sorted(PERM_SYS.values(), key=lambda s: -len(s["sistema"]))
    s = next((x for x in cand if _palabras_en(t, x["sistema"])), None)
    if not s:
        falta = [x for x in PERM_LIST if not perm_tengo(x, d) and (PERM_SYS[x.lower()].get("tipo") in ("rango", "reputacion"))]
        return ("Dime de qué sistema. " + (f"Te faltan {len(falta)} que se pueden conseguir, por ejemplo {', '.join(falta[:3])}"
                                           if falta else "Tienes todos los que se pueden conseguir"))
    tengo = perm_tengo(s["sistema"], d)
    t_ = f"Permiso de {s['sistema']}: " + ("ya lo tienes. " if tengo else "")
    t_ += f"Lo da {s.get('titular')}. " if s.get("titular") and s["titular"] != "Desconocido" else ""
    como = perm_como(s)
    t_ += como[:1].upper() + como[1:]
    if s.get("ventajas"):
        t_ += f". Allí: {s['ventajas']}"
    return t_

RARAS_L = [(m, st, sy) for (st, sy), L_ in RARAS.items() for m in L_]
RAR = {"coords": False}

def _rara_en(t):
    """La mercancía rara que nombras (la que más palabras suyas tiene en la pregunta), o None."""
    best, punt = None, 0
    for m, st, s_ in RARAS_L:
        w = [x for x in re.findall(r"[a-z]+", _norm(m)) if len(x) > 3]
        p = sum(1 for x in w if re.search(r"\b" + x[:5], t))
        if w and p > punt and p >= (1 if len(w) == 1 else 2):
            best, punt = (m, st, s_), p
    return best

def r_raras(d, now, t):
    sy = (d.get("system") or "").lower()
    best = _rara_en(t)                                     # ¿dónde venden <rara>?
    if best:
        m, st, s_ = best
        return f"{m} se vende en {st.title()}, sistema {s_.title()}. Se paga mejor a más de 150 años luz"
    aqui = [m for m, st, s_ in RARAS_L if s_ == sy]
    if aqui:
        return f"En este sistema venden: {', '.join(aqui)}"
    pos = d.get("starpos")
    if not RAR["coords"]:
        RAR["coords"] = True
        for s_ in {x[2] for x in RARAS_L}:
            redsm_want(s_.title())
    if pos and len(pos) == 3:
        dist = []
        for m, st, s_ in RARAS_L:
            c = (REDSM.get(s_.title()) or {}).get("coords") or {}
            if c.get("x") is not None:
                dist.append((math.dist(pos, (c["x"], c["y"], c["z"])), m, st, s_))
        if dist:
            dist.sort()
            return "Las más cercanas: " + "; ".join(f"{m} en {s_.title()}, a {k:.0f} años luz" for k, m, st, s_ in dist[:3])
    return "Estoy buscando dónde están las mercancías raras. Pregúntame otra vez en un par de minutos"

OIDO.setdefault("rver", "")

def r_versiones(d, now, t):
    sv = d.get("sver") or "desconocido"
    rv = OIDO.get("rver") or "desconocida"
    t_ = f"Panel {PANEL_VER.split(' ')[0]}, sender {sv}, robot {rv}"
    malas = []
    if sv != SENDER_OK:
        malas.append(f"el sender debería ser {SENDER_OK}")
    if rv != ROBOT_OK:
        malas.append(f"el robot debería ser {ROBOT_OK}")
    return t_ + (". Ojo: " + " y ".join(malas) if malas else ". Todo cuadra")

def r_repite(d, now, t):
    if ROB_ULT.get("tit") and now - ROB_ULT.get("t", 0) < 1800:
        return "Último aviso: " + ROB_ULT["tit"]
    a = ui.get("alert") or {}
    return ("Último aviso: " + a.get("text", "")) if a.get("text") else "No hay ningún aviso reciente"

def r_calla(d, now, t):
    try:
        p = voice.get("proc")
        if p and p.poll() is None:
            p.terminate()
    except Exception:
        pass
    return "Vale, me callo"

def r_duerme(d, now, t):
    ROBM["zzz"] = True
    return "Buenas noches, Comandante. Me despierto en cuanto pase algo"

def r_despierta(d, now, t):
    ROBM["zzz"], ROBM["t"] = False, now
    return "Aquí estoy, Comandante"

# --- órdenes ---
OIDO.setdefault("pend", None)

def _tabla(tab, lab):
    return next((it[1] for it in tab if it[0] == lab), None)

def _tecla(acts, dflt=None):
    keys = ((state.get("data") or {}).get("binds") or {}).get("keys") or {}
    for a in acts.split("|"):
        k = keys.get(a)
        if k and key_ok(k):
            return k
    return dflt if dflt and key_ok(dflt) else None

def _es_pregunta(t):
    return re.search(r"\b(cuant\w*|queda\w*|donde|cuando|cual\w*|como|tengo|llevo|que|quien|dime|sabes)\b", t) is not None

def _orden(t, d):
    """(nombre, [teclas] o None, ¿pide confirmación?, respuesta si no hace falta tecla) o None."""
    fl, fl2 = d.get("Flags", 0), d.get("Flags2", 0)
    pie, srv = bool(fl2 & 1), bool(fl & (1 << 26))
    h = lambda *w: _hay(t, *w)
    def k(acts, dflt=None):
        x = _tecla(acts, dflt)
        return [x] if x else None
    if h("tren"):
        return "tren", k("LandingGearToggle", _tabla(BUTTONS, "TREN")), False, None
    if h("luces", "luz", "faros", "linterna"):
        if pie:
            return "linterna", k("HumanoidToggleFlashlightButton", _tabla(PIE_BTNS, "LINTERNA")), False, None
        if srv:
            return "faros", k("HeadlightsBuggyButton", _tabla(SRV_BTNS, "FAROS")), False, None
        return "luces", k("ShipSpotLightToggle", _tabla(BUTTONS, "LUCES")), False, None
    if h("vision"):
        return "visión nocturna", (k("HumanoidToggleNightVisionButton", _tabla(PIE_BTNS, "VISIÓN NOC")) if pie else
                                   k("NightVisionToggle", _tabla(BUTTONS, "VISIÓN NOC"))), False, None
    if h("recogedor", "bodega", "compuerta"):
        return "recogedor", k("ToggleCargoScoop_Buggy|ToggleCargoScoop" if srv else "ToggleCargoScoop", _tabla(BUTTONS, "RECOGEDOR")), False, None
    if h("armas") and h("fuera", "saca", "despliega", "dentro", "guarda", "recoge"):
        fuera = h("fuera", "saca", "despliega")
        if bool(fl & (1 << 6)) == fuera:
            return "armas", [], False, "Las armas ya están " + ("fuera" if fuera else "dentro")
        return "armas " + ("fuera" if fuera else "dentro"), k("DeployHardpointToggle"), fuera, None
    if h("modo") and h("combate", "analisis"):
        quiero_an = h("analisis")
        if bool(fl & (1 << 27)) == quiero_an:
            return "modo", [], False, "Ya estás en modo " + ("análisis" if quiero_an else "combate")
        return "modo " + ("análisis" if quiero_an else "combate"), k("PlayerHUDModeToggle"), False, None
    if h("silencio", "silenciosa"):
        return "marcha silenciosa", k("ToggleButtonUpInput", _tabla(BUTTONS, "SILENCIO")), False, None
    if h("disipador"):
        return "disipador", k("DeployHeatSink", _tabla(BUTTONS, "DISIPADOR")), False, None
    if h("senuelo", "chaff"):
        return "señuelo", k("FireChaffLauncher", _tabla(BUTTONS, "CHAFF")), False, None
    if h("escudo") and pie:
        return "escudo personal", k("HumanoidToggleShieldsButton", _tabla(PIE_BTNS, "ESCUDO")), False, None
    if h("celula"):
        return "célula de escudo", k("UseShieldCell", _tabla(BUTTONS, "ESCUDO")), False, None
    if h("refuerzo", "turbo", "boost"):
        return "refuerzo", k("UseBoostJuice"), False, None
    if h("frena", "para la nave", "todo parado", "parada total", "velocidad cero", "propulsion cero"):
        return "parada", k("SetSpeedZero"), False, None
    if h("propulsion", "velocidad", "acelera"):
        for w_, act, lab in ((("cincuenta", "50", "mitad"), "SetSpeed50", "50 %"), (("setenta", "75"), "SetSpeed75", "75 %"),
                             (("maxim", "cien", "100", "tope", "todo"), "SetSpeed100", "100 %")):
            if h(*w_):
                return "propulsión " + lab, k(act), False, None
    if h("pips", "energia"):
        for w_, lab in ((("motor",), "MAX MOT"), (("arma",), "MAX ARM"), (("sistema", "escudo"), "MAX SIS"),
                        (("equilibr", "reset", "igual", "normal"), "RESET")):
            if h(*w_):
                seq = next((s_ for n_, s_ in PIP_PRESETS if n_ == lab), None)
                nom = {"MAX MOT": "pips a motores", "MAX ARM": "pips a armas", "MAX SIS": "pips a sistemas"}.get(lab, "pips equilibrados")
                return nom, (list(seq) if seq and all(key_ok(x) for x in seq) else None), False, None
    if h("siguiente sistema", "siguiente salto", "siguiente de la ruta"):
        return "siguiente sistema de la ruta", k("TargetNextRouteSystem"), False, None
    if h("supercrucero"):
        return "supercrucero", k("Supercruise|HyperSuperCombination", _tabla(BUTTONS, "SUPERCRUC.")), True, None
    if h("salta", "salto", "hiperespacio"):
        return "salto al hiperespacio", k("Hyperspace|HyperSuperCombination", _tabla(BUTTONS, "SALTO FSD")), True, None
    if h("mapa"):
        if h("galact"):
            return "mapa galáctico", k("GalaxyMapOpen", _tabla(BUTTONS, "MAPA GAL")), False, None
        if h("sistema"):
            return "mapa del sistema", k("SystemMapOpen", _tabla(BUTTONS, "MAPA SIS")), False, None
    if h("objetivo", "fija", "subsistema"):
        for w_, act, lab in ((("peligros", "amenaza"), "SelectHighestThreat", "objetivo más peligroso"),
                             (("subsistema", "subobjetivo"), "CycleNextSubsystem", "siguiente subsistema"),
                             (("su objetivo", "objetivo del objetivo"), "SelectTargetsTarget", "su objetivo"),
                             (("ala uno", "ala 1", "lider"), "TargetWingman0", "ala 1"), (("ala dos", "ala 2"), "TargetWingman1", "ala 2"),
                             (("ala tres", "ala 3"), "TargetWingman2", "ala 3"),
                             (("siguiente",), "CycleNextTarget", "siguiente objetivo"), (("anterior",), "CyclePreviousTarget", "objetivo anterior"),
                             (("delante", "fija", "enfrente"), "SelectTarget", "objetivo de delante")):
            if h(*w_):
                return lab, k(act), False, None
        if h("borra", "quita", "suelta"):
            return "borrar objetivo", [], False, "Eso no tiene tecla en el juego"
    if h("nave") and h("llama", "despide", "manda"):
        desp = h("despide", "manda")
        return ("despedir la nave" if desp else "llamar a la nave"), k("RecallDismissShip", _tabla(SRV_BTNS, "NAVE")), desp, None
    if h("atraque") and h("pide", "solicita"):
        return "pedir atraque", [], False, "Pedir atraque no tiene tecla en el juego: va por el panel izquierdo"
    if h("despliega", "lanza") and h("rhino", "vehiculo", "srv", "scarab", "scorpion"):
        return "desplegar vehículo", [], False, "Desplegar el vehículo no tiene tecla: va por el panel derecho"
    # panel
    for w_, v_, lab in ((("en vivo",), 100, "EN VIVO"), (("menu",), 0, "MENÚ"), (("pantalla mapa", "panel mapa", "navegacion"), 3, "NAVEGACIÓN"),
                        (("pantalla combate", "panel combate"), 6, "COMBATE"), (("pantalla estacion", "panel estacion"), 8, "ESTACIÓN"),
                        (("pantalla mercado", "panel mercado"), 127, "MERCADO"), (("pantalla colonia", "colonizacion"), 135, "COLONIZACIÓN")):
        if h("panel", "pantalla", "pon", "abre") and h(*w_):
            ui["view"] = v_; ui["idle_skip"] = time.time() + 60; TAP_EV.set()
            return "panel", [], False, f"Panel en {lab}"
    return None

def r_orden(d, now, t):
    o = _orden(t, d)
    if not o:
        return None
    nombre, teclas, confirmar, resp = o
    if resp:
        return resp
    if not teclas:
        return f"No encuentro la tecla de {nombre} en tus controles"
    if confirmar:
        OIDO["pend"] = (nombre, teclas, now)
        return f"¿Confirmas {nombre}? Toca y di sí"
    press_seq(teclas)
    plog(f"ROBOT orden por voz: {nombre} {teclas}")
    return f"Hecho: {nombre}"

def r_confirma(d, now, t):
    p, OIDO["pend"] = OIDO.get("pend"), None
    if not p or now - p[2] > 30:
        return "No tenía nada pendiente de confirmar"
    if _hay(t, "no", "cancela", "anula", "olvida"):
        return f"Cancelado: {p[0]}"
    press_seq(p[1])
    plog(f"ROBOT orden por voz confirmada: {p[0]} {p[1]}")
    return f"Hecho: {p[0]}"

def _hay_pend(t):
    p = OIDO.get("pend")
    return bool(p) and time.time() - p[2] < 30 and re.search(r"^\s*(si|sí|no|vale|confirmo|adelante|hazlo|cancela|anula)\b", t) is not None

PREG_V1117 = [
    (_hay_pend, r_confirma),
    (lambda t: _hay(t, "permiso"), r_permiso),
    (lambda t: _hay(t, "rara", "raras") or (_hay(t, "donde") and _hay(t, "vend", "compr") and _rara_en(t) is not None), r_raras),
    (lambda t: _hay(t, "version"), r_versiones),
    (lambda t: _hay(t, "repite", "repiteme", "que has dicho"), r_repite),
    (lambda t: re.search(r"\b(calla|callate|silencio por favor)\b", t) is not None, r_calla),
    (lambda t: _hay(t, "duermete", "a dormir", "descansa"), r_duerme),
    (lambda t: _hay(t, "despierta", "despiertate"), r_despierta),
]

_oido_respuesta_v1117 = oido_respuesta

def oido_respuesta(texto):
    t = _norm(texto)
    if t:
        with lock:
            d = state.get("data") or {}
        now = time.time()
        for cond, fn in PREG_V1117:
            try:
                if cond(t):
                    return fn(d, now, t), "ok"
            except Exception as e:
                log_exc("oido " + fn.__name__, e)
                return "Uy, no he podido mirarlo", "nada"
        if ev_on("robcmd") and not _es_pregunta(t):
            try:
                r_ = r_orden(d, now, t)
                if r_:
                    return r_, "ok"
            except Exception as e:
                log_exc("oido orden", e)
                return "Uy, no he podido hacerlo", "nada"
    return _oido_respuesta_v1117(texto)

# ===============================================================================================================
# 6) OÍDO más rápido: Vosk siempre listo en la Pi 4, lista de palabras y voces guardadas
# ===============================================================================================================
def _es_pi4():
    try:
        with open("/proc/device-tree/model") as fh:
            m = fh.read()
        return "Raspberry Pi 4" in m or "Raspberry Pi 5" in m
    except OSError:
        return False

PI4 = _es_pi4()

def _oido_fijo():
    time.sleep(90)
    while True:
        try:
            if PI4 and cfg.get("stackchan") and ev_on("robvosk") and ev_on("roboido") and oido_ok():
                if OIDO["model"] is None:
                    plog("ROBOT: cargo el oído (Vosk) para que conteste más rápido")
                _oido_model()                                  # carga (si hace falta) y lo mantiene vivo
                _oido_gram()
        except Exception as e:
            log_exc("oído fijo", e)
        time.sleep(240)

threading.Thread(target=_oido_fijo, daemon=True, name="oido-fijo").start()

GRAM = {"g": None, "hecho": False}
OIDO_EXTRA = """si no vale confirmo adelante hazlo cancela anula olvida el la los las un una de del en a al y o que como cuanto cuanta
cuantos cuantas donde cuando cual hay me te se mi tu su por para con sin mas menos muy ya pon abre cierra saca guarda despliega
recoge fuera dentro llama despide manda pide solicita fija borra quita suelta silencia siguiente anterior delante enfrente nave
panel pantalla robot comandante hola gracias ayuda cero uno dos tres cuatro cinco seis siete ocho nueve diez cincuenta setenta
cien maxima mitad tope todo""".split()

def _oido_claves():
    """Palabras que entiende el panel: las de las preguntas (de los ficheros de las partes) y las órdenes."""
    K = set(OIDO_EXTRA)
    base = os.path.join(PANEL_DIR, "partes")
    try:
        for fn in os.listdir(base):
            if fn.endswith(".py"):
                with open(os.path.join(base, fn), encoding="utf-8") as fh:
                    src = fh.read()
                for m in re.finditer(r"_hay\(t,([^)]*)\)", src):
                    K.update(_norm(x) for x in re.findall(r'"([^"]+)"', m.group(1)))
    except OSError:
        pass
    for pals, fn in OIDO_PREG:
        K.update(_norm(p) for p in pals)
    for s in PERM_SYS.values():
        K.update(re.findall(r"[a-z0-9]+", _norm(s["sistema"])))
    for m, st, sy in RARAS_L:
        K.update(x for x in re.findall(r"[a-z]+", _norm(m)) if len(x) > 2)
    out = set()
    for k in K:
        out.update(x for x in k.split() if x)
    return out

def _oido_gram():
    """Lista de palabras para Vosk (las del modelo que empiezan por alguna de las claves). None si no se puede."""
    if GRAM["hecho"]:
        return GRAM["g"]
    GRAM["hecho"] = True
    wf = None
    for raiz, dirs, files in os.walk(VOSK_DIR):
        if "words.txt" in files:
            wf = os.path.join(raiz, "words.txt"); break
    if not wf:
        plog("ROBOT: el modelo de Vosk no trae words.txt, sin lista de palabras")
        return None
    claves = _oido_claves()
    sel = set()
    with open(wf, encoding="utf-8") as fh:
        for ln in fh:
            w = ln.split(" ")[0].strip()
            if not w or w.startswith(("<", "#", "!")):
                continue
            n = _norm(w)
            if n in claves or any(n[:k] in claves for k in range(4, len(n))):
                sel.add(w)
    if len(sel) < 50:
        return None
    GRAM["g"] = json.dumps(sorted(sel) + ["[unk]"], ensure_ascii=False)
    plog(f"ROBOT: lista de palabras de Vosk con {len(sel)} palabras")
    return GRAM["g"]

def oido_texto(pcm, rate=16000):
    """Audio PCM 16 bits mono -> texto. Primero con la lista de palabras (rápido); si no lo entiende, con todo."""
    import vosk, array, sys as _s
    a = array.array("h"); a.frombytes(pcm[:len(pcm) // 2 * 2])
    if _s.byteorder != "little":
        a.byteswap()
    pico = max((abs(x) for x in a), default=0)
    if 0 < pico < 12000:
        k = 12000 / pico
        a = array.array("h", (max(-32768, min(32767, int(x * k))) for x in a))
    pcm = a.tobytes()
    model = _oido_model()

    def pasa(rec):
        for i in range(0, len(pcm), 8000):
            rec.AcceptWaveform(pcm[i:i + 8000])
        return (json.loads(rec.FinalResult()).get("text") or "").strip()
    g = None
    try:
        g = _oido_gram() if ev_on("robvosk") else None
    except Exception as e:
        log_exc("vosk lista", e)
    if g:
        try:
            txt = pasa(vosk.KaldiRecognizer(model, rate, g))
            limpio = " ".join(w for w in txt.split() if w != "[unk]")
            if limpio and txt.count("[unk]") <= len(limpio.split()) // 2:
                return limpio
        except Exception as e:
            log_exc("vosk con lista", e)
    return pasa(vosk.KaldiRecognizer(model, rate))

ROB_FIJAS = ["No te he oído. Toca la pantalla y habla cerca", "Uy, no he podido mirarlo", "Vale, me callo",
             "Aquí estoy, Comandante", "Buenas noches, Comandante. Me despierto en cuanto pase algo",
             "No tenía nada pendiente de confirmar", "Hecho: tren", "Hecho: luces", "Hecho: recogedor",
             "Hecho: disipador", "Hecho: señuelo", "Hecho: célula de escudo", "¿Confirmas salto al hiperespacio? Toca y di sí",
             "¿Confirmas supercrucero? Toca y di sí", "Hecho: salto al hiperespacio", "Hecho: supercrucero"]
VOZC = {}

def oido_wav(texto):
    t = re.sub(r"\s+", " ", voz_txt(texto)).strip()
    if t in VOZC:
        return VOZC[t]
    try:
        data = None
        if piper_ok():
            with open(_piper_wav(t), "rb") as fh:
                data = fh.read()
        elif shutil.which("espeak-ng"):
            r = subprocess.run(["espeak-ng", "-v", "es", "-s", "150", "-a", "130", "--stdout", t], capture_output=True, timeout=20)
            data = r.stdout or None
        if data and len(data) < 600000:
            if len(VOZC) > 60:
                VOZC.clear()
            VOZC[t] = data
        return data
    except Exception as e:
        log_exc("oido voz", e)
    return None

def _voces_fijas():
    time.sleep(150)
    if not cfg.get("stackchan"):
        return
    for f_ in ROB_FIJAS:
        try:
            t = re.sub(r"\s+", " ", voz_txt(f_)).strip()
            if piper_ok():
                _piper_wav(t, low=True)
            else:
                oido_wav(f_)
        except Exception:
            pass

threading.Thread(target=_voces_fijas, daemon=True, name="voces-fijas").start()

# --- servidor del robot (8081): también /quita (doble toque en la cabeza) y la versión del robot al preguntar ---
def sc_foto_srv():
    if SC_FOTO["srv"]:
        return
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    import urllib.parse as _up

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _envia(self, data, tipo):
            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = _up.urlparse(self.path)
            q = _up.parse_qs(u.query)
            if u.path == "/foto" and cfg.get("stackchan"):
                f = (q.get("f") or [""])[0]
                data = None
                try:
                    data = sc_foto_rotulada(f)
                except Exception as e:
                    log_exc("stackchan foto " + f, e)
                if data:
                    return self._envia(data, "image/jpeg")
            if u.path == "/resp":
                try:
                    data = OIDO["resp"].get(int((q.get("n") or ["0"])[0]))
                except ValueError:
                    data = None
                if data:
                    return self._envia(data, "audio/wav")
            if u.path == "/quita" and cfg.get("stackchan"):
                ev = (q.get("ev") or [""])[0]
                if ev and ev_num(ev):
                    cfg.setdefault("ev", {})[ev] = False
                    cfg["alerts"] = True
                    save_cfg()
                    plog(f"ROBOT: quitado el aviso #{ev_num(ev)} {_ev_nombre(ev)} (doble toque en la cabeza)")
                    txt = f"Quitado el aviso {ev_num(ev)}: {_ev_nombre(ev)}. Se vuelve a poner en ALERTAS"
                else:
                    txt = "Ese aviso no tiene número: no se puede quitar"
                return self._envia(json.dumps({"txt": txt}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            self.send_error(404)

        def do_POST(self):
            u = _up.urlparse(self.path)
            if u.path != "/oir":
                self.send_error(404); return
            try:
                q = _up.parse_qs(u.query)
                OIDO["rver"] = (q.get("v") or [OIDO.get("rver") or ""])[0][:20]
                n = int(self.headers.get("Content-Length") or 0)
                rate = int((q.get("r") or ["16000"])[0])
                if n <= 0 or n > 400000:
                    self.send_error(413); return
                pcm = self.rfile.read(n)
                out = oido_atiende(pcm, rate)
            except Exception as e:
                log_exc("robot oido", e)
                out = {"txt": "Uy, algo ha fallado al oírte"}
            self._envia(json.dumps(out, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", SC_FOTO_PORT), H)
        srv.daemon_threads = True
        SC_FOTO["srv"] = srv
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    except OSError as e:
        print("STACKCHAN fotos/oido:", e)

# la ayuda cuenta lo nuevo
def r_ayuda(d, now):
    return ("Pregúntame por combustible, ruta, tick, facción, dinero, misiones, carga, ingenieros, permisos, mercancías raras, "
            "construcción o versiones. Y dame órdenes: tren, luces, pips a motores, siguiente sistema, salto")

OIDO_PREG[:] = [(p, r_ayuda if fn.__name__ == "r_ayuda" else fn) for p, fn in OIDO_PREG]

# ===============================================================================================================
# todo lo de arriba, una vez por segundo desde el dibujo
# ===============================================================================================================
_render_v1117 = render
W1117 = {"t": 0.0}

def render(surf):
    r_ = _render_v1117(surf)
    now = time.time()
    if now - W1117["t"] >= 1:
        W1117["t"] = now
        try:
            with lock:
                d, rx = state["data"], state["rx"]
            if d and now - rx < 5:
                for fn in (col_todo_watch, pax_robot_watch, ing_watch):
                    try:
                        fn(d)
                    except Exception as e:
                        log_exc(fn.__name__, e)
                parado_watch(d, now)
        except Exception as e:
            log_exc("v1.1.17", e)
    return r_

_on_tap_v1117 = on_tap

def on_tap(x, y):
    if ui.get("view") == 127 and y > TOP and not ui.get("idle_on") and not (ui.get("alert") and time.time() < ui["alert"]["until"]):
        d = state.get("data") or {}
        if col_falta(d):
            ui["mkcol"] = not ui.get("mkcol")
            MKC["st"] = (d.get("station") or {}).get("mid")
            tap_flash((127, 0))
            TAP_EV.set()
            return
    ROBM["t"] = time.time()                                # tocar el panel cuenta como actividad
    return _on_tap_v1117(x, y)
