# Panel Elite v1.1 · parte 22: preguntas nuevas al ROBOT (v1.1.10)
#   INGENIEROS: los que tienes desbloqueados, quién mejora un módulo (grado, si lo tienes y a qué distancia),
#               y cómo vas con uno concreto.
#   PLANOS:     qué materiales te faltan para un plano y grado (recetas de Coriolis: EDCD/coriolis-data,
#               se descargan en la Pi la primera vez). Necesita el sender v1.0b14 (manda todos los materiales).
#   TIENDAS:    dónde venden cerca un arma o un módulo (búsqueda en Spansh; necesita internet).
#   Y además:   sistema, cuerpos valiosos, biología, valor de la carga aquí, construcción, objetivo fijado,
#               minería, amigos conectados, objetivo de comunidad, GALNET, rangos y portanaves.
import urllib.request as _ur, urllib.parse as _up, difflib as _dl, csv as _csv, io as _io

RDIR = os.path.join(PANEL_DIR, "datos_robot")
RDATA = {"bp": None, "mods": None, "mat": None, "coords": None, "lock": threading.Lock(), "err": ""}
_CORIOLIS = "https://raw.githubusercontent.com/EDCD/coriolis-data/master/modifications/"
_FDEV_MAT = "https://raw.githubusercontent.com/EDCD/FDevIDs/master/material.csv"

def _bajar(url, fich, dias=30, data=None, cab=None):
    """Descarga (y guarda en datos_robot/) o usa la copia si tiene menos de 'dias'."""
    ruta = os.path.join(RDIR, fich)
    try:
        if os.path.exists(ruta) and time.time() - os.path.getmtime(ruta) < dias * 86400:
            with open(ruta, "rb") as fh:
                return fh.read()
    except OSError:
        pass
    try:
        req = _ur.Request(url, data=data, headers=dict({"User-Agent": "PanelEliteRPi/1.1"}, **(cab or {})))
        with _ur.urlopen(req, timeout=20) as r_:
            b = r_.read()
        os.makedirs(RDIR, exist_ok=True)
        with open(ruta + ".tmp", "wb") as fh:
            fh.write(b)
        os.replace(ruta + ".tmp", ruta)
        return b
    except Exception as e:
        RDATA["err"] = str(e)[:60]
        log_exc("robot datos " + fich, e)
        try:                                              # sin internet: la copia vieja vale
            with open(ruta, "rb") as fh:
                return fh.read()
        except OSError:
            return None

def recetas():
    """(blueprints, modules, nombre inglés del material -> id) de Coriolis/FDevIDs."""
    with RDATA["lock"]:
        if RDATA["bp"] is None and time.time() - RDATA.get("bp_t", 0) > 600:
            RDATA["bp_t"] = time.time()                  # sin internet: no se reintenta en cada pregunta
            b, m, c = _bajar(_CORIOLIS + "blueprints.json", "blueprints.json"), _bajar(_CORIOLIS + "modules.json", "modules.json"), \
                _bajar(_FDEV_MAT, "material.csv")
            if b and m and c:
                RDATA["bp"], RDATA["mods"] = json.loads(b), json.loads(m)
                RDATA["mat"] = {r["name"].strip().lower(): r["symbol"].strip().lower()
                                for r in _csv.DictReader(_io.StringIO(c.decode("utf-8")))}
    return RDATA["bp"], RDATA["mods"], RDATA["mat"]

def _eng_coords():
    """Coordenadas de los sistemas de los ingenieros (EDSM, una sola consulta, guardada 90 días)."""
    if RDATA["coords"] is None or (not RDATA["coords"] and time.time() - RDATA.get("coords_t", 0) > 600):
        RDATA["coords_t"] = time.time()                  # si falló, se reintenta a los 10 min
        nombres = sorted({e["system"] for e in eng_table().values() if e.get("system")})
        q = "&".join("systemName[]=" + _up.quote(n) for n in nombres) + "&showCoordinates=1"
        b = _bajar("https://www.edsm.net/api-v1/systems?" + q, "ingenieros_coords.json", dias=90)
        try:
            RDATA["coords"] = {s["name"].lower(): s["coords"] for s in json.loads(b or b"[]") if s.get("coords")}
        except Exception:
            RDATA["coords"] = {}
    return RDATA["coords"]

