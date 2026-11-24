# Panel Elite v2.2 · parte 56: v2.2b1 — COMBATE DE NAVE en 2 CUADROS GRANDES (con PANTALLA v2)
#   Tablero de la HDMI en modo COMBATE (armas fuera): en vez de los 4 cuadros (EN VIVO, COMBATE, REGISTRO, PIPS),
#   dos cuadros grandes y una franja abajo:
#     - OBJETIVO: modelo, piloto y rango, BUSCADO/LIMPIO, ESCUDOS y ARMAZÓN en grande, subsistema y su estado,
#       facción, recompensa, potencia y escuadrón (lo que el juego dé según el escaneo); botones NÚCLEO y SIG. SUBSIST.
#       Sin objetivo: OBJETIVO, SIGUIENTE, PELIGROSO y SU OBJETIVO para fijar uno.
#     - TU NAVE: escudos (activos / caídos con su tiempo), casco, calor, combustible y PIPS con sus botones.
#     - REGISTRO: los últimos derribos y, en su borde, SESIÓN · SIN ENTREGAR · TOTAL (bajas de nave).
#   Los botones hacen lo mismo que los de COMBATE y PIPS (mismas teclas). Con el caza fuera sigue el tablero de siempre.
#   12 AJUSTES > PANTALLA > COMBATE: 2 CUADROS / 4 CUADROS (2 de fábrica).

AMBAR = (255, 210, 60)
C2_LETRAS = (("big", 54), ("btn", 40), ("small", 31), ("num", 64), ("clock", 110), ("mono", 20), ("tiny", 26), ("chip", 20))
C2_L = (6, 102, 628, 566)                         # cuadros en coordenadas del lienzo (1280x800)
C2_R = (646, 102, 628, 566)
C2_B = (6, 680, 1268, 114)

def comb2_on():
    return cfg.get("comb2", "2") == "2"

# ---------------------------------------------------------------------------------------------------------------
# zona: un trozo del tablero con su propio tamaño base, dibujado a la escala del lienzo (como las celdas de 640x316)
# ---------------------------------------------------------------------------------------------------------------
class _ZonaSurf(ScaledSurf):
    def __init__(self, real, k, bw, bh):
        ScaledSurf.__init__(self, real, k, k)
        self.bw, self.bh = bw, bh
    def get_size(self):
        return (self.bw, self.bh)
    def get_width(self):
        return self.bw
    def get_height(self):
        return self.bh
    def get_rect(self, **kw):
        r = pygame.Rect(0, 0, self.bw, self.bh)
        for a, v in kw.items():
            setattr(r, a, v)
        return r
    def get_clip(self):
        return self.clip or pygame.Rect(0, 0, self.bw, self.bh)

ZonaSurf = type("ScaledSurf", (_ZonaSurf,), {})

def c2_letras(k):
    out = {}
    for n, base in C2_LETRAS:
        size = max(6, int(round(base * k)))
        if ("c2", n, size) not in _HIF:
            mono = pygame.font.match_font("dejavusansmono") or pygame.font.match_font("monospace")
            _HIF[("c2", n, size)] = pygame.font.Font(mono if n == "mono" else None, size)
        out[n] = FontProxy(_HIF[("c2", n, size)], size / base)
    return out

def lz_zona(S, fn, v, rect, d, flags, now):
    """Dibuja fn(Z, d, flags, now) en el trozo rect del lienzo; sus toques van a LZ['cel'][v] (como un cuadro)."""
    s, _, _ = lienzo_escala()
    rect = pygame.Rect(rect)
    sub_r = lz_real(rect).clip(S.get_rect())
    if sub_r.w < 8 or sub_r.h < 8:
        return False
    sub = S.subsurface(sub_r)
    keep, hits0 = dict(F), LZ["hits"]
    LZ["hits"] = []
    HI_IDS.clear(); HI_KEEP.clear()
    F.update(c2_letras(s))
    try:
        fn(ZonaSurf(sub, s, rect.w, rect.h), d, flags, now)
        LZ["cel"][v] = (sub_r, s, LZ["hits"])
        return True
    except Exception as e:
        log_exc(f"combate 2 cuadros ({v})", e)
        sub.fill(BLACK)
        return False
    finally:
        LZ["hits"] = hits0
        F.clear(); F.update(keep)
        HI_IDS.clear(); HI_KEEP.clear()

