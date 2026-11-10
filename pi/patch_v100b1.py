#!/usr/bin/env python3
# Parche v1.0 beta 1 (desde la v0.99k):
#  foto del destino mas grande, voz "cr" = creditos, avatar de Inara, RAM y MHz, aviso de reloj y de SD,
#  borde sencillo en la HDMI en modo PANEL, ESCUDOS CAIDOS solo si de verdad estan caidos.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def avatar_photo" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.99k' not in s:
    sys.exit("Este parche es para la v0.99k")
shutil.copy(P, P + ".bak99k")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# 1. foto del destino 220x124; los textos de encima a lo ancho; FACCION debajo de la clase de estacion
rep('''def route_thumb(surf, d):''', '''THUMB_TOP = H - 130                                  # foto del destino: 220x124 abajo a la derecha

def route_thumb(surf, d):''')
rep('''    r = pygame.Rect(W - 178, H - 102, 170, 96)\n''', '''    r = pygame.Rect(W - 228, THUMB_TOP, 220, 124)\n''')
rep('''"sin datos: no escaneado (o es una estación/señal)",
            (8, H - 16), DIM if src else ORANGE, W - 190)''', '''"sin datos: no escaneado (o es una estación/señal)",
            (8, H - 16), DIM if src else ORANGE, W - 240)''')
rep('''eng_card(surf, d or {}, pygame.Rect(4, H - 112, W - (190 if th else 8), 108))''',
    '''eng_card(surf, d or {}, pygame.Rect(4, H - 112, W - (240 if th else 8), 108))''')
a = s.index("def carrier_info(surf, d):"); b = s.index("\n_navx1 = view_navx", a)
blk = s[a:b]
if "    y, x, wd = TOP + 58, 8, W - 190\n" not in blk:
    sys.exit("No encuentro carrier_info")
blk = blk.replace("    y, x, wd = TOP + 58, 8, W - 190\n",
                  "    y, x = TOP + 58, 8\n    wd_ = lambda y_: W - 16 if y_ + 18 <= THUMB_TOP else W - 240   # a lo ancho si queda encima de la foto\n")
blk = blk.replace(", wd)", ", wd_(y))")
s = s[:a] + blk + s[b:]
rep('''    y = TOP + 58 if carrier_dest(d)[0] not in ("fc", "sq") else H - 40\n''',
    '''    y = TOP + 80 if carrier_dest(d)[0] not in ("fc", "sq") else H - 40\n''')
rep('''    put(surf, F["btn"], fac, (8, y + 14), WHITE, W - 196)\n''',
    '''    put(surf, F["btn"], fac, (8, y + 14), WHITE, W - 16 if y + 34 <= THUMB_TOP else W - 246)\n''')
rep('''        put(surf, F["btn"], "  ·  ".join(bits), (8, y + 36), col, W - 196)\n''',
    '''        put(surf, F["btn"], "  ·  ".join(bits), (8, y + 36), col, W - 16 if y + 56 <= THUMB_TOP else W - 246)\n''')

# 2. avatar de Inara (si no hay, la foto de su nave)
rep('''ph_ = cfg.get("cmdrpics", True) and o.get("ship") and ship_photo(surf, {"ship": o.get("ship")}, {}, pygame.Rect(W - 60, y + 3, 52, 29))''',
    '''ph_ = cfg.get("cmdrpics", True) and (o.get("avatar") or o.get("ship")) and (avatar_photo(surf, o.get("avatar"), pygame.Rect(W - 60, y + 3, 52, 29)) or ship_photo(surf, {"ship": o.get("ship")}, {}, pygame.Rect(W - 60, y + 3, 52, 29)))''')
rep('''            ship_photo(surf, {"type": t.get("stype"), "ship": t.get("ship") or ia2_.get("ship")}, {},
                       pygame.Rect(card.right - 62, card.bottom - 34, 56, 31))''',
    '''            (avatar_photo(surf, ia2_.get("avatar"), pygame.Rect(card.right - 62, card.bottom - 34, 56, 31)) or
             ship_photo(surf, {"type": t.get("stype"), "ship": t.get("ship") or ia2_.get("ship")}, {},
                        pygame.Rect(card.right - 62, card.bottom - 34, 56, 31)))''')

