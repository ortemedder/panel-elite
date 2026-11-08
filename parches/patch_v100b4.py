#!/usr/bin/env python3
# Parche v1.0 beta 4 (desde la beta 3):
#  - pestanas COMBATE | COMBATE + CAZA | CAZA
#  - VIAJES con zoom (tocar el mapa amplia x2; boton - aleja)
#  - tick del BGS de cada sistema (EDCAS): proximo tick, margen, ultimo y grafica; aviso al empezar la ventana
#  - los textos de las alertas siempre caben (letra mas pequena o dos lineas)
#  - MI FACCION: datos de la faccion desde GitHub (los sube la escucha EDDN); pestana en DIA y en ESCUADRON,
#    y en la pantalla de espera alternando cada 20 s con GALNET
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def view_fac" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v1.0b3' not in s:
    sys.exit("Este parche es para la v1.0 beta 3")
shutil.copy(P, P + ".bak100b3")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# alertas: el texto siempre cabe
rep('''    put(surf, F["big"], a["title"], (cx, y), col if on else WHITE, box.w - 20, anchor="midtop"); y += 36
    put(surf, F["num"], a["big"], (cx, y), WHITE, box.w - 20, anchor="midtop"); y += 52
    for ln_ in a["lines"]:
        if ln_:
            t_, c2 = ln_ if isinstance(ln_, tuple) else (ln_, col)
            put(surf, F["btn"], t_, (cx, y), c2, box.w - 20, anchor="midtop")
        y += 26''', '''    put_fit(surf, ("big", "btn", "small"), a["title"], (cx, y), col if on else WHITE, box.w - 20, anchor="midtop"); y += 36
    put_fit(surf, ("num", "big", "btn"), a["big"], (cx, y), WHITE, box.w - 20, anchor="midtop"); y += 52
    for ln_ in [l for l in a["lines"] if l][:3]:
        t_, c2 = ln_ if isinstance(ln_, tuple) else (ln_, col)
        y += put_wrap(surf, t_, (cx, y), c2, box.w - 20, max(1, (box.bottom - 6 - y) // 22))''')
rep('''    put(surf, F["big"] if len(a["text"]) > 16 else F["num"], a["text"], (box.centerx, box.centery - (14 if a["sub"] else 0)),
        col if on else WHITE, box.w - 20, anchor="center")
    if a["sub"]:
        put(surf, F["btn"], a["sub"], (box.centerx, box.centery + 26), WHITE, box.w - 20, anchor="center")''',
    '''    two_ = bool(a["sub"]) and len(wrap_lines(F["btn"], a["sub"], box.w - 20)) > 1
    put_fit(surf, ("num", "big", "btn", "small") if len(a["text"]) <= 16 else ("big", "btn", "small"), a["text"],
            (box.centerx, box.centery - (28 if two_ else 14 if a["sub"] else 0)), col if on else WHITE, box.w - 20, anchor="center")
    if a["sub"]:
        put_wrap(surf, a["sub"], (box.centerx, box.centery + (2 if two_ else 16)), WHITE, box.w - 20, 2)''')

