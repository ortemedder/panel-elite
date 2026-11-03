import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak50")
s = open(p, encoding="utf-8").read()
if "def view_diary" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
a2 = '        elif kind == "gravity" and len(p) >= 2:'
rep(a2, r'''        elif kind == "honk" and len(p) >= 3:
            n = int(p[0] or 0)
            known = int(p[2]) if p[2] not in ("", "None") else None
            info_ = "SIN DATOS EN EDSM: todo por descubrir" if not known else (
                f"EDSM conoce {known} · {max(0, n - known)} nuevos" if n > known else f"EDSM los conoce todos ({known})")
            xa["a"] = dict(until=now + 4, col=(90, 200, 255), title="ESCANEO DE DESCUBRIMIENTO", big=f"{n} CUERPOS",
                           lines=[f"{p[1]} señales", info_])
        elif kind == "risk" and len(p) >= 1:
            xa["a"] = dict(until=now + 6, col=ORANGE, title="DATOS EN RIESGO", big=f"{cr(float(p[0]))} cr",
                           lines=["llevas esto sin vender", "si te destruyen, se pierde"])
''' + a2)
rep("def view_sub12", r'''# ---------- 7.5 diario de exploracion ----------
def view_diary(surf, d, flags, now):
    X = (d or {}).get("exdiary") or {}
    y = TOP + 6
    secs = int(now - (X.get("start") or now))
    put(surf, F["small"], f"SESIÓN DE EXPLORACIÓN · {secs // 3600}h {secs % 3600 // 60:02d}m", (8, y), DIM); y += 18
    rows = [("SISTEMAS VISITADOS", X.get("systems", 0), WHITE), ("AÑOS LUZ", X.get("ly", 0), WHITE),
            ("CUERPOS ESCANEADOS", X.get("scanned", 0), WHITE), ("1º DESCUBRIMIENTOS", X.get("first", 0), GREEN),
            ("CUERPOS MAPEADOS", X.get("mapped", 0), WHITE), ("1º MAPEADOS", X.get("first_mapped", 0), GREEN),
            ("MUESTRAS BIO", X.get("bio", 0), WHITE)]
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

''' + "def view_sub12")
rep('("4", "YACIM.")]):\n        draw_button(surf, grid(i, 4, 1)', '("4", "YACIM."), ("5", "DIARIO")]):\n        draw_button(surf, grid(i, 3, 2)')
rep('74: "YACIMIENTOS"', '74: "YACIMIENTOS", 75: "DIARIO DE EXPLORACIÓN"')
rep("74: 7,", "74: 7, 75: 7,")
rep("74: view_rings,", "74: view_rings, 75: view_diary,")
rep('''        put(surf, F["small"], f"RUTA  -  destino: {route[-1][0]}", (8, y), DIM, W - 16); y += 18''',
'''        put(surf, F["small"], f"RUTA  -  destino: {route[-1][0]}", (8, y), DIM, W - 210)
        RI = (d or {}).get("routeinfo") or {}
        bits = []
        if RI.get("eta"):
            bits.append(f"ETA {RI['eta'] // 3600}h {RI['eta'] % 3600 // 60:02d}m" if RI["eta"] >= 3600 else f"ETA {RI['eta'] // 60} min")
        if RI.get("neutron"):
            bits.append(f"neutrón a {RI['neutron']}")
        if bits:
            put(surf, F["small"], "  ·  ".join(bits), (W - 8, y), BLUE, anchor="topright")
        y += 18''')
s, n = re.subn(r'(for i in range\()4(\):\n\s+if grid\(i, )4, 1(\)\.collidepoint\(x, y\):\n\s+tap_flash\(\(7, i\)\))', r'\g<1>5\g<2>3, 2\g<3>', s, count=1)
if not n: print("NO ENCONTRADO: toque del 7"); ok = False
rep("\n]\n\ndef view_changelog", '\n    ("0.50", "Exploración: escaneo, ruta, diario 7.5, riesgo y distancias"),\n]\n\ndef view_changelog')
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.50 · 29/10/2026 14:50"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
