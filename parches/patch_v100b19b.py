#!/usr/bin/env python3
# Parche v1.0 beta 19b (desde la beta 19): el RADAR (menu 7) daba error al arrastrar la lista de SISTEMAS CONTROLADOS.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "first_ = int(off_ // 14)" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b19 ', s):
    sys.exit("Este parche es para la v1.0 beta 19")
shutil.copy(P, P + ".bak100b19")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep("    first_ = off_ // 14", "    first_ = int(off_ // 14)")
rep('''    CTL_LIST["off"] = max(0, min(CTL_LIST["max"], DRAG["off0"] - (b[1] - DRAG["y0"])))''',
    '''    CTL_LIST["off"] = int(max(0, min(CTL_LIST["max"], DRAG["off0"] - (b[1] - DRAG["y0"]))))''')
rep('''# Novedades v1.0 beta 19''', '''# Novedades v1.0 beta 19b
- Arreglado el error del RADAR al arrastrar la lista de SISTEMAS CONTROLADOS.
# Novedades v1.0 beta 19''')
rep('    ("1.0b19", ', '    ("1.0b19b", "Arreglo del RADAR al arrastrar"),\n    ("1.0b19", ')
s = re.sub(r'PANEL_VER = "v1\.0b19 [^"]*"', 'PANEL_VER = "v1.0b19b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 19b  (copia en " + P + ".bak100b19)")
