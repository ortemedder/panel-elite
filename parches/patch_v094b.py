#!/usr/bin/env python3
# Parche v0.94b: el titulo del cuadro 11 dice RESUMEN DEL DIA y el tiempo jugado no sigue sumando con el juego cerrado.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
old = 'MENU.update({12: "AJUSTES", 11: "SESIÓN·GALNET"})'
if old not in s:
    sys.exit("Ya estaba aplicado o no es la v0.94")
shutil.copy(P, P + ".bak94")
s = s.replace(old, 'MENU.update({12: "AJUSTES", 11: "RESUMEN DEL DÍA"})', 1)
s = s.replace("- 11 SESIÓN·GALNET: resumen de la sesión", "- 11 RESUMEN DEL DÍA: todo lo del día", 1)
# tiempo jugado: solo hasta la ultima señal de vida del juego (no hasta ahora)
s = s.replace('(max(0, time.time() - s_["seg"]) if s_.get("seg") else 0)',
              '(max(0, (s_.get("lastts") or s_["seg"]) - s_["seg"]) if s_.get("seg") else 0)', 1)
s = re.sub(r'PANEL_VER = "v0\.94[^"]*"', 'PANEL_VER = "v0.94b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.94b  (copia en " + P + ".bak94)")
