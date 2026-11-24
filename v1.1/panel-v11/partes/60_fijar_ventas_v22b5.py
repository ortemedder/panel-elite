# Panel Elite v2.2 · parte 60: v2.2b5 — FIJAR PANTALLA, DATOS VENDIDOS, VENTA EN EL MERCADO y hora de los derribos
#   (va con el sender v1.0b20)
#   - FIJAR (idea de CMDR KORZO): candado en la barra de arriba del tablero. Tocarlo deja fija la pantalla que se ve
#     (combate, minería, exobiología, colonización...) con sus datos en vivo; el candado late en ámbar y un borde ámbar
#     enmarca el tablero. Tocarlo otra vez lo abre (animación corta) y vuelve el cambio automático. Los avisos siguen
#     saliendo. CAMBIO AUTO > «EL COMBATE QUITA LO FIJADO» (sí de fábrica). Al reiniciar el panel se suelta.
#   - DATOS VENDIDOS: aviso con los sistemas vendidos y lo cobrado (con su número en ALERTAS / SONIDO).
#   - VENTA EN EL MERCADO: «VENDIDO N t de X · +cr · beneficio»; sonido de caja si pasa de 10 M cr.
#   - REGISTRO de combate (nave y a pie): hora de cada derribo.

SENDER_OK = SENDER_REQ = "v1.0b20"

EV_LIST.append(("datavend", "DATOS VENDIDOS (EXPLORACIÓN)"))
EV_LIST.append(("venta", "VENTA EN EL MERCADO"))
AUTO_LIST.append(("fixcomb", "EL COMBATE QUITA LA PANTALLA FIJADA"))

try:
    SOUNDS["caja"] = "/tmp/panel_caja.wav"
    _w = __import__("wave")
    if not os.path.exists(SOUNDS["caja"]):
        _fr = 22050
        _buf = bytearray()
        for f_, dur in ((1318, .07), (0, .03), (1568, .07), (0, .03), (2093, .22)):
            for i in range(int(_fr * dur)):
                v = 0 if not f_ else int(9000 * math.sin(2 * math.pi * f_ * i / _fr) * (1 - i / (_fr * dur)))
                _buf += int(v).to_bytes(2, "little", signed=True)
        with _w.open(SOUNDS["caja"], "wb") as _o:
            _o.setnchannels(1); _o.setsampwidth(2); _o.setframerate(_fr); _o.writeframes(bytes(_buf))
except Exception as _e:
    print("sin sonido de caja:", _e)

# ---------------------------------------------------------------------------------------------------------------
# avisos de venta
# ---------------------------------------------------------------------------------------------------------------
def _xa_venta(key, snd, **a):
    k0 = XA_K[0]
    try:
        XA_K[0] = key
        xa["a"] = dict(until=time.time() + a.pop("secs", 7), **a)
        play(snd)
    finally:
        XA_K[0] = k0

_handle_note_v22b5 = handle_note

def handle_note(kind, text):
    if kind == "datavend":
        p = str(text).split("|")
        try:
            n, tot, bonus = int(p[0]), int(p[1]), int(p[2] or 0)
        except (ValueError, IndexError):
            return
        lista = []
        for it in ("|".join(p[3:])).split(";"):
            if ":" in it:
                nm, v = it.rsplit(":", 1)
                lista.append(f"{nm}  {cr(int(v))} cr" if v.isdigit() and int(v) else nm)
        plog(f"DATOS VENDIDOS: {n} sistemas, {fnum(tot, 0)} cr")
        if ev_on("datavend"):
            lines = lista[:3] if len(lista) <= 3 else lista[:2] + [f"... y {len(lista) - 2} sistemas más"]
            _xa_venta("datavend", "caja" if tot >= 10_000_000 else "ok", col=GREEN,
                      title="DATOS VENDIDOS" + (f" · BONO +{cr(bonus)} cr" if bonus else ""),
                      big=f"{n} SISTEMAS · +{cr(tot)} cr", lines=lines, secs=10)
        return
    if kind == "venta":
        p = (str(text).split("|") + [""] * 5)[:5]
        try:
            n, nombre, tot, ben, avg = int(p[0]), p[1], int(float(p[2])), int(float(p[3])), int(float(p[4] or 0))
        except ValueError:
            return _handle_note_v22b5(kind, text)
        plog(f"VENDIDO {n} t de {nombre}: {fnum(tot, 0)} cr (beneficio {fnum(ben, 0)})")
        if ev_on("venta") and not (xa.get("a") and xa["a"].get("until", 0) - time.time() > 6.5):
            lines = [f"beneficio {'+' if ben >= 0 else '-'}{cr(abs(ben))} cr" + (f"  (pagado a {fnum(avg, 0)} cr/t)" if avg else "")]
            _xa_venta("venta", "caja" if tot >= 10_000_000 else "ok", col=GREEN if ben >= 0 else ORANGE,
                      title=f"VENDIDO {fnum(n, 0)} t DE {nombre.upper()}"[:40], big=f"+{cr(tot)} cr", lines=lines, secs=5)
        return
    return _handle_note_v22b5(kind, text)

