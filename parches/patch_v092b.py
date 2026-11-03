#!/usr/bin/env python3
# Parche v0.92b: nombres de los gestos como los tiene el juego.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
old = 'EMOTES = ["SALUDAR", "SEÑALAR", "SÍ", "NO", "ADELANTE", "ALTO", "SALUDO MILITAR", "GRACIAS"]'
if old not in s:
    sys.exit("Ya estaba aplicado o no es la v0.92")
shutil.copy(P, P + ".bak92")
s = s.replace(old, 'EMOTES = ["SEÑALAR", "SALUDO INFORMAL", "DE ACUERDO", "EN DESACUERDO", "VAMOS", "ALTO", "APLAUSO", "SALUDO MILITAR"]', 1)
s = re.sub(r'PANEL_VER = "v0\.92[^"]*"', 'PANEL_VER = "v0.92b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.92b  (copia en " + P + ".bak92)")
