import os, sys
import cargar, capturar_hdmi_b12 as hdmi12, capturar_hdmi_b13 as hdmi13
C = cargar.C; T0 = C.T0
PANT = [12, 124, 1244, 160, 161, 162, 163, 164, 1245, 1246, 121, 122, 140, 141, 77, 78, 100, 150]
def capturar(panel, salida):
    P = cargar.cargar(panel); pg = P.pygame
    os.makedirs(salida, exist_ok=True)
    d = hdmi12.datos_b12(P); hdmi13.preparar(P)
    res = {}
    for v in PANT:
        for tam in ((1280, 800), (1024, 600)):
            P.BIG["w"], P.BIG["h"] = tam
            S = pg.Surface(tam)
            P.state["data"] = d; P.state["rx"] = T0
            P.ui.update(view=v, alert=None, idle_on=False); P.xa["a"] = None; P.ui["shipcard"] = 0
            ok = P.lienzo_dibuja(S, P.lz_panel_dibuja, v, d, d.get("Flags", 0), T0, True)
            n = f"p{v}_{tam[0]}.png"; pg.image.save(S, os.path.join(salida, n)); res[n] = ok
    print({k: v for k, v in res.items() if not v} or "todo OK")
if __name__ == "__main__":
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
