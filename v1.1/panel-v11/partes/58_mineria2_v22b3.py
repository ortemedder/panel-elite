# Panel Elite v2.2 · parte 58: v2.2b3 — MINERÍA en 2 CUADROS (asteroides y planetaria)
#   - MINERÍA DE ASTEROIDES (minando en un anillo: prospector, recolector o refinado en los últimos 10 min):
#     ASTEROIDE PROSPECTADO (veta madre, contenido, % de cada material, lo que queda y los últimos asteroides) y
#     BODEGA · REFINERÍA · DRONES (bodega, refinado por material, t/h, valor aproximado, drones que quedan y lanzados).
#     El juego no dice cómo va cada hueco de la refinería: sale lo refinado en toneladas.
#   - MINERÍA PLANETARIA (en el SRV o el Rhino; con el SRV normal solo si has recogido algo en los últimos 5 min):
#     MAPA (rastro, nave y un punto verde donde recogiste material) y SRV/RHINO (escudos, combustible, bodega y
#     MATERIALES recogidos con su total / máximo; en rojo los que ya están al máximo).
#   - REGISTRO abajo con lo último (prospecciones, vetas, refinado, materiales) y sus contadores.
#   - 12 AJUSTES > PANTALLA > MINERÍA / BIO: 2 CUADROS / 4 CUADROS (2 de fábrica).

def mina2_on():
    return cfg.get("mina2", "2") == "2"

MH = {"sig": None, "ref": None, "ast": [], "log": [], "sm": None, "smt": 0, "km": (0, 0.0)}

def _mh_log(tag, txt, col, cat="ast"):
    MH["log"].insert(0, (time.time(), tag, txt, col, cat))
    del MH["log"][12:]

def _cont(c):
    c = (c or "").split(":")[-1].strip()
    return c.upper()

def mh_update(d, now):
    """Historial del panel: asteroides prospectados, toneladas refinadas y materiales recogidos en el SRV."""
    m = (d or {}).get("mining") or {}
    last = m.get("last")
    sig = str(last)[:300] if last else None
    if MH["sig"] is None:
        MH["sig"] = sig or ""
    elif sig and sig != MH["sig"]:
        MH["sig"] = sig
        mats = last.get("mats") or []
        top = mats[0] if mats else ["?", 0]
        MH["ast"].insert(0, (now, top[0], top[1], _cont(last.get("content")), last.get("motherlode"), last.get("remaining")))
        del MH["ast"][8:]
        if last.get("motherlode"):
            _mh_log("VETA MADRE", f"{last['motherlode']} · núcleo", PURPLE)
        _mh_log("PROSPECCIÓN", f"{top[0]} {top[1]:.0f} % · {_cont(last.get('content')).lower()}", GREEN)
    ref = dict(m.get("refined") or {})
    if MH["ref"] is None:
        MH["ref"] = ref
    elif ref != MH["ref"]:
        for k, n in ref.items():
            dn = n - MH["ref"].get(k, 0)
            if dn > 0:
                _mh_log("REFINADO", f"{k} · +{dn} t", AMBAR)
        MH["ref"] = ref
    sm = {n: c for n, c, _ in ((d or {}).get("srvmats") or [])}
    if MH["sm"] is None:
        MH["sm"] = sm
    elif sm != MH["sm"]:
        nuevo = False
        for k, c in sm.items():
            dc = c - MH["sm"].get(k, 0)
            if dc > 0:
                _mh_log("MATERIAL", f"{k} +{dc}", PURPLE, "srv")
                nuevo = True
        MH["sm"] = sm
        if nuevo:
            MH["smt"] = now
            try:
                track_item("mat")
            except Exception:
                pass

PURPLE = (190, 120, 255)

def mina_asteroides(d, flags, now, mode):
    f2 = (d or {}).get("Flags2", 0)
    return (str(mode).startswith(("APROXIMACIÓN", "VIAJE")) and not f2 & 1 and not flags & ((1 << 26) | (1 << 1))
            and mining_active(d, now))

def mina_planeta(d, flags, now, mode):
    if not str(mode).startswith("SUPERFICIE") or not flags & (1 << 26):
        return False
    return "rhino" in ((d or {}).get("srvtype") or "").lower() or now - MH["smt"] < 300

