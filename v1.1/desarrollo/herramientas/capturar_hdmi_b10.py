#!/usr/bin/env python3
"""Capturas de la HDMI (MENÚ a 1280x800 / 1024x600 y cuadros del tablero) de las pantallas de la b10.
Uso: python3 hdmi.py PANEL.py SALIDA"""
import os, sys, copy, hashlib, json
import cargar
C = cargar.C
T0 = C.T0

def datos_b10(P):
    d = C.datos(P)
    d["cargo"] = [["Acero", 300], ["Polímeros", 120], ["Oro", 64], ["Agua", 22], ["Aluminio", 180], ["Titanio", 90], ["Cobre", 8]]
    d["cargocap"] = 784
    d["missions"] = [["Entregar 300 t de acero", "Ibanez Hub · Pirawoth", T0 + 7200],
                     ["Masacre: 24 piratas", "Pirawoth", T0 + 1500],
                     ["Transporte de datos a Wolf 359", "Lomas Orbital", T0 + 86400 * 3]]
    d["pax"] = {"list": [{"n": 6, "nom": "6 turistas buscan viaje", "tipo": "Tourist", "cr": 1250000, "exp": T0 + 5400,
                          "st": "Lomas Orbital", "sys": "Wolf 359", "vip": True},
                         {"n": 2, "nom": "", "tipo": "Criminal", "cr": 4800000, "exp": T0 + 900, "st": "Ibanez Hub",
                          "sys": "Pirawoth", "wanted": True},
                         {"n": 4, "nom": "", "tipo": "Scientist", "cr": 860000, "exp": T0 + 40000, "st": "Hale Port", "sys": "Sol"}]}
    d["naves"] = {"cur": {"ship": "Python", "type": "python", "name": "SION CARGO", "ident": "CS-01", "jump": 24.6, "fuel": 32,
                          "cargo": 784, "mass": 512.4, "value": 210500000, "id": 7, "fbay": True,
                          "mods": [{"s": "6A", "n": "Generador de escudos", "h": 72, "e": "Reforzado G5"},
                                   {"s": "5A", "n": "Impulsores", "h": 100, "e": "Sucio G5"},
                                   {"s": "5A", "n": "Motor de salto", "h": 96, "e": "Mayor alcance G5"},
                                   {"s": "4E", "n": "Cabina de pasajeros", "h": 100},
                                   {"s": "3B", "n": "Cabina de pasajeros", "h": 100},
                                   {"s": "6E", "n": "Compartimento de carga", "h": 100},
                                   {"s": "6E", "n": "Compartimento de carga", "h": 100},
                                   {"s": "5A", "n": "Planta de energía", "h": 88, "e": "Blindada"},
                                   {"s": "4A", "n": "Distribuidor", "h": 100},
                                   {"s": "3A", "n": "Sensores", "h": 100},
                                   {"s": "5A", "n": "Hangar de cazas", "h": 100}]},
                  "fleet": [{"ship": "Python", "type": "python", "name": "SION CARGO", "here": True, "jump": 24, "cargo": 784, "weapons": 0, "id": 7},
                            {"ship": "Krait Mk II", "type": "krait_mkii", "name": "LANZA", "sys": "Wolf 359", "jump": 31, "cargo": 32,
                             "weapons": 5, "xtime": 5400, "xprice": 820000, "id": 3},
                            {"ship": "Anaconda", "type": "anaconda", "sys": "Sol", "jump": 50, "cargo": 0, "weapons": 0, "transit": True, "id": 2},
                            {"ship": "Adder", "type": "adder", "sys": "Pirawoth", "jump": 18, "cargo": 12, "weapons": 2, "id": 9}],
                  "fleet_t": T0 - 3600, "xfer": [{"ship": "Anaconda", "to": "Pirawoth", "arrive": T0 + 4000}],
                  "veh": {"fighter": "LISTO"}}
    d["ops"] = {"crew": {"name": "Ana Torres"}}
    d["mats"] = {"n": 14, "full": 2, "list": [["Hierro", 300, 300], ["Níquel", 280, 300], ["Carbono", 120, 300], ["Vanadio", 250, 250],
                                             ["Cromo", 40, 250], ["Zinc", 200, 250], ["Germanio", 10, 200], ["Selenio", 190, 200],
                                             ["Escudos modificados", 50, 100], ["Datos de emisión", 12, 150], ["Polonio", 3, 100],
                                             ["Telurio", 90, 100], ["Itrio", 5, 100], ["Rutenio", 0, 100]]}
    d["carrier"] = {"name": "Caballeros de Sion", "callsign": "K8Z-41X", "system": "Pirawoth", "fuel": 620, "balance": 4250000000,
                    "dest": "Wolf 359", "depart": T0 + 754}
    d["sqcarrier"] = {"system": "Lomas"}
    return d

PANTALLAS = [4, 210, 217, 125, 126, 135, 170, 171]
CELDAS = [4, 210, 217]

def capturar(panel, salida):
    P = cargar.cargar(panel)
    pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    base = datos_b10(P)
    hu = {}
    casos = []
    for v in PANTALLAS:
        casos.append((v, "", {}))
    casos += [(4, "_mis", {"tab4": 1}), (4, "_pax", {"tab4": 2}), (4, "_vacia", {"tab4": 0, "_vacia": True}),
              (135, "_aqui", {"colf": "aqui"}), (135, "_sis", {"colf": "sis"}), (126, "_sin", {"_sincar": True}),
              (170, "_p2", {"shippage": 1})]
    for v, suf, extra in casos:
        d = copy.deepcopy(base)
        if extra.get("_vacia"):
            d["cargo"] = []; d["missions"] = []; d["pax"] = {"list": []}
        if extra.get("_sincar"):
            d["carrier"] = {}
        for k, x in extra.items():
            if not k.startswith("_"):
                P.ui[k] = x
        for tam in ((1280, 800), (1024, 600)):
            P.BIG["w"], P.BIG["h"] = tam
            S = pg.Surface(tam)
            P.state["data"] = d; P.state["rx"] = T0
            P.ui.update(view=v, alert=None, idle_on=False, bye=False); P.xa["a"] = None; P.ui["shipcard"] = 0
            ok = P.lienzo_dibuja(S, P.lz_panel_dibuja, v, d, d.get("Flags", 0), T0, True) if v in P.LZ_PANEL else False
            if not ok:
                S.fill((0, 0, 0)); pg.draw.line(S, (255, 0, 0), (0, 0), tam, 5)
            n = f"p{v}{suf}_{tam[0]}.png"
            pg.image.save(S, os.path.join(salida, n))
            hu[n] = (ok, len(P.LZ["phits"]))
        for k in ("tab4", "colf", "shippage"):
            P.ui[k] = {"tab4": 0, "colf": "todo", "shippage": 0}[k]
    for v in CELDAS:
        d = copy.deepcopy(base)
        P.state["data"] = d
        for tam in ((640, 316), (480, 237)):
            S = pg.Surface(tam)
            fn = P.LZ_CELDA.get(v)
            ok = bool(fn) and P.lz_celda_dibuja(S, fn, v, d, d.get("Flags", 0), T0, pg.Rect(0, 0, *tam), "fit")
            n = f"c{v}_{tam[0]}.png"
            pg.image.save(S, os.path.join(salida, n))
            hu[n] = (ok,)
    print(json.dumps(hu, indent=0))

if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
