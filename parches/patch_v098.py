#!/usr/bin/env python3
# Parche v0.98: pantalla tactil en la HDMI (p. ej. 7" ILITEK por USB) ademas de la pequena.
#  - HDMI en modo PANEL: se maneja tocando, igual que la pequena.
#  - HDMI en 4 CUADROS: tocar un cuadro lo abre en grande (modo PANEL); pulsacion larga (1,2 s) vuelve a 4 CUADROS.
#  - AJUSTES > OPCIONES > PANTALLA HDMI: PANEL / 4 CUADROS.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def touch_loop2" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.97c' not in s:
    sys.exit("Este parche es para la v0.97c")
shutil.copy(P, P + ".bak97c")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# el tactil principal: siempre el de la pantalla pequena si esta (ADS7846)
if "def is_touch" in s:                                # version con el parche del tactil USB (KORZO)
    rep('''    for p in list_devices():
        d = InputDevice(p)
        if is_touch(d):
            dev = d; break''', '''    devs_ = [InputDevice(p) for p in list_devices()]
    dev = next((d for d in devs_ if "ADS7846" in d.name), None) or next((d for d in devs_ if is_touch2(d)), None)''')
else:
    rep('''    for p in list_devices():
        d = InputDevice(p)
        if 'ADS7846' in d.name or 'touch' in d.name.lower():
            dev = d; break''', '''    devs_ = [InputDevice(p) for p in list_devices()]
    dev = next((d for d in devs_ if "ADS7846" in d.name), None) or next((d for d in devs_ if is_touch2(d)), None)''')
    rep('''        elif ev.type == ecodes.EV_KEY and ev.code == ecodes.BTN_TOUCH:''',
        '''        elif ev.type == ecodes.EV_KEY and ev.code in (ecodes.BTN_TOUCH, ecodes.BTN_LEFT):''')
rep('''    threading.Thread(target=touch_loop, daemon=True).start()''',
    '''    threading.Thread(target=touch_loop, daemon=True).start()
    threading.Thread(target=touch_loop2, daemon=True).start()''')
# AJUSTES > OPCIONES > PANTALLA HDMI
rep('''("FOTOS CMDR", cfg.get("cmdrpics", True))]''', '''("FOTOS CMDR", cfg.get("cmdrpics", True)), ("PANTALLA HDMI", None)]''')
rep('''        if name == "MERCADO":''', '''        if name == "PANTALLA HDMI":
            draw_button(surf, r, "HDMI", "PANEL" if hdmi_panel() else "4 CUADROS", F["btn"], filled=True,
                        lit=flash.get((124, i), 0) > now)
            continue
        if name == "MERCADO":''')
rep('''"keys", "killbtn", "mkt", "cmdrpics"]):''', '''"keys", "killbtn", "mkt", "cmdrpics", "hdmi"]):''')
rep('''                if k == "mkt":''', '''                if k == "hdmi":
                    tap_flash((124, i)); hdmi_toggle(); return
                if k == "mkt":''')

CODE = r'''
# ---------- v0.98: tactil de la pantalla HDMI ----------
def is_touch2(d):
    n = (d.name or "")
    if "ADS7846" in n or "touch" in n.lower() or "触控" in n or "qdtech" in n.lower() or "ilitek" in n.lower():
        return True
    try:
        from evdev import ecodes as ec_
        caps = d.capabilities()
        abs_ = [a[0] if isinstance(a, tuple) else a for a in caps.get(ec_.EV_ABS, [])]
        return ec_.ABS_X in abs_ and ec_.ABS_Y in abs_ and ec_.EV_REL not in caps
    except Exception:
        return False

def big_tap(xn, yn):
    """Toque en la HDMI (coordenadas 0..1)."""
    bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
    if hdmi_panel():
        sc = min(bw / W, bh / H)
        ox, oy = (bw - W * sc) / 2, (bh - H * sc) / 2
        px, py = (xn * bw - ox) / sc, (yn * bh - oy) / sc
        if 0 <= px < W and 0 <= py < H:
            on_tap(int(px), int(py))
        return
    for v, r in BIG.get("rects") or []:
        if r.collidepoint(xn * bw, yn * bh):
            ui["view"] = v if v in VIEWS else ui["view"]
            cfg["hdmi"] = "panel"; save_cfg(); TAP_EV.set()
            return

def touch_loop2():
    """Segundo tactil (el de la HDMI) cuando tambien esta la pantalla pequena."""
    try:
        from evdev import InputDevice, list_devices, ecodes as ec
    except ImportError:
        return
    while True:
        try:
            devs_ = [InputDevice(p) for p in list_devices()]
        except Exception:
            time.sleep(5); continue
        if not any("ADS7846" in d.name for d in devs_):
            return                                   # sin pantalla pequena lo lleva touch_loop
        dev = next((d for d in devs_ if "ADS7846" not in d.name and is_touch2(d)), None)
        if not dev:
            time.sleep(5); continue
        print("Tactil HDMI:", dev.name)
        try:
            ax, ay = dev.absinfo(ec.ABS_X), dev.absinfo(ec.ABS_Y)
            rx = ry = 0; t_down = None; pos = None
            for ev in dev.read_loop():
                if ev.type == ec.EV_ABS:
                    if ev.code == ec.ABS_X: rx = ev.value
                    elif ev.code == ec.ABS_Y: ry = ev.value
                elif ev.type == ec.EV_KEY and ev.code in (ec.BTN_TOUCH, ec.BTN_LEFT):
                    if ev.value == 1:
                        t_down, pos = time.time(), None
                    elif t_down is not None:
                        dur = time.time() - t_down; t_down = None
                        if pos is None:
                            continue
                        if dur >= 1.2:
                            hdmi_toggle(); TAP_EV.set()          # pulsacion larga: PANEL <-> 4 CUADROS
                        else:
                            big_tap(*pos)
                elif ev.type == ec.EV_SYN and t_down is not None and pos is None:
                    pos = ((rx - ax.min) / max(1, ax.max - ax.min), (ry - ay.min) / max(1, ay.max - ay.min))
        except OSError:
            time.sleep(2)                                # desconectado: se vuelve a buscar
        except Exception as e:
            log_exc("tactil HDMI", e); time.sleep(5)

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")
rep('''# Enlace energético''', '''# Novedades v0.98
- Pantalla HDMI táctil (por ejemplo una de 7" con táctil USB), junto a la pequeña: en modo PANEL se maneja tocando igual que la pequeña; en 4 CUADROS, tocar un cuadro lo abre en grande y una pulsación larga (más de 1 segundo) vuelve a 4 CUADROS. También en AJUSTES > OPCIONES > PANTALLA HDMI.
# Enlace energético''')
rep('    ("0.97c", "BASE DE INGENIERO solo en las bases de verdad"),\n',
    '    ("0.97c", "BASE DE INGENIERO solo en las bases de verdad"),\n'
    '    ("0.98", "Pantalla HDMI táctil: PANEL o 4 CUADROS"),\n')
s = re.sub(r'PANEL_VER = "v0\.97c[^"]*"', 'PANEL_VER = "v0.98 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.98  (copia en " + P + ".bak97c)")
