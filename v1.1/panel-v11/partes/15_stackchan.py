# Panel Elite v1.1 · parte 15: STACKCHAN (robot M5Stack que reacciona a los avisos del panel)
# Sin EMITIR: el panel manda cada aviso por UDP (puerto 5007) y la StackChan contesta para saber que esta ahi.
# Primero por difusion a toda la red; cuando la StackChan contesta, directo a su IP.
# Fotos: {"t":"foto","f":...,"port":8081,"titulo","dato","seg"} y la StackChan la baja de http://IP:8081/foto?f=...
# Mensajes:  {"t":"hola","ver":...}  cada 3 s   ·   {"t":"aviso","n":..,"ev":..,"kind":..,"titulo":..,"dato":..}
# Respuesta de la StackChan: "STACKCHAN-OK"
SC_PORT = 5007
SC = {"sock": None, "ip": None, "ok": 0.0, "n": 0}

def sc_sock():
    if SC["sock"] is None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.bind(("0.0.0.0", SC_PORT))
            SC["sock"] = s
            threading.Thread(target=sc_rx, daemon=True).start()
        except OSError as e:
            print("STACKCHAN:", e)
    return SC["sock"]

def sc_rx():
    s = SC["sock"]
    while True:
        try:
            data, addr = s.recvfrom(256)
        except OSError:
            time.sleep(1); continue
        if data.startswith(b"STACKCHAN-OK"):
            SC["ip"], SC["ok"] = addr[0], time.time()

def sc_send(obj):
    s = sc_sock()
    if not s:
        return
    data = json.dumps(obj, ensure_ascii=False).encode()
    viva = SC["ip"] and time.time() - SC["ok"] < 10
    try:
        s.sendto(data, (SC["ip"], SC_PORT) if viva else ("<broadcast>", SC_PORT))
    except OSError:
        pass

# ---------- PELIGRO continuo: escudos caidos o casco < 70 % (en la nave, sin atracar) ----------
SC_PEL = {"on": None, "motivo": "", "nave": None, "conescudo": False, "rec": False, "rectxt": "", "pie": False, "clima": ""}

def sc_peligro_calc():
    with lock:
        d = state.get("data") or {}
        rx = state.get("rx") or 0
    if not d or time.time() - rx > 5:
        return False, ""
    fl, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    if f2 & 1 and not f2 & 2:                        # A PIE (no en taxi): salud < 50 % o poco oxigeno
        L = d.get("live") or {}
        m = []
        hp, oxy = L.get("health"), L.get("oxy")
        if isinstance(hp, (int, float)) and hp < 0.5:
            m.append(f"SALUD {int(hp * 100)} %")
        if f2 & (1 << 6):
            m.append(f"OXIGENO {int(oxy * 100)} %" if isinstance(oxy, (int, float)) else "POCO OXIGENO")
        return bool(m), " · ".join(m)
    nave = ((d.get("naves") or {}).get("cur") or {}).get("id")
    if nave != SC_PEL["nave"]:                       # nave nueva: aun no sabemos si lleva escudo
        SC_PEL["nave"], SC_PEL["conescudo"] = nave, False
    if fl & (1 << 24) and fl & (1 << 3):
        SC_PEL["conescudo"] = True                   # ha tenido escudos arriba: esta nave lleva escudo
    if not fl & (1 << 24) or fl & 0b11:              # no va en la nave, o atracado / posado
        return False, ""
    m = []
    if SC_PEL["conescudo"] and not fl & (1 << 3):    # naves sin escudo: nunca "escudos caidos"
        m.append("ESCUDOS CAIDOS")
    hull = ((d.get("live") or {}).get("ship") or {}).get("hull")
    if hull is not None and hull < 0.7:
        m.append(f"CASCO {int(hull * 100)} %")
    return bool(m), " · ".join(m)

def sc_recarga_calc():
    """Recogiendo combustible de una estrella (Status: ScoopingFuel, bit 11)."""
    with lock:
        d = state.get("data") or {}
        rx = state.get("rx") or 0
    if not d or time.time() - rx > 5 or not d.get("Flags", 0) & (1 << 11):
        return False, ""
    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
    if fuel is not None and cap:
        return True, f"RECARGANDO {int(100 * fuel / cap)} %"
    return True, "RECARGANDO"

