#!/usr/bin/env python3
# Parche v0.91: foto de fondo al pedir atraque en cada tipo de estacion, base y asentamiento.
# Las fotos fondo_*.jpg van junto a panel.py; si falta alguna, ese tipo sale como antes.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "ST_BG = " in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.90c' not in s:
    sys.exit("Este parche es para la v0.90c")
shutil.copy(P, P + ".bak90c")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

rep('''        return "fc", ("TU PORTANAVES" if mid and mid == own.get("id") else "PORTANAVES"), ORANGE
    return None, "", None''', '''        return "fc", ("TU PORTANAVES" if mid and mid == own.get("id") else "PORTANAVES"), ORANGE
    if stype in ST_BG:
        return ST_BG[stype], ST_TYPE.get(stype, stype).upper(), ORANGE
    return None, "", None''')
rep('''BG_FILES = {"fc": "fondo_portanaves.jpg", "sq": "fondo_escuadron.jpg"}''',
    '''BG_FILES = {"fc": "fondo_portanaves.jpg", "sq": "fondo_escuadron.jpg"}
ST_BG = {"Coriolis": "coriolis", "Orbis": "orbis", "Ocellus": "ocellus", "Bernal": "ocellus", "Dodec": "dodec",
         "AsteroidBase": "asteroide", "Outpost": "outpost", "MegaShip": "meganave", "CraterPort": "craterport",
         "SurfaceStation": "craterport", "CraterOutpost": "crateroutpost", "OnFootSettlement": "asentamiento"}
BG_FILES.update({v: f"fondo_{v}.jpg" for v in set(ST_BG.values())})''')

rep('''    put(surf, F["big"], label, (8, H - 30), col, W - 16)''',
    '''    put(surf, F["big"], label, (W - 8, H - 30), col, W // 2 + 20, anchor="topright")''')

rep('''# Enlace energético''', '''# Novedades v0.91
- Al pedir atraque sale la foto de cada tipo de sitio de fondo: Coriolis, Orbis, Ocellus, Dodec, base asteroide, puesto avanzado, mega nave, puerto y puesto planetario y asentamiento (fondo_*.jpg junto a panel.py).
# Enlace energético''')
rep('    ("0.90c", "Neutrones sin modo combate y foto del portanaves en la ruta"),\n',
    '    ("0.90c", "Neutrones sin modo combate y foto del portanaves en la ruta"),\n'
    '    ("0.91", "Fotos de fondo de cada tipo de estación al pedir atraque"),\n')
s = re.sub(r'PANEL_VER = "v0\.90c[^"]*"', 'PANEL_VER = "v0.91 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.91  (copia en " + P + ".bak90c)")
