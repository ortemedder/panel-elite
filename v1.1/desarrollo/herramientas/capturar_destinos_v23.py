#!/usr/bin/env python3
"""Capturas y toques de DESTINOS EN EL PLANETA (v2.3b2).  Uso: python3 capturar_destinos_v23.py PANEL.py SALIDA
Ojo: trabaja sobre una copia del panel en /tmp para no tocar sitios_planeta.json ni las notas."""
import os, sys, copy, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC
import capturar_planeta_v23 as CPL
T0 = CC.T0

def capturar(panel, salida):
    tmp = tempfile.mkdtemp()
    src = os.path.dirname(panel)
    shutil.copytree(os.path.join(src, "partes"), os.path.join(tmp, "partes"), ignore=shutil.ignore_patterns("__cache__"))
    shutil.copy(panel, tmp)
    P = CC.cargar.cargar(os.path.join(tmp, "panel.py")); pg = P.pygame; CPL.PP[0] = P
    os.makedirs(salida, exist_ok=True)
    P.trip["list"] = []
    P.cfg["mina2"] = "2"
    res = []
    def pintar_tab(dd, nom):
        S = CC.preparar(P, dd, (1280, 800)); P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.LZ["lleno"] = "tablero"; P.cfg["hdmi"] = "tablero"
        P.fight["t"] = 0; P.lz_tablero(S, dd, dd["Flags"], T0 + 3)
        pg.image.save(S, os.path.join(salida, nom))
    def pintar_menu(dd, v, nom):
        for tam in ((1280, 800), (1024, 600)):
            P.BIG["w"], P.BIG["h"] = tam; S = pg.Surface(tam)
            P.state["data"] = dd; P.state["rx"] = T0
            P.ui.update(view=v, alert=None, idle_on=False); P.xa["a"] = None
            ok = P.lienzo_dibuja(S, P.lz_panel_dibuja, v, dd, dd.get("Flags", 0), T0, True)
            pg.image.save(S, os.path.join(salida, f"{nom}_{tam[0]}.png"))
            res.append((f"dibuja {nom} {tam[0]}", ok))
    base = CPL.datos(P); base["system"] = "HIP 4120"
    # 1) aprende el sitio cuando el juego da sus coordenadas
    P.np_update(base, T0)
    res.append(("APRENDE", "hip 4120|puerto hale dock" in P.SITIOS))
    # 2) otro día: el juego fija el puerto sin coordenadas -> sale igual (CONOCIDO)
    sin = copy.deepcopy(base); sin["dest"] = {"name": "Puerto Hale Dock"}
    dst = P.np_destino(sin)
    res.append(("DESTINO RÁPIDO", bool(dst) and dst.get("src") == "memoria"))
    res.append(("SALE LA ESFERA", P.nav_activa(sin, sin["Flags"], T0, P.big_mode(sin, sin["Flags"]))))
    pintar_tab(sin, "destino_conocido_1280.png")
    # 3) pestaña PLANETA y teclado
    sup = copy.deepcopy(base); sup["Flags"] = (1 << 21) | (1 << 24); CPL.mueve(sup, 3000, 20); sup["dest"] = {}
    P.state["data"] = sup
    pintar_menu(sup, 182, "pestana_planeta")
    P.ui["view"] = 182; P.on_tap(*P.np_fila(0).center)
    res.append(("TOCAR SITIO = IR", (P.NAVP["manual"] or {}).get("name") == "Puerto Hale Dock"))
    P.on_tap(*P.NPB["quitar"].center); res.append(("QUITAR", P.NAVP["manual"] is None))
    P.on_tap(*P.NPB["mano"].center); res.append(("A MANO abre teclado", P.ui["view"] == 183))
    for k in "-12,5":
        f, c = next((f, c) for f, fila in enumerate(P.NP_KEYS) for c, t in enumerate(fila) if t == k)
        P.on_tap(*P.np_tecla_r(f, c).center)
    P.on_tap(*P.NP_CAMPO["lon"].center)
    for k in "63,25":
        f, c = next((f, c) for f, fila in enumerate(P.NP_KEYS) for c, t in enumerate(fila) if t == k)
        P.on_tap(*P.np_tecla_r(f, c).center)
    pintar_menu(sup, 183, "teclado")
    P.ui["view"] = 183; P.on_tap(*P.NP_OK.center)
    m = P.NAVP["manual"] or {}
    res.append(("TECLADO -> DESTINO", abs(m.get("lat", 0) + 12.5) < 1e-9 and abs(m.get("lon", 0) - 63.25) < 1e-9 and m.get("body") == "HIP 4120 3 A"))
    res.append(("GUARDADO EN NOTAS", P.trip["list"] and P.trip["list"][0].get("tag") == "A MANO"))
    # teclado: error
    P.NP_TECLA.update(lat="95", lon="1", campo="lat", err=""); P.ui["view"] = 183; P.on_tap(*P.NP_OK.center)
    res.append(("LAT MALA", P.NP_TECLA["err"] != "" and P.ui["view"] == 183))
    # 4) notas: IR AQUÍ
    P.np_quitar()
    P.trip["sel"] = 0; P.ui["view"] = 129; P.on_tap(*P.NP_IR.center)
    res.append(("NOTA IR AQUÍ", (P.NAVP["manual"] or {}).get("src") == "fav"))
    pintar_menu(sup, 129, "nota_ir")
    # 5) punto automático: aterrizar y SRV
    a = copy.deepcopy(sup); a["Flags"] = (1 << 21) | (1 << 24)
    P.np_update(a, T0); a["Flags"] |= 2; P.np_update(a, T0 + 1)
    s2 = copy.deepcopy(a); s2["dest"] = dict(base["dest"]); CPL.mueve(s2, 2000, 0); s2["dest"] = {}; s2["Flags"] = (1 << 21) | (1 << 26); P.np_update(s2, T0 + 2)
    nombres = [n for n, _, _ in P.np_puntos(s2)]
    res.append(("PUNTOS ATERRIZAJE/SRV", "ATERRIZAJE" in nombres and "SRV" in nombres))
    pintar_tab(s2, "puntos_auto_1280.png")
    print(res)
    print("TODO OK" if all(o for _, o in res) else "FALLOS " + str([n for n, o in res if not o]))
    shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
