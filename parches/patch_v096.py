#!/usr/bin/env python3
# Parche v0.96: version del sender, foto de la nave fijada, dias sin cobrar, base de ingeniero, combustible por saltos,
# interdiccion por CMDR, mineria por hora, Powerplay de la semana, respuesta inmediata al toque y tiempos de cada pantalla.
# Va con el sender v0.96. Arranque rapido: panel_run.py (ver LEEME).
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "PANEL_PERF_V" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.95' not in s:
    sys.exit("Este parche es para la v0.95")
shutil.copy(P, P + ".bak95")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# 2. foto de la nave fijada (NPC o CMDR) por su tipo real
rep('''        tph_ = bool(cmdr and cfg.get("cmdrpics", True) and ia2_.get("ship")) and \\
            ship_photo(surf, {"ship": ia2_.get("ship")}, {}, pygame.Rect(card.right - 62, card.bottom - 34, 56, 31))''',
    '''        tph_ = bool(cfg.get("cmdrpics", True)) and \\
            ship_photo(surf, {"type": t.get("stype"), "ship": t.get("ship") or ia2_.get("ship")}, {},
                       pygame.Rect(card.right - 62, card.bottom - 34, 56, 31))''')
# 3. dias sin cobrar
rep('''        put(surf, F["small"], "SIN COBRAR (bonos + recompensas)", (8, H - 54), DIM)''',
    '''        dd_ = int((time.time() - (d or {}).get("uncl_t0")) // 86400) if (d or {}).get("uncl_t0") else 0
        put(surf, F["small"], "SIN COBRAR (bonos + recompensas)" + (f"  ·  desde hace {dd_} días" if dd_ else ""),
            (8, H - 54), ORANGE if dd_ >= 2 else DIM)''')
# 5. combustible: saltos que te quedan
rep('''    put(surf, F["small"], f"quedan {total}" + (f" · {end[0]}" if end and total > 1 else ""), (W - 8, y), DIM, 140, anchor="topright")
    return y + 22''', '''    put(surf, F["small"], f"quedan {total}" + (f" · {end[0]}" if end and total > 1 else ""), (W - 8, y), DIM, 140, anchor="topright")
    fj_, fm_ = d.get("fuelj"), (d.get("Fuel") or {}).get("FuelMain")
    if fj_ and fm_ is not None:
        n_ = int(fm_ / fj_) if fj_ > 0 else 0
        put(surf, F["small"], f"combustible para ~{n_} saltos" + ("  ·  ¡recoge en la ruta!" if n_ < min(total, 6) else ""),
            (8, y + 14), RED if n_ < 3 else ORANGE if n_ < min(total, 6) else GREEN, W - 16)
        return y + 36
    return y + 22''')
# 6. interdiccion: comandante o NPC
rep('''        set_alert("¡INTERDICCIÓN!", text, secs=4); play("alarm")''',
    '''        nm_, pl_ = ((text or "") + "|0").split("|")[:2]
        set_alert("¡INTERDICCIÓN!", (nm_ + ("  ·  ¡COMANDANTE!" if pl_ == "1" else "  ·  NPC")) if nm_ else "", secs=6 if pl_ == "1" else 4)
        play("alarm")''')
# 11. respuesta inmediata al toque
rep('''            time.sleep(0.1)''', '''            TAP_EV.wait(0.1); TAP_EV.clear()''')
# 12. tiempo de cada pantalla
rep('''            fn(surf, d if online else None, flags, now)''', '''            t_ = time.perf_counter()
            fn(surf, d if online else None, flags, now)
            perf_view(v, time.perf_counter() - t_)''')

