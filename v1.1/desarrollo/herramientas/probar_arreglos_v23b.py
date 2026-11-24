#!/usr/bin/env python3
"""Arreglos v2.3b: COMBATE en anillos y MEGA NAVE solo a pie.  Uso: python3 probar_arreglos_v23b.py PANEL.py"""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC
T0 = CC.T0

def probar(panel):
    P = CC.cargar.cargar(panel)
    d = CC.datos(P); d.update(body="LHS 346 1 A Ring", Flags=(1 << 6) | (1 << 24) | (1 << 3), Flags2=0, mining={}, station={})
    P.fight["t"] = 0; P.MINE["t"] = 0; P.MINE["sig"] = None
    P.state["data"] = d
    r = [("ANILLO ARMAS FUERA = COMBATE", P._big_mode_base(d, d["Flags"]) == "COMBATE")]
    m = copy.deepcopy(d); P.mining_active(m, P.time.time()); m["mining"] = {"prospectors": 1}
    r.append(("MINANDO = APROXIMACIÓN", P._big_mode_base(m, m["Flags"]) == "APROXIMACIÓN"))
    s = copy.deepcopy(d); s["Flags"] = (1 << 24); P.MINE["t"] = 0
    r.append(("ARMAS DENTRO = APROXIMACIÓN", P._big_mode_base(s, s["Flags"]) == "APROXIMACIÓN"))
    o = copy.deepcopy(d); o["ops"] = {"on": True}; P.MEGA["t0"] = None; P.state["data"] = o
    r.append(("OPS EN NAVE: SIN MEGA", P.mega_left(o, T0) is None and P.mega_rect(1280, 800).w == 0))
    f = copy.deepcopy(o); f["Flags2"] = 1; P.state["data"] = f
    r.append(("OPS A PIE: MEGA 15:00", P.mega_left(f, T0) is False and P.mega_rect(1280, 800).w > 0))
    P.mega_tap(T0); P.state["data"] = o
    r.append(("ARRANCADO: SIGUE EN NAVE", (P.mega_left(o, T0 + 60) or 0) > 0))
    print(r)
    print("TODO OK" if all(x for _, x in r) else "FALLOS " + str([n for n, x in r if not x]))

if __name__ == "__main__":
    probar(os.path.abspath(sys.argv[1]))
