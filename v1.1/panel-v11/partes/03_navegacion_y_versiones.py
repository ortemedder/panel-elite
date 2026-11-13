# Panel Elite v1.1 · parte 03: navegacion y versiones (lineas 1804-2541 del panel entero)
# ---------- 3 navegacion: cara SISTEMA (politica) ----------
pol = {"sys": None, "until": 0}

def nav_show_pol(d, now):
    sysn = (d or {}).get("system")
    if sysn and sysn != pol["sys"]:
        if pol["sys"] is not None:
            pol["until"] = now + 20
            pol["t0"] = now
        pol["sys"] = sysn
    if NAVBIG[0]:
        return False
    return bool(ui.get("navtab")) or now < pol["until"]

def view_pol_base(surf, d, flags, now):
    S = (d or {}).get("sysinfo") or {}
    if not S.get("faction") and not S.get("gov"):
        put(surf, F["btn"], "Sin datos del sistema", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    y = TOP + 4
    sec = (S.get("sec") or "").lower()
    seccol = GREEN if "alta" in sec or "high" in sec else ORANGE if "media" in sec or "medium" in sec else RED
    pop = S.get("pop")
    popt = (f"{pop / 1e9:.1f} mil M hab." if pop >= 1e9 else f"{pop / 1e6:.1f} M hab." if pop >= 1e6 else f"{pop:,} hab.").replace(".", ",") if pop else ""
    tags = [(S.get("gov"), ORANGE), (S.get("alleg"), BLUE), (S.get("sec"), seccol), (S.get("econ"), WHITE), (popt, DIM)]
    x = 6
    for t, col in tags:
        if not t:
            continue
        w_ = F["small"].size(t)[0] + 12
        if x + w_ > W - 4:
            x = 6; y += 20
        pygame.draw.rect(surf, col, (x, y, w_ - 4, 17), 1, border_radius=3)
        put(surf, F["small"], t, (x + 4, y + 2), col)
        x += w_
    y += 24
    put(surf, F["small"], "CONTROLA", (6, y + 5), DIM)
    put(surf, F["btn"], S.get("faction") or "?", (96, y + 1), ORANGE, 280)
    if S.get("fstate"):
        put(surf, F["small"], S["fstate"], (W - 6, y + 5), RED if S["fstate"] in ("GUERRA", "GUERRA CIVIL", "BLOQUEO", "DISTURBIOS", "ATAQUE PIRATA") else GREEN, anchor="topright")
    y += 24
    put(surf, F["small"], "POWERPLAY", (6, y + 4), DIM)
    if S.get("pp"):
        put(surf, F["btn"], S["pp"], (96, y), BLUE, 230)
        put(surf, F["small"], S.get("ppstate") or "", (W - 6, y + 4), BLUE, anchor="topright")
    else:
        rivals = [p for p in S.get("powers") or []]
        put(surf, F["small"], ("en disputa: " + ", ".join(rivals)) if rivals else "sin potencia", (96, y + 4), DIM, W - 106)
    y += 22
    pygame.draw.line(surf, DIM, (6, y), (W - 6, y)); y += 3
    for name, infl, st_, rep in (S.get("facs") or [])[:6]:
        if y > H - 40:
            break
        put(surf, F["small"], name, (6, y + 3), ORANGE if name == S.get("faction") else WHITE, 190)
        bx = pygame.Rect(200, y + 4, 110, 11)
        pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, BLUE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(100, infl) / 100), bx.h - 4))
        put(surf, F["small"], f"{infl:.0f}%", (342, y + 3), WHITE, anchor="topright")
        put(surf, F["small"], st_ or "", (348, y + 3), RED if st_ in ("GUERRA", "GUERRA CIVIL", "BLOQUEO") else DIM, 80)
        if rep is not None:
            put(surf, F["small"], f"{rep:+.0f}", (W - 6, y + 3), GREEN if rep >= 35 else RED if rep <= -35 else ORANGE, anchor="topright")
        y += 19
    if S.get("st_name"):
        pygame.draw.line(surf, DIM, (6, H - 22), (W - 6, H - 22))
        t = f"{S['st_name']} · {S.get('st_faction') or '?'} · {S.get('st_gov') or ''}"
        put(surf, F["small"], t, (6, H - 18), ORANGE, W - 12)

def nav_strip(surf, d):
    S = (d or {}).get("sysinfo") or {}
    parts = [S.get("gov"), S.get("alleg"), S.get("sec"), S.get("fstate")]
    t = " · ".join(p for p in parts if p)
    if t:
        sec = (S.get("sec") or "").lower()
        col = GREEN if "alta" in sec or "high" in sec else ORANGE if "media" in sec or "medium" in sec else RED
        pygame.draw.line(surf, DIM, (8, H - 22), (W - 8, H - 22))
        put(surf, F["small"], t, (8, H - 18), col, W - 16)

# ---------- 3 navegacion: cara POWERPLAY ----------

NAVBIG = [False]

def view_navbig(surf, d, flags, now):
    """Pantalla grande: 10 s sistema, 5 s powerplay (si hay), luego ruta/destino."""
    nav_show_pol(d, now)
    S = (d or {}).get("sysinfo") or {}
    el = now - pol.get("t0", 0)
    if el < 10:
        return view_pol(surf, d, flags, now)
    if el < 15 and (S.get("pp") or S.get("pp_conf") or S.get("powers")):
        return view_pp(surf, d, flags, now)
    NAVBIG[0] = True
    try:
        view_navx(surf, d, flags, now)
    finally:
        NAVBIG[0] = False

