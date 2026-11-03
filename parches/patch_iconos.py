import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak49")
s = open(p, encoding="utf-8").read()
if "def view_menux" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- menu principal con iconos (12.4 -> 7 ICONOS) ----------
ICONS_FILE = "/home/ortem/iconos.txt"
try:
    ICONS_ON = [open(ICONS_FILE).read().strip() == "si"]
except OSError:
    ICONS_ON = [False]

def icons_toggle():
    ICONS_ON[0] = not ICONS_ON[0]
    try:
        with open(ICONS_FILE, "w") as f:
            f.write("si" if ICONS_ON[0] else "no")
    except OSError:
        pass

def menu_icon(s, i, c, cx, cy):
    L = lambda a, b, w=2: pygame.draw.line(s, c, a, b, w)
    C = lambda p_, r, w=2: pygame.draw.circle(s, c, p_, r, w)
    R = lambda x, y, w, h, wd=2: pygame.draw.rect(s, c, (cx + x, cy + y, w, h), wd)
    if i == 0:
        R(-12, 6, 24, 6); L((cx, cy + 6), (cx, cy - 8), 3); C((cx, cy - 11), 5, 0)
    elif i == 1:
        for j, h in enumerate((10, 16, 8)):
            R(-13 + j * 10, 10 - h, 7, h, 0)
    elif i == 2:
        C((cx, cy), 13); pygame.draw.polygon(s, c, [(cx, cy - 11), (cx + 4, cy), (cx, cy + 11), (cx - 4, cy)], 0)
    elif i == 3:
        R(-12, -9, 24, 18); L((cx - 12, cy - 3), (cx + 12, cy - 3)); L((cx, cy - 9), (cx, cy - 3))
    elif i == 4:
        R(-14, -6, 28, 9); C((cx - 8, cy + 7), 4); C((cx + 8, cy + 7), 4)
    elif i == 5:
        C((cx, cy), 11); L((cx - 15, cy), (cx - 5, cy)); L((cx + 5, cy), (cx + 15, cy))
        L((cx, cy - 15), (cx, cy - 5)); L((cx, cy + 5), (cx, cy + 15))
    elif i == 6:
        C((cx, cy), 8, 0); pygame.draw.ellipse(s, c, (cx - 16, cy - 4, 32, 8), 2)
    elif i == 7:
        pygame.draw.polygon(s, c, [(cx, cy - 13), (cx + 13, cy), (cx, cy + 13), (cx - 13, cy)], 2); R(-5, -2, 10, 4, 0)
    elif i == 8:
        pygame.draw.polygon(s, c, [(cx, cy - 12), (cx + 11, cy + 10), (cx, cy + 5), (cx - 11, cy + 10)], 2)
    elif i == 9:
        pygame.draw.polygon(s, c, [(cx - 12, cy + 2), (cx - 5, cy - 9), (cx + 6, cy - 7), (cx + 12, cy + 3),
                                   (cx + 3, cy + 11), (cx - 8, cy + 9)], 2); L((cx - 3, cy - 1), (cx + 4, cy + 4))
    elif i == 10:
        C((cx, cy), 12); L((cx, cy), (cx, cy - 8)); L((cx, cy), (cx + 6, cy + 3))
    elif i == 11:
        C((cx, cy), 6)
        for a in range(8):
            r = math.radians(a * 45)
            L((cx + 9 * math.cos(r), cy + 9 * math.sin(r)), (cx + 13 * math.cos(r), cy + 13 * math.sin(r)), 3)

def view_menux(surf, d, flags, now):
    if not ICONS_ON[0]:
        return view_menu(surf, d, flags, now)
    for i in range(12):
        name = MENU.get(i + 1)
        r = grid(i)
        draw_button(surf, r, "", None, F["small"], lit=flash.get((0, i), 0) > now, dim=name is None)
        col = DIM if name is None else ORANGE
        menu_icon(surf, i, col, r.centerx, r.y + int(r.h * 0.38))
        put(surf, F["small"], f"{i + 1} {name or 'vacío'}", (r.centerx, r.bottom - 18), col, r.w - 8, anchor="midtop")

'''
rep("def view_sub12", SNIP + "def view_sub12")
rep("0: view_menu,", "0: view_menux,")
rep('("6", "BORDES")]', '("6", "BORDES"), ("7", "ICONOS")]')
rep('''if i == 5 else name),''', '''if i == 5 else f"ICONOS {'SÍ' if ICONS_ON[0] else 'NO'}" if i == 6 else name),''')
rep('draw_button(surf, grid(i, 3, 2), n, "¿SEGURO?" if sure', 'draw_button(surf, grid(i, 4, 2), n, "¿SEGURO?" if sure')
rep('''    if i == 5:
        borders_toggle(); return''', '''    if i == 5:
        borders_toggle(); return
    if i == 6:
        icons_toggle(); return''')
s, n = re.subn(r'(for i in range\()6(\):\n\s+if grid\(i, )3, 2(\)\.collidepoint\(x, y\):\n\s+power_tap\(i\); return)', r'\g<1>7\g<2>4, 2\g<3>', s, count=1)
if not n: print("NO ENCONTRADO: toque del 12.4"); ok = False
rep("\n]\n\ndef view_changelog", '\n    ("0.49", "Menú principal con iconos (botón ICONOS)"),\n]\n\ndef view_changelog')
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.49 · 29/10/2026 14:30"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
