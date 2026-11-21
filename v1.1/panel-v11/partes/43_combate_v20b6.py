# Panel Elite v2.0 · parte 43: v2.0b6 — COMBATE, COMBATE + CAZA, OBJETIVO, MINERÍA y ALTÍMETRO a 1280x800
#   En el MENÚ (LZ_PANEL) y como cuadros del tablero (LZ_CELDA). Mismos datos y avisos que antes; los botones tocan el
#   centro de su botón de 480x320 (mismas teclas). El ALTÍMETRO usa sus mismos instrumentos (draw_alt), ahora dibujados
#   directamente a la resolución de la pantalla con las letras nuevas.

def lc_barra2(L, x, y, w, h, label, pct, col):
    """Barra con su rótulo a la izquierda, de alto h."""
    lw = put(L, F["small"], label, (x, y + (h - F["small"].get_height()) // 2), DIM) + 10
    bx = pygame.Rect(x + lw, y, w - lw, h)
    pygame.draw.rect(L, DIM, bx, 2, border_radius=3)
    if pct is not None:
        pygame.draw.rect(L, col, (bx.x + 3, bx.y + 3, int((bx.w - 6) * max(0, min(100, pct)) / 100), bx.h - 6))
        put(L, F["small"], f"{pct:.0f}%", (bx.right - 8, bx.centery), WHITE, anchor="midright")
    return bx

# ---------------------------------------------------------------------------------------------------------------
# ficha del objetivo (COMBATE y OBJETIVO)
# ---------------------------------------------------------------------------------------------------------------
def lz_ficha_objetivo(L, card, d, flags, now, foto=True):
    pygame.draw.rect(L, DIM, card, 2, border_radius=10)
    t = (d or {}).get("target")
    if not t:
        put(L, F["big"], "SIN OBJETIVO", card.center, DIM, anchor="center")
        return
    hb, hs = F["big"].get_height(), F["small"].get_height()
    pad = max(8, card.h // 30)
    x, y = card.x + 2 * pad, card.y + pad
    cmdr = t.get("cmdr")
    mine = TGT["key"] == (t.get("stype"), t.get("pilot"))
    put(L, F["big"], (t.get("ship") or "?").upper(), (x, y), ORANGE, card.w * 0.55)
    age = ((d or {}).get("pcnow") or 0) - (t.get("t") or 0) if t.get("t") and (d or {}).get("pcnow") else 0
    put(L, F["small"], f"ESCANEO {t.get('scan', 0)}/3" + (f" · hace {age:.0f} s" if age >= 5 else ""),
        (card.right - 2 * pad, y + 4), ORANGE if age >= 30 else DIM, card.w * 0.4, anchor="topright")
    y += hb + 2
    if t.get("pilot"):
        w_ = put(L, F["btn"], t["pilot"], (x, y), BLUE if cmdr else ORANGE, card.w * 0.5)
        if cmdr:
            put(L, F["small"], " COMANDANTE", (x + w_ + 6, y + 6), BLUE)
        ia_ = t.get("inara") or {}
        if cmdr and ia_ and not ia_.get("none"):
            ally = my_squad(d) and ia_.get("squad", "").lower() == my_squad(d).lower()
            put(L, F["small"], ("ALIADO · " if ally else "INARA: ") + inara_line(ia_, d, short=True),
                (card.right - 2 * pad, y + 6), GREEN if ally else ORANGE, card.w - w_ - 4 * pad - 180, anchor="topright")
        else:
            put(L, F["small"], t.get("rank") or "", (card.right - 2 * pad, y + 6), DIM, anchor="topright")
    y += F["btn"].get_height() + pad
    half = (card.w - 6 * pad) // 2
    bh = max(18, int(hs * 1.2))
    lc_barra2(L, x, y, half, bh, "ESCUDO", t.get("shield"), BLUE)
    b2 = lc_barra2(L, x + half + 2 * pad, y, half, bh, "CASCO", t.get("hull"), RED if (t.get("hull") or 100) < 25 else ORANGE)
    if mine:
        for xx, v in ((x + half - 70, TGT["dsh"]), (b2.right - 70, TGT["dhu"])):
            if v and v >= 1:
                put(L, F["small"], f"-{v:.0f}%", (xx, y + (bh - hs) // 2), RED, anchor="topright")
    y += bh + pad
    legal = t.get("legal") or ""
    ia2_ = t.get("inara") or {}
    fr = pygame.Rect(card.right - 2 * pad - int(card.h * 0.55), card.bottom - pad - int(card.h * 0.31), int(card.h * 0.55), int(card.h * 0.31))
    tph_ = foto and bool(cfg.get("cmdrpics", True)) and \
        (avatar_photo(L, ia2_.get("avatar"), fr) or
         ship_photo(L, {"type": t.get("stype"), "ship": t.get("ship") or ia2_.get("ship")}, {}, fr))
    rx = (fr.x - pad) if tph_ else card.right - 2 * pad
    wanted = legal.lower() == "wanted"
    lw = put(L, F["small"], ("BUSCADO" if wanted else legal.upper()) or "-", (x, y + 2), RED if wanted else GREEN)
    if t.get("bounty"):
        put(L, F["small"], f"RECOMPENSA {t['bounty']:,} cr".replace(",", "."), (x + lw + 16, y + 2), RED, card.w * 0.35)
    if t.get("subsys"):
        sh = t.get("subhealth")
        put(L, F["btn"], f"{t['subsys']}" + (f" {sh:.0f}%" if sh is not None else ""), (rx, y),
            RED if sh is not None and sh < 20 else ORANGE, card.w // 2 - 60, anchor="topright")
    y += F["btn"].get_height() + 2
    fac, pw = t.get("faction"), t.get("power")
    if fac or pw:
        fw = 0
        if fac:
            fw = put(L, F["small"], fac, (x, y), GREEN if es_mi_fac(fac) else DIM, max(40, rx - x - 200))
        if pw:
            put(L, F["small"], ("  ·  " if fac else "") + pw, (x + fw, y), MERC, max(40, rx - x - fw - 8))

def lz_escudos_caidos(L, card, d, flags, now):
    """ESCUDOS mm:ss (escudos propios caídos) en la línea del piloto, a la derecha, tapando el rango (como antes)."""
    sd = None if flags & 8 else ((d or {}).get("combat") or {}).get("sd")
    if not sd:
        return
    el = int(now - sd)
    pad = max(8, card.h // 30)
    f = F["small"]
    w_ = tw_(f, "ESCUDOS  00:00") + 30
    r = pygame.Rect(card.right - 2 * pad - w_, card.y + pad + F["big"].get_height() + 2, w_, F["btn"].get_height())
    pygame.draw.rect(L, BLACK, r)
    pygame.draw.rect(L, RED, r, 3, border_radius=6)
    put(L, f, f"ESCUDOS  {el // 60:02d}:{el % 60:02d}", r.center, RED if int(now * 2) % 2 else WHITE, anchor="center")

def lv_combate(L, area, d, flags, now):
    ch = int(area.h * 0.44)
    card = pygame.Rect(area.x + 6, area.y + 4, area.w - 12, ch - 8)
    lz_ficha_objetivo(L, card, d, flags, now)
    lz_escudos_caidos(L, card, d, flags, now)
    zona = pygame.Rect(area.x, area.y + ch, area.w, area.h - ch)
    for i, (txt, key) in enumerate(COMBAT_BTNS):
        lz_boton_v(L, lz_grid(zona, i, 4, 3, gap=8), txt, key.upper(), F["btn"], lit=flash.get((6, i), 0) > now, viejo=c6_rect(i))

def lv_objetivo(L, area, d, flags, now):
    ch = int(area.h * 0.50)
    card = pygame.Rect(area.x + 6, area.y + 4, area.w - 12, ch - 8)
    lz_ficha_objetivo(L, card, d, flags, now, foto=False)
    t = (d or {}).get("target") or {}
    r = pygame.Rect(area.centerx - int(area.h * 0.45), area.y + ch + 4, int(area.h * 0.9), area.h - ch - 12)
    if not (cfg.get("cmdrpics", True) and ship_photo(L, {"type": t.get("stype"), "ship": t.get("ship")}, {}, r)):
        put(L, F["small"], "sin foto de esta nave", r.center, DIM, anchor="center")

def lv_combate_caza(L, area, d, flags, now):
    d = d or {}
    t = d.get("target") or {}
    th = int(area.h * 0.24)
    card = pygame.Rect(area.x + 6, area.y + 4, area.w - 12, th - 8)
    pygame.draw.rect(L, DIM, card, 2, border_radius=10)
    pad = max(8, card.h // 12)
    mid = card.x + card.w * 0.62
    hb = F["btn"].get_height()
    if t:
        put(L, F["btn"], (t.get("ship") or "?").upper(), (card.x + 2 * pad, card.y + pad), ORANGE, card.w * 0.28)
        lg = t.get("legal") or ""
        bits = [x for x in (t.get("pilot"), "BUSCADO" if lg.lower() == "wanted" else "") if x]
        put(L, F["small"], " · ".join(bits), (card.x + card.w * 0.31, card.y + pad + 4), RED if "BUSCADO" in bits else WHITE, card.w * 0.29)
        bh = max(16, (card.h - hb - 4 * pad) // 2)
        bw = int(card.w * 0.40)
        lc_barra2(L, card.x + 2 * pad, card.y + hb + 2 * pad, bw, bh, "ESCUDO", t.get("shield"), BLUE)
        lc_barra2(L, card.x + 2 * pad, card.y + hb + 3 * pad + bh, bw, bh, "CASCO", t.get("hull"), ORANGE)
        if t.get("t"):
            ago = int(pc_now(d, now) - t["t"])
            put(L, F["small"], f"hace {ago} s" if ago < 120 else f"hace {ago // 60} min", (card.x + 3 * pad + bw, card.y + hb + 3 * pad + bh), DIM)
    else:
        put(L, F["btn"], "SIN OBJETIVO", (card.x + card.w * 0.31, card.centery), DIM, anchor="center")
    pygame.draw.line(L, DIM, (mid, card.y + pad), (mid, card.bottom - pad), 2)
    f = d.get("fighter") or {}
    txt, col = FIGHTER_STATE.get(f.get("state"), ("SIN DATOS", DIM))
    put(L, F["small"], "CAZA", (mid + 2 * pad, card.y + pad), DIM)
    put(L, F["btn"], txt, (mid + 2 * pad, card.y + pad + F["small"].get_height() + 2), col, card.right - mid - 4 * pad)
    if f.get("pilot") and f.get("state") == "out":
        put(L, F["small"], f"Piloto: {f['pilot']}", (mid + 2 * pad, card.bottom - pad - F["small"].get_height()), ORANGE,
            card.right - mid - 4 * pad)
    zona_i = pygame.Rect(area.x, area.y + th, area.w // 2 - 6, area.h - th)
    zona_d = pygame.Rect(area.centerx + 6, area.y + th, area.w // 2 - 6, area.h - th)
    cb = dict(COMBAT_BTNS)
    for k, lab in enumerate(CC_L):
        lz_boton_v(L, lz_grid(zona_i, k, 2, 3, gap=8), lab, (cb.get(lab) or "").upper(), F["btn"],
                   lit=flash.get((191, k), 0) > now, viejo=cc_rect(0, k))
    pygame.draw.line(L, ORANGE, (area.centerx, area.y + th), (area.centerx, area.bottom - 4), 3)
    fb = {b[0]: (i, b) for i, b in enumerate(FIGHTER_BTNS)}
    for k, lab in enumerate(CC_R):
        i, b = fb.get(lab, (None, (lab, "", None)))
        lz_boton_v(L, lz_grid(zona_d, k, 2, 3, gap=8), lab, (b[1] or "").replace("KP", "NUM "), F["btn"],
                   filled=b[2] is not None and ui["orders"].get(b[2]) == i, lit=flash.get((191, 10 + k), 0) > now,
                   viejo=cc_rect(1, k))

# ---------------------------------------------------------------------------------------------------------------
# MINERÍA
# ---------------------------------------------------------------------------------------------------------------
def lv_mineria(L, area, d, flags, now):
    d = d or {}
    m = d.get("mining") or {}
    last = m.get("last")
    hs, hb = F["small"].get_height(), F["btn"].get_height()
    x0, xm = area.x + 14, area.x + int(area.w * 0.60)
    pie = area.bottom - hb - 14
    y = area.y + 8
    rhino = "rhino" in (d.get("srvtype") or "").lower()
    if not rhino and last and last.get("motherlode"):
        blink = int(now * 2) % 2
        r = pygame.Rect(area.x + 6, y, area.w - 12, F["big"].get_height() + 10)
        pygame.draw.rect(L, RED if blink else BLACK, r, border_radius=8)
        pygame.draw.rect(L, RED, r, 3, border_radius=8)
        put(L, F["big"], f"NÚCLEO: {last['motherlode'].upper()}", r.center, WHITE, anchor="center")
        y = r.bottom + 8
    put(L, F["small"], "BODEGA DEL RHINO" if rhino else "ÚLTIMO PROSPECTOR", (x0, y), DIM)
    put(L, F["small"], "REFINADO (SESIÓN)", (xm + 14, y), DIM)
    y += hs + 6
    yy = y
    if rhino:
        inv, tot = d.get("srvinv") or [], d.get("srvcargo")
        put(L, F["big"], f"{tot if tot is not None else '?'} t", (x0, y), ORANGE); y += F["big"].get_height() + 4
        for name, n in inv[:8]:
            if y > pie - hb:
                break
            put(L, F["small"], name, (x0, y + 2), ORANGE, xm - x0 - 130)
            put(L, F["btn"], f"{n} t", (xm - 14, y), WHITE, anchor="topright"); y += hb + 2
        if not inv:
            put(L, F["small"], "vacía", (x0, y), DIM)
    elif not last:
        put(L, F["btn"], "Lanza un prospector", (x0, y + 4), DIM)
    else:
        put(L, F["btn"], f"Contenido: {last.get('content') or '?'}", (x0, y), ORANGE, xm - x0 - 10); y += hb + 4
        if last.get("remaining") is not None:
            put(L, F["small"], f"Restante {last['remaining']:.0f}%", (x0, y), DIM); y += hs + 4
        bx0 = x0 + int((xm - x0) * 0.40)
        bw = int((xm - x0) * 0.42)
        for name, pct in last.get("mats") or []:
            if y > pie - hs - 10:
                break
            put(L, F["small"], name, (x0, y + 1), ORANGE, bx0 - x0 - 8)
            bx = pygame.Rect(bx0, y + 2, bw, hs - 4)
            pygame.draw.rect(L, DIM, bx, 2)
            pygame.draw.rect(L, BLUE, (bx.x + 3, bx.y + 3, int((bx.w - 6) * min(pct, 100) / 100), bx.h - 6))
            put(L, F["small"], f"{pct:.1f}%", (xm - 14, y + 1), WHITE, anchor="topright")
            y += hs + 8
    pygame.draw.line(L, DIM, (xm, yy - hs - 8), (xm, pie - 10), 2)
    ref = sorted((m.get("refined") or {}).items(), key=lambda kv: -kv[1])
    if not ref:
        put(L, F["small"], "nada aún", (xm + 14, yy + 4), DIM)
    for name, n in ref[:8]:
        if yy > pie - hb:
            break
        put(L, F["small"], name, (xm + 14, yy + 2), ORANGE, area.right - xm - 140)
        put(L, F["btn"], f"{n}" + ("" if rhino else " t"), (area.right - 14, yy), ORANGE, anchor="topright"); yy += hb + 2
    pygame.draw.line(L, DIM, (area.x + 8, pie - 8), (area.right - 8, pie - 8), 2)
    if rhino:
        sf = (d.get("Fuel") or {}).get("FuelReservoir")
        put(L, F["btn"], f"COMBUSTIBLE: {sf:.2f} t".replace(".", ",") if sf is not None else "COMBUSTIBLE: ?",
            (x0, pie), RED if sf is not None and sf < 0.1 else ORANGE)
        zonas = sum(c for n, c in ((d.get("rings") or {}).get("signals") or []) if "miner" in n.lower() or "mining" in n.lower())
        put(L, F["small"], f"Zonas de minería en el planeta: {zonas}", (area.right - 14, pie + 4), DIM, anchor="topright")
        return
    lim = m.get("limpets")
    put(L, F["btn"], f"LIMPETS: {lim if lim is not None else '?'}", (x0, pie), RED if lim == 0 else ORANGE)
    put(L, F["small"], f"Prospectores {m.get('prospectors', 0)}   ·   Recolectores {m.get('collectors', 0)}",
        (area.right - 14, pie + 4), DIM, area.w * 0.55, anchor="topright")
    # ritmo (t/h y cr/h) y barra de la bodega, encima de la línea de abajo
    tons = sum((m.get("refined") or {}).values())
    yb = pie - 8 - hs - 14
    if tons and m.get("t0") and m.get("t1") and m["t1"] > m["t0"]:
        h = (m["t1"] - m["t0"]) / 3600
        rate = tons / h if h > 0.02 else None
        prices = {r[0].lower(): r[1] for r in ((d.get("market") or {}).get("best") or [])}
        prices.update({r[0].lower(): r[2] for r in ((d.get("market") or {}).get("sell") or [])})
        val = sum(n * prices.get(k.lower(), 0) for k, n in (m.get("refined") or {}).items())
        put(L, F["small"], f"{rate:.0f} t/h".replace(".", ",") + (f"  ·  ~{crx(val / h)} cr/h" if val and h > 0.02 else "")
            if rate else f"{tons} t refinadas", (area.right - 14, yb), GREEN, area.w * 0.45, anchor="topright")
    cap = d.get("cargocap")
    used = sum(c for _, c in (d.get("cargo") or []))
    if cap:
        pct = min(1.0, used / cap)
        full = used >= cap
        col = RED if full else ORANGE if pct >= 0.9 else BLUE
        r = pygame.Rect(x0, yb - 2, int(area.w * 0.42), hs + 6)
        pygame.draw.rect(L, BLACK, r.inflate(6, 6))
        pygame.draw.rect(L, DIM, r, 2)
        if not full or int(now * 3) % 2 == 0:
            pygame.draw.rect(L, col, (r.x + 3, r.y + 3, int((r.w - 6) * pct), r.h - 6))
        txt = "¡BODEGA LLENA!" if full else (f"BODEGA {pct * 100:.0f} %" + (f"  ·  {used}/{cap} t" if pct < 0.9 else "  ·  casi llena"))
        put(L, F["small"], txt, r.center, WHITE, r.w - 12, anchor="center")

# ---------------------------------------------------------------------------------------------------------------
# ALTÍMETRO Y VELOCIDAD (mismos instrumentos, a resolución real)
# ---------------------------------------------------------------------------------------------------------------
def lv_altimetro(L, area, d, flags, now):
    hb = F["small"].get_height() + 14
    r = pygame.Rect(area.x + 6, area.y + 4, area.w - 12, area.h - hb - 12)
    draw_alt(L, r, d, now, big=area.w > 900)
    b = pygame.Rect(area.right - 230, area.bottom - hb - 4, 224, hb)
    on = cfg.get("alt_srv", False)
    ALT_SRV_R[0] = pygame.Rect(W - 112, H - 30, 106, 24)      # el toque va a su botón de 480x320
    lz_boton_v(L, b, "SRV: " + ("SÍ" if on else "NO"), None, F["small"], filled=on, viejo=ALT_SRV_R[0])

LZ_PANEL.update({6: lv_combate, 191: lv_combate_caza, 177: lv_objetivo, 10: lv_mineria, 137: lv_altimetro})
for _v, _fn in ((6, lv_combate), (191, lv_combate_caza), (177, lv_objetivo), (10, lv_mineria), (137, lv_altimetro)):
    LZ_CELDA[_v] = (lambda fn: (lambda L, d, flags, now: fn(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now)))(_fn)
