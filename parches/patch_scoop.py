import shutil
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak2")
s = open(p, encoding="utf-8").read()
SNIP = r'''
# ---------- recogida de combustible ----------
scoop = {"hist": [], "was": False, "full_until": 0}

def fnum(v, nd=1):
    return f"{v:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def dur_s(sec):
    sec = max(0, int(sec))
    return f"{sec // 60}m {sec % 60:02d}s" if sec >= 60 else f"{sec} s"

def draw_scoop(surf, d, flags, now):
    fuel = ((d or {}).get("Fuel") or {}).get("FuelMain")
    cap = (d or {}).get("fuelcap")
    on, hot = bool(flags & (1 << 11)), bool(flags & (1 << 20))
    if on and fuel is not None:
        h = scoop["hist"]; h.append((now, fuel))
        while now - h[0][0] > 6: h.pop(0)
    else:
        if scoop["was"] and fuel is not None and cap and fuel >= cap - 0.05:
            scoop["full_until"] = now + 4
        scoop["hist"] = []
    scoop["was"] = on
    full = now < scoop["full_until"]
    if not on and not full:
        return
    blink = int(now * 3) % 2 == 0
    col = GREEN if full and not on else (RED if hot and blink else ORANGE)
    for k in range(4):
        pygame.draw.rect(surf, col, (k * 3, k * 3, W - k * 6, H - k * 6), 2)
    box = pygame.Rect(24, 58, W - 48, 214)
    pygame.draw.rect(surf, BLACK, box)
    for j in range(12):
        yy = box.y + 10 + (j * 19) % (box.h - 20)
        ln = (j * 41 + int(now * 120)) % 90
        pygame.draw.line(surf, (90, 45, 0), (box.x + 8, yy), (box.x + 8 + ln, yy))
        pygame.draw.line(surf, (90, 45, 0), (box.right - 8 - ln, yy), (box.right - 8, yy))
    pygame.draw.rect(surf, col, box, 3, border_radius=8)
    cx, y = box.centerx, box.y + 14
    if full and not on:
        put(surf, F["num"], "DEPÓSITO LLENO", (cx, box.centery - 14), GREEN, box.w - 20, anchor="center")
        if fuel is not None:
            put(surf, F["btn"], f"{fnum(fuel)} t", (cx, box.centery + 26), WHITE, anchor="center")
        return
    put(surf, F["big"], "RECOGIENDO COMBUSTIBLE", (cx, y), ORANGE, box.w - 20, anchor="midtop"); y += 34
    if fuel is not None:
        put(surf, F["num"], f"{fnum(fuel)} / {fnum(cap) if cap else '?'} t", (cx, y), WHITE, box.w - 20, anchor="midtop"); y += 46
        bx = pygame.Rect(box.x + 20, y, box.w - 40, 18)
        pygame.draw.rect(surf, DIM, bx, 1)
        if cap:
            pct = max(0.0, min(1.0, fuel / cap))
            pygame.draw.rect(surf, ORANGE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * pct), bx.h - 4))
            put(surf, F["small"], f"{pct * 100:.0f}%", (bx.centerx, bx.y + 3), WHITE, anchor="midtop")
        y += 28
    h = scoop["hist"]
    if len(h) >= 2 and h[-1][0] - h[0][0] > 1:
        rate = (h[-1][1] - h[0][1]) / (h[-1][0] - h[0][0])
        put(surf, F["btn"], f"{fnum(rate, 2)} t/s", (box.x + 20, y), ORANGE)
        if rate > 0.001 and cap and fuel is not None:
            put(surf, F["btn"], f"lleno en {dur_s((cap - fuel) / rate)}", (box.right - 20, y), ORANGE, anchor="topright")
    y += 26
    if hot:
        put(surf, F["big"], "¡SOBRECALENTAMIENTO!", (cx, y), RED if blink else WHITE, box.w - 20, anchor="midtop")
    else:
        put(surf, F["small"], "temperatura OK", (cx, y + 6), GREEN, anchor="midtop")

'''
if "def draw_scoop" not in s:
    s = s.replace("def render(surf):", SNIP.lstrip("\n") + "def render(surf):", 1)
    old = '    if ui["alert"]:\n        if now < ui["alert"]["until"]:'
    if old in s:
        s = s.replace(old, '    draw_scoop(surf, d if online else None, flags, now)\n' + old, 1)
        print("OK")
    else:
        print("NO ENCONTRADO el sitio de la llamada")
open(p, "w", encoding="utf-8").write(s)