def _dist(d, sistema):
    p = d.get("starpos")
    c = _eng_coords().get((sistema or "").lower())
    if not p or not c:
        return None
    return ((p[0] - c["x"]) ** 2 + (p[1] - c["y"]) ** 2 + (p[2] - c["z"]) ** 2) ** 0.5

def _grado(t):
    m = re.search(r"\b(?:grado|nivel|g)\s*(\d|uno|dos|tres|cuatro|cinco)\b", t)
    if not m:
        return 5
    v = m.group(1)
    return int(v) if v.isdigit() else ["uno", "dos", "tres", "cuatro", "cinco"].index(v) + 1

# ---------- módulos: (palabras, prefijo de los planos, nombre, nombre en ingenieros.json) ----------
# el orden importa: lo más concreto primero («refuerzo de casco» antes que «casco»)
MODS_V = [
    (("interdictor",), "FSDinterdictor_", "interdictor FSD", "Interdictor FSD"),
    (("fsd", "distorsion", "motor de salto"), "FSD_", "FSD", "FSD"),
    (("propulsor", "motores"), "Engine_", "propulsores", "Propulsores"),
    (("planta",), "PowerPlant_", "planta de energía", "Planta de energía"),
    (("distribuidor",), "PowerDistributor_", "distribuidor de energía", "Distribuidor de energía"),
    (("potenciador", "booster"), "ShieldBooster_", "potenciador de escudo", "Potenciador de escudo"),
    (("celula",), "ShieldCellBank_", "banco de células", "Banco de células de escudo"),
    (("refuerzo de casco", "refuerzo del casco"), "HullReinforcement_", "refuerzo de casco", "Refuerzo de casco"),
    (("refuerzo de modulo",), None, "refuerzo de módulos", "Refuerzo de módulos"),
    (("generador", "escudo"), "ShieldGenerator_", "generador de escudo", "Generador de escudo"),
    (("blindaje", "armadura", "casco"), "Armour_", "blindaje", "Blindaje"),
    (("sensor",), "Sensor_", "sensores", "Sensores"),
    (("soporte vital",), "LifeSupport_", "soporte vital", "Soporte vital"),
    (("recogedor",), "FuelScoop_", "recogedor de combustible", "Recogedor de combustible"),
    (("refineria",), "Refineries_", "refinería", "Refinería"),
    (("bodega",), "CargoRack_", "bodega", "Bodega"),
    (("multicanon",), "Weapon_", "multicañón", "Multicañón"),
    (("canon de riel", "riel", "rail"), "Weapon_", "cañón de riel", "Cañón de riel"),
    (("fragment", "escopeta"), "Weapon_", "cañón de fragmentación", "Cañón de fragmentación"),
    (("plasma",), "Weapon_", "acelerador de plasma", "Acelerador de plasma"),
    (("pulso",), "Weapon_", "láser de pulsos", "Láser de pulsos"),
    (("rafaga",), "Weapon_", "láser de ráfaga", "Láser de ráfaga"),
    (("laser de haz", "haz"), "Weapon_", "láser de haz", "Láser de haz"),
    (("buscador",), "Weapon_", "misiles buscadores", "Misiles buscadores"),
    (("misil",), "Weapon_", "lanzamisiles", "Lanzamisiles"),
    (("torpedo",), "Weapon_", "torpedos", "Torpedos"),
    (("mina",), "Weapon_", "lanzaminas", "Lanzaminas"),
    (("canon",), "Weapon_", "cañón", "Cañón"),
    (("arma", "laser"), "Weapon_", "armas", None),
]

def _modulo(t):
    for pals, pre, nom, ing in MODS_V:
        if any(re.search(r"\b" + re.escape(p), t) for p in pals):
            return pre, nom, ing
    return None

