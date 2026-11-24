# Panel Elite v2.2 · parte 57: v2.2b2 — COMBATE A PIE en 2 CUADROS y EDMC (va con el sender v1.0b19)
#   - COMBATE A PIE (pantalla grande, en combate a pie): MAPA grande a la izquierda (el plano de siempre: rastro, nave,
#     asentamiento y una ✕ en cada baja; tocar = zoom ZONA / 100 m / TODO), TRAJE a la derecha (salud, escudo, oxígeno,
#     temperatura, arma, explosivos «quedan X de Y», botiquines y baterías, con sus botones) y REGISTRO abajo con
#     SESIÓN · SIN ENTREGAR · TOTAL A PIE. Va con el mismo botón 12 AJUSTES > PANTALLA > COMBATE (2 / 4 CUADROS).
#   - EDMC: el sender v1.0b19 abre EDMarketConnector (Inara) al arrancar el juego si no está abierto; el panel avisa
#     «EDMC ABIERTO» o «NO ENCUENTRO EDMC» (se quitan en ALERTAS / SONIDO).

SENDER_OK = SENDER_REQ = "v1.0b19"

EV_LIST.append(("edmc", "EDMC (INARA) ABIERTO / NO ENCONTRADO"))

_handle_note_v22b2 = handle_note

def handle_note(kind, text):
    if kind == "edmc":
        p = (str(text).split("|") + ["", ""])[:2]
        ok = p[0] == "ok"
        plog("EDMC: " + ("abierto por el sender" if ok else "no lo encuentro") + (f" ({p[1]})" if p[1] else ""))
        if ev_on("edmc"):
            if ok:
                _xa_show("edmc", col=GREEN, title="EDMC ABIERTO", big="INARA AL DÍA",
                         lines=["el sender ha abierto EDMarketConnector"], secs=4)
            else:
                _xa_show("edmc", col=ORANGE, title="NO ENCUENTRO EDMC", big="INARA SIN ACTUALIZAR",
                         lines=["ábrelo a mano o pon su ruta en EDMC_EXE (arriba del sender)"], secs=8)
        return
    return _handle_note_v22b2(kind, text)

# ---------------------------------------------------------------------------------------------------------------
# COMBATE A PIE
# ---------------------------------------------------------------------------------------------------------------
P2_L = (6, 102, 780, 566)                         # mapa más ancho
P2_R = (798, 102, 476, 566)

LZ_ACC["mapzoom"] = lambda acc, X, Y: (tap_flash(("mapzoom",)), track.__setitem__("zoom", (track["zoom"] + 1) % 3))

def p2_mapa(Z, d, flags, now):
    d = d or {}
    b = d.get("bio") or {}
    zm = ("ZONA", "100 m", "TODO")[track["zoom"] % 3]
    Zc = d.get("footcz") or {}
    zona = (Zc.get("zone") or "").upper()
    a = c2_marco(Z, "MAPA · " + zm, zona or None)
    r = pygame.Rect(a.x - 14, a.y - 10, a.w + 28, a.h + 20)
    draw_map(Z, r, d, now)
    lz_hit(r, "mapzoom")

def _p2_boton(Z, r, nombre):
    i = next((k for k, b in enumerate(PIE_BTNS) if b[0] == nombre), None)
    if i is None:
        return
    lit = flash.get((5, 6 + i), 0) > time.time()
    pygame.draw.rect(Z, WHITE if lit else ORANGE, r, border_radius=8)
    put_fit(Z, ("small", "tiny", "chip"), nombre, (r.centerx, r.y + 4), BLACK, r.w - 8, anchor="midtop")
    put(Z, F["tiny"], PIE_BTNS[i][1].upper(), (r.centerx, r.bottom - 4), BLACK, r.w - 8, anchor="midbottom")
    v = m5_rect(6 + i)
    lz_hit(r, "old", v.centerx, v.centery)

