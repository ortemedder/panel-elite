import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak15")
s = open(p, encoding="utf-8").read()
if "def big_frame" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- pantalla grande HDMI: tablero de 4 cuadros segun la situacion ----------
BIG = {"dev": None, "fb": None, "w": 0, "h": 0, "bpp": 16, "stride": 0, "surf": None, "s16": None,
       "last": None, "n": 0, "fonts": None, "cell": None}
BIG_SETS = {"VIAJE": [100, 3, 71, 11], "PLANETA": [100, 73, 72, 128],
            "ATRACADO": [100, 8, 127, 4], "COMBATE": [100, 6, 9, 11]}

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

def big_blit(dst, src, area):
    s = min(area.w / src.get_width(), area.h / src.get_height())
    size = (max(1, int(src.get_width() * s)), max(1, int(src.get_height() * s)))
    try:
        img = pygame.transform.smoothscale(src, size)
    except ValueError:
        img = pygame.transform.scale(src, size)
    dst.blit(img, img.get_rect(center=area.center))

def big_mode(d, flags):
    f2 = d.get("Flags2", 0)
    if flags & 1:
        return "ATRACADO"
    if f2 & 1 or flags & ((1 << 26) | 2 | (1 << 21)):
        return "PLANETA"
    if d.get("target") or flags & 64:
        return "COMBATE"
    return "VIAJE"

def render_big():
    S, cell = BIG["surf"], BIG["cell"]
    bw, bh = BIG["w"], BIG["h"]
    with lock:
        d, rx = state["data"], state["rx"]
    now = time.time()
    online = d is not None and now - rx < 5
    if BIG["fonts"] is None:
        BIG["fonts"] = (pygame.font.Font(None, 40), pygame.font.Font(None, 26))
    fbig, fsm = BIG["fonts"]
    S.fill(BLACK)
    flags = (d or {}).get("Flags", 0) if online else 0
    full = None
    if ui.get("alert") and now < ui["alert"]["until"]:
        full = "alert"
    elif xa.get("a") and now < xa["a"]["until"]:
        full = "xa"
    elif online and (flags & (1 << 11) or now < scoop["full_until"]):
        full = "scoop"
    if now - ui["start"] < 3:
        draw_splash(cell, now); big_blit(S, cell, S.get_rect()); return
    if not online:
        draw_idle(cell, now); big_blit(S, cell, S.get_rect()); return
    if full:
        cell.fill(BLACK)
        if full == "alert":
            draw_alert(cell, now)
        elif full == "xa":
            draw_xa(cell, now)
        else:
            draw_scoop(cell, d, flags, now)
        big_blit(S, cell, S.get_rect()); return
    mode = big_mode(d, flags)
    hh = 44
    put(S, fbig, (d.get("system") or "---").upper(), (12, 9), ORANGE, 400)
    put(S, fsm, mode, (bw // 2 - 60, 14), GREEN, 140, anchor="midtop")
    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
    if fuel is not None:
        bx = pygame.Rect(bw // 2 + 20, 12, 240, 18)
        pygame.draw.rect(S, DIM, bx, 1)
        if cap:
            pct = max(0.0, min(1.0, fuel / cap))
            pygame.draw.rect(S, RED if pct < 0.25 else ORANGE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * pct), bx.h - 4))
        put(S, fsm, f"FUEL {fuel:.1f} t", (bx.right + 10, 14), ORANGE)
    put(S, fbig, time.strftime("%H:%M"), (bw - 12, 9), ORANGE, anchor="topright")
    pygame.draw.line(S, DIM, (0, hh - 2), (bw, hh - 2), 1)
    cw, ch = bw // 2, (bh - hh) // 2
    for i, v in enumerate(BIG_SETS[mode]):
        r = pygame.Rect((i % 2) * cw, hh + (i // 2) * ch, cw, ch)
        cell.fill(BLACK)
        fn = VIEWS.get(v)
        try:
            if fn:
                fn(cell, d, flags, now)
        except Exception as e:
            put(cell, F["small"], f"error: {e}"[:60], (8, TOP + 8), RED)
        pygame.draw.rect(S, DIM, r.inflate(-6, -6), 1, border_radius=6)
        put(S, fsm, str(MENU.get(v, v)).upper(), (r.x + 12, r.y + 6), DIM, r.w - 24)
        big_blit(S, cell.subsurface((0, TOP, W, H - TOP)), pygame.Rect(r.x + 6, r.y + 26, r.w - 12, r.h - 32))

def big_frame():
    if BIG["fb"] is None:
        if BIG["dev"] is None and not big_open():
            BIG["dev"] = False
        if BIG["fb"] is None:
            return
    try:
        render_big()
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

'''
rep("def render(surf):", SNIP + "def render(surf):")
rep("            decorate(surf)\n", '            decorate(surf)\n            BIG["n"] += 1\n            if BIG["n"] % 2 == 0:\n                big_frame()\n')
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.15 · 28/10/2026 23:22"', s, count=1)
if not n: print("NO ENCONTRADO: PANEL_VER"); ok = False
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
