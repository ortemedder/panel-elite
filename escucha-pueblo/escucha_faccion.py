#!/usr/bin/env python3
# Escucha de EDDN para el Panel Elite: guarda el estado de una faccion en todos sus sistemas
# y lo ofrece en la red de casa en http://<IP>:8090/faccion.json
# - EDDN en directo (solo galaxia actual, no Legacy)
# - EDSM cada 6 h para los sistemas de los que no llega nada
# Configuracion: config.json junto a este archivo.
import base64, calendar, hashlib, json, os, threading, time, urllib.error, urllib.request, urllib.parse, zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = {"faccion": "Caballeros de Sion", "puerto": 8090, "edsm_horas": 6, "github": "ortemedder/cdsn-datos",
       "github_min": 15, "resumen_hora": 21}
try:
    with open(os.path.join(HERE, "config.json"), encoding="utf-8") as f:
        CFG.update(json.load(f))
except (OSError, ValueError):
    pass
FAC = CFG["faccion"]
DATA_FILE = os.path.join(HERE, "faccion.json")
SYS_FILE = os.path.join(HERE, "sistemas.txt")
lock = threading.Lock()
DB = {"faccion": FAC, "sistemas": {}, "eddn": {"ok": False, "ultimo": 0, "msgs": 0, "mios": 0}, "t": 0}
dirty = [False]

def log(*a):
    print(time.strftime("%d/%m %H:%M:%S"), *a, flush=True)

def load():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            j = json.load(f)
        if j.get("faccion") == FAC:
            DB["sistemas"] = j.get("sistemas") or {}
    except (OSError, ValueError):
        pass
    try:
        with open(SYS_FILE, encoding="utf-8") as f:
            for l in f:
                n = l.strip()
                if n and not n.startswith("#") and n not in DB["sistemas"]:
                    DB["sistemas"][n] = {"sys": n, "t": 0}
    except OSError:
        pass

def save():
    with lock:
        DB["t"] = time.time()
        txt = json.dumps(DB, ensure_ascii=False, separators=(",", ":"))
        dirty[0] = False
    with open(DATA_FILE + ".tmp", "w", encoding="utf-8") as f:
        f.write(txt)
    os.replace(DATA_FILE + ".tmp", DATA_FILE)

def iso2epoch(s):
    try:
        return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))
    except (TypeError, ValueError):
        return 0

