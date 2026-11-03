import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak35")
s = open(p, encoding="utf-8").read()
if "def view_stationx" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- 8 estacion: a los 15 s de atracar, ficha de la estacion y facciones ----------
stdock = {"key": None, "t": 0}

def view_stationx(surf, d, flags, now):
    st = (d or {}).get("station") or {}
    key = (st.get("name"), st.get("status"))
    if st.get("status") == "ATRACADO":
        if stdock["key"] != key:
            stdock.update(key=key, t=now)
        if now - stdock["t"] >= 15:
            return view_station_info(surf, d, st)
    else:
        stdock["key"] = None
    return view_station(surf, d, flags, now)

def view_station_info(surf, d, st):
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

'''
rep("def view_sub12", SNIP + "def view_sub12")
rep(" 8: view_station,", " 8: view_stationx,")
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.35 · 29/10/2026 02:45"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
