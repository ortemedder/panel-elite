#!/usr/bin/env python3
# Parche v1.0 beta 6 (desde la beta 5): actividad de la faccion (necesita la escucha v3 en la Orange Pi)
#  - trafico de comandantes por sistema (columna en FACCION y grafica de 7 dias)
#  - zonas de conflicto y portanaves vistos en tus sistemas
#  - Powerplay a menos de 20 al con minimapa (pestana ZONA de la ficha)
#  - estados en colores (verde bueno, naranja malo, rojo conflicto) con pistas de que hacer
#  - aviso urgente de guerra, guerra civil y elecciones; recordatorio cada hora; aviso al terminar
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def view_facact" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v1.0b5' not in s:
    sys.exit("Este parche es para la v1.0 beta 5")
shutil.copy(P, P + ".bak100b5")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

CODE = r'''
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
        if x + w_ - pos[0] > maxw:
            put(surf, font, "…", (x, y), DIM); return
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

def fac_watch(now):
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

_render_b6 = render

def render(surf):
    try:
        fac_watch(time.time())
    except Exception as e:
        log_exc("faccion avisos", e)
    return _render_b6(surf)

_on_tap_b6 = on_tap

def on_tap(x, y):
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
    _on_tap_b6(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 6
- FACCIÓN: estados en colores (verde = buenos, naranja = malos, rojo = guerra, elecciones o retirada), «ZC ×N» si hay zonas de conflicto vistas, y a la derecha cuántos comandantes han pasado hoy (rojo si es el triple de lo normal). Los sistemas en guerra o elecciones salen los primeros y parpadeando.
- Ficha del sistema con tres pestañas: FACCIONES (con los estados de tu facción y qué hacer en los malos), ACTIVIDAD (comandantes por día de la última semana, zonas de conflicto de las últimas 24 h y portanaves vistos) y ZONA (minimapa de 20 al con el Powerplay de alrededor; tocar un sistema tuyo abre su ficha).
- Aviso urgente (rojo, alarma y voz) de guerra, guerra civil y elecciones en tu facción: al aparecer, al arrancar, cada hora mientras juegas y al terminar (ganada o perdida). También aviso de TRÁFICO ALTO si hay mucho movimiento y baja tu influencia. Se apaga en ALERTAS: GUERRA / ELECCIONES DE TU FACCIÓN.
- Necesita la escucha de EDDN nueva (v3) en la Orange Pi.
# Enlace energético''')
rep('    ("1.0b5", ', '    ("1.0b6", "Actividad de la facción: tráfico, zonas de conflicto, portanaves, Powerplay cercano, aviso de guerra"),\n    ("1.0b5", ')
s = re.sub(r'PANEL_VER = "v1\.0b5[^"]*"', 'PANEL_VER = "v1.0b6 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 6  (copia en " + P + ".bak100b5)")
