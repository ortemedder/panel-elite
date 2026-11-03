import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak25")
s = open(p, encoding="utf-8").read()
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
if "FuelReservoir" in s:
    print("ya estaba"); raise SystemExit
rep('''    fuel = ((d or {}).get("Fuel") or {}).get("FuelMain")
    cap = (d or {}).get("fuelcap")
''', '''    fuel = ((d or {}).get("Fuel") or {}).get("FuelMain")
    cap = (d or {}).get("fuelcap")
    if (d or {}).get("Flags", 0) & (1 << 26):
        fuel, cap = ((d or {}).get("Fuel") or {}).get("FuelReservoir"), None
''')
rep('''    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
''', '''    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
    if flags & (1 << 26):
        fuel, cap = (d.get("Fuel") or {}).get("FuelReservoir"), None
''')
rep('''                put(surf, F["small"], inv, (240, y + 8), WHITE, W - 248)
        draw_compass(surf, d, d.get("bio") or {})''', '''                put(surf, F["small"], inv, (240, y + 8), WHITE, W - 248)
        sf = (d.get("Fuel") or {}).get("FuelReservoir")
        put(surf, F["small"], "COMBUSTIBLE", (8, y + 40), DIM)
        put(surf, F["big"], f"{sf:.2f} t".replace(".", ",") if sf is not None else "?", (110, y + 34),
            RED if sf is not None and sf < 0.1 else ORANGE)
        sh = flags & 8
        put(surf, F["btn"], "ESCUDOS ACTIVOS" if sh else "SIN ESCUDOS", (W - 8, y + 36), BLUE if sh else RED, anchor="topright")
        draw_compass(surf, d, d.get("bio") or {})''')
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.25 · 29/10/2026 01:05"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
