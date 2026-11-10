#!/usr/bin/env python3
# Parche v0.99j: cronometro de la mega nave a mano. En Operations sale el cuadro MEGA NAVE (15:00);
# al tocarlo empieza la cuenta atras; tocarlo otra vez la reinicia (segunda planta).
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def mega_tap" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.99i' not in s:
    sys.exit("Este parche es para la v0.99i")
shutil.copy(P, P + ".bak99i")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

CODE = r'''
# ---------- v0.99j: cronometro de la mega nave a mano ----------
MEGA = {"t0": None}

def ops_on(d):
    return bool(((d or {}).get("ops") or {}).get("on"))

def mega_left(d, now):
    if not ops_on(d):
        MEGA["t0"] = None
        return None
    t0 = MEGA["t0"]
    if t0 and t0 + MEGA_SECS - now < -30:
        MEGA["t0"] = t0 = None                        # acabado: vuelve a 15:00 en espera
    return False if not t0 else t0 + MEGA_SECS - now   # False = en espera de que lo toques

def mega_tap(now=None):
    MEGA["t0"] = time.time() if now is None else now
    xa.pop("mega60", None)
    play("ok")
    TAP_EV.set()

def mega_rect(w, h):
    k = h / H
    return pygame.Rect(w - int(140 * k), h - int(52 * k), int(132 * k), int(46 * k))

def mega_watch(d, now):
    left = mega_left(d, now)
    if not left:
        return
    k0 = XA_K[0]
    try:
        XA_K[0] = "opmega"
        key = MEGA["t0"]
        if 0 < left <= 60 and xa.get("mega60") != key:
            xa["mega60"] = key
            xa["a"] = dict(until=now + 6, col=RED, title="MEGA NAVE", big="¡QUEDA 1 MINUTO!", lines=["despega ya"])
            play("alarm")
    finally:
        XA_K[0] = k0

def draw_mega(surf, d, now):
    left = mega_left(d, now)
    if left is None:
        return
    w, h = surf.get_size()
    k = h / H
    key = round(k, 2)
    if key not in _MGF:
        _MGF[key] = (pygame.font.Font(None, int(40 * k)), pygame.font.Font(None, int(18 * k)))
    f1, f2 = _MGF[key] if type(surf).__name__ != "ScaledSurf" else (F["big"], F["small"])
    r = mega_rect(w, h)
    if left is False:
        col, txt, lab = DIM, "15:00", "MEGA NAVE · TOCA"
    else:
        col = GREEN if left > 300 else ORANGE if left > 60 else (RED if int(now * 3) % 2 == 0 else WHITE)
        l_ = max(0, int(left)); txt, lab = f"{l_ // 60}:{l_ % 60:02d}", "MEGA NAVE"
    pygame.draw.rect(surf, BLACK, r, border_radius=6)
    pygame.draw.rect(surf, col, r, 2, border_radius=6)
    put(surf, f2, lab, (r.centerx, r.y + int(10 * k)), DIM, anchor="center")
    put(surf, f1, txt, (r.centerx, r.y + int(30 * k)), col, anchor="center")

_on_tap99j = on_tap

def on_tap(x, y):
    with lock:
        d_ = state["data"]
    if ops_on(d_) and mega_rect(W, H).collidepoint(x, y):
        mega_tap(); return
    _on_tap99j(x, y)

_big_tap99j = big_tap

def big_tap(xn, yn):
    if not hdmi_panel():
        with lock:
            d_ = state["data"]
        bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
        if ops_on(d_) and mega_rect(bw, bh).collidepoint(xn * bw, yn * bh):
            mega_tap(); return
    _big_tap99j(xn, yn)

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")
rep('''# Enlace energético''', '''# Novedades v0.99j
- MEGA NAVE a mano: en Operations sale abajo a la derecha el cuadro MEGA NAVE · TOCA (15:00). Al tocarlo empieza la cuenta atrás de 15 minutos; tocarlo otra vez la vuelve a poner en 15:00 (segunda planta). Aviso al último minuto.
# Enlace energético''')
rep('    ("0.99g", "Solo pantalla', '    ("0.99j", "MEGA NAVE a mano: tocar el cuadro empieza los 15:00"),\n    ("0.99g", "Solo pantalla')
s = re.sub(r'PANEL_VER = "v0\.99i[^"]*"', 'PANEL_VER = "v0.99j · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99j  (copia en " + P + ".bak99i)")
