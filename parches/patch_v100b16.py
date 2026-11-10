#!/usr/bin/env python3
# Parche v1.0 beta 16 (desde la beta 15): EMITIR sin que suba la memoria (Pi 3 de KORZO), reloj de atraque desde 9:59,
# cronometro de salida abajo del todo y altimetro de cinta con velocidad vertical (pestana ALTIMETRO y en la pantalla
# grande al acercarte a un planeta). No necesita sender nuevo.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def mem_loop" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b15 ', s):
    sys.exit("Este parche es para la v1.0 beta 15")
shutil.copy(P, P + ".bak100b15")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# EMITIR: como mucho 3 a la vez y fuera los que se atascan
rep('''            which = "big" if path == "/hdmi" else "small"
            self.send_response(200)''', '''            which = "big" if path == "/hdmi" else "small"
            if stream["clients"] >= 3:                   # b16: como mucho 3 a la vez
                self.send_error(503); return
            try:
                self.connection.settimeout(10)           # b16: si no puede enviar en 10 s, se corta
            except Exception:
                pass
            self.send_response(200)''')
# reloj de atraque desde 9:59
rep('DOCK_SECS = 595', 'DOCK_SECS = 599')
# cronometro de salida abajo del todo (con su rotulo)
rep('''    r = pygame.Rect(0, TOP, W, 46)
    pygame.draw.rect(surf, BLACK, r)
    pygame.draw.rect(surf, RED if left < 60 else ORANGE, r, 2, border_radius=6)''', '''    r = pygame.Rect(0, H - 46, W, 46)
    pygame.draw.rect(surf, BLACK, r)
    pygame.draw.rect(surf, RED if left < 60 else ORANGE, r, 2, border_radius=6)''')
rep('''        box = pygame.Rect(bw // 2 - 400, 54, 800, 150)''', '''        box = pygame.Rect(bw // 2 - 400, BIG["h"] - 160, 800, 150)''')

