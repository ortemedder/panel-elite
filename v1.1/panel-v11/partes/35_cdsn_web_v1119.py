# Panel Elite v1.1 · parte 35: novedades v1.1.19 — CDSN ESTILO WEB
#   9 FACCIÓN > 3 CDSN (antes RADAR) y la pantalla de espera de la facción, como la web cdsn-web:
#     pestañas RADAR · SISTEMAS · VISITAS · RESUMEN, franja de avisos (POSIBLE ATAQUE, ACTIVIDAD INUSUAL,
#     DEFENSA EN CURSO…), franja de EXPANSIÓN (tocar = ver / ocultar sus aros), radar con barrido, aros de aviso
#     con los colores de la web (rojo grave, amarillo disputado, naranja aviso, verde a favor, morado pendiente),
#     los conflictos en marcha se atenúan al parpadear, leyenda del mapa (?), lista de alertas y ficha corta.
#   Mismas reglas que la web v1.12 y el radar ESP32 v2.8 (alerta(), conflicto día a día, picos de visitas).
#   Aviso grande con voz (una vez al día por sistema): POSIBLE ATAQUE, DÍA DECISIVO, SISTEMA EN DERROTA
#     (ALERTAS > CDSN: ATAQUE / DERROTA). Con CDSN activo no sale además el viejo TRÁFICO ALTO.
#   Se desactiva en AJUSTES > PANTALLA > RADAR CDSN: ESTILO WEB / CLÁSICO (con CLÁSICO todo queda como en la v1.1.18).
import datetime as _dt_cw

EV_LIST.append(("cdsnalarma", "CDSN: ATAQUE / DERROTA"))
MENU[77] = "CDSN"

def cdsn_on():
    return cfg.get("cdsnweb", True)

# ---------------------------------------------------------------------------------------------------------------
# colores de la web (fijos: no cambian con el COLOR del panel, como en la web)
# ---------------------------------------------------------------------------------------------------------------
CWC = {"fondo": (18, 11, 2), "panel": (30, 19, 4), "rej": (74, 44, 8), "linea": (58, 36, 8), "verde": (90, 220, 120),
       "amar": (255, 210, 40), "nar": (255, 140, 0), "rojo": (255, 70, 50), "blanco": (255, 255, 255),
       "nmed": (170, 95, 10), "dim": (130, 80, 20), "ilum": (255, 235, 180), "az": (90, 170, 255),
       "gr": (255, 70, 50), "di": (255, 235, 0), "av": (255, 100, 0), "fa": (90, 220, 120), "pu": (175, 95, 255)}
CW_ES = {"Expansion": "Expansión", "Retreat": "Retirada", "War": "Guerra", "CivilWar": "Guerra civil", "Election": "Elecciones",
         "Boom": "Auge", "Bust": "Crisis", "CivilUnrest": "Disturbios", "Famine": "Hambruna", "Outbreak": "Epidemia",
         "Lockdown": "Cierre", "Investment": "Inversión", "CivilLiberty": "Libertades", "PirateAttack": "Ataque pirata",
         "Drought": "Sequía", "Blight": "Plaga", "NaturalDisaster": "Desastre natural", "PublicHoliday": "Fiesta",
         "InfrastructureFailure": "Fallo de infraestructuras", "TerroristAttack": "Ataque terrorista"}
CW_TIPO = {"war": "Guerra", "civilwar": "Guerra civil", "election": "Elecciones"}

def cw_mix(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))

def c1(v):
    return "—" if v is None else f"{v:.1f}".replace(".", ",")

def cw_parp(now):
    return int(now * 2) % 2 == 0                          # fase del parpadeo (medio segundo)

# ---------------------------------------------------------------------------------------------------------------
# reglas (las mismas que la web: app.js alerta(), pico(), ataque(), conflicto())
# ---------------------------------------------------------------------------------------------------------------
def cw_dia(n, now=None):
    return time.strftime("%Y-%m-%d", time.gmtime((now or time.time()) - 86400 * n))

def cw_pico(s, now):
    t = s.get("trafico") or {}
    d = lambda n: t.get(cw_dia(n, now)) or 0
    for k in (0, 1):
        v = d(k)
        m = sum(d(i) for i in range(k + 1, k + 8)) / 7
        if v >= 5 and v >= 3 * max(m, 1):
            return {"v": v, "m": m, "dia": "ayer" if k else "hoy"}
    return None

def cw_ataque(s, now):
    p = cw_pico(s, now)
    if not p:
        return None
    pv, inf = s.get("prev"), s.get("inf") or 0
    baja = pv is not None and pv - inf >= 1
    sube = pv is not None and inf - pv >= 0.5
    txt = f"{p['v']} pilotos {p['dia']} (media {c1(p['m'])})"
    if baja:
        txt += f" y la influencia baja {c1(pv - inf)} puntos"
    elif sube:
        txt += f" y la influencia sube {c1(inf - pv)} puntos"
    return dict(p, baja=baja, sube=sube, txt=txt)

CW_DIAS = 7
CW_FASES = {"victoria": ("VICTORIA SEGURA", "fa", False, False), "a_un_dia": ("A UN DÍA DE GANAR", "fa", True, False),
            "defensa": ("DEFENSA EN CURSO", "fa", True, False), "disputado": ("DISPUTADO", "di", False, False),
            "igualado": ("DISPUTADO", "di", True, False), "decisivo": ("DÍA DECISIVO", "gr", True, True),
            "derrota": ("SISTEMA EN DERROTA", "gr", True, True), "sin_remedio": ("SISTEMA EN DERROTA", "gr", True, True)}

def cw_fase(g, p, dia):
    q = CW_DIAS + 1 - dia
    if p + q < g: return "victoria"
    if g + q < p: return "sin_remedio"
    if p == 3 or (dia >= CW_DIAS and abs(g - p) <= 1): return "decisivo"
    if g == 3 and p <= 1: return "a_un_dia"
    if g > p: return "defensa"
    if g < p: return "derrota"
    return "disputado" if g == 0 and dia <= 3 else "igualado"

def cw_final(g, p, dia):
    if g >= 4: return "victoria"
    if p >= 4: return "derrota"
    if dia >= CW_DIAS: return "victoria" if g > p else "derrota" if p > g else "empate"
    return "sigue"

def cw_juego(g, p, dia):
    a, b = cw_final(g + 1, p, dia), cw_final(g, p + 1, dia)
    if a == "sigue" and b == "sigue":
        return ""
    return f"ganar = {a} · perder = {b}" + (f" · sin resultado = {cw_final(g, p, dia)}" if dia >= CW_DIAS else "")

