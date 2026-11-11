# Panel Elite v1.1 · parte 04: ajustes y espera (lineas 2542-3316 del panel entero)
# ---------- 12.4 ajustes ----------
def view_settings(surf, d, flags, now):
    items = [("CAMBIO AUTO", cfg["auto"]), ("ALERTAS", cfg["alerts"]), ("SONIDO", cfg["sound"]), ("COLOR", None),
             ("VOZ", cfg.get("voice", False)), ("EMITIR", cfg.get("stream", False)), ("TECLAS", None),
             ("CERRAR JUEGO", cfg.get("killbtn", True)), ("MERCADO", None), ("FOTOS CMDR", cfg.get("cmdrpics", True)), ("PANTALLA HDMI", None)]
    for i, (name, on) in enumerate(items):
        r = grid(i, 4, 3)
        if name == "PANTALLA HDMI":
            draw_button(surf, r, "HDMI", "PANEL" if hdmi_panel() else "4 CUADROS", F["btn"], filled=True,
                        lit=flash.get((124, i), 0) > now)
            continue
        if name == "MERCADO":
            mk_ = cfg.get("mkt", "CON CARGA")
            draw_button(surf, r, name, mk_, F["btn"], filled=mk_ != "NUNCA", lit=flash.get((124, i), 0) > now)
            continue
        if name == "TECLAS":
            miss = len(BINDS["missing"])
            draw_button(surf, r, name, (f"{miss} SIN TECLA  >" if miss else "TODAS  >") if BINDS["file"] else "DE FÁBRICA  >",
                        F["btn"], filled=bool(BINDS["file"]) and not miss, lit=flash.get((124, i), 0) > now)
            continue
        lit = flash.get((124, i), 0) > now
        if on is None:
            draw_button(surf, r, name, THEMES[cfg["theme"]][0], F["btn"], filled=True, lit=lit)
            continue
        sub = "ACTIVADO" if on else "DESACTIVADO"
        if name in ("ALERTAS", "CAMBIO AUTO", "SONIDO"):
            L, st, _, _, df = EVL[{"ALERTAS": 161, "CAMBIO AUTO": 162, "SONIDO": 163}[name]]
            n = sum(1 for k, _ in L if (cfg.get(st) or {}).get(k, df.get(k, True))) if on else 0
            on = n > 0
            sub = f"{n} de {len(L)}  >"
        if name == "VOZ" and not voice_ok():
            sub = "falta espeak-ng"
        if name == "CERRAR JUEGO":
            sub = "3 toques en el sistema" if on else "DESACTIVADO"
        if name == "EMITIR" and on:
            sub = stream["err"] or f"{my_ip()}:{STREAM_PORT}" + (f"  ({stream['clients']})" if stream["clients"] else "")
        draw_button(surf, r, name, sub, F["btn"] if F["btn"].size(name)[0] < r.w - 10 else F["small"], filled=on, lit=lit)

# ---------- reposo y pantalla de inicio ----------
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]

def draw_emblem(surf, cx, cy, r, t):
    for k in range(3):
        pygame.draw.circle(surf, DIM, (cx, cy), r - k * 9, 1)
    a = t * 0.8
    for k in range(3):
        ang = a + k * 2 * math.pi / 3
        pygame.draw.circle(surf, ORANGE, (int(cx + (r - 9) * math.cos(ang)), int(cy + (r - 9) * math.sin(ang))), 3)
    pts = [(cx, cy - r * 0.45), (cx + r * 0.38, cy + r * 0.3), (cx, cy + r * 0.12), (cx - r * 0.38, cy + r * 0.3)]
    pygame.draw.polygon(surf, ORANGE, pts, 2)