# ---------- planos: palabra dicha -> sufijos del plano en Coriolis, y su nombre en español ----------
BP_PAL = [("largo alcance", ["LongRange"]), ("alcance", ["LongRange"]), ("arranque", ["FastBoot"]), ("fuego rapido", ["RapidFire"]),
          ("escaneo rapido", ["FastScan"]), ("rapid", ["FastBoot", "RapidFire", "FastScan", "Rapid"]), ("sucio", ["Dirty"]),
          ("limpio", ["Tuned"]), ("servicio pesado", ["HeavyDuty"]), ("pesad", ["HeavyDuty"]), ("reforzad", ["Reinforced", "HeavyDuty"]),
          ("blindad", ["Shielded", "Armoured"]), ("protegid", ["Shielded"]), ("ligero", ["LightWeight", "Advanced"]),
          ("sobrecarg", ["Overcharged"]), ("sobrealiment", ["Boosted"]), ("potenciad", ["Boosted"]),
          ("alta capacidad", ["HighCapacity"]), ("capacidad", ["HighCapacity", "IncreasedCapacity"]), ("municion", ["HighCapacity"]),
          ("frecuencia", ["HighFrequency"]), ("eficien", ["Efficient"]), ("enfoc", ["Focused"]), ("cinetic", ["Kinetic"]),
          ("termic", ["Thermic"]), ("explosiv", ["Explosive"]), ("resistiv", ["Resistive"]), ("optimiz", ["Optimised"]),
          ("sigil", ["Stealth"]), ("emision", ["Stealth"]), ("doble", ["DoubleShot"]), ("corto", ["ShortRange"]),
          ("robust", ["Sturdy"]), ("ampliad", ["Expanded"]), ("expandid", ["Expanded"]), ("angular", ["WideAngle"]),
          ("especializ", ["Specialised"]), ("prioridad", ["PriorityEngines", "PrioritySystems", "PriorityWeapons"])]
BP_ES = {"LongRange": "largo alcance", "FastBoot": "arranque rápido", "Dirty": "ajuste sucio", "Tuned": "ajuste limpio",
         "Reinforced": "reforzado", "Shielded": "blindado", "LightWeight": "ligero", "Advanced": "ligero", "Overcharged": "sobrecargado",
         "Boosted": "sobrealimentado", "HighCapacity": "alta capacidad", "IncreasedCapacity": "más capacidad",
         "HighFrequency": "alta frecuencia", "Efficient": "eficiente", "Focused": "enfocado", "HeavyDuty": "servicio pesado",
         "Kinetic": "resistente cinético", "Thermic": "resistente térmico", "Explosive": "resistente a explosivos",
         "Resistive": "resistivo", "Optimised": "optimizado", "Stealth": "baja emisión", "Armoured": "blindada",
         "DoubleShot": "doble disparo", "ShortRange": "corto alcance", "Sturdy": "robusto", "RapidFire": "fuego rápido",
         "Expanded": "ampliado", "WideAngle": "gran angular", "FastScan": "escaneo rápido", "Rapid": "carga rápida",
         "Specialised": "especializado", "PriorityEngines": "prioridad motores", "PrioritySystems": "prioridad sistemas",
         "PriorityWeapons": "prioridad armas", "Expanded_": "ampliado"}

def _bp_es(fd):
    return BP_ES.get(fd.split("_", 1)[-1], fd.split("_", 1)[-1].lower())

