#!/usr/bin/env python3
# Parche v1.0 beta 14 (desde la beta 13): EN EL SISTEMA sin textos montados y con «dato antiguo» (> 30 dias), nombre de la
# nave en EN VIVO en azul (como el copiloto), y aviso al pedir atraque / abrir el mercado si la estacion no vende nada
# de lo que le falta a tu construccion (necesita el sender v1.0b10).
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def colbuy_watch" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b13 ', s):
    sys.exit("Este parche es para la v1.0 beta 13")
shutil.copy(P, P + ".bak100b13")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# EN EL SISTEMA: las filas que quepan y los datos antiguos en gris
rep('''        pages = max(1, (len(hit) + 7) // 8)
        pg = ui.get("colpg", 0) % pages
        for name, key, req, prov, inb, real in hit[pg * 8:(pg + 1) * 8]:
            o = off[key][0]''', '''        per = max(1, (H - 18 - y) // 28)                 # las que quepan sobre el pie
        pages = max(1, (len(hit) + per - 1) // per)
        pg = ui.get("colpg", 0) % pages
        for name, key, req, prov, inb, real in hit[pg * per:(pg + 1) * per]:
            o = next((q for q in off[key] if not q[5] or now - q[5] < 30 * 86400), off[key][0])   # mejor uno reciente''')
rep('''                    + (f" · hace {_hace(now - mt)}" if mt else ""))
            put(surf, F["tiny"], line.replace("→", ">"), (16, y + 14), WHITE, W - 24)''', '''                    + (f" · hace {_hace(now - mt)}" if mt else ""))
            old_ = bool(mt) and now - mt > 30 * 86400
            put(surf, F["tiny"], line.replace("→", ">") + (" · DATO ANTIGUO" if old_ else ""), (16, y + 14), DIM if old_ else WHITE, W - 24)''')
rep('''    return "?" if not sec or sec < 0 else f"{int(sec // 60)} min" if sec < 3600''',
    '''    return "?" if sec is None or sec < 0 else "ahora" if sec < 60 else f"{int(sec // 60)} min" if sec < 3600''')
# EN VIVO: nombre de la nave en el azul del copiloto
rep('''        put(surf, F["small"], nm, (W - 8, y + 16), DIM, 300, anchor="topright")''',
    '''        put(surf, F["small"], nm, (W - 8, y + 16), (70, 120, 230), 300, anchor="topright")''')

