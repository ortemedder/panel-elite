import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak24")
s = open(p, encoding="utf-8").read()
old = '''            put(surf, F["big"], f"{d['srvcargo']} t", (170, y + 2), ORANGE)'''
if "srvinv" in s:
    print("ya estaba"); raise SystemExit
if old not in s:
    print("NO ENCONTRADO"); raise SystemExit
s = s.replace(old, old + '''
            inv = ", ".join(f"{n} {c}" for n, c in (d.get("srvinv") or [])[:4])
            if inv:
                put(surf, F["small"], inv, (240, y + 8), WHITE, W - 248)''', 1)
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.24 · 29/10/2026 01:00"', s, count=1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
