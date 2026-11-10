#!/usr/bin/env python3
# Parche v1.0 beta 12b (desde la beta 12): COLONIZACION se abria al atracar pero enseguida la tapaba el cambio
# automatico a ESTACION. Ahora espera 3 s y, durante 8 s, si otro cambio automatico la quita, vuelve a ella.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def col_pend" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b12 ', s):
    sys.exit("Este parche es para la v1.0 beta 12")
shutil.copy(P, P + ".bak100b12")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('''            ui["view"] = 135; ui["colsel"] = None; ui["colpg"] = 0
            plog("Colonización: abro la pestaña (" + why + ")")''', '''            COLB["pend"] = (now + 3, why)                # b12b: despues de que se asiente el atraque''')

CODE = r'''
# ---------- v1.0 beta 12b: COLONIZACION gana al cambio automatico de ESTACION ----------
COLB.setdefault("pend", None)
COLB.setdefault("hold", 0)

def col_pend(now):
    p = COLB.get("pend")
    if p and now >= p[0]:
        COLB["pend"] = None
        ui["view"] = 135; ui["colsel"] = None; ui["colpg"] = 0
        COLB["hold"] = now + 8
        plog("Colonización: abro la pestaña (" + p[1] + ")")
    elif now < COLB.get("hold", 0) and ui.get("view") in (0, 8, 100, 126, 127) and not ui.get("idle_on"):
        ui["view"] = 135                                 # otro cambio automatico la ha quitado: vuelve
        plog("Colonización: vuelvo a la pestaña (la había tapado otro cambio automático)")

_render_b12b = render

def render(surf):
    r_ = _render_b12b(surf)
    try:
        col_pend(time.time())
    except Exception as e:
        log_exc("colonización", e)
    return r_

_on_tap_b12b = on_tap

def on_tap(x, y):
    COLB["hold"] = 0                                     # si tocas tu, manda lo que tocas
    _on_tap_b12b(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 12''', '''# Novedades v1.0 beta 12b
- COLONIZACIÓN ya no la tapa el cambio automático a ESTACIÓN al atracar: espera 3 s y, si otro cambio automático la quita en los 8 s siguientes, vuelve a ella. Si tocas la pantalla, manda lo que tocas.
# Novedades v1.0 beta 12''')
rep('    ("1.0b12", ', '    ("1.0b12b", "COLONIZACIÓN ya no la tapa ESTACIÓN al atracar"),\n    ("1.0b12", ')
s = re.sub(r'PANEL_VER = "v1\.0b12 [^"]*"', 'PANEL_VER = "v1.0b12b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 12b  (copia en " + P + ".bak100b12)")
