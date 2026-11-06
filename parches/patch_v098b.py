#!/usr/bin/env python3
# Parche v0.98b: la HDMI tactil siempre responde (en 4 CUADROS sin cuadros, un toque pasa a PANEL) y los toques van al LOG.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "BIGTAP_N" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.98' not in s:
    sys.exit("Este parche es para la v0.98")
shutil.copy(P, P + ".bak98")
old = '''def big_tap(xn, yn):
    """Toque en la HDMI (coordenadas 0..1)."""
    bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600'''
new = '''BIGTAP_N = [0]

def big_tap(xn, yn):
    """Toque en la HDMI (coordenadas 0..1)."""
    bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
    if BIGTAP_N[0] < 30:
        BIGTAP_N[0] += 1
        plog(f"toque HDMI {xn:.2f},{yn:.2f}  modo {'PANEL' if hdmi_panel() else '4 CUADROS'}  cuadros {len(BIG.get('rects') or [])}")'''
old2 = '''    for v, r in BIG.get("rects") or []:
        if r.collidepoint(xn * bw, yn * bh):
            ui["view"] = v if v in VIEWS else ui["view"]
            cfg["hdmi"] = "panel"; save_cfg(); TAP_EV.set()
            return'''
new2 = '''    for v, r in BIG.get("rects") or []:
        if r.collidepoint(xn * bw, yn * bh):
            ui["view"] = v if v in VIEWS else ui["view"]
            cfg["hdmi"] = "panel"; save_cfg(); TAP_EV.set()
            return
    cfg["hdmi"] = "panel"; save_cfg(); TAP_EV.set()      # sin cuadros (espera, atraque...): pasa a PANEL'''
for a, b in ((old, new), (old2, new2)):
    if a not in s:
        sys.exit("No encuentro: " + a[:60])
    s = s.replace(a, b, 1)
s = s.replace('    ("0.98", "Pantalla HDMI táctil: PANEL o 4 CUADROS"),\n',
              '    ("0.98", "Pantalla HDMI táctil: PANEL o 4 CUADROS"),\n'
              '    ("0.98b", "La HDMI táctil siempre responde; toques al LOG"),\n', 1)
s = re.sub(r'PANEL_VER = "v0\.98[^"]*"', 'PANEL_VER = "v0.98b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.98b  (copia en " + P + ".bak98)")