def sc_pie_calc():
    """A pie (no en taxi) y si hace mucho frio o calor."""
    with lock:
        d = state.get("data") or {}
        rx = state.get("rx") or 0
    f2 = d.get("Flags2", 0) if d and time.time() - rx <= 5 else 0
    if not f2 & 1 or f2 & 2:
        return False, ""
    return True, "frio" if f2 & ((1 << 8) | (1 << 10)) else "calor" if f2 & ((1 << 9) | (1 << 11)) else ""

def sc_peligro_watch():
    on, motivo = sc_peligro_calc()
    rec, rectxt = sc_recarga_calc()
    pie, clima = sc_pie_calc()
    nuevo = (on, motivo, rec, rectxt, pie, clima)
    if nuevo != tuple(SC_PEL[k] for k in ("on", "motivo", "rec", "rectxt", "pie", "clima")):
        SC_PEL.update(on=on, motivo=motivo, rec=rec, rectxt=rectxt, pie=pie, clima=clima)
        sc_send({"t": "peligro", "on": on, "motivo": motivo, "recarga": rec, "rectxt": rectxt, "pie": pie, "clima": clima})

def sc_hola_loop():
    while True:
        if cfg.get("stackchan"):
            sc_send({"t": "hola", "ver": PANEL_VER.split(" ")[0], "peligro": bool(SC_PEL["on"]), "motivo": SC_PEL["motivo"],
                     "recarga": SC_PEL["rec"], "rectxt": SC_PEL["rectxt"], "pie": SC_PEL["pie"], "clima": SC_PEL["clima"]})
        time.sleep(3)

def sc_aviso(ev, kind, titulo, dato):
    SC["n"] += 1
    sc_send({"t": "aviso", "n": SC["n"], "ev": ev or "", "kind": kind or "",
             "titulo": titulo or "", "dato": dato or ""})

def sc_estado():
    if not cfg.get("stackchan"):
        return "NO"
    return "CONECTADO" if SC["ip"] and time.time() - SC["ok"] < 10 else "BUSCANDO"

threading.Thread(target=sc_hola_loop, daemon=True).start()

# ---------- FOTOS para la pantalla de la StackChan (320x240) ----------
# El panel sirve las fotos en http://IP:8081/foto?f=...  (solo con ROBOT activado)
#   bg:<tipo>   fondo de estacion/portanaves (fondo_*.jpg)   ship:<fichero>   foto de nave (naves/)   logo   logo_faccion.png
SC_FOTO_PORT = 8081
SC_FOTO = {"srv": None, "cache": {}, "st": None, "ship": None, "t": 0.0}

def sc_foto_file(f):
    base = os.path.dirname(os.path.abspath(__file__))
    if f == "logo":
        return os.path.join(base, "logo_faccion.png")
    if f.startswith("bg:") and f[3:] in BG_FILES:
        return os.path.join(base, BG_FILES[f[3:]])
    if f.startswith("ship:"):
        n = os.path.basename(f[5:])
        return os.path.join(_SHIPDIR, n) if n.startswith("nave_") and n.endswith(".jpg") else None
    return None

