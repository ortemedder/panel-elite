# Panel Elite v1.1 · parte 05: pantalla grande (lineas 3317-3748 del panel entero)
# ---------- pantalla grande HDMI: tablero de 4 cuadros segun la situacion ----------
BIG = {"dev": None, "fb": None, "w": 0, "h": 0, "bpp": 16, "stride": 0, "surf": None, "s16": None,
       "last": None, "n": 0, "fonts": None, "cell": None}
BIG_SETS = {"COMBATE A PIE": [100, 5, 150], "VIAJE": [100, 3, 71, 72], "APROXIMACIÓN": [100, 72, 73, 74], "SUPERFICIE": [100, 73, 5, 150],
            "ATRACADO": [100, 8, 127, 4], "ATRAQUE": [8], "COMBATE": [100, 6, 61, 2]}

def big_open():
    import glob, os, fcntl
    for p in sorted(glob.glob('/sys/class/graphics/fb*')):
        try:
            name = open(p + '/name').read().strip()
            if 'vc4' not in name.lower():
                continue
            w, h = map(int, open(p + '/virtual_size').read().strip().split(','))
            bpp = int(open(p + '/bits_per_pixel').read())
            stride = int(open(p + '/stride').read())
            dev = '/dev/' + os.path.basename(p)
            fb = open(dev, 'r+b', buffering=0)
        except Exception as e:
            print("HDMI:", e, flush=True); continue
        try:
            buf = bytearray(160)
            fcntl.ioctl(fb, 0x4600, buf)        # FBIOGET_VSCREENINFO
            fcntl.ioctl(fb, 0x4601, buf)        # FBIOPUT_VSCREENINFO (enciende la salida)
            fcntl.ioctl(fb, 0x4611, 0)          # FBIOBLANK: desbloquear
        except OSError:
            pass
        masks = (0xF800, 0x07E0, 0x001F, 0) if bpp == 16 else (0xFF0000, 0xFF00, 0xFF, 0)
        BIG.update(dev=dev, fb=fb, w=w, h=h, bpp=bpp, stride=stride, surf=pygame.Surface((w, h), 0, 32),
                   s16=pygame.Surface((w, h), 0, bpp, masks), cell=pygame.Surface((W, H), 0, 32))
        print("Pantalla grande", dev, w, h, bpp, flush=True)
        return True
    return False

BIG_ROT = 10          # segundos por cuadro en modo GRANDE
BIGMODES = {"4": "4 CUADROS", "MIXTO": "MIXTO", "GRANDE": "GRANDE"}


def big_fill(dst, src, area):
    """Escala el cuadro a todo el hueco (un poco mas ancho que alto) para no dejar bandas a los lados."""
    try:
        img = pygame.transform.smoothscale(src, area.size)
    except ValueError:
        img = pygame.transform.scale(src, area.size)
    dst.blit(img, area.topleft)

def big_blit(dst, src, area):
    s = min(area.w / src.get_width(), area.h / src.get_height())
    size = (max(1, int(src.get_width() * s)), max(1, int(src.get_height() * s)))
    try:
        img = pygame.transform.smoothscale(src, size)
    except ValueError:
        img = pygame.transform.scale(src, size)
    dst.blit(img, img.get_rect(center=area.center))

def _big_mode_base(d, flags):
    f2 = d.get("Flags2", 0)
    if in_fight(d):
        return "COMBATE A PIE"
    if not f2 & 1 and hp_out(d, flags) and time.time() - fight["t"] < FIGHT_SECS:
        return "COMBATE"                     # combate de nave: manda aunque el juego diga atracado
    if flags & 1:
        return "ATRACADO"
    if (d.get("station") or {}).get("status") == "CONCEDIDO":
        return "ATRAQUE"
    if f2 & 1 or flags & ((1 << 26) | 2):
        return "SUPERFICIE"
    if (d.get("body") or "").endswith(" Ring"):
        return "APROXIMACIÓN"
    if hp_out(d, flags):
        return "COMBATE"
    if flags & (1 << 21):
        return "APROXIMACIÓN"
    return "VIAJE"


def big_frame():
    if BIG["fb"] is None:
        if BIG["dev"] is None and not big_open():
            BIG["dev"] = False
        if BIG["fb"] is None:
            return
    try:
        PERF["frames"] += 1
        render_big()
        draw_kill_cell(time.time())
        draw_shipcard(BIG["surf"], time.time())
        with lock:
            dm_ = state["data"]
        draw_mega(BIG["surf"], dm_, time.time())
        draw_hpcrit(BIG["surf"], time.time())
        decorate_big(BIG["surf"])
        draw_borders(BIG["surf"])
        rhino_banner(BIG["surf"])
        s16 = BIG["s16"]
        s16.blit(BIG["surf"], (0, 0))
        raw = s16.get_buffer().raw
        pitch, stride = s16.get_pitch(), BIG["stride"]
        if pitch != stride:
            n = min(pitch, stride)
            raw = b"".join(raw[y * pitch:y * pitch + n].ljust(stride, b"\0") for y in range(BIG["h"]))
        if raw != BIG["last"]:
            BIG["fb"].seek(0); BIG["fb"].write(raw); BIG["last"] = raw
    except Exception as e:
        print("HDMI:", e, flush=True)

