# Panel Elite v2.3 · parte 64: v2.3b — arreglos de la v2.3 (log de Operations del 24/11)
#   - COMBATE EN ANILLOS: con las armas fuera en un anillo salía APROXIMACIÓN hasta la música de combate o el primer
#     «te atacan» (casi 1 min en una zona de combate de Operations). Ahora armas fuera en un anillo = COMBATE, salvo que
#     estés minando (prospectores, recolectores o refinado en los últimos 10 min): entonces sigue MINERÍA. Si te atacan
#     minando, COMBATE como siempre.
#   - MEGA NAVE (Operations): el contador de 15 min solo sale A PIE (o si ya lo has arrancado); en los combates con
#     nave no sale ni ocupa la esquina de los toques.

_big_mode_base_v23b = _big_mode_base

def _big_mode_base(d, flags):
    m = _big_mode_base_v23b(d, flags)
    d = d or {}
    if m == "APROXIMACIÓN" and (d.get("body") or "").endswith(" Ring") and hp_out(d, flags) \
            and not mining_active(d, time.time()):
        return "COMBATE"
    return m

def mega_ver(d):
    return MEGA["t0"] is not None or bool((d or {}).get("Flags2", 0) & 1)

_mega_left_v23b = mega_left

def mega_left(d, now):
    r = _mega_left_v23b(d, now)
    if r is False and not mega_ver(d):
        return None                                      # en espera y no estás a pie: no se enseña
    return r

_mega_rect_v23b = mega_rect

def mega_rect(w, h):
    with lock:
        d = state["data"]
    if ops_on(d) and not mega_ver(d):
        return pygame.Rect(0, 0, 0, 0)                   # sin cuadro: los toques de esa esquina van a lo de debajo
    return _mega_rect_v23b(w, h)

# v2.3c: con la pestaña PLANETA, las de NAVEGACIÓN llegaban debajo del engranaje (480x320) y tocar PLANETA abría
# AJUSTES. Si las pestañas no caben antes del engranaje, se estrechan todas por igual.
_tab_rects_v23c = tab_rects

def tab_rects(v):
    out = _tab_rects_v23c(v)
    if not out:
        return out
    x0, lim = out[0][2].x, GEAR.x - 4
    if out[-1][2].right <= lim:
        return out
    k = (lim - x0 - 3 * (len(out) - 1)) / sum(r.w for _, _, r, _ in out)
    res, x = [], x0
    for t, name, r, on in out:
        w = max(20, int(r.w * k))
        res.append((t, name, pygame.Rect(x, r.y, w, r.h), on))
        x += w + 3
    return res

# ---------------------------------------------------------------------------------------------------------------
# v2.3d: COMBATE + CAZA — ficha del objetivo bien encuadrada en el cuadro del tablero y botón NÚCLEO
# (y el REGISTRO DE COMBATE ya no da «too many values to unpack» con los derribos con hora del sender b20)
# ---------------------------------------------------------------------------------------------------------------
_lv_combate_caza_v23d = lv_combate_caza

def lv_combate_caza(L, area, d, flags, now):
    d = d or {}
    t = d.get("target") or {}
    th = int(area.h * 0.24)
    card = pygame.Rect(area.x + 6, area.y + 4, area.w - 12, th - 8)
    # se dibuja todo como antes y luego se rehace la parte del objetivo
    _lv_combate_caza_v23d(L, area, dict(d, target=None), flags, now)   # caza y botones como antes; el objetivo, aquí
    mid = card.x + card.w * 0.62
    pygame.draw.rect(L, BLACK, (card.x + 3, card.y + 3, int(mid - card.x) - 6, card.h - 6))
    pad = max(4, card.h // 14)
    fb = "btn" if card.h >= 3 * F["btn"].get_height() else "small"
    hb = F[fb].get_height()
    if not t:
        put(L, F["btn"], "SIN OBJETIVO", (card.x + (mid - card.x) / 2, card.centery), DIM, anchor="center")
        return
    x0 = card.x + 2 * pad
    put(L, F[fb], (t.get("ship") or "?").upper(), (x0, card.y + pad), ORANGE, (mid - card.x) * 0.48)
    lg = t.get("legal") or ""
    yl = card.y + pad + max(0, hb - F["small"].get_height()) // 2
    xl, wl = card.x + (mid - card.x) * 0.52, (mid - card.x) * 0.46
    sub_ = t.get("subsys")
    sh = t.get("subhealth")
    if sub_ and nuc_es_planta(t):                        # v2.3e: núcleo apuntado, muy a la vista
        on = int(now * 1.5) % 2 == 0
        pygame.draw.rect(L, GREEN if on else (30, 110, 50), card, 4, border_radius=10)
        put_fit(L, (fb, "small"), "NÚCLEO" + (f" · {sh:.0f} %" if sh is not None else ""), (xl, card.y + pad), GREEN, wl)
    elif sub_:
        put(L, F["small"], str(sub_).upper() + (f" · {sh:.0f} %" if sh is not None else ""), (xl, yl), ORANGE, wl)
    else:
        bits = [x for x in (t.get("pilot"), "BUSCADO" if lg.lower() == "wanted" else "") if x]
        put(L, F["small"], " · ".join(bits), (xl, yl), RED if "BUSCADO" in bits else WHITE, wl)
    top = card.y + pad + hb + pad
    bh = max(6, (card.bottom - pad - top - pad) // 2)
    bw = int((mid - card.x) * 0.60)
    lc_barra2(L, x0, top, bw, bh, "ESCUDO", t.get("shield"), BLUE)
    lc_barra2(L, x0, top + bh + pad, bw, bh, "CASCO", t.get("hull"), ORANGE)
    # NÚCLEO a la derecha de las barras
    rn = pygame.Rect(x0 + bw + 2 * pad, top, int(mid - 2 * pad - (x0 + bw + 2 * pad)), 2 * bh + pad)
    if rn.w > 40:
        ok = nuc_es_planta(t)
        auto = (cfg.get("autoev") or {}).get("nucleo", False)
        sub = NUC["msg"] if NUC["run"] else ("APUNTADO" if ok else ("AUTO" if auto else ""))
        if t.get("t"):
            ago = int(pc_now(d, now) - t["t"])
            sub = sub or (f"hace {ago} s" if ago < 120 else f"hace {ago // 60} min")
        if ok and not NUC["run"]:                       # v2.3e: botón verde «NÚCLEO FIJADO»
            br = max(6, rn.h // 10)
            pygame.draw.rect(L, GREEN, rn, border_radius=br)
            put_fit(L, ("btn", "small", "tiny"), "FIJADO", rn.center, BLACK, rn.w - 10, anchor="center")
        else:
            lz_boton_v(L, rn, "NÚCLEO", sub or None, F["small"], filled=False, lit=NUC["run"] and int(now * 3) % 2 == 0)
        lz_hit(rn, "nucleo")

LZ_PANEL[191] = lv_combate_caza
if 191 in LZ_CELDA:
    LZ_CELDA[191] = lambda L, d, flags, now: lv_combate_caza(L, pygame.Rect(0, 0, CW0, CH0), d, flags, now)
