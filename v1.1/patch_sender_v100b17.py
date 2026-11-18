#!/usr/bin/env python3
# Sender v1.0 beta 17 (desde la beta 16), para el panel v1.1.18:
# - objetivo fijado: facción y poder («faction», «power»)
# - MASACRE: cuenta las bajas de cada misión (Bounty de la facción objetivo; una por facción que da la misión,
#   como en el juego) y avisa al panel al completar cada una («masdone»). Paquete «masacre».
# - EVACUACIONES: marca los pasajeros de evacuación/rescate («evac») y lleva el resumen del día (paquete «evac»:
#   misiones, pasajeros, créditos y tiempo total)
# Uso:  python patch_sender_v100b17.py elite_sender.py   (deja una copia elite_sender.py.bak100b16)
import shutil, sys
P = sys.argv[1] if len(sys.argv) > 1 else "elite_sender.py"
s = open(P, encoding="utf-8").read()
if 'SENDER_VER = "v1.0b17"' in s:
    sys.exit("Ya estaba aplicado")
if 'SENDER_VER = "v1.0b16"' not in s:
    sys.exit("Este parche es para el sender v1.0b16")
shutil.copy(P, P + ".bak100b16")

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('SENDER_VER = "v1.0b16"', 'SENDER_VER = "v1.0b17"')
rep('''"subsys": e.get("Subsystem_Localised"), "subhealth": e.get("SubsystemHealth"), "t": time.time()}''',
    '''"subsys": e.get("Subsystem_Localised"), "subhealth": e.get("SubsystemHealth"), "t": time.time(),
                      "faction": e.get("Faction_Localised") or e.get("Faction"), "power": e.get("Power_Localised") or e.get("Power")}''')
rep('''"rutaext": rutaext_pkt(), "scb": SCB, "mtrack": music["track"],''',
    '''"rutaext": rutaext_pkt(), "scb": SCB, "mtrack": music["track"], "masacre": mass_pkt(), "evac": EVS,''')
rep('''_v096_load()
print("Sender", SENDER_VER)''', '''# ---- v1.0b17: misiones de masacre y evacuaciones ----
MASS = {}                                                   # MissionID -> misión de masacre
EVAC = {}                                                   # MissionID -> (pasajeros, hora de aceptarla)
EVS = {"day": None, "m": 0, "n": 0, "cr": 0, "s": 0}        # evacuaciones entregadas hoy

def _es_evac(e):
    n = (e.get("Name") or "").lower()
    return "evacuat" in n or "rescue" in n or (e.get("PassengerType") or "").lower() == "refugee"

def _mass_left():
    return sum(1 for m in MASS.values() if m["k"] < m["n"])

def _mass_done(m):
    if LIVE[0]:
        note("masdone", f"{m['giver']}|{m['target']}|{m['k']}|{m['n']}|{_mass_left()}")

def mass_event(e):
    ev = e.get("event")
    mid = e.get("MissionID")
    if ev == "MissionAccepted":
        if "massacre" in (e.get("Name") or "").lower() and e.get("KillCount"):
            MASS[mid] = {"giver": e.get("Faction") or "?", "target": e.get("TargetFaction") or "?",
                         "n": int(e.get("KillCount") or 0), "k": 0, "exp": iso2epoch(e.get("Expiry")),
                         "cr": e.get("Reward", 0), "t": iso2epoch(e.get("timestamp"))}
        if e.get("PassengerCount") and _es_evac(e):
            EVAC[mid] = (e.get("PassengerCount", 0), iso2epoch(e.get("timestamp")))
            if mid in pax:
                pax[mid]["evac"] = True
    elif ev == "Bounty":
        vic = e.get("VictimFaction") or ""
        usadas = set()
        for m in sorted(MASS.values(), key=lambda m: m["t"] or 0):
            if m["target"] == vic and m["k"] < m["n"] and m["giver"] not in usadas:
                usadas.add(m["giver"])
                m["k"] += 1
                if m["k"] >= m["n"]:
                    _mass_done(m)
    elif ev == "MissionRedirected" and mid in MASS:
        m = MASS[mid]
        if m["k"] < m["n"]:
            m["k"] = m["n"]
            _mass_done(m)
    elif ev in ("MissionCompleted", "MissionAbandoned", "MissionFailed"):
        MASS.pop(mid, None)
        p = EVAC.pop(mid, None)
        if p and ev == "MissionCompleted":
            day = (e.get("timestamp") or "")[:10]
            if EVS["day"] != day:
                EVS.update(day=day, m=0, n=0, cr=0, s=0)
            EVS["m"] += 1; EVS["n"] += p[0]; EVS["cr"] += e.get("Reward", 0)
            EVS["s"] += max(0, (iso2epoch(e.get("timestamp")) or 0) - (p[1] or 0))
    elif ev == "Missions":
        act = {m.get("MissionID") for m in e.get("Active") or []}
        for k in [k for k in MASS if k not in act]:
            MASS.pop(k, None)
        for k in [k for k in EVAC if k not in act]:
            EVAC.pop(k, None)

def mass_pkt():
    now = time.time()
    L = sorted((m for m in MASS.values() if not m["exp"] or m["exp"] > now), key=lambda m: m["t"] or 0)
    return [[m["giver"][:30], m["target"][:30], m["k"], m["n"], m["exp"], m["cr"]] for m in L[:12]]

_handle_b16 = handle

def handle(e):
    _handle_b16(e)
    try:
        mass_event(e)
    except Exception as ex:
        print("masacre/evacuación:", ex, flush=True)

_v096_load()
print("Sender", SENDER_VER)''')
open(P, "w", encoding="utf-8").write(s)
print("Sender actualizado a v1.0b17")
