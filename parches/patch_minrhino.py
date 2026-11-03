import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak27")
s = open(p, encoding="utf-8").read()
old = '''    m = (d or {}).get("mining") or {}
    last = m.get("last")
    y = TOP + 6
'''
if "BODEGA DEL RHINO" in s:
    print("ya estaba"); raise SystemExit
if old not in s:
    print("NO ENCONTRADO"); raise SystemExit
new = old + '''    if "rhino" in ((d or {}).get("srvtype") or "").lower():
        put(surf, F["small"], "BODEGA DEL RHINO", (8, y), DIM)
        put(surf, F["small"], "REFINADO (SESIÓN)", (318, y), DIM); y += 14
        yy = y
        inv, tot = (d or {}).get("srvinv") or [], (d or {}).get("srvcargo")
        put(surf, F["big"], f"{tot if tot is not None else '?'} t", (8, y), ORANGE); y += 30
        for name, n in inv[:8]:
            put(surf, F["small"], name, (8, y + 2), ORANGE, 220)
            put(surf, F["btn"], f"{n} t", (300, y), WHITE, anchor="topright"); y += 20
        if not inv:
            put(surf, F["small"], "vacía", (8, y), DIM)
        pygame.draw.line(surf, DIM, (310, yy - 14), (310, H - 30))
        ref = sorted((m.get("refined") or {}).items(), key=lambda kv: -kv[1])
        if not ref:
            put(surf, F["small"], "nada aún", (318, yy + 4), DIM)
        for name, n in ref[:8]:
            put(surf, F["small"], name, (318, yy + 2), ORANGE, 110)
            put(surf, F["btn"], f"{n}", (W - 8, yy), ORANGE, anchor="topright"); yy += 20
        pygame.draw.line(surf, DIM, (8, H - 26), (W - 8, H - 26))
        sf = ((d or {}).get("Fuel") or {}).get("FuelReservoir")
        put(surf, F["btn"], f"COMBUSTIBLE: {sf:.2f} t".replace(".", ",") if sf is not None else "COMBUSTIBLE: ?",
            (8, H - 22), RED if sf is not None and sf < 0.1 else ORANGE)
        zonas = sum(c for n, c in (((d or {}).get("rings") or {}).get("signals") or []) if "miner" in n.lower() or "mining" in n.lower())
        put(surf, F["small"], f"Zonas de minería en el planeta: {zonas}", (W - 8, H - 18), DIM, anchor="topright")
        return
'''
s = s.replace(old, new, 1)
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.27 · 29/10/2026 01:30"', s, count=1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