# ---------------------------------------------------------------------------------------------------------------
# ASTEROIDES
# ---------------------------------------------------------------------------------------------------------------
def _ccol(c):
    c = c.lower()
    return GREEN if c.startswith(("alt", "hig")) else AMBAR if c.startswith(("med",)) else DIM

def m2_asteroide(Z, d, flags, now):
    m = (d or {}).get("mining") or {}
    last = m.get("last")
    ast = MH["ast"]
    age = now - ast[0][0] if ast else None
    a = c2_marco(Z, "ASTEROIDE PROSPECTADO", f"hace {age:.0f} s" if age is not None and age >= 3 else None)
    x, w = a.x, a.w
    y = a.y - 4
    if not last:
        put(Z, F["big"], "LANZA UN PROSPECTOR", (Z.get_width() // 2, a.y + 120), DIM, w, anchor="center")
        return
    cont = _cont(last.get("content"))
    if cont:
        cw_ = max(120, tw_(F["small"], cont) + 24)
        c2_etiqueta(Z, pygame.Rect(x + w - cw_, y, cw_, 42), cont, _ccol(cont))
    else:
        cw_ = 0
    if last.get("motherlode"):
        blink = int(now * 2) % 2 == 0
        r = pygame.Rect(x, y, 210, 42)
        pygame.draw.rect(Z, PURPLE if blink else BLACK, r, border_radius=6)
        pygame.draw.rect(Z, PURPLE, r, 3, border_radius=6)
        put(Z, F["small"], "VETA MADRE", r.center, BLACK if blink else PURPLE, anchor="center")
        put(Z, F["btn"], last["motherlode"].upper(), (x + 224, y + 2), PURPLE, w - 224 - cw_ - 12)
    y += 56
    hs = F["small"].get_height()
    for name, pct in (last.get("mats") or [])[:5]:
        put(Z, F["small"], name, (x, y), WHITE, w * 0.32)
        bx = pygame.Rect(x + int(w * 0.34), y + 4, int(w * 0.46), hs - 6)
        pygame.draw.rect(Z, DIM, bx, 2)
        pygame.draw.rect(Z, AMBAR if pct >= 20 else ORANGE, (bx.x + 3, bx.y + 3, int((bx.w - 6) * min(pct, 50) / 50), bx.h - 6))
        put(Z, F["small"], f"{pct:.1f} %".replace(".", ","), (x + w, y), AMBAR if pct >= 20 else WHITE, anchor="topright")
        y += hs + 10
    rem = last.get("remaining")
    if rem is not None:
        y = c2_barra(Z, x, y + 4, w, 28, "QUEDA EN EL ASTEROIDE", rem, GREEN if rem >= 100 else ORANGE if rem > 0 else RED,
                     txt=f"{rem:.0f} %" if rem > 0 else "AGOTADO") + 10
    if len(ast) > 1 and y < a.bottom - 40:
        pygame.draw.line(Z, DIM, (x, y), (x + w, y), 1)
        y += 6
        put(Z, F["tiny"], "ÚLTIMOS ASTEROIDES", (x, y), DIM)
        y += F["tiny"].get_height() + 4
        for t_, mat, pct, c, ml, rm in ast[1:]:
            if y + hs > a.bottom + 6:
                break
            put(Z, F["tiny"], time.strftime("%H:%M", time.localtime(t_)), (x, y + 3), DIM)
            put(Z, F["small"], f"{mat} {pct:.0f} %", (x + 90, y), WHITE, w * 0.5)
            est = "VETA" if ml else ("AGOTADO" if rm == 0 else c)
            put(Z, F["small"], est, (x + w, y), PURPLE if ml else _ccol(c), anchor="topright")
            y += hs + 4

def _valor_ref(d, refined):
    prices = {r[0].lower(): r[1] for r in ((d.get("market") or {}).get("best") or [])}
    prices.update({r[0].lower(): r[2] for r in ((d.get("market") or {}).get("sell") or [])})
    return sum(n * (prices.get(k.lower()) or 0) for k, n in refined.items())

def m2_bodega(Z, d, flags, now):
    d = d or {}
    m = d.get("mining") or {}
    Lv = d.get("live") or {}
    sh = (Lv.get("ship") or {}).get("ship")
    a = c2_marco(Z, "BODEGA · REFINERÍA · DRONES", sh.upper() if sh else None)
    x, w = a.x, a.w
    y = a.y - 4
    cap = d.get("cargocap")
    used = sum(c for _, c in (d.get("cargo") or []))
    pct = used / cap * 100 if cap else None
    y = c2_barra(Z, x, y, w, 34, "BODEGA", pct, RED if pct is not None and pct >= 95 else ORANGE,
                 txt=f"{used} / {cap} t" if cap else f"{used} t") + 12
    put(Z, F["tiny"], "REFINADO EN ESTA SESIÓN", (x, y), DIM)
    y += F["tiny"].get_height() + 4
    ref = sorted((m.get("refined") or {}).items(), key=lambda kv: -kv[1])
    hs = F["small"].get_height()
    mx = max([n for _, n in ref] + [1])
    if not ref:
        put(Z, F["small"], "nada aún", (x, y), DIM)
        y += hs + 6
    for name, n in ref[:5]:
        put(Z, F["small"], name, (x, y), WHITE, w * 0.32)
        pygame.draw.rect(Z, AMBAR, (x + int(w * 0.34), y + 5, int(w * 0.46 * n / mx), hs - 10))
        put(Z, F["small"], f"{n} t", (x + w, y), AMBAR, anchor="topright")
        y += hs + 6
    pygame.draw.line(Z, DIM, (x, y + 2), (x + w, y + 2), 1)
    y += 10
    tons = sum(n for _, n in ref)
    if tons and m.get("t0") and m.get("t1") and m["t1"] > m["t0"]:
        h = (m["t1"] - m["t0"]) / 3600
        put(Z, F["small"], "RITMO", (x, y + 2), DIM)
        mins = int((m["t1"] - m["t0"]) // 60)
        rate = f"{tons / h:.0f} t/h · " if h > 0.02 else ""
        put(Z, F["btn"], f"{rate}{mins // 60} h {mins % 60:02d} m", (x + w, y - 2), GREEN, w - 110, anchor="topright")
        y += F["btn"].get_height() + 4
        val = _valor_ref(d, dict(ref))
        if val:
            put(Z, F["small"], "VALOR (último mercado)", (x, y + 2), DIM)
            put(Z, F["btn"], f"~ {cr(val)} cr", (x + w, y - 2), GREEN, anchor="topright")
            y += F["btn"].get_height() + 4
    lim = m.get("limpets")
    yb = a.bottom - F["big"].get_height() - 4
    pygame.draw.line(Z, DIM, (x, yb - 8), (x + w, yb - 8), 1)
    put(Z, F["small"], "DRONES", (x, yb + 10), DIM)
    put(Z, F["big"], f"{lim}" if lim is not None else "?", (x + 120, yb), RED if lim == 0 else WHITE)
    put(Z, F["small"], f"prospectores {m.get('prospectors', 0)} · recolectores {m.get('collectors', 0)}",
        (x + w, yb + 12), DIM, w - 200, anchor="topright")

# ---------------------------------------------------------------------------------------------------------------
# PLANETARIA
# ---------------------------------------------------------------------------------------------------------------
def _recorrido_km(d):
    b = (d or {}).get("bio") or {}
    R = b.get("R")
    pts = track["pts"]
    if not R:
        return None
    n0, km = MH["km"]
    if n0 > len(pts):
        n0, km = 0, 0.0
    prev = pts[n0 - 1] if n0 else None
    for p in pts[n0:]:
        if p is not None and prev is not None:
            km += hav(prev, p, R) / 1000
        prev = p
    MH["km"] = (len(pts), km)
    return km

def m2_mapa(Z, d, flags, now):
    zm = ("ZONA", "100 m", "TODO")[track["zoom"] % 3]
    a = c2_marco(Z, "MAPA · " + zm, ((d or {}).get("body") or "").upper() or None)
    r = pygame.Rect(a.x - 14, a.y - 10, a.w + 28, a.h + 20)
    draw_map(Z, r, d, now)
    lz_hit(r, "mapzoom")

def m2_srv(Z, d, flags, now):
    d = d or {}
    tipo = (d.get("srvtype") or "SRV").upper()
    a = c2_marco(Z, tipo)
    x, w = a.x, a.w
    y = a.y - 4
    shd = flags & 8
    y = c2_barra(Z, x, y, w, 26, "ESCUDOS", 100 if shd else 0, BLUE if shd else RED, txt="ACTIVOS" if shd else "SIN ESCUDOS") + 8
    sf = (d.get("Fuel") or {}).get("FuelReservoir")
    put(Z, F["small"], "COMBUSTIBLE", (x, y + 4), DIM)
    put(Z, F["btn"], f"{sf:.2f} t".replace(".", ",") if sf is not None else "?", (x + w, y), RED if sf is not None and sf < 0.1 else ORANGE, anchor="topright")
    y += F["btn"].get_height() + 4
    if d.get("srvcargo") is not None:
        put(Z, F["small"], "BODEGA", (x, y + 4), DIM)
        put(Z, F["btn"], f"{d['srvcargo']} t", (x + w, y), ORANGE, anchor="topright")
        y += F["btn"].get_height()
        inv = ", ".join(f"{n} {c}" for n, c in (d.get("srvinv") or [])[:4])
        if inv:
            put(Z, F["tiny"], inv, (x, y), WHITE, w)
            y += F["tiny"].get_height() + 2
    chips = [t for t, on in (("TORRETA", flags & (1 << 13)), ("FRENO", flags & (1 << 12)), ("CARGA", flags & (1 << 9)),
                             ("SOBRECALENT.", flags & (1 << 20))) if on]
    if chips:
        put(Z, F["tiny"], " · ".join(chips), (x, y + 2), RED if "SOBRECALENT." in chips else AMBAR, w)
        y += F["tiny"].get_height() + 4
    pygame.draw.line(Z, DIM, (x, y + 2), (x + w, y + 2), 1)
    y += 8
    put(Z, F["tiny"], "MATERIALES RECOGIDOS", (x, y), DIM)
    y += F["tiny"].get_height() + 4
    tot = {n.lower(): (c, mx) for n, c, mx in (((d.get("mats") or {}).get("list")) or [])}
    sm = d.get("srvmats") or []
    hs = F["small"].get_height()
    if not sm:
        put(Z, F["small"], "nada aún", (x, y), DIM)
    llenos = []
    for name, c, full in sm:
        if y + hs > a.bottom + 4:
            break
        t, mx = tot.get(name.lower(), (None, None))
        col = RED if full else PURPLE
        put(Z, F["small"], name, (x, y), WHITE, w * 0.36)
        put(Z, F["small"], f"+{c}", (x + int(w * 0.38), y), col)
        if t is not None and mx:
            bx = pygame.Rect(x + int(w * 0.52), y + 5, int(w * 0.20), hs - 10)
            pygame.draw.rect(Z, DIM, bx, 1)
            pygame.draw.rect(Z, col, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(1, t / mx)), bx.h - 4))
            put(Z, F["tiny"], f"{t}/{mx}", (x + w, y + 3), col, anchor="topright")
        if full:
            llenos.append(name)
        y += hs + 4
    if llenos:
        put(Z, F["tiny"], f"{llenos[0]} lleno: deja de recogerlo", (x, a.bottom - F["tiny"].get_height() + 6), RED, w)

# ---------------------------------------------------------------------------------------------------------------
# REGISTRO
# ---------------------------------------------------------------------------------------------------------------
def m2_registro(Z, d, flags, now, cont, cat):
    a = c2_marco(Z, "REGISTRO", cont or None, dcol=WHITE)
    x, w = a.x, a.w
    y = a.y - 12
    lh = (a.bottom + 8 - y) // 3
    log = [e for e in MH["log"] if e[4] == cat][:3]
    if not log:
        put(Z, F["small"], "aún nada en esta sesión", (x, y + 4), DIM)
    for t_, tag, txt, col, _ in log:
        put(Z, F["tiny"], time.strftime("%H:%M", time.localtime(t_)), (x, y + 3), DIM)
        put(Z, F["small"], tag, (x + 90, y), col)
        put(Z, F["small"], txt, (x + 330, y), WHITE, w - 340)
        y += lh

def m2_reg_ast(Z, d, flags, now):
    m = (d or {}).get("mining") or {}
    tons = sum((m.get("refined") or {}).values())
    m2_registro(Z, d, flags, now, f"SESIÓN {fnum(tons, 0)} t  ·  PROSPECTORES {m.get('prospectors', 0)}  ·  "
                                  f"RECOLECTORES {m.get('collectors', 0)}  ·  ASTEROIDES {len(MH['ast'])}", "ast")

def m2_reg_srv(Z, d, flags, now):
    n = sum(c for _, c, _ in ((d or {}).get("srvmats") or []))
    km = _recorrido_km(d)
    bits = [f"SESIÓN {fnum(n, 0)} materiales"]
    if (d or {}).get("srvcargo") is not None:
        bits.append(f"BODEGA {d['srvcargo']} t")
    if km is not None:
        bits.append(f"RECORRIDO {km:.1f} km".replace(".", ","))
    m2_registro(Z, d, flags, now, "  ·  ".join(bits), "srv")

# ---------------------------------------------------------------------------------------------------------------
# enganche en el tablero
# ---------------------------------------------------------------------------------------------------------------
_lz_tablero_v22b3 = lz_tablero

def lz_tablero(S, d, flags, now):
    try:
        mh_update(d, now)
    except Exception as e:
        log_exc("historial de minería", e)
    mode = big_mode(d, flags)
    if not (mina2_on() and cfg.get("bigmode", "4") == "4"):
        return _lz_tablero_v22b3(S, d, flags, now)
    if mina_asteroides(d, flags, now, mode):
        zonas = ((m2_asteroide, 10, C2_L), (m2_bodega, 4, C2_R), (m2_reg_ast, 61, C2_B))
    elif mina_planeta(d, flags, now, mode):
        zonas = ((m2_mapa, 150, P2_L), (m2_srv, 5, P2_R), (m2_reg_srv, 61, C2_B))
        BIG["fast"] = True
    else:
        return _lz_tablero_v22b3(S, d, flags, now)
    if not lienzo_dibuja(S, lz_tab_cabecera, d, flags, now, "MINERÍA"):
        return _lz_tablero_v22b3(S, d, flags, now)
    if cfg.get("perf"):
        pr = lz_real((700, 64, 10, 10))
        perf_draw(S, pr.x, pr.y)
    LZ["colr"] = None
    BIG["cellmap"] = []
    ok = all([lz_zona(S, fn, v, rc, d, flags, now) for fn, v, rc in zonas])
    BIG["rects"] = [(v, lz_real(rc)) for _, v, rc in zonas]
    if not ok:
        S.fill(BLACK)
        LZ["cel"] = {}
        return _lz_tablero_v22b3(S, d, flags, now)
    return True

# ---------------------------------------------------------------------------------------------------------------
# 12 AJUSTES > PANTALLA: 8.º botón MINERÍA / BIO
# ---------------------------------------------------------------------------------------------------------------
_view_pantalla_v22b3 = view_pantalla

def view_pantalla(surf, d, flags, now):
    _view_pantalla_v22b3(surf, d, flags, now)
    r = _pant_r(7)
    draw_button(surf, r, "MINERÍA / BIO", "2 CUADROS" if mina2_on() else "4 CUADROS", F["small"], filled=mina2_on(),
                lit=flash.get((160, 7), 0) > now)

VIEWS[160] = view_pantalla

_on_tap_v22b3 = on_tap

def on_tap(x, y):
    if ui.get("view") == 160 and not ui.get("idle_on") and _pant_r(7).collidepoint(x, y):
        tap_flash((160, 7))
        cfg["mina2"] = "4" if mina2_on() else "2"
        plog("PANTALLA > MINERÍA / BIO: " + ("2 CUADROS" if mina2_on() else "4 CUADROS"))
        save_cfg(); TAP_EV.set()
        return
    return _on_tap_v22b3(x, y)