# ---------------------------------------------------------------------------------------------------------------
# hora en el REGISTRO de combate (nave y a pie): el sender b20 manda [objetivo, cr, tipo, hora]
# ---------------------------------------------------------------------------------------------------------------
def _reg_kills(Z, d, a, palabra):
    kills = ((d.get("combat") or {}).get("kills") or [])[:3]
    x, w = a.x, a.w
    y = a.y - 12
    lh = (a.bottom + 8 - y) // 3
    if not kills:
        put(Z, F["small"], f"sin {palabra.lower()}s en esta sesión", (x, y + 4), DIM)
    for k_ in kills:
        tgt, rew, kind = k_[0], k_[1], k_[2]
        t_ = k_[3] if len(k_) > 3 else None
        tag, sub, col = C2_TIPO.get(kind, (palabra, "", DIM))
        if t_:
            put(Z, F["tiny"], time.strftime("%H:%M", time.localtime(t_)), (x, y + 3), DIM)
        put(Z, F["small"], palabra.upper(), (x + 90, y), GREEN)
        put(Z, F["small"], tgt, (x + 250, y), WHITE, w * 0.4)
        put(Z, F["tiny"], sub, (x + 250 + int(w * 0.42), y + 3), col)
        if rew:
            put(Z, F["small"], f"+{fnum(rew, 0)} cr", (x + w, y), GREEN, anchor="topright")
        y += lh
    lz_hit((0, 0, Z.get_width(), Z.get_height()), "vista", 61)

def c2_registro(Z, d, flags, now):
    d = d or {}
    _reg_kills(Z, d, c2_marco(Z, "REGISTRO", c2_contadores(d) or None, dcol=WHITE), "Derribo")

def p2_registro(Z, d, flags, now):
    d = d or {}
    _reg_kills(Z, d, c2_marco(Z, "REGISTRO", p2_contadores(d) or None, dcol=WHITE), "Baja")

# ---------------------------------------------------------------------------------------------------------------
# FIJAR PANTALLA
# ---------------------------------------------------------------------------------------------------------------
FIX = {"on": False, "kind": None, "mode": None, "abre": 0.0, "nom": ""}
FIX_R = pygame.Rect(178, 12, 70, 70)                 # en el lienzo, junto a MENÚ

_big_mode_v22b5 = big_mode
_mina_ast_v22b5, _mina_pla_v22b5, _bio_v22b5 = mina_asteroides, mina_planeta, bio_activa

def fix_tipo(d, flags, now):
    """Qué pantalla se está viendo ahora (sin lo fijado)."""
    mode = _big_mode_v22b5(d, flags)
    if mina2_on() and _bio_v22b5(d, flags, now, mode):
        return "bio", mode, "EXOBIOLOGÍA"
    if mina2_on() and _mina_ast_v22b5(d, flags, now, mode):
        return "ast", mode, "MINERÍA"
    if mina2_on() and _mina_pla_v22b5(d, flags, now, mode):
        return "srv", mode, "MINERÍA PLANETARIA"
    return "modo", mode, str(mode)

def fix_soltar(motivo):
    if FIX["on"]:
        FIX.update(on=False, abre=time.time())
        plog(f"PANTALLA FIJADA: suelta ({motivo})")
    TAP_EV.set()

def fix_tocar():
    with lock:
        d = state["data"] or {}
    if FIX["on"]:
        tap_flash(("fix",))
        return fix_soltar("candado")
    k, mode, nom = fix_tipo(d, d.get("Flags", 0), time.time())
    FIX.update(on=True, kind=k, mode=mode, nom=nom)
    tap_flash(("fix",))
    plog(f"PANTALLA FIJADA: {nom}")
    TAP_EV.set()

def big_mode(d, flags):
    real = _big_mode_v22b5(d, flags)
    if not FIX["on"]:
        return real
    if (str(real).startswith("COMBATE") and not str(FIX["mode"]).startswith("COMBATE")
            and (cfg.get("autoev") or {}).get("fixcomb", True)):
        fix_soltar("combate")
        return real
    return FIX["mode"]

def mina_asteroides(d, flags, now, mode):
    return FIX["kind"] == "ast" if FIX["on"] else _mina_ast_v22b5(d, flags, now, mode)

