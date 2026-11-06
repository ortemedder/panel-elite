#!/usr/bin/env python3
# Parche reloj (v0.99f o posterior -> letra siguiente)
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def pc_now" in s:
    sys.exit("Ya estaba aplicado")
m = re.search(r'PANEL_VER = "v0\.99([f-y])', s)
if not m:
    sys.exit("Este parche es para la v0.99f o posterior")
CUR = m.group(1); NEW = chr(ord(CUR) + 1)
shutil.copy(P, P + ".bak99" + CUR)

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

rep('''def mega_left(d, now):
    t0 = (d or {}).get("mega")
    return None if not t0 else t0 + MEGA_SECS - now''', '''def pc_now(d, now=None):
    """Hora del PC (la del juego). Si el sender manda su reloj, se corrige el de la Pi."""
    now = time.time() if now is None else now
    pn = (d or {}).get("pcnow")
    return now + (pn - state["rx"]) if pn and state.get("rx") else now

def mega_left(d, now):
    t0 = (d or {}).get("mega")
    return None if not t0 else t0 + MEGA_SECS - pc_now(d, now)''')
rep('''and time.time() - ((d or {}).get("scan_t") or 0) > 20''', '''and pc_now(d) - ((d or {}).get("scan_t") or 0) > 20''')
rep('''# Enlace energético''', '''# Novedades v0.99 (reloj)
- La cuenta atrás de la mega nave usa la hora del PC: funciona aunque el reloj de la Pi vaya mal.
# Enlace energético''')
if f'    ("0.99{CUR}", ' in s:
    rep(f'    ("0.99{CUR}", ', f'    ("0.99{NEW}", "Mega nave: cuenta atrás con la hora del PC"),\n    ("0.99{CUR}", ')
s = re.sub(r'PANEL_VER = "v0\.99' + CUR + '[^"]*"', 'PANEL_VER = "v0.99' + NEW + ' · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99" + NEW + "  (copia en " + P + ".bak99" + CUR + ")")
