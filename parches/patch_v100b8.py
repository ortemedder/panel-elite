#!/usr/bin/env python3
# Parche v1.0 beta 8 (desde la beta 7):
#  - pantalla de Caballeros de Sion sin los datos de la Pi (CPU, MHz, temperatura, RAM, FPS)
#  - PRUEBA: tercera pantalla de espera ACTIVIDAD GALACTICA en directo. Mientras se ve, la Pi escucha EDDN
#    (necesita python3-zmq) y enciende un destello en cada salto. Alterna vista galaxia / vista de tu zona.
#    Rotacion de la espera cada 20 s: normal -> faccion -> actividad.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def draw_act_screen" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b7', s):
    sys.exit("Este parche es para la v1.0 beta 7")
shutil.copy(P, P + ".bak100b7")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

CODE = r'''
# ---------- v1.0 beta 8 ----------
IDLE_MODE = {"m": None, "t": 0}                         # que pantalla de espera se esta viendo

_perf_side_b8 = perf_side

def perf_side(S):
    if IDLE_MODE["m"] in ("fac", "act") and time.time() - IDLE_MODE["t"] < 2:
        return                                           # pantallas de facción y actividad: limpias
    _perf_side_b8(S)

# --- actividad galactica en directo (EDDN escuchado por la propia Pi solo mientras se ve) ---
ACT = {"want": 0, "on": False, "err": "", "pings": deque(maxlen=600), "feed": deque(maxlen=12),
       "jumps": deque(maxlen=20000), "uids": {}, "zmq": None}

def act_ok():
    if ACT["zmq"] is None:
        try:
            import zmq  # noqa
            ACT["zmq"] = True
        except ImportError:
            ACT["zmq"] = False
    return ACT["zmq"]

def act_loop():
    while True:
        if time.time() - ACT["want"] > 30 or not act_ok():
            time.sleep(1); continue
        try:
            import zmq, zlib as _z
            ctx = zmq.Context.instance()
            sub = ctx.socket(zmq.SUB)
            sub.setsockopt(zmq.SUBSCRIBE, b""); sub.setsockopt(zmq.RCVTIMEO, 1000)
            sub.connect("tcp://eddn.edcd.io:9500")
            ACT.update(on=True, err="")
            plog("Actividad galáctica: escuchando EDDN")
            while time.time() - ACT["want"] < 30:        # deja de escuchar 30 s despues de quitar la pantalla
                try:
                    raw = sub.recv()
                except zmq.Again:
                    continue
                pkt = _z.decompress(raw)
                if b"FSDJump" not in pkt and b"CarrierJump" not in pkt:
                    continue
                d = json.loads(pkt)
                if "/journal/" not in d.get("$schemaRef", ""):
                    continue
                hd = d.get("header") or {}
                gv = hd.get("gameversion") or ""
                if gv.startswith("3.") or "legacy" in gv.lower():
                    continue
                m = d.get("message") or {}
                if m.get("event") not in ("FSDJump", "CarrierJump") or not m.get("StarPos"):
                    continue
                now = time.time()
                x, y_, z = m["StarPos"]
                nm = m.get("StarSystem") or "?"
                mine = nm in ((FACD["data"] or {}).get("sistemas") or {})
                ACT["pings"].append((x, z, now, mine))
                ACT["jumps"].append(now)
                ACT["uids"][str(hd.get("uploaderID"))[:10]] = now
                ACT["feed"].appendleft((nm, mine, now))
            sub.close(0)
            ACT["on"] = False
            plog("Actividad galáctica: deja de escuchar")
        except Exception as e:
            ACT.update(on=False, err=str(e)[:60]); log_exc("actividad EDDN", e); time.sleep(10)

threading.Thread(target=act_loop, daemon=True, name="actividad").start()

_GALBG = {}

def gal_points():
    if "pts" not in _GALBG:
        import random as _r
        rnd = _r.Random(7); pts = []
        for k in range(5000):
            arm = k % 4; t = rnd.random() ** 0.6 * 4.2; a = t * 1.15 + arm * math.pi / 2 + rnd.gauss(0, 0.22)
            r = 1500 + t * 9500 + rnd.gauss(0, 900)
            pts.append((25 + r * math.cos(a), 25900 + r * math.sin(a), rnd.randint(25, 70)))
        for k in range(900):
            r = abs(rnd.gauss(0, 2600)); a = rnd.random() * 6.283
            pts.append((25 + r * math.cos(a), 25900 + r * math.sin(a), rnd.randint(60, 120)))
        _GALBG["pts"] = pts
    return _GALBG["pts"]

def act_view(M, gal):
    """(funcion mundo->pantalla, escala) para la vista galaxia o la de tu zona."""
    if gal:
        X0, X1, Z0, Z1 = -45000, 45000, -18000, 72000
    else:
        S_ = [v["pos"] for v in ((FACD["data"] or {}).get("sistemas") or {}).values() if v.get("pos") and None not in v["pos"]]
        if S_:
            xs, zs = sorted(p[0] for p in S_), sorted(p[2] for p in S_)
            cx_, cz_ = xs[len(xs) // 2], zs[len(zs) // 2]           # mediana: un sistema lejano no lo descentra
            ds = sorted(max(abs(p[0] - cx_), abs(p[2] - cz_)) for p in S_)
            hw = max(40, ds[int(len(ds) * 0.85)] * 1.25)
        else:
            cx_, cz_, hw = 0, 0, 260
        X0, X1, Z0, Z1 = cx_ - hw, cx_ + hw, cz_ - hw * 0.87, cz_ + hw * 0.87
    sc = min(M.w / (X1 - X0), M.h / (Z1 - Z0))
    cx, cz = (X0 + X1) / 2, (Z0 + Z1) / 2
    return (lambda x, z: (M.centerx + (x - cx) * sc, M.centery - (z - cz) * sc)), sc

def act_bg(surf, M, gal):
    real, rr = (surf.real, surf._r(M)) if type(surf).__name__ == "ScaledSurf" else (surf, pygame.Rect(M))
    key = (rr.w, rr.h, gal, len((FACD["data"] or {}).get("sistemas") or {}) if not gal else 0)
    if key not in _GALBG:
        bg = pygame.Surface(rr.size); bg.fill(BLACK)
        loc = pygame.Rect(0, 0, rr.w, rr.h)
        pt, sc = act_view(loc, gal)
        for x, z, b in gal_points():
            px, py = pt(x, z)
            if 0 <= px < rr.w and 0 <= py < rr.h:
                bg.set_at((int(px), int(py)), (b, int(b * 0.75), int(b * 0.55)))
        _GALBG[key] = bg
    real.blit(_GALBG[key], rr.topleft)

def draw_act_screen(surf, now):
    ACT["want"] = now
    surf.fill(BLACK)
    gal = int(now // 10) % 2 == 0                        # 10 s galaxia, 10 s tu zona
    put(surf, F["big"], "ACTIVIDAD GALÁCTICA", (10, 6), ORANGE)
    put(surf, F["small"], ("en directo desde EDDN" if ACT["on"] else "conectando con EDDN…" if act_ok() else "falta python3-zmq en la Pi")
        + ("  ·  GALAXIA" if gal else "  ·  TU ZONA"), (10, 32), DIM if act_ok() else RED)
    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 8, 8), ORANGE, anchor="topright")
    pygame.draw.line(surf, ORANGE, (6, 50), (W - 6, 50), 1)
    M = pygame.Rect(6, 54, 300, 262)
    act_bg(surf, M, gal)
    pygame.draw.rect(surf, DIM, M, 1, border_radius=4)
    pt, sc = act_view(M, gal)
    old = surf.get_clip(); surf.set_clip(M)
    if gal:
        for n, x, z in (("SOL", 0, 0), ("COLONIA", -9530, 19808), ("SAG A*", 25, 25900)):
            px, py = pt(x, z); pygame.draw.circle(surf, DIM, (int(px), int(py)), 3, 1)
            put(surf, F["tiny"], n, (int(px) + 5, int(py) - 6), DIM)
    else:
        used = []
        for n, v in sorted(((FACD["data"] or {}).get("sistemas") or {}).items(), key=lambda kv: -(kv[1].get("inf") or 0)):
            if v.get("pos") and None not in v["pos"] and not v.get("fuera"):
                px, py = pt(v["pos"][0], v["pos"][2])
                pygame.draw.circle(surf, ORANGE if v.get("ctrl") else (120, 80, 30), (int(px), int(py)), 3, 0 if v.get("ctrl") else 1)
                if v.get("ctrl"):
                    nm = n if len(n) <= 14 else n[:13] + "…"
                    lr = pygame.Rect(int(px) + 5, int(py) - 6, tw_(F["tiny"], nm), 12)
                    if not M.contains(lr):
                        lr.right = int(px) - 5
                    if M.contains(lr) and not any(lr.colliderect(u) for u in used):
                        used.append(lr); put(surf, F["tiny"], nm, lr.topleft, (200, 140, 60))
        px, py = pt(0, 0)
        if M.collidepoint(px, py):
            pygame.draw.circle(surf, DIM, (int(px), int(py)), 3, 1); put(surf, F["tiny"], "SOL", (int(px) + 5, int(py) - 6), DIM)
    for x, z, t, mine in list(ACT["pings"]):
        age = now - t
        if age > 1.6 or age < 0:
            continue
        px, py = pt(x, z)
        if not M.collidepoint(px, py):
            continue
        col = ORANGE if mine else (90, 200, 255)
        f_ = max(0.0, 1 - age / 1.6)
        pygame.draw.circle(surf, tuple(int(c * f_) for c in col), (int(px), int(py)), int(2 + age * 10), 1)
        if age < 0.4:
            pygame.draw.circle(surf, col, (int(px), int(py)), 2)
    surf.set_clip(old)
    X, y = 314, 58
    j = ACT["jumps"]
    pm = sum(1 for t in j if now - t < 60)
    cm = sum(1 for t in ACT["uids"].values() if now - t < 300)
    put(surf, F["small"], "SALTOS POR MINUTO", (X, y), DIM); y += 14
    put(surf, F["num"], str(pm), (W - 8, y), BLUE, anchor="topright"); y += 44
    put(surf, F["small"], "COMANDANTES (5 MIN)", (X, y), DIM); y += 14
    put(surf, F["big"], str(cm), (W - 8, y), WHITE, anchor="topright"); y += 30
    hoyk = time.strftime("%Y-%m-%d", time.gmtime())
    ent = sum(((v.get("trafico") or {}).get(hoyk, 0)) for v in ((FACD["data"] or {}).get("sistemas") or {}).values())
    put(surf, F["small"], "EN TUS SISTEMAS HOY", (X, y), DIM); put(surf, F["big"], str(ent), (W - 8, y + 10), ORANGE, anchor="topright"); y += 40
    pygame.draw.line(surf, DIM, (X, y), (W - 6, y)); y += 4
    put(surf, F["small"], "ÚLTIMOS SALTOS", (X, y), DIM); y += 15
    for nm, mine, t in list(ACT["feed"])[:6]:
        put(surf, F["tiny"], nm, (X, y), ORANGE if mine else WHITE, 120)
        put(surf, F["tiny"], f"{max(0, int(now - t))} s", (W - 8, y), DIM, anchor="topright"); y += 13

def act_enabled():
    if cfg.get("actividad") is not None:
        return cfg["actividad"]
    try:
        model = open("/proc/device-tree/model").read()
    except OSError:
        model = ""
    return "Pi 3" not in model                           # en la Pi 3 viene apagada (se puede encender en el cfg)

def draw_idle(surf, now):
    D, S, gap = fac_rows()
    modes = ["norm"] + (["fac"] if S else []) + (["act"] if act_enabled() else [])
    m = modes[int(now // 20) % len(modes)]
    IDLE_MODE.update(m=m, t=time.time())
    try:
        if m == "fac":
            draw_fac_screen(surf, now); return
        if m == "act":
            draw_act_screen(surf, now); return
    except Exception as e:
        log_exc("espera " + m, e)
    _draw_idle_b7(surf, now)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 8
- La pantalla de Caballeros de Sion ya no muestra los datos de la Pi (CPU, MHz, temperatura, RAM, FPS).
- PRUEBA: tercera pantalla de espera, ACTIVIDAD GALÁCTICA en directo. Mientras se ve, la Pi escucha EDDN y enciende un destello en cada salto que hace un comandante (naranja si es en tus sistemas). 10 s la galaxia entera y 10 s tu zona. A la derecha: saltos por minuto, comandantes activos, comandantes en tus sistemas hoy y los últimos saltos. Necesita: sudo apt install python3-zmq. En la Pi 3 viene apagada.
# Enlace energético''')
rep('    ("1.0b7", ', '    ("1.0b8", "Facción sin datos de la Pi; prueba de ACTIVIDAD GALÁCTICA en directo"),\n    ("1.0b7", ')
s = re.sub(r'PANEL_VER = "v1\.0b7[^"]*"', 'PANEL_VER = "v1.0b8 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 8  (copia en " + P + ".bak100b7)")