def draw_splash(surf, now):
    surf.fill(BLACK)
    k = min(1, (now - ui["start"]) / 2.5)
    img = cmdr_img()
    if img:
        r = img.get_rect(center=(W // 2, 105))
        surf.blit(img, r)
        pygame.draw.rect(surf, ORANGE, r.inflate(6, 6), 2, border_radius=4)
    else:
        draw_emblem(surf, W // 2, 110, 70, now)
    put(surf, F["small"], "CMDR", (W // 2, 200), DIM, anchor="center")
    put(surf, F["big"], cfg["cmdr"], (W // 2, 224), ORANGE, anchor="center")
    put(surf, F["small"], "PANEL DE MANDO  ·  ELITE DANGEROUS", (W // 2, 252), DIM, anchor="center")
    pygame.draw.rect(surf, DIM, (140, 280, 200, 8), 1)
    pygame.draw.rect(surf, ORANGE, (142, 282, int(196 * k), 4))

CMDR_IMG = [None]

def cmdr_img():
    if CMDR_IMG[0] is None:
        try:
            CMDR_IMG[0] = pygame.image.load(os.path.join(PANEL_DIR, "cmdr.jpg"))
        except Exception as e:
            print("foto:", e); CMDR_IMG[0] = False
    return CMDR_IMG[0]

IPC = {"ip": None, "t": 0}

def my_ip():
    import socket
    if time.time() - IPC["t"] > 30:
        IPC["t"] = time.time()
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sk.connect(("192.168.0.1", 9))
            IPC["ip"] = sk.getsockname()[0]
            sk.close()
        except OSError:
            IPC["ip"] = None
    return IPC["ip"]

IDLE_PHOTO = (66, 70)
IDLE_BOX = pygame.Rect(6, 150, W - 12, 152)
IDLE_SPEED = 14          # pixeles por segundo que suben las noticias

def idle_photo():
    img = cmdr_img()
    if not img:
        return None
    key = ("idlephoto", id(img))
    c = style["cache"]
    if key not in c:
        k = min(116 / img.get_width(), 120 / img.get_height(), 1.0)
        size = (int(img.get_width() * k), int(img.get_height() * k))
        c[key] = pygame.transform.smoothscale(img, size) if k < 1 else img
    return c[key]

def idle_crawl_lines():
    L = galnet["list"][:6]
    key = tuple(n["id"] for n in L)
    if galnet.get("crawl", (None,))[0] != key:
        out, w = [], IDLE_BOX.w - 16
        for n in L:
            for t in wrap_lines(F["btn"], n["title"], w):
                out.append((F["btn"], t, ORANGE, 21))
            out.append((F["small"], n["date"], BLUE, 17))
            body = [b for b in wrap_lines(F["small"], n["body"], w)]
            for t in body[:9]:
                out.append((F["small"], t, WHITE, 16))
            if len(body) > 9:
                out.append((F["small"], "...  (sigue en 12.9 GALNET)", DIM, 16))
            out.append((None, "", None, 22))
        galnet["crawl"] = (key, out, sum(h for *_, h in out))
    return galnet["crawl"][1], galnet["crawl"][2]

def idle_crawl_base(surf, now, box=None, waiting=True):
    box = box or IDLE_BOX
    pygame.draw.rect(surf, DIM, box, 1, border_radius=6)
    put(surf, F["small"], "NOTICIAS GALNET", (box.x + 8, box.y + 5), ORANGE)
    if power["now"] and int(now * 2) % 2 == 0:
        put(surf, F["small"], "BAJA TENSIÓN", (box.right - 8, box.y + 5), RED, anchor="topright")
        draw_bolt(surf, box.right - 108, box.y + 2, RED, 0.85)
    elif waiting and int(now) % 4 < 3 and not (state.get("data") or {}).get("menu"):
        t_ = "ESPERANDO A ELITE DANGEROUS"
        w_ = F["small"].size(t_)[0] + 14
        r_ = pygame.Rect(box.right - 6 - w_, box.y + 2, w_, 18)
        pygame.draw.rect(surf, RED, r_, border_radius=4)
        put(surf, F["small"], t_, r_.center, (255, 215, 0), anchor="center")
    pygame.draw.line(surf, DIM, (box.x + 6, box.y + 21), (box.right - 6, box.y + 21))
    area = pygame.Rect(box.x + 8, box.y + 24, box.w - 16, box.h - 28)
    lines, total = idle_crawl_lines()
    if not lines:
        put(surf, F["small"], galnet["err"] or "descargando noticias...", area.center, DIM, area.w, anchor="center")
        return
    off = (now * IDLE_SPEED) % total
    old = surf.get_clip()
    surf.set_clip(area)
    y = area.bottom - off
    while y < area.bottom:
        for f, t, col, h in lines:
            if area.y - h < y < area.bottom and f:
                put(surf, f, t, (area.x, int(y)), col, area.w)
            y += h
    surf.set_clip(old)
    fade = style["cache"].get("idlefade")
    if fade is None:
        fade = pygame.Surface((area.w, 12), pygame.SRCALPHA)
        for k in range(12):
            pygame.draw.line(fade, (0, 0, 0, 255 - k * 21), (0, k), (area.w, k))
        style["cache"]["idlefade"] = fade
    surf.blit(fade, (area.x, area.y))
    surf.blit(pygame.transform.flip(fade, False, True), (area.x, area.bottom - 12))



# ---------- 12.2 stream (OBS websocket v5) ----------
obs = {"ok": False, "err": "sin conectar", "scenes": [], "scene": None, "stream": False, "stime": "",
       "rec": False, "mic": None}
obs_cmds = queue.Queue()

def obs_loop():
    while True:
        try:
            import websocket
        except ImportError:
            obs["err"] = "falta python3-websocket"; time.sleep(30); continue
        if "XXX" in OBS_HOST:
            obs["err"] = "pon OBS_HOST en panel.py"; time.sleep(30); continue
        try:
            ws = websocket.create_connection(f"ws://{OBS_HOST}:{OBS_PORT}", timeout=4)
            hello = json.loads(ws.recv())["d"]
            ident = {"rpcVersion": 1, "eventSubscriptions": 0}
            auth = hello.get("authentication")
            if auth:
                sec = base64.b64encode(hashlib.sha256((OBS_PASSWORD + auth["salt"]).encode()).digest()).decode()
                ident["authentication"] = base64.b64encode(hashlib.sha256((sec + auth["challenge"]).encode()).digest()).decode()
            ws.send(json.dumps({"op": 1, "d": ident}))
            if json.loads(ws.recv()).get("op") != 2:
                raise RuntimeError("contraseña incorrecta")
            n = [0]
            def req(t, data=None):
                n[0] += 1; rid = str(n[0])
                ws.send(json.dumps({"op": 6, "d": {"requestType": t, "requestId": rid, "requestData": data or {}}}))
                while True:
                    m = json.loads(ws.recv())
                    if m.get("op") == 7 and m["d"].get("requestId") == rid:
                        return m["d"].get("responseData") or {}
            mic = OBS_MIC or req("GetSpecialInputs").get("mic1")
            obs.update(ok=True, err="", micname=mic)
            last_list = 0
            while True:
                while not obs_cmds.empty():
                    t, data = obs_cmds.get()
                    if t == "ToggleInputMute":
                        data = {"inputName": mic}
                    req(t, data)
                if time.time() - last_list > 5:
                    sl = req("GetSceneList")
                    obs["scenes"] = [x["sceneName"] for x in reversed(sl.get("scenes", []))][:8]
                    last_list = time.time()
                obs["scene"] = req("GetCurrentProgramScene").get("currentProgramSceneName")
                st = req("GetStreamStatus")
                obs["stream"], obs["stime"] = st.get("outputActive", False), (st.get("outputTimecode") or "")[:8]
                obs["rec"] = req("GetRecordStatus").get("outputActive", False)
                obs["mic"] = req("GetInputMute", {"inputName": mic}).get("inputMuted") if mic else None
                time.sleep(0.5)
        except Exception as e:
            obs.update(ok=False, err=(str(e) or type(e).__name__)[:40])
            time.sleep(5)

ST_CARD = TOP + 46
def scene_rect(i): return grid(i, 4, 2, ST_CARD, 246)
def sbtn_rect(i):  return grid(i, 3, 1, 246, H)

def tap_stream(x, y):
    for i, name in enumerate(obs["scenes"]):
        if scene_rect(i).collidepoint(x, y):
            tap_flash((122, i)); obs_cmds.put(("SetCurrentProgramScene", {"sceneName": name})); return
    for i, cmd in enumerate(["ToggleInputMute", "ToggleStream", "ToggleRecord"]):
        if sbtn_rect(i).collidepoint(x, y):
            if i == 0:
                tap_flash((122, 20)); obs_cmds.put((cmd, None)); return
            c, until = ui["confirm"]
            if c == cmd and time.time() < until:       # segundo toque: confirmar
                ui["confirm"] = (None, 0); tap_flash((122, 20 + i)); obs_cmds.put((cmd, None))
            else:
                ui["confirm"] = (cmd, time.time() + 3)
            return

def view_stream(surf, d, flags, now):
    card = pygame.Rect(4, TOP + 2, W - 8, ST_CARD - TOP - 4)
    pygame.draw.rect(surf, DIM, card, 1, border_radius=6)
    if not obs["ok"]:
        put(surf, F["btn"], "OBS: " + obs["err"], card.center, RED, card.w - 16, anchor="center")
    else:
        live = obs["stream"]
        if live and int(now * 2) % 2:
            pygame.draw.circle(surf, RED, (card.x + 16, card.y + 18), 7)
        put(surf, F["big"], ("EN DIRECTO  " + obs["stime"]) if live else "SIN EMITIR", (card.x + 30, card.y + 8), RED if live else DIM)
        if obs["rec"]:
            pygame.draw.circle(surf, RED, (card.right - 138, card.y + 17), 6)
            put(surf, F["btn"], "GRABANDO", (card.right - 126, card.y + 10), RED)
        mic = obs["mic"]
        put(surf, F["small"], "MICRO " + ("SILENCIADO" if mic else "ACTIVO" if mic is False else "?"),
            (card.right - 8, card.y + 30), RED if mic else GREEN, anchor="topright")
    for i, name in enumerate(obs["scenes"]):
        draw_button(surf, scene_rect(i), name, None, F["btn"], filled=name == obs["scene"],
                    lit=flash.get((122, i), 0) > now)
    if obs["ok"] and not obs["scenes"]:
        put(surf, F["btn"], "Sin escenas", (W // 2, (ST_CARD + 246) // 2), DIM, anchor="center")
    c, until = ui["confirm"]
    conf = c if time.time() < until else None
    labels = [("MICRO", "SILENCIAR" if obs["mic"] is False else "ACTIVAR", obs["mic"] is True),
              ("DIRECTO", "¿SEGURO?" if conf == "ToggleStream" else ("PARAR" if obs["stream"] else "EMPEZAR"), obs["stream"]),
              ("GRABAR", "¿SEGURO?" if conf == "ToggleRecord" else ("PARAR" if obs["rec"] else "EMPEZAR"), obs["rec"])]
    for i, (t, sub, on) in enumerate(labels):
        draw_button(surf, sbtn_rect(i), t, sub, F["btn"], filled=on, lit=flash.get((122, 20 + i), 0) > now,
                    dim=not obs["ok"])

VIEWS = {0: view_menux, 1: view_mandos, 2: view_pips, 3: view_navx_base, 4: view_carga, 5: view_srv, 6: view_combatx, 61: view_combatlog, 7: None, 71: view_explo_base, 72: view_orrery, 73: view_bio, 74: view_rings, 75: view_diary, 76: view_alien, 8: view_stationx,
         9: view_fighter, 10: view_mining_base, 11: view_session3, 100: view_live, 12: None, 121: view_log, 122: view_stream,
         123: view_ranks, 124: view_sub124_base, 1244: view_settings, 1245: view_changelog_base, 125: view_mats, 126: view_carrier, 127: view_market_base, 128: view_trip, 129: view_trip_detail}

# ---------- recogida de combustible ----------
scoop = {"hist": [], "was": False, "full_until": 0}

def fnum(v, nd=1):
    return f"{v:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def dur_s(sec):
    sec = max(0, int(sec))
    return f"{sec // 60}m {sec % 60:02d}s" if sec >= 60 else f"{sec} s"

def draw_scoop(surf, d, flags, now):
    fuel = ((d or {}).get("Fuel") or {}).get("FuelMain")
    cap = (d or {}).get("fuelcap")
    if (d or {}).get("Flags", 0) & (1 << 26):
        fuel, cap = ((d or {}).get("Fuel") or {}).get("FuelReservoir"), None
    on, hot = bool(flags & (1 << 11)), bool(flags & (1 << 20))
    if on and fuel is not None:
        h = scoop["hist"]; h.append((now, fuel))
        while now - h[0][0] > 6: h.pop(0)
    else:
        if scoop["was"] and fuel is not None and cap and fuel >= cap - 0.05:
            scoop["full_until"] = now + 4
        scoop["hist"] = []
    scoop["was"] = on
    full = now < scoop["full_until"]
    if not on and not full:
        return
    blink = int(now * 3) % 2 == 0
    col = GREEN if full and not on else (RED if hot and blink else ORANGE)
    for k in range(4):
        pygame.draw.rect(surf, col, (k * 3, k * 3, W - k * 6, H - k * 6), 2)
    box = pygame.Rect(24, 58, W - 48, 214)
    pygame.draw.rect(surf, BLACK, box)
    for j in range(12):
        yy = box.y + 10 + (j * 19) % (box.h - 20)
        ln = (j * 41 + int(now * 120)) % 90
        pygame.draw.line(surf, (90, 45, 0), (box.x + 8, yy), (box.x + 8 + ln, yy))
        pygame.draw.line(surf, (90, 45, 0), (box.right - 8 - ln, yy), (box.right - 8, yy))
    pygame.draw.rect(surf, col, box, 3, border_radius=8)
    cx, y = box.centerx, box.y + 14
    if full and not on:
        put(surf, F["num"], "DEPÓSITO LLENO", (cx, box.centery - 14), GREEN, box.w - 20, anchor="center")
        if fuel is not None:
            put(surf, F["btn"], f"{fnum(fuel)} t", (cx, box.centery + 26), WHITE, anchor="center")
        return
    put(surf, F["big"], "RECOGIENDO COMBUSTIBLE", (cx, y), ORANGE, box.w - 20, anchor="midtop"); y += 34
    if fuel is not None:
        put(surf, F["num"], f"{fnum(fuel)} / {fnum(cap) if cap else '?'} t", (cx, y), WHITE, box.w - 20, anchor="midtop"); y += 46
        bx = pygame.Rect(box.x + 20, y, box.w - 40, 18)
        pygame.draw.rect(surf, DIM, bx, 1)
        if cap:
            pct = max(0.0, min(1.0, fuel / cap))
            pygame.draw.rect(surf, ORANGE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * pct), bx.h - 4))
            put(surf, F["small"], f"{pct * 100:.0f}%", (bx.centerx, bx.y + 3), WHITE, anchor="midtop")
        y += 28
    h = scoop["hist"]
    if len(h) >= 2 and h[-1][0] - h[0][0] > 1:
        rate = (h[-1][1] - h[0][1]) / (h[-1][0] - h[0][0])
        put(surf, F["btn"], f"{fnum(rate, 2)} t/s", (box.x + 20, y), ORANGE)
        if rate > 0.001 and cap and fuel is not None:
            put(surf, F["btn"], f"lleno en {dur_s((cap - fuel) / rate)}", (box.right - 20, y), ORANGE, anchor="topright")
    y += 26
    if hot:
        put(surf, F["big"], "¡SOBRECALENTAMIENTO!", (cx, y), RED if blink else WHITE, box.w - 20, anchor="midtop")
    else:
        put(surf, F["small"], "temperatura OK", (cx, y + 6), GREEN, anchor="midtop")

# ---------- avisos extra: combustible en ruta, neutrones, gravedad ----------
xa = XaDict({"seq": None, "a": None})
NEON = (90, 200, 255)

def xa_notes(d, now):
    try:
        _xa_notes(d, now)
    finally:
        XA_K[0] = None

def _xa_notes(d, now):
    if not d:
        return
    XA_K[0] = "hplow"
    hp_ = (d.get("live") or {}).get("health")
    if d.get("Flags2", 0) & 1 and isinstance(hp_, (int, float)):
        lvl = 3 if hp_ < HP_CRIT else 2 if hp_ < 0.5 else 1 if hp_ < 0.75 else 0
        prev = xa.get("hplvl", 0)
        if lvl == 3 and prev < 3:
            if ev_on("hplow"):
                HPC["t0"] = now
                play("alarm")
        elif lvl > prev:
            xa["a"] = dict(until=now + (4 if lvl > 1 else 3), col=ORANGE if lvl == 1 else RED, title="SALUD BAJA",
                           big=f"{hp_ * 100:.0f} %", lines=["usa un botiquín" if lvl < 3 else "¡BOTIQUÍN YA!"])
            if lvl > 1:
                play("alarm")
        xa["hplvl"] = 0 if lvl == 0 else max(prev, lvl)
    else:
        xa["hplvl"] = 0
    taxi_watch(d, now)
    mega_watch(d, now)
    battle_watch(d, now)
    eng_watch(d, now)
    ver_check(d)
    uncl_watch(d, now)
    # avisos de peligro a pie y combustible del vehiculo (al empezar cada situacion)
    dg = xa.setdefault("dg", {})
    f2, fl = d.get("Flags2", 0), d.get("Flags", 0)
    L = d.get("live") or {}
    sf = (d.get("Fuel") or {}).get("FuelReservoir")
    foot = f2 & 1
    conds = {"oxy": foot and f2 & (1 << 6), "hp": foot and f2 & (1 << 7),
             "cold": foot and f2 & (1 << 10), "hot": foot and f2 & (1 << 11),
             "fuel": bool(fl & (1 << 26)) and sf is not None and sf < 0.1}
    for k, on in conds.items():
        if on and not dg.get(k):
            XA_K[0] = {"hp": "hplow", "cold": "temp", "hot": "temp", "fuel": "srvfuel"}.get(k, k)
            t = L.get("temp")
            tc = f"{t - 273.15:.0f} °C" if t is not None else ""
            msg = {"oxy": ("POCO OXÍGENO", f"{(L.get('oxy') or 0) * 100:.0f}%", "vuelve a la nave o recarga"),
                   "hp": ("SALUD BAJA", f"{(L.get('health') or 0) * 100:.0f}%", "usa un botiquín"),
                   "cold": ("FRÍO EXTREMO", tc, "busca refugio"),
                   "hot": ("CALOR EXTREMO", tc, "busca sombra o refugio"),
                   "fuel": ("COMBUSTIBLE DEL VEHÍCULO", f"{sf or 0:.2f} t".replace(".", ","), "vuelve a la nave a repostar")}[k]
            xa["a"] = dict(until=now + 6, col=RED if k != "cold" else (90, 200, 255), title=msg[0], big=msg[1], lines=[msg[2]])
        dg[k] = bool(on)
    notes = d.get("notes") or []
    if xa["seq"] is None:
        xa["seq"] = max([n[0] for n in notes], default=0); return
    for seq, kind, text in notes:
        if seq <= xa["seq"]:
            continue
        xa["seq"] = seq
        XA_K[0] = kind
        p = (text or "").split("|")
        if kind == "fuelroute" and len(p) >= 5:
            here = p[0] == "here"
            dest = f"{p[3]} saltos hasta {p[4]}" if p[4] else f"{p[3]} saltos y no hay estrellas recolectables"
            xa["a"] = dict(until=now + 8, col=ORANGE if here else RED,
                           title="RECOGE COMBUSTIBLE AQUÍ" if here else "¡NO LLEGAS A REPOSTAR!",
                           big=f"{p[1].replace('.', ',')} t / ~{p[2].replace('.', ',')} t",
                           lines=["tienes / necesitas", dest])
        elif kind == "jetcone":
            xa["a"] = dict(until=now + 6, col=NEON, title="FSD SOBREALIMENTADO",
                           big=f"ALCANCE x{p[0].replace('.', ',')}", lines=["el próximo salto llega mucho más lejos"])
        elif kind == "jetdmg":
            xa["a"] = dict(until=now + 6, col=RED, title="¡DAÑO EN EL FSD!", big="CHORRO DE NEUTRONES",
                           lines=[p[0] or "FSD", "revisa la salud del módulo"])
        elif kind == "matfull" and len(p) >= 2:
            xa["a"] = dict(until=now + 5, col=ORANGE, title="MATERIAL AL MÁXIMO", big=p[0],
                           lines=[f"{p[1]} / {p[1]}", "lo que recojas de más se pierde"])
        elif kind == "find" and len(p) >= 5:
            first = p[3] == "1"
            xa["a"] = dict(until=now + 7, col=GREEN if first else ORANGE,
                           title="¡1º DESCUBRIMIENTO!" if first else "HALLAZGO VALIOSO", big=p[0].upper(),
                           lines=[p[1], f"~{cr(float(p[2]))} cr  ·  mapeado ~{cr(float(p[4]))} cr"])
        elif kind == "codex" and len(p) >= 3:
            xa["a"] = dict(until=now + 6, col=(90, 200, 255), title="NUEVO EN EL CÓDICE", big=p[0],
                           lines=[p[1], p[2]])
        elif kind == "wanted" and len(p) >= 3:
            xa["a"] = dict(until=now + 6, col=RED, title="OBJETIVO BUSCADO", big=f"{cr(float(p[2] or 0))} cr",
                           lines=[p[0], p[1]])
        elif kind == "missionexp" and len(p) >= 2:
            xa["a"] = dict(until=now + 7, col=ORANGE, title="MISIÓN A PUNTO DE CADUCAR", big=f"{p[1]} min",
                           lines=[p[0], f"destino: {p[2]}" if len(p) > 2 and p[2] else ""])
        elif kind == "missionhere" and len(p) >= 2:
            n = int(p[0])
            xa["a"] = dict(until=now + 7, col=GREEN, title="ENTREGA AQUÍ", big=f"{n} MISIÓN" + ("ES" if n > 1 else ""),
                           lines=[p[1], "busca la estación de destino"])
        elif kind == "sessend" and len(p) >= 9:
            v = [float(x) for x in p]
            secs = int(v[1])
            xa["a"] = dict(until=now + 20, col=(90, 200, 255), title="SESIÓN TERMINADA", big=f"+{cr(v[0])} cr" if v[0] >= 1 else "SIN CRÉDITOS",
                           lines=[f"{secs // 3600}h {secs % 3600 // 60:02d}m  ·  {int(v[2])} saltos  ·  {int(v[3])} al",
                                  f"Expl. {cr(v[4])} · Bio {cr(v[5])} · Comercio {cr(v[6])} · Recomp. {cr(v[7])}" if v[0] >= 1 else "",
                                  f"Refinado: {int(v[8])} t" if v[8] else ""])
        elif kind == "lowcons" and len(p) >= 2:
            xa["a"] = dict(until=now + 6, col=ORANGE, title="QUEDAN POCOS", big=p[0].upper(),
                           lines=[f"te quedan {p[1]}", "repón en un asentamiento o estación"])
        elif kind == "crime" and len(p) >= 4:
            fine, bounty = float(p[1] or 0), float(p[2] or 0)
            xa["a"] = dict(until=now + 7, col=RED, title="DELITO COMETIDO", big=p[0].upper(),
                           lines=[(f"multa {cr(fine)} cr" if fine else "") + (f"  recompensa {cr(bounty)} cr" if bounty else ""), p[3]])
        elif kind == "taxi" and len(p) >= 4:
            xa["a"] = dict(until=now + 7, col=(90, 200, 255), title=p[0], big=p[2] or p[1],
                           lines=[p[1], f"coste {cr(float(p[3] or 0))} cr"])
        elif kind == "settle" and len(p) >= 5:
            rep = float(p[4]) if p[4] not in ("", "None") else None
            hostil = rep is not None and rep <= -35
            xa["a"] = dict(until=now + 7, col=RED if hostil else GREEN, title="ASENTAMIENTO", big=p[0],
                           lines=[f"{p[1]} · {p[2]}", ("HOSTIL HACIA TI" if hostil else (f"reputación {rep:+.0f}" if rep is not None else "")) + (f" · {p[3]}" if p[3] else "")])
        elif kind == "kill" and len(p) >= 3:
            rew = float(p[1] or 0)
            veh = p[3] if len(p) > 3 else "N"
            num = p[4] if len(p) > 4 and p[4].isdigit() and p[4] != "0" else ""
            name = "BAJA" if veh == "F" else "DERRIBO (SRV)" if veh == "S" else "DERRIBO"
            col = RED if p[2] == "P" else BLUE if p[2] in ("B", "T") else GREEN
            lines = [p[0]]
            if len(p) > 6 and p[6] not in ("", "0"):
                lines.append(f"{p[5]} sin cobrar  ·  {crx(float(p[6]))} cr")
            tot_ = p[7] if len(p) > 7 and p[7].isdigit() else ""
            if tot_:
                lab_ = "total" if veh == "F" else "bonos" if p[2] in ("B", "T") else "recompensas"
                name = (f"{name} nº {num}" if num else name) + f" · {lab_} {fnum(int(tot_), 0)}"
                num = ""
            xa["a"] = dict(until=now + 3, col=col, title=f"{name} nº {num}" if num else name,
                           big=f"+{crx(rew)} cr" if rew else "PvP", lines=lines)
        elif kind == "dropship":
            xa["a"] = dict(until=now + 6, col=ORANGE, title="TRANSPORTE A ZONA DE COMBATE",
                           big=(p[0] or "").upper(), lines=[p[1]] if len(p) > 1 and p[1] else [])
        elif kind == "deploy":
            st = {"War": "EN GUERRA", "CivilWar": "EN GUERRA CIVIL"}.get(p[2] if len(p) > 2 else "", p[2] if len(p) > 2 else "")
            sub = (f"Asentamiento de {p[1]}" if len(p) > 1 and p[1] else "") + (f"  ·  {st}" if st else "")
            xa["a"] = dict(until=now + 6, col=RED, title="¡DESPLEGADO!", big=(p[0] or "").upper(), lines=[sub] if sub else [])
        elif kind == "escaped" and len(p) >= 2:
            xa["a"] = dict(until=now + 5, col=GREEN, title="¡ESCAPADO!", big=p[0] or "INTERDICCIÓN",
                           lines=["era un comandante" if p[1] == "1" else "era un NPC"])
        elif kind == "submitted" and len(p) >= 2:
            xa["a"] = dict(until=now + 5, col=ORANGE, title="TE HAS SOMETIDO", big=p[0] or "INTERDICCIÓN",
                           lines=["COMANDANTE" if p[1] == "1" else "NPC", "carga el FSD y salta"])
        elif kind == "rebuy" and len(p) >= 2:
            xa["a"] = dict(until=now + 8, col=RED, title="CASCO CRÍTICO", big=f"{p[0]}%",
                           lines=[f"REBUY {cr(float(p[1] or 0))} cr", "considera huir"])
        elif kind == "arrive" and len(p) >= 5:
            nm, t_, body_, btype = p[0], int(p[1] or 0), p[2], p[3]
            if nm and (p[4] == "1" or btype == "Station"):
                xa["a"] = dict(until=now + 4, col=BLUE, title="LLEGADA A", big=nm.upper(), lines=[body_] if body_ and body_ != nm else [])
                if auto_on("arrst"):
                    ui["view"] = 8
            elif nm:
                conflict = "conflict" in nm.lower()
                xa["a"] = dict(until=now + 6, col=RED if conflict else threat_col(t_), title=f"SEÑAL  ·  AMENAZA {t_}",
                               big=nm.upper(), lines=["zona de conflicto" if conflict else "salida de supercrucero"])
                if t_ >= 3 or conflict:
                    play("alarm")
                    if auto_on("arrsig"):
                        ui["view"] = 6
            elif btype == "Station" and body_:
                xa["a"] = dict(until=now + 3, col=BLUE, title="LLEGADA A", big=body_.upper(), lines=[])
        elif kind == "thrown" and len(p) >= 3:
            mx_ = suit_max(d).get(cons_kind(p[0]) or "", None)
            xa["a"] = dict(until=now + 2, col=GREY, title=f"{p[1].upper()} LANZADO",
                           big=f"quedan {p[2]}" + (f" de {mx_}" if mx_ else ""), lines=[])
        elif kind == "opstart" and len(p) >= 2:
            xa["a"] = dict(until=now + 6, col=ORANGE, title="OPERACIÓN INICIADA", big=(p[0] or "").upper(),
                           lines=[f"escuadrón {p[1]}"] if p[1] else [])
            play("ok")
        elif kind == "opend" and len(p) >= 5:
            l1 = f"{p[0]} derribos  ·  {p[4]} min" + (f"  ·  +{p[3]} méritos" if p[3] not in ("", "0") else "")
            lm = (f"+{p[2]} MERC COIN", MERC) if p[2] not in ("", "0") else ""
            xa["a"] = dict(until=now + 12, col=GREEN, title="OPERACIÓN TERMINADA", big=f"{crx(float(p[1] or 0))} cr",
                           lines=[l1, lm, "cobra al salir, en una estación"])
            play("ok")
        elif kind == "pickup" and len(p) >= 3:
            xa["a"] = dict(until=now + 2.5, col=YELLOW if p[0] == "energycell" else GREEN if p[0] == "healthpack" else GREY,
                           title=f"+1 {p[1].upper()}", big=f"llevas {p[2]}", lines=[])
        elif kind == "usecons" and len(p) >= 3:
            left = int(p[2]) if p[2].isdigit() else -1
            xa["a"] = dict(until=now + (4 if left == 0 else 2.5), col=RED if left == 0 else ORANGE,
                           title=f"{p[1].upper()} USADO", big="¡NO TE QUEDAN!" if left == 0 else f"quedan {left}", lines=[])
            if left == 0:
                play("alarm")
        elif kind == "redeem" and len(p) >= 2:
            amt, tr = float(p[0] or 0), float(p[1] or 0)
            xa["a"] = dict(until=now + 7, col=GREEN, title="COBRADO", big=f"{crx(amt)} cr",
                           lines=[f"el panel llevaba sumados {crx(tr)} cr"] + ([f"diferencia {'+' if amt >= tr else ''}{crx(amt - tr)} cr"] if tr else []))
        elif kind == "died" and len(p) >= 4 and (((d or {}).get("footcz") or {}).get("onfoot") or (d or {}).get("Flags2", 0) & 1):
            xa["a"] = dict(until=now + 10, col=RED, title="HAS CAÍDO", big=p[0] or "",
                           lines=["al reaparecer en la zona conservas los bonos"])
        elif kind == "died" and len(p) >= 4:
            xa["a"] = dict(until=now + 15, col=RED, title="NAVE DESTRUIDA", big=p[0] or "?",
                           lines=[" · ".join(x for x in (p[1].replace("_", " ").title(), p[2]) if x), f"rebuy {cr(float(p[3] or 0))} cr"])
        elif kind == "cmdrtarget" and len(p) >= 3:
            ia_ = ((d or {}).get("target") or {}).get("inara") or {}
            l2_ = inara_line(ia_, d) if ia_ and not ia_.get("none") else "posible PvP"
            xa["a"] = dict(until=now + 6, col=ORANGE, title="COMANDANTE FIJADO", big=p[0],
                           lines=[" · ".join(x for x in (p[1], p[2]) if x), l2_])
        elif kind == "arrive" and len(p) >= 4:
            cur = xa.get("a")
            if not (cur and cur.get("title") == "SISTEMA SIN EXPLORAR" and now < cur["until"]):
                ui["alert"] = None
                scoop = p[2] == "1"
                xa["a"] = dict(until=now + 3, col=GREEN if scoop else ORANGE, title="LLEGADA", big=p[0].upper(),
                               lines=[f"{p[1]}  ·  {'RECOLECTABLE' if scoop else 'NO RECOLECTABLE'}",
                                      f"EDSM: {p[3]} cuerpos conocidos" if p[3] not in ("", "0") else "SIN DATOS EN EDSM"])
        elif kind == "newsys" and len(p) >= 1:
            ui["alert"] = None
            xa["a"] = dict(until=now + 6, col=GREEN, title="SISTEMA SIN EXPLORAR", big=p[0].upper(),
                           lines=["nadie ha descubierto esta estrella", "escanea todo con el FSS"])
        elif kind == "honk" and len(p) >= 3:
            n = int(p[0] or 0)
            known = int(p[2]) if p[2] not in ("", "None") else None
            info_ = "SIN DATOS EN EDSM: todo por descubrir" if not known else (
                f"EDSM conoce {known} · {max(0, n - known)} nuevos" if n > known else f"EDSM los conoce todos ({known})")
            xa["a"] = dict(until=now + 4, col=(90, 200, 255), title="ESCANEO DE DESCUBRIMIENTO", big=f"{n} CUERPOS",
                           lines=[f"{p[1]} señales", info_])
        elif kind == "risk" and len(p) >= 1:
            xa["a"] = dict(until=now + 6, col=ORANGE, title="DATOS EN RIESGO", big=f"{cr(float(p[0]))} cr",
                           lines=["llevas esto sin vender", "si te destruyen, se pierde"])
        elif kind == "alien" and len(p) >= 3:
            tgk = p[0] == "THARGOIDES"
            xa["a"] = dict(until=now + 6, col=(120, 230, 120) if tgk else (90, 200, 255), title=f"SEÑALES {p[0]}",
                           big=f"{p[1]} EN EL PLANETA", lines=[p[2], "míralas en 7.6 ALIENÍGENAS" if not tgk else "cuidado: posible actividad thargoide"])
        elif kind == "tgwar" and len(p) >= 4:
            pr = float(p[1] or 0)
            xa["a"] = dict(until=now + 6, col=RED if p[0] in ("INVASIÓN", "CONTROLADO", "BASTIÓN") else ORANGE,
                           title="GUERRA THARGOIDE", big=p[0], lines=[f"progreso {pr * 100:.0f}%" + (f" · puertos {p[2]}" if p[2] else ""), p[3]])
        elif kind == "friend" and len(p) >= 2:
            t = {"on": ("AMIGO CONECTADO", GREEN), "off": ("AMIGO DESCONECTADO", DIM), "req": ("SOLICITUD DE AMISTAD", BLUE)}.get(p[1])
            if t:
                xa["a"] = dict(until=now + 4, col=t[1], title=t[0], big=p[0], lines=[])
        elif kind == "wing" and len(p) >= 2:
            t = {"invite": "INVITACIÓN A ALA", "join": "TE HAS UNIDO A UN ALA", "add": "NUEVO EN TU ALA", "leave": "HAS SALIDO DEL ALA"}.get(p[1])
            if t:
                xa["a"] = dict(until=now + 4, col=BLUE, title=t, big=p[0] if p[0] != "-" else "", lines=[])
        elif kind == "cg" and len(p) >= 2:
            xa["a"] = dict(until=now + 6, col=GREEN, title="OBJETIVO COMUNITARIO", big=p[1].upper(), lines=[p[0]])
        elif kind == "shutdown":
            xa["a"] = dict(until=now + 8, col=(120, 230, 120), title="¡SISTEMAS APAGADOS!", big="ENCUENTRO THARGOIDE",
                           lines=["la nave se reiniciará en unos segundos"])
            play("alarm")
        elif kind == "thargmusic":
            xa["a"] = dict(until=now + 6, col=(120, 230, 120), title="ENCUENTRO THARGOIDE",
                           big="MÚSICA DE ALERTA", lines=["el juego ha puesto la música thargoide"])
            play("alarm")
        elif kind == "scanned" and len(p) >= 4:
            bad = p[2] == "1"
            xa["a"] = dict(until=now + 5, col=RED if bad else ORANGE, title="TE ESCANEAN",
                           big=SCAN_ES.get(p[0], p[0].upper()),
                           lines=[x for x in ((f"probablemente {p[1]}" if p[1] else ""),
                                              ("¡LLEVAS CARGA ILEGAL O ROBADA!" if bad else "")) if x])
            if bad:
                play("alarm")
        elif kind == "engbase" and eng_by_base(text):
            eb_ = eng_by_base(text)
            st_, _ = eng_status(eb_, d)
            xa["a"] = dict(until=now + 6, col=BLUE, title="BASE DE INGENIERO", big=eb_["name"].upper(),
                           lines=[f"{eb_['base']}  ·  {st_}", "mira tus materiales en 12 > MATERIALES"])
            if auto_on("docking"):
                ui["view"] = 125
        elif kind == "shipswap":
            ui["shipcard"] = now + 15; ui["shippage"] = 0
        elif kind == "shipxfer" and len(p) >= 2:
            sec = int(p[1] or 0)
            xa["a"] = dict(until=now + 6, col=BLUE, title="TRANSFERENCIA EN CAMINO", big=p[0].upper(),
                           lines=[f"llega en {sec // 3600} h {sec % 3600 // 60} min" if sec >= 3600 else f"llega en {sec // 60} min"])
        elif kind == "shiparrived" and len(p) >= 2:
            xa["a"] = dict(until=now + 8, col=GREEN, title="NAVE TRANSFERIDA", big=f"TU {p[0].upper()} YA ESTÁ",
                           lines=[f"en {p[1]}" if p[1] else ""])
            play("ok")
        elif kind == "moddmg" and len(p) >= 2:
            xa["a"] = dict(until=now + 8, col=ORANGE, title="MÓDULOS DAÑADOS (< 80 %)", big=f"{p[0]} MÓDULO" + ("S" if p[0] != "1" else ""),
                           lines=[p[1], "repara en una estación"])
        elif kind == "gravity" and len(p) >= 2:
            g = float(p[0])
            xa["a"] = dict(until=now + 7, col=RED if g >= 2 else ORANGE, title="GRAVEDAD ALTA",
                           big=f"{p[0].replace('.', ',')} G", lines=[p[1], "aterriza despacio" if g >= 2 else ""])

MERC = (255, 80, 200)      # rosa de las Merc Coin, como en el juego


PANEL_VER = "v1.1 · 11/11/2026 17:48"

# ---------- estilo CABINA (decoracion, se cambia en SESION) ----------
STYLE_FILE = os.path.join(PANEL_DIR, "estilo.txt")

def style_load():
    try:
        return open(STYLE_FILE).read().strip() == "cabina"
    except OSError:
        return False

style = {"cab": style_load(), "view": None, "vt": 0.0, "cache": {}}
STYLE_BTN = pygame.Rect(W - 160, H - 58, 152, 52)
HOLO = (90, 200, 255)

def style_toggle():
    style["cab"] = not style["cab"]
    try:
        with open(STYLE_FILE, "w") as f:
            f.write("cabina" if style["cab"] else "clasico")
    except OSError:
        pass

_orig_rect = pygame.draw.rect

def _cab_rect(surf, col, rect, width=0, border_radius=0, *a, **k):
    """En modo CABINA los rectangulos redondeados pasan a esquinas cortadas."""
    if style["cab"] and border_radius and border_radius > 0:
        r = pygame.Rect(rect)
        c = max(3, min(10, r.h // 3, r.w // 3))
        pts = [(r.x + c, r.y), (r.right - 1, r.y), (r.right - 1, r.bottom - 1 - c),
               (r.right - 1 - c, r.bottom - 1), (r.x, r.bottom - 1), (r.x, r.y + c)]
        return pygame.draw.polygon(surf, col, pts, width)
    return _orig_rect(surf, col, rect, width, border_radius, *a, **k)

pygame.draw.rect = _cab_rect

def _cached(key, make):
    c = style["cache"]
    if key not in c:
        c[key] = make()
    return c[key]

def _scan():
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(0, H, 3):
        pygame.draw.line(s, (0, 0, 0, 55), (0, y), (W, y))
    return s

def _hexes():
    s = pygame.Surface((W, H - TOP), pygame.SRCALPHA)
    r = 16
    dx, dy = r * 1.732, r * 1.5
    for row in range(int((H - TOP) / dy) + 2):
        for col in range(int(W / dx) + 2):
            cx = col * dx + (dx / 2 if row % 2 else 0)
            cy = row * dy
            pts = [(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]
            pygame.draw.polygon(s, (255, 140, 0, 16), pts, 1)
    return s

def _dots():
    s = pygame.Surface((W, H - TOP), pygame.SRCALPHA)
    for y in range(8, H - TOP, 16):
        for x in range(8, W, 16):
            s.set_at((x, y), (255, 140, 0, 60))
    return s

def _tint(col):
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((col[0], col[1], col[2], 22))
    return s

def _stars():
    import random
    rnd = random.Random(7)
    return [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(4, 25), rnd.randint(60, 200)) for _ in range(45)]

def decorate(surf):
    now = time.time()
    v = ui["view"]
    splash = now - ui["start"] < 3
    if False:
        draw_button(surf, STYLE_BTN, "ESTILO", "CABINA" if style["cab"] else "CLÁSICO", F["small"], filled=style["cab"])
    if not style["cab"]:
        return
    with lock:
        d, rx = state["data"], state["rx"]
    online = d is not None and now - rx < 5
    if v != style["view"]:
        style["view"], style["vt"] = v, now
    if ui["idle_on"]:
        # 8: estrellas y marco holografico de la foto
        for x0, y0, sp, b in _cached("stars", _stars):
            x = (x0 + now * sp) % W
            if y0 > 146:
                continue
            surf.set_at((int(x), int(y0)), (b, b, b))
        r = pygame.Rect(0, 0, 124, 128); r.center = IDLE_PHOTO
        k = 0.5 + 0.5 * math.sin(now * 2)
        col = tuple(int(c * (0.4 + 0.6 * k)) for c in HOLO)
        for (x, y), (sx, sy) in (((r.left, r.top), (1, 1)), ((r.right, r.top), (-1, 1)),
                                 ((r.left, r.bottom), (1, -1)), ((r.right, r.bottom), (-1, -1))):
            pygame.draw.line(surf, col, (x, y), (x + 16 * sx, y), 2)
            pygame.draw.line(surf, col, (x, y), (x, y + 16 * sy), 2)
        yy = r.top + int((now * 40) % r.h)
        pygame.draw.line(surf, col, (r.left + 4, yy), (r.right - 4, yy), 1)
    elif not splash:
        if online:
            flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
            # 6: fondo tenue segun el modo
            ground = f2 & 1 or flags & (1 << 26)
            surf.blit(_cached("dots" if ground else "hex", _dots if ground else _hexes), (0, TOP))
            # 7: tinte segun la situacion
            L = d.get("live") or {}
            hull = (L.get("ship") or {}).get("hull")
            danger = L.get("legal") in ("Wanted", "Hostile", "Warrant") or (hull is not None and hull < 0.3)
            cols = border_cols(d)
            if cols:
                surf.blit(_cached(("tint", tuple(cols[0][:3])), lambda: _tint(cols[0])), (0, 0))
        # 3: barra superior con barrido y piloto de datos
        p = (now * 160) % (W + 200) - 100
        for x in range(0, W, 3):
            b = max(0.25, 1 - abs(x - p) / 90)
            pygame.draw.line(surf, tuple(int(c * b) for c in ORANGE[:3]), (x, TOP - 2), (x + 2, TOP - 2))
        fresh = online and now - rx < 0.6
        pygame.draw.circle(surf, GREEN if fresh else DIM, (W - 5, TOP - 8), 3)
        # 5: barrido al cambiar de pantalla
        dt = now - style["vt"]
        if dt < 0.35:
            x = int(W * dt / 0.35)
            _orig_rect(surf, BLACK, (x, TOP, W - x, H - TOP))
            pygame.draw.line(surf, ORANGE, (x, TOP), (x, H), 2)
    # 2: lineas de escaneo y franja que baja
    surf.blit(_cached("scan", _scan), (0, 0))
    yy = int((now * 35) % H)
    band = _cached("band", lambda: pygame.Surface((W, 3), pygame.SRCALPHA))
    band.fill((255, 170, 60, 28))
    surf.blit(band, (0, yy))

