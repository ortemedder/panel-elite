#!/usr/bin/env python3
# Parche v0.97: misiones fijas en la pantalla grande y los 38 ingenieros (aviso, ficha en EXPLORACION y marca en la ruta).
# Va con el sender v0.97. Carpeta ingenieros/ (caras + ingenieros.json) junto a panel.py.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def eng_here" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.96' not in s:
    sys.exit("Este parche es para la v0.96")
shutil.copy(P, P + ".bak96")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# 1. con misiones: el cuadro se queda en MISIONES (sin GALNET)
rep('''def atr_cell(d, now):
    rot = [(133, 20)]''', '''def atr_cell(d, now):
    if (d or {}).get("missions"):
        return 4                                     # con misiones: fijo en MISIONES
    rot = [(133, 20)]''')
# 2. marca de ingeniero en el destino de la ruta
rep('''    put(surf, F["small"], f"quedan {total}" + (f" · {end[0]}" if end and total > 1 else ""), (W - 8, y), DIM, 140, anchor="topright")''',
    '''    eg_ = eng_at((end or [""])[0]) if end else None
    put(surf, F["small"], f"quedan {total}" + (f" · {end[0]}" if end and total > 1 else ""), (W - 8, y), DIM, 140, anchor="topright")
    if eg_:
        put(surf, F["small"], "ING. " + eg_["name"], (W - 8, y - 30), BLUE, 200, anchor="topright")''')
rep('''    battle_watch(d, now)''', '''    battle_watch(d, now)
    eng_watch(d, now)''')
rep('''("engbase", "BASE DE INGENIERO"),''', '''("engbase", "BASE DE INGENIERO"), ("engsys", "INGENIERO EN EL SISTEMA"),''')

CODE = r'''
# ---------- v0.97: ingenieros ----------
_ENGDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingenieros")
_ENG = {"data": None}
ENG_PROG = {"Known": "conocido", "Invited": "invitado", "Acquainted": "le conoces", "Unlocked": "desbloqueado", "Barred": "vetado"}

def eng_table():
    if _ENG["data"] is None:
        try:
            import json as _j
            with open(os.path.join(_ENGDIR, "ingenieros.json"), encoding="utf-8") as f:
                _ENG["data"] = {k: dict(v, key=k) for k, v in _j.load(f).items()}
        except Exception as e:
            log_exc("ingenieros.json", e)
            _ENG["data"] = {}
    return _ENG["data"]

def eng_at(system):
    sy = (system or "").lower()
    return next((v for v in eng_table().values() if v.get("system", "").lower() == sy), None) if sy else None

def eng_here(d):
    return eng_at((d or {}).get("system"))

def eng_status(e, d):
    p = ((d or {}).get("engprog") or {}).get(e["name"].lower())
    if not p:
        return "no le conoces", DIM
    prog, rank = p
    if prog == "Unlocked":
        return (f"rango {rank}" if rank is not None else "desbloqueado"), GREEN
    return ENG_PROG.get(prog, prog.lower() or "?"), ORANGE

def eng_where(e):
    pl = e.get("planet") or ""
    body = pl if pl and not pl[:1].isdigit() and len(pl.split()[0]) > 2 else f"{e['system']} {pl}".strip()
    return f"{e['base']}  ·  {body}  ·  {e.get('region', '')}".strip(" ·")

ENGW = {"sys": None}

def eng_watch(d, now):
    sy = (d or {}).get("system")
    if not sy or sy == ENGW["sys"]:
        return
    first = ENGW["sys"] is None
    ENGW["sys"] = sy
    e = eng_at(sy)
    if not e or first:
        return
    st, _ = eng_status(e, d)
    k0 = XA_K[0]
    try:
        XA_K[0] = "engsys"
        xa["a"] = dict(until=now + 8, col=BLUE, title="INGENIERO EN EL SISTEMA", big=e["name"].upper(),
                       lines=[st, eng_where(e)])
        play("ok")
    finally:
        XA_K[0] = k0

def eng_card(surf, d, r):
    """Ficha del ingeniero: cara, nombre y rango, donde esta y lo que mejora."""
    e = eng_here(d)
    if not e:
        return False
    pygame.draw.rect(surf, BLACK, r)
    pygame.draw.rect(surf, BLUE, r, 1, border_radius=6)
    ph = pygame.Rect(r.x + 6, r.y + 6, int((r.h - 12) * 240 / 210), r.h - 12)
    real, rr = (surf.real, surf._r(ph)) if type(surf).__name__ == "ScaledSurf" else (surf, ph)
    img = ship_img(os.path.join(_ENGDIR, f"ing_{e['key']}.jpg"), rr.w, rr.h, 255)
    if img is not None:
        real.blit(img, rr.topleft)
    x = ph.right + 8
    wd = r.right - x - 6
    st, col = eng_status(e, d)
    put(surf, F["btn"], e["name"].upper(), (x, r.y + 4), BLUE, wd - 110)
    put(surf, F["small"], st, (r.right - 8, r.y + 7), col, 110, anchor="topright")
    put(surf, F["small"], eng_where(e), (x, r.y + 26), ORANGE, wd)
    mods = sorted(e.get("mods") or [], key=lambda m: -int(m[1]) if m[:1] == "G" and m[1:2].isdigit() else 0)
    y = r.y + 44
    line = ""
    for m in mods:
        t = (line + "  ·  " if line else "") + m
        if F["small"].size(t)[0] > wd:
            put(surf, F["small"], line, (x, y), WHITE, wd); y += 15; line = m
            if y > r.bottom - 16:
                break
        else:
            line = t
    if line and y <= r.bottom - 16:
        put(surf, F["small"], line, (x, y), WHITE, wd)
    return True

_vex0 = view_explo

def view_explo(surf, d, flags, now):
    _vex0(surf, d, flags, now)
    eng_card(surf, d or {}, pygame.Rect(4, H - 112, W - 8, 108))

VIEWS[71] = view_explo

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")
rep('''# Enlace energético''', '''# Novedades v0.97
- Con misiones activas, el cuadro de la pantalla grande se queda en MISIONES (sin GALNET).
- Ingenieros (38, de nave y de a pie; carpeta ingenieros/ junto a panel.py): al llegar a su sistema, aviso INGENIERO EN EL SISTEMA con tu rango; en 7.1 EXPLORACIÓN su ficha con cara, base, planeta y lo que mejora; en NAVEGACIÓN, «ING.» si el destino de la ruta es su sistema.
# Enlace energético''')
rep('    ("0.96", "Versión del sender, foto del objetivo, sin cobrar, ingenieros, combustible, minería, Powerplay y rapidez"),\n',
    '    ("0.96", "Versión del sender, foto del objetivo, sin cobrar, ingenieros, combustible, minería, Powerplay y rapidez"),\n'
    '    ("0.97", "Misiones fijas en la pantalla grande y los 38 ingenieros con su ficha"),\n')
s = re.sub(r'PANEL_VER = "v0\.96[^"]*"', 'PANEL_VER = "v0.97 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.97  (copia en " + P + ".bak96)")
