#!/usr/bin/env python3
"""v2.2b5: FIJAR PANTALLA (candado), avisos DATOS VENDIDOS / VENTA y hora de los derribos.
Uso: python3 probar_fijar_v22.py PANEL.py SALIDA"""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC, capturar_mineria_v22 as CM, capturar_exobio_v22 as CE
T0 = CC.T0

def probar(panel, salida):
    P = CC.cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    P.cfg["mina2"] = P.cfg["comb2"] = "2"
    fallos = []
    def pintar(S, d, now):
        P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.BIG["rects"] = []; P.LZ["lleno"] = "tablero"; P.cfg["hdmi"] = "tablero"
        P.fight["t"] = 0
        P.lz_tablero(S, d, d["Flags"], now)
    # exobiología -> fijar -> me subo al SRV: sigue la exobiología
    d, ll = CE.datos(P); d["bio"].update(step=1, pts=[ll(-560, 600)])
    S = CC.preparar(P, d, (1280, 800)); P.fight["t"] = 0
    P.state["data"] = d; pintar(S, d, T0)
    s, ox, oy = P.lienzo_escala()
    P.big_tap((ox + 213 * s) / 1280, (oy + 47 * s) / 800)
    print("fijada:", P.FIX["on"], P.FIX["kind"], P.FIX["nom"]); fallos += [] if P.FIX["kind"] == "bio" else ["fijar bio"]
    srv = copy.deepcopy(d); srv.update(Flags=(1 << 21) | (1 << 26), Flags2=0, srvtype="Scarab")
    pintar(S, srv, T0 + 5); pg.image.save(S, os.path.join(salida, "fijada_bio_en_srv.png"))
    print("en SRV con exobio fijada -> modo", P.big_mode(srv, srv["Flags"]), "bio", P.bio_activa(srv, srv["Flags"], T0, "x"))
    fallos += [] if P.bio_activa(srv, srv["Flags"], T0, "x") else ["sigue bio"]
    # combate de nave la suelta
    comb = CC.datos(P); comb["station"] = {}
    P.fight["t"] = T0
    m = P.big_mode(comb, comb["Flags"]); print("al entrar en combate:", m, "fijada:", P.FIX["on"])
    fallos += [] if not P.FIX["on"] else ["combate suelta"]
    # fijar el combate y luego guardar armas: sigue el combate
    S = CC.preparar(P, comb, (1280, 800)); P.state["data"] = comb
    P.fix_tocar(); print("fijado:", P.FIX["kind"], P.FIX["mode"])
    paz = copy.deepcopy(comb); paz["Flags"] &= ~(1 << 6); P.fight["t"] = 0
    print("armas guardadas -> modo", P.big_mode(paz, paz["Flags"])); fallos += [] if P.big_mode(paz, paz["Flags"]) == "COMBATE" else ["combate fijo"]
    P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.LZ["lleno"] = "tablero"; P.cfg["hdmi"] = "tablero"; P.lz_tablero(S, paz, paz["Flags"], T0 + 0.5)
    pg.image.save(S, os.path.join(salida, "fijada_combate.png"))
    P.fix_tocar(); print("soltada:", P.FIX["on"])
    P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.lz_tablero(S, paz, paz["Flags"], P.FIX["abre"] + 0.3)
    pg.image.save(S, os.path.join(salida, "abriendo.png"))
    # avisos
    for k, t, n in (("datavend", "12|48650000|8100000|HIP 21991:12000000;Synuefe XR-H:9500000;Col 285 Sector AB:0;" + ";".join(f"S{i}:100000" for i in range(9)), "datos_vendidos"),
                    ("venta", "184|Platino|41300000|41300000|0", "venta_platino"),
                    ("venta", "720|Oro|6912000|-288000|10000", "venta_perdida")):
        S = CC.preparar(P, comb, (1280, 800)); P.handle_note(k, t); P.xa["a"]["until"] = T0 + 9
        S.fill((0, 0, 0)); P.lienzo_dibuja(S, P.lz_xa, T0); pg.image.save(S, os.path.join(salida, n + ".png"))
    # hora en el registro
    comb["combat"]["kills"] = [["Eagle", 38200, "B", T0 - 60], ["Vulture", 96500, "R", T0 - 300], ["Cobra", 0, "P"]]
    P.fight["t"] = T0; S = CC.preparar(P, comb, (1280, 800)); pintar(S, comb, T0); P.fight["t"] = T0
    P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.lz_tablero(S, comb, comb["Flags"], T0); pg.image.save(S, os.path.join(salida, "registro_hora.png"))
    print("OK" if not fallos else f"FALLOS {fallos}")

if __name__ == "__main__":
    probar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
