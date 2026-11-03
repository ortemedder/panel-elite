import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak51")
s = open(p, encoding="utf-8").read()
if "def view_alien" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
a2 = '        elif kind == "gravity" and len(p) >= 2:'
rep(a2, r'''        elif kind == "alien" and len(p) >= 3:
            tgk = p[0] == "THARGOIDES"
            xa["a"] = dict(until=now + 6, col=(120, 230, 120) if tgk else (90, 200, 255), title=f"SEÑALES {p[0]}",
                           big=f"{p[1]} EN EL PLANETA", lines=[p[2], "míralas en 7.6 ALIENÍGENAS" if not tgk else "cuidado: posible actividad thargoide"])
        elif kind == "tgwar" and len(p) >= 4:
            pr = float(p[1] or 0)
            xa["a"] = dict(until=now + 6, col=RED if p[0] in ("INVASIÓN", "CONTROLADO", "BASTIÓN") else ORANGE,
                           title="GUERRA THARGOIDE", big=p[0], lines=[f"progreso {pr * 100:.0f}%" + (f" · puertos {p[2]}" if p[2] else ""), p[3]])
''' + a2)
rep("def view_sub12", r'''# ---------- 7.6 alienigenas: thargoides y guardianes (toca para cambiar) ----------
TGCOL = (120, 230, 120)

def view_alien(surf, d, flags, now):
    A = (d or {}).get("alien") or {}
    tab = ui.get("alientab", 0)
    for i, t in enumerate(("THARGOIDES", "GUARDIANES")):
        r = pygame.Rect(4 + i * (W // 2), TOP + 2, W // 2 - 8, 26)
        on = tab == i
        pygame.draw.rect(surf, (TGCOL if i == 0 else BLUE) if on else DIM, r, 0 if on else 1, border_radius=4)
        put(surf, F["btn"], t, r.center, BLACK if on else DIM, anchor="center")
    y = TOP + 36
    if tab == 0:
        w = A.get("tgwar")
        if w:
            put(surf, F["small"], "GUERRA EN EL SISTEMA", (8, y + 4), DIM)
            put(surf, F["big"], w["state"], (180, y), RED if w["state"] in ("INVASIÓN", "CONTROLADO", "BASTIÓN") else ORANGE)
            y += 28
            pr = w.get("progress")
            if pr is not None:
                bx = pygame.Rect(8, y, W - 90, 14)
                pygame.draw.rect(surf, DIM, bx, 1)
                pygame.draw.rect(surf, TGCOL, (bx.x + 2, bx.y + 2, int((bx.w - 4) * max(0, min(1, pr))), bx.h - 4))
                put(surf, F["btn"], f"{pr * 100:.0f}%", (W - 8, y - 4), WHITE, anchor="topright"); y += 20
            extra = " · ".join(x for x in (f"puertos restantes {w['ports']}" if w.get("ports") else "", str(w.get("time") or "")) if x)
            if extra:
                put(surf, F["small"], extra, (8, y), DIM, W - 16); y += 18
        else:
            put(surf, F["btn"], "Sistema sin guerra thargoide", (8, y), GREEN); y += 26
        put(surf, F["small"], "DERRIBOS THARGOIDES (sesión)", (8, y + 4), DIM)
        put(surf, F["btn"], f"{A.get('tgk', 0)}  ·  {cr(A.get('tgb', 0))} cr", (W - 8, y), TGCOL, anchor="topright"); y += 26
        rows = A.get("tg") or []
        title, col = "MATERIALES THARGOIDES", TGCOL
    else:
        bp = A.get("bp") or {}
        put(surf, F["small"], "PLANOS GUARDIANES", (8, y), DIM); y += 16
        for k, (lab, key) in enumerate((("MÓDULO", "module"), ("ARMA", "weapon"), ("NAVE", "vessel"))):
            x0 = 8 + k * (W // 3)
            put(surf, F["small"], lab, (x0, y + 6), DIM)
            put(surf, F["big"], str(bp.get(key, 0)), (x0 + W // 3 - 30, y), BLUE, anchor="topright")
        y += 32
        rows = A.get("gd") or []
        title, col = "MATERIALES Y DATOS GUARDIANES", BLUE
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
    put(surf, F["small"], title, (8, y), DIM); y += 16
    if not rows:
        put(surf, F["small"], "ninguno", (8, y), DIM)
    for k, (n, c) in enumerate(rows):
        cx, cy = (8 if k % 2 == 0 else W // 2 + 4), y + (k // 2) * 18
        if cy > H - 18:
            break
        put(surf, F["small"], n, (cx, cy), WHITE, W // 2 - 50)
        put(surf, F["small"], str(c), (cx + W // 2 - 14, cy), col, anchor="topright")

''' + "def view_sub12")
rep('("5", "DIARIO")]', '("5", "DIARIO"), ("6", "ALIEN")]')
rep('75: "DIARIO DE EXPLORACIÓN"', '75: "DIARIO DE EXPLORACIÓN", 76: "ALIENÍGENAS"')
rep("75: 7,", "75: 7, 76: 7,")
rep("75: view_diary,", "75: view_diary, 76: view_alien,")
s, n = re.subn(r'(for i in range\()5(\):\n\s+if grid\(i, 3, 2\)\.collidepoint\(x, y\):\n\s+tap_flash\(\(7, i\)\))', r'\g<1>6\g<2>', s, count=1)
if not n: print("NO ENCONTRADO: toque del 7"); ok = False
L = s.split("\n")
t = next((i for i, l in enumerate(L) if l.strip() == "elif v == 71:"), None)
if t is None:
    print("NO ENCONTRADO: toque"); ok = False
else:
    ind = L[t][:len(L[t]) - len(L[t].lstrip())]
    L[t:t] = [ind + "elif v == 76:", ind + "    ui['alientab'] = 1 - ui.get('alientab', 0); return"]
s = "\n".join(L)
rep("\n]\n\ndef view_changelog", '\n    ("0.51", "7.6 Alienígenas: thargoides y guardianes, señales y guerra"),\n]\n\ndef view_changelog')
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.51 · 29/10/2026 15:10"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
