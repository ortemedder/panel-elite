#!/usr/bin/env python3
"""Capturas y toques del COMBATE A PIE en 2 cuadros (v2.2b2) y del aviso EDMC.
Uso: python3 capturar_pie_v22.py PANEL.py SALIDA"""
import os, sys, copy, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC
T0 = CC.T0

def datos(P):
    d = CC.datos(P)
    d.update(Flags=(1 << 21), Flags2=1 | (1 << 4) | (1 << 16), body="HIP 21991 A 3", target=None)
    d["live"] = {"suit": {"name": "Dominator", "loadout": "ASALTO"}, "health": 0.85, "oxy": 1.0, "temp": 294.0,
                 "weapon": "Karma AR-50", "legal": "Clean"}
    d["bio"] = {"lat": -8.2214, "lon": 151.0877, "R": 2500000, "hdg": 38, "ship": [-8.2240, 151.0850]}
    d["pack"] = {"cons": [["Granada de fragmentación", 2], ["Disruptor de escudo", 3], ["Proyector de escudo", 1],
                          ["Botiquín", 2], ["Célula de energía", 1]]}
    d["footcz"] = {"n": 7, "zone": "Zona de conflicto alta", "side": "Caballeros de Sion", "enemy": "Frente de Liberación",
                   "suit": "Dominator", "led": {"n": 7, "cr": 63800, "bonds": [7, 63800], "bounties": [0, 0]}}
    d["combat"]["kills"] = [["Soldado", 12400, "B"], ["Técnico", 8900, "B"], ["Capitán", 15000, "B"]]
    d["sess"] = {"kills": 1234, "kfoot": 7}
    return d

def pistas(P, d):
    b = d["bio"]; R = b["R"]
    def ll(x, y):  # metros -> lat/lon
        return (b["lat"] + math.degrees(y / R), b["lon"] + math.degrees(x / (R * math.cos(math.radians(b["lat"])))))
    P.track.update(body=d["body"], pts=[ll(-230 + i * 5.5, 170 - i * 4.0) for i in range(42)], kills=[ll(-70, 40), ll(-20, 10), ll(30, -40)], items=[], zoom=0)

def capturar(panel, salida):
    P = CC.cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    teclas, fallos = [], []
    P.press_seq = lambda ks: teclas.append(list(ks))
    P.press = lambda *a, **k: teclas.append(list(a))
    d = datos(P); pistas(P, d)
    caido = copy.deepcopy(d); caido["combat"]["sd"] = T0 - 20; caido["live"]["health"] = 0.2
    caido["career"]["foot"] = 999999; caido["footcz"]["led"].update(n=999999, cr=2345678901)
    for nom, dd in (("pie", d), ("pie_caido", caido)):
        for tam in ((1280, 800), (1024, 600)):
            S = CC.preparar(P, dd, tam); P.cfg["comb2"] = "2"; P.cfg["hdmi"] = "tablero"
            print(tam, "modo:", P.big_mode(dd, dd["Flags"]))
            P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.BIG["rects"] = []; P.LZ["lleno"] = "tablero"
            P.lz_tablero(S, dd, dd["Flags"], T0)
            pg.image.save(S, os.path.join(salida, f"{nom}_{tam[0]}.png"))
    # toques (1280 y 1024)
    for tam in ((1280, 800), (1024, 600)):
        S = CC.preparar(P, d, tam); s, ox, oy = P.lienzo_escala()
        def toca(X, Y):
            P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.BIG["rects"] = []; P.LZ["lleno"] = "tablero"
            P.lz_tablero(S, d, d["Flags"], T0); P.ui["view"] = 0; P.cfg["hdmi"] = "tablero"
            P.big_tap((ox + X * s) / tam[0], (oy + Y * s) / tam[1])
        z0 = P.track["zoom"]; toca(400, 400); ok1 = P.track["zoom"] != z0
        t0 = len(teclas); toca(860, 640); ok2 = len(teclas) > t0 and "f1" in str(teclas[-1]).lower()
        t0 = len(teclas); toca(1220, 640); ok3 = len(teclas) > t0 and "r" in str(teclas[-1]).lower()
        toca(640, 750); ok4 = P.ui["view"] == 61
        r = [("ZOOM", ok1), ("BOTIQUÍN", ok2), ("RECARGAR", ok3), ("REGISTRO", ok4)]
        print(tam, r, teclas[-2:]); fallos += [f"{tam[0]} {n}" for n, o in r if not o]
    # aviso EDMC
    P.cfg["hdmi"] = "tablero"
    for txt, n in (("ok|C:\\EDMC\\EDMarketConnector.exe", "edmc_ok"), ("no|", "edmc_no")):
        S = CC.preparar(P, d, (1280, 800)); P.handle_note("edmc", txt); P.xa["a"]["until"] = T0 + 5
        S.fill((0, 0, 0)); P.lienzo_dibuja(S, P.lz_xa, T0); pg.image.save(S, os.path.join(salida, f"{n}.png"))
    print("TOQUES OK" if not fallos else f"FALLOS: {fallos}")

if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
