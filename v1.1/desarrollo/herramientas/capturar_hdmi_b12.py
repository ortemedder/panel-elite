import os, sys, copy
import cargar, capturar_hdmi_b10 as hdmi
C = cargar.C; T0 = C.T0
def datos_b12(P):
    d = hdmi.datos_b10(P)
    d["sess"] = {"earn": {"bounty": 1250000, "trade": 32000000, "explo": 0, "missions": 4500000, "bio": 12000000},
                 "play": 7200, "day": True, "jumps": 34, "ly": 812.4, "kfoot": 3, "kills": 11, "deaths": 1,
                 "credits0": 4100000000, "pending": 820000, "pending_n": 4}
    d["balance"] = 4150000000
    d["friends"] = {"on": ["KORZO", "Lobo Gris", "Atenea"], "off": [["Vega", 12], ["Orion", 140]], "wing": ["KORZO", "Atenea"]}
    d["inara"] = {"ok": True, "t": T0 - 600, "me": {"squad": "Caballeros de Sion", "sqrank": "Almirante", "sqn": 14},
                  "others": [{"name": n, "ship": s, "squad": "CDSN", "ranks": [["combat", 5, 0]]} for n, s in
                             (("KORZO", "Python"), ("Lobo Gris", "Anaconda"), ("Atenea", "Krait Mk II"), ("Vega", "Adder"),
                              ("Orion", "Cobra Mk III"), ("Hermes", "Mamba"), ("Draco", "Corsair"), ("Lira", "Asp Explorer"))]}
    d["squad"] = {"name": "Caballeros de Sion", "rank": 4}
    d["ranks"] = {"cmdr": "ORTEM ED DER", "rank": {"Combat": 5, "Trade": 8, "Explore": 6, "Soldier": 2, "Exobiologist": 4, "Federation": 3, "Empire": 10},
                  "progress": {"Combat": 45, "Trade": 0, "Explore": 70, "Soldier": 12, "Exobiologist": 88, "Federation": 5, "Empire": 30}}
    d["career"] = {"foot": 120, "bonds": 340, "bounties": 1820}
    d["combat"] = {"kills": [["Pirata Python", 250000, "R"], ["Federal Corvette", 80000, "B"], ["KORZO", 0, "P"], ["Vulture", 45000, "R"]],
                   "bonds": [["Caballeros de Sion", 1200000], ["Beasts of Bestia", 300000]]}
    d["masacre"] = [["Caballeros de Sion", "Piratas de Wolf", 12, 24], ["Sion Fed", "Piratas de Wolf", 24, 24]]
    d["mycg"] = [{"title": "Construir la estación de Pirawoth", "sys": "Pirawoth", "market": "Ibanez Hub", "expiry": "2026-12-01T00:00:00Z",
                  "tier": "Tier 3", "top": "Tier 8", "mine": 4500, "band": 25, "contrib": 812}]
    return d
PANT = [(165, "", {}), (165, "_p1", {"sqpage": 1}), (215, "", {}), (123, "", {}), (132, "", {}), (11, "", {}), (11, "_amigos", {"sesstab": 1}),
        (11, "_compras", {"sesstab": 2}), (61, "", {})]
def capturar(panel, salida):
    P = cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    d = datos_b12(P)
    P.cgoals["list"] = [{"title": "Defensa de Sol", "sys": "Sol", "market": "Abraham Lincoln", "expiry": "2026-11-25T00:00:00Z",
                         "qty": 5000000, "target": 20000000, "text": "Entrega bonos de combate"},
                        {"title": "Ayuda a Wolf 359", "sys": "Wolf 359", "expiry": "2026-11-01T00:00:00Z", "complete": True}]
    P.cgoals["t"] = T0
    P.COMPRAS.update(day=P.time.strftime("%Y-%m-%d"), list=[{"st": "Ibanez Hub", "sys": "Pirawoth", "items": ["Acero", "Polímeros"], "t": T0 - 300}])
    res = {}
    for v, suf, ext in PANT:
        for k in ("sqpage", "sesstab"):
            P.ui[k] = ext.get(k, 0)
        for tam in ((1280, 800), (1024, 600)):
            P.BIG["w"], P.BIG["h"] = tam
            S = pg.Surface(tam)
            P.state["data"] = d; P.state["rx"] = T0
            P.ui.update(view=v, alert=None, idle_on=False); P.xa["a"] = None; P.ui["shipcard"] = 0
            ok = P.lienzo_dibuja(S, P.lz_panel_dibuja, v, d, d.get("Flags", 0), T0, True) if v in P.LZ_PANEL else False
            n = f"p{v}{suf}_{tam[0]}.png"; pg.image.save(S, os.path.join(salida, n)); res[n] = ok
    P.ui["sesstab"] = 0
    for v in (11, 61):
        S = pg.Surface((640, 316))
        ok = P.lz_celda_dibuja(S, P.LZ_CELDA[v], v, d, 0, T0, pg.Rect(0, 0, 640, 316), "fit")
        n = f"c{v}.png"; pg.image.save(S, os.path.join(salida, n)); res[n] = ok
    print(res)
if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
