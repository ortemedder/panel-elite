#!/usr/bin/env python3
# Parche v1.0 beta 6b (arreglo de la beta 6): con NITIDEZ ALTA los textos medidos salian la mitad de anchos
# y se montaban (estados de FACCION, nombres en VIAJES, ESPERANDO A ELITE DANGEROUS cortado, alertas).
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "# v1.0b6b" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v1.0b6 ' not in s and 'PANEL_VER = "v1.0b6·' not in s and not re.search(r'PANEL_VER = "v1\.0b6 ', s):
    sys.exit("Este parche es para la v1.0 beta 6")
shutil.copy(P, P + ".bak100b6")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('''def tw_(font, text):
    return font.size(str(text))[0] / getattr(font, "f", 1)''', '''def tw_(font, text):                                    # v1.0b6b: FontProxy ya mide en pixeles del panel
    return font.size(str(text))[0]''')
rep('''        tw, th = F["small"].size(txt)
        tw, th = int(tw / getattr(F["small"], "f", 1)), int(th / getattr(F["small"], "f", 1))''', '''        tw, th = F["small"].size(txt)''')

rep('''        t_ = (", " if i else "") + t
        w_ = tw_(font, t_)
        if x + w_ - pos[0] > maxw:
            put(surf, font, "…", (x, y), DIM); return
        put(surf, font, t_, (x, y), c); x += w_''', '''        t_ = (", " if i else "") + t
        w_ = tw_(font, t_)
        if x + w_ - pos[0] > maxw:                      # no cabe entero: lo que quepa, cortado
            rest = maxw - (x - pos[0])
            if rest > tw_(font, "…") + 20:
                put(surf, font, t_, (x, y), c, rest)
            else:
                put(surf, font, "…", (x, y), DIM)
            return
        put(surf, font, t_, (x, y), c); x += w_''')
rep('''- Necesita la escucha de EDDN nueva (v3) en la Orange Pi.''', '''- Necesita la escucha de EDDN nueva (v3) en la Orange Pi.
- 6b: con NITIDEZ ALTA los estados ya no se montan unos sobre otros, ni los nombres de VIAJES, y «ESPERANDO A ELITE DANGEROUS» sale entero.''')
rep('    ("1.0b6", ', '    ("1.0b6b", "Textos que se montaban con NITIDEZ ALTA"),\n    ("1.0b6", ')
s = re.sub(r'PANEL_VER = "v1\.0b6[^"]*"', 'PANEL_VER = "v1.0b6b · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 6b  (copia en " + P + ".bak100b6)")
