#!/usr/bin/env python3
# Parche v1.0 beta 20 (desde la beta 19b): al cargar la partida, cuando termina la ficha de la nave, la pantalla
# grande pasa a 4 CUADROS.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "LGB = {" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b19b', s):
    sys.exit("Este parche es para la v1.0 beta 19b")
shutil.copy(P, P + ".bak100b19b")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

CODE = r'''
# ---------- v1.0 beta 20: tras cargar la partida, 4 CUADROS ----------
LGB = {"t": 0}
_handle_note_b20 = handle_note

def handle_note(kind, text):
    if kind == "loadgame":
        LGB["t"] = time.time()
    _handle_note_b20(kind, text)

_render_b20 = render

def render(surf):
    r_ = _render_b20(surf)
    try:
        now = time.time()
        if LGB["t"] and now - LGB["t"] > 3 and not (ui.get("shipcard") and now < ui["shipcard"]):
            LGB["t"] = 0
            if hdmi_panel():
                cfg["hdmi"] = "tablero"; save_cfg()
                plog("Partida cargada: pantalla grande en 4 CUADROS")
    except Exception as e:
        log_exc("4 cuadros al cargar", e)
    return r_

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 19b''', '''# Novedades v1.0 beta 20
- Al cargar la partida, cuando termina la ficha de la nave, la pantalla grande pasa a 4 CUADROS (con una pulsación larga se vuelve al PANEL).
- Nuevo subir_todo.sh: sube todo el proyecto a GitHub (panel, parches, imágenes, los dos senders y el escucha), nunca las claves ni los datos personales.
# Novedades v1.0 beta 19b''')
rep('    ("1.0b19b", ', '    ("1.0b20", "4 CUADROS al cargar la partida y subir_todo.sh"),\n    ("1.0b19b", ')
s = re.sub(r'PANEL_VER = "v1\.0b19b[^"]*"', 'PANEL_VER = "v1.0b20 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 20  (copia en " + P + ".bak100b19b)")
