#!/usr/bin/env python3
# Parche v0.94: RESUMEN DEL DIA, nombres de amigos, fotos de naves de otros CMDR (se pueden apagar),
# CARGA/MISION con prioridad a misiones y ficha BATALLA TERMINADA. Va con el sender v0.94.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def battle_end" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.93' not in s:
    sys.exit("Este parche es para la v0.93")
shutil.copy(P, P + ".bak93")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# 1. RESUMEN DEL DIA
rep('''        [(11, "SESIÓN"), (130, "GALNET"), (132, "OBJ.COM"), (123, "RANGOS")]]''',
    '''        [(11, "DÍA"), (130, "GALNET"), (132, "OBJ.COM"), (123, "RANGOS")]]''')
rep('''    left = [("TIEMPO", dur(time.time() - (s_.get("start") or time.time()))), ("SALTOS", str(s_.get("jumps", 0))),''',
    '''    play_ = (s_.get("play") or 0) + (max(0, time.time() - s_["seg"]) if s_.get("seg") else 0)
    left = [("HOY " + game_date(), dur(play_ if s_.get("day") else time.time() - (s_.get("start") or time.time()))),
            ("SALTOS", str(s_.get("jumps", 0))),''')
rep('''        put(surf, F["small"], l1, (8, y + 4), DIM)
        put(surf, F["big"], v1, (226, y), RED if l1 == "MUERTES" and v1 != "0" else ORANGE, anchor="topright")''',
    '''        put(surf, F["small"], l1, (8, y + 4), BLUE if l1.startswith("HOY") else DIM, 130)
        put(surf, F["big"], v1, (226, y), RED if l1 == "MUERTES" and v1 != "0" else ORANGE, 90, anchor="topright")''')
rep('''11: "SESIÓN", 12:''', '''11: "RESUMEN DEL DÍA", 12:''')

# 2. nombres de los amigos conectados
rep('''    put(surf, F["small"], f"toca para ver AMIGOS ({n} conectados)" + (f"  ·  copiloto -{crx(paid_)} cr" if paid_ else ""),''',
    '''    on_ = ((d or {}).get("friends") or {}).get("on") or []
    put(surf, F["small"], (f"AMIGOS ({n}): " + ", ".join(on_) if on_ else "toca para ver AMIGOS (0 conectados)")
        + (f"  ·  copiloto -{crx(paid_)} cr" if paid_ else ""),''')

# 3. fotos de las naves de otros CMDR
rep('''        put(surf, F["small"], "  ·  ".join(b for b in bits if b) or "sin datos públicos", (170, y + 6), DIM, W - 178)''',
    '''        ph_ = cfg.get("cmdrpics", True) and o.get("ship") and ship_photo(surf, {"ship": o.get("ship")}, {}, pygame.Rect(W - 60, y + 3, 52, 29))
        put(surf, F["small"], "  ·  ".join(b for b in bits if b) or "sin datos públicos", (170, y + 6), DIM, W - (240 if ph_ else 178))''')
rep('''                (card.right - 8, y), ORANGE, card.w // 2 - 20, anchor="topright")''',
    '''                (card.right - (68 if tph_ else 8), y), ORANGE, card.w // 2 - 20, anchor="topright")''')
rep('''        legal = t.get("legal") or ""
        wanted = legal.lower() == "wanted"''', '''        legal = t.get("legal") or ""
        ia2_ = t.get("inara") or {}
        tph_ = bool(cmdr and cfg.get("cmdrpics", True) and ia2_.get("ship")) and \\
            ship_photo(surf, {"ship": ia2_.get("ship")}, {}, pygame.Rect(card.right - 62, card.bottom - 34, 56, 31))
        wanted = legal.lower() == "wanted"''')
# ajuste FOTOS CMDR
rep('''             ("CERRAR JUEGO", cfg.get("killbtn", True)), ("MERCADO", None)]''',
    '''             ("CERRAR JUEGO", cfg.get("killbtn", True)), ("MERCADO", None), ("FOTOS CMDR", cfg.get("cmdrpics", True))]''')
rep('''        for i, k in enumerate(["auto", "alerts", "sound", "theme", "voice", "stream", "keys", "killbtn", "mkt"]):''',
    '''        for i, k in enumerate(["auto", "alerts", "sound", "theme", "voice", "stream", "keys", "killbtn", "mkt", "cmdrpics"]):''')
rep('''                if k == "killbtn":
                    tap_flash((124, i)); cfg["killbtn"] = not cfg.get("killbtn", True); save_cfg(); return''',
    '''                if k == "killbtn":
                    tap_flash((124, i)); cfg["killbtn"] = not cfg.get("killbtn", True); save_cfg(); return
                if k == "cmdrpics":
                    tap_flash((124, i)); cfg["cmdrpics"] = not cfg.get("cmdrpics", True); save_cfg(); return''')

# 4. CARGA / MISION: primero misiones
rep('''    dk = bool(fl & 1)''', '''    v4_ = ui["view"] == 4
    if not v4_ or not GLOW.get("v4"):
        ui["tab4"] = 1 if d.get("missions") else 0
        if v4_:
            ui["page4"] = 0
    GLOW["v4"] = v4_
    dk = bool(fl & 1)''')

