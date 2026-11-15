# Panel Elite v1.1 · parte 19: el ROBOT contesta preguntas por voz (v1.1.9)
#   Tocas la pantalla del robot, te escucha 4 s y manda el audio aquí (POST /oir al puerto 8081).
#   La Pi lo pasa a texto con Vosk (español, sin internet), busca la pregunta y contesta:
#   el texto va al bocadillo y la voz (Piper o espeak-ng) la reproduce el robot por su altavoz.
#   Vosk se instala aparte con instalar_oido_robot.sh. El modelo se carga al primer uso y se suelta
#   tras 10 min sin preguntas, para no gastar RAM (sobre todo en la Pi 3).
#   Preguntas: combustible, saltos/ruta, dónde estoy, tick, facción, dinero, misiones, carga, hora,
#   datos sin vender, atraque, nave, tiempo jugando, ayuda.
import unicodedata as _ud

VOSK_DIR = os.path.join(PANEL_DIR, "vosk-es")
OIDO = {"model": None, "t": 0.0, "lock": threading.Lock(), "err": "", "resp": {}, "n": 0}

def oido_ok():
    try:
        import vosk  # noqa: F401
    except Exception:
        return False
    return os.path.isdir(VOSK_DIR)

def _oido_model():
    with OIDO["lock"]:
        if OIDO["model"] is None:
            import vosk
            vosk.SetLogLevel(-1)
            OIDO["model"] = vosk.Model(VOSK_DIR)
        OIDO["t"] = time.time()
        return OIDO["model"]

def _oido_suelta():
    while True:
        time.sleep(60)
        if OIDO["model"] is not None and time.time() - OIDO["t"] > 600:
            with OIDO["lock"]:
                OIDO["model"] = None
            try:
                if _LC is not None:
                    _LC.malloc_trim(0)
            except Exception:
                pass

threading.Thread(target=_oido_suelta, daemon=True, name="oido").start()

