import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak33")
s = open(p, encoding="utf-8").read()
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
if '"ATRAQUE"' in s:
    print("ya estaba"); raise SystemExit
rep('"ATRACADO": [100, 8, 127, 4],', '"ATRACADO": [100, 8, 127, 4], "ATRAQUE": [8],')
rep('''    if flags & 1:
        return "ATRACADO"
''', '''    if flags & 1:
        return "ATRACADO"
    if (d.get("station") or {}).get("status") == "CONCEDIDO":
        return "ATRAQUE"
''')
rep("    for i, v in enumerate(cells):", '''    if len(cells) == 1:
        cell.fill(BLACK)
        try:
            VIEWS[cells[0]](cell, d, flags, now)
        except Exception as e:
            put(cell, F["small"], f"error: {e}"[:60], (8, TOP + 8), RED)
        big_blit(S, cell.subsurface((0, TOP, W, H - TOP)), pygame.Rect(4, hh + 4, bw - 8, bh - hh - 8))
        return
    for i, v in enumerate(cells):''')
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.33 · 29/10/2026 02:30"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
