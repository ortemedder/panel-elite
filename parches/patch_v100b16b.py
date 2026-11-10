#!/usr/bin/env python3
# Parche v1.0 beta 16b (desde la beta 16): MERCADO daba «Error en esta pantalla» con el sender v1.0b11
# (las mercancias de la colonia llegan con un dato mas, su nombre interno).
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "# b16b: mercado" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b16 ', s):
    sys.exit("Este parche es para la v1.0 beta 16")
shutil.copy(P, P + ".bak100b16")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('''    for name, stock, price, need in rows[:n]:''', '''    for name, stock, price, need in (r_[:4] for r_ in rows[:n]):     # b16b: mercado, ahora con 5 datos''')
rep('''    for name, stock, price, need in L[:n]:''', '''    for name, stock, price, need in (r_[:4] for r_ in L[:n]):''')
rep('''# Novedades v1.0 beta 16''', '''# Novedades v1.0 beta 16b
- Arreglado «Error en esta pantalla» en MERCADO con el recuadro PARA TU COLONIA (sender v1.0b11).
# Novedades v1.0 beta 16''')
rep('    ("1.0b16", ', '    ("1.0b16b", "Arreglo del error en MERCADO"),\n    ("1.0b16", ')
s = re.sub(r'PANEL_VER = "v1\.0b16 [^"]*"', 'PANEL_VER = "v1.0b16b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 16b  (copia en " + P + ".bak100b16)")
