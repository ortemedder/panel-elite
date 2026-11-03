p = "/home/ortem/panel.py"
s = open(p, encoding="utf-8").read()
if "PANEL_VER" in s:
    import re
    s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v10 · 28/10/2026 18:17"', s, count=1)
    open(p, "w", encoding="utf-8").write(s); print("OK (actualizada)"); raise SystemExit
call = "        fn(surf, d if online else None, flags, now)\n"
if call not in s or "def render(surf):" not in s:
    print("NO ENCONTRADO"); raise SystemExit
s = s.replace("def render(surf):", 'PANEL_VER = "v10 · 28/10/2026 18:17"\n\ndef render(surf):', 1)
s = s.replace(call, call + '        if v == 100:\n            put(surf, F["small"], PANEL_VER, (W - 6, H - 14), GREEN, anchor="topright")\n', 1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
