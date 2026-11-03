import shutil
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak10")
s = open(p, encoding="utf-8").read()
if "def view_mats" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- 12.5 materiales / 12.6 portanaves / 12.7 mercado ----------
def pager(key, n, per):
    pages = max(1, (n + per - 1) // per)
    pg = ui.get(key, 0) % pages
    if pages > 1:
        put(surf_ref[0], F["small"], f"pág {pg + 1}/{pages}  (toca para pasar)", (W // 2, H - 9), DIM, anchor="center")
    return pg
surf_ref = [None]

def view_mats(surf, d, flags, now):
    surf_ref[0] = surf
    M = (d or {}).get("mats") or {}
    rows = M.get("list") or []
    y = TOP + 4
    put(surf, F["small"], f"{M.get('n', 0)} materiales", (8, y), DIM)
    put(surf, F["small"], f"AL MÁXIMO: {M.get('full', 0)}", (W - 8, y), RED if M.get("full") else DIM, anchor="topright")
    y += 16
    if not rows:
        put(surf, F["btn"], "Sin datos (carga la partida)", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    per = 10
    pg = pager("page125", len(rows), per)
    for name, c, mx in rows[pg * per:(pg + 1) * per]:
        pct = c / mx
        col = RED if c >= mx else ORANGE if pct >= 0.9 else DIM
        put(surf, F["small"], name, (8, y + 3), ORANGE, 200)
        bx = pygame.Rect(214, y + 3, 186, 12)
        pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, RED if c >= mx else BLUE, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(1, pct)), bx.h - 4))
        put(surf, F["small"], f"{c}/{mx}", (W - 8, y + 3), col if c >= 0.9 * mx else WHITE, anchor="topright")
        y += 22

def view_carrier(surf, d, flags, now):
    c = (d or {}).get("carrier") or {}
    if not (c.get("name") or c.get("callsign")):
        put(surf, F["btn"], "Sin datos del portanaves", (W // 2, (H + TOP) // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], "abre su gestión en el juego una vez", (W // 2, (H + TOP) // 2 + 12), DIM, anchor="center")
        return
    y = TOP + 6
    put(surf, F["big"], (c.get("name") or "").upper(), (8, y), ORANGE, W - 140)
    put(surf, F["btn"], c.get("callsign") or "", (W - 8, y + 2), DIM, anchor="topright"); y += 30
    put(surf, F["small"], "SISTEMA", (8, y + 4), DIM)
    put(surf, F["btn"], c.get("system") or "?", (80, y + 1), ORANGE, W - 90); y += 28
    fuel = c.get("fuel")
    put(surf, F["small"], "TRITIO", (8, y + 1), DIM)
    bx = pygame.Rect(80, y, W - 170, 16)
    pygame.draw.rect(surf, DIM, bx, 1)
    if fuel is not None:
        pygame.draw.rect(surf, RED if fuel < 135 else GREEN, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(1, fuel / 1000)), bx.h - 4))
    put(surf, F["btn"], f"{fuel} t" if fuel is not None else "?", (W - 8, y - 2), RED if fuel is not None and fuel < 135 else ORANGE, anchor="topright")
    y += 28
    put(surf, F["small"], "SALDO", (8, y + 4), DIM)
    put(surf, F["big"], f"{cr(c.get('balance'))} cr", (80, y), ORANGE); y += 34
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 8
    dest, dep = c.get("dest"), c.get("depart")
    if dest and dep:
        left = dep - time.time()
        put(surf, F["small"], "SALTO PROGRAMADO A", (8, y), DIM)
        put(surf, F["big"], dest.upper(), (8, y + 14), BLUE, W - 16); y += 46
        if left > 0:
            put(surf, F["num"], f"{int(left) // 60:02d}:{int(left) % 60:02d}", (W // 2, y), ORANGE if left > 60 else RED, anchor="midtop")
        else:
            put(surf, F["big"], "SALTANDO...", (W // 2, y + 8), BLUE if int(now * 2) % 2 else WHITE, anchor="midtop")
    else:
        put(surf, F["btn"], "Sin salto programado", (W // 2, y + 30), DIM, anchor="center")

def view_market(surf, d, flags, now):
    surf_ref[0] = surf
    m = (d or {}).get("market") or {}
    if not m.get("station"):
        put(surf, F["btn"], "Abre el mercado en una estación", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    y = TOP + 4
    age = int((time.time() - (m.get("t") or time.time())) / 60)
    put(surf, F["btn"], m["station"].upper(), (8, y), ORANGE, W - 120)
    put(surf, F["small"], f"hace {age} min" if age else "ahora", (W - 8, y + 4), DIM, anchor="topright"); y += 22
    sell = m.get("sell") or []
    rows = sell if sell else m.get("best") or []
    put(surf, F["small"], "TU BODEGA AQUÍ" if sell else "BODEGA VACÍA · LO MEJOR PAGADO AQUÍ (vs media)", (8, y), DIM)
    if sell:
        put(surf, F["small"], "TOTAL", (W - 8, y), DIM, anchor="topright")
    y += 16
    per = 7 if sell else 9
    pg = pager("page127", len(rows), per)
    for r in rows[pg * per:(pg + 1) * per]:
        if sell:
            name, n, price, mean, dem = r
        else:
            name, price, mean = r; n = None
        diff = (price - mean) / mean * 100 if mean else 0
        put(surf, F["small"], name, (8, y + 3), ORANGE, 170)
        if n is not None:
            put(surf, F["small"], f"{n} t", (200, y + 3), WHITE, anchor="topright")
        put(surf, F["small"], f"{price:,} cr".replace(",", "."), (300, y + 3), WHITE, anchor="topright")
        put(surf, F["small"], f"{diff:+.0f}%", (350, y + 3), GREEN if diff >= 0 else RED, anchor="topright")
        if n is not None:
            put(surf, F["btn"], cr(n * price), (W - 8, y), GREEN if diff >= 0 else ORANGE, anchor="topright")
        y += 22
    if sell:
        tot = sum(r[1] * r[2] for r in sell)
        pygame.draw.line(surf, DIM, (8, H - 40), (W - 8, H - 40))
        put(surf, F["btn"], f"VENDIENDO TODO: {cr(tot)} cr", (8, H - 36), GREEN)

'''
rep("def view_sub12", SNIP + "def view_sub12")
rep('[("1", "LOG"), ("2", "STREAM"), ("3", "RANGOS"), ("4", "AJUSTES")]):\n        draw_button(surf, grid(i, 2, 2)',
    '[("1", "LOG"), ("2", "STREAM"), ("3", "RANGOS"), ("4", "AJUSTES"), ("5", "MATERIAL"), ("6", "PORTANAV."), ("7", "MERCADO")]):\n        draw_button(surf, grid(i, 4, 2)')
rep('100: "EN VIVO"}', '100: "EN VIVO", 125: "MATERIALES", 126: "PORTANAVES", 127: "MERCADO"}')
rep("123: 12, 124: 12}", "123: 12, 124: 12, 125: 12, 126: 12, 127: 12}")
rep("123: view_ranks, 124: view_settings}", "123: view_ranks, 124: view_settings, 125: view_mats, 126: view_carrier, 127: view_market}")
rep('AUTO_VIEW = {"embark": 100,', 'AUTO_VIEW = {"embark": 100, "market": 127,')
rep('        elif kind == "gravity" and len(p) >= 2:',
'''        elif kind == "matfull" and len(p) >= 2:
            xa["a"] = dict(until=now + 5, col=ORANGE, title="MATERIAL AL MÁXIMO", big=p[0],
                           lines=[f"{p[1]} / {p[1]}", "lo que recojas de más se pierde"])
        elif kind == "gravity" and len(p) >= 2:''')
L = s.split("\n")
try:
    j = next(i for i, l in enumerate(L) if 'ui["view"] = 121 + i' in l)
    k = j
    while "v == 12" not in L[k]:
        k -= 1
    for i in range(k, j + 1):
        L[i] = L[i].replace("grid(i, 2, 2)", "grid(i, 4, 2)").replace("range(4)", "range(7)")
    print("toque del 12:"); print("\n".join(L[k:j + 1]))
    t = next(i for i, l in enumerate(L) if l.strip() == "elif v == 71:")
    ind = L[t][:len(L[t]) - len(L[t].lstrip())]
    L[t:t] = [ind + "elif v in (125, 127):", ind + "    ui[f'page{v}'] = ui.get(f'page{v}', 0) + 1; return"]
except StopIteration:
    print("NO ENCONTRADO: bloque de toque"); ok = False
s = "\n".join(L)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
