import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak19")
s = open(p, encoding="utf-8").read()
old = '''("CARGA", flags & (1 << 9), ORANGE), ("SOBRECALENT.", flags & (1 << 20), RED)], y)
        draw_compass(surf, d, d.get("bio") or {})'''
if "srvcargo" in s:
    print("ya estaba"); raise SystemExit
if old not in s:
    print("NO ENCONTRADO"); raise SystemExit
s = s.replace(old, '''("CARGA", flags & (1 << 9), ORANGE), ("SOBRECALENT.", flags & (1 << 20), RED)], y)
        if d.get("srvcargo") is not None:
            put(surf, F["small"], "BODEGA DEL VEHÍCULO", (8, y + 8), DIM)
            put(surf, F["big"], f"{d['srvcargo']} t", (170, y + 2), ORANGE)
        draw_compass(surf, d, d.get("bio") or {})''', 1)
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.19 · 29/10/2026 00:10"', s, count=1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
