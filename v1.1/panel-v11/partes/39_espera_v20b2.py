# Panel Elite v2.0 · parte 39: v2.0b2 — PANTALLA DE ESPERA a 1280x800 de verdad (HDMI, con PANTALLA v2)
#   Reloj y GALNET, CDSN (RADAR · SISTEMAS · VISITAS · RESUMEN) y ACTIVIDAD GALÁCTICA dibujados en el lienzo de
#   1280x800: pantalla entera, sin franjas en la de 10" y con letras pensadas para 10".
#   Mismos datos y reglas que las pantallas de 480x320 (que siguen en el MENÚ hasta que les toque su beta).
#   Toques propios en coordenadas del lienzo (LZ["hits"]); en AUTO la espera va a 10 imágenes por segundo.
#   Si algo falla o el CDSN está en CLÁSICO, se dibuja como en la v2.0b1 (puente nítido).

# La superficie del lienzo se llama «ScaledSurf» por dentro: así put(), act_bg() y draw_hold() la tratan como tal.
LienzoSurf = type("ScaledSurf", (LienzoSurf,), {})

LZ.update(hits=[], modo=None, crawl=None)

def lz_hit(r, *accion):
    LZ["hits"].append((pygame.Rect(r), accion))

def lz_boton(L, r, txt, on=False, col=None, accion=None, font=None):
    col = col or CWC["nar"]
    r = pygame.Rect(r)
    if on:
        pygame.draw.rect(L, col, r, border_radius=8)
    else:
        pygame.draw.rect(L, CWC["fondo"], r, border_radius=8)
        pygame.draw.rect(L, col, r, 2, border_radius=8)
    put(L, font or F["small"], txt, r.center, BLACK if on else col, r.w - 10, anchor="center")
    if accion:
        lz_hit(r, *accion)

def lz_icono(L, ico, x, y, col, t=24):
    """espadas (guerra) o sobre (elecciones) de t x t píxeles con la esquina arriba-izquierda en x, y."""
    if ico == "espadas":
        pygame.draw.line(L, col, (x, y), (x + t, y + t), 4)
        pygame.draw.line(L, col, (x + t, y), (x, y + t), 4)
        pygame.draw.line(L, col, (x, y + t * 0.65), (x + t * 0.35, y + t), 3)
        pygame.draw.line(L, col, (x + t * 0.65, y + t), (x + t, y + t * 0.65), 3)
        return t + 8
    if ico == "sobre":
        pygame.draw.rect(L, col, (x, y + 2, t + 4, t * 0.8), 2)
        pygame.draw.lines(L, col, False, [(x, y + 2), (x + t / 2 + 2, y + t * 0.5), (x + t + 4, y + 2)], 2)
        return t + 12
    return 0

