#!/usr/bin/env python3
# Parche v0.97c: BASE DE INGENIERO solo en las bases de la tabla (las estaciones grandes tambien tienen servicio "engineer").
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "eng_by_base" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.97b' not in s:
    sys.exit("Este parche es para la v0.97b")
shutil.copy(P, P + ".bak97b")
old = '''        elif kind == "engbase":
            xa["a"] = dict(until=now + 6, col=BLUE, title="BASE DE INGENIERO", big=(text or "").upper(),
                           lines=["mira tus materiales en 12 > MATERIALES"])
            if auto_on("docking"):
                ui["view"] = 125'''
new = '''        elif kind == "engbase" and eng_by_base(text):
            eb_ = eng_by_base(text)
            st_, _ = eng_status(eb_, d)
            xa["a"] = dict(until=now + 6, col=BLUE, title="BASE DE INGENIERO", big=eb_["name"].upper(),
                           lines=[f"{eb_['base']}  ·  {st_}", "mira tus materiales en 12 > MATERIALES"])
            if auto_on("docking"):
                ui["view"] = 125'''
if old not in s:
    sys.exit("No encuentro el aviso de base de ingeniero")
s = s.replace(old, new, 1)
code = r'''
def eng_by_base(name):
    n = (name or "").strip().lower()
    return next((v for v in eng_table().values() if v.get("base", "").lower() == n), None) if n else None

'''
s = s.replace("\ndef render(surf):", code + "\ndef render(surf):", 1)
s = s.replace('    ("0.97b", "Ficha del ingeniero en NAVEGACIÓN y EXOBIOLOGÍA"),\n',
              '    ("0.97b", "Ficha del ingeniero en NAVEGACIÓN y EXOBIOLOGÍA"),\n'
              '    ("0.97c", "BASE DE INGENIERO solo en las bases de verdad"),\n', 1)
s = re.sub(r'PANEL_VER = "v0\.97b[^"]*"', 'PANEL_VER = "v0.97c · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.97c  (copia en " + P + ".bak97b)")
