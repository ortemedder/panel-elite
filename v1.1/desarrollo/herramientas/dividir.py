#!/usr/bin/env python3
"""Paso 3: divide panel.py en partes/NN_nombre.py (en el mismo orden) y deja un panel.py pequeño que las carga
todas en el mismo espacio de nombres. Se ejecuta exactamente lo mismo, en el mismo orden: no cambia nada.
Uso: python3 herramientas/dividir.py panel_entero.py carpeta_destino"""
import ast, os, re, sys

PARTES = [  # (linea donde empieza aprox., nombre) — se ajusta a la primera instruccion de nivel superior
    (1, "inicio_y_menus"), (372, "red_y_tactil"), (726, "exploracion"), (1804, "navegacion_y_versiones"),
    (2542, "ajustes_y_espera"), (3317, "pantalla_grande"), (3749, "galnet_objetivos_y_voz"),
    (5569, "alertas_y_combate"), (6574, "v092_a_v099"), (8268, "faccion"), (9047, "radar_colonizacion_viajes"),
    (9814, "relojes_altimetro_velocidad"), (10564, "avisos_y_modo_pantalla"), (10806, "cadenas"),
]

LOADER = '''#!/usr/bin/env python3
# Panel Elite v1.1 · el codigo esta en partes/ y se carga en orden (00, 01, ...) en un solo espacio de nombres,
# exactamente como si fuera un unico archivo. Cada parte se puede leer y editar por separado.
import os as _os
_PARTES = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "partes")
for _f in sorted(x for x in _os.listdir(_PARTES) if x.endswith(".py") and x[:2].isdigit()):
    _ruta = _os.path.join(_PARTES, _f)
    with open(_ruta, encoding="utf-8") as _fh:
        exec(compile(_fh.read(), _ruta, "exec"), globals())
'''

def main(src, dst):
    texto = open(src, encoding="utf-8").read()
    L = texto.split("\\n") if False else texto.split("\n")
    T = ast.parse(texto)
    rangos = [(n.lineno - (len(n.decorator_list) if hasattr(n, "decorator_list") else 0), n.end_lineno) for n in T.body]
    def dentro(ln):
        return any(a < ln <= b for a, b in rangos)
    cortes = []
    for ln, nombre in PARTES:
        x = ln
        while dentro(x):
            x += 1
        cortes.append((x, nombre))
    os.makedirs(os.path.join(dst, "partes"), exist_ok=True)
    for i, (ln, nombre) in enumerate(cortes):
        fin = cortes[i + 1][0] - 1 if i + 1 < len(cortes) else len(L)
        trozo = "\n".join(L[ln - 1:fin])
        cab = f"# Panel Elite v1.1 · parte {i:02d}: {nombre.replace('_', ' ')} (lineas {ln}-{fin} del panel entero)\n"
        open(os.path.join(dst, "partes", f"{i:02d}_{nombre}.py"), "w", encoding="utf-8").write(cab + trozo + "\n")
        print(f"{i:02d}_{nombre}.py  {fin - ln + 1:5d} lineas")
    open(os.path.join(dst, "panel.py"), "w", encoding="utf-8").write(LOADER)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
