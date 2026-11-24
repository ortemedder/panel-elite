#!/usr/bin/env python3
"""Capturas y toques de EXOBIOLOGÍA en 2 cuadros (v2.2b4).  Uso: python3 capturar_exobio_v22.py PANEL.py SALIDA"""
import os, sys, copy, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC
import capturar_pie_v22 as CP
T0 = CC.T0

def datos(P):
    d = CP.datos(P)
    d["live"].update(suit={"name": "Artemis", "loadout": "BIO"}, weapon="Muestreador genético")
    d.update(Flags=(1 << 21), Flags2=1 | (1 << 4) | (1 << 16), combat={"kills": [], "sd": None}, station={})
    b = d["bio"]; R = b["R"]
    def ll(x, y):
        return [b["lat"] + math.degrees(y / R), b["lon"] + math.degrees(x / (R * math.cos(math.radians(b["lat"]))))]
    b.update(body="HIP 21991 A 3", signals=4, genuses=["Bacterium", "Osseus", "Stratum", "Fungoida"], done=["Bacterium"],
             species="Osseus Discus", genus="Osseus", variant="Esmeralda", step=0, range=800, pts=[],
             unsold=6, unsold_cr=41200000, value=12934600, exact=True, bonus=True, ship=ll(-1150, 200))
    return d, ll

def capturar(panel, salida):
    P = CC.cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    P.cfg["mina2"] = "2"
    d, ll = datos(P)
    CP.pistas(P, d)
    def pintar(S, dd, now):
        P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.BIG["rects"] = []; P.LZ["lleno"] = "tablero"; P.cfg["hdmi"] = "tablero"
        P.fight["t"] = 0
        return P.lz_tablero(S, dd, dd["Flags"], now)
    S = CC.preparar(P, d, (1280, 800)); pintar(S, d, T0)
    d["bio"].update(step=1, pts=[ll(-560, 600)]); pintar(S, d, T0 + 30)
    d["bio"].update(step=2, pts=[ll(-560, 600), ll(620, 520)]); pintar(S, d, T0 + 60)
    print("modo:", P.big_mode(d, d["Flags"]), "bio:", P.bio_activa(d, d["Flags"], T0, P.big_mode(d, d["Flags"])), "log", [e[1] for e in P.BH["log"]])
    for tam in ((1280, 800), (1024, 600)):
        S = CC.preparar(P, d, tam); pintar(S, d, T0 + 60)
        pg.image.save(S, os.path.join(salida, f"exobio_{tam[0]}.png"))
    cerca = copy.deepcopy(d); cerca["bio"]["pts"] = [ll(-560, 600), ll(300, 200)]
    S = CC.preparar(P, cerca, (1280, 800)); pintar(S, cerca, T0 + 70); pg.image.save(S, os.path.join(salida, "exobio_cerca.png"))
    fin = copy.deepcopy(d); fin["bio"].update(step=3, pts=[], done=["Bacterium", "Osseus"])
    S = CC.preparar(P, fin, (1280, 800)); pintar(S, fin, T0 + 90); pg.image.save(S, os.path.join(salida, "exobio_analizado.png"))
    print("tras analizar:", [e[1] for e in P.BH["log"][:2]], P.BH["n"], P.BH["cr"])
    otro = copy.deepcopy(d); otro["live"].update(suit={"name": "Maverick"}, weapon="Karma AR-50"); otro["bio"].update(species=None, step=0)
    print("Maverick sin muestrear -> exobio:", P.bio_activa(otro, otro["Flags"], T0, P.big_mode(otro, otro["Flags"])))
    otro["bio"].update(species="Osseus Discus", step=1)
    print("Maverick muestreando -> exobio:", P.bio_activa(otro, otro["Flags"], T0, P.big_mode(otro, otro["Flags"])))
    # toques
    fallos = []
    for tam in ((1280, 800), (1024, 600)):
        S = CC.preparar(P, d, tam); s, ox, oy = P.lienzo_escala()
        def toca(X, Y):
            pintar(S, d, T0 + 60); P.ui["view"] = 0
            P.big_tap((ox + X * s) / tam[0], (oy + Y * s) / tam[1])
        z0 = P.BH["zoom"]; toca(300, 300); ok1 = P.BH["zoom"] != z0
        nav = []; P._lz_nave_aqui = lambda *a: nav.append(1); P.LZ_ACC["naveaqui"] = P._lz_nave_aqui
        toca(690, 630); ok2 = bool(nav)
        toca(640, 750); ok3 = P.ui["view"] == 61
        print(tam, [("ZOOM", ok1), ("NAVE AQUÍ", ok2), ("REGISTRO", ok3)])
        fallos += [n for n, o in (("ZOOM", ok1), ("NAVE AQUÍ", ok2), ("REGISTRO", ok3)) if not o]
    print("TOQUES OK" if not fallos else f"FALLOS {fallos}")

if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
