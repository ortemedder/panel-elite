import os, sys, copy, json
import cargar, capturar_hdmi_b10 as hdmi
C = cargar.C; T0 = C.T0
def fac_rica(P):
    D = copy.deepcopy(P.FACD["data"])
    S = D["sistemas"]
    import random
    rnd = random.Random(3)
    base = S["Pirawoth"]
    for i in range(14):
        n = f"Sistema {chr(65 + i)}{i}"
        v = copy.deepcopy(base); v["sys"] = n; v["ctrl"] = i % 3 == 0; v["inf"] = round(rnd.uniform(8, 70), 1)
        v["prev"] = v["inf"] + rnd.choice((-1.3, 0.6, 0)); v["segunda_inf"] = round(rnd.uniform(5, 40), 1)
        v["pos"] = [base["pos"][0] + rnd.uniform(-15, 15), 0, base["pos"][2] + rnd.uniform(-15, 15)]
        v["activos"] = rnd.choice(([], ["Boom"], ["War"], ["Famine"], ["Expansion"]))
        v["pendientes"] = rnd.choice(([], ["Retreat"], ["Investment"]))
        v["trafico"] = {f"2026-11-0{k}": rnd.randint(0, 9) for k in range(3, 10)}
        S[n] = v
    p = S["Pirawoth"]
    p["hinf"] = [[T0 - 86400 * (8 - k), 60 + k * 1.3 - (k % 3)] for k in range(9)]
    p["conflictos"] = [{"tipo": "war", "contra": "Beasts of Bestia", "ganados": 2, "perdidos": 1}]
    p["activos"] = ["War", "Famine"]; p["pendientes"] = ["Expansion"]
    p["trafico"] = {f"2026-11-0{k}": k for k in range(3, 10)}
    p["tick_ult"] = T0 - 3600 * 5; p["tick_prox"] = T0 + 3600 * 19; p["tick_disp"] = 20
    p["todas"] += [{"n": f"Facción {k}", "inf": 4 - k * 0.5, "act": ["Boom"] if k == 1 else [], "pend": [], "gov": "$government_Democracy;"} for k in range(4)]
    for k in range(5):
        D["zona"][f"Vecino {k}"] = {"pos": [base["pos"][0] + k * 3 - 6, 0, base["pos"][2] + 8 - k * 4], "pot": ["Jerome Archer", "Edmund Mahon", "Li Yong-Rui"][k % 3],
                                    "est": "Fortified", "prog": 0.2 * k}
    return D
PANT = [220, 192, 194, 195, 196, 214, 213]
def capturar(panel, salida):
    P = cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    P.FACD["data"] = fac_rica(P); P.fac_watch = lambda now: None
    d = hdmi.datos_b10(P); d["starpos"] = [-10, 0, -90]
    P.ui["facsys"] = "Pirawoth"; P.ui["facback"] = 192
    res = {}
    for v, suf, ext in [(v, "", {}) for v in PANT] + [(213, "_al", {"solo": "al"}), (192, "_p2", {"facpg": 1})]:
        P.C_ = None
        P.BGS["solo"] = ext.get("solo"); P.ui["facpg"] = ext.get("facpg", 0)
        for tam in ((1280, 800), (1024, 600)):
            P.BIG["w"], P.BIG["h"] = tam
            S = pg.Surface(tam)
            P.state["data"] = d; P.state["rx"] = T0
            P.ui.update(view=v, alert=None, idle_on=False); P.xa["a"] = None; P.ui["shipcard"] = 0
            P.fac_watch = lambda now: None
            ok = P.lienzo_dibuja(S, P.lz_panel_dibuja, v, d, d.get("Flags", 0), T0, True) if v in P.LZ_PANEL else False
            n = f"p{v}{suf}_{tam[0]}.png"; pg.image.save(S, os.path.join(salida, n)); res[n] = ok
    print(res)
if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
