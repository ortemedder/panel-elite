#!/usr/bin/env python3
"""Compara el COMPORTAMIENTO (no solo el dibujo) de dos versiones: big_mode y handle_note con muchos casos."""
import importlib.util, itertools, json, os, random, sys, time
T0 = 1794200000.0

def cargar(path, nombre):
    spec = importlib.util.spec_from_file_location(nombre, path)
    P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
    P.pygame.init(); P.load_fonts()
    P.LOG_ = []
    P.plog = lambda *a, **k: P.LOG_.append(" ".join(map(str, a)))
    P.play = lambda *a: None; P.voice_say = lambda *a: None
    return P

def casos_big(P):
    out = []
    rnd = random.Random(1)
    for _ in range(400):
        flags = rnd.choice([0, 1, 2, 1 << 21, (1 << 21) | 2, 1 << 26, (1 << 26) | (1 << 21), 1 << 6, (1 << 6) | 1])
        d = {"Flags": flags, "Flags2": rnd.choice([0, 0, 1]), "body": rnd.choice(["", "X 1 Ring", "X 3"]),
             "station": {"status": rnd.choice(["", "CONCEDIDO", "ATRACADO"])},
             "colonia": {"dock": rnd.choice([None, "123"])}, "live": {"alt": rnd.choice([None, 500])},
             "bio": {"lat": rnd.choice([None, 1.0]), "lon": 2.0, "R": 1e6, "hdg": 3}}
        P.state["data"] = d
        try:
            out.append(P.big_mode(d, flags))
        except Exception as e:
            out.append("ERR " + type(e).__name__)
    return out

def casos_nota(P):
    out = []
    rnd = random.Random(2)
    kinds = ["underattack", "combatmusic", "loadgame", "died", "jump", "jumpend", "interdicted", "shields_down", "fighter",
             "docking", "market", "embark", "foot", "srv", "mainmenu", "ppmenu", "sqmenu", "hull", "heat"]
    t = T0
    for i in range(500):
        t += rnd.choice([0.5, 1, 4, 70])
        P.time.time = lambda t=t: t
        d = {"Flags": rnd.choice([0, 1, 2, 1 << 6]), "Flags2": rnd.choice([0, 1]), "station": {"status": rnd.choice(["", "ATRACADO", "DESPEGADO"])},
             "exitst": rnd.choice([None, {"t0": t - 20, "out": None}, {"t0": t - 300, "out": t - 200}]), "pcnow": t}
        P.state["data"] = d; P.state["rx"] = t
        P.ui["view"] = rnd.choice([0, 3, 6, 9, 100]); P.ui["alert"] = None
        k = rnd.choice(kinds); txt = rnd.choice(["", "Combat_Unknown", "Combat_Dogfight", "Sol|G", "40"])
        try:
            P.handle_note(k, txt)
            out.append((k, txt, P.ui["view"], (P.ui["alert"] or {}).get("text"), list(P.LOG_)))
        except Exception as e:
            out.append((k, "ERR " + type(e).__name__))
        P.LOG_.clear()
    return out

def casos_toques(P):
    """Toques al azar en todas las pantallas: que se abra lo mismo y cambien igual los ajustes."""
    import socket as _s
    P.socket.socket = lambda *a, **k: type("S", (), {n_: (lambda *x, **y: None) for n_ in ("sendto", "close", "connect", "settimeout", "send", "setsockopt", "bind")} | {"getsockname": lambda *x: ("192.168.0.94", 0)})()
    out = []
    rnd = random.Random(3)
    vistas = VISTAS or sorted(k for k in P.VIEWS if isinstance(k, int))   # solo las que tienen las dos versiones
    P.FACD["data"] = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos_prueba", "faccion.json"), encoding="utf-8"))
    for i in range(600):
        t = T0 + i
        P.time.time = lambda t=t: t
        P.state["data"] = {"Flags": 0, "Flags2": 0, "system": "X", "menu": False, "notes": [], "pcnow": t}; P.state["rx"] = t
        P.ui.update(view=rnd.choice(vistas), alert=None, idle_on=False, idle_skip=t + 1e6, start=0)
        x, y = rnd.randrange(P.W), rnd.randrange(P.H)
        try:
            P.on_tap(x, y)
            out.append((P.ui["view"], P.ui.get("facsys"), P.ui.get("colf"), P.ui.get("vjp"), P.cfg.get("alt_srv"),
                        P.cfg.get("hdmi"), (P.ui["alert"] or {}).get("text")))
        except Exception as e:
            out.append("ERR " + type(e).__name__ + " " + str(e)[:40])
        P.LOG_.clear()
    return out

VISTAS = None
A = cargar(sys.argv[1], "pa"); B = cargar(sys.argv[2], "pb")
VISTAS = sorted(k for k in A.VIEWS if isinstance(k, int) and k in B.VIEWS)
for P_ in (A, B):
    P_.save_cfg = lambda: None
for nombre, f in (("big_mode", casos_big), ("handle_note", casos_nota), ("on_tap", casos_toques)):
    ra, rb = f(A), f(B)
    dif = [i for i, (x, y) in enumerate(zip(ra, rb)) if x != y]
    print(f"{nombre}: {len(ra) - len(dif)} de {len(ra)} casos iguales" + (f" · primera diferencia caso {dif[0]}: {ra[dif[0]]} / {rb[dif[0]]}" if dif else ""))
