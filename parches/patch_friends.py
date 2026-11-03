import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak52")
s = open(p, encoding="utf-8").read()
if "def view_friends" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
a2 = '        elif kind == "gravity" and len(p) >= 2:'
rep(a2, r'''        elif kind == "friend" and len(p) >= 2:
            t = {"on": ("AMIGO CONECTADO", GREEN), "off": ("AMIGO DESCONECTADO", DIM), "req": ("SOLICITUD DE AMISTAD", BLUE)}.get(p[1])
            if t:
                xa["a"] = dict(until=now + 4, col=t[1], title=t[0], big=p[0], lines=[])
        elif kind == "wing" and len(p) >= 2:
            t = {"invite": "INVITACIÓN A ALA", "join": "TE HAS UNIDO A UN ALA", "add": "NUEVO EN TU ALA", "leave": "HAS SALIDO DEL ALA"}.get(p[1])
            if t:
                xa["a"] = dict(until=now + 4, col=BLUE, title=t, big=p[0] if p[0] != "-" else "", lines=[])
''' + a2)
rep("def view_sub12", r'''# ---------- 11 sesion: cara AMIGOS (toca para cambiar) ----------
def view_friends(surf, d, flags, now):
    Fr = (d or {}).get("friends") or {}
    on, off, wg = Fr.get("on") or [], Fr.get("off") or [], Fr.get("wing") or []
    y = TOP + 4
    put(surf, F["small"], f"AMIGOS CONECTADOS ({len(on)})", (8, y), DIM)
    put(surf, F["small"], "toca para volver a SESIÓN", (W - 8, y), DIM, anchor="topright"); y += 16
    if not on:
        put(surf, F["btn"], "ninguno", (8, y), DIM); y += 24
    for k, n in enumerate(on[:10]):
        cx, cy = (8 if k % 2 == 0 else W // 2 + 4), y + (k // 2) * 22
        pygame.draw.circle(surf, GREEN, (cx + 5, cy + 8), 4)
        put(surf, F["btn"], n, (cx + 14, cy), GREEN, W // 2 - 26)
    y += ((min(len(on), 10) + 1) // 2) * 22 + 6
    if wg:
        pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
        put(surf, F["small"], "TU ALA", (8, y), DIM); y += 16
        put(surf, F["btn"], "  ·  ".join(wg), (8, y), BLUE, W - 16); y += 26
    if off and y < H - 40:
        pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
        put(surf, F["small"], "DESCONECTADOS HACE POCO", (8, y), DIM); y += 16
        for n, mins in off:
            if y > H - 18:
                break
            put(surf, F["small"], n, (8, y), WHITE, 300)
            put(surf, F["small"], f"hace {mins} min" if mins < 60 else f"hace {mins // 60} h", (W - 8, y), DIM, anchor="topright")
            y += 17

def view_session3(surf, d, flags, now):
    if ui.get("sesstab"):
        return view_friends(surf, d, flags, now)
    view_session2(surf, d, flags, now)
    n = len(((d or {}).get("friends") or {}).get("on") or [])
    put(surf, F["small"], f"toca para ver AMIGOS ({n} conectados)", (8, 252), GREEN if n else DIM)

''' + "def view_sub12")
rep("11: view_session2,", "11: view_session3,")
L = s.split("\n")
t = next((i for i, l in enumerate(L) if l.strip() == "elif v == 71:"), None)
if t is None:
    print("NO ENCONTRADO: toque"); ok = False
else:
    ind = L[t][:len(L[t]) - len(L[t].lstrip())]
    L[t:t] = [ind + "elif v == 11:", ind + "    ui['sesstab'] = 1 - ui.get('sesstab', 0); return"]
s = "\n".join(L)
rep("\n]\n\ndef view_changelog", '\n    ("0.52", "Amigos y ala: avisos y cara AMIGOS en Sesión"),\n]\n\ndef view_changelog')
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.52 · 29/10/2026 15:30"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
