#!/usr/bin/env python3
# Panel Elite v1.1 · el codigo esta en partes/ y se carga en orden (00, 01, ...) en un solo espacio de nombres,
# exactamente como si fuera un unico archivo. Cada parte se puede leer y editar por separado.
import os as _os
_PARTES = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "partes")
for _f in sorted(x for x in _os.listdir(_PARTES) if x.endswith(".py") and x[:2].isdigit()):
    _ruta = _os.path.join(_PARTES, _f)
    with open(_ruta, encoding="utf-8") as _fh:
        exec(compile(_fh.read(), _ruta, "exec"), globals())

if __name__ == "__main__":
    main()
