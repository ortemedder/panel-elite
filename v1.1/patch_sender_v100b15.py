#!/usr/bin/env python3
# Sender v1.0 beta 15 (desde la beta 14b), para el panel v1.1.11:
# - el cuerpo donde estás: tipo, atmósfera, vulcanismo, si se puede aterrizar y señales biológicas y geológicas
# - los módulos que vende la estación (Outfitting.json) y el mercado completo (Market.json), para el diario del panel
# - RUTA EXTERNA: el CSV más nuevo de la carpeta rutas/ junto a este sender (Spansh, neutrones...)
# - células de escudo de la nave del Loadout (para el contador aproximado del panel)
import shutil, sys
P = sys.argv[1] if len(sys.argv) > 1 else "elite_sender.py"
s = open(P, encoding="utf-8").read()
if "def cuerpo_event" in s:
    sys.exit("Ya estaba aplicado")
if 'SENDER_VER = "v1.0b14b"' not in s:
    sys.exit("Este parche es para el sender v1.0b14b")
shutil.copy(P, P + ".bak100b14b")

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('''"colbuy": COLBUY, "matsall": mats,''',
    '''"colbuy": COLBUY, "matsall": mats, "cuerpo": cuerpo_pkt(st), "outfit": OUTFIT, "mktall": MKTALL, "rutaext": rutaext_pkt(), "scb": SCB,''')
rep('''HEAVY = ("matsall", "colonia",''', '''HEAVY = ("outfit", "mktall", "rutaext", "matsall", "colonia",''')

