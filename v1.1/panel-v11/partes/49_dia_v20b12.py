# Panel Elite v2.0 · parte 49: v2.0b12 — ESCUADRÓN y DÍA a 1280x800 (con PANTALLA v2)
#   165 ESCUADRÓN (y sus páginas de comandantes de Inara), 215 AMIGOS, 123 RANGOS, 132 OBJETIVOS COMUNITARIOS,
#   11 RESUMEN DEL DÍA (con AMIGOS y DÓNDE COMPRAR HOY) y 61 REGISTRO DE COMBATE (con MASACRE), en el MENÚ
#   (LZ_PANEL) y, DÍA y REGISTRO DE COMBATE, como cuadros del tablero (LZ_CELDA). Mismos datos y toques que antes;
#   los del DÍA (AMIGOS, DÓNDE COMPRAR, BORRAR, ESCUADRÓN >) son acciones propias.

def _lz_diatab(acc, X, Y):
    ui["sesstab"] = acc[1]

def _lz_sqbtn(acc, X, Y):
    tap_flash(("sqbtn",)); ui["view"] = 165; ui["sqpage"] = 0

def _lz_ledb(acc, X, Y):
    if time.time() < LEDB["sure"]:
        LEDB["sure"] = 0; led_clear()
    else:
        LEDB["sure"] = time.time() + 3

def _lz_irsys(acc, X, Y):
    tap_flash(("irsys", acc[1])); ir_send(acc[1])

LZ_ACC.update(diatab=_lz_diatab, sqbtn=_lz_sqbtn, ledb=_lz_ledb, irsys=_lz_irsys)

def lz_grande(area):
    return area.h > 400

