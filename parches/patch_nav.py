import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak20")
s = open(p, encoding="utf-8").read()
if "def view_navx" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- 3 navegacion: ficha del destino dentro del sistema ----------
def view_navx(surf, d, flags, now):
    D = (d or {}).get("dest")
    if not D or not D.get("name"):
        return view_nav(surf, d, flags, now)
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
    src = D.get("src")
    put(surf, F["small"], f"datos: {src}" if src else "sin datos: no escaneado (o es una estación/señal)",
        (8, H - 16), DIM if src else ORANGE)

'''
rep("def view_sub12", SNIP + "def view_sub12")
rep("3: view_nav,", "3: view_navx,")
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.20 · 29/10/2026 00:15"', s, count=1)
if not n: print("NO ENCONTRADO: PANEL_VER"); ok = False
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
