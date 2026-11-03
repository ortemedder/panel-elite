import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak44")
s = open(p, encoding="utf-8").read()
if "def view_changelog" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- 12.4.5 versiones: resumen de cambios ----------
CHANGES = [
    ("base", "Panel de 12 botones, teclado USB y estado del juego por red"),
    ("base", "7.3 Xenobiología: muestras, distancia, valor de especies y x5"),
    ("base", "Recogida de combustible en naranja y sobrecalentamiento"),
    ("base", "Brújula para volver a la nave"),
    ("base", "EN VIVO como inicio (nave/a pie/SRV) con botón MENÚ"),
    ("base", "7.1 Exploración con EDSM y páginas"),
    ("base", "Avisos: combustible en ruta, neutrones y gravedad"),
    ("base", "12.5 Materiales, 12.6 Portanaves y 12.7 Mercado"),
    ("0.10", "Versión en la pantalla del reloj"),
    ("0.11", "12.8 Notas de viaje con brújula al destino"),
    ("0.12", "Foto del CMDR en reloj y arranque"),
    ("0.13", "Estilo CABINA (botón ESTILO en Sesión)"),
    ("0.14", "Botón ESTILO más grande"),
    ("0.15", "Pantalla grande HDMI: tablero de 4 cuadros"),
    ("0.16", "Viaje con SISTEMA y Combate con PIPS"),
    ("0.17", "Aproximación/Superficie y 7.4 Yacimientos"),
    ("0.18", "Tablero especial con el Rhino"),
    ("0.19", "Bodega del vehículo"),
    ("0.20", "Ficha del destino en Navegación"),
    ("0.21", "Altitud para desplegar el Rhino"),
    ("0.22", "RHINO en la pantalla 5"),
    ("0.23", "Pantalla 5: SRV / RHINO / A PIE"),
    ("0.24", "Lista de minerales de la bodega del Rhino"),
    ("0.25", "Combustible y escudos del Rhino"),
    ("0.26", "Superficie con Materiales y Minería"),
    ("0.27", "Minería en modo Rhino"),
    ("0.28", "Avisos de nave (el juego no los registra)"),
    ("0.29", "RHINO A BORDO"),
    ("0.30", "Franja RHINO PREPARADO"),
    ("0.31", "Franja de altura: 100-41 / 40-7 / <7 m"),
    ("0.32", "Brújula a puertos planetarios"),
    ("0.33", "Tablero ATRAQUE con la plataforma"),
    ("0.34", "Navegación: cara SISTEMA (política)"),
    ("0.35", "Estación: ficha y facciones a los 15 s"),
    ("0.36", "12.4 Salir, reiniciar y apagar"),
    ("0.37", "Navegación: cara POWERPLAY"),
    ("0.38", "Grande: 10 s sistema y 5 s Powerplay"),
    ("0.39", "Estación alterna ficha y Powerplay"),
    ("0.40", "Hallazgos, Códice, buscados, misiones, fin de sesión"),
    ("0.41", "A pie: peligros, mochila, asentamientos, delitos, taxi"),
    ("0.42", "Combate: escudos, derribos, bonos, rebuy, PvP"),
    ("0.43", "Ficha de llegada y sistema sin explorar"),
    ("0.44", "Esta lista de versiones"),
]

def view_changelog(surf, d, flags, now):
    per = 11
    rows = list(reversed(CHANGES))
    pages = max(1, (len(rows) + per - 1) // per)
    pg = ui.get("page1245", 0) % pages
    y = TOP + 4
    put(surf, F["small"], f"{len(CHANGES)} cambios  ·  lo más nuevo primero", (8, y), DIM)
    put(surf, F["small"], f"pág {pg + 1}/{pages}  (toca)", (W - 8, y), DIM, anchor="topright")
    y += 18
    for ver, txt in rows[pg * per:(pg + 1) * per]:
        put(surf, F["small"], "v" + ver if ver != "base" else "base", (8, y + 2), GREEN if ver != "base" else DIM)
        put(surf, F["btn"], txt, (62, y), ORANGE, W - 70)
        y += 22

'''
rep("def view_sub12", SNIP + "def view_sub12")
rep('("4", "PREFERENCIAS")]', '("4", "PREFERENCIAS"), ("5", "VERSIONES")]')
rep('draw_button(surf, grid(i, 2, 2), n, "¿SEGURO?" if sure', 'draw_button(surf, grid(i, 3, 2), n, "¿SEGURO?" if sure')
rep('''    if i == 3:
        ui["view"] = 1244; return''', '''    if i == 3:
        ui["view"] = 1244; return
    if i == 4:
        ui["view"] = 1245; return''')
s, n = re.subn(r'(for i in range\()4(\):\n\s+if grid\(i, )2, 2(\)\.collidepoint\(x, y\):\n\s+power_tap\(i\); return)', r'\g<1>5\g<2>3, 2\g<3>', s, count=1)
if not n: print("NO ENCONTRADO: toque del 12.4"); ok = False
rep("1244: 124", "1244: 124, 1245: 124")
rep('1244: "PREFERENCIAS"', '1244: "PREFERENCIAS", 1245: "VERSIONES"')
rep("1244: view_settings", "1244: view_settings, 1245: view_changelog")
L = s.split("\n")
t = next((i for i, l in enumerate(L) if l.strip() == "elif v == 71:"), None)
if t is None:
    print("NO ENCONTRADO: toque"); ok = False
else:
    ind = L[t][:len(L[t]) - len(L[t].lstrip())]
    L[t:t] = [ind + "elif v == 1245:", ind + "    ui['page1245'] = ui.get('page1245', 0) + 1; return"]
s = "\n".join(L)
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.44 · 29/10/2026 13:00"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