def sc_foto_jpg(f):
    if f in SC_FOTO["cache"]:
        return SC_FOTO["cache"][f]
    ruta = sc_foto_file(f)
    if not ruta or not os.path.isfile(ruta):
        return None
    import io
    src = pygame.image.load(ruta)
    w, h = 320, 240
    sw, sh = src.get_size()
    if f == "logo":                                   # logo entero sobre negro
        sc = min(w / sw, h / sh) * 0.9
        img = pygame.Surface((w, h)); img.fill((0, 0, 0))
        lg = pygame.transform.smoothscale(src, (int(sw * sc), int(sh * sc)))
        img.blit(lg, ((w - lg.get_width()) // 2, (h - lg.get_height()) // 2))
    else:                                             # foto que llena la pantalla
        sc = max(w / sw, h / sh)
        img = pygame.transform.smoothscale(src, (int(sw * sc) + 1, int(sh * sc) + 1))
        img = img.subsurface(pygame.Rect((img.get_width() - w) // 2, (img.get_height() - h) // 2, w, h)).copy()
    b = io.BytesIO()
    pygame.image.save(img, b, "foto.jpg")
    data = b.getvalue()
    if len(SC_FOTO["cache"]) > 20:
        SC_FOTO["cache"].clear()
    SC_FOTO["cache"][f] = data
    return data

def sc_foto_srv():
    if SC_FOTO["srv"]:
        return
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    import urllib.parse as _up

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass
        def do_GET(self):
            u = _up.urlparse(self.path)
            f = (_up.parse_qs(u.query).get("f") or [""])[0]
            data = None
            if u.path == "/foto" and cfg.get("stackchan"):
                try:
                    data = sc_foto_jpg(f)
                except Exception as e:
                    log_exc("stackchan foto " + f, e)
            if not data:
                self.send_error(404); return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", SC_FOTO_PORT), H)
        srv.daemon_threads = True
        SC_FOTO["srv"] = srv
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    except OSError as e:
        print("STACKCHAN fotos:", e)

def sc_foto(f, titulo, dato, seg=6):
    sc_foto_srv()
    if sc_foto_file(f):
        sc_send({"t": "foto", "f": f, "port": SC_FOTO_PORT, "titulo": titulo or "", "dato": dato or "", "seg": seg})

def sc_fotos_watch():
    """Atraque concedido -> foto de la estacion; cambio de nave -> foto de la nave."""
    now = time.time()
    if now - SC_FOTO["t"] < 1:
        return
    SC_FOTO["t"] = now
    with lock:
        d = state.get("data") or {}
    st = d.get("station") or {}
    clave = (st.get("name"), st.get("status"))
    if clave != SC_FOTO["st"]:
        primera = SC_FOTO["st"] is None
        SC_FOTO["st"] = clave
        if not primera and st.get("status") == "CONCEDIDO":
            try:
                k, lab, _ = carrier_kind(d, st)
            except Exception:
                k, lab = None, ""
            if k:
                sc_foto("bg:" + k, st.get("name") or lab, "ATRAQUE CONCEDIDO" + (f" · PLATAFORMA {st['pad']}" if st.get("pad") else ""), 8)
    c = (d.get("naves") or {}).get("cur") or {}
    nid = c.get("id")
    if nid is not None and nid != SC_FOTO["ship"]:
        primera = SC_FOTO["ship"] is None
        SC_FOTO["ship"] = nid
        if not primera:
            try:
                f = ship_file(c, d)
            except Exception:
                f = None
            if f:
                sc_foto("ship:" + os.path.basename(f), c.get("name") or c.get("ship") or "", (c.get("ship") or "").upper(), 7)

def sc_es_faccion(ev, titulo, dato):
    t = f"{titulo} {dato}".upper()
    return ev == "facwar" or "CDSN" in t or "CABALLEROS" in t

# los mismos avisos que van a la voz (respeta SONIDO Y VOZ uno a uno)
_voice_watch_b15 = voice_watch

def voice_watch():
    a, x = ui.get("alert"), xa.get("a")
    nueva_a, nueva_x = a is not voice["alert"], x is not voice["xa"]
    _voice_watch_b15()
    if not cfg.get("stackchan"):
        return
    if nueva_a and a and snd_on(a.get("ev")):
        sc_aviso_o_logo(a.get("ev"), a.get("kind"), a.get("text"), a.get("sub"))
    if nueva_x and x and snd_on(x.get("ev")):
        sc_aviso_o_logo(x.get("ev"), "alarm" if x.get("col") == RED else "ok", x.get("title"), x.get("big"))
    sc_fotos_watch()
    sc_peligro_watch()

def sc_aviso_o_logo(ev, kind, titulo, dato):
    if sc_es_faccion(ev, titulo, dato):               # avisos de CDSN: primero el logo de la faccion
        sc_foto("logo", titulo, dato, 4)
    sc_aviso(ev, kind, titulo, dato)

# boton en 12 AJUSTES
SET12.append(("ROBOT", "stackchan"))           # StackChan
