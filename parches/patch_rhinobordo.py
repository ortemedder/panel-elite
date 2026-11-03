import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak29")
s = open(p, encoding="utf-8").read()
old = '        chips(surf, [("ATRACADO", flags & 1, BLUE),'
if "RHINO {rh}" in s:
    print("ya estaba"); raise SystemExit
if old not in s:
    print("NO ENCONTRADO"); raise SystemExit
s = s.replace(old, '''        rh = sh.get("rhino")
        rcol = GREEN if rh == "A BORDO" else RED if rh == "SIN RHINO" else ORANGE
        chips(surf, ([(f"RHINO {rh}" if rh != "SIN RHINO" else rh, rh in ("A BORDO", "SIN RHINO", "FUERA"), rcol)] if rh else []) + [("ATRACADO", flags & 1, BLUE),''', 1)
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.29 · 29/10/2026 01:55"', s, count=1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
