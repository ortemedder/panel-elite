#!/usr/bin/env python3
# Parche v1.0 beta 12 (desde la beta 11): COLONIZACION se abre sola al atracar en un sitio de construccion (por el tipo de
# estacion o al llegar datos del deposito estando atracado); la pestana pasa a llamarse COLONIZACION; la expansion
# probable sale de la ficha del sistema y no del radar.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "# ---------- v1.0 beta 12 ----------" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b11', s):
    sys.exit("Este parche es para la v1.0 beta 11")
shutil.copy(P, P + ".bak100b11")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# fuera del radar: la expansion probable (la linea roja, el circulo y la etiqueta)
EXPBLK = '        # expansiones: linea roja parpadeante hacia el destino probable\n        for v in ps:\n            if "Expansion" in (v.get("activos") or []) + (v.get("pendientes") or []):\n                o = to_px(v["pos"])\n                if not o:\n                    continue\n                tg = exp_target(D, v)\n                if tg:\n                    dd, tn, tp = tg\n                    t_ = to_px(tp)\n                    if t_ and blink:\n                        pygame.draw.line(surf, RED, o, t_, 2)\n                    if t_:\n                        pygame.draw.circle(surf, RED if blink else (110, 0, 0), t_, 7, 2)\n                        lab = "PROBABLE " + (tn.upper() if len(tn) <= 12 else tn.upper()[:11] + "…")\n                        lr = pygame.Rect(t_[0] + 9, t_[1] - 6, tw_(F["tiny"], lab), 12)\n                        if lr.right > R.right:\n                            lr.right = t_[0] - 9\n                        lr.x = max(2, lr.x)\n                        if blink:\n                            put(surf, F["tiny"], lab, lr.topleft, RED); used.append(lr)\n                else:\n                    pygame.draw.circle(surf, RED if blink else (110, 0, 0), o, 14, 1)\n'
rep(EXPBLK, "")
rep('"MAPA DE LA FACCIÓN" if z == 1 else f"MAPA x{z}"', '"MAPA" if z == 1 else f"MAPA x{z}"')
rep('TABS[1].append((135, "COLONIA"))', 'TABS[1].append((135, "COLONIZACIÓN"))')
rep('f"  +{len(L) - n} más en COLONIA"', 'f"  +{len(L) - n} más en COLONIZACIÓN"')