# ---------------------------------------------------------------------------------------------------------------
# piezas
# ---------------------------------------------------------------------------------------------------------------
def c2_marco(Z, titulo, dch=None, col=ORANGE, dcol=DIM):
    w, h = Z.get_size()
    r = pygame.Rect(1, 14, w - 2, h - 15)
    pygame.draw.rect(Z, col, r, 2, border_radius=4)
    for cx, cy, sx, sy in ((r.x, r.y, 1, 1), (r.right - 1, r.y, -1, 1), (r.x, r.bottom - 1, 1, -1), (r.right - 1, r.bottom - 1, -1, -1)):
        pygame.draw.line(Z, AMBAR, (cx, cy), (cx + 22 * sx, cy), 4)
        pygame.draw.line(Z, AMBAR, (cx, cy), (cx, cy + 22 * sy), 4)
    f = F["small"]
    tw = tw_(f, titulo)
    pygame.draw.rect(Z, BLACK, (16, 0, min(tw, w * 0.7) + 14, 28))
    put(Z, f, titulo, (23, 1), col, w * 0.7)
    if dch:
        hueco = w - tw - 100
        fd = next((F[n] for n in ("tiny", "chip") if tw_(F[n], dch) <= hueco), F["chip"])
        dw = min(tw_(fd, dch), hueco)
        pygame.draw.rect(Z, BLACK, (w - 44 - dw, 2, dw + 16, 26))
        put(Z, fd, dch, (w - 36, 4 + (F["tiny"].get_height() - fd.get_height()) // 2), dcol, hueco, anchor="topright")
    return pygame.Rect(r.x + 22, r.y + 22, r.w - 44, r.h - 34)

def c2_barra(Z, x, y, w, h, etq, pct, col, txt=None, delta=None):
    """Barra de 10 tramos con su rótulo y valor encima."""
    put(Z, F["small"], etq, (x, y), DIM)
    val = txt if txt is not None else ("-" if pct is None else f"{pct:.0f} %")
    vw = put(Z, F["btn"], val, (x + w, y - 4), col if pct is not None or txt else DIM, anchor="topright")
    if delta and delta >= 1:
        put(Z, F["small"], f"-{delta:.0f}%", (x + w - vw - 14, y), RED, anchor="topright")
    y += F["small"].get_height() + 6
    r = pygame.Rect(x, y, w, h)
    pygame.draw.rect(Z, DIM, r, 2)
    if pct:
        pygame.draw.rect(Z, col, (r.x + 3, r.y + 3, int((r.w - 6) * max(0, min(100, pct)) / 100), r.h - 6))
    for i in range(1, 10):
        xx = r.x + r.w * i // 10
        pygame.draw.line(Z, BLACK, (xx, r.y + 2), (xx, r.bottom - 2), 2)
    return r.bottom

def c2_etiqueta(Z, r, txt, col, txtcol=BLACK):
    pygame.draw.rect(Z, col, r, border_radius=6)
    put(Z, F["small"], txt, r.center, txtcol, r.w - 10, anchor="center")

def c2_fila(Z, x, y, w, etq, val, col=WHITE):
    put(Z, F["tiny"], etq, (x, y + 4), DIM)
    put(Z, F["small"], val, (x + 180, y), col, w - 180)
    return y + F["small"].get_height() + 4

def _c6_i(nombre):
    return next((i for i, b in enumerate(COMBAT_BTNS) if b[0] == nombre), None)

def c2_boton6(Z, r, nombre, txt=None, sub=None, col=None):
    """Botón de COMBATE (6): misma tecla que el de 480x320."""
    i = _c6_i(nombre)
    if i is None:
        return
    key = COMBAT_BTNS[i][1]
    lz_boton_v(Z, r, txt or nombre, sub if sub is not None else (key.upper() if key and key != SIN else "sin tecla"),
               F["btn"], lit=flash.get((6, i), 0) > time.time(), viejo=c6_rect(i))

# ---------------------------------------------------------------------------------------------------------------
# OBJETIVO
# ---------------------------------------------------------------------------------------------------------------
def c2_objetivo(Z, d, flags, now):
    d = d or {}
    t = d.get("target")
    W_, H_ = Z.get_size()
    if not t:
        a = c2_marco(Z, "OBJETIVO")
        put(Z, F["big"], "SIN OBJETIVO", (W_ // 2, a.y + 120), DIM, anchor="center")
        put(Z, F["small"], "fija una nave para ver sus escudos y su armazón", (W_ // 2, a.y + 170), DIM, a.w, anchor="center")
        bh = 76
        for k, nom in enumerate(("OBJETIVO", "SIGUIENTE", "PELIGROSO", "SU OBJ.")):
            r = pygame.Rect(a.x + (k % 2) * (a.w // 2 + 6), a.bottom - 2 * bh - 10 + (k // 2) * (bh + 10), a.w // 2 - 6, bh)
            c2_boton6(Z, r, nom)
        return
    scan = t.get("scan", 0)
    age = pc_now(d, now) - t["t"] if t.get("t") else 0
    a = c2_marco(Z, f"OBJETIVO · ESCANEO {scan}/3", f"hace {age:.0f} s" if age >= 5 else None)
    x, w = a.x, a.w
    y = a.y - 4
    legal = (t.get("legal") or "")
    wanted = legal.lower() == "wanted"
    if legal:
        lg = LEGAL.get(legal, (legal.upper(), None))[0]
        lw = max(130, tw_(F["small"], lg) + 24)
        c2_etiqueta(Z, pygame.Rect(x + w - lw, y + 4, lw, 40), lg, RED if wanted else GREEN, WHITE if wanted else BLACK)
        nw = w - lw - 16
    else:
        nw = w
    put_fit(Z, ("big", "btn", "small"), (t.get("ship") or "?").upper(), (x, y), WHITE, nw)
    y += F["big"].get_height() + 2
    cmdr = t.get("cmdr")
    if t.get("pilot"):
        piloto = t["pilot"] + (f" · {t['rank']}" if t.get("rank") else "")
        pw = put(Z, F["small"], piloto, (x, y), BLUE if cmdr else WHITE, w - (170 if cmdr else 0))
        if cmdr:
            put(Z, F["tiny"], "COMANDANTE", (x + pw + 14, y + 4), BLUE)
    y += F["small"].get_height() + 14
    mine = TGT["key"] == (t.get("stype"), t.get("pilot"))
    sh, hu = t.get("shield"), t.get("hull")
    y = c2_barra(Z, x, y, w, 40, "ESCUDOS", sh, BLUE, delta=TGT["dsh"] if mine else None) + 14
    hcol = RED if hu is not None and hu < 25 else GREEN
    y = c2_barra(Z, x, y, w, 40, "ARMAZÓN", hu, hcol, delta=TGT["dhu"] if mine else None) + 16
    bot_btn = a.bottom - 58
    if t.get("subsys"):
        shs = t.get("subhealth")
        put(Z, F["tiny"], "SUBSISTEMA", (x, y), DIM)
        y += F["tiny"].get_height() + 2
        scol = RED if shs is not None and shs < 20 else AMBAR
        vw = put(Z, F["btn"], f"{shs:.0f} %" if shs is not None else "", (x + w, y), scol, anchor="topright")
        put(Z, F["btn"], t["subsys"].upper(), (x, y), scol, w - vw - 16)
        y += F["btn"].get_height() + 8
    pygame.draw.line(Z, DIM, (x, y), (x + w, y), 1)
    y += 8
    filas = []
    if t.get("faction"):
        filas.append(("FACCIÓN", t["faction"], GREEN if es_mi_fac(t["faction"]) else WHITE))
    if t.get("bounty"):
        filas.append(("RECOMPENSA", f"{fnum(t['bounty'], 0)} cr", RED))
    if t.get("power"):
        filas.append(("POTENCIA", t["power"], MERC))
    ia = t.get("inara") or {}
    if cmdr and ia and not ia.get("none") and ia.get("squad"):
        ally = my_squad(d) and ia["squad"].lower() == my_squad(d).lower()
        filas.append(("ESCUADRÓN", ia["squad"] + ("  · ALIADO" if ally else ""), GREEN if ally else WHITE))
    if not filas and scan < 3:
        put(Z, F["small"], "sigue apuntando para terminar el escaneo", (x, y), DIM, w)
    for etq, val, col in filas:
        if y + F["small"].get_height() > bot_btn - 6:
            break
        y = c2_fila(Z, x, y, w, etq, val, col)
    # botones
    half = (w - 14) // 2
    rn = pygame.Rect(x, bot_btn, half, 58)
    ok = nuc_es_planta(t)
    auto = (cfg.get("autoev") or {}).get("nucleo", False)
    sub = NUC["msg"] if NUC["run"] else ("APUNTADO" if ok else ("AUTO" if auto else "planta de energía"))
    lit = NUC["run"] and int(now * 3) % 2 == 0
    if ok or lit:
        pygame.draw.rect(Z, WHITE if lit else GREEN, rn, border_radius=8)
        tc = BLACK
    else:
        pygame.draw.rect(Z, RED, rn, border_radius=8)
        tc = WHITE
    put(Z, F["btn"], "NÚCLEO", (rn.centerx, rn.y + 4), tc, rn.w - 10, anchor="midtop")
    put(Z, F["tiny"], sub, (rn.centerx, rn.bottom - 4), tc, rn.w - 10, anchor="midbottom")
    lz_hit(rn, "nucleo")
    c2_boton6(Z, pygame.Rect(x + half + 14, bot_btn, half, 58), "SUBSIST.", "SIG. SUBSIST.")

# ---------------------------------------------------------------------------------------------------------------
# TU NAVE
# ---------------------------------------------------------------------------------------------------------------
def c2_nave(Z, d, flags, now):
    d = d or {}
    Lv = d.get("live") or {}
    sh = Lv.get("ship") or {}
    nom = " · ".join(x for x in (sh.get("name"), sh.get("ident")) if x)
    a = c2_marco(Z, "TU NAVE" + (f" · {sh['ship'].upper()}" if sh.get("ship") else ""), nom or None)
    x, w = a.x, a.w
    y = a.y - 4
    # escudos: el juego no da el %, solo si están activos o caídos
    sd = None if flags & 8 else ((d.get("combat") or {}).get("sd"))
    if flags & 8:
        y = c2_barra(Z, x, y, w, 34, "ESCUDOS", 100, BLUE, txt="ACTIVOS") + 12
    else:
        el = int(now - sd) if sd else None
        txt = f"CAÍDOS {el // 60:02d}:{el % 60:02d}" if el is not None else "SIN ESCUDOS"
        blink = el is not None and int(now * 2) % 2 == 0
        y = c2_barra(Z, x, y, w, 34, "ESCUDOS", 0, RED if not blink else WHITE, txt=txt) + 12
    hull = pctv(sh.get("hull"))
    y = c2_barra(Z, x, y, w, 34, "CASCO", hull, RED if hull is not None and hull < 25 else ORANGE if hull is not None and hull < 50 else GREEN) + 12
    half = (w - 20) // 2
    calor = bool(flags & (1 << 20))
    put(Z, F["small"], "CALOR", (x, y), DIM)
    y2 = y + F["small"].get_height() + 4
    r = pygame.Rect(x, y2, half, 34)
    pygame.draw.rect(Z, RED if calor else DIM, r, 0 if calor else 2, border_radius=4)
    if calor and int(now * 2) % 2 == 0:
        pygame.draw.rect(Z, WHITE, r, 3, border_radius=4)
    put(Z, F["small"], "SOBRECALENTADO" if calor else ("SILENCIOSO" if flags & (1 << 10) else "NORMAL"), r.center,
        WHITE if calor else (BLUE if flags & (1 << 10) else GREEN), r.w - 10, anchor="center")
    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
    fp = fuel / cap * 100 if fuel is not None and cap else None
    c2_barra(Z, x + half + 20, y, half, 34, "COMBUST.", fp, RED if fp is not None and fp < 25 else ORANGE,
             txt=None if fp is not None else (f"{fuel:.1f} t" if fuel is not None else None))
    y = y2 + 34 + 14
    # PIPS: tocar una columna suma un pip (como en PIPS); abajo los atajos
    pips = d.get("Pips") or [0, 0, 0]
    bh = 50
    pz = pygame.Rect(x, y, w, a.bottom - bh - 12 - y)
    sc = scb_aprox(d)
    put(Z, F["small"], "PIPS", (x, y - 2), DIM)
    if sc:
        n, mx = sc
        put(Z, F["small"], f"CÉLULAS ≈ {n}" + (f" / {mx}" if mx else ""), (x + w, y - 2), RED if n <= 1 else BLUE, anchor="topright")
    top = y + F["small"].get_height() + 2
    cw = w // 3
    for i, (name, key) in enumerate(PIP_COLS):
        col = pygame.Rect(x + i * cw + 6, top, cw - 12, pz.bottom - top)
        lit = flash.get((2, i), 0) > now
        val = pips[i] if i < len(pips) else 0
        lab_h = F["btn"].get_height()
        bot = col.bottom - lab_h - 6
        gap = 6
        bh_ = max(8, (bot - col.y - 3 * gap) // 4)
        for p in range(4):
            br = pygame.Rect(col.x + 18, bot - (p + 1) * bh_ - p * gap, col.w - 36, bh_)
            fill = max(0, min(2, val - p * 2))
            pygame.draw.rect(Z, DIM, br, 1)
            if fill:
                pygame.draw.rect(Z, WHITE if lit else ORANGE, (br.x + 2, br.y + 2, (br.w - 4) * fill // 2, br.h - 4))
        put(Z, F["btn"], ("SYS", "MOT", "ARM")[i] if i < 3 else name, (col.centerx, bot + 4), WHITE if lit else ORANGE, anchor="midtop")
        lz_hit(col, "old", pip_rect(i).centerx, pip_rect(i).centery)
    yb = a.bottom - bh
    bw = (w - 3 * 10) // 4
    for i, (name, ks) in enumerate(PIP_PRESETS):
        r = pygame.Rect(x + i * (bw + 10), yb, bw, bh)
        lit = flash.get((2, 10 + i), 0) > now
        pygame.draw.rect(Z, WHITE if lit else (ORANGE if i else DIM), r, border_radius=8)
        put(Z, F["small"], name, r.center, BLACK if (lit or i) else WHITE, r.w - 8, anchor="center")
        lz_hit(r, "old", preset_rect(i).centerx, preset_rect(i).centery)

# ---------------------------------------------------------------------------------------------------------------
# REGISTRO y contadores de bajas (nave)
# ---------------------------------------------------------------------------------------------------------------
def c2_contadores(d):
    d = d or {}
    s_ = d.get("sess") or {}
    led = (d.get("footcz") or {}).get("led") or {}
    car = d.get("career") or {}
    bits = []
    if s_.get("kills") is not None:
        bits.append(f"SESIÓN {fnum(max(0, s_.get('kills', 0) - s_.get('kfoot', 0)), 0)}")
    if led.get("n"):
        bits.append(f"SIN ENTREGAR {fnum(led['n'], 0)} ({cr(led.get('cr', 0))} cr)")
    elif led:
        bits.append("SIN ENTREGAR 0")
    if car.get("bonds") is not None or car.get("bounties") is not None:
        bits.append(f"TOTAL {fnum((car.get('bonds') or 0) + (car.get('bounties') or 0), 0)}")
    return "  ·  ".join(bits)

C2_TIPO = {"R": ("DERRIBO", "RECOMPENSA", ORANGE), "B": ("DERRIBO", "BONO", BLUE), "P": ("DERRIBO", "PvP", RED),
           "T": ("DERRIBO", "THARGOIDE", GREEN)}

def c2_registro(Z, d, flags, now):
    d = d or {}
    a = c2_marco(Z, "REGISTRO", c2_contadores(d) or None, dcol=WHITE)
    kills = ((d.get("combat") or {}).get("kills") or [])[:3]
    x, w = a.x, a.w
    y = a.y - 12
    lh = (a.bottom + 8 - y) // 3
    if not kills:
        put(Z, F["small"], "sin derribos en esta sesión", (x, y + 4), DIM)
    for tgt, rew, kind in kills:
        tag, sub, col = C2_TIPO.get(kind, ("DERRIBO", "", DIM))
        put(Z, F["small"], tag, (x, y), GREEN)
        put(Z, F["small"], tgt, (x + 150, y), WHITE, w * 0.45)
        put(Z, F["tiny"], sub, (x + 150 + int(w * 0.47), y + 3), col)
        if rew:
            put(Z, F["small"], f"+{fnum(rew, 0)} cr", (x + w, y), GREEN, anchor="topright")
        y += lh
    lz_hit((0, 0, Z.get_width(), Z.get_height()), "vista", 61)

LZ_ACC["vista"] = lambda acc, X, Y: ui.__setitem__("view", acc[1])

# ---------------------------------------------------------------------------------------------------------------
# enganche en el tablero
# ---------------------------------------------------------------------------------------------------------------
_lz_tablero_v22b1 = lz_tablero

def lz_tablero(S, d, flags, now):
    mode = big_mode(d, flags)
    if not (mode == "COMBATE" and comb2_on() and cfg.get("bigmode", "4") == "4" and not fighter_out(d)):
        return _lz_tablero_v22b1(S, d, flags, now)
    if not lienzo_dibuja(S, lz_tab_cabecera, d, flags, now, mode):
        return _lz_tablero_v22b1(S, d, flags, now)
    if cfg.get("perf"):
        pr = lz_real((700, 64, 10, 10))
        perf_draw(S, pr.x, pr.y)
    LZ["colr"] = None
    BIG["cellmap"] = []
    ok = all([lz_zona(S, c2_objetivo, 6, C2_L, d, flags, now),
              lz_zona(S, c2_nave, 2, C2_R, d, flags, now),
              lz_zona(S, c2_registro, 61, C2_B, d, flags, now)])
    BIG["rects"] = [(6, lz_real(C2_L)), (2, lz_real(C2_R)), (61, lz_real(C2_B))]
    if not ok:                                         # algo ha fallado: el tablero de siempre
        S.fill(BLACK)
        LZ["cel"] = {}
        return _lz_tablero_v22b1(S, d, flags, now)
    return True

# ---------------------------------------------------------------------------------------------------------------
# 12 AJUSTES > PANTALLA: 7.º botón COMBATE (2 CUADROS / 4 CUADROS); la pantalla pasa a 4 columnas
# ---------------------------------------------------------------------------------------------------------------
def _pant_r(i, cols=4):
    return grid(i, cols, 2, TOP, H - 40)

def view_pantalla(surf, d, flags, now):
    f = cfg.get("bigfps", "AUTO")
    items = [("MODO", BIGMODES.get(cfg.get("bigmode", "4"), "4 CUADROS"), False),
             ("NITIDEZ", "ALTA" if cfg.get("sharp") else "NORMAL", bool(cfg.get("sharp"))),
             ("FPS", "AUTO (3/10)" if f == "AUTO" else f"{f} por seg.", False),
             ("CONSUMO", "SÍ" if cfg.get("perf") else "NO", bool(cfg.get("perf"))),
             ("RELOJ", clock_style() + ("" if cfg.get("reloj") else " (auto)"), False),
             ("RADAR CDSN", "ESTILO WEB" if cdsn_on() else "CLÁSICO", cdsn_on()),
             ("COMBATE", "2 CUADROS" if comb2_on() else "4 CUADROS", comb2_on())]
    for i, (t, sub, fill) in enumerate(items):
        r = _pant_r(i)
        draw_button(surf, r, t, sub, F["btn"] if F["btn"].size(t)[0] < r.w - 10 else F["small"], filled=fill,
                    lit=flash.get((160, i), 0) > now)
    perf_update()
    x = 8
    for j, (t, col) in enumerate(perf_parts()):
        x += put(surf, F["btn"], t, (x, H - 32), col) + 14
    put(surf, F["small"], "pantalla grande", (W - 8, H - 26), DIM, anchor="topright")

VIEWS[160] = view_pantalla

_on_tap_v22b1 = on_tap

def on_tap(x, y):
    if ui.get("view") == 160 and not ui.get("idle_on") and TOP <= y < H - 40:
        i = next((k for k in range(8) if _pant_r(k).collidepoint(x, y)), None)
        if i is None or i == 7:
            return
        if i == 6:
            tap_flash((160, 6))
            cfg["comb2"] = "4" if comb2_on() else "2"
            plog("PANTALLA > COMBATE: " + ("2 CUADROS" if comb2_on() else "4 CUADROS"))
            save_cfg(); TAP_EV.set()
            return
        c = _pant_r(i, 3)                              # los 6 de siempre: a su sitio de antes (3 columnas)
        return _on_tap_v22b1(c.centerx, c.centery)
    return _on_tap_v22b1(x, y)
