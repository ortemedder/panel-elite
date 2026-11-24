#!/usr/bin/env python3
"""COMBATE + CAZA (v2.3d): ficha del objetivo, NÚCLEO y REGISTRO con derribos con hora.  Uso: PANEL.py SALIDA"""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC
T0 = CC.T0

def capturar(panel, salida):
    P = CC.cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    d = CC.datos(P)
    d["fighter"] = {"state": "out", "pilot": "Tripulante"}
    d["target"].update(ship="Kestrel Mk II", pilot="Harlann Rayne", shield=22.0, hull=54.0)
    d["combat"]["kills"] = [k + [int(T0) - 60 * i] for i, k in enumerate(d["combat"]["kills"])]
    errs = []
    P.log_exc = lambda w, e: errs.append(f"{w}: {e}")
    for tam in ((1280, 800), (1024, 600)):
        S = CC.preparar(P, d, tam); P.cfg["hdmi"] = "tablero"
        P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.BIG["rects"] = []; P.LZ["lleno"] = "tablero"
        P.lz_tablero(S, d, d["Flags"], T0)
        pg.image.save(S, os.path.join(salida, f"caza_tablero_{tam[0]}.png"))
        P.BIG["w"], P.BIG["h"] = tam; S2 = pg.Surface(tam)
        P.ui.update(view=191); P.lienzo_dibuja(S2, P.lz_panel_dibuja, 191, d, d["Flags"], T0, True)
        pg.image.save(S2, os.path.join(salida, f"caza_menu_{tam[0]}.png"))
    # v2.3e: otro subsistema (motores)
    o = copy.deepcopy(d); o["target"].update(subsys="Motores", subhealth=80.0, subraw="$int_engine_size5_class5_name;")
    S = CC.preparar(P, o, (1280, 800)); P.cfg["hdmi"] = "tablero"
    P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.LZ["lleno"] = "tablero"; P.lz_tablero(S, o, o["Flags"], T0)
    pg.image.save(S, os.path.join(salida, "caza_tablero_motores.png"))
    # toque en NÚCLEO del cuadro
    llam = []; P.nuc_go = lambda *a: llam.append(1); P.LZ_ACC["nucleo"] = lambda acc, X, Y: P.nuc_go()
    S = CC.preparar(P, d, (1280, 800)); P.cfg["hdmi"] = "tablero"
    P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.LZ["lleno"] = "tablero"; P.lz_tablero(S, d, d["Flags"], T0)
    hit = None
    for v, (sub, k, hits) in P.LZ["cel"].items():
        for r, acc in hits:
            if acc[0] == "nucleo":
                hit = (sub.x + r.centerx * k, sub.y + r.centery * k)
    if hit:
        P.ui["view"] = 0; P.big_tap(hit[0] / 1280, hit[1] / 800)
    res = [("SIN ERRORES", not errs), ("BOTÓN NÚCLEO EN EL CUADRO", bool(hit)), ("TOCAR = NÚCLEO", bool(llam))]
    print(errs[:3]); print(res)
    print("TODO OK" if all(o for _, o in res) else "FALLOS " + str([n for n, o in res if not o]))

if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