def r_plano(d, now, t):
    mo = _modulo(t)
    if not mo or not mo[0]:
        return "Dime el módulo y el plano, por ejemplo: FSD largo alcance grado 5"
    pre, nom, _ = mo
    bp, mods, mat = recetas()
    if not bp:
        return "No tengo las recetas de los planos: hace falta internet en la Pi la primera vez"
    cands = [k for k in bp if k.startswith(pre)]
    elegido = None
    for pal, sufs in BP_PAL:
        if pal in t:
            elegido = next((k for s_ in sufs for k in cands if k == pre + s_), None)
            if elegido:
                break
    if not elegido:
        return f"Para {nom} hay: " + ", ".join(_bp_es(k) for k in cands[:6]) + ". Dime cuál y el grado"
    g = min(_grado(t), max(int(x) for x in bp[elegido]["grades"]))
    comp = bp[elegido]["grades"][str(g)]["components"]
    tengo = (d.get("matsall") or {})
    falta, n_ = [], 10 ** 9
    for en, need in comp.items():
        sid = mat.get(en.strip().lower(), "")
        loc, have = (tengo.get(sid) or [en, 0])[:2]
        n_ = min(n_, have // need)
        if have < need:
            falta.append(f"{loc} ({have} de {need})")
    t_ = f"{nom} {_bp_es(elegido)} G{g}: "
    if not d.get("matsall"):
        t_ += "pide " + ", ".join(f"{c} {en}" for en, c in comp.items()) + " (actualiza el sender a v1.0b14 para ver lo que tienes)"
    elif falta:
        t_ += "te falta " + ", ".join(falta)
    else:
        t_ += f"tienes material para {n_} intento{'s' if n_ != 1 else ''}"
    ings = []
    for mk, mv in (mods or {}).items():
        b_ = (mv.get("blueprints") or {}).get(elegido)
        if b_:
            ings = (b_.get("grades") or {}).get(str(g), {}).get("engineers") or []
            break
    if ings:
        prog = d.get("engprog") or {}
        ok = [e for e in ings if (prog.get(e.lower()) or [""])[0] == "Unlocked"]
        L_ = (ok or ings)[:2]
        t_ += (". Lo hacen " if len(L_) > 1 else ". Lo hace ") + " y ".join(L_) + \
              ((" (desbloqueados)" if len(L_) > 1 else " (desbloqueado)") if ok else "")
    return t_

# ---------- ingenieros ----------
def _eng_estado(e, d):
    p = (d.get("engprog") or {}).get(e["name"].lower())
    if not p:
        return "no le conoces", 3
    prog, rank = p
    if prog == "Unlocked":
        return (f"rango {rank}" if rank is not None else "desbloqueado"), 0
    return ENG_PROG.get(prog, (prog or "?").lower()), 1 if prog in ("Invited", "Acquainted") else 2

def _eng_nombre(t):
    tabla = list(eng_table().values())
    palabras = [w for w in re.findall(r"[a-z]+", t) if len(w) >= 4]
    claves = {}
    for e in tabla:
        for w in re.findall(r"[a-z]+", _norm(e["name"])):
            if len(w) >= 4 and w not in ("colonel", "professor", "blaster", "the"):
                claves.setdefault(w, e)
    for w in palabras:
        m = _dl.get_close_matches(w, list(claves), n=1, cutoff=0.78)
        if m:
            return claves[m[0]]
    return None

def r_ingenieros(d, now, t):
    tabla = list(eng_table().values())
    if not tabla:
        return "No tengo la lista de ingenieros"
    mo = _modulo(t)
    if mo and mo[2]:
        lab = _norm(mo[2])
        hay = []
        for e in tabla:
            for m in e.get("mods") or []:
                g_, _, nm = m.partition(" ")
                if g_[:1] == "G" and _norm(nm) == lab:
                    est, pri = _eng_estado(e, d)
                    hay.append((pri, -int(g_[1:]), _dist(d, e.get("system")) or 9e9, e, int(g_[1:]), est))
        if not hay:
            return f"Ningún ingeniero de la lista mejora {mo[1]}"
        hay.sort(key=lambda x: x[:3])
        partes = []
        for pri, _, dist_, e, g_, est in hay[:3]:
            partes.append(f"{e['name']} G{g_}, {est}" + (f", a {dist_:.0f} al" if dist_ < 9e8 else ""))
        return f"Mejoran {mo[1]}: " + "; ".join(partes)
    e = _eng_nombre(t)
    if e:
        est, _ = _eng_estado(e, d)
        dist_ = _dist(d, e.get("system"))
        return f"{e['name']}: {est}. Está en {e.get('system')}, base {e.get('base')}" + (f", a {dist_:.0f} al" if dist_ else "")
    prog = d.get("engprog") or {}
    ok = [e["name"] for e in tabla if (prog.get(e["name"].lower()) or [""])[0] == "Unlocked"]
    if not prog:
        return "Aún no sé tu progreso con los ingenieros: se sabe al cargar la partida"
    return f"Tienes {len(ok)} de {len(tabla)} ingenieros desbloqueados" + (": " + ", ".join(ok[:5]) + ("…" if len(ok) > 5 else "") if ok else "")

# ---------- dónde venden un módulo (Spansh) ----------
TIENDA = [(("canon de riel", "riel", "rail"), "Rail Gun", "cañón de riel"), (("multicanon",), "Multi-cannon", "multicañón"),
          (("fragment", "escopeta"), "Fragment Cannon", "cañón de fragmentación"), (("plasma",), "Plasma Accelerator", "acelerador de plasma"),
          (("laser de mineria", "mineria"), "Mining Laser", "láser de minería"), (("pulso",), "Pulse Laser", "láser de pulsos"),
          (("rafaga",), "Burst Laser", "láser de ráfaga"), (("haz",), "Beam Laser", "láser de haz"),
          (("buscador",), "Seeker Missile Rack", "misiles buscadores"), (("misil",), "Missile Rack", "lanzamisiles"),
          (("torpedo",), "Torpedo Pylon", "torpedos"), (("mina",), "Mine Launcher", "lanzaminas"), (("canon",), "Cannon", "cañón"),
          (("interdictor",), "Frame Shift Drive Interdictor", "interdictor FSD"),
          (("fsd", "distorsion", "motor de salto"), "Frame Shift Drive", "FSD"), (("propulsor", "motores"), "Thrusters", "propulsores"),
          (("planta",), "Power Plant", "planta de energía"), (("distribuidor",), "Power Distributor", "distribuidor de energía"),
          (("potenciador", "booster"), "Shield Booster", "potenciador de escudo"), (("celula",), "Shield Cell Bank", "banco de células"),
          (("generador", "escudo"), "Shield Generator", "generador de escudo"), (("recogedor",), "Fuel Scoop", "recogedor de combustible"),
          (("tanque",), "Fuel Tank", "tanque de combustible"), (("refineria",), "Refinery", "refinería"), (("bodega",), "Cargo Rack", "bodega"),
          (("refuerzo de casco", "refuerzo del casco"), "Hull Reinforcement Package", "refuerzo de casco"),
          (("refuerzo de modulo",), "Module Reinforcement Package", "refuerzo de módulos"),
          (("disipador",), "Heat Sink Launcher", "lanzador de disipadores"), (("chaff",), "Chaff Launcher", "lanzador de chaff"),
          (("defensa puntual",), "Point Defence", "defensa puntual"), (("escaner de superficie", "sonda"), "Detailed Surface Scanner", "escáner de superficie"),
          (("ordenador de atraque",), "Standard Docking Computer", "ordenador de atraque"),
          (("prospector",), "Prospector Limpet Controller", "drones prospectores"), (("recolector",), "Collector Limpet Controller", "drones recolectores"),
          (("sensor",), "Sensors", "sensores"), (("soporte vital",), "Life Support", "soporte vital")]

def _spansh(sistema, modulo, clase=None):
    """Estaciones más cercanas que venden 'modulo'. Prueba los dos formatos de filtro que usa Spansh."""
    filtro = {"name": [modulo]}
    if clase:
        filtro["class"] = [str(clase)]
    for mods in ([filtro], {"value": [filtro]}):
        cuerpo = json.dumps({"filters": {"modules": mods}, "sort": [{"distance": {"direction": "asc"}}],
                             "size": 3, "page": 0, "reference_system": sistema}).encode()
        try:
            req = _ur.Request("https://spansh.co.uk/api/stations/search", data=cuerpo,
                              headers={"User-Agent": "PanelEliteRPi/1.1", "Content-Type": "application/json"})
            with _ur.urlopen(req, timeout=12) as r_:
                j = json.loads(r_.read().decode("utf-8") or "{}")
            res = j.get("results")
            if isinstance(res, list):
                return res
            plog(f"Spansh: respuesta sin resultados: {str(j)[:200]}")
        except Exception as e:
            plog(f"Spansh: {str(e)[:120]}")
    return None

def r_tienda(d, now, t):
    sy = d.get("system")
    mod = next(((en, es) for pals, en, es in TIENDA if any(re.search(r"\b" + re.escape(p), t) for p in pals)), None)
    if not mod:
        return "¿Qué módulo buscas? Por ejemplo: dónde venden multicañón"
    if not sy:
        return "No sé en qué sistema estamos"
    m = re.search(r"\bclase\s*(\d|uno|dos|tres|cuatro|cinco|seis|siete|ocho)\b", t)
    clase = None
    if m:
        v = m.group(1)
        clase = int(v) if v.isdigit() else ["uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho"].index(v) + 1
    res = _spansh(sy, mod[0], clase)
    if res is None:
        return "Spansh no responde ahora mismo"
    if not res:
        return f"No encuentro {mod[1]}" + (f" clase {clase}" if clase else "") + " cerca"
    a = res[0]
    t_ = f"{mod[1].capitalize()}" + (f" clase {clase}" if clase else "") + \
         f": {a.get('name', '?')} en {a.get('system_name', '?')}, a {float(a.get('distance') or 0):.0f} al"
    if a.get("distance_to_arrival") is not None:
        t_ += f" y {float(a['distance_to_arrival']):.0f} ls"
    if len(res) > 1:
        b = res[1]
        t_ += f". También {b.get('name', '?')} en {b.get('system_name', '?')}"
    return t_

# ---------- el resto de preguntas del juego ----------
_cr_v119 = _cr

def _cr(v):
    v = float(v or 0)
    if abs(v) >= 1e9:
        return f"{v / 1e9:.1f} mil millones de cr".replace(".", ",")
    return _cr_v119(v)

CLS_ES = {"earthlike body": "tipo Tierra", "water world": "mundo de agua", "ammonia world": "mundo de amoníaco",
          "high metal content body": "alto contenido metálico", "metal rich body": "rico en metales"}

def r_sistema(d, now, t):
    s_ = d.get("sysinfo") or {}
    if not s_:
        return "No tengo datos del sistema"
    bits = [f"{d.get('system') or 'Este sistema'}: controla {s_.get('faction') or '?'}"]
    if s_.get("fstate"):
        bits.append(s_["fstate"].lower())
    bits.append(f"seguridad {(s_.get('sec') or '?').lower()}")
    if s_.get("econ"):
        bits.append(f"economía {s_['econ'].lower()}")
    bits.append(f"{s_['pop']:,} habitantes".replace(",", ".") if s_.get("pop") else "deshabitado")
    if s_.get("pp"):
        bits.append(f"Powerplay: {s_['pp']}")
    return ", ".join(bits)

def r_cuerpos(d, now, t):
    ex = d.get("explo") or {}
    top = [b for b in ex.get("top") or [] if len(b) > 5]
    if not top:
        return "No hay cuerpos escaneados en este sistema"
    top.sort(key=lambda b: -(b[5] or 0))
    out = []
    for b in top[:2]:
        cls = CLS_ES.get(str(b[1]).lower(), b[1] or "")
        out.append(f"{b[0]} ({cls}, unos {_cr(b[5])}" + (", sin cartografiar" if not b[4] else "") + (", primer descubrimiento" if b[3] else "") + ")")
    tot = ex.get("total")
    return f"Escaneados {ex.get('scanned', 0)}" + (f" de {tot}" if tot else "") + ". Lo más valioso: " + "; ".join(out)

def r_bio(d, now, t):
    b = d.get("bio") or {}
    if not b.get("body"):
        return "No estamos en un planeta"
    sig = b.get("signals")
    gen, hecho = b.get("genuses") or [], set(b.get("done") or [])
    if not sig and not gen:
        return f"En {b['body']} no hay señales biológicas"
    falta = [g for g in gen if g not in hecho]
    t_ = f"En {b['body']} hay {sig if sig is not None else len(gen)} señales biológicas"
    if gen:
        t_ += (". Te faltan: " + ", ".join(falta[:4])) if falta else ". Ya las tienes todas"
    if b.get("species"):
        t_ += f". Muestreando {b['species']}, paso {b.get('step') or 0} de 3"
    return t_

def r_valor_carga(d, now, t):
    m = d.get("market") or {}
    rows = m.get("sell") or []
    if not rows:
        return "Aquí no sé lo que te dan por la carga: abre el mercado"
    tot = sum(r[1] * r[2] for r in rows)
    medio = sum(r[1] * r[3] for r in rows if len(r) > 3 and r[3])
    t_ = f"En {m.get('station') or 'esta estación'} te dan {_cr(tot)} por la carga"
    if medio:
        t_ += f", un {100 * tot / medio:.0f} % del precio medio"
    return t_

def r_construccion(d, now, t):
    C = d.get("colonia") or {}
    L = [x for x in C.get("list") or [] if not x.get("done") and not x.get("fail")]
    if not L:
        return "No hay ninguna construcción en marcha"
    x = L[0]
    falta = sorted(((r[1] - r[2], r[0]) for r in x.get("res") or [] if len(r) > 2 and r[1] - r[2] > 0), reverse=True)
    tot = sum(f for f, _ in falta)
    t_ = f"{x.get('st') or 'Construcción'} en {x.get('sys') or '?'}: {x.get('prog', 0):.0f} %"
    if falta:
        t_ += f". Faltan {tot:,} t".replace(",", ".") + ", sobre todo " + ", ".join(f"{f:,} de {n}".replace(",", ".") for f, n in falta[:2])
    return t_

LEGAL_ES = {"Clean": "limpio", "Wanted": "buscado", "Enemy": "enemigo", "WantedEnemy": "buscado y enemigo",
            "Lawless": "sin ley", "Hunter": "cazador", "Allied": "aliado", "Warrant": "con orden de busca"}

def r_objetivo(d, now, t):
    tg = d.get("target")
    if not tg:
        return "No hay ninguna nave fijada"
    t_ = f"{tg.get('ship') or 'Nave'}"
    if tg.get("pilot"):
        t_ += f", piloto {tg['pilot']}"
    if tg.get("rank"):
        t_ += f", {tg['rank']}"
    if tg.get("legal"):
        t_ += ", " + LEGAL_ES.get(tg["legal"], tg["legal"])
    if tg.get("bounty"):
        t_ += f", recompensa {_cr(tg['bounty'])}"
    if tg.get("hull") is not None:
        t_ += f". Casco {tg['hull']:.0f} %" + (f", escudos {tg['shield']:.0f} %" if tg.get("shield") is not None else "")
    return t_

def r_mineria(d, now, t):
    mi = d.get("mining") or {}
    ref = mi.get("refined") or {}
    if not ref:
        return "Aún no has refinado nada"
    tot = sum(ref.values())
    top = sorted(ref.items(), key=lambda x: -x[1])[:3]
    return f"Has refinado {tot} t: " + ", ".join(f"{c} de {n}" for n, c in top) + \
           (f". Quedan {mi['limpets']} drones" if mi.get("limpets") is not None else "")

def r_amigos(d, now, t):
    f = d.get("friends") or {}
    on = f.get("on") or []
    if not on:
        return "No hay ningún amigo conectado"
    return f"Conectado{'s' if len(on) > 1 else ''}: " + ", ".join(on[:5]) + ("…" if len(on) > 5 else "")

def r_cg(d, now, t):
    L = d.get("mycg") or []
    if not L:
        return "No estás en ningún objetivo de comunidad"
    g = L[0]
    t_ = f"{g.get('title')}: {g.get('tier') or 'sin nivel'}"
    if g.get("mine"):
        t_ += f", tu aporte {g['mine']:,}".replace(",", ".")
    if g.get("band"):
        t_ += f", estás en el {g['band']} % mejor"
    return t_

def r_galnet(d, now, t):
    L = galnet.get("list") or []
    if not L:
        return "No tengo noticias de GALNET"
    return f"GALNET, {L[0].get('date', '')}: {L[0].get('title', '')}"

def r_rangos(d, now, t):
    r = d.get("ranks") or {}
    rk, pr = r.get("rank") or {}, r.get("progress") or {}
    if not rk:
        return "No sé tus rangos todavía"
    filas = []
    for lab, key in RANK_ROWS[:5]:
        n = rk.get(key)
        if n is None or n >= 8:                          # ya es Elite: no sale
            continue
        filas.append((-(pr.get(key) or 0), lab.lower(), rank_name(key, n), pr.get(key) or 0))
    filas.sort()
    return "Más cerca de subir: " + "; ".join(f"{l} {n}, {p} %" for _, l, n, p in filas[:3])

def r_portanaves(d, now, t):
    c = d.get("carrier") or {}
    if not c.get("id"):
        return "No tengo datos de tu portanaves"
    t_ = f"Tu portanaves está en {c.get('system') or '?'}"
    if c.get("fuel") is not None:
        t_ += f", tritio {c['fuel']} t"
    if c.get("balance") is not None:
        t_ += f", saldo {_cr(c['balance'])}"
    if c.get("dest"):
        t_ += f". Saltando a {c['dest']}"
    return t_

# ---------- quién contesta: lo nuevo va antes que las preguntas de la v1.1.9 ----------
def _hay(t, *pals):
    return any(re.search(r"\b" + re.escape(p), t) for p in pals)

PREG_V1110 = [
    (lambda t: (_hay(t, "quien mejora", "quien hace", "quien modifica", "quien sube") and _modulo(t)) or _hay(t, "ingenier") or (_hay(t, "como voy con", "como va con") and _eng_nombre(t)), r_ingenieros),
    (lambda t: _hay(t, "plano", "receta", "material") or (_hay(t, "grado") and _modulo(t)), r_plano),
    (lambda t: _hay(t, "donde") and _hay(t, "venden", "vende", "compro", "comprar", "consigo", "encuentro"), r_tienda),
    (lambda t: _hay(t, "comunidad"), r_cg),
    (lambda t: _hay(t, "objetivo", "fijad", "enemigo"), r_objetivo),
    (lambda t: _hay(t, "construccion", "colonia", "colonizacion"), r_construccion),
    (lambda t: _hay(t, "cuanto vale", "me dan", "precio", "cuanto pagan"), r_valor_carga),
    (lambda t: _hay(t, "controla", "seguridad", "poblacion", "economia", "gobierno", "este sistema", "que sistema"), r_sistema),
    (lambda t: _hay(t, "valios", "terraform", "cuerpo", "escanead", "planetas"), r_cuerpos),
    (lambda t: _hay(t, "biolog", "muestra", "organic", "exobio", "especie") and not _hay(t, "sin vender"), r_bio),
    (lambda t: _hay(t, "miner", "minado", "refinad"), r_mineria),
    (lambda t: _hay(t, "amigo", "conectad"), r_amigos),
    (lambda t: _hay(t, "galnet", "noticia"), r_galnet),
    (lambda t: _hay(t, "rango", "ascenso", "subir de"), r_rangos),
    (lambda t: _hay(t, "portanaves", "carrier"), r_portanaves),
]

_oido_respuesta_v119 = oido_respuesta

def oido_respuesta(texto):
    t = _norm(texto)
    if t:
        for cond, fn in PREG_V1110:
            try:
                if cond(t):
                    with lock:
                        d = state.get("data") or {}
                    return fn(d, time.time(), t), "ok"
            except Exception as e:
                log_exc("oido " + fn.__name__, e)
                return "Uy, no he podido mirarlo", "nada"
    return _oido_respuesta_v119(texto)

# la ayuda cuenta también lo nuevo
def r_ayuda(d, now):
    return ("Pregúntame por combustible, ruta, dónde estamos, tick, facción, dinero, misiones, carga, hora, "
            "ingenieros, planos, dónde venden un módulo, el sistema, biología, construcción, objetivo, rangos o GALNET")

OIDO_PREG[:] = [(p, r_ayuda if fn.__name__ == "r_ayuda" else fn) for p, fn in OIDO_PREG]
# «biología» ya no va a «datos sin vender» (salvo que digas «sin vender»)
OIDO_PREG[:] = [(tuple(x for x in p if x != "biologia"), fn) for p, fn in OIDO_PREG]

# las recetas y las coordenadas se bajan en segundo plano al arrancar (si hay internet)
def _robot_datos_bg():
    time.sleep(60)
    try:
        if cfg.get("stackchan"):
            recetas(); _eng_coords()
    except Exception as e:
        log_exc("robot datos", e)

threading.Thread(target=_robot_datos_bg, daemon=True, name="robot-datos").start()
