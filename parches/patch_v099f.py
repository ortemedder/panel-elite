#!/usr/bin/env python3
# Parche v0.99f: MINERIA sin tapar los drones (toneladas/hora encima de la raya), barra de BODEGA con aviso de llena
# y MINERIA en el cuadro 3 de la pantalla grande mientras mines.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def mining_active" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.99e' not in s:
    sys.exit("Este parche es para la v0.99e")
shutil.copy(P, P + ".bak99e")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

rep('''        pygame.draw.rect(surf, BLACK, (0, H - 18, W, 18))
        put(surf, F["small"], f"{tons} t refinadas" + (f"  ·  {rate:.0f} t/hora".replace(".", ",") if rate else "")
            + (f"  ·  ~{crx(val / h)} cr/hora" if val and h > 0.02 else ""), (8, H - 16), GREEN, W - 16)''',
    '''        put(surf, F["small"], f"{rate:.0f} t/h".replace(".", ",") + (f"  ·  ~{crx(val / h)} cr/h" if val and h > 0.02 else "")
            if rate else f"{tons} t refinadas", (W - 8, H - 42), GREEN, W - 236, anchor="topright")''')
rep('''VIEWS[10] = view_mining''', '''VIEWS[10] = view_mining

def mining_cargo_bar(surf, d, now):
    """Barra de la bodega en MINERIA: naranja desde el 90 %, roja parpadeando llena."""
    cap = (d or {}).get("cargocap")
    used = sum(c for _, c in ((d or {}).get("cargo") or []))
    if not cap:
        return
    pct = min(1.0, used / cap)
    full = used >= cap
    col = RED if full else ORANGE if pct >= 0.9 else BLUE
    r = pygame.Rect(8, H - 44, 220, 16)
    pygame.draw.rect(surf, BLACK, r.inflate(4, 4))
    pygame.draw.rect(surf, DIM, r, 1)
    if not full or int(now * 3) % 2 == 0:
        pygame.draw.rect(surf, col, (r.x + 2, r.y + 2, int((r.w - 4) * pct), r.h - 4))
    txt = "¡BODEGA LLENA!" if full else (f"BODEGA {pct * 100:.0f} %" + (f"  ·  {used}/{cap} t" if pct < 0.9 else "  ·  casi llena"))
    put(surf, F["small"], txt, r.center, WHITE if full or pct >= 0.9 else WHITE, r.w - 8, anchor="center")

_vmin1 = view_mining

def view_mining(surf, d, flags, now):
    _vmin1(surf, d, flags, now)
    if "rhino" not in ((d or {}).get("srvtype") or "").lower():
        mining_cargo_bar(surf, d, now)

VIEWS[10] = view_mining

MINE = {"sig": None, "t": 0.0}

def mining_active(d, now):
    """Se esta minando: prospector, recolector, roca prospectada o tonelada refinada en los ultimos 10 min."""
    m = (d or {}).get("mining") or {}
    sig = (m.get("prospectors"), m.get("collectors"), m.get("t1"), str(m.get("last"))[:200])
    if MINE["sig"] is None:
        MINE["sig"] = sig
    elif sig != MINE["sig"]:
        MINE["sig"] = sig; MINE["t"] = now
    return now - MINE["t"] < 600''')
rep('''    if d.get("target") and mode != "COMBATE" and len(cells) >= 3:''',
    '''    if mode != "COMBATE" and len(cells) >= 3 and 10 not in cells and mining_active(d, now) and not (d.get("Flags2", 0) & 1):
        cells[2] = 10                                # minando: MINERIA en el cuadro 3
    if d.get("target") and mode != "COMBATE" and len(cells) >= 3:''')
s = s.replace('    ("0.99e", "Sin los toques de prueba en el LOG"),\n',
              '    ("0.99e", "Sin los toques de prueba en el LOG"),\n'
              '    ("0.99f", "MINERÍA: barra de bodega, toneladas/hora sin tapar y en el cuadro 3 al minar"),\n', 1)
s = re.sub(r'PANEL_VER = "v0\.99e[^"]*"', 'PANEL_VER = "v0.99f · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.99f  (copia en " + P + ".bak99e)")