CODE = r'''
# ---------- v0.96 ----------
import threading as _thr
PANEL_PERF_V = {}
TAP_EV = _thr.Event()
_on_tap96 = on_tap

def on_tap(x, y):
    try:
        _on_tap96(x, y)
    finally:
        TAP_EV.set()                                 # redibuja ya, sin esperar al siguiente ciclo

def perf_view(v, dt):
    a = PANEL_PERF_V.setdefault(v, [0, 0.0, 0.0])
    a[0] += 1; a[1] += dt; a[2] = max(a[2], dt)
    t0 = PANEL_PERF_V.setdefault("_t", time.time())
    if time.time() - t0 > 300:
        top = sorted(((k, x) for k, x in PANEL_PERF_V.items() if k != "_t"), key=lambda kv: -kv[1][1] / max(1, kv[1][0]))[:5]
        plog("TIEMPOS (5 min): " + "  ".join(f"{MENU.get(k, k)} {x[1] / max(1, x[0]) * 1000:.0f} ms (máx {x[2] * 1000:.0f})" for k, x in top)
             + f"  ·  CPU {PERF.get('cpu') or 0:.0f}%  ·  {PERF.get('fps') or 0:.0f} FPS")
        PANEL_PERF_V.clear(); PANEL_PERF_V["_t"] = time.time()

# 1. version del sender
VERW = {"done": False}

def ver_check(d):
    sv = (d or {}).get("sver")
    pv = PANEL_VER.split(" · ")[0][:5]
    if VERW["done"] or not d or "Flags" not in d:
        return
    VERW["done"] = True
    if (sv or "")[:5] != pv:
        k0 = XA_K[0]
        try:
            XA_K[0] = "keys"
            xa["a"] = dict(until=time.time() + 10, col=ORANGE, title="VERSIONES DISTINTAS", big=f"panel {pv} · sender {sv or 'antiguo'}",
                           lines=["pon en el PC el elite_sender.py de la misma versión"])
        finally:
            XA_K[0] = k0

_vcl0 = view_changelog

def view_changelog(surf, d, flags, now):
    _vcl0(surf, d, flags, now)
    sv = (d or {}).get("sver")
    pygame.draw.rect(surf, BLACK, (0, H - 18, W, 18))
    put(surf, F["small"], f"panel {PANEL_VER.split(' · ')[0]}  ·  sender {sv or 'antiguo (sin versión)'}", (8, H - 16),
        GREEN if (sv or '')[:5] == PANEL_VER.split(' · ')[0][:5] else ORANGE, W - 16)

VIEWS[1245] = view_changelog

# 3. aviso de dinero sin cobrar (una vez al arrancar)
UNC = {"done": False}

def uncl_watch(d, now):
    if UNC["done"] or not d:
        return
    led = ((d.get("footcz") or {}).get("led") or {})
    t0 = d.get("uncl_t0")
    if not t0 or not led.get("cr"):
        return
    UNC["done"] = True
    days = int((now - t0) // 86400)
    if days >= 2 or led["cr"] >= 50e6:
        k0 = XA_K[0]
        try:
            XA_K[0] = "redeem"
            xa["a"] = dict(until=now + 8, col=ORANGE, title="SIN COBRAR", big=f"{crx(led['cr'])} cr",
                           lines=[f"desde hace {days} días" if days else "", "si te destruyen la nave, se pierden"])
        finally:
            XA_K[0] = k0

# 7. mineria por hora
_vmin0 = view_mining

def view_mining(surf, d, flags, now):
    _vmin0(surf, d, flags, now)
    m = (d or {}).get("mining") or {}
    tons = sum((m.get("refined") or {}).values())
    if tons and m.get("t0") and m.get("t1") and m["t1"] > m["t0"]:
        h = (m["t1"] - m["t0"]) / 3600
        rate = tons / h if h > 0.02 else None
        prices = {r[0].lower(): r[1] for r in (((d or {}).get("market") or {}).get("best") or [])}
        prices.update({r[0].lower(): r[2] for r in (((d or {}).get("market") or {}).get("sell") or [])})
        val = sum(n * prices.get(k.lower(), 0) for k, n in (m.get("refined") or {}).items())
        pygame.draw.rect(surf, BLACK, (0, H - 18, W, 18))
        put(surf, F["small"], f"{tons} t refinadas" + (f"  ·  {rate:.0f} t/hora".replace(".", ",") if rate else "")
            + (f"  ·  ~{crx(val / h)} cr/hora" if val and h > 0.02 else ""), (8, H - 16), GREEN, W - 16)

VIEWS[10] = view_mining

# 8. Powerplay: meritos de la semana y corte
_vpp0 = view_pp

def view_pp(surf, d, flags, now):
    _vpp0(surf, d, flags, now)
    w = (d or {}).get("ppweek") or {}
    if not w.get("end"):
        return
    left = max(0, int(w["end"] - time.time()))
    pygame.draw.rect(surf, BLACK, (0, H - 18, W, 18))
    put(surf, F["small"], f"ESTA SEMANA: {fnum(w.get('merits', 0), 0)} méritos  ·  corte en {left // 86400} d {left % 86400 // 3600} h",
        (8, H - 16), BLUE, W - 16)

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")
# avisos de version, sin cobrar y base de ingeniero
rep('''    battle_watch(d, now)''', '''    battle_watch(d, now)
    ver_check(d)
    uncl_watch(d, now)''')
rep('''        elif kind == "shipswap":''', '''        elif kind == "engbase":
            xa["a"] = dict(until=now + 6, col=BLUE, title="BASE DE INGENIERO", big=(text or "").upper(),
                           lines=["mira tus materiales en 12 > MATERIALES"])
            if auto_on("docking"):
                ui["view"] = 125
        elif kind == "shipswap":''')
rep('''("scanned", "TE ESCANEAN"),''', '''("scanned", "TE ESCANEAN"), ("engbase", "BASE DE INGENIERO"),''')

rep('''# Enlace energético''', '''# Novedades v0.96
- AJUSTES > VERSIONES dice la versión del panel y del sender; si no coinciden, aviso al arrancar.
- Foto de la nave que fijas (NPC o comandante), por su tipo real.
- Dinero sin cobrar: desde cuántos días (RESUMEN DEL DÍA) y aviso al arrancar si son 2 días o más, o más de 50 M.
- Base de ingeniero: aviso al atracar y salta a MATERIALES.
- NAVEGACIÓN: «combustible para ~N saltos» (rojo si quedan menos de 3).
- Interdicción: dice si es COMANDANTE o NPC.
- MINERÍA: toneladas por hora y créditos por hora aproximados. POWERPLAY: méritos de esta semana y cuánto falta para el corte (jueves 9:00).
- Al tocar, el panel responde al momento. Cada 5 minutos apunta en el LOG qué pantallas tardan más en dibujarse.
# Enlace energético''')
rep('    ("0.95", "Bajas a pie / nave, registro de combate en la mega nave y nave de investigación"),\n',
    '    ("0.95", "Bajas a pie / nave, registro de combate en la mega nave y nave de investigación"),\n'
    '    ("0.96", "Versión del sender, foto del objetivo, sin cobrar, ingenieros, combustible, minería, Powerplay y rapidez"),\n')
s = re.sub(r'PANEL_VER = "v0\.95[^"]*"', 'PANEL_VER = "v0.96 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.96  (copia en " + P + ".bak95)")
