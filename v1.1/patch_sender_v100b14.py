#!/usr/bin/env python3
# Sender v1.0 beta 14b (desde la beta 13), para el panel v1.1.10:
# - PARADA DE EMERGENCIA: salida de supercrucero sin destino elegido en una estrella, o en un planeta
#   cuando el juego vuelve a escribir ApproachBody en el mismo instante (b14b; la b14 usaba «menos de 10 s»)
# - todos los materiales con su nombre interno (para las preguntas de planos del robot)
import shutil, sys
P = sys.argv[1] if len(sys.argv) > 1 else "elite_sender.py"
s = open(P, encoding="utf-8").read()
if "def emerg_event" in s:
    sys.exit("Ya estaba aplicado")
if 'SENDER_VER = "v1.0b13"' not in s:
    sys.exit("Este parche es para el sender v1.0b13")
shutil.copy(P, P + ".bak100b13")

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('''"colbuy": COLBUY,''', '''"colbuy": COLBUY, "matsall": mats,''')
rep('''HEAVY = ("colonia",''', '''HEAVY = ("matsall", "colonia",''')                # solo cuando cambian

CODE = r'''
# ---------- v1.0 beta 14b: parada de emergencia ----------
# Estrella: salida de supercrucero en la estrella sin destino elegido.
# Planeta: salida sin destino ni asentamiento cerca y, en el mismo instante, el juego vuelve a escribir
#          ApproachBody del mismo planeta (asi pasa en las paradas de emergencia; en las bajadas normales no).
EMERG = {"drop": 0.0, "settl": 0.0, "pend": None}

def emerg_event(e):
    ev = e.get("event")
    t = iso2epoch(e.get("timestamp")) or time.time()
    if ev == "SupercruiseDestinationDrop":
        EMERG["drop"] = t
    elif ev == "ApproachSettlement":
        EMERG["settl"] = t
    elif ev == "ApproachBody":
        p = EMERG["pend"]
        EMERG["pend"] = None
        if p and p[1] == e.get("Body") and 0 <= t - p[0] <= 3:
            emerg_aviso("Planet", p[1])
    elif ev == "SupercruiseExit" and not e.get("Taxi") and not e.get("Multicrew"):
        EMERG["pend"] = None
        bt = e.get("BodyType") or ""
        if t - EMERG["drop"] < 15:                       # habias elegido destino: salida normal
            return
        if bt == "Star":
            emerg_aviso(bt, e.get("Body"))
        elif bt == "Planet" and t - EMERG["settl"] > 60:
            EMERG["pend"] = (t, e.get("Body"))           # se confirma si vuelve a llegar ApproachBody
    elif ev not in ("Music", "ShipLocker", "FSSSignalDiscovered", "ReceiveText"):
        EMERG["pend"] = None

def emerg_aviso(bt, body):
    print(time.strftime("%H:%M:%S"), "PARADA DE EMERGENCIA:", body, flush=True)
    if LIVE[0]:
        note("emergstop", f"{bt}|{body or ''}")

_handle_b14 = handle

def handle(e):
    _handle_b14(e)
    try:
        emerg_event(e)
    except Exception as ex:
        print("parada de emergencia:", ex, flush=True)

'''
rep("_v096_load()\nprint(\"Sender\", SENDER_VER)", CODE + "_v096_load()\nprint(\"Sender\", SENDER_VER)")
rep('SENDER_VER = "v1.0b13"', 'SENDER_VER = "v1.0b14b"')
open(P, "w", encoding="utf-8").write(s)
print("OK sender v1.0 beta 14b  (copia en " + P + ".bak100b13)")