CODE = r'''
# ---------- v1.0 beta 4 ----------
def tw_(font, text):
    return font.size(str(text))[0] / getattr(font, "f", 1)

def put_fit(surf, names, text, pos, col, maxw, anchor="topleft"):
    """La letra mas grande de la lista con la que el texto cabe entero."""
    for n in names:
        if tw_(F[n], text) <= maxw:
            return put(surf, F[n], text, pos, col, anchor=anchor)
    return put(surf, F[names[-1]], text, pos, col, maxw, anchor=anchor)

def put_wrap(surf, text, pos, col, maxw, maxlines=2):
    """Texto en F['btn'] partido en lineas (si no cabe en maxlines, en F['small']). Devuelve el alto usado."""
    for f_, lh in ((F["btn"], 24), (F["small"], 17)):
        L = wrap_lines(f_, str(text), maxw)
        if len(L) <= maxlines or f_ is F["small"]:
            x, y = pos
            for t in L[:maxlines]:
                put(surf, f_, t, (x, y), col, maxw, anchor="midtop")
                y += lh
            return lh * min(len(L), maxlines)

# --- pestanas de combate ---
TABS.append([(6, "COMBATE"), (191, "COMBATE + CAZA"), (9, "CAZA")])

# --- VIAJES con zoom ---
VJT = {}

def vj_btn(i):
    return pygame.Rect(4 + i * 79, H - 28, 75, 25)

def view_viajes(surf, d, flags, now):
    V = (d or {}).get("viajes") or {}
    per = ui.get("vjp", "30"); zm = ui.get("vjz", "zona"); Z = ui.get("vjzoom")
    for i, (k, lab) in enumerate(VJ_PER):
        draw_button(surf, vj_btn(i), lab, "", F["small"], filled=k == per, compact=True)
    draw_button(surf, vj_btn(4), "GALAXIA" if zm == "gal" else "ZONA", "", F["small"], compact=True)
    draw_button(surf, vj_btn(5), f"−  x{Z[0]}" if Z else "−", "", F["small"], compact=True, dim=not Z)
    D = V.get(per)
    M = pygame.Rect(4, TOP + 2, W - 8, H - TOP - 34)
    pygame.draw.rect(surf, DIM, M, 1, border_radius=4)
    if not D or not D.get("n"):
        put(surf, F["btn"], "sin saltos en este periodo" if V else "esperando datos del sender", M.center, DIM, anchor="center")
        return
    nodes, edges, cur = D["n"], D["e"], D.get("cur")
    A = M.inflate(-30, -36).move(0, -2)
    pt0, sc0 = _vj_view(nodes, cur, zm, A)
    if Z:
        f_, wx, wz = Z
        sc = sc0 * f_
        pt = lambda x, z: (A.centerx + (x - wx) * sc, A.centery - (z - wz) * sc)
    else:
        pt, sc = pt0, sc0
    VJT.update(A=A, pt=pt, sc=sc)
    old_clip = surf.get_clip(); surf.set_clip(M)
    if zm == "gal":
        c = pt(*GAL_C)
        pygame.draw.circle(surf, (45, 30, 10), (int(c[0]), int(c[1])), max(2, min(4000, int(45000 * sc))), 1)
        pygame.draw.circle(surf, (70, 45, 15), (int(c[0]), int(c[1])), max(2, min(2000, int(4000 * sc))))
    P_ = [pt(n[1], n[2]) for n in nodes]
    mx = max([e[2] for e in edges] or [1])
    outs = []
    for i, j, c, h in sorted(edges, key=lambda e: e[2]):
        a, b = P_[i], P_[j]
        w = 1 + round(4 * (c - 1) / max(1, mx - 1))
        cl = M.clipline(a, b)
        if not cl:
            continue
        pygame.draw.line(surf, ORANGE if c > 1 else (150, 80, 0), cl[0], cl[1], w)
        ina, inb = M.collidepoint(a), M.collidepoint(b)
        if ina != inb:
            outs.append((nodes[j], cl[1], h) if ina else (nodes[i], cl[0], h))
        elif h >= 5 and math.dist(a, b) > 70:
            put(surf, F["small"], f"{h} saltos", ((a[0] + b[0]) / 2 + 4, (a[1] + b[1]) / 2 - 14), DIM)
    for k, n in enumerate(nodes):
        x, y = P_[k]
        if M.collidepoint(x, y):
            r = 2 + min(3, n[3] // 2)
            pygame.draw.circle(surf, WHITE if n[4] else (160, 160, 160), (int(x), int(y)), r + (1 if n[4] else 0))
    used = []
    def label(txt, x, y, col):
        tw, th = F["small"].size(txt)
        tw, th = int(tw / getattr(F["small"], "f", 1)), int(th / getattr(F["small"], "f", 1))
        for dx, dy in ((9, -th // 2), (-9 - tw, -th // 2), (-tw // 2, -th - 8), (-tw // 2, 8), (9, -th - 4), (9, 4), (-9 - tw, 4)):
            r = pygame.Rect(int(x + dx), int(y + dy), tw, th)
            if M.contains(r) and not any(r.colliderect(u) for u in used):
                used.append(r.inflate(4, 2)); pygame.draw.rect(surf, BLACK, r.inflate(4, 0))
                put(surf, F["small"], txt, r.topleft, col); return
    ci = next((k for k, n in enumerate(nodes) if n[0] and n[0] == cur), None)
    if ci is not None and M.collidepoint(P_[ci]):
        x, y = P_[ci]
        pygame.draw.circle(surf, BLUE, (int(x), int(y)), 7 if int(now * 2) % 2 else 9, 2)
        label(cur.upper()[:20], x, y, BLUE)
    nlab = 6 if not Z else 16                            # con zoom caben mas nombres
    for k in sorted(range(len(nodes)), key=lambda k: -nodes[k][3])[:nlab]:
        n = nodes[k]
        if n[0] and k != ci and M.collidepoint(P_[k]):
            label(n[0].upper()[:18], *P_[k], WHITE)
    ref = nodes[ci] if ci is not None else max(nodes, key=lambda n: n[3])
    seen = set()
    for far, (ex, ey), h in sorted(outs, key=lambda o: -math.hypot(o[0][1] - ref[1], o[0][2] - ref[2])):
        key = far[0] or (round(far[1]), round(far[2]))
        if key in seen or len(seen) >= 4:
            continue
        seen.add(key)
        dist = math.hypot(far[1] - ref[1], far[2] - ref[2])
        pygame.draw.circle(surf, ORANGE, (int(ex), int(ey)), 4)
        label(f"» {(far[0] or 'destino').upper()[:14]} {dist:,.0f} al".replace(",", "."), ex, ey, ORANGE)
    surf.set_clip(old_clip)
    st_ = f"{D['j']} SALTOS · {D['ly']:,} al · {D['s']} SISTEMAS".replace(",", ".") + ("" if Z else "  ·  toca para ampliar")
    r_ = pygame.Rect(M.x + 3, M.bottom - 17, tw_(F["small"], st_) + 8, 15)
    pygame.draw.rect(surf, BLACK, r_)
    put(surf, F["small"], st_, (r_.x + 4, r_.y + 1), DIM)

VIEWS[190] = view_viajes

# --- tick del BGS por sistema (EDCAS) ---
ETA = {"key": None}

def _hm(sec):
    sec = max(0, int(sec))
    return f"{sec // 3600} h {sec % 3600 // 60:02d} min"

def bgs_lines(d, now):
    out = []
    E = (d or {}).get("etick") or {}
    pn = pc_now(d, now)
    if E.get("next") and E.get("sys") == (d or {}).get("system"):
        w = (E.get("win") or 0) * 60
        if pn < E["next"] - w:
            out.append((f"PRÓXIMO TICK en {_hm(E['next'] - w - pn)} (± {E.get('win')} min) · datos: EDCAS", BLUE))
        elif pn < E["next"] + w:
            out.append((f"TICK EN CURSO · la ventana acaba en {_hm(E['next'] + w - pn)} · datos: EDCAS", GREEN))
        else:
            out.append(("tick previsto ya pasado · esperando datos nuevos de EDCAS", DIM))
        if E.get("last"):
            out.append((f"ÚLTIMO TICK {time.strftime('%d/%m %H:%M', time.localtime(E['last']))} (hace {_hm(pn - E['last'])})", DIM))
    else:
        tk = (d or {}).get("tick")
        if tk:
            out.append((f"ÚLTIMO TICK (general) hace {_hm(pn - tk)} ({time.strftime('%H:%M', time.localtime(tk))})", BLUE))
    b = (d or {}).get("bgsv") or {}
    if b.get("prev"):
        days = (pn - b["prev"]) / 86400
        cuando = "hoy" if days < 1 else f"hace {days:.0f} día{'s' if days >= 1.5 else ''}"
        out.append(("BGS ACTUALIZADO desde tu última visita (" + cuando + ")" if b.get("chg") else
                    "BGS sin cambios desde tu última visita (" + cuando + ")", GREEN if b.get("chg") else DIM))
    return out

def tick_graph(surf, d, r):
    """Hora del tick (UTC) de los ultimos dias en este sistema."""
    E = (d or {}).get("etick") or {}
    H_ = E.get("hist") or []
    if len(H_) < 2 or E.get("sys") != (d or {}).get("system"):
        return False
    pygame.draw.rect(surf, BLACK, r); pygame.draw.rect(surf, DIM, r, 1, border_radius=3)
    pts = []
    for k, t in enumerate(H_):
        g = time.gmtime(t); hh = g.tm_hour + g.tm_min / 60
        pts.append((r.x + 4 + k * (r.w - 8) / max(1, len(H_) - 1), r.bottom - 4 - hh / 24 * (r.h - 8)))
    pygame.draw.lines(surf, ORANGE, False, pts, 1)
    for p_ in pts:
        pygame.draw.circle(surf, ORANGE, (int(p_[0]), int(p_[1])), 2)
    put(surf, F["small"], "hora del tick (UTC)", (r.x, r.y - 14), DIM)
    return True

_view_pol_b4 = _view_pol_b3

def view_pol(surf, d, flags, now):
    _view_pol_b4(surf, d, flags, now)
    L = bgs_lines(d, now)
    g = tick_graph(surf, d, pygame.Rect(W - 128, H - 8 - 15 * max(1, len(L)) - 40, 122, 36)) if L else False
    y = H - 4 - 15 * len(L)
    if L:
        pygame.draw.rect(surf, BLACK, (0, y - 2, W, H - y + 2))
    for txt, col in L:
        put(surf, F["small"], txt, (8, y), col, W - 16); y += 15

def etick_watch(d, now):
    E = (d or {}).get("etick") or {}
    if not E.get("next") or E.get("sys") != (d or {}).get("system"):
        return
    w = (E.get("win") or 0) * 60
    pn = pc_now(d, now)
    key = (E["sys"], E["next"])
    if E["next"] - w <= pn < E["next"] + w and ETA["key"] != key and ev_on("bgstick"):
        ETA["key"] = key
        k0 = XA_K[0]
        try:
            XA_K[0] = "bgstick"
            set_alert("TICK DEL BGS", f"empieza la ventana en {E['sys']} (± {E.get('win')} min)", BLUE, 6)
            play("ok")
        finally:
            XA_K[0] = k0

# --- MI FACCION (datos de GitHub) ---
FAC_URL = "https://raw.githubusercontent.com/ortemedder/cdsn-datos/main/faccion.json"
FAC_CACHE = os.path.join(PANEL_DIR, "faccion_cache.json")
FACD = {"data": None, "t": 0, "err": ""}
ES_ST = {"Expansion": "Expansión", "War": "Guerra", "CivilWar": "Guerra civil", "Election": "Elecciones", "Retreat": "Retirada",
         "Boom": "Auge", "Bust": "Crisis", "Famine": "Hambruna", "Outbreak": "Epidemia", "Lockdown": "Confinamiento",
         "CivilUnrest": "Disturbios", "PirateAttack": "Ataque pirata", "Drought": "Sequía", "Blight": "Plaga",
         "InfrastructureFailure": "Fallo infraestr.", "NaturalDisaster": "Desastre", "TerroristAttack": "Atentado",
         "CivilLiberty": "Libertad civil", "Investment": "Inversión", "PublicHoliday": "Festividad"}

def fac_loop():
    try:
        with open(FAC_CACHE, encoding="utf-8") as f:
            FACD.update(data=json.load(f))
    except (OSError, ValueError):
        pass
    url = FAC_URL
    try:
        u_ = open(os.path.join(PANEL_DIR, "faccion_url.txt")).read().strip()
        url = u_ or url
    except OSError:
        pass
    while True:
        try:
            import urllib.request
            req = urllib.request.Request(url + "?t=" + str(int(time.time() // 300)), headers={"User-Agent": "PanelEliteRPi/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                j = json.loads(r.read().decode("utf-8"))
            FACD.update(data=j, t=time.time(), err="")
            with open(FAC_CACHE + ".tmp", "w", encoding="utf-8") as f:
                json.dump(j, f)
            os.replace(FAC_CACHE + ".tmp", FAC_CACHE)
        except Exception as e:
            FACD["err"] = str(e)[:60]
        time.sleep(600)

threading.Thread(target=fac_loop, daemon=True, name="faccion").start()

def fac_rows():
    D = FACD["data"] or {}
    S = [v for v in (D.get("sistemas") or {}).values() if v.get("inf") and not v.get("fuera")]
    gap = lambda v: v["inf"] - (v.get("segunda_inf") or 0)
    S.sort(key=lambda v: (0 if v.get("ctrl") and (gap(v) < 5 or v.get("conflictos") or "Retreat" in (v.get("pendientes") or []) + (v.get("activos") or []))
                          else 1 if v.get("ctrl") else 2, -v["inf"]))
    return D, S, gap

def fac_states(v):
    st = [ES_ST.get(a, a) for a in v.get("activos") or []] + [ES_ST.get(a, a) + " (pend.)" for a in v.get("pendientes") or []] \
        + [ES_ST.get(a, a) + " (rec.)" for a in v.get("recuperando") or []]
    for c in v.get("conflictos") or []:
        st.insert(0, f"{'GUERRA' if (c.get('tipo') or '').lower() != 'election' else 'ELECCIONES'} vs {c.get('contra')} "
                     f"{c.get('ganados') or 0}-{c.get('perdidos') or 0}")
    return st

FAC_PER = 6
MENU[192] = MENU[193] = "MI FACCIÓN"
PARENT[192] = PARENT[193] = 0
TABS[3].append((192, "FACCIÓN"))
TABS.append([(165, "ESCUADRÓN"), (193, "FACCIÓN")])

def view_fac(surf, d, flags, now):
    D, S, gap = fac_rows()
    y = TOP + 3
    if not S:
        put(surf, F["btn"], "sin datos de la facción", (W // 2, H // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], FACD["err"] or "descargando…", (W // 2, H // 2 + 14), DIM, W - 16, anchor="center")
        return
    pages = (len(S) + FAC_PER - 1) // FAC_PER
    pg = ui.get("facpg", 0) % pages
    put(surf, F["btn"], (D.get("faccion") or "").upper(), (8, y), ORANGE, 230)
    put(surf, F["small"], f"{sum(1 for v in S if v.get('ctrl'))} controlados · {len(S)} sistemas", (W - 8, y + 4), DIM, anchor="topright")
    y += 22
    for v in S[pg * FAC_PER:(pg + 1) * FAC_PER]:
        g = gap(v)
        pygame.draw.line(surf, (40, 28, 10), (6, y - 1), (W - 6, y - 1))
        col = ORANGE if v.get("ctrl") else WHITE
        if v.get("ctrl"):
            pygame.draw.polygon(surf, ORANGE, [(8, y + 4), (14, y + 4), (11, y + 9)])
        put(surf, F["small"], v["sys"].upper(), (18, y + 1), col, 170)
        st = fac_states(v)
        put(surf, F["small"], ", ".join(st) or "sin estados", (18, y + 15), RED if v.get("conflictos") or "Retreat" in " ".join(st) else BLUE if st else DIM, 170)
        bx = pygame.Rect(194, y + 5, 110, 12); pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, ORANGE if v.get("ctrl") else (170, 170, 170), (bx.x + 1, bx.y + 1, int((bx.w - 2) * min(100, v["inf"]) / 100), bx.h - 2))
        tx = bx.x + int(bx.w * min(100, v.get("segunda_inf") or 0) / 100); pygame.draw.line(surf, RED, (tx, bx.y - 2), (tx, bx.bottom + 1), 2)
        put(surf, F["btn"], f"{v['inf']:.1f}%".replace(".", ","), (310, y + 2), col)
        if v.get("prev") is not None and abs(v["inf"] - v["prev"]) >= 0.1:
            tr = v["inf"] - v["prev"]; c_ = GREEN if tr > 0 else RED; x_, y_ = 312, y + 21
            pygame.draw.polygon(surf, c_, [(x_, y_ + 5), (x_ + 8, y_ + 5), (x_ + 4, y_)] if tr > 0 else [(x_, y_), (x_ + 8, y_), (x_ + 4, y_ + 5)])
            put(surf, F["small"], f"{abs(tr):.1f}".replace(".", ","), (x_ + 11, y_ - 3), c_)
        put(surf, F["btn"], (f"+{g:.1f}" if g >= 0 else f"{g:.1f}").replace(".", ","), (W - 60, y + 2),
            GREEN if g >= 5 else ORANGE if g >= 0 else DIM, anchor="topright")
        age = (time.time() - (v.get("t") or 0)) / 3600
        put(surf, F["small"], f"{age:.0f} h" if age < 48 else f"{age / 24:.0f} d", (W - 8, y + 5), DIM, anchor="topright")
        y += 32
    put(surf, F["small"], (f"pág {pg + 1}/{pages} · toca para pasar  ·  " if pages > 1 else "") + "raya roja = 2ª facción · +N = ventaja",
        (8, H - 14), DIM, W - 16)

VIEWS[192] = VIEWS[193] = view_fac

def fac_summary(maxn=3):
    D, S, gap = fac_rows()
    if not S:
        return None, []
    head = f"{(D.get('faccion') or '').upper()} · {sum(1 for v in S if v.get('ctrl'))} controlados · {len(S)} sistemas"
    return head, S

_idle_crawl_b4 = idle_crawl

def idle_crawl(surf, now, box=None, waiting=True):
    _idle_crawl_b4(surf, now, box, waiting)
    head, S = fac_summary()
    if not S or int(now // 20) % 2 == 0:
        return                                           # 20 s GALNET, 20 s facción
    box = box or IDLE_BOX
    w_ = tw_(F["small"], "NOTICIAS GALNET") + 4
    pygame.draw.rect(surf, BLACK, (box.x + 6, box.y + 3, w_ + 4, 16))
    put(surf, F["small"], head, (box.x + 8, box.y + 5), ORANGE, box.w // 2)
    area = pygame.Rect(box.x + 8, box.y + 24, box.w - 16, box.h - 28)
    pygame.draw.rect(surf, BLACK, area)
    D, S, gap = fac_rows()
    y = area.y + 2
    for v in S:
        if y + 16 > area.bottom:
            break
        g = gap(v)
        alarm = v.get("ctrl") and (g < 5 or v.get("conflictos") or "Retreat" in (v.get("pendientes") or []) + (v.get("activos") or []))
        col = RED if alarm else ORANGE if v.get("ctrl") else WHITE
        put(surf, F["small"], ("» " if v.get("ctrl") else "   ") + v["sys"].upper(), (area.x, y), col, area.w * 0.42)
        put(surf, F["small"], f"{v['inf']:.1f} %  ({'+' if g >= 0 else ''}{g:.1f})".replace(".", ","), (area.x + area.w * 0.44, y), col)
        put(surf, F["small"], ", ".join(fac_states(v)), (area.x + area.w * 0.66, y), RED if alarm else BLUE, area.w * 0.34)
        y += 16

_on_tap_b4 = on_tap

def on_tap(x, y):
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
    _on_tap_b4(x, y)

_render_b4 = render

def render(surf):
    try:
        with lock:
            d_ = state["data"]
        etick_watch(d_, time.time())
    except Exception:
        pass
    return _render_b4(surf)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 4
- COMBATE, COMBATE + CAZA y CAZA con pestañas: se puede abrir cualquiera a mano.
- VIAJES con zoom: tocar el mapa lo amplía x2 donde tocas (hasta x64); el botón − aleja. Con zoom salen más nombres.
- Pantalla del sistema: tick del BGS de ESE sistema con datos de EDCAS (próximo tick con su margen, último tick y gráfica de la hora del tick de los últimos días). Aviso al empezar la ventana. Si EDCAS no tiene datos, el tick general.
- Las alertas ya no cortan el texto: la letra se hace más pequeña o se parte en dos líneas.
- MI FACCIÓN (pestaña FACCIÓN en DÍA y en ESCUADRÓN): todos los sistemas de tu facción, primero los que están en peligro, con influencia, ventaja sobre la 2ª facción, estados, conflictos y cambio desde el dato anterior. Los datos los sube a GitHub la escucha de EDDN. En la pantalla de espera, el recuadro alterna 20 s GALNET y 20 s tu facción.
# Enlace energético''')
rep('    ("1.0b3", ', '    ("1.0b4", "Pestañas de combate, zoom en VIAJES, tick EDCAS, alertas que caben, MI FACCIÓN"),\n    ("1.0b3", ')
s = re.sub(r'PANEL_VER = "v1\.0b3[^"]*"', 'PANEL_VER = "v1.0b4 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 4  (copia en " + P + ".bak100b3)")
