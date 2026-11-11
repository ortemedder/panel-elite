#!/usr/bin/env python3
"""Paso 2a: quita las versiones de funciones que ya no se usan nunca (las tapa una definicion posterior y nadie
guardo una referencia a la vieja mientras existia). No cambia lo que hace el panel.
Uso: python3 herramientas/limpiar_muertas.py entrada.py salida.py"""
import ast, sys

def cargas_modulo(nodo, nombre):
    """True si a nivel de modulo (ejecutado al importar) se usa `nombre` como valor o se llama."""
    pila = [nodo]
    while pila:
        n = pila.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            if isinstance(n, ast.ClassDef):
                pila.extend(n.body)                     # el cuerpo de una clase si se ejecuta al importar
            else:
                pila.extend(getattr(n, "decorator_list", []) + list(getattr(n.args, "defaults", [])) if hasattr(n, "args") else [])
            continue
        if isinstance(n, ast.Name) and n.id == nombre and isinstance(n.ctx, ast.Load):
            return True
        pila.extend(ast.iter_child_nodes(n))
    return False

def main(src, dst):
    texto = open(src, encoding="utf-8").read()
    arbol = ast.parse(texto)
    cuerpo = arbol.body
    defs = {}
    for i, n in enumerate(cuerpo):
        if isinstance(n, ast.FunctionDef):
            defs.setdefault(n.name, []).append(i)
    quitar = []
    for nombre, idx in defs.items():
        for a, b in zip(idx, idx[1:]):
            if not any(cargas_modulo(cuerpo[k], nombre) for k in range(a + 1, b)):
                quitar.append(cuerpo[a])
    lineas = texto.split("\n")
    borrar = set()
    for n in quitar:
        for l in range(n.lineno - 1 - len(n.decorator_list), n.end_lineno):
            borrar.add(l)
    salida = [l for k, l in enumerate(lineas) if k not in borrar]
    open(dst, "w", encoding="utf-8").write("\n".join(salida))
    print(f"Quitadas {len(quitar)} versiones muertas ({len(borrar)} líneas): " + ", ".join(sorted({n.name for n in quitar})))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
