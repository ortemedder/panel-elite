import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak23")
s = open(p, encoding="utf-8").read()
n = s.count("SRV / A PIE")
if not n:
    print("NO ENCONTRADO"); raise SystemExit
s = s.replace("SRV / A PIE", "SRV / RHINO / A PIE")
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.23 · 29/10/2026 00:35"', s, count=1)
open(p, "w", encoding="utf-8").write(s)
print(f"OK ({n} cambios)")
