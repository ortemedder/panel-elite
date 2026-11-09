#!/usr/bin/env python3
# Parche v1.0 beta 10 (desde la beta 9): boton FIJAR/SEGUIR con los logos de Elite y mas pequeno, actividad galactica
# encendida por defecto (si la Pi tiene python3-zmq), RADAR y ACTIVIDAD en el menu 7, avisos de influencia, flechas de
# tendencia, tocar el radar abre la ficha, tus sistemas brillan en la actividad, contador del dia, boton IR (copia el
# sistema al portapapeles del PC), estado del escucha del pueblo en AJUSTES y hora corregida al arrancar.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def b10_hold_img" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b9', s):
    sys.exit("Este parche es para la v1.0 beta 9")
shutil.copy(P, P + ".bak100b9")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# radar de la faccion: guarda donde queda cada sistema (para tocarlo) y flechas de tendencia en CONTROLADOS
rep('''    ps = [v for v in S if v.get("pos") and None not in v["pos"]]
    used = []
    if ps:''', '''    ps = [v for v in S if v.get("pos") and None not in v["pos"]]
    used = []
    RADAR_PTS.clear()
    if ps:''')
rep('''            px, py = int(c[0] + dx * rad * 0.88), int(c[1] - dz * rad * 0.88)
            war = fac_war(v)''', '''            px, py = int(c[0] + dx * rad * 0.88), int(c[1] - dz * rad * 0.88)
            RADAR_PTS.append((px, py, v["sys"]))
            war = fac_war(v)''')
rep('''        put(surf, F["tiny"], f"{v['inf']:.0f}%", (W - 8, y), GREEN if g >= 5 else RED, anchor="topright")
        y += 14''', '''        put(surf, F["tiny"], f"{v['inf']:.0f}%", (W - 8, y), GREEN if g >= 5 else RED, anchor="topright")
        trend_arrow(surf, v, W - 44, y + 3)
        y += 14''')
# alertas del radar: tambien influencia baja y rival cerca
rep('''    war = [v for v in S if fac_war(v)]
    if war:''', '''    war = [v for v in S if fac_war(v)] + [v for v in S if not fac_war(v) and inf_warn(v)]
    if war:''')
rep('''        for v in war[:4]:
            cf = (v.get("conflictos") or [{}])[0]''', '''        for v in war[:4]:
            if not fac_war(v):
                t1, t2 = inf_warn(v)
                put(surf, F["small"], t1 + " · " + v["sys"], (X + 8, yy), WHITE, box.w - 16)
                put(surf, F["tiny"], t2, (X + 8, yy + 14), ORANGE, box.w - 16)
                yy += 30; continue
            cf = (v.get("conflictos") or [{}])[0]''')
# actividad: en la vista del menu 7 tambien se cambia galaxia/zona tocando el mapa
rep('''    gal = ACT_GAL[0] if IDLEHOLD["m"] == "act" else int(now // 10) % 2 == 0   # 10 s galaxia, 10 s tu zona (o fija)''',
    '''    gal = ACT_GAL[0] if IDLEHOLD["m"] == "act" or ui.get("view") == 78 else int(now // 10) % 2 == 0   # 10 s galaxia, 10 s tu zona (o fija)''')
# actividad: saltos a tus sistemas (brillo + contador del dia)
rep('''                ACT["feed"].appendleft((nm, mine, now))''', '''                ACT["feed"].appendleft((nm, mine, now))
                if mine:
                    act_mine_hit(nm, x, z, now)''')
rep('''    put(surf, F["small"], "EN TUS SISTEMAS HOY", (X, y), DIM); put(surf, F["big"], str(ent), (W - 8, y + 10), ORANGE, anchor="topright"); y += 40''',
    '''    put(surf, F["small"], "TUS SISTEMAS HOY", (X, y), DIM); put(surf, F["big"], str(ent), (W - 8, y + 10), ORANGE, anchor="topright")
    put(surf, F["tiny"], f"comandantes · {ACT_DAY.get(hoyk, 0)} salto{'' if ACT_DAY.get(hoyk, 0) == 1 else 's'} visto{'' if ACT_DAY.get(hoyk, 0) == 1 else 's'}", (X, y + 40), DIM, W - X - 8); y += 54''')
rep('''    surf.set_clip(old)
    X, y = 314, 58
    j = ACT["jumps"]''', '''    act_hit_draw(surf, M, pt, now)
    surf.set_clip(old)
    X, y = 314, 58
    j = ACT["jumps"]''')
rep('''    for nm, mine, t in list(ACT["feed"])[:6]:''', '''    for nm, mine, t in list(ACT["feed"])[:5]:''')

