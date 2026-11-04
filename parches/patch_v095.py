#!/usr/bin/env python3
# Parche v0.95: bajas a pie / en nave en el RESUMEN DEL DIA, REGISTRO DE COMBATE en lugar de GALNET en la mega nave
# y la nave de investigacion de Operations con foto de mega nave. Va con el sender v0.95.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def mega_dock" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.94b' not in s:
    sys.exit("Este parche es para la v0.94b")
shutil.copy(P, P + ".bak94b")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

rep('''("DERRIBOS", str(s_.get("kills", 0))),''',
    '''("BAJAS  pie · nave", f"{s_.get('kfoot', 0)} · {s_.get('kills', 0) - s_.get('kfoot', 0)}"),''')
rep('''        cells[cells.index(4)] = atr_cell(d, now)''', '''        cells[cells.index(4)] = atr_cell(d, now)
    if mega_dock(d) and 133 in cells:
        cells[cells.index(133)] = 61                 # mega nave: REGISTRO DE COMBATE en lugar de GALNET''')

CODE = r'''
# ---------- v0.95 ----------
def mega_dock(d):
    st = (d or {}).get("station") or {}
    nm = ((st.get("name") or "") + " " + (st.get("sraw") or "")).lower()
    return bool((d or {}).get("mega")) or (st.get("status") == "ATRACADO" and
                                         (st.get("type") == "MegaShip" or "megaship" in nm or "investig" in nm))

_ck1 = carrier_kind

def carrier_kind(d, st):
    nm = ((st.get("name") or "") + " " + (st.get("sraw") or "")).lower()
    if st.get("type") == "SurfaceStation" and ("investig" in nm or "megaship" in nm):
        return "meganave", "NAVE DE INVESTIGACIÓN", ORANGE
    return _ck1(d, st)

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")
rep('''# Enlace energético''', '''# Novedades v0.95
- RESUMEN DEL DÍA: BAJAS a pie · en nave por separado.
- Atracado en la mega nave: el cuadro de GALNET pasa a REGISTRO DE COMBATE.
- Operations: la «Nave de investigación» (masacre en mega nave) sale con la foto de la mega nave; el Runner con la de operaciones.
# Enlace energético''')
rep('    ("0.94", "Resumen del día, nombres de amigos, fotos de naves de CMDR, misiones primero y BATALLA TERMINADA"),\n',
    '    ("0.94", "Resumen del día, nombres de amigos, fotos de naves de CMDR, misiones primero y BATALLA TERMINADA"),\n'
    '    ("0.95", "Bajas a pie / nave, registro de combate en la mega nave y nave de investigación"),\n')
s = re.sub(r'PANEL_VER = "v0\.94b[^"]*"', 'PANEL_VER = "v0.95 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.95  (copia en " + P + ".bak94b)")
