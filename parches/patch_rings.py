import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak17")
s = open(p, encoding="utf-8").read()
if "def view_rings" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- 7.4 yacimientos: zonas de mineria del planeta (Rhino) y anillos ----------
RES_COL = {"PRÍSTINAS": GREEN, "MAYORES": GREEN, "COMUNES": ORANGE, "BAJAS": RED, "AGOTADAS": RED}

def view_rings(surf, d, flags, now):
    R = (d or {}).get("rings") or {}
    if not R.get("planet"):
        put(surf, F["btn"], "Acércate a un planeta", (W // 2, (H + TOP) // 2), DIM, anchor="center"); return
    y = TOP + 4
    put(surf, F["big"], R["planet"].upper(), (8, y), ORANGE, W - 150)
    if R.get("reserve"):
        put(surf, F["small"], "RESERVAS", (W - 8, y), DIM, anchor="topright")
        put(surf, F["btn"], R["reserve"], (W - 8, y + 12), RES_COL.get(R["reserve"], ORANGE), anchor="topright")
    y += 34
    sig = R.get("signals") or []
    put(surf, F["small"], "SEÑALES DEL PLANETA", (8, y), DIM); y += 15
    if not sig:
        put(surf, F["small"], "sin datos: escanea el planeta (FSS) o mapéalo con la sonda (DSS)", (8, y), DIM, W - 16); y += 20
    else:
        x = 8
        for name, c in sig:
            low = name.lower()
            col = GREEN if ("bio" in low) else BLUE if ("geo" in low) else ORANGE
            txt = f"{name} x{c}"
            w_ = F["btn"].size(txt)[0] + 14
            if x + w_ > W - 6:
                x = 8; y += 24
            pygame.draw.rect(surf, col, (x, y, w_ - 4, 21), 1, border_radius=4)
            put(surf, F["btn"], txt, (x + 5, y + 2), col)
            x += w_
        y += 28
    rings = R.get("rings") or []
    if not rings:
        return
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
    here = R.get("here") or ""
    for name, cls, hs in rings:
        if y > H - 40:
            break
        inside = bool(here) and here.endswith(name)
        r = pygame.Rect(6, y, W - 12, 26 + 20 * max(1, (len(hs or []) + 1) // 2))
        pygame.draw.rect(surf, GREEN if inside else DIM, r, 1, border_radius=5)
        put(surf, F["btn"], name.upper(), (r.x + 8, r.y + 4), ORANGE, 110)
        put(surf, F["small"], cls, (r.x + 120, r.y + 8), BLUE, 160)
        if inside:
            put(surf, F["small"], "ESTÁS AQUÍ", (r.right - 8, r.y + 8), GREEN, anchor="topright")
        yy = r.y + 26
        if not hs:
            put(surf, F["small"], "sin sondear: usa la sonda de superficie en el anillo", (r.x + 8, yy + 2), DIM, r.w - 16)
        else:
            for k, (m, c) in enumerate(hs):
                put(surf, F["btn"], f"{m}  x{c}", (r.x + 8 + (k % 2) * (r.w // 2), yy + (k // 2) * 20),
                    GREEN if c >= 2 else WHITE, r.w // 2 - 12)
        y = r.bottom + 6

'''
rep("def view_sub12", SNIP + "def view_sub12")
rep('("3", "XENOBIO")]):\n        draw_button(surf, grid(i, 3, 1)', '("3", "XENOBIO"), ("4", "YACIM.")]):\n        draw_button(surf, grid(i, 4, 1)')
rep('73: "XENOBIOLOGÍA"', '73: "XENOBIOLOGÍA", 74: "YACIMIENTOS"')
rep("PARENT = {0: 100, 71: 7, 72: 7, 73: 7,", "PARENT = {0: 100, 71: 7, 72: 7, 73: 7, 74: 7,")
rep("73: view_bio,", "73: view_bio, 74: view_rings,")
s, n = re.subn(r'BIG_SETS = \{.*?\}\n', '''BIG_SETS = {"VIAJE": [100, 3, 71, 72], "APROXIMACIÓN": [100, 72, 73, 74], "SUPERFICIE": [100, 73, 5, 128],
            "ATRACADO": [100, 8, 127, 4], "COMBATE": [100, 6, 9, 2]}
''', s, count=1, flags=re.S)
if not n: print("NO ENCONTRADO: BIG_SETS"); ok = False
s, n = re.subn(r'def big_mode\(d, flags\):.*?return "VIAJE"\n', '''def big_mode(d, flags):
    f2 = d.get("Flags2", 0)
    if flags & 1:
        return "ATRACADO"
    if f2 & 1 or flags & ((1 << 26) | 2):
        return "SUPERFICIE"
    if (d.get("body") or "").endswith(" Ring"):
        return "APROXIMACIÓN"
    if d.get("target") or flags & 64:
        return "COMBATE"
    if flags & (1 << 21):
        return "APROXIMACIÓN"
    return "VIAJE"
''', s, count=1, flags=re.S)
if not n: print("NO ENCONTRADO: big_mode"); ok = False
rep("    for i, v in enumerate(BIG_SETS[mode]):", '''    cells = list(BIG_SETS[mode])
    if 74 in cells and not ((d.get("rings") or {}).get("rings") or (d.get("rings") or {}).get("signals")):
        cells[cells.index(74)] = 128
    for i, v in enumerate(cells):''')
rep('put(S, fsm, mode, (bw // 2 - 60, 14), GREEN, 140, anchor="midtop")', 'put(S, fsm, mode, (bw // 2 - 80, 14), GREEN, 190, anchor="midtop")')
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.17 · 28/10/2026 23:46"', s, count=1)
if not n: print("NO ENCONTRADO: PANEL_VER"); ok = False
L = s.split("\n")
try:
    j = next(i for i, l in enumerate(L) if 'ui["view"] = 71 + i' in l)
    k = j
    while "v == 7" not in L[k]:
        k -= 1
    for i in range(k, j + 1):
        L[i] = L[i].replace("grid(i, 3, 1)", "grid(i, 4, 1)").replace("range(3)", "range(4)")
    print("toque del 7:"); print("\n".join(L[k:j + 1]))
except StopIteration:
    print("NO ENCONTRADO: toque del 7"); ok = False
s = "\n".join(L)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
