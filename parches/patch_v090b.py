#!/usr/bin/env python3
# Parche v0.90b: las fotos de fondo de los portanaves no se cargaban (convert() sin modo de video).
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
old = "BG_FILES[k])).convert()"
if old not in s:
    sys.exit("Ya estaba aplicado o no es la v0.90")
shutil.copy(P, P + ".bak90")
s = s.replace(old, "BG_FILES[k]))", 1)
s = re.sub(r'PANEL_VER = "v0\.90[^"]*"', 'PANEL_VER = "v0.90b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.90b  (copia en " + P + ".bak90)")
