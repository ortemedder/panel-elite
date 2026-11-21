# Panel Elite v1.1 · parte 18: el ROBOT como compañero de viaje (v1.1.9)
#   copiloto en ruta (saltos, combustible, siguiente estrella) · exploración sin vender si hay peligro
#   misiones a punto de caducar (1 h y 15 min) · descanso cada 2 h · resumen al atracar
#   ascensos y primer descubrimiento · llegada a un sistema de CDSN con su tendencia
#   se duerme en el menú del juego o con el juego cerrado
#   Todo va solo a la StackChan (no cambia nada en las pantallas del panel). Se quita uno a uno en ALERTAS.
EV_LIST.extend([("robcop", "ROBOT: COPILOTO EN RUTA"), ("robexplo", "ROBOT: DATOS SIN VENDER EN PELIGRO"),
                ("robmision", "ROBOT: MISIONES A PUNTO DE CADUCAR"), ("robdescanso", "ROBOT: DESCANSO CADA 2 H"),
                ("robresumen", "ROBOT: RESUMEN AL ATRACAR"), ("robhito", "ROBOT: ASCENSOS Y DESCUBRIMIENTOS"),
                ("robcdsn", "ROBOT: LLEGADA A SISTEMA CDSN"), ("robzzz", "ROBOT: DORMIR EN EL MENÚ"),
                ("robdock", "ROBOT: CUENTA ATRÁS DEL ATRAQUE"), ("robllegada", "ROBOT: LLEGADA AL DESTINO"),
                ("robnoche", "ROBOT: MODO NOCHE (23 A 8 H)")])

ROB = {"t": 0.0, "cop": "", "zzz": False, "pel": False, "explo_t": 0.0, "mis": set(), "rest": set(),
       "dock": None, "res_t": 0.0, "ranks": None, "fsys": set(), "first": None, "sys": None, "fin": False, "datq": -1, "dest": None, "noche": False}

def _mill(v):
    v = float(v or 0)
    if v >= 1e6:
        return f"{v / 1e6:.1f} M".replace(".", ",")
    return f"{v / 1e3:.0f} mil" if v >= 1e4 else f"{v:.0f}"

def _rob_say(ev, kind, titulo, dato):
    if cfg.get("stackchan") and ev_on(ev):
        sc_aviso_o_logo(ev, kind, titulo, dato)

def rob_cop(d):
    """Texto de copiloto mientras vuelas con ruta: saltos, combustible y la siguiente estrella."""
    route = d.get("route") or []
    n = d.get("routen") or len(route)
    if not n or not route or d.get("Flags", 0) & 1 or not ev_on("robcop"):
        return ""
    fuel, cap = (d.get("Fuel") or {}).get("FuelMain"), d.get("fuelcap")
    f_ = f" - comb {100 * fuel / cap:.0f}%" if fuel is not None and cap else ""
    k = star_kind(route[0][1])
    sig = {"neu": "NEUTRONES!", "wd": "ENANA BLANCA!"}.get(k) or ("recolectable" if star_ok(route[0][1]) else "no recolectable")
    return f"{n} salto{'s' if n != 1 else ''}{f_}\nsig: {sig}"