def oido_texto(pcm, rate=16000):
    """Audio PCM 16 bits mono -> texto (minúsculas)."""
    import vosk, array, sys as _s
    a = array.array("h"); a.frombytes(pcm[:len(pcm) // 2 * 2])
    if _s.byteorder != "little":
        a.byteswap()
    pico = max((abs(x) for x in a), default=0)
    if 0 < pico < 12000:                                  # el micro del robot suena bajo: se sube el volumen
        k = 12000 / pico
        a = array.array("h", (max(-32768, min(32767, int(x * k))) for x in a))
        pcm = a.tobytes()
    rec = vosk.KaldiRecognizer(_oido_model(), rate)
    for i in range(0, len(pcm), 8000):
        rec.AcceptWaveform(pcm[i:i + 8000])
    return (json.loads(rec.FinalResult()).get("text") or "").strip()

def _norm(t):
    t = _ud.normalize("NFD", (t or "").lower())
    return "".join(c for c in t if _ud.category(c) != "Mn")

def _mm(sec):
    sec = max(0, int(sec))
    h, m = sec // 3600, sec % 3600 // 60
    return f"{h} h {m:02d} min" if h else f"{m} min"

def _cr(v):
    v = float(v or 0)
    if abs(v) >= 1e6:
        return f"{v / 1e6:.1f} M cr".replace(".", ",")
    return f"{v / 1e3:.0f} mil cr" if abs(v) >= 1e4 else f"{v:.0f} cr"

# ---- respuestas: cada una devuelve el texto (corto: cabe en el bocadillo y se dice rápido) ----
def r_combustible(d, now):
    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
    if fuel is None:
        return "No sé el combustible ahora mismo"
    t = f"Combustible al {100 * fuel / cap:.0f} %" if cap else f"Llevas {fuel:.1f} t de combustible"
    route = d.get("route") or []
    if route:
        k = next((i + 1 for i, r in enumerate(route) if star_ok(r[1])), None)
        t += f". Próxima recolectable a {k} salto{'s' if k != 1 else ''}" if k else ". No hay estrellas recolectables en la ruta"
    return t

def r_ruta(d, now):
    route = d.get("route") or []
    n = d.get("routen") or len(route)
    if not n:
        return "No hay ruta trazada"
    end = ((d.get("routeend") or route[-1]) or [""])[0]
    t = f"Quedan {n} salto{'s' if n != 1 else ''} hasta {end}"
    eta = ((d.get("routeinfo") or {}).get("eta"))
    if eta:
        t += f". Llegamos en unos {_mm(eta)}"
    return t

def r_donde(d, now):
    sy = d.get("system") or "un sistema desconocido"
    st = d.get("station") or {}
    if d.get("Flags", 0) & 1 and st.get("name"):
        return f"Atracados en {st['name']}, sistema {sy}"
    body = d.get("body")
    return f"En {sy}" + (f", cerca de {body}" if body and body != sy else "")

def r_tick(d, now):
    tn = tick_next(now)
    if not tn:
        return "No sé cuándo es el tick"
    p, disp = tn
    t = f"El próximo tick es a las {time.strftime('%H:%M', time.localtime(p))}"
    if disp:
        t += f", más o menos {disp} minutos"
    return t + f". Faltan {_mm(p - now)}" if p > now else t

def r_faccion(d, now):
    S = ((FACD["data"] or {}).get("sistemas") or {})
    vivos = [(n, v) for n, v in S.items() if not v.get("fuera")]
    if not vivos:
        return "No tengo datos de Caballeros de Sion"
    malos = []
    for n, v in vivos:
        w = inf_warn(v)
        if fac_war(v):
            malos.append(f"{n} en conflicto")
        elif w:
            malos.append(f"{n}: {w[0].lower()}")
    t = f"Caballeros de Sion está en {len(vivos)} sistemas"
    return t + (". Ojo: " + "; ".join(malos[:2]) if malos else ". Todo tranquilo")

def r_dinero(d, now):
    se = d.get("sess") or {}
    sn = se.get("snap") or {}
    e0, ea = sn.get("earn") or {}, se.get("earn") or {}
    earn = sum(ea.get(k, 0) - e0.get(k, 0) for k in ea)
    t = f"Esta partida llevas {_cr(earn)}"
    if d.get("balance") is not None:
        t += f". En la cuenta tienes {_cr(d['balance'])}"
    return t

def r_misiones(d, now):
    pn = d.get("pcnow") or now
    M = [m for m in d.get("missions") or [] if len(m) > 2]
    if not M:
        return "No tienes misiones activas"
    t = f"Tienes {len(M)} misi{'ones' if len(M) != 1 else 'ón'}"
    pr = sorted((m for m in M if m[2] and m[2] > pn), key=lambda m: m[2])
    if pr:
        t += f". La más urgente caduca en {_mm(pr[0][2] - pn)}"
    return t

def r_carga(d, now):
    h = hold_state(d)
    if not h:
        return "No sé cuánta carga llevas"
    used, cap = h
    if not used:
        return f"La bodega está vacía, caben {cap} t"
    top = sorted(d.get("cargo") or [], key=lambda c: -c[1])[:2]
    return f"Llevas {used} de {cap} t" + (": " + ", ".join(f"{c} t de {n}" for n, c in top) if top else "")

def r_hora(d, now):
    return "Son las " + time.strftime("%H:%M")

def r_datos(d, now):
    un = (d.get("explo") or {}).get("unsold") or 0
    bio = (d.get("bio") or {}).get("unsold_cr") or 0
    if not un and not bio:
        return "No llevas datos sin vender"
    t = f"Llevas {_cr(un)} de exploración sin vender" if un else ""
    if bio:
        t += (" y " if t else "Llevas ") + f"{_cr(bio)} de biología"
    return t

def r_atraque(d, now):
    st = d.get("station") or {}
    left = dock_left(d, now)
    if left is None:
        return "No tenemos atraque concedido"
    return f"Plataforma {st.get('pad', '?')} en {st.get('name', 'la estación')}. Quedan {int(left // 60)}:{int(left % 60):02d}"

def r_nave(d, now):
    sh = ((d.get("live") or {}).get("ship")) or {}
    if not sh:
        return "No sé en qué nave vamos"
    t = f"Vamos en la {sh.get('name') or sh.get('ship')}"
    if sh.get("hull") is not None:
        t += f", casco al {sh['hull'] * 100:.0f} %"
    return t

def r_jugando(d, now):
    seg = (d.get("sess") or {}).get("seg")
    pn = d.get("pcnow") or now
    return f"Llevas {_mm(pn - seg)} jugando" if seg else "No sé cuánto llevas jugando"

def r_ayuda(d, now):
    return "Pregúntame por combustible, ruta, dónde estamos, tick, facción, dinero, misiones, carga o la hora"

def r_hola(d, now):
    return "o7 Comandante"

# (palabras clave, respuesta). Va la primera que coincida, en este orden.
OIDO_PREG = [
    (("ayuda", "que puedes", "que sabes"), r_ayuda),
    (("combustible", "gasolina", "fuel", "repostar", "deposito"), r_combustible),
    (("atraque", "plataforma", "aterrizar", "atracar"), r_atraque),
    (("salto", "ruta", "destino", "falta", "llegamos"), r_ruta),
    (("tick",), r_tick),
    (("faccion", "caballero", "sion", "influencia", "cdsn"), r_faccion),
    (("dinero", "credito", "ganado", "ganancia", "cuenta"), r_dinero),
    (("mision", "pasajero"), r_misiones),
    (("jugando", "cuanto tiempo", "cuanto llevo"), r_jugando),
    (("sin vender", "exploracion", "datos", "biologia"), r_datos),
    (("carga", "bodega", "llevo", "llevamos"), r_carga),
    (("hora",), r_hora),
    (("donde", "sistema", "estamos"), r_donde),
    (("nave", "casco"), r_nave),
    (("hola", "buenas", "o7"), r_hola),
]

def oido_respuesta(texto):
    """Texto oído -> (respuesta, ev para la cara)."""
    with lock:
        d = state.get("data") or {}
    now = time.time()
    t = _norm(texto)
    if not t:
        return "No te he oído. Toca la pantalla y habla cerca", "nada"
    for pals, fn in OIDO_PREG:
        if any(re.search(r"\b" + re.escape(p), t) for p in pals):     # al principio de palabra («hora» no es «ahora»)
            try:
                return fn(d, now), "ok"
            except Exception as e:
                log_exc("oido " + fn.__name__, e)
                return "Uy, no he podido mirarlo", "nada"
    return f"No te he entendido: {texto}", "nada"

def oido_wav(texto):
    """Voz de la respuesta (wav) o None. Piper si está; si no, espeak-ng."""
    t = re.sub(r"\s+", " ", voz_txt(texto)).strip()
    try:
        if piper_ok():
            with open(_piper_wav(t), "rb") as fh:
                return fh.read()
        if shutil.which("espeak-ng"):
            r = subprocess.run(["espeak-ng", "-v", "es", "-s", "150", "-a", "130", "--stdout", t],
                               capture_output=True, timeout=20)
            return r.stdout or None
    except Exception as e:
        log_exc("oido voz", e)
    return None

def oido_atiende(pcm, rate):
    """Lo que hace el panel con una pregunta: devuelve el JSON para el robot."""
    if not cfg.get("stackchan"):
        return {"txt": "ROBOT desactivado en el panel"}
    if not ev_on("roboido"):
        return {"txt": "Las preguntas por voz están quitadas en ALERTAS"}
    if not oido_ok():
        return {"txt": "No tengo oídos: instala instalar_oido_robot.sh en la Pi"}
    t0 = time.time()
    oido = oido_texto(pcm, rate)
    resp, cara = oido_respuesta(oido)
    plog(f"ROBOT oye «{oido}» -> {resp} ({time.time() - t0:.1f} s)")
    out = {"oido": oido, "txt": resp, "cara": cara}
    wav = oido_wav(resp)
    if wav and len(wav) < 600000:
        OIDO["n"] += 1
        OIDO["resp"] = {OIDO["n"]: wav}                 # solo la última respuesta
        out["wav"] = f"/resp?n={OIDO['n']}"
    return out

EV_LIST.append(("roboido", "ROBOT: PREGUNTAS POR VOZ"))

# --- el servidor de fotos de la StackChan (8081) ahora también oye y devuelve la voz ---
def sc_foto_srv():
    if SC_FOTO["srv"]:
        return
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    import urllib.parse as _up

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _envia(self, data, tipo):
            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = _up.urlparse(self.path)
            q = _up.parse_qs(u.query)
            data = None
            if u.path == "/foto" and cfg.get("stackchan"):
                f = (q.get("f") or [""])[0]
                try:
                    data = sc_foto_rotulada(f)              # v1.1.9c: con el rótulo pintado (parte 20)
                except Exception as e:
                    log_exc("stackchan foto " + f, e)
                if data:
                    return self._envia(data, "image/jpeg")
            if u.path == "/resp":
                try:
                    data = OIDO["resp"].get(int((q.get("n") or ["0"])[0]))
                except ValueError:
                    data = None
                if data:
                    return self._envia(data, "audio/wav")
            self.send_error(404)

        def do_POST(self):
            u = _up.urlparse(self.path)
            if u.path != "/oir":
                self.send_error(404); return
            try:
                n = int(self.headers.get("Content-Length") or 0)
                rate = int((_up.parse_qs(u.query).get("r") or ["16000"])[0])
                if n <= 0 or n > 400000:
                    self.send_error(413); return
                pcm = self.rfile.read(n)
                out = oido_atiende(pcm, rate)
            except Exception as e:
                log_exc("robot oido", e)
                out = {"txt": "Uy, algo ha fallado al oírte"}
            self._envia(json.dumps(out, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", SC_FOTO_PORT), H)
        srv.daemon_threads = True
        SC_FOTO["srv"] = srv
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    except OSError as e:
        print("STACKCHAN fotos/oido:", e)

# el servidor tiene que estar escuchando aunque aún no se haya enseñado ninguna foto
_rob_watch_v119 = rob_watch

def rob_watch(now):
    if cfg.get("stackchan") and not SC_FOTO["srv"]:
        sc_foto_srv()
    return _rob_watch_v119(now)