CODE = r'''
# ---------- v1.0 beta 12 ----------
# --- COLONIZACION: se abre sola (una vez por atraque) ---
COLB = {"done": set(), "t": None}

def col_auto(d, now):
    C = (d or {}).get("colonia") or {}
    L = C.get("list") or []
    fl = (d or {}).get("Flags", 0)
    docked = bool(fl & 1) or bool(fl & 2)                # atracado o posado
    if not docked:
        COLB["done"].clear()
    newest = max((x.get("t") or 0 for x in L), default=0)
    why = key = None
    if C.get("dock") and docked and C["dock"] not in COLB["done"]:
        why, key = "atracado en un depósito", C["dock"]
    elif COLB["t"] is not None and newest > COLB["t"] and docked and L and L[0].get("mid") not in COLB["done"]:
        why, key = "datos nuevos del depósito", L[0].get("mid")
    COLB["t"] = newest if COLB["t"] is None else max(COLB["t"], newest)
    if why:
        COLB["done"].add(key)
        if auto_on("colonia") and not ui.get("idle_on"):
            ui["view"] = 135; ui["colsel"] = None; ui["colpg"] = 0
            plog("Colonización: abro la pestaña (" + why + ")")
        else:
            plog("Colonización: no la abro (" + why + "; cambio auto apagado o en espera)")

_render_b12 = render

def render(surf):
    COLA["pend"] = 0                                     # la apertura de la b11 queda sustituida
    COLA["dock"] = None
    r_ = _render_b12(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d is not None and time.time() - rx < 5:
            col_auto(d, time.time())
    except Exception as e:
        log_exc("colonización auto", e)
    return r_

# --- ficha del sistema: destino probable de la expansion ---
_ficha_b12 = VIEWS[194]

def ficha_b12(surf, d, flags, now):
    _ficha_b12(surf, d, flags, now)
    D, name, v = fs_get()
    if not v or "Expansion" not in (v.get("activos") or []) + (v.get("pendientes") or []):
        return
    bad = [st for st in (v.get("activos") or []) + (v.get("pendientes") or []) if st in TIPS and st not in ST_GOOD][:2]
    y = H - 44 + 15 + 13 * len(bad)
    if y > H - 14:
        return
    tg = exp_target(D or FACD["data"] or {}, v)
    txt = (f"EXPANSIÓN · destino probable: {tg[1]} (a {tg[0]:.1f} al)".replace(".", ",") if tg
           else "EXPANSIÓN · destino desconocido (ningún sistema conocido a menos de 30 al)")
    put(surf, F["tiny"], txt, (100, y), BLUE, W - 104)

VIEWS[194] = ficha_b12

# --- ALERTAS y SONIDO: numero pequeno en cada boton (el mismo #n que sale en el aviso) ---
_evlist_b12 = view_evlist

def view_evlist(surf, d, flags, now):
    v = ui["view"]
    if v not in (161, 163):
        return _evlist_b12(surf, d, flags, now)
    L, st, pk = _evl(v)
    pages = (len(L) + EVPP - 1) // EVPP
    pg = ui.get(pk, 0) % pages
    on = cfg.get(st) or {}
    df = EVL[v][4]
    n = sum(1 for k, _ in L if on.get(k, df.get(k, True)))
    top = [("TODOS ON", None), ("TODOS OFF", None), (f"PÁG {pg + 1}/{pages}" if pages > 1 else f"{n} de {len(L)}", None)]
    for i, (t, _) in enumerate(top):
        draw_button(surf, grid(i, 3, 1, TOP, TOP + 40), t, None, F["btn"], lit=flash.get((v, 100 + i), 0) > now)
    for i, (k, name) in enumerate(L[pg * EVPP:(pg + 1) * EVPP]):
        r = grid(i, 2, 6, TOP + 38, H)
        lit = flash.get((v, i), 0) > now
        fill = on.get(k, df.get(k, True))
        if fill or lit:
            pygame.draw.rect(surf, WHITE if lit else ORANGE, r, border_radius=6)
        else:
            pygame.draw.rect(surf, ORANGE, r, 2, border_radius=6)
        col = BLACK if fill or lit else ORANGE
        lab = str(pg * EVPP + i + 1)
        put(surf, F["tiny"], lab, (r.x + 6, r.centery), col, anchor="midleft")
        x0 = r.x + 10 + tw_(F["tiny"], "00")
        put(surf, F["small"] if len(name) > 17 else F["btn"], name, ((x0 + r.right - 4) // 2, r.centery), col, r.right - 4 - x0, anchor="center")

VIEWS[161] = VIEWS[163] = view_evlist
'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 11''', '''# Novedades v1.0 beta 12
- COLONIZACIÓN (antes COLONIA) se abre sola al atracar en un sitio de construcción, una vez por atraque: lo detecta por el tipo de estación o al llegar datos del depósito estando atracado o posado. En el LOG queda apuntado cuándo la abre. Necesita el sender v1.0b8.
- La expansión probable ya no sale en el radar; está en la ficha del sistema que se expande, con el destino probable y la distancia.
- ALERTAS y SONIDO: cada botón lleva su número en pequeño (el mismo #n que sale en la esquina del aviso).
# Novedades v1.0 beta 11''')
rep('    ("1.0b11", ', '    ("1.0b12", "COLONIZACIÓN se abre sola; expansión probable en la ficha; números en ALERTAS"),\n    ("1.0b11", ')
s = re.sub(r'PANEL_VER = "v1\.0b11[^"]*"', 'PANEL_VER = "v1.0b12 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 12  (copia en " + P + ".bak100b11)")
