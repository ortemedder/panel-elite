#!/usr/bin/env python3
# Parche v1.0 beta 12c (desde la beta 12b): en la pantalla grande en 4 CUADROS, al estar atracado en un sitio de
# construccion sale el modo COLONIZACION: COLONIZACION, EN VIVO, MERCADO y ESTACION.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if 'BIG_SETS["COLONIZACIÓN"]' in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b12b', s):
    sys.exit("Este parche es para la v1.0 beta 12b")
shutil.copy(P, P + ".bak100b12b")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

CODE = r'''
# ---------- v1.0 beta 12c: modo COLONIZACION en la pantalla grande (4 CUADROS) ----------
BIG_SETS["COLONIZACIÓN"] = [135, 100, 127, 8]
_big_mode_b12c = big_mode

def big_mode(d, flags):
    m = _big_mode_b12c(d, flags)
    if m == "ATRACADO" and ((d or {}).get("colonia") or {}).get("dock"):
        if BIGCOL.get("m") != "COLONIZACIÓN":
            plog("Colonización: pantalla grande en modo COLONIZACIÓN")
        BIGCOL["m"] = "COLONIZACIÓN"
        return "COLONIZACIÓN"
    BIGCOL["m"] = m
    return m

BIGCOL = {"m": None}
'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 12b''', '''# Novedades v1.0 beta 12c
- Pantalla grande en 4 CUADROS: al estar atracado en un sitio de construcción sale el modo COLONIZACIÓN (COLONIZACIÓN, EN VIVO, MERCADO y ESTACIÓN).
# Novedades v1.0 beta 12b''')
rep('    ("1.0b12b", ', '    ("1.0b12c", "Modo COLONIZACIÓN en 4 CUADROS"),\n    ("1.0b12b", ')
s = re.sub(r'PANEL_VER = "v1\.0b12b[^"]*"', 'PANEL_VER = "v1.0b12c · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 12c  (copia en " + P + ".bak100b12b)")