CODE = r'''
# ---------- v1.0 beta 15: cuerpo actual, módulos y mercado completos, ruta externa, células de escudo ----------
CUERPOS = {}                                             # nombre -> tipo, atmósfera, vulcanismo, señales
OUTFIT, MKTALL = {}, {}
SCB = {"n": None, "max": 0, "tlo": 0, "tref": 0}
RUTAEXT = {"f": None, "m": 0, "p": [], "t": 0.0}
RUTA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rutas")

def cuerpo_event(e):
    ev = e.get("event")
    if ev == "Scan" and e.get("BodyName") and e.get("PlanetClass"):
        c = CUERPOS.setdefault(e["BodyName"], {})
        c.update(cls=e.get("PlanetClass") or "", atm=e.get("Atmosphere") or "", atmt=e.get("AtmosphereType") or "",
                 volc=e.get("Volcanism") or "", land=bool(e.get("Landable")), grav=e.get("SurfaceGravity"),
                 temp=e.get("SurfaceTemperature"))
    elif ev in ("FSSBodySignals", "SAASignalsFound") and e.get("BodyName"):
        c = CUERPOS.setdefault(e["BodyName"], {})
        for x in e.get("Signals") or []:
            ty = x.get("Type") or ""
            if "Biological" in ty:
                c["bio"] = x.get("Count", 0)
            elif "Geological" in ty:
                c["geo"] = x.get("Count", 0)
    elif ev == "FSDJump":
        CUERPOS.clear()
    elif ev == "Outfitting":
        try:
            with open(os.path.join(DIR, "Outfitting.json"), encoding="utf-8") as f:
                o = json.load(f)
            OUTFIT.clear()
            OUTFIT.update(mid=o.get("MarketID"), st=o.get("StationName"), sys=o.get("StarSystem"),
                          t=iso2epoch(o.get("timestamp")) or time.time(),
                          items=sorted({(x.get("Name") or "").lower() for x in o.get("Items") or [] if x.get("Name")}))
        except (OSError, ValueError):
            pass
    elif ev == "Market":
        try:
            with open(os.path.join(DIR, "Market.json"), encoding="utf-8") as f:
                m = json.load(f)
            items = []
            for it in m.get("Items") or []:
                k = (it.get("Name") or "").lower().strip("$").replace("_name;", "")
                items.append([k, (it.get("Name_Localised") or k)[:26], it.get("BuyPrice", 0), it.get("SellPrice", 0),
                              it.get("MeanPrice", 0), it.get("Stock", 0), it.get("Demand", 0)])
            MKTALL.clear()
            MKTALL.update(mid=m.get("MarketID"), st=m.get("StationName"), sys=m.get("StarSystem"),
                          t=iso2epoch(m.get("timestamp")) or time.time(), items=items)
        except (OSError, ValueError):
            pass
    elif ev == "Loadout":
        n = 0; hay = False
        for md in e.get("Modules") or []:
            if "shieldcellbank" in (md.get("Item") or "").lower():
                hay = True
                n += (md.get("AmmoInClip") or 0) + (md.get("AmmoInHopper") or 0)
        SCB.update(n=n if hay else None, max=max(SCB["max"], n) if hay else 0,
                   tlo=iso2epoch(e.get("timestamp")) or time.time())
    elif ev == "BuyAmmo":
        SCB["tref"] = iso2epoch(e.get("timestamp")) or time.time()

def cuerpo_pkt(st):
    b = st.get("BodyName")
    if not b:
        return None
    return dict(CUERPOS.get(b) or {}, name=b)

def rutaext_pkt():
    """El CSV más nuevo de rutas/ (se mira cada 5 s): [nombre, neutrón, saltos] de cada parada."""
    now = time.time()
    if now - RUTAEXT["t"] < 5:
        return RUTAEXT.get("pkt")
    RUTAEXT["t"] = now
    try:
        fs = [os.path.join(RUTA_DIR, f) for f in os.listdir(RUTA_DIR) if f.lower().endswith(".csv")]
    except OSError:
        fs = []
    if not fs:
        RUTAEXT.update(f=None, p=[], pkt=None)
        return None
    f = max(fs, key=os.path.getmtime)
    m = os.path.getmtime(f)
    if f != RUTAEXT["f"] or m != RUTAEXT["m"]:
        import csv as _csv
        paradas = []
        try:
            with open(f, encoding="utf-8-sig", newline="") as fh:
                filas = list(_csv.reader(fh))
            cab = [c.strip().lower() for c in (filas[0] if filas else [])]
            ci = next((i for i, c in enumerate(cab) if "system" in c or "sistema" in c), 0)
            ni = next((i for i, c in enumerate(cab) if "neutron" in c or "neutrón" in c), None)
            ji = next((i for i, c in enumerate(cab) if c in ("jumps", "saltos")), None)
            for r in filas[1:501]:
                if len(r) > ci and r[ci].strip():
                    neu = ni is not None and len(r) > ni and r[ni].strip().lower() in ("yes", "true", "1", "si", "sí")
                    paradas.append([r[ci].strip(), neu, r[ji].strip() if ji is not None and len(r) > ji else ""])
            print(time.strftime("%H:%M:%S"), "RUTA EXTERNA:", os.path.basename(f), len(paradas), "paradas", flush=True)
        except Exception as ex:
            print("ruta externa:", ex, flush=True)
        RUTAEXT.update(f=f, m=m, p=paradas)
    RUTAEXT["pkt"] = {"f": os.path.basename(RUTAEXT["f"]), "m": RUTAEXT["m"], "p": RUTAEXT["p"]}
    return RUTAEXT["pkt"]

_handle_b15 = handle

def handle(e):
    _handle_b15(e)
    try:
        cuerpo_event(e)
    except Exception as ex:
        print("cuerpo/outfitting:", ex, flush=True)

'''
rep("_v096_load()\nprint(\"Sender\", SENDER_VER)", CODE + "_v096_load()\nprint(\"Sender\", SENDER_VER)")
rep('SENDER_VER = "v1.0b14b"', 'SENDER_VER = "v1.0b15"')
open(P, "w", encoding="utf-8").write(s)
print("OK sender v1.0 beta 15  (copia en " + P + ".bak100b14b)")
