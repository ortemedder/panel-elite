#!/usr/bin/env python3
# Parche v0.99c: fotos de los cazas (F63 Condor, GU-97, Taipan y los guardianes XG7/XG8/XG9).
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if '"f63condor"' in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.99' not in s:
    sys.exit("Este parche es para la v0.99b")
shutil.copy(P, P + ".bak99b")
old = '''    "kestrelmkii": "kestrel", "lynxhighliner": "lynx", "anacondamkii": "anaconda_mkii"}'''
new = '''    "kestrelmkii": "kestrel", "lynxhighliner": "lynx", "anacondamkii": "anaconda_mkii",
    "f63condor": "federation_fighter", "condor": "federation_fighter", "gu97": "empire_fighter",
    "taipan": "independent_fighter", "xg7trident": "gdn_hybrid_fighter_v1", "trident": "gdn_hybrid_fighter_v1",
    "xg8javelin": "gdn_hybrid_fighter_v2", "javelin": "gdn_hybrid_fighter_v2", "xg9lance": "gdn_hybrid_fighter_v3",
    "lance": "gdn_hybrid_fighter_v3"}'''
if old not in s:
    sys.exit("No encuentro la tabla de naves")
s = s.replace(old, new, 1)
s = s.replace('    ("0.99b", "Nave fijada sin armas: ficha OBJETIVO en la pantalla grande"),\n',
              '    ("0.99b", "Nave fijada sin armas: ficha OBJETIVO en la pantalla grande"),\n'
              '    ("0.99c", "Fotos de los cazas"),\n', 1)
s = re.sub(r'PANEL_VER = "v0\.99[^"]*"', 'PANEL_VER = "v0.99c · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99c  (copia en " + P + ".bak99b)")
