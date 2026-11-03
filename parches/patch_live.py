import shutil
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak4")
s = open(p, encoding="utf-8").read()
if "def view_live" in s:
    print("ya estaba"); raise SystemExit
SNIP = r'''
# ---------- 11 submenu / 11.2 en vivo ----------
def view_sub11(surf, d, flags, now):
    for i, (n, name) in enumerate([("1", "SESIÓN"), ("2", "EN VIVO")]):
        draw_button(surf, grid(i, 2, 1), n, name, F["num"], lit=flash.get((11, i), 0) > now)

def chips(surf, items, y, cols=4):
    cw = (W - 16) // cols
    for k, (txt, on, col) in enumerate(items):
        r = pygame.Rect(8 + (k % cols) * cw, y + (k // cols) * 24, cw - 4, 20)
        if on:
            pygame.draw.rect(surf, col, r, border_radius=4)
            put(surf, F["small"], txt, r.center, BLACK, cw - 8, anchor="center")
        else:
            pygame.draw.rect(surf, DIM, r, 1, border_radius=4)
            put(surf, F["small"], txt, r.center, DIM, cw - 8, anchor="center")
    return y + ((len(items) + cols - 1) // cols) * 24

LEGAL = {"Clean": ("LIMPIO", None), "IllegalCargo": ("CARGA ILEGAL", "r"), "Speeding": ("EXCESO VELOCIDAD", "r"),
         "Wanted": ("BUSCADO", "r"), "Hostile": ("HOSTIL", "r"), "PassengerWanted": ("PASAJERO BUSCADO", "r"),
         "Warrant": ("ORDEN DE ARRESTO", "r"), "Allied": ("ALIADO", None), "Thargoid": ("THARGOIDE", "r")}

def pctv(v):
    return None if v is None else v * 100

def view_live(surf, d, flags, now):
    d = d or {}
    L, f2 = d.get("live") or {}, d.get("Flags2", 0)
    if f2 & 1:
        mode = "A PIE"
    elif flags & (1 << 26):
        mode = "SRV"
    elif flags & (1 << 25):
        mode = "CAZA"
    else:
        mode = "NAVE"
    y = TOP + 4
    put(surf, F["big"], mode, (8, y), GREEN)
    if mode == "A PIE":
        s_ = L.get("suit") or {}
        put(surf, F["small"], " · ".join(x for x in (s_.get("name"), s_.get("loadout")) if x), (W - 8, y + 6), ORANGE, 300, anchor="topright")
        y += 30
        oxy, hp = pctv(L.get("oxy")), pctv(L.get("health"))
        half = (W - 24) // 2
        bar(surf, 8, y, half, "OXÍGENO", oxy, RED if oxy is not None and oxy < 25 else BLUE)
        bar(surf, 16 + half, y, half, "SALUD", hp, RED if hp is not None and hp < 25 else GREEN)
        y += 22
        t = L.get("temp")
        tcol = RED if f2 & ((1 << 9) | (1 << 11)) else BLUE if f2 & ((1 << 8) | (1 << 10)) else ORANGE
        put(surf, F["small"], "TEMPERATURA", (8, y + 4), DIM)
        put(surf, F["big"], f"{t - 273.15:.0f} °C" if t is not None else "?", (100, y), tcol)
        g = L.get("grav")
        put(surf, F["small"], "GRAVEDAD", (250, y + 4), DIM)
        put(surf, F["big"], f"{g:.2f} G".replace(".", ",") if g is not None else "-", (W - 8, y),
            RED if g and g > 2 else ORANGE, anchor="topright")
        y += 26
        put(surf, F["small"], "ARMA", (8, y + 4), DIM)
        put(surf, F["btn"], L.get("weapon") or "-", (60, y + 1), ORANGE, W - 70); y += 24
        y = chips(surf, [("ESTACIÓN", f2 & (1 << 3), BLUE), ("PLANETA", f2 & (1 << 4), BLUE),
                         ("RESPIRABLE", f2 & (1 << 16), GREEN), ("POCO O2", f2 & (1 << 6), RED),
                         ("SALUD BAJA", f2 & (1 << 7), RED), ("FRÍO", f2 & ((1 << 8) | (1 << 10)), BLUE),
                         ("CALOR", f2 & ((1 << 9) | (1 << 11)), RED), ("PLANEO", f2 & (1 << 12), ORANGE)], y)
        draw_compass(surf, d, d.get("bio") or {})
    elif mode == "SRV":
        put(surf, F["small"], d.get("body") or "", (W - 8, y + 6), ORANGE, 300, anchor="topright")
        y += 34
        y = chips(surf, [("FRENO MANO", flags & (1 << 12), RED), ("TORRETA", flags & (1 << 13), ORANGE),
                         ("TORR. RECOGIDA", flags & (1 << 14), DIM), ("ASIST. CONDUC.", flags & (1 << 15), GREEN),
                         ("LUCES", flags & (1 << 8), ORANGE), ("LUCES LARGAS", flags & (1 << 31), ORANGE),
                         ("CARGA", flags & (1 << 9), ORANGE), ("SOBRECALENT.", flags & (1 << 20), RED)], y)
        draw_compass(surf, d, d.get("bio") or {})
    else:
        sh = L.get("ship") or {}
        nm = " · ".join(x for x in (sh.get("name"), sh.get("ident")) if x)
        put(surf, F["small"], (sh.get("ship") or "").upper(), (W - 8, y + 2), ORANGE, 300, anchor="topright")
        put(surf, F["small"], nm, (W - 8, y + 16), DIM, 300, anchor="topright")
        y += 32
        hull = pctv(sh.get("hull"))
        half = (W - 24) // 2
        bar(surf, 8, y, half, "CASCO", hull, RED if hull is not None and hull < 30 else ORANGE)
        cg, cap = L.get("cargo"), d.get("cargocap")
        put(surf, F["small"], "CARGA", (16 + half, y + 1), DIM)
        put(surf, F["btn"], f"{cg:.0f} / {cap if cap is not None else '?'} t" if cg is not None else "-",
            (W - 8, y - 2), ORANGE, anchor="topright")
        y += 22
        lg, kind = LEGAL.get(L.get("legal"), (L.get("legal") or "-", None))
        put(surf, F["small"], "ESTADO", (8, y + 4), DIM)
        put(surf, F["btn"], lg, (64, y + 1), RED if kind else GREEN)
        alt = L.get("alt")
        if alt is not None and flags & (1 << 21):
            put(surf, F["small"], "ALTITUD", (250, y + 4), DIM)
            put(surf, F["btn"], f"{alt / 1000:.1f} km".replace(".", ",") if alt >= 1000 else f"{alt:.0f} m",
                (W - 8, y + 1), ORANGE, anchor="topright")
        y += 26
        chips(surf, [("ATRACADO", flags & 1, BLUE), ("ATERRIZADO", flags & 2, BLUE), ("TREN", flags & 4, ORANGE),
                     ("ESCUDOS", flags & 8, BLUE), ("SUPERCRUCERO", flags & 16, BLUE), ("FA OFF", flags & 32, RED),
                     ("ARMAS", flags & 64, RED), ("LUCES", flags & 256, ORANGE), ("RECOGEDOR", flags & 512, ORANGE),
                     ("SILENCIOSO", flags & 1024, BLUE), ("RECOG. COMB.", flags & 2048, ORANGE),
                     ("MASA BLOQ.", flags & (1 << 16), RED), ("FSD CARGANDO", flags & (1 << 17), BLUE),
                     ("FSD ENFRIANDO", flags & (1 << 18), DIM), ("SOBRECALENT.", flags & (1 << 20), RED),
                     ("VISIÓN NOCT.", flags & (1 << 28), GREEN)], y)

'''
def rep(old, new):
    global s
    if old not in s: print("NO ENCONTRADO:", old); return
    s = s.replace(old, new, 1)

