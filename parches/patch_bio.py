import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak")
s = open(p, encoding="utf-8").read()

def rep(old, new):
    global s
    if old not in s: print("NO ENCONTRADO:", old); return
    s = s.replace(old, new, 1)

rep('71: "EXPLORACIÓN", 72: "SISTEMA"}', '71: "EXPLORACIÓN", 72: "SISTEMA", 73: "XENOBIOLOGÍA"}')
rep('PARENT = {71: 7, 72: 7,', 'PARENT = {71: 7, 72: 7, 73: 7,')
rep('72: view_orrery,', '72: view_orrery, 73: view_bio,')
rep('[("1", "EXPLORACIÓN"), ("2", "SISTEMA")]', '[("1", "EXPLORACIÓN"), ("2", "SISTEMA"), ("3", "XENOBIO")]')

# 3 botones en el submenu 7 (dibujo y toque)
L = s.split("\n")
for i, l in enumerate(L):
    if "def view_sub7" in l:
        for j in range(i, i + 4):
            L[j] = L[j].replace("grid(i, 2, 1)", "grid(i, 3, 1)")
for j in range(318, 331):
    if "71 + i" in L[j] or "grid(i, 2, 1)" in L[j] or "range(2)" in L[j]:
        L[j] = L[j].replace("grid(i, 2, 1)", "grid(i, 3, 1)").replace("range(2)", "range(3)")
s = "\n".join(L)

BIO = r'''
# ---------- 7.3 xenobiologia ----------
def hav(a, b, R):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(min(1, h)))

def view_bio(surf, d, flags, now):
    b = (d or {}).get("bio") or {}
    y = TOP + 6
    put(surf, F["small"], "CUERPO", (8, y), DIM)
    sig = b.get("signals")
    put(surf, F["small"], f"SEÑALES BIO: {sig if sig is not None else '?'}", (W - 8, y), DIM, anchor="topright"); y += 14
    put(surf, F["btn"], b.get("body") or "No estás en un planeta", (8, y), ORANGE if b.get("body") else DIM, W - 16); y += 22
    done = set(b.get("done") or [])
    gx = 8
    for g in b.get("genuses") or []:
        t = ("OK " if g in done else "") + g
        w_ = F["small"].size(t)[0] + 10
        if gx + w_ > W - 4: break
        pygame.draw.rect(surf, GREEN if g in done else DIM, (gx, y, w_ - 4, 16), 1, border_radius=3)
        put(surf, F["small"], t, (gx + 3, y + 2), GREEN if g in done else ORANGE)
        gx += w_
    y += 22
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 6
    if not b.get("species"):
        put(surf, F["btn"], "Sin muestreo en curso", (W // 2, y + 50), DIM, anchor="center")
    else:
        step = b.get("step", 0)
        put(surf, F["big"], b["species"].upper(), (8, y), GREEN if step >= 3 else ORANGE, W - 90)
        for k in range(3):
            pygame.draw.circle(surf, ORANGE, (W - 70 + k * 22, y + 12), 8, 0 if k < step else 1)
        y += 26
        put(surf, F["small"], b.get("variant") or "", (8, y), DIM, W - 16); y += 20
        pts, R = b.get("pts") or [], b.get("R")
        lat, lon, rng = b.get("lat"), b.get("lon"), b.get("range", 100)
        if step >= 3:
            put(surf, F["big"], "MUESTRA COMPLETA", (W // 2, y + 22), GREEN, anchor="center")
        elif pts and R and lat is not None:
            dist = min(hav(p, (lat, lon), R) for p in pts)
            ok = dist >= rng
            put(surf, F["num"], f"{dist:,.0f} m".replace(",", "."), (8, y), GREEN if ok else RED)
            put(surf, F["btn"], f"mín. {rng} m", (W - 8, y + 4), DIM, anchor="topright")
            put(surf, F["small"], "PUEDES MUESTREAR" if ok else "ALÉJATE", (W - 8, y + 26), GREEN if ok else RED, anchor="topright")
            bx = pygame.Rect(8, y + 44, W - 16, 12)
            pygame.draw.rect(surf, DIM, bx, 1)
            pygame.draw.rect(surf, GREEN if ok else RED, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(1, dist / rng)), bx.h - 4))
        else:
            put(surf, F["btn"], f"Distancia mínima del género: {rng} m", (8, y + 10), DIM)
    pygame.draw.line(surf, DIM, (8, H - 24), (W - 8, H - 24))
    put(surf, F["btn"], f"MUESTRAS SIN VENDER: {b.get('unsold', 0)}", (8, H - 20), ORANGE)

'''
if "def view_bio" not in s:
    rep("def view_sub12", BIO.lstrip("\n") + "def view_sub12")
open(p, "w", encoding="utf-8").write(s)
print("OK")
