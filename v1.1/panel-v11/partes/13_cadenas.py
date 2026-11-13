# Panel Elite v1.1 · parte 13: cadenas (lineas 10806-12334 del panel entero)
# ========== carrier_kind: cadena de 2 etapas, cada una llama a la anterior ==========
# carrier_kind_base -> carrier_kind

def carrier_kind_base(d, st):
    stype = (st.get("type") or "")
    mid = st.get("mid")
    sq, own = d.get("sqcarrier") or {}, d.get("carrier") or {}
    if stype == "SurfaceStation" or (st.get("name") or "").startswith("$Operations"):
        return ("op", "PORTANAVES DE OPERACIONES", BLUE) if (d.get("ops") or {}).get("on") or \
            (st.get("name") or "").startswith("$Operations") else (None, "", None)
    if "squadron" in stype.lower() or (mid and mid == sq.get("id")):
        return "sq", "PORTANAVES DE ESCUADRÓN", BLUE
    if stype == "FleetCarrier":
        return "fc", ("TU PORTANAVES" if mid and mid == own.get("id") else "PORTANAVES"), ORANGE
    if stype in ST_BG:
        return ST_BG[stype], ST_TYPE.get(stype, stype).upper(), ORANGE
    return None, "", None

def carrier_kind(d, st):
    nm = ((st.get("name") or "") + " " + (st.get("sraw") or "")).lower()
    if st.get("type") == "SurfaceStation" and ("investig" in nm or "megaship" in nm):
        return "meganave", "NAVE DE INVESTIGACIÓN", ORANGE
    return carrier_kind_base(d, st)


# ========== col_pend: cadena de 2 etapas, cada una llama a la anterior ==========
# col_pend_base -> col_pend

def col_pend_base(now):
    p = COLB.get("pend")
    if p and now >= p[0]:
        COLB["pend"] = None
        ui["view"] = 135; ui["colsel"] = None; ui["colpg"] = 0
        COLB["hold"] = now + 8
        plog("Colonización: abro la pestaña (" + p[1] + ")")
    elif now < COLB.get("hold", 0) and ui.get("view") in (0, 8, 100, 126, 127) and not ui.get("idle_on"):
        ui["view"] = 135                                 # otro cambio automatico la ha quitado: vuelve
        plog("Colonización: vuelvo a la pestaña (la había tapado otro cambio automático)")

def col_pend(now):
    p = COLB.get("pend")
    col_pend_base(now)
    if p and now >= p[0] and "atracado" in p[1]:
        try:
            d = state.get("data")
            C, L, i = col_pick(d)
            if L:
                bod = sum(t[4] for t in col_rows(d, L[i]))
                if bod and ev_on("colentrega"):
                    k0 = XA_K[0]
                    try:
                        XA_K[0] = "colentrega"
                        set_alert(f"LLEVAS {bod:,} t PARA ESTA CONSTRUCCIÓN".replace(",", "."), "descárgalas aquí", BLUE, 8, kind="info")
                        play("ok")
                    finally:
                        XA_K[0] = k0
        except Exception as e:
            log_exc("colonia entrega", e)


# ========== combat_music_ok: cadena de 2 etapas, cada una llama a la anterior ==========
# combat_music_ok_base -> combat_music_ok

def combat_music_ok_base(text):
    d = state.get("data") or {}
    now = time.time()
    x = d.get("exitst") or {}
    if x.get("t0") and (not x.get("out") or pc_now(d, now) - x["t0"] < 60):
        return False, "dentro de la estación o recién despegado"
    st = d.get("station") or {}
    if st.get("status") in ("SOLICITADO", "CONCEDIDO", "ATRACADO") or d.get("Flags", 0) & 1:
        return False, "atracando o atracado"
    if text == "Combat_Unknown" and now - CMB["att"] > 60 and not d.get("Flags", 0) & (1 << 6):
        return False, "Combat_Unknown sin ataque ni armas fuera"
    return True, ""

def combat_music_ok(text):
    if time.time() - UNDK["t"] < 60:
        return False, "recién despegado"
    return combat_music_ok_base(text)


# ========== draw_alert: cadena de 2 etapas, cada una llama a la anterior ==========
# draw_alert_base -> draw_alert

def draw_alert_base(surf, now):
    a = ui["alert"]
    col = a["col"]
    on = int(now * 3) % 2 == 0 or a["kind"] != "red"
    for k in range(4 if on else 2):
        pygame.draw.rect(surf, col, (k * 3, k * 3, W - k * 6, H - k * 6), 2)
    box = pygame.Rect(30, 105, W - 60, 110)
    pygame.draw.rect(surf, BLACK, box)
    pygame.draw.rect(surf, col, box, 3, border_radius=8)
    if a["kind"] == "jump":
        for j in range(14):                       # estela de salto
            yy = box.y + 8 + ((j * 23 + int(now * 160)) % (box.h - 16))
            pygame.draw.line(surf, (40, 70, 130), (box.x + 10, yy), (box.x + 10 + (j * 37) % 120, yy))
            pygame.draw.line(surf, (40, 70, 130), (box.right - 10 - (j * 53) % 120, yy), (box.right - 10, yy))
    two_ = bool(a["sub"]) and len(wrap_lines(F["btn"], a["sub"], box.w - 20)) > 1
    put_fit(surf, ("num", "big", "btn", "small") if len(a["text"]) <= 16 else ("big", "btn", "small"), a["text"],
            (box.centerx, box.centery - (28 if two_ else 14 if a["sub"] else 0)), col if on else WHITE, box.w - 20, anchor="center")
    if a["sub"]:
        put_wrap(surf, a["sub"], (box.centerx, box.centery + (2 if two_ else 16)), WHITE, box.w - 20, 2)

def draw_alert(surf, now):
    draw_alert_base(surf, now)
    a = ui.get("alert")
    if a:
        draw_num(surf, pygame.Rect(30, 105, W - 60, 110), a.get("ev"))


# ========== draw_alt: cadena de 2 etapas, cada una llama a la anterior ==========
# draw_alt_base -> draw_alt

