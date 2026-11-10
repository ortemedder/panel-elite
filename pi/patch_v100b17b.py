#!/usr/bin/env python3
# Parche v1.0 beta 17b (desde la beta 17): cronometro de salida de la estacion en 5:00 (antes 6:00).
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "EXIT_SECS = 300" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b17 ', s):
    sys.exit("Este parche es para la v1.0 beta 17")
shutil.copy(P, P + ".bak100b17")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep("EXIT_SECS = 360", "EXIT_SECS = 300")
rep('''# Novedades v1.0 beta 17''', '''# Novedades v1.0 beta 17b
- El cronómetro de salida de la estación empieza en 5:00.
# Novedades v1.0 beta 17''')
rep('    ("1.0b17", ', '    ("1.0b17b", "Cronómetro de salida en 5:00"),\n    ("1.0b17", ')
s = re.sub(r'PANEL_VER = "v1\.0b17 [^"]*"', 'PANEL_VER = "v1.0b17b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 17b  (copia en " + P + ".bak100b17)")
