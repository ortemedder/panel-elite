#!/usr/bin/env python3
# KORZO: de v0.99g a v0.99i, igual que el panel de Ortem:
#  - Solo pantalla HDMI: el tactil lo lleva touch_loop2 (toque escalado a la HDMI, pulsacion larga PANEL/4 CUADROS).
#  - Cierre de emergencia: IP del PC fija opcional en pc_ip.txt (junto a panel.py).
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "pc_ip.txt" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.99g' not in s or "def pc_now" not in s:
    sys.exit("Este parche es para la v0.99g (con el reloj del PC)")
shutil.copy(P, P + ".bak99g")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

rep('''    dev = next((d for d in devs_ if "ADS7846" in d.name), None) or next((d for d in devs_ if is_touch2(d)), None)''',
    '''    dev = next((d for d in devs_ if "ADS7846" in d.name), None)''')
rep('''        print("No encuentro el tactil"); return''',
    '''        return   # sin pantalla pequena: el tactil HDMI lo lleva touch_loop2''')
rep('''        if not any("ADS7846" in d.name for d in devs_):
            return                                   # sin pantalla pequena lo lleva touch_loop
''', '')
rep('''def kill_send():
    pc = state.get("pc")''', '''def kill_send():
    pc = None
    try:
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pc_ip.txt")
        pc = open(f).read().strip() or None
    except Exception:
        pass
    pc = pc or state.get("pc")''')
rep('''    ("0.99g", "Mega nave: cuenta atrás con la hora del PC"),\n''', '')
rep('''    ("0.99f", "MINERÍA: barra de bodega, toneladas/hora sin tapar y en el cuadro 3 al minar"),\n''',
    '''    ("0.99f", "MINERÍA: barra de bodega, toneladas/hora sin tapar y en el cuadro 3 al minar"),\n'''
    '''    ("0.99g", "Solo pantalla de 10\\": táctil HDMI sin la pequeña de 3.5\\""),\n'''
    '''    ("0.99i", "Mega nave: cuenta atrás con la hora del PC"),\n'''
    '''    ("0.99h", "Cierre de emergencia: IP del PC fija opcional en pc_ip.txt"),\n''')
s = s.replace("# Novedades v0.99g\n", "# Novedades v0.99 (reloj)\n", 1)
s = re.sub(r'PANEL_VER = "v0\.99g[^"]*"', 'PANEL_VER = "v0.99i · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99i  (copia en " + P + ".bak99g)")
