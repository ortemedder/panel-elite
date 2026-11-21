# Panel Elite v1.1 · parte 07: alertas y combate (lineas 5569-6573 del panel entero)
# ---------- AJUSTES > OPCIONES > ALERTAS (161) y CAMBIO AUTO (162): uno a uno ----------
EVPP = 12

EVL = {161: (EV_LIST, "ev", "evpage", "alerts", {}), 162: (AUTO_LIST, "autoev", "autopage", "auto", {}),
       163: (EV_LIST, "snd", "sndpage", "sound", SND_DEF)}

def _evl(v):
    return EVL[v][:3]

def view_evlist_base(surf, d, flags, now):
    v = ui["view"]
    L, st, pk = _evl(v)
    pages = (len(L) + EVPP - 1) // EVPP
    pg = ui.get(pk, 0) % pages
    on = cfg.get(st) or {}
    df = EVL[v][4]
    n = sum(1 for k, _ in L if on.get(k, df.get(k, True)))
    top = [("TODOS ON", None), ("TODOS OFF", None), (f"PÁG {pg + 1}/{pages}" if pages > 1 else f"{n} de {len(L)}", None)]
    for i, (t, _) in enumerate(top):
        draw_button(surf, grid(i, 3, 1, TOP, TOP + 40), t, None, F["btn"], lit=flash.get((v, 100 + i), 0) > now)
    for i, (k, name) in enumerate(L[pg * EVPP:(pg + 1) * EVPP]):
        r = grid(i, 2, 6, TOP + 38, H)
        draw_button(surf, r, name, None, F["small"] if len(name) > 17 else F["btn"], filled=on.get(k, df.get(k, True)),
                    lit=flash.get((v, i), 0) > now)

def tap_evlist(x, y):
    v = ui["view"]
    L, st, pk = _evl(v)
    pages = (len(L) + EVPP - 1) // EVPP
    pg = ui.get(pk, 0) % pages
    on = cfg.setdefault(st, {})
    for i in range(3):
        if grid(i, 3, 1, TOP, TOP + 40).collidepoint(x, y):
            tap_flash((v, 100 + i))
            if i < 2:
                for k, _ in L:
                    on[k] = i == 0
                cfg[EVL[v][3]] = True
                save_cfg()
            else:
                ui[pk] = pg + 1
            return
    for i, (k, _) in enumerate(L[pg * EVPP:(pg + 1) * EVPP]):
        if grid(i, 2, 6, TOP + 38, H).collidepoint(x, y):
            tap_flash((v, i))
            on[k] = not on.get(k, EVL[v][4].get(k, True))
            cfg[EVL[v][3]] = True
            save_cfg()
            return

VIEWS[161] = view_evlist_base
VIEWS[162] = view_evlist_base
VIEWS[163] = view_evlist_base
MENU[163] = "SONIDO Y VOZ"
PARENT[163] = 1244
MENU[161] = "ALERTAS"
MENU[162] = "CAMBIO AUTO"
PARENT[161] = 1244
PARENT[162] = 1244


# ---------- v0.74: PANEL nitido y FPS de la pantalla grande ----------
HI_PASS = [False]
PHI = {"surf": None, "n": -1, "fail": 0.0}
BIGFPS = ["AUTO", "3", "5", "10"]

def panel_hi():
    """El panel (pantalla pequena) dibujado a tamano grande: para la HDMI en modo PANEL y la web /panel."""
    if ui.get("bye"):
        return None
    if PHI["n"] == BIG["n"] and PHI["surf"] is not None:
        return PHI["surf"]
    if time.time() - PHI["fail"] < 60:
        return None
    bw, bh = BIG["w"] or 1024, BIG["h"] or 600
    sc = min(bw / W, bh / H)
    size = (int(W * sc), int(H * sc))
    real = PHI["surf"] if PHI["surf"] is not None and PHI["surf"].get_size() == size else pygame.Surface(size)
    keep = dict(F)
    HI_IDS.clear(); HI_KEEP.clear()
    F.update(hi_fonts(sc))
    HI_PASS[0] = True
    try:
        ss = ScaledSurf(real, sc, sc)
        if ui.get("bye"):
            draw_bye(ss)
        else:
            render(ss); decorate(ss); rhino_banner(ss)
        draw_pointer(ss)
    except Exception as e:
        log_exc("panel nitido", e)
        PHI["fail"] = time.time()
        return None
    finally:
        HI_PASS[0] = False
        F.clear(); F.update(keep)
        HI_IDS.clear(); HI_KEEP.clear()
    PHI.update(surf=real, n=BIG["n"])
    return real

def big_due():
    f = cfg.get("bigfps", "AUTO")
    if f == "AUTO":
        f = "10" if BIG.get("fast") else "3"
    step = {"3": 3, "5": 2, "10": 1}.get(f, 3)
    return BIG["n"] % step == 0


# ---------- v0.77: teclas del juego, indicador de CPU y PANEL ligero ----------
# Que accion del juego hace cada boton (nombres del fichero .binds). Varias = la primera que tenga tecla.
BIND_MAP = {
    "BUTTONS": {"TREN": "LandingGearToggle", "LUCES": "ShipSpotLightToggle", "VISIÓN NOC": "NightVisionToggle",
                "RECOGEDOR": "ToggleCargoScoop", "SUPERCRUC.": "Supercruise|HyperSuperCombination",
                "SILENCIO": "ToggleButtonUpInput", "DISIPADOR": "DeployHeatSink", "CHAFF": "FireChaffLauncher",
                "SALTO FSD": "Hyperspace|HyperSuperCombination", "ESCUDO": "UseShieldCell",
                "MAPA GAL": "GalaxyMapOpen", "MAPA SIS": "SystemMapOpen"},
    "PIP_COLS": {"SISTEMAS": "IncreaseSystemsPower", "MOTORES": "IncreaseEnginesPower", "ARMAS": "IncreaseWeaponsPower"},
    "SRV_BTNS": {"FAROS": "HeadlightsBuggyButton", "TORRETA": "ToggleBuggyTurretButton",
                 "RECOGER": "ToggleCargoScoop_Buggy", "NAVE": "RecallDismissShip",
                 "MAPA GAL": "GalaxyMapOpen_Buggy|GalaxyMapOpen", "MAPA SIS": "SystemMapOpen_Buggy|SystemMapOpen"},
    "PIE_BTNS": {"LINTERNA": "HumanoidToggleFlashlightButton", "VISIÓN NOC": "HumanoidToggleNightVisionButton",
                 "ESCUDO": "HumanoidToggleShieldsButton", "BOTIQUÍN": "HumanoidHealthPack",
                 "BATERÍA": "HumanoidBattery", "RECARGAR": "HumanoidReloadButton"},
    "COMBAT_BTNS": {"OBJETIVO": "SelectTarget", "SIGUIENTE": "CycleNextTarget", "ANTERIOR": "CyclePreviousTarget",
                    "PELIGROSO": "SelectHighestThreat", "SU OBJ.": "SelectTargetsTarget",
                    "SUBSIST.": "CycleNextSubsystem|CyclePreviousSubsystem", "ALA 1": "TargetWingman0",
                    "ALA 2": "TargetWingman1", "ALA 3": "TargetWingman2", "CHAFF": "FireChaffLauncher",
                    "DISIPADOR": "DeployHeatSink", "ESCUDO": "UseShieldCell"},
    "FIGHTER_BTNS": {"DEFENSIVO": "OrderDefensiveBehaviour", "AGRESIVO": "OrderAggressiveBehaviour",
                     "ATACAR": "OrderFocusTarget", "ALTO FUEGO": "OrderHoldFire", "POSICIÓN": "OrderHoldPosition",
                     "SEGUIRME": "OrderFollow", "VOLVER": "OrderRequestDock", "ÓRDENES": "OpenOrders"},
}
PIP_RESET_ACT = "ResetPowerDistribution"
SIN = "SIN TECLA"
BINDS = {"sig": None, "file": None, "missing": [], "free": [], "page": 0}
_BDEF = {}

