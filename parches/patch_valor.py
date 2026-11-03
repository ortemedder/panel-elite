import shutil
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak6")
s = open(p, encoding="utf-8").read()
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:60]); ok = False; return
    s = s.replace(old, new, 1)

rep('''        put(surf, F["small"], b.get("variant") or "", (8, y), DIM, W - 16); y += 20''',
'''        put(surf, F["small"], b.get("variant") or "", (8, y), DIM, W - 220)
        val = b.get("value")
        if val:
            txt = ("" if b.get("exact") else "~") + cr(val) + " cr"
            if b.get("bonus"):
                txt += f"  x5 = {cr(val * 5)}"
            put(surf, F["btn"], txt, (W - 8, y - 3), GREEN if b.get("bonus") else ORANGE, 210, anchor="topright")
        y += 20''')
rep('''    put(surf, F["btn"], f"MUESTRAS SIN VENDER: {b.get('unsold', 0)}", (8, H - 20), ORANGE)''',
'''    put(surf, F["btn"], f"MUESTRAS SIN VENDER: {b.get('unsold', 0)}", (8, H - 20), ORANGE)
    if b.get("unsold_cr"):
        put(surf, F["btn"], f"~ {cr(b['unsold_cr'])} cr", (W - 8, H - 20), ORANGE, anchor="topright")''')
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
