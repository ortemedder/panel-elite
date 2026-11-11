#!/usr/bin/env python3
"""Dibuja TODAS las pantallas del panel con los mismos datos de prueba y guarda una foto y una huella de cada una.
Sirve para comprobar que la v1.1 depurada se ve exactamente igual que la v1.0b20.
Uso:  python3 herramientas/capturar.py original/panel_v1.0b20.py capturas/b20
      python3 herramientas/capturar.py v11/panel.py capturas/v11
      python3 herramientas/capturar.py --comparar capturas/b20 capturas/v11"""
import hashlib, importlib.util, json, os, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
T0 = 1794200000.0                                        # hora fija: todas las capturas iguales

def datos(P):
    d = {"Flags": (1 << 21) | (1 << 4), "Flags2": 0, "system": "Pirawoth", "menu": False, "notes": [], "sver": "v1.0b12",
         "pcnow": T0, "body": "Pirawoth 3 a", "cargocap": 784, "cargo": [["Acero", 300]],
         "live": {"alt": 1850, "ship": {"ship": "Python", "name": "SION CARGO", "ident": "CS-01", "hull": 1.0}},
         "bio": {"lat": 10.0, "lon": 20.0, "R": 3000000, "hdg": 35},
         "station": {"status": "CONCEDIDO", "name": "Ibanez Hub", "type": "Coriolis", "mid": 5, "pad": 23, "gt": T0 - 60},
         "market": {"station": "Ibanez Hub", "mid": 5, "t": T0, "sell": [["Acero", 300, 4000, 4100, 900]], "best": [["Oro", 50000, 45000]],
                    "col": [["Acero", 9000, 300, 800, "steel"]]},
         "colonia": {"dock": None, "list": [{"mid": "1", "sys": "Pirawoth", "st": "Depósito", "t": T0, "prog": 42.0,
                                            "res": [["Acero", 1000, 200, "steel"], ["Polímeros", 500, 0, "polymers"]]}]},
         "colsys": {"sys": "Pirawoth", "t": T0, "status": "ok", "n": 2, "off": {"polymers": [["Base Y", 300, 250, 300, "M", T0, False, "2"]]}}}
    return d

def fijar(P):
    """Deja quietos los datos que cambian solos (hilos de red, rendimiento, log), para comparar sin falsos avisos."""
    import tempfile, threading
    for name in ("PERF",):
        if hasattr(P, name):
            getattr(P, name).update(cpu=20.0, mhz=1500, temp=45.0, ram=7.0, fps=8)
    if hasattr(P, "_rd") and not getattr(P, "_rd_fijo", False):     # memoria y CPU de mentira, siempre iguales
        _rd0 = P._rd
        fake = {"/proc/meminfo": "MemTotal: 4000000 kB\nMemFree: 3000000 kB\nMemAvailable: 3720000 kB\n"}
        P._rd = lambda f, *a, **k: fake.get(f) if f in fake else _rd0(f, *a, **k)
        P._rd_fijo = True
    if hasattr(P, "galnet"):
        P.galnet.update(list=[], t=0, err="sin red (prueba)", page=0, sel=None, apage=0, lines=None); P.galnet["new"] = set()
    if hasattr(P, "cgoals"):
        P.cgoals.update(list=[], t=0, err="sin red (prueba)", page=0, d=None)
    P.FACD.update(t=T0 - 300, err="", data=json.load(open(os.path.join(AQUI, "..", "datos_prueba", "faccion.json"), encoding="utf-8")))
    for name, val in (("GH", {"t": T0 - 600, "err": ""}), ("FTICK", {"next": T0 + 3600, "win": 20, "sys": "Pirawoth", "t": T0})):
        if hasattr(P, name):
            getattr(P, name).update(val)
    if hasattr(P, "ACT"):
        P.ACT.update(on=True, err="")
        for k in ("pings", "feed", "jumps"):
            P.ACT[k].clear()
        P.ACT["uids"].clear()
    log = os.path.join(tempfile.mkdtemp(), "panel.log")
    open(log, "w", encoding="utf-8").write("10/11 00:00:00 Panel de prueba\n")
    P.PANEL_LOG = log
    P.state["log"].clear() if hasattr(P.state.get("log"), "clear") else None

def capturar(panel, salida):
    sys.argv = [panel]
    spec = importlib.util.spec_from_file_location("panel", panel)
    P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
    pg = P.pygame; pg.init(); P.load_fonts()
    P.fac_watch = lambda now: None
    P.FACD["data"] = json.load(open(os.path.join(AQUI, "..", "datos_prueba", "faccion.json"), encoding="utf-8"))
    P.time.time = lambda: T0
    fijar(P)
    os.makedirs(salida, exist_ok=True)
    s = pg.Surface((P.W, P.H))
    huellas, fallos = {}, []
    d = datos(P)
    for v in sorted(k for k in P.VIEWS if isinstance(k, int)):
        P.state["data"] = d; P.state["rx"] = T0; P.ui.update(start=0, idle_skip=T0 + 1e6, view=v, alert=None)
        P.xa["a"] = None
        fijar(P)
        try:
            P.render(s)
            pg.image.save(s, os.path.join(salida, f"{v}.png"))
            huellas[str(v)] = hashlib.md5(pg.image.tostring(s, "RGB")).hexdigest()
        except Exception as e:
            fallos.append(f"{v}: {e}")
    json.dump({"huellas": huellas, "fallos": fallos, "panel": panel}, open(os.path.join(salida, "huellas.json"), "w"), indent=1)
    print(f"{len(huellas)} pantallas capturadas en {salida}" + (f" · {len(fallos)} con error: {fallos}" if fallos else ""))

def comparar(a, b):
    A = json.load(open(os.path.join(a, "huellas.json")))["huellas"]
    B = json.load(open(os.path.join(b, "huellas.json")))["huellas"]
    dif = sorted((k for k in A if A[k] != B.get(k)), key=int)
    falta = sorted(set(A) - set(B), key=int)
    print(f"{len(A) - len(dif)} de {len(A)} pantallas iguales" + (f" · distintas: {dif}" if dif else "") + (f" · faltan: {falta}" if falta else ""))
    return not dif

if __name__ == "__main__":
    if sys.argv[1] == "--comparar":
        sys.exit(0 if comparar(sys.argv[2], sys.argv[3]) else 1)
    capturar(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
