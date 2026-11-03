import shutil
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak3")
s = open(p, encoding="utf-8").read()
SNIP = r'''def draw_compass(surf, d, b):
    ship, lat, lon, R = b.get("ship"), b.get("lat"), b.get("lon"), b.get("R")
    out = bool((d or {}).get("Flags", 0) & (1 << 26)) or bool((d or {}).get("Flags2", 0) & 1)
    if not ship or lat is None or not R or not out:
        return
    y0 = H - 62
    pygame.draw.line(surf, DIM, (8, y0 - 4), (W - 8, y0 - 4))
    dist = hav(ship, (lat, lon), R)
    p1, p2, dl = math.radians(lat), math.radians(ship[0]), math.radians(ship[1] - lon)
    brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                  math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
    hdg = b.get("hdg")
    cx, cy, r = 32, y0 + 17, 17
    pygame.draw.circle(surf, DIM, (cx, cy), r, 1)
    if hdg is not None:
        a = math.radians(brg - hdg)
        pt = lambda k, da: (cx + r * k * math.sin(a + da), cy - r * k * math.cos(a + da))
        pygame.draw.polygon(surf, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
    txt = f"{dist / 1000:.1f} km".replace(".", ",") if dist >= 1000 else f"{dist:.0f} m"
    put(surf, F["small"], "NAVE", (60, y0 + 2), DIM)
    put(surf, F["big"], txt, (60, y0 + 14), GREEN)
    put(surf, F["btn"], f"rumbo {brg:.0f}°", (W - 8, y0 + 4), ORANGE, anchor="topright")
    if hdg is not None:
        put(surf, F["small"], f"vas a {hdg:.0f}°", (W - 8, y0 + 24), DIM, anchor="topright")

'''
old = '    pygame.draw.line(surf, DIM, (8, H - 24), (W - 8, H - 24))\n    put(surf, F["btn"], f"MUESTRAS SIN VENDER'
if "def draw_compass" in s:
    print("ya estaba")
elif old not in s:
    print("NO ENCONTRADO")
else:
    s = s.replace("def view_bio(", SNIP + "def view_bio(", 1)
    s = s.replace(old, "    draw_compass(surf, d, b)\n" + old, 1)
    open(p, "w", encoding="utf-8").write(s)
    print("OK")
