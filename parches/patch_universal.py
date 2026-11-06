#!/usr/bin/env python3
# Parche universal (paso a la v1.0): vale para cualquier usuario, Pi 3 o Pi 4, con o sin pantalla pequena.
#  - Los archivos (notas, estilo, bordes, iconos, galnet, cmdr.jpg) van junto a panel.py, no en /home/ortem.
#  - El tactil solo se invierte en la pantalla pequena (ADS7846); los tactiles USB van tal cual.
#  - Sin teclado USB (/dev/hidg0, p. ej. Pi 3), los botones mandan las teclas al sender del PC por la red.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "panel.py"
s = open(P, encoding="utf-8").read()
if "ELITEPANEL-KEYS" in s:
    sys.exit("Ya estaba aplicado")
shutil.copy(P, P + ".bakuniv")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# 1. rutas junto a panel.py
rep('''import pygame
import numpy as np
''', '''import pygame
import numpy as np
PANEL_DIR = os.path.dirname(os.path.abspath(__file__))
''')
s = re.sub(r'"/home/(?:ortem|elite)/([^"]+)"', r'os.path.join(PANEL_DIR, "\1")', s)

s = re.sub(r'PANEL_LOG = "[^"]*"', 'PANEL_LOG = os.path.join(PANEL_DIR, "panel.log")', s, count=1)
s = s.replace('SETTINGS_FILE = os.path.expanduser("~/panel_ajustes.json")', 'SETTINGS_FILE = os.path.join(PANEL_DIR, "panel_ajustes.json")', 1)

# 2. tactil: solo se invierte la pantalla pequena
rep('''            if INV_Y: y = 1 - y''', '''            if INV_Y and "ADS7846" in dev.name: y = 1 - y''')
if '''            if "ADS7846" in d.name or "touch" in d.name.lower():''' in s:
    rep('''            if "ADS7846" in d.name or "touch" in d.name.lower():''', '''            if is_touch2(d):''')

# 3. teclas por la red cuando no hay teclado USB
rep('''def press_seq(keys):
    if not all(key_ok(k) for k in keys):
        set_alert("SIN TECLA EN EL JUEGO", "mira AJUSTES > OPCIONES > TECLAS", ORANGE, 3)
        return''', '''def press_seq(keys):
    if not all(key_ok(k) for k in keys):
        set_alert("SIN TECLA EN EL JUEGO", "mira AJUSTES > OPCIONES > TECLAS", ORANGE, 3)
        return
    if not os.path.exists("/dev/hidg0"):
        pc = state.get("pc")
        if not pc:
            set_alert("NO SÉ LA IP DEL PC", "el sender no está enviando", RED, 3)
            return
        try:
            so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            so.sendto(("ELITEPANEL-KEYS|" + ",".join(keys)).encode(), (pc, 5006))
            so.close()
        except OSError as e:
            print("Error teclas por red:", e)
        return''')
s = s.replace("# Panel tactil Elite Dangerous - Raspberry Pi 4 + pantalla 3.5\" 480x320",
              "# Panel tactil Elite Dangerous - Raspberry Pi 3 / 4, pantalla pequena y/o HDMI", 1)
open(P, "w", encoding="utf-8").write(s)
print("OK universal  (copia en " + P + ".bakuniv)")