def lz_tag(L, a, x, y, maxw, now, caja=True, font=None):
    if not a or not a[0] and a[1] != "EXPANSIÓN PEND.":
        return 0
    font = font or F["tiny"]
    col = CWC.get(a[3], CWC["rojo"])
    if a[5] and not cw_parp(now):
        col = cw_mix(col, CWC["fondo"], 0.6)
    h = font.get_height() + 8
    w = min(maxw, (32 if a[4] else 0) + tw_(font, a[1]) + 18)
    if caja:
        pygame.draw.rect(L, cw_mix(col, CWC["fondo"], 0.8), (x, y, w, h), border_radius=6)
        pygame.draw.rect(L, col, (x, y, w, h), 2, border_radius=6)
    dx = lz_icono(L, a[4], x + 8, y + (h - 22) // 2, col, 20)
    put(L, font, a[1], (x + 8 + dx, y + 4), col, w - 14 - dx)
    return w

def lz_paginas(L, n, por, i, y, x1=LW - 20):
    pags = max(1, (n + por - 1) // por)
    CW["pg"][i] %= pags
    if pags > 1:
        put(L, F["tiny"], f"pág. {CW['pg'][i] + 1}/{pags}", (x1 - 250, y + 10), CWC["dim"], anchor="topright")
        lz_boton(L, (x1 - 236, y, 110, 48), "^", accion=("pagm", i))
        lz_boton(L, (x1 - 110, y, 110, 48), "v", accion=("pag", i))
    return CW["pg"][i] * por

# ---------------------------------------------------------------------------------------------------------------
# botón FIJAR / SEGUIR (arriba a la derecha en todas las pantallas de espera)
# ---------------------------------------------------------------------------------------------------------------
LZ_HOLD = pygame.Rect(LW - 120, 14, 104, 104)

def lz_hold(L, now):
    r = LZ_HOLD
    held = IDLEHOLD["m"] is not None
    pygame.draw.rect(L, BLACK, r, border_radius=8)
    src = b10_hold_img("boton_fijado.png" if held else "boton_seguir.png")
    if src is not None:
        ir = pygame.Rect(r.x + 4, r.y + 4, r.w - 8, r.h - 40)
        rr = L._r(ir)
        k = ("lz", id(src), rr.w, rr.h)
        if k not in _BIMGC:
            try:
                _BIMGC[k] = pygame.transform.smoothscale(src, (rr.w, rr.h))
            except ValueError:
                _BIMGC[k] = pygame.transform.scale(src, (rr.w, rr.h))
        L.real.blit(_BIMGC[k], rr.topleft)
    col = (RED if int(now * 2) % 2 else (120, 0, 0)) if held else ORANGE
    pygame.draw.rect(L, col, r, 3, border_radius=8)
    put(L, F["tiny"], "SEGUIR" if held else "FIJAR", (r.centerx, r.bottom - 18), WHITE if held else ORANGE, anchor="center")
    lz_hit(r.inflate(10, 10), "hold")

# ---------------------------------------------------------------------------------------------------------------
# ESPERA NORMAL: foto, reloj, CMDR y noticias de GALNET que suben
# ---------------------------------------------------------------------------------------------------------------
LZ_GAL = pygame.Rect(30, 372, LW - 60, 362)

def lz_foto(s=1.0):
    img = cmdr_img()
    if not img:
        return None
    key = ("lzfoto", id(img), round(s, 3))
    c = style["cache"]
    if key not in c:
        k = min(300 / img.get_width(), 300 / img.get_height()) * s
        c[key] = pygame.transform.smoothscale(img, (int(img.get_width() * k), int(img.get_height() * k)))
    return c[key]

def lz_crawl_lineas():
    L_ = galnet["list"][:6]
    key = (tuple(n["id"] for n in L_), round(F["btn"].f, 3))
    if LZ["crawl"] is None or LZ["crawl"][0] != key:
        out, w = [], LZ_GAL.w - 40
        for n in L_:
            for t in wrap_lines(F["btn"], n["title"], w):
                out.append((F["btn"], t, ORANGE, 54))
            out.append((F["small"], n["date"], BLUE, 44))
            body = wrap_lines(F["small"], n["body"], w)
            for t in body[:9]:
                out.append((F["small"], t, WHITE, 40))
            if len(body) > 9:
                out.append((F["small"], "...  (sigue en 12.9 GALNET)", DIM, 40))
            out.append((None, "", None, 56))
        LZ["crawl"] = (key, out, sum(h for *_, h in out))
    return LZ["crawl"][1], LZ["crawl"][2]

def lz_galnet(L, now):
    box = LZ_GAL
    pygame.draw.rect(L, DIM, box, 2, border_radius=12)
    put(L, F["small"], "NOTICIAS GALNET", (box.x + 20, box.y + 12), ORANGE)
    if power["now"] and int(now * 2) % 2 == 0:
        put(L, F["small"], "BAJA TENSIÓN", (box.right - 20, box.y + 12), RED, anchor="topright")
    elif int(now) % 4 < 3 and not (state.get("data") or {}).get("menu"):
        t_ = "ESPERANDO A ELITE DANGEROUS"
        w_ = tw_(F["small"], t_) + 30
        r_ = pygame.Rect(box.right - 14 - w_, box.y + 8, w_, 44)
        pygame.draw.rect(L, RED, r_, border_radius=8)
        put(L, F["small"], t_, r_.center, (255, 215, 0), anchor="center")
    pygame.draw.line(L, DIM, (box.x + 14, box.y + 58), (box.right - 14, box.y + 58), 2)
    area = pygame.Rect(box.x + 20, box.y + 64, box.w - 40, box.h - 74)
    lines, total = lz_crawl_lineas()
    if not lines:
        put(L, F["small"], galnet["err"] or "descargando noticias...", area.center, DIM, area.w, anchor="center")
        return
    off = (now * IDLE_SPEED * 2.5) % total
    old = L.get_clip()
    L.set_clip(area)
    y = area.bottom - off
    while y < area.bottom:
        for f, t, col, h in lines:
            if area.y - h < y < area.bottom and f:
                put(L, f, t, (area.x, int(y)), col, area.w)
            y += h
    L.set_clip(old)

def lz_espera_norm(L, now):
    L.fill(BLACK)
    lt = time.localtime(now)
    img = lz_foto(L.sx)
    if img:
        w_, h_ = img.get_width() / L.sx, img.get_height() / L.sy          # tamaño en el lienzo
        r = pygame.Rect(0, 0, w_, h_); r.center = (190, 180)
        L.real.blit(img, L._r(r).topleft)
        pygame.draw.rect(L, ORANGE, r.inflate(16, 16), 3, border_radius=8)
    else:
        draw_emblem(L, 190, 180, 130, now / 3)
    cx = 770
    put(L, F["clock"], time.strftime("%H:%M", lt), (cx, 112), ORANGE, anchor="center")
    put(L, F["btn"], f"{DIAS[lt.tm_wday]} {lt.tm_mday} de {MESES[lt.tm_mon - 1]}", (cx, 232), DIM, anchor="center")
    put(L, F["big"], "CMDR " + cfg["cmdr"], (cx, 290), ORANGE, 820, anchor="center")
    ip = my_ip()
    put(L, F["small"], PANEL_VER.split(" · ")[0], (400, 325), GREEN)
    put(L, F["small"], game_date(), (cx + 10, 325), BLUE, anchor="midtop")
    put(L, F["small"], f"IP {ip}" if ip else "SIN RED", (LW - 30, 325), DIM if ip else RED, anchor="topright")
    lz_galnet(L, now)
    put(L, F["small"], "toca la pantalla para abrir el menú", (LW // 2, LH - 30), DIM, anchor="center")

# ---------------------------------------------------------------------------------------------------------------
# ACTIVIDAD GALÁCTICA
# ---------------------------------------------------------------------------------------------------------------
LZ_ACTM = pygame.Rect(20, 150, 780, 630)
LZ_ACTB = [pygame.Rect(560 + i * 150, 34, 140, 60) for i in range(3)]

def lz_actividad(L, now):
    ACT["want"] = now
    L.fill(BLACK)
    fixed = IDLEHOLD["m"] == "act"
    mode = ACT_MODE[0] if fixed else ("gal", "sol", "col")[int(now // 10) % 3]
    put(L, F["big"], "ACTIVIDAD GALÁCTICA", (30, 20), ORANGE)
    put(L, F["small"], "en directo desde EDDN" if ACT["on"] else "conectando con EDDN…" if act_ok() else "falta python3-zmq en la Pi",
        (30, 88), DIM if act_ok() else RED, 640)
    put(L, F["btn"], time.strftime("%H:%M", time.localtime(now)), (LW - 140, 40), ORANGE, anchor="topright")
    for i, (k, lab) in enumerate(ACT_MODES):
        lz_boton(L, LZ_ACTB[i], lab, k == mode, col=ORANGE, accion=("act", i))
    pygame.draw.line(L, ORANGE, (20, 134), (LW - 20, 134), 2)
    M = LZ_ACTM
    act_bg(L, M, mode)
    pygame.draw.rect(L, DIM, M, 2, border_radius=8)
    pt, sc = act_view_b18(M, mode)
    old = L.get_clip(); L.set_clip(M)
    marks = {"gal": (("SOL", 0, 0), ("COLONIA", -9530, 19808), ("SAG A*", 25, 25900)),
             "col": (("COLONIA", -9530, 19808),), "sol": (("SOL", 0, 0),)}[mode]
    for n, x, z in marks:
        px, py = pt(x, z); pygame.draw.circle(L, DIM, (int(px), int(py)), 8, 2)
        put(L, F["tiny"], n, (int(px) + 14, int(py) - 16), (200, 160, 110))
    if mode == "sol":
        used = []
        for n, v in sorted(((FACD["data"] or {}).get("sistemas") or {}).items(), key=lambda kv: -(kv[1].get("inf") or 0)):
            if v.get("pos") and None not in v["pos"] and not v.get("fuera") and v.get("inf"):
                px, py = pt(v["pos"][0], v["pos"][2])
                if not M.collidepoint(px, py):
                    continue
                pygame.draw.circle(L, ORANGE if v.get("ctrl") else (120, 80, 30), (int(px), int(py)), 7, 0 if v.get("ctrl") else 2)
                if v.get("ctrl"):
                    nm = n if len(n) <= 18 else n[:17] + "…"
                    lr = pygame.Rect(int(px) + 12, int(py) - 16, tw_(F["tiny"], nm), 30)
                    if not M.contains(lr):
                        lr.right = int(px) - 12
                    if M.contains(lr) and not any(lr.colliderect(u) for u in used):
                        used.append(lr); put(L, F["tiny"], nm, lr.topleft, (200, 140, 60))
    for x, z, t, mine in list(ACT["pings"]):
        age = now - t
        if age > 1.6 or age < 0:
            continue
        px, py = pt(x, z)
        if not M.collidepoint(px, py):
            continue
        col = ORANGE if mine else (90, 200, 255)
        f_ = max(0.0, 1 - age / 1.6)
        pygame.draw.circle(L, tuple(int(c * f_) for c in col), (int(px), int(py)), int(5 + age * 25), 2)
        if age < 0.4:
            pygame.draw.circle(L, col, (int(px), int(py)), 5)
    lz_act_aviso(L, M, pt, now)
    L.set_clip(old)
    lz_hit(M, "actmapa")
    X, y = 830, 156
    j = list(ACT["jumps"])
    pm = len(j) - bisect.bisect_left(j, now - 60)
    cm = sum(1 for t in list(ACT["uids"].values()) if now - t < 300)
    put(L, F["small"], "SALTOS POR MINUTO", (X, y), DIM); y += 40
    put(L, F["num"], str(pm), (LW - 30, y), BLUE, anchor="topright"); y += 100
    put(L, F["small"], "COMANDANTES (5 MIN)", (X, y), DIM); y += 40
    put(L, F["big"], str(cm), (LW - 30, y), WHITE, anchor="topright"); y += 70
    hoyk = time.strftime("%Y-%m-%d", time.gmtime())
    ent = sum(((v.get("trafico") or {}).get(hoyk, 0)) for v in ((FACD["data"] or {}).get("sistemas") or {}).values())
    put(L, F["small"], "TUS SISTEMAS HOY", (X, y), DIM)
    put(L, F["big"], str(ent), (LW - 30, y + 30), ORANGE, anchor="topright")
    nv = ACT_DAY.get(hoyk, 0)
    put(L, F["tiny"], f"comandantes · {nv} salto{'' if nv == 1 else 's'} visto{'' if nv == 1 else 's'}", (X, y + 100), DIM, LW - X - 30)
    y += 146
    pygame.draw.line(L, DIM, (X, y), (LW - 20, y), 2); y += 12
    put(L, F["small"], "ÚLTIMOS SALTOS", (X, y), DIM); y += 44
    for nm, mine, t in list(ACT["feed"])[:5]:
        put(L, F["tiny"], nm, (X, y), ORANGE if mine else WHITE, 320)
        put(L, F["tiny"], f"{max(0, int(now - t))} s", (LW - 30, y), DIM, anchor="topright"); y += 34
    return mode

def lz_act_aviso(L, M, pt, now):
    age = now - ACT_HIT["t"]
    if not ACT_HIT["n"] or age > 10 or age < 0:
        return
    px, py = pt(ACT_HIT["x"], ACT_HIT["z"])
    if M.collidepoint(px, py):
        f_ = 1 - age / 10
        for k in range(3):
            rr = int(10 + ((age * 35 + k * 15) % 45))
            pygame.draw.circle(L, tuple(int(c * f_) for c in ORANGE), (int(px), int(py)), rr, 2)
        pygame.draw.circle(L, ORANGE, (int(px), int(py)), 9)
    b = pygame.Rect(M.x + 16, M.bottom - 66, M.w - 32, 50)
    pygame.draw.rect(L, (40, 22, 0), b, border_radius=8)
    pygame.draw.rect(L, ORANGE if int(now * 3) % 2 else (140, 80, 0), b, 2, border_radius=8)
    put(L, F["small"], "COMANDANTE EN " + ACT_HIT["n"].upper(), b.center, ORANGE, b.w - 20, anchor="center")

# ---------------------------------------------------------------------------------------------------------------
# CDSN (como la web): pestañas, franja de avisos, RADAR + ALERTAS / ficha, SISTEMAS, VISITAS, RESUMEN
# ---------------------------------------------------------------------------------------------------------------
LZ_RA = pygame.Rect(0, 140, 770, LH - 140)                    # radar
LZ_RP = pygame.Rect(780, 140, LW - 800, LH - 156)              # panel de la derecha

def lz_cabecera(L, S, now):
    for i, t in enumerate(CW_TABS):
        lz_boton(L, (20 + i * 262, 16, 250, 60), t, CW["tab"] == i, accion=("tab", i), font=F["btn"])
    A = cw_alertas(S)
    alarm = [o for o in A if o["al"][6]]
    inus = [o for o in S if o["al"][1] == "ACTIVIDAD INUSUAL"]
    defe = [o for o in S if o["al"][1] in ("DEFENSA EN CURSO", "A UN DÍA DE GANAR")]
    nexp = sum(1 for o in S if o["exp"])
    xr = LZ_HOLD.x - 16
    if nexp:
        te = f"EXPANSIÓN {nexp}"
        r = pygame.Rect(xr - tw_(F["tiny"], te) - 30, 88, tw_(F["tiny"], te) + 30, 40)
        on = CW["verexp"]
        pygame.draw.rect(L, CWC["av"] if on else CWC["fondo"], r, border_radius=6)
        pygame.draw.rect(L, CWC["av"], r, 2, border_radius=6)
        put(L, F["tiny"], te, r.center, BLACK if on else CWC["av"], r.w - 8, anchor="center")
        lz_hit(r.inflate(6, 10), "exp")
        xr = r.x - 12
    r = pygame.Rect(20, 88, xr - 20, 40)
    if alarm:
        o = alarm[0]; a = o["al"]
        pygame.draw.rect(L, CWC["rojo"] if cw_parp(now) else cw_mix(CWC["rojo"], CWC["fondo"], 0.45), r, border_radius=6)
        put(L, F["small"], f"{a[1]} · {o['s']['sys']}" + (f"  (+{len(alarm) - 1})" if len(alarm) > 1 else ""),
            (r.x + 14, r.y + 3), BLACK, r.w - 24)
        lz_hit(r.inflate(0, 10), "sel", o["s"]["sys"])
    elif inus or defe:
        o = (inus or defe)[0]; a = o["al"]
        col = CWC[a[3]]
        pygame.draw.rect(L, cw_mix(col, CWC["fondo"], 0.8), r, border_radius=6)
        pygame.draw.rect(L, col, r, 2, border_radius=6)
        n = len(inus or defe)
        put(L, F["small"], f"{a[1]} · {o['s']['sys']}" + (f"  (+{n - 1})" if n > 1 else ""), (r.x + 14, r.y + 3), col, r.w - 24)
        lz_hit(r.inflate(0, 10), "sel", o["s"]["sys"])
    else:
        D = FACD["data"] or {}
        put(L, F["small"], f"{len(S)} sistemas · datos del escucha {cw_hace(D.get('t'), now)}" + (" · todo tranquilo" if not A else ""),
            (r.x + 4, r.y + 3), CWC["dim"], r.w - 8)

def lz_radar(L, S, now):
    RA_ = LZ_RA
    cx, cy = RA_.centerx, RA_.centery - 20
    R = min(RA_.w, RA_.h - 40) // 2 - 16
    k = 0.9 * R / CW["d80"] * CW["z"]
    L.set_clip(RA_)
    ang = (now * 90) % 360
    A = lambda a: math.radians(a - 90)
    for i in range(9, -1, -1):
        a1, a2 = ang - (i + 1) * 4, ang - i * 4 + 0.6
        col = cw_mix((200, 110, 0), CWC["fondo"], 0.35 + 0.65 * (i / 10) ** 0.8)
        pts = [(cx, cy)] + [(cx + R * math.cos(A(a1 + (a2 - a1) * j / 3)), cy + R * math.sin(A(a1 + (a2 - a1) * j / 3))) for j in range(4)]
        pygame.draw.polygon(L, col, pts)
    for i in (1, 2, 3):
        pygame.draw.circle(L, CWC["rej"], (cx, cy), R * i // 3, 2)
    pygame.draw.line(L, CWC["rej"], (cx - R, cy), (cx + R, cy), 2)
    pygame.draw.line(L, CWC["rej"], (cx, cy - R), (cx, cy + R), 2)
    pygame.draw.line(L, (255, 200, 90), (cx, cy), (cx + R * math.cos(A(ang)), cy + R * math.sin(A(ang))), 4)
    pulso = (math.sin(now * 6) + 1) / 2
    P = []
    for o in S:
        o["lx"] = None
        if o["x"] is None:
            continue
        dx, dz = (o["x"] - CW["cx"]) * k, (o["z"] - CW["cz"]) * k
        x, y = cx + dx, cy - dz
        o["lx"], o["ly"] = x, y
        if not (RA_.x - 40 < x < RA_.right + 40 and RA_.y - 40 < y < RA_.bottom + 40):
            continue
        a = (math.degrees(math.atan2(dx, dz)) + 360) % 360
        o["lluz"] = max(0.0, 1 - ((ang - a + 360) % 360) / 45) if math.hypot(dx, dz) <= R else 0.0
        P.append(o)
    for o in P:
        x, y, al = o["lx"], o["ly"], o["al"]
        ca = CWC.get(al[3], CWC["rojo"])
        if al[5] and not cw_parp(now):
            ca = cw_mix(ca, CWC["fondo"], 0.65)
        if o["niv"] == 2:
            pygame.draw.circle(L, ca, (x, y), 22 + pulso * 12, 4)
        elif o["niv"] == 1 or (o["exp"] and CW["verexp"]):
            pygame.draw.circle(L, cw_mix(ca, CWC["fondo"], 0.5), (x, y), 19, 2)
    for o in P:
        x, y, s = o["lx"], o["ly"], o["s"]
        col = cw_color_inf(s)
        if o["lluz"] > 0.05:
            col = cw_mix(col, CWC["ilum"], o["lluz"])
        if s.get("ctrl"):
            pygame.draw.rect(L, col, (x - 9, y - 9, 18, 18))
        else:
            pygame.draw.circle(L, col, (x, y), 7)
        if CW["sel"] == s.get("sys"):
            pygame.draw.rect(L, CWC["blanco"], (x - 18, y - 18, 36, 36), 2)
    kz, lab = CW["z"], []
    for pas in ((0, 1, 2) if not CW["ley"] else ()):
        if (pas == 1 and kz < 1.4) or (pas == 2 and kz < 3):
            break
        for o in P:
            s, niv = o["s"], o["niv"]
            ok = niv > 1 if pas == 0 else ((s.get("ctrl") and not niv) or niv == 1) if pas == 1 else (not s.get("ctrl") and not niv)
            if not ok and not (pas == 0 and CW["sel"] == s.get("sys")):
                continue
            n = s.get("sys") or "?"
            x, y = o["lx"] + (38 if niv else 18), o["ly"] - 16
            wd = tw_(F["tiny"], n)
            if x + wd > RA_.right - 6:                        # no cabe a la derecha: a la izquierda del punto
                x = o["lx"] - (38 if niv else 18) - wd
            if x < RA_.x or y < RA_.y or y > RA_.bottom:
                continue
            if any(x < r[0] + r[2] + 6 and r[0] < x + wd + 6 and abs(y - r[1]) < 30 for r in lab):
                continue
            lab.append((x, y, wd))
            put(L, F["tiny"], n, (x, y), CWC.get(o["al"][3], CWC["rojo"]) if niv else CWC["blanco"] if s.get("ctrl") else CWC["nmed"])
    L.set_clip(None)
    put(L, F["tiny"], f"anillo {round(R / 3 / k)} ly", (RA_.right - 10, RA_.bottom - 44), CWC["rej"], anchor="topright")
    lz_hit(RA_, "radar")
    for i, (t, acc) in enumerate((("+", "zoom+"), ("−", "zoom-"), ("C", "centro"), ("?", "ley"))):
        lz_boton(L, (20 + i * 80, RA_.bottom - 64, 70, 56), t, t == "?" and CW["ley"], accion=(acc,), font=F["btn"])
    if CW["ley"]:
        lz_leyenda(L, now)

def lz_leyenda(L, now):
    r = pygame.Rect(LZ_RA.x + 16, LZ_RA.y + 8, LZ_RA.w - 32, LZ_RA.h - 84)
    pygame.draw.rect(L, CWC["panel"], r, border_radius=12)
    pygame.draw.rect(L, CWC["nar"], r, 2, border_radius=12)
    put(L, F["small"], "LEYENDA DEL MAPA", (r.x + 20, r.y + 12), CWC["nar"])
    y = r.y + 60
    def fila(dib, txt, col=None):
        nonlocal y
        dib(r.x + 40, y + 15)
        put(L, F["tiny"], txt, (r.x + 80, y), col or CWC["blanco"], r.w - 100)
        y += 36
    fila(lambda x, yy: pygame.draw.rect(L, CWC["verde"], (x - 9, yy - 9, 18, 18)), "controlado (verde > 50 %, amarillo > 20 %)")
    fila(lambda x, yy: pygame.draw.circle(L, CWC["nar"], (x, yy), 7), "presencia, sin control")
    fila(lambda x, yy: pygame.draw.circle(L, CWC["rojo"], (x, yy), 16, 4), "aro grueso que late: alerta grave")
    fila(lambda x, yy: pygame.draw.circle(L, cw_mix(CWC["av"], CWC["fondo"], .5), (x, yy), 16, 2), "aro fino: aviso leve (nombre con zoom)")
    fila(lambda x, yy: pygame.draw.circle(L, CWC["verde"] if cw_parp(now) else cw_mix(CWC["verde"], CWC["fondo"], .65), (x, yy), 16, 4),
         "parpadea (se atenúa): conflicto en marcha")
    for t, k_ in (("rojo: derrota, día decisivo, ataque, retirada", "gr"), ("amarillo: conflicto disputado", "di"),
                  ("naranja: bajada, actividad inusual", "av"), ("verde: defensa, victoria, a favor", "fa"),
                  ("morado: conflicto pendiente", "pu")):
        fila(lambda x, yy, c=CWC[k_]: pygame.draw.circle(L, c, (x, yy), 14, 4), t, CWC[k_])
    fila(lambda x, yy: lz_icono(L, "espadas", x - 11, yy - 11, CWC["nar"], 22), "guerra")
    fila(lambda x, yy: lz_icono(L, "sobre", x - 13, yy - 10, CWC["nar"], 22), "elecciones")
    fila(lambda x, yy: pygame.draw.rect(L, CWC["blanco"], (x - 16, yy - 16, 32, 32), 2), "sistema marcado")
    put(L, F["tiny"], "EXPANSIÓN (arriba): ver u ocultar sus aros", (r.x + 20, y + 4), CWC["av"], r.w - 40)

def lz_panel(L, S, now):
    RP_ = LZ_RP
    pygame.draw.rect(L, CWC["panel"], RP_, border_radius=12)
    o = next((o for o in S if o["s"].get("sys") == CW["sel"]), None) if CW["sel"] else None
    if o:
        lz_ficha_corta(L, o, now); return
    A = cw_alertas(S)
    put(L, F["small"], f"ALERTAS ({len(A)})", (RP_.x + 18, RP_.y + 12), CWC["nar"])
    rh = 84
    por = (RP_.h - 130) // rh
    pg = CW["pg"][0] % max(1, (len(A) + por - 1) // por)
    CW["pg"][0] = pg
    y = RP_.y + 62
    for o in A[pg * por:(pg + 1) * por]:
        a, s = o["al"], o["s"]
        r = pygame.Rect(RP_.x + 12, y, RP_.w - 24, rh - 8)
        col = CWC.get(a[3], CWC["rojo"])
        pygame.draw.rect(L, CWC["fondo"], r, border_radius=8)
        pygame.draw.rect(L, col if not (a[5] and not cw_parp(now)) else cw_mix(col, CWC["fondo"], .6), (r.x, r.y, 7, r.h))
        put(L, F["small"], s.get("sys"), (r.x + 20, r.y + 4), CWC["blanco"] if s.get("ctrl") else CWC["nar"], r.w - 30)
        lz_tag(L, a, r.x + 16, r.y + 40, r.w - 30, now, caja=False)
        lz_hit(r, "sel", s.get("sys"))
        y += rh
    if not A:
        put(L, F["small"], "todo tranquilo", (RP_.centerx, RP_.y + 130), CWC["verde"], anchor="center")
    if len(A) > por:
        n = (len(A) + por - 1) // por
        lz_boton(L, (RP_.x + 12, RP_.bottom - 62, RP_.w - 24, 50), f"más  v   {pg + 1}/{n}", accion=("pag", 0))

def lz_ficha_corta(L, o, now):
    RP_ = LZ_RP
    s, a = o["s"], o["al"]
    x, y, w = RP_.x + 18, RP_.y + 12, RP_.w - 36
    put_fit(L, ("big", "btn", "small", "tiny"), s.get("sys"), (x, y), CWC["blanco"] if s.get("ctrl") else CWC["nar"], w - 70)
    lz_boton(L, (RP_.right - 64, RP_.y + 10, 52, 52), "×", accion=("x",), font=F["btn"])
    y += 66
    put(L, F["tiny"], "CONTROLADO" if s.get("ctrl") else "presencia", (x, y), CWC["verde"] if s.get("ctrl") else CWC["dim"]); y += 36
    inf, pv = s.get("inf") or 0, s.get("prev")
    t_ = f"influencia {c1(inf)} %"
    put(L, F["btn"], t_, (x, y), cw_color_inf(s))
    if pv is not None:
        put(L, F["tiny"], f"  ({'+' if inf - pv >= 0 else ''}{c1(inf - pv)} ayer)", (x + tw_(F["btn"], t_) + 4, y + 12),
            CWC["verde"] if inf - pv >= 0 else CWC["rojo"])
    y += 56
    if s.get("segunda"):
        put(L, F["tiny"], f"ventaja {c1(inf - (s.get('segunda_inf') or 0))} sobre {s.get('segunda')}", (x, y), CWC["dim"], w); y += 38
    if a[0] or a[1]:
        y += 4; lz_tag(L, a, x, y, w, now); y += 50
        for ln in cw_lineas(F["tiny"], a[2], w, 4):
            put(L, F["tiny"], ln, (x, y), CWC["blanco"]); y += 32
    est = [CW_ES.get(e, e) for e in (s.get("activos") or [])] + [CW_ES.get(e, e) + " (pend.)" for e in (s.get("pendientes") or [])]
    if est:
        y += 6
        for ln in cw_lineas(F["tiny"], "estados: " + ", ".join(est), w, 2):
            put(L, F["tiny"], ln, (x, y), CWC["nar"]); y += 32
    t = s.get("trafico") or {}
    y += 6
    put(L, F["tiny"], f"visitas hoy {t.get(cw_dia(0, now)) or 0} · ayer {t.get(cw_dia(1, now)) or 0}", (x, y), CWC["az"], w)
    lz_boton(L, (RP_.x + 12, RP_.bottom - 64, RP_.w - 24, 52), "FICHA COMPLETA  >", accion=("ficha", s.get("sys")))

def lz_sistemas(L, S, now):
    Ls = sorted(S, key=cw_orden)
    y0, rh = 186, 44
    por = (LH - 76 - y0) // rh
    for t, xx, an in (("Sistema", 24, "topleft"), ("Infl.", 610, "topright"), ("Ayer", 730, "topright"),
                      ("Vent.", 850, "topright"), ("Aviso", 880, "topleft")):
        put(L, F["tiny"], t, (xx, 144), CWC["dim"], anchor=an)
    pygame.draw.line(L, CWC["linea"], (12, 180), (LW - 12, 180), 2)
    i0 = lz_paginas(L, len(Ls), por, 1, LH - 62)
    for j, o in enumerate(Ls[i0:i0 + por]):
        s, a = o["s"], o["al"]
        y = y0 + j * rh
        r = pygame.Rect(8, y, LW - 16, rh - 2)
        if j % 2:
            pygame.draw.rect(L, CWC["panel"], r)
        if a[0]:
            pygame.draw.rect(L, CWC.get(a[3], CWC["rojo"]), (8, y, 7, rh - 2))
        put(L, F["small"], s.get("sys"), (24, y + 3), CWC["blanco"] if s.get("ctrl") else CWC["nar"], 480)
        inf, pv = s.get("inf") or 0, s.get("prev")
        put(L, F["small"], c1(inf), (610, y + 3), cw_color_inf(s), anchor="topright")
        if pv is not None:
            d_ = inf - pv
            put(L, F["tiny"], ("+" if d_ >= 0 else "") + c1(d_), (730, y + 7),
                CWC["verde"] if d_ > 0.05 else CWC["rojo"] if d_ < -0.05 else CWC["dim"], anchor="topright")
        if s.get("segunda") is not None:
            v = inf - (s.get("segunda_inf") or 0)
            put(L, F["tiny"], c1(v), (850, y + 7), CWC["rojo"] if s.get("ctrl") and v < 5 else CWC["dim"], anchor="topright")
        if a[0] or o["exp"]:
            lz_tag(L, a, 874, y + 2, LW - 890, now, caja=False)
        lz_hit(r, "ficha", s.get("sys"))
    put(L, F["tiny"], f"{len(Ls)} sistemas · {sum(1 for o in Ls if o['s'].get('ctrl'))} controlados · toca uno para su ficha",
        (20, LH - 50), CWC["dim"], LW - 560)

def lz_visitas(L, S, now):
    dias = [cw_dia(n, now) for n in range(5)]
    Lv = []
    for o in S:
        t = o["s"].get("trafico") or {}
        serie = [t.get(d) or 0 for d in reversed(dias)]
        a1 = o["al"][1]
        at = 3 if a1 == "POSIBLE ATAQUE" else 2 if a1 == "ACTIVIDAD INUSUAL" else 1 if a1 == "ACTIVIDAD A FAVOR" else 0
        if sum(serie) or at:
            m = sum(t.get(cw_dia(i, now)) or 0 for i in range(1, 8)) / 7
            Lv.append(dict(o=o, at=at, hoy=serie[-1], ayer=serie[-2], m=m, serie=serie))
    Lv.sort(key=lambda v: (-v["at"], -v["hoy"], -sum(v["serie"]), -(v["o"]["s"].get("inf") or 0)))
    tot = sum(v["hoy"] for v in Lv)
    put(L, F["small"], f"hoy {tot} visitas en {sum(1 for v in Lv if v['hoy'])} sistemas · {len(S) - len(Lv)} sin visitas en 5 días",
        (24, 140), CWC["az"], LW - 48)
    y0, rh = 230, 44
    for t, xx, an in (("Sistema", 24, "topleft"), ("Hoy", 560, "topright"), ("Ayer", 660, "topright"),
                      ("Media", 770, "topright"), ("5 días", 800, "topleft"), ("Aviso", 960, "topleft")):
        put(L, F["tiny"], t, (xx, 188), CWC["dim"], anchor=an)
    pygame.draw.line(L, CWC["linea"], (12, 224), (LW - 12, 224), 2)
    por = (LH - 76 - y0) // rh
    i0 = lz_paginas(L, len(Lv), por, 2, LH - 62)
    for j, v in enumerate(Lv[i0:i0 + por]):
        o = v["o"]; s, a = o["s"], o["al"]
        y = y0 + j * rh
        r = pygame.Rect(8, y, LW - 16, rh - 2)
        if j % 2:
            pygame.draw.rect(L, CWC["panel"], r)
        put(L, F["small"], s.get("sys"), (24, y + 3), CWC["blanco"] if s.get("ctrl") else CWC["nar"], 440)
        put(L, F["small"], str(v["hoy"]), (560, y + 3), CWC["az"] if v["hoy"] else CWC["dim"], anchor="topright")
        put(L, F["tiny"], str(v["ayer"]), (660, y + 7), CWC["az"] if v["ayer"] else CWC["dim"], anchor="topright")
        put(L, F["tiny"], c1(v["m"]), (770, y + 7), CWC["dim"], anchor="topright")
        mx = max(1, max(v["serie"]))
        for k_, n in enumerate(v["serie"]):
            hh = max(2, round(n / mx * 32)) if n else 2
            pygame.draw.rect(L, CWC["az"] if n else CWC["linea"], (804 + k_ * 28, y + 38 - hh, 20, hh))
        if v["at"]:
            lz_tag(L, a, 954, y + 2, LW - 970, now, caja=False)
        lz_hit(r, "ficha", s.get("sys"))
    if not Lv:
        put(L, F["small"], "nadie ha pasado por nuestros sistemas en 5 días", (LW // 2, 420), CWC["dim"], anchor="center")
    put(L, F["tiny"], "pilotos distintos por día que envían datos a EDDN", (20, LH - 50), CWC["dim"], LW - 560)

def lz_resumen(L, S, now):
    A = cw_alertas(S)
    t0 = cw_dia(0, now)
    cajas = [("SISTEMAS", len(S), CWC["nar"]), ("CONTROLADOS", sum(1 for o in S if o["s"].get("ctrl")), CWC["blanco"]),
             ("GRAVES", sum(1 for o in A if o["niv"] == 2), CWC["rojo"]),
             ("VISITAS HOY", sum((o["s"].get("trafico") or {}).get(t0) or 0 for o in S), CWC["az"])]
    for i, (t, n, col) in enumerate(cajas):
        r = pygame.Rect(20 + i * 312, 140, 300, 100)
        pygame.draw.rect(L, CWC["panel"], r, border_radius=10)
        put(L, F["big"], str(n), (r.centerx, r.y + 6), col, anchor="midtop")
        put(L, F["tiny"], t, (r.centerx, r.bottom - 36), CWC["dim"], anchor="midtop")
    T = cw_tareas(now)
    put(L, F["small"], "QUÉ HACER HOY" + (f"  ·  {len(T)} sistemas, de más a menos urgente" if T else ""), (24, 254), CWC["nar"], LW - 48)
    y0, rh = 300, 112
    por = (LH - 76 - y0) // rh
    i0 = lz_paginas(L, len(T), por, 3, LH - 62)
    for j, t in enumerate(T[i0:i0 + por]):
        s = t["s"]
        y = y0 + j * rh
        r = pygame.Rect(8, y, LW - 16, rh - 6)
        pygame.draw.rect(L, CWC["panel"], r, border_radius=8)
        pygame.draw.rect(L, CWC.get(t["k"], CWC["rojo"]), (8, y, 7, rh - 6))
        wn = put(L, F["small"], s.get("sys"), (24, y + 4), CWC["blanco"] if s.get("ctrl") else CWC["nar"], 520)
        lz_tag(L, [1, t["tag"], "", t["k"], t["ico"], t["parp"], False], 40 + wn, y + 4, LW - 80 - wn, now)
        put(L, F["tiny"], t["por"], (24, y + 44), CWC["dim"], LW - 48)
        put(L, F["tiny"], "> " + t["acc"], (24, y + 74), CWC["verde"], LW - 48)
        lz_hit(r, "ficha", s.get("sys"))
    if not T:
        put(L, F["small"], "Todo tranquilo: ningún sistema necesita ayuda ahora mismo.", (LW // 2, 460), CWC["verde"], anchor="center")
    D = FACD["data"] or {}
    put(L, F["tiny"], f"datos del escucha {cw_hace(D.get('t'), now)}", (20, LH - 50), CWC["dim"], LW - 560)

def lz_cdsn(L, now):
    L.fill(CWC["fondo"])
    S = cw_datos(now)
    if CW["sel"] and not any(o["s"].get("sys") == CW["sel"] for o in S):
        CW["sel"] = None
    lz_cabecera(L, S, now)
    tab = CW["tab"]
    if tab == 0:
        lz_radar(L, S, now)
        lz_panel(L, S, now)
    elif tab == 1:
        lz_sistemas(L, S, now)
    elif tab == 2:
        lz_visitas(L, S, now)
    else:
        lz_resumen(L, S, now)

# ---------------------------------------------------------------------------------------------------------------
# la espera entera: elige la pantalla (como draw_idle) y la dibuja en el lienzo
# ---------------------------------------------------------------------------------------------------------------
def lz_espera_modo(now):
    m = IDLEHOLD["m"]
    if m:
        return m
    D, S, gap = fac_rows()
    modes = ["norm"] + (["fac"] if S else []) + (["act"] if act_enabled() else [])
    return modes[int(now // 20) % len(modes)]

def lz_espera_puede(now):
    """False si la pantalla que toca no tiene versión de 1280x800 (CDSN en CLÁSICO): se usa el puente."""
    return not (lz_espera_modo(now) == "fac" and not cdsn_on())

def lz_espera(L, now, rotulo=None):
    LZ["hits"] = []
    m = lz_espera_modo(now)
    IDLE_MODE.update(m=m, t=time.time())
    LZ["modo"] = m
    if m == "fac":
        lz_cdsn(L, now)
    elif m == "act":
        lz_actividad(L, now)
    else:
        lz_espera_norm(L, now)
    lz_hold(L, now)
    if rotulo:
        pygame.draw.rect(L, BLACK, (0, LH - 70, LW, 70))
        put(L, F["big"], rotulo, (LW // 2, LH - 36), GREEN, anchor="center")

# ---------------------------------------------------------------------------------------------------------------
# toques en la espera de 1280x800
# ---------------------------------------------------------------------------------------------------------------
def lz_toque_espera(X, Y):
    now = time.time()
    m = LZ.get("modo")
    for r, acc in reversed(LZ["hits"]):
        if not r.collidepoint(X, Y):
            continue
        k = acc[0]
        if k == "hold":
            IDLEHOLD["m"] = None if IDLEHOLD["m"] else (m or "norm")
            if IDLEHOLD["m"] == "act":
                ACT_GAL[0] = int(now // 10) % 2 == 0
            return True
        if k == "act":
            ACT_MODE[0] = ACT_MODES[acc[1]][0]
            IDLEHOLD["m"] = "act"
            return True
        if k == "actmapa":
            if IDLEHOLD["m"] == "act":
                i = [mm for mm, _ in ACT_MODES].index(ACT_MODE[0]) if ACT_MODE[0] in [mm for mm, _ in ACT_MODES] else 0
                ACT_MODE[0] = ACT_MODES[(i + 1) % 3][0]
                return True
            continue
        if m == "fac":
            IDLEHOLD["m"] = "fac"                         # usando el CDSN, la espera se queda en él
        if k == "tab":
            CW["tab"] = acc[1]
        elif k == "exp":
            CW["verexp"] = not CW["verexp"]; CW["key"] = None
        elif k == "sel":
            CW["tab"] = 0
            if CW["sel"] == acc[1]:
                return lz_ficha(acc[1])
            CW["sel"] = acc[1]
        elif k == "x":
            CW["sel"] = None
        elif k == "ficha":
            return lz_ficha(acc[1])
        elif k == "pag":
            CW["pg"][acc[1]] += 1
        elif k == "pagm":
            CW["pg"][acc[1]] = max(0, CW["pg"][acc[1]] - 1)
        elif k == "zoom+":
            CW["z"] = min(12.0, CW["z"] * 1.5)
        elif k == "zoom-":
            CW["z"] = max(0.5, CW["z"] / 1.5)
        elif k == "centro":
            CW["def"] = False; cw_vista_def(); CW["sel"] = None
        elif k == "ley":
            CW["ley"] = not CW["ley"]
        elif k == "radar":
            if CW["ley"]:
                CW["ley"] = False; return True
            hit = None
            for o in CW["S"]:
                if o.get("lx") is None:
                    continue
                d = math.hypot(o["lx"] - X, o["ly"] - Y)
                if d < 34 and (hit is None or d < hit[0]):
                    hit = (d, o)
            if hit:
                n = hit[1]["s"].get("sys")
                if CW["sel"] == n:
                    return lz_ficha(n)
                CW["sel"] = n
            else:
                R = min(LZ_RA.w, LZ_RA.h - 40) // 2 - 16
                kk = 0.9 * R / CW["d80"] * CW["z"]
                CW["cx"] += (X - LZ_RA.centerx) / kk
                CW["cz"] -= (Y - (LZ_RA.centery - 20)) / kk
        return True
    return False

def lz_ficha(n):
    """FICHA COMPLETA: todavía es de 480x320, así que se abre en el MENÚ."""
    ui["idle_skip"] = time.time() + 60
    ui["facsys"] = n; ui["facback"] = 77; ui["view"] = 194
    lienzo_menu()
    return True

# ---------------------------------------------------------------------------------------------------------------
# enganche: la espera de la HDMI usa el lienzo; los toques van a lz_toque_espera
# ---------------------------------------------------------------------------------------------------------------
_render_big_base_v20b2 = render_big_base

def render_big_base():
    S = BIG.get("surf")
    if lienzo_on() and S is not None and not hdmi_panel() and not ui.get("bye"):
        with lock:
            d, rx = state["data"], state["rx"]
        now = time.time()
        online = d is not None and now - rx < 5
        rot = None
        espera = False
        if now - ui["start"] >= 3 and not online:
            espera = True
        elif online and d.get("menu") and not (ui.get("alert") and now < ui["alert"]["until"]) \
                and not (xa.get("a") and now < xa["a"]["until"]) \
                and not ((d or {}).get("Flags", 0) & (1 << 11) or now < scoop["full_until"]):
            espera, rot = True, "MENÚ PRINCIPAL"
        if espera and lz_espera_puede(now):
            S.fill(BLACK)
            if lienzo_dibuja(S, lz_espera, now, rot):
                BIG["rects"] = []
                BIG["fast"] = True                        # en AUTO, la espera va a 10 imágenes por segundo
                LZ["lleno"] = "nuevo"
                return
    return _render_big_base_v20b2()

_big_tap_v20b2 = big_tap

def big_tap(xn, yn):
    if lienzo_on() and not hdmi_panel() and LZ.get("lleno") == "nuevo":
        HDMIF["t"] = time.time()
        p = lienzo_punto(xn, yn)
        if p:
            try:
                usado = lz_toque_espera(*p)
            except Exception as e:
                log_exc("toque espera", e); usado = True
            if not usado:
                ui["idle_skip"] = time.time() + 60    # «toca la pantalla para abrir el menú»
                lienzo_menu()
        TAP_EV.set()
        return
    return _big_tap_v20b2(xn, yn)
