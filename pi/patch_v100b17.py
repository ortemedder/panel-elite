#!/usr/bin/env python3
# Parche v1.0 beta 17 (desde la beta 16b): fotos de fondo del atraque mas brillantes (55 -> 75), COMBATE ya no se abre
# al despegar por la musica, y avisos de colonizacion con «MATERIALES DE COLONIZACION».
import os, re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/panel.py")
s = open(P, encoding="utf-8").read()
if "def combat_music_ok" in s:
    sys.exit("Ya estaba aplicado")
if not re.search(r'PANEL_VER = "v1\.0b16b', s):
    sys.exit("Este parche es para la v1.0 beta 16b")
shutil.copy(P, P + ".bak100b16b")

def rep(old, new, n=1):
    global s
    if s.count(old) != n:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

# 1) fondo del atraque mas claro (antes 55; para volver atras, poner 55)
rep('''    carrier_bg(surf, d or {}, st, dark=55, label=False)''', '''    carrier_bg(surf, d or {}, st, dark=BG_DOCK_DARK, label=False)''')
# 3) textos de los avisos de colonizacion
rep('''                    _col_alert(f"AQUÍ HAY {len(have)} DE LO QUE TE FALTA", ", ".join(have[:3]) + ("…" if len(have) > 3 else "") + f" · {B.get('st')}", GREEN)''',
    '''                    _col_alert(f"AQUÍ HAY {len(have)} MATERIAL{'ES' if len(have) != 1 else ''} DE COLONIZACIÓN",
                               ", ".join(have[:3]) + ("…" if len(have) > 3 else "") + f" · {B.get('st')}", GREEN)''')
rep('''                    _col_alert("ESTA ESTACIÓN NO VENDE NADA DE LO QUE TE FALTA",
                               (f"prueba en {alt[0]} ({', '.join(alt[1][:3])})" if alt else f"{B.get('st')} · para tu construcción"),
                               RED, "esta estación no vende nada de lo que te falta")''',
    '''                    _col_alert("ESTA ESTACIÓN NO TIENE MATERIALES DE COLONIZACIÓN",
                               (f"prueba en {alt[0]} ({', '.join(alt[1][:3])})" if alt else f"{B.get('st')} · para tu construcción"),
                               RED, "esta estación no tiene materiales de colonización")''')
rep('''            if not any(t_[0].lower() in here for t_ in need):
                alt = _col_alt(d, need, str(mk.get("mid")))
                _col_alert("AQUÍ NO SE VENDE NADA DE LO QUE FALTA",''', '''            if not any(_hh(here, t_[0], t_[1]) is not None for t_ in need):
                alt = _col_alt(d, need, str(mk.get("mid")))
                _col_alert("AQUÍ NO HAY MATERIALES DE COLONIZACIÓN",''')

CODE = r'''
# ---------- v1.0 beta 17 ----------
BG_DOCK_DARK = 75                                        # brillo de la foto de fondo al atracar (antes 55)

# --- COMBATE por la musica: no al despegar ni dentro de la estacion; «Combat_Unknown» solo si hay pelea de verdad ---
CMB = {"att": 0}

def combat_music_ok(text):
    d = state.get("data") or {}
    now = time.time()
    x = d.get("exitst") or {}
    if x.get("t0") and (not x.get("out") or pc_now(d, now) - x["t0"] < 60):
        return False, "dentro de la estación o recién despegado"
    st = d.get("station") or {}
    if st.get("status") in ("SOLICITADO", "CONCEDIDO", "ATRACADO") or d.get("Flags", 0) & 1:
        return False, "atracando o atracado"
    if text == "Combat_Unknown" and now - CMB["att"] > 60 and not d.get("Flags", 0) & (1 << 6):
        return False, "Combat_Unknown sin ataque ni armas fuera"
    return True, ""

_handle_note_b17 = handle_note

def handle_note(kind, text):
    if kind == "underattack":
        CMB["att"] = time.time()
    if kind == "combatmusic":
        ok, why = combat_music_ok(text)
        if not ok:
            plog(f"Música de combate ({text}) sin abrir COMBATE: {why}")
            return
    _handle_note_b17(kind, text)

'''
rep("\nif __name__ == \"__main__\":", CODE + "\nif __name__ == \"__main__\":")
rep('''# Novedades v1.0 beta 16b''', '''# Novedades v1.0 beta 17
- Fotos de fondo al atracar y aterrizar más claras (oscurecido 75 en lugar de 55).
- COMBATE ya no se abre al despegar: se ignora la música de combate dentro de la estación, durante el primer minuto tras despegar y mientras atracas; la música «Combat_Unknown» solo lo abre si te atacan o sacas las armas. En el LOG queda apuntado cuándo se ignora.
- Avisos de colonización: «AQUÍ HAY N MATERIALES DE COLONIZACIÓN» y «ESTA ESTACIÓN NO TIENE MATERIALES DE COLONIZACIÓN» (o «AQUÍ NO HAY…» al abrir el mercado).
# Novedades v1.0 beta 16b''')
rep('    ("1.0b16b", ', '    ("1.0b17", "Fondo del atraque más claro, COMBATE no se abre al despegar, avisos de materiales de colonización"),\n    ("1.0b16b", ')
s = re.sub(r'PANEL_VER = "v1\.0b16b[^"]*"', 'PANEL_VER = "v1.0b17 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v1.0 beta 17  (copia en " + P + ".bak100b16b)")