def update(sysname, t, facs, ctrl_name, src, conflicts=(), extra=None):
    """facs: lista de dicts con Name, Influence (0..1), FactionState, ActiveStates... (formato journal)."""
    facs = sorted(facs, key=lambda x: -(x.get("Influence") or 0))
    me = next((x for x in facs if x.get("Name") == FAC), None)
    with lock:
        old = DB["sistemas"].get(sysname)
        if old and old.get("t", 0) >= t:                 # ya tengo un dato igual o mas nuevo:
            fill = {}                                    # solo se completa lo que le falte (datos de la v1)
            if old.get("todas") is None and me:
                fill["todas"] = [{"n": x.get("Name"), "inf": round((x.get("Influence") or 0) * 100, 2), "gov": x.get("Government") or "",
                                  "alg": x.get("Allegiance") or "", "act": [y.get("State") for y in x.get("ActiveStates") or [] if y.get("State")],
                                  "pend": [y.get("State") for y in x.get("PendingStates") or [] if y.get("State")],
                                  "jug": x.get("isPlayer")} for x in facs if (x.get("Influence") or 0) > 0]
                fill["ctrl_n"] = ctrl_name or ""
            for k_ in ("pos", "sis", "pp"):
                if not old.get(k_) and (extra or {}).get(k_):
                    fill[k_] = extra[k_]
            if fill:
                old.update(fill); dirty[0] = True
            return False
        if not me:
            if old and old.get("inf") is not None:
                DB["sistemas"][sysname] = {"sys": sysname, "t": t, "src": src, "fuera": True, "inf": 0}
                dirty[0] = True
                log("¡", FAC, "ya no está en", sysname, "!")
                discord(f"⚠️ **{FAC}** ya no está en **{sysname}**")
            return False
        inf = round((me.get("Influence") or 0) * 100, 2)
        sec = next((x for x in facs if x.get("Name") != FAC), {})
        st = lambda k: [x.get("State") for x in me.get(k) or [] if x.get("State")]
        con = [{"tipo": c.get("WarType"), "estado": c.get("Status"),
                "contra": (c["Faction2"] if c["Faction1"].get("Name") == FAC else c["Faction1"]).get("Name"),
                "ganados": (c["Faction1"] if c["Faction1"].get("Name") == FAC else c["Faction2"]).get("WonDays"),
                "perdidos": (c["Faction2"] if c["Faction1"].get("Name") == FAC else c["Faction1"]).get("WonDays")}
               for c in conflicts or [] if FAC in ((c.get("Faction1") or {}).get("Name"), (c.get("Faction2") or {}).get("Name"))]
        new = {"sys": sysname, "t": t, "src": src, "inf": inf, "ctrl": ctrl_name == FAC,
               "estado": me.get("FactionState") or "None", "activos": st("ActiveStates"), "pendientes": st("PendingStates"),
               "recuperando": st("RecoveringStates"), "segunda": sec.get("Name") or "",
               "segunda_inf": round((sec.get("Influence") or 0) * 100, 2), "conflictos": con,
               "todas": [{"n": x.get("Name"), "inf": round((x.get("Influence") or 0) * 100, 2), "gov": x.get("Government") or "",
                          "alg": x.get("Allegiance") or "", "act": [y.get("State") for y in x.get("ActiveStates") or [] if y.get("State")],
                          "pend": [y.get("State") for y in x.get("PendingStates") or [] if y.get("State")],
                          "jug": x.get("isPlayer")} for x in facs if (x.get("Influence") or 0) > 0],
               "ctrl_n": ctrl_name or ""}
        for k_ in ("pos", "sis", "pp"):                  # lo que no traiga este dato se conserva del anterior
            v_ = (extra or {}).get(k_) or (old or {}).get(k_)
            if v_:
                new[k_] = v_
        for k_ in ("trafico", "zc", "pn"):               # actividad: siempre se conserva
            if (old or {}).get(k_):
                new[k_] = old[k_]
        if old and old.get("inf") is not None and abs(old["inf"] - inf) >= 0.01:
            new["prev"], new["prev_t"] = old["inf"], old.get("t")
        elif old:
            new["prev"], new["prev_t"] = old.get("prev"), old.get("prev_t")
        DB["sistemas"][sysname] = new
        dirty[0] = True
    avisos(sysname, old, new)
    return True


# ---------- avisos a Discord (opcional: discord_webhook.txt junto a este archivo) ----------
ES = {"Expansion": "Expansión", "War": "Guerra", "CivilWar": "Guerra civil", "Election": "Elecciones", "Retreat": "Retirada",
      "Boom": "Auge", "Bust": "Crisis", "Famine": "Hambruna", "Outbreak": "Epidemia", "Lockdown": "Confinamiento",
      "CivilUnrest": "Disturbios", "PirateAttack": "Ataque pirata", "Drought": "Sequía", "Blight": "Plaga",
      "InfrastructureFailure": "Fallo de infraestructura", "NaturalDisaster": "Desastre natural", "TerroristAttack": "Atentado",
      "CivilLiberty": "Libertad civil", "Investment": "Inversión", "PublicHoliday": "Festividad"}
DQ = []

def discord(txt):
    DQ.append(txt)

def discord_loop():
    f = os.path.join(HERE, "discord_webhook.txt")
    while True:
        time.sleep(3)
        if not DQ:
            continue
        try:
            url = open(f).read().strip()
        except OSError:
            DQ.clear(); continue                         # sin webhook: no se manda nada
        txt = DQ.pop(0)
        try:
            req = urllib.request.Request(url, data=json.dumps({"content": txt[:1900]}).encode(),
                                         headers={"Content-Type": "application/json", "User-Agent": "PanelEliteRPi-escucha/1.0"})
            urllib.request.urlopen(req, timeout=15).read()
        except Exception as e:
            log("Discord:", e)

