# Panel Elite v2.0 · parte 41: v2.0b4 — CUADROS NUEVOS en el tablero (EN VIVO) y RECOGIDA DE COMBUSTIBLE a 1280x800
#   - Cuadros del tablero con diseño propio: cada uno se dibuja en una celda de 640x316 (CeldaSurf) que se escala igual
#     en ancho y alto al hueco del cuadro (4 CUADROS x1, GRANDE x2…). Registro LZ_CELDA[v] = función de dibujo.
#   - EN VIVO (100) nuevo: nave, SRV y a pie (también EN COMBATE a pie y el transporte), con las líneas de operación,
#     Merc Coin, copiloto, células de escudo y la banda del FSD. Toques: nombre de la nave -> ficha NAVE en el MENÚ;
#     NAVE AQUÍ -> fija la nave donde estás.
#   - RECOGIDA DE COMBUSTIBLE a pantalla entera, dibujada a 1280x800.
#   - Si un cuadro nuevo falla, se dibuja el de antes (nítido); con PANTALLA v2 en NO, todo como antes.

CW0, CH0 = 640, 316
LZ_CELF = (("big", 40), ("btn", 30), ("small", 24), ("num", 64), ("clock", 110), ("mono", 16), ("tiny", 20), ("chip", 17))
LZ_CELDA = {}
LZ["cel"] = {}

class _CeldaSurf(ScaledSurf):
    def get_size(self):
        return (CW0, CH0)
    def get_width(self):
        return CW0
    def get_height(self):
        return CH0
    def get_rect(self, **k):
        r = pygame.Rect(0, 0, CW0, CH0)
        for a, v in k.items():
            setattr(r, a, v)
        return r
    def get_clip(self):
        return self.clip or pygame.Rect(0, 0, CW0, CH0)

CeldaSurf = type("ScaledSurf", (_CeldaSurf,), {})

def lz_celda_letras(k):
    out = {}
    for n, base in LZ_CELF:
        size = max(6, int(round(base * k)))
        if ("cel", n, size) not in _HIF:
            mono = pygame.font.match_font("dejavusansmono") or pygame.font.match_font("monospace")
            _HIF[("cel", n, size)] = pygame.font.Font(mono if n == "mono" else None, size)
        out[n] = FontProxy(_HIF[("cel", n, size)], size / base)
    return out

