# Panel Elite v1.1 · parte 09: faccion (lineas 8268-9046 del panel entero)
# ---------- v1.0 beta 6: actividad de la faccion ----------
ST_GOOD = {"Boom", "Investment", "CivilLiberty", "PublicHoliday", "Expansion"}
ST_WAR = {"War", "CivilWar", "Election", "Retreat"}
TIPS = {"Famine": "llevar comida", "Outbreak": "llevar suministros médicos", "Lockdown": "cazar recompensas y entregar datos",
        "CivilUnrest": "misiones de seguridad y armas", "Bust": "comerciar con beneficio", "Drought": "llevar agua",
        "Blight": "llevar productos agrícolas", "PirateAttack": "cazar piratas", "TerroristAttack": "cazar recompensas",
        "InfrastructureFailure": "llevar maquinaria y metales", "NaturalDisaster": "rescate y suministros",
        "Retreat": "misiones y comercio para subir por encima del 2,5 %", "War": "zonas de conflicto y misiones de guerra",
        "CivilWar": "zonas de conflicto y misiones de guerra", "Election": "misiones de la facción (no de combate)"}

def st_col(st):
    return RED if st in ST_WAR else GREEN if st in ST_GOOD else ORANGE

def fac_parts(v):
    """[(texto, color)] de los estados de tu faccion en ese sistema."""
    out = []
    for c in v.get("conflictos") or []:
        out.append((f"{'ELECCIONES' if (c.get('tipo') or '').lower() == 'election' else 'GUERRA'} vs {c.get('contra')} "
                    f"{c.get('ganados') or 0}-{c.get('perdidos') or 0}", RED))
    zc = [z for z in v.get("zc") or [] if time.time() - (z.get("t") or 0) < 86400]
    if zc and (v.get("conflictos") or any(x in ST_WAR for x in v.get("activos") or [])):
        out.append((f"ZC ×{len(zc)}", RED))
    for k, suf in (("activos", ""), ("pendientes", " (pend.)"), ("recuperando", " (rec.)")):
        for st in v.get(k) or []:
            out.append((ES_ST.get(st, st) + suf, st_col(st) if k != "recuperando" else DIM))
    return out

def put_parts(surf, font, parts, pos, maxw):
    x, y = pos
    for i, (t, c) in enumerate(parts):
        t_ = (", " if i else "") + t
        w_ = tw_(font, t_)
        if x + w_ - pos[0] > maxw:                      # no cabe entero: lo que quepa, cortado
            rest = maxw - (x - pos[0])
            if rest > tw_(font, "…") + 20:
                put(surf, font, t_, (x, y), c, rest)
            else:
                put(surf, font, "…", (x, y), DIM)
            return
        put(surf, font, t_, (x, y), c); x += w_

def fac_states(v):
    return [t for t, c in fac_parts(v)]

def traf(v):
    T = v.get("trafico") or {}
    if not T:
        return None, None, False
    days = sorted(T)
    hoy = T.get(time.strftime("%Y-%m-%d", time.gmtime()), 0)
    prev = [T[d] for d in days if d != time.strftime("%Y-%m-%d", time.gmtime())]
    media = sum(prev) / len(prev) if prev else 0
    alto = media >= 2 and hoy > 3 * media
    return hoy, media, alto

def fac_rows():
    D = FACD["data"] or {}
    S = [v for v in (D.get("sistemas") or {}).values() if v.get("inf") and not v.get("fuera")]
    gap = lambda v: v["inf"] - (v.get("segunda_inf") or 0)
    war = lambda v: bool(v.get("conflictos")) or any(x in ("War", "CivilWar", "Election") for x in (v.get("activos") or []) + (v.get("pendientes") or []))
    S.sort(key=lambda v: (0 if war(v) else 1 if v.get("ctrl") and (gap(v) < 5 or "Retreat" in (v.get("pendientes") or []) + (v.get("activos") or []))
                          else 2 if v.get("ctrl") else 3, -v["inf"]))
    return D, S, gap

