import os, sys
import cargar, capturar_hdmi_b12 as hdmi12
C = cargar.C; T0 = C.T0
TXT = ("La Federación anuncia nuevas medidas de seguridad en los sistemas fronterizos tras una serie de ataques. " * 8 + "\n\n") * 3
def preparar(P):
    P.galnet.update(list=[{"id": f"n{k}", "title": f"Noticia {k}: los Caballeros de Sion amplían su influencia en el sector {k}",
                           "date": "21 NOV 3312", "body": TXT} for k in range(9)], t=T0, err="", page=0, sel=0, apage=0, lines=None)
    P.galnet["new"] = {"n0", "n2"}
    P.trip["list"] = [{"sys": "Pirawoth", "body": "Pirawoth 3 a", "lat": 10.5, "lon": 22.0, "R": 3000000, "pos": [-19, 0, -95],
                       "tag": "EXOBIO", "t": T0 - 3600 * k} for k in range(8)]
    P.trip["sel"] = 0; P.trip["page"] = 0
    P.CALC.update(cur="1250", acc=None, op=None, expr="", new=True,
                  tape=[("120 × 3", "360"), ("4.500.000 + 820.000", "5.320.000"), ("100 ÷ 7", "14,2857")])
PANT = [(130, ""), (131, ""), (128, ""), (129, ""), (211, "")]
def capturar(panel, salida):
    P = cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    d = hdmi12.datos_b12(P); d["body"] = "Pirawoth 3 a"; d["bio"] = {"lat": 10.0, "lon": 20.0, "R": 3000000, "hdg": 35}
    preparar(P)
    res = {}
    for v, suf in PANT:
        for tam in ((1280, 800), (1024, 600)):
            P.BIG["w"], P.BIG["h"] = tam
            S = pg.Surface(tam)
            P.state["data"] = d; P.state["rx"] = T0
            P.ui.update(view=v, alert=None, idle_on=False); P.xa["a"] = None; P.ui["shipcard"] = 0
            ok = P.lienzo_dibuja(S, P.lz_panel_dibuja, v, d, 0, T0, True)
            n = f"p{v}{suf}_{tam[0]}.png"; pg.image.save(S, os.path.join(salida, n)); res[n] = ok
    S = pg.Surface((640, 316))
    res["c133"] = P.lz_celda_dibuja(S, P.LZ_CELDA[133], 133, d, 0, T0 + 30, pg.Rect(0, 0, 640, 316), "fit")
    pg.image.save(S, os.path.join(salida, "c133.png"))
    print(res)
if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