def lz_celda_dibuja(S, fn, v, d, flags, now, area, how):
    k = min(area.w / CW0, area.h / CH0)
    w, h = int(CW0 * k), int(CH0 * k)
    y = area.y if how == "top" else area.centery - h // 2
    sub_r = pygame.Rect(area.centerx - w // 2, y, w, h).clip(S.get_rect())
    if sub_r.w < 4 or sub_r.h < 4:
        return False
    sub = S.subsurface(sub_r)
    keep, hits0 = dict(F), LZ["hits"]
    LZ["hits"] = []
    HI_IDS.clear(); HI_KEEP.clear()
    F.update(lz_celda_letras(k))
    try:
        fn(CeldaSurf(sub, k, k), d, flags, now)
        LZ["cel"][v] = (sub_r, k, LZ["hits"])
        return True
    except Exception as e:
        log_exc(f"cuadro {v}", e)
        sub.fill(BLACK)
        return False
    finally:
        LZ["hits"] = hits0
        F.clear(); F.update(keep)
        HI_IDS.clear(); HI_KEEP.clear()

_big_cell_v20b4 = big_cell

def big_cell(S, cell, v, d, flags, now, r, font, how, extra=""):
    fn = LZ_CELDA.get(v)
    if fn is None or not lienzo_on() or LZ.get("lleno") != "tablero":
        return _big_cell_v20b4(S, cell, v, d, flags, now, r, font, how, extra)
    if not BIG.get("rects"):
        BIG["cellmap"] = []
    BIG.setdefault("rects", []).append((v, r))
    pygame.draw.rect(S, DIM, r.inflate(-4, -4), 1, border_radius=6)
    lab = font.render(str(MENU.get(v, v)).upper() + extra, True, DIM)
    S.blit(lab, (r.x + 10, r.y + 4))
    top = r.y + lab.get_height() + 6
    area = pygame.Rect(r.x + 4, top, r.w - 8, r.bottom - 3 - top)
    if lz_celda_dibuja(S, fn, v, d, flags, now, area, how):
        return None
    vf = VIEWS.get(v)                                          # falla el nuevo: el de antes, nítido
    if vf is None or not hi_cell(S, vf, d, flags, now, area, how):
        big_cell_draw(cell, vf, d, flags, now)
        big_blit(S, cell.subsurface((0, TOP, W, H - TOP)), area)
    BIG["cellmap"].append((v, area, how))
    return None

# ---------------------------------------------------------------------------------------------------------------
# piezas de la celda (640x316)
# ---------------------------------------------------------------------------------------------------------------
def lc_barra(L, x, y, w, label, pct, col):
    lw = put(L, F["small"], label, (x, y + 2), DIM) + 10
    bx = pygame.Rect(x + lw, y, w - lw, 26)
    pygame.draw.rect(L, DIM, bx, 2, border_radius=3)
    if pct is not None:
        pygame.draw.rect(L, col, (bx.x + 3, bx.y + 3, int((bx.w - 6) * max(0, min(100, pct)) / 100), bx.h - 6))
        put(L, F["small"], f"{pct:.0f}%", (bx.right - 6, y + 2), WHITE, anchor="topright")

def lc_chips(L, items, y, cols=5, rh=30):
    cw = (CW0 - 16) // cols
    for k, (txt, on, col) in enumerate(items):
        r = pygame.Rect(8 + (k % cols) * cw, y + (k // cols) * rh, cw - 6, rh - 5)
        if on and glow(txt):
            col = WHITE
        if on:
            pygame.draw.rect(L, col, r, border_radius=5)
            put(L, F["chip"], txt, r.center, BLACK, cw - 10, anchor="center")
        else:
            pygame.draw.rect(L, DIM, r, 1, border_radius=5)
            put(L, F["chip"], txt, r.center, DIM, cw - 10, anchor="center")
    return y + ((len(items) + cols - 1) // cols) * rh

def lc_brujula(L, d, b, y0):
    """Brújula para volver a la nave (SRV y a pie) en la franja de abajo, con el botón NAVE AQUÍ."""
    ship, lat, lon, R = ship_pos(b), b.get("lat"), b.get("lon"), b.get("R")
    out = bool((d or {}).get("Flags", 0) & (1 << 26)) or bool((d or {}).get("Flags2", 0) & 1)
    SHIPOV["cur"] = (lat, lon) if (out and lat is not None) else None
    if out and lat is not None and R:
        r = pygame.Rect(250, y0 + 8, 150, 46)
        lit = flash.get(("nave", 0), 0) > time.time()
        pygame.draw.rect(L, WHITE if lit else ORANGE, r, 0 if lit else 2, border_radius=6)
        put(L, F["small"], "NAVE AQUÍ", r.center, BLACK if lit else ORANGE, anchor="center")
        lz_hit(r, "naveaqui")
    if not ship or lat is None or not R or not out:
        return
    pygame.draw.line(L, DIM, (8, y0), (CW0 - 8, y0), 1)
    dist = hav(ship, (lat, lon), R)
    p1, p2, dl = math.radians(lat), math.radians(ship[0]), math.radians(ship[1] - lon)
    brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                  math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
    hdg = b.get("hdg")
    cx, cy, r = 34, y0 + 31, 24
    pygame.draw.circle(L, DIM, (cx, cy), r, 2)
    if hdg is not None:
        a = math.radians(brg - hdg)
        pt = lambda k, da: (cx + r * k * math.sin(a + da), cy - r * k * math.cos(a + da))
        pygame.draw.polygon(L, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
    txt = f"{dist / 1000:.1f} km".replace(".", ",") if dist >= 1000 else f"{dist:.0f} m"
    put(L, F["tiny"], "NAVE", (70, y0 + 6), DIM)
    put(L, F["big"], txt, (70, y0 + 22), GREEN, 170)
    put(L, F["btn"], f"rumbo {brg:.0f}°", (CW0 - 8, y0 + 8), ORANGE, anchor="topright")
    if hdg is not None:
        put(L, F["small"], f"vas a {hdg:.0f}°", (CW0 - 8, y0 + 38), DIM, anchor="topright")

def lc_consumibles(L, d, x, y):
    c, mx = cons_count(d), suit_max(d)
    h_ = F["btn"].get_height()
    draw_med(L, x + 9, y + h_ // 2, 1.6, cons_col(c.get("med", 0)))
    x += 22 + put(L, F["btn"], str(c.get("med", 0)), (x + 22, y), cons_col(c.get("med", 0))) + 12
    draw_bolt(L, x, y + 2, cons_col(c.get("cell", 0)), 1.2)
    x += 18 + put(L, F["btn"], str(c.get("cell", 0)), (x + 18, y), cons_col(c.get("cell", 0))) + 14
    for k, lab in EXPL:
        if not mx.get(k) and not c.get(k):
            continue
        x += put(L, F["tiny"], lab, (x, y + h_ // 2 - 9), DIM) + 6
        x += draw_pips(L, x, y + h_ // 2 - 8, c.get(k, 0), mx.get(k, 0), 16, 16) + 12

def lc_franja(L, d, flags, now):
    """Línea de abajo de la nave: banda del FSD, o operación / Merc Coin a la izquierda y copiloto / células a la derecha."""
    y = CH0 - 34
    if FSDC.get("t0") is not None:
        el = now - FSDC["t0"]
        r = pygame.Rect(8, y, CW0 - 16, 30)
        pygame.draw.rect(L, BLACK, r)
        pygame.draw.rect(L, BLUE, r, 2, border_radius=5)
        if FSDC["est"]:
            k = min(1.0, el / FSDC["est"])
            pygame.draw.rect(L, (20, 50, 90), (r.x + 2, r.y + 2, int((r.w - 4) * k), r.h - 4), border_radius=5)
            txt = f"FSD LISTO EN ≈ {FSDC['left']:.0f} s" if FSDC["left"] > 0.5 else "FSD CASI LISTO…"
        else:
            txt = f"FSD ENFRIÁNDOSE · {el:.0f} s (aprendiendo cuánto tarda esta nave)"
        put(L, F["small"], txt, r.center, WHITE, r.w - 12, anchor="center")
        return
    O = d.get("ops") or {}
    izq = ""
    col_i = MERC
    if O.get("on"):
        mins = int((now - (O.get("t0") or now)) // 60)
        izq = f"OPERACIÓN · {O.get('kills', 0)} derribos · {crx(O.get('cr', 0))} cr · {mins} min"
        col_i = RED
    elif O.get("merc") is not None:
        izq = f"MERC COIN {fnum(O['merc'], 0)}" + (f"  (+{O['lastgain']})" if O.get("lastgain") else "")
    wi = put(L, F["small"], izq, (8, y + 4), col_i, CW0 - 16) if izq else 0
    c_ = O.get("crew") or {}
    sc = scb_aprox(d)
    if c_.get("paid"):
        put(L, F["small"], f"copiloto {c_.get('name', '')}: -{crx(c_['paid'])} cr", (CW0 - 8, y + 4), (70, 120, 230),
            max(60, CW0 - 30 - wi), anchor="topright")
    elif sc:
        n, mx = sc
        put(L, F["small"], f"CÉLULAS ≈ {n}" + (f" / {mx}" if mx else ""), (CW0 - 8, y + 4), RED if n <= 1 else BLUE,
            max(60, CW0 - 30 - wi), anchor="topright")

# ---------------------------------------------------------------------------------------------------------------
# EN VIVO
# ---------------------------------------------------------------------------------------------------------------
def lc_envivo(L, d, flags, now):
    d = d or {}
    if lc_taxi(L, d, now):
        return
    Lv, f2 = d.get("live") or {}, d.get("Flags2", 0)
    if f2 & 1:
        mode = "A PIE"
    elif flags & (1 << 26):
        mode = (d.get("srvtype") or "SRV").upper()
    elif flags & (1 << 25):
        mode = "CAZA"
    else:
        mode = "NAVE"
    if mode == "A PIE" and in_fight(d, now):
        return lc_combate_pie(L, d, now)
    put(L, F["big"], mode, (10, 4), GREEN)
    if mode == "A PIE":
        return lc_a_pie(L, d, Lv, f2, now)
    if flags & (1 << 26):
        return lc_srv(L, d, flags, now)
    return lc_nave(L, d, Lv, flags, now)

def lc_nave(L, d, Lv, flags, now):
    sh = Lv.get("ship") or {}
    nm = " · ".join(x for x in (sh.get("name"), sh.get("ident")) if x)
    put(L, F["small"], (sh.get("ship") or "").upper(), (CW0 - 10, 4), ORANGE, 380, anchor="topright")
    put(L, F["small"], nm, (CW0 - 10, 30), (70, 120, 230), 380, anchor="topright")
    lz_hit((CW0 - 400, 0, 400, 58), "nave")
    y = 64
    hull = pctv(sh.get("hull"))
    half = (CW0 - 28) // 2
    lc_barra(L, 8, y, half, "CASCO", hull, RED if hull is not None and hull < 30 else ORANGE)
    cg, cap = Lv.get("cargo"), d.get("cargocap")
    put(L, F["small"], "CARGA", (20 + half, y + 2), DIM)
    put(L, F["btn"], f"{cg:.0f} / {cap if cap is not None else '?'} t" if cg is not None else "-", (CW0 - 10, y - 2), ORANGE,
        anchor="topright")
    y += 36
    lg, kind = LEGAL.get(Lv.get("legal"), (Lv.get("legal") or "-", None))
    put(L, F["small"], "ESTADO", (8, y + 4), DIM)
    put(L, F["btn"], lg, (100, y), RED if kind else GREEN, 230)
    alt = Lv.get("alt")
    if alt is not None and flags & (1 << 21):
        real = not flags & (1 << 29)
        lab, acol = "ALTITUD", ORANGE
        if real and 7 <= alt <= 40:
            lab, acol = "RHINO OK", GREEN
        elif real and alt < 7:
            lab, acol = "SUBE A 7 m", ORANGE
        elif real and alt <= 80:
            lab, acol = "BAJA A 40 m", ORANGE
        put(L, F["small"], lab, (350, y + 4), acol if lab != "ALTITUD" else DIM)
        put(L, F["btn"], f"{alt / 1000:.1f} km".replace(".", ",") if alt >= 1000 else f"{alt:.0f} m", (CW0 - 10, y), acol,
            anchor="topright")
    y += 38
    rh = sh.get("rhino")
    rcol = GREEN if rh == "A BORDO" else RED if rh == "SIN RHINO" else ORANGE
    lc_chips(L, ([(f"RHINO {rh}" if rh != "SIN RHINO" else rh, rh in ("A BORDO", "SIN RHINO", "FUERA"), rcol)] if rh else [])
             + veh_chips(d, rh) + [("ATRACADO", flags & 1, BLUE), ("ATERRIZADO", flags & 2, BLUE), ("TREN", flags & 4, ORANGE),
                                   ("ESCUDOS", flags & 8, BLUE), ("SUPERCRUCERO", flags & 16, BLUE), ("FA OFF", flags & 32, RED),
                                   ("ARMAS", flags & 64, RED), ("LUCES", flags & 256, ORANGE), ("RECOGEDOR", flags & 512, ORANGE),
                                   ("SILENCIOSO", flags & 1024, BLUE), ("RECOG. COMB.", flags & 2048, ORANGE),
                                   ("MASA BLOQ.", flags & (1 << 16), RED), ("FSD CARGANDO", flags & (1 << 17), BLUE),
                                   ("FSD ENFRIANDO", flags & (1 << 18), DIM), ("SOBRECALENT.", flags & (1 << 20), RED),
                                   ("VISIÓN NOCT.", flags & (1 << 28), GREEN)], y)
    lc_franja(L, d, flags, now)

def lc_srv(L, d, flags, now):
    put(L, F["small"], d.get("body") or "", (CW0 - 10, 10), ORANGE, 380, anchor="topright")
    y = lc_chips(L, [("FRENO MANO", flags & (1 << 12), RED), ("TORRETA", flags & (1 << 13), ORANGE),
                     ("TORR. RECOGIDA", flags & (1 << 14), DIM), ("ASIST. CONDUC.", flags & (1 << 15), GREEN),
                     ("LUCES", flags & (1 << 8), ORANGE), ("LUCES LARGAS", flags & (1 << 31), ORANGE),
                     ("CARGA", flags & (1 << 9), ORANGE), ("SOBRECALENT.", flags & (1 << 20), RED)], 58, cols=4)
    if d.get("srvcargo") is not None:
        put(L, F["small"], "BODEGA", (8, y + 8), DIM)
        put(L, F["big"], f"{d['srvcargo']} t", (110, y), ORANGE)
        inv = ", ".join(f"{n} {c}" for n, c in (d.get("srvinv") or [])[:4])
        if inv:
            put(L, F["small"], inv, (230, y + 8), WHITE, CW0 - 240)
    y += 44
    sf = (d.get("Fuel") or {}).get("FuelReservoir")
    put(L, F["small"], "COMBUSTIBLE", (8, y + 8), DIM)
    put(L, F["big"], f"{sf:.2f} t".replace(".", ",") if sf is not None else "?", (160, y), RED if sf is not None and sf < 0.1 else ORANGE)
    shd = flags & 8
    put(L, F["btn"], "ESCUDOS ACTIVOS" if shd else "SIN ESCUDOS", (CW0 - 10, y + 4), BLUE if shd else RED, anchor="topright")
    y += 44
    sm = d.get("srvmats") or []
    if sm:
        put(L, F["small"], "RECOGIDO: " + ", ".join(f"{n} {c}" + (" (MÁX)" if full else "") for n, c, full in sm[:5]),
            (8, y), RED if any(x[2] for x in sm) else ORANGE, CW0 - 16)
    lc_brujula(L, d, d.get("bio") or {}, CH0 - 64)

def lc_a_pie(L, d, Lv, f2, now):
    s_ = Lv.get("suit") or {}
    put(L, F["small"], " · ".join(x for x in (s_.get("name"), s_.get("loadout")) if x), (CW0 - 10, 10), ORANGE, 380, anchor="topright")
    y = 54
    oxy, hp = pctv(Lv.get("oxy")), pctv(Lv.get("health"))
    half = (CW0 - 28) // 2
    lc_barra(L, 8, y, half, "OXÍGENO", oxy, RED if oxy is not None and oxy < 25 else BLUE)
    lc_barra(L, 20 + half, y, half, "SALUD", hp, RED if hp is not None and hp < 30 else GREEN)
    y += 32
    t = Lv.get("temp")
    tcol = RED if f2 & ((1 << 9) | (1 << 11)) else BLUE if f2 & ((1 << 8) | (1 << 10)) else ORANGE
    put(L, F["small"], "TEMPERATURA", (8, y + 6), DIM)
    put(L, F["big"], f"{t - 273.15:.0f} °C" if t is not None else "?", (160, y), tcol)
    g = Lv.get("grav")
    put(L, F["small"], "GRAVEDAD", (350, y + 6), DIM)
    put(L, F["big"], f"{g:.2f} G".replace(".", ",") if g is not None else "-", (CW0 - 10, y), RED if g and g > 2 else ORANGE,
        anchor="topright")
    y += 40
    put(L, F["small"], "ARMA", (8, y + 4), DIM)
    put(L, F["btn"], Lv.get("weapon") or "-", (80, y), ORANGE, CW0 - 90)
    y += 32
    act_ = [c_ for c_ in [("ESTACIÓN", f2 & (1 << 3), BLUE), ("PLANETA", f2 & (1 << 4), BLUE),
                          ("RESPIRABLE", f2 & (1 << 16), GREEN), ("POCO O2", f2 & (1 << 6), RED),
                          ("SALUD BAJA", f2 & (1 << 7), RED), ("FRÍO", f2 & ((1 << 8) | (1 << 10)), BLUE),
                          ("CALOR", f2 & ((1 << 9) | (1 << 11)), RED), ("PLANEO", f2 & (1 << 12), ORANGE)] if c_[1]]
    if act_:
        y = lc_chips(L, act_[:5], y)
    Z = d.get("footcz") or {}
    P = d.get("pack") or {}
    if Z.get("n"):
        led = Z.get("led") or {}
        zt = (Z.get("zone") or "ZONA DE COMBATE").upper() + (f"  ·  por {Z['side']}" if Z.get("side") else "")
        put(L, F["tiny"], zt, (8, y + 2), BLUE, CW0 - 16)
        put(L, F["btn"], f"{Z['n']} BAJAS", (8, y + 24), GREEN)
        put(L, F["btn"], f"{crx(led.get('cr', 0))} cr sin cobrar", (170, y + 24), ORANGE, 300)
        y += 58
    lc_consumibles(L, d, 8, y + 2)
    y += 34
    b = d.get("bio") or {}
    tiene_brujula = ship_pos(b) and b.get("lat") is not None and b.get("R")
    if not Z.get("n") and not tiene_brujula and (P.get("n_items") or P.get("n_comp") or P.get("n_data")):
        put(L, F["small"], f"Mochila: {P.get('n_items', 0)} objetos · {P.get('n_comp', 0)} componentes · {P.get('n_data', 0)} datos",
            (8, y), DIM, CW0 - 16)
    lc_brujula(L, d, b, CH0 - 64)

def lc_combate_pie(L, d, now):
    Lv, Z = d.get("live") or {}, d.get("footcz") or {}
    led = Z.get("led") or {}
    on_ = int(now * 2) % 2 == 0
    r_ = pygame.Rect(8, 4, 270, 44)
    pygame.draw.rect(L, RED, r_, 0 if on_ else 4, border_radius=8)
    put(L, F["big"], "EN COMBATE", r_.center, BLACK if on_ else RED, anchor="center")
    put(L, F["small"], suit_name_of(d), (CW0 - 10, 14), ORANGE, 330, anchor="topright")
    y = 58
    hp = pctv(Lv.get("health"))
    sd = (d.get("combat") or {}).get("sd")
    hb = pygame.Rect(8, y, CW0 - 210, 34)
    pygame.draw.rect(L, DIM, hb, 2)
    if hp is not None:
        pygame.draw.rect(L, RED if hp < 25 else ORANGE if hp < 50 else GREEN,
                         (hb.x + 3, hb.y + 3, int((hb.w - 6) * max(0, min(100, hp)) / 100), hb.h - 6))
    put(L, F["btn"], f"SALUD {hp:.0f} %" if hp is not None else "SALUD ?", hb.center, WHITE, anchor="center")
    sr = pygame.Rect(CW0 - 194, y, 186, 34)
    if sd:
        el = int(now - sd)
        pygame.draw.rect(L, RED, sr, 0 if on_ else 3, border_radius=6)
        put(L, F["btn"], f"ESCUDO {el // 60:02d}:{el % 60:02d}", sr.center, BLACK if on_ else RED, anchor="center")
    else:
        pygame.draw.rect(L, BLUE, sr, 3, border_radius=6)
        put(L, F["btn"], "ESCUDO OK", sr.center, BLUE, anchor="center")
    y += 42
    nb = str(Z.get("n") or 0)
    put(L, F["num"], nb, (8, y), GREEN)
    put(L, F["small"], "BAJAS", (16 + tw_(F["num"], nb), y + 34), GREEN)
    tf_ = (d.get("career") or {}).get("foot")
    if tf_ is not None:
        put(L, F["tiny"], f"total {fnum(tf_, 0)}", (16 + tw_(F["num"], nb), y + 8), DIM)
    c = cons_count(d)
    x = CW0 - 10
    for k in ("cell", "med"):
        n = c.get(k, 0)
        tw = tw_(F["num"], str(n))
        put(L, F["num"], str(n), (x, y), cons_col(n), anchor="topright")
        x -= tw + 8
        if k == "med":
            draw_med(L, x - 18, y + 30, 3.2, cons_col(n)); x -= 48
        else:
            draw_bolt(L, x - 30, y + 4, cons_col(n), 2.5); x -= 52
    y += 70
    put(L, F["big"], f"{crx(led.get('cr', 0))} cr", (8, y), ORANGE)
    put(L, F["small"], "sin cobrar", (16 + tw_(F["big"], f"{crx(led.get('cr', 0))} cr"), y + 12), DIM)
    if Z.get("rate"):
        put(L, F["btn"], f"{str(Z['rate']).replace('.', ',')} / min", (CW0 - 10, y + 4), DIM, anchor="topright")
    y += 48
    mx = suit_max(d)
    x = 8
    for k, lab in EXPL:
        if not mx.get(k) and not c.get(k):
            continue
        x += put(L, F["btn"], lab, (x, y + 2), DIM) + 8
        x += draw_pips(L, x, y, c.get(k, 0), mx.get(k, 0), 24, 30) + 18
    zt = (Z.get("zone") or "").upper() + (f"  ·  por {Z['side']}" if Z.get("side") else "")
    put(L, F["small"], "  ·  ".join(t for t in (zt, Lv.get("weapon")) if t), (8, CH0 - 30), DIM, CW0 - 16)

def lc_taxi(L, d, now):
    t = d.get("taxi") or {}
    st = t.get("st")
    if st not in ("booked", "aboard"):
        return False
    if st == "booked" and taxi_left(t, now) <= -TAXI_LOST:
        return False
    military = "MILITAR" in (t.get("kind") or "")
    kind = ("RETIRADA · " if t.get("retreat") else "") + (t.get("kind") or "TRANSPORTE")
    dest = t.get("loc") or t.get("sys") or ""
    y = 4
    put(L, F["small"], kind, (10, y), BLUE if not military else ORANGE, CW0 - 20); y += 32
    if st == "booked":
        left = taxi_left(t, now)
        if left <= 0:
            on_ = int(now * 3) % 2 == 0
            put(L, F["big"], "TRANSPORTE PERDIDO", (CW0 // 2, CH0 // 2 - 20), RED if on_ else ORANGE, anchor="center")
            put(L, F["small"], "se acabó el tiempo para subir", (CW0 // 2, CH0 // 2 + 24), DIM, anchor="center")
            return True
        put(L, F["big"], "TRANSPORTE RESERVADO", (10, y), GREEN); y += 48
        col = GREEN if left > 120 else ORANGE if left > 60 else (RED if int(now * 4) % 2 == 0 else BLACK)
        m_, s_ = int(left) // 60, int(left) % 60
        put(L, F["clock"], f"{m_}:{s_:02d}", (CW0 // 2, y + 50), col, anchor="center"); y += 104
        put(L, F["btn"], "para subir" if left > 60 else "¡SUBE YA!", (CW0 // 2, y), DIM if left > 60 else RED, anchor="center"); y += 30
        if dest:
            put(L, F["small"], "DESTINO", (10, y + 4), DIM)
            put(L, F["btn"], dest.upper(), (120, y), ORANGE, CW0 - 130); y += 34
        if t.get("cost"):
            put(L, F["small"], f"coste {cr(t['cost'])} cr", (10, y), DIM)
        return True
    put(L, F["big"], "A BORDO", (10, y), GREEN)
    put(L, F["big"], t.get("phase") or "", (CW0 - 10, y), BLUE, CW0 // 2, anchor="topright"); y += 50
    if dest:
        put(L, F["small"], "DESTINO", (10, y + 4), DIM)
        put(L, F["btn"], dest.upper(), (120, y), ORANGE, CW0 - 130); y += 38
    Lv = d.get("live") or {}
    alt, g = Lv.get("alt"), Lv.get("grav")
    if alt is not None or g is not None:
        if alt is not None:
            put(L, F["small"], "ALTITUD", (10, y + 4), DIM)
            put(L, F["btn"], f"{alt / 1000:.1f} km".replace(".", ",") if alt >= 1000 else f"{alt:.0f} m", (120, y), ORANGE)
        if g is not None:
            put(L, F["small"], "GRAVEDAD", (350, y + 4), DIM)
            put(L, F["btn"], f"{g:.2f} G".replace(".", ","), (CW0 - 10, y), RED if g > 2 else ORANGE, anchor="topright")
        y += 40
    if military and (t.get("zone") or t.get("fac")):
        pygame.draw.line(L, DIM, (10, y), (CW0 - 10, y), 1); y += 8
        put(L, F["small"], "ZONA DE COMBATE", (10, y), DIM); y += 28
        put(L, F["btn"], (t.get("zone") or "").upper(), (10, y), RED, CW0 - 20); y += 36
        fst = FSTATE_ES.get(t.get("fstate") or "", t.get("fstate") or "")
        put(L, F["small"], "  ·  ".join(x for x in (t.get("fac"), fst) if x), (10, y), ORANGE, CW0 - 20)
    return True

LZ_CELDA[100] = lc_envivo

# ---------------------------------------------------------------------------------------------------------------
# RECOGIDA DE COMBUSTIBLE a pantalla entera
# ---------------------------------------------------------------------------------------------------------------
def lz_recogida(L, d, flags, now):
    LZ["hits"] = []
    fuel = ((d or {}).get("Fuel") or {}).get("FuelMain")
    cap = (d or {}).get("fuelcap")
    if (d or {}).get("Flags", 0) & (1 << 26):
        fuel, cap = ((d or {}).get("Fuel") or {}).get("FuelReservoir"), None
    on, hot = bool(flags & (1 << 11)), bool(flags & (1 << 20))
    if on and fuel is not None:                               # mismo seguimiento que draw_scoop
        h = scoop["hist"]; h.append((now, fuel))
        while now - h[0][0] > 6:
            h.pop(0)
    else:
        if scoop["was"] and fuel is not None and cap and fuel >= cap - 0.05:
            scoop["full_until"] = now + 4
        scoop["hist"] = []
    scoop["was"] = on
    full = now < scoop["full_until"]
    L.fill(BLACK)
    if not on and not full:
        return
    blink = int(now * 3) % 2 == 0
    col = GREEN if full and not on else (RED if hot and blink else ORANGE)
    lz_marco(L, col, True)
    box = pygame.Rect(60, 130, LW - 120, 540)
    pygame.draw.rect(L, BLACK, box)
    for j in range(12):
        yy = box.y + 24 + (j * 47) % (box.h - 48)
        ln = (j * 103 + int(now * 300)) % 230
        pygame.draw.line(L, (90, 45, 0), (box.x + 20, yy), (box.x + 20 + ln, yy), 2)
        pygame.draw.line(L, (90, 45, 0), (box.right - 20 - ln, yy), (box.right - 20, yy), 2)
    pygame.draw.rect(L, col, box, 6, border_radius=20)
    cx, y = box.centerx, box.y + 36
    if full and not on:
        put_fit(L, ("clock", "num", "big"), "DEPÓSITO LLENO", (cx, box.centery - 30), GREEN, box.w - 60, anchor="center")
        if fuel is not None:
            put(L, F["big"], f"{fnum(fuel)} t", (cx, box.centery + 70), WHITE, anchor="center")
        return
    put(L, F["big"], "RECOGIENDO COMBUSTIBLE", (cx, y), ORANGE, box.w - 60, anchor="midtop"); y += 84
    if fuel is not None:
        put_fit(L, ("clock", "num", "big"), f"{fnum(fuel)} / {fnum(cap) if cap else '?'} t", (cx, y), WHITE, box.w - 60, anchor="midtop")
        y += 180
        bx = pygame.Rect(box.x + 50, y, box.w - 100, 44)
        pygame.draw.rect(L, DIM, bx, 3, border_radius=6)
        if cap:
            pct = max(0.0, min(1.0, fuel / cap))
            pygame.draw.rect(L, ORANGE, (bx.x + 5, bx.y + 5, int((bx.w - 10) * pct), bx.h - 10), border_radius=4)
            put(L, F["small"], f"{pct * 100:.0f}%", bx.center, WHITE, anchor="center")
        y += 64
    h = scoop["hist"]
    if len(h) >= 2 and h[-1][0] - h[0][0] > 1:
        rate = (h[-1][1] - h[0][1]) / (h[-1][0] - h[0][0])
        put(L, F["btn"], f"{fnum(rate, 2)} t/s", (box.x + 50, y), ORANGE)
        if rate > 0.001 and cap and fuel is not None:
            put(L, F["btn"], f"lleno en {dur_s((cap - fuel) / rate)}", (box.right - 50, y), ORANGE, anchor="topright")
    y += 66
    if hot:
        put(L, F["big"], "¡SOBRECALENTAMIENTO!", (cx, y), RED if blink else WHITE, box.w - 60, anchor="midtop")
    else:
        put(L, F["small"], "temperatura OK", (cx, y + 10), GREEN, anchor="midtop")

# ---------------------------------------------------------------------------------------------------------------
# enganches: dibujo (recogida y celdas) y toques de las celdas nuevas
# ---------------------------------------------------------------------------------------------------------------
_render_big_base_v20b4 = render_big_base

def render_big_base():
    LZ["cel"] = {}
    S = BIG.get("surf")
    if lienzo_on() and S is not None and not hdmi_panel() and not ui.get("bye"):
        with lock:
            d, rx = state["data"], state["rx"]
        now = time.time()
        if d is not None and now - rx < 5 and now - ui["start"] >= 3 \
                and not (ui.get("alert") and now < ui["alert"]["until"]) \
                and not (xa.get("a") and now < xa["a"]["until"] and not kill_in_cell(xa["a"])):
            flags = d.get("Flags", 0)
            if flags & (1 << 11) or now < scoop["full_until"]:
                S.fill(BLACK)
                if lienzo_dibuja(S, lz_recogida, d, flags, now):
                    BIG["rects"] = []; BIG["fast"] = True; LZ["lleno"] = "aviso"
                    return
    return _render_big_base_v20b4()

_big_tap_v20b4 = big_tap

def big_tap(xn, yn):
    if lienzo_on() and not hdmi_panel() and LZ.get("lleno") == "tablero" and LZ["cel"]:
        bw, bh = BIG.get("w") or LW, BIG.get("h") or LH
        X, Y = xn * bw, yn * bh
        for v, (sub, k, hits) in list(LZ["cel"].items()):
            if not sub.collidepoint(X, Y):
                continue
            HDMIF["t"] = time.time()
            lx, ly = (X - sub.x) / k, (Y - sub.y) / k
            for r, acc in reversed(hits):
                if r.collidepoint(lx, ly):
                    if acc[0] == "nave":
                        ui["view"] = 170; lienzo_menu()
                    elif acc[0] == "naveaqui":
                        ship_here()
                    TAP_EV.set()
                    return
            return                                           # en la celda, pero fuera de sus botones: nada
    return _big_tap_v20b4(xn, yn)