# 5. BATALLA TERMINADA
rep('''            if kind == "kill":
                track_kill()''', '''            battle_note(kind, text, d)
            if kind == "kill":
                track_kill()''')
rep('''    mega_watch(d, now)''', '''    mega_watch(d, now)
    battle_watch(d, now)''')
rep('''    if xa.get("a") and xa["a"].get("title") == "SESIÓN TERMINADA" and time.time() < xa["a"]["until"]:''',
    '''    if xa.get("a") and xa["a"].get("title") in ("SESIÓN TERMINADA", "BATALLA TERMINADA") and time.time() < xa["a"]["until"]:''')

CODE = r'''
# ---------- v0.94: BATALLA TERMINADA (el juego no apunta la victoria: se deduce) ----------
BAT = {"on": False}

def battle_note(kind, text, d):
    p = (text or "").split("|")
    now = time.time()
    if kind == "kill" and len(p) > 3 and p[3] == "F":
        if not BAT.get("on"):
            Z = (d or {}).get("footcz") or {}
            BAT.clear()
            BAT.update(on=True, t0=now, k=0, cr=0, med=0, cell=0, gren=0, zone=Z.get("zone") or "", side=Z.get("side") or "")
        BAT["k"] += 1
        BAT["cr"] += float(p[1] or 0)
        BAT["last"] = now
    elif not BAT.get("on"):
        return
    elif kind == "usecons" and p:
        BAT["med" if p[0] == "healthpack" else "cell"] += 1
    elif kind == "thrown":
        BAT["gren"] += 1
    elif kind in ("taxi", "dropship"):
        battle_end(now, delay=7)                     # despues del aviso del transporte

def battle_watch(d, now):
    if BATP.get("a") and now >= BATP["at"]:
        k0 = XA_K[0]
        try:
            XA_K[0] = "battle"
            xa["a"] = dict(BATP["a"], until=now + 15)
            play("ok")
        finally:
            XA_K[0] = k0
        BATP["a"] = None
    if not BAT.get("on"):
        return
    Z = (d or {}).get("footcz") or {}
    if Z.get("zone"):
        BAT["zone"] = Z["zone"]
    if Z.get("side"):
        BAT["side"] = Z["side"]
    if not ((d or {}).get("Flags2", 0) & 1) or now - max(BAT.get("last", 0), fight["t"]) > 120:
        battle_end(now)

BATP = {"a": None, "at": 0}

def battle_end(now, delay=0):
    B = dict(BAT)
    BAT.clear(); BAT["on"] = False
    if B.get("k", 0) < 3:
        return                                       # dos bajas sueltas no son una batalla
    mins = max(1, round(((B.get("last") or now) - B["t0"]) / 60))
    cons = "  ·  ".join(x for x in ((f"botiquines {B['med']}" if B["med"] else ""), (f"células {B['cell']}" if B["cell"] else ""),
                                    (f"granadas {B['gren']}" if B["gren"] else "")) if x)
    BATP["a"] = dict(col=GREEN, title="BATALLA TERMINADA", big=(B.get("zone") or "ZONA DE COMBATE").upper(),
                     lines=[f"{B['k']} bajas  ·  +{crx(B['cr'])} cr sin cobrar",
                            f"duración {mins} min  ·  {B['k'] / mins:.1f} bajas/min".replace(".", ","),
                            cons, f"por {B['side']}" if B.get("side") else ""])
    BATP["at"] = now + delay

EV_LIST.append(("battle", "BATALLA TERMINADA"))

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")

rep('''# Enlace energético''', '''# Novedades v0.94
- 11 RESUMEN DEL DÍA (pestaña DÍA): suma todas las partidas del día (se pone a cero a las 00:00) con la fecha del juego y el tiempo jugado.
- La línea de AMIGOS dice sus nombres.
- Fotos de la nave principal (Inara) de otros CMDR: al fijarlos y en la lista del ESCUADRÓN. Se apagan en OPCIONES > FOTOS CMDR.
- 4 CARGA/MISIÓN se abre en MISIONES si tienes; si no, en BODEGA (y así sale en la pantalla grande).
- BATALLA TERMINADA a pie: al reservar transporte, subir a la nave o tras 2 min sin bajas, resumen de bajas, créditos, duración y consumibles (el juego no dice si ganaste).
# Enlace energético''')
rep('    ("0.93", "Mercado de la estación donde estás, fotos de naves, facción del destino, transporte 5:20 / 6:00"),\n',
    '    ("0.93", "Mercado de la estación donde estás, fotos de naves, facción del destino, transporte 5:20 / 6:00"),\n'
    '    ("0.94", "Resumen del día, nombres de amigos, fotos de naves de CMDR, misiones primero y BATALLA TERMINADA"),\n')
s = re.sub(r'PANEL_VER = "v0\.93[^"]*"', 'PANEL_VER = "v0.94 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.94  (copia en " + P + ".bak93)")