# ---------------------------------------------------------------------------------------------------------------
# 165 ESCUADRÓN
# ---------------------------------------------------------------------------------------------------------------
def lz_squad_page(L, area, d, pg):
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    ina = d.get("inara") or {}
    on = set((d.get("friends") or {}).get("on") or [])
    oth = sorted(ina.get("others") or [], key=lambda o: (o.get("name") not in on, (o.get("name") or "").lower()))
    y = area.y + 4
    xc = x0 + 380
    put(L, F["small"], "COMANDANTE", (x0, y), DIM)
    put(L, F["small"], "NAVE  ·  COMBATE  ·  ESCUADRÓN", (xc, y), DIM); y += hs + 10
    pie = area.bottom - hs - 8
    pw, ph = 150, 84
    rh = ph + 12
    per = max(1, (pie - y) // rh)
    pages = 1 + (len(oth) + per - 1) // per
    pg = (pg - 1) % max(1, pages - 1) + 1
    for o in oth[(pg - 1) * per:pg * per]:
        live = o.get("name") in on
        pygame.draw.circle(L, GREEN if live else DIM, (x0 + 10, y + hb // 2 + 4), 10, 0 if live else 2)
        put(L, F["btn"], o.get("name", "?"), (x0 + 32, y + 4), GREEN if live else ORANGE, xc - x0 - 50)
        bits = [o.get("ship"), inara_rank(o), o.get("squad")]
        r_ = pygame.Rect(x1 - pw, y, pw, ph)
        ph_ = cfg.get("cmdrpics", True) and (o.get("avatar") or o.get("ship")) and \
            (avatar_photo(L, o.get("avatar"), r_) or ship_photo(L, {"ship": o.get("ship")}, {}, r_))
        put(L, F["small"], "  ·  ".join(b for b in bits if b) or "sin datos públicos", (xc, y + 4 + (hb - hs) // 2), DIM,
            (x1 - pw - 20 if ph_ else x1) - xc)
        pygame.draw.line(L, (60, 40, 12), (x0, y + rh - 6), (x1, y + rh - 6), 1)
        y += rh
    put(L, F["small"], f"pág {pg + 1}/{pages}  ·  verde = conectado  ·  toca para pasar", (x1, pie + 4), DIM, x1 - x0, anchor="topright")

def lv_squad(L, area, d, flags, now):
    d = d or {}
    lz_hit(area, "old", W // 2, TOP + 60)                  # tocar: página siguiente (tap_squad)
    pg = ui.get("sqpage", 0) % squad_pages(d)
    if pg:
        return lz_squad_page(L, area, d, pg)
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    sq = d.get("squad") or {}
    fr = d.get("friends") or {}
    ina = d.get("inara") or {}
    me = ina.get("me") or {}
    y = area.y + 6
    name = sq.get("name") or me.get("squad")
    if name:
        lg = hg + hb + 10
        lx = x0 + lg + 20 if es_mi_fac(name) and blit_logo(L, pygame.Rect(x0, y, lg, lg)) else x0
        put(L, F["big"], name.upper(), (lx, y), ORANGE, x1 - lx); y += hg + 8
        rk = me.get("sqrank") or (f"rango {sq['rank']}" if sq.get("rank") is not None else "")
        if rk:
            n_ = f"  ·  {me['sqn']} miembros" if me.get("sqn") else ""
            put(L, F["btn"], f"tu rango: {rk}{n_}", (lx, y), BLUE, x1 - lx)
        y = max(y + hb, area.y + 6 + lg) + 14
    else:
        put(L, F["btn"], "Sin escuadrón (o aún no hay datos)", (x0, y), DIM, x1 - x0); y += hb + 14
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 14
    wing = fr.get("wing") or []
    if wing:
        put(L, F["small"], "ALA", (x0, y + (hb - hs) // 2), DIM)
        put(L, F["btn"], "  ·  ".join(str(w) for w in wing), (x0 + 90, y), GREEN, x1 - x0 - 90); y += hb + 16
    on = fr.get("on") or []
    put(L, F["small"], f"AMIGOS CONECTADOS ({len(on)})", (x0, y), DIM); y += hs + 6
    put(L, F["btn"], "  ·  ".join(on[:8]) if on else "ninguno ahora mismo", (x0, y), GREEN if on else DIM, x1 - x0); y += hb + 18
    oth = ina.get("others") or []
    if oth:
        n_on = sum(1 for o in oth if o.get("name") in on)
        put(L, F["small"], "INARA", (x0, y), DIM); y += hs + 6
        put(L, F["btn"], f"{len(oth)} comandantes  ·  {n_on} conectados  ·  toca para verlos", (x0, y), ORANGE, x1 - x0)
    if ina.get("ok"):
        mins = int((time.time() - (ina.get("t") or time.time())) // 60)
        st = f"Inara: hace {mins} min" if mins else "Inara: al día"
    else:
        st = "Inara: sin datos" + (f" ({ina['err']})" if ina.get("err") else "")
    put(L, F["small"], st, (x1, area.bottom - hs - 4), DIM, x1 - x0, anchor="topright")

# ---------------------------------------------------------------------------------------------------------------
# 215 AMIGOS (y la pestaña AMIGOS del DÍA)
# ---------------------------------------------------------------------------------------------------------------
def lz_amigos(L, area, d, now, volver=False):
    Fr = (d or {}).get("friends") or {}
    on, off, wg = Fr.get("on") or [], Fr.get("off") or [], Fr.get("wing") or []
    hs, hb, hg = lz_alturas()
    grande = lz_grande(area)
    x0, x1 = area.x + 14, area.right - 14
    fb = F["btn"] if grande else F["small"]
    fs = F["small"] if grande else F["tiny"]
    y = area.y + 4
    put(L, fs, f"AMIGOS CONECTADOS ({len(on)})", (x0, y), DIM)
    if volver:
        put(L, fs, "toca para volver al DÍA", (x1, y), DIM, anchor="topright")
    y += fs.get_height() + 8
    # ESCUADRÓN > abajo a la derecha
    bh = fb.get_height() + (18 if grande else 10)
    rb = pygame.Rect(x1 - (300 if grande else 170), area.bottom - bh - 6, 300 if grande else 170, bh)
    lz_boton_v(L, rb, "ESCUADRÓN  >", None, fb, lit=flash.get(("sqbtn",), 0) > now)
    lz_hit(rb, "sqbtn")
    if not on:
        put(L, fb, "ninguno", (x0, y), DIM); y += fb.get_height() + 10
    rh = fb.get_height() + (12 if grande else 4)
    cw = (x1 - x0) // 3 if grande else (x1 - x0) // 2
    nc = 3 if grande else 2
    maxn = nc * (4 if grande else 3)
    for k, n in enumerate(on[:maxn]):
        cx, cy = x0 + (k % nc) * cw, y + (k // nc) * rh
        pygame.draw.circle(L, GREEN, (cx + 9, cy + fb.get_height() // 2), 8 if grande else 5)
        put(L, fb, n, (cx + 26, cy), GREEN, cw - 34)
    y += ((min(len(on), maxn) + nc - 1) // nc) * rh + 10
    if wg:
        pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8
        put(L, fs, "TU ALA", (x0, y), DIM); y += fs.get_height() + 6
        put(L, fb, "  ·  ".join(wg), (x0, y), BLUE, x1 - x0); y += fb.get_height() + 12
    if off and y < rb.y - fs.get_height() * 2:
        pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8
        put(L, fs, "DESCONECTADOS HACE POCO", (x0, y), DIM); y += fs.get_height() + 6
        for n, mins in off:
            if y + fs.get_height() > rb.y - 6:
                break
            put(L, fs, n, (x0, y), WHITE, (x1 - x0) // 2)
            put(L, fs, f"hace {mins} min" if mins < 60 else f"hace {mins // 60} h", (x0 + (x1 - x0) // 2 + 20, y), DIM)
            y += fs.get_height() + 6

def lv_amigos(L, area, d, flags, now):
    lz_amigos(L, area, d, now)

# ---------------------------------------------------------------------------------------------------------------
# 123 RANGOS
# ---------------------------------------------------------------------------------------------------------------
def lv_ranks(L, area, d, flags, now):
    r = (d or {}).get("ranks") or {}
    rank, prog = r.get("rank") or {}, r.get("progress") or {}
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    put(L, F["small"], "CMDR " + ((r.get("cmdr") or cfg["cmdr"]).upper()), (x1, area.y + 4), DIM, anchor="topright")
    if not rank:
        return lz_vacio(L, area, "Sin datos de rangos (carga la partida)")
    car_ = (d or {}).get("career") or {}
    pie = any(car_.get(k) is not None for k in ("foot", "bonds", "bounties"))
    y = area.y + hs + 14
    bot = area.bottom - ((hb + 24) if pie else 4)
    rh = (bot - y) // len(RANK_ROWS)
    cn, cb = x0 + 280, x0 + 760
    for label, key in RANK_ROWS:
        n, p_ = rank.get(key), prog.get(key, 0)
        yy = y + (rh - hg) // 2
        put(L, F["small"], label, (x0, yy + (hg - hs) // 2), DIM)
        put(L, F["big"], rank_name(key, n).upper(), (cn, yy), ORANGE, cb - cn - 20)
        lz_barra_h(L, pygame.Rect(cb, yy + hg // 2 - 12, x1 - cb - 110, 24), (p_ or 0) / 100, BLUE)
        put(L, F["btn"], f"{p_ or 0}%", (x1, yy + (hg - hb) // 2), WHITE, anchor="topright")
        pygame.draw.line(L, (50, 32, 10), (x0, y + rh - 1), (x1, y + rh - 1), 1)
        y += rh
    if pie:
        pygame.draw.line(L, DIM, (x0, bot + 6), (x1, bot + 6), 2)
        x_ = x0
        for k, lab, col in (("foot", "bajas a pie", GREEN), ("bonds", "bonos nave", BLUE), ("bounties", "recompensas", ORANGE)):
            if car_.get(k) is None:
                continue
            x_ += put(L, F["btn"], fnum(car_[k], 0), (x_, bot + 16), col)
            x_ += put(L, F["small"], " " + lab, (x_, bot + 16 + (hb - hs)), DIM) + 40

# ---------------------------------------------------------------------------------------------------------------
# 132 OBJETIVOS COMUNITARIOS
# ---------------------------------------------------------------------------------------------------------------
def lz_cg_band(L, r, g):
    """Ficha cerrada: velo oscuro y banda roja CERRADO (cg_band a la escala del lienzo)."""
    rr = L._r(r).clip(L.real.get_rect())
    veil = pygame.Surface(rr.size); veil.set_alpha(150); veil.fill(BLACK)
    L.real.blit(veil, rr.topleft)
    k = L.sx
    f = pygame.font.Font(None, max(10, int(56 * k)))
    band = pygame.Surface((int(rr.w * 0.6), int(56 * k)), pygame.SRCALPHA)
    band.fill(RED)
    tx = f.render("CERRADO", True, WHITE)
    band.blit(tx, tx.get_rect(center=band.get_rect().center))
    band = pygame.transform.rotate(band, 8)
    L.real.blit(band, band.get_rect(center=rr.center).topleft)
    if g.get("me"):
        put(L, F["small"], "cobra la recompensa", (r.centerx, r.bottom - 22), GREEN, anchor="center")

def lv_cgoals(L, area, d, flags, now):
    cgoals["d"] = d
    lz_hit(area, "old", W // 2, H // 2)                    # tocar: página siguiente
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    Lg = cg_all(d)
    per = 3
    pages = max(1, (len(Lg) + per - 1) // per)
    pg = cgoals["page"] % pages
    if cgoals["err"] and not Lg:
        info, col = cgoals["err"], RED
    elif cgoals["t"]:
        na = sum(1 for g in Lg if not g.get("closed"))
        info, col = f"{na} activo{'s' if na != 1 else ''} · actualizado " + time.strftime("%H:%M", time.localtime(cgoals["t"])), DIM
    else:
        info, col = "descargando...", DIM
    y = area.y + 4
    put(L, F["small"], info, (x0, y), col, x1 - x0 - 300)
    if pages > 1:
        put(L, F["small"], f"pág {pg + 1}/{pages}  ·  toca para pasar", (x1, y), ORANGE, anchor="topright")
    if not Lg:
        return lz_vacio(L, area, "No hay objetivos comunitarios activos")
    y += hs + 10
    fh = (area.bottom - y - 2 * 12) // per
    for i, g in enumerate(Lg[pg * per:(pg + 1) * per]):
        r = pygame.Rect(area.x + 8, y + i * (fh + 12), area.w - 16, fh)
        me = g.get("me")
        pygame.draw.rect(L, GREEN if me else DIM, r, 2, border_radius=10)
        xa, xb = r.x + 16, r.right - 16
        yy = r.y + 8
        put(L, F["btn"], g["title"], (xa, yy), ORANGE, xb - xa); yy += hb + 6
        left = "COMPLETADO" if g.get("complete") else cg_left(g.get("expiry", ""))
        where = " · ".join(x for x in (g.get("sys", "").upper(), g.get("market", "")) if x)
        put(L, F["small"], left, (xb, yy), GREEN if g.get("complete") else BLUE, anchor="topright")
        put(L, F["small"], where, (xa, yy), WHITE, xb - xa - tw_(F["small"], left) - 30); yy += hs + 8
        t, top = _tier(g.get("tier")), _tier(g.get("top"))
        if t is not None and top:
            pct, txt = min(1.0, t / top), f"NIVEL {t} de {top}"
        elif g.get("qty") is not None and g.get("target"):
            pct = min(1.0, g["qty"] / g["target"]); txt = f"{fnum(g['qty'], 0)} / {fnum(g['target'], 0)}"
        else:
            pct, txt = None, ""
        bw = xb - xa - 300
        bar = pygame.Rect(xa, yy + 2, bw, hs - 4)
        lz_barra_h(L, bar, pct or 0, GREEN if me else ORANGE)
        put(L, F["small"], txt, (xb, yy), GREEN if me else ORANGE, 290, anchor="topright"); yy += hs + 8
        if me:
            mine = f"TU APORTACIÓN: {fnum(g.get('mine') or 0, 0)}"
            if g.get("band"):
                mine += f"   ·   estás en el {g['band']}% mejor"
            if g.get("toprank"):
                mine += "   ·   TOP"
            if g.get("contrib"):
                put(L, F["small"], f"{fnum(g['contrib'], 0)} pilotos", (xb, yy), DIM, anchor="topright")
            put(L, F["small"], mine, (xa, yy), GREEN, xb - xa - 220)
        elif g.get("text") and yy + hs < r.bottom - 4:
            put(L, F["small"], g["text"].replace("\n", " "), (xa, yy), DIM, xb - xa)
        if g.get("closed"):
            lz_cg_band(L, r, g)

# ---------------------------------------------------------------------------------------------------------------
# 11 RESUMEN DEL DÍA (pestañas propias: DÍA · AMIGOS · DÓNDE COMPRAR HOY)
# ---------------------------------------------------------------------------------------------------------------
def lz_compras(L, area, d, now):
    hs, hb, hg = lz_alturas()
    grande = lz_grande(area)
    x0, x1 = area.x + 14, area.right - 14
    fb = F["btn"] if grande else F["small"]
    fs = F["small"] if grande else F["tiny"]
    lz_hit(area, "diatab", 0)                              # tocar fuera: vuelve al DÍA
    Lc = _compras_day()
    y = area.y + 4
    put(L, fb, "DÓNDE COMPRAR HOY · materiales de colonización", (x0, y), GREEN, x1 - x0); y += fb.get_height() + 12
    if not Lc:
        put(L, fs, "todavía ninguna estación hoy", (x0, y), DIM)
    pie = area.bottom - fs.get_height() - 6
    rh = fb.get_height() + fs.get_height() + (20 if grande else 6)
    for e in sorted(Lc, key=lambda e: -e["t"])[:max(1, (pie - y) // rh)]:
        r = pygame.Rect(x0 - 8, y - 4, x1 - x0 + 16, rh - 6)
        pygame.draw.rect(L, (0, 24, 8), r, border_radius=6)
        put(L, fb, e["st"], (x0, y), ORANGE, x1 - x0 - 120)
        put(L, fs, time.strftime("%H:%M", time.localtime(e["t"])), (x1, y + 2), DIM, anchor="topright")
        put(L, fs, f"{e['sys']} · " + ", ".join(e["items"]), (x0, y + fb.get_height() + 4), GREEN, x1 - x0)
        lz_hit(r, "irsys", e["sys"])
        y += rh
    put(L, fs, "toca una estación para copiar su sistema en el PC · toca fuera para volver", (area.centerx, pie), DIM, x1 - x0,
        anchor="midtop")

def lv_dia(L, area, d, flags, now):
    st = ui.get("sesstab")
    if st == 1:
        lz_hit(area, "diatab", 0)                          # tocar: vuelve al DÍA (ESCUADRÓN > encima)
        return lz_amigos(L, area, d, now, volver=True)
    if st:
        return lz_compras(L, area, d, now)
    d = d or {}
    hs, hb, hg = lz_alturas()
    grande = lz_grande(area)
    x0, x1 = area.x + 14, area.right - 14
    fv = F["big"] if grande else F["btn"]
    fl = F["small"] if grande else F["tiny"]
    lz_hit(area, "diatab", 1)                              # tocar: AMIGOS (como antes)
    s_ = d.get("sess") or {}
    y = area.y + 4
    lineas = dia_lineas(d, now)
    if not s_:
        put(L, F["btn"], "Sin sesión (carga la partida)", (area.centerx, y + 60), DIM, anchor="center")
        y += 120
    else:
        e = s_.get("earn") or {}
        play_ = (s_.get("play") or 0) + (max(0, (s_.get("lastts") or s_["seg"]) - s_["seg"]) if s_.get("seg") else 0)
        left = [("HOY " + game_date(), dur(play_ if s_.get("day") else time.time() - (s_.get("start") or time.time()))),
                ("SALTOS", str(s_.get("jumps", 0))),
                ("AÑOS LUZ", f"{s_.get('ly', 0):,.0f}".replace(",", ".")),
                ("BAJAS  pie · nave", f"{s_.get('kfoot', 0)} · {s_.get('kills', 0) - s_.get('kfoot', 0)}"),
                ("MUERTES", str(s_.get("deaths", 0)))]
        right = [("RECOMPENSAS", e.get("bounty")), ("COMERCIO", e.get("trade")), ("EXPLORACIÓN", e.get("explo")),
                 ("MISIONES", e.get("missions")), ("EXOBIOLOGÍA", e.get("bio"))]
        nl = min(len(lineas), 4 if grande else 2)
        abajo = fv.get_height() + 12 + nl * (fl.get_height() + (10 if grande else 4))
        rh = max(fv.get_height() + 2, (area.bottom - y - abajo - 14) // 5)
        xm = area.centerx
        for (l1, v1), (l2, v2) in zip(left, right):
            yv = y + (rh - fv.get_height()) // 2
            put(L, fl, l1, (x0, yv + (fv.get_height() - fl.get_height()) // 2), BLUE if l1.startswith("HOY") else DIM, xm - x0 - 200)
            put(L, fv, v1, (xm - 24, yv), RED if l1 == "MUERTES" and v1 != "0" else ORANGE, 260, anchor="topright")
            put(L, fl, l2, (xm + 24, yv + (fv.get_height() - fl.get_height()) // 2), DIM)
            put(L, fv, cr(v2), (x1, yv), ORANGE, anchor="topright")
            y += rh
        pygame.draw.line(L, DIM, (xm, area.y + 4), (xm, y - 4), 2)
        pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8
        bal, c0 = d.get("balance"), s_.get("credits0")
        if bal is not None:
            put(L, fl, "SALDO", (x0, y + (fv.get_height() - fl.get_height()) // 2), DIM)
            xs = x0 + tw_(fl, "SALDO") + 20
            bw = put(L, fv, f"{bal:,.0f} cr".replace(",", "."), (xs, y), ORANGE)
            if c0 is not None:
                diff = bal - c0
                dw = put(L, fv, ("+" if diff >= 0 else "") + cr(diff), (x1, y), GREEN if diff >= 0 else RED, anchor="topright")
                ch = cr_hora(s_, d)
                if ch and ch[1] > 0:
                    htx = f"{cr(ch[1])}/h"
                    hx = x1 - dw - 24
                    if hx - tw_(fl, htx) > xs + bw + 20:
                        put(L, fl, htx, (hx, y + (fv.get_height() - fl.get_height()) // 2), GREEN, anchor="topright")
        y += fv.get_height() + 12
    fh = fl.get_height()
    for txt, col, k in lineas:
        if y + fh > area.bottom - 2:
            break
        w = x1 - x0
        if k == "led":
            sure = time.time() < LEDB["sure"]
            bw_ = 170 if grande else 110
            r = pygame.Rect(x1 - bw_, y - 4, bw_, fh + 8)
            pygame.draw.rect(L, ORANGE if sure else BLACK, r, border_radius=6)
            pygame.draw.rect(L, ORANGE, r, 2, border_radius=6)
            put(L, fl, "¿SEGURO?" if sure else "BORRAR", r.center, BLACK if sure else ORANGE, anchor="center")
            lz_hit(r.inflate(4, 8), "ledb")
            w = r.x - x0 - 20
        if k in ("amigos", "pax"):
            linea_mov(L, fl, txt, x0, y, w, col, now, h=fh)
        else:
            put(L, fl, txt, (x0, y), col, w)
        if k == "compras":
            lz_hit(pygame.Rect(x0, y - 4, w, fh + 8), "diatab", 2)
        y += fh + (10 if grande else 4)

# ---------------------------------------------------------------------------------------------------------------
# 61 REGISTRO DE COMBATE (con MASACRE)
# ---------------------------------------------------------------------------------------------------------------
def lv_combatlog(L, area, d, flags, now):
    C = (d or {}).get("combat") or {}
    hs, hb, hg = lz_alturas()
    grande = lz_grande(area)
    x0, x1 = area.x + 14, area.right - 14
    fb = F["btn"] if grande else F["small"]
    fs = F["small"] if grande else F["tiny"]
    fv = F["big"] if grande else F["btn"]
    y = area.y + 4
    sd = None if flags & 8 else C.get("sd")
    put(L, fs, "ESCUDOS", (x0, y + (fv.get_height() - fs.get_height()) // 2), DIM)
    xv = x0 + tw_(fs, "ESCUDOS") + 24
    if sd:
        el = int(now - sd)
        put(L, fv, f"CAÍDOS  {el // 60:02d}:{el % 60:02d}", (xv, y), RED if int(now * 2) % 2 else WHITE)
    else:
        put(L, fv, "ACTIVOS" if flags & 8 else "SIN ESCUDOS", (xv, y), BLUE if flags & 8 else DIM)
    car_ = (d or {}).get("career") or {}
    if car_.get("bonds") is not None:
        put(L, fs, f"bonos {fnum(car_['bonds'], 0)}", (x1, y), BLUE, anchor="topright")
    if car_.get("bounties") is not None:
        put(L, fs, f"recompensas {fnum(car_['bounties'], 0)}", (x1, y + fs.get_height() + 2), ORANGE, anchor="topright")
    y += max(fv.get_height(), 2 * fs.get_height() + 2) + 8
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 6
    # abajo: sin cobrar y MASACRE
    s_ = (d or {}).get("sess") or {}
    M = (d or {}).get("masacre") or []
    bot = area.bottom - 2
    if s_.get("pending"):
        bot -= fs.get_height() + 4
        put(L, fs, f"RECOMPENSAS SIN COBRAR: {cr(s_['pending'])} cr ({s_.get('pending_n', 0)})", (x0, bot), RED, x1 - x0)
        bot -= 6
    if M:
        rows = M[:3 if grande else 2]
        rh_ = fs.get_height() + (8 if grande else 3)
        bh = fs.get_height() + 12 + rh_ * len(rows)
        r = pygame.Rect(area.x + 6, bot - bh, area.w - 12, bh)
        pygame.draw.rect(L, BLACK, r)
        pygame.draw.rect(L, GREEN, r, 2, border_radius=8)
        falta = sum(max(0, m[3] - m[2]) for m in M)
        put(L, fs, "MASACRE" + (f" · faltan {falta} bajas" if falta else " · COMPLETADA, ve a cobrar"), (r.x + 12, r.y + 4), GREEN, r.w - 24)
        yy = r.y + fs.get_height() + 10
        for giv, tgt, k, n, *_ in rows:
            put(L, fs, f"{giv} -> {tgt}", (r.x + 12, yy), WHITE if k < n else GREEN, r.w - 420)
            lz_barra_h(L, pygame.Rect(r.right - 380, yy + 2, 260, fs.get_height() - 4), k / max(1, n), GREEN)
            put(L, fs, f"{k}/{n}", (r.right - 12, yy), GREEN if k >= n else ORANGE, anchor="topright")
            yy += rh_
        bot = r.y - 6
    # derribos y bonos (dos columnas en la pantalla grande)
    kills = C.get("kills") or []
    bonds = C.get("bonds") or []
    xm = area.centerx if (grande and bonds) else x1
    put(L, fs, "ÚLTIMOS DERRIBOS", (x0, y), DIM)
    yk = y + fs.get_height() + 6
    if not kills:
        put(L, fs, "ninguno en esta sesión", (x0, yk), DIM)
    rh = fb.get_height() + (10 if grande else 2)
    for tgt, rew, kind in kills[:max(1, (bot - yk) // rh)]:
        tag, col = {"R": ("RECOMPENSA", ORANGE), "B": ("BONO", BLUE), "P": ("PvP", RED)}.get(kind, ("", DIM))
        rw = f"+{cr(rew)}" if rew else ""
        wt = (xm - x0) - tw_(fb, rw) - tw_(fs, "RECOMPENSA") - 60
        put(L, fb, tgt, (x0, yk), WHITE, wt)
        put(L, fs, tag, (x0 + wt + 16, yk + (fb.get_height() - fs.get_height()) // 2), col)
        if rew:
            put(L, fb, rw, (xm - (30 if xm != x1 else 0), yk), GREEN, anchor="topright")
        yk += rh
    if bonds:
        if xm == x1:
            yb = yk + 6
            pygame.draw.line(L, DIM, (x0, yb), (x1, yb), 1); yb += 6
            xb0 = x0
        else:
            pygame.draw.line(L, DIM, (xm, y), (xm, bot - 4), 1)
            yb, xb0 = y, xm + 30
        if yb + fs.get_height() < bot:
            put(L, fs, "BONOS DE GUERRA POR FACCIÓN", (xb0, yb), DIM); yb += fs.get_height() + 6
            for fac, v in bonds:
                if yb + fb.get_height() > bot:
                    break
                put(L, fs, fac, (xb0, yb + (fb.get_height() - fs.get_height()) // 2), BLUE, x1 - xb0 - 220)
                put(L, fb, f"{cr(v)} cr", (x1, yb), BLUE, anchor="topright"); yb += rh

_LZ_B12 = {165: lv_squad, 215: lv_amigos, 123: lv_ranks, 132: lv_cgoals, 11: lv_dia, 61: lv_combatlog}
LZ_PANEL.update(_LZ_B12)
for _v in (11, 61):
    LZ_CELDA[_v] = (lambda fn: (lambda L, d, flags, now: fn(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now)))(_LZ_B12[_v])
