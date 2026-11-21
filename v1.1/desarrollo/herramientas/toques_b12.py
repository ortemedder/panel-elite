import sys
import cargar, capturar_hdmi_b12 as hdmi12
P = cargar.cargar(sys.argv[1]); T0 = cargar.C.T0; pg = P.pygame
d = hdmi12.datos_b12(P)
P.COMPRAS.update(day=P.time.strftime("%Y-%m-%d"), list=[{"st": "Ibanez Hub", "sys": "Pirawoth", "items": ["Acero"], "t": T0}])
P.cgoals["list"] = [{"title": f"CG {k}", "sys": "Sol", "expiry": "2026-12-25T00:00:00Z", "qty": 1, "target": 2} for k in range(5)]
env = []; P.ir_send = lambda s: env.append(s); led = []; P.led_clear = lambda: led.append(1)
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
P.ui["sqpage"] = 0; toca(165, lambda r, a: a[0] == "old" and r.y > 108); caso("165 página", P.ui["sqpage"] == 1)
toca(215, lambda r, a: a[0] == "sqbtn"); caso("215 ESCUADRÓN >", P.ui["view"] == 165 and P.ui["sqpage"] == 0)
P.cgoals["page"] = 0; toca(132, lambda r, a: a[0] == "old" and r.y > 108); caso("132 página", P.cgoals["page"] == 1)
P.ui["sesstab"] = 0; toca(11, lambda r, a: a == ("diatab", 1)); caso("11 -> AMIGOS", P.ui["sesstab"] == 1)
toca(11, lambda r, a: a == ("diatab", 0)); caso("11 AMIGOS -> DÍA", P.ui["sesstab"] == 0)
P.ui["sesstab"] = 1; toca(11, lambda r, a: a[0] == "sqbtn"); caso("11 AMIGOS ESCUADRÓN >", P.ui["view"] == 165)
P.ui["sesstab"] = 0; toca(11, lambda r, a: a == ("diatab", 2)); caso("11 -> DÓNDE COMPRAR", P.ui["sesstab"] == 2)
env.clear(); toca(11, lambda r, a: a[0] == "irsys"); caso("11 compras fila -> IR", env == ["Pirawoth"])
toca(11, lambda r, a: a == ("diatab", 0)); caso("11 compras fuera -> DÍA", P.ui["sesstab"] == 0)
d["footcz"] = {"led": {"cr": 900000, "bonds": [2, 300000], "bounties": [3, 600000]}}
P.LEDB["sure"] = 0; toca(11, lambda r, a: a[0] == "ledb"); caso("11 BORRAR -> ¿SEGURO?", P.LEDB["sure"] > 0 and not led)
P.LEDB["sure"] = P.time.time() + 3; toca(11, lambda r, a: a[0] == "ledb"); caso("11 ¿SEGURO? -> borra", led == [1])
toca(11, lambda r, a: a[0] == "old" and r.y < 108 and any(t == 130 and ro.collidepoint(a[1], a[2]) for t, _, ro, _ in P.tab_rects(11))); caso("11 pestaña GALNET", P.ui["view"] == 130)
print(f"{ok}/{ok + fallos} toques OK")