def draw_alt_base(surf, r, d, now, big=False):
    alt = alt_now(d)
    if alt is None:
        put(surf, F["btn"], "sin altura", (r.centerx, r.centery - 10), DIM, anchor="center")
        put(surf, F["small"], "aparece cerca de un planeta", (r.centerx, r.centery + 12), DIM, r.w - 10, anchor="center")
        return
    fl = (d or {}).get("Flags", 0)
    vs = alt_vs()
    tape = pygame.Rect(r.x + 8, r.y + 18, int(r.w * 0.52), r.h - 26)
    pygame.draw.rect(surf, (14, 14, 16), tape); pygame.draw.rect(surf, (80, 80, 86), tape, 1)
    span = 60 if alt < 200 else 600 if alt < 3000 else 6000 if alt < 30000 else 60000   # metros visibles
    step = span // 6
    ppm = tape.h / span
    mid = tape.centery
    old = surf.get_clip(); surf.set_clip(tape)
    m0 = int((alt - span) // (step / 5)) * (step / 5)
    k = 0
    m = m0
    while m < alt + span and k < 200:
        yy = mid - (m - alt) * ppm
        if m >= 0 and abs(round(m / step) * step - m) < 1e-6:
            pygame.draw.line(surf, WHITE, (tape.x, yy), (tape.x + 12, yy), 2)
            put(surf, F["small"], f"{int(m):,}".replace(",", "."), (tape.x + 16, int(yy) - 8), WHITE)
        elif m >= 0:
            pygame.draw.line(surf, (150, 150, 150), (tape.x, yy), (tape.x + 6, yy), 1)
        m += step / 5; k += 1
    gy = mid + alt * ppm                                  # el suelo
    if gy < tape.bottom:
        pygame.draw.rect(surf, (60, 35, 10), (tape.x, int(gy), tape.w, tape.bottom - int(gy)))
    surf.set_clip(old)
    put(surf, F["tiny"], "ALT" + (" (radio medio)" if fl & (1 << 29) else ""), (tape.x, r.y + 3), DIM)
    txt = f"{alt:,.0f} m".replace(",", ".") if alt < 100000 else f"{alt / 1000:,.0f} km".replace(",", ".")
    box = pygame.Rect(tape.x + tape.w * 2 // 5, mid - 15, tape.w * 3 // 5 + 26, 30)
    pts = [(box.x, mid), (box.x + 10, box.y), (box.right, box.y), (box.right, box.bottom), (box.x + 10, box.bottom)]
    pygame.draw.polygon(surf, BLACK, pts); pygame.draw.polygon(surf, ORANGE, pts, 2)
    put(surf, F["big"], txt, (box.centerx + 5, mid), ORANGE, box.w - 14, anchor="center")
    # velocidad vertical
    vsr = pygame.Rect(tape.right + 40, tape.y + 14, 28, tape.h - 44)
    pygame.draw.rect(surf, (14, 14, 16), vsr)
    pygame.draw.line(surf, DIM, (vsr.x, vsr.centery), (vsr.right, vsr.centery), 1)
    put(surf, F["tiny"], "VERT.", (vsr.centerx, vsr.y - 12), DIM, anchor="center")
    if vs is not None:
        lim = 200 if alt > 2000 else 50
        h_ = int(min(1.0, abs(vs) / lim) * (vsr.h // 2 - 2))
        col = BLUE if vs < 0 else GREEN
        if vs < 0:
            pygame.draw.rect(surf, col, (vsr.x + 4, vsr.centery, vsr.w - 8, h_))
        else:
            pygame.draw.rect(surf, col, (vsr.x + 4, vsr.centery - h_, vsr.w - 8, h_))
        warn = vs < -30 and alt < 300                     # bajando rapido muy cerca del suelo
        put(surf, F["btn"], f"{vs:+.0f}", (vsr.centerx, vsr.bottom + 12), RED if warn and int(now * 2) % 2 else col, anchor="center")
        put(surf, F["tiny"], "m/s", (vsr.centerx, vsr.bottom + 28), DIM, anchor="center")

def draw_alt(surf, r, d, now, big=False):
    if in_srv(d):                                         # SRV / Rhino: reloj de 0-40 m/s, km/h y brujula
        gs = SPD.get("gs")
        vm = SPD["vmax"].setdefault(srv_name(d), 40)
        if gs and gs > vm * 0.95:
            vm = SPD["vmax"][srv_name(d)] = int(math.ceil(gs * 1.2 / 10.0)) * 10
        R_ = min(r.h // 2 - 8, r.w // 4)
        draw_arc(surf, r.x + r.w // 4 + 4, r.centery, R_, gs, vm, 5 if vm <= 50 else 10,
                 [(0, vm * 0.62, GREEN), (vm * 0.62, vm * 0.85, ORANGE), (vm * 0.85, vm, RED)], srv_name(d), now)
        if gs is not None:
            put(surf, F["btn"], f"{gs * 3.6:.0f} km/h", (r.x + r.w // 4 + 4, r.bottom - 12), WHITE, anchor="center")
        draw_hdg_compass(surf, r.x + 3 * r.w // 4, r.centery - 6, min(r.h // 2 - 22, r.w // 5), _geo(d)[3])
        return
    draw_alt_base(surf, r, d, now, big)
    if alt_now(d) is None:
        return
    gs, vs = SPD.get("gs"), alt_vs()
    vm = ship_vmax(d)
    tape_r = int(r.w * 0.52) + 8
    cx = r.x + tape_r + 80 + (r.w - tape_r - 80) // 2
    R_ = min((r.w - tape_r - 90) // 2, r.h // 2 - 22)
    if R_ < 30:
        return
    draw_arc(surf, cx, r.y + 18 + R_, R_, gs, vm, 100 if vm <= 600 else 200,
             [(0, 100, GREEN), (100, vm * 0.66, ORANGE), (vm * 0.66, vm, RED)], "SUELO", now)
    if gs is not None and vs is not None:
        put(surf, F["small"], f"total {math.hypot(gs, vs):.0f} m/s", (cx, r.y + 18 + 2 * R_ + 18), WHITE, anchor="center")


# ========== draw_fac_screen: cadena de 3 etapas, cada una llama a la anterior ==========
# draw_fac_screen_base -> draw_fac_screen_2 -> draw_fac_screen

def draw_fac_screen_base(surf, now):
    D, S, gap = fac_rows()
    surf.fill(BLACK)
    for x in range(0, W, 24):
        pygame.draw.line(surf, (14, 9, 3), (x, 0), (x, H))
    for y in range(0, H, 24):
        pygame.draw.line(surf, (14, 9, 3), (0, y), (W, y))
    # cabecera
    if not blit_logo(surf, pygame.Rect(4, 2, 46, 46)):
        shield(surf, 26, 24, ORANGE)
    put(surf, F["big"], (D.get("faccion") or "").upper(), (56, 6), ORANGE, W - 170)
    nctl = sum(1 for v in S if v.get("ctrl"))
    med = sum(v["inf"] for v in S) / len(S)
    put(surf, F["small"], f"{nctl} sistemas controlados de {len(S)} · influencia media {med:.1f} %".replace(".", ","), (56, 32), DIM, W - 64)
    tmax = max([v.get("t") or 0 for v in S] or [0])
    a_txt, a_col = fac_age(tmax)
    put(surf, F["small"], "act. " + a_txt, (W - 72, 8), a_col, anchor="topright")
    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 72, 22), ORANGE, anchor="topright")
    pygame.draw.line(surf, ORANGE, (6, 50), (W - 6, 50), 1)
    # radar con tus sistemas
    R = pygame.Rect(6, 56, 200, 200); c = R.center; rad = 96
    blit_logo(surf, pygame.Rect(c[0] - 85, c[1] - 85, 170, 170), dark=40)
    for k in (1, 2, 3):
        pygame.draw.circle(surf, (40, 26, 8), c, rad * k // 3, 1)
    pygame.draw.line(surf, (40, 26, 8), (c[0] - rad, c[1]), (c[0] + rad, c[1]))
    pygame.draw.line(surf, (40, 26, 8), (c[0], c[1] - rad), (c[0], c[1] + rad))
    ang = math.radians((now * 60) % 360)
    for k in range(28):
        a = ang - math.radians(k * 1.4)
        f_ = (1 - k / 28) * 0.5
        pygame.draw.line(surf, (int(255 * f_), int(140 * f_), 0), c, (c[0] + rad * math.cos(a), c[1] + rad * math.sin(a)), 2)
    ps = [v for v in S if v.get("pos") and None not in v["pos"]]
    used = []
    RADAR_PTS.clear()
    if ps:
        ctl_ = [v for v in ps if v.get("ctrl")] or ps
        mx = sum(v["pos"][0] for v in ctl_) / len(ctl_); mz = sum(v["pos"][2] for v in ctl_) / len(ctl_)
        ext = sorted(max(abs(v["pos"][0] - mx), abs(v["pos"][2] - mz)) for v in ps)
        ext = (ext[int(len(ext) * 0.9)] if len(ext) > 3 else ext[-1]) or 1     # el 90 % mas cercano, sin que uno lejano lo encoja todo
        blink = int(now * 2) % 2
        for v in sorted(ps, key=lambda v: (fac_war(v), v.get("ctrl"))):
            dx, dz = (v["pos"][0] - mx) / ext, (v["pos"][2] - mz) / ext
            d_ = math.hypot(dx, dz)
            if d_ > 1:
                dx, dz = dx / d_, dz / d_                 # los lejanos, en el borde
            px, py = int(c[0] + dx * rad * 0.88), int(c[1] - dz * rad * 0.88)
            RADAR_PTS.append((px, py, v["sys"]))
            war = fac_war(v)
            r = 3 + int(v["inf"] / 18)
            if v.get("ctrl"):
                for g in range(3):
                    pygame.draw.circle(surf, (90 - g * 25, 50 - g * 15, 0), (px, py), r + 6 - g * 2)
            pygame.draw.circle(surf, RED if war else ORANGE if v.get("ctrl") else (150, 150, 150), (px, py), r)
            if war and blink:
                pygame.draw.circle(surf, RED, (px, py), r + 6, 1)
            if v.get("ctrl") or war:
                nm = v["sys"].upper()
                nm = nm if len(nm) <= 12 else nm[:11] + "…"
                tw = tw_(F["tiny"], nm)
                lr = pygame.Rect(px + r + 3, py - 7, tw, 12)
                if lr.right > R.right:
                    lr.right = px - r - 3
                if R.contains(lr) and not any(lr.colliderect(u) for u in used):
                    used.append(lr)
                    put(surf, F["tiny"], nm, lr.topleft, RED if war else (230, 170, 90))
    put(surf, F["tiny"], "MAPA DE LA FACCIÓN", (R.x + 4, R.bottom - 14), DIM)
    # alertas
    X, y = 214, 58
    war = [v for v in S if fac_war(v)] + [v for v in S if not fac_war(v) and inf_warn(v)]
    if war:
        box = pygame.Rect(X, y, W - X - 6, 18 + min(4, len(war)) * 30)
        pygame.draw.rect(surf, (30, 0, 0), box, border_radius=6)
        pygame.draw.rect(surf, RED if int(now * 2) % 2 else (120, 0, 0), box, 2, border_radius=6)
        put(surf, F["small"], "ALERTAS", (X + 8, y + 3), RED)
        yy = y + 18
        for v in war[:4]:
            if not fac_war(v):
                t1, t2 = inf_warn(v)
                put(surf, F["small"], t1 + " · " + v["sys"], (X + 8, yy), WHITE, box.w - 16)
                put(surf, F["tiny"], t2, (X + 8, yy + 14), ORANGE, box.w - 16)
                yy += 30; continue
            cf = (v.get("conflictos") or [{}])[0]
            t = tipo_es(cf.get("tipo") or next((x for x in (v.get("activos") or []) + (v.get("pendientes") or []) if x in ("War", "CivilWar", "Election")), "war"))
            put(surf, F["small"], f"{t} · {v['sys']}", (X + 8, yy), WHITE, box.w - 16)
            put(surf, F["tiny"], f"contra {cf.get('contra') or '?'} · {cf.get('ganados') or 0}-{cf.get('perdidos') or 0} días", (X + 8, yy + 14), RED, box.w - 16)
            yy += 30
        y = box.bottom + 8
    put(surf, F["small"], "SISTEMAS CONTROLADOS", (X, y), DIM); y += 16
    for v in sorted([v for v in S if v.get("ctrl")], key=lambda v: -v["inf"]):
        if y + 14 > H - 28:
            break
        g = gap(v)
        put(surf, F["tiny"], v["sys"].upper(), (X, y), ORANGE, 110)
        bx = pygame.Rect(X + 112, y + 3, 90, 8); pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, ORANGE, (bx.x + 1, bx.y + 1, int(88 * min(100, v["inf"]) / 100), 6))
        put(surf, F["tiny"], f"{v['inf']:.0f}%", (W - 8, y), GREEN if g >= 5 else RED, anchor="topright")
        trend_arrow(surf, v, W - 44, y + 3)
        y += 14
    # cinta con los estados
    pygame.draw.line(surf, ORANGE, (6, H - 24), (W - 6, H - 24), 1)
    segs = []
    for v in S:
        parts = fac_parts(v)
        hoy, media, alto = traf(v)
        if alto:
            parts = parts + [(f"TRÁFICO ALTO {hoy} cmdr", RED)]
        if parts:
            segs.append((v["sys"].upper() + ": ", ORANGE))
            for i, (t, col) in enumerate(parts):
                segs.append(((", " if i else "") + t, col))
            segs.append(("     ·     ", DIM))
    if segs:
        total = sum(tw_(F["small"], t) for t, c in segs) or 1
        x0 = 8 - int((now * 40) % total)
        old = surf.get_clip(); surf.set_clip(pygame.Rect(0, H - 22, W, 22))
        x = x0
        while x < W:
            for t, col in segs:
                w_ = tw_(F["small"], t)
                if x + w_ > 0 and x < W:
                    put(surf, F["small"], t, (x, H - 20), col)
                x += w_
        surf.set_clip(old)
    else:
        put(surf, F["small"], "sin estados especiales en tus sistemas", (W // 2, H - 12), DIM, anchor="center")

def draw_fac_screen_2(surf, now):
    ALR.clear()
    _draw_fac_b15(surf, now)

def draw_fac_screen(surf, now):
    if now - CTL_LIST.get("seen", 0) > 30 and ui.get("view") != 77:
        CTL_LIST["off"] = 0                              # en la espera vuelve arriba
    draw_fac_screen_2(surf, now)


# ========== draw_idle: cadena de 3 etapas, cada una llama a la anterior ==========
# draw_idle_base -> draw_idle_b7 -> draw_idle

def draw_idle_base(surf, now):
    surf.fill(BLACK)
    lt = time.localtime(now)
    img = idle_photo()
    if img:
        r = img.get_rect(center=IDLE_PHOTO)
        surf.blit(img, r)
        pygame.draw.rect(surf, ORANGE, r.inflate(6, 6), 2, border_radius=4)
    else:
        draw_emblem(surf, IDLE_PHOTO[0], IDLE_PHOTO[1], 50, now / 3)
    cx = 310
    put(surf, F["clock"], time.strftime("%H:%M", lt), (cx, 44), ORANGE, anchor="center")
    put(surf, F["btn"], f"{DIAS[lt.tm_wday]} {lt.tm_mday} de {MESES[lt.tm_mon - 1]}", (cx, 90), DIM, anchor="center")
    put(surf, F["big"], "CMDR " + cfg["cmdr"], (cx, 114), ORANGE, 320, anchor="center")
    ip = my_ip()
    put(surf, F["small"], PANEL_VER.split(" · ")[0], (150, 132), GREEN)
    put(surf, F["small"], game_date(), (cx + 4, 132), BLUE, anchor="midtop")
    put(surf, F["small"], f"IP {ip}" if ip else "SIN RED", (W - 8, 132), DIM if ip else RED, anchor="topright")
    idle_crawl(surf, now)
    put(surf, F["small"], "toca la pantalla para abrir el menú", (W // 2, H - 9), DIM, anchor="center")

def draw_idle_b7(surf, now):
    D, S, gap = fac_rows()
    modes = ["norm"] + (["fac"] if S else []) + (["act"] if act_enabled() else [])
    m = modes[int(now // 20) % len(modes)]
    IDLE_MODE.update(m=m, t=time.time())
    try:
        if m == "fac":
            draw_fac_screen(surf, now); return
        if m == "act":
            draw_act_screen(surf, now); return
    except Exception as e:
        log_exc("espera " + m, e)
    draw_idle_base(surf, now)

def draw_idle(surf, now):
    m = IDLEHOLD["m"]
    if m:
        IDLE_MODE.update(m=m, t=time.time())
        try:
            if m == "fac" and fac_rows()[1]:
                draw_fac_screen(surf, now)
            elif m == "act":
                draw_act_screen(surf, now)
            else:
                draw_idle_base(surf, now)
        except Exception as e:
            log_exc("espera fija", e); draw_idle_base(surf, now)
    else:
        draw_idle_b7(surf, now)
    draw_hold(surf, IDLE_MODE["m"] or "norm", now)


# ========== draw_xa: cadena de 2 etapas, cada una llama a la anterior ==========
# draw_xa_base -> draw_xa

def draw_xa_base(surf, now):
    a = xa["a"]
    if not a:
        return
    if now > a["until"]:
        xa["a"] = None; return
    col = a["col"]
    on = int(now * 3) % 2 == 0 or col != RED
    for k in range(4 if on else 2):
        pygame.draw.rect(surf, col, (k * 3, k * 3, W - k * 6, H - k * 6), 2)
    box = pygame.Rect(24, 64, W - 48, 196)
    pygame.draw.rect(surf, BLACK, box)
    dim = tuple(int(c) // 3 for c in col[:3])
    for j in range(12):
        yy = box.y + 10 + (j * 17) % (box.h - 20)
        ln = (j * 41 + int(now * 160)) % 100
        pygame.draw.line(surf, dim, (box.x + 8, yy), (box.x + 8 + ln, yy))
        pygame.draw.line(surf, dim, (box.right - 8 - ln, yy), (box.right - 8, yy))
    pygame.draw.rect(surf, col, box, 3, border_radius=8)
    cx, y = box.centerx, box.y + 16
    put_fit(surf, ("big", "btn", "small"), a["title"], (cx, y), col if on else WHITE, box.w - 20, anchor="midtop"); y += 36
    put_fit(surf, ("num", "big", "btn"), a["big"], (cx, y), WHITE, box.w - 20, anchor="midtop"); y += 52
    for ln_ in [l for l in a["lines"] if l][:3]:
        t_, c2 = ln_ if isinstance(ln_, tuple) else (ln_, col)
        y += put_wrap(surf, t_, (cx, y), c2, box.w - 20, max(1, (box.bottom - 6 - y) // 22))

def draw_xa(surf, now):
    a = xa.get("a")
    draw_xa_base(surf, now)
    if a and xa.get("a") is a and now <= a.get("until", 0):
        draw_num(surf, pygame.Rect(24, 64, W - 48, 196), a.get("ev"))


# ========== fac_watch: cadena de 3 etapas, cada una llama a la anterior ==========
# fac_watch_base -> fac_watch_b10 -> fac_watch

def fac_watch_base(now):
    D = FACD["data"]
    if not D:
        return
    cur = fac_conf(D)
    online = state.get("data") is not None and now - state.get("rx", 0) < 10
    if FW["seen"] is None:                               # al arrancar: recordatorio de lo que haya
        FW["seen"] = set(cur)
        FW["info"] = dict(cur)
        if cur:
            (n, contra), (t, est, g, p) = next(iter(cur.items()))
            fw_alert(f"{tipo_es(t)} EN TU FACCIÓN", f"{n}", [f"contra {contra} · {g}-{p} días" + (f"  (+{len(cur) - 1} más)" if len(cur) > 1 else "")],
                     f"{tipo_es(t).lower()} en {n}")
            FW["rem"] = now
        return
    for k in cur:
        if k not in FW["seen"]:
            (n, contra), (t, est, g, p) = k, cur[k]
            fw_alert(f"¡{tipo_es(t)}!", n, [f"contra {contra}", "empieza tras el tick" if est == "pending" else f"{g}-{p} días"],
                     f"atención, {tipo_es(t).lower()} en {n}")
            FW["rem"] = now
    for k in FW["seen"] - set(cur):
        (n, contra), (t, est, g, p) = k, FW["info"].get(k, ("war", "", 0, 0))
        res = "GANADA" if g > p else "PERDIDA" if p > g else "EMPATE"
        fw_alert(f"{tipo_es(t)} TERMINADA", n, [f"contra {contra} · {g}-{p} días · {res}"], f"{tipo_es(t).lower()} terminada en {n}")
    FW["seen"] = set(cur); FW["info"].update(cur)
    if cur and online and now - FW["rem"] > 3600:        # mientras dure: cada hora jugando
        FW["rem"] = now
        (n, contra), (t, est, g, p) = next(iter(cur.items()))
        fw_alert(f"{tipo_es(t)} EN CURSO", n, [f"contra {contra} · {g}-{p} días" + (f"  (+{len(cur) - 1} más)" if len(cur) > 1 else "")],
                 f"recuerda, {tipo_es(t).lower()} en {n}")
    hoyk = time.strftime("%Y-%m-%d", time.gmtime())
    for n, v in (D.get("sistemas") or {}).items():       # trafico alto y bajando influencia
        hoy, media, alto = traf(v)
        if alto and v.get("prev") is not None and v["inf"] < v["prev"] and (n, hoyk) not in FW["trf"]:
            FW["trf"].add((n, hoyk))
            fw_alert("TRÁFICO ALTO", n, [f"{hoy} comandantes hoy (media {media:.0f}) y tu influencia baja"], f"tráfico alto en {n}")

def fac_watch_b10(now):
    fac_watch_base(now)
    D = FACD["data"]
    if not D:
        return
    hoyk = time.strftime("%Y-%m-%d", time.gmtime())
    for n, v in (D.get("sistemas") or {}).items():
        w_ = inf_warn(v)
        if w_ and (n, w_[0], hoyk) not in INFW:
            INFW.add((n, w_[0], hoyk))
            fw_alert(w_[0], n, [w_[1]], f"{w_[0].lower()} en {n}")

def fac_watch(now):
    fac_watch_b10(now)
    D = FACD["data"]
    if D and (D.get("t") or 0) != FWS["t"]:                         # solo cuando llegan datos nuevos
        FWS["t"] = D.get("t") or 0
        try:
            fac_events(D, now)
        except Exception as e:
            log_exc("faccion expansion/control", e)


# ========== on_tap: cadena de 16 etapas, cada una llama a la anterior ==========
# on_tap_base -> on_tap_96 -> on_tap_99j -> on_tap_b3 -> on_tap_b4 -> on_tap_b5 -> on_tap_b6 -> on_tap_b9 -> on_tap_b10 -> on_tap_b10c -> on_tap_b11 -> on_tap_b12b -> on_tap_b13 -> on_tap_b15 -> on_tap_b16 -> on_tap

def on_tap_base(x, y):
    if CAL:
        print("toque", x, y)
    if kill_tap(x, y):
        return
    if ui.get("shipcard") and time.time() < ui["shipcard"]:
        ui["shipcard"] = 0; return
    if xa.get("a") and xa["a"].get("title") in ("SESIÓN TERMINADA", "BATALLA TERMINADA") and time.time() < xa["a"]["until"]:
        xa["a"] = None; return
    if ui["alert"] and time.time() < ui["alert"]["until"]:
        ui["alert"] = None; return
    if ui["idle_on"]:
        ui["idle_skip"] = time.time() + 60; return
    v = ui["view"]
    if BACK.collidepoint(x, y):
        ui["view"] = 0 if v == 100 else PARENT.get(v, 0); ui["pause"] = False
        return
    if y < TOP and tap_topbar(x, y, v):
        return
    if v == 0:
        for i in range(12):
            if grid(i).collidepoint(x, y):
                tap_flash((0, i)); ui["view"] = i + 1; ui["page4"] = 0
                return
    elif v == 1:
        for i, b in enumerate(BUTTONS):
            if grid(i).collidepoint(x, y):
                tap_flash((1, i)); press_seq([b[1]]); return
    elif v == 2:
        for i, (_, k) in enumerate(PIP_COLS):
            if pip_rect(i).collidepoint(x, y):
                tap_flash((2, i)); press_seq([k]); return
        for i, (_, ks) in enumerate(PIP_PRESETS):
            if preset_rect(i).collidepoint(x, y):
                tap_flash((2, 10 + i)); press_seq(ks); return
    elif v == 4:
        n_ = carga_ntabs()
        for i in range(n_):
            if tab_rect_n(i, n_).collidepoint(x, y):
                ui["tab4"] = i; ui["page4"] = 0; return
        if y > TOP + TAB_H:
            ui["page4"] += 1
    elif v == 51:
        for i in range(len(EMOTES)):
            if grid(i, 4, 2).collidepoint(x, y):
                tap_flash((51, i))
                k = emote_key(i)
                if k:
                    press_seq([k])
                return
    elif v == 5:
        if y < SEC_TOP and x > W // 2:
            ui["view"] = 51; return
        for i, b in enumerate(SRV_BTNS + PIE_BTNS):
            if m5_rect(i).collidepoint(x, y):
                tap_flash((5, i)); press_seq([b[1]])
                if i >= 6 and b[0] in GLOW_LBL:            # a pie el juego no dice si estan encendidas
                    GLOW[GLOW_LBL[b[0]]] = time.time()
                return
    elif v == 6:
        for i, b in enumerate(COMBAT_BTNS):
            if c6_rect(i).collidepoint(x, y):
                tap_flash((6, i)); press_seq([b[1]]); return
    elif v == 9:
        for i, (txt, key, grp) in enumerate(FIGHTER_BTNS):
            if c9_rect(i).collidepoint(x, y):
                tap_flash((9, i)); press_seq([key])
                if grp:
                    ui["orders"][grp] = i
                    if txt == "VOLVER":
                        ui["orders"].pop("a", None)
                return
    elif v == 7:
        for i in range(6):
            if grid(i, 3, 2).collidepoint(x, y):
                tap_flash((7, i)); ui["view"] = 71 + i; return
    elif v in (125, 127):
        ui[f'page{v}'] = ui.get(f'page{v}', 0) + 1; return
    elif v in (128, 129):
        tap_trip(x, y); return
    elif v == 3:
        cur = ui.get('navtab') or (1 if time.time() < pol['until'] else 0); ui['navtab'] = (cur + 1) % 3; pol['until'] = 0; return
    elif v == 124:
        for i in range(7):
            if grid(i, 4, 2).collidepoint(x, y):
                power_tap(i); return
    elif v == 1245:
        ui['page1245'] = ui.get('page1245', 0) + 1; return
    elif v == 100 and SHIP_NAME_R.collidepoint(x, y) and not ((state.get("data") or {}).get("Flags2", 0) & 1):
        ui["view"] = 170; return
    elif v in (170, 171):
        ui["shippage"] = ui.get("shippage", 0) + 1; return
    elif (v == 100 and NAVE_BTN.collidepoint(x, y)) or (v == 73 and NAVE_BTN_BIO.collidepoint(x, y)):
        ship_here(); return
    elif v == 76:
        ui['alientab'] = 1 - ui.get('alientab', 0); return
    elif v == 11:
        if ui.get('sesstab') and SQ_BTN.collidepoint(x, y):
            tap_flash(("sqbtn",)); ui["view"] = 165; ui["sqpage"] = 0; return
        ui['sesstab'] = 1 - ui.get('sesstab', 0); return
    elif v == 150:
        tap_map(x, y); return
    elif v == 160:
        tap_pantalla(x, y); return
    elif v == 211:
        tap_calc(x, y); return
    elif v == 210:
        if y > TOP:
            ui["page4"] += 1
        return
    elif v == 164:
        tap_keys(x, y); return
    elif v == 165:
        tap_squad(x, y); return
    elif v in (161, 162, 163):
        tap_evlist(x, y); return
    elif v in (140, 141):
        tap_manual(x, y); return
    elif v == 132:
        cgoals["page"] += 1; return
    elif v in (130, 131):
        tap_galnet(x, y); return
    elif v == 71:
        ui['page71'] = ui.get('page71', 0) + 1; return
    elif v == 72:
        tap_orrery(x, y)
    elif v == 12:
        tap_sub12(x, y); return
    elif v == 1244:
        for i, k in enumerate(["auto", "alerts", "sound", "theme", "voice", "stream", "keys", "killbtn", "mkt", "cmdrpics", "hdmi"]):
            if grid(i, 4, 3).collidepoint(x, y):
                if k == "hdmi":
                    tap_flash((124, i)); hdmi_toggle(); return
                if k == "mkt":
                    tap_flash((124, i))
                    opts_ = ["CON CARGA", "SIEMPRE", "NUNCA"]
                    cfg["mkt"] = opts_[(opts_.index(cfg.get("mkt", "CON CARGA")) + 1) % 3]; save_cfg(); return
                if k == "keys":
                    tap_flash((124, i)); ui["view"] = 164; return
                if k == "killbtn":
                    tap_flash((124, i)); cfg["killbtn"] = not cfg.get("killbtn", True); save_cfg(); return
                if k == "cmdrpics":
                    tap_flash((124, i)); cfg["cmdrpics"] = not cfg.get("cmdrpics", True); save_cfg(); return
                tap_flash((124, i))
                if k in ("alerts", "auto", "sound"):
                    ui["view"] = {"alerts": 161, "auto": 162, "sound": 163}[k]; return
                if k == "theme":
                    cfg["theme"] = (cfg["theme"] + 1) % len(THEMES); apply_theme()
                else:
                    cfg[k] = not cfg.get(k, False)
                    if k == "sound" and cfg[k]: play("ok")
                    if k == "voice" and cfg[k]: voice["last"].clear(); voice_say("Voz de la nave activada")
                    if k == "stream" and cfg[k]: stream_start()
                save_cfg(); return
    elif v == 121:
        if y > TOP:
            ui["pause"] = not ui["pause"]
    elif v == 122:
        tap_stream(x, y)

def on_tap_96(x, y):
    try:
        on_tap_base(x, y)
    finally:
        TAP_EV.set()                                 # redibuja ya, sin esperar al siguiente ciclo

def on_tap_99j(x, y):
    with lock:
        d_ = state["data"]
    if ops_on(d_) and mega_rect(W, H).collidepoint(x, y):
        mega_tap(); return
    on_tap_96(x, y)

def on_tap_b3(x, y):
    v = ui.get("view")
    if v == 190 and y >= H - 30:
        for i in range(5):
            if vj_btn(i).collidepoint(x, y):
                if i < 4:
                    ui["vjp"] = VJ_PER[i][0]
                else:
                    ui["vjz"] = "zona" if ui.get("vjz", "zona") == "gal" else "gal"
                TAP_EV.set(); return
    if v == 191:
        cb = dict(COMBAT_BTNS)
        for k, lab in enumerate(CC_L):
            if cc_rect(0, k).collidepoint(x, y) and cb.get(lab):
                tap_flash((191, k)); press_seq([cb[lab]]); return
        for k, lab in enumerate(CC_R):
            if cc_rect(1, k).collidepoint(x, y):
                for i, (txt, key, grp) in enumerate(FIGHTER_BTNS):
                    if txt == lab:
                        tap_flash((191, 10 + k)); press_seq([key])
                        if grp:
                            ui["orders"][grp] = i
                            if txt == "VOLVER":
                                ui["orders"].pop("a", None)
                return
    on_tap_99j(x, y)

def on_tap_b4(x, y):
    v = ui.get("view")
    if v == 190:
        if y >= H - 30:
            for i in range(6):
                if vj_btn(i).collidepoint(x, y):
                    if i < 4:
                        ui["vjp"] = VJ_PER[i][0]; ui["vjzoom"] = None
                    elif i == 4:
                        ui["vjz"] = "zona" if ui.get("vjz", "zona") == "gal" else "gal"; ui["vjzoom"] = None
                    else:
                        Z = ui.get("vjzoom")
                        ui["vjzoom"] = None if not Z or Z[0] <= 2 else (Z[0] // 2, Z[1], Z[2])
                    TAP_EV.set(); return
            return
        A, pt, sc = VJT.get("A"), VJT.get("pt"), VJT.get("sc")
        if A and sc and TOP < y < H - 34:
            c0 = pt(0, 0)                                    # punto del mundo bajo el dedo
            wx, wz = (x - c0[0]) / sc, -(y - c0[1]) / sc
            Z = ui.get("vjzoom")
            f_ = (Z[0] if Z else 1) * 2
            if f_ <= 64:
                ui["vjzoom"] = (f_, wx, wz)
            TAP_EV.set(); return
    if v in (192, 193) and y > TOP:
        ui["facpg"] = ui.get("facpg", 0) + 1; TAP_EV.set(); return
    on_tap_b3(x, y)

def on_tap_b5(x, y):
    v = ui.get("view")
    if v == 0 and grid(8).collidepoint(x, y) and y > TOP:
        tap_flash((0, 8)); ui["view"] = 192; TAP_EV.set(); return
    if v in (192, 193) and y > TOP:
        D, S, gap = fac_rows()
        pages = max(1, (len(S) + FAC_PER - 1) // FAC_PER)
        if pages > 1:
            for k in (0, 1):
                if fac_pg_btn(k).collidepoint(x, y):
                    ui["facpg"] = (ui.get("facpg", 0) + (1 if k else -1)) % pages; TAP_EV.set(); return
        for r, name in FROWS:
            if r.collidepoint(x, y):
                ui["facsys"] = name; ui["facback"] = v; ui["view"] = 194; TAP_EV.set(); return
        return
    if v == 194 and y > TOP:
        if pygame.Rect(4, H - 26, 90, 23).collidepoint(x, y):
            ui["view"] = ui.get("facback", 192); TAP_EV.set()
        return
    on_tap_b4(x, y)

def on_tap_b6(x, y):
    v = ui.get("view")
    if v in (194, 195, 196) and BACK_R.collidepoint(x, y):
        ui["view"] = ui.get("facback", 192); TAP_EV.set(); return
    if v == 196 and y > TOP:
        for r, n in ZPTS:
            if r.collidepoint(x, y):
                ui["facsys"] = n; ui["view"] = 194; TAP_EV.set(); return
        return
    if v == 195 and y > TOP:
        return
    if v == 194 and y > TOP:
        return
    on_tap_b5(x, y)

def on_tap_b9(x, y):
    if ui.get("idle_on"):
        m = IDLE_MODE["m"] or "norm"
        if hold_rect(m).inflate(10, 10).collidepoint(x, y):
            IDLEHOLD["m"] = None if IDLEHOLD["m"] else m
            if IDLEHOLD["m"] == "act":
                ACT_GAL[0] = int(time.time() // 10) % 2 == 0
            TAP_EV.set(); return
        if IDLEHOLD["m"] == "act" and ACT_MAP.collidepoint(x, y):
            ACT_GAL[0] = not ACT_GAL[0]; TAP_EV.set(); return
    on_tap_b6(x, y)

def on_tap_b10(x, y):
    v = ui.get("view")
    if v == 7 and not ui.get("idle_on"):
        for i in range(8):
            if grid(i, 4, 2).collidepoint(x, y):
                tap_flash((7, i)); ui["view"] = 71 + i
                if i == 7:
                    ACT_GAL[0] = True
                TAP_EV.set(); return
        # b10b: menu 7, fuera de los 8 botones sigue (el boton < MENU)
    if v in (77, 78):
        if FULL_BACK.inflate(10, 10).collidepoint(x, y):
            ui["view"] = 7; TAP_EV.set(); return
        if v == 77:
            n = radar_hit(x, y)
            if n:
                ui["facsys"] = n; ui["facback"] = 77; ui["view"] = 194; TAP_EV.set()
            return
        if ACT_MAP.collidepoint(x, y):
            ACT_GAL[0] = not ACT_GAL[0]; TAP_EV.set()
        return
    if v in (194, 195, 196) and IR_R.inflate(6, 6).collidepoint(x, y):
        D, name, vv = fs_get()
        if name:
            tap_flash(("ir", 0)); ir_send(name); TAP_EV.set()
        return
    if v == 124 and grid(7, 4, 2).collidepoint(x, y):
        tap_flash((1240, 7))
        sub, col, det = pueblo_estado(time.time())
        set_alert("ESCUCHA DEL PUEBLO", det, col, 6, kind="info"); TAP_EV.set(); return
    if ui.get("idle_on") and IDLE_MODE["m"] == "fac" and not hold_rect("fac").inflate(10, 10).collidepoint(x, y):
        n = radar_hit(x, y)
        if n:
            ui["idle_skip"] = time.time() + 60
            ui["facsys"] = n; ui["facback"] = 192; ui["view"] = 194; TAP_EV.set(); return
    on_tap_b9(x, y)

def on_tap_b10c(x, y):
    if ui.get("view") == 1244 and not ui.get("idle_on") and PUEBLO_R.collidepoint(x, y):
        tap_flash(("pueblo",))
        sub, col, det = pueblo_estado(time.time())
        set_alert("FLUJO DATOS EDDN", det, col, 7, kind="info"); TAP_EV.set(); return
    on_tap_b10(x, y)

def on_tap_b11(x, y):
    if num_tap(x, y):
        return
    v = ui.get("view")
    if v == 190 and vj_btn(6).collidepoint(x, y):
        vj_plus(); TAP_EV.set(); return
    if v == 135 and y > TOP:
        if COL_HEAD.collidepoint(x, y):
            C, L, i = col_pick(state.get("data"))
            if L:
                ui["colsel"] = (i + 1) % len(L); ui["colpg"] = 0
        else:
            ui["colpg"] = ui.get("colpg", 0) + 1
        TAP_EV.set(); return
    if (v == 77 or (ui.get("idle_on") and IDLE_MODE["m"] == "fac")) and not FULL_BACK.inflate(10, 10).collidepoint(x, y) \
            and not hold_rect("fac").inflate(10, 10).collidepoint(x, y):
        if radar_tap(x, y):
            return
    on_tap_b10c(x, y)

def on_tap_b12b(x, y):
    COLB["hold"] = 0                                     # si tocas tu, manda lo que tocas
    on_tap_b11(x, y)

def on_tap_b13(x, y):
    v = ui.get("view")
    if v == 127 and MKBOX.get("r") and MKBOX["r"].collidepoint(x, y) and not (ui.get("alert") and time.time() < ui["alert"]["until"]):
        ui["view"] = 135; ui["colf"] = "aqui"; ui["colsel"] = None; ui["colpg"] = 0; TAP_EV.set(); return
    if v == 135 and y > TOP and not (ui.get("alert") and time.time() < ui["alert"]["until"]):
        for k, (fk, lab) in enumerate(COLF):
            if COLF_R[k].inflate(4, 8).collidepoint(x, y):
                ui["colf"] = fk; ui["colpg"] = 0; TAP_EV.set(); return
        if COL_HEAD.collidepoint(x, y):
            C, L, i = col_pick(state.get("data"))
            if L:
                ui["colsel"] = (i + 1) % len(L); ui["colpg"] = 0
            TAP_EV.set(); return
        if ui.get("colf") == "sis" and y < H - 18:
            for r, stn in COLROWS:
                if r.collidepoint(x, y):
                    ir_send(stn); TAP_EV.set(); return
            return
        ui["colpg"] = ui.get("colpg", 0) + 1; TAP_EV.set(); return
    on_tap_b12b(x, y)

def on_tap_b15(x, y):
    v = ui.get("view")
    if (v == 77 or (ui.get("idle_on") and IDLE_MODE["m"] == "fac")) and not FULL_BACK.inflate(10, 10).collidepoint(x, y) \
            and not hold_rect("fac").inflate(10, 10).collidepoint(x, y) and not (ui.get("alert") and time.time() < ui["alert"]["until"]):
        for r, n in ALR:
            if r.collidepoint(x, y):
                ui["idle_skip"] = time.time() + 60
                ui["facsys"] = n; ui["facback"] = 77; ui["view"] = 194; TAP_EV.set(); return
    on_tap_b13(x, y)

def on_tap_b16(x, y):
    if ui.get("view") == 137 and ALT_SRV_R[0].collidepoint(x, y):
        cfg["alt_srv"] = not cfg.get("alt_srv", False); save_cfg(); TAP_EV.set(); return
    on_tap_b15(x, y)

def on_tap(x, y):
    if DRAG.get("on"):
        return
    v = ui.get("view")
    if v == 11 and LEDB.get("r") and LEDB["r"].collidepoint(x, y):
        if time.time() < LEDB["sure"]:
            LEDB["sure"] = 0; led_clear()
        else:
            LEDB["sure"] = time.time() + 3
        TAP_EV.set(); return
    act_vis = v == 78 or (ui.get("idle_on") and IDLE_MODE.get("m") == "act")
    if act_vis and not (ui.get("alert") and time.time() < ui["alert"]["until"]):
        for i, b in enumerate(ACT_BTN):
            if b.inflate(4, 8).collidepoint(x, y):
                ACT_MODE[0] = ACT_MODES[i][0]
                if ui.get("idle_on"):
                    IDLEHOLD["m"] = "act"                # en la espera: se queda fija en esa vista
                TAP_EV.set(); return
        if ACT_MAP.collidepoint(x, y) and (v == 78 or IDLEHOLD["m"] == "act"):
            k = [m for m, _ in ACT_MODES].index(ACT_MODE[0]) if ACT_MODE[0] in [m for m, _ in ACT_MODES] else 0
            ACT_MODE[0] = ACT_MODES[(k + 1) % 3][0]; TAP_EV.set(); return
    radar_vis = v == 77 or (ui.get("idle_on") and IDLE_MODE.get("m") == "fac")
    if radar_vis:
        for r, n in CTL_ROWS:
            if r.collidepoint(x, y):
                ui["idle_skip"] = time.time() + 60
                ui["facsys"] = n; ui["facback"] = 77; ui["view"] = 194; TAP_EV.set(); return
    on_tap_b16(x, y)


# ========== perf_side: cadena de 2 etapas, cada una llama a la anterior ==========
# perf_side_base -> perf_side

def perf_side_base(S):
    f = BIG.get("pfont") or BIG.setdefault("pfont", pygame.font.Font(None, 20))
    y = 8
    for t, col in perf_parts():
        put(S, f, t, (BIG["w"] - 6, y), col, anchor="topright"); y += 16

def perf_side(S):
    if IDLE_MODE["m"] in ("fac", "act") and time.time() - IDLE_MODE["t"] < 2:
        return                                           # pantallas de facción y actividad: limpias
    perf_side_base(S)


# ========== perf_update: cadena de 2 etapas, cada una llama a la anterior ==========
# perf_update_base -> perf_update

def perf_update_base():
    now = time.time()
    if now - PERF["t"] < 2:
        return
    try:
        with open("/proc/self/stat") as f:
            st = f.read().rsplit(")", 1)[1].split()
        c = (int(st[11]) + int(st[12])) / os.sysconf("SC_CLK_TCK")
        if PERF["c0"] is not None:
            PERF["cpu"] = 100.0 * (c - PERF["c0"]) / max(0.1, now - PERF["w0"])
        PERF["c0"], PERF["w0"] = c, now
    except (OSError, ValueError, IndexError):
        pass
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            PERF["temp"] = int(f.read()) / 1000
    except (OSError, ValueError):
        PERF["temp"] = None
    if PERF["t"]:
        PERF["fps"] = (PERF["frames"] - PERF["f0"]) / (now - PERF["t"])
    PERF["f0"], PERF["t"] = PERF["frames"], now

def perf_update():
    t0 = PERF["t"]
    perf_update_base()
    if PERF["t"] == t0:
        return
    m = dict((l.split(":")[0], int(l.split()[1])) for l in _rd("/proc/meminfo").splitlines() if l.split()[1:2] and l.split()[1].isdigit())
    if m.get("MemTotal") and m.get("MemAvailable") is not None:
        PERF["ram"] = 100.0 * (m["MemTotal"] - m["MemAvailable"]) / m["MemTotal"]
    c = _rd("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq").strip()
    PERF["mhz"] = int(c) / 1000 if c.isdigit() else None
    if PERF_MAXMHZ[0] is None:
        mx = _rd("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq").strip()
        PERF_MAXMHZ[0] = int(mx) / 1000 if mx.isdigit() else 0


# ========== render: cadena de 15 etapas, cada una llama a la anterior ==========
# render_base -> render_b3 -> render_b4 -> render_b6 -> render_b9 -> render_b10 -> render_b11 -> render_b12 -> render_b12b -> render_b14 -> render_b15 -> render_b16 -> render_b18 -> render_b19 -> render

def render_base(surf):
    with lock:
        d, rx = state["data"], state["rx"]
    now = time.time()
    online = d is not None and now - rx < 5
    if online and not HI_PASS[0]:
        glow_watch(d)
        binds_check(d)
        process_notes(d)
        track_update(d, now)
    if now - ui["start"] < 3:
        draw_splash(surf, now); return
    menu_ = online and (d or {}).get("menu")
    ui["idle_on"] = (not online or menu_) and ui["view"] in (0, 100) and now > ui["idle_skip"] and now - ui["start"] > 8
    if ui["idle_on"]:
        if menu_ and not HI_PASS[0]:
            xa_notes(d, now)
        draw_idle(surf, now)
        if menu_:
            draw_xa(surf, now)
            pygame.draw.rect(surf, BLACK, (0, H - 18, W, 18))
            put(surf, F["btn"], "MENÚ PRINCIPAL", (W // 2, H - 9), NEON_G, anchor="center")
        draw_shipcard(surf, now)
        return
    if False:
        draw_idle(surf, now); return
    flags = (d or {}).get("Flags", 0) if online else 0
    v = ui["view"]
    surf.fill(BLACK)
    # barra superior
    x0 = 8
    if True:
        pygame.draw.rect(surf, ORANGE, BACK.inflate(-8, -8), 2, border_radius=6)
        put(surf, F["btn"], "MENÚ" if v == 100 else "< INICIO" if v == 0 else "< MENÚ", BACK.center, ORANGE, anchor="center")
        x0 = BACK.right + 4
    title = ("MENÚ PRINCIPAL" if (d or {}).get("menu") else ((d or {}).get("system") or "---").upper()) if online else "SIN DATOS"
    alert0 = next((t for b, t in ALERTS if flags & (1 << b)), None) if online else None
    if alert0 and tab_group(v)[0]:
        put(surf, F["big"], alert0, (x0, 6), RED, W - 182 - x0)
    else:
        put(surf, F["big"], title, (x0, 6), (GREEN if (d or {}).get("menu") else ORANGE) if online else DIM, W - 182 - x0)
    draw_gear(surf, v, now)
    fuel = ((d or {}).get("Fuel") or {}).get("FuelMain")
    cap = (d or {}).get("fuelcap")
    if online and fuel is not None:
        pct = max(0.0, min(1.0, fuel / cap)) if cap else None
        bx = pygame.Rect(W - 176, 6, 120, 14)
        pygame.draw.rect(surf, DIM, bx, 1)
        if pct is not None:
            pygame.draw.rect(surf, RED if pct < 0.25 else ORANGE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * pct), bx.h - 4))
        put(surf, F["small"], f"FUEL {fuel:.1f}t", (W - 176, 21))
    mode = (d or {}).get("mode") if online else None
    if mode and not tab_group(v)[0]:
        put(surf, F["small"], f"MODO: {mode}", (W - 176, 37), RED, 120)
    alert = next((t for b, t in ALERTS if flags & (1 << b)), None) if online else None
    if tab_group(v)[0]:
        draw_tabs(surf, v)
    elif alert:
        put(surf, F["small"], alert, (x0, 34), RED)
    elif v:
        put(surf, F["small"], MENU.get(v, f"MENU {v}"), (x0, 34), DIM)
    pygame.draw.line(surf, DIM, (0, TOP - 2), (W, TOP - 2), 1)
    fn = VIEWS.get(v)
    if fn:
        try:
            t_ = time.perf_counter()
            fn(surf, d if online else None, flags, now)
            perf_view(v, time.perf_counter() - t_)
        except Exception as e:
            log_exc(f"pantalla {v}", e)
            put(surf, F["btn"], "Error en esta pantalla", (W // 2, (H + TOP) // 2 - 10), RED, anchor="center")
            put(surf, F["small"], "está apuntado en 12 AJUSTES > LOG", (W // 2, (H + TOP) // 2 + 14), DIM, anchor="center")
    else:
        put(surf, F["btn"], f"Menú {v} vacío", (W // 2, (H + TOP) // 2), DIM, anchor="center")
    draw_scoop(surf, d if online else None, flags, now)
    if not HI_PASS[0]:
        xa_notes(d if online else None, now)
    draw_xa(surf, now)
    draw_toast(surf, now)
    draw_shipcard(surf, now)
    draw_mega(surf, d if online else None, now)
    draw_hpcrit(surf, now)
    draw_kill(surf, now)
    if (cfg.get("voice") or cfg.get("stream") or cfg.get("stackchan")) and not HI_PASS[0]:
        voice_watch()
    if ui["alert"]:
        if now < ui["alert"]["until"]:
            draw_alert(surf, now)
        else:
            ui["alert"] = None

def render_b3(surf):
    try:
        with lock:
            d_ = state["data"]
        bgs_watch(d_, time.time())
    except Exception:
        pass
    return render_base(surf)

def render_b4(surf):
    try:
        with lock:
            d_ = state["data"]
        etick_watch(d_, time.time())
    except Exception:
        pass
    return render_b3(surf)

def render_b6(surf):
    try:
        fac_watch(time.time())
    except Exception as e:
        log_exc("faccion avisos", e)
    return render_b4(surf)

def render_b9(surf):
    r_ = render_b6(surf)
    if not ui.get("idle_on") and IDLEHOLD["m"]:
        IDLEHOLD["m"] = None                             # al entrar al juego se suelta
    return r_

def render_b10(surf):
    v = ui.get("view")
    if v not in (77, 78):
        return render_b9(surf)
    with lock:
        d, rx = state["data"], state["rx"]
    now = time.time()
    online = d is not None and now - rx < 5
    ui["idle_on"] = False
    try:
        if online and not HI_PASS[0]:
            glow_watch(d); binds_check(d); process_notes(d); track_update(d, now)
        fac_watch(now)
    except Exception as e:
        log_exc("menú 7 datos", e)
    try:
        view_full(surf, d, (d or {}).get("Flags", 0) if online else 0, now)
    except Exception as e:
        log_exc("menú 7 " + str(v), e); surf.fill(BLACK)
        put(surf, F["btn"], "error, mira el LOG", (W // 2, H // 2), RED, anchor="center")
        pygame.draw.rect(surf, ORANGE, FULL_BACK, 1, border_radius=4)
    if online and not HI_PASS[0]:
        try:
            xa_notes(d, now)
        except Exception:
            pass
    draw_xa(surf, now)
    if ui.get("alert") and now < ui["alert"]["until"]:
        draw_alert(surf, now)

def render_b11(surf):
    r_ = render_b10(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        now = time.time()
        if d is not None and now - rx < 5:
            dk = ((d or {}).get("colonia") or {}).get("dock")
            if dk != COLA["dock"]:
                COLA["dock"] = dk
                COLA["pend"] = now + 2 if dk else 0
            if COLA["pend"] and now > COLA["pend"]:
                COLA["pend"] = 0
                if auto_on("colonia") and not ui.get("idle_on"):
                    ui["view"] = 135; ui["colsel"] = None; ui["colpg"] = 0
    except Exception as e:
        log_exc("colonia auto", e)
    return r_

def render_b12(surf):
    COLA["pend"] = 0                                     # la apertura de la b11 queda sustituida
    COLA["dock"] = None
    r_ = render_b11(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d is not None and time.time() - rx < 5:
            col_auto(d, time.time())
    except Exception as e:
        log_exc("colonización auto", e)
    return r_

def render_b12b(surf):
    r_ = render_b12(surf)
    try:
        col_pend(time.time())
    except Exception as e:
        log_exc("colonización", e)
    return r_

def render_b14(surf):
    r_ = render_b12b(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d is not None and time.time() - rx < 5:
            colbuy_watch(d, time.time())
    except Exception as e:
        log_exc("colonia compra", e)
    return r_

def render_b15(surf):
    r_ = render_b14(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        now = time.time()
        if d is not None and now - rx < 5:
            x = d.get("exitst") or {}
            if x.get("out") and EXW["out"] != x["out"]:
                if EXW["out"] is not None and auto_on("salida") and not ui.get("idle_on") and now - rx < 5:
                    ui["view"] = 100
                    plog("Salida de la estación (" + str(x.get("why")) + "): EN VIVO")
                EXW["out"] = x["out"]
            elif EXW["out"] is None:
                EXW["out"] = x.get("out") or 0
            if not ui.get("idle_on"):
                draw_exit_band(surf, d, now)
    except Exception as e:
        log_exc("salida estación", e)
    return r_

def render_b16(surf):
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d is not None and time.time() - rx < 5:
            alt_track(d, time.time())
    except Exception:
        pass
    return render_b15(surf)

def render_b18(surf):
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d is not None and time.time() - rx < 5:
            dk = bool(d.get("Flags", 0) & 3)
            if UNDK["dock"] and not dk:
                UNDK["t"] = time.time()                  # acaba de despegar
            UNDK["dock"] = dk
    except Exception:
        pass
    return render_b16(surf)

def render_b19(surf):
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        now = time.time()
        if d is not None and now - rx < 5:
            spd_track(d, now); caja_track(d, now); suelo_watch(d, now)
        if PLR["n"] and now - PLR["t"] > 5:
            plog_base(f"  (repetido ×{PLR['n'] + 1})"); PLR["n"] = 0
        if REPN["n"] and now - REPN["t"] > 5:
            plog_base(f"  ({REPN['k'][0]}: repetido ×{REPN['n'] + 1})"); REPN["n"] = 0
    except Exception as e:
        log_exc("velocidad", e)
    return render_b18(surf)

def render(surf):
    r_ = render_b19(surf)
    try:
        now = time.time()
        if LGB["t"] and now - LGB["t"] > 3 and not (ui.get("shipcard") and now < ui["shipcard"]):
            LGB["t"] = 0
            if hdmi_panel():
                cfg["hdmi"] = "tablero"; save_cfg()
                plog("Partida cargada: pantalla grande en 4 CUADROS")
    except Exception as e:
        log_exc("4 cuadros al cargar", e)
    try:
        sc_watch(time.time())
    except Exception as e:
        log_exc("4 cuadros en supercrucero", e)
    return r_


# --- v1.1: al entrar en supercrucero, la pantalla grande pasa a 4 CUADROS (CAMBIO AUTO > SUPERCRUCERO) ---
SCW = {"on": None}

def sc_watch(now):
    with lock:
        d, rx = state["data"], state["rx"]
    if not d or now - rx > 5:
        return
    sc = bool((d.get("Flags") or 0) & (1 << 4))
    if sc and SCW["on"] is False and auto_on("supercrucero") and hdmi_panel() and BIG.get("fb") is not None:
        cfg["hdmi"] = "tablero"; save_cfg(); TAP_EV.set()
        plog("Supercrucero: pantalla grande en 4 CUADROS")
    SCW["on"] = sc


# ========== render_big: cadena de 2 etapas, cada una llama a la anterior ==========
# render_big_base -> render_big

def render_big_base():
    S, cell = BIG["surf"], BIG["cell"]
    BIG["fast"] = False
    BIG["rects"] = []
    if hdmi_panel() and not ui.get("bye") and render_big_panel(S):
        return
    if ui.get("bye"):
        S.fill(BLACK); return
    bw, bh = BIG["w"], BIG["h"]
    with lock:
        d, rx = state["data"], state["rx"]
    now = time.time()
    online = d is not None and now - rx < 5
    if BIG["fonts"] is None:
        BIG["fonts"] = (pygame.font.Font(None, 40), pygame.font.Font(None, 26))
    fbig, fsm = BIG["fonts"]
    S.fill(BLACK)
    flags = (d or {}).get("Flags", 0) if online else 0
    full = None
    if ui.get("alert") and now < ui["alert"]["until"]:
        full = "alert"
    elif xa.get("a") and now < xa["a"]["until"] and not kill_in_cell(xa["a"]):
        full = "xa"
    elif online and (flags & (1 << 11) or now < scoop["full_until"]):
        full = "scoop"
    if now - ui["start"] < 3:
        draw_splash(cell, now); big_blit(S, cell, S.get_rect()); return
    if not online:
        draw_idle(cell, now); big_blit(S, cell, S.get_rect()); return
    if full:
        cell.fill(BLACK)
        if full == "alert":
            draw_alert(cell, now)
        elif full == "xa":
            draw_xa(cell, now)
        else:
            draw_scoop(cell, d, flags, now)
        big_blit(S, cell, S.get_rect()); return
    if d.get("menu"):
        draw_idle(cell, now); big_blit(S, cell, S.get_rect())
        put(S, fbig, "MENÚ PRINCIPAL", (bw // 2, bh - 40), GREEN, anchor="center")
        return
    mode = big_mode(d, flags)
    hh = 44
    tw = put(S, fbig, (d.get("system") or "---").upper(), (12, 9), ORANGE, 400)
    put(S, fsm, mode, (12 + tw + 14, 16), GREEN, max(40, bw // 2 + 10 - (12 + tw + 14)))
    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
    if flags & (1 << 26):
        fuel, cap = (d.get("Fuel") or {}).get("FuelReservoir"), None
    if fuel is not None:
        bx = pygame.Rect(bw // 2 + 20, 8 if cfg.get("perf") else 12, 160, 14 if cfg.get("perf") else 18)
        pygame.draw.rect(S, DIM, bx, 1)
        if cap:
            pct = max(0.0, min(1.0, fuel / cap))
            pygame.draw.rect(S, RED if pct < 0.25 else ORANGE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * pct), bx.h - 4))
        put(S, fsm, f"FUEL {fuel:.1f} t", (bx.right + 10, 6 if cfg.get("perf") else 14), ORANGE)
    put(S, fbig, time.strftime("%H:%M"), (bw - 12, 9), ORANGE, anchor="topright")
    if cfg.get("perf"):
        perf_draw(S, bw // 2 + 20, 27)
    put(S, fsm, game_date().upper(), (bw - 28 - fbig.size(time.strftime("%H:%M"))[0], 16), BLUE, anchor="topright")
    pygame.draw.line(S, DIM, (0, hh - 2), (bw, hh - 2), 1)
    cw, ch = bw // 2, (bh - hh) // 2
    cells = list(BIG_SETS[mode])
    if mode == "COMBATE" and fighter_out(d) and 6 in cells:
        cells[cells.index(6)] = 191                  # caza lanzado: COMBATE + CAZA
    if 74 in cells and not ((d.get("rings") or {}).get("rings") or (d.get("rings") or {}).get("signals")):
        cells[cells.index(74)] = 128
    if 127 in cells and not mkt_show(d):
        cells[cells.index(127)] = 11                 # sin carga: SESION en lugar del MERCADO
    if pax_list(d):                                   # v1.1: con pasajeros, su cuadro en lugar de CARGA / VIAJES
        if mode == "ATRACADO" and 4 in cells:
            cells[cells.index(4)] = 210
        elif mode == "VIAJE" and 190 in cells:
            cells[cells.index(190)] = 210
    if mode == "ATRACADO" and 4 in cells:
        cells[cells.index(4)] = atr_cell(d, now)
    if mega_dock(d) and 133 in cells:
        cells[cells.index(133)] = 61                 # mega nave: REGISTRO DE COMBATE en lugar de GALNET
    if mode != "COMBATE" and len(cells) >= 3 and 10 not in cells and mining_active(d, now) and not (d.get("Flags2", 0) & 1):
        cells[2] = 10                                # minando: MINERIA en el cuadro 3
    if d.get("target") and mode != "COMBATE" and len(cells) >= 3:
        k_ = next((c for c in (71, 72) if c in cells), cells[2])
        cells[cells.index(k_)] = 177                  # nave fijada sin armas: su ficha
    if mode == "SUPERFICIE" and flags & (1 << 26) and "rhino" in (d.get("srvtype") or "").lower():
        cells = [100, 74, 5, 10]
    if len(cells) == 1:
        cell.fill(BLACK)
        try:
            VIEWS[cells[0]](cell, d, flags, now)
        except Exception as e:
            put(cell, F["small"], f"error: {e}"[:60], (8, TOP + 8), RED)
        big_blit(S, cell.subsurface((0, TOP, W, H - TOP)), pygame.Rect(4, hh + 4, bw - 8, bh - hh - 8))
        return
    bm = cfg.get("bigmode", "4")
    if bm == "GRANDE":
        # un cuadro a pantalla completa (letra al doble); van rotando cada BIG_ROT segundos
        k = int(now // BIG_ROT) % len(cells)
        r = pygame.Rect(0, hh, bw, bh - hh)
        big_cell(S, cell, cells[k], d, flags, now, r, fbig, "fit", f"  {k + 1}/{len(cells)}")
        pct = (now % BIG_ROT) / BIG_ROT
        pygame.draw.rect(S, DIM, (r.right - 130, r.y + 14, 110, 6), 1)
        pygame.draw.rect(S, ORANGE, (r.right - 129, r.y + 15, int(108 * pct), 4))
        return
    if bm == "MIXTO":
        # el cuadro principal grande a la izquierda; los demas pequenos a la derecha
        main = cells[1] if len(cells) > 1 else cells[0]
        rest = [c for c in cells if c != main][:3]
        bwl = bw * 2 // 3
        big_cell(S, cell, main, d, flags, now, pygame.Rect(0, hh, bwl, bh - hh), fbig, "top")
        if rest:
            h3 = (bh - hh) // len(rest)
            for k, v in enumerate(rest):
                big_cell(S, cell, v, d, flags, now, pygame.Rect(bwl, hh + k * h3, bw - bwl, h3), fsm, "fill")
        return
    if len(cells) == 3 and cells[2] == 150:
        # combate a pie: EN VIVO arriba a la izquierda, botones abajo a la izquierda y el MAPA a toda la altura
        big_cell(S, cell, cells[0], d, flags, now, pygame.Rect(0, hh, cw, ch), fsm, "fill")
        big_cell(S, cell, cells[1], d, flags, now, pygame.Rect(0, hh + ch, cw, ch), fsm, "fill")
        big_cell(S, cell, 150, d, flags, now, pygame.Rect(cw, hh, cw, bh - hh), fsm, "fill")
        return
    if len(cells) == 2:
        for i, v in enumerate(cells):
            big_cell(S, cell, v, d, flags, now, pygame.Rect(i * cw, hh, cw, bh - hh), fbig, "fit")
        return
    for i, v in enumerate(cells):
        r = pygame.Rect((i % 2) * cw, hh + (i // 2) * ch, cw, ch)
        big_cell(S, cell, v, d, flags, now, r, fsm, "fill")

def render_big():
    render_big_base()
    try:
        S = BIG.get("surf")
        if S is None or hdmi_panel():
            return
        with lock:
            d = state["data"]
        now = time.time()
        left, x = exit_left(d, now)
        if left is None:
            return
        bw = BIG["w"]
        box = pygame.Rect(bw // 2 - 400, BIG["h"] - 160, 800, 150)
        pygame.draw.rect(S, BLACK, box, border_radius=12)
        pygame.draw.rect(S, RED if left < 60 else ORANGE, box, 3, border_radius=12)
        fb, fs = BIG.get("fonts") or (pygame.font.Font(None, 40), pygame.font.Font(None, 26))
        S.blit(fb.render("DENTRO DE LA ESTACIÓN", True, ORANGE), (box.x + 20, box.y + 18))
        S.blit(fs.render("sal por la ranura · " + (x.get("st") or ""), True, DIM), (box.x + 20, box.y + 60))
        draw_flip(S, pygame.Rect(box.right - 290, box.y + 16, 270, 118), mmss(left), clock_col(left, now), now, "exitbig")
    except Exception as e:
        log_exc("salida pantalla grande", e)


# ========== view_pp: cadena de 2 etapas, cada una llama a la anterior ==========
# view_pp_base -> view_pp

def view_pp_base(surf, d, flags, now):
    S = (d or {}).get("sysinfo") or {}
    me = (d or {}).get("ppme") or {}
    y = TOP + 4
    put(surf, F["small"], "POWERPLAY DEL SISTEMA", (8, y), DIM)
    if S.get("ppstate"):
        put(surf, F["small"], S["ppstate"], (W - 8, y), BLUE, anchor="topright")
    y += 16
    pp, mine = S.get("pp"), me.get("power")
    if pp:
        put(surf, F["big"], pp.upper(), (8, y), BLUE, W - 130)
        if mine:
            put(surf, F["btn"], "TU POTENCIA" if pp == mine else "RIVAL", (W - 8, y + 4), GREEN if pp == mine else RED, anchor="topright")
        y += 30
        prog = S.get("pp_prog")
        if prog is not None:
            put(surf, F["small"], "CONTROL", (8, y + 2), DIM)
            bx = pygame.Rect(80, y, 300, 16)
            pygame.draw.rect(surf, DIM, bx, 1)
            pygame.draw.rect(surf, BLUE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * max(0, min(1, prog))), bx.h - 4))
            put(surf, F["btn"], f"{prog * 100:.0f}%", (W - 8, y - 2), WHITE, anchor="topright")
            y += 24
        ri, un = S.get("pp_reinf"), S.get("pp_under")
        if ri is not None or un is not None:
            ri, un = ri or 0, un or 0
            tot = max(1, ri + un)
            put(surf, F["small"], "REFUERZO", (8, y + 2), DIM)
            put(surf, F["btn"], f"{ri:,}".replace(",", "."), (150, y - 1), GREEN, anchor="topright")
            put(surf, F["small"], "SABOTAJE", (250, y + 2), DIM)
            put(surf, F["btn"], f"{un:,}".replace(",", "."), (W - 8, y - 1), RED, anchor="topright")
            y += 20
            bx = pygame.Rect(8, y, W - 16, 10)
            pygame.draw.rect(surf, RED, bx)
            pygame.draw.rect(surf, GREEN, (bx.x, bx.y, int(bx.w * ri / tot), bx.h))
            y += 18
    else:
        put(surf, F["big"], "SIN POTENCIA", (8, y), DIM); y += 30
    conf = S.get("pp_conf") or []
    if conf:
        put(surf, F["small"], "CONQUISTA EN CURSO (100% = toma el control)", (8, y), DIM); y += 16
        for power, cp in conf[:4]:
            col = GREEN if power == mine else ORANGE
            put(surf, F["small"], power, (8, y + 1), col, 170)
            bx = pygame.Rect(184, y + 2, 220, 12)
            pygame.draw.rect(surf, DIM, bx, 1)
            pygame.draw.rect(surf, col, (bx.x + 2, bx.y + 2, int((bx.w - 4) * max(0, min(1, cp))), bx.h - 4))
            put(surf, F["small"], f"{cp * 100:.0f}%", (W - 8, y + 1), WHITE, anchor="topright")
            y += 18
    elif S.get("powers") and not pp:
        put(surf, F["small"], "presentes: " + ", ".join(S["powers"]), (8, y), DIM, W - 16); y += 18
    pygame.draw.line(surf, DIM, (8, H - 44), (W - 8, H - 44))
    if mine:
        put(surf, F["small"], "TU POTENCIA", (8, H - 40), DIM)
        put(surf, F["btn"], mine, (100, H - 43), GREEN if pp == mine else ORANGE, 200)
        put(surf, F["small"], f"RANGO {me.get('rank', '?')}", (W - 8, H - 40), WHITE, anchor="topright")
        m = me.get("merits")
        put(surf, F["small"], f"Méritos: {m:,}".replace(",", ".") if m is not None else "Méritos: ?", (8, H - 20), ORANGE)
        if me.get("session"):
            put(surf, F["small"], f"+{me['session']:,} en esta sesión".replace(",", "."), (W - 8, H - 20), GREEN, anchor="topright")
    else:
        put(surf, F["small"], "No estás alineado con ninguna potencia", (8, H - 30), DIM)

def view_pp(surf, d, flags, now):
    view_pp_base(surf, d, flags, now)
    w = (d or {}).get("ppweek") or {}
    if not w.get("end"):
        return
    left = max(0, int(w["end"] - time.time()))
    pygame.draw.rect(surf, BLACK, (0, H - 18, W, 18))
    put(surf, F["small"], f"ESTA SEMANA: {fnum(w.get('merits', 0), 0)} méritos  ·  corte en {left // 86400} d {left % 86400 // 3600} h",
        (8, H - 16), BLUE, W - 16)


# ========== voice_ok: cadena de 2 etapas, cada una llama a la anterior ==========
# voice_ok_base -> voice_ok

def voice_ok_base():
    return bool(shutil.which("espeak-ng"))

def voice_ok():
    return piper_ok() or voice_ok_base()


# ========== voice_say: cadena de 3 etapas, cada una llama a la anterior ==========
# voice_say_base -> voice_say_0 -> voice_say

def voice_say_base(text):
    if not cfg.get("voice") or not voice_ok():
        return
    t = re.sub(r"[¡!¿?>|·_]", " ", text or "")
    t = re.sub(r"\s+", " ", t).strip(" .")
    if not t or time.time() - voice["last"].get(t, 0) < 30:      # no repetir lo mismo en 30 s
        return
    p_ = voice["proc"]
    if p_ and p_.poll() is None:                                  # ya esta hablando
        return
    voice["last"][t] = time.time()
    try:
        voice["proc"] = subprocess.Popen(["espeak-ng", "-v", "es", "-s", "150", "-a", "130", t],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass

def voice_say_0(text):
    if not cfg.get("voice") or not piper_ok():
        return voice_say_base(text)
    t = re.sub(r"[¡!¿?>|·_]", " ", text or "")
    t = re.sub(r"\s+", " ", t).strip(" .")
    if not t or time.time() - voice["last"].get(t, 0) < 30:
        return
    p_ = voice["proc"]
    if voice.get("busy") or (p_ and p_.poll() is None):
        return
    voice["last"][t] = time.time()
    voice["busy"] = True
    threading.Thread(target=_piper_play, args=(t,), daemon=True).start()

def voice_say(text):
    return voice_say_0(voz_txt(text))


# ========== voz_txt: cadena de 2 etapas, cada una llama a la anterior ==========
# voz_txt_base -> voz_txt

def voz_txt_base(t):
    t = t or ""
    t = re.sub(r"(?<![\d.,])1(?:[.,]0)?\s*M\s*cr\b", "un millón de créditos", t)
    t = re.sub(r"(\d+(?:[.,]\d+)?)\s*M\s*cr\b", r"\1 millones de créditos", t)
    t = re.sub(r"(\d+(?:[.,]\d+)?)\s*[kK]\s*cr\b", r"\1 mil créditos", t)
    return re.sub(r"\bcr\b", "créditos", t, flags=re.I)

def voz_txt(t):
    t = voz_txt_base(t)
    t = re.sub(r"#\d+", "", t)
    n_ = r"(\d+(?:[.,]\d+)?)\s*"
    for pat, rep_ in ((n_ + r"m/s\b", r"\1 metros por segundo"), (n_ + r"km\b", r"\1 kilómetros"), (n_ + r"ls\b", r"\1 segundos luz"),
                      (n_ + r"al\b", r"\1 años luz"), (n_ + r"t\b", r"\1 toneladas"), (n_ + r"M\b", r"\1 millones"), (n_ + r"k\b", r"\1 mil")):
        t = re.sub(pat, rep_, t)
    t = re.sub(r"\bZC\b", "zona de conflicto", t)
    return re.sub(r"\bcmdrs?\b", "comandantes", t, flags=re.I)