def avisos(sysname, old, new):
    if not old or old.get("inf") is None or old.get("t", 0) == 0:
        if old is None and new.get("src") == "EDDN":
            discord(f"🆕 **{FAC}** aparece en **{sysname}** ({new['inf']:.1f} %)")
        return
    gap_o = old["inf"] - (old.get("segunda_inf") or 0)
    gap_n = new["inf"] - (new.get("segunda_inf") or 0)
    if new.get("ctrl") and gap_n < 5 <= gap_o:
        discord(f"🔻 **{sysname}**: ventaja de solo {gap_n:.1f} puntos sobre {new.get('segunda')}".replace(".", ","))
    if old.get("conflictos") and not new.get("conflictos"):
        c = old["conflictos"][0]
        g_, p_ = c.get("ganados") or 0, c.get("perdidos") or 0
        discord(f"🏁 **{sysname}**: terminó el conflicto contra **{c.get('contra')}** ({g_}-{p_} días, {'GANADO' if g_ > p_ else 'PERDIDO' if p_ > g_ else 'empate'})")
    if new.get("conflictos") and not old.get("conflictos"):
        c = new["conflictos"][0]
        tipo = {"war": "Guerra", "civilwar": "Guerra civil", "election": "Elecciones"}.get((c.get("tipo") or "").lower(), "Conflicto")
        discord(f"⚔️ **{sysname}**: {tipo} contra **{c.get('contra')}**")
    for k, lab in (("pendientes", "pendiente"), ("activos", "activo")):
        for st_ in set(new.get(k) or []) - set(old.get(k) or []):
            if st_ in ("Retreat", "Expansion", "War", "CivilWar", "Election"):
                discord(f"{'🚨' if st_ == 'Retreat' else '📣'} **{sysname}**: {ES.get(st_, st_)} {lab}")

def resumen():
    with lock:
        S = [v for v in DB["sistemas"].values() if v.get("inf") and not v.get("fuera")]
    S.sort(key=lambda v: (not v.get("ctrl"), -(v.get("inf") or 0)))
    L = [f"📊 **{FAC}** · {sum(1 for v in S if v.get('ctrl'))} controlados · {len(S)} sistemas"]
    for v in S:
        gap = v["inf"] - (v.get("segunda_inf") or 0)
        tr = v["inf"] - v["prev"] if v.get("prev") is not None else 0
        est = ", ".join([ES.get(x, x) for x in v.get("activos") or []] + [ES.get(y, y) + " (pend.)" for y in v.get("pendientes") or []])
        L.append((f"{'🏰' if v.get('ctrl') else '·'} {v['sys']}: {v['inf']:.1f} % ({'+' if gap >= 0 else ''}{gap:.1f})"
                  + (f" {'▲' if tr > 0 else '▼'}{abs(tr):.1f}" if abs(tr) >= 0.1 else "")).replace(".", ",") + (f" · {est}" if est else ""))
    discord("\n".join(L))

def resumen_loop():
    hecho = None
    while True:
        time.sleep(60)
        lt = time.localtime()
        if lt.tm_hour == CFG["resumen_hora"] and hecho != lt.tm_yday:
            hecho = lt.tm_yday
            resumen()

