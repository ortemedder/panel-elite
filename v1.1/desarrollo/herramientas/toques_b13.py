import sys
import cargar, capturar_hdmi_b12 as hdmi12, capturar_hdmi_b13 as hdmi13
P = cargar.cargar(sys.argv[1]); T0 = cargar.C.T0; pg = P.pygame
d = hdmi12.datos_b12(P); hdmi13.preparar(P)
P.trip_save = lambda: None
P.BIG["w"], P.BIG["h"] = 1280, 800
ok = fallos = 0
def caso(n, c):
    global ok, fallos
    if c: ok += 1
    else: fallos += 1; print("FALLO", n)
def toca(v, pred):
    S = pg.Surface((1280, 800)); P.state["data"] = d; P.state["rx"] = T0
    P.ui.update(view=v, alert=None, idle_on=False); P.xa["a"] = None; P.ui["shipcard"] = 0
    assert P.lienzo_dibuja(S, P.lz_panel_dibuja, v, d, 0, T0, True)
    h = next(((r, a) for r, a in reversed(P.LZ["phits"]) if pred(r, a)), None)
    P.ui["view"] = v
    return h and P.lz_panel_toque(*h[0].center)
P.galnet["page"] = 0; toca(130, lambda r, a: a[0] == "galpg"); caso("130 página", P.galnet["page"] == 1)
P.galnet["page"] = 0; toca(130, lambda r, a: a == ("galsel", 2)); caso("130 noticia -> 131", P.ui["view"] == 131 and P.galnet["sel"] == 2 and "n2" not in P.galnet["new"])
P.galnet["apage"] = 0; toca(131, lambda r, a: a[0] == "galart"); caso("131 página", P.galnet["apage"] == 1)
P.trip["page"] = 0; toca(128, lambda r, a: a[0] == "trippg"); caso("128 página", P.trip["page"] == 1)
P.trip["page"] = 0; toca(128, lambda r, a: a == ("tripsel", 3)); caso("128 nota -> 129", P.ui["view"] == 129 and P.trip["sel"] == 3)
n0 = len(P.trip["list"]); toca(128, lambda r, a: a[0] == "old" and P.TRIP_SAVE.collidepoint(a[1], a[2])); caso("128 GUARDAR AQUÍ", len(P.trip["list"]) == n0 + 1)
P.trip["sel"] = 0; P.ui["confirm"] = (None, 0); n0 = len(P.trip["list"])
toca(129, lambda r, a: a[0] == "old" and P.TRIP_DEL.collidepoint(a[1], a[2])); caso("129 BORRAR -> ¿SEGURO?", P.ui["confirm"][0] == "trip_del")
toca(129, lambda r, a: a[0] == "old" and P.TRIP_DEL.collidepoint(a[1], a[2])); caso("129 ¿SEGURO? -> borra", len(P.trip["list"]) == n0 - 1 and P.ui["view"] == 128)
P.CALC.update(cur="0", acc=None, op=None, expr="", new=True)
for k in "12+3=":
    i, j = next((i, j) for i, row in enumerate(P.CK) for j, kk in enumerate(row) if kk == k)
    toca(211, lambda r, a, i=i, j=j: a[0] == "old" and P.c_key(i, j).collidepoint(a[1], a[2]))
caso("211 12+3=15", P.CALC["cur"] == "15")
toca(211, lambda r, a: a[0] == "old" and P.C_CLR.collidepoint(a[1], a[2])); caso("211 C", P.CALC["cur"] == "0")
toca(211, lambda r, a: a == ("calctape", 0)); caso("211 cinta", P.CALC["cur"] == "15")
print(f"{ok}/{ok + fallos} toques OK")
