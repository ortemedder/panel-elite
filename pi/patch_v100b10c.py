#!/usr/bin/env python3
# Parche v1.0 beta 10c (desde la beta 10b): el estado del flujo de datos EDDN (escucha) pasa a AJUSTES > OPCIONES
# (boton FLUJO DATOS EDDN, el que faltaba) y muestra la hora real de la ultima subida a GitHub.
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def gh_loop" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b10b', s):
    sys.exit("Este parche es para la v1.0 beta 10b")
shutil.copy(P, P + ".bak100b10b")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

CODE = r'''
# ---------- v1.0 beta 10c: FLUJO DATOS EDDN en AJUSTES > OPCIONES, con la ultima subida a GitHub ----------
GH = {"t": 0, "err": ""}

def gh_loop():
    """Hora del ultimo commit de faccion.json en GitHub (API publica, cada 10 min)."""
    import urllib.request, datetime
    while True:
        try:
            url = FAC_URL
            try:
                url = open(os.path.join(PANEL_DIR, "faccion_url.txt")).read().strip() or url
            except OSError:
                pass
            m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)", url)
            if m:
                own, repo, br, path = m.groups()
                api = f"https://api.github.com/repos/{own}/{repo}/commits?path={path}&sha={br}&per_page=1"
                req = urllib.request.Request(api, headers={"User-Agent": "PanelEliteRPi/1.0", "Accept": "application/vnd.github+json"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    j = json.loads(r.read().decode("utf-8"))
                dt = j[0]["commit"]["committer"]["date"]
                GH.update(t=datetime.datetime.fromisoformat(dt.replace("Z", "+00:00")).timestamp(), err="")
        except Exception as e:
            GH["err"] = str(e)[:50]
        time.sleep(600)

threading.Thread(target=gh_loop, daemon=True, name="github").start()

def _hace(sec):
    return "?" if sec is None else f"{max(0, int(sec // 60))} min" if sec < 3600 else f"{sec / 3600:.0f} h" if sec < 172800 else f"{sec / 86400:.0f} días"

def pueblo_estado(now):
    D = FACD["data"] or {}
    e = D.get("eddn") or {}
    if not D:
        return "SIN DATOS", RED, "no se ha podido descargar faccion.json " + (FACD["err"] or "")
    sub_t = GH["t"] or D.get("t") or 0
    age = now - sub_t if sub_t else None
    ok = bool(e.get("ok")) and age is not None and age < 7 * 3600     # sube cada 15 min si cambia, y cada 6 h siempre
    sub = ("OK · " if ok else "¡OJO! · ") + _hace(age)
    det = (f"EDDN {'conectado' if e.get('ok') else 'DESCONECTADO'} · {e.get('msgs', 0):,} mensajes".replace(",", ".")
           + f" · subido a GitHub hace {_hace(age)}" + ("" if GH["t"] else " (aprox.)")
           + (f" · bajado aquí hace {_hace(now - FACD['t'])}" if FACD.get("t") else ""))
    return sub, GREEN if ok else RED, det

PUEBLO_R = grid(11, 4, 3)
_view_settings_b10c = VIEWS[1244]

def view_settings_b10c(surf, d, flags, now):
    _view_settings_b10c(surf, d, flags, now)
    sub, col, det = pueblo_estado(now)
    r = PUEBLO_R
    ok = col == GREEN
    lit = flash.get(("pueblo",), 0) > now
    pygame.draw.rect(surf, WHITE if lit else ORANGE if ok else BLACK, r, border_radius=6)
    pygame.draw.rect(surf, ORANGE if ok else RED, r, 2, border_radius=6)
    tc = BLACK if ok or lit else ORANGE
    put(surf, F["small"], "FLUJO DATOS", (r.centerx, r.centery - 20), tc, r.w - 8, anchor="center")
    put(surf, F["small"], "EDDN", (r.centerx, r.centery - 5), tc, r.w - 8, anchor="center")
    put(surf, F["small"], sub, (r.centerx, r.centery + 16), BLACK if ok or lit else RED, r.w - 8, anchor="center")

VIEWS[1244] = view_settings_b10c

_on_tap_b10c = on_tap

def on_tap(x, y):
    if ui.get("view") == 1244 and not ui.get("idle_on") and PUEBLO_R.collidepoint(x, y):
        tap_flash(("pueblo",))
        sub, col, det = pueblo_estado(time.time())
        set_alert("FLUJO DATOS EDDN", det, col, 7, kind="info"); TAP_EV.set(); return
    _on_tap_b10c(x, y)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''- AJUSTES (menú 12 > 4): botón 8 PUEBLO con el estado del escucha (OK y hace cuánto llegaron datos). Tocarlo da el detalle.''',
    '''- (10c) AJUSTES > OPCIONES: botón FLUJO DATOS EDDN con el estado del escucha (OK y hace cuánto se subió a GitHub; en rojo si lleva más de 7 h sin subir o EDDN está desconectado). Tocarlo da el detalle.''')
rep('    ("1.0b10b", ', '    ("1.0b10c", "FLUJO DATOS EDDN en AJUSTES > OPCIONES, con la última subida a GitHub"),\n    ("1.0b10b", ')
s = re.sub(r'PANEL_VER = "v1\.0b10b[^"]*"', 'PANEL_VER = "v1.0b10c · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 10c  (copia en " + P + ".bak100b10b)")
