import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak34")
s = open(p, encoding="utf-8").read()
if "def view_pol" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- 3 navegacion: cara SISTEMA (politica) ----------
pol = {"sys": None, "until": 0}

def nav_show_pol(d, now):
    sysn = (d or {}).get("system")
    if sysn and sysn != pol["sys"]:
        if pol["sys"] is not None:
            pol["until"] = now + 20
        pol["sys"] = sysn
    return bool(ui.get("navtab")) or now < pol["until"]

def view_pol(surf, d, flags, now):
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

'''
rep("def view_navx(", SNIP + "def view_navx(")
rep('''def view_navx(surf, d, flags, now):
    D = (d or {}).get("dest")
    if not D or not D.get("name"):
        return view_nav(surf, d, flags, now)
''', '''def view_navx(surf, d, flags, now):
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
''')
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.34 · 29/10/2026 02:35"', s, count=1)
L = s.split("\n")
t = next((i for i, l in enumerate(L) if l.strip() == "elif v == 71:"), None)
if t is None:
    print("NO ENCONTRADO: toque"); ok = False
else:
    ind = L[t][:len(L[t]) - len(L[t].lstrip())]
    L[t:t] = [ind + "elif v == 3:", ind + "    ui['navtab'] = 0 if (ui.get('navtab') or time.time() < pol['until']) else 1; pol['until'] = 0; return"]
s = "\n".join(L)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
