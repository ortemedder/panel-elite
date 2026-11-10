#!/usr/bin/env python3
# Parche v1.0 beta 10b (desde la beta 10): en el menu 7 el boton < MENU no hacia nada.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "# b10b: menu 7" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b10 ', s):
    sys.exit("Este parche es para la v1.0 beta 10")
shutil.copy(P, P + ".bak100b10")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('''                if i == 7:
                    ACT_GAL[0] = True
                TAP_EV.set(); return
        return
    if v in (77, 78):''', '''                if i == 7:
                    ACT_GAL[0] = True
                TAP_EV.set(); return
        # b10b: menu 7, fuera de los 8 botones sigue (el boton < MENU)
    if v in (77, 78):''')
rep('''- Al arrancar, la Pi sincroniza la hora;''', '''- (10b) Menú 7: el botón < MENÚ vuelve a funcionar.
- Al arrancar, la Pi sincroniza la hora;''')
rep('    ("1.0b10", ', '    ("1.0b10b", "Menú 7: el botón < MENÚ vuelve a funcionar"),\n    ("1.0b10", ')
s = re.sub(r'PANEL_VER = "v1\.0b10 [^"]*"', 'PANEL_VER = "v1.0b10b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 10b  (copia en " + P + ".bak100b10)")
