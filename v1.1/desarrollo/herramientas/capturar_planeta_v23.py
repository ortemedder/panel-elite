#!/usr/bin/env python3
"""Capturas y toques de NAVEGACIÓN PLANETARIA (v2.3b1).  Uso: python3 capturar_planeta_v23.py PANEL.py SALIDA"""
import os, sys, copy, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capturar_combate_v22 as CC
T0 = CC.T0
R = 2_500_000
PP = [None]

def datos(P):
    d = CC.datos(P)
    d.update(Flags=(1 << 21) | (1 << 24) | (1 << 4), Flags2=0, body="HIP 4120 3 A", target=None,
             combat={"kills": [], "sd": None}, station={})
    d["live"] = {"ship": {"ship": "Krait Mk II", "name": "LANZA", "hull": 1.0}, "alt": 48200, "legal": "Clean"}
    d["bio"] = {"body": "HIP 4120 3 A", "lat": -12.41, "lon": 63.08, "R": R, "hdg": 198, "ship": None, "pts": [], "step": 0}
    d["dest"] = {"name": "Puerto Hale Dock", "lat": 8.75, "lon": 92.30, "sbody": "HIP 4120 3 A"}
    return d

def mueve(d, dist_m, rumbo_off=0.0):
    """Pone tu posición a dist_m del destino (rumbo al destino + rumbo_off)."""
    P_ = PP[0]
    dp = (d["dest"]["lat"], d["dest"]["lon"])
    yo = P_.np_avanza(dp, 225.0, dist_m / R)
    d["bio"].update(lat=yo[0], lon=yo[1])
    d["bio"]["hdg"] = (P_.np_rumbo(yo, dp) + rumbo_off) % 360

