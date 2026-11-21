import copy, sys
import cargar, capturar_hdmi_b10 as hdmi
P = cargar.cargar(sys.argv[1]); T0 = cargar.C.T0
pg = P.pygame
base = hdmi.datos_b10(P)
enviados = []
P.ir_send = lambda s: enviados.append(s)
P.BIG["w"], P.BIG["h"] = 1280, 800
ok = fallos = 0
def pinta(v, d):
    S = pg.Surface((1280, 800))
    P.state["data"] = d; P.state["rx"] = T0
    P.ui.update(view=v, alert=None, idle_on=False); P.xa["a"] = None; P.ui["shipcard"] = 0
    assert P.lienzo_dibuja(S, P.lz_panel_dibuja, v, d, d.get("Flags", 0), T0, True)
def toca(v, d, X, Y):
    pinta(v, d); P.ui["view"] = v
    return P.lz_panel_toque(X, Y)
def caso(nom, cond):
    global ok, fallos
    if cond: ok += 1
    else: fallos += 1; print("FALLO", nom)
d = copy.deepcopy(base)
# 4: pestañas (y = 112+4+2+ ~26)
for i, x in enumerate((220, 640, 1060)):
    P.ui["tab4"] = 0; P.ui["page4"] = 5
    toca(4, d, x, 140); caso(f"4 pestaña {i}", P.ui["tab4"] == i and P.ui["page4"] == 0)
P.ui["tab4"] = 1; P.ui["page4"] = 0; toca(4, d, 640, 500); caso("4 página", P.ui["page4"] == 1 and P.ui["tab4"] == 1)
P.ui["page4"] = 0; toca(210, d, 640, 500); caso("210 página", P.ui["page4"] == 1)
P.ui["page125"] = 0; toca(125, d, 640, 500); caso("125 página", P.ui["page125"] == 1)
for v in (170, 171):
    P.ui["shippage"] = 0; toca(v, d, 640, 600); caso(f"{v} página", P.ui["shippage"] == 1)
# 135 filtros
for fk, x in (("todo", 870), ("aqui", 985), ("sis", 1150)):
    P.ui["colf"] = "todo" if fk != "todo" else "sis"
    toca(135, d, x, 140)
    caso(f"135 filtro {fk}", P.ui["colf"] == fk)
P.ui["colf"] = "todo"; P.ui["colpg"] = 0; toca(135, d, 640, 600); caso("135 página", P.ui["colpg"] == 1)
P.ui["colf"] = "sis"; enviados.clear(); toca(135, d, 400, 300); caso("135 fila -> ir_send", enviados == ["Base Y"])
d2 = copy.deepcopy(d); d2["colonia"]["list"].append({"mid": "2", "sys": "Wolf 359", "st": "Puerto", "t": T0, "prog": 10.0, "res": [["Agua", 100, 0, "water"]]})
P.ui["colf"] = "todo"; P.ui["colsel"] = 0
toca(135, d2, 200, 140); caso("135 cabecera -> otra construcción", P.ui.get("colsel") == 1)
# pestañas de la barra (NAVE -> FLOTA)
toca(170, d, 420, 82); caso("barra 170 -> 171", P.ui["view"] == 171)
toca(4, d, 200, 40); caso("< MENÚ", P.ui["view"] != 4)
print(f"{ok}/{ok + fallos} toques OK")
# pestañas de todos los grupos: tocar cada pestaña nueva lleva a su pantalla
for v0 in (3, 4, 8, 170, 6, 11, 194, 165):
    if v0 not in P.LZ_PANEL:
        continue
    pinta(v0, d)
    tabs = [(r, a) for r, a in P.LZ["phits"] if r.y == 57 - 5]
    for t, n, r_old, act in P.tab_rects(v0):
        P.ui["view"] = v0; pinta(v0, d); P.ui["view"] = v0
        hit = next(((r, a) for r, a in P.LZ["phits"] if a[0] == "old" and r.y < 108 and r_old.collidepoint(a[1], a[2]) and r.x > 250 and r.right < 1150), None)
        caso(f"pestaña {n} desde {v0}", hit is not None)
        if hit:
            P.lz_panel_toque(*hit[0].center); caso(f"pestaña {n} -> {t}", P.ui["view"] == t)
print(f"{ok}/{ok + fallos} toques OK")
