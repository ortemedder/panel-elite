#!/usr/bin/env python3
# Parche v0.97b: ficha del ingeniero en NAVEGACION (con la foto de su base al lado) y EXOBIOLOGIA en lugar de XENOBIOLOGIA.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "_navx3" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.97' not in s or "def eng_card" not in s:
    sys.exit("Este parche es para la v0.97")
shutil.copy(P, P + ".bak97")

# nombre del ingeniero: que no se corte cuando la ficha es estrecha
s = s.replace('''    put(surf, F["btn"], e["name"].upper(), (x, r.y + 4), BLUE, wd - 110)''',
              '''    narrow_ = r.w < W - 100                         # ficha estrecha: el rango baja a la segunda linea
    put(surf, F["btn"], e["name"].upper(), (x, r.y + 4), BLUE, wd if narrow_ else wd - F["small"].size(st)[0] - 12)''', 1)
s = s.replace('''    put(surf, F["small"], st, (r.right - 8, r.y + 7), col, 110, anchor="topright")
    put(surf, F["small"], eng_where(e), (x, r.y + 26), ORANGE, wd)''',
              '''    if not narrow_:
        put(surf, F["small"], st, (r.right - 8, r.y + 7), col, 110, anchor="topright")
    put(surf, F["small"], (st + "  ·  " if narrow_ else "") + eng_where(e), (x, r.y + 26), col if narrow_ else ORANGE, wd)''', 1)
# EXOBIOLOGIA (como en el juego)
for a, b in (("XENOBIOLOGÍA", "EXOBIOLOGÍA"), ('"XENOBIO"', '"EXOBIO"'), ("Xenobiología", "Exobiología"),
             ("xenobiología", "exobiología")):
    s = s.replace(a, b)

CODE = r'''
# ---------- v0.97b: la ficha del ingeniero pasa a NAVEGACION ----------
view_explo = _vex0
VIEWS[71] = _vex0
_navx3 = view_navx

def view_navx(surf, d, flags, now):
    _navx3(surf, d, flags, now)
    if not (ui.get("navtab") == 2 and not NAVBIG[0]) and not nav_show_pol(d, now) and eng_here(d):
        th = carrier_dest(d or {})[0]                 # foto de su base (destino marcado) a la derecha
        eng_card(surf, d or {}, pygame.Rect(4, H - 112, W - (190 if th else 8), 108))

VIEWS[3] = view_navx

'''
old = "\ndef render(surf):"
if old not in s:
    sys.exit("No encuentro render")
s = s.replace(old, CODE + old, 1)
s = s.replace("en 7.1 EXPLORACIÓN su ficha con cara", "en NAVEGACIÓN su ficha con cara (y la foto de su base si la marcas como destino)", 1)
s = s.replace('    ("0.97", "Misiones fijas en la pantalla grande y los 38 ingenieros con su ficha"),\n',
              '    ("0.97", "Misiones fijas en la pantalla grande y los 38 ingenieros con su ficha"),\n'
              '    ("0.97b", "Ficha del ingeniero en NAVEGACIÓN y EXOBIOLOGÍA"),\n', 1)
s = re.sub(r'PANEL_VER = "v0\.97[^"]*"', 'PANEL_VER = "v0.97b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.97b  (copia en " + P + ".bak97)")
