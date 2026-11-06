#!/usr/bin/env python3
# Parche v0.99b: con una nave fijada y las armas guardadas, la pantalla grande cambia EXPLORACION por la ficha OBJETIVO
# (nombre, piloto, escudos, casco, buscado y foto grande de su nave).
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def view_target" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.99' not in s:
    sys.exit("Este parche es para la v0.99")
shutil.copy(P, P + ".bak99")
old = '''        cells[cells.index(133)] = 61                 # mega nave: REGISTRO DE COMBATE en lugar de GALNET'''
new = old + '''
    if d.get("target") and mode != "COMBATE" and len(cells) >= 3:
        k_ = next((c for c in (71, 72) if c in cells), cells[2])
        cells[cells.index(k_)] = 177                  # nave fijada sin armas: su ficha'''
if old not in s:
    sys.exit("No encuentro el sitio de los cuadros")
s = s.replace(old, new, 1)
code = r'''
# ---------- v0.99b: ficha del objetivo en la pantalla grande ----------
def view_target(surf, d, flags, now):
    view_combat(surf, d, flags, now)
    pygame.draw.rect(surf, BLACK, (0, CARD6, W, H - CARD6))
    t = (d or {}).get("target") or {}
    r = pygame.Rect(W // 2 - 122, CARD6 + 6, 244, H - CARD6 - 12)
    if not (cfg.get("cmdrpics", True) and ship_photo(surf, {"type": t.get("stype"), "ship": t.get("ship")}, {}, r)):
        put(surf, F["small"], "sin foto de esta nave", r.center, DIM, anchor="center")

VIEWS[177] = view_target
MENU[177] = "OBJETIVO"

'''
s = s.replace("\ndef render(surf):", code + "\ndef render(surf):", 1)
s = s.replace('    ("0.99", "Voz con Piper y COMBATE solo con las armas sacadas"),\n',
              '    ("0.99", "Voz con Piper y COMBATE solo con las armas sacadas"),\n'
              '    ("0.99b", "Nave fijada sin armas: ficha OBJETIVO en la pantalla grande"),\n', 1)
s = re.sub(r'PANEL_VER = "v0\.99[^"]*"', 'PANEL_VER = "v0.99b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99b  (copia en " + P + ".bak99)")
