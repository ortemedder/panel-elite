#!/usr/bin/env python3
"""Paso 2b-3: cada cadena de envoltorios (x__1, x__2, ..., x) queda junta y con nombres que dicen de que parche es:
x_base, x_b3, x_b6, ..., y la final `x`. Los alias (_x_b6 = x__5) desaparecen: cada etapa llama directamente a la
anterior por su nombre. Si al importar nadie usa las etapas (solo los alias), la cadena entera se mueve junta al final
con un indice; si no, se renombra en su sitio. No cambia lo que hace el panel.
Uso: python3 herramientas/juntar_cadenas.py entrada.py salida.py"""
import ast, re, sys
from collections import defaultdict

def cadenas(T):
    vers = defaultdict(dict)
    for n in T.body:
        if isinstance(n, ast.FunctionDef):
            m = re.fullmatch(r"(.+)__(\d+)", n.name)
            if m:
                vers[m.group(1)][int(m.group(2))] = n.name
    return vers

def main(src, dst):
    texto = open(src, encoding="utf-8").read()
    T = ast.parse(texto)
    final = {n.name for n in T.body if isinstance(n, ast.FunctionDef)}
    resumen = []
    for base_name, vs in sorted(cadenas(T).items()):
        if base_name not in final:
            continue
        T = ast.parse(texto)
        orden = [vs[k] for k in sorted(vs)] + [base_name]
        # alias: X = etapa (a nivel de modulo)
        alias = {}
        for n in T.body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) \
                    and n.targets[0].id.startswith("_") and isinstance(n.value, ast.Name) and n.value.id in orden[:-1]:
                alias[n.targets[0].id] = (n.value.id, n)
        # nombre nuevo de cada etapa: por el alias que llama (de que parche es)
        defs = {n.name: n for n in T.body if isinstance(n, ast.FunctionDef) and n.name in orden}
        nuevo = {orden[0]: f"{base_name}_base"}
        for st in orden[1:-1]:
            usa = [x.id for x in ast.walk(defs[st]) if isinstance(x, ast.Name) and x.id in alias]
            tag = re.sub(r"^_+", "", usa[0]) if usa else st.split("__")[1]
            tag = tag.replace(base_name, "").strip("_") or st.split("__")[1]
            cand = f"{base_name}_{tag}"
            while cand in nuevo.values() or cand in final:
                cand += "x"
            nuevo[st] = cand
        if len(set(nuevo.values())) != len(nuevo):
            continue
        # sustituciones: alias -> etapa nueva; etapa vieja -> nombre nuevo
        reemp = {a: nuevo[v] for a, (v, _) in alias.items()}
        reemp.update(nuevo)
        # ¿alguien usa las etapas al importar (fuera de los alias)?
        usos_import = False
        for n in T.body:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                continue
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in alias:
                continue
            if any(isinstance(x, ast.Name) and x.id in reemp for x in ast.walk(n)):
                usos_import = True
        L = texto.split("\n")
        borrar = set()
        for a, (v, n) in alias.items():
            borrar.update(range(n.lineno - 1, n.end_lineno))
        bloques = []
        if not usos_import:
            for st in orden:
                n = defs[st]
                bloques.append("\n".join(L[n.lineno - 1:n.end_lineno]))
                borrar.update(range(n.lineno - 1, n.end_lineno))
        L = [l for k, l in enumerate(L) if k not in borrar]
        texto = "\n".join(L)
        if bloques:
            idx = " -> ".join([nuevo.get(s, s) for s in orden])
            bloque = (f"\n\n# ========== {base_name}: cadena de {len(orden)} etapas, cada una llama a la anterior ==========\n"
                      f"# {idx}\n\n" + "\n\n".join(bloques) + "\n")
            i = texto.rindex('\nif __name__ == "__main__":')
            texto = texto[:i] + bloque + texto[i:]
        for viejo in sorted(reemp, key=len, reverse=True):
            texto = re.sub(r"(?<![\w.])" + re.escape(viejo) + r"(?!\w)", reemp[viejo], texto)
        resumen.append(f"{base_name} ({len(orden)}{', junta al final' if bloques else ''})")
    open(dst, "w", encoding="utf-8").write(texto)
    print("Cadenas ordenadas: " + ", ".join(resumen))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
