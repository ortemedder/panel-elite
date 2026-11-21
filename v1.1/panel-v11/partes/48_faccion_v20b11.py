# Panel Elite v2.0 · parte 48: v2.0b11 — FACCIÓN a 1280x800 (con PANTALLA v2)
#   220 FACCIÓN (submenú), 192/193 MI FACCIÓN (SISTEMAS), 213 BGS y la ficha del sistema 194 FACCIONES, 195 ACTIVIDAD,
#   196 ZONA y 214 INFLUENCIA, en el MENÚ (LZ_PANEL). Mismos datos que antes.
#   Toques: botones de siempre (submenú, < VOLVER, IR >) al centro de su botón de 480x320; filas, páginas,
#   filtros y cabeceras del BGS con acciones propias (no dependen de la pantalla vieja). El BGS ya no se arrastra:
#   flechas ▲ ▼.

LZ["bgs"] = {"off": 0, "max": 0, "nvis": 1}

def _lz_facsys(acc, X, Y):
    """acc = ("facsys", sistema, volver_a): abre la ficha del sistema."""
    tap_flash(("facsys", acc[1]))
    ui["facsys"] = acc[1]
    if acc[2] is not None:
        ui["facback"] = acc[2]
    ui["view"] = 194

def _lz_facpg(acc, X, Y):
    ui["facpg"] = ui.get("facpg", 0) + acc[1]

def _lz_bgssolo(acc, X, Y):
    BGS["solo"] = None if BGS["solo"] == acc[1] else acc[1]
    BGS["off"] = 0; LZ["bgs"]["off"] = 0

def _lz_bgsord(acc, X, Y):
    k = acc[1]
    if BGS["orden"] == k:
        BGS["asc"] = not BGS["asc"]
    else:
        BGS["orden"], BGS["asc"] = k, k == "sys"
    LZ["bgs"]["off"] = 0

def _lz_bgsoff(acc, X, Y):
    B = LZ["bgs"]
    B["off"] = max(0, min(B["max"], B["off"] + acc[1] * max(1, B["nvis"] - 1)))

LZ_ACC.update(facsys=_lz_facsys, facpg=_lz_facpg, bgssolo=_lz_bgssolo, bgsord=_lz_bgsord, bgsoff=_lz_bgsoff)

def lz_tri(L, x, y, s, arriba, col):
    pts = [(x, y + s), (x + s, y + s), (x + s / 2, y)] if arriba else [(x, y), (x + s, y), (x + s / 2, y + s)]
    pygame.draw.polygon(L, col, pts)

def lz_bar_inf(L, r, inf, seg, col):
    pygame.draw.rect(L, DIM, r, 2, border_radius=3)
    pygame.draw.rect(L, col, (r.x + 3, r.y + 3, int((r.w - 6) * min(100, inf or 0) / 100), r.h - 6))
    if seg:
        tx = r.x + int(r.w * min(100, seg) / 100)
        pygame.draw.line(L, RED, (tx, r.y - 4), (tx, r.bottom + 3), 3)

def lz_parts(L, font, parts, x, y, maxw):
    """Estados en color separados por comas (put_parts a la escala del lienzo)."""
    put_parts(L, font, parts, (x, y), maxw)

def lz_volver(L, area):
    """< VOLVER abajo a la izquierda (toca el BACK_R viejo). Devuelve la y de arriba del pie."""
    hb = F["btn"].get_height()
    r = pygame.Rect(area.x + 10, area.bottom - hb - 22, 250, hb + 18)
    lz_boton_v(L, r, "< VOLVER", None, F["btn"], viejo=BACK_R)
    return r