def view_navx_base(surf, d, flags, now):
    if ui.get("navtab") == 2 and not NAVBIG[0]:
        return view_pp(surf, d, flags, now)
    if nav_show_pol(d, now):
        return view_pol(surf, d, flags, now)
    D = (d or {}).get("dest")
    if not D or not D.get("name"):
        nav = (d or {}).get("nav") or {}
        if not nav.get("target") and not (d or {}).get("route"):
            return view_pol(surf, d, flags, now)
        view_nav(surf, d, flags, now)
        nav_strip(surf, d)
        return
    y = TOP + 4
    arrived = (d or {}).get("body") == D["name"]
    put(surf, F["small"], "DESTINO EN EL SISTEMA", (8, y), DIM)
    if arrived:
        put(surf, F["btn"], "HAS LLEGADO", (W - 8, y - 2), GREEN, anchor="topright")
    elif flags & 16:
        put(surf, F["btn"], "EN RUTA", (W - 8, y - 2), BLUE if int(now * 2) % 2 else WHITE, anchor="topright")
    y += 16
    put(surf, F["big"], D["name"].upper(), (8, y), ORANGE, W - 16); y += 30
    if D.get("cls"):
        put(surf, F["btn"], D["cls"], (8, y), BLUE, 280)
    if D.get("dist") is not None:
        put(surf, F["btn"], f"{D['dist']:,} ls".replace(",", "."), (W - 8, y), WHITE, anchor="topright")
    if D.get("cls") or D.get("dist") is not None:
        y += 26
    tags = []
    if D.get("land") is not None:
        tags.append(("ATERRIZABLE", GREEN) if D["land"] else ("NO ATERRIZABLE", DIM))
    g = D.get("g")
    if g is not None:
        tags.append((f"{g:.2f} G".replace(".", ","), RED if g >= 2 else ORANGE if g >= 1.5 else WHITE))
    if D.get("rings"):
        tags.append(("ANILLOS", BLUE))
    if D.get("tf"):
        tags.append(("TERRAFORMABLE", GREEN))
    if D.get("first"):
        tags.append(("1º DESCUBRIMIENTO", GREEN))
    if D.get("mapped"):
        tags.append(("MAPEADO", BLUE))
    for name, c in D.get("signals") or []:
        low = name.lower()
        tags.append((f"{name} x{c}", GREEN if "bio" in low else BLUE if "geo" in low else ORANGE))
    x = 8
    for t, col in tags:
        w_ = F["btn"].size(t)[0] + 14
        if x + w_ > W - 6:
            x = 8; y += 26
        pygame.draw.rect(surf, col, (x, y, w_ - 4, 22), 1, border_radius=4)
        put(surf, F["btn"], t, (x + 5, y + 2), col)
        x += w_
    if tags:
        y += 30
    if D.get("value"):
        put(surf, F["small"], "VALOR DE DATOS", (8, y + 4), DIM)
        put(surf, F["big"], f"~ {cr(D['value'])} cr", (130, y), ORANGE)
    b = (d or {}).get("bio") or {}
    if D.get("lat") is not None and b.get("lat") is not None and b.get("R") and (d or {}).get("body") == D.get("sbody"):
        p1, p2 = math.radians(b["lat"]), math.radians(D["lat"])
        dl = math.radians(D["lon"] - b["lon"])
        brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                      math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
        m = hav((b["lat"], b["lon"]), (D["lat"], D["lon"]), b["R"])
        cx, cy, rr = 34, H - 48, 22
        pygame.draw.circle(surf, DIM, (cx, cy), rr, 1)
        hdg = b.get("hdg")
        if hdg is not None:
            a = math.radians(brg - hdg)
            pt = lambda k, da: (cx + rr * k * math.sin(a + da), cy - rr * k * math.cos(a + da))
            pygame.draw.polygon(surf, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
        txt = f"{m / 1000:.1f} km".replace(".", ",") if m >= 1000 else f"{m:.0f} m"
        put(surf, F["small"], "DISTANCIA AL DESTINO", (66, H - 70), DIM)
        put(surf, F["big"], txt, (66, H - 56), GREEN)
        put(surf, F["btn"], f"rumbo {brg:.0f}°", (W - 8, H - 52), ORANGE, anchor="topright")
    src = D.get("src")
    if src or not (d or {}).get("dstinfo"):
        put(surf, F["small"], f"datos: {src}" if src else "sin datos: no escaneado (o es una estación/señal)",
            (8, H - 16), DIM if src else ORANGE, W - 240)

# ---------- 8 estacion: a los 15 s de atracar, ficha de la estacion y facciones ----------
stdock = {"key": None, "t": 0}

def view_stationx(surf, d, flags, now):
    st = (d or {}).get("station") or {}
    key = (st.get("name"), st.get("status"))
    if st.get("status") == "ATRACADO":
        if stdock["key"] != key:
            stdock.update(key=key, t=now)
        if now - stdock["t"] >= 15:
            S = (d or {}).get("sysinfo") or {}
            stpp = S.get("pp") or S.get("pp_conf") or S.get("powers")
            if stpp and (now - stdock["t"] - 15) % 15 >= 10:
                return view_pp(surf, d, flags, now)
            return view_station_info(surf, d, st)
    else:
        stdock["key"] = None
    return view_station(surf, d, flags, now)

def view_station_info(surf, d, st):
    carrier_bg(surf, d or {}, st, dark=BG_DOCK_DARK, label=False)
    S = (d or {}).get("sysinfo") or {}
    y = TOP + 4
    put(surf, F["big"], (st.get("name") or "?").upper(), (8, y), ORANGE, W - 16); y += 27
    put(surf, F["small"], ST_TYPE.get(st.get("type"), st.get("type") or ""), (8, y), DIM, 200)
    put(surf, F["small"], "ATRACADO", (220, y), BLUE)
    if st.get("dist"):
        put(surf, F["small"], f"{st['dist']:,.0f} ls de la estrella".replace(",", "."), (W - 8, y), DIM, anchor="topright")
    y += 18
    fac = st.get("faction") or S.get("st_faction")
    put(surf, F["small"], "FACCIÓN", (8, y + 4), DIM)
    put(surf, F["btn"], fac or "?", (80, y), ORANGE, 290)
    fst = S.get("st_fstate")
    if fst:
        put(surf, F["small"], fst, (W - 8, y + 4), RED if fst in ("GUERRA", "GUERRA CIVIL", "BLOQUEO", "DISTURBIOS") else GREEN, anchor="topright")
    y += 22
    gv = " · ".join(x for x in (S.get("st_gov"), S.get("st_alleg"), st.get("economy")) if x)
    if gv:
        put(surf, F["small"], gv, (80, y), WHITE, W - 88); y += 18
    srv = set(st.get("services") or [])
    tags = [t for k, t in SERVICES if k in srv]
    tx = 8
    for t in tags:
        w_ = F["small"].size(t)[0] + 10
        if tx + w_ > W - 4:
            tx = 8; y += 18
        pygame.draw.rect(surf, DIM, (tx, y, w_ - 4, 16), 1, border_radius=3)
        put(surf, F["small"], t, (tx + 3, y + 2), ORANGE)
        tx += w_
    if tags:
        y += 22
    facs = S.get("facs") or []
    if facs and y < H - 36:
        pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 3
        put(surf, F["small"], "FACCIONES DEL SISTEMA", (8, y), DIM); y += 15
        for name, infl, st_, rep in facs:
            if y > H - 18:
                break
            put(surf, F["small"], name, (8, y), ORANGE if name == fac else WHITE, 200)
            bx = pygame.Rect(212, y + 1, 100, 10)
            pygame.draw.rect(surf, DIM, bx, 1)
            pygame.draw.rect(surf, BLUE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(100, infl) / 100), bx.h - 4))
            put(surf, F["small"], f"{infl:.0f}%", (346, y), WHITE, anchor="topright")
            put(surf, F["small"], st_ or "", (352, y), RED if st_ in ("GUERRA", "GUERRA CIVIL", "BLOQUEO") else DIM, 80)
            if rep is not None:
                put(surf, F["small"], f"{rep:+.0f}", (W - 8, y), GREEN if rep >= 35 else RED if rep <= -35 else ORANGE, anchor="topright")
            y += 17