# ---------- subida a GitHub (todos los paneles leen de ahi) ----------
def gh_loop():
    tf = os.path.join(HERE, "github_token.txt")
    last_h, last_t = None, 0
    api = f"https://api.github.com/repos/{CFG['github']}/contents/faccion.json"
    time.sleep(60)
    while True:
        try:
            token = open(tf).read().strip()
        except OSError:
            token = ""
        if token:
            with lock:
                h = hashlib.md5(json.dumps(DB["sistemas"], sort_keys=True).encode()).hexdigest()
                body = json.dumps(DB, ensure_ascii=False, indent=1)
            if h != last_h or time.time() - last_t > 6 * 3600:
                hdr = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
                       "User-Agent": "PanelEliteRPi-escucha/1.0", "X-GitHub-Api-Version": "2022-11-28"}
                try:
                    sha = None
                    try:
                        with urllib.request.urlopen(urllib.request.Request(api, headers=hdr), timeout=20) as r:
                            sha = json.loads(r.read().decode()).get("sha")
                    except urllib.error.HTTPError as e:
                        if e.code != 404:
                            raise
                    put = {"message": "Datos " + time.strftime("%d/%m/%Y %H:%M"),
                           "content": base64.b64encode(body.encode("utf-8")).decode()}
                    if sha:
                        put["sha"] = sha
                    req = urllib.request.Request(api, data=json.dumps(put).encode(), headers=hdr, method="PUT")
                    urllib.request.urlopen(req, timeout=30).read()
                    last_h, last_t = h, time.time()
                    log("GitHub: faccion.json subido")
                except Exception as e:
                    log("GitHub:", e)
        time.sleep(CFG["github_min"] * 60)


# ---------- actividad (v3): trafico, zonas de conflicto, portanaves y Powerplay de alrededor ----------
import math, re as _re
FAC_B = FAC.encode("utf-8")
NAMES = {"b": [], "t": 0}
TRAF_FILE = os.path.join(HERE, "trafico.json")
try:
    with open(TRAF_FILE, encoding="utf-8") as _f:
        TRAF = {k: {d: set(v) for d, v in dd.items()} for k, dd in json.load(_f).items()}
except (OSError, ValueError):
    TRAF = {}
CALLSIGN = _re.compile(r"\b([A-Z0-9]{3}-[A-Z0-9]{3})\b")
ZONA_LY = 20.0

def mis_sistemas():
    if time.time() - NAMES["t"] > 60:
        with lock:
            NAMES["b"] = [(n.encode("utf-8"), n) for n, v in DB["sistemas"].items() if not v.get("fuera")]
        NAMES["t"] = time.time()
    return NAMES["b"]

def cerca(pos):
    if not pos:
        return False
    with lock:
        P_ = [v.get("pos") for v in DB["sistemas"].values() if v.get("pos") and not v.get("fuera")]
    return any(math.dist(pos, q) <= ZONA_LY for q in P_ if None not in q)

def traf_save():
    try:
        with open(TRAF_FILE + ".tmp", "w", encoding="utf-8") as f:
            json.dump({k: {d: sorted(v) for d, v in dd.items()} for k, dd in TRAF.items()}, f)
        os.replace(TRAF_FILE + ".tmp", TRAF_FILE)
    except OSError as e:
        log("trafico:", e)