def apply_binds(B):
    """Pone en los botones las teclas del juego (las manda el sender). Sin datos: las de fabrica."""
    g = globals()
    if not _BDEF:
        for name in BIND_MAP:
            _BDEF[name] = list(g[name])
        _BDEF["PIP_PRESETS"] = list(PIP_PRESETS)
    keys = (B or {}).get("keys") if B else None
    missing = []
    for name, amap in BIND_MAP.items():
        new = []
        for it in _BDEF[name]:
            it = list(it)
            if keys is not None and it[0] in amap:
                acts = amap[it[0]].split("|")
                k = next((keys[a] for a in acts if a in keys and key_ok(keys[a])), None)
                if k is None:
                    missing.append((it[0], acts[0], (B.get("bad") or {}).get(acts[0])))
                it[1] = k or SIN
            new.append(tuple(it))
        g[name][:] = new
    if keys is not None:
        r = keys.get(PIP_RESET_ACT) if key_ok(keys.get(PIP_RESET_ACT)) else None
        if r is None:
            missing.append(("RESET PIPS", PIP_RESET_ACT, (B.get("bad") or {}).get(PIP_RESET_ACT)))
        sy, mo, ar = [k for _, k in PIP_COLS]
        PIP_PRESETS[:] = [("RESET", [r or SIN]), ("MAX SIS", [r or SIN] + [sy] * 4),
                          ("MAX MOT", [r or SIN] + [mo] * 4), ("MAX ARM", [r or SIN] + [ar] * 4)]
    else:
        PIP_PRESETS[:] = _BDEF["PIP_PRESETS"]
    seen, uniq = set(), []
    for m in missing:
        if (m[0], m[1]) not in seen:
            seen.add((m[0], m[1])); uniq.append(m)
    BINDS.update(file=(B or {}).get("file") if keys is not None else None, missing=uniq,
                 free=list((B or {}).get("free") or []))

def binds_check(d):
    B = (d or {}).get("binds")
    sig = (B or {}).get("file"), len((B or {}).get("keys") or {}), str(sorted(((B or {}).get("keys") or {}).items()))[:4000]
    if B and sig != BINDS["sig"]:
        BINDS["sig"] = sig
        apply_binds(B)
        if BINDS["missing"] and ev_on("keys"):
            set_alert("TECLAS DEL JUEGO", f"{len(BINDS['missing'])} botones sin tecla: AJUSTES > OPCIONES > TECLAS", ORANGE, 5)

