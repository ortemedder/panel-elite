#!/usr/bin/env python3
# Sender v1.0 beta 13 (desde la beta 12), para el panel v1.1:
# - bodega tambien con el nombre interno de cada mercancia (COLONIZACION descuenta todos los materiales)
# - misiones de pasajeros (numero, tipo, VIP, buscados, destino, plazo, recompensa) y pasajeros de la sesion
# - aviso al panel de cada venta en el mercado (para avisar si vendes material de tu construccion)
import shutil, sys
P = sys.argv[1] if len(sys.argv) > 1 else "elite_sender.py"
s = open(P, encoding="utf-8").read()
if "def pax_event" in s:
    sys.exit("Ya estaba aplicado")
if 'SENDER_VER = "v1.0b12"' not in s:
    sys.exit("Este parche es para el sender v1.0b12")
shutil.copy(P, P + ".bak100b12")

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# bodega con nombre interno
rep('''        cargo = [(x.get("Name_Localised") or x.get("Name", "?").capitalize(), x.get("Count", 0))
                 for x in c.get("Inventory") or []]''', '''        cargo = [(x.get("Name_Localised") or x.get("Name", "?").capitalize(), x.get("Count", 0))
                 for x in c.get("Inventory") or []]
        cargok.clear()
        for x in c.get("Inventory") or []:
            k_ = (x.get("Name") or "").lower()
            if k_:
                cargok[k_] = cargok.get(k_, 0) + x.get("Count", 0)''')
rep('''"cargo": cargo[:40], "colonia": col_pkt(),''', '''"cargo": cargo[:40], "cargok": cargok, "pax": pax_pkt(), "colonia": col_pkt(),''')

CODE = r'''
# ---------- v1.0 beta 13: bodega por nombre interno, pasajeros y ventas ----------
cargok = {}                                              # nombre interno -> toneladas
pax = {}                                                 # MissionID -> datos de la mision de pasajeros
PAXS = {"day": None, "n": 0, "cr": 0}                    # pasajeros entregados hoy y sus creditos

def pax_event(e):
    ev = e.get("event")
    if ev == "MissionAccepted" and e.get("PassengerCount"):
        pax[e["MissionID"]] = {"n": e.get("PassengerCount", 0), "tipo": e.get("PassengerType") or "",
                               "nom": (e.get("LocalisedName") or "")[:60], "vip": bool(e.get("PassengerVIPs")),
                               "wanted": bool(e.get("PassengerWanted")), "sys": e.get("DestinationSystem") or "",
                               "st": e.get("DestinationStation") or "", "exp": iso2epoch(e.get("Expiry")),
                               "cr": e.get("Reward", 0), "fac": e.get("Faction") or "", "t": iso2epoch(e.get("timestamp"))}
        if LIVE[0]:
            n_ = sum(p["n"] for p in pax.values())
            note("paxin", f"{e.get('PassengerCount', 0)}|{e.get('PassengerType') or ''}|{n_}|{e.get('DestinationStation') or ''}")
    elif ev == "MissionRedirected" and e.get("MissionID") in pax:
        pax[e["MissionID"]].update(sys=e.get("NewDestinationSystem") or pax[e["MissionID"]]["sys"],
                                   st=e.get("NewDestinationStation") or pax[e["MissionID"]]["st"])
    elif ev in ("MissionCompleted", "MissionAbandoned", "MissionFailed"):
        p = pax.pop(e.get("MissionID"), None)
        if p and ev == "MissionCompleted":
            day = (e.get("timestamp") or "")[:10]
            if PAXS["day"] != day:
                PAXS.update(day=day, n=0, cr=0)
            PAXS["n"] += p["n"]; PAXS["cr"] += e.get("Reward", 0)
    elif ev == "Missions":
        act = {m.get("MissionID") for m in e.get("Active") or []}
        for mid in [k for k in pax if k not in act]:
            pax.pop(mid, None)
    elif ev == "MarketSell" and LIVE[0]:
        note("mktsell", f"{(e.get('Type') or '').lower()}|{e.get('Type_Localised') or e.get('Type') or ''}|{e.get('Count', 0)}|{e.get('MarketID')}")

def pax_pkt():
    now = time.time()
    L = sorted(([mid, p] for mid, p in pax.items() if not p["exp"] or p["exp"] > now), key=lambda x: x[1]["exp"] or 9e12)
    return {"list": [dict(p, id=mid) for mid, p in L[:12]], "hoy": PAXS}

_handle_b13 = handle

def handle(e):
    _handle_b13(e)
    try:
        pax_event(e)
    except Exception as ex:
        print("pasajeros:", ex, flush=True)

'''
rep("_v096_load()\nprint(\"Sender\", SENDER_VER)", CODE + "_v096_load()\nprint(\"Sender\", SENDER_VER)")
rep('SENDER_VER = "v1.0b12"', 'SENDER_VER = "v1.0b13"')
open(P, "w", encoding="utf-8").write(s)
print("OK sender v1.0 beta 13  (copia en " + P + ".bak100b12)")
