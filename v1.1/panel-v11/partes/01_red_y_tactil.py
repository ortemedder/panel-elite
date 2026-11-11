# Panel Elite v1.1 · parte 01: red y tactil (lineas 372-725 del panel entero)
# ---------- UDP ----------
def udp_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", UDP_PORT))
    while True:
        pkt, addr_ = s.recvfrom(65535)
        state["pc"] = addr_[0]
        try:
            if pkt[:1] == b"Z":
                import zlib
                pkt = zlib.decompress(pkt[1:])
            d = json.loads(pkt)
        except Exception:
            continue
        with lock:
            if "log" in d:
                if not ui["pause"]:
                    state["log"].append(d["log"])
            else:
                old = state["data"] or {}
                for k, v in old.items():          # lo que no ha cambiado no viene: se conserva
                    if k not in d:
                        d[k] = v
                state["data"] = d
                state["rx"] = time.time()

# ---------- layout ----------
TOP = 56
BACK = pygame.Rect(0, 0, 96, TOP - 4)

def grid(i, cols=4, rows=3, top=TOP, bottom=H, left=0, right=W):
    cw, ch = (right - left) // cols, (bottom - top) // rows
    c, r = i % cols, i // cols
    return pygame.Rect(left + c * cw + 4, top + r * ch + 4, cw - 8, ch - 8)

PIP_BOTTOM = 238
SEC_TOP = TOP + 20   # menu 5: hueco para los titulos SRV / RHINO / A PIE
TAB_H = 36           # menu 4: pestanas