# --- lista FACCION: estados en color, ZC y trafico ---
def view_fac(surf, d, flags, now):
    FROWS.clear()
    D, S, gap = fac_rows()
    y = TOP + 3
    if not S:
        put(surf, F["btn"], "sin datos de la facción", (W // 2, H // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], FACD["err"] or "descargando…", (W // 2, H // 2 + 14), DIM, W - 16, anchor="center")
        return
    pages = (len(S) + FAC_PER - 1) // FAC_PER
    pg = ui.get("facpg", 0) % pages
    x = put(surf, F["btn"], (D.get("faccion") or "").upper(), (8, y), ORANGE, 210)
    tmax = max([v.get("t") or 0 for v in S] or [0])
    a_txt, a_col = fac_age(tmax)
    put(surf, F["small"], f"act. {time.strftime('%H:%M', time.localtime(tmax))} ({a_txt})" if tmax else "sin fecha", (8 + x + 10, y + 4), a_col, W - x - 120)
    put(surf, F["small"], f"{sum(1 for v in S if v.get('ctrl'))} contr. · {len(S)} sist.", (W - 8, y + 4), DIM, anchor="topright")
    y += 22
    for v in S[pg * FAC_PER:(pg + 1) * FAC_PER]:
        FROWS.append((pygame.Rect(0, y - 1, W, 32), v["sys"]))
        g = gap(v)
        parts = fac_parts(v)
        warn = any(c == RED for t, c in parts)
        pygame.draw.line(surf, (40, 28, 10), (6, y - 1), (W - 6, y - 1))
        col = (RED if int(now * 2) % 2 else WHITE) if warn else ORANGE if v.get("ctrl") else WHITE
        if v.get("ctrl"):
            pygame.draw.polygon(surf, ORANGE, [(8, y + 4), (14, y + 4), (11, y + 9)])
        put(surf, F["small"], v["sys"].upper(), (18, y + 1), col, 170)
        if parts:
            put_parts(surf, F["small"], parts, (18, y + 15), 170)
        else:
            put(surf, F["small"], "sin estados", (18, y + 15), DIM)
        bx = pygame.Rect(194, y + 5, 110, 12); pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, ORANGE if v.get("ctrl") else (170, 170, 170), (bx.x + 1, bx.y + 1, int((bx.w - 2) * min(100, v["inf"]) / 100), bx.h - 2))
        tx = bx.x + int(bx.w * min(100, v.get("segunda_inf") or 0) / 100); pygame.draw.line(surf, RED, (tx, bx.y - 2), (tx, bx.bottom + 1), 2)
        put(surf, F["btn"], f"{v['inf']:.1f}%".replace(".", ","), (310, y + 2), ORANGE if v.get("ctrl") else WHITE)
        if v.get("prev") is not None and abs(v["inf"] - v["prev"]) >= 0.1:
            tr = v["inf"] - v["prev"]; c_ = GREEN if tr > 0 else RED; x_, y_ = 312, y + 21
            pygame.draw.polygon(surf, c_, [(x_, y_ + 5), (x_ + 8, y_ + 5), (x_ + 4, y_)] if tr > 0 else [(x_, y_), (x_ + 8, y_), (x_ + 4, y_ + 5)])
            put(surf, F["small"], f"{abs(tr):.1f}".replace(".", ","), (x_ + 11, y_ - 3), c_)
        put(surf, F["btn"], (f"+{g:.1f}" if g >= 0 else f"{g:.1f}").replace(".", ","), (W - 60, y + 2),
            GREEN if g >= 5 else ORANGE if g >= 0 else DIM, anchor="topright")
        hoy, media, alto = traf(v)
        if hoy is not None:
            put(surf, F["small"], f"{hoy} cmdr", (W - 8, y + 5), RED if alto else ORANGE if media and hoy > 1.5 * media else DIM, anchor="topright")
        else:
            put(surf, F["small"], fac_age(v.get("t"))[0].replace("hace ", ""), (W - 8, y + 5), DIM, anchor="topright")
        y += 32
    put(surf, F["small"], (f"pág {pg + 1}/{pages} · " if pages > 1 else "") + "toca un sistema para ver su ficha", (8, H - 20), DIM, W - 110)
    if pages > 1:
        for k, t in enumerate(("<", ">")):
            draw_button(surf, fac_pg_btn(k), t, "", F["btn"], compact=True)

VIEWS[192] = VIEWS[193] = view_fac

# --- ficha del sistema: pestanas FACCIONES | ACTIVIDAD | ZONA ---
MENU[195] = MENU[196] = MENU[194] = "SISTEMA DE LA FACCIÓN"
PARENT[195] = PARENT[196] = 192
TABS.append([(194, "FACCIONES"), (195, "ACTIVIDAD"), (196, "ZONA")])
BACK_R = pygame.Rect(4, H - 26, 90, 23)

def fs_head(surf, d, v, name):
    y = TOP + 3
    put(surf, F["btn"], name.upper(), (8, y), ORANGE, 300)
    pos, here = v.get("pos"), (d or {}).get("starpos")
    if pos and here and None not in pos:
        dist = math.dist(pos, here)
        put(surf, F["btn"], "AQUÍ" if dist < 0.01 else f"a {dist:,.1f} al".replace(",", "X").replace(".", ",").replace("X", "."),
            (W - 8, y), BLUE, anchor="topright")
    a_txt, a_col = fac_age(v.get("t"))
    put(surf, F["small"], f"datos {a_txt} · {v.get('src') or '?'}", (8, y + 21), a_col)
    return y + 38

def fs_get():
    D = FACD["data"] or {}
    name = ui.get("facsys")
    return D, name, (D.get("sistemas") or {}).get(name)

_facsys_b6 = view_facsys

def view_facsys6(surf, d, flags, now):
    _facsys_b6(surf, d, flags, now)
    D, name, v = fs_get()
    if not v:
        return
    parts = fac_parts(v)
    bad = [st for st in (v.get("activos") or []) + (v.get("pendientes") or []) if st in TIPS and st not in ST_GOOD]
    r = pygame.Rect(100, H - 44, W - 104, 42)
    pygame.draw.rect(surf, BLACK, r)
    pygame.draw.rect(surf, BLACK, (0, H - 46, 100, 19))
    put(surf, F["tiny"], "TU FACCIÓN:", (r.x, r.y + 2), DIM)
    if parts:
        put_parts(surf, F["tiny"], parts, (r.x + 72, r.y + 2), r.w - 74)
    else:
        put(surf, F["tiny"], "sin estados", (r.x + 72, r.y + 2), DIM)
    yy = r.y + 15
    for st in bad[:2]:
        put(surf, F["tiny"], f"{ES_ST.get(st, st)}: {TIPS[st]}", (r.x, yy), st_col(st), r.w); yy += 13

VIEWS[194] = view_facsys6

def view_facact(surf, d, flags, now):
    D, name, v = fs_get()
    if not v:
        put(surf, F["btn"], "sin datos", (W // 2, H // 2), DIM, anchor="center"); return
    y = fs_head(surf, d, v, name)
    T = v.get("trafico") or {}
    hoy, media, alto = traf(v)
    put(surf, F["small"], "COMANDANTES POR DÍA", (8, y), DIM)
    if hoy is not None:
        put(surf, F["small"], f"hoy {hoy} · media {media:.0f}".replace(".", ",") + (" · TRIPLE DE LO NORMAL" if alto else ""),
            (W - 8, y), RED if alto else ORANGE, anchor="topright")
    y += 28
    gh, gw = 40, W - 24
    if T:
        days = sorted(T)[-7:]
        mx = max(T[k] for k in days) or 1
        hoy_k = time.strftime("%Y-%m-%d", time.gmtime())
        for i, k in enumerate(days):
            bw = gw // 7 - 8
            bh = max(2, int(gh * T[k] / mx))
            rr = pygame.Rect(12 + i * (gw // 7) + 4, y + gh - bh, bw, bh)
            pygame.draw.rect(surf, (RED if alto else ORANGE) if k == hoy_k else (150, 90, 20), rr)
            put(surf, F["tiny"], str(T[k]), (rr.centerx, rr.y - 13), WHITE, anchor="midtop")
            lab = "hoy" if k == hoy_k else ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"][time.strptime(k, "%Y-%m-%d").tm_wday]
            put(surf, F["tiny"], lab, (rr.centerx, y + gh + 2), DIM, anchor="midtop")
    else:
        put(surf, F["small"], "todavía sin datos (los cuenta la escucha de EDDN)", (12, y + 12), DIM)
    y += gh + 16
    pygame.draw.line(surf, DIM, (6, y), (W - 6, y)); y += 4
    put(surf, F["small"], "ZONAS DE CONFLICTO (24 h)", (8, y), DIM)
    for c in v.get("conflictos") or []:
        put(surf, F["small"], f"{'ELECCIONES' if (c.get('tipo') or '').lower() == 'election' else 'GUERRA'} vs {c.get('contra')} · "
                              f"{c.get('ganados') or 0}-{c.get('perdidos') or 0} días", (W - 8, y), RED, W - 200, anchor="topright")
    y += 15
    zc = [z for z in v.get("zc") or [] if time.time() - (z.get("t") or 0) < 86400]
    if not zc:
        put(surf, F["tiny"], "ninguna vista", (12, y)); y += 14
    for z in zc[:3]:
        lv = {"High": ("ALTA INTENSIDAD", RED), "Med": ("MEDIA INTENSIDAD", ORANGE), "Low": ("BAJA INTENSIDAD", (230, 200, 60))}.get(z.get("i"), ("?", DIM))
        pygame.draw.rect(surf, lv[1], (10, y + 3, 7, 7))
        put(surf, F["tiny"], lv[0], (22, y), lv[1]); put(surf, F["tiny"], fac_age(z.get("t"))[0], (W - 8, y), DIM, anchor="topright"); y += 13
    pygame.draw.line(surf, DIM, (6, y + 1), (W - 6, y + 1)); y += 4
    put(surf, F["small"], "PORTANAVES VISTOS (7 días)", (8, y), DIM); y += 15
    pn = sorted((v.get("pn") or {}).items(), key=lambda kv: -kv[1].get("t", 0))
    if not pn:
        put(surf, F["tiny"], "ninguno visto", (12, y), DIM)
    for cs, c in pn:
        if y + 13 > H - 28:
            break
        put(surf, F["tiny"], c.get("n") or "?", (12, y), WHITE, 190); put(surf, F["tiny"], cs, (210, y), BLUE)
        put(surf, F["tiny"], fac_age(c.get("t"))[0], (W - 8, y), DIM, anchor="topright"); y += 13
    draw_button(surf, BACK_R, "< VOLVER", "", F["small"], compact=True)

VIEWS[195] = view_facact

PW_COL = {"Edmund Mahon": (80, 170, 255), "Jerome Archer": (230, 60, 60), "Li Yong-Rui": (60, 200, 120), "Zemina Torval": (200, 170, 40),
          "Aisling Duval": (90, 140, 255), "Arissa Lavigny-Duval": (180, 90, 220), "Denton Patreus": (230, 140, 40),
          "Felicia Winters": (240, 200, 90), "Pranav Antal": (230, 230, 230), "Archon Delaine": (200, 40, 40),
          "Yuri Grom": (150, 150, 150), "Nakato Kaine": (120, 220, 200)}
ZPTS = []

def view_faczona(surf, d, flags, now):
    ZPTS.clear()
    D, name, v = fs_get()
    if not v or not v.get("pos"):
        put(surf, F["btn"], "sin coordenadas de este sistema todavía", (W // 2, H // 2), DIM, anchor="center")
        draw_button(surf, BACK_R, "< VOLVER", "", F["small"], compact=True); return
    y = fs_head(surf, d, v, name)
    c0 = v["pos"]
    M = pygame.Rect(4, y, 190, H - y - 30)
    pygame.draw.rect(surf, DIM, M, 1, border_radius=4)
    sc = (M.w / 2 - 6) / 20
    pygame.draw.circle(surf, (45, 30, 10), M.center, int(20 * sc), 1)
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
        pygame.draw.circle(surf, col, (int(px), int(py)), 4)
        if mine:
            pygame.draw.circle(surf, ORANGE, (int(px), int(py)), 7, 2)
            ZPTS.append((pygame.Rect(int(px) - 9, int(py) - 9, 18, 18), n))
    pygame.draw.circle(surf, BLUE, M.center, 10, 1)
    put(surf, F["tiny"], "20 al", (M.right - 30, M.bottom - 14), DIM)
    lx, ly = M.right + 8, y
    put(surf, F["small"], "POWERPLAY ALREDEDOR (20 al)", (lx, ly), DIM); ly += 16
    rows = sorted([p for p in pts if p[2]], key=lambda p: math.dist(p[1], c0))
    if not rows:
        put(surf, F["tiny"], "sin datos de Powerplay cerca todavía", (lx, ly), DIM)
    for n, p_, pot, est, prog, mine in rows:
        if ly + 14 > H - 44:
            break
        col = PW_COL.get(pot, (130, 130, 130))
        pygame.draw.circle(surf, col, (lx + 4, ly + 7), 4)
        put(surf, F["tiny"], n, (lx + 12, ly), ORANGE if mine else WHITE, 84)
        put(surf, F["tiny"], f"{pot.split()[-1]} · {tr_(est)}", (lx + 98, ly), col, 92)
        if prog is not None:
            bx = pygame.Rect(W - 50, ly + 3, 44, 8); pygame.draw.rect(surf, DIM, bx, 1)
            pygame.draw.rect(surf, col, (bx.x + 1, bx.y + 1, int((bx.w - 2) * max(0, min(1, float(prog)))), bx.h - 2))
        ly += 14
    if rows:
        cnt = {}
        for r_ in rows:
            cnt[r_[2]] = cnt.get(r_[2], 0) + 1
        top = max(cnt, key=cnt.get)
        put(surf, F["tiny"], f"{top} controla {cnt[top]} de {len(pts)} sistemas cercanos", (lx, H - 42), PW_COL.get(top, WHITE), W - lx - 6)
    put(surf, F["tiny"], "círculo naranja = tu facción · tócalo", (lx, H - 28), DIM, W - lx - 6)
    draw_button(surf, BACK_R, "< VOLVER", "", F["small"], compact=True)

VIEWS[196] = view_faczona

# --- avisos urgentes de guerra y elecciones ---
EV_LIST.append(("facwar", "GUERRA / ELECCIONES DE TU FACCIÓN"))
FW = {"seen": None, "info": {}, "rem": 0, "trf": set()}

def fac_conf(D):
    out = {}
    for n, v in (D.get("sistemas") or {}).items():
        if v.get("fuera"):
            continue
        for c in v.get("conflictos") or []:
            out[(n, c.get("contra"))] = (c.get("tipo") or "war", c.get("estado") or "", c.get("ganados") or 0, c.get("perdidos") or 0)
        for st in (v.get("activos") or []) + (v.get("pendientes") or []):
            if st in ("War", "CivilWar", "Election") and not v.get("conflictos"):
                out[(n, "?")] = (st.lower(), "", 0, 0)
    return out

def fw_alert(title, big, lines, voz):
    if not ev_on("facwar"):
        return
    k0 = XA_K[0]
    try:
        XA_K[0] = "facwar"
        xa["a"] = dict(until=time.time() + 10, col=RED, title=title, big=big, lines=lines)
        play("alarm")
        voice_say(voz)
    finally:
        XA_K[0] = k0

def tipo_es(t):
    t = (t or "").lower()
    return "ELECCIONES" if t == "election" else "GUERRA CIVIL" if t == "civilwar" else "GUERRA"







# ---------- v1.0 beta 7: pantalla de espera de la faccion ----------
idle_crawl = idle_crawl_base                              # el recuadro vuelve a ser solo GALNET
LOGO = {"src": None, "miss": False}
_LOGOC = {}

def logo_src():
    if LOGO["src"] is None and not LOGO["miss"]:
        try:
            LOGO["src"] = pygame.image.load(os.path.join(PANEL_DIR, "logo_faccion.png"))
        except Exception:
            LOGO["miss"] = True
    return LOGO["src"]

def blit_logo(surf, rect, dark=255):
    """El logo de la faccion en rect (nitido tambien en la HDMI). False si no hay logo."""
    src = logo_src()
    if src is None:
        return False
    real, rr = (surf.real, surf._r(rect)) if type(surf).__name__ == "ScaledSurf" else (surf, pygame.Rect(rect))
    key = (rr.w, rr.h, dark)
    if key not in _LOGOC:
        try:
            im = pygame.transform.smoothscale(src, (rr.w, rr.h))
        except ValueError:
            im = pygame.transform.scale(src, (rr.w, rr.h))
        if dark < 255:
            im = im.copy(); im.fill((dark, dark, dark, 255), special_flags=pygame.BLEND_RGBA_MULT)
        _LOGOC[key] = im
    real.blit(_LOGOC[key], rr.topleft)
    return True

def shield(surf, cx, cy, col):
    pygame.draw.polygon(surf, col, [(cx - 14, cy - 16), (cx + 14, cy - 16), (cx + 14, cy + 2), (cx, cy + 18), (cx - 14, cy + 2)], 2)
    pygame.draw.line(surf, col, (cx, cy - 12), (cx, cy + 10), 2); pygame.draw.line(surf, col, (cx - 8, cy - 4), (cx + 8, cy - 4), 2)

def fac_war(v):
    return bool(v.get("conflictos")) or any(x in ("War", "CivilWar", "Election") for x in (v.get("activos") or []) + (v.get("pendientes") or []))





# ---------- v1.0 beta 8 ----------
IDLE_MODE = {"m": None, "t": 0}                         # que pantalla de espera se esta viendo



# --- actividad galactica en directo (EDDN escuchado por la propia Pi solo mientras se ve) ---
ACT = {"want": 0, "on": False, "err": "", "pings": deque(maxlen=600), "feed": deque(maxlen=12),
       "jumps": deque(maxlen=20000), "uids": {}, "zmq": None}

def act_ok():
    if ACT["zmq"] is None:
        try:
            import zmq  # noqa
            ACT["zmq"] = True
        except ImportError:
            ACT["zmq"] = False
    return ACT["zmq"]

ACT_KEEP = 180                                           # sigue escuchando 3 min tras quitar la pantalla (la espera la vuelve a poner cada minuto)

def act_loop():
    while True:
        if time.time() - ACT["want"] > ACT_KEEP or not act_ok():
            time.sleep(1); continue
        try:
            import zmq, zlib as _z
            ctx = zmq.Context.instance()
            sub = ctx.socket(zmq.SUB)
            sub.setsockopt(zmq.SUBSCRIBE, b""); sub.setsockopt(zmq.RCVTIMEO, 1000)
            sub.connect("tcp://eddn.edcd.io:9500")
            ACT.update(on=True, err="")
            plog("Actividad galáctica: escuchando EDDN")
            while time.time() - ACT["want"] < ACT_KEEP:  # deja de escuchar 3 min despues de quitar la pantalla
                try:
                    raw = sub.recv()
                except zmq.Again:
                    continue
                pkt = _z.decompress(raw)
                if b"FSDJump" not in pkt and b"CarrierJump" not in pkt:
                    continue
                d = json.loads(pkt)
                if "/journal/" not in d.get("$schemaRef", ""):
                    continue
                hd = d.get("header") or {}
                gv = hd.get("gameversion") or ""
                if gv.startswith("3.") or "legacy" in gv.lower():
                    continue
                m = d.get("message") or {}
                if m.get("event") not in ("FSDJump", "CarrierJump") or not m.get("StarPos"):
                    continue
                now = time.time()
                x, y_, z = m["StarPos"]
                nm = m.get("StarSystem") or "?"
                mine = nm in ((FACD["data"] or {}).get("sistemas") or {})
                ACT["pings"].append((x, z, now, mine))
                ACT["jumps"].append(now)
                ACT["uids"][str(hd.get("uploaderID"))[:10]] = now
                if now - ACT.get("uprune", 0) > 60:      # fuera los comandantes de hace mas de 5 min (no crece sin fin)
                    ACT["uprune"] = now
                    ACT["uids"] = {k: v for k, v in list(ACT["uids"].items()) if now - v < 300}
                ACT["feed"].appendleft((nm, mine, now))
                if mine:
                    act_mine_hit(nm, x, z, now)
            sub.close(0)
            ACT["on"] = False
            plog("Actividad galáctica: deja de escuchar")
        except Exception as e:
            ACT.update(on=False, err=str(e)[:60]); log_exc("actividad EDDN", e); time.sleep(10)

threading.Thread(target=act_loop, daemon=True, name="actividad").start()

_GALBG = {}

def gal_points():
    if "pts" not in _GALBG:
        import random as _r
        rnd = _r.Random(7); pts = []
        for k in range(5000):
            arm = k % 4; t = rnd.random() ** 0.6 * 4.2; a = t * 1.15 + arm * math.pi / 2 + rnd.gauss(0, 0.22)
            r = 1500 + t * 9500 + rnd.gauss(0, 900)
            pts.append((25 + r * math.cos(a), 25900 + r * math.sin(a), rnd.randint(25, 70)))
        for k in range(900):
            r = abs(rnd.gauss(0, 2600)); a = rnd.random() * 6.283
            pts.append((25 + r * math.cos(a), 25900 + r * math.sin(a), rnd.randint(60, 120)))
        _GALBG["pts"] = pts
    return _GALBG["pts"]

def act_view(M, gal):
    """(funcion mundo->pantalla, escala) para la vista galaxia o la de tu zona."""
    if gal:
        X0, X1, Z0, Z1 = -45000, 45000, -18000, 72000
    else:
        S_ = [v["pos"] for v in ((FACD["data"] or {}).get("sistemas") or {}).values() if v.get("pos") and None not in v["pos"]]
        if S_:
            xs, zs = sorted(p[0] for p in S_), sorted(p[2] for p in S_)
            cx_, cz_ = xs[len(xs) // 2], zs[len(zs) // 2]           # mediana: un sistema lejano no lo descentra
            ds = sorted(max(abs(p[0] - cx_), abs(p[2] - cz_)) for p in S_)
            hw = max(40, ds[int(len(ds) * 0.85)] * 1.25)
        else:
            cx_, cz_, hw = 0, 0, 260
        X0, X1, Z0, Z1 = cx_ - hw, cx_ + hw, cz_ - hw * 0.87, cz_ + hw * 0.87
    sc = min(M.w / (X1 - X0), M.h / (Z1 - Z0))
    cx, cz = (X0 + X1) / 2, (Z0 + Z1) / 2
    return (lambda x, z: (M.centerx + (x - cx) * sc, M.centery - (z - cz) * sc)), sc






# ---------- v1.0 beta 9: boton FIJAR de la pantalla de espera ----------
IDLEHOLD = {"m": None}
ACT_GAL = [True]
ACT_MAP = pygame.Rect(6, 54, 300, 262)










# ---------- v1.0 beta 10 ----------
# --- boton FIJAR / SEGUIR con los logos (boton_seguir.png y boton_fijado.png junto a panel.py) ---
_BIMG, _BIMGC = {}, {}

def b10_hold_img(name):
    if name not in _BIMG:
        try:
            _BIMG[name] = pygame.image.load(os.path.join(PANEL_DIR, name))
        except Exception:
            _BIMG[name] = None
    return _BIMG[name]

def hold_rect(m):
    return pygame.Rect(430, 24, 46, 38) if m == "norm" else pygame.Rect(W - 50, 4, 46, 38)

def draw_hold(surf, m, now):
    r = hold_rect(m)
    held = IDLEHOLD["m"] is not None
    src = b10_hold_img("boton_fijado.png" if held else "boton_seguir.png")
    pygame.draw.rect(surf, BLACK, r, border_radius=4)
    if src is not None:
        ir = pygame.Rect(r.x, r.y, r.w, 28)
        real, rr = (surf.real, surf._r(ir)) if type(surf).__name__ == "ScaledSurf" else (surf, ir)
        k = (id(src), rr.w, rr.h)
        if k not in _BIMGC:
            try:
                _BIMGC[k] = pygame.transform.smoothscale(src, (rr.w, rr.h))
            except ValueError:
                _BIMGC[k] = pygame.transform.scale(src, (rr.w, rr.h))
        real.blit(_BIMGC[k], rr.topleft)
    elif held:
        cx, cy = r.centerx, r.y + 14
        pygame.draw.polygon(surf, WHITE, [(cx - 5, cy - 7), (cx - 5, cy + 7), (cx + 6, cy)])
    else:
        cx, cy = r.centerx, r.y + 14
        pygame.draw.rect(surf, ORANGE, (cx - 5, cy - 7, 4, 14)); pygame.draw.rect(surf, ORANGE, (cx + 1, cy - 7, 4, 14))
    col = (RED if int(now * 2) % 2 else (120, 0, 0)) if held else ORANGE
    pygame.draw.rect(surf, col, r, 1, border_radius=4)
    put(surf, F["tiny"], "SEGUIR" if held else "FIJAR", (r.centerx, r.bottom - 5), WHITE if held else ORANGE, anchor="center")

# --- actividad: encendida por defecto si la Pi tiene python3-zmq (se apaga con "actividad": false en el cfg) ---
def act_enabled():
    if cfg.get("actividad") is not None:
        return cfg["actividad"]
    return act_ok()

# --- avisos de influencia y flechas de tendencia ---
INF_MIN = 40.0                                          # aviso si un sistema controlado baja de este %
INF_GAP = 5.0                                           # o si la segunda faccion se acerca a menos de estos puntos
INFW = set()

def inf_warn(v):
    """(titulo, detalle) si un sistema controlado esta en peligro, o None."""
    if not v.get("ctrl") or not v.get("inf"):
        return None
    g = v["inf"] - (v.get("segunda_inf") or 0)
    if g < INF_GAP:
        return "RIVAL CERCA", f"{v.get('segunda') or 'otra facción'} a {g:.1f} puntos ({v['inf']:.1f} %)".replace(".", ",")
    if v["inf"] < INF_MIN:
        return "INFLUENCIA BAJA", f"{v['inf']:.1f} % (aviso por debajo del {INF_MIN:.0f} %)".replace(".", ",")
    return None

def trend_arrow(surf, v, x_, y_):
    if v.get("prev") is None or abs(v["inf"] - v["prev"]) < 0.1:
        return
    up = v["inf"] > v["prev"]
    pygame.draw.polygon(surf, GREEN if up else RED,
                        [(x_, y_ + 5), (x_ + 8, y_ + 5), (x_ + 4, y_)] if up else [(x_, y_), (x_ + 8, y_), (x_ + 4, y_ + 5)])



# --- actividad: tus sistemas brillan y contador de saltos del dia ---
ACT_HIT = {"n": None, "x": 0, "z": 0, "t": 0}
ACT_DAY_F = os.path.join(PANEL_DIR, "actividad_hoy.json")
try:
    ACT_DAY = json.load(open(ACT_DAY_F))
except Exception:
    ACT_DAY = {}

def act_mine_hit(nm, x, z, now):
    ACT_HIT.update(n=nm, x=x, z=z, t=now)
    k = time.strftime("%Y-%m-%d", time.gmtime(now))
    for d_ in [d_ for d_ in ACT_DAY if d_ != k]:
        ACT_DAY.pop(d_, None)
    ACT_DAY[k] = ACT_DAY.get(k, 0) + 1
    try:
        json.dump(ACT_DAY, open(ACT_DAY_F, "w"))
    except OSError:
        pass

def act_hit_draw(surf, M, pt, now):
    age = now - ACT_HIT["t"]
    if not ACT_HIT["n"] or age > 10 or age < 0:
        return
    px, py = pt(ACT_HIT["x"], ACT_HIT["z"])
    if M.collidepoint(px, py):
        f_ = 1 - age / 10
        for k in range(3):
            rr = int(4 + ((age * 14 + k * 6) % 18))
            pygame.draw.circle(surf, tuple(int(c * f_) for c in ORANGE), (int(px), int(py)), rr, 1)
        pygame.draw.circle(surf, ORANGE, (int(px), int(py)), 4)
    nm = ACT_HIT["n"].upper()
    b = pygame.Rect(M.x + 6, M.bottom - 26, M.w - 12, 20)
    pygame.draw.rect(surf, (40, 22, 0), b, border_radius=4)
    pygame.draw.rect(surf, ORANGE if int(now * 3) % 2 else (140, 80, 0), b, 1, border_radius=4)
    put(surf, F["small"], "COMANDANTE EN " + nm, b.center, ORANGE, b.w - 10, anchor="center")

# --- menu 7: RADAR y ACTIVIDAD (pantallas enteras con boton para volver) ---
MENU[77] = "RADAR DE LA FACCIÓN"
MENU[78] = "ACTIVIDAD GALÁCTICA"
PARENT[77] = PARENT[78] = 7
RADAR_PTS = []
FULL_BACK = pygame.Rect(W - 50, 4, 46, 38)

def view_sub7(surf, d, flags, now):
    for i, (n, name) in enumerate([("1", "EXPLORACIÓN"), ("2", "SISTEMA"), ("3", "EXOBIO"), ("4", "YACIM."), ("5", "DIARIO"),
                                   ("6", "ALIEN"), ("7", "RADAR"), ("8", "ACTIVIDAD")]):
        draw_button(surf, grid(i, 4, 2), n, name, F["num"], lit=flash.get((7, i), 0) > now)

def view_full(surf, d, flags, now):
    v = ui.get("view")
    D, S, gap = fac_rows()
    if v == 77 and not S:
        surf.fill(BLACK)
        put(surf, F["btn"], "sin datos de la facción", (W // 2, H // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], FACD["err"] or "descargando…", (W // 2, H // 2 + 14), DIM, W - 16, anchor="center")
    elif v == 77:
        draw_fac_screen(surf, now)
    else:
        draw_act_screen(surf, now)
    r = FULL_BACK
    pygame.draw.rect(surf, BLACK, r, border_radius=4)
    pygame.draw.rect(surf, ORANGE, r, 1, border_radius=4)
    put(surf, F["btn"], "<", (r.centerx, r.y + 13), ORANGE, anchor="center")
    put(surf, F["tiny"], "MENÚ 7", (r.centerx, r.bottom - 6), ORANGE, anchor="center")

VIEWS[7] = view_sub7
VIEWS[77] = VIEWS[78] = view_full

# --- ficha del sistema: boton IR (copia el nombre al portapapeles del PC) ---
IR_R = pygame.Rect(W - 76, TOP + 3, 72, 20)

def ir_draw(surf, now):
    D, name, v = fs_get()
    if not name:
        return
    lit = flash.get(("ir", 0), 0) > now
    pygame.draw.rect(surf, ORANGE if lit else BLACK, IR_R, border_radius=4)
    pygame.draw.rect(surf, ORANGE, IR_R, 1, border_radius=4)
    put(surf, F["small"], "IR  >", IR_R.center, BLACK if lit else ORANGE, anchor="center")

def ir_send(name):
    pc = pc_addr()
    if not pc:
        set_alert("NO SÉ LA IP DEL PC", "el sender no está enviando", RED, 3); return
    try:
        so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        so.sendto(("ELITEPANEL-CLIP|" + name).encode("utf-8"), (pc, 5006)); so.close()
        set_alert("COPIADO EN EL PC", f"{name}: Ctrl+V en el mapa galáctico", GREEN, 4, kind="info")
    except OSError as e:
        set_alert("NO SE PUDO COPIAR", str(e)[:40], RED, 3)

for _v in (194, 195, 196):
    def _mk(fn):
        def _f(surf, d, flags, now):
            fn(surf, d, flags, now)
            ir_draw(surf, now)
        return _f
    VIEWS[_v] = _mk(VIEWS[_v])

# --- AJUSTES: estado del escucha del pueblo (boton 8) ---

def view_sub124(surf, d, flags, now):
    _view_sub124_b10(surf, d, flags, now)
    sub, col, det = pueblo_estado(now)
    draw_button(surf, grid(7, 4, 2), "8", "PUEBLO " + sub, F["num"], filled=col == GREEN, lit=flash.get((1240, 7), 0) > now)

_view_sub124_b10 = VIEWS[124]
VIEWS[124] = view_sub124

# --- hora: al arrancar fuerza la sincronizacion; si no hay NTP, la toma de un servidor web ---
def hora_loop():
    import subprocess, http.client, email.utils
    time.sleep(5)
    def synced():
        try:
            return subprocess.run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], capture_output=True,
                                  text=True, timeout=10).stdout.strip() == "yes"
        except Exception:
            return False
    try:
        subprocess.run(["timedatectl", "set-ntp", "true"], capture_output=True, timeout=15)
        subprocess.run(["systemctl", "restart", "systemd-timesyncd"], capture_output=True, timeout=30)
    except Exception as e:
        plog("Hora: no puedo reiniciar timesyncd:", e)
    for _ in range(20):
        if synced():
            plog("Hora: sincronizada por NTP"); return
        time.sleep(3)
    for host in ("raw.githubusercontent.com", "www.google.com", "cloudflare.com"):
        try:
            c_ = http.client.HTTPConnection(host, 80, timeout=10)
            t0 = time.time(); c_.request("HEAD", "/"); r_ = c_.getresponse(); t1 = time.time()
            dt = r_.getheader("Date"); c_.close()
            if not dt:
                continue
            web = email.utils.parsedate_to_datetime(dt).timestamp() + (t1 - t0) / 2
            dif = web - time.time()
            if abs(dif) < 60:
                plog(f"Hora: sin NTP, pero bien ({dif:+.0f} s con {host})"); return
            subprocess.run(["date", "-s", "@%d" % int(web)], capture_output=True, timeout=10)
            plog(f"Hora: corregida {dif:+.0f} s con {host} (sin NTP)")
            set_alert("HORA CORREGIDA", f"{dif / 60:+.0f} min · tomada de {host}", ORANGE, 6, kind="info")
            return
        except Exception as e:
            plog("Hora:", host, e)
    plog("Hora: no he podido comprobarla")

threading.Thread(target=hora_loop, daemon=True, name="hora").start()

# --- render: pantallas enteras del menu 7 ---


# --- toques ---

def radar_hit(x, y):
    best = None
    for px, py, n in RADAR_PTS:
        d_ = math.hypot(px - x, py - y)
        if d_ < 16 and (best is None or d_ < best[0]):
            best = (d_, n)
    return best[1] if best else None



# ---------- v1.0 beta 10c: FLUJO DATOS EDDN en AJUSTES > OPCIONES, con la ultima subida a GitHub ----------
GH = {"t": 0, "err": ""}

def gh_loop():
    """Hora del ultimo commit de faccion.json en GitHub (API publica, cada 10 min)."""
    import urllib.request, datetime
    while True:
        try:
            url = FAC_URL
            try:
                url = open(os.path.join(PANEL_DIR, "faccion_url.txt")).read().strip() or url
            except OSError:
                pass
            m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)", url)
            if m:
                own, repo, br, path = m.groups()
                api = f"https://api.github.com/repos/{own}/{repo}/commits?path={path}&sha={br}&per_page=1"
                req = urllib.request.Request(api, headers={"User-Agent": "PanelEliteRPi/1.0", "Accept": "application/vnd.github+json"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    j = json.loads(r.read().decode("utf-8"))
                dt = j[0]["commit"]["committer"]["date"]
                GH.update(t=datetime.datetime.fromisoformat(dt.replace("Z", "+00:00")).timestamp(), err="")
        except Exception as e:
            GH["err"] = str(e)[:50]
        time.sleep(600)

threading.Thread(target=gh_loop, daemon=True, name="github").start()


def pueblo_estado(now):
    D = FACD["data"] or {}
    e = D.get("eddn") or {}
    if not D:
        return "SIN DATOS", RED, "no se ha podido descargar faccion.json " + (FACD["err"] or "")
    sub_t = GH["t"] or D.get("t") or 0
    age = now - sub_t if sub_t else None
    ok = bool(e.get("ok")) and age is not None and age < 7 * 3600     # sube cada 15 min si cambia, y cada 6 h siempre
    sub = ("OK · " if ok else "¡OJO! · ") + _hace(age)
    det = (f"EDDN {'conectado' if e.get('ok') else 'DESCONECTADO'} · {e.get('msgs', 0):,} mensajes".replace(",", ".")
           + f" · subido a GitHub hace {_hace(age)}" + ("" if GH["t"] else " (aprox.)")
           + (f" · bajado aquí hace {_hace(now - FACD['t'])}" if FACD.get("t") else ""))
    return sub, GREEN if ok else RED, det

PUEBLO_R = grid(11, 4, 3)
_view_settings_b10c = VIEWS[1244]

def view_settings_b10c(surf, d, flags, now):
    _view_settings_b10c(surf, d, flags, now)
    sub, col, det = pueblo_estado(now)
    r = PUEBLO_R
    ok = col == GREEN
    lit = flash.get(("pueblo",), 0) > now
    pygame.draw.rect(surf, WHITE if lit else ORANGE if ok else BLACK, r, border_radius=6)
    pygame.draw.rect(surf, ORANGE if ok else RED, r, 2, border_radius=6)
    tc = BLACK if ok or lit else ORANGE
    put(surf, F["small"], "FLUJO DATOS", (r.centerx, r.centery - 20), tc, r.w - 8, anchor="center")
    put(surf, F["small"], "EDDN", (r.centerx, r.centery - 5), tc, r.w - 8, anchor="center")
    put(surf, F["small"], sub, (r.centerx, r.centery + 16), BLACK if ok or lit else RED, r.w - 8, anchor="center")

VIEWS[1244] = view_settings_b10c




