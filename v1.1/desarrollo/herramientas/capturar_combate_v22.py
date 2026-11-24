#!/usr/bin/env python3
"""Capturas del tablero de COMBATE de nave (v2.2b1) a 1280x800 y 1024x600, con y sin objetivo, y prueba de toques.
Uso: python3 capturar_combate_v22.py PANEL.py SALIDA"""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cargar
C = cargar.C; T0 = C.T0

def datos(P):
    d = C.datos(P)
    d.update(Flags=(1 << 3) | (1 << 6) | (1 << 24), Flags2=0, system="HIP 21991", body="", fuelcap=32,
             Fuel={"FuelMain": 23.4, "FuelReservoir": 0.6}, Pips=[4, 2, 6])
    d["live"] = {"ship": {"ship": "Krait Mk II", "name": "LANZA", "ident": "CS-02", "hull": 0.87}, "legal": "Clean"}
    d["target"] = {"stype": "ferdelance", "ship": "Fer-de-Lance", "scan": 3, "pilot": "Cmdr Varkas Tolen", "cmdr": True,
                   "rank": "Peligroso", "shield": 38.0, "hull": 71.0, "legal": "Wanted", "bounty": 412800,
                   "subsys": "Planta de energía", "subhealth": 64.0, "subraw": "$int_powerplant_size6_class5_name;",
                   "t": T0 - 2, "faction": "Frente de Liberación HIP 21991", "power": "Archon Delaine",
                   "inara": {"squad": "KRAITS DEL VACÍO", "rank": "Peligroso"}}
    d["combat"] = {"kills": [["Eagle", 38200, "B"], ["Vulture", 96500, "B"], ["Cobra Mk III", 120400, "R"],
                             ["Asp Explorer", 210000, "R"]], "sd": None, "bonds": [["Federación", 134700]]}
    d["sess"] = {"kills": 1234, "kfoot": 7, "pending": 612300, "pending_n": 9, "earn": {}}
    d["career"] = {"foot": 104512, "bonds": 98765, "bounties": 123456}
    d["footcz"] = {"n": 0, "led": {"n": 9, "cr": 612300, "bonds": [3, 230000], "bounties": [6, 382300]}}
    return d

def preparar(P, d, tam):
    pg = P.pygame
    P.BIG["w"], P.BIG["h"] = tam
    S = pg.Surface(tam)
    P.BIG["surf"] = S
    if P.BIG.get("cell") is None:
        P.BIG["cell"] = pg.Surface((P.W, P.H))
    P.state["data"] = d; P.state["rx"] = T0
    P.ui.update(view=0, alert=None, idle_on=False, start=0); P.xa["a"] = None
    P.cfg["bigmode"] = "4"
    P.fight["t"] = T0
    return S

def capturar(panel, salida):
    P = cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    base = datos(P)
    casos = {"objetivo": base}
    sin = copy.deepcopy(base); sin["target"] = None; casos["sin_objetivo"] = sin
    caidos = copy.deepcopy(base); caidos["Flags"] &= ~(1 << 3); caidos["combat"]["sd"] = T0 - 75
    caidos["target"]["shield"] = 0.0; caidos["target"]["hull"] = 12.0; caidos["Flags"] |= 1 << 20
    caidos["sess"]["pending"] = 2345678901; caidos["footcz"]["led"].update(n=999999, cr=2345678901)
    caidos["career"].update(bonds=999999, bounties=999999)
    casos["caidos_grandes"] = caidos
    nave_npc = copy.deepcopy(base); nave_npc["target"].update(cmdr=False, pilot="Krissa Vell", inara=None, scan=1,
                                                              legal=None, bounty=None, subsys=None, subhealth=None, subraw="", faction=None, power=None,
                                                              shield=100.0, hull=100.0)
    casos["escaneo_1"] = nave_npc
    for cfgv in ("2", "4"):
        P.cfg["comb2"] = cfgv
        for nom, d in casos.items():
            for tam in ((1280, 800), (1024, 600)):
                S = preparar(P, d, tam)
                P.LZ["cel"] = {}
                S.fill((0, 0, 0)); P.BIG["rects"] = []; P.LZ["lleno"] = "tablero"
                P.lz_tablero(S, d, d["Flags"], T0)
                pg.image.save(S, os.path.join(salida, f"comb{cfgv}_{nom}_{tam[0]}.png"))
    return P

if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
