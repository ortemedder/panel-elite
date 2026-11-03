import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak11")
s = open(p, encoding="utf-8").read()
if "def view_trip" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- 12.8 notas de viaje ----------
NOTES_FILE = "/home/ortem/notas.json"

def trip_load():
    try:
        with open(NOTES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []

trip = {"list": trip_load(), "sel": None, "page": 0, "d": None}

def trip_save():
    import os
    try:
        with open(NOTES_FILE + ".tmp", "w", encoding="utf-8") as f:
            json.dump(trip["list"], f, ensure_ascii=False, indent=1)
        os.replace(NOTES_FILE + ".tmp", NOTES_FILE)
    except OSError as e:
        print("notas:", e)

def trip_here(d):
    d = d or {}
    flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    b = d.get("bio") or {}
    st = d.get("station") or {}
    if b.get("species") and 0 < b.get("step", 0) < 3: tag = "XENOBIO"
    elif flags & 1: tag = "ESTACIÓN"
    elif f2 & 1: tag = "A PIE"
    elif flags & (1 << 26): tag = "SRV"
    elif flags & 2: tag = "ATERRIZADO"
    elif d.get("body"): tag = "PLANETA"
    else: tag = "ESPACIO"
    return {"sys": d.get("system"), "body": d.get("body"), "st": st.get("name") if flags & 1 else None,
            "lat": b.get("lat"), "lon": b.get("lon"), "R": b.get("R"), "pos": d.get("starpos"),
            "tag": tag, "t": time.time()}

def trip_label(n):
    sysname, body = n.get("sys") or "?", n.get("body") or ""
    if n.get("st"):
        return n["st"]
    if body and body != sysname:
        return body
    return sysname

def trip_dist(n, d):
    a, b = n.get("pos"), (d or {}).get("starpos")
    if not a or not b:
        return ""
    ly = math.dist(a, b)
    return "aquí" if ly < 0.01 else f"{ly:,.1f} al".replace(",", "X").replace(".", ",").replace("X", ".")

TRIP_SAVE = pygame.Rect(8, TOP + 2, 210, 34)
TRIP_PAGE = pygame.Rect(W - 118, TOP + 2, 110, 34)
TRIP_DEL = pygame.Rect(W - 130, H - 42, 122, 36)
TRIP_PER = 6
TAG_COL = {"XENOBIO": GREEN, "ESTACIÓN": BLUE, "A PIE": GREEN, "SRV": ORANGE, "ATERRIZADO": ORANGE,
           "PLANETA": ORANGE, "ESPACIO": DIM}

def trip_row(i):
    return pygame.Rect(8, TOP + 42 + i * 32, W - 16, 30)

def view_trip(surf, d, flags, now):
    trip["d"] = d
    L = trip["list"]
    draw_button(surf, TRIP_SAVE, "GUARDAR AQUÍ", None, F["btn"], filled=True, dim=not (d or {}).get("system"),
                lit=flash.get((128, "save"), 0) > now)
    pages = max(1, (len(L) + TRIP_PER - 1) // TRIP_PER)
    pg = trip["page"] % pages
    if pages > 1:
        draw_button(surf, TRIP_PAGE, f"PÁG {pg + 1}/{pages} >", None, F["small"])
    else:
        put(surf, F["small"], f"{len(L)} sitios", (W - 8, TOP + 12), DIM, anchor="topright")
    if not L:
        put(surf, F["btn"], "Aún no has guardado ningún sitio", (W // 2, (H + TOP) // 2 + 16), DIM, anchor="center")
        return
    for i, n in enumerate(L[pg * TRIP_PER:(pg + 1) * TRIP_PER]):
        r = trip_row(i)
        pygame.draw.rect(surf, DIM, r, 1, border_radius=4)
        put(surf, F["btn"], trip_label(n), (r.x + 6, r.y + 2), ORANGE, 290)
        tag = n.get("tag", "")
        put(surf, F["small"], tag, (r.right - 6, r.y + 3), TAG_COL.get(tag, DIM), anchor="topright")
        sub = f"{n.get('sys') or '?'}  ·  {time.strftime('%d/%m %H:%M', time.localtime(n.get('t', 0)))}"
        put(surf, F["small"], sub, (r.x + 6, r.y + 17), DIM, 330)
        put(surf, F["small"], trip_dist(n, d), (r.right - 6, r.y + 17), BLUE, anchor="topright")

def view_trip_detail(surf, d, flags, now):
    trip["d"] = d
    L, i = trip["list"], trip["sel"]
    if i is None or i >= len(L):
        ui["view"] = 128; return
    n = L[i]
    y = TOP + 4
    put(surf, F["big"], (n.get("sys") or "?").upper(), (8, y), ORANGE, W - 16); y += 28
    if n.get("st") or (n.get("body") and n.get("body") != n.get("sys")):
        put(surf, F["btn"], trip_label(n), (8, y), WHITE, W - 16); y += 22
    tag = n.get("tag", "")
    put(surf, F["small"], tag, (8, y), TAG_COL.get(tag, DIM))
    put(surf, F["small"], time.strftime("%d/%m/%Y %H:%M", time.localtime(n.get("t", 0))), (W - 8, y), DIM, anchor="topright"); y += 18
    if n.get("lat") is not None:
        put(surf, F["small"], f"lat {n['lat']:.4f}   lon {n['lon']:.4f}", (8, y), DIM); y += 18
    dist = trip_dist(n, d)
    if dist:
        put(surf, F["small"], "DISTANCIA", (8, y + 6), DIM)
        put(surf, F["big"], dist, (90, y), BLUE); y += 30
    b = (d or {}).get("bio") or {}
    here = (d or {}).get("body") and (d or {}).get("body") == n.get("body")
    if here and n.get("lat") is not None and b.get("lat") is not None and b.get("R"):
        p1, p2 = math.radians(b["lat"]), math.radians(n["lat"])
        dl = math.radians(n["lon"] - b["lon"])
        brg = math.degrees(math.atan2(math.sin(dl) * math.cos(p2),
                                      math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) % 360
        m = hav((b["lat"], b["lon"]), (n["lat"], n["lon"]), b["R"])
        cx, cy, r = 40, H - 40, 26
        pygame.draw.circle(surf, DIM, (cx, cy), r, 1)
        hdg = b.get("hdg")
        if hdg is not None:
            a = math.radians(brg - hdg)
            pt = lambda k, da: (cx + r * k * math.sin(a + da), cy - r * k * math.cos(a + da))
            pygame.draw.polygon(surf, GREEN, [pt(0.95, 0), pt(0.6, 2.5), (cx, cy), pt(0.6, -2.5)])
        txt = f"{m / 1000:.1f} km".replace(".", ",") if m >= 1000 else f"{m:.0f} m"
        put(surf, F["small"], "DESTINO", (76, H - 64), DIM)
        put(surf, F["big"], txt, (76, H - 50), GREEN)
        put(surf, F["small"], f"rumbo {brg:.0f}°", (76, H - 22), ORANGE)
    c, until = ui["confirm"]
    sure = c == "trip_del" and time.time() < until
    draw_button(surf, TRIP_DEL, "¿SEGURO?" if sure else "BORRAR", None, F["btn"], filled=sure)

def tap_trip(x, y):
    v, d = ui["view"], trip["d"]
    L = trip["list"]
    if v == 128:
        if TRIP_SAVE.collidepoint(x, y):
            n = trip_here(d)
            if not n["sys"]:
                set_alert("SIN DATOS DEL JUEGO", secs=2); return
            L.insert(0, n); trip_save(); trip["page"] = 0
            tap_flash((128, "save"))
            set_alert("SITIO GUARDADO", trip_label(n), col=GREEN, secs=2, kind="ok")
            return
        pages = max(1, (len(L) + TRIP_PER - 1) // TRIP_PER)
        if pages > 1 and TRIP_PAGE.collidepoint(x, y):
            trip["page"] += 1; return
        pg = trip["page"] % pages
        for i in range(TRIP_PER):
            idx = pg * TRIP_PER + i
            if idx < len(L) and trip_row(i).collidepoint(x, y):
                trip["sel"] = idx; ui["view"] = 129; return
    elif v == 129 and TRIP_DEL.collidepoint(x, y):
        c, until = ui["confirm"]
        if c == "trip_del" and time.time() < until:
            ui["confirm"] = (None, 0)
            if trip["sel"] is not None and trip["sel"] < len(L):
                L.pop(trip["sel"]); trip_save()
            ui["view"] = 128
        else:
            ui["confirm"] = ("trip_del", time.time() + 3)

'''
rep("def view_sub12", SNIP + "def view_sub12")
rep('("7", "MERCADO")]):', '("7", "MERCADO"), ("8", "NOTAS")]):')
rep('127: "MERCADO"}', '127: "MERCADO", 128: "NOTAS DE VIAJE", 129: "NOTA"}')
rep("126: 12, 127: 12}", "126: 12, 127: 12, 128: 12, 129: 128}")
rep("127: view_market}", "127: view_market, 128: view_trip, 129: view_trip_detail}")
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.11 · 28/10/2026 18:24"', s, count=1)
if not n: print("NO ENCONTRADO: PANEL_VER"); ok = False
L = s.split("\n")
try:
    j = next(i for i, l in enumerate(L) if 'ui["view"] = 121 + i' in l)
    k = j
    while "v == 12" not in L[k]:
        k -= 1
    for i in range(k, j + 1):
        L[i] = L[i].replace("range(7)", "range(8)")
    print("toque del 12:"); print("\n".join(L[k:j + 1]))
    t = next(i for i, l in enumerate(L) if l.strip() == "elif v == 71:")
    ind = L[t][:len(L[t]) - len(L[t].lstrip())]
    L[t:t] = [ind + "elif v in (128, 129):", ind + "    tap_trip(x, y); return"]
except StopIteration:
    print("NO ENCONTRADO: bloque de toque"); ok = False
s = "\n".join(L)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
