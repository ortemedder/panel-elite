p = "/home/ortem/panel.py"
s = open(p, encoding="utf-8").read()
home = '        if v == 100:\n            put(surf, F["small"], PANEL_VER, (W - 6, H - 14), GREEN, anchor="topright")\n'
s = s.replace(home, "", 1)
old = '    put(surf, F["big"], "CMDR " + cfg["cmdr"], (290, 215), ORANGE, 300, anchor="center")\n'
if old not in s:
    print("NO ENCONTRADO"); raise SystemExit
if "PANEL_VER, (290" not in s:
    s = s.replace(old, old + '    put(surf, F["small"], PANEL_VER, (290, 270), GREEN, anchor="center")\n', 1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
