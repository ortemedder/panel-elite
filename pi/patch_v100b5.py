#!/usr/bin/env python3
# Parche v1.0 beta 5 (desde la beta 4):
#  - menu: 6 COMBATE (con pestanas COMBATE | COMBATE + CAZA | CAZA) y 9 FACCION
#  - pantalla de espera: titulo de la faccion bien tapado y letra mas pequena en sus datos
#  - FACCION: hora de la ultima actualizacion en rosa; tocar un sistema abre su ficha
#    (todas las facciones, Powerplay, datos del sistema, distancia desde donde estas); paginas con < >
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def view_facsys" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v1.0b4' not in s:
    sys.exit("Este parche es para la v1.0 beta 4")
shutil.copy(P, P + ".bak100b4")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# letra pequena nueva (15) en las dos versiones de las fuentes
rep('''    for k, base in (("big", 30), ("btn", 24), ("small", 18), ("num", 48), ("clock", 110), ("mono", 11)):''',
    '''    for k, base in (("big", 30), ("btn", 24), ("small", 18), ("num", 48), ("clock", 110), ("mono", 11), ("tiny", 15)):''')
rep('''             num=pygame.font.Font(None, 48), mono=pygame.font.Font(mono, 11), clock=pygame.font.Font(None, 110))''',
    '''             num=pygame.font.Font(None, 48), mono=pygame.font.Font(mono, 11), clock=pygame.font.Font(None, 110),
             tiny=pygame.font.Font(None, 15))''')

