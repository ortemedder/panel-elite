#!/usr/bin/env python3
# Parche v1.0 beta 9 (desde la beta 8): boton FIJAR en la pantalla de espera para dejar quieta la pantalla
# que se esta viendo (normal, faccion o actividad). Sigue viva (radar, destellos, cinta, datos); solo deja de rotar.
# En ACTIVIDAD fijada, tocar el mapa cambia entre galaxia y tu zona. Al entrar al juego se suelta sola.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def hold_rect" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b8', s):
    sys.exit("Este parche es para la v1.0 beta 8")
shutil.copy(P, P + ".bak100b8")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# la hora y la actualizacion de las pantallas de faccion y actividad, a la izquierda del boton
rep('''    put(surf, F["small"], "act. " + a_txt, (W - 8, 8), a_col, anchor="topright")
    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 8, 22), ORANGE, anchor="topright")''',
    '''    put(surf, F["small"], "act. " + a_txt, (W - 72, 8), a_col, anchor="topright")
    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 72, 22), ORANGE, anchor="topright")''')
rep('''    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 8, 8), ORANGE, anchor="topright")
    pygame.draw.line(surf, ORANGE, (6, 50), (W - 6, 50), 1)
    M = pygame.Rect(6, 54, 300, 262)''', '''    put(surf, F["small"], time.strftime("%H:%M", time.localtime(now)), (W - 72, 8), ORANGE, anchor="topright")
    pygame.draw.line(surf, ORANGE, (6, 50), (W - 6, 50), 1)
    M = pygame.Rect(6, 54, 300, 262)''')
rep('''    gal = int(now // 10) % 2 == 0                        # 10 s galaxia, 10 s tu zona''',
    '''    gal = ACT_GAL[0] if IDLEHOLD["m"] == "act" else int(now // 10) % 2 == 0   # 10 s galaxia, 10 s tu zona (o fija)''')

CODE = r'''
# ---------- v1.0 beta 9: boton FIJAR de la pantalla de espera ----------
IDLEHOLD = {"m": None}
ACT_GAL = [True]
ACT_MAP = pygame.Rect(6, 54, 300, 262)

def hold_rect(m):
    return pygame.Rect(414, 26, 62, 34) if m == "norm" else pygame.Rect(W - 66, 6, 62, 38)

def draw_hold(surf, m, now):
    r = hold_rect(m)
    held = IDLEHOLD["m"] is not None
    if held:
        on = int(now * 2) % 2
        pygame.draw.rect(surf, RED if on else (120, 0, 0), r, border_radius=6)
        pygame.draw.rect(surf, WHITE, r, 1, border_radius=6)
        cx, cy = r.x + 13, r.centery
        pygame.draw.polygon(surf, WHITE, [(cx - 5, cy - 7), (cx - 5, cy + 7), (cx + 6, cy)])
        put(surf, F["tiny"], "SEGUIR", (r.x + 39, cy), WHITE, anchor="center")
    else:
        pygame.draw.rect(surf, ORANGE, r, border_radius=6)
        cx, cy = r.x + 12, r.centery
        pygame.draw.rect(surf, BLACK, (cx - 5, cy - 7, 4, 14)); pygame.draw.rect(surf, BLACK, (cx + 1, cy - 7, 4, 14))
        put(surf, F["tiny"], "FIJAR", (r.x + 39, cy), BLACK, anchor="center")

_draw_idle_b9 = draw_idle

def draw_idle(surf, now):
    m = IDLEHOLD["m"]
    if m:
        IDLE_MODE.update(m=m, t=time.time())
        try:
            if m == "fac" and fac_rows()[1]:
                draw_fac_screen(surf, now)
            elif m == "act":
                draw_act_screen(surf, now)
            else:
                _draw_idle_b7(surf, now)
        except Exception as e:
            log_exc("espera fija", e); _draw_idle_b7(surf, now)
    else:
        _draw_idle_b9(surf, now)
    draw_hold(surf, IDLE_MODE["m"] or "norm", now)

_render_b9 = render

def render(surf):
    r_ = _render_b9(surf)
    if not ui.get("idle_on") and IDLEHOLD["m"]:
        IDLEHOLD["m"] = None                             # al entrar al juego se suelta
    return r_

_on_tap_b9 = on_tap

def on_tap(x, y):
    if ui.get("idle_on"):
        m = IDLE_MODE["m"] or "norm"
        if hold_rect(m).inflate(10, 10).collidepoint(x, y):
            IDLEHOLD["m"] = None if IDLEHOLD["m"] else m
            if IDLEHOLD["m"] == "act":
                ACT_GAL[0] = int(time.time() // 10) % 2 == 0
            TAP_EV.set(); return
        if IDLEHOLD["m"] == "act" and ACT_MAP.collidepoint(x, y):
            ACT_GAL[0] = not ACT_GAL[0]; TAP_EV.set(); return
    _on_tap_b9(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Enlace energético''', '''# Novedades v1.0 beta 9
- Pantalla de espera: botón FIJAR arriba a la derecha. Deja quieta la pantalla que estás viendo (normal, facción o actividad) sin que deje de moverse ni de actualizarse; el botón pasa a SEGUIR en rojo parpadeando. Con ACTIVIDAD fijada, tocar el mapa cambia entre la galaxia y tu zona. Al entrar al juego se suelta sola. Tocar fuera del botón sigue abriendo el menú.
# Enlace energético''')
rep('    ("1.0b8", ', '    ("1.0b9", "Botón FIJAR en la pantalla de espera"),\n    ("1.0b8", ')
s = re.sub(r'PANEL_VER = "v1\.0b8[^"]*"', 'PANEL_VER = "v1.0b9 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 9  (copia en " + P + ".bak100b8)")