# 3. borde de estado: en la HDMI en modo PANEL solo el del panel (no el de toda la pantalla)
rep('''        draw_borders(BIG["surf"])''', '''        if not hdmi_panel():
            draw_borders(BIG["surf"])''')

# 4. ESCUDOS CAIDOS: no si la nave en la que vas tiene los escudos arriba
rep('''    sd = C.get("sd")''', '''    sd = None if flags & 8 else C.get("sd")''')
rep('''    sd = ((d or {}).get("combat") or {}).get("sd")''', '''    sd = None if flags & 8 else ((d or {}).get("combat") or {}).get("sd")''')

# 5. TIEMPOS del LOG con RAM y MHz
rep('''+ f"  ·  CPU {PERF.get('cpu') or 0:.0f}%  ·  {PERF.get('fps') or 0:.0f} FPS")''',
    '''+ f"  ·  CPU {PERF.get('cpu') or 0:.0f}%  ·  {PERF.get('mhz') or 0:.0f} MHz  ·  RAM {PERF.get('ram') or 0:.0f}%  ·  {PERF.get('fps') or 0:.0f} FPS")''')

CODE = r'''
# ---------- v1.0 beta 1 ----------
# voz: "cr" son creditos
def voz_txt(t):
    t = t or ""
    t = re.sub(r"(?<![\d.,])1(?:[.,]0)?\s*M\s*cr\b", "un millón de créditos", t)
    t = re.sub(r"(\d+(?:[.,]\d+)?)\s*M\s*cr\b", r"\1 millones de créditos", t)
    t = re.sub(r"(\d+(?:[.,]\d+)?)\s*[kK]\s*cr\b", r"\1 mil créditos", t)
    return re.sub(r"\bcr\b", "créditos", t, flags=re.I)

_voice_say_b1 = voice_say

def voice_say(text):
    return _voice_say_b1(voz_txt(text))

# avatar de Inara: se baja una vez y se guarda en avatares/ junto a panel.py
AV_DIR = os.path.join(PANEL_DIR, "avatares")
_AV = {}

def _av_file(url):
    ext = os.path.splitext(url.split("?")[0])[1].lower()
    return os.path.join(AV_DIR, hashlib.md5(url.encode()).hexdigest()[:16] + (ext if ext in (".jpg", ".jpeg", ".png", ".gif") else ".jpg"))

def _av_get(url):
    try:
        import urllib.request
        os.makedirs(AV_DIR, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "PanelEliteRPi/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read(2_000_000)
        f = _av_file(url)
        with open(f + ".tmp", "wb") as o:
            o.write(data)
        os.replace(f + ".tmp", f)
        _AV.pop(("st", url), None)
    except Exception as e:
        _AV[("st", url)] = time.time()                      # fallo: se reintenta en 1 hora
        log_exc("avatar", e)

def avatar_photo(surf, url, r):
    if not url or not cfg.get("cmdrpics", True) or not url.startswith("http"):
        return False
    real, rr = (surf.real, surf._r(r)) if type(surf).__name__ == "ScaledSurf" else (surf, r)
    key = (url, rr.w, rr.h)
    img = _AV.get(key)
    if img is None:
        f = _av_file(url)
        if not os.path.exists(f):
            st = _AV.get(("st", url))
            if st is None or (st != "pend" and time.time() - st > 3600):
                _AV[("st", url)] = "pend"
                threading.Thread(target=_av_get, args=(url,), daemon=True).start()
            return False
        try:
            src = pygame.image.load(f)
            sw, sh = src.get_size()
            sc = min(rr.w / sw, rr.h / sh)
            im = pygame.transform.smoothscale(src, (max(1, int(sw * sc)), max(1, int(sh * sc))))
            img = pygame.Surface(rr.size); img.fill(BLACK)
            img.blit(im, ((rr.w - im.get_width()) // 2, (rr.h - im.get_height()) // 2))
        except Exception as e:
            log_exc("avatar", e); img = False
        _AV[key] = img
    if not img:
        return False
    real.blit(img, rr.topleft)
    pygame.draw.rect(surf, DIM, r, 1, border_radius=3)
    return True

# RAM % y MHz junto a CPU y temperatura
_perf_update_b1 = perf_update
PERF_MAXMHZ = [None]

def _rd(p):
    try:
        with open(p) as f:
            return f.read()
    except OSError:
        return ""

def perf_update():
    t0 = PERF["t"]
    _perf_update_b1()
    if PERF["t"] == t0:
        return
    m = dict((l.split(":")[0], int(l.split()[1])) for l in _rd("/proc/meminfo").splitlines() if l.split()[1:2] and l.split()[1].isdigit())
    if m.get("MemTotal") and m.get("MemAvailable") is not None:
        PERF["ram"] = 100.0 * (m["MemTotal"] - m["MemAvailable"]) / m["MemTotal"]
    c = _rd("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq").strip()
    PERF["mhz"] = int(c) / 1000 if c.isdigit() else None
    if PERF_MAXMHZ[0] is None:
        mx = _rd("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq").strip()
        PERF_MAXMHZ[0] = int(mx) / 1000 if mx.isdigit() else 0

def perf_parts():
    c, t, ram, mhz = PERF["cpu"], PERF["temp"], PERF.get("ram"), PERF.get("mhz")
    out = []
    if c is not None:
        out.append((f"CPU {c:.0f} %", GREEN if c < 30 else ORANGE if c < 60 else RED))
    if mhz:
        out.append((f"{mhz:.0f} MHz", GREEN if not PERF_MAXMHZ[0] or mhz >= PERF_MAXMHZ[0] * 0.9 else ORANGE))
    if t is not None:
        out.append((f"{t:.0f} °C", GREEN if t < 70 else ORANGE if t < 80 else RED))
    if ram is not None:
        out.append((f"RAM {ram:.0f} %", GREEN if ram < 70 else ORANGE if ram < 85 else RED))
    out.append((f"{PERF['fps']:.0f} FPS", GREEN))
    return out

# salud de la Pi: reloj sin sincronizar y poco espacio en la tarjeta SD
def salud_loop():
    time.sleep(60)                                       # tras el arranque, que le de tiempo a coger la hora
    avisado = {"ntp": 0, "sd": 0}
    while True:
        try:
            r = subprocess.run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
                               capture_output=True, text=True, timeout=5).stdout.strip()
            if r == "no" and time.time() - avisado["ntp"] > 6 * 3600:
                avisado["ntp"] = time.time()
                plog("AVISO: el reloj de la Pi no está sincronizado con internet")
                set_alert("RELOJ SIN SINCRONIZAR", "la Pi no tiene la hora de internet", ORANGE, 8)
        except Exception:
            pass
        try:
            du = shutil.disk_usage(PANEL_DIR)
            if du.free / du.total < 0.10 and time.time() - avisado["sd"] > 6 * 3600:
                avisado["sd"] = time.time()
                plog(f"AVISO: poco espacio en la tarjeta SD ({du.free / 1e9:.1f} GB libres)")
                set_alert("POCO ESPACIO EN LA SD", f"quedan {du.free / 1e9:.1f} GB ({100 * du.free / du.total:.0f} %)", ORANGE, 8)
        except Exception:
            pass
        time.sleep(1800)

threading.Thread(target=salud_loop, daemon=True, name="salud").start()

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 1
- NAVEGACIÓN: la foto del destino es más grande; los datos de encima usan todo el ancho.
- Voz: «cr» se lee «créditos» («2,5 M cr» = 2,5 millones de créditos; «250k cr» = 250 mil créditos).
- Fotos de otros CMDR: su avatar de Inara (si no tiene, la foto de su nave). Se guardan en avatares/.
- Pantalla grande: RAM en % y velocidad de la CPU en MHz junto a la CPU y la temperatura (y en las líneas TIEMPOS del LOG).
- Aviso si el reloj de la Pi no tiene la hora de internet y si queda menos del 10 % de espacio en la tarjeta SD.
- HDMI en modo PANEL: el borde de estado sale una sola vez, alrededor del panel.
- ESCUDOS CAÍDOS ya no se queda puesto al perder el caza o cambiar de nave.
# Enlace energético''')
rep('    ("0.99k", ', '    ("1.0b1", "Foto destino grande, voz créditos, avatar Inara, RAM/MHz, avisos reloj y SD"),\n    ("0.99k", ')
s = re.sub(r'PANEL_VER = "v0\.99k[^"]*"', 'PANEL_VER = "v1.0b1 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 1  (copia en " + P + ".bak99k)")