def rob_watch(now):
    if not cfg.get("stackchan") or now - ROB["t"] < 1:
        return
    ROB["t"] = now
    with lock:
        d, rx = state["data"], state["rx"]
    online = d is not None and now - rx < 60
    ROB["zzz"] = ev_on("robzzz") and (not online or bool((d or {}).get("menu")) or ROB["fin"])
    h_ = time.localtime().tm_hour
    ROB["noche"] = ev_on("robnoche") and (h_ >= 23 or h_ < 8)
    if not online:
        ROB["cop"] = ""; ROB["datq"] = -1; return
    pn = d.get("pcnow") or now
    ROB["cop"] = rob_cop(d)

    # cuenta atrás del atraque (el robot la lleva él solo segundo a segundo)
    left = dock_left(d, now) if ev_on("robdock") else None
    ROB["datq"] = int(left) if left is not None and left > 0 else -1

    # llegada al final de la ruta
    route = d.get("route") or []
    if route:
        ROB["dest"] = ((d.get("routeend") or route[-1]) or [None])[0]
    elif ROB["dest"]:
        if d.get("system") == ROB["dest"]:
            _rob_say("robllegada", "ok", "HEMOS LLEGADO!", ROB["dest"])
        ROB["dest"] = None

    # exploración y biología sin vender al empezar un peligro
    pel = bool(SC_PEL.get("on"))
    if pel and not ROB["pel"] and now - ROB["explo_t"] > 600:
        un = ((d.get("explo") or {}).get("unsold") or 0) + ((d.get("bio") or {}).get("unsold_cr") or 0)
        if un >= 1e6:
            ROB["explo_t"] = now
            _rob_say("robexplo", "alarm", "CUIDADO CON LOS DATOS", f"llevas {_mill(un)} cr sin vender")
    ROB["pel"] = pel

    # misiones a punto de caducar: avisa al bajar de 1 h y de 15 min
    for m in d.get("missions") or []:
        if len(m) < 3 or not m[2]:
            continue
        left = m[2] - pn
        th = 900 if left <= 900 else 3600 if left <= 3600 else None
        if left > 0 and th and (m[0], m[2], th) not in ROB["mis"]:
            ROB["mis"].update({(m[0], m[2], th), (m[0], m[2], 3600)})     # al bajar de 15 min ya no avisa la de 1 h
            _rob_say("robmision", "alarm", "MISION CADUCA PRONTO", f"quedan {int(left // 60)} min: {m[0][:34]}")

    # descanso cada 2 h de juego seguido
    se = d.get("sess") or {}
    seg = se.get("seg")
    if seg:
        k = int((pn - seg) // 7200)
        if k >= 1 and (seg, k) not in ROB["rest"]:
            ROB["rest"].add((seg, k))
            _rob_say("robdescanso", "ok", f"LLEVAS {2 * k} H JUGANDO", "estira las piernas y bebe agua")

    # resumen de la partida al atracar (como mucho cada 30 min)
    dock = bool(d.get("Flags", 0) & 1)
    if dock and ROB["dock"] is False and now - ROB["res_t"] > 1800:
        sn = se.get("snap") or {}
        e0, ea = sn.get("earn") or {}, se.get("earn") or {}
        earn = sum(ea.get(k, 0) - e0.get(k, 0) for k in ea)
        j, ly = se.get("jumps", 0) - sn.get("jumps", 0), se.get("ly", 0) - sn.get("ly", 0)
        if j > 0 or earn > 0:
            ROB["res_t"] = now
            _rob_say("robresumen", "ok", "RESUMEN DE LA PARTIDA",
                     f"{j} saltos - {ly:.0f} al - +{_mill(earn)} cr".replace(".", ","))
    ROB["dock"] = dock

    # ascensos
    rk = dict((d.get("ranks") or {}).get("rank") or {})
    if rk:
        if ROB["ranks"]:
            for key, n in rk.items():
                o = ROB["ranks"].get(key)
                if isinstance(n, int) and isinstance(o, int) and n > o and key in RANK_NAMES:
                    lab = dict((b, a) for a, b in RANK_ROWS).get(key, key)
                    _rob_say("robhito", "ok", "ASCENSO!", f"{lab}: {rank_name(key, n)}")
        ROB["ranks"] = rk

    # primer descubrimiento (una vez por sistema)
    fi = (d.get("exdiary") or {}).get("first")
    sy = d.get("system")
    if isinstance(fi, int):
        if ROB["first"] is not None and fi > ROB["first"] and sy and sy not in ROB["fsys"]:
            ROB["fsys"].add(sy)
            _rob_say("robhito", "ok", "PRIMER DESCUBRIMIENTO!", f"nadie habia estado en {sy}")
        ROB["first"] = fi

    # llegada a un sistema de CDSN (las guerras, elecciones y retiradas ya las avisa la ruta)
    if sy and sy != ROB["sys"]:
        if ROB["sys"] is not None:
            v = ((FACD["data"] or {}).get("sistemas") or {}).get(sy)
            st_ = ((v or {}).get("activos") or []) + ((v or {}).get("pendientes") or [])
            if v and not v.get("fuera") and v.get("inf") and not fac_war(v) and "Retreat" not in st_ and "Election" not in st_:
                t_ = _trend(v)
                inf = f"{v['inf']:.1f} %".replace(".", ",")
                if t_ <= -0.1:
                    _rob_say("robcdsn", "alarm", "SISTEMA CDSN", f"{sy}: {inf}, bajando")
                else:
                    _rob_say("robcdsn", "ok", "SISTEMA CDSN", f"{sy}: {inf}" + (", subiendo" if t_ >= 0.1 else ", estable"))
        ROB["sys"] = sy

_render_v119 = render

def render(surf):
    r_ = _render_v119(surf)
    try:
        rob_watch(time.time())
    except Exception as e:
        log_exc("robot", e)
    return r_

_sc_send_v119b = sc_send

def sc_send(obj):
    if obj.get("t") == "hola":
        obj = dict(obj, cop=ROB["cop"], zzz=ROB["zzz"], datq=ROB["datq"], noche=ROB["noche"])
    return _sc_send_v119b(obj)

# fin de sesión (al salir al menú o cerrar el juego): el robot se duerme hasta que cargues otra partida
_handle_note_v119b = handle_note

def handle_note(kind, text):
    if kind == "sessend":
        ROB["fin"] = True
    elif kind == "loadgame":
        ROB["fin"] = False
    return _handle_note_v119b(kind, text)
