#!/usr/bin/env python3
"""Prueba de toques del COMBATE en 2 cuadros (v2.2b1): cada botón manda la tecla de siempre o hace su acción."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC
T0 = CC.T0

def probar(panel):
    P = CC.cargar.cargar(panel)
    teclas, nuc = [], []
    P.press_seq = lambda ks: teclas.append(list(ks))
    P.press = lambda *a, **k: teclas.append(list(a))
    P.nuc_go = lambda auto=False: nuc.append(1)
    P.cfg["comb2"] = "2"
    d = CC.datos(P)
    fallos = []
    for tam in ((1280, 800), (1024, 600)):
        S = CC.preparar(P, d, tam)
        def pintar():
            P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.BIG["rects"] = []; P.LZ["lleno"] = "tablero"
            P.lz_tablero(S, d, d["Flags"], T0)
        s, ox, oy = P.lienzo_escala()
        def toca(X, Y):
            pintar()
            P.ui["view"] = 0; P.cfg["hdmi"] = "tablero"
            P.big_tap((ox + X * s) / tam[0], (oy + Y * s) / tam[1])
        casos = []
        # NÚCLEO (abajo a la izquierda del OBJETIVO)
        n0 = len(nuc); toca(150, 640); casos.append(("NÚCLEO", len(nuc) == n0 + 1))
        # SIG. SUBSIST.
        t0 = len(teclas); toca(470, 640); casos.append(("SIG. SUBSIST.", len(teclas) > t0 and teclas[-1] and "a" in str(teclas[-1]).lower()))
        # columna de PIPS de ARMAS
        t0 = len(teclas); toca(1150, 470); casos.append(("PIP ARM", len(teclas) > t0))
        # RESET
        t0 = len(teclas); toca(740, 640); casos.append(("RESET", len(teclas) > t0))
        # REGISTRO -> MENÚ en REGISTRO DE COMBATE
        toca(640, 750); casos.append(("REGISTRO", P.ui["view"] == 61))
        for n, ok in casos:
            if not ok:
                fallos.append(f"{tam[0]}: {n}")
        print(tam, [(n, ok) for n, ok in casos], teclas[-3:])
    print("TOQUES OK" if not fallos else f"FALLOS: {fallos}")

if __name__ == "__main__":
    probar(os.path.abspath(sys.argv[1]))
