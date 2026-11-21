# Panel Elite v2.0 · parte 50: v2.0b13 — GALNET, NOTAS y CALCULADORA a 1280x800 (con PANTALLA v2)
#   130 GALNET, 131 NOTICIA, 128 NOTAS DE VIAJE, 129 NOTA y 211 CALCULADORA en el MENÚ (LZ_PANEL) y el cuadro GALNET (133)
#   del tablero ATRACADO (LZ_CELDA). Mismos datos y toques: GUARDAR AQUÍ, BORRAR y las teclas de la calculadora tocan su
#   botón de 480x320; filas, páginas y la cinta son acciones propias (cada pantalla nueva tiene su propio reparto).

def _lz_galpg(acc, X, Y):
    galnet["page"] += 1

def _lz_galsel(acc, X, Y):
    L_ = galnet["list"]
    i = acc[1]
    if i < len(L_):
        galnet["sel"], galnet["apage"] = i, 0
        galnet["new"].discard(L_[i]["id"])
        ui["view"] = 131

def _lz_galart(acc, X, Y):
    galnet["apage"] += 1

def _lz_trippg(acc, X, Y):
    trip["page"] += 1

def _lz_tripsel(acc, X, Y):
    if acc[1] < len(trip["list"]):
        trip["sel"] = acc[1]; ui["view"] = 129

def _lz_calctape(acc, X, Y):
    T = list(reversed(CALC["tape"]))
    k = acc[1]
    if 0 <= k < len(T) and T[k][1] != "Error":
        tap_flash((211, "tape", k))
        CALC["cur"] = T[k][1].replace(".", ""); CALC["new"] = False

LZ_ACC.update(galpg=_lz_galpg, galsel=_lz_galsel, galart=_lz_galart, trippg=_lz_trippg, tripsel=_lz_tripsel,
              calctape=_lz_calctape)
LZ["galart"] = None                                       # (id, ancho, letras) -> líneas de la noticia ya partidas
LZ["galcel"] = None

def lz_pag_btn(L, r, pg, pages, accion):
    lz_boton_v(L, r, f"PÁG {pg + 1}/{pages}  >", None, F["small"])
    lz_hit(r, *accion)