def capturar(panel, salida):
    P = CC.cargar.cargar(panel); pg = P.pygame; PP[0] = P
    os.makedirs(salida, exist_ok=True)
    P.cfg["mina2"] = "2"
    def pintar(S, dd, now):
        P.LZ["cel"] = {}; S.fill((0, 0, 0)); P.BIG["rects"] = []; P.LZ["lleno"] = "tablero"; P.cfg["hdmi"] = "tablero"
        P.fight["t"] = 0
        return P.lz_tablero(S, dd, dd["Flags"], now)
    base = datos(P)
    casos = []
    o = copy.deepcopy(base); casos.append(("orbita", o))
    o2 = copy.deepcopy(base); mueve(o2, 180_000, -14); o2["live"]["alt"] = 31000; casos.append(("orbita_cerca", o2))
    g = copy.deepcopy(base); g["Flags"] &= ~(1 << 4); g["Flags2"] = 1 << 12; mueve(g, 22_000, 9); g["live"]["alt"] = 6000
    casos.append(("planeo", g))
    s_ = copy.deepcopy(base); s_["Flags"] &= ~(1 << 4); mueve(s_, 3400, -38); s_["live"]["alt"] = 120
    casos.append(("superficie", s_))
    v = copy.deepcopy(s_); v["Flags"] = (1 << 21) | (1 << 26); v["live"]["alt"] = 0
    yo = (v["bio"]["lat"], v["bio"]["lon"])
    v["bio"]["ship"] = list(P.np_avanza(yo, 300, 1200 / R))
    v["bio"]["pts"] = [list(P.np_avanza(yo, 40, 900 / R))]; v["bio"]["species"] = "Osseus Discus"; v["bio"]["step"] = 1
    casos.append(("srv_puntos", v))
    for nom, dd in casos:
        for tam in ((1280, 800), (1024, 600)) if nom in ("orbita", "superficie") else ((1280, 800),):
            S = CC.preparar(P, dd, tam)
            for k in range(3):                              # 3 cuadros para tener velocidad (LLEGAS EN)
                if k:
                    P.NAVP["dist"] = [(T0 + i, P.np_calc(dd, T0)["dist"] + 300 * (3 - i)) for i in range(3)]
                pintar(S, dd, T0 + 3)
            print(nom, tam, "modo:", P.big_mode(dd, dd["Flags"]), "nav:", P.nav_activa(dd, dd["Flags"], T0, P.big_mode(dd, dd["Flags"])),
                  "fase:", P.np_calc(dd, T0)["fase"])
            pg.image.save(S, os.path.join(salida, f"planeta_{nom}_{tam[0]}.png"))
    # FLECHA AL MÁS CERCANO
    S = CC.preparar(P, v, (1280, 800)); s, ox, oy = P.lienzo_escala()
    def toca(dd, X, Y):
        pintar(S, dd, T0 + 3); P.ui["view"] = 0
        P.big_tap((ox + X * s) / 1280, (oy + Y * s) / 800)
    toca(v, 870, 630); ok1 = P.NAVP["modo"] == "cerca"
    pintar(S, v, T0 + 3); pg.image.save(S, os.path.join(salida, "planeta_srv_cerca_1280.png"))
    toca(v, 870, 630); ok2 = P.NAVP["modo"] == "dest"
    toca(v, 300, 300); ok3 = P.NAVP["forzar"][1] is True
    pintar(S, v, T0 + 3); pg.image.save(S, os.path.join(salida, "planeta_srv_esfera_1280.png"))
    P.NAVP["forzar"] = None
    # llegada
    ll = copy.deepcopy(s_); mueve(ll, 300, 0)
    S = CC.preparar(P, ll, (1280, 800)); pintar(S, ll, T0 + 10)
    aviso = (P.xa.get("a") or {}).get("title")
    pg.image.save(S, os.path.join(salida, "planeta_llegada_1280.png"))
    vis1 = P.nav_activa(ll, ll["Flags"], T0 + 15, P.big_mode(ll, ll["Flags"]))
    vis2 = P.nav_activa(ll, ll["Flags"], T0 + 40, P.big_mode(ll, ll["Flags"]))
    # bio manda
    b = copy.deepcopy(v); b["Flags"] = 1 << 21; b["Flags2"] = 1 | (1 << 4); b["live"].update(suit={"name": "Artemis"}, weapon="Muestreador genético")
    bio = P.bio_activa(b, b["Flags"], T0, P.big_mode(b, b["Flags"]))
    # sin destino
    sd = copy.deepcopy(s_); sd["dest"] = {}
    nod = P.nav_activa(sd, sd["Flags"], T0, P.big_mode(sd, sd["Flags"]))
    # apagado en CAMBIO AUTO
    P.cfg.setdefault("autoev", {})["navpla"] = False
    off = P.nav_activa(s_, s_["Flags"], T0, P.big_mode(s_, s_["Flags"]))
    P.cfg["autoev"]["navpla"] = True
    # FIJAR con el planeta en pantalla
    P.state["data"] = s_
    P.fix_tocar(); fij = P.FIX["on"] and P.FIX["kind"] == "nav"
    sd2 = copy.deepcopy(s_); sd2["Flags"] = (1 << 21) | 2            # aterrizado: sigue fijado
    fij2 = P.nav_activa(sd2, sd2["Flags"], T0, P.big_mode(sd2, sd2["Flags"]))
    P.fix_tocar()
    r = [("FIJAR PLANETA", fij and fij2), ("FLECHA CERCANO", ok1), ("FLECHA DESTINO", ok2), ("ESFERA/FLECHA", ok3), ("AVISO", aviso == "HAS LLEGADO"),
         ("VE LLEGADA", vis1), ("SE QUITA A LOS 20 s", not vis2), ("BIO MANDA", bool(bio)), ("SIN DESTINO NADA", not nod),
         ("CAMBIO AUTO NO", not off)]
    print(r)
    print("TODO OK" if all(o_ for _, o_ in r) else "FALLOS " + str([n for n, o_ in r if not o_]))

if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
