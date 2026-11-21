import sys
import cargar, capturar_hdmi_b12 as hdmi12, capturar_hdmi_b13 as hdmi13
P = cargar.cargar(sys.argv[1]); T0 = cargar.C.T0; pg = P.pygame
d = hdmi12.datos_b12(P); hdmi13.preparar(P)
P.save_cfg = lambda *a, **k: None
ok = fallos = 0
def caso(n, c):
    global ok, fallos
    if c: ok += 1
    else: fallos += 1; print("FALLO", n)
def toca(v, xn, yn, tam=(1280, 800)):
    """toca en (xn, yn) del panel viejo, convertido al punto de la HDMI donde se ve ese botón"""
    P.BIG["w"], P.BIG["h"] = tam
    S = pg.Surface(tam); P.state["data"] = d; P.state["rx"] = T0
    P.ui.update(view=v, alert=None, idle_on=False); P.xa["a"] = None; P.ui["shipcard"] = 0
    assert P.lienzo_dibuja(S, P.lz_panel_dibuja, v, d, 0, T0, True)
    r, a = next((r, a) for r, a in reversed(P.LZ["phits"]) if a[0] == "adap")
    area = P.pygame.Rect(a[1], a[2], a[3], a[4]); y0 = a[5]
    if y0 == 0:
        k = min(area.w / P.W, area.h / P.H)
        area = P.pygame.Rect(area.x + (area.w - int(P.W * k)) // 2, area.y, int(P.W * k), area.h)
    X = area.x + xn * area.w / P.W; Y = area.y + (yn - y0) * area.h / (P.H - y0)
    P.ui["view"] = v
    P.lz_panel_toque(X, Y)
c = lambda r: (r.centerx, r.centery)
for tam in ((1280, 800), (1024, 600)):
    P.LZ["pv"] = 12
    toca(12, *c(P.grid(0, 4, P.SET12_ROWS())), tam); caso(f"12 OPCIONES {tam}", P.ui["view"] == 1244)
    toca(12, *c(P.grid(4, 4, P.SET12_ROWS())), tam); caso(f"12 VERSIONES {tam}", P.ui["view"] == 1245)
    P.manual = getattr(P, "manual", None)
    toca(140, *c(P.grid(1, 4, 3)), tam); caso(f"140 -> 141 {tam}", P.ui["view"] == 141)
    toca(77, *c(P.FULL_BACK), tam); caso(f"77 < MENÚ 9 {tam}", P.ui["view"] == 220)
    p0 = P.ui.get("page1245", 0); toca(1245, P.W // 2, P.H // 2, tam); caso(f"1245 página {tam}", P.ui.get("page1245", 0) == p0 + 1)
print(f"{ok}/{ok + fallos} toques OK")
