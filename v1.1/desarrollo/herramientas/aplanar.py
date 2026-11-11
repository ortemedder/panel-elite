#!/usr/bin/env python3
"""Paso 2b: aplana una cadena de envoltorios. Quita todas las versiones de `nombre` menos la primera (que pasa a
llamarse `base`), quita las lineas `_nombre_bN = nombre` y añade al final la version unica que se le pase.
Uso (desde otro script): aplanar(texto, nombre, base, codigo_nuevo) -> texto"""
import ast, re

def aplanar(texto, nombre, base, codigo):
    arbol = ast.parse(texto)
    defs = [n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == nombre]
    alias = [n for n in arbol.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id == nombre
             and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and re.match(r"_" + nombre + r"_", n.targets[0].id)]
    lineas = texto.split("\n")
    borrar = set()
    for n in defs[1:] + alias:
        borrar.update(range(n.lineno - 1, n.end_lineno))
    l0 = defs[0].lineno - 1
    lineas[l0] = lineas[l0].replace(f"def {nombre}(", f"def {base}(", 1)
    out = [l for k, l in enumerate(lineas) if k not in borrar]
    texto = "\n".join(out)
    marca = '\nif __name__ == "__main__":'
    i = texto.rindex(marca)
    return texto[:i] + "\n" + codigo.strip("\n") + "\n\n" + texto[i:]
