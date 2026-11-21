# Panel Elite v1.1 · parte 30: novedades v1.1.14
#   HDMI en 4 CUADROS: la versión del panel en oscuro a la derecha de los FPS (si cabe sin pisar la fecha).
#   CERCA DEL SUELO: con el atraque CONCEDIDO en un puerto planetario solo avisa si bajas muy rápido
#   (el aterrizaje automático no llega a esas velocidades). Si un sender futuro manda la música («mtrack»),
#   con «DockingComputer» no avisa nunca.

# ---------------------------------------------------------------------------------------------------------------
# versión junto a los FPS (solo HDMI en 4 CUADROS)
# ---------------------------------------------------------------------------------------------------------------
def perf_draw(S, x, y):
    f = BIG.get("pfont") or BIG.setdefault("pfont", pygame.font.Font(None, 20))
    for i, (t, col) in enumerate(perf_parts()):
        if i:
            x += put(S, f, "·", (x + 6, y), DIM) + 12
        x += put(S, f, t, (x, y), col)
    if cfg.get("bigmode", "4") == "4":
        v = PANEL_VER.split()[0]
        fv = BIG.get("vfont") or BIG.setdefault("vfont", pygame.font.Font(None, 17))
        w = 10 + fv.size(v)[0]
        bw = BIG.get("w") or 1024
        try:                                              # donde empieza la fecha del juego (como render_big_base)
            fbig, fsm = BIG["fonts"]
            lim = bw - 28 - fbig.size(time.strftime("%H:%M"))[0] - fsm.size(game_date().upper())[0] - 4
        except Exception:
            lim = bw - 250
        if x + w <= lim:                                  # sin pisar la fecha
            put(S, fv, v, (x + 10, y + 2), DIM)

# ---------------------------------------------------------------------------------------------------------------
# aviso CERCA DEL SUELO sin molestar al atracar
# ---------------------------------------------------------------------------------------------------------------
def suelo_watch(d, now):
    d = d or {}
    alt, vs = alt_now(d), alt_vs()
    fl = d.get("Flags", 0)
    if alt is None or vs is None or in_srv(d) or fl & 3 or fl & (1 << 29):
        return
    if d.get("mtrack") == "DockingComputer":             # aterrizaje automático
        return
    st = d.get("station") or {}
    atraque = st.get("status") == "CONCEDIDO" and st.get("type") not in STARPORTS
    if atraque:                                           # aterrizando a mano en tu plataforma: solo si es muy rápido
        peligro = (alt < 250 and vs < -70) or (alt < 60 and vs < -30)
    else:
        peligro = (alt < 250 and vs < -35) or (alt < 60 and vs < -15)
    if peligro and now - SUELO["t"] > 12 and ev_on("suelo"):
        SUELO["t"] = now
        k0 = XA_K[0]
        try:
            XA_K[0] = "suelo"
            set_alert("CERCA DEL SUELO, PELIGRO", "", RED, 4)
            play("alarm")
            voice_say("cerca del suelo, peligro")
        finally:
            XA_K[0] = k0