# ---------- aviso RHINO PREPARADO (7-40 m) en las dos pantallas ----------
RB_FONTS = {}

def rhino_ready():
    with lock:
        d, rx = state["data"], state["rx"]
    if not d or time.time() - rx > 5:
        return None
    flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    if flags & ((1 << 26) | 1 | 2) or f2 & 1:            # en SRV, atracado, aterrizado o a pie
        return None
    if not flags & (1 << 21) or flags & (1 << 29):       # sin altitud real sobre el terreno
        return None
    L = d.get("live") or {}
    alt, rh = L.get("alt"), (L.get("ship") or {}).get("rhino")
    if alt is not None and alt <= 100 and rh in ("A BORDO", "HANGAR"):
        return alt
    return None

def rhino_banner(surf):
    alt = rhino_ready()
    if alt is None:
        return
    now = time.time()
    if alt > 40:
        col, txt = (255, 80, 0), "BAJA PARA EL RHINO"
    elif alt >= 7:
        col, txt = (0, 170, 60), "RHINO PREPARADO"
    else:
        col = (255, 0, 0) if int(now * 4) % 2 == 0 else (60, 0, 0)
        txt = "DEMASIADO BAJO"
    w, h = surf.get_size()
    bh = max(58, h // 7)
    r = pygame.Rect(0, h - bh, w, bh)
    pygame.draw.rect(surf, col, r)
    pygame.draw.rect(surf, WHITE, r, 3)
    size = int(bh * 0.8)
    if size not in RB_FONTS:
        RB_FONTS[size] = (pygame.font.Font(None, size), pygame.font.Font(None, max(18, size // 2)))
    fb, fs = RB_FONTS[size]
    img = fb.render(txt, True, WHITE)
    surf.blit(img, img.get_rect(center=(r.centerx - w // 14, r.centery)))
    a = fs.render(f"{alt:.0f} m", True, WHITE)
    surf.blit(a, a.get_rect(midright=(r.right - 12, r.centery)))

# ---------- estilo CABINA tambien en la pantalla grande ----------
def _bpat(w, h, ground):
    sf = pygame.Surface((w, h), pygame.SRCALPHA)
    if ground:
        for y in range(8, h, 20):
            for x in range(8, w, 20):
                sf.set_at((x, y), (255, 140, 0, 60))
    else:
        r = 22
        dx, dy = r * 1.732, r * 1.5
        for row in range(int(h / dy) + 2):
            for col in range(int(w / dx) + 2):
                cx = col * dx + (dx / 2 if row % 2 else 0)
                cy = row * dy
                pts = [(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]
                pygame.draw.polygon(sf, (255, 140, 0, 16), pts, 1)
    return sf

def _bscan(w, h):
    sf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 3):
        pygame.draw.line(sf, (0, 0, 0, 55), (0, y), (w, y))
    return sf

def _btint(w, h, col):
    sf = pygame.Surface((w, h), pygame.SRCALPHA)
    sf.fill((col[0], col[1], col[2], 22))
    return sf

def decorate_big(S):
    if not style["cab"]:
        return
    now = time.time()
    w, h = S.get_size()
    hh = 44
    with lock:
        d, rx = state["data"], state["rx"]
    online = d is not None and now - rx < 5
    if online and now - ui["start"] >= 3:
        flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
        ground = bool(f2 & 1 or flags & (1 << 26))
        S.blit(_cached(("bpat", ground, w, h), lambda: _bpat(w, h - hh, ground)), (0, hh))
        L = d.get("live") or {}
        hull = (L.get("ship") or {}).get("hull")
        danger = L.get("legal") in ("Wanted", "Hostile", "Warrant") or (hull is not None and hull < 0.3)
        cols = border_cols(d)
        if cols:
            S.blit(_cached(("btint", tuple(cols[0][:3]), w, h), lambda: _btint(w, h, cols[0])), (0, 0))
        p_ = (now * 300) % (w + 300) - 150
        for x in range(0, w, 4):
            b = max(0.25, 1 - abs(x - p_) / 150)
            pygame.draw.line(S, tuple(int(c * b) for c in ORANGE[:3]), (x, hh - 2), (x + 3, hh - 2))
        pygame.draw.circle(S, GREEN if now - rx < 0.6 else DIM, (w - 6, 6), 4)
    S.blit(_cached(("bscan", w, h), lambda: _bscan(w, h)), (0, 0))
    band = _cached(("bband", w), lambda: pygame.Surface((w, 4), pygame.SRCALPHA))
    band.fill((255, 170, 60, 28))
    S.blit(band, (0, int((now * 60) % h)))

# ---------- bordes de situacion (rojo, naranja, marron, azul) ----------
BROWN = (150, 90, 40)
BORDERS_FILE = os.path.join(PANEL_DIR, "bordes.txt")
try:
    style["borders"] = open(BORDERS_FILE).read().strip() != "no"
except OSError:
    style["borders"] = True

def borders_toggle():
    style["borders"] = not style["borders"]
    try:
        with open(BORDERS_FILE, "w") as f:
            f.write("si" if style["borders"] else "no")
    except OSError:
        pass

def border_cols(d):
    flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    L = d.get("live") or {}
    hull = (L.get("ship") or {}).get("hull")
    sec = ((d.get("sysinfo") or {}).get("sec") or "").lower()
    out = []
    if L.get("legal") in ("Wanted", "Hostile", "Warrant") or (hull is not None and hull < 0.3 and not f2 & 1):
        out.append(RED)
    if "anarqu" in sec or "lawless" in sec or "sin ley" in sec:
        out.append(ORANGE)
    if f2 & (1 << 4) or flags & (1 << 26):
        out.append(BROWN)
    if flags & 1:
        out.append(BLUE)
    return out[:3]

def draw_borders(surf):
    if not style.get("borders", True):
        return
    now = time.time()
    with lock:
        d, rx = state["data"], state["rx"]
    if not d or now - rx > 5 or now - ui["start"] < 3 or ui.get("idle_on"):
        return
    w, h = surf.get_size()
    th = 2 if w < 600 else 3
    for k, col in enumerate(border_cols(d)):
        o = k * (th + 1)
        _orig_rect(surf, col, (o, o, w - 2 * o, h - 2 * o), th)

# ---------- 12.9 GALNET: noticias oficiales (la Pi las baja sola) ----------
import re
GALNET_URL = ("https://cms.zaonce.net/es-ES/jsonapi/node/galnet_article"
              "?sort=-published_at&page%5Blimit%5D=20")
GALNET_FILE = os.path.join(PANEL_DIR, "galnet.json")
GALNET_EVERY = 1800
galnet = {"list": [], "t": 0, "err": "", "page": 0, "sel": None, "apage": 0, "new": set(), "lines": None}

def galnet_text(html_):
    import html as _h
    t = re.sub(r"(?i)<br\s*/?>|</p>", "\n", html_ or "")
    t = re.sub(r"<[^>]+>", "", t)
    t = _h.unescape(t).replace("\r", "")
    return re.sub(r"\n{3,}", "\n\n", t).strip()

def galnet_fetch():
    import urllib.request
    req = urllib.request.Request(GALNET_URL, headers={"User-Agent": "PanelElite/1.0",
                                                      "Accept": "application/vnd.api+json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    out = []
    for a in data.get("data", []):
        t = a.get("attributes") or {}
        out.append({"id": a.get("id"), "title": (t.get("title") or "").strip(),
                    "date": t.get("field_galnet_date") or "",
                    "body": galnet_text((t.get("body") or {}).get("value", ""))})
    return out

def galnet_loop():
    try:
        with open(GALNET_FILE, encoding="utf-8") as f:
            galnet["list"] = json.load(f)
    except (OSError, ValueError):
        pass
    first = not galnet["list"]
    while True:
        try:
            L = galnet_fetch()
            if L:
                old = {n["id"] for n in galnet["list"]}
                nuevas = [n for n in L if n["id"] not in old]
                galnet["list"], galnet["t"], galnet["err"] = L, time.time(), ""
                if nuevas and not first:
                    galnet["new"].update(n["id"] for n in nuevas)
                    if ev_on("galnet"):
                        set_alert("NUEVA NOTICIA GALNET", nuevas[0]["title"], BLUE, 6, "galnet")
                first = False
                with open(GALNET_FILE + ".tmp", "w", encoding="utf-8") as f:
                    json.dump(L, f, ensure_ascii=False)
                import os as _os
                _os.replace(GALNET_FILE + ".tmp", GALNET_FILE)
            time.sleep(GALNET_EVERY)
        except Exception as e:
            galnet["err"] = str(e)[:60]
            print("galnet:", e, flush=True)
            time.sleep(300)

threading.Thread(target=galnet_loop, daemon=True).start()

def wrap_lines(font, text, width):
    out = []
    for par in text.split("\n"):
        if not par.strip():
            out.append(""); continue
        line = ""
        for w in par.split():
            test = (line + " " + w).strip()
            if font.size(test)[0] <= width:
                line = test
            else:
                if line:
                    out.append(line)
                line = w
        out.append(line)
    return out

GAL_PER = 6
GAL_PAGE = pygame.Rect(W - 118, TOP + 2, 110, 30)

def gal_row(i):
    return pygame.Rect(8, TOP + 38 + i * 37, W - 16, 34)

def view_galnet(surf, d, flags, now):
    L = galnet["list"]
    pages = max(1, (len(L) + GAL_PER - 1) // GAL_PER)
    pg = galnet["page"] % pages
    if galnet["t"]:
        info = "actualizado " + time.strftime("%H:%M", time.localtime(galnet["t"]))
    else:
        info = galnet["err"] or "descargando..."
    put(surf, F["small"], info, (8, TOP + 10), RED if galnet["err"] else DIM, W - 140)
    if pages > 1:
        draw_button(surf, GAL_PAGE, f"PÁG {pg + 1}/{pages} >", None, F["small"])
    if not L:
        put(surf, F["btn"], "Sin noticias todavía", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    for i, n in enumerate(L[pg * GAL_PER:(pg + 1) * GAL_PER]):
        r = gal_row(i)
        nueva = n["id"] in galnet["new"]
        pygame.draw.rect(surf, GREEN if nueva else DIM, r, 1, border_radius=4)
        put(surf, F["btn"], n["title"], (r.x + 6, r.y + 2), GREEN if nueva else ORANGE, r.w - 12)
        put(surf, F["small"], n["date"] + ("   · NUEVA" if nueva else ""), (r.x + 6, r.y + 19), BLUE if not nueva else GREEN)

def view_galnet_art(surf, d, flags, now):
    L, i = galnet["list"], galnet["sel"]
    if i is None or i >= len(L):
        ui["view"] = 130; return
    n = L[i]
    if galnet["lines"] is None or galnet["lines"][0] != n["id"]:
        galnet["lines"] = (n["id"], wrap_lines(F["big"], n["title"], W - 16)[:2],
                           wrap_lines(F["small"], n["body"], W - 16))
    _, tl, body = galnet["lines"]
    y = TOP + 2
    for t in tl:
        put(surf, F["big"], t, (8, y), ORANGE); y += 24
    put(surf, F["small"], "GALNET · " + n["date"], (8, y), BLUE); y += 18
    per = max(1, (H - y - 4) // 16)
    pages = max(1, (len(body) + per - 1) // per)
    pg = galnet["apage"] % pages
    put(surf, F["small"], f"pág {pg + 1}/{pages}  (toca)", (W - 8, y - 18), DIM, anchor="topright")
    for line in body[pg * per:(pg + 1) * per]:
        put(surf, F["small"], line, (8, y), WHITE); y += 16

def tap_galnet(x, y):
    v, L = ui["view"], galnet["list"]
    if v == 130:
        pages = max(1, (len(L) + GAL_PER - 1) // GAL_PER)
        if pages > 1 and GAL_PAGE.collidepoint(x, y):
            galnet["page"] += 1; return
        pg = galnet["page"] % pages
        for i in range(GAL_PER):
            idx = pg * GAL_PER + i
            if idx < len(L) and gal_row(i).collidepoint(x, y):
                galnet["sel"], galnet["apage"] = idx, 0
                galnet["new"].discard(L[idx]["id"])
                ui["view"] = 131; return
    elif v == 131:
        galnet["apage"] += 1

VIEWS.update({130: view_galnet, 131: view_galnet_art})
MENU.update({130: "GALNET", 131: "NOTICIA"})
PARENT.update({130: 12, 131: 130})


# ---------- fecha del juego y cuadro GALNET de la pantalla grande ----------
MES3 = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

def game_date():
    g = time.gmtime()
    return f"{g.tm_mday} {MES3[g.tm_mon - 1]} {g.tm_year + 1286}"

def view_galnet_cell(surf, d, flags, now):
    idle_crawl(surf, now, pygame.Rect(4, TOP + 2, W - 8, H - TOP - 6), waiting=False)

ATR_ROT = [(133, 20), (4, 4), (132, 20)]     # GALNET 20 s, CARGA/MISIÓN 4 s, OBJ. COMUNITARIOS 20 s

def atr_cell(d, now):
    if (d or {}).get("missions"):
        return 4                                     # con misiones: fijo en MISIONES
    rot = [(133, 20)]
    if (d or {}).get("cargo") or (d or {}).get("missions"):
        rot.append((4, 4))
    if 132 in VIEWS and cg_all(d):
        rot.append((132, 20))
    if len(rot) == 1:
        return 133
    t = now % sum(s_ for _, s_ in rot)
    for v, s_ in rot:
        if t < s_:
            return v
        t -= s_
    return 133

VIEWS[133] = view_galnet_cell
MENU[133] = "GALNET"


