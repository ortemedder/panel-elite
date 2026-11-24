#!/usr/bin/env python3
"""Capturas de MINERÍA en 2 cuadros (v2.2b3): asteroides y planetaria (Rhino), con su historial y el ajuste.
Uso: python3 capturar_mineria_v22.py PANEL.py SALIDA"""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC
import capturar_pie_v22 as CP
T0 = CC.T0

def ast(P):
    d = CC.datos(P)
    d.update(Flags=(1 << 21) | (1 << 6), Flags2=0, body="HIP 21991 A 2 A Ring", target=None)
    d["mining"] = {"last": None, "refined": {}, "limpets": 38, "prospectors": 0, "collectors": 0, "t0": None, "t1": None}
    d["cargo"] = [["Platino", 142], ["Paladio", 21], ["Drones", 38]]; d["cargocap"] = 256
    d["market"] = {"sell": [["Platino", 0, 210000]], "best": [["Paladio", 52000]]}
    return d

def planeta(P):
    d = CP.datos(P)
    d.update(Flags=(1 << 21) | (1 << 26) | (1 << 3) | (1 << 13), Flags2=0, srvtype="Rhino", srvcargo=6,
             srvinv=[["Platino", 4], ["Oro", 2]], combat={"kills": [], "sd": None})
    d["Fuel"] = {"FuelMain": 20, "FuelReservoir": 0.34}
    d["srvmats"] = [["Hierro", 57, False], ["Níquel", 41, True], ["Polonio", 3, False]]
    d["mats"] = {"list": [["Hierro", 244, 300], ["Níquel", 300, 300], ["Polonio", 88, 150]], "n": 3, "full": 1}
    return d

def pintar(P, S, d, now):
    P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.BIG["rects"] = []; P.LZ["lleno"] = "tablero"; P.cfg["hdmi"] = "tablero"
    P.fight["t"] = 0; d["station"] = {}
    P.lz_tablero(S, d, d["Flags"], now)

def capturar(panel, salida):
    P = CC.cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    P.cfg["mina2"] = "2"
    d = ast(P)
    S = CC.preparar(P, d, (1280, 800))
    P.fight["t"] = 0
    pintar(P, S, d, T0)                                  # sin minar todavía: tablero de siempre
    print("sin minar:", P.big_mode(d, d["Flags"]), P.mina_asteroides(d, d["Flags"], T0, P.big_mode(d, d["Flags"])))
    seq = [({"Content_Localised": "Contenido de material: Bajo", "remaining": 100.0, "mats": [["Paladio", 9.0]]}, {}),
           ({"Content_Localised": "Contenido de material: Medio", "remaining": 100.0, "mats": [["Platino", 21.0], ["Oro", 5.0]]}, {"Platino": 3}),
           ({"Content_Localised": "Contenido de material: Alto", "remaining": 100.0, "motherlode": "Platino",
             "mats": [["Platino", 38.4], ["Paladio", 12.1], ["Oro", 6.7], ["Osmio", 3.2]]}, {"Platino": 9, "Paladio": 2})]
    t = T0
    for i, (last, ref) in enumerate(seq):
        t += 90
        d["mining"]["last"] = {"content": last["Content_Localised"], "motherlode": last.get("motherlode"),
                               "remaining": last["remaining"], "mats": last["mats"]}
        d["mining"]["refined"] = dict(ref); d["mining"]["prospectors"] = i + 1; d["mining"]["collectors"] = 2 * i
        d["mining"]["t0"] = T0; d["mining"]["t1"] = t
        P.time.time = (lambda tt: (lambda: tt))(t)
        pintar(P, S, d, t)
    print("minando:", P.mina_asteroides(d, d["Flags"], t, P.big_mode(d, d["Flags"])), "historial", len(P.MH["ast"]), len(P.MH["log"]))
    for tam in ((1280, 800), (1024, 600)):
        S = CC.preparar(P, d, tam); pintar(P, S, d, t + 12)
        pg.image.save(S, os.path.join(salida, f"asteroides_{tam[0]}.png"))
    # planetaria
    dp = planeta(P); CP.pistas(P, dp)
    P.MH["sm"] = None
    for tam in ((1280, 800), (1024, 600)):
        S = CC.preparar(P, dp, tam); pintar(P, S, dp, t + 20)
        pg.image.save(S, os.path.join(salida, f"planeta_{tam[0]}.png"))
    sc = copy.deepcopy(dp); sc["srvtype"] = "Scarab"
    S = CC.preparar(P, sc, (1280, 800)); P.MH["smt"] = 0; pintar(P, S, sc, t + 20)
    print("modo SRV:", P.big_mode(sc, sc["Flags"]), sc["Flags"] & (1 << 26), P.MH["smt"])
    print("scarab sin recoger -> minería:", P.mina_planeta(sc, sc["Flags"], t + 20, P.big_mode(sc, sc["Flags"])))
    sc["srvmats"] = [["Hierro", 60, False], ["Níquel", 41, True], ["Polonio", 3, False]]
    pintar(P, S, sc, t + 30)
    print("scarab al recoger -> minería:", P.mina_planeta(sc, sc["Flags"], t + 30, P.big_mode(sc, sc["Flags"])), P.MH["log"][0][1:3])
    # toque del ajuste
    r = P._pant_r(7); P.ui.update(view=160); m0 = P.cfg.get("mina2"); P.on_tap(r.centerx, r.centery)
    print("ajuste MINERÍA / BIO:", m0, "->", P.cfg.get("mina2"))
    S = CC.preparar(P, d, (1280, 800)); P.ui.update(view=160); P.cfg["hdmi"] = "panel"
    P.lienzo_dibuja(S, P.lz_panel_dibuja, 160, d, d["Flags"], T0, True); pg.image.save(S, os.path.join(salida, "p160.png"))

if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
