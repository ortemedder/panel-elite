#!/usr/bin/env python3
# Parche v1.0 beta 13 (desde la beta 12c): COLONIZACION con filtros TODO / AQUI / EN EL SISTEMA, lo que llevas en la
# bodega se descuenta (en azul, recogido sin entregar), aviso de carga por entregar al atracar en el deposito, y tocar
# el recuadro verde del MERCADO abre COLONIZACION > AQUI. EN EL SISTEMA necesita el sender v1.0b9.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def col_rows" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b12c', s):
    sys.exit("Este parche es para la v1.0 beta 12c")
shutil.copy(P, P + ".bak100b12c")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

CODE = r'''
# ---------- v1.0 beta 13: COLONIZACION con bodega, filtros y EN EL SISTEMA ----------
EV_LIST.append(("colentrega", "COLONIA: CARGA POR ENTREGAR"))
COLF = [("todo", "TODO"), ("aqui", "AQUÍ"), ("sis", "EN EL SISTEMA")]
COLF_R = [pygame.Rect(W - 90 - 4 - 56 - 4 - 50, TOP + 2, 50, 18), pygame.Rect(W - 90 - 4 - 56, TOP + 2, 56, 18),
          pygame.Rect(W - 90, TOP + 2, 86, 18)]
COL_HEAD = pygame.Rect(0, TOP, COLF_R[0].x - 4, 22)
COLROWS = []                                             # (rect, nombre de estacion) en EN EL SISTEMA
MKBOX = {"r": None}

def col_rows(d, x):
    """Cada mercancia: (nombre, clave, pedido, entregado, en bodega util, falta de verdad)."""
    carg = {(n or "").lower(): c for n, c in ((d or {}).get("cargo") or [])}
    out = []
    for r in x.get("res") or []:
        name, req, prov = r[0], r[1], r[2]
        key = r[3] if len(r) > 3 else ""
        pend = max(0, req - prov)
        if not pend:
            continue
        inb = min(carg.get((name or "").lower(), 0), pend)
        out.append((name, key, req, prov, inb, pend - inb))
    out.sort(key=lambda t: (t[5] == 0, -t[5], -t[4]))
    return out

def col_here(d):
    mk = (d or {}).get("market") or {}
    return {(r[0] or "").lower(): r for r in (mk.get("col") or [])}

def col_sys_state(d, rows):
    S = (d or {}).get("colsys") or {}
    off = S.get("off") or {}
    hit = [t for t in rows if t[5] > 0 and off.get(t[1])]
    if not S or S.get("status", "").startswith("consultando") or not S.get("status"):
        return S, off, hit, DIM
    return S, off, hit, GREEN if hit else RED

def _hace(sec):
    return "?" if not sec or sec < 0 else f"{int(sec // 60)} min" if sec < 3600 else f"{sec / 3600:.0f} h" if sec < 172800 else f"{sec / 86400:.0f} días"

def view_colonia(surf, d, flags, now):
    C, L, i = col_pick(d)
    COLROWS.clear()
    if not L:
        if d and "colonia" not in d:
            put(surf, F["btn"], "actualiza el sender a la v1.0b9", (W // 2, H // 2 - 10), ORANGE, W - 16, anchor="center")
        else:
            put(surf, F["btn"], "sin construcciones", (W // 2, H // 2 - 12), DIM, anchor="center")
            put(surf, F["small"], "atraca en un depósito de construcción y abre su mercado", (W // 2, H // 2 + 12), DIM, W - 16, anchor="center")
        return
    x = L[i]
    rows = col_rows(d, x)
    here = col_here(d)
    S, off, hit, scol = col_sys_state(d, rows)
    f = ui.get("colf", "todo")
    # cabecera: nombre (tocar = otra construccion) y filtros
    y = TOP + 3
    nm = (x.get("st") or "CONSTRUCCIÓN").upper() + (" · " + x["sys"] if x.get("sys") else "")
    w_ = put(surf, F["btn"], nm, (8, y), ORANGE, COLF_R[0].x - 60)
    if len(L) > 1:
        put(surf, F["tiny"], f"{i + 1}/{len(L)} >", (14 + w_, y + 4), BLUE)
    for k, (fk, lab) in enumerate(COLF):
        r = COLF_R[k]
        sel = f == fk
        col = scol if fk == "sis" else ORANGE
        pygame.draw.rect(surf, col if sel else BLACK, r, border_radius=4)
        pygame.draw.rect(surf, col, r, 1, border_radius=4)
        put(surf, F["tiny"], lab, r.center, BLACK if sel else col, r.w - 4, anchor="center")
    y += 21
    # progreso
    bar = pygame.Rect(8, y, W - 16, 11)
    pygame.draw.rect(surf, DIM, bar, 1)
    pygame.draw.rect(surf, GREEN if x.get("done") else ORANGE, (bar.x + 1, bar.y + 1, int((bar.w - 2) * min(100, x.get("prog") or 0) / 100), bar.h - 2))
    st_ = "COMPLETADA" if x.get("done") else "FALLIDA" if x.get("fail") else f"{x.get('prog', 0):.1f} %".replace(".", ",")
    put(surf, F["tiny"], st_, bar.center, WHITE, anchor="center")
    y += 14
    falta = sum(t[5] for t in rows)
    bod = sum(t[4] for t in rows)
    cap = (d or {}).get("cargocap") or 0
    t_ = f"FALTAN {falta:,} t".replace(",", ".") + (f" · ~{-(-falta // cap)} viajes de {cap} t" if cap and falta else "")
    xx = put(surf, F["small"], t_, (8, y), WHITE if falta else GREEN, W - 16)
    if bod:
        put(surf, F["small"], f" · {bod:,} t en bodega por entregar".replace(",", "."), (8 + xx, y), BLUE, W - 24 - xx)
    y += 16
    cw = (W - 16) // 2
    if f == "todo":
        pages = max(1, (len(rows) + 25) // 26)
        pg = ui.get("colpg", 0) % pages
        vis = rows[pg * 26:(pg + 1) * 26]
        nrow = max(1, (len(vis) + 1) // 2)
        for k, (name, key, req, prov, inb, real) in enumerate(vis):
            cx, cy = 8 + (k // nrow) * (cw + 4), y + (k % nrow) * 14
            sold = name.lower() in here and real > 0
            col = BLUE if real == 0 else GREEN if sold else ORANGE
            put(surf, F["tiny"], ("• " if sold else "") + name, (cx, cy), col, 96)
            b = pygame.Rect(cx + 100, cy + 3, 40, 7)
            pygame.draw.rect(surf, DIM, b, 1)
            w1 = int(38 * prov / req) if req else 0
            w2 = int(38 * inb / req) if req else 0
            pygame.draw.rect(surf, ORANGE, (b.x + 1, b.y + 1, w1, 5))
            if w2:
                pygame.draw.rect(surf, BLUE, (b.x + 1 + w1, b.y + 1, min(w2, 38 - w1), 5))
            if real == 0:
                put(surf, F["tiny"], f"{inb:,} en bodega".replace(",", "."), (cx + cw - 4, cy), BLUE, anchor="topright")
            else:
                xr = put(surf, F["tiny"], f"{real:,}".replace(",", "."), (cx + cw - 4, cy), col, anchor="topright")
                if inb:
                    put(surf, F["tiny"], f"+{inb:,}".replace(",", "."), (cx + cw - 8 - tw_(F["tiny"], f"{real:,}".replace(",", ".")), cy), BLUE, anchor="topright")
        foot = f"pág {pg + 1}/{pages} · " if pages > 1 else ""
        put(surf, F["tiny"], foot + "verde = se vende aquí · azul = en tu bodega · naranja = falta", (8, H - 14), DIM, W - 16)
    elif f == "aqui":
        mk = (d or {}).get("market") or {}
        vis = [t for t in rows if t[5] > 0 and t[0].lower() in here]
        if not here and not mk.get("col"):
            put(surf, F["small"], "abre el mercado de esta estación para ver qué se vende", (W // 2, y + 40), DIM, W - 16, anchor="center")
        elif not vis:
            put(surf, F["btn"], "aquí no se vende nada de lo que falta", (W // 2, y + 40), RED, W - 16, anchor="center")
        put(surf, F["tiny"], f"EN {(mk.get('station') or 'ESTA ESTACIÓN').upper()}", (8, y), DIM, W - 16); y += 14
        for name, key, req, prov, inb, real in vis[:13]:
            r_ = here[name.lower()]
            put(surf, F["small"], name, (8, y), GREEN, 170)
            put(surf, F["small"], f"hay {r_[1]:,} t · {r_[2]:,} cr".replace(",", "."), (184, y), WHITE, 170)
            put(surf, F["small"], f"faltan {real:,} t".replace(",", "."), (W - 8, y), ORANGE, anchor="topright")
            y += 15
    else:
        st = S.get("status") or ""
        info = (f"{S.get('sys')}: " if S.get("sys") else "") + (
            f"{S.get('n', 0)} mercados en EDSM · consultado hace {_hace(now - (S.get('t') or now))}" if st == "ok" else st or "entra en un sistema con la construcción sin terminar")
        put(surf, F["tiny"], info, (8, y), DIM, W - 16); y += 14
        vis = [t for t in rows if t[5] > 0]
        if st == "ok" and not hit:
            put(surf, F["btn"], "en este sistema no se vende nada de lo que falta", (W // 2, y + 40), RED, W - 16, anchor="center")
        pages = max(1, (len(hit) + 7) // 8)
        pg = ui.get("colpg", 0) % pages
        for name, key, req, prov, inb, real in hit[pg * 8:(pg + 1) * 8]:
            o = off[key][0]
            stn, stock, price, dist, pad, mt, fc = o[0], o[1], o[2], o[3], o[4], o[5], o[6]
            put(surf, F["small"], name, (8, y), GREEN, 220)
            put(surf, F["small"], f"faltan {real:,} t".replace(",", "."), (W - 8, y), ORANGE, anchor="topright")
            line = (f"→ {stn}" + (" (PORTANAVES)" if fc else "") + f" · {stock:,} t · {price:,} cr · {dist:,} ls · pad {pad}".replace(",", ".")
                    + (f" · hace {_hace(now - mt)}" if mt else ""))
            put(surf, F["tiny"], line.replace("→", ">"), (16, y + 14), WHITE, W - 24)
            COLROWS.append((pygame.Rect(0, y, W, 27), stn))
            y += 28
        put(surf, F["tiny"], (f"pág {pg + 1}/{pages} · " if pages > 1 else "") + "toca una fila: copia la estación al portapapeles del PC · abajo: página",
            (8, H - 14), DIM, W - 16)

VIEWS[135] = view_colonia

# --- MERCADO: recuadro verde con lo que falta de verdad (descontando la bodega); tocarlo abre COLONIZACION > AQUI ---
def view_market_b13(surf, d, flags, now):
    _view_market_b11(surf, d, flags, now)              # el MERCADO sin el recuadro de la b11
    MKBOX["r"] = None
    mk = (d or {}).get("market") or {}
    try:
        m_ = market_pick(d, now)
        if m_.get("missing") or m_.get("src") == "EDSM" or m_.get("other"):
            return
    except Exception:
        pass
    C, L, i = col_pick(d)
    if not L:
        return
    real = {t[0].lower(): t[5] for t in col_rows(d, L[i])}
    rows = [r for r in (mk.get("col") or []) if real.get((r[0] or "").lower(), 0) > 0]
    if not rows:
        return
    n = min(4, len(rows))
    box = pygame.Rect(6, H - 44 - 18 - n * 14, W - 12, 18 + n * 14)
    pygame.draw.rect(surf, (0, 28, 8), box, border_radius=5)
    pygame.draw.rect(surf, GREEN, box, 1, border_radius=5)
    put(surf, F["small"], "PARA TU COLONIA (se vende aquí)" + (f"  +{len(rows) - n} más" if len(rows) > n else "") + "  · toca: ver todo",
        (box.x + 6, box.y + 2), GREEN, box.w - 12)
    yy = box.y + 18
    for name, stock, price, need in rows[:n]:
        put(surf, F["tiny"], name, (box.x + 8, yy), GREEN, 170)
        put(surf, F["tiny"], f"hay {stock:,} t · {price:,} cr".replace(",", "."), (box.x + 190, yy), WHITE, 150)
        put(surf, F["tiny"], f"faltan {real[name.lower()]:,} t".replace(",", "."), (box.right - 8, yy), ORANGE, anchor="topright")
        yy += 14
    MKBOX["r"] = box

VIEWS[127] = view_market_b13

# --- aviso: carga por entregar al atracar en el deposito ---
_col_pend_b13 = col_pend

def col_pend(now):
    p = COLB.get("pend")
    _col_pend_b13(now)
    if p and now >= p[0] and "atracado" in p[1]:
        try:
            d = state.get("data")
            C, L, i = col_pick(d)
            if L:
                bod = sum(t[4] for t in col_rows(d, L[i]))
                if bod and ev_on("colentrega"):
                    k0 = XA_K[0]
                    try:
                        XA_K[0] = "colentrega"
                        set_alert(f"TIENES {bod:,} t POR ENTREGAR".replace(",", "."), "entrégalas en este depósito", BLUE, 8, kind="info")
                        play("ok")
                    finally:
                        XA_K[0] = k0
        except Exception as e:
            log_exc("colonia entrega", e)

# --- toques ---
_on_tap_b13 = on_tap

def on_tap(x, y):
    v = ui.get("view")
    if v == 127 and MKBOX.get("r") and MKBOX["r"].collidepoint(x, y) and not (ui.get("alert") and time.time() < ui["alert"]["until"]):
        ui["view"] = 135; ui["colf"] = "aqui"; ui["colsel"] = None; ui["colpg"] = 0; TAP_EV.set(); return
    if v == 135 and y > TOP and not (ui.get("alert") and time.time() < ui["alert"]["until"]):
        for k, (fk, lab) in enumerate(COLF):
            if COLF_R[k].inflate(4, 8).collidepoint(x, y):
                ui["colf"] = fk; ui["colpg"] = 0; TAP_EV.set(); return
        if COL_HEAD.collidepoint(x, y):
            C, L, i = col_pick(state.get("data"))
            if L:
                ui["colsel"] = (i + 1) % len(L); ui["colpg"] = 0
            TAP_EV.set(); return
        if ui.get("colf") == "sis" and y < H - 18:
            for r, stn in COLROWS:
                if r.collidepoint(x, y):
                    ir_send(stn); TAP_EV.set(); return
            return
        ui["colpg"] = ui.get("colpg", 0) + 1; TAP_EV.set(); return
    _on_tap_b13(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 12c''', '''# Novedades v1.0 beta 13
- COLONIZACIÓN: lo que llevas en la bodega se descuenta de lo que falta. En azul lo que ya llevas (recogido, sin entregar); «+N» en azul si solo cubre una parte. La barra tiene dos tramos: entregado (naranja) y en bodega (azul).
- Filtros arriba: TODO, AQUÍ (lo que falta y se vende en esta estación) y EN EL SISTEMA (la mejor estación del sistema para cada mercancía, según EDSM: existencias, precio, distancia, pad y antigüedad). EN EL SISTEMA en verde si hay algo, en rojo si no, en gris consultando. Tocar una fila copia la estación al portapapeles del PC. Necesita el sender v1.0b9.
- MERCADO: el recuadro verde ya descuenta tu bodega; tocarlo abre COLONIZACIÓN > AQUÍ.
- Al atracar en el depósito con carga que le sirve: aviso TIENES N t POR ENTREGAR (se apaga en ALERTAS).
# Novedades v1.0 beta 12c''')
rep('    ("1.0b12c", ', '    ("1.0b13", "COLONIZACIÓN: bodega, filtros TODO / AQUÍ / EN EL SISTEMA, aviso de carga por entregar"),\n    ("1.0b12c", ')
s = re.sub(r'PANEL_VER = "v1\.0b12c[^"]*"', 'PANEL_VER = "v1.0b13 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 13  (copia en " + P + ".bak100b12c)")