def process(pkt):
    hit = next((n for b_, n in mis_sistemas() if b_ in pkt), None)
    pp_ = b'"ControllingPower"' in pkt or b'"Powers"' in pkt
    if not hit and FAC_B not in pkt and not pp_:
        return                                           # rapido: no es de ningun sistema que interese
    d = json.loads(pkt)
    sch = d.get("$schemaRef", "")
    hdr = d.get("header") or {}
    gv = hdr.get("gameversion") or ""
    if gv.startswith("3.") or "legacy" in gv.lower() or "/test" in sch:
        return                                           # galaxia antigua (Horizons 3.8) o pruebas
    m = d.get("message") or {}
    sname = m.get("StarSystem") or m.get("systemName")
    t = iso2epoch(m.get("timestamp")) or int(time.time())
    with lock:
        mine = DB["sistemas"].get(sname) if sname else None
    # trafico: comandantes distintos por dia (id anonimo de EDDN)
    if mine and not mine.get("fuera") and hdr.get("uploaderID"):
        day = time.strftime("%Y-%m-%d", time.gmtime(t))
        dd = TRAF.setdefault(sname, {})
        ids = dd.setdefault(day, set())
        uid = str(hdr["uploaderID"])[:12]
        if uid not in ids:
            ids.add(uid)
            for old_ in sorted(dd)[:-8]:
                dd.pop(old_, None)
            with lock:
                mine["trafico"] = {k: len(v) for k, v in dd.items()}
                dirty[0] = True
    # senales: zonas de conflicto y portanaves
    if mine and "/fsssignaldiscovered/" in sch:
        for sg in m.get("signals") or []:
            nm = sg.get("SignalName") or ""
            ts = iso2epoch(sg.get("timestamp")) or t
            with lock:
                if "Warzone_PointRace" in nm:
                    lv = "High" if "High" in nm else "Med" if "Med" in nm else "Low"
                    zc = {z["n"]: z for z in mine.get("zc") or [] if time.time() - z["t"] < 86400}
                    zc[nm] = {"n": nm, "i": lv, "t": ts}
                    mine["zc"] = sorted(zc.values(), key=lambda z: -z["t"])[:8]
                    dirty[0] = True
                elif sg.get("SignalType") == "FleetCarrier" or (sg.get("IsStation") and CALLSIGN.search(nm)):
                    cs = CALLSIGN.search(nm)
                    if cs:
                        pn = {k: v for k, v in (mine.get("pn") or {}).items() if time.time() - v["t"] < 7 * 86400}
                        pn[cs.group(1)] = {"n": nm.replace(cs.group(1), "").strip(), "t": ts}
                        mine["pn"] = pn
                        dirty[0] = True
        return
    if "/journal/" not in sch or m.get("event") not in ("FSDJump", "Location", "CarrierJump"):
        return
    # Powerplay de los sistemas a menos de 20 al de los tuyos
    if (m.get("ControllingPower") or m.get("Powers")) and cerca(m.get("StarPos")):
        with lock:
            DB.setdefault("zona", {})[sname] = {"pos": m.get("StarPos"), "pot": m.get("ControllingPower"), "est": m.get("PowerplayState"),
                                                 "prog": m.get("PowerplayStateControlProgress"), "pots": m.get("Powers") or [], "t": t}
            dirty[0] = True
    if FAC_B not in pkt or not m.get("Factions"):
        return
    ex = {"pos": m.get("StarPos"),
          "sis": {"pob": m.get("Population"), "eco": m.get("SystemEconomy"), "eco2": m.get("SystemSecondEconomy"),
                  "seg": m.get("SystemSecurity"), "gov": m.get("SystemGovernment"), "alg": m.get("SystemAllegiance")},
          "pp": {"pot": m.get("ControllingPower"), "est": m.get("PowerplayState"), "prog": m.get("PowerplayStateControlProgress"),
                 "ref": m.get("PowerplayStateReinforcement"), "soc": m.get("PowerplayStateUndermining"),
                 "pots": m.get("Powers") or []}}
    if update(sname, t, m["Factions"], (m.get("SystemFaction") or {}).get("Name"), "EDDN", m.get("Conflicts"), ex):
        DB["eddn"]["mios"] += 1; DB["eddn"]["ultimo"] = time.time()
        s_ = DB["sistemas"][sname]
        log(f"EDDN {sname}: {s_['inf']:.1f}% {'(controla)' if s_['ctrl'] else ''} {' '.join(s_['activos'] + s_['pendientes'])}")

# ---------- EDDN ----------
def eddn_loop():
    import zmq
    ctx = zmq.Context()
    while True:
        sub = ctx.socket(zmq.SUB)
        sub.setsockopt(zmq.SUBSCRIBE, b"")
        sub.setsockopt(zmq.RCVTIMEO, 600000)             # 10 min sin nada: se reconecta
        sub.connect("tcp://eddn.edcd.io:9500")
        log("EDDN conectado")
        DB["eddn"]["ok"] = True
        try:
            while True:
                raw = sub.recv()
                DB["eddn"]["msgs"] += 1
                try:
                    process(zlib.decompress(raw))
                except Exception as e:                   # un mensaje raro no corta la escucha
                    DB["eddn"]["malos"] = DB["eddn"].get("malos", 0) + 1
                    if DB["eddn"]["malos"] % 100 == 1:
                        log("EDDN mensaje:", e)
        except Exception as e:
            log("EDDN:", e)
        DB["eddn"]["ok"] = False
        try:
            sub.close(0)
        except Exception:
            pass
        time.sleep(30)

