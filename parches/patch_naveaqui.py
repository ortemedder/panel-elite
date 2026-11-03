import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak48")
s = open(p, encoding="utf-8").read()
if "def ship_here" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
rep('''def draw_compass(surf, d, b):
    ship, lat, lon, R = b.get("ship"), b.get("lat"), b.get("lon"), b.get("R")
    out = bool((d or {}).get("Flags", 0) & (1 << 26)) or bool((d or {}).get("Flags2", 0) & 1)
    if not ship or lat is None or not R or not out:
        return
''', '''SHIPOV = {"pos": None, "src": None, "cur": None}
NAVE_BTN = pygame.Rect(196, H - 60, 124, 40)

def ship_pos(b):
    s_ = b.get("ship")
    if s_ != SHIPOV["src"]:              # el juego da una posicion nueva: manda la del juego
        SHIPOV["src"], SHIPOV["pos"] = s_, None
    return SHIPOV["pos"] or s_

def ship_here():
    if SHIPOV["cur"]:
        SHIPOV["pos"] = list(SHIPOV["cur"])
        tap_flash(("nave", 0))

def draw_compass(surf, d, b):
    ship, lat, lon, R = ship_pos(b), b.get("lat"), b.get("lon"), b.get("R")
    out = bool((d or {}).get("Flags", 0) & (1 << 26)) or bool((d or {}).get("Flags2", 0) & 1)
    SHIPOV["cur"] = (lat, lon) if (out and lat is not None) else None
    if out and lat is not None and R:
        draw_button(surf, NAVE_BTN, "NAVE AQUÍ", None, F["btn"], lit=flash.get(("nave", 0), 0) > time.time())
    if not ship or lat is None or not R or not out:
        return
''')
L = s.split("\n")
t = next((i for i, l in enumerate(L) if l.strip() == "elif v == 71:"), None)
if t is None:
    print("NO ENCONTRADO: toque"); ok = False
else:
    ind = L[t][:len(L[t]) - len(L[t].lstrip())]
    L[t:t] = [ind + "elif v in (100, 73) and NAVE_BTN.collidepoint(x, y):", ind + "    ship_here(); return"]
s = "\n".join(L)
rep("\n]\n\ndef view_changelog", '\n    ("0.48", "Brújula NAVE: corrección automática y botón NAVE AQUÍ"),\n]\n\ndef view_changelog')
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.48 · 29/10/2026 14:10"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
