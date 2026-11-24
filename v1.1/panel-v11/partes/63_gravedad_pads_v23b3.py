# Panel Elite v2.3 · parte 63: v2.3b3 — GRAVEDAD y PLATAFORMAS en la pantalla PLANETA (va con el sender v1.0b21)
#   - GRAVEDAD del planeta (del escaneo) en DESTINO: blanca, naranja desde 1,5 G y roja desde 2 G («BAJA DESPACIO»).
#     El aviso GRAVEDAD ALTA al acercarte ya existía (ALERTAS > GRAVEDAD ALTA).
#   - PLATAFORMAS del puerto de destino (S / M / L) y el tamaño de tu nave; «NO CABES» en rojo si no hay plataforma
#     para ella. El sender b21 manda las plataformas al atracar y el panel las guarda con el sitio (sitios_planeta.json):
#     se ven desde la segunda vez que vas a ese puerto.

SENDER_OK = SENDER_REQ = "v1.0b21"

NP_TALLA = (("cutter", "L"), ("corvette", "L"), ("anaconda", "L"), ("type-9", "L"), ("type 9", "L"), ("type9", "L"),
            ("type-10", "L"), ("type 10", "L"), ("type9_military", "L"), ("beluga", "L"), ("orca", "L"),
            ("clipper", "L"), ("type-7", "L"), ("type 7", "L"), ("type7", "L"), ("caspian", "L"), ("panther", "L"),
            ("python", "M"), ("krait", "M"), ("fer-de-lance", "M"), ("ferdelance", "M"), ("mamba", "M"),
            ("federal assault", "M"), ("federal dropship", "M"), ("federal gunship", "M"), ("federation_dropship", "M"),
            ("federation_gunship", "M"), ("type-8", "M"), ("type 8", "M"), ("type8", "M"), ("type-11", "M"),
            ("type 11", "M"), ("asp", "M"), ("chieftain", "M"), ("crusader", "M"), ("challenger", "M"),
            ("keelback", "M"), ("type-6", "M"), ("type 6", "M"), ("type6", "M"), ("mandalay", "M"), ("corsair", "M"),
            ("diamondback", "S"), ("cobra", "S"), ("viper", "S"), ("eagle", "S"), ("hauler", "S"), ("adder", "S"),
            ("sidewinder", "S"), ("vulture", "S"), ("courier", "S"), ("dolphin", "S"), ("kestrel", "S"))

def np_talla(d):
    n = str((((d or {}).get("live") or {}).get("ship") or {}).get("ship") or "").lower()
    return next((t for k, t in NP_TALLA if k in n), None) if n else None

def np_gravedad(d):
    d = d or {}
    body = (d.get("bio") or {}).get("body") or d.get("body")
    c = d.get("cuerpo") or {}
    if c.get("grav") and (not c.get("name") or c.get("name") == body):
        return c["grav"] / 9.80665
    return None

def np_pads(d, dst):
    s_ = SITIOS.get(_sitio_k((d or {}).get("system"), (dst or {}).get("name")))
    return (s_ or {}).get("pads")

# aprender las plataformas al atracar
_np_update_v23b3 = np_update

def np_update(d, now):
    d = d or {}
    r = _np_update_v23b3(d, now)                           # primero se aprende el sitio; luego sus plataformas
    try:
        si = d.get("sysinfo") or {}
        st = d.get("station") or {}
        fl = d.get("Flags", 0)
        nom = st.get("name") or si.get("st_name")
        if fl & 1 and fl & (1 << 21) and nom and si.get("st_pads"):
            k = _sitio_k(d.get("system"), nom)
            if k in SITIOS and SITIOS[k].get("pads") != si["st_pads"]:
                SITIOS[k]["pads"] = list(si["st_pads"])
                _sitios_save()
    except Exception as e:
        log_exc("planeta: plataformas", e)
    return r

_np_dch_v23b3 = np_dch

def np_dch(Z, d, flags, now):
    _np_dch_v23b3(Z, d, flags, now)
    c = np_calc(d, now)
    if c is None:
        return
    w, h = Z.get_size()
    a = pygame.Rect(23, 36, w - 46, h - 49)                  # el hueco de c2_marco
    x = a.x
    hs, ht = F["small"].get_height(), F["tiny"].get_height()
    y = a.bottom - 58 + 6 - 2 * (ht + hs + 6) - 8
    g = np_gravedad(d)
    if g is not None:
        col = RED if g >= 2 else ORANGE if g >= 1.5 else WHITE
        put(Z, F["tiny"], "GRAVEDAD", (x, y), DIM)
        put(Z, F["small"], f"{g:.2f} G".replace(".", ",") + ("  ·  BAJA DESPACIO" if g >= 2 else ""), (x, y + ht + 2), col, a.w - 130)
    y += ht + hs + 10
    pads, talla = np_pads(d, c["dst"]), np_talla(d)
    if pads:
        put(Z, F["tiny"], "PLATAFORMAS" + (f"  ·  TU NAVE {talla}" if talla else ""), (x, y), DIM)
        txt = f"S {pads[0]}   M {pads[1]}   L {pads[2]}"
        cabe = None
        if talla:
            cabe = (pads[2] > 0) if talla == "L" else (pads[1] + pads[2] > 0) if talla == "M" else (sum(pads) > 0)
        put(Z, F["small"], txt + ("" if cabe is None else "  ·  CABES" if cabe else "  ·  NO CABES"),
            (x, y + ht + 2), RED if cabe is False else GREEN if cabe else WHITE, a.w - 130)