# ---------- 12.4 ajustes: salir, reiniciar, apagar, preferencias ----------
POWER = [("1", "SALIR"), ("2", "REINICIAR"), ("3", "APAGAR"), ("4", "PREFERENCIAS"), ("5", "VERSIONES"), ("6", "BORDES"), ("7", "ICONOS")]

# ---------- 11 sesion: recompensas pendientes de cobrar ----------
def view_session2(surf, d, flags, now):
    view_session(surf, d, flags, now)
    s_ = (d or {}).get("sess") or {}
    led = ((d or {}).get("footcz") or {}).get("led") or {}
    if led.get("cr"):
        b, rw = led.get("bonds") or [0, 0], led.get("bounties") or [0, 0]
        dd_ = int((time.time() - (d or {}).get("uncl_t0")) // 86400) if (d or {}).get("uncl_t0") else 0
        put(surf, F["small"], "SIN COBRAR (bonos + recompensas)" + (f"  ·  desde hace {dd_} días" if dd_ else ""),
            (8, H - 54), ORANGE if dd_ >= 2 else DIM)
        put(surf, F["big"], f"{crx(led['cr'])} cr", (8, H - 40), RED)
        put(surf, F["small"], f"{b[0]} bonos {crx(b[1])} cr  ·  {rw[0]} recompensas {crx(rw[1])} cr", (8, H - 16), DIM, 330)
    elif s_.get("pending"):
        put(surf, F["small"], "RECOMPENSAS SIN COBRAR", (8, H - 54), DIM)
        put(surf, F["big"], f"{cr(s_['pending'])} cr", (8, H - 40), RED)
        put(surf, F["small"], f"{s_.get('pending_n', 0)} derribos · cóbralas en una estación", (8, H - 16), DIM, 300)

# ---------- registro de combate (pantalla grande, tablero COMBATE) y escudos caidos ----------
def view_combatlog(surf, d, flags, now):
    C = (d or {}).get("combat") or {}
    y = TOP + 4
    sd = None if flags & 8 else C.get("sd")
    put(surf, F["small"], "ESCUDOS", (8, y + 6), DIM)
    if sd:
        el = int(now - sd)
        put(surf, F["big"], f"CAÍDOS  {el // 60:02d}:{el % 60:02d}", (80, y), RED if int(now * 2) % 2 else WHITE)
    else:
        put(surf, F["big"], "ACTIVOS" if flags & 8 else "SIN ESCUDOS", (80, y), BLUE if flags & 8 else DIM)
    car_ = (d or {}).get("career") or {}
    if car_.get("bonds") is not None:
        put(surf, F["small"], f"bonos {fnum(car_['bonds'], 0)}", (W - 8, y), BLUE, anchor="topright")
    if car_.get("bounties") is not None:
        put(surf, F["small"], f"recompensas {fnum(car_['bounties'], 0)}", (W - 8, y + 15), ORANGE, anchor="topright")
    y += 32
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
    kills = C.get("kills") or []
    put(surf, F["small"], "ÚLTIMOS DERRIBOS", (8, y), DIM); y += 16
    if not kills:
        put(surf, F["small"], "ninguno en esta sesión", (8, y), DIM); y += 18
    for tgt, rew, kind in kills[:6]:
        tag, col = {"R": ("RECOMPENSA", ORANGE), "B": ("BONO", BLUE), "P": ("PvP", RED)}.get(kind, ("", DIM))
        put(surf, F["btn"], tgt, (8, y), WHITE, 230)
        put(surf, F["small"], tag, (250, y + 4), col)
        if rew:
            put(surf, F["btn"], f"+{cr(rew)}", (W - 8, y), GREEN, anchor="topright")
        y += 22
    bonds = C.get("bonds") or []
    if bonds and y < H - 60:
        pygame.draw.line(surf, DIM, (8, y + 2), (W - 8, y + 2)); y += 6
        put(surf, F["small"], "BONOS DE GUERRA POR FACCIÓN", (8, y), DIM); y += 16
        for fac, v in bonds:
            if y > H - 38:
                break
            put(surf, F["small"], fac, (8, y), BLUE, 300)
            put(surf, F["btn"], f"{cr(v)} cr", (W - 8, y - 3), BLUE, anchor="topright"); y += 18
    s_ = (d or {}).get("sess") or {}
    if s_.get("pending"):
        put(surf, F["small"], f"RECOMPENSAS SIN COBRAR: {cr(s_['pending'])} cr ({s_.get('pending_n', 0)})", (8, H - 16), RED, W - 16)

def view_combatx(surf, d, flags, now):
    view_combat(surf, d, flags, now)
    sd = None if flags & 8 else ((d or {}).get("combat") or {}).get("sd")
    if sd:
        el = int(now - sd)
        r = pygame.Rect(W - 190, TOP + 34, 182, 22)
        pygame.draw.rect(surf, BLACK, r)
        pygame.draw.rect(surf, RED, r, 2, border_radius=4)
        put(surf, F["btn"], f"ESCUDOS  {el // 60:02d}:{el % 60:02d}", r.center, RED if int(now * 2) % 2 else WHITE, anchor="center")

# ---------- 12.4.5 versiones: resumen de cambios ----------
CHANGES = [
    ("base", "Panel de 12 botones, teclado USB y estado del juego por red"),
    ("base", "7.3 Exobiología: muestras, distancia, valor de especies y x5"),
    ("base", "Recogida de combustible en naranja y sobrecalentamiento"),
    ("base", "Brújula para volver a la nave"),
    ("base", "EN VIVO como inicio (nave/a pie/SRV) con botón MENÚ"),
    ("base", "7.1 Exploración con EDSM y páginas"),
    ("base", "Avisos: combustible en ruta, neutrones y gravedad"),
    ("base", "12.5 Materiales, 12.6 Portanaves y 12.7 Mercado"),
    ("0.10", "Versión en la pantalla del reloj"),
    ("0.11", "12.8 Notas de viaje con brújula al destino"),
    ("0.12", "Foto del CMDR en reloj y arranque"),
    ("0.13", "Estilo CABINA (botón ESTILO en Sesión)"),
    ("0.14", "Botón ESTILO más grande"),
    ("0.15", "Pantalla grande HDMI: tablero de 4 cuadros"),
    ("0.16", "Viaje con SISTEMA y Combate con PIPS"),
    ("0.17", "Aproximación/Superficie y 7.4 Yacimientos"),
    ("0.18", "Tablero especial con el Rhino"),
    ("0.19", "Bodega del vehículo"),
    ("0.20", "Ficha del destino en Navegación"),
    ("0.21", "Altitud para desplegar el Rhino"),
    ("0.22", "RHINO en la pantalla 5"),
    ("0.23", "Pantalla 5: SRV / RHINO / A PIE"),
    ("0.24", "Lista de minerales de la bodega del Rhino"),
    ("0.25", "Combustible y escudos del Rhino"),
    ("0.26", "Superficie con Materiales y Minería"),
    ("0.27", "Minería en modo Rhino"),
    ("0.28", "Avisos de nave (el juego no los registra)"),
    ("0.29", "RHINO A BORDO"),
    ("0.30", "Franja RHINO PREPARADO"),
    ("0.31", "Franja de altura: 100-41 / 40-7 / <7 m"),
    ("0.32", "Brújula a puertos planetarios"),
    ("0.33", "Tablero ATRAQUE con la plataforma"),
    ("0.34", "Navegación: cara SISTEMA (política)"),
    ("0.35", "Estación: ficha y facciones a los 15 s"),
    ("0.36", "12.4 Salir, reiniciar y apagar"),
    ("0.37", "Navegación: cara POWERPLAY"),
    ("0.38", "Grande: 10 s sistema y 5 s Powerplay"),
    ("0.39", "Estación alterna ficha y Powerplay"),
    ("0.40", "Hallazgos, Códice, buscados, misiones, fin de sesión"),
    ("0.41", "A pie: peligros, mochila, asentamientos, delitos, taxi"),
    ("0.42", "Combate: escudos, derribos, bonos, rebuy, PvP"),
    ("0.43", "Ficha de llegada y sistema sin explorar"),
    ("0.44", "Esta lista de versiones"),
    ("0.45", "Estilo CABINA también en la pantalla grande"),
    ("0.46", "Bordes de situación por riesgo y botón BORDES"),
    ("0.47", "IP de la Pi en la pantalla del reloj"),
    ("0.48", "Brújula NAVE: corrección automática y botón NAVE AQUÍ"),
    ("0.49", "Menú principal con iconos (botón ICONOS)"),
    ("0.50", "Exploración: escaneo, ruta, diario 7.5, riesgo y distancias"),
    ("0.51", "7.6 Alienígenas: thargoides y guardianes, señales y guerra"),
    ("0.52", "Amigos y ala: avisos y cara AMIGOS en Sesión"),
    ("0.53", "12.9 GALNET: noticias oficiales y aviso de noticia nueva"),
    ("0.54", "Reloj: foto arriba y noticias GALNET subiendo"),
    ("0.55", "Pantalla grande ATRACADO: GALNET y carga/misión; fecha del juego"),
    ("0.56", "12.10 Objetivos comunitarios (web y los tuyos)"),
    ("0.57", "SALIR: shell en la HDMI y aviso en la pequeña"),
    ("0.58", "12 AJUSTES a la vista, pestañas de información y engranaje"),
    ("0.59", "Optimización de pantallas y aviso de BAJA TENSIÓN"),
    ("0.60", "Datos comprimidos, registro de errores, arranque y aviso thargoide"),
    ("0.61", "Pantalla grande: cuadros a todo lo ancho, texto más grande"),
    ("0.62", "Pantalla grande: modos 4 CUADROS, MIXTO y GRANDE (AJUSTES)"),
    ("0.63", "EMITIR pantallas por la red (PC, OBS, VR) y VOZ de la nave"),
    ("0.64", "Voz y pitidos en el PC: página /voz y en EMITIR"),
    ("0.65", "MANUAL de uso en AJUSTES y en http://IP:8080/manual"),
    ("0.66", "Bajas a pie y derribos con contador, bonos sin cobrar, zona de combate y luces del atraque"),
    ("0.67", "EN COMBATE a pie (grande en 2 cuadros) y salud baja al 75/50/25 %"),
    ("0.68", "MAPA de recorrido a pie, SRV y Rhino"),
    ("0.69", "Botiquines y células en avisos y MAPA, MARCAR RECARGA, HAS CAÍDO y COBRADO"),
    ("0.70", "Ratón y teclado; la HDMI puede mostrar el PANEL (TAB o clic derecho)"),
    ("0.71", "Llegada y señales, OPERATIONS, Merc Coin, copiloto, SISTEMA grande y clic desde el PC"),
    ("0.72", "NITIDEZ ALTA: pantalla grande a 1024x600 real (AJUSTES > PANTALLA)"),
    ("0.73", "ALERTAS y CAMBIO AUTO uno a uno (OPCIONES); NITIDEZ ALTA por defecto"),
    ("0.74", "Merc Coin rosa, PANEL nítido, teclas en la web, FPS, fecha del juego, plataforma exacta"),
    ("0.75", "SONIDO Y VOZ uno a uno (bajas en silencio); te atacan a pie > EN VIVO; mapa ZONA"),
    ("0.76", "Mapa a pie sin el vuelo del transporte, leyenda de símbolos y más zoom en ZONA"),
    ("0.77", "Teclas del juego (.binds), indicador de CPU/temperatura/FPS y modo PANEL ligero"),
    ("0.78", "Arreglo: el mapa a pie vuelve a dibujar el recorrido"),
    ("0.79", "Enlace energético: parado 8 s = RECARGANDO y punto de recarga en el mapa"),
    ("0.80", "Menú principal, música de combate y thargoide, Powerplay y ficha ESCUADRÓN"),
    ("0.81", "Inara (solo lectura): nombre de tu rango de escuadrón y otros CMDR en ESCUADRÓN"),
    ("0.82", "ESCUADRÓN por páginas: hasta 30 comandantes, conectados primero"),
    ("0.83", "Botiquines, células y explosivos (máximo por traje) siempre a la vista; EN COMBATE en grande"),
    ("0.84", "Cierre de emergencia del juego, ESCUADRÓN en AMIGOS, MENÚ PRINCIPAL en verde y arreglos"),
    ("0.85", "Cierre de emergencia: zona más grande en la barra de arriba y aviso de toques 1/3, 2/3"),
    ("0.86", "Salud < 30 %: pantalla roja; cierre en 3 s; copiloto en azul; arreglo del falso MENÚ PRINCIPAL al morir"),
    ("0.87", "Objetivos CERRADOS, bajas en un cuadro, combate de nave manda, Inara del CMDR fijado, EDSM y arreglos"),
    ("0.88", "Fichas NAVE y FLOTA, nave nueva a pantalla completa, transferencias, módulos dañados, SRV y caza"),
    ("0.89", "Transporte reservado y a bordo, totales de carrera, destello de luces, nave en la carga de Operations"),
    ("0.90", "Línea de saltos, fondos de portanaves, portanaves de escuadrón y arreglos"),
    ("0.90c", "Neutrones sin modo combate y foto del portanaves en la ruta"),
    ("0.91", "Fotos de fondo de cada tipo de estación al pedir atraque"),
    ("0.92", "TE ESCANEAN, SALUDOS, mega nave 15:00, datos del portanaves y fotos en ruta y atracado"),
    ("0.93", "Mercado de la estación donde estás, fotos de naves, facción del destino, transporte 5:20 / 6:00"),
    ("0.94", "Resumen del día, nombres de amigos, fotos de naves de CMDR, misiones primero y BATALLA TERMINADA"),
    ("0.95", "Bajas a pie / nave, registro de combate en la mega nave y nave de investigación"),
    ("0.96", "Versión del sender, foto del objetivo, sin cobrar, ingenieros, combustible, minería, Powerplay y rapidez"),
    ("0.97", "Misiones fijas en la pantalla grande y los 38 ingenieros con su ficha"),
    ("0.97b", "Ficha del ingeniero en NAVEGACIÓN y EXOBIOLOGÍA"),
    ("0.97c", "BASE DE INGENIERO solo en las bases de verdad"),
    ("0.98", "Pantalla HDMI táctil: PANEL o 4 CUADROS"),
    ("0.98b", "La HDMI táctil siempre responde; toques al LOG"),
    ("0.99", "Voz con Piper y COMBATE solo con las armas sacadas"),
    ("0.99b", "Nave fijada sin armas: ficha OBJETIVO en la pantalla grande"),
    ("0.99c", "Fotos de los cazas"),
    ("0.99d", "Fotos de los depósitos de construcción y fotos mejores"),
    ("0.99e", "Sin los toques de prueba en el LOG"),
    ("0.99f", "MINERÍA: barra de bodega, toneladas/hora sin tapar y en el cuadro 3 al minar"),
    ("1.1.6", "ROBOT a pie: cara verde; roja con salud < 50 % o poco oxígeno; azul con frío y naranja con calor"),
    ("1.1.5", "ROBOT: cara amarilla y % de combustible mientras recoges de una estrella"),
    ("1.1.4b", "ROBOT: las naves sin escudo ya no dan ESCUDOS CAÍDOS"),
    ("1.1.4", "ROBOT: peligro continuo (escudos caídos o casco < 70 %): rojo y cara enfadada hasta que pasa"),
    ("1.1.3", "ROBOT: la StackChan enseña la foto de la estación al atracar, tu nave al cambiarla y el logo de CDSN"),
    ("1.1.2", "12 AJUSTES > ROBOT: la StackChan de M5Stack reacciona a los avisos sin necesitar EMITIR"),
    ("1.1.1", "RUTA desplazable con marcas, hora y combustible de llegada; pestaña BGS; INFLUENCIA; dónde comprar hoy; más rápido"),
    ("1.1", "Código depurado y en partes; pasajeros, calculadora, tick de cada sistema, reloj LCD, avisos de colonización"),
    ("1.0b20", "4 CUADROS al cargar la partida y subir_todo.sh"),
    ("1.0b19b", "Arreglo del RADAR al arrastrar"),
    ("1.0b19", "Voz con abreviaturas, velocímetro (nave, SRV y Rhino), aviso de suelo, caja negra, repetidos"),
    ("1.0b18", "ACTIVIDAD con fondo nuevo y GALAXIA/COLONIA/SOL, controlados con el dedo, COMBATE al despegar, BORRAR recompensas"),
    ("1.0b17b", "Cronómetro de salida en 5:00"),
    ("1.0b17", "Fondo del atraque más claro, COMBATE no se abre al despegar, avisos de materiales de colonización"),
    ("1.0b16b", "Arreglo del error en MERCADO"),
    ("1.0b16", "EMITIR sin subir la memoria, atraque 9:59, salida abajo, altímetro de cinta"),
    ("1.0b15", "Relojes de lamas (atraque y salida), salida de la estación, ALERTAS del radar, avisos de expansión y control, AQUÍ arreglado"),
    ("1.0b14", "Aviso de compra para tu construcción, EN EL SISTEMA sin solapes y con datos antiguos, nombre de la nave en azul"),
    ("1.0b13", "COLONIZACIÓN: bodega, filtros TODO / AQUÍ / EN EL SISTEMA, aviso de carga por entregar"),
    ("1.0b12c", "Modo COLONIZACIÓN en 4 CUADROS"),
    ("1.0b12b", "COLONIZACIÓN ya no la tapa ESTACIÓN al atracar"),
    ("1.0b12", "COLONIZACIÓN se abre sola; expansión probable en la ficha; números en ALERTAS"),
    ("1.0b11", "Radar con tick, tráfico, expansión y zoom; COLONIA; + en VIAJES; número de aviso"),
    ("1.0b10c", "FLUJO DATOS EDDN en AJUSTES > OPCIONES, con la última subida a GitHub"),
    ("1.0b10b", "Menú 7: el botón < MENÚ vuelve a funcionar"),
    ("1.0b10", "Logos en FIJAR, RADAR y ACTIVIDAD en el menú 7, avisos de influencia, IR, estado del pueblo y hora"),
    ("1.0b9", "Botón FIJAR en la pantalla de espera"),
    ("1.0b8", "Facción sin datos de la Pi; prueba de ACTIVIDAD GALÁCTICA en directo"),
    ("1.0b7", "Pantalla de espera de la facción con logo, radar y alertas"),
    ("1.0b6b", "Textos que se montaban con NITIDEZ ALTA"),
    ("1.0b6", "Actividad de la facción: tráfico, zonas de conflicto, portanaves, Powerplay cercano, aviso de guerra"),
    ("1.0b5", "Menú 9 FACCIÓN, ficha de cada sistema de la facción, espera más legible"),
    ("1.0b4", "Pestañas de combate, zoom en VIAJES, tick EDCAS, alertas que caben, MI FACCIÓN"),
    ("1.0b3", "VIAJES, COMBATE + CAZA, tick del BGS, teclas por red sin USB"),
    ("1.0b2", "Borde por fuera en la HDMI; botones en 4 CUADROS; MHz"),
    ("1.0b1", "Foto destino grande, voz créditos, avatar Inara, RAM/MHz, avisos reloj y SD"),
    ("0.99k", "Vigilante: si se congela, LOG y reinicio solo"),
    ("0.99j", "MEGA NAVE a mano: tocar el cuadro empieza los 15:00"),
    ("0.99g", "Solo pantalla de 10\": táctil HDMI sin la pequeña de 3.5\""),
    ("0.99i", "Mega nave: cuenta atrás con la hora del PC"),
    ("0.99h", "Cierre de emergencia: IP del PC fija opcional en pc_ip.txt"),
]

def view_changelog_base(surf, d, flags, now):
    per = 11
    rows = list(reversed(CHANGES))
    pages = max(1, (len(rows) + per - 1) // per)
    pg = ui.get("page1245", 0) % pages
    y = TOP + 4
    put(surf, F["small"], f"{len(CHANGES)} cambios  ·  lo más nuevo primero", (8, y), DIM)
    put(surf, F["small"], f"pág {pg + 1}/{pages}  (toca)", (W - 8, y), DIM, anchor="topright")
    y += 18
    for ver, txt in rows[pg * per:(pg + 1) * per]:
        put(surf, F["small"], "v" + ver if ver != "base" else "base", (8, y + 2), GREEN if ver != "base" else DIM)
        put(surf, F["btn"], txt, (62, y), ORANGE, W - 70)
        y += 22

# ---------- menu principal con iconos (12.4 -> 7 ICONOS) ----------
ICONS_FILE = os.path.join(PANEL_DIR, "iconos.txt")
try:
    ICONS_ON = [open(ICONS_FILE).read().strip() == "si"]
except OSError:
    ICONS_ON = [False]

def icons_toggle():
    ICONS_ON[0] = not ICONS_ON[0]
    try:
        with open(ICONS_FILE, "w") as f:
            f.write("si" if ICONS_ON[0] else "no")
    except OSError:
        pass

def menu_icon(s, i, c, cx, cy):
    L = lambda a, b, w=2: pygame.draw.line(s, c, a, b, w)
    C = lambda p_, r, w=2: pygame.draw.circle(s, c, p_, r, w)
    R = lambda x, y, w, h, wd=2: pygame.draw.rect(s, c, (cx + x, cy + y, w, h), wd)
    if i == 0:
        R(-12, 6, 24, 6); L((cx, cy + 6), (cx, cy - 8), 3); C((cx, cy - 11), 5, 0)
    elif i == 1:
        for j, h in enumerate((10, 16, 8)):
            R(-13 + j * 10, 10 - h, 7, h, 0)
    elif i == 2:
        C((cx, cy), 13); pygame.draw.polygon(s, c, [(cx, cy - 11), (cx + 4, cy), (cx, cy + 11), (cx - 4, cy)], 0)
    elif i == 3:
        R(-12, -9, 24, 18); L((cx - 12, cy - 3), (cx + 12, cy - 3)); L((cx, cy - 9), (cx, cy - 3))
    elif i == 4:
        R(-14, -6, 28, 9); C((cx - 8, cy + 7), 4); C((cx + 8, cy + 7), 4)
    elif i == 5:
        C((cx, cy), 11); L((cx - 15, cy), (cx - 5, cy)); L((cx + 5, cy), (cx + 15, cy))
        L((cx, cy - 15), (cx, cy - 5)); L((cx, cy + 5), (cx, cy + 15))
    elif i == 6:
        C((cx, cy), 8, 0); pygame.draw.ellipse(s, c, (cx - 16, cy - 4, 32, 8), 2)
    elif i == 7:
        pygame.draw.polygon(s, c, [(cx, cy - 13), (cx + 13, cy), (cx, cy + 13), (cx - 13, cy)], 2); R(-5, -2, 10, 4, 0)
    elif i == 8:
        pygame.draw.polygon(s, c, [(cx, cy - 12), (cx + 11, cy + 10), (cx, cy + 5), (cx - 11, cy + 10)], 2)
    elif i == 9:
        pygame.draw.polygon(s, c, [(cx - 12, cy + 2), (cx - 5, cy - 9), (cx + 6, cy - 7), (cx + 12, cy + 3),
                                   (cx + 3, cy + 11), (cx - 8, cy + 9)], 2); L((cx - 3, cy - 1), (cx + 4, cy + 4))
    elif i == 10:
        C((cx, cy), 12); L((cx, cy), (cx, cy - 8)); L((cx, cy), (cx + 6, cy + 3))
    elif i == 11:
        C((cx, cy), 6)
        for a in range(8):
            r = math.radians(a * 45)
            L((cx + 9 * math.cos(r), cy + 9 * math.sin(r)), (cx + 13 * math.cos(r), cy + 13 * math.sin(r)), 3)

def view_menux(surf, d, flags, now):
    if not ICONS_ON[0]:
        return view_menu(surf, d, flags, now)
    for i in range(12):
        name = MENU.get(i + 1)
        r = grid(i)
        draw_button(surf, r, "", None, F["small"], lit=flash.get((0, i), 0) > now, dim=name is None)
        col = DIM if name is None else ORANGE
        menu_icon(surf, i, col, r.centerx, r.y + int(r.h * 0.38))
        put(surf, F["small"], f"{i + 1} {name or 'vacío'}", (r.centerx, r.bottom - 18), col, r.w - 8, anchor="midtop")

# ---------- 7.5 diario de exploracion ----------
def view_diary(surf, d, flags, now):
    X = (d or {}).get("exdiary") or {}
    y = TOP + 6
    secs = int(now - (X.get("start") or now))
    put(surf, F["small"], f"SESIÓN DE EXPLORACIÓN · {secs // 3600}h {secs % 3600 // 60:02d}m", (8, y), DIM); y += 18
    rows = [("SISTEMAS VISITADOS", X.get("systems", 0), WHITE), ("AÑOS LUZ", X.get("ly", 0), WHITE),
            ("CUERPOS ESCANEADOS", X.get("scanned", 0), WHITE), ("1º DESCUBRIMIENTOS", X.get("first", 0), GREEN),
            ("CUERPOS MAPEADOS", X.get("mapped", 0), WHITE), ("1º MAPEADOS", X.get("first_mapped", 0), GREEN),
            ("MUESTRAS BIO", X.get("bio", 0), WHITE), ("SEÑALES VISITADAS", X.get("signals", 0), WHITE)]
    for k, (lab, val, col) in enumerate(rows):
        x0 = 8 if k % 2 == 0 else W // 2 + 4
        put(surf, F["small"], lab, (x0, y + 5), DIM)
        put(surf, F["big"], f"{val:,}".replace(",", "."), (x0 + W // 2 - 20, y), col, anchor="topright")
        if k % 2 == 1:
            y += 28
    y += 30
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 6
    tot = (X.get("unsold") or 0) + (X.get("unsold_bio") or 0)
    put(surf, F["small"], "SIN VENDER (exploración + bio)", (8, y + 6), DIM)
    put(surf, F["big"], f"{cr(tot)} cr", (W - 8, y), RED if tot >= 50e6 else ORANGE, anchor="topright"); y += 32
    if X.get("dsol") is not None:
        put(surf, F["small"], "DISTANCIA A SOL", (8, y + 4), DIM)
        put(surf, F["btn"], f"{X['dsol']:,.0f} al".replace(",", "."), (W - 8, y), BLUE, anchor="topright"); y += 22
    if X.get("dst") is not None:
        put(surf, F["small"], f"A LA ÚLTIMA ESTACIÓN ({X.get('stname') or '?'})", (8, y + 4), DIM, 330)
        put(surf, F["btn"], f"{X['dst']:,.0f} al".replace(",", "."), (W - 8, y), BLUE, anchor="topright")

# ---------- 7.6 alienigenas: thargoides y guardianes (toca para cambiar) ----------
TGCOL = (120, 230, 120)

def view_alien(surf, d, flags, now):
    A = (d or {}).get("alien") or {}
    tab = ui.get("alientab", 0)
    for i, t in enumerate(("THARGOIDES", "GUARDIANES")):
        r = pygame.Rect(4 + i * (W // 2), TOP + 2, W // 2 - 8, 26)
        on = tab == i
        pygame.draw.rect(surf, (TGCOL if i == 0 else BLUE) if on else DIM, r, 0 if on else 1, border_radius=4)
        put(surf, F["btn"], t, r.center, BLACK if on else DIM, anchor="center")
    y = TOP + 36
    if tab == 0:
        w = A.get("tgwar")
        if w:
            put(surf, F["small"], "GUERRA EN EL SISTEMA", (8, y + 4), DIM)
            put(surf, F["big"], w["state"], (180, y), RED if w["state"] in ("INVASIÓN", "CONTROLADO", "BASTIÓN") else ORANGE)
            y += 28
            pr = w.get("progress")
            if pr is not None:
                bx = pygame.Rect(8, y, W - 90, 14)
                pygame.draw.rect(surf, DIM, bx, 1)
                pygame.draw.rect(surf, TGCOL, (bx.x + 2, bx.y + 2, int((bx.w - 4) * max(0, min(1, pr))), bx.h - 4))
                put(surf, F["btn"], f"{pr * 100:.0f}%", (W - 8, y - 4), WHITE, anchor="topright"); y += 20
            extra = " · ".join(x for x in (f"puertos restantes {w['ports']}" if w.get("ports") else "", str(w.get("time") or "")) if x)
            if extra:
                put(surf, F["small"], extra, (8, y), DIM, W - 16); y += 18
        else:
            put(surf, F["btn"], "Sistema sin guerra thargoide", (8, y), GREEN); y += 26
        put(surf, F["small"], "DERRIBOS THARGOIDES (sesión)", (8, y + 4), DIM)
        put(surf, F["btn"], f"{A.get('tgk', 0)}  ·  {cr(A.get('tgb', 0))} cr", (W - 8, y), TGCOL, anchor="topright"); y += 26
        rows = A.get("tg") or []
        title, col = "MATERIALES THARGOIDES", TGCOL
    else:
        bp = A.get("bp") or {}
        put(surf, F["small"], "PLANOS GUARDIANES", (8, y), DIM); y += 16
        for k, (lab, key) in enumerate((("MÓDULO", "module"), ("ARMA", "weapon"), ("NAVE", "vessel"))):
            x0 = 8 + k * (W // 3)
            put(surf, F["small"], lab, (x0, y + 6), DIM)
            put(surf, F["big"], str(bp.get(key, 0)), (x0 + W // 3 - 30, y), BLUE, anchor="topright")
        y += 32
        rows = A.get("gd") or []
        title, col = "MATERIALES Y DATOS GUARDIANES", BLUE
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
    put(surf, F["small"], title, (8, y), DIM); y += 16
    if not rows:
        put(surf, F["small"], "ninguno", (8, y), DIM)
    for k, (n, c) in enumerate(rows):
        cx, cy = (8 if k % 2 == 0 else W // 2 + 4), y + (k // 2) * 18
        if cy > H - 18:
            break
        put(surf, F["small"], n, (cx, cy), WHITE, W // 2 - 50)
        put(surf, F["small"], str(c), (cx + W // 2 - 14, cy), col, anchor="topright")

# ---------- 11 sesion: cara AMIGOS (toca para cambiar) ----------
def view_friends(surf, d, flags, now):
    Fr = (d or {}).get("friends") or {}
    on, off, wg = Fr.get("on") or [], Fr.get("off") or [], Fr.get("wing") or []
    y = TOP + 4
    put(surf, F["small"], f"AMIGOS CONECTADOS ({len(on)})", (8, y), DIM)
    put(surf, F["small"], "toca para volver a SESIÓN", (W - 8, y), DIM, anchor="topright"); y += 16
    draw_button(surf, SQ_BTN, "ESCUADRÓN  >", None, F["btn"], lit=flash.get(("sqbtn",), 0) > now)
    if not on:
        put(surf, F["btn"], "ninguno", (8, y), DIM); y += 24
    for k, n in enumerate(on[:10]):
        cx, cy = (8 if k % 2 == 0 else W // 2 + 4), y + (k // 2) * 22
        pygame.draw.circle(surf, GREEN, (cx + 5, cy + 8), 4)
        put(surf, F["btn"], n, (cx + 14, cy), GREEN, W // 2 - 26)
    y += ((min(len(on), 10) + 1) // 2) * 22 + 6
    if wg:
        pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
        put(surf, F["small"], "TU ALA", (8, y), DIM); y += 16
        put(surf, F["btn"], "  ·  ".join(wg), (8, y), BLUE, W - 16); y += 26
    if off and y < H - 40:
        pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
        put(surf, F["small"], "DESCONECTADOS HACE POCO", (8, y), DIM); y += 16
        for n, mins in off:
            if y > H - 40:
                break
            put(surf, F["small"], n, (8, y), WHITE, 300)
            put(surf, F["small"], f"hace {mins} min" if mins < 60 else f"hace {mins // 60} h", (W - 8, y), DIM, anchor="topright")
            y += 17

def view_session3(surf, d, flags, now):
    if ui.get("sesstab"):
        return view_friends(surf, d, flags, now)
    view_session2(surf, d, flags, now)
    n = len(((d or {}).get("friends") or {}).get("on") or [])
    paid_ = (((d or {}).get("ops") or {}).get("crew") or {}).get("paid")
    on_ = ((d or {}).get("friends") or {}).get("on") or []
    put(surf, F["small"], (f"AMIGOS ({n}): " + ", ".join(on_) if on_ else "toca para ver AMIGOS (0 conectados)")
        + (f"  ·  copiloto -{crx(paid_)} cr" if paid_ else ""),
        (8, 252), GREEN if n else DIM, W - 16)

def view_sub124_base(surf, d, flags, now):
    c, until = ui["confirm"]
    for i, (n, name) in enumerate(POWER):
        sure = c == ("pw", i) and time.time() < until
        draw_button(surf, grid(i, 4, 2), n, "¿SEGURO?" if sure else (f"BORDES {'SÍ' if style.get('borders', True) else 'NO'}" if i == 5 else f"ICONOS {'SÍ' if ICONS_ON[0] else 'NO'}" if i == 6 else name), F["num"], filled=sure,
                    lit=flash.get((1240, i), 0) > now)

def power_tap(i):
    import subprocess
    if i == 3:
        ui["view"] = 1244; return
    if i == 4:
        ui["view"] = 1245; return
    if i == 5:
        borders_toggle(); return
    if i == 6:
        icons_toggle(); return
    c, until = ui["confirm"]
    if c != ("pw", i) or time.time() > until:
        ui["confirm"] = (("pw", i), time.time() + 3); return
    ui["confirm"] = (None, 0)
    tap_flash((1240, i))
    cmd = [["systemctl", "stop", "elite-panel"], ["systemctl", "reboot"], ["systemctl", "poweroff"]][i]
    ui["bye"] = time.time()                              # pantalla en negro mientras suena la despedida
    threading.Thread(target=_power_go, args=(i, cmd), daemon=True).start()

def _power_go(i, cmd):
    play_inicio(wait=True)
    if i == 0:
        ui["bye"] = time.time()
        sh = ("sleep 1; systemctl stop elite-panel; con2fbmap 1 0; "
              "cat /dev/zero > /dev/fb0 2>/dev/null; chvt 2; chvt 1; setterm --blank 0 --cursor on > /dev/tty1")
        subprocess.Popen(["sudo", "-n", "systemd-run", "--no-block", "--collect", "sh", "-c", sh])
        return
    subprocess.Popen(["sudo", "-n"] + cmd)


# ---------- 12.3 rangos ----------
RANK_NAMES = {
    "Combat": ["Harmless", "Mostly Harmless", "Novice", "Competent", "Expert", "Master", "Dangerous", "Deadly", "Elite"],
    "Trade": ["Penniless", "Mostly Penniless", "Peddler", "Dealer", "Merchant", "Broker", "Entrepreneur", "Tycoon", "Elite"],
    "Explore": ["Aimless", "Mostly Aimless", "Scout", "Surveyor", "Trailblazer", "Pathfinder", "Ranger", "Pioneer", "Elite"],
    "Soldier": ["Defenceless", "Mostly Defenceless", "Rookie", "Soldier", "Gunslinger", "Warrior", "Gladiator", "Deadeye", "Elite"],
    "Exobiologist": ["Directionless", "Mostly Directionless", "Compiler", "Collector", "Cataloguer", "Taxonomist",
                     "Ecologist", "Geneticist", "Elite"],
    "Federation": ["None", "Recruit", "Cadet", "Midshipman", "Petty Officer", "Chief Petty Officer", "Warrant Officer",
                   "Ensign", "Lieutenant", "Lt. Commander", "Post Commander", "Post Captain", "Rear Admiral",
                   "Vice Admiral", "Admiral"],
    "Empire": ["None", "Outsider", "Serf", "Master", "Squire", "Knight", "Lord", "Baron", "Viscount", "Count", "Earl",
               "Marquis", "Duke", "Prince", "King"]}
RANK_ROWS = [("COMBATE", "Combat"), ("COMERCIO", "Trade"), ("EXPLORACIÓN", "Explore"), ("MERCENARIO", "Soldier"),
             ("EXOBIOLOGÍA", "Exobiologist"), ("FEDERACIÓN", "Federation"), ("IMPERIO", "Empire")]

def rank_name(key, n):
    names = RANK_NAMES[key]
    if n is None: return "?"
    if n < len(names): return names[n]
    return f"Elite {['I', 'II', 'III', 'IV', 'V'][min(4, n - len(names))]}"

def view_ranks(surf, d, flags, now):
    r = (d or {}).get("ranks") or {}
    rank, prog = r.get("rank") or {}, r.get("progress") or {}
    put(surf, F["small"], "CMDR " + ((r.get("cmdr") or cfg["cmdr"]).upper()), (W - 8, TOP + 4), DIM, anchor="topright")
    if not rank:
        put(surf, F["btn"], "Sin datos de rangos (carga la partida)", (W // 2, (H + TOP) // 2), DIM, anchor="center")
        return
    y = TOP + 18
    for label, key in RANK_ROWS:
        n, p_ = rank.get(key), prog.get(key, 0)
        put(surf, F["small"], label, (8, y + 4), DIM)
        put(surf, F["btn"], rank_name(key, n).upper(), (118, y), ORANGE, 210)
        bx = pygame.Rect(330, y + 3, 110, 12)
        pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, BLUE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(p_ or 0, 100) / 100), bx.h - 4))
        put(surf, F["small"], f"{p_ or 0}%", (W - 6, y + 3), WHITE, anchor="topright")
        y += 31
    car_ = (d or {}).get("career") or {}
    if any(car_.get(k) is not None for k in ("foot", "bonds", "bounties")):
        pygame.draw.line(surf, DIM, (8, H - 26), (W - 8, H - 26))
        x_ = 8
        for k, lab, col in (("foot", "bajas a pie", GREEN), ("bonds", "bonos nave", BLUE), ("bounties", "recompensas", ORANGE)):
            if car_.get(k) is None:
                continue
            x_ += put(surf, F["btn"], fnum(car_[k], 0), (x_, H - 22), col)
            x_ += put(surf, F["small"], " " + lab, (x_, H - 18), DIM) + 14