def mina_planeta(d, flags, now, mode):
    return FIX["kind"] == "srv" if FIX["on"] else _mina_pla_v22b5(d, flags, now, mode)

def bio_activa(d, flags, now, mode):
    return FIX["kind"] == "bio" if FIX["on"] else _bio_v22b5(d, flags, now, mode)

def lz_candado(L, r, now, cerrado, abre):
    """Candado: cerrado late en ámbar (cada 2 s); abierto en gris. Al abrirse, el arco sube en 0,6 s."""
    if cerrado:
        f_ = 0.6 + 0.4 * (0.5 + 0.5 * math.sin(now * math.pi))
        col = tuple(int(c * f_) for c in AMBAR)
        lift = 0
    else:
        col = DIM
        lift = 14 if now - abre > 0.6 else int(14 * (now - abre) / 0.6)
    pygame.draw.rect(L, BLACK, r, border_radius=10)
    pygame.draw.rect(L, col, r, 3 if cerrado else 2, border_radius=10)
    cuerpo = pygame.Rect(r.x + 17, r.y + 32, r.w - 34, 26)
    arco = pygame.Rect(r.x + 23, r.y + 12 - lift, r.w - 46, 34)
    pygame.draw.arc(L, col, arco, 0 if cerrado else 0.0, math.pi, 5)
    pygame.draw.line(L, col, (arco.x + 2, arco.centery), (arco.x + 2, cuerpo.y), 5)
    if cerrado:
        pygame.draw.line(L, col, (arco.right - 3, arco.centery), (arco.right - 3, cuerpo.y), 5)
    pygame.draw.rect(L, col, cuerpo, 0, border_radius=4)
    pygame.draw.circle(L, BLACK, (cuerpo.centerx, cuerpo.centery - 2), 4)

def lz_tab_cabecera(L, d, flags, now, mode):
    LZ["hits"] = []
    lz_boton(L, (14, 12, 156, 70), "MENÚ", col=ORANGE, accion=("menu",), font=F["btn"])
    lit = flash.get(("fix",), 0) > now
    lz_candado(L, FIX_R, now, FIX["on"], FIX["abre"])
    if lit:
        pygame.draw.rect(L, WHITE, FIX_R, 3, border_radius=10)
    x0 = 266
    put_fit(L, ("big", "btn", "small"), (d.get("system") or "---").upper(), (x0, 8), ORANGE, 420)
    if FIX["on"]:
        put(L, F["tiny"], f"{FIX['nom']} · FIJADA", (x0, 62), AMBAR, 420)
    else:
        put(L, F["tiny"], mode, (x0, 62), GREEN, 420)
    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
    if flags & (1 << 26):
        fuel, cap = (d.get("Fuel") or {}).get("FuelReservoir"), None
    if fuel is not None:
        bx = pygame.Rect(700, 16, 190, 26)
        pygame.draw.rect(L, DIM, bx, 2, border_radius=4)
        if cap:
            pct = max(0.0, min(1.0, fuel / cap))
            pygame.draw.rect(L, RED if pct < 0.25 else ORANGE, (bx.x + 4, bx.y + 4, int((bx.w - 8) * pct), bx.h - 8))
        put(L, F["tiny"], f"FUEL {fuel:.1f} t", (bx.right + 12, 15), ORANGE, 170)
    put(L, F["big"], time.strftime("%H:%M"), (LW - 20, 8), ORANGE, anchor="topright")
    put(L, F["tiny"], game_date().upper(), (LW - 20, 60), BLUE, anchor="topright")
    pygame.draw.line(L, AMBAR if FIX["on"] else DIM, (0, LZ_CABH - 4), (LW, LZ_CABH - 4), 2)

_lz_tablero_v22b5 = lz_tablero

def lz_tablero(S, d, flags, now):
    r = _lz_tablero_v22b5(S, d, flags, now)
    if FIX["on"] or now - FIX["abre"] < 0.7:
        BIG["fast"] = True                               # para que el candado se mueva
    if FIX["on"]:
        rr = lz_real((1, LZ_CABH - 4, LW - 2, LH - LZ_CABH + 3))
        f_ = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(now * math.pi))
        pygame.draw.rect(S, tuple(int(c * f_) for c in AMBAR), rr, 2)
    return r

_big_tap_v22b5 = big_tap

def big_tap(xn, yn):
    if lienzo_on() and not hdmi_panel() and LZ.get("lleno") == "tablero":
        p = lienzo_punto(xn, yn)
        if p and FIX_R.inflate(10, 10).collidepoint(p):
            fix_tocar()
            return
    return _big_tap_v22b5(xn, yn)
