# Panel Elite v2.3 · parte 64: v2.3b — arreglos de la v2.3 (log de Operations del 24/11)
#   - COMBATE EN ANILLOS: con las armas fuera en un anillo salía APROXIMACIÓN hasta la música de combate o el primer
#     «te atacan» (casi 1 min en una zona de combate de Operations). Ahora armas fuera en un anillo = COMBATE, salvo que
#     estés minando (prospectores, recolectores o refinado en los últimos 10 min): entonces sigue MINERÍA. Si te atacan
#     minando, COMBATE como siempre.
#   - MEGA NAVE (Operations): el contador de 15 min solo sale A PIE (o si ya lo has arrancado); en los combates con
#     nave no sale ni ocupa la esquina de los toques.

_big_mode_base_v23b = _big_mode_base

def _big_mode_base(d, flags):
    m = _big_mode_base_v23b(d, flags)
    d = d or {}
    if m == "APROXIMACIÓN" and (d.get("body") or "").endswith(" Ring") and hp_out(d, flags) \
            and not mining_active(d, time.time()):
        return "COMBATE"
    return m

def mega_ver(d):
    return MEGA["t0"] is not None or bool((d or {}).get("Flags2", 0) & 1)

_mega_left_v23b = mega_left

def mega_left(d, now):
    r = _mega_left_v23b(d, now)
    if r is False and not mega_ver(d):
        return None                                      # en espera y no estás a pie: no se enseña
    return r

_mega_rect_v23b = mega_rect

def mega_rect(w, h):
    with lock:
        d = state["data"]
    if ops_on(d) and not mega_ver(d):
        return pygame.Rect(0, 0, 0, 0)                   # sin cuadro: los toques de esa esquina van a lo de debajo
    return _mega_rect_v23b(w, h)