CODE = r'''
# ---------- v1.0 beta 10 ----------
# --- boton FIJAR / SEGUIR con los logos (boton_seguir.png y boton_fijado.png junto a panel.py) ---
_BIMG, _BIMGC = {}, {}

def b10_hold_img(name):
    if name not in _BIMG:
        try:
            _BIMG[name] = pygame.image.load(os.path.join(PANEL_DIR, name))
        except Exception:
            _BIMG[name] = None
    return _BIMG[name]

def hold_rect(m):
    return pygame.Rect(430, 24, 46, 38) if m == "norm" else pygame.Rect(W - 50, 4, 46, 38)

def draw_hold(surf, m, now):
    r = hold_rect(m)
    held = IDLEHOLD["m"] is not None
    src = b10_hold_img("boton_fijado.png" if held else "boton_seguir.png")
    pygame.draw.rect(surf, BLACK, r, border_radius=4)
    if src is not None:
        ir = pygame.Rect(r.x, r.y, r.w, 28)
        real, rr = (surf.real, surf._r(ir)) if type(surf).__name__ == "ScaledSurf" else (surf, ir)
        k = (id(src), rr.w, rr.h)
        if k not in _BIMGC:
            try:
                _BIMGC[k] = pygame.transform.smoothscale(src, (rr.w, rr.h))
            except ValueError:
                _BIMGC[k] = pygame.transform.scale(src, (rr.w, rr.h))
        real.blit(_BIMGC[k], rr.topleft)
    elif held:
        cx, cy = r.centerx, r.y + 14
        pygame.draw.polygon(surf, WHITE, [(cx - 5, cy - 7), (cx - 5, cy + 7), (cx + 6, cy)])
    else:
        cx, cy = r.centerx, r.y + 14
        pygame.draw.rect(surf, ORANGE, (cx - 5, cy - 7, 4, 14)); pygame.draw.rect(surf, ORANGE, (cx + 1, cy - 7, 4, 14))
    col = (RED if int(now * 2) % 2 else (120, 0, 0)) if held else ORANGE
    pygame.draw.rect(surf, col, r, 1, border_radius=4)
    put(surf, F["tiny"], "SEGUIR" if held else "FIJAR", (r.centerx, r.bottom - 5), WHITE if held else ORANGE, anchor="center")

# --- actividad: encendida por defecto si la Pi tiene python3-zmq (se apaga con "actividad": false en el cfg) ---
def act_enabled():
    if cfg.get("actividad") is not None:
        return cfg["actividad"]
    return act_ok()

# --- avisos de influencia y flechas de tendencia ---
INF_MIN = 40.0                                          # aviso si un sistema controlado baja de este %
INF_GAP = 5.0                                           # o si la segunda faccion se acerca a menos de estos puntos
INFW = set()

def inf_warn(v):
    """(titulo, detalle) si un sistema controlado esta en peligro, o None."""
    if not v.get("ctrl") or not v.get("inf"):
        return None
    g = v["inf"] - (v.get("segunda_inf") or 0)
    if g < INF_GAP:
        return "RIVAL CERCA", f"{v.get('segunda') or 'otra facción'} a {g:.1f} puntos ({v['inf']:.1f} %)".replace(".", ",")
    if v["inf"] < INF_MIN:
        return "INFLUENCIA BAJA", f"{v['inf']:.1f} % (aviso por debajo del {INF_MIN:.0f} %)".replace(".", ",")
    return None

def trend_arrow(surf, v, x_, y_):
    if v.get("prev") is None or abs(v["inf"] - v["prev"]) < 0.1:
        return
    up = v["inf"] > v["prev"]
    pygame.draw.polygon(surf, GREEN if up else RED,
                        [(x_, y_ + 5), (x_ + 8, y_ + 5), (x_ + 4, y_)] if up else [(x_, y_), (x_ + 8, y_), (x_ + 4, y_ + 5)])

_fac_watch_b10 = fac_watch

def fac_watch(now):
    _fac_watch_b10(now)
    D = FACD["data"]
    if not D:
        return
    hoyk = time.strftime("%Y-%m-%d", time.gmtime())
    for n, v in (D.get("sistemas") or {}).items():
        w_ = inf_warn(v)
        if w_ and (n, w_[0], hoyk) not in INFW:
            INFW.add((n, w_[0], hoyk))
            fw_alert(w_[0], n, [w_[1]], f"{w_[0].lower()} en {n}")

# --- actividad: tus sistemas brillan y contador de saltos del dia ---
ACT_HIT = {"n": None, "x": 0, "z": 0, "t": 0}
ACT_DAY_F = os.path.join(PANEL_DIR, "actividad_hoy.json")
try:
    ACT_DAY = json.load(open(ACT_DAY_F))
except Exception:
    ACT_DAY = {}

def act_mine_hit(nm, x, z, now):
    ACT_HIT.update(n=nm, x=x, z=z, t=now)
    k = time.strftime("%Y-%m-%d", time.gmtime(now))
    for d_ in [d_ for d_ in ACT_DAY if d_ != k]:
        ACT_DAY.pop(d_, None)
    ACT_DAY[k] = ACT_DAY.get(k, 0) + 1
    try:
        json.dump(ACT_DAY, open(ACT_DAY_F, "w"))
    except OSError:
        pass

def act_hit_draw(surf, M, pt, now):
    age = now - ACT_HIT["t"]
    if not ACT_HIT["n"] or age > 10 or age < 0:
        return
    px, py = pt(ACT_HIT["x"], ACT_HIT["z"])
    if M.collidepoint(px, py):
        f_ = 1 - age / 10
        for k in range(3):
            rr = int(4 + ((age * 14 + k * 6) % 18))
            pygame.draw.circle(surf, tuple(int(c * f_) for c in ORANGE), (int(px), int(py)), rr, 1)
        pygame.draw.circle(surf, ORANGE, (int(px), int(py)), 4)
    nm = ACT_HIT["n"].upper()
    b = pygame.Rect(M.x + 6, M.bottom - 26, M.w - 12, 20)
    pygame.draw.rect(surf, (40, 22, 0), b, border_radius=4)
    pygame.draw.rect(surf, ORANGE if int(now * 3) % 2 else (140, 80, 0), b, 1, border_radius=4)
    put(surf, F["small"], "COMANDANTE EN " + nm, b.center, ORANGE, b.w - 10, anchor="center")

# --- menu 7: RADAR y ACTIVIDAD (pantallas enteras con boton para volver) ---
MENU[77] = "RADAR DE LA FACCIÓN"
MENU[78] = "ACTIVIDAD GALÁCTICA"
PARENT[77] = PARENT[78] = 7
RADAR_PTS = []
FULL_BACK = pygame.Rect(W - 50, 4, 46, 38)

def view_sub7(surf, d, flags, now):
    for i, (n, name) in enumerate([("1", "EXPLORACIÓN"), ("2", "SISTEMA"), ("3", "EXOBIO"), ("4", "YACIM."), ("5", "DIARIO"),
                                   ("6", "ALIEN"), ("7", "RADAR"), ("8", "ACTIVIDAD")]):
        draw_button(surf, grid(i, 4, 2), n, name, F["num"], lit=flash.get((7, i), 0) > now)

def view_full(surf, d, flags, now):
    v = ui.get("view")
    D, S, gap = fac_rows()
    if v == 77 and not S:
        surf.fill(BLACK)
        put(surf, F["btn"], "sin datos de la facción", (W // 2, H // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], FACD["err"] or "descargando…", (W // 2, H // 2 + 14), DIM, W - 16, anchor="center")
    elif v == 77:
        draw_fac_screen(surf, now)
    else:
        draw_act_screen(surf, now)
    r = FULL_BACK
    pygame.draw.rect(surf, BLACK, r, border_radius=4)
    pygame.draw.rect(surf, ORANGE, r, 1, border_radius=4)
    put(surf, F["btn"], "<", (r.centerx, r.y + 13), ORANGE, anchor="center")
    put(surf, F["tiny"], "MENÚ 7", (r.centerx, r.bottom - 6), ORANGE, anchor="center")

VIEWS[7] = view_sub7
VIEWS[77] = VIEWS[78] = view_full

# --- ficha del sistema: boton IR (copia el nombre al portapapeles del PC) ---
IR_R = pygame.Rect(W - 76, TOP + 3, 72, 20)

def ir_draw(surf, now):
    D, name, v = fs_get()
    if not name:
        return
    lit = flash.get(("ir", 0), 0) > now
    pygame.draw.rect(surf, ORANGE if lit else BLACK, IR_R, border_radius=4)
    pygame.draw.rect(surf, ORANGE, IR_R, 1, border_radius=4)
    put(surf, F["small"], "IR  >", IR_R.center, BLACK if lit else ORANGE, anchor="center")

def ir_send(name):
    pc = pc_addr()
    if not pc:
        set_alert("NO SÉ LA IP DEL PC", "el sender no está enviando", RED, 3); return
    try:
        so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        so.sendto(("ELITEPANEL-CLIP|" + name).encode("utf-8"), (pc, 5006)); so.close()
        set_alert("COPIADO EN EL PC", f"{name}: Ctrl+V en el mapa galáctico", GREEN, 4, kind="info")
    except OSError as e:
        set_alert("NO SE PUDO COPIAR", str(e)[:40], RED, 3)

for _v in (194, 195, 196):
    def _mk(fn):
        def _f(surf, d, flags, now):
            fn(surf, d, flags, now)
            ir_draw(surf, now)
        return _f
    VIEWS[_v] = _mk(VIEWS[_v])

# --- AJUSTES: estado del escucha del pueblo (boton 8) ---
def pueblo_estado(now):
    D = FACD["data"] or {}
    e = D.get("eddn") or {}
    t = D.get("t") or 0
    if not D:
        return "SIN DATOS", RED, "no se ha podido descargar " + (FACD["err"] or "")
    age = now - t if t else None
    ok = bool(e.get("ok")) and age is not None and age < 7 * 3600
    a_ = "?" if age is None else f"{int(age // 60)} min" if age < 3600 else f"{age / 3600:.0f} h"
    sub = "OK" if ok else a_ if age is not None else "?"
    det = (f"EDDN {'conectado' if e.get('ok') else 'desconectado'} · {e.get('msgs', 0):,} mensajes".replace(",", ".")
           + f" · datos de hace {a_}" + (f" · bajado hace {int((now - FACD['t']) // 60)} min" if FACD.get("t") else ""))
    return sub, GREEN if ok else RED, det

def view_sub124(surf, d, flags, now):
    _view_sub124_b10(surf, d, flags, now)
    sub, col, det = pueblo_estado(now)
    draw_button(surf, grid(7, 4, 2), "8", "PUEBLO " + sub, F["num"], filled=col == GREEN, lit=flash.get((1240, 7), 0) > now)

_view_sub124_b10 = VIEWS[124]
VIEWS[124] = view_sub124

# --- hora: al arrancar fuerza la sincronizacion; si no hay NTP, la toma de un servidor web ---
def hora_loop():
    import subprocess, http.client, email.utils
    time.sleep(5)
    def synced():
        try:
            return subprocess.run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], capture_output=True,
                                  text=True, timeout=10).stdout.strip() == "yes"
        except Exception:
            return False
    try:
        subprocess.run(["timedatectl", "set-ntp", "true"], capture_output=True, timeout=15)
        subprocess.run(["systemctl", "restart", "systemd-timesyncd"], capture_output=True, timeout=30)
    except Exception as e:
        plog("Hora: no puedo reiniciar timesyncd:", e)
    for _ in range(20):
        if synced():
            plog("Hora: sincronizada por NTP"); return
        time.sleep(3)
    for host in ("raw.githubusercontent.com", "www.google.com", "cloudflare.com"):
        try:
            c_ = http.client.HTTPConnection(host, 80, timeout=10)
            t0 = time.time(); c_.request("HEAD", "/"); r_ = c_.getresponse(); t1 = time.time()
            dt = r_.getheader("Date"); c_.close()
            if not dt:
                continue
            web = email.utils.parsedate_to_datetime(dt).timestamp() + (t1 - t0) / 2
            dif = web - time.time()
            if abs(dif) < 60:
                plog(f"Hora: sin NTP, pero bien ({dif:+.0f} s con {host})"); return
            subprocess.run(["date", "-s", "@%d" % int(web)], capture_output=True, timeout=10)
            plog(f"Hora: corregida {dif:+.0f} s con {host} (sin NTP)")
            set_alert("HORA CORREGIDA", f"{dif / 60:+.0f} min · tomada de {host}", ORANGE, 6, kind="info")
            return
        except Exception as e:
            plog("Hora:", host, e)
    plog("Hora: no he podido comprobarla")

threading.Thread(target=hora_loop, daemon=True, name="hora").start()

# --- render: pantallas enteras del menu 7 ---
_render_b10 = render

def render(surf):
    v = ui.get("view")
    if v not in (77, 78):
        return _render_b10(surf)
    with lock:
        d, rx = state["data"], state["rx"]
    now = time.time()
    online = d is not None and now - rx < 5
    ui["idle_on"] = False
    try:
        if online and not HI_PASS[0]:
            glow_watch(d); binds_check(d); process_notes(d); track_update(d, now)
        fac_watch(now)
    except Exception as e:
        log_exc("menú 7 datos", e)
    try:
        view_full(surf, d, (d or {}).get("Flags", 0) if online else 0, now)
    except Exception as e:
        log_exc("menú 7 " + str(v), e); surf.fill(BLACK)
        put(surf, F["btn"], "error, mira el LOG", (W // 2, H // 2), RED, anchor="center")
        pygame.draw.rect(surf, ORANGE, FULL_BACK, 1, border_radius=4)
    if online and not HI_PASS[0]:
        try:
            xa_notes(d, now)
        except Exception:
            pass
    draw_xa(surf, now)
    if ui.get("alert") and now < ui["alert"]["until"]:
        draw_alert(surf, now)

# --- toques ---
_on_tap_b10 = on_tap

def radar_hit(x, y):
    best = None
    for px, py, n in RADAR_PTS:
        d_ = math.hypot(px - x, py - y)
        if d_ < 16 and (best is None or d_ < best[0]):
            best = (d_, n)
    return best[1] if best else None

def on_tap(x, y):
    v = ui.get("view")
    if v == 7 and not ui.get("idle_on"):
        for i in range(8):
            if grid(i, 4, 2).collidepoint(x, y):
                tap_flash((7, i)); ui["view"] = 71 + i
                if i == 7:
                    ACT_GAL[0] = True
                TAP_EV.set(); return
        return
    if v in (77, 78):
        if FULL_BACK.inflate(10, 10).collidepoint(x, y):
            ui["view"] = 7; TAP_EV.set(); return
        if v == 77:
            n = radar_hit(x, y)
            if n:
                ui["facsys"] = n; ui["facback"] = 77; ui["view"] = 194; TAP_EV.set()
            return
        if ACT_MAP.collidepoint(x, y):
            ACT_GAL[0] = not ACT_GAL[0]; TAP_EV.set()
        return
    if v in (194, 195, 196) and IR_R.inflate(6, 6).collidepoint(x, y):
        D, name, vv = fs_get()
        if name:
            tap_flash(("ir", 0)); ir_send(name); TAP_EV.set()
        return
    if v == 124 and grid(7, 4, 2).collidepoint(x, y):
        tap_flash((1240, 7))
        sub, col, det = pueblo_estado(time.time())
        set_alert("ESCUCHA DEL PUEBLO", det, col, 6, kind="info"); TAP_EV.set(); return
    if ui.get("idle_on") and IDLE_MODE["m"] == "fac" and not hold_rect("fac").inflate(10, 10).collidepoint(x, y):
        n = radar_hit(x, y)
        if n:
            ui["idle_skip"] = time.time() + 60
            ui["facsys"] = n; ui["facback"] = 192; ui["view"] = 194; TAP_EV.set(); return
    _on_tap_b10(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 10
- Pantalla de espera: el botón FIJAR / SEGUIR es más pequeño y lleva el logo de Elite (negro al girar, con el planeta rojo cuando está fijada).
- Menú 7 EXPLORACIÓN: botones 7 RADAR (pantalla de tu facción) y 8 ACTIVIDAD (EDDN en directo). A pantalla entera; el botón de arriba a la derecha vuelve al menú 7. En RADAR, tocar un sistema abre su ficha; en ACTIVIDAD, tocar el mapa cambia entre galaxia y tu zona.
- Radar de la facción (también en la pantalla de espera): tocar un sistema abre su ficha. Flechas de tendencia de la influencia en los controlados.
- Aviso (con voz) si un sistema controlado baja del 40 % o la segunda facción se acerca a menos de 5 puntos; sale también en ALERTAS del radar.
- Actividad galáctica: encendida por defecto si la Pi tiene python3-zmq (también en la Pi 3). Cuando alguien salta a uno de tus sistemas, el punto brilla y sale «COMANDANTE EN …». Contador de saltos vistos hoy en tus sistemas.
- Ficha del sistema: botón IR. Copia el nombre al portapapeles del PC; en el mapa galáctico, Ctrl+V. Necesita el sender v1.0b5.
- AJUSTES (menú 12 > 4): botón 8 PUEBLO con el estado del escucha (OK y hace cuánto llegaron datos). Tocarlo da el detalle.
- Al arrancar, la Pi sincroniza la hora; si no hay NTP, la toma de un servidor web y avisa con HORA CORREGIDA.
# Enlace energético''')
rep('    ("1.0b9", ', '    ("1.0b10", "Logos en FIJAR, RADAR y ACTIVIDAD en el menú 7, avisos de influencia, IR, estado del pueblo y hora"),\n    ("1.0b9", ')
s = re.sub(r'PANEL_VER = "v1\.0b9[^"]*"', 'PANEL_VER = "v1.0b10 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 10  (copia en " + P + ".bak100b9)")
