#!/usr/bin/env python3
# Parche v1.0 beta 7 (desde la beta 6b): pantalla de espera alternando cada 20 s entre la normal (con GALNET)
# y una pantalla entera de tu faccion: logo, radar con tus sistemas, alertas de guerra y elecciones,
# sistemas controlados y una cinta con los estados. Logo: logo_faccion.png junto a panel.py.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def draw_fac_screen" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b6b', s):
    sys.exit("Este parche es para la v1.0 beta 6b")
shutil.copy(P, P + ".bak100b6b")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

CODE = r'''
# ---------- v1.0 beta 7: pantalla de espera de la faccion ----------
idle_crawl = _idle_crawl_b4                              # el recuadro vuelve a ser solo GALNET
LOGO = {"src": None, "miss": False}
_LOGOC = {}

def logo_src():
    if LOGO["src"] is None and not LOGO["miss"]:
        try:
            LOGO["src"] = pygame.image.load(os.path.join(PANEL_DIR, "logo_faccion.png"))
        except Exception:
            LOGO["miss"] = True
    return LOGO["src"]

def blit_logo(surf, rect, dark=255):
    """El logo de la faccion en rect (nitido tambien en la HDMI). False si no hay logo."""
    src = logo_src()
    if src is None:
        return False
    real, rr = (surf.real, surf._r(rect)) if type(surf).__name__ == "ScaledSurf" else (surf, pygame.Rect(rect))
    key = (rr.w, rr.h, dark)
    if key not in _LOGOC:
        try:
            im = pygame.transform.smoothscale(src, (rr.w, rr.h))
        except ValueError:
            im = pygame.transform.scale(src, (rr.w, rr.h))
        if dark < 255:
            im = im.copy(); im.fill((dark, dark, dark, 255), special_flags=pygame.BLEND_RGBA_MULT)
        _LOGOC[key] = im
    real.blit(_LOGOC[key], rr.topleft)
    return True

def shield(surf, cx, cy, col):
    pygame.draw.polygon(surf, col, [(cx - 14, cy - 16), (cx + 14, cy - 16), (cx + 14, cy + 2), (cx, cy + 18), (cx - 14, cy + 2)], 2)
    pygame.draw.line(surf, col, (cx, cy - 12), (cx, cy + 10), 2); pygame.draw.line(surf, col, (cx - 8, cy - 4), (cx + 8, cy - 4), 2)

def fac_war(v):
    return bool(v.get("conflictos")) or any(x in ("War", "CivilWar", "Election") for x in (v.get("activos") or []) + (v.get("pendientes") or []))

def draw_fac_screen(surf, now):
    D, S, gap = fac_rows()
    surf.fill(BLACK)
    for x in range(0, W, 24):
        pygame.draw.line(surf, (14, 9, 3), (x, 0), (x, H))
    for y in range(0, H, 24):
        pygame.draw.line(surf, (14, 9, 3), (0, y), (W, y))
    # cabecera
    if not blit_logo(surf, pygame.Rect(4, 2, 46, 46)):
        shield(surf, 26, 24, ORANGE)
    put(surf, F["big"], (D.get("faccion") or "").upper(), (56, 6), ORANGE, W - 170)
    nctl = sum(1 for v in S if v.get("ctrl"))
    med = sum(v["inf"] for v in S) / len(S)
    put(surf, F["small"], f"{nctl} sistemas controlados de {len(S)} · influencia media {med:.1f} %".replace(".", ","), (56, 32), DIM, W - 64)
    tmax = max([v.get("t") or 0 for v in S] or [0])
    a_txt, a_col = fac_age(tmax)
    put(surf, F["small"], "act. " + a_txt, (W - 8, 8), a_col, anchor="topright")
    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 8, 22), ORANGE, anchor="topright")
    pygame.draw.line(surf, ORANGE, (6, 50), (W - 6, 50), 1)
    # radar con tus sistemas
    R = pygame.Rect(6, 56, 200, 200); c = R.center; rad = 96
    blit_logo(surf, pygame.Rect(c[0] - 85, c[1] - 85, 170, 170), dark=40)
    for k in (1, 2, 3):
        pygame.draw.circle(surf, (40, 26, 8), c, rad * k // 3, 1)
    pygame.draw.line(surf, (40, 26, 8), (c[0] - rad, c[1]), (c[0] + rad, c[1]))
    pygame.draw.line(surf, (40, 26, 8), (c[0], c[1] - rad), (c[0], c[1] + rad))
    ang = math.radians((now * 60) % 360)
    for k in range(28):
        a = ang - math.radians(k * 1.4)
        f_ = (1 - k / 28) * 0.5
        pygame.draw.line(surf, (int(255 * f_), int(140 * f_), 0), c, (c[0] + rad * math.cos(a), c[1] + rad * math.sin(a)), 2)
    ps = [v for v in S if v.get("pos") and None not in v["pos"]]
    used = []
    if ps:
        ctl_ = [v for v in ps if v.get("ctrl")] or ps
        mx = sum(v["pos"][0] for v in ctl_) / len(ctl_); mz = sum(v["pos"][2] for v in ctl_) / len(ctl_)
        ext = sorted(max(abs(v["pos"][0] - mx), abs(v["pos"][2] - mz)) for v in ps)
        ext = (ext[int(len(ext) * 0.9)] if len(ext) > 3 else ext[-1]) or 1     # el 90 % mas cercano, sin que uno lejano lo encoja todo
        blink = int(now * 2) % 2
        for v in sorted(ps, key=lambda v: (fac_war(v), v.get("ctrl"))):
            dx, dz = (v["pos"][0] - mx) / ext, (v["pos"][2] - mz) / ext
            d_ = math.hypot(dx, dz)
            if d_ > 1:
                dx, dz = dx / d_, dz / d_                 # los lejanos, en el borde
            px, py = int(c[0] + dx * rad * 0.88), int(c[1] - dz * rad * 0.88)
            war = fac_war(v)
            r = 3 + int(v["inf"] / 18)
            if v.get("ctrl"):
                for g in range(3):
                    pygame.draw.circle(surf, (90 - g * 25, 50 - g * 15, 0), (px, py), r + 6 - g * 2)
            pygame.draw.circle(surf, RED if war else ORANGE if v.get("ctrl") else (150, 150, 150), (px, py), r)
            if war and blink:
                pygame.draw.circle(surf, RED, (px, py), r + 6, 1)
            if v.get("ctrl") or war:
                nm = v["sys"].upper()
                nm = nm if len(nm) <= 12 else nm[:11] + "…"
                tw = tw_(F["tiny"], nm)
                lr = pygame.Rect(px + r + 3, py - 7, tw, 12)
                if lr.right > R.right:
                    lr.right = px - r - 3
                if R.contains(lr) and not any(lr.colliderect(u) for u in used):
                    used.append(lr)
                    put(surf, F["tiny"], nm, lr.topleft, RED if war else (230, 170, 90))
    put(surf, F["tiny"], "MAPA DE LA FACCIÓN", (R.x + 4, R.bottom - 14), DIM)
    # alertas
    X, y = 214, 58
    war = [v for v in S if fac_war(v)]
    if war:
        box = pygame.Rect(X, y, W - X - 6, 18 + min(4, len(war)) * 30)
        pygame.draw.rect(surf, (30, 0, 0), box, border_radius=6)
        pygame.draw.rect(surf, RED if int(now * 2) % 2 else (120, 0, 0), box, 2, border_radius=6)
        put(surf, F["small"], "ALERTAS", (X + 8, y + 3), RED)
        yy = y + 18
        for v in war[:4]:
            cf = (v.get("conflictos") or [{}])[0]
            t = tipo_es(cf.get("tipo") or next((x for x in (v.get("activos") or []) + (v.get("pendientes") or []) if x in ("War", "CivilWar", "Election")), "war"))
            put(surf, F["small"], f"{t} · {v['sys']}", (X + 8, yy), WHITE, box.w - 16)
            put(surf, F["tiny"], f"contra {cf.get('contra') or '?'} · {cf.get('ganados') or 0}-{cf.get('perdidos') or 0} días", (X + 8, yy + 14), RED, box.w - 16)
            yy += 30
        y = box.bottom + 8
    put(surf, F["small"], "SISTEMAS CONTROLADOS", (X, y), DIM); y += 16
    for v in sorted([v for v in S if v.get("ctrl")], key=lambda v: -v["inf"]):
        if y + 14 > H - 28:
            break
        g = gap(v)
        put(surf, F["tiny"], v["sys"].upper(), (X, y), ORANGE, 110)
        bx = pygame.Rect(X + 112, y + 3, 90, 8); pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, ORANGE, (bx.x + 1, bx.y + 1, int(88 * min(100, v["inf"]) / 100), 6))
        put(surf, F["tiny"], f"{v['inf']:.0f}%", (W - 8, y), GREEN if g >= 5 else RED, anchor="topright")
        y += 14
    # cinta con los estados
    pygame.draw.line(surf, ORANGE, (6, H - 24), (W - 6, H - 24), 1)
    segs = []
    for v in S:
        parts = fac_parts(v)
        hoy, media, alto = traf(v)
        if alto:
            parts = parts + [(f"TRÁFICO ALTO {hoy} cmdr", RED)]
        if parts:
            segs.append((v["sys"].upper() + ": ", ORANGE))
            for i, (t, col) in enumerate(parts):
                segs.append(((", " if i else "") + t, col))
            segs.append(("     ·     ", DIM))
    if segs:
        total = sum(tw_(F["small"], t) for t, c in segs) or 1
        x0 = 8 - int((now * 40) % total)
        old = surf.get_clip(); surf.set_clip(pygame.Rect(0, H - 22, W, 22))
        x = x0
        while x < W:
            for t, col in segs:
                w_ = tw_(F["small"], t)
                if x + w_ > 0 and x < W:
                    put(surf, F["small"], t, (x, H - 20), col)
                x += w_
        surf.set_clip(old)
    else:
        put(surf, F["small"], "sin estados especiales en tus sistemas", (W // 2, H - 12), DIM, anchor="center")

_draw_idle_b7 = draw_idle

def draw_idle(surf, now):
    D, S, gap = fac_rows()
    if S and int(now // 20) % 2 == 1:
        try:
            draw_fac_screen(surf, now); return
        except Exception as e:
            log_exc("espera facción", e)
    _draw_idle_b7(surf, now)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 7
- Pantalla de espera: 20 s la normal (foto, hora y GALNET) y 20 s una pantalla entera de tu facción, con su logo (logo_faccion.png junto a panel.py), un radar con tus sistemas en su posición (los controlados brillan, los que están en guerra o elecciones parpadean en rojo), un recuadro de ALERTAS, los sistemas controlados con su influencia y una cinta que va pasando con los estados de todos tus sistemas.
# Enlace energético''')
rep('    ("1.0b6b", ', '    ("1.0b7", "Pantalla de espera de la facción con logo, radar y alertas"),\n    ("1.0b6b", ')
s = re.sub(r'PANEL_VER = "v1\.0b6b[^"]*"', 'PANEL_VER = "v1.0b7 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 7  (copia en " + P + ".bak100b6b)")
