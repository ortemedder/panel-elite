#!/usr/bin/env python3
# Parche v0.99e: quita del LOG los "toque HDMI" (eran solo para la prueba de la pantalla de 7").
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
old = '''    if BIGTAP_N[0] < 30:
        BIGTAP_N[0] += 1
        plog(f"toque HDMI {xn:.2f},{yn:.2f}  modo {'PANEL' if hdmi_panel() else '4 CUADROS'}  cuadros {len(BIG.get('rects') or [])}")
'''
if old not in s:
    sys.exit("Ya estaba aplicado o no es la v0.99d")
shutil.copy(P, P + ".bak99d")
s = s.replace(old, "", 1)
s = s.replace('    ("0.99d", "Fotos de los depósitos de construcción y fotos mejores"),\n',
              '    ("0.99d", "Fotos de los depósitos de construcción y fotos mejores"),\n    ("0.99e", "Sin los toques de prueba en el LOG"),\n', 1)
s = re.sub(r'PANEL_VER = "v0\.99[^"]*"', 'PANEL_VER = "v0.99e · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99e  (copia en " + P + ".bak99d)")
