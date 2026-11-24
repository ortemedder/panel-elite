#!/usr/bin/env python3
"""GRAVEDAD y PLATAFORMAS en PLANETA (v2.3b3).  Uso: python3 capturar_gravedad_v23.py PANEL.py SALIDA (copia en /tmp)"""
import os, sys, copy, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC
import capturar_planeta_v23 as CPL
T0 = CC.T0

def capturar(panel, salida):
    tmp = tempfile.mkdtemp()
    shutil.copytree(os.path.join(os.path.dirname(panel), "partes"), os.path.join(tmp, "partes"), ignore=shutil.ignore_patterns("__cache__"))
    shutil.copy(panel, tmp)
    P = CC.cargar.cargar(os.path.join(tmp, "panel.py")); pg = P.pygame; CPL.PP[0] = P
    os.makedirs(salida, exist_ok=True)
    res = []
    base = CPL.datos(P); base["system"] = "HIP 4120"
    base["cuerpo"] = {"name": "HIP 4120 3 A", "grav": 2.31 * 9.80665}
    # atraca una vez: aprende sitio y plataformas
    dock = copy.deepcopy(base); dock["Flags"] = 1 | (1 << 21) | (1 << 24)
    dock["bio"].update(lat=8.75, lon=92.30); dock["station"] = {"name": "Puerto Hale Dock"}
    dock["sysinfo"] = {"st_name": "Puerto Hale Dock", "st_pads": [4, 2, 0]}
    P.np_update(dock, T0)
    res.append(("APRENDE PLATAFORMAS", P.SITIOS.get("hip 4120|puerto hale dock", {}).get("pads") == [4, 2, 0]))
    for nave, talla, cabe in (("Anaconda", "L", False), ("Krait Mk II", "M", True)):
        d = copy.deepcopy(base); d["dest"] = {"name": "Puerto Hale Dock"}; d["live"]["ship"]["ship"] = nave
        res.append((f"TALLA {nave}", P.np_talla(d) == talla))
        S = CC.preparar(P, d, (1280, 800)); P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.LZ["lleno"] = "tablero"; P.cfg["hdmi"] = "tablero"
        P.fight["t"] = 0; P.lz_tablero(S, d, d["Flags"], T0 + 3)
        pg.image.save(S, os.path.join(salida, f"gravedad_pads_{talla}.png"))
    res.append(("GRAVEDAD", abs(P.np_gravedad(base) - 2.31) < 1e-6))
    print(res)
    print("TODO OK" if all(o for _, o in res) else "FALLOS " + str([n for n, o in res if not o]))
    shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