CODE = r'''
# ---------- v1.0 beta 14: aviso de compra para tu construccion ----------
EV_LIST.append(("colcompra", "COLONIA: ESTACIÓN SIN LO QUE TE FALTA"))
CBW = {"t": None, "mk": None}

def _col_need_keys(d):
    C, L, i = col_pick(d)
    if not L:
        return None, []
    x = next((y for y in L if not y.get("done") and not y.get("fail")), None)
    if not x:
        return None, []
    return x, [t for t in col_rows(d, x) if t[5] > 0]

def _col_alert(title, sub, col, voz=None):
    if not ev_on("colcompra"):
        return
    k0 = XA_K[0]
    try:
        XA_K[0] = "colcompra"
        set_alert(title, sub, col, 8, kind="info")
        play("alarm" if col == RED else "ok")
        if voz:
            voice_say(voz)
    finally:
        XA_K[0] = k0

def _col_alt(d, need, skip_mid=None):
    """Estacion del sistema (segun EDSM) que vende mas cosas de lo que falta: (nombre, [mercancias])."""
    off = ((d or {}).get("colsys") or {}).get("off") or {}
    cnt = {}
    for fresh in (True, False):                          # primero solo con datos de menos de 30 dias
        for name, key, req, prov, inb, real in need:
            for o in off.get(key) or []:
                if o[7] != skip_mid and (not fresh or not o[5] or time.time() - o[5] < 30 * 86400):
                    cnt.setdefault(o[0], []).append(name)
        if cnt:
            break
    if not cnt:
        return None
    st = max(cnt, key=lambda k: len(cnt[k]))
    return st, cnt[st]

def colbuy_watch(d, now):
    B = (d or {}).get("colbuy") or {}
    t = B.get("t")
    if CBW["t"] is None:
        CBW["t"] = t or 0                                # al arrancar no avisa de lo antiguo
    elif t and t != CBW["t"]:
        CBW["t"] = t
        if B.get("status") == "ok" and not B.get("dep"):
            x, need = _col_need_keys(d)
            if need:
                keys = set(B.get("keys") or [])
                have = [t_[0] for t_ in need if t_[1] in keys]
                if have:
                    _col_alert(f"AQUÍ HAY {len(have)} DE LO QUE TE FALTA", ", ".join(have[:3]) + ("…" if len(have) > 3 else "") + f" · {B.get('st')}", GREEN)
                else:
                    alt = _col_alt(d, need, B.get("mid"))
                    _col_alert("ESTA ESTACIÓN NO VENDE NADA DE LO QUE TE FALTA",
                               (f"prueba en {alt[0]} ({', '.join(alt[1][:3])})" if alt else f"{B.get('st')} · para tu construcción"),
                               RED, "esta estación no vende nada de lo que te falta")
    # al abrir el mercado ya atracado: con los datos del juego
    mk = (d or {}).get("market") or {}
    key_ = (mk.get("mid"), mk.get("t"))
    if CBW["mk"] is None:
        CBW["mk"] = key_
    elif key_ != CBW["mk"] and mk.get("t") and (d or {}).get("Flags", 0) & 1:
        CBW["mk"] = key_
        C = (d or {}).get("colonia") or {}
        mids = {str(y.get("mid")) for y in C.get("list") or []}
        if str(mk.get("mid")) in mids or C.get("dock"):
            return                                       # es un deposito de construccion
        x, need = _col_need_keys(d)
        if need:
            here = col_here(d)
            if not any(t_[0].lower() in here for t_ in need):
                alt = _col_alt(d, need, str(mk.get("mid")))
                _col_alert("AQUÍ NO SE VENDE NADA DE LO QUE FALTA",
                           (f"prueba en {alt[0]} ({', '.join(alt[1][:3])})" if alt else (mk.get("station") or "") + " · mercado del juego"), RED)

_render_b14 = render

def render(surf):
    r_ = _render_b14(surf)
    try:
        with lock:
            d, rx = state["data"], state["rx"]
        if d is not None and time.time() - rx < 5:
            colbuy_watch(d, time.time())
    except Exception as e:
        log_exc("colonia compra", e)
    return r_

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 13''', '''# Novedades v1.0 beta 14
- Aviso de compra para tu construcción: al pedir atraque, si esa estación no vende nada de lo que te falta (según EDSM), «ESTA ESTACIÓN NO VENDE NADA DE LO QUE TE FALTA» y dónde probar en el sistema; si vende algo, «AQUÍ HAY N DE LO QUE TE FALTA». Al abrir el mercado se confirma con los datos del juego. Se apaga en ALERTAS. Necesita el sender v1.0b10.
- COLONIZACIÓN > EN EL SISTEMA: ya no se montan los textos de abajo; los datos de EDSM de más de 30 días salen en gris como DATO ANTIGUO (y se prefiere uno reciente si lo hay).
- EN VIVO: el nombre de la nave en azul, como el del copiloto.
# Novedades v1.0 beta 13''')
rep('    ("1.0b13", ', '    ("1.0b14", "Aviso de compra para tu construcción, EN EL SISTEMA sin solapes y con datos antiguos, nombre de la nave en azul"),\n    ("1.0b13", ')
s = re.sub(r'PANEL_VER = "v1\.0b13 [^"]*"', 'PANEL_VER = "v1.0b14 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 14  (copia en " + P + ".bak100b13)")