def p2_traje(Z, d, flags, now):
    d = d or {}
    Lv = d.get("live") or {}
    f2 = d.get("Flags2", 0)
    a = c2_marco(Z, "TRAJE", suit_name_of(d).upper() or None)
    x, w = a.x, a.w
    y = a.y - 4
    sd = (d.get("combat") or {}).get("sd")
    if sd:
        el = int(now - sd)
        y = c2_barra(Z, x, y, w, 30, "ESCUDO", 0, WHITE if int(now * 2) % 2 == 0 else RED, txt=f"CAÍDO {el // 60:02d}:{el % 60:02d}") + 10
    else:
        y = c2_barra(Z, x, y, w, 30, "ESCUDO", 100, BLUE, txt="ACTIVO") + 10
    hp = pctv(Lv.get("health"))
    y = c2_barra(Z, x, y, w, 30, "SALUD", hp, RED if hp is not None and hp < 25 else ORANGE if hp is not None and hp < 50 else GREEN) + 10
    half = (w - 16) // 2
    oxy = pctv(Lv.get("oxy"))
    c2_barra(Z, x, y, half, 24, "OXÍGENO", oxy, RED if oxy is not None and oxy < 25 else BLUE)
    t = Lv.get("temp")
    tcol = RED if f2 & ((1 << 9) | (1 << 11)) else BLUE if f2 & ((1 << 8) | (1 << 10)) else GREEN
    put(Z, F["small"], "TEMP.", (x + half + 16, y), DIM)
    put(Z, F["btn"], f"{t - 273.15:.0f} °C" if t is not None else "-", (x + w, y - 4), tcol, anchor="topright")
    put(Z, F["tiny"], "respirable" if f2 & (1 << 16) else "no respirable", (x + w, y + F["btn"].get_height() + 2), DIM,
        anchor="topright")
    y += F["small"].get_height() + 6 + 24 + 12
    pygame.draw.line(Z, DIM, (x, y), (x + w, y), 1)
    y += 6
    put(Z, F["tiny"], "ARMA", (x, y + 4), DIM)
    put(Z, F["small"], Lv.get("weapon") or "-", (x + w, y), WHITE, w - 80, anchor="topright")
    y += F["small"].get_height() + 8
    c, mx = cons_count(d), suit_max(d)
    lh = F["small"].get_height() + 6
    for k, lab in EXPL:
        if not mx.get(k) and not c.get(k):
            continue
        n, m = c.get(k, 0), mx.get(k, 0)
        put(Z, F["small"], {"frag": "GRANADAS", "emp": "EMP", "shield": "PROYECTOR"}.get(k, lab), (x, y), WHITE)
        bw = 40
        for j in range(max(m, n)):
            pygame.draw.rect(Z, (ORANGE if k == "frag" else BLUE if k == "emp" else GREEN) if j < n else (40, 25, 10),
                             (x + 170 + j * (bw + 8), y + 3, bw, lh - 12))
            pygame.draw.rect(Z, DIM, (x + 170 + j * (bw + 8), y + 3, bw, lh - 12), 1)
        put(Z, F["small"], f"{n}/{m}" if m else str(n), (x + w, y), cons_col(n, m), anchor="topright")
        y += lh
    med, cell = c.get("med", 0), c.get("cell", 0)
    put(Z, F["small"], f"BOTIQUINES {med}", (x, y + 2), cons_col(med))
    put(Z, F["small"], f"BATERÍAS {cell}", (x + w, y + 2), cons_col(cell), anchor="topright")
    bh = 58
    yb = a.bottom - bh
    bw = (w - 3 * 8) // 4
    for i, nom in enumerate(("BOTIQUÍN", "BATERÍA", "ESCUDO", "RECARGAR")):
        _p2_boton(Z, pygame.Rect(x + i * (bw + 8), yb, bw, bh), nom)

def p2_contadores(d):
    d = d or {}
    s_ = d.get("sess") or {}
    led = (d.get("footcz") or {}).get("led") or {}
    car = d.get("career") or {}
    bits = []
    if s_.get("kfoot") is not None or s_.get("kills") is not None:
        bits.append(f"SESIÓN {fnum(s_.get('kfoot', 0), 0)}")
    if led.get("n"):
        bits.append(f"SIN ENTREGAR {fnum(led['n'], 0)} ({cr(led.get('cr', 0))} cr)")
    elif led:
        bits.append("SIN ENTREGAR 0")
    if car.get("foot") is not None:
        bits.append(f"TOTAL A PIE {fnum(car['foot'], 0)}")
    return "  ·  ".join(bits)

def p2_registro(Z, d, flags, now):
    d = d or {}
    a = c2_marco(Z, "REGISTRO", p2_contadores(d) or None, dcol=WHITE)
    kills = ((d.get("combat") or {}).get("kills") or [])[:3]
    Zc = d.get("footcz") or {}
    x, w = a.x, a.w
    y = a.y - 12
    lh = (a.bottom + 8 - y) // 3
    if not kills:
        put(Z, F["small"], "sin bajas en esta sesión", (x, y + 4), DIM)
    for tgt, rew, kind in kills:
        tag, sub, col = C2_TIPO.get(kind, ("BAJA", "", DIM))
        put(Z, F["small"], "BAJA", (x, y), GREEN)
        put(Z, F["small"], tgt, (x + 150, y), WHITE, w * 0.45)
        put(Z, F["tiny"], sub, (x + 150 + int(w * 0.47), y + 3), col)
        if rew:
            put(Z, F["small"], f"+{fnum(rew, 0)} cr", (x + w, y), GREEN, anchor="topright")
        y += lh
    lz_hit((0, 0, Z.get_width(), Z.get_height()), "vista", 61)

_lz_tablero_v22b2 = lz_tablero

def lz_tablero(S, d, flags, now):
    mode = big_mode(d, flags)
    if not (mode == "COMBATE A PIE" and comb2_on() and cfg.get("bigmode", "4") == "4"):
        return _lz_tablero_v22b2(S, d, flags, now)
    if not lienzo_dibuja(S, lz_tab_cabecera, d, flags, now, mode):
        return _lz_tablero_v22b2(S, d, flags, now)
    if cfg.get("perf"):
        pr = lz_real((700, 64, 10, 10))
        perf_draw(S, pr.x, pr.y)
    LZ["colr"] = None
    BIG["cellmap"] = []
    BIG["fast"] = True                               # el mapa se mueve
    ok = all([lz_zona(S, p2_mapa, 150, P2_L, d, flags, now),
              lz_zona(S, p2_traje, 5, P2_R, d, flags, now),
              lz_zona(S, p2_registro, 61, C2_B, d, flags, now)])
    BIG["rects"] = [(150, lz_real(P2_L)), (5, lz_real(P2_R)), (61, lz_real(C2_B))]
    if not ok:
        S.fill(BLACK)
        LZ["cel"] = {}
        return _lz_tablero_v22b2(S, d, flags, now)
    return True