def cw_conflicto(c):
    g, p, t = c.get("ganados") or 0, c.get("perdidos") or 0, (c.get("tipo") or "").lower()
    dia, exacto = c.get("dia") or 0, bool(c.get("dia_exacto"))
    if not dia:
        dia, exacto = min(CW_DIAS, g + p + 1), False
    fase = c.get("fase") if c.get("fase") in CW_FASES else cw_fase(g, p, dia)
    tit, tono, parp, alarma = CW_FASES[fase]
    return dict(g=g, p=p, dia=dia, fase=fase, tit=tit, tono=tono, parp=parp, alarma=alarma,
                ico="sobre" if t == "election" else "espadas", tipo=CW_TIPO.get(t, "Conflicto"),
                juego=cw_juego(g, p, dia), diaTxt=f"día {'' if exacto else '≥'}{dia}/{CW_DIAS}")

def cw_alerta(s, now):
    """[nivel, titulo, texto, tono, icono, parpadea, alarma] (nivel 0 nada, 1 aviso, 2 grave)."""
    for c in s.get("conflictos") or []:
        t = (c.get("tipo") or "").lower()
        nom, ico = CW_TIPO.get(t, "Conflicto"), "sobre" if t == "election" else "espadas"
        if c.get("estado") == "active":
            k = cw_conflicto(c)
            return [2, k["tit"], f"{nom} contra {c.get('contra')} · {k['diaTxt']} · {k['g']}-{k['p']}"
                    + (" (sin remedio)" if k["fase"] == "sin_remedio" else "") + (" · " + k["juego"] if k["juego"] else ""),
                    k["tono"], k["ico"], k["parp"], k["alarma"]]
        if c.get("estado") == "pending":
            return [2, nom.upper() + " PEND.", f"contra {c.get('contra')} · empieza en el próximo tick", "pu", ico, False, False]
    act, pen, inf = s.get("activos") or [], s.get("pendientes") or [], s.get("inf") or 0
    if "Retreat" in act or "Retreat" in pen:
        return [2, "RETIRADA", f"influencia {c1(inf)} %", "gr", "", False, False]
    vent = inf - (s.get("segunda_inf") or 0)
    if s.get("ctrl") and vent < 5:
        return [2, "VENTAJA BAJA", f"solo {c1(vent)} sobre {s.get('segunda')}", "gr", "", False, False]
    at = cw_ataque(s, now)
    if at and at["baja"]:
        return [2, "POSIBLE ATAQUE", at["txt"], "gr", "", False, True]
    pv = s.get("prev")
    if pv is not None and pv - inf >= 3:
        return [1, "BAJADA", f"{c1(inf - pv)} desde ayer", "av", "", False, False]
    if at and not at["sube"]:
        return [1, "ACTIVIDAD INUSUAL", at["txt"], "av", "", False, False]
    if at:
        return [1, "ACTIVIDAD A FAVOR", at["txt"] + " (gente propia o ayuda externa)", "fa", "", False, False]
    if "Expansion" in pen:
        return [1, "EXPANSIÓN PEND.", "", "av", "", False, False]
    return [0, "", "", "no", "", False, False]

CW_ACC = {"war": "Combate: zonas de conflicto y misiones de combate a favor de CDSN",
          "civilwar": "Combate: zonas de conflicto y misiones de combate a favor de CDSN",
          "election": "Sin violencia: misiones, comercio con beneficio y datos de exploración en estaciones de CDSN"}
CW_SUBIR = "Subir influencia: misiones de CDSN, comercio con beneficio, bonos y datos de exploración en sus estaciones"

def cw_tareas(now):
    L = []
    for s in ((FACD["data"] or {}).get("sistemas") or {}).values():
        if s.get("fuera") or s.get("inf") is None:
            continue
        inf, act, pen = s["inf"], s.get("activos") or [], s.get("pendientes") or []
        v = inf - (s.get("segunda_inf") or 0)
        add = lambda p, tag, k, por, acc, ico="", parp=False: L.append(dict(s=s, p=p, tag=tag, k=k, por=por, acc=acc, ico=ico, parp=parp))
        hecho = False
        for c in s.get("conflictos") or []:
            t = (c.get("tipo") or "").lower(); nom = CW_TIPO.get(t, "Conflicto")
            if c.get("estado") == "active":
                k = cw_conflicto(c)
                pr = {"decisivo": 104, "sin_remedio": 103, "derrota": 102, "igualado": 100, "disputado": 99, "defensa": 97,
                      "a_un_dia": 96, "victoria": 60}[k["fase"]]
                add(pr, k["tit"], k["tono"], f"{nom} contra {c.get('contra')} · {k['diaTxt']} · {k['g']}-{k['p']}"
                    + (f" · {k['juego']}" if k["juego"] else "") + (f" · en juego: {c['en_juego']}" if c.get("en_juego") else ""),
                    CW_ACC.get(t, CW_SUBIR), k["ico"], k["parp"]); hecho = True
            elif c.get("estado") == "pending":
                add(90, nom.upper() + " PEND.", "pu", f"contra {c.get('contra')} · empieza en el próximo tick",
                    "Prepararse: " + CW_ACC.get(t, CW_SUBIR)[0].lower() + CW_ACC.get(t, CW_SUBIR)[1:]); hecho = True
        if hecho:
            continue
        at = cw_ataque(s, now)
        pv = s.get("prev")
        if "Retreat" in act or "Retreat" in pen:
            add(95, "RETIRADA", "gr", f"influencia {c1(inf)} %, CDSN puede salir del sistema", CW_SUBIR)
        elif inf < 5:
            add(85, "RIESGO RETIRADA", "gr", f"influencia {c1(inf)} %, por debajo del 5 %", CW_SUBIR)
        elif at and at["baja"]:
            add(88, "POSIBLE ATAQUE", "gr", at["txt"] + ": puede que alguien esté trabajando contra CDSN", CW_SUBIR)
        elif s.get("ctrl") and v < 5:
            add(80, "VENTAJA BAJA", "gr", f"solo {c1(v)} puntos sobre {s.get('segunda')}: puede haber conflicto por el control", CW_SUBIR)
        elif pv is not None and pv - inf >= 3:
            add(60, "BAJADA", "av", f"{c1(inf - pv)} puntos desde ayer", CW_SUBIR)
        elif at and at["sube"]:
            add(45, "ACTIVIDAD A FAVOR", "fa", at["txt"] + ": alguien trabaja a favor de CDSN",
                "Seguir así; si no es nuestra gente, averiguar quién nos ayuda")
        elif at:
            add(55, "ACTIVIDAD INUSUAL", "av", at["txt"] + ": vigilar la influencia en el próximo tick",
                "Pasar por el sistema y ver qué misiones se hacen; si baja la influencia, " + CW_SUBIR[0].lower() + CW_SUBIR[1:])
        elif s.get("ctrl") and v < 10:
            add(50, "VENTAJA AJUSTADA", "av", f"{c1(v)} puntos sobre {s.get('segunda')}", CW_SUBIR)
        elif "Expansion" in pen or "Expansion" in act:
            add(40, "EXPANSIÓN", "av", "expansión pendiente" if "Expansion" in pen else "expansión en curso",
                "Mantener la influencia alta mientras dura")
        elif s.get("ctrl") and inf >= 70:
            add(30, "CERCA DE EXPANSIÓN", "fa", f"{c1(inf)} %, la expansión salta al 75 %", CW_SUBIR)
    return sorted(L, key=lambda t: (-t["p"], t["s"]["inf"]))

