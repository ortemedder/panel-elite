# Panel Elite v2.0 · parte 53: v2.0c
#   - SIGUIENTE SALTO (copiado al PC): aviso con su número (#NN), dura 6 s (antes 4) y suena; el mensaje se quita en
#     ALERTAS y el pitido en SONIDO, cada uno por su lado.
#   - RECOGIENDO COMBUSTIBLE a 1280x800 con animación nueva: depósito que se llena (con olas y burbujas), «LLENO EN»
#     en grande y termómetro de CALOR (el juego solo dice si te sobrecalientas, no da la temperatura en número).
#     Se apaga en ALERTAS > «RECOGIDA: DEPÓSITO ANIMADO» (vuelve la pantalla de la v2.0, gasta menos CPU).

EV_LIST.append(("sigsalto", "SIGUIENTE SALTO COPIADO"))
EV_LIST.append(("recanim", "RECOGIDA: DEPÓSITO ANIMADO (CPU)"))

# ---------------------------------------------------------------------------------------------------------------
# SIGUIENTE SALTO con número
# ---------------------------------------------------------------------------------------------------------------
_rx_copia_v20c = rx_copia

def rx_copia(nombre, titulo=None):
    if titulo != "SIGUIENTE SALTO":
        return _rx_copia_v20c(nombre, titulo)
    _rx_copia_v20c(nombre)                                  # copia al PC sin aviso
    if ev_on("sigsalto"):
        k0 = XA_K[0]
        try:
            XA_K[0] = "sigsalto"
            set_alert(titulo, f"copiado {nombre} · Ctrl+V en el mapa galáctico", GREEN, 6, kind="info")
        finally:
            XA_K[0] = k0
    if snd_on("sigsalto"):
        play("ok")

# ---------------------------------------------------------------------------------------------------------------
# RECOGIDA DE COMBUSTIBLE: depósito animado
# ---------------------------------------------------------------------------------------------------------------
_lz_recogida_v20 = lz_recogida

def _rc_deposito(L, r, pct, col, now, vivo):
    """Depósito vertical que se llena hasta pct (0..1); con olas y burbujas si vivo."""
    pygame.draw.rect(L, (20, 20, 20), r, border_radius=24)
    hl = int((r.h - 16) * max(0.0, min(1.0, pct)))
    top = r.bottom - 8 - hl
    if hl > 0:
        oscuro = tuple(c // 2 for c in col)
        x0, x1 = r.x + 8, r.right - 8
        pts = [(x0, r.bottom - 8)]
        for x in range(x0, x1 + 1, 10):
            ola = 6 * math.sin(x / 22 + now * 4) if vivo and hl > 14 else 0
            pts.append((x, max(r.y + 8, top + ola)))
        pts.append((x1, r.bottom - 8))
        pygame.draw.polygon(L, oscuro, pts)
        pygame.draw.lines(L, col, False, pts[1:-1], 4)
        if vivo and hl > 30:
            for j in range(6):
                bx = x0 + 20 + (j * 37) % (x1 - x0 - 40)
                by = r.bottom - 16 - ((now * 90 + j * 53) % max(1, hl - 24))
                pygame.draw.circle(L, col, (int(bx), int(by)), 4 + j % 3, 2)
    for q in (0.25, 0.5, 0.75):                                     # marcas del 25, 50 y 75 %
        yy = r.bottom - 8 - int((r.h - 16) * q)
        pygame.draw.line(L, DIM, (r.right - 30, yy), (r.right - 8, yy), 2)
    pygame.draw.rect(L, col, r, 5, border_radius=24)
    put(L, F["big"], f"{pct * 100:.0f}%", (r.centerx, r.centery), WHITE, anchor="center")

def _rc_calor(L, r, hot, now):
    """Termómetro de CALOR: verde y bajo si va bien; rojo, lleno y parpadeando si te sobrecalientas."""
    blink = int(now * 3) % 2 == 0
    put(L, F["btn"], "CALOR", (r.x, r.y), DIM)
    n, x0, w = 10, r.x + 140, (r.w - 140) // 10
    for i in range(n):
        c = (RED if blink else (110, 0, 0)) if hot else (GREEN if i < 3 else (30, 30, 30))
        pygame.draw.rect(L, c, (x0 + i * w, r.y, w - 6, 40), border_radius=4)
    put(L, F["btn"] if hot else F["small"], "¡SOBRECALENTAMIENTO!" if hot else "temperatura OK",
        (r.centerx + 70, r.y + 56), (RED if blink else WHITE) if hot else GREEN, r.w - 140, anchor="midtop")

def lz_recogida(L, d, flags, now):
    if not ev_on("recanim"):
        return _lz_recogida_v20(L, d, flags, now)
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
    box = pygame.Rect(60, 110, LW - 120, 580)
    pygame.draw.rect(L, BLACK, box)
    pygame.draw.rect(L, col, box, 6, border_radius=20)
    tanque = pygame.Rect(box.x + 60, box.y + 40, 250, box.h - 80)
    pct = max(0.0, min(1.0, fuel / cap)) if fuel is not None and cap else (1.0 if full else 0.0)
    xd, wd = tanque.right + 60, box.right - 50 - (tanque.right + 60)
    cxd = xd + wd // 2
    if full and not on:
        _rc_deposito(L, tanque, 1.0, GREEN, now, False)
        put_fit(L, ("clock", "num", "big"), "DEPÓSITO LLENO", (cxd, box.centery - 40), GREEN, wd, anchor="center")
        if fuel is not None:
            put(L, F["big"], f"{fnum(fuel)} t", (cxd, box.centery + 70), WHITE, anchor="center")
        return
    _rc_deposito(L, tanque, pct, RED if hot and blink else ORANGE, now, True)
    y = box.y + 34
    put(L, F["big"], "RECOGIENDO COMBUSTIBLE", (cxd, y), ORANGE, wd, anchor="midtop"); y += 70
    if fuel is not None:
        put_fit(L, ("num", "big"), f"{fnum(fuel)} / {fnum(cap) if cap else '?'} t", (cxd, y), WHITE, wd, anchor="midtop")
    y += 100
    h = scoop["hist"]
    rate = (h[-1][1] - h[0][1]) / (h[-1][0] - h[0][0]) if len(h) >= 2 and h[-1][0] - h[0][0] > 1 else None
    put(L, F["small"], "LLENO EN", (cxd, y), DIM, anchor="midtop"); y += 30
    if rate and rate > 0.001 and cap and fuel is not None:
        put_fit(L, ("clock", "num", "big"), dur_s((cap - fuel) / rate), (cxd, y), ORANGE, wd, anchor="midtop")
    else:
        put(L, F["big"], "calculando…", (cxd, y + 20), DIM, anchor="midtop")
    y += 150
    if rate is not None:
        put(L, F["btn"], f"{fnum(rate, 2)} t/s", (cxd, y), ORANGE, anchor="midtop")
    _rc_calor(L, pygame.Rect(xd, box.bottom - 120, wd, 100), hot, now)
