import sys, copy
sys.argv = ["x", sys.argv[1]]
import cargar, capturar_hdmi_b10 as hdmi, capturar_hdmi_b11 as hdmi11
P = cargar.cargar(sys.argv[1]); T0 = cargar.C.T0; pg = P.pygame
P.FACD["data"] = hdmi11.fac_rica(P); P.fac_watch = lambda now: None
d = hdmi.datos_b10(P); d["starpos"] = [-10, 0, -90]
env = []; P.ir_send = lambda s: env.append(s)
P.BIG["w"], P.BIG["h"] = 1280, 800
ok = fallos = 0
def caso(n, c):
    global ok, fallos
    if c: ok += 1
    else: fallos += 1; print("FALLO", n)
def pinta(v):
    S = pg.Surface((1280, 800)); P.state["data"] = d; P.state["rx"] = T0
    P.ui.update(view=v, alert=None, idle_on=False); P.xa["a"] = None; P.ui["shipcard"] = 0
    assert P.lienzo_dibuja(S, P.lz_panel_dibuja, v, d, d.get("Flags", 0), T0, True)
def hit(v, pred):
    pinta(v)
    return next(((r, a) for r, a in reversed(P.LZ["phits"]) if pred(r, a)), None)
def toca(v, pred):
    h = hit(v, pred); P.ui["view"] = v
    if not h: return False
    return P.lz_panel_toque(*h[0].center)
for i, (n, dest) in enumerate(P.SUB9):
    toca(220, lambda r, a, i=i: a[0] == "old" and P.grid(i, 4, 2).collidepoint(a[1], a[2]))
    caso(f"220 botón {n}", P.ui["view"] == dest)
P.ui["facpg"] = 0
toca(192, lambda r, a: a[0] == "facsys"); caso("192 fila -> 194", P.ui["view"] == 194 and P.ui["facback"] == 192)
P.ui["facpg"] = 0; toca(192, lambda r, a: a == ("facpg", 1)); caso("192 ►", P.ui["facpg"] == 1)
toca(192, lambda r, a: a == ("facpg", -1)); caso("192 ◄", P.ui["facpg"] == 0)
for v in (194, 195, 196, 214):
    P.ui["facsys"] = "Pirawoth"; P.ui["facback"] = 213
    toca(v, lambda r, a: a[0] == "old" and P.BACK_R.collidepoint(a[1], a[2])); caso(f"{v} VOLVER", P.ui["view"] == 213)
    env.clear(); toca(v, lambda r, a: a[0] == "old" and P.IR_R.collidepoint(a[1], a[2])); caso(f"{v} IR", env == ["Pirawoth"])
for t in (195, 196, 214, 194):
    P.ui["facsys"] = "Pirawoth"
    toca(194 if t != 194 else 214, lambda r, a, t=t: a[0] == "old" and r.y < 108 and any(tt == t and ro.collidepoint(a[1], a[2]) for tt, _, ro, _ in P.tab_rects(194)))
    caso(f"pestaña -> {t}", P.ui["view"] == t)
P.ui["facsys"] = "Pirawoth"
toca(196, lambda r, a: a[0] == "facsys"); caso("196 punto -> otra ficha", P.ui["view"] == 194 and P.ui["facsys"] != "Pirawoth")
P.ui["facsys"] = "Pirawoth"
P.BGS["solo"] = None; toca(213, lambda r, a: a == ("bgssolo", "al")); caso("213 solo alertas", P.BGS["solo"] == "al")
toca(213, lambda r, a: a == ("bgssolo", "al")); caso("213 quitar filtro", P.BGS["solo"] is None)
P.BGS["orden"] = "inf"; toca(213, lambda r, a: a == ("bgsord", "sys")); caso("213 ordenar SISTEMA", P.BGS["orden"] == "sys" and P.BGS["asc"])
toca(213, lambda r, a: a == ("bgsord", "sys")); caso("213 invertir", P.BGS["orden"] == "sys" and not P.BGS["asc"])
P.LZ["bgs"]["off"] = 0; toca(213, lambda r, a: a == ("bgsoff", 1)); caso("213 ▼", P.LZ["bgs"]["off"] > 0)
toca(213, lambda r, a: a[0] == "facsys"); caso("213 fila -> ficha", P.ui["view"] == 194 and P.ui["facback"] == 213)
print(f"{ok}/{ok + fallos} toques OK")
