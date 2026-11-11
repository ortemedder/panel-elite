#!/usr/bin/env python3
"""Paso 2b-2: ninguna funcion definida dos veces. Cada version anterior pasa a llamarse nombre__1, nombre__2...
y las referencias que se hacian a ella al importar (alias _x_bN = x, VIEWS[...] = x) apuntan a ese nombre.
Las llamadas dentro de las funciones siguen usando `nombre` (la ultima version), como antes: no cambia nada.
Despues quita las versiones que solo quedaban apuntadas en VIEWS y se sobrescribian mas abajo.
Uso: python3 herramientas/nombres_unicos.py entrada.py salida.py"""
import ast, re, sys
from collections import defaultdict

def renombrar(texto):
    T = ast.parse(texto); L = texto.split("\n")
    defs = defaultdict(list)
    for i, n in enumerate(T.body):
        if isinstance(n, ast.FunctionDef):
            defs[n.name].append(i)
    cambios = []                                         # (linea, col, largo, nuevo)
    total = 0
    for name, idx in defs.items():
        if len(idx) < 2:
            continue
        for v, (a, b) in enumerate(zip(idx, idx[1:]), 1):
            nuevo = f"{name}__{v}"
            n = T.body[a]
            col = L[n.lineno - 1].index("def " + name + "(") + 4
            cambios.append((n.lineno - 1, col, len(name), nuevo))
            for k in range(a + 1, b):                    # lo que se ejecuta al importar entre esta version y la siguiente
                st = T.body[k]
                if isinstance(st, (ast.FunctionDef, ast.ClassDef)):
                    continue
                if isinstance(st, ast.Assign) and any(isinstance(tg, ast.Name) and tg.id == name for tg in st.targets):
                    break                                # x = otra_funcion: desde aqui x ya no es esta version
                pila = [st]
                while pila:
                    x = pila.pop()
                    if isinstance(x, ast.Lambda):
                        continue                         # una lambda se ejecuta luego: usa la ultima version
                    if isinstance(x, ast.Name) and x.id == name and isinstance(x.ctx, ast.Load):
                        cambios.append((x.lineno - 1, x.col_offset, len(name), nuevo))
                    pila.extend(ast.iter_child_nodes(x))
            total += 1
    for ln, col, ln_, nuevo in sorted(cambios, key=lambda c: (c[0], -c[1])):
        L[ln] = L[ln][:col] + nuevo + L[ln][col + ln_:]
    return "\n".join(L), total

def quitar_views_tapadas(texto):
    """Funciones nombre__k que solo se usan como VIEWS[K] = ... (o en el dict VIEWS = {...}) y luego se sobrescriben."""
    quitadas = []
    while True:
        T = ast.parse(texto); L = texto.split("\n")
        asign = []                                       # (orden, clave, nombre, nodo)
        for i, st in enumerate(T.body):
            if isinstance(st, ast.Assign):
                for tg in st.targets:
                    if isinstance(tg, ast.Subscript) and isinstance(tg.value, ast.Name) and tg.value.id == "VIEWS":
                        k = tg.slice.value if isinstance(tg.slice, ast.Constant) else None
                        if isinstance(st.value, ast.Name):
                            asign.append((i, k, st.value.id, st))
                if any(isinstance(tg, ast.Name) and tg.id == "VIEWS" for tg in st.targets) and isinstance(st.value, ast.Dict):
                    for kk, vv in zip(st.value.keys, st.value.values):
                        if isinstance(kk, ast.Constant) and isinstance(vv, ast.Name):
                            asign.append((i, kk.value, vv.id, None))
        lect = []                                        # (orden, clave) de cada lectura VIEWS[K] al importar
        for i, st in enumerate(T.body):
            if isinstance(st, (ast.FunctionDef, ast.ClassDef)):
                continue
            for x in ast.walk(st):
                if isinstance(x, ast.Subscript) and isinstance(x.value, ast.Name) and x.value.id == "VIEWS" \
                        and isinstance(x.ctx, ast.Load) and isinstance(x.slice, ast.Constant):
                    lect.append((i, x.slice.value))
        uso = defaultdict(int)
        for x in ast.walk(T):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                uso[x.id] += 1
        objetivo = None
        for i, k, nm, st in asign:
            if "__" not in nm or k is None:
                continue
            sig = min([j for j, kk, _, _ in asign if j > i and kk == k] or [None]) if any(j > i and kk == k for j, kk, _, _ in asign) else None
            tapada = sig is not None and not any(i <= j2 < sig and k2 == k for j2, k2 in lect)
            refs_views = sum(1 for _, _, n2, _ in asign if n2 == nm)
            if tapada and uso[nm] == refs_views:
                objetivo = nm; break
        if not objetivo:
            return texto, quitadas
        fn = next(n for n in T.body if isinstance(n, ast.FunctionDef) and n.name == objetivo)
        borrar = set(range(fn.lineno - 1, fn.end_lineno))
        for i, k, nm, st in asign:
            if nm == objetivo and st is not None and st.lineno == st.end_lineno and len(st.targets) == 1:
                borrar.add(st.lineno - 1)
        L = [l for j, l in enumerate(L) if j not in borrar]
        texto = "\n".join(L)
        # en el dict VIEWS = {...} la entrada queda en None (mismo orden de claves); mas abajo se le pone la buena
        texto = re.sub(r"(\d+): %s\b" % re.escape(objetivo), lambda m: f"{m.group(1)}: None", texto)
        quitadas.append(objetivo)

if __name__ == "__main__":
    t = open(sys.argv[1], encoding="utf-8").read()
    t, n = renombrar(t)
    t, q = quitar_views_tapadas(t)
    open(sys.argv[2], "w", encoding="utf-8").write(t)
    print(f"{n} versiones renombradas (nombre__N); {len(q)} quitadas por estar tapadas en VIEWS: {', '.join(q)}")