# ---------------------------------------------------------------------------------------------------------------
# 220 FACCIÓN (submenú)
# ---------------------------------------------------------------------------------------------------------------
def lv_sub9(L, area, d, flags, now):
    alarma = False
    if cdsn_on():
        try:
            alarma = any(o["al"][6] for o in cw_datos(now))
        except Exception:
            alarma = False
    for i, (name, v) in enumerate(SUB9):
        r = lz_grid(area, i, 4, 2)
        cdsn = i == 2 and cdsn_on()
        lz_boton_v(L, r, str(i + 1), "CDSN" if cdsn else name, F["num"], filled=cdsn and alarma and cw_parp(now),
                   lit=flash.get((9, i), 0) > now, viejo=grid(i, 4, 2))
        if cdsn and alarma:
            pygame.draw.rect(L, RED, r, 5, border_radius=max(6, r.h // 10))

# ---------------------------------------------------------------------------------------------------------------
# 192 / 193 MI FACCIÓN: lista de sistemas
# ---------------------------------------------------------------------------------------------------------------
def lv_fac(L, area, d, flags, now):
    D, S, gap = fac_rows()
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    v_ = ui.get("view")
    if not S:
        return lz_vacio(L, area, "sin datos de la facción", FACD["err"] or "descargando…")
    y = area.y + 4
    cnt = f"{sum(1 for v in S if v.get('ctrl'))} contr. · {len(S)} sist."     # (el BGS va en su pestaña, v1.1.8)
    xr = x1
    put(L, F["small"], cnt, (xr, y + (hb + 14 - hs) // 2), DIM, anchor="topright")
    xr -= tw_(F["small"], cnt) + 24
    w_ = put(L, F["big"], (D.get("faccion") or "").upper(), (x0, y + (hb + 14 - hg) // 2), ORANGE, int((xr - x0) * 0.6))
    tmax = max([v.get("t") or 0 for v in S] or [0])
    a_txt, a_col = fac_age(tmax)
    put(L, F["small"], f"act. {time.strftime('%H:%M', time.localtime(tmax))} ({a_txt})" if tmax else "sin fecha",
        (x0 + w_ + 20, y + (hb + 14 - hs) // 2), a_col, xr - x0 - w_ - 20)
    y += hb + 26
    pie = area.bottom - hb - 24
    rh = hb + hs + 22
    per = max(1, (pie - y) // rh)
    pages = (len(S) + per - 1) // per
    pg = ui.get("facpg", 0) % pages
    cb = x0 + 470                                              # barra de influencia
    wb = 250
    for v in S[pg * per:(pg + 1) * per]:
        fr = pygame.Rect(area.x + 4, y - 6, area.w - 8, rh - 4)
        lz_hit(fr, "facsys", v["sys"], v_)
        g = gap(v)
        parts = fac_parts(v)
        warn = any(c == RED for t, c in parts)
        pygame.draw.line(L, (60, 40, 12), (x0, y - 8), (x1, y - 8), 2)
        col = (RED if int(now * 2) % 2 else WHITE) if warn else ORANGE if v.get("ctrl") else WHITE
        if v.get("ctrl"):
            lz_tri(L, x0, y + 10, 16, False, ORANGE)
        put(L, F["btn"], v["sys"].upper(), (x0 + 26, y), col, cb - x0 - 46)
        if parts:
            lz_parts(L, F["small"], parts, x0 + 26, y + hb + 4, cb - x0 - 46)
        else:
            put(L, F["small"], "sin estados", (x0 + 26, y + hb + 4), DIM)
        lz_bar_inf(L, pygame.Rect(cb, y + 6, wb, 22), v["inf"], v.get("segunda_inf"), ORANGE if v.get("ctrl") else (170, 170, 170))
        xi = cb + wb + 20
        put(L, F["btn"], f"{v['inf']:.1f}%".replace(".", ","), (xi, y), ORANGE if v.get("ctrl") else WHITE)
        if v.get("prev") is not None and abs(v["inf"] - v["prev"]) >= 0.1:
            tr = v["inf"] - v["prev"]; c_ = GREEN if tr > 0 else RED
            lz_tri(L, xi + 2, y + hb + 8, 14, tr > 0, c_)
            put(L, F["small"], f"{abs(tr):.1f}".replace(".", ","), (xi + 24, y + hb + 4), c_)
        put(L, F["btn"], (f"+{g:.1f}" if g >= 0 else f"{g:.1f}").replace(".", ","), (x1 - 150, y),
            GREEN if g >= 5 else ORANGE if g >= 0 else DIM, anchor="topright")
        put(L, F["tiny"], "VENTAJA", (x1 - 150, y + hb + 6), DIM, anchor="topright")
        hoy, media, alto = traf(v)
        if hoy is not None:
            put(L, F["small"], f"{hoy} cmdr", (x1, y + 4), RED if alto else ORANGE if media and hoy > 1.5 * media else DIM, anchor="topright")
        else:
            put(L, F["small"], fac_age(v.get("t"))[0].replace("hace ", ""), (x1, y + 4), DIM, anchor="topright")
        y += rh
    put(L, F["small"], (f"pág {pg + 1}/{pages} · " if pages > 1 else "") + "toca un sistema para ver su ficha",
        (x0, pie + 14), DIM, x1 - x0 - 300)
    if pages > 1:
        for k, (t, dlt) in enumerate((("◄", -1), ("►", 1))):
            r = pygame.Rect(x1 - 260 + k * 135, pie + 2, 125, hb + 18)
            pygame.draw.rect(L, ORANGE, r, 3, border_radius=8)
            pts = [(r.centerx + 10, r.centery - 12), (r.centerx + 10, r.centery + 12), (r.centerx - 12, r.centery)] if dlt < 0 else \
                  [(r.centerx - 10, r.centery - 12), (r.centerx - 10, r.centery + 12), (r.centerx + 12, r.centery)]
            pygame.draw.polygon(L, ORANGE, pts)
            lz_hit(r, "facpg", dlt)

# ---------------------------------------------------------------------------------------------------------------
# ficha del sistema: cabecera común (nombre, distancia, IR >, datos, tick, población)
# ---------------------------------------------------------------------------------------------------------------
def lz_fs_cab(L, area, d, v, name, now, pob=True):
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    y = area.y + 2
    lit = flash.get(("ir", 0), 0) > now
    ri = pygame.Rect(x1 - 160, y, 160, hb + 14)
    lz_boton_v(L, ri, "IR  >", None, F["btn"], lit=lit, viejo=IR_R)
    xr = ri.x - 24
    pos, here = v.get("pos"), (d or {}).get("starpos")
    if pos and here and None not in pos:
        dist = math.dist(pos, here)
        t_ = "AQUÍ" if dist < 0.01 else f"a {dist:,.1f} al".replace(",", "X").replace(".", ",").replace("X", ".")
        put(L, F["btn"], t_, (xr, y + (hb + 14 - hb) // 2), BLUE, anchor="topright")
        xr -= tw_(F["btn"], t_) + 24
    put(L, F["big"], name.upper(), (x0, y + (hb + 14 - hg) // 2), ORANGE, xr - x0)
    y += hb + 22
    a_txt, a_col = fac_age(v.get("t"))
    w_ = put(L, F["small"], f"datos {a_txt} · {v.get('src') or '?'}", (x0, y), a_col)
    S_ = v.get("sis") or {}
    xr = x1
    if pob and S_:
        t_ = f"POBLACIÓN {fnum_pob(S_.get('pob'))}"
        put(L, F["small"], t_, (x1, y), DIM, anchor="topright")
        xr = x1 - tw_(F["small"], t_) - 24
    txt, col = sys_tick_txt(v, now)
    if txt and xr - (x0 + w_ + 24) > 80:
        put(L, F["small"], txt, (x0 + w_ + 24, y), col, xr - x0 - w_ - 24)
    return y + hs + 12

def lz_fs_sin(L, area, txt):
    lz_vacio(L, area, txt)
    lz_volver(L, area)

# ---------------------------------------------------------------------------------------------------------------
# 194 FACCIONES (ficha del sistema)
# ---------------------------------------------------------------------------------------------------------------
def lv_ficha(L, area, d, flags, now):
    D, name, v = fs_get()
    if not v:
        return lz_fs_sin(L, area, "sin datos de este sistema")
    hs, hb, hg = lz_alturas()
    ht = F["tiny"].get_height()
    me = D.get("faccion")
    x0, x1 = area.x + 14, area.right - 14
    y = lz_fs_cab(L, area, d, v, name, now)
    xv = x0 + tw_(F["small"], "POWERPLAY") + 24
    put(L, F["small"], "CONTROLA", (x0, y + (hb - hs) // 2), DIM)
    put(L, F["btn"], v.get("ctrl_n") or ("tu facción" if v.get("ctrl") else "?"), (xv, y), ORANGE if v.get("ctrl") else WHITE, x1 - xv)
    y += hb + 8
    S_ = v.get("sis") or {}
    if S_:
        eco = tr_(S_.get("eco")) + (f" / {tr_(S_.get('eco2'))}" if S_.get("eco2") and tr_(S_.get("eco2")) != "—" else "")
        put(L, F["small"], f"SEGURIDAD {tr_(S_.get('seg'))}  ·  ECONOMÍA {eco}  ·  {tr_(S_.get('gov'))}, {tr_(S_.get('alg'))}",
            (x0, y), WHITE, x1 - x0)
        y += hs + 8
    pp = v.get("pp") or {}
    if pp.get("pot"):
        put(L, F["small"], "POWERPLAY", (x0, y), DIM)
        x = xv + put(L, F["small"], f"{pp['pot']} · {tr_(pp.get('est'))}", (xv, y), BLUE, 520)
        if pp.get("prog") is not None:
            pr = max(0.0, min(1.0, float(pp["prog"])))
            lz_barra_h(L, pygame.Rect(x + 20, y + 2, 220, hs - 4), pr, BLUE)
            put(L, F["small"], f"{pr * 100:.0f} %", (x + 256, y), BLUE)
        y += hs + 8
    elif pp.get("pots"):
        put(L, F["small"], "POWERPLAY  en disputa: " + ", ".join(pp["pots"]), (x0, y), BLUE, x1 - x0); y += hs + 8
    elif pp:
        put(L, F["small"], "POWERPLAY  sin potencia", (x0, y), DIM); y += hs + 8
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 8
    # pie: conflictos, TU FACCIÓN, consejos y EXPANSIÓN (encima de < VOLVER)
    rv = lz_volver(L, area)
    parts = fac_parts(v)
    bad = [st for st in (v.get("activos") or []) + (v.get("pendientes") or []) if st in TIPS and st not in ST_GOOD][:2]
    exp_ = "Expansion" in (v.get("activos") or []) + (v.get("pendientes") or [])
    confs = v.get("conflictos") or []
    nl = 1 + len(bad) + (1 if exp_ else 0) + len(confs)
    yb = rv.y - 10 - nl * (hs + 6)
    lim = yb - 8
    # facciones del sistema
    T = sorted(v.get("todas") or [], key=lambda f: -(f.get("inf") or 0))
    if not T:
        put(L, F["small"], "las demás facciones llegarán con el próximo dato de este sistema", (x0, y + 4), DIM, x1 - x0)
    rh = hs + 10
    cb, wb = x0 + 440, 200
    for k, f in enumerate(T):
        if y + rh > lim:
            put(L, F["small"], f"… y {len(T) - k} más", (x0, y), DIM); break
        mine = f.get("n") == me
        col = ORANGE if mine else WHITE
        ctl = f.get("n") == v.get("ctrl_n")
        if ctl:
            lz_tri(L, x0, y + 4, 14, False, col)
        put(L, F["small"], f.get("n") or "?", (x0 + 24, y), col, cb - x0 - 40)
        lz_bar_inf(L, pygame.Rect(cb, y + 2, wb, hs - 4), f.get("inf") or 0, None, ORANGE if mine else (150, 150, 150))
        put(L, F["small"], f"{f.get('inf') or 0:.1f}%".replace(".", ","), (cb + wb + 90, y), col, anchor="topright")
        st = [ES_ST.get(a, a) for a in f.get("act") or []] + [ES_ST.get(a, a) + " (p)" for a in f.get("pend") or []]
        put(L, F["small"], ", ".join(st) or tr_(f.get("gov")), (cb + wb + 110, y), BLUE if st else DIM, x1 - cb - wb - 110)
        y += rh
    y = yb
    pygame.draw.line(L, DIM, (x0, y - 6), (x1, y - 6), 1)
    for c in confs:
        put(L, F["small"], f"{'ELECCIONES' if (c.get('tipo') or '').lower() == 'election' else 'GUERRA'} contra {c.get('contra')}: "
                           f"{c.get('ganados') or 0}-{c.get('perdidos') or 0} días", (x0, y), RED, x1 - x0)
        y += hs + 6
    w_ = put(L, F["small"], "TU FACCIÓN:", (x0, y), DIM) + 14
    if parts:
        lz_parts(L, F["small"], parts, x0 + w_, y, x1 - x0 - w_)
    else:
        put(L, F["small"], "sin estados", (x0 + w_, y), DIM)
    y += hs + 6
    for st in bad:
        put(L, F["small"], f"{ES_ST.get(st, st)}: {TIPS[st]}", (x0, y), st_col(st), x1 - x0); y += hs + 6
    if exp_:
        tg = exp_target(D or FACD["data"] or {}, v)
        txt = (f"EXPANSIÓN · destino probable: {tg[1]} (a {tg[0]:.1f} al)".replace(".", ",") if tg
               else "EXPANSIÓN · destino desconocido (ningún sistema conocido a menos de 30 al)")
        put(L, F["small"], txt, (x0, y), BLUE, x1 - x0)

# ---------------------------------------------------------------------------------------------------------------
# 195 ACTIVIDAD
# ---------------------------------------------------------------------------------------------------------------
def lv_facact(L, area, d, flags, now):
    D, name, v = fs_get()
    if not v:
        return lz_fs_sin(L, area, "sin datos")
    hs, hb, hg = lz_alturas()
    ht = F["tiny"].get_height()
    x0, x1 = area.x + 14, area.right - 14
    y = lz_fs_cab(L, area, d, v, name, now, pob=False)
    rv = lz_volver(L, area)
    T = v.get("trafico") or {}
    hoy, media, alto = traf(v)
    put(L, F["small"], "COMANDANTES POR DÍA", (x0, y), DIM)
    if hoy is not None:
        put(L, F["small"], f"hoy {hoy} · media {media:.0f}".replace(".", ",") + (" · TRIPLE DE LO NORMAL" if alto else ""),
            (x1, y), RED if alto else ORANGE, anchor="topright")
    y += hs + 10
    gh = 150
    if T:
        days = sorted(T)[-7:]
        mx = max(T[k] for k in days) or 1
        hoy_k = time.strftime("%Y-%m-%d", time.gmtime())
        cw = (x1 - x0) // 7
        top = y + ht + 4
        for i, k in enumerate(days):
            bh = max(4, int((gh - ht - 4) * T[k] / mx))
            rr = pygame.Rect(x0 + i * cw + 16, top + gh - ht - 4 - bh, cw - 32, bh)
            pygame.draw.rect(L, (RED if alto else ORANGE) if k == hoy_k else (150, 90, 20), rr, border_radius=4)
            put(L, F["small"], str(T[k]), (rr.centerx, rr.y - 4), WHITE, anchor="midbottom")
            lab = "hoy" if k == hoy_k else ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"][time.strptime(k, "%Y-%m-%d").tm_wday]
            put(L, F["small"], lab, (rr.centerx, top + gh - ht), DIM, anchor="midtop")
        y = top + gh + hs
    else:
        put(L, F["small"], "todavía sin datos (los cuenta la escucha de EDDN)", (x0 + 10, y + 20), DIM); y += 70
    pygame.draw.line(L, DIM, (x0, y), (x1, y), 2); y += 10
    # dos columnas: zonas de conflicto | portanaves vistos
    xm = area.centerx
    yc = y
    put(L, F["small"], "ZONAS DE CONFLICTO (24 h)", (x0, y), DIM); y += hs + 8
    for c in v.get("conflictos") or []:
        put(L, F["small"], f"{'ELECCIONES' if (c.get('tipo') or '').lower() == 'election' else 'GUERRA'} vs {c.get('contra')} · "
                           f"{c.get('ganados') or 0}-{c.get('perdidos') or 0} días", (x0, y), RED, xm - x0 - 30)
        y += hs + 6
    zc = [z for z in v.get("zc") or [] if time.time() - (z.get("t") or 0) < 86400]
    if not zc:
        put(L, F["small"], "ninguna vista", (x0 + 10, y), DIM)
    for z in zc[:5]:
        if y + hs > rv.y - 6:
            break
        lv = {"High": ("ALTA INTENSIDAD", RED), "Med": ("MEDIA INTENSIDAD", ORANGE), "Low": ("BAJA INTENSIDAD", (230, 200, 60))}.get(z.get("i"), ("?", DIM))
        pygame.draw.rect(L, lv[1], (x0 + 4, y + hs // 2 - 7, 14, 14))
        put(L, F["small"], lv[0], (x0 + 28, y), lv[1])
        put(L, F["small"], fac_age(z.get("t"))[0], (xm - 30, y), DIM, anchor="topright")
        y += hs + 6
    pygame.draw.line(L, DIM, (xm, yc), (xm, rv.y - 10), 1)
    y = yc
    put(L, F["small"], "PORTANAVES VISTOS (7 días)", (xm + 30, y), DIM); y += hs + 8
    pn = sorted((v.get("pn") or {}).items(), key=lambda kv: -kv[1].get("t", 0))
    if not pn:
        put(L, F["small"], "ninguno visto", (xm + 40, y), DIM)
    for cs, c in pn:
        if y + hs > area.bottom - 6:
            break
        put(L, F["small"], c.get("n") or "?", (xm + 30, y), WHITE, 300)
        put(L, F["small"], cs, (xm + 340, y), BLUE)
        put(L, F["small"], fac_age(c.get("t"))[0], (x1, y), DIM, anchor="topright")
        y += hs + 6

# ---------------------------------------------------------------------------------------------------------------
# 196 ZONA (Powerplay a 20 al)
# ---------------------------------------------------------------------------------------------------------------
def lv_faczona(L, area, d, flags, now):
    D, name, v = fs_get()
    if not v or not v.get("pos"):
        return lz_fs_sin(L, area, "sin coordenadas de este sistema todavía")
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    y = lz_fs_cab(L, area, d, v, name, now)
    rv = lz_volver(L, area)
    c0 = v["pos"]
    lado = min(rv.y - 12 - y, 520)
    M = pygame.Rect(x0, y, lado, lado)
    pygame.draw.rect(L, DIM, M, 2, border_radius=8)
    sc = (M.w / 2 - 14) / 20
    pygame.draw.circle(L, (45, 30, 10), M.center, int(20 * sc), 2)
    pygame.draw.circle(L, (45, 30, 10), M.center, int(10 * sc), 1)
    pts = []
    for n, z in (D.get("zona") or {}).items():
        if z.get("pos") and math.dist(z["pos"], c0) <= 20:
            pts.append((n, z["pos"], z.get("pot"), z.get("est"), z.get("prog"), n in (D.get("sistemas") or {})))
    for n, f in (D.get("sistemas") or {}).items():
        if f.get("pos") and not f.get("fuera") and math.dist(f["pos"], c0) <= 20 and n not in (D.get("zona") or {}):
            pp_ = f.get("pp") or {}
            pts.append((n, f["pos"], pp_.get("pot"), pp_.get("est"), pp_.get("prog"), True))
    for n, p_, pot, est, prog, mine in pts:
        px, py = M.centerx + (p_[0] - c0[0]) * sc, M.centery - (p_[2] - c0[2]) * sc
        col = PW_COL.get(pot, (130, 130, 130))
        pygame.draw.circle(L, col, (int(px), int(py)), 9)
        if mine:
            pygame.draw.circle(L, ORANGE, (int(px), int(py)), 16, 3)
            if n != name:
                lz_hit(pygame.Rect(int(px) - 24, int(py) - 24, 48, 48), "facsys", n, None)
    pygame.draw.circle(L, BLUE, M.center, 22, 2)
    put(L, F["small"], "20 al", (M.right - 10, M.bottom - 8), DIM, anchor="bottomright")
    lx, ly = M.right + 30, y
    put(L, F["small"], "POWERPLAY ALREDEDOR (20 al)", (lx, ly), DIM); ly += hs + 10
    rows = sorted([p for p in pts if p[2]], key=lambda p: math.dist(p[1], c0))
    if not rows:
        put(L, F["small"], "sin datos de Powerplay cerca todavía", (lx, ly), DIM)
    pie = area.bottom - 2 * (hs + 6) - 6
    rh = hs + 10
    for n, p_, pot, est, prog, mine in rows:
        if ly + rh > pie:
            break
        col = PW_COL.get(pot, (130, 130, 130))
        pygame.draw.circle(L, col, (lx + 9, ly + hs // 2), 8)
        w = x1 - lx
        put(L, F["small"], n, (lx + 28, ly), ORANGE if mine else WHITE, int(w * 0.36))
        put(L, F["small"], f"{pot.split()[-1]} · {tr_(est)}", (lx + 28 + int(w * 0.38), ly), col, int(w * 0.36))
        if prog is not None:
            lz_barra_h(L, pygame.Rect(x1 - 110, ly + 3, 110, hs - 6), max(0, min(1, float(prog))), col)
        ly += rh
    if rows:
        cnt = {}
        for r_ in rows:
            cnt[r_[2]] = cnt.get(r_[2], 0) + 1
        top = max(cnt, key=cnt.get)
        put(L, F["small"], f"{top} controla {cnt[top]} de {len(pts)} sistemas cercanos", (lx, pie), PW_COL.get(top, WHITE), x1 - lx)
    put(L, F["small"], "círculo naranja = tu facción · tócalo", (lx, pie + hs + 6), DIM, x1 - lx)

# ---------------------------------------------------------------------------------------------------------------
# 214 INFLUENCIA
# ---------------------------------------------------------------------------------------------------------------
def lz_hinf(L, r, h, now):
    """Gráfica en escalones (draw_hinf a la escala del lienzo)."""
    pygame.draw.rect(L, (15, 10, 4), r, border_radius=10)
    pygame.draw.rect(L, DIM, r, 2, border_radius=10)
    if not h or len(h) < 2:
        put(L, F["small"], "histórico: aprendiendo… (lo guarda el escucha v5)", r.center, DIM, r.w - 30, anchor="center"); return
    ft = F["small"]
    hs = ft.get_height()
    t0, t1 = h[0][0], max(h[-1][0] + 3600, now)
    vals = [p[1] for p in h]
    mn, mx = min(vals), max(vals)
    if mx - mn < 2:
        m = (mx + mn) / 2; mn, mx = m - 1, m + 1
    mn -= .5; mx += .5
    gl = r.x + tw_(ft, "100,0") + 24
    X = lambda t: gl + (t - t0) / max(1, t1 - t0) * (r.right - 16 - gl)
    Y = lambda v: r.y + 14 + (1 - (v - mn) / (mx - mn)) * (r.h - hs - 34)
    for k in range(5):                                         # rejilla
        yy = r.y + 14 + k * (r.h - hs - 34) / 4
        pygame.draw.line(L, (45, 30, 10), (gl, yy), (r.right - 16, yy), 1)
    pts = []
    for i, (t, v) in enumerate(h):
        xn = X(h[i + 1][0]) if i + 1 < len(h) else r.right - 16
        pts += [(X(t), Y(v)), (xn, Y(v))]
    pygame.draw.lines(L, ORANGE, False, pts, 4)
    for t, v in h:
        pygame.draw.circle(L, ORANGE, (int(X(t)), int(Y(v))), 5)
    f = lambda t: time.strftime("%d/%m", time.localtime(t))
    put(L, ft, f"{mx:.1f}".replace(".", ","), (r.x + 10, Y(mx) - hs // 2), DIM)
    put(L, ft, f"{mn:.1f}".replace(".", ","), (r.x + 10, Y(mn) - hs // 2), DIM)
    put(L, ft, f(t0), (gl, r.bottom - hs - 6), DIM)
    put(L, ft, f(t1), (r.right - 16, r.bottom - hs - 6), DIM, anchor="topright")

def lv_facinf(L, area, d, flags, now):
    D, name, v = fs_get()
    if not v:
        return lz_fs_sin(L, area, "sin datos")
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 14, area.right - 14
    y = lz_fs_cab(L, area, d, v, name, now)
    rv = lz_volver(L, area)
    h = [list(p) for p in v.get("hinf") or []]
    gh = int((rv.y - y) * 0.58)
    lz_hinf(L, pygame.Rect(x0, y, x1 - x0, gh), h, now)
    y += gh + 14
    put(L, F["small"], "ÚLTIMOS CAMBIOS", (x0, y), DIM); y += hs + 8
    rh = hs + 8
    filas = max(1, (rv.y - 8 - y) // rh)
    cw = (x1 - x0) // 2
    k = 0
    for i in range(len(h) - 1, max(0, len(h) - 2 * filas) - 1, -1):
        t, val = h[i]
        dv = val - h[i - 1][1] if i > 0 else None
        cx = x0 + (k // filas) * cw + (0 if k < filas else 20)
        cy = y + (k % filas) * rh
        if cx > x0 and cy + hs > area.bottom:
            break
        put(L, F["small"], time.strftime("%d/%m %H:%M", time.localtime(t)), (cx, cy), DIM)
        put(L, F["small"], f"{val:.1f} %".replace(".", ","), (cx + 220, cy), ORANGE)
        if dv is not None:
            put(L, F["small"], f"{dv:+.1f}".replace(".", ","), (cx + 360, cy), GREEN if dv > 0 else RED)
        k += 1
        if k >= 2 * filas:
            break

# ---------------------------------------------------------------------------------------------------------------
# 213 BGS (la tabla de la web cdsn-web)
# ---------------------------------------------------------------------------------------------------------------
def lv_bgs(L, area, d, flags, now):
    hs, hb, hg = lz_alturas()
    x0, x1 = area.x + 8, area.right - 8
    R = bgs_rows(now)
    tot, ctl = len(R), sum(1 for r in R if r["s"].get("ctrl"))
    al, traf_ = sum(1 for r in R if r["niv"]), sum(r["traf"] for r in R)
    tn = tick_next(now)
    cards = [("SISTEMAS", str(tot), WHITE), ("CONTROLADOS", str(ctl), ORANGE), ("ALERTAS", str(al), RED if al else GREEN),
             ("TRÁFICO HOY", str(traf_), BLUE), ("PRÓX. TICK", "~" + time.strftime("%H:%M", time.localtime(tn[0])) if tn else "—", MERC)]
    y = area.y + 2
    ch = hs + hb + 14
    cw = (x1 - x0) / len(cards)
    for i, (a, b, c) in enumerate(cards):
        r = pygame.Rect(int(x0 + i * cw), y, int(cw) - 10, ch)
        pygame.draw.rect(L, (26, 18, 8), r, border_radius=8)
        put(L, F["small"], a, (r.x + 10, r.y + 4), GREEN)
        put(L, F["btn"], b, (r.right - 12, r.y + hs + 8), c, anchor="topright")
    y += ch + 10
    bh = hs + 14
    for i, (k, lab) in enumerate((("ctrl", "solo controlados"), ("al", "solo alertas"))):
        r = pygame.Rect(x0 + i * 270, y, 256, bh)
        on = BGS["solo"] == k
        pygame.draw.rect(L, ORANGE if on else BLACK, r, border_radius=8)
        pygame.draw.rect(L, ORANGE if on else DIM, r, 2, border_radius=8)
        put(L, F["small"], lab, r.center, BLACK if on else DIM, anchor="center")
        lz_hit(r.inflate(4, 8), "bgssolo", k)
    if BGS["solo"] == "ctrl":
        R = [r for r in R if r["s"].get("ctrl")]
    elif BGS["solo"] == "al":
        R = [r for r in R if r["niv"]]
    B = LZ["bgs"]
    fa = 76                                                   # ancho de las flechas
    put(L, F["small"], f"{len(R)} de {tot} · toca una cabecera para ordenar", (x1 - 2 * fa - 30, y + (bh - hs) // 2), DIM,
        anchor="topright")
    y += bh + 12
    anchos = {"est": 62, "conf": 80, "traf": 26, "pp": 60, "t": 36, "tick": 44}     # algo más de sitio a DATO y TICK
    cols = [(c[0], c[1], anchos.get(c[0], c[2]), c[3]) for c in BGS_COLS]
    k = BGS["orden"]
    def _key(r):
        val = r["niv"] if k == "conf" else r[k]
        if k in ("sys", "est", "pp"):
            return str(val).lower()
        return val if val is not None else -1e9
    R.sort(key=_key, reverse=not BGS["asc"])
    xt = x1 - fa - 10                                         # la tabla deja sitio a las flechas
    sc = (xt - x0) / sum(c[2] for c in cols)
    xs, x = [], x0
    f = F["small"]
    for c in cols:
        w = c[2] * sc
        xs.append((x, w))
        on = c[0] == k
        ww = put(L, f, c[1], (x + (w - 4 if c[3] == "r" else 4), y), ORANGE if on else GREEN, int(w) - 4,
                 anchor="topright" if c[3] == "r" else "topleft")
        if on:                                                # orden: triangulito bajo la cabecera
            tx = (x + w - 4 - ww // 2) if c[3] == "r" else (x + 4 + ww // 2)
            pygame.draw.polygon(L, ORANGE, [(tx - 7, y + hs + 6), (tx + 7, y + hs + 6), (tx, y + hs - 1)] if BGS["asc"] else
                                [(tx - 7, y + hs - 1), (tx + 7, y + hs - 1), (tx, y + hs + 6)])
        lz_hit(pygame.Rect(int(x), y - 8, int(w), hs + 16), "bgsord", c[0])
        x += w
    y += hs + 10
    pygame.draw.line(L, DIM, (x0, y), (xt, y), 2); y += 4
    rh = hs + 10
    nvis = max(1, (area.bottom - y - 4) // rh)
    B["nvis"] = nvis
    B["max"] = max(0, len(R) - nvis)
    B["off"] = max(0, min(B["off"], B["max"]))
    ytab = y
    for r in R[B["off"]:B["off"] + nvis]:
        s = r["s"]
        if r["niv"]:
            pygame.draw.line(L, RED if r["niv"] == 2 else YELLOW, (x0 - 4, y + 3), (x0 - 4, y + rh - 5), 5)
        if s.get("ctrl"):
            pygame.draw.rect(L, ORANGE, (int(xs[0][0]) + 6, y + rh // 2 - 7, 12, 12))
        vals = {"sys": (s["sys"], ORANGE if s.get("ctrl") else WHITE),
                "inf": (f"{r['inf']:.1f}".replace(".", ","), WHITE),
                "d": ("—" if r["d"] is None else f"{r['d']:+.1f}".replace(".", ","), GREEN if (r["d"] or 0) > 0 else RED if (r["d"] or 0) < 0 else DIM),
                "vent": (f"{r['vent']:.1f}".replace(".", ","), RED if r["vent"] < 5 else WHITE if r["vent"] < 15 else GREEN),
                "est": (r["est"] or "—", DIM), "conf": (r["conf"], RED if r["niv"] == 2 else YELLOW),
                "traf": (str(r["traf"] or "—"), BLUE), "pob": (fnum_pob(r["pob"]) if r["pob"] else "—", DIM),
                "pp": (r["pp"] or "—", DIM), "t": (_lz_hace(now - r["t"]) if r["t"] else "—", DIM),
                "tick": ("~" + time.strftime("%H:%M", time.localtime(r["tick"])) if r["tick"] else "—", MERC)}
        for i, ((x, w), c) in enumerate(zip(xs, cols)):
            t_, col = vals[c[0]]
            fc = F["tiny"] if c[0] in ("est", "pob", "pp", "t", "tick") else f
            xx = x + (w - 4 if c[3] == "r" else 4) + (26 if i == 0 else 0)
            put(L, fc, t_, (xx, y + 4 + (hs - fc.get_height()) // 2), col, int(w) - 8 - (26 if i == 0 else 0), anchor="topright" if c[3] == "r" else "topleft")
        lz_hit(pygame.Rect(x0, y, xt - x0, rh), "facsys", s["sys"], 213)
        pygame.draw.line(L, (40, 28, 10), (x0, y + rh - 1), (xt, y + rh - 1), 1)
        y += rh
    # flechas ▲ ▼ (como la ruta de NAVEGACIÓN)
    if B["max"]:
        alto = (area.bottom - ytab - 60) // 2
        for j, (dlt, on) in enumerate(((-1, B["off"] > 0), (1, B["off"] < B["max"]))):
            r = pygame.Rect(x1 - fa, ytab + j * (alto + 60), fa, alto)
            lz_flecha_btn(L, r, dlt < 0, on)
            if on:
                lz_hit(r, "bgsoff", dlt)
        put(L, F["tiny"], f"{B['off'] + 1}-{min(len(R), B['off'] + nvis)}", (x1 - fa // 2, ytab + alto + 18), DIM, anchor="center")
        put(L, F["tiny"], f"de {len(R)}", (x1 - fa // 2, ytab + alto + 20 + F["tiny"].get_height()), DIM, anchor="center")

_LZ_B11 = {220: lv_sub9, 192: lv_fac, 193: lv_fac, 194: lv_ficha, 195: lv_facact, 196: lv_faczona, 214: lv_facinf, 213: lv_bgs}
LZ_PANEL.update(_LZ_B11)