def view_keys(surf, d, flags, now):
    y = TOP + 4
    if not BINDS["file"]:
        put(surf, F["btn"], "Teclas de fábrica del panel", (8, y), ORANGE); y += 24
        for t in ["El sender del PC no ha mandado tus controles.",
                  "Actualiza elite_sender.py (v0.77) en el PC de juego:",
                  "lee el fichero .binds que usa el juego y el panel",
                  "pone en cada botón tu tecla."]:
            put(surf, F["small"], t, (8, y), DIM, W - 16); y += 18
        return
    miss = BINDS["missing"]
    put(surf, F["btn"], BINDS["file"], (8, y), ORANGE, W - 16); y += 22
    if not miss:
        put(surf, F["btn"], "Todos los botones tienen tecla", (8, y + 6), GREEN); y += 34
        put(surf, F["small"], "El panel usa las teclas de tus controles del juego.", (8, y), DIM, W - 16)
        return
    put(surf, F["small"], f"{len(miss)} botones sin tecla de teclado. Asígnales en el juego (OPCIONES > CONTROLES)",
        (8, y), DIM, W - 16); y += 16
    put(surf, F["small"], "una de estas teclas, que no usas:", (8, y), DIM, W - 16); y += 20
    free = BINDS["free"]
    per = 6
    pages = max(1, (len(miss) + per - 1) // per)
    pg = BINDS["page"] % pages
    for i, (lab, act, bad) in enumerate(miss[pg * per:(pg + 1) * per]):
        j = pg * per + i
        put(surf, F["btn"], lab, (8, y), WHITE, 120)
        put(surf, F["small"], act, (132, y + 4), DIM, 210)
        sug = f"tecla {bad.replace('Key_', '')} no válida" if bad else (free[j] if j < len(free) else "")
        put(surf, F["btn"], sug, (W - 8, y), RED if bad else GREEN, 130, anchor="topright")
        y += 26
    if pages > 1:
        put(surf, F["small"], f"pág {pg + 1}/{pages}  (toca)", (W - 8, H - 18), DIM, anchor="topright")

def tap_keys(x, y):
    BINDS["page"] += 1

VIEWS[164] = view_keys
MENU[164] = "TECLAS DEL JUEGO"
PARENT[164] = 1244

# --- consumo: CPU del panel (como top), temperatura de la Pi y FPS de la pantalla grande
PERF = {"t": 0.0, "cpu": None, "temp": None, "fps": 0.0, "frames": 0, "f0": 0, "c0": None, "w0": None}



def perf_draw(S, x, y):
    f = BIG.get("pfont") or BIG.setdefault("pfont", pygame.font.Font(None, 20))
    for i, (t, col) in enumerate(perf_parts()):
        if i:
            x += put(S, f, "·", (x + 6, y), DIM) + 12
        x += put(S, f, t, (x, y), col)




# ---------- v0.80: ficha ESCUADRON (al abrir el menu de escuadron del juego) ----------
INARA_RK = {"combat": "Combat", "trade": "Trade", "exploration": "Explore", "soldier": "Soldier",
            "mercenary": "Soldier", "exobiologist": "Exobiologist", "federation": "Federation", "empire": "Empire"}

def inara_rank(o, which="combat"):
    for n, v, _ in (o or {}).get("ranks") or []:
        if str(n).lower() == which and INARA_RK.get(which) in RANK_NAMES and isinstance(v, int):
            return rank_name(INARA_RK[which], v)
    return ""

SQ_PER = 6

def squad_pages(d):
    oth = (((d or {}).get("inara") or {}).get("others")) or []
    return 1 + (len(oth) + SQ_PER - 1) // SQ_PER

def view_squad_page(surf, d, pg):
    """Pagina pg (1..): miembros con nave, rango de combate, escuadron y si estan conectados."""
    ina = d.get("inara") or {}
    on = set((d.get("friends") or {}).get("on") or [])
    oth = sorted(ina.get("others") or [], key=lambda o: (o.get("name") not in on, (o.get("name") or "").lower()))
    y = TOP + 6
    put(surf, F["small"], "COMANDANTE", (8, y), DIM)
    put(surf, F["small"], "NAVE  ·  COMBATE  ·  ESCUADRÓN", (170, y), DIM); y += 18
    for o in oth[(pg - 1) * SQ_PER:pg * SQ_PER]:
        live = o.get("name") in on
        pygame.draw.circle(surf, GREEN if live else DIM, (14, y + 10), 5, 0 if live else 1)
        put(surf, F["btn"], o.get("name", "?"), (26, y + 2), GREEN if live else ORANGE, 140)
        bits = [o.get("ship"), inara_rank(o), o.get("squad")]
        ph_ = cfg.get("cmdrpics", True) and (o.get("avatar") or o.get("ship")) and (avatar_photo(surf, o.get("avatar"), pygame.Rect(W - 60, y + 3, 52, 29)) or ship_photo(surf, {"ship": o.get("ship")}, {}, pygame.Rect(W - 60, y + 3, 52, 29)))
        put(surf, F["small"], "  ·  ".join(b for b in bits if b) or "sin datos públicos", (170, y + 6), DIM, W - (240 if ph_ else 178))
        y += 36
    put(surf, F["small"], f"pág {pg + 1}/{squad_pages(d)}  ·  verde = conectado  ·  toca", (W - 8, H - 16), DIM,
        W - 16, anchor="topright")

def tap_squad(x, y):
    with lock:
        d = state["data"]
    ui["sqpage"] = (ui.get("sqpage", 0) + 1) % squad_pages(d)

def view_squad(surf, d, flags, now):
    d = d or {}
    pg = ui.get("sqpage", 0) % squad_pages(d)
    if pg:
        return view_squad_page(surf, d, pg)
    sq = d.get("squad") or {}
    fr = d.get("friends") or {}
    ina = d.get("inara") or {}
    me = ina.get("me") or {}
    y = TOP + 6
    name = sq.get("name") or me.get("squad")
    if name:
        put(surf, F["big"], name.upper(), (8, y), ORANGE, W - 16); y += 30
        rk = me.get("sqrank") or (f"rango {sq['rank']}" if sq.get("rank") is not None else "")
        if rk:
            n_ = f"  ·  {me['sqn']} miembros" if me.get("sqn") else ""
            put(surf, F["btn"], f"tu rango: {rk}{n_}", (8, y), BLUE, W - 16); y += 24
    else:
        put(surf, F["btn"], "Sin escuadrón (o aún no hay datos)", (8, y), DIM, W - 16); y += 26
    pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 6
    wing = fr.get("wing") or []
    if wing:
        put(surf, F["small"], "ALA", (8, y), DIM)
        put(surf, F["btn"], ", ".join(str(w) for w in wing)[:50], (60, y - 3), GREEN, W - 68); y += 22
    on = fr.get("on") or []
    put(surf, F["small"], f"AMIGOS CONECTADOS ({len(on)})", (8, y), DIM); y += 16
    put(surf, F["btn"], ", ".join(on[:5]) if on else "ninguno ahora mismo", (8, y), GREEN if on else DIM, W - 16); y += 26
    oth = ina.get("others") or []
    if oth:
        n_on = sum(1 for o in oth if o.get("name") in on)
        put(surf, F["small"], "INARA", (8, y), DIM); y += 16
        put(surf, F["btn"], f"{len(oth)} comandantes  ·  {n_on} conectados  ·  toca para verlos", (8, y), ORANGE, W - 16)
    if ina.get("ok"):
        mins = int((time.time() - (ina.get("t") or time.time())) // 60)
        st = f"Inara: hace {mins} min" if mins else "Inara: al día"
    else:
        st = "Inara: sin datos" + (f" ({ina['err']})" if ina.get("err") else "")
    put(surf, F["small"], st, (W - 8, H - 16), DIM, W - 16, anchor="topright")

VIEWS[165] = view_squad
MENU[165] = "ESCUADRÓN"
PARENT[165] = 0


# ---------- v0.83: consumibles a la vista y EN COMBATE a pie en grande ----------
# maximo de explosivos por traje (comprobado por el CMDR): fragmentacion, disruptor (EMP), proyector de escudo
SUIT_EXPL = {"dominator": (3, 3, 2), "maverick": (2, 1, 1), "artemis": (1, 1, 1), "vuelo": (0, 0, 0), "flight": (0, 0, 0)}
EXPL = [("frag", "FRAG."), ("emp", "DISRUPT."), ("shield", "PROYECT.")]

def cons_kind(name):
    n = (name or "").lower()
    if "frag" in n:
        return "frag"
    if "emp" in n or "disrup" in n or "supres" in n:
        return "emp"
    if "proyect" in n or "project" in n or "grenade_shield" in n:
        return "shield"
    if "botiqu" in n or "health" in n or "medkit" in n:
        return "med"
    if "lula" in n or "energycell" in n or "energy cell" in n or "cell" in n:
        return "cell"
    return None

def cons_count(d):
    out = {}
    for it in (((d or {}).get("pack") or {}).get("cons") or []):
        k = cons_kind(it[0])
        if k:
            out[k] = out.get(k, 0) + (it[1] or 0)
    return out

def suit_name_of(d):
    d = d or {}
    return str(((d.get("live") or {}).get("suit") or {}).get("name") or (d.get("footcz") or {}).get("suit") or "")

def suit_max(d):
    sn = suit_name_of(d).lower()
    t = next((v for k, v in SUIT_EXPL.items() if k in sn), None)
    return dict(zip(("frag", "emp", "shield"), t)) if t else {}

def cons_col(n, mx=None):
    if n <= 1:
        return RED
    if mx and n < mx:
        return ORANGE
    return GREEN

def draw_med(surf, x, y, k, col):
    a, b = int(5 * k), int(2 * k)
    pygame.draw.rect(surf, col, (x - b, y - a, 2 * b, 2 * a))
    pygame.draw.rect(surf, col, (x - a, y - b, 2 * a, 2 * b))

def draw_pips(surf, x, y, n, mx, w, h):
    for i in range(max(mx, n)):
        r = pygame.Rect(x + i * (w + 4), y, w, h)
        if i < n:
            pygame.draw.rect(surf, cons_col(n, mx), r)
        else:
            pygame.draw.rect(surf, DIM, r, 1)
    return max(mx, n) * (w + 4)

def draw_cons_row(surf, d, x, y, font, ph):
    """Una fila: + botiquines, rayo celulas, y los explosivos con barritas segun el traje."""
    c, mx = cons_count(d), suit_max(d)
    h_ = font.get_height()
    draw_med(surf, x + 7, y + h_ // 2, h_ / 18, cons_col(c.get("med", 0)))
    x += 16 + put(surf, font, str(c.get("med", 0)), (x + 18, y), cons_col(c.get("med", 0))) + 8
    draw_bolt(surf, x, y + 1, cons_col(c.get("cell", 0)), h_ / 22)
    x += 14 + put(surf, font, str(c.get("cell", 0)), (x + 14, y), cons_col(c.get("cell", 0))) + 10
    for k, lab in EXPL:
        if not mx.get(k) and not c.get(k):
            continue
        x += put(surf, F["small"], lab, (x, y + h_ // 2 - 6), DIM) + 4
        x += draw_pips(surf, x, y + h_ // 2 - ph // 2, c.get(k, 0), mx.get(k, 0), ph, ph) + 8
    return y + h_

def draw_fight_big(surf, d, now):
    """EN COMBATE a pie: lo importante en grande para mirarlo de reojo."""
    L, Z = d.get("live") or {}, d.get("footcz") or {}
    led = Z.get("led") or {}
    y = TOP + 2
    on_ = int(now * 2) % 2 == 0
    r_ = pygame.Rect(8, y, 200, 30)
    pygame.draw.rect(surf, RED, r_, 0 if on_ else 3, border_radius=6)
    put(surf, F["big"], "EN COMBATE", r_.center, BLACK if on_ else RED, anchor="center")
    put(surf, F["small"], suit_name_of(d), (W - 8, y + 8), ORANGE, 250, anchor="topright")
    y += 36
    hp = pctv(L.get("health"))
    sd = (d.get("combat") or {}).get("sd")
    hb = pygame.Rect(8, y, W - 160, 22)
    pygame.draw.rect(surf, DIM, hb, 1)
    if hp is not None:
        pygame.draw.rect(surf, RED if hp < 25 else ORANGE if hp < 50 else GREEN,
                         (hb.x + 2, hb.y + 2, int((hb.w - 4) * max(0, min(100, hp)) / 100), hb.h - 4))
    put(surf, F["btn"], f"SALUD {hp:.0f} %" if hp is not None else "SALUD ?", hb.center, WHITE, anchor="center")
    sr = pygame.Rect(W - 146, y, 138, 22)
    if sd:
        el = int(now - sd)
        pygame.draw.rect(surf, RED, sr, 0 if on_ else 2, border_radius=4)
        put(surf, F["btn"], f"ESCUDO {el // 60:02d}:{el % 60:02d}", sr.center, BLACK if on_ else RED, anchor="center")
    else:
        pygame.draw.rect(surf, BLUE, sr, 2, border_radius=4)
        put(surf, F["btn"], "ESCUDO OK", sr.center, BLUE, anchor="center")
    y += 28
    # bajas y consumibles en grande
    put(surf, F["num"], str(Z.get("n") or 0), (8, y), GREEN)
    put(surf, F["small"], "BAJAS", (12 + F["num"].size(str(Z.get("n") or 0))[0], y + 26), GREEN)
    tf_ = (d.get("career") or {}).get("foot")
    if tf_ is not None:
        put(surf, F["small"], f"total {fnum(tf_, 0)}", (12 + F["num"].size(str(Z.get("n") or 0))[0], y + 8), DIM)
    c = cons_count(d)
    x = W - 8
    for k in ("cell", "med"):
        n = c.get(k, 0)
        tw = F["num"].size(str(n))[0]
        put(surf, F["num"], str(n), (x, y), cons_col(n), anchor="topright")
        x -= tw + 6
        if k == "med":
            draw_med(surf, x - 14, y + 20, 2.4, cons_col(n)); x -= 36
        else:
            draw_bolt(surf, x - 22, y + 2, cons_col(n), 1.9); x -= 40
    y += 48
    put(surf, F["big"], f"{crx(led.get('cr', 0))} cr", (8, y), ORANGE)
    put(surf, F["small"], "sin cobrar", (12 + F["big"].size(f"{crx(led.get('cr', 0))} cr")[0], y + 10), DIM)
    if Z.get("rate"):
        put(surf, F["btn"], f"{str(Z['rate']).replace('.', ',')} / min", (W - 8, y + 4), DIM, anchor="topright")
    y += 34
    # explosivos con barritas gruesas
    mx = suit_max(d)
    x = 8
    for k, lab in EXPL:
        if not mx.get(k) and not c.get(k):
            continue
        x += put(surf, F["btn"], lab, (x, y + 2), DIM) + 6
        x += draw_pips(surf, x, y, c.get(k, 0), mx.get(k, 0), 18, 22) + 14
    y += 30
    zt = (Z.get("zone") or "").upper() + (f"  ·  por {Z['side']}" if Z.get("side") else "")
    put(surf, F["small"], "  ·  ".join(t for t in (zt, L.get("weapon")) if t), (8, H - 18), DIM, W - 16)


# ---------- v0.84: boton ESCUADRON y cierre de emergencia del juego ----------
SQ_BTN = pygame.Rect(W - 160, H - 36, 152, 32)
KILL_PORT, KILL_MSG = 5006, b"ELITEPANEL-KILL"
KILL = {"taps": [], "t0": None, "sent": 0.0, "seq": None}
KILL_SECS = 3.0
KILL_CANCEL = pygame.Rect(W // 2 - 110, H - 90, 220, 60)

def kill_title_rect():
    # KILL zona v085: toda la barra de arriba entre MENU y el engranaje; con pestanas, solo la franja del nombre
    v = ui.get("view")
    h = 30 if tab_group(v)[0] else TOP - 4
    return pygame.Rect(BACK.right, 0, GEAR.x - 8 - BACK.right, h)

def kill_tap(x, y):
    """3 toques en el nombre del sistema: cuenta atras y el sender cierra el juego. Cualquier toque cancela."""
    now = time.time()
    if KILL["t0"]:
        KILL["t0"] = None
        set_alert("CIERRE CANCELADO", "", GREEN, 1.5, "ok")
        return True
    if not cfg.get("killbtn", True) or not kill_title_rect().collidepoint(x, y):
        return False
    KILL["taps"] = [t for t in KILL["taps"] if now - t < 2.5] + [now]
    if len(KILL["taps"]) >= 3:
        KILL["taps"] = []
        KILL["t0"] = now
        play("alarm")
    else:
        ui["toast"] = (f"CERRAR JUEGO: toque {len(KILL['taps'])} de 3", now + 2)
    return True

def kill_send():
    pc = None
    try:
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pc_ip.txt")
        pc = open(f).read().strip() or None
    except Exception:
        pass
    pc = pc or state.get("pc")
    if not pc:
        set_alert("NO SÉ LA IP DEL PC", "el sender no está enviando", RED, 3)
        return
    try:
        so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        so.sendto(KILL_MSG, (pc, KILL_PORT))
        so.close()
        KILL["sent"] = time.time()
        set_alert("CERRANDO ELITE...", f"orden enviada al PC {pc}", ORANGE, 4)
    except OSError as e:
        set_alert("NO SE PUDO ENVIAR", str(e)[:40], RED, 3)

def draw_kill(surf, now):
    with lock:
        d = state["data"] or {}
    kr = d.get("killres") or {}
    if kr.get("seq") is not None and kr.get("seq") != KILL["seq"]:
        first = KILL["seq"] is None and now - KILL["sent"] > 30
        KILL["seq"] = kr.get("seq")
        if not first:
            set_alert("JUEGO CERRADO" if kr.get("ok") else "NO SE PUDO CERRAR", kr.get("msg", ""),
                      GREEN if kr.get("ok") else RED, 4)
    if not KILL["t0"]:
        return
    el = now - KILL["t0"]
    if el >= KILL_SECS:
        KILL["t0"] = None
        kill_send()
        return
    n = 3 - int(el / (KILL_SECS / 3))
    surf.fill(RED)
    put(surf, F["big"], "CERRANDO ELITE DANGEROUS", (W // 2, 40), (255, 215, 0), W - 16, anchor="center")
    put(surf, F["clock"], str(n), (W // 2, 130), (255, 215, 0), anchor="center")
    pygame.draw.rect(surf, BLACK, KILL_CANCEL, border_radius=10)
    pygame.draw.rect(surf, (255, 215, 0), KILL_CANCEL, 3, border_radius=10)
    put(surf, F["big"], "CANCELAR", KILL_CANCEL.center, (255, 215, 0), anchor="center")
    put(surf, F["small"], "toca en cualquier sitio para cancelar", (W // 2, H - 18), BLACK, anchor="center")


# ---------- v0.86: salud critica a pie ----------
HP_CRIT = 0.30
HPC = {"t0": None}
_HPF = {}

def draw_hpcrit(surf, now):
    """Salud < 30 % a pie: 3 s de pantalla roja parpadeando deprisa y luego borde rojo hasta que te cures."""
    if HPC["t0"] is None:
        return
    with lock:
        d = state["data"] or {}
    hp = (d.get("live") or {}).get("health")
    if not (d.get("Flags2", 0) & 1) or hp is None or hp >= HP_CRIT:
        HPC["t0"] = None
        return
    w, h = surf.get_size()
    on = int(now * 10) % 2 == 0                      # 5 parpadeos por segundo
    if now - HPC["t0"] < 3:
        surf.fill(RED if on else BLACK)
        k = h / 320
        key = round(k, 2)
        if key not in _HPF:
            _HPF[key] = (pygame.font.Font(None, int(96 * k)), pygame.font.Font(None, int(44 * k)))
        f1, f2 = _HPF[key] if type(surf).__name__ != "ScaledSurf" else (F["num"], F["big"])
        col = (255, 215, 0) if on else RED
        put(surf, f1, f"¡SALUD {hp * 100:.0f} %!", (w // 2, int(h * 0.38)), col, anchor="center")
        put(surf, f2, "¡BOTIQUÍN YA!", (w // 2, int(h * 0.66)), col, anchor="center")
    elif on:
        t = max(4, h // 50)
        pygame.draw.rect(surf, RED, (0, 0, w, h), t)


# ---------- v0.87: avisos de bajas en un cuadro e Inara del CMDR fijado ----------
def kill_in_cell(a):
    return a.get("ev") == "kill" and cfg.get("bigmode", "4") != "GRANDE"

def draw_kill_cell(now):
    """Baja a pie -> en el cuadro SRV / A PIE; derribo en nave -> en el cuadro 3. El resto de cuadros, a la vista."""
    a = xa.get("a")
    rects = BIG.get("rects") or []
    if not a or now > a["until"] or not kill_in_cell(a) or not rects or hdmi_panel():
        return
    foot = str(a.get("title", "")).startswith("BAJA")
    r = next((rr for v, rr in rects if v == 5), None) if foot else None
    if r is None:
        r = rects[2][1] if len(rects) >= 3 else rects[-1][1]
    S, cell = BIG["surf"], BIG["cell"]
    pygame.draw.rect(S, BLACK, r)
    cell.fill(BLACK)
    draw_xa(cell, now)
    big_blit(S, cell, r.inflate(-6, -6))

def my_squad(d):
    d = d or {}
    return (d.get("squad") or {}).get("name") or ((d.get("inara") or {}).get("me") or {}).get("squad") or ""

def inara_line(ia, d, short=False):
    bits = [ia.get("squad"), inara_rank(ia), None if short else ia.get("ship"), None if short else ia.get("power")]
    return "  ·  ".join(b for b in bits if b) or "sin datos públicos"


# ---------- v0.88: NAVE, FLOTA y cambio de nave ----------
SHIP_NAME_R = pygame.Rect(W - 260, TOP, 260, 34)
SHIP_PER = 8

def veh_chips(d, rh):
    v = ((d or {}).get("naves") or {}).get("veh") or {}
    out = []
    if v.get("srvcap") and not rh and v.get("srv"):
        n = max(0, v["srvcap"] - (v.get("srvlost") or 0))
        st = v["srv"]
        lab = f"SRV A BORDO {n}/{v['srvcap']}" if st == "A BORDO" else ("SIN SRV" if n == 0 else f"SRV {st}")
        out.append((lab, True, GREEN if st == "A BORDO" and n else RED if n == 0 else ORANGE))
    if v.get("fighter"):
        f = v["fighter"]
        out.append((f"CAZA {f}", True, GREEN if f == "LISTO" else RED if f == "RECONSTRUYENDO" else ORANGE))
    return out

def _mod_col(h):
    return RED if h < 80 else ORANGE if h < 95 else GREEN

def view_ship(surf, d, flags, now):
    N = (d or {}).get("naves") or {}
    c = N.get("cur")
    if not c:
        put(surf, F["btn"], "Sin datos de la nave", (W // 2, (H + TOP) // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], "llegan al cargar la partida o al equiparla (sender v0.88)", (W // 2, (H + TOP) // 2 + 12), DIM, anchor="center")
        return
    y = TOP + 4
    ph_ = ship_photo(surf, c, d or {}, pygame.Rect(W - 104, TOP + 2, 96, 54))
    put(surf, F["big"], (c.get("ship") or "?").upper(), (8, y), ORANGE, W // 2)
    put(surf, F["small"], " · ".join(x for x in (c.get("name"), c.get("ident")) if x), (W - (112 if ph_ else 8), y + 6), DIM,
        W // 2 - (110 if ph_ else 10), anchor="topright")
    y += 28
    stats = [("SALTO", f"{c['jump']:.1f} al" if c.get("jump") else "-"), ("COMB.", f"{c.get('fuel') or 0:g} t"),
             ("CARGA", f"{c.get('cargo') or 0} t"), ("MASA", f"{c.get('mass') or 0:.0f} t"), ("VALOR", f"{crx(c.get('value') or 0)}")]
    stats = [x for x in stats if x[0] != "VALOR" or c.get("value")]
    cw = (W - (128 if ph_ else 16)) // len(stats)
    for i, (k, v) in enumerate(stats):
        put(surf, F["small"], k, (8 + i * cw, y), DIM)
        put(surf, F["btn"], v.replace(".", ","), (8 + i * cw, y + 12), WHITE, cw - 4)
    y += 36
    fb = c.get("fbay")
    if fb:
        crew = ((d.get("ops") or {}).get("crew") or {})
        fs = (N.get("veh") or {}).get("fighter") or "-"
        put(surf, F["small"], f"HANGAR DE CAZAS · caza {fs}" + (f" · piloto {crew.get('name')}" if crew.get("name") else ""),
            (8, y), BLUE, W - 16); y += 16
    mods = sorted(c.get("mods") or [], key=lambda m: m["h"] >= 80)          # danados arriba
    pages = max(1, (len(mods) + SHIP_PER - 1) // SHIP_PER)
    pg = ui.get("shippage", 0) % pages
    for m in mods[pg * SHIP_PER:(pg + 1) * SHIP_PER]:
        put(surf, F["small"], m.get("s") or "", (8, y + 1), DIM)
        w_ = put(surf, F["btn"], m["n"], (34, y - 2), RED if m["h"] < 80 else ORANGE, 220)
        if m.get("e"):
            put(surf, F["small"], m["e"], (40 + max(w_, 0), y + 1), BLUE, W - 100 - w_)
        put(surf, F["small"], f"{m['h']}%", (W - 8, y + 1), _mod_col(m["h"]), anchor="topright")
        y += 20
    put(surf, F["small"], f"pág {pg + 1}/{pages}  ·  toca para pasar" if pages > 1 else f"{len(mods)} módulos",
        (W - 8, H - 16), DIM, anchor="topright")

def view_fleet(surf, d, flags, now):
    N = (d or {}).get("naves") or {}
    y = TOP + 4
    for x in N.get("xfer") or []:
        left = max(0, int(x.get("arrive", now) - time.time()))
        put(surf, F["small"], f"EN CAMINO: {x.get('ship', '?')} > {x.get('to') or '?'}  ·  quedan "
                              f"{left // 3600} h {left % 3600 // 60} min" if left >= 3600 else
                              f"EN CAMINO: {x.get('ship', '?')} > {x.get('to') or '?'}  ·  quedan {left // 60} min {left % 60} s",
            (8, y), BLUE, W - 16); y += 16
    fl = N.get("fleet") or []
    if not fl:
        put(surf, F["btn"], "Abre el astillero en una estación", (W // 2, (H + TOP) // 2 - 10), DIM, anchor="center")
        put(surf, F["small"], "y el panel guardará dónde están tus naves", (W // 2, (H + TOP) // 2 + 12), DIM, anchor="center")
        return
    t = N.get("fleet_t")
    put(surf, F["small"], f"{len(fl)} naves guardadas" + (f" · astillero del {time.strftime('%d/%m %H:%M', time.localtime(t))}" if t else ""),
        (8, y), DIM, W - 16); y += 16
    put(surf, F["small"], "SALTO  CARGA  ARMAS", (W - 8, y), DIM, anchor="topright"); y += 14
    per = 6
    pages = max(1, (len(fl) + per - 1) // per)
    pg = ui.get("shippage", 0) % pages
    fl = sorted(fl, key=lambda f: (not f.get("here"), f.get("transit", False), f.get("sys") or ""))
    for f in fl[pg * per:(pg + 1) * per]:
        nm = f.get("name") or ""
        ph_ = ship_photo(surf, f, d or {}, pygame.Rect(8, y + 1, 54, 30))
        x_ = 68 if ph_ else 8
        put(surf, F["btn"], (f.get("ship") or "?") + (f" «{nm}»" if nm and nm != f.get("ship") else ""), (x_, y), ORANGE, W - 170 - x_ + 8)
        sub = "AQUÍ" if f.get("here") else ("en tránsito" if f.get("transit") else f.get("sys") or "?")
        if not f.get("here") and f.get("xtime"):
            sec = int(f["xtime"])
            sub += f"  ·  traer: {sec // 3600} h {sec % 3600 // 60} min · {crx(f.get('xprice') or 0)} cr"
        put(surf, F["small"], sub, (x_, y + 18), GREEN if f.get("here") else DIM, W - 8 - x_)
        cols = [f"{f['jump']:.0f}" if f.get("jump") else "-", f"{f['cargo']}" if f.get("cargo") is not None else "-",
                f"{f['weapons']}" if f.get("weapons") is not None else "-"]
        put(surf, F["btn"], "   ".join(cols), (W - 8, y), WHITE, 160, anchor="topright")
        y += 34
    if pages > 1:
        put(surf, F["small"], f"pág {pg + 1}/{pages}  ·  toca", (W - 8, H - 16), DIM, anchor="topright")

VIEWS[170] = view_ship
VIEWS[171] = view_fleet
MENU[170] = "NAVE"
MENU[171] = "FLOTA"
PARENT[170] = 100
PARENT[171] = 100
TABS.append([(170, "NAVE"), (171, "FLOTA")])
_SCF = {}

def draw_shipcard(surf, now):
    """Al cambiar de nave: todos sus datos a pantalla completa sobre fondo negro (15 s o hasta tocar)."""
    if not ui.get("shipcard") or now > ui["shipcard"]:
        return
    with lock:
        c = ((state["data"] or {}).get("naves") or {}).get("cur")
    if not c:
        return
    w, h = surf.get_size()
    k = h / 320
    key = round(k, 2)
    if key not in _SCF:
        _SCF[key] = [pygame.font.Font(None, int(n * k)) for n in (52, 26, 20, 16)]
    f1, f2, f3, f4 = _SCF[key] if type(surf).__name__ != "ScaledSurf" else (F["num"], F["big"], F["btn"], F["small"])
    surf.fill(BLACK)
    ship_bg(surf, c, (d_sc_() or {}))
    m_ = int(8 * k)
    y = m_
    put(surf, f1, (c.get("ship") or "?").upper(), (m_, y), ORANGE, w - 2 * m_); y += f1.get_height()
    put(surf, f2, " · ".join(x for x in (c.get("name"), c.get("ident")) if x), (m_, y), WHITE, w - 2 * m_); y += f2.get_height() + int(4 * k)
    stats = [("SALTO", f"{c['jump']:.1f} al" if c.get("jump") else "-"), ("COMBUSTIBLE", f"{c.get('fuel') or 0:g} t"),
             ("CARGA", f"{c.get('cargo') or 0} t"), ("MASA", f"{c.get('mass') or 0:.0f} t"), ("VALOR", f"{crx(c.get('value') or 0)} cr")]
    stats = [x for x in stats if x[0] != "VALOR" or c.get("value")]
    cw = (w - 2 * m_) // len(stats)
    for i, (a, b) in enumerate(stats):
        put(surf, f4, a, (m_ + i * cw, y), DIM)
        put(surf, f2, b.replace(".", ","), (m_ + i * cw, y + f4.get_height()), GREEN, cw - 4)
    y += f4.get_height() + f2.get_height() + int(6 * k)
    pygame.draw.line(surf, DIM, (m_, y), (w - m_, y)); y += int(4 * k)
    mods = c.get("mods") or []
    col_w = (w - 3 * m_) // 2
    lh = f3.get_height() + 1
    rows = max(1, (h - y - f4.get_height() - m_) // lh)
    for i, md in enumerate(mods[:rows * 2]):
        x = m_ + (i // rows) * (col_w + m_)
        yy = y + (i % rows) * lh
        tw = put(surf, f3, f"{md.get('s') or ''} {md['n']}".strip(), (x, yy), RED if md["h"] < 80 else ORANGE, int(col_w * 0.55))
        if md.get("e"):
            put(surf, f4, md["e"], (x + tw + int(6 * k), yy + int(3 * k)), BLUE, col_w - tw - int(50 * k))
        put(surf, f4, f"{md['h']}%", (x + col_w, yy + int(3 * k)), _mod_col(md["h"]), anchor="topright")
    put(surf, f4, "NAVE NUEVA  ·  toca para cerrar", (w - m_, h - m_ - f4.get_height()), DIM, anchor="topright")


# ---------- v0.89: transporte, carrera y destello de luces ----------
GLOW = {"luz": 0.0, "nv": 0.0, "prev": None}
GLOW_LBL = {"LUCES": "luz", "LINTERNA": "luz", "FAROS": "luz", "LUCES LARGAS": "luz",
            "VISIÓN NOC": "nv", "VISIÓN NOCT.": "nv"}

def glow_watch(d):
    fl = d.get("Flags", 0)
    foot = bool(d.get("Flags2", 0) & 1)
    if GLOW.get("foot") and not foot and ui.get("alert") and "ESCUDO" in (ui["alert"].get("text") or ""):
        ui["alert"] = None
    GLOW["foot"] = foot
    v4_ = ui["view"] == 4
    if not v4_ or not GLOW.get("v4"):
        ui["tab4"] = 2 if pax_list(d) else 1 if d.get("missions") else 0
        if v4_:
            ui["page4"] = 0
    GLOW["v4"] = v4_
    dk = bool(fl & 1)
    if dk and GLOW.get("dk") is False:
        fight["t"] = 0.0                         # atracado (o reaparecido en estacion): fuera el modo combate
    GLOW["dk"] = dk
    st = (bool(fl & (1 << 8) or fl & (1 << 31)), bool(fl & (1 << 28)))
    pv = GLOW["prev"]
    if pv is not None:
        if st[0] and not pv[0]:
            GLOW["luz"] = time.time()
        if st[1] and not pv[1]:
            GLOW["nv"] = time.time()
    GLOW["prev"] = st

def glow(txt):
    """Al encender: 4 destellos blancos en menos de 1 s y luego su color."""
    k = GLOW_LBL.get(txt)
    if not k:
        return False
    el = time.time() - GLOW[k]
    return el < 0.9 and int(el * 9) % 2 == 0

TAXI_SECS = 300            # tiempo para subir al transporte reservado
TAXI_LOST = 60             # el aviso de perdido se ve 1 minuto

def taxi_left(t, now):
    return (t.get("t0") or now) + (360 if t.get("planet") else 320) - now

def taxi_watch(d, now):
    t = (d or {}).get("taxi") or {}
    k0 = XA_K[0]
    try:
        XA_K[0] = "taxi"
        if t.get("st") != "booked":
            return
        left = taxi_left(t, now)
        key = t.get("t0")
        if 0 < left <= 60 and xa.get("taxi60") != key:
            xa["taxi60"] = key
            xa["a"] = dict(until=now + 6, col=RED, title=t.get("kind") or "TRANSPORTE", big="¡SUBE A LA LANZADERA!",
                           lines=["queda 1 minuto"])
            play("alarm")
        elif -TAXI_LOST < left <= 0 and xa.get("taxilost") != key:
            xa["taxilost"] = key
            xa["a"] = dict(until=now + 6, col=RED, title=t.get("kind") or "TRANSPORTE", big="TRANSPORTE PERDIDO",
                           lines=["se acabó el tiempo para subir"])
    finally:
        XA_K[0] = k0

FSTATE_ES = {"War": "EN GUERRA", "CivilWar": "EN GUERRA CIVIL", "Boom": "AUGE", "Bust": "QUIEBRA",
             "Election": "ELECCIONES", "Expansion": "EXPANSIÓN", "Lockdown": "CONFINAMIENTO", "Outbreak": "EPIDEMIA",
             "CivilUnrest": "DISTURBIOS", "Famine": "HAMBRUNA", "Retreat": "RETIRADA", "Investment": "INVERSIÓN",
             "PirateAttack": "ATAQUE PIRATA", "Terrorism": "TERRORISMO", "Blight": "PLAGA", "Drought": "SEQUÍA"}

def draw_taxi(surf, d, now):
    """Transporte reservado (cuenta atras para subir) o a bordo (fase, altitud, gravedad y zona)."""
    t = d.get("taxi") or {}
    st = t.get("st")
    if st not in ("booked", "aboard"):
        return False
    if st == "booked" and taxi_left(t, now) <= -TAXI_LOST:
        return False
    w_, h_ = surf.get_size()
    military = "MILITAR" in (t.get("kind") or "")
    kind = ("RETIRADA · " if t.get("retreat") else "") + (t.get("kind") or "TRANSPORTE")
    dest = t.get("loc") or t.get("sys") or ""
    y = TOP + 4
    put(surf, F["small"], kind, (8, y), BLUE if not military else ORANGE, W - 16); y += 18
    if st == "booked":
        left = taxi_left(t, now)
        if left <= 0:
            on_ = int(now * 3) % 2 == 0
            put(surf, F["big"], "TRANSPORTE PERDIDO", (W // 2, y + 30), RED if on_ else ORANGE, anchor="center")
            put(surf, F["small"], "se acabó el tiempo para subir", (W // 2, y + 58), DIM, anchor="center")
            return True
        put(surf, F["big"], "TRANSPORTE RESERVADO", (8, y), GREEN); y += 30
        col = GREEN if left > 120 else ORANGE if left > 60 else (RED if int(now * 4) % 2 == 0 else BLACK)
        m_, s_ = int(left) // 60, int(left) % 60
        put(surf, F["num"], f"{m_}:{s_:02d}", (W // 2, y + 26), col, anchor="center"); y += 58
        put(surf, F["btn"], "para subir" if left > 60 else "¡SUBE YA!", (W // 2, y), DIM if left > 60 else RED, anchor="center"); y += 26
        if dest:
            put(surf, F["small"], "DESTINO", (8, y + 4), DIM)
            put(surf, F["btn"], dest.upper(), (80, y), ORANGE, W - 88); y += 24
        if t.get("cost"):
            put(surf, F["small"], f"coste {cr(t['cost'])} cr", (8, y), DIM)
        return True
    put(surf, F["big"], "A BORDO", (8, y), GREEN)
    ph = t.get("phase") or ""
    put(surf, F["big"], ph, (W - 8, y), BLUE, W // 2, anchor="topright"); y += 32
    if dest:
        put(surf, F["small"], "DESTINO", (8, y + 4), DIM)
        put(surf, F["btn"], dest.upper(), (80, y), ORANGE, W - 88); y += 26
    L = d.get("live") or {}
    alt, g = L.get("alt"), L.get("grav")
    if alt is not None or g is not None:
        if alt is not None:
            put(surf, F["small"], "ALTITUD", (8, y + 4), DIM)
            put(surf, F["btn"], f"{alt / 1000:.1f} km".replace(".", ",") if alt >= 1000 else f"{alt:.0f} m", (80, y), ORANGE)
        if g is not None:
            put(surf, F["small"], "GRAVEDAD", (250, y + 4), DIM)
            put(surf, F["btn"], f"{g:.2f} G".replace(".", ","), (W - 8, y), RED if g > 2 else ORANGE, anchor="topright")
        y += 26
    if military and (t.get("zone") or t.get("fac")):
        pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 6
        put(surf, F["small"], "ZONA DE COMBATE", (8, y), DIM); y += 16
        put(surf, F["btn"], (t.get("zone") or "").upper(), (8, y), RED, W - 16); y += 24
        fst = FSTATE_ES.get(t.get("fstate") or "", t.get("fstate") or "")
        put(surf, F["small"], "  ·  ".join(x for x in (t.get("fac"), fst) if x), (8, y), ORANGE, W - 16)
    return True


# ---------- v0.90: linea de ruta, fondos de portanaves y portanaves de escuadron ----------
NEON_G = (57, 255, 20)

def star_kind(c):
    c = c or ""
    if c == "N":
        return "neu"
    if c.startswith("D"):
        return "wd"
    if not c:
        return "?"
    return "ok" if star_ok(c) else "no"

def draw_routeline(surf, d, y, now):
    """Circulos de la ruta: amarillo recolectable, rojo no, azul parpadeando neutrones, blanco parpadeando enana blanca."""
    route = d.get("route") or []
    if not route:
        return y
    total = d.get("routen") or len(route)
    end = d.get("routeend") or route[-1]
    nodes = [[d.get("system") or "?", d.get("curstar")]] + [list(r) for r in route[:9]]
    gap = total > 9
    if gap:
        nodes = nodes[:9] + [list(end)]
    on = int(now * 3) % 2 == 0
    x0, x1, cy = 20, W - 20, y + 12
    n = len(nodes)
    step = (x1 - x0) / max(1, n - 1)
    xs = [int(x0 + i * step) for i in range(n)] if n > 1 else [x0]
    for i in range(n - 1):
        if gap and i == n - 2:
            for k in range(xs[i] + 8, xs[i + 1] - 6, 6):
                pygame.draw.line(surf, DIM, (k, cy), (k + 2, cy), 2)
        else:
            pygame.draw.line(surf, DIM, (xs[i], cy), (xs[i + 1], cy), 2)
    for i, (name, c) in enumerate(nodes):
        k = star_kind(c)
        col = {"ok": YELLOW, "no": RED, "neu": BLUE if on else DIM, "wd": WHITE if on else DIM, "?": DIM}[k]
        r = 9 if i == 0 else 7 if i < n - 1 or not gap else 8
        pygame.draw.circle(surf, col, (xs[i], cy), r)
        if i == 0:
            pygame.draw.circle(surf, ORANGE, (xs[i], cy), r + 4, 2)
        if i == n - 1:
            pygame.draw.circle(surf, GREEN, (xs[i], cy), r + 4, 2)
    y += 28
    nxt = route[0][0] if route else ""
    put(surf, F["small"], f"{(d.get('system') or '?')}  >  {nxt}", (8, y), ORANGE, W - 150)
    eg_ = eng_at((end or [""])[0]) if end else None
    put(surf, F["small"], f"quedan {total}" + (f" · {end[0]}" if end and total > 1 else ""), (W - 8, y), DIM, 140, anchor="topright")
    if eg_:
        put(surf, F["small"], "ING. " + eg_["name"], (W - 8, y - 30), BLUE, 200, anchor="topright")
    fj_, fm_ = d.get("fuelj"), (d.get("Fuel") or {}).get("FuelMain")
    if fj_ and fm_ is not None:
        n_ = int(fm_ / fj_) if fj_ > 0 else 0
        put(surf, F["small"], f"combustible para ~{n_} saltos" + ("  ·  ¡recoge en la ruta!" if n_ < min(total, 6) else ""),
            (8, y + 14), RED if n_ < 3 else ORANGE if n_ < min(total, 6) else GREEN, W - 16)
        return y + 36
    return y + 22

_BG = {}
BG_FILES = {"fc": "fondo_portanaves.jpg", "sq": "fondo_escuadron.jpg"}
ST_BG = {"Coriolis": "coriolis", "Orbis": "orbis", "Ocellus": "ocellus", "Bernal": "ocellus", "Dodec": "dodec",
         "AsteroidBase": "asteroide", "Outpost": "outpost", "MegaShip": "meganave", "CraterPort": "craterport",
         "SurfaceStation": "craterport", "CraterOutpost": "crateroutpost", "OnFootSettlement": "asentamiento"}
BG_FILES.update({v: f"fondo_{v}.jpg" for v in set(ST_BG.values())})



def view_carrier90(surf, d, flags, now):
    view_carrier(surf, d, flags, now)
    sq = (d or {}).get("sqcarrier") or {}
    if sq.get("system"):
        pygame.draw.rect(surf, BLACK, (0, H - 24, W, 24))
        pygame.draw.line(surf, DIM, (8, H - 24), (W - 8, H - 24))
        put(surf, F["small"], "PORTANAVES DE ESCUADRÓN", (8, H - 18), BLUE)
        put(surf, F["btn"], sq["system"], (W - 8, H - 21), BLUE, W - 200, anchor="topright")

VIEWS[126] = view_carrier90


# ---------- v0.90c: miniatura del portanaves de destino ----------
import re as _re
CALLSIGN = _re.compile(r"\b[A-Z0-9]{3}-[A-Z0-9]{3}\b")


def bg_img(k, w, h, dark=95):
    key = (k, w, h, dark)
    if key not in _BG:
        img = None
        try:
            src = pygame.image.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), BG_FILES[k]))
            sw, sh = src.get_size()
            sc = max(w / sw, h / sh)
            img = pygame.transform.smoothscale(src, (int(sw * sc) + 1, int(sh * sc) + 1))
            img = img.subsurface(pygame.Rect((img.get_width() - w) // 2, (img.get_height() - h) // 2, w, h)).copy()
            if dark < 255:
                img.fill((dark, dark, dark), special_flags=pygame.BLEND_MULT)
        except Exception as e:
            log_exc("foto " + k, e)
        _BG[key] = img
    return _BG[key]

THUMB_TOP = H - 130                                  # foto del destino: 220x124 abajo a la derecha

def route_thumb(surf, d):
    k, label = carrier_dest(d)
    if not k:
        return
    r = pygame.Rect(W - 228, THUMB_TOP, 220, 124)
    if type(surf).__name__ == "ScaledSurf":
        real, rr = surf.real, surf._r(r)
    else:
        real, rr = surf, r
    img = bg_img(k, rr.w, rr.h, 230)
    if img is not None:
        real.blit(img, rr.topleft)
    pygame.draw.rect(surf, BLUE if k == "sq" else ORANGE, r, 2, border_radius=4)
    pygame.draw.rect(surf, BLACK, (r.x + 2, r.bottom - 16, r.w - 4, 14))
    put(surf, F["small"], label.replace("PORTANAVES DE ESCUADRÓN", "ESCUADRÓN"), (r.centerx, r.bottom - 9),
        BLUE if k == "sq" else ORANGE, r.w - 6, anchor="center")


def view_navx_navx0(surf, d, flags, now):
    view_navx_base(surf, d, flags, now)
    if not (ui.get("navtab") == 2 and not NAVBIG[0]) and not nav_show_pol(d, now):
        route_thumb(surf, d or {})

VIEWS[3] = view_navx_navx0


