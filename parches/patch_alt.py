import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak21")
s = open(p, encoding="utf-8").read()
old = '''            put(surf, F["small"], "ALTITUD", (250, y + 4), DIM)
            put(surf, F["btn"], f"{alt / 1000:.1f} km".replace(".", ",") if alt >= 1000 else f"{alt:.0f} m",
                (W - 8, y + 1), ORANGE, anchor="topright")'''
new = '''            real = not flags & (1 << 29)
            lab, acol = "ALTITUD", ORANGE
            if real and alt <= 30:
                lab, acol = "RHINO OK", GREEN
            elif real and alt <= 60:
                lab, acol = "BAJA A 30 m", ORANGE
            put(surf, F["small"], lab, (250, y + 4), acol if lab != "ALTITUD" else DIM)
            put(surf, F["btn"], f"{alt / 1000:.1f} km".replace(".", ",") if alt >= 1000 else f"{alt:.0f} m",
                (W - 8, y + 1), acol, anchor="topright")'''
if "RHINO OK" in s:
    print("ya estaba"); raise SystemExit
if old not in s:
    print("NO ENCONTRADO"); raise SystemExit
s = s.replace(old, new, 1)
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.21 · 29/10/2026 00:25"', s, count=1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