CODE = r'''
# ---------- v1.0 beta 16 ----------
# --- memoria: pocas reservas de malloc y devolver lo libre (EMITIR copiaba 4 MB por fotograma en muchos hilos) ---
def _libc():
    import ctypes
    try:
        return ctypes.CDLL("libc.so.6")
    except OSError:
        return None

_LC = _libc()
try:
    if _LC is not None:
        _LC.mallopt(-8, 2)                              # M_ARENA_MAX = 2
except Exception:
    pass
IS_PI3 = False
try:
    IS_PI3 = "Pi 3" in open("/proc/device-tree/model").read()
except OSError:
    pass

def mem_rss_pct():
    try:
        rss = int(open("/proc/self/statm").read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
        tot = int(next(l for l in open("/proc/meminfo") if l.startswith("MemTotal")).split()[1]) * 1024
        return 100.0 * rss / tot
    except Exception:
        return 0.0

def mem_loop():
    warned = 0
    while True:
        time.sleep(30)
        try:
            if _LC is not None:
                _LC.malloc_trim(0)                      # devuelve al sistema la memoria libre
        except Exception:
            pass
        p = mem_rss_pct()
        if p > 60 and cfg.get("stream"):
            cfg["stream"] = False
            plog(f"EMITIR apagado: el panel usaba el {p:.0f} % de la RAM")
            set_alert("EMITIR APAGADO", f"el panel usaba el {p:.0f} % de la RAM · vuelve a encenderlo en AJUSTES", RED, 10)
        elif p > 75 and time.time() - warned > 600:
            warned = time.time()
            plog(f"Memoria del panel: {p:.0f} %")

threading.Thread(target=mem_loop, daemon=True, name="memoria").start()

# --- EMITIR: menos fotogramas en la Pi 3 y mas pequenos ---
_SNAP = {"t": 0}

def stream_snap(small):
    if not cfg.get("stream") or stream["clients"] <= 0:
        return
    now = time.time()
    if now - _SNAP["t"] < (0.2 if IS_PI3 else 0.1):     # 5 imagenes/s en la Pi 3, 10 en las demas
        return
    _SNAP["t"] = now
    with stream_lock:
        hi = panel_hi() if cfg.get("sharp") else None
        src = hi if hi is not None else small
        big = BIG["surf"] if BIG.get("fb") and BIG.get("surf") is not None else None
        if IS_PI3:
            sc = lambda S_: pygame.transform.scale(S_, (S_.get_width() * 3 // 4, S_.get_height() * 3 // 4)) if S_.get_width() > 800 else S_.copy()
            stream["small"] = sc(src)
            stream["big"] = sc(big) if big is not None else None
        else:
            stream["small"] = src.copy()
            stream["big"] = big.copy() if big is not None else None
        stream["seq"] += 1

# --- altimetro de cinta con velocidad vertical ---
MENU[137] = "ALTÍMETRO"
TABS[0].append((137, "ALTÍMETRO"))
ALTH = deque(maxlen=40)                                 # (hora, altura)

def alt_now(d):
    """Altura (m) si el juego la da y toca mostrarla; si no, None."""
    d = d or {}
    fl, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    alt = (d.get("live") or {}).get("alt")
    if alt is None or not fl & (1 << 21) or f2 & 1:     # sin coordenadas planetarias o a pie: nada
        return None
    if fl & (1 << 26) and not cfg.get("alt_srv", False):
        return None                                      # en el SRV solo si se ha activado
    return alt

def alt_vs():
    if len(ALTH) < 2:
        return None
    t1, a1 = ALTH[-1]
    old = [(t, a) for t, a in ALTH if t1 - t <= 3]
    t0, a0 = old[0]
    return (a1 - a0) / (t1 - t0) if t1 - t0 >= 0.5 else None

def alt_track(d, now):
    alt = alt_now(d)
    if alt is None:
        ALTH.clear(); return
    if not ALTH or ALTH[-1][1] != alt or now - ALTH[-1][0] > 1:
        ALTH.append((now, alt))

def draw_alt(surf, r, d, now, big=False):
    alt = alt_now(d)
    if alt is None:
        put(surf, F["btn"], "sin altura", (r.centerx, r.centery - 10), DIM, anchor="center")
        put(surf, F["small"], "aparece cerca de un planeta", (r.centerx, r.centery + 12), DIM, r.w - 10, anchor="center")
        return
    fl = (d or {}).get("Flags", 0)
    vs = alt_vs()
    tape = pygame.Rect(r.x + 8, r.y + 18, int(r.w * 0.52), r.h - 26)
    pygame.draw.rect(surf, (14, 14, 16), tape); pygame.draw.rect(surf, (80, 80, 86), tape, 1)
    span = 60 if alt < 200 else 600 if alt < 3000 else 6000 if alt < 30000 else 60000   # metros visibles
    step = span // 6
    ppm = tape.h / span
    mid = tape.centery
    old = surf.get_clip(); surf.set_clip(tape)
    m0 = int((alt - span) // (step / 5)) * (step / 5)
    k = 0
    m = m0
    while m < alt + span and k < 200:
        yy = mid - (m - alt) * ppm
        if m >= 0 and abs(round(m / step) * step - m) < 1e-6:
            pygame.draw.line(surf, WHITE, (tape.x, yy), (tape.x + 12, yy), 2)
            put(surf, F["small"], f"{int(m):,}".replace(",", "."), (tape.x + 16, int(yy) - 8), WHITE)
        elif m >= 0:
            pygame.draw.line(surf, (150, 150, 150), (tape.x, yy), (tape.x + 6, yy), 1)
        m += step / 5; k += 1
    gy = mid + alt * ppm                                  # el suelo
    if gy < tape.bottom:
        pygame.draw.rect(surf, (60, 35, 10), (tape.x, int(gy), tape.w, tape.bottom - int(gy)))
    surf.set_clip(old)
    put(surf, F["tiny"], "ALT" + (" (radio medio)" if fl & (1 << 29) else ""), (tape.x, r.y + 3), DIM)
    txt = f"{alt:,.0f} m".replace(",", ".") if alt < 100000 else f"{alt / 1000:,.0f} km".replace(",", ".")
    box = pygame.Rect(tape.x + tape.w * 2 // 5, mid - 15, tape.w * 3 // 5 + 26, 30)
    pts = [(box.x, mid), (box.x + 10, box.y), (box.right, box.y), (box.right, box.bottom), (box.x + 10, box.bottom)]
    pygame.draw.polygon(surf, BLACK, pts); pygame.draw.polygon(surf, ORANGE, pts, 2)
    put(surf, F["big"], txt, (box.centerx + 5, mid), ORANGE, box.w - 14, anchor="center")
    # velocidad vertical
    vsr = pygame.Rect(tape.right + 40, tape.y + 14, 28, tape.h - 44)
    pygame.draw.rect(surf, (14, 14, 16), vsr)
    pygame.draw.line(surf, DIM, (vsr.x, vsr.centery), (vsr.right, vsr.centery), 1)
    put(surf, F["tiny"], "VERT.", (vsr.centerx, vsr.y - 12), DIM, anchor="center")
    if vs is not None:
        lim = 200 if alt > 2000 else 50
        h_ = int(min(1.0, abs(vs) / lim) * (vsr.h // 2 - 2))
        col = BLUE if vs < 0 else GREEN
        if vs < 0:
            pygame.draw.rect(surf, col, (vsr.x + 4, vsr.centery, vsr.w - 8, h_))
        else:
            pygame.draw.rect(surf, col, (vsr.x + 4, vsr.centery - h_, vsr.w - 8, h_))
        warn = vs < -30 and alt < 300                     # bajando rapido muy cerca del suelo
        put(surf, F["btn"], f"{vs:+.0f}", (vsr.centerx, vsr.bottom + 12), RED if warn and int(now * 2) % 2 else col, anchor="center")
        put(surf, F["tiny"], "m/s", (vsr.centerx, vsr.bottom + 28), DIM, anchor="center")

def view_alt(surf, d, flags, now):
    r = pygame.Rect(4, TOP + 2, W - 8, H - TOP - 6)
    draw_alt(surf, r, d, now)
    b = pygame.Rect(W - 112, H - 30, 106, 24)
    on = cfg.get("alt_srv", False)
    draw_button(surf, b, "SRV: " + ("SÍ" if on else "NO"), None, F["small"], filled=on, compact=True)
    ALT_SRV_R[0] = b

ALT_SRV_R = [pygame.Rect(0, 0, 0, 0)]
VIEWS[137] = view_alt

# pantalla grande: el altimetro sustituye a una de las 4 cuando hay altura
_big_mode_b16 = big_mode
BIG_SETS["APROXIMACIÓN + ALTÍMETRO"] = [100, 72, 73, 137]
BIG_SETS["SUPERFICIE + ALTÍMETRO"] = [100, 73, 137, 150]
BIG_SETS["PUERTO PLANETARIO"] = [100, 8, 127, 137]

def big_mode(d, flags):
    m = _big_mode_b16(d, flags)
    if alt_now(d) is not None:
        if m == "APROXIMACIÓN":
            return "APROXIMACIÓN + ALTÍMETRO"
        if m == "SUPERFICIE" and not (d.get("Flags2", 0) & 1) and not flags & (1 << 26):
            return "SUPERFICIE + ALTÍMETRO"
        if m == "ATRACADO":
            return "PUERTO PLANETARIO"                         # puerto planetario
    return m

_render_b16 = render

def render(surf):
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d is not None and time.time() - rx < 5:
            alt_track(d, time.time())
    except Exception:
        pass
    return _render_b16(surf)

_on_tap_b16 = on_tap

def on_tap(x, y):
    if ui.get("view") == 137 and ALT_SRV_R[0].collidepoint(x, y):
        cfg["alt_srv"] = not cfg.get("alt_srv", False); save_cfg(); TAP_EV.set(); return
    _on_tap_b16(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 15''', '''# Novedades v1.0 beta 16
- EMITIR: la memoria ya no sube sin parar (la Pi 3 de KORZO llegaba al 85 %). Como mucho 3 a la vez, los que se atascan se cortan a los 10 s, en la Pi 3 va a 5 imágenes/s y más pequeño, y si el panel pasa del 60 % de la RAM se apaga EMITIR con un aviso.
- Reloj de atraque desde 9:59.
- El cronómetro de salida de la estación y su rótulo van abajo del todo (también en 4 CUADROS).
- ALTÍMETRO de cinta con velocidad vertical (azul bajando, verde subiendo; rojo si bajas rápido cerca del suelo): pestaña en NAVEGACIÓN y, en la pantalla grande, sustituye a un cuadro al acercarte a un planeta, al aterrizar y en los puertos planetarios. Solo sale cuando el juego da la altura. En el SRV apagado (botón SRV: SÍ/NO en la pestaña).
# Novedades v1.0 beta 15''')
rep('    ("1.0b15", ', '    ("1.0b16", "EMITIR sin subir la memoria, atraque 9:59, salida abajo, altímetro de cinta"),\n    ("1.0b15", ')
s = re.sub(r'PANEL_VER = "v1\.0b15 [^"]*"', 'PANEL_VER = "v1.0b16 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 16  (copia en " + P + ".bak100b15)")
