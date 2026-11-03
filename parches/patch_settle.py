import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak32")
s = open(p, encoding="utf-8").read()
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
if "DISTANCIA AL DESTINO" in s:
    print("ya estaba"); raise SystemExit
rep('''    src = D.get("src")
    put(surf, F["small"], f"datos: {src}" if src else''', '''    b = (d or {}).get("bio") or {}
    if D.get("lat") is not None and b.get("lat") is not None and b.get("R") and (d or {}).get("body") == D.get("sbody"):
        p1, p2 = math.radians(b["lat"]), math.radians(D["lat"])
        dl = math.radians(D["lon"] - b["lon"])
        brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                      math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
        m = hav((b["lat"], b["lon"]), (D["lat"], D["lon"]), b["R"])
        cx, cy, rr = 34, H - 48, 22
        pygame.draw.circle(surf, DIM, (cx, cy), rr, 1)
        hdg = b.get("hdg")
        if hdg is not None:
            a = math.radians(brg - hdg)
            pt = lambda k, da: (cx + rr * k * math.sin(a + da), cy - rr * k * math.cos(a + da))
            pygame.draw.polygon(surf, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
        txt = f"{m / 1000:.1f} km".replace(".", ",") if m >= 1000 else f"{m:.0f} m"
        put(surf, F["small"], "DISTANCIA AL DESTINO", (66, H - 70), DIM)
        put(surf, F["big"], txt, (66, H - 56), GREEN)
        put(surf, F["btn"], f"rumbo {brg:.0f}°", (W - 8, H - 52), ORANGE, anchor="topright")
    src = D.get("src")
    put(surf, F["small"], f"datos: {src}" if src else''')
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.32 · 29/10/2026 02:20"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