# ---------------------------------------------------------------------------------------------------------------
# estado de la pantalla y datos preparados (se rehacen al llegar datos nuevos o cada minuto)
# ---------------------------------------------------------------------------------------------------------------
CW = {"tab": 0, "sel": None, "cx": 0.0, "cz": 0.0, "d80": 50.0, "z": 1.0, "def": False, "verexp": False, "ley": False,
      "pg": [0, 0, 0, 0, 0], "hits": [], "S": [], "key": None}
CW_TABS = ["RADAR", "SISTEMAS", "VISITAS", "RESUMEN"]

def cw_datos(now):
    D = FACD["data"] or {}
    key = (id(D), D.get("t"), CW["verexp"], int(now // 60))
    if key == CW["key"]:
        return CW["S"]
    CW["key"] = key
    S = []
    for s in (D.get("sistemas") or {}).values():
        if s.get("fuera") or s.get("inf") is None:
            continue
        a = cw_alerta(s, now)
        exp = a[1] == "EXPANSIÓN PEND."
        pos = s.get("pos") or s.get("coords")
        S.append({"s": s, "x": pos[0] if pos else None, "z": pos[2] if pos and len(pos) > 2 else None, "al": a, "exp": exp,
                  "niv": 0 if exp and not CW["verexp"] else a[0]})
    CW["S"] = S
    if not CW["def"]:
        cw_vista_def()
    return S

def cw_vista_def():
    P = [o for o in CW["S"] if o["x"] is not None]
    if not P:
        return
    C = [o for o in P if o["s"].get("ctrl")] or P
    med = lambda v: sorted(v)[len(v) // 2]
    cx, cz = med([o["x"] for o in C]), med([o["z"] for o in C])
    ds = sorted(math.hypot(o["x"] - cx, o["z"] - cz) for o in P)
    CW.update(cx=cx, cz=cz, d80=max(1.0, ds[int(len(ds) * 0.8)] if ds else 50.0), z=1.0, **{"def": True})

def cw_orden(o):
    a = o["al"]
    return (-(a[0] * 10 + (5 if a[6] else 0) + (2 if a[3] == "gr" else 0)), -(o["s"].get("inf") or 0))

def cw_alertas(S):
    return sorted([o for o in S if o["niv"] > 0], key=cw_orden)

def cw_hit(r, *accion):
    if not HI_PASS[0]:
        CW["hits"].append((pygame.Rect(r), accion))

# ---------------------------------------------------------------------------------------------------------------
# dibujo: piezas comunes
# ---------------------------------------------------------------------------------------------------------------
def cw_icono(surf, ico, x, y, col):
    """espadas (guerra) o sobre (elecciones), 10x10 con la esquina arriba-izquierda en x, y."""
    if ico == "espadas":
        pygame.draw.line(surf, col, (x, y), (x + 9, y + 9), 2)
        pygame.draw.line(surf, col, (x + 9, y), (x, y + 9), 2)
        pygame.draw.line(surf, col, (x, y + 6), (x + 3, y + 9), 1)
        pygame.draw.line(surf, col, (x + 6, y + 9), (x + 9, y + 6), 1)
        return 13
    if ico == "sobre":
        pygame.draw.rect(surf, col, (x, y + 1, 11, 8), 1)
        pygame.draw.lines(surf, col, False, [(x, y + 1), (x + 5, y + 5), (x + 10, y + 1)], 1)
        return 14
    return 0

def cw_tag(surf, a, x, y, maxw, now, font=None, caja=True):
    """etiqueta de aviso (como .tag de la web): icono + titulo en su color; devuelve el ancho."""
    if not a or not a[0] and a[1] != "EXPANSIÓN PEND.":
        return 0
    font = font or F["tiny"]
    col = CWC.get(a[3], CWC["rojo"])
    if a[5] and not cw_parp(now):
        col = cw_mix(col, CWC["fondo"], 0.6)
    w = min(maxw, (14 if a[4] else 0) + tw_(font, a[1]) + 8)
    if caja:
        pygame.draw.rect(surf, cw_mix(col, CWC["fondo"], 0.8), (x, y, w, 14), border_radius=3)
        pygame.draw.rect(surf, col, (x, y, w, 14), 1, border_radius=3)
    dx = cw_icono(surf, a[4], x + 4, y + 2, col)
    put(surf, font, a[1], (x + 4 + dx, y + 2), col, w - 6 - dx)
    return w

def cw_lineas(font, text, w, n=3):
    out, cur = [], ""
    for p in str(text or "").split():
        t = (cur + " " + p).strip()
        if tw_(font, t) <= w:
            cur = t
        else:
            if cur:
                out.append(cur)
            cur = p
        if len(out) >= n:
            break
    if cur and len(out) < n:
        out.append(cur)
    return out

def cw_hace(t, now):
    if not t:
        return "—"
    m = int((now - t) / 60)
    return "ahora" if m < 1 else f"hace {m} min" if m < 120 else f"hace {m // 60} h" if m < 2880 else f"hace {m // 1440} d"

def cw_boton(surf, r, txt, on=False, col=None, accion=None):
    col = col or CWC["nar"]
    r = pygame.Rect(r)
    if on:
        pygame.draw.rect(surf, col, r, border_radius=4)
    else:
        pygame.draw.rect(surf, CWC["fondo"], r, border_radius=4)
        pygame.draw.rect(surf, col, r, 1, border_radius=4)
    put(surf, F["small"], txt, r.center, BLACK if on else col, r.w - 4, anchor="center")
    if accion:
        cw_hit(r, *accion)

def cw_cabecera(surf, S, now):
    for i, t in enumerate(CW_TABS):                           # pestañas (como la web)
        r = pygame.Rect(4 + i * 106, 4, 102, 21)
        cw_boton(surf, r, t, CW["tab"] == i, accion=("tab", i))
    # franja de avisos: lo más grave primero
    A = cw_alertas(S)
    alarm = [o for o in A if o["al"][6]]
    inus = [o for o in S if o["al"][1] == "ACTIVIDAD INUSUAL"]
    defe = [o for o in S if o["al"][1] in ("DEFENSA EN CURSO", "A UN DÍA DE GANAR")]
    nexp = sum(1 for o in S if o["exp"])
    xr = W - 54                                               # a la derecha queda el botón de volver / FIJAR
    if nexp:                                                  # chip de la expansión (de toda la facción)
        te = f"EXPANSIÓN {nexp}"
        r = pygame.Rect(xr - tw_(F["tiny"], te) - 12, 28, tw_(F["tiny"], te) + 12, 15)
        on = CW["verexp"]
        pygame.draw.rect(surf, CWC["av"] if on else CWC["fondo"], r, border_radius=3)
        pygame.draw.rect(surf, CWC["av"], r, 1, border_radius=3)
        put(surf, F["tiny"], te, r.center, BLACK if on else CWC["av"], r.w - 4, anchor="center")
        cw_hit(r.inflate(4, 8), "exp")
        xr = r.x - 4
    r = pygame.Rect(4, 28, xr - 4, 15)
    if alarm:
        o = alarm[0]; a = o["al"]
        on = cw_parp(now)
        pygame.draw.rect(surf, CWC["rojo"] if on else cw_mix(CWC["rojo"], CWC["fondo"], 0.45), r, border_radius=3)
        t = f"⚠ {a[1]} · {o['s']['sys']}" + (f"  (+{len(alarm) - 1})" if len(alarm) > 1 else "")
        put(surf, F["tiny"], t.replace("⚠ ", ""), (r.x + 6, r.y + 2), BLACK, r.w - 10)
        cw_hit(r.inflate(0, 8), "sel", o["s"]["sys"])
    elif inus or defe:
        o = (inus or defe)[0]; a = o["al"]
        col = CWC[a[3]]
        pygame.draw.rect(surf, cw_mix(col, CWC["fondo"], 0.8), r, border_radius=3)
        pygame.draw.rect(surf, col, r, 1, border_radius=3)
        n = len(inus or defe)
        put(surf, F["tiny"], f"{a[1]} · {o['s']['sys']}" + (f"  (+{n - 1})" if n > 1 else ""), (r.x + 6, r.y + 2), col, r.w - 10)
        cw_hit(r.inflate(0, 8), "sel", o["s"]["sys"])
    else:
        D = FACD["data"] or {}
        put(surf, F["tiny"], f"{len(S)} sistemas · datos del escucha {cw_hace(D.get('t'), now)}" + (" · todo tranquilo" if not A else ""),
            (r.x + 2, r.y + 2), CWC["dim"], r.w - 4)

# ---------------------------------------------------------------------------------------------------------------
# pestaña RADAR
# ---------------------------------------------------------------------------------------------------------------
RA = pygame.Rect(0, 46, 300, H - 46)                          # zona del radar
RP = pygame.Rect(304, 46, W - 308, H - 48)                    # panel de la derecha

def cw_color_inf(s):
    i = s.get("inf") or 0
    return CWC["verde"] if i > 50 else CWC["amar"] if i > 20 else CWC["nar"]

def cw_radar(surf, S, now):
    cx, cy = RA.centerx, RA.centery
    R = min(RA.w, RA.h) // 2 - 6
    k = 0.9 * R / CW["d80"] * CW["z"]
    surf.set_clip(RA)
    ang = (now * 90) % 360                                    # una vuelta cada 4 s
    A = lambda a: math.radians(a - 90)
    for i in range(9, -1, -1):                                # estela del barrido
        a1, a2 = ang - (i + 1) * 4, ang - i * 4 + 0.6
        col = cw_mix((200, 110, 0), CWC["fondo"], 0.35 + 0.65 * (i / 10) ** 0.8)
        pts = [(cx, cy)] + [(cx + R * math.cos(A(a1 + (a2 - a1) * j / 3)), cy + R * math.sin(A(a1 + (a2 - a1) * j / 3))) for j in range(4)]
        pygame.draw.polygon(surf, col, pts)
    for i in (1, 2, 3):                                       # rejilla
        pygame.draw.circle(surf, CWC["rej"], (cx, cy), R * i // 3, 1)
    pygame.draw.line(surf, CWC["rej"], (cx - R, cy), (cx + R, cy))
    pygame.draw.line(surf, CWC["rej"], (cx, cy - R), (cx, cy + R))
    pygame.draw.line(surf, (255, 200, 90), (cx, cy), (cx + R * math.cos(A(ang)), cy + R * math.sin(A(ang))), 2)
    pulso = (math.sin(now * 6) + 1) / 2
    P = []
    for o in S:
        if o["x"] is None:
            continue
        dx, dz = (o["x"] - CW["cx"]) * k, (o["z"] - CW["cz"]) * k
        x, y = cx + dx, cy - dz
        o["sx"], o["sy"] = x, y
        if not (RA.x - 20 < x < RA.right + 20 and RA.y - 20 < y < RA.bottom + 20):
            continue
        a = (math.degrees(math.atan2(dx, dz)) + 360) % 360
        dif = (ang - a + 360) % 360
        o["luz"] = max(0.0, 1 - dif / 45) if math.hypot(dx, dz) <= R else 0.0
        P.append(o)
    for o in P:                                               # aros de aviso
        x, y, al = o["sx"], o["sy"], o["al"]
        ca = CWC.get(al[3], CWC["rojo"])
        if al[5] and not cw_parp(now):
            ca = cw_mix(ca, CWC["fondo"], 0.65)               # al parpadear se atenúa, no se apaga
        if o["niv"] == 2:
            pygame.draw.circle(surf, ca, (x, y), 9 + pulso * 5, 2)
        elif o["niv"] == 1 or (o["exp"] and CW["verexp"]):
            pygame.draw.circle(surf, cw_mix(ca, CWC["fondo"], 0.5), (x, y), 8, 1)
    for o in P:                                               # sistemas
        x, y, s = o["sx"], o["sy"], o["s"]
        col = cw_color_inf(s)
        if o["luz"] > 0.05:
            col = cw_mix(col, CWC["ilum"], o["luz"])
        if s.get("ctrl"):
            pygame.draw.rect(surf, col, (x - 4, y - 4, 8, 8))
        else:
            pygame.draw.circle(surf, col, (x, y), 3)
        if CW["sel"] == s.get("sys"):
            pygame.draw.rect(surf, CWC["blanco"], (x - 8, y - 8, 16, 16), 1)
    kz = CW["z"]                                              # nombres: alertas, luego controlados, luego el resto
    lab = []
    for pas in (0, 1, 2):
        if (pas == 1 and kz < 1.4) or (pas == 2 and kz < 3):
            break
        for o in P:
            s, niv = o["s"], o["niv"]
            ok = niv > 1 if pas == 0 else ((s.get("ctrl") and not niv) or niv == 1) if pas == 1 else (not s.get("ctrl") and not niv)
            if not ok and not (pas == 0 and CW["sel"] == s.get("sys")):
                continue
            n = s.get("sys") or "?"
            x, y = o["sx"] + (16 if niv else 8), o["sy"] - 6
            wd = tw_(F["tiny"], n)
            if x > RA.right or y < RA.y or y > RA.bottom:
                continue
            if any(x < r[0] + r[2] + 3 and r[0] < x + wd + 3 and abs(y - r[1]) < 11 for r in lab):
                continue
            lab.append((x, y, wd))
            put(surf, F["tiny"], n, (x, y), CWC.get(o["al"][3], CWC["rojo"]) if niv else CWC["blanco"] if s.get("ctrl") else CWC["nmed"])
    surf.set_clip(None)
    put(surf, F["tiny"], f"anillo {round(R / 3 / k)} ly", (RA.right - 4, RA.bottom - 14), CWC["rej"], anchor="topright")
    for i, (t, acc) in enumerate((("+", "zoom+"), ("−", "zoom-"), ("C", "centro"), ("?", "ley"))):
        cw_boton(surf, (4 + i * 28, RA.bottom - 24, 24, 20), t, t == "?" and CW["ley"], accion=(acc,))
    cw_hit(RA, "radar")
    if CW["ley"]:
        cw_leyenda(surf, now)

def cw_leyenda(surf, now):
    r = pygame.Rect(RA.x + 6, RA.y + 4, RA.w - 12, RA.h - 34)
    pygame.draw.rect(surf, CWC["panel"], r, border_radius=6)
    pygame.draw.rect(surf, CWC["nar"], r, 1, border_radius=6)
    put(surf, F["small"], "LEYENDA DEL MAPA", (r.x + 8, r.y + 5), CWC["nar"])
    y = r.y + 24
    def fila(dib, txt, col=None):
        nonlocal y
        dib(r.x + 16, y + 6)
        put(surf, F["tiny"], txt, (r.x + 32, y), col or CWC["blanco"], r.w - 40)
        y += 15
    fila(lambda x, yy: pygame.draw.rect(surf, CWC["verde"], (x - 4, yy - 4, 8, 8)), "controlado (verde > 50 %, amarillo > 20 %)")
    fila(lambda x, yy: pygame.draw.circle(surf, CWC["nar"], (x, yy), 3), "presencia, sin control")
    fila(lambda x, yy: pygame.draw.circle(surf, CWC["rojo"], (x, yy), 7, 2), "aro grueso que late: alerta grave")
    fila(lambda x, yy: pygame.draw.circle(surf, cw_mix(CWC["av"], CWC["fondo"], .5), (x, yy), 7, 1), "aro fino: aviso leve (nombre con zoom)")
    fila(lambda x, yy: pygame.draw.circle(surf, CWC["verde"] if cw_parp(now) else cw_mix(CWC["verde"], CWC["fondo"], .65), (x, yy), 7, 2),
         "parpadea (se atenúa): conflicto en marcha")
    for t, k_ in (("rojo: derrota, día decisivo, ataque, retirada", "gr"), ("amarillo: conflicto disputado", "di"),
                  ("naranja: bajada, actividad inusual", "av"), ("verde: defensa, victoria, a favor", "fa"),
                  ("morado: conflicto pendiente", "pu")):
        fila(lambda x, yy, c=CWC[k_]: pygame.draw.circle(surf, c, (x, yy), 6, 2), t, CWC[k_])
    fila(lambda x, yy: cw_icono(surf, "espadas", x - 5, yy - 5, CWC["nar"]), "guerra")
    fila(lambda x, yy: cw_icono(surf, "sobre", x - 5, yy - 5, CWC["nar"]), "elecciones")
    fila(lambda x, yy: pygame.draw.rect(surf, CWC["blanco"], (x - 7, yy - 7, 14, 14), 1), "sistema marcado")
    put(surf, F["tiny"], "EXPANSIÓN (arriba): ver u ocultar sus aros", (r.x + 8, y + 2), CWC["av"], r.w - 16)

def cw_panel(surf, S, now):
    pygame.draw.rect(surf, CWC["panel"], RP, border_radius=6)
    o = next((o for o in S if o["s"].get("sys") == CW["sel"]), None) if CW["sel"] else None
    if o:
        cw_ficha_corta(surf, o, now); return
    A = cw_alertas(S)
    put(surf, F["small"], f"ALERTAS ({len(A)})", (RP.x + 6, RP.y + 4), CWC["nar"])
    por = (RP.h - 40) // 32
    pg = CW["pg"][0] % max(1, (len(A) + por - 1) // por)
    CW["pg"][0] = pg
    y = RP.y + 22
    for o in A[pg * por:(pg + 1) * por]:
        a, s = o["al"], o["s"]
        r = pygame.Rect(RP.x + 4, y, RP.w - 8, 30)
        col = CWC.get(a[3], CWC["rojo"])
        pygame.draw.rect(surf, CWC["fondo"], r, border_radius=4)
        pygame.draw.rect(surf, col if not (a[5] and not cw_parp(now)) else cw_mix(col, CWC["fondo"], .6), (r.x, r.y, 3, r.h))
        put(surf, F["small"], s.get("sys"), (r.x + 8, r.y + 1), CWC["blanco"] if s.get("ctrl") else CWC["nar"], r.w - 12)
        cw_tag(surf, a, r.x + 8, r.y + 15, r.w - 14, now, caja=False)
        cw_hit(r, "sel", s.get("sys"))
        y += 32
    if not A:
        put(surf, F["tiny"], "todo tranquilo", (RP.centerx, RP.y + 50), CWC["verde"], anchor="center")
    if len(A) > por:
        n = (len(A) + por - 1) // por
        cw_boton(surf, (RP.x + 4, RP.bottom - 20, RP.w - 8, 17), f"más  ▼   {pg + 1}/{n}".replace("▼", "v"), accion=("pag", 0))

def cw_ficha_corta(surf, o, now):
    s, a = o["s"], o["al"]
    x, y, w = RP.x + 6, RP.y + 4, RP.w - 12
    put_fit(surf, ("btn", "small", "tiny"), s.get("sys"), (x, y + 2), CWC["blanco"] if s.get("ctrl") else CWC["nar"], w - 20)
    cw_boton(surf, (RP.right - 22, RP.y + 3, 18, 18), "×", accion=("x",))
    y += 22
    put(surf, F["tiny"], "CONTROLADO" if s.get("ctrl") else "presencia", (x, y), CWC["verde"] if s.get("ctrl") else CWC["dim"]); y += 13
    inf, pv = s.get("inf") or 0, s.get("prev")
    d_ = "" if pv is None else f"  ({'+' if inf - pv >= 0 else ''}{c1(inf - pv)} ayer)"
    put(surf, F["small"], f"influencia {c1(inf)} %", (x, y), cw_color_inf(s))
    if d_:
        put(surf, F["tiny"], d_, (x + tw_(F["small"], f"influencia {c1(inf)} %") + 2, y + 2),
            CWC["verde"] if inf - pv >= 0 else CWC["rojo"])
    y += 16
    if s.get("segunda"):
        put(surf, F["tiny"], f"ventaja {c1(inf - (s.get('segunda_inf') or 0))} sobre {s.get('segunda')}", (x, y), CWC["dim"], w); y += 14
    if a[0] or a[1]:
        y += 2; cw_tag(surf, a, x, y, w, now); y += 18
        for ln in cw_lineas(F["tiny"], a[2], w, 4):
            put(surf, F["tiny"], ln, (x, y), CWC["blanco"]); y += 12
    est = [CW_ES.get(e, e) for e in (s.get("activos") or [])] + [CW_ES.get(e, e) + " (pend.)" for e in (s.get("pendientes") or [])]
    if est:
        y += 2
        for ln in cw_lineas(F["tiny"], "estados: " + ", ".join(est), w, 2):
            put(surf, F["tiny"], ln, (x, y), CWC["nar"]); y += 12
    t = s.get("trafico") or {}
    y += 2
    put(surf, F["tiny"], f"visitas hoy {t.get(cw_dia(0, now)) or 0} · ayer {t.get(cw_dia(1, now)) or 0}", (x, y), CWC["az"], w)
    cw_boton(surf, (RP.x + 4, RP.bottom - 22, RP.w - 8, 19), "FICHA COMPLETA  >", accion=("ficha", s.get("sys")))

# ---------------------------------------------------------------------------------------------------------------
# pestañas SISTEMAS · VISITAS · RESUMEN
# ---------------------------------------------------------------------------------------------------------------
def cw_paginas(surf, n, por, i, y):
    pags = max(1, (n + por - 1) // por)
    CW["pg"][i] %= pags
    if pags > 1:
        put(surf, F["tiny"], f"pág. {CW['pg'][i] + 1}/{pags}", (W - 100, y + 3), CWC["dim"], anchor="topright")
        cw_boton(surf, (W - 94, y, 42, 18), "^", accion=("pagm", i))
        cw_boton(surf, (W - 48, y, 42, 18), "v", accion=("pag", i))
    return CW["pg"][i] * por

def cw_sistemas(surf, S, now):
    L = sorted(S, key=cw_orden)
    y0, rh = 64, 17
    por = (H - 24 - y0) // rh
    for t, xx, an in (("Sistema", 8, "topleft"), ("Infl.", 238, "topright"), ("Ayer", 280, "topright"),
                      ("Vent.", 322, "topright"), ("Aviso", 332, "topleft")):
        put(surf, F["tiny"], t, (xx, 50), CWC["dim"], anchor=an)
    pygame.draw.line(surf, CWC["linea"], (4, 62), (W - 4, 62))
    i0 = cw_paginas(surf, len(L), por, 1, H - 21)
    for j, o in enumerate(L[i0:i0 + por]):
        s, a = o["s"], o["al"]
        y = y0 + j * rh
        r = pygame.Rect(2, y, W - 4, rh - 1)
        if j % 2:
            pygame.draw.rect(surf, CWC["panel"], r)
        if a[0]:
            pygame.draw.rect(surf, CWC.get(a[3], CWC["rojo"]), (2, y, 3, rh - 1))
        put(surf, F["small"], s.get("sys"), (8, y + 1), CWC["blanco"] if s.get("ctrl") else CWC["nar"], 186)
        inf, pv = s.get("inf") or 0, s.get("prev")
        put(surf, F["small"], c1(inf), (238, y + 1), cw_color_inf(s), anchor="topright")
        if pv is not None:
            d_ = inf - pv
            put(surf, F["tiny"], ("+" if d_ >= 0 else "") + c1(d_), (280, y + 3), CWC["verde"] if d_ > 0.05 else CWC["rojo"] if d_ < -0.05 else CWC["dim"], anchor="topright")
        if s.get("segunda") is not None:
            v = inf - (s.get("segunda_inf") or 0)
            put(surf, F["tiny"], c1(v), (322, y + 3), CWC["rojo"] if s.get("ctrl") and v < 5 else CWC["dim"], anchor="topright")
        if a[0] or o["exp"]:
            cw_tag(surf, a, 332, y + 1, W - 336, now, caja=False)
        cw_hit(r, "ficha", s.get("sys"))
    put(surf, F["tiny"], f"{len(L)} sistemas · {sum(1 for o in L if o['s'].get('ctrl'))} controlados · toca uno para su ficha",
        (6, H - 18), CWC["dim"], W - 200)

def cw_visitas(surf, S, now):
    dias = [cw_dia(n, now) for n in range(5)]
    L = []
    for o in S:
        t = o["s"].get("trafico") or {}
        serie = [t.get(d) or 0 for d in reversed(dias)]
        a1 = o["al"][1]
        at = 3 if a1 == "POSIBLE ATAQUE" else 2 if a1 == "ACTIVIDAD INUSUAL" else 1 if a1 == "ACTIVIDAD A FAVOR" else 0
        if sum(serie) or at:
            m = sum(t.get(cw_dia(i, now)) or 0 for i in range(1, 8)) / 7
            L.append(dict(o=o, at=at, hoy=serie[-1], ayer=serie[-2], m=m, serie=serie))
    L.sort(key=lambda v: (-v["at"], -v["hoy"], -sum(v["serie"]), -(v["o"]["s"].get("inf") or 0)))
    tot = sum(v["hoy"] for v in L)
    put(surf, F["tiny"], f"hoy {tot} visitas en {sum(1 for v in L if v['hoy'])} sistemas · {len(S) - len(L)} sin visitas en 5 días",
        (8, 48), CWC["az"], W - 16)
    y0, rh = 78, 17
    for t, xx, an in (("Sistema", 8, "topleft"), ("Hoy", 222, "topright"), ("Ayer", 258, "topright"),
                      ("Media", 300, "topright"), ("5 días", 308, "topleft"), ("Aviso", 366, "topleft")):
        put(surf, F["tiny"], t, (xx, 63), CWC["dim"], anchor=an)
    pygame.draw.line(surf, CWC["linea"], (4, 76), (W - 4, 76))
    por = (H - 24 - y0) // rh
    i0 = cw_paginas(surf, len(L), por, 2, H - 21)
    for j, v in enumerate(L[i0:i0 + por]):
        o = v["o"]; s, a = o["s"], o["al"]
        y = y0 + j * rh
        r = pygame.Rect(2, y, W - 4, rh - 1)
        if j % 2:
            pygame.draw.rect(surf, CWC["panel"], r)
        put(surf, F["small"], s.get("sys"), (8, y + 1), CWC["blanco"] if s.get("ctrl") else CWC["nar"], 176)
        put(surf, F["small"], str(v["hoy"]), (222, y + 1), CWC["az"] if v["hoy"] else CWC["dim"], anchor="topright")
        put(surf, F["tiny"], str(v["ayer"]), (258, y + 3), CWC["az"] if v["ayer"] else CWC["dim"], anchor="topright")
        put(surf, F["tiny"], c1(v["m"]), (300, y + 3), CWC["dim"], anchor="topright")
        mx = max(1, max(v["serie"]))
        for k_, n in enumerate(v["serie"]):                   # barritas de los 5 días
            hh = max(1, round(n / mx * 12)) if n else 1
            pygame.draw.rect(surf, CWC["az"] if n else CWC["linea"], (310 + k_ * 10, y + 14 - hh, 7, hh))
        if v["at"]:
            cw_tag(surf, a, 366, y + 1, W - 370, now, caja=False)
        cw_hit(r, "ficha", s.get("sys"))
    if not L:
        put(surf, F["small"], "nadie ha pasado por nuestros sistemas en 5 días", (W // 2, 140), CWC["dim"], anchor="center")
    put(surf, F["tiny"], "pilotos distintos por día que envían datos a EDDN", (6, H - 18), CWC["dim"], W - 200)

def cw_resumen(surf, S, now):
    A = cw_alertas(S)
    t0 = cw_dia(0, now)
    cajas = [("SISTEMAS", len(S), CWC["nar"]), ("CONTROLADOS", sum(1 for o in S if o["s"].get("ctrl")), CWC["blanco"]),
             ("GRAVES", sum(1 for o in A if o["niv"] == 2), CWC["rojo"]),
             ("VISITAS HOY", sum((o["s"].get("trafico") or {}).get(t0) or 0 for o in S), CWC["az"])]
    for i, (t, n, col) in enumerate(cajas):
        r = pygame.Rect(4 + i * 119, 48, 115, 36)
        pygame.draw.rect(surf, CWC["panel"], r, border_radius=5)
        put(surf, F["big"], str(n), (r.centerx, r.y + 3), col, anchor="midtop")
        put(surf, F["tiny"], t, (r.centerx, r.bottom - 12), CWC["dim"], anchor="midtop")
    T = cw_tareas(now)
    put(surf, F["small"], "QUÉ HACER HOY" + (f"  ·  {len(T)} sistemas, de más a menos urgente" if T else ""), (6, 89), CWC["nar"], W - 12)
    y0, rh = 106, 42
    por = (H - 24 - y0) // rh
    i0 = cw_paginas(surf, len(T), por, 3, H - 21)
    for j, t in enumerate(T[i0:i0 + por]):
        s = t["s"]
        y = y0 + j * rh
        r = pygame.Rect(2, y, W - 4, rh - 2)
        pygame.draw.rect(surf, CWC["panel"], r, border_radius=4)
        pygame.draw.rect(surf, CWC.get(t["k"], CWC["rojo"]), (2, y, 3, rh - 2))
        wn = put(surf, F["small"], s.get("sys"), (8, y + 2), CWC["blanco"] if s.get("ctrl") else CWC["nar"], 200)
        cw_tag(surf, [1, t["tag"], "", t["k"], t["ico"], t["parp"], False], 14 + wn, y + 2, W - 24 - wn, now)
        put(surf, F["tiny"], t["por"], (8, y + 16), CWC["dim"], W - 16)
        put(surf, F["tiny"], "> " + t["acc"], (8, y + 28), CWC["verde"], W - 16)
        cw_hit(r, "ficha", s.get("sys"))
    if not T:
        put(surf, F["small"], "Todo tranquilo: ningún sistema necesita ayuda ahora mismo.", (W // 2, 160), CWC["verde"], anchor="center")
    D = FACD["data"] or {}
    put(surf, F["tiny"], f"datos del escucha {cw_hace(D.get('t'), now)}", (6, H - 18), CWC["dim"], W - 200)

# ---------------------------------------------------------------------------------------------------------------
# pantalla entera (menú 9 > 3 CDSN y pantalla de espera)
# ---------------------------------------------------------------------------------------------------------------
def draw_cdsn(surf, now):
    if not HI_PASS[0]:
        CW["hits"] = []
    surf.fill(CWC["fondo"])
    S = cw_datos(now)
    if CW["sel"] and not any(o["s"].get("sys") == CW["sel"] for o in S):
        CW["sel"] = None
    cw_cabecera(surf, S, now)
    tab = CW["tab"]
    if tab == 0:
        cw_radar(surf, S, now)
        cw_panel(surf, S, now)
    elif tab == 1:
        cw_sistemas(surf, S, now)
    elif tab == 2:
        cw_visitas(surf, S, now)
    else:
        cw_resumen(surf, S, now)

_dfs_v1119 = draw_fac_screen

def draw_fac_screen(surf, now):
    if cdsn_on():
        try:
            return draw_cdsn(surf, now)
        except Exception as e:
            log_exc("CDSN web", e)
    return _dfs_v1119(surf, now)

def cw_toque(x, y):
    """Toques en la pantalla CDSN. True si los ha usado."""
    for r, acc in reversed(CW["hits"]):
        if not r.collidepoint(x, y):
            continue
        k = acc[0]
        if k == "tab":
            CW["tab"] = acc[1]
        elif k == "exp":
            CW["verexp"] = not CW["verexp"]; CW["key"] = None
        elif k == "sel":
            CW["tab"] = 0
            if CW["sel"] == acc[1]:
                return cw_abre_ficha(acc[1])
            CW["sel"] = acc[1]
        elif k == "x":
            CW["sel"] = None
        elif k == "ficha":
            return cw_abre_ficha(acc[1])
        elif k == "pag":
            CW["pg"][acc[1]] += 1
        elif k == "pagm":
            CW["pg"][acc[1]] = max(0, CW["pg"][acc[1]] - 1)
        elif k == "zoom+":
            CW["z"] = min(12.0, CW["z"] * 1.5)
        elif k == "zoom-":
            CW["z"] = max(0.5, CW["z"] / 1.5)
        elif k == "centro":
            CW["def"] = False; cw_vista_def(); CW["sel"] = None
        elif k == "ley":
            CW["ley"] = not CW["ley"]
        elif k == "radar":
            if CW["ley"]:
                CW["ley"] = False; return True
            hit = None
            for o in CW["S"]:                                 # el sistema más cercano al dedo
                if o.get("sx") is None:
                    continue
                d = math.hypot(o["sx"] - x, o["sy"] - y)
                if d < 14 and (hit is None or d < hit[0]):
                    hit = (d, o)
            if hit:
                n = hit[1]["s"].get("sys")
                if CW["sel"] == n:
                    return cw_abre_ficha(n)
                CW["sel"] = n
            else:                                             # vacío: centrar ahí
                kk = 0.9 * (min(RA.w, RA.h) // 2 - 6) / CW["d80"] * CW["z"]
                CW["cx"] += (x - RA.centerx) / kk
                CW["cz"] -= (y - RA.centery) / kk
        TAP_EV.set()
        return True
    return False

def cw_abre_ficha(n):
    if ui.get("idle_on"):
        ui["idle_skip"] = time.time() + 60
    ui["facsys"] = n; ui["facback"] = 77; ui["view"] = 194
    TAP_EV.set()
    return True

# ---------------------------------------------------------------------------------------------------------------
# toques: delante de todo lo demás en la pantalla CDSN
# ---------------------------------------------------------------------------------------------------------------
_on_tap_v1119 = on_tap

def on_tap(x, y):
    v = ui.get("view")
    if v == 160 and not ui.get("idle_on") and grid(5, 3, 2, TOP, H - 40).collidepoint(x, y):
        tap_flash((160, 5)); cfg["cdsnweb"] = not cdsn_on(); save_cfg(); TAP_EV.set(); return
    vis = v == 77 or (ui.get("idle_on") and IDLE_MODE.get("m") == "fac")
    tapa = (ui.get("alert") and time.time() < ui["alert"]["until"]) or xa.get("a")
    if vis and cdsn_on() and not tapa and not FULL_BACK.inflate(10, 10).collidepoint(x, y):
        try:
            if cw_toque(x, y):
                if ui.get("idle_on"):
                    IDLEHOLD["m"] = "fac"                     # en la espera: se queda en CDSN mientras lo usas
                return
        except Exception as e:
            log_exc("CDSN toque", e)
    return _on_tap_v1119(x, y)

# ---------------------------------------------------------------------------------------------------------------
# menú 9: el botón 3 se llama CDSN (rojo si hay alerta grande)
# ---------------------------------------------------------------------------------------------------------------
_view_sub9_v1119 = view_sub9

def view_sub9(surf, d, flags, now):
    _view_sub9_v1119(surf, d, flags, now)
    if not cdsn_on():
        return
    r = grid(2, 4, 2)
    pygame.draw.rect(surf, BLACK, r)
    try:
        alarma = any(o["al"][6] for o in cw_datos(now))
    except Exception:
        alarma = False
    draw_button(surf, r, "3", "CDSN", F["num"], filled=alarma and cw_parp(now), lit=flash.get((9, 2), 0) > now)
    if alarma:
        pygame.draw.rect(surf, RED, r, 3, border_radius=6)

VIEWS[220] = view_sub9

# AJUSTES > PANTALLA: botón 6 RADAR CDSN (ESTILO WEB / CLÁSICO)
_view_pantalla_v1119 = view_pantalla

def view_pantalla(surf, d, flags, now):
    _view_pantalla_v1119(surf, d, flags, now)
    r = grid(5, 3, 2, TOP, H - 40)
    pygame.draw.rect(surf, BLACK, r)
    draw_button(surf, r, "RADAR CDSN", "ESTILO WEB" if cdsn_on() else "CLÁSICO", F["big"], filled=cdsn_on(),
                lit=flash.get((160, 5), 0) > now)

VIEWS[160] = view_pantalla

# ---------------------------------------------------------------------------------------------------------------
# avisos grandes con voz: POSIBLE ATAQUE, DÍA DECISIVO, SISTEMA EN DERROTA (una vez al día por sistema)
# ---------------------------------------------------------------------------------------------------------------
CW_AVF = os.path.join(PANEL_DIR, "cdsn_avisos.json")
CW_AV = {"vistos": None, "t": 0.0}

def cw_avisos(now):
    if now - CW_AV["t"] < 30 or not FACD.get("data"):
        return
    CW_AV["t"] = now
    if CW_AV["vistos"] is None:
        try:
            CW_AV["vistos"] = set(json.load(open(CW_AVF)))
        except Exception:
            CW_AV["vistos"] = set()
    hoy = cw_dia(0, now)
    for o in cw_datos(now):
        a = o["al"]
        if not a[6]:
            continue
        n = o["s"].get("sys")
        k = f"{hoy}|{n}|{a[1]}"
        if k in CW_AV["vistos"]:
            continue
        CW_AV["vistos"] = {x for x in CW_AV["vistos"] if x.startswith(hoy)} | {k}
        try:
            json.dump(sorted(CW_AV["vistos"]), open(CW_AVF, "w"))
        except Exception:
            pass
        fx_alert("cdsnalarma", a[1], n, cw_lineas(F["small"], a[2], 380, 2), f"{a[1].lower()} en {n}")
        plog(f"CDSN: {a[1]} en {n} · {a[2]}")
        return                                                # uno cada vez

_fac_watch_v1119 = fac_watch

def fac_watch(now):
    if cdsn_on():                                             # el viejo TRÁFICO ALTO es el POSIBLE ATAQUE de CDSN
        try:
            hoyk = time.strftime("%Y-%m-%d", time.gmtime())
            for n in ((FACD["data"] or {}).get("sistemas") or {}):
                FW["trf"].add((n, hoyk))
        except Exception:
            pass
    _fac_watch_v1119(now)
    if cdsn_on():
        try:
            cw_avisos(now)
        except Exception as e:
            log_exc("CDSN avisos", e)
