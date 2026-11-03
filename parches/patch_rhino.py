import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak18")
s = open(p, encoding="utf-8").read()
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
rep('    elif flags & (1 << 26):\n        mode = "SRV"\n', '    elif flags & (1 << 26):\n        mode = (d.get("srvtype") or "SRV").upper()\n')
rep('    elif mode == "SRV":\n', '    elif flags & (1 << 26):\n')
rep("    for i, v in enumerate(cells):", '''    if mode == "SUPERFICIE" and flags & (1 << 26) and "rhino" in (d.get("srvtype") or "").lower():
        cells = [100, 74, 5, 128]
    for i, v in enumerate(cells):''')
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.18 · 28/10/2026 23:55"', s, count=1)
if not n: print("NO ENCONTRADO: PANEL_VER"); ok = False
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