CODE = r'''
# ---------- v1.0 beta 5 ----------
# --- menu: 9 = FACCION ---
_menu_b5 = VIEWS[0]

def flag_icon(surf, col, cx, cy):
    pygame.draw.line(surf, col, (cx - 12, cy - 16), (cx - 12, cy + 18), 3)
    pygame.draw.polygon(surf, col, [(cx - 11, cy - 16), (cx + 14, cy - 10), (cx - 11, cy - 2)])
    pygame.draw.circle(surf, col, (cx + 6, cy + 10), 6, 2)

def view_menu_b5(surf, d, flags, now):
    keep = MENU.get(9)
    MENU[9] = "FACCIÓN"
    try:
        _menu_b5(surf, d, flags, now)
    finally:
        MENU[9] = keep
    if ICONS_ON[0]:
        r = grid(8)
        draw_button(surf, r, "", None, F["small"], lit=flash.get((0, 8), 0) > now)
        flag_icon(surf, ORANGE, r.centerx, r.y + int(r.h * 0.38))
        put(surf, F["small"], "9 FACCIÓN", (r.centerx, r.bottom - 18), ORANGE, r.w - 8, anchor="midtop")

VIEWS[0] = view_menu_b5

# --- traducciones ---
def _clean(v):
    v = str(v or "")
    if v.startswith("$"):
        v = v.split("_", 1)[-1].rstrip(";")
        for p_ in ("SECURITY_", "security_"):
            v = v.replace(p_, "")
    return v

TR_ = {"high": "Alta", "medium": "Media", "low": "Baja", "anarchy": "Anarquía", "lawless": "Sin ley",
       "Industrial": "Industrial", "Extraction": "Extracción", "Refinery": "Refinería", "Agri": "Agrícola", "Agriculture": "Agrícola",
       "HighTech": "Alta tecnología", "High Tech": "Alta tecnología", "Military": "Militar", "Tourism": "Turismo",
       "Service": "Servicios", "Colony": "Colonia", "Terraforming": "Terraformación", "Prison": "Prisión", "None": "—",
       "Democracy": "Democracia", "Corporate": "Corporativo", "Dictatorship": "Dictadura", "Feudal": "Feudal",
       "Patronage": "Mecenazgo", "Communism": "Comunismo", "Cooperative": "Cooperativa", "Confederacy": "Confederación",
       "Theocracy": "Teocracia", "PrisonColony": "Colonia penal", "Prison colony": "Colonia penal", "Anarchy": "Anarquía",
       "Federation": "Federación", "Empire": "Imperio", "Alliance": "Alianza", "Independent": "Independiente",
       "Fortified": "Fortificado", "Stronghold": "Bastión", "Exploited": "Explotado", "Unoccupied": "Sin ocupar",
       "Contested": "En disputa", "Controlled": "Controlado", "InPrepareRadius": "En preparación", "Prepared": "Preparado"}

def tr_(v):
    c = _clean(v)
    return TR_.get(c, TR_.get(c.lower(), c))

def fnum_pob(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "?"
    return f"{n / 1e9:.1f} mil M".replace(".", ",") if n >= 1e9 else f"{n / 1e6:.1f} M".replace(".", ",") if n >= 1e6 else f"{n:,}".replace(",", ".")

def fac_age(t):
    if not t:
        return "sin fecha", DIM
    a = time.time() - t
    if a < 3600:
        txt = f"hace {int(a // 60)} min"
    elif a < 86400:
        txt = f"hace {a / 3600:.0f} h"
    else:
        txt = f"hace {a / 86400:.0f} d"
    return txt, (MERC if a < 86400 else ORANGE)

# --- pantalla de espera: titulo bien tapado y letra pequena ---
def idle_crawl(surf, now, box=None, waiting=True):
    _idle_crawl_b4(surf, now, box, waiting)
    head, S = fac_summary()
    if not S or int(now // 20) % 2 == 0:
        return
    box = box or IDLE_BOX
    badge = tw_(F["small"], "ESPERANDO A ELITE DANGEROUS") + 30
    cover = pygame.Rect(box.x + 4, box.y + 2, box.w - 8 - badge, 18)
    pygame.draw.rect(surf, BLACK, cover)
    D = FACD["data"] or {}
    tmax = max([v.get("t") or 0 for v in S] or [0])
    a_txt, a_col = fac_age(tmax)
    nctl = sum(1 for v in S if v.get("ctrl"))
    x = put(surf, F["tiny"], (D.get("faccion") or "").upper(), (box.x + 8, box.y + 6), ORANGE)
    put(surf, F["tiny"], f" · {nctl} contr. · {a_txt}", (box.x + 8 + x, box.y + 6), a_col, max(20, cover.w - x - 8))
    area = pygame.Rect(box.x + 8, box.y + 24, box.w - 16, box.h - 28)
    pygame.draw.rect(surf, BLACK, area)
    D, S, gap = fac_rows()
    y = area.y + 1
    for v in S:
        if y + 14 > area.bottom:
            break
        g = gap(v)
        alarm = v.get("ctrl") and (g < 5 or v.get("conflictos") or "Retreat" in (v.get("pendientes") or []) + (v.get("activos") or []))
        col = RED if alarm else ORANGE if v.get("ctrl") else WHITE
        put(surf, F["tiny"], ("» " if v.get("ctrl") else "   ") + v["sys"].upper(), (area.x, y), col, area.w * 0.40)
        put(surf, F["tiny"], f"{v['inf']:.1f} %  ({'+' if g >= 0 else ''}{g:.1f})".replace(".", ","), (area.x + area.w * 0.41, y), col)
        put(surf, F["tiny"], ", ".join(fac_states(v)), (area.x + area.w * 0.60, y), RED if alarm else BLUE, area.w * 0.40)
        y += 14

# --- FACCION: hora de actualizacion, filas que se tocan y paginas ---
FROWS = []
MENU[194] = "SISTEMA DE LA FACCIÓN"
PARENT[194] = 192

def fac_pg_btn(k):
    return pygame.Rect(W - 96 + k * 46, H - 26, 42, 23)

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
    a_txt, a_col = fac_age(max([v.get("t") or 0 for v in S] or [0]))
    tmax = max([v.get("t") or 0 for v in S] or [0])
    put(surf, F["small"], f"act. {time.strftime('%H:%M', time.localtime(tmax))} ({a_txt})" if tmax else "sin fecha",
        (8 + x + 10, y + 4), a_col, W - x - 120)
    put(surf, F["small"], f"{sum(1 for v in S if v.get('ctrl'))} contr. · {len(S)} sist.", (W - 8, y + 4), DIM, anchor="topright")
    y += 22
    for v in S[pg * FAC_PER:(pg + 1) * FAC_PER]:
        FROWS.append((pygame.Rect(0, y - 1, W, 32), v["sys"]))
        g = gap(v)
        pygame.draw.line(surf, (40, 28, 10), (6, y - 1), (W - 6, y - 1))
        col = ORANGE if v.get("ctrl") else WHITE
        if v.get("ctrl"):
            pygame.draw.polygon(surf, ORANGE, [(8, y + 4), (14, y + 4), (11, y + 9)])
        put(surf, F["small"], v["sys"].upper(), (18, y + 1), col, 170)
        st = fac_states(v)
        put(surf, F["small"], ", ".join(st) or "sin estados", (18, y + 15),
            RED if v.get("conflictos") or "Retreat" in " ".join(st) else BLUE if st else DIM, 170)
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
        put(surf, F["small"], fac_age(v.get("t"))[0].replace("hace ", ""), (W - 8, y + 5), DIM, anchor="topright")
        y += 32
    put(surf, F["small"], (f"pág {pg + 1}/{pages} · " if pages > 1 else "") + "toca un sistema para ver su ficha",
        (8, H - 20), DIM, W - 110)
    if pages > 1:
        for k, t in enumerate(("<", ">")):
            draw_button(surf, fac_pg_btn(k), t, "", F["btn"], compact=True)

VIEWS[192] = VIEWS[193] = view_fac

def view_facsys(surf, d, flags, now):
    D = FACD["data"] or {}
    name = ui.get("facsys")
    v = (D.get("sistemas") or {}).get(name)
    if not v:
        put(surf, F["btn"], "sin datos de este sistema", (W // 2, H // 2), DIM, anchor="center"); return
    me = D.get("faccion")
    y = TOP + 3
    put(surf, F["btn"], name.upper(), (8, y), ORANGE, 260)
    pos, here = v.get("pos"), (d or {}).get("starpos")
    if pos and here and None not in pos:
        dist = math.dist(pos, here)
        put(surf, F["btn"], "AQUÍ" if dist < 0.01 else f"a {dist:,.1f} al".replace(",", "X").replace(".", ",").replace("X", "."),
            (W - 8, y), BLUE, anchor="topright")
    y += 21
    a_txt, a_col = fac_age(v.get("t"))
    put(surf, F["small"], f"datos {a_txt} · {v.get('src') or '?'}", (8, y), a_col)
    S_ = v.get("sis") or {}
    if S_:
        put(surf, F["small"], f"POBLACIÓN {fnum_pob(S_.get('pob'))}", (W - 8, y), DIM, anchor="topright")
    y += 16
    put(surf, F["small"], "CONTROLA", (8, y + 2), DIM)
    put(surf, F["btn"], v.get("ctrl_n") or ("tu facción" if v.get("ctrl") else "?"), (88, y - 1), ORANGE if v.get("ctrl") else WHITE, W - 96)
    y += 21
    if S_:
        eco = tr_(S_.get("eco")) + (f" / {tr_(S_.get('eco2'))}" if S_.get("eco2") and tr_(S_.get("eco2")) != "—" else "")
        put(surf, F["small"], f"SEGURIDAD {tr_(S_.get('seg'))}  ·  ECONOMÍA {eco}  ·  {tr_(S_.get('gov'))}, {tr_(S_.get('alg'))}",
            (8, y), WHITE, W - 16)
        y += 16
    pp = v.get("pp") or {}
    if pp.get("pot"):
        put(surf, F["small"], "POWERPLAY", (8, y + 1), DIM)
        x = 86 + put(surf, F["small"], f"{pp['pot']} · {tr_(pp.get('est'))}", (86, y + 1), BLUE, 240)
        if pp.get("prog") is not None:
            bx = pygame.Rect(x + 8, y + 3, 90, 10); pygame.draw.rect(surf, DIM, bx, 1)
            pr = max(0.0, min(1.0, float(pp["prog"])))
            pygame.draw.rect(surf, BLUE, (bx.x + 1, bx.y + 1, int((bx.w - 2) * pr), bx.h - 2))
            put(surf, F["small"], f"{pr * 100:.0f} %", (bx.right + 4, y + 1), BLUE)
        y += 16
    elif pp.get("pots"):
        put(surf, F["small"], "POWERPLAY  en disputa: " + ", ".join(pp["pots"]), (8, y + 1), BLUE, W - 16); y += 16
    elif pp:
        put(surf, F["small"], "POWERPLAY  sin potencia", (8, y + 1), DIM); y += 16
    pygame.draw.line(surf, DIM, (6, y + 1), (W - 6, y + 1)); y += 4
    T = sorted(v.get("todas") or [], key=lambda f: -(f.get("inf") or 0))
    if not T:
        put(surf, F["small"], "las demás facciones llegarán con el próximo dato de este sistema", (8, y + 4), DIM, W - 16)
    for f in T:
        if y + 15 > H - 30:
            put(surf, F["tiny"], f"… y {len(T) - T.index(f)} más", (8, y), DIM); break
        mine = f.get("n") == me
        col = ORANGE if mine else WHITE
        ctl = f.get("n") == v.get("ctrl_n")
        put(surf, F["tiny"], ("» " if ctl else "   ") + (f.get("n") or "?"), (8, y), col, 170)
        bx = pygame.Rect(182, y + 2, 80, 9); pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, ORANGE if mine else (150, 150, 150), (bx.x + 1, bx.y + 1, int((bx.w - 2) * min(100, f.get("inf") or 0) / 100), bx.h - 2))
        put(surf, F["tiny"], f"{f.get('inf') or 0:.1f}%".replace(".", ","), (268, y), col)
        st = [ES_ST.get(a, a) for a in f.get("act") or []] + [ES_ST.get(a, a) + " (p)" for a in f.get("pend") or []]
        put(surf, F["tiny"], ", ".join(st) or tr_(f.get("gov")), (312, y), BLUE if st else DIM, W - 318)
        y += 14
    for c in v.get("conflictos") or []:
        put(surf, F["small"], f"{'ELECCIONES' if (c.get('tipo') or '').lower() == 'election' else 'GUERRA'} contra {c.get('contra')}: "
                              f"{c.get('ganados') or 0}-{c.get('perdidos') or 0} días", (8, H - 44), RED, W - 110)
    draw_button(surf, pygame.Rect(4, H - 26, 90, 23), "< VOLVER", "", F["small"], compact=True)

VIEWS[194] = view_facsys

_on_tap_b5 = on_tap

def on_tap(x, y):
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
    _on_tap_b5(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 5
- Menú: el botón 9 es ahora FACCIÓN. CAZA está dentro de 6 COMBATE (pestañas COMBATE | COMBATE + CAZA | CAZA).
- Pantalla de espera: los datos de la facción en letra más pequeña (caben más sistemas) y con la hora del último dato.
- FACCIÓN: al lado del nombre, la hora de la última actualización en rosa (naranja si tiene más de un día). Tocar un sistema abre su ficha: quién lo controla, todas las facciones con su influencia y estados, Powerplay, seguridad, economía, población y la distancia desde donde estás. Páginas con los botones < >.
# Enlace energético''')
rep('    ("1.0b4", ', '    ("1.0b5", "Menú 9 FACCIÓN, ficha de cada sistema de la facción, espera más legible"),\n    ("1.0b4", ')
s = re.sub(r'PANEL_VER = "v1\.0b4[^"]*"', 'PANEL_VER = "v1.0b5 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 5  (copia en " + P + ".bak100b4)")
