#!/usr/bin/env python3
# Sender v1.0 beta 14 (desde la beta 13), para el panel v1.1.10:
# - PARADA DE EMERGENCIA: salida de supercrucero sin destino elegido en una estrella, o en un planeta
#   a menos de 10 s de entrar en su zona (sin acercarte a un asentamiento ni a una construcción)
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
# ---------- v1.0 beta 14: parada de emergencia ----------
EMERG = {"drop": 0.0, "appr": 0.0, "settl": 0.0}

def emerg_event(e):
    ev = e.get("event")
    t = iso2epoch(e.get("timestamp")) or time.time()
    if ev == "SupercruiseDestinationDrop":
        EMERG["drop"] = t
    elif ev == "ApproachBody":
        EMERG["appr"] = t
    elif ev == "ApproachSettlement":
        EMERG["settl"] = t
    elif ev == "SupercruiseExit" and not e.get("Taxi") and not e.get("Multicrew"):
        bt = e.get("BodyType") or ""
        if t - EMERG["drop"] < 15:                       # habias elegido destino: salida normal
            return
        if bt == "Star" or (bt == "Planet" and t - EMERG["settl"] > 60 and t - EMERG["appr"] < 10):
            print(time.strftime("%H:%M:%S"), "PARADA DE EMERGENCIA:", e.get("Body"), flush=True)
            if LIVE[0]:
                note("emergstop", f"{bt}|{e.get('Body') or ''}")

_handle_b14 = handle

def handle(e):
    _handle_b14(e)
    try:
        emerg_event(e)
    except Exception as ex:
        print("parada de emergencia:", ex, flush=True)

'''
rep("_v096_load()\nprint(\"Sender\", SENDER_VER)", CODE + "_v096_load()\nprint(\"Sender\", SENDER_VER)")
rep('SENDER_VER = "v1.0b13"', 'SENDER_VER = "v1.0b14"')
open(P, "w", encoding="utf-8").write(s)
print("OK sender v1.0 beta 14  (copia en " + P + ".bak100b13)")
