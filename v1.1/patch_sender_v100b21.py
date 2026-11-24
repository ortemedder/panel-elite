#!/usr/bin/env python3
# Sender v1.0 beta 21 (desde la beta 20), para el panel v2.3b3:
# - PLATAFORMAS: al atracar manda cuántas plataformas pequeñas, medianas y grandes tiene la estación (LandingPads),
#   para que el panel avise si tu nave cabe en un puerto planetario antes de llegar.
# Uso:  python patch_sender_v100b21.py elite_sender.py   (deja una copia elite_sender.py.bak100b20)
import shutil, sys
P = sys.argv[1] if len(sys.argv) > 1 else "elite_sender.py"
s = open(P, encoding="utf-8").read()
if 'SENDER_VER = "v1.0b21"' in s:
    sys.exit("Ya estaba aplicado")
if 'SENDER_VER = "v1.0b20"' not in s:
    sys.exit("Este parche es para el sender v1.0b20 (aplica antes patch_sender_v100b20.py)")
shutil.copy(P, P + ".bak100b20")

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('SENDER_VER = "v1.0b20"', 'SENDER_VER = "v1.0b21"')
rep('''                       st_gov=e.get("StationGovernment_Localised") or "", st_alleg=ALLEG_ES.get(e.get("StationAllegiance"), e.get("StationAllegiance") or ""))''',
    '''                       st_gov=e.get("StationGovernment_Localised") or "", st_alleg=ALLEG_ES.get(e.get("StationAllegiance"), e.get("StationAllegiance") or ""))
        lp = e.get("LandingPads") or {}
        sysinfo["st_pads"] = [lp.get("Small", 0), lp.get("Medium", 0), lp.get("Large", 0)] if lp else None   # v1.0b21''')
rep('''        for k in ("st_name", "st_faction", "st_fstate", "st_gov", "st_alleg"):''',
    '''        for k in ("st_name", "st_faction", "st_fstate", "st_gov", "st_alleg", "st_pads"):''')
open(P, "w", encoding="utf-8").write(s)
print("Sender actualizado a v1.0b21")