rep("def view_sub12", SNIP.lstrip("\n") + "def view_sub12")
rep("11: view_session,", "11: view_sub11, 111: view_session, 112: view_live,")
rep('73: "XENOBIOLOGÍA"}', '73: "XENOBIOLOGÍA", 111: "SESIÓN", 112: "EN VIVO"}')
rep("PARENT = {71: 7, 72: 7, 73: 7,", "PARENT = {71: 7, 72: 7, 73: 7, 111: 11, 112: 11,")

# toque del submenu 11: copia del bloque del submenu 7
L = s.split("\n")
j = next(i for i, l in enumerate(L) if 'ui["view"] = 71 + i' in l)
k = j
while not L[k].lstrip().startswith(("if v == 7", "elif v == 7")):
    k -= 1
blk = [l.replace("v == 7", "v == 11").replace("(7, i)", "(11, i)").replace("71 + i", "111 + i")
        .replace("grid(i, 3, 1)", "grid(i, 2, 1)").replace("range(3)", "range(2)") for l in L[k:j + 1]]
blk[0] = blk[0].replace("if v == 11", "elif v == 11", 1) if blk[0].lstrip().startswith("if ") else blk[0]
L[j + 1:j + 1] = blk
s = "\n".join(L)
open(p, "w", encoding="utf-8").write(s)
print("OK - bloque de toque añadido:")
print("\n".join(blk))
