import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak46")
s = open(p, encoding="utf-8").read()
if "def draw_borders" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new, need=True):
    global s, ok
    if old not in s:
        if need:
            print("NO ENCONTRADO:", old.strip()[:70]); ok = False
        return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- bordes de situacion (rojo, naranja, marron, azul) ----------
BROWN = (150, 90, 40)
BORDERS_FILE = "/home/ortem/bordes.txt"
try:
    style["borders"] = open(BORDERS_FILE).read().strip() != "no"
except OSError:
    style["borders"] = True

def borders_toggle():
    style["borders"] = not style["borders"]
    try:
        with open(BORDERS_FILE, "w") as f:
            f.write("si" if style["borders"] else "no")
    except OSError:
        pass

def border_cols(d):
    flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    L = d.get("live") or {}
    hull = (L.get("ship") or {}).get("hull")
    sec = ((d.get("sysinfo") or {}).get("sec") or "").lower()
    out = []
    if L.get("legal") in ("Wanted", "Hostile", "Warrant") or (hull is not None and hull < 0.3 and not f2 & 1):
        out.append(RED)
    if "anarqu" in sec or "lawless" in sec or "sin ley" in sec:
        out.append(ORANGE)
    if f2 & (1 << 4) or flags & (1 << 26):
        out.append(BROWN)
    if flags & 1:
        out.append(BLUE)
    return out[:3]

def draw_borders(surf):
    if not style.get("borders", True):
        return
    now = time.time()
    with lock:
        d, rx = state["data"], state["rx"]
    if not d or now - rx > 5 or now - ui["start"] < 3 or ui.get("idle_on"):
        return
    w, h = surf.get_size()
    th = 2 if w < 600 else 3
    for k, col in enumerate(border_cols(d)):
        o = k * (th + 1)
        _orig_rect(surf, col, (o, o, w - 2 * o, h - 2 * o), th)

'''
rep("def render(surf):", SNIP + "def render(surf):")
rep('''            tint = RED if danger else BLUE if flags & 1 else None
            if tint:
                surf.blit(_cached(("tint", tuple(tint[:3])), lambda: _tint(tint)), (0, 0))
                _orig_rect(surf, tint, (0, 0, W, H), 2)''', '''            cols = border_cols(d)
            if cols:
                surf.blit(_cached(("tint", tuple(cols[0][:3])), lambda: _tint(cols[0])), (0, 0))''')
rep('''        tint = RED if danger else BLUE if flags & 1 else None
        if tint:
            S.blit(_cached(("btint", tuple(tint[:3]), w, h), lambda: _btint(w, h, tint)), (0, 0))
            _orig_rect(S, tint, (0, 0, w, h), 3)''', '''        cols = border_cols(d)
        if cols:
            S.blit(_cached(("btint", tuple(cols[0][:3]), w, h), lambda: _btint(w, h, cols[0])), (0, 0))''', need=False)
rep("            decorate(surf)\n", "            decorate(surf)\n            draw_borders(surf)\n")
if 'decorate_big(BIG["surf"])\n' in s:
    rep('        decorate_big(BIG["surf"])\n', '        decorate_big(BIG["surf"])\n        draw_borders(BIG["surf"])\n')
else:
    rep("        render_big()\n", '        render_big()\n        draw_borders(BIG["surf"])\n')
rep('("5", "VERSIONES")]', '("5", "VERSIONES"), ("6", "BORDES")]')
rep('"¿SEGURO?" if sure else name,', '''"¿SEGURO?" if sure else (f"BORDES {'SÍ' if style.get('borders', True) else 'NO'}" if i == 5 else name),''')
rep('''    if i == 4:
        ui["view"] = 1245; return''', '''    if i == 4:
        ui["view"] = 1245; return
    if i == 5:
        borders_toggle(); return''')
s, n = re.subn(r'(for i in range\()5(\):\n\s+if grid\(i, 3, 2\)\.collidepoint\(x, y\):\n\s+power_tap\(i\); return)', r'\g<1>6\g<2>', s, count=1)
if not n: print("NO ENCONTRADO: toque del 12.4"); ok = False
rep("\n]\n\ndef view_changelog", '\n    ("0.46", "Bordes de situación por riesgo y botón BORDES"),\n]\n\ndef view_changelog')
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.46 · 29/10/2026 13:40"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