# ---------- EDSM (rellena huecos) ----------
def edsm_one(name):
    url = "https://www.edsm.net/api-system-v1/factions?" + urllib.parse.urlencode({"systemName": name})
    req = urllib.request.Request(url, headers={"User-Agent": "PanelEliteRPi-escucha/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        j = json.loads(r.read().decode() or "{}")
    fs = j.get("factions") or []
    if not fs:
        return
    t = max(f.get("lastUpdate") or 0 for f in fs)
    conv = lambda L: [{"State": x.get("state")} for x in L or []]
    facs = [{"Name": f.get("name"), "Influence": f.get("influence") or 0, "FactionState": f.get("state"),
             "Government": f.get("government"), "Allegiance": f.get("allegiance"), "isPlayer": f.get("isPlayer"),
             "ActiveStates": conv(f.get("activeStates")), "PendingStates": conv(f.get("pendingStates")),
             "RecoveringStates": conv(f.get("recoveringStates"))} for f in fs]
    ex = None
    if not (DB["sistemas"].get(name) or {}).get("pos"):    # coordenadas y datos del sistema, una sola vez
        try:
            u2 = "https://www.edsm.net/api-v1/system?" + urllib.parse.urlencode(
                {"systemName": name, "showCoordinates": 1, "showInformation": 1})
            with urllib.request.urlopen(urllib.request.Request(u2, headers={"User-Agent": "PanelEliteRPi-escucha/1.0"}), timeout=20) as r:
                j2 = json.loads(r.read().decode() or "{}")
            c, inf_ = j2.get("coords") or {}, j2.get("information") or {}
            ex = {"pos": [c.get("x"), c.get("y"), c.get("z")] if c else None,
                  "sis": {"pob": inf_.get("population"), "eco": inf_.get("economy"), "eco2": inf_.get("secondEconomy"),
                          "seg": inf_.get("security"), "gov": inf_.get("government"), "alg": inf_.get("allegiance")} if inf_ else None}
        except Exception as e:
            log("EDSM sistema", name, e)
    if update(name, t, facs, (j.get("controllingFaction") or {}).get("name"), "EDSM", (), ex):
        log(f"EDSM {name}: actualizado")

def edsm_loop():
    time.sleep(20)
    while True:
        for name in list(DB["sistemas"]):
            v_ = DB["sistemas"][name]
            if time.time() - (v_.get("t") or 0) > 3 * 3600 or v_.get("todas") is None or not v_.get("pos"):
                try:
                    edsm_one(name)
                except Exception as e:
                    log("EDSM", name, e)
                time.sleep(3)                            # sin prisa: EDSM pide no saturar
        time.sleep(CFG["edsm_horas"] * 3600)

# ---------- servidor para el panel ----------
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] not in ("/", "/faccion.json"):
            self.send_error(404); return
        with lock:
            body = json.dumps(DB, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass

def saver_loop():
    n_ = 0
    while True:
        time.sleep(10)
        n_ += 1
        if n_ % 30 == 0:                                 # cada 5 min
            traf_save()
            with lock:
                z_ = DB.get("zona") or {}
                for k in [k for k, v in z_.items() if time.time() - (v.get("t") or 0) > 7 * 86400]:
                    z_.pop(k, None)
        if dirty[0]:
            try:
                save()
            except OSError as e:
                log("guardar:", e)

if __name__ == "__main__":
    load()
    log(f"Escuchando a '{FAC}' · {len(DB['sistemas'])} sistemas conocidos · puerto {CFG['puerto']}")
    for fn in (eddn_loop, edsm_loop, saver_loop, gh_loop, discord_loop, resumen_loop):
        threading.Thread(target=fn, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", CFG["puerto"]), H).serve_forever()
