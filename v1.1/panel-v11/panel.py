#!/usr/bin/env python3
# Panel Elite v1.1 · el codigo esta en partes/ y se carga en orden (00, 01, ...) en un solo espacio de nombres,
# exactamente como si fuera un unico archivo. Cada parte se puede leer y editar por separado.
# v1.1.1: cada parte compilada se guarda en partes/__cache__ y el siguiente arranque la usa directamente
# (se vuelve a compilar sola si la parte cambia o cambia la version de Python).
import os as _os, sys as _sys, marshal as _marshal
_PARTES = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "partes")
_CACHE = _os.path.join(_PARTES, "__cache__")

def _cargar_parte(_ruta):
    _st = _os.stat(_ruta)
    _clave = f"{_st.st_mtime_ns}-{_st.st_size}-{_sys.version_info[0]}.{_sys.version_info[1]}".encode()
    _cf = _os.path.join(_CACHE, _os.path.basename(_ruta) + ".bin")
    try:
        with open(_cf, "rb") as _fh:
            _cab, _bloque = _fh.read().split(b"\n", 1)
        if _cab == _clave:
            return _marshal.loads(_bloque)
    except (OSError, ValueError, EOFError, TypeError):
        pass
    with open(_ruta, encoding="utf-8") as _fh:
        _code = compile(_fh.read(), _ruta, "exec")
    try:
        _os.makedirs(_CACHE, exist_ok=True)
        with open(_cf + ".tmp", "wb") as _fh:
            _fh.write(_clave + b"\n" + _marshal.dumps(_code))
        _os.replace(_cf + ".tmp", _cf)
    except OSError:
        pass
    return _code

for _f in sorted(x for x in _os.listdir(_PARTES) if x.endswith(".py") and x[:2].isdigit()):
    exec(_cargar_parte(_os.path.join(_PARTES, _f)), globals())

if __name__ == "__main__":
    main()