# ---------------------------------------------------------------------------------------------------------------
# 130 GALNET (lista) y 131 NOTICIA
# ---------------------------------------------------------------------------------------------------------------
def lv_galnet(L, area, d, flags, now):
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    Lg = galnet["list"]
    y = area.y + 4
    info = ("actualizado " + time.strftime("%H:%M", time.localtime(galnet["t"]))) if galnet["t"] else (galnet["err"] or "descargando...")
    bh = hs + 22
    rh = hb + hs + 26
    per = max(1, (area.bottom - y - bh - 12) // rh)
    pages = max(1, (len(Lg) + per - 1) // per)
    pg = galnet["page"] % pages
    put(L, F["small"], info, (x0, y + (bh - hs) // 2), RED if galnet["err"] else DIM, x1 - x0 - 300)
    if pages > 1:
        lz_pag_btn(L, pygame.Rect(x1 - 260, y, 260, bh), pg, pages, ("galpg",))
    if not Lg:
        return lz_vacio(L, area, "Sin noticias todavía")
    y += bh + 12
    for i, n in enumerate(Lg[pg * per:(pg + 1) * per]):
        r = pygame.Rect(x0 - 4, y, x1 - x0 + 8, rh - 10)
        nueva = n["id"] in galnet["new"]
        pygame.draw.rect(L, GREEN if nueva else DIM, r, 2, border_radius=8)
        put(L, F["btn"], n["title"], (r.x + 14, r.y + 6), GREEN if nueva else ORANGE, r.w - 28)
        put(L, F["small"], n["date"] + ("   · NUEVA" if nueva else ""), (r.x + 14, r.y + 10 + hb), GREEN if nueva else BLUE)
        lz_hit(r, "galsel", pg * per + i)
        y += rh

def lv_galnet_art(L, area, d, flags, now):
    Lg, i = galnet["list"], galnet["sel"]
    if i is None or i >= len(Lg):
        ui["view"] = 130
        return lz_vacio(L, area, "Sin noticia")
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    n = Lg[i]
    lz_hit(area, "galart")                                   # tocar: página siguiente
    key = (n["id"], x1 - x0, round(F["small"].f, 3))
    if LZ["galart"] is None or LZ["galart"][0] != key:
        LZ["galart"] = (key, wrap_lines(F["big"], n["title"], x1 - x0)[:2], wrap_lines(F["small"], n["body"], x1 - x0))
    _, tl, body = LZ["galart"]
    y = area.y + 4
    for t in tl:
        put(L, F["big"], t, (x0, y), ORANGE); y += hg + 4
    rh = hs + 10
    per = max(1, (area.bottom - y - hs - 16) // rh)
    pages = max(1, (len(body) + per - 1) // per)
    pg = galnet["apage"] % pages
    put(L, F["small"], "GALNET · " + n["date"], (x0, y), BLUE)
    put(L, F["small"], f"pág {pg + 1}/{pages}  ·  toca para pasar", (x1, y), DIM, anchor="topright")
    y += hs + 14
    for line in body[pg * per:(pg + 1) * per]:
        put(L, F["small"], line, (x0, y), WHITE); y += rh

# ---------------------------------------------------------------------------------------------------------------
# 133 GALNET en el cuadro del tablero (las noticias suben despacio, como en la espera)
# ---------------------------------------------------------------------------------------------------------------
def lc_galnet(L, d, flags, now):
    area = pygame.Rect(10, 4, CW0 - 20, CH0 - 8)
    Lg = galnet["list"][:6]
    if not Lg:
        return put(L, F["small"], galnet["err"] or "descargando noticias...", area.center, DIM, area.w, anchor="center")
    key = (tuple(n["id"] for n in Lg), round(F["btn"].f, 3))
    if LZ["galcel"] is None or LZ["galcel"][0] != key:
        out = []
        hb_, hs_ = F["btn"].get_height(), F["small"].get_height()
        for n in Lg:
            for t in wrap_lines(F["btn"], n["title"], area.w):
                out.append((F["btn"], t, ORANGE, hb_ + 4))
            out.append((F["small"], n["date"], BLUE, hs_ + 6))
            body = wrap_lines(F["small"], n["body"], area.w)
            for t in body[:7]:
                out.append((F["small"], t, WHITE, hs_ + 4))
            out.append((None, "", None, hb_))
        LZ["galcel"] = (key, out, sum(h for *_, h in out))
    _, lines, total = LZ["galcel"]
    off = (now * IDLE_SPEED * 1.2) % total
    old = L.get_clip()
    L.set_clip(area)
    y = area.bottom - off
    while y < area.bottom:
        for f, t, col, h in lines:
            if area.y - h < y < area.bottom and f:
                put(L, f, t, (area.x, int(y)), col, area.w)
            y += h
    L.set_clip(old)

# ---------------------------------------------------------------------------------------------------------------
# 128 NOTAS DE VIAJE y 129 NOTA
# ---------------------------------------------------------------------------------------------------------------
def lv_trip(L, area, d, flags, now):
    trip["d"] = d
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    Lt = trip["list"]
    y = area.y + 4
    bh = hb + 22
    lz_boton_v(L, pygame.Rect(x0, y, 380, bh), "GUARDAR AQUÍ", None, F["btn"], filled=True, dim=not (d or {}).get("system"),
               lit=flash.get((128, "save"), 0) > now, viejo=TRIP_SAVE)
    rh = hb + hs + 26
    per = max(1, (area.bottom - y - bh - 14) // rh)
    pages = max(1, (len(Lt) + per - 1) // per)
    pg = trip["page"] % pages
    if pages > 1:
        lz_pag_btn(L, pygame.Rect(x1 - 260, y, 260, bh), pg, pages, ("trippg",))
    else:
        put(L, F["small"], f"{len(Lt)} sitios", (x1, y + (bh - hs) // 2), DIM, anchor="topright")
    if not Lt:
        return lz_vacio(L, pygame.Rect(area.x, y + bh, area.w, area.bottom - y - bh), "Aún no has guardado ningún sitio")
    y += bh + 14
    for i, n in enumerate(Lt[pg * per:(pg + 1) * per]):
        r = pygame.Rect(x0 - 4, y, x1 - x0 + 8, rh - 10)
        pygame.draw.rect(L, DIM, r, 2, border_radius=8)
        tag = n.get("tag", "")
        put(L, F["small"], tag, (r.right - 14, r.y + 6 + (hb - hs) // 2), TAG_COL.get(tag, DIM), anchor="topright")
        put(L, F["btn"], trip_label(n), (r.x + 14, r.y + 6), ORANGE, r.w - 60 - tw_(F["small"], tag))
        sub = f"{n.get('sys') or '?'}  ·  {time.strftime('%d/%m %H:%M', time.localtime(n.get('t', 0)))}"
        dist = trip_dist(n, d)
        put(L, F["small"], sub, (r.x + 14, r.y + 10 + hb), DIM, r.w - 60 - tw_(F["small"], dist))
        put(L, F["small"], dist, (r.right - 14, r.y + 10 + hb), BLUE, anchor="topright")
        lz_hit(r, "tripsel", pg * per + i)
        y += rh

def lv_trip_detail(L, area, d, flags, now):
    trip["d"] = d
    Lt, i = trip["list"], trip["sel"]
    if i is None or i >= len(Lt):
        ui["view"] = 128
        return lz_vacio(L, area, "Sin nota")
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    n = Lt[i]
    y = area.y + 4
    put(L, F["big"], (n.get("sys") or "?").upper(), (x0, y), ORANGE, x1 - x0); y += hg + 8
    if n.get("st") or (n.get("body") and n.get("body") != n.get("sys")):
        put(L, F["btn"], trip_label(n), (x0, y), WHITE, x1 - x0); y += hb + 8
    tag = n.get("tag", "")
    put(L, F["small"], tag, (x0, y), TAG_COL.get(tag, DIM))
    put(L, F["small"], time.strftime("%d/%m/%Y %H:%M", time.localtime(n.get("t", 0))), (x1, y), DIM, anchor="topright"); y += hs + 10
    if n.get("lat") is not None:
        put(L, F["small"], f"lat {n['lat']:.4f}   lon {n['lon']:.4f}", (x0, y), DIM); y += hs + 10
    dist = trip_dist(n, d)
    if dist:
        put(L, F["small"], "DISTANCIA", (x0, y + (hg - hs) // 2), DIM)
        put(L, F["big"], dist, (x0 + tw_(F["small"], "DISTANCIA") + 24, y), BLUE); y += hg + 10
    # BORRAR abajo a la derecha
    c, until = ui["confirm"]
    sure = c == "trip_del" and time.time() < until
    rb = pygame.Rect(x1 - 300, area.bottom - hb - 30, 300, hb + 24)
    lz_boton_v(L, rb, "¿SEGURO?" if sure else "BORRAR", None, F["btn"], filled=sure, viejo=TRIP_DEL)
    # brújula al sitio si estás en ese cuerpo
    b = (d or {}).get("bio") or {}
    here = (d or {}).get("body") and (d or {}).get("body") == n.get("body")
    if here and n.get("lat") is not None and b.get("lat") is not None and b.get("R"):
        p1, p2 = math.radians(b["lat"]), math.radians(n["lat"])
        dl = math.radians(n["lon"] - b["lon"])
        brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                      math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
        m = hav((b["lat"], b["lon"]), (n["lat"], n["lon"]), b["R"])
        r = min(110, (area.bottom - y - 30) // 2)
        if r > 30:
            cx, cy = x0 + r + 10, area.bottom - r - 14
            pygame.draw.circle(L, DIM, (cx, cy), r, 3)
            hdg = b.get("hdg")
            if hdg is not None:
                a = math.radians(brg - hdg)
                pt = lambda k, da: (cx + r * k * math.sin(a + da), cy - r * k * math.cos(a + da))
                pygame.draw.polygon(L, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
            tx = cx + r + 40
            txt = f"{m / 1000:.1f} km".replace(".", ",") if m >= 1000 else f"{m:.0f} m"
            put(L, F["small"], "DESTINO", (tx, cy - hg // 2 - hs - 6), DIM)
            put(L, F["big"], txt, (tx, cy - hg // 2), GREEN)
            put(L, F["btn"], f"rumbo {brg:.0f}°", (tx, cy + hg // 2 + 6), ORANGE)

# ---------------------------------------------------------------------------------------------------------------
# 211 CALCULADORA (con cinta)
# ---------------------------------------------------------------------------------------------------------------
def lv_calc(L, area, d, flags, now):
    hs, hb, hg = lz_alturas()
    ht = F["tiny"].get_height()
    x0, x1 = area.x + 14, area.right - 14
    gap = 14
    teclas_w = int((x1 - x0) * 0.62)
    xt = x0 + teclas_w + 24                                    # cinta a la derecha
    y = area.y + 4
    dh = ht + F["num"].get_height() + 14
    disp = pygame.Rect(x0, y, teclas_w - 2 * (150 + gap), dh)
    pygame.draw.rect(L, (20, 12, 0), disp, border_radius=10)
    pygame.draw.rect(L, DIM, disp, 2, border_radius=10)
    if CALC["expr"]:
        put(L, F["tiny"], CALC["expr"], (disp.right - 14, disp.y + 4), DIM, disp.w - 28, anchor="topright")
    put(L, F["num"], c_cur_txt(), (disp.right - 14, disp.y + ht + 8), ORANGE, disp.w - 28, anchor="topright")
    rc = pygame.Rect(disp.right + gap, y, 150, dh)
    rd = pygame.Rect(rc.right + gap, y, 150, dh)
    lz_boton_v(L, rc, "C", None, F["big"], lit=flash.get((211, "c"), 0) > now, viejo=C_CLR)
    lz_boton_v(L, rd, "BORRA", None, F["btn"], lit=flash.get((211, "b"), 0) > now, viejo=C_DEL)
    yk = y + dh + gap
    kh = (area.bottom - yk - 3 * gap) // 4
    kw = (teclas_w - 3 * gap) // 4
    for i, row in enumerate(CK):
        for j, k in enumerate(row):
            r = pygame.Rect(x0 + j * (kw + gap), yk + i * (kh + gap), kw, kh)
            lz_boton_v(L, r, k, None, F["num"] if k not in "÷×−+=," else F["num"], filled=k == "=",
                       lit=flash.get((211, k), 0) > now, viejo=c_key(i, j))
    # cinta
    tape = pygame.Rect(xt, y, x1 - xt, area.bottom - y)
    pygame.draw.rect(L, DIM, tape, 2, border_radius=10)
    put(L, F["small"], "CINTA · toca para recuperar", (tape.x + 14, tape.y + 8), DIM, tape.w - 28)
    yy = tape.y + hs + 18
    rh = ht + hb + 16
    T = list(reversed(CALC["tape"]))
    for k, (expr, res) in enumerate(T[:max(1, (tape.bottom - yy) // rh)]):
        r = pygame.Rect(tape.x + 6, yy - 4, tape.w - 12, rh - 4)
        if flash.get((211, "tape", k), 0) > now:
            pygame.draw.rect(L, (60, 35, 0), r, border_radius=6)
        put(L, F["tiny"], expr, (tape.x + 14, yy), DIM, tape.w - 28)
        put(L, F["btn"], "= " + res, (tape.right - 14, yy + ht + 4), ORANGE, tape.w - 28, anchor="topright")
        lz_hit(r, "calctape", k)
        pygame.draw.line(L, (50, 32, 10), (tape.x + 14, yy + rh - 6), (tape.right - 14, yy + rh - 6), 1)
        yy += rh
    if not T:
        put(L, F["small"], "vacía", (tape.centerx, tape.centery), DIM, anchor="center")

_LZ_B13 = {130: lv_galnet, 131: lv_galnet_art, 128: lv_trip, 129: lv_trip_detail, 211: lv_calc}
LZ_PANEL.update(_LZ_B13)
LZ_CELDA[133] = lc_galnet
