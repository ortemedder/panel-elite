# Panel Elite v1.1 · parte 26: CACHÉ y DIARIO en la Pi (v1.1.11) · SQLite en ~/panel-v11/datos_robot/panel.db
#   CACHÉ: lo que se busca por internet se guarda en disco y vale aunque se reinicie la Pi:
#          tiendas de Spansh (1 día), sistemas de EDSM (1 semana), cuerpos de un sistema (1 mes).
#   DIARIO: cada estación donde abres el mercado o el equipamiento (sender v1.0b15) se apunta con sus precios y
#           sus módulos. El robot contesta antes y sin internet: «¿dónde venden multicañón?» (primero en tu diario),
#           «¿dónde vendo el oro?» y «¿dónde compro acero?» (las estaciones donde has estado).
import sqlite3 as _sq

DB_FILE = os.path.join(PANEL_DIR, "datos_robot", "panel.db")
DB = {"c": None, "lock": threading.Lock(), "mkt_t": None, "out_t": None, "redsm": set(), "t": 0.0}

def db():
    if DB["c"] is None:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        c = _sq.connect(DB_FILE, check_same_thread=False, timeout=10)
        c.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT, t REAL);
            CREATE TABLE IF NOT EXISTS estaciones (mid INTEGER PRIMARY KEY, nombre TEXT, sistema TEXT, x REAL, y REAL, z REAL, t REAL);
            CREATE TABLE IF NOT EXISTS mercado (mid INTEGER, clave TEXT, nombre TEXT, compra INTEGER, venta INTEGER,
                                                media INTEGER, stock INTEGER, demanda INTEGER, t REAL, PRIMARY KEY (mid, clave));
            CREATE TABLE IF NOT EXISTS modulos (mid INTEGER, item TEXT, t REAL, PRIMARY KEY (mid, item));
            CREATE INDEX IF NOT EXISTS i_merc ON mercado (clave);
            CREATE INDEX IF NOT EXISTS i_mod ON modulos (item);
        """)
        DB["c"] = c
    return DB["c"]

def cache_get(k, maxage):
    try:
        with DB["lock"]:
            r = db().execute("SELECT v, t FROM cache WHERE k=?", (k,)).fetchone()
        if r and time.time() - r[1] < maxage:
            return json.loads(r[0])
    except Exception as e:
        log_exc("caché leer", e)
    return None

def cache_put(k, v):
    try:
        with DB["lock"]:
            db().execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)", (k, json.dumps(v, ensure_ascii=False), time.time()))
            db().commit()
    except Exception as e:
        log_exc("caché guardar", e)

# --- Spansh con caché de 1 día ---
_spansh_v1111 = _spansh

def _spansh(sistema, modulo, clase=None):
    k = f"spansh:{sistema}|{modulo}|{clase or ''}"
    v = cache_get(k, 86400)
    if v is not None:
        return v
    v = _spansh_v1111(sistema, modulo, clase)
    if v is not None:
        cache_put(k, v)
    return v

# --- EDSM de los sistemas de la ruta: se guardan y se recuperan de la caché (1 semana) ---
_redsm_want_v1111 = redsm_want

def redsm_want(n):
    if n and n not in REDSM:
        v = cache_get("edsm_sys:" + n, 7 * 86400)
        if v is not None:
            REDSM[n] = v
            DB["redsm"].add(n)
            return
    return _redsm_want_v1111(n)

# --- DIARIO: mercado y módulos de cada estación ---
def diario_watch(d):
    now = time.time()
    if now - DB["t"] < 2:
        return
    DB["t"] = now
    for n, v in list(REDSM.items()):                      # lo nuevo de EDSM, a la caché
        if v is not None and n not in DB["redsm"]:
            DB["redsm"].add(n)
            cache_put("edsm_sys:" + n, v)
    m, o = d.get("mktall") or {}, d.get("outfit") or {}
    nuevo_m = bool(m.get("mid")) and m.get("t") != DB["mkt_t"]
    nuevo_o = bool(o.get("mid")) and o.get("t") != DB["out_t"]
    if not (nuevo_m or nuevo_o):                          # solo se escribe en la SD cuando hay algo nuevo
        return
    pos = d.get("starpos") or [None, None, None]
    with DB["lock"]:
        c = db()
        for x, nuevo in ((m, nuevo_m), (o, nuevo_o)):
            if nuevo:
                aqui = (x.get("sys") or "") == (d.get("system") or "")
                old = c.execute("SELECT x, y, z FROM estaciones WHERE mid=?", (x["mid"],)).fetchone()
                p = pos if aqui and pos[0] is not None else (old or (None, None, None))
                c.execute("INSERT OR REPLACE INTO estaciones VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (x["mid"], x.get("st"), x.get("sys"), p[0], p[1], p[2], x.get("t") or now))
        if nuevo_m:
            DB["mkt_t"] = m.get("t")
            c.execute("DELETE FROM mercado WHERE mid=?", (m["mid"],))
            c.executemany("INSERT OR REPLACE INTO mercado VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                          [(m["mid"], it[0], it[1], it[2], it[3], it[4], it[5], it[6], m.get("t") or now)
                           for it in m.get("items") or [] if len(it) > 6])
        if nuevo_o:
            DB["out_t"] = o.get("t")
            c.execute("DELETE FROM modulos WHERE mid=?", (o["mid"],))
            c.executemany("INSERT OR REPLACE INTO modulos VALUES (?, ?, ?)",
                          [(o["mid"], it, o.get("t") or now) for it in o.get("items") or []])
        c.commit()

def _miles(n):
    return f"{int(n or 0):,}".replace(",", ".")

def _hace(t):
    s = time.time() - (t or 0)
    return f"hace {s / 86400:.0f} días" if s > 2 * 86400 else f"hace {s / 3600:.0f} h" if s > 5400 else "hace poco"

def _dist3(p, q):
    if not p or not q or None in p or None in q:
        return None
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2) ** 0.5

# nombre en inglés de Spansh -> trozo del nombre interno del juego (Outfitting.json)
MOD_INTERNO = {"Rail Gun": "railgun", "Multi-cannon": "multicannon", "Fragment Cannon": "slugshot",
               "Plasma Accelerator": "plasmaaccelerator", "Mining Laser": "mininglaser", "Pulse Laser": "pulselaser_",
               "Burst Laser": "pulselaserburst", "Beam Laser": "beamlaser", "Seeker Missile Rack": "basicmissilerack",
               "Missile Rack": "dumbfiremissilerack", "Torpedo Pylon": "advancedtorppylon", "Mine Launcher": "minelauncher",
               "Cannon": "hpt_cannon_", "Frame Shift Drive Interdictor": "fsdinterdictor", "Frame Shift Drive": "int_hyperdrive",
               "Thrusters": "int_engine", "Power Plant": "int_powerplant", "Power Distributor": "int_powerdistributor",
               "Shield Booster": "shieldbooster", "Shield Cell Bank": "shieldcellbank", "Shield Generator": "int_shieldgenerator",
               "Fuel Scoop": "fuelscoop", "Fuel Tank": "int_fueltank", "Refinery": "refinery", "Cargo Rack": "int_cargorack",
               "Hull Reinforcement Package": "hullreinforcement", "Module Reinforcement Package": "modulereinforcement",
               "Heat Sink Launcher": "heatsinklauncher", "Chaff Launcher": "chafflauncher", "Point Defence": "plasmapointdefence",
               "Detailed Surface Scanner": "detailedsurfacescanner", "Standard Docking Computer": "dockingcomputer_standard",
               "Prospector Limpet Controller": "dronecontrol_prospector", "Collector Limpet Controller": "dronecontrol_collection",
               "Sensors": "int_sensors", "Life Support": "int_lifesupport"}

def diario_modulo(en, clase, d):
    """La estación de tu diario más cercana que vende el módulo (o None)."""
    trozo = MOD_INTERNO.get(en)
    if not trozo:
        return None
    q = "SELECT e.nombre, e.sistema, e.x, e.y, e.z, m.t, m.item FROM modulos m JOIN estaciones e ON e.mid=m.mid WHERE m.item LIKE ?"
    with DB["lock"]:
        filas = db().execute(q, ("%" + trozo + "%",)).fetchall()
    if clase:
        filas = [f for f in filas if f"size{clase}" in f[6] or (f"_{clase}_" in f[6])]
    if not filas:
        return None
    pos = d.get("starpos")
    filas.sort(key=lambda f: _dist3(pos, f[2:5]) if _dist3(pos, f[2:5]) is not None else 9e9)
    f = filas[0]
    return f[0], f[1], _dist3(pos, f[2:5]), f[5]

_r_tienda_v1111 = r_tienda

def r_tienda(d, now, t):
    mod = next(((en, es) for pals, en, es in TIENDA if any(re.search(r"\b" + re.escape(p), t) for p in pals)), None)
    if mod:
        m = re.search(r"\bclase\s*(\d|uno|dos|tres|cuatro|cinco|seis|siete|ocho)\b", t)
        clase = None
        if m:
            v = m.group(1)
            clase = int(v) if v.isdigit() else ["uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho"].index(v) + 1
        try:
            h = diario_modulo(mod[0], clase, d)
        except Exception as e:
            log_exc("diario módulo", e); h = None
        if h and (h[2] is None or h[2] < 150):
            return f"En tu diario: {mod[1]}" + (f" clase {clase}" if clase else "") + f" en {h[0]}, {h[1]}" + \
                   (f", a {h[2]:.0f} al" if h[2] and h[2] >= 1 else ", aquí" if h[2] is not None else "") + f" (visto {_hace(h[3])})"
    return _r_tienda_v1111(d, now, t)

def _mercancia(t):
    """La mercancía de la pregunta, buscando sus palabras en los nombres del diario."""
    pal = [w for w in re.findall(r"[a-z]+", t) if len(w) >= 3 and w not in
           ("donde", "vendo", "venden", "compro", "comprar", "vender", "puedo", "mejor", "precio", "pagan", "cuanto",
            "barato", "barata", "mercado", "estacion", "los", "las", "del", "una", "uno", "que", "mas", "por", "con", "consigo")]
    if not pal:
        return None
    with DB["lock"]:
        noms = [r[0] for r in db().execute("SELECT DISTINCT nombre FROM mercado").fetchall()]
    for w in pal:
        for n in noms:
            if w in _norm(n):
                return n
    return None

def r_dondevendo(d, now, t):
    n = _mercancia(t)
    if not n:
        return "No encuentro esa mercancía en tu diario: abre el mercado en las estaciones para que la apunte"
    with DB["lock"]:
        filas = db().execute("SELECT e.nombre, e.sistema, m.venta, m.media, m.t, e.x, e.y, e.z FROM mercado m JOIN estaciones e "
                             "ON e.mid=m.mid WHERE m.nombre=? AND m.venta>0 AND m.demanda>0 ORDER BY m.venta DESC LIMIT 3", (n,)).fetchall()
    if not filas:
        return f"Ninguna estación de tu diario compra {n}"
    f = filas[0]
    dd = _dist3(d.get("starpos"), f[5:8])
    return f"{n}: donde mejor te pagan es {f[0]}, {f[1]}, a {_miles(f[2])} cr" + \
           (f" ({100 * f[2] / f[3] - 100:+.0f} % de la media)" if f[3] else "") + (f", a {dd:.0f} al" if dd and dd >= 1 else ", aquí" if dd is not None else "") + \
           f", visto {_hace(f[4])}"

def r_dondecompro(d, now, t):
    n = _mercancia(t)
    if not n:
        return "No encuentro esa mercancía en tu diario"
    with DB["lock"]:
        filas = db().execute("SELECT e.nombre, e.sistema, m.compra, m.stock, m.t, e.x, e.y, e.z FROM mercado m JOIN estaciones e "
                             "ON e.mid=m.mid WHERE m.nombre=? AND m.compra>0 AND m.stock>0", (n,)).fetchall()
    if not filas:
        return f"Ninguna estación de tu diario vende {n}"
    pos = d.get("starpos")
    filas.sort(key=lambda f: (f[2], _dist3(pos, f[5:8]) or 0))
    f = filas[0]
    dd = _dist3(pos, f[5:8])
    return f"{n}: más barato en {f[0]}, {f[1]}, a {_miles(f[2])} cr, hay {_miles(f[3])} t" + \
           (f", a {dd:.0f} al" if dd and dd >= 1 else ", aquí" if dd is not None else "") + f", visto {_hace(f[4])}"

PREG_V1110[:] = [(c_, r_tienda if fn is _r_tienda_v1111 else fn) for c_, fn in PREG_V1110]   # la lista guardaba la de antes
PREG_V1110.insert(0, (lambda t: _hay(t, "donde") and _hay(t, "vendo", "vender", "pagan") and not _modulo(t), r_dondevendo))
PREG_V1110.insert(0, (lambda t: _hay(t, "donde") and _hay(t, "compro", "comprar", "consigo") and not _modulo(t)
                       and not any(re.search(r"\b" + re.escape(p), t) for pals, _, _ in TIENDA for p in pals), r_dondecompro))

_render_v1111b = render

def render(surf):
    r_ = _render_v1111b(surf)
    try:
        with lock:
            d = state["data"]
        if d:
            diario_watch(d)
    except Exception as e:
        log_exc("diario", e)
    return r_
