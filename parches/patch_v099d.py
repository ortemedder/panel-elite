#!/usr/bin/env python3
# Parche v0.99d: fotos de los depositos de construccion (colonizacion).
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "SpaceConstructionDepot" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.99' not in s:
    sys.exit("Este parche es para la v0.99c")
shutil.copy(P, P + ".bak99c")
code = r'''
# ---------- v0.99d: depositos de construccion ----------
ST_BG.update({"SpaceConstructionDepot": "deposito_espacial", "PlanetaryConstructionDepot": "deposito_planetario"})
BG_FILES.update({"deposito_espacial": "fondo_deposito_espacial.jpg", "deposito_planetario": "fondo_deposito_planetario.jpg"})
ST_TYPE.update({"SpaceConstructionDepot": "Depósito de construcción", "PlanetaryConstructionDepot": "Depósito planetario"})

'''
s = s.replace("\ndef render(surf):", code + "\ndef render(surf):", 1)
s = s.replace('    ("0.99c", "Fotos de los cazas"),\n',
              '    ("0.99c", "Fotos de los cazas"),\n    ("0.99d", "Fotos de los depósitos de construcción y fotos mejores"),\n', 1)
s = re.sub(r'PANEL_VER = "v0\.99[^"]*"', 'PANEL_VER = "v0.99d · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99d  (copia en " + P + ".bak99c)")
