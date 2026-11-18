#!/usr/bin/env python3
# Sender v1.0 beta 16 (desde la beta 15), para el panel v1.1.17:
# - manda la música del juego («mtrack»): con el aterrizaje automático («DockingComputer») el panel ya no avisa
#   CERCA DEL SUELO
# Uso:  python patch_sender_v100b16.py elite_sender.py   (deja una copia elite_sender.py.bak100b15)
import shutil, sys
P = sys.argv[1] if len(sys.argv) > 1 else "elite_sender.py"
s = open(P, encoding="utf-8").read()
if 'SENDER_VER = "v1.0b16"' in s:
    sys.exit("Ya estaba aplicado")
if 'SENDER_VER = "v1.0b15"' not in s:
    sys.exit("Este parche es para el sender v1.0b15")
shutil.copy(P, P + ".bak100b15")

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('SENDER_VER = "v1.0b15"', 'SENDER_VER = "v1.0b16"')
rep('''"rutaext": rutaext_pkt(), "scb": SCB,''', '''"rutaext": rutaext_pkt(), "scb": SCB, "mtrack": music["track"],''')
open(P, "w", encoding="utf-8").write(s)
print("Sender actualizado a v1.0b16")
