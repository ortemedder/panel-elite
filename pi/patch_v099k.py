#!/usr/bin/env python3
# Parche v0.99k: vigilante. Si la pantalla se queda congelada mas de 45 s, apunta en el LOG
# donde estaba atascado cada hilo y reinicia el panel solo (systemd lo vuelve a arrancar en 3 s).
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def watchdog_loop" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.99j' not in s:
    sys.exit("Este parche es para la v0.99j")
shutil.copy(P, P + ".bak99j")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

CODE = r'''
# ---------- v0.99k: vigilante del bucle principal ----------
WD = {"t": time.time(), "on": False}
WD_SECS = 45

def wd_dump(why):
    import sys, traceback as tb_
    names = {t.ident: t.name for t in threading.enumerate()}
    out = [f"PANEL COLGADO ({why}): reinicio. Donde estaba cada hilo:"]
    for tid, fr in sys._current_frames().items():
        st = tb_.extract_stack(fr)[-4:]
        out.append(f"  [{names.get(tid, tid)}] " + " <- ".join(f"{x.name}:{x.lineno}" for x in reversed(st)))
        out.append("      " + ((st[-1].line or "") if st else ""))
    plog("\n".join(out))

def watchdog_loop():
    while True:
        time.sleep(5)
        if WD["on"] and time.time() - WD["t"] > WD_SECS:
            try:
                wd_dump(f"{time.time() - WD['t']:.0f} s sin dibujar")
            finally:
                os._exit(3)                              # systemd lo arranca otra vez

_big_go99k = big_go

def big_go(surf):
    WD["t"] = time.time()
    if not WD["on"]:
        WD["on"] = True
        threading.Thread(target=watchdog_loop, daemon=True, name="vigilante").start()
    return _big_go99k(surf)

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")
rep('''# Enlace energético''', '''# Novedades v0.99k
- Vigilante: si la pantalla se queda congelada más de 45 segundos, el panel apunta en el LOG dónde se atascó («PANEL COLGADO») y se reinicia solo.
# Enlace energético''')
rep('    ("0.99j", ', '    ("0.99k", "Vigilante: si se congela, LOG y reinicio solo"),\n    ("0.99j", ')
s = re.sub(r'PANEL_VER = "v0\.99j[^"]*"', 'PANEL_VER = "v0.99k · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99k  (copia en " + P + ".bak99j)")