def pip_rect(i):  return grid(i, 3, 1, TOP, PIP_BOTTOM)
def preset_rect(i): return grid(i, 4, 1, PIP_BOTTOM, H)
def tab_rect(i):  return grid(i, 2, 1, TOP, TOP + TAB_H)
def m5_rect(i):   return grid(i % 2 + (2 if i >= 6 else 0) + 4 * ((i % 6) // 2), 4, 3, SEC_TOP, H)

CARD6 = TOP + 112      # menu 6: alto de la ficha del objetivo
CARD9 = TOP + 76       # menu 9: alto de la ficha del caza
def c6_rect(i): return grid(i, 4, 3, CARD6, H)
def c9_rect(i): return grid(i, 4, 2, CARD9, H)

def tap_flash(key):
    flash[key] = time.time() + 0.25


# ---------- tactil ----------
def touch_loop():
    from evdev import InputDevice, list_devices, ecodes
    dev = None
    devs_ = [InputDevice(p) for p in list_devices()]
    dev = next((d for d in devs_ if "ADS7846" in d.name), None)
    if not dev:
        return   # sin pantalla pequena: el tactil HDMI lo lleva touch_loop2
    ax, ay = dev.absinfo(ecodes.ABS_X), dev.absinfo(ecodes.ABS_Y)
    rx = ry = 0; down = False; pending = False
    for ev in dev.read_loop():
        if ev.type == ecodes.EV_ABS:
            if ev.code == ecodes.ABS_X: rx = ev.value
            elif ev.code == ecodes.ABS_Y: ry = ev.value
        elif ev.type == ecodes.EV_KEY and ev.code in (ecodes.BTN_TOUCH, ecodes.BTN_LEFT):
            down = ev.value == 1
            if down: pending = True
        elif ev.type == ecodes.EV_SYN and pending and down:
            pending = False
            x = (rx - ax.min) / max(1, ax.max - ax.min)
            y = (ry - ay.min) / max(1, ay.max - ay.min)
            if SWAP_XY: x, y = y, x
            if INV_X: x = 1 - x
            if INV_Y and "ADS7846" in dev.name: y = 1 - y
            on_tap(int(x * W), int(y * H))

# ---------- utilidades de dibujo ----------
F = {}

def fit(font, text, width):
    text = str(text)
    if font.size(text)[0] <= width:
        return text
    while text and font.size(text + "...")[0] > width:
        text = text[:-1]
    return text + "..."

def put(surf, font, text, pos, col=None, width=None, anchor="topleft"):
    col = col or ORANGE
    if width:
        text = fit(font, text, width)
    t = font.render(str(text), True, col)
    if type(surf).__name__ == "ScaledSurf":
        f_ = getattr(font, "f", 1)
        r_ = pygame.Rect(0, 0, int(t.get_width() / f_), int(t.get_height() / f_))
        setattr(r_, anchor, pos)
        surf.blit(t, r_.topleft)
        return r_.w
    surf.blit(t, t.get_rect(**{anchor: pos}))
    return t.get_width()

def draw_button(surf, r, txt, sub, f_txt, filled=False, lit=False, dim=False, compact=False):
    if filled or lit:
        pygame.draw.rect(surf, WHITE if lit else ORANGE, r, border_radius=6)
        col = BLACK
    else:
        pygame.draw.rect(surf, DIM if dim else ORANGE, r, 2, border_radius=6)
        col = DIM if dim else ORANGE
    up, down = (7, 12) if compact else (8, 18)
    put(surf, f_txt, txt, (r.centerx, r.centery - (up if sub else 0)), col, r.w - 8, "center")
    if sub:
        put(surf, F["small"], sub, (r.centerx, r.centery + down), col, r.w - 8, "center")

def fmt_time(sec):
    if sec <= 0: return "CADUCADA"
    d, h, m = int(sec // 86400), int(sec % 86400 // 3600), int(sec % 3600 // 60)
    return f"{d}d {h}h" if d else (f"{h}h {m:02d}m" if h else f"{m}m")

def star_ok(cls):
    return (cls or "").split("_")[0] in SCOOPABLE

# ---------- vistas ----------
def view_menu(surf, d, flags, now):
    for i in range(12):
        name = MENU.get(i + 1)
        draw_button(surf, grid(i), str(i + 1), name or "vacío", F["num"],
                    lit=flash.get((0, i), 0) > now, dim=name is None)

def view_mandos(surf, d, flags, now):
    for i, (txt, key, bit) in enumerate(BUTTONS):
        draw_button(surf, grid(i), txt, key.upper(), F["btn"],
                    filled=bit is not None and bool(flags & (1 << bit)), lit=flash.get((1, i), 0) > now or glow(txt))

def view_pips(surf, d, flags, now):
    pips = (d or {}).get("Pips") or [0, 0, 0]
    for i, (name, key) in enumerate(PIP_COLS):
        r = pip_rect(i)
        lit = flash.get((2, i), 0) > now
        pygame.draw.rect(surf, WHITE if lit else ORANGE, r, 2, border_radius=6)
        put(surf, F["btn"], name, (r.centerx, r.y + 14), ORANGE, anchor="center")
        val = pips[i] if i < len(pips) else 0
        bw, bh, gap = r.w - 40, 24, 6
        for p in range(4):                       # 4 pips, de abajo arriba
            br = pygame.Rect(r.x + 20, r.bottom - 30 - (p + 1) * (bh + gap), bw, bh)
            fill = max(0, min(2, val - p * 2))   # medios pips
            pygame.draw.rect(surf, DIM, br, 1)
            if fill:
                pygame.draw.rect(surf, BLUE, (br.x + 2, br.y + 2, (br.w - 4) * fill // 2, br.h - 4))
        put(surf, F["small"], f"{val / 2:g} / 4   [{key.upper()}]", (r.centerx, r.bottom - 14), ORANGE, anchor="center")
    for i, (name, ks) in enumerate(PIP_PRESETS):
        draw_button(surf, preset_rect(i), name, ks[0].upper() if len(ks) == 1 else None, F["btn"],
                    lit=flash.get((2, 10 + i), 0) > now)

def view_nav(surf, d, flags, now):
    nav = (d or {}).get("nav") or {}
    route = (d or {}).get("route") or []
    y = TOP + 6
    tgt = nav.get("target")
    if not tgt and not route:
        put(surf, F["big"], "Sin ruta trazada", (W // 2, (H + TOP) // 2), DIM, anchor="center")
        return
    put(surf, F["small"], "SIGUIENTE SALTO", (8, y), DIM); y += 16
    put(surf, F["big"], (tgt or route[0][0]).upper(), (8, y), ORANGE, W - 16); y += 30
    cls = nav.get("star") or (route[0][1] if route else "")
    ok = star_ok(cls)
    x = 8 + put(surf, F["btn"], f"Estrella {cls or '?'}   ", (8, y), ORANGE)
    put(surf, F["btn"], "RECOLECTABLE" if ok else "NO RECOLECTABLE", (x, y), NEON_G if ok else RED); y += 26
    jumps = nav.get("jumps")
    last = nav.get("last")
    put(surf, F["btn"], f"Saltos restantes: {jumps if jumps is not None else len(route)}", (8, y))
    if last:
        put(surf, F["btn"], f"Último salto: {last:.1f} al", (W - 8, y), ORANGE, anchor="topright")
    y += 30
    y = draw_routeline(surf, d or {}, y, time.time())
    pygame.draw.line(surf, DIM, (8, y - 4), (W - 8, y - 4))
    if route:
        put(surf, F["small"], f"RUTA  -  destino: {((d or {}).get('routeend') or route[-1])[0]}", (8, y), DIM, W - 210)
        RI = (d or {}).get("routeinfo") or {}
        bits = []
        if RI.get("eta"):
            bits.append(f"ETA {RI['eta'] // 3600}h {RI['eta'] % 3600 // 60:02d}m" if RI["eta"] >= 3600 else f"ETA {RI['eta'] // 60} min")
        if RI.get("neutron"):
            bits.append(f"neutrón a {RI['neutron']}")
        if bits:
            put(surf, F["small"], "  ·  ".join(bits), (W - 8, y), BLUE, anchor="topright")
        y += 18
        for n, (name, c) in enumerate(route[:3]):
            col = ORANGE if star_ok(c) else RED
            tw_ = 182 if carrier_dest(d or {})[0] else 0
            put(surf, F["btn"], f"{n + 1}. {name}", (8, y), col, W - 90 - tw_)
            put(surf, F["btn"], c or "?", (W - 8 - tw_, y), col, anchor="topright")
            y += 22

def view_carga(surf, d, flags, now):
    cargo = (d or {}).get("cargo") or []
    miss = (d or {}).get("missions") or []
    used = sum(c for _, c in cargo)
    cap = (d or {}).get("cargocap")
    tabs = [f"BODEGA {used}/{cap if cap is not None else '?'} t", f"MISIONES ({len(miss)})"]
    for i, t in enumerate(tabs):
        draw_button(surf, tab_rect(i), t, None, F["btn"], filled=ui["tab4"] == i)
    top = TOP + TAB_H + 4
    if ui["tab4"] == 0:
        rows, rh = [(n, c) for n, c in cargo], 24
        if not rows:
            put(surf, F["btn"], "Bodega vacía", (W // 2, (H + top) // 2), DIM, anchor="center"); return
    else:
        rows, rh = miss, 42
        if not rows:
            put(surf, F["btn"], "Sin misiones activas", (W // 2, (H + top) // 2), DIM, anchor="center"); return
    per = max(1, (H - top - 18) // rh)
    pages = (len(rows) + per - 1) // per
    pg = ui["page4"] % pages
    y = top
    for row in rows[pg * per:(pg + 1) * per]:
        if ui["tab4"] == 0:
            name, cnt = row
            put(surf, F["btn"], name, (10, y), ORANGE, W - 90)
            put(surf, F["btn"], f"{cnt} t", (W - 10, y), ORANGE, anchor="topright")
        else:
            name, dest, exp = row
            put(surf, F["btn"], name, (10, y), ORANGE, W - 20)
            left = exp - time.time() if exp else 0
            put(surf, F["small"], f"-> {dest or '?'}", (10, y + 20), DIM, W - 110)
            put(surf, F["small"], fmt_time(left) if exp else "", (W - 10, y + 20),
                RED if exp and left < 3600 else DIM, anchor="topright")
        y += rh
    if pages > 1:
        put(surf, F["small"], f"pág {pg + 1}/{pages}  (toca para pasar)", (W // 2, H - 10), DIM, anchor="center")

def view_srv(surf, d, flags, now):
    flags2 = (d or {}).get("Flags2", 0)
    in_srv, on_foot = bool(flags & (1 << 26)), bool(flags2 & 1)
    for label, cx, act in ((("RHINO" if "rhino" in ((d or {}).get("srvtype") or "").lower() else "SRV"), W // 4, in_srv), ("A PIE", 3 * W // 4, on_foot)):
        put(surf, F["small"], label + ("  (ACTIVO)" if act else "") + ("   ·   SALUDOS >" if label == "A PIE" else ""),
            (cx, TOP + 9), GREEN if act else (ORANGE if label == "A PIE" else DIM), anchor="center")
    pygame.draw.line(surf, DIM, (W // 2, TOP + 2), (W // 2, H - 4))
    for i, (txt, key, bit) in enumerate(SRV_BTNS + PIE_BTNS):
        dim = (i < 6 and on_foot) or (i >= 6 and in_srv)
        draw_button(surf, m5_rect(i), txt, key.upper(), F["btn"], dim=dim,
                    filled=bit is not None and in_srv and i < 6 and bool(flags & (1 << bit)),
                    lit=flash.get((5, i), 0) > now or glow(txt))

def bar(surf, x, y, w, label, pct, col):
    put(surf, F["small"], label, (x, y + 1), DIM)
    bx = pygame.Rect(x + 52, y, w - 52, 14)
    pygame.draw.rect(surf, DIM, bx, 1)
    if pct is not None:
        pygame.draw.rect(surf, col, (bx.x + 2, bx.y + 2, int((bx.w - 4) * max(0, min(100, pct)) / 100), bx.h - 4))
        put(surf, F["small"], f"{pct:.0f}%", (bx.right - 4, y + 1), WHITE, anchor="topright")

def view_combat(surf, d, flags, now):
    t = (d or {}).get("target")
    card = pygame.Rect(4, TOP + 2, W - 8, CARD6 - TOP - 4)
    pygame.draw.rect(surf, DIM, card, 1, border_radius=6)
    if not t:
        put(surf, F["big"], "SIN OBJETIVO", card.center, DIM, anchor="center")
    else:
        x, y = card.x + 8, card.y + 6
        cmdr = t.get("cmdr")
        put(surf, F["big"], (t.get("ship") or "?").upper(), (x, y), ORANGE, card.w - 140)
        put(surf, F["small"], f"ESCANEO {t.get('scan', 0)}/3", (card.right - 8, y + 4), DIM, anchor="topright")
        y += 28
        if t.get("pilot"):
            w_ = put(surf, F["btn"], t["pilot"], (x, y), BLUE if cmdr else ORANGE, card.w - 170)
            if cmdr:
                put(surf, F["small"], " COMANDANTE", (x + w_ + 4, y + 4), BLUE)
            ia_ = t.get("inara") or {}
            if cmdr and ia_ and not ia_.get("none"):
                ally = my_squad(d) and ia_.get("squad", "").lower() == my_squad(d).lower()
                put(surf, F["small"], ("ALIADO · " if ally else "INARA: ") + inara_line(ia_, d, short=True),
                    (card.right - 8, y + 4), GREEN if ally else ORANGE, card.w - w_ - 120, anchor="topright")
            else:
                put(surf, F["small"], t.get("rank") or "", (card.right - 8, y + 4), DIM, anchor="topright")
        y += 24
        half = (card.w - 24) // 2
        bar(surf, x, y, half, "ESCUDO", t.get("shield"), BLUE)
        bar(surf, x + half + 8, y, half, "CASCO", t.get("hull"), ORANGE)
        y += 20
        legal = t.get("legal") or ""
        ia2_ = t.get("inara") or {}
        tph_ = bool(cfg.get("cmdrpics", True)) and \
            (avatar_photo(surf, ia2_.get("avatar"), pygame.Rect(card.right - 62, card.bottom - 34, 56, 31)) or
             ship_photo(surf, {"type": t.get("stype"), "ship": t.get("ship") or ia2_.get("ship")}, {},
                        pygame.Rect(card.right - 62, card.bottom - 34, 56, 31)))
        wanted = legal.lower() == "wanted"
        put(surf, F["small"], ("BUSCADO" if wanted else legal.upper()) or "-", (x, y), RED if wanted else GREEN)
        if t.get("bounty"):
            put(surf, F["small"], f"RECOMPENSA {t['bounty']:,} cr".replace(",", "."), (x + 90, y), RED)
        if t.get("subsys"):
            sh = t.get("subhealth")
            put(surf, F["small"], f"{t['subsys']}" + (f"  {sh:.0f}%" if sh is not None else ""),
                (card.right - (68 if tph_ else 8), y), ORANGE, card.w // 2 - 20, anchor="topright")
    for i, (txt, key) in enumerate(COMBAT_BTNS):
        draw_button(surf, c6_rect(i), txt, key.upper(), F["btn"], lit=flash.get((6, i), 0) > now, compact=True)

FIGHTER_STATE = {"hangar": ("EN EL HANGAR", DIM), "out": ("LANZADO", GREEN), "dead": ("DESTRUIDO - RECONSTRUYENDO", RED),
                 "ready": ("RECONSTRUIDO - LISTO", ORANGE)}

def view_fighter(surf, d, flags, now):
    f = (d or {}).get("fighter") or {}
    card = pygame.Rect(4, TOP + 2, W - 8, CARD9 - TOP - 4)
    pygame.draw.rect(surf, DIM, card, 1, border_radius=6)
    txt, col = FIGHTER_STATE.get(f.get("state"), ("SIN DATOS DEL CAZA", DIM))
    if flags & (1 << 25):
        txt, col = "PILOTANDO EL CAZA", BLUE
    put(surf, F["small"], "CAZA", (card.x + 8, card.y + 6), DIM)
    put(surf, F["big"], txt, (card.x + 8, card.y + 22), col, card.w - 16)
    who = f.get("pilot")
    if who and f.get("state") == "out":
        put(surf, F["small"], f"Piloto: {who}", (card.x + 8, card.y + 50), ORANGE)
    orders = ui["orders"]
    for i, (t_, key, grp) in enumerate(FIGHTER_BTNS):
        draw_button(surf, c9_rect(i), t_, key.replace("KP", "NUM "), F["btn"],
                    filled=grp is not None and orders.get(grp) == i, lit=flash.get((9, i), 0) > now)

def view_log(surf, d, flags, now):
    with lock:
        log = list(state["log"])
    f = F["mono"]
    cw, lh = f.size("M")[0], f.get_linesize()
    ncols, nrows = (W - 8) // cw, (H - TOP - 4) // lh
    rows = []
    for line in reversed(log):
        rows[:0] = [line[i:i + ncols] for i in range(0, len(line), ncols)] or [""]
        if len(rows) >= nrows:
            break
    for j, r in enumerate(rows[-nrows:]):
        surf.blit(f.render(r, True, RED if r.startswith("[PANEL]") else ORANGE), (4, TOP + 2 + j * lh))
    if ui["pause"]:
        t = F["btn"].render(" PAUSA ", True, BLACK, WHITE)
        surf.blit(t, (W - t.get_width() - 6, TOP + 4))
    if not log:
        put(surf, F["btn"], "Esperando eventos del journal...", (8, TOP + 10), DIM)

# ---------- formatos ----------
def crx(v):
    v = v or 0
    return fnum(v, 0) if abs(v) < 1e6 else cr(v)

def cr(v):
    v = v or 0
    a = abs(v)
    if a >= 1e9: return f"{v / 1e9:.2f} mil M".replace(".", ",")
    if a >= 1e6: return f"{v / 1e6:.1f} M".replace(".", ",")
    if a >= 1e3: return f"{v / 1e3:.0f} k"
    return f"{v:.0f}"

def dur(sec):
    sec = max(0, int(sec)); return f"{sec // 3600}h {sec % 3600 // 60:02d}m"

