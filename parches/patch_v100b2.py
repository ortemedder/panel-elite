#!/usr/bin/env python3
# Parche v1.0 beta 2 (desde la beta 1):
#  - HDMI en modo PANEL: el borde de estado va por el exterior de la pantalla (no alrededor del panel).
#  - 4 CUADROS: los botones de cada cuadro funcionan al tocarlos (tocar fuera de un boton abre el cuadro en grande).
#  - MHz en verde aunque la CPU baje a 1200 MHz en reposo (es normal); naranja solo si la Pi se frena por calor o corriente.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if 'power.get("cap")' in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v1.0b1' not in s:
    sys.exit("Este parche es para la v1.0 beta 1")
shutil.copy(P, P + ".bak100b1")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# borde: en la HDMI siempre por fuera; el panel nitido ya no lleva el suyo; el panel normal solo si hay pantalla pequena
rep('''        if not hdmi_panel():
            draw_borders(BIG["surf"])''', '''        draw_borders(BIG["surf"])''')
rep('''            render(ss); decorate(ss); draw_borders(real); rhino_banner(ss)''',
    '''            render(ss); decorate(ss); rhino_banner(ss)''')
rep('''                draw_borders(surf)\n''', '''                if not SMALL.get("null"):
                    draw_borders(surf)\n''')
# MHz: naranja solo si de verdad se esta frenando
rep('''            power.update(now=bool(v & 1), past=bool(v & 0x10000), ok=True)''',
    '''            power.update(now=bool(v & 1), past=bool(v & 0x10000), ok=True, cap=bool(v & 0x6))''')
rep('''        out.append((f"{mhz:.0f} MHz", GREEN if not PERF_MAXMHZ[0] or mhz >= PERF_MAXMHZ[0] * 0.9 else ORANGE))''',
    '''        out.append((f"{mhz:.0f} MHz", ORANGE if power.get("cap") else GREEN))''')

CODE = r"""
# ---------- v1.0 beta 2: botones de los cuadros (4 CUADROS) ----------
_big_cell_b2 = big_cell

def big_cell(S, cell, v, d, flags, now, r, font, how, extra=""):
    if not BIG.get("rects"):
        BIG["cellmap"] = []
    if v != 150:
        top = r.y + font.size(str(MENU.get(v, v)).upper() + extra)[1] + 6
        BIG["cellmap"].append((v, pygame.Rect(r.x + 4, top, r.w - 8, r.bottom - 3 - top), how))
    return _big_cell_b2(S, cell, v, d, flags, now, r, font, how, extra)

def cell_point(area, how, X, Y):
    # punto de la pantalla grande -> punto del panel (480x320) dentro de ese cuadro
    if how == "fill":
        return (X - area.x) * W / area.w, TOP + (Y - area.y) * (H - TOP) / area.h
    sc = min(area.w / W, area.h / (H - TOP))
    cw, ch = W * sc, (H - TOP) * sc
    x0 = area.centerx - cw / 2
    y0 = area.y if how == "top" else area.centery - ch / 2
    return (X - x0) / sc, TOP + (Y - y0) / sc

_big_tap_b2 = big_tap

def big_tap(xn, yn):
    if not hdmi_panel():
        bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
        X, Y = xn * bw, yn * bh
        for v, area, how in BIG.get("cellmap") or []:
            if not area.collidepoint(X, Y) or v not in VIEWS:
                continue
            px, py = cell_point(area, how, X, Y)
            if not (0 <= px < W and TOP <= py < H):
                break
            f0, v0 = dict(flash), ui["view"]
            ui["view"] = v
            on_tap(int(px), int(py))
            if flash != f0 or ui["view"] != v:          # ha tocado un boton: se queda en 4 CUADROS
                if ui["view"] == v:
                    ui["view"] = v0
                TAP_EV.set()
                return
            ui["view"] = v0
            break
    _big_tap_b2(xn, yn)

"""
rep("\ndef render(surf):", CODE + "\ndef render(surf):")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 2
- Pantalla HDMI en modo PANEL: el borde de estado va por el borde exterior de la pantalla.
- 4 CUADROS: los botones de cada cuadro (COMBATE, PIPS...) funcionan al tocarlos. Tocar fuera de un botón abre el cuadro en grande, como antes.
- Los MHz salen en naranja solo si la Pi se está frenando (calor o falta de corriente); bajar a 1200 MHz en reposo es normal.
# Enlace energético''')
rep('    ("1.0b1", ', '    ("1.0b2", "Borde por fuera en la HDMI; botones en 4 CUADROS; MHz"),\n    ("1.0b1", ')
s = re.sub(r'PANEL_VER = "v1\.0b1[^"]*"', 'PANEL_VER = "v1.0b2 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 2  (copia en " + P + ".bak100b1)")
