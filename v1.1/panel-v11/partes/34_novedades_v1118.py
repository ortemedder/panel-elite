# Panel Elite v1.1 · parte 34: novedades v1.1.18
#   ROBOT: la voz se pasa a 16 kHz (ocupa menos y el robot ya no se queda mudo con las respuestas largas); si la
#     respuesta es larga dice un resumen y el texto entero sale en su pantalla; si aun así no cabe, se corta con
#     un final suave (en el log: «ROBOT: voz demasiado larga, recortada»). Vosk con lista de palabras aunque el
#     modelo no traiga words.txt. «¿en qué sistema estoy?» ya no dice «seguridad seguridad».
#   RESUMEN DEL DÍA (y su cuadro de la HDMI): cada cosa en su línea, sin pisarse (AMIGOS, PASAJEROS HOY,
#     DÓNDE COMPRAR HOY, SIN COBRAR con su BORRAR); AMIGOS en movimiento si no caben; créditos por hora.
#   SESIÓN TERMINADA con créditos por hora.
#   MASACRE: contador de bajas por misión (sender b17), aviso al completar cada una, en REGISTRO DE COMBATE y por
#     voz («¿cómo va la masacre?»).
#   EVACUACIONES: resumen del día (pasajeros, créditos, tiempo medio) y aviso si a una le quedan menos de 30 min.
#   COMBATE: ficha del objetivo con lo que bajó desde la lectura anterior, antigüedad del dato, subsistema grande
#     (rojo por debajo del 20 %), facción y poder; avisos ESCUDOS DEL OBJETIVO CAÍDOS y CASCO BAJO 25 %;
#     al derribarlo, la nave y lo que duró el combate en el aviso del derribo.
#   EN VIVO: MERC COIN y copiloto ya no se pisan.
EV_LIST.extend([("tgtescudo", "OBJETIVO: ESCUDOS CAÍDOS"), ("tgtcasco", "OBJETIVO: CASCO BAJO 25 %"),
                ("masacre", "MASACRE: MISIÓN COMPLETA"), ("evac30", "EVACUACIÓN: MENOS DE 30 MIN"),
                ("amigosmov", "DÍA: AMIGOS EN MOVIMIENTO")])

SENDER_OK, ROBOT_OK = "v1.0b17", "v1.1.18"
SENDER_REQ = SENDER_OK

# ===============================================================================================================
# A. ROBOT: voz a 16 kHz, resumen hablado y recorte suave
# ===============================================================================================================
VOZ_MAX = 590000
VOZ16 = {}

def _wav_info(b):
    """(rate, canales, bits, inicio de datos, bytes de datos) de un wav PCM, o None."""
    import struct
    if not b or len(b) < 44 or b[:4] != b"RIFF" or b[8:12] != b"WAVE":
        return None
    i, fmt = 12, None
    while i + 8 <= len(b):
        cid, sz = b[i:i + 4], struct.unpack("<I", b[i + 4:i + 8])[0]
        if cid == b"fmt ":
            au, ch, rate, _, _, bits = struct.unpack("<HHIIHH", b[i + 8:i + 24])
            fmt = (au, ch, rate, bits)
        elif cid == b"data":
            if not fmt or fmt[0] != 1:
                return None
            return fmt[2], fmt[1], fmt[3], i + 8, min(sz, len(b) - i - 8)
        i += 8 + sz + (sz & 1)
    return None

def _wav_hdr(rate, n):
    import struct
    return (b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
            + b"data" + struct.pack("<I", n))

def wav16(b):
    """Pasa la voz (mono, 16 bits) a 16 kHz. Si no es lo esperado, la deja como está."""
    inf = _wav_info(b)
    if not inf:
        return b
    rate, ch, bits, off, n = inf
    if ch != 1 or bits != 16 or rate <= 16000:
        return b
    import array, sys as _s
    a = array.array("h"); a.frombytes(b[off:off + n // 2 * 2])
    if _s.byteorder != "little":
        a.byteswap()
    m = int(len(a) * 16000 / rate)
    try:
        import numpy as np
        x = np.frombuffer(a.tobytes(), dtype=np.int16).astype(np.float32)
        y = np.interp(np.arange(m) * (rate / 16000.0), np.arange(len(x)), x).astype(np.int16)
        out = y.tobytes() if _s.byteorder == "little" else y.byteswap().tobytes()
    except Exception:
        st, la, src = rate / 16000.0, len(a) - 1, a
        o = array.array("h", bytes(2 * m))
        for i in range(m):
            p = i * st; j = int(p)
            x0 = src[j] if j < la else src[la]
            x1 = src[j + 1] if j < la else x0
            o[i] = int(x0 + (x1 - x0) * (p - j))
        if _s.byteorder != "little":
            o.byteswap()
        out = o.tobytes()
    return _wav_hdr(16000, len(out)) + out

def wav_recorta(b, lim=VOZ_MAX):
    """Si no cabe en el robot, la corta con un final suave (0,3 s) y lo apunta en el log."""
    if not b or len(b) <= lim:
        return b
    inf = _wav_info(b)
    if not inf or inf[1] != 1 or inf[2] != 16:
        return None
    rate, _, _, off, n = inf
    import array, sys as _s
    keep = (lim - 44) // 2 * 2
    a = array.array("h"); a.frombytes(b[off:off + keep])
    if _s.byteorder != "little":
        a.byteswap()
    f = min(len(a), int(rate * 0.3))
    for i in range(f):
        k = len(a) - f + i
        a[k] = int(a[k] * (f - i) / f)
    if _s.byteorder != "little":
        a.byteswap()
    plog(f"ROBOT: voz demasiado larga, recortada ({len(b) // 1024} KB)")
    return _wav_hdr(rate, len(a) * 2) + a.tobytes()

def voz_corta(t, n=240):
    """Lo que dice el robot en voz alta: la respuesta, o su principio si es larga (el resto lo enseña en pantalla)."""
    t = re.sub(r"\s+", " ", t or "").strip()
    if len(t) <= n + 40:
        return t
    out = ""
    for trozo in re.split(r"(?<=[.;:])\s+", t):
        if len(out) + len(trozo) > n:
            break
        out += (" " if out else "") + trozo
    if len(out) < 60:
        cut = t[:n]
        out = cut[:cut.rfind(",")] if cut.rfind(",") > 60 else cut[:cut.rfind(" ")]
    return out.rstrip(" ,;:.") + ". El resto, en pantalla."

def voz_robot(resp):
    vt = voz_corta(resp)
    if vt in VOZ16:
        return VOZ16[vt]
    w = oido_wav(vt)
    if not w:
        return None
    w = wav_recorta(wav16(w))
    if w:
        if len(VOZ16) > 40:
            VOZ16.clear()
        VOZ16[vt] = w
    return w

def oido_atiende(pcm, rate):
    """Lo que hace el panel con una pregunta: devuelve el JSON para el robot (v1.1.18: voz a 16 kHz y resumida)."""
    if not cfg.get("stackchan"):
        return {"txt": "ROBOT desactivado en el panel"}
    if not ev_on("roboido"):
        return {"txt": "Las preguntas por voz están quitadas en ALERTAS"}
    if not oido_ok():
        return {"txt": "No tengo oídos: instala instalar_oido_robot.sh en la Pi"}
    t0 = time.time()
    oido = oido_texto(pcm, rate)
    resp, cara = oido_respuesta(oido)
    plog(f"ROBOT oye «{oido}» -> {resp} ({time.time() - t0:.1f} s)")
    out = {"oido": oido, "txt": resp, "cara": cara}
    try:
        wav = voz_robot(resp)
    except Exception as e:
        log_exc("voz robot", e)
        wav = None
    if wav and len(wav) <= 600000:
        OIDO["n"] += 1
        OIDO["resp"] = {OIDO["n"]: wav}
        out["wav"] = f"/resp?n={OIDO['n']}"
    return out

# Vosk: lista de palabras también con modelos sin words.txt (se pregunta al modelo palabra a palabra)
_oido_gram_v1117 = _oido_gram
_ACENTO = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"}

def _variantes(k):
    out = {k}
    for suf in ("s", "es", "a", "o", "as", "os", "n", "r"):
        out.add(k + suf)
    for i, c in enumerate(k):
        if c in _ACENTO:
            out.add(k[:i] + _ACENTO[c] + k[i + 1:])
        elif c == "n":
            out.add(k[:i] + "ñ" + k[i + 1:])
    return out

def _oido_gram():
    if GRAM["hecho"]:
        return GRAM["g"]
    for raiz, dirs, files in os.walk(VOSK_DIR):
        if "words.txt" in files:
            return _oido_gram_v1117()
    GRAM["hecho"] = True
    model = _oido_model()
    if not hasattr(model, "find_word"):
        plog("ROBOT: este Vosk no deja mirar palabras, sin lista")
        return None
    sel = set()
    for k in _oido_claves():
        if len(k) < 2 or not k.isalpha():
            continue
        for v in _variantes(k):
            try:
                if model.find_word(v) >= 0:
                    sel.add(v)
            except Exception:
                pass
    if len(sel) < 50:
        plog(f"ROBOT: solo {len(sel)} palabras en el modelo, sin lista")
        return None
    GRAM["g"] = json.dumps(sorted(sel) + ["[unk]"], ensure_ascii=False)
    plog(f"ROBOT: lista de palabras de Vosk con {len(sel)} palabras (sin words.txt)")
    return GRAM["g"]

# ===============================================================================================================
# B. RESUMEN DEL DÍA: cada cosa en su línea
# ===============================================================================================================
DIA = {"x0": time.time()}
_view11_v1118 = VIEWS[11]

def linea_mov(surf, font, txt, x, y, w, col, now, h=16):
    """Una línea de texto; si no cabe, se mueve sola (se quita en ALERTAS > DÍA: AMIGOS EN MOVIMIENTO)."""
    tw = tw_(font, txt)
    if tw <= w or not ev_on("amigosmov"):
        put(surf, font, txt, (x, y), col, w)
        return
    gap = 60
    off = int((now - DIA["x0"]) * 30) % (tw + gap)
    old = surf.get_clip()
    surf.set_clip(pygame.Rect(x, y - 1, w, h + 2))
    put(surf, font, txt, (x - off, y), col)
    put(surf, font, txt, (x - off + tw + gap, y), col)
    surf.set_clip(old)

def cr_hora(s_, d):
    """(créditos ganados, por hora) de la sesión, o None."""
    bal, c0 = (d or {}).get("balance"), s_.get("credits0")
    play_ = (s_.get("play") or 0) + (max(0, (s_.get("lastts") or s_["seg"]) - s_["seg"]) if s_.get("seg") else 0)
    if not s_.get("day"):
        play_ = time.time() - (s_.get("start") or time.time())
    if bal is None or c0 is None or play_ < 600:
        return None
    g = bal - c0
    return g, g * 3600 / play_

def evac_txt(d):
    e = (d or {}).get("evac") or {}
    if not e.get("m") or e.get("day") != time.strftime("%Y-%m-%d", time.gmtime()):
        return ""
    med = e.get("s", 0) / e["m"] / 60
    return f"EVACUACIONES {e['m']} · {e.get('n', 0)} pas. · {cr(e.get('cr', 0))} cr · media {med:.0f} min"

def dia_lineas(d, now):
    """Líneas de abajo del RESUMEN DEL DÍA: (texto, color, tipo)."""
    L = []
    fr = (d.get("friends") or {}).get("on") or []
    L.append(((f"AMIGOS ({len(fr)}): " + ", ".join(fr)) if fr else "toca para ver AMIGOS (0 conectados)",
              GREEN if fr else DIM, "amigos"))
    h_ = (d.get("pax") or {}).get("hoy") or {}
    bits = []
    if h_.get("n") and h_.get("day") == time.strftime("%Y-%m-%d", time.gmtime()):
        bits.append(f"PASAJEROS HOY {h_['n']} · {cr(h_.get('cr', 0))} cr")
    ev_ = evac_txt(d)
    if ev_:
        bits.append(ev_)
    paid_ = ((d.get("ops") or {}).get("crew") or {}).get("paid")
    if paid_:
        bits.append(f"copiloto -{crx(paid_)} cr")
    if bits:
        L.append(("  ·  ".join(bits), BLUE, "pax"))
    C = _compras_day()
    if C:
        L.append((f"DÓNDE COMPRAR HOY ({len(C)}): " + ", ".join(e["st"] for e in C[-3:]) + "  >", GREEN, "compras"))
    led = (d.get("footcz") or {}).get("led") or {}
    s_ = d.get("sess") or {}
    if led.get("cr"):
        b, rw = led.get("bonds") or [0, 0], led.get("bounties") or [0, 0]
        dd_ = int((time.time() - d.get("uncl_t0")) // 86400) if d.get("uncl_t0") else 0
        L.append((f"SIN COBRAR {crx(led['cr'])} cr · {b[0]} bonos {crx(b[1])} · {rw[0]} recomp. {crx(rw[1])}"
                  + (f" · {dd_} d" if dd_ else ""), RED, "led"))
    elif s_.get("pending"):
        L.append((f"RECOMPENSAS SIN COBRAR {cr(s_['pending'])} cr · {s_.get('pending_n', 0)} derribos", RED, "pend"))
    return L

def view11_v1118(surf, d, flags, now):
    st = ui.get("sesstab")
    if st == 1:
        return view_friends(surf, d, flags, now)
    if st:
        return _view11_v1118(surf, d, flags, now)
    d = d or {}
    COMPRAS["line"] = None
    LEDB["r"] = None
    s_ = d.get("sess") or {}
    if not s_:
        put(surf, F["btn"], "Sin sesión (carga la partida)", (W // 2, TOP + 70), DIM, anchor="center")
        y = TOP + 110
    else:
        e = s_.get("earn") or {}
        play_ = (s_.get("play") or 0) + (max(0, (s_.get("lastts") or s_["seg"]) - s_["seg"]) if s_.get("seg") else 0)
        left = [("HOY " + game_date(), dur(play_ if s_.get("day") else time.time() - (s_.get("start") or time.time()))),
                ("SALTOS", str(s_.get("jumps", 0))),
                ("AÑOS LUZ", f"{s_.get('ly', 0):,.0f}".replace(",", ".")),
                ("BAJAS  pie · nave", f"{s_.get('kfoot', 0)} · {s_.get('kills', 0) - s_.get('kfoot', 0)}"),
                ("MUERTES", str(s_.get("deaths", 0)))]
        right = [("RECOMPENSAS", e.get("bounty")), ("COMERCIO", e.get("trade")), ("EXPLORACIÓN", e.get("explo")),
                 ("MISIONES", e.get("missions")), ("EXOBIOLOGÍA", e.get("bio"))]
        y = TOP + 4
        for (l1, v1), (l2, v2) in zip(left, right):
            put(surf, F["small"], l1, (8, y + 4), BLUE if l1.startswith("HOY") else DIM, 130)
            put(surf, F["big"], v1, (226, y), RED if l1 == "MUERTES" and v1 != "0" else ORANGE, 90, anchor="topright")
            put(surf, F["small"], l2, (246, y + 4), DIM)
            put(surf, F["big"], cr(v2), (W - 8, y), ORANGE, anchor="topright")
            y += 28
        pygame.draw.line(surf, DIM, (236, TOP + 4), (236, y - 2))
        pygame.draw.line(surf, DIM, (8, y), (W - 8, y)); y += 4
        bal, c0 = d.get("balance"), s_.get("credits0")
        if bal is not None:
            put(surf, F["small"], "SALDO", (8, y + 6), DIM)
            bw = put(surf, F["big"], f"{bal:,.0f} cr".replace(",", "."), (60, y), ORANGE)
            if c0 is not None:
                diff = bal - c0
                dtx = ("+" if diff >= 0 else "") + cr(diff)
                dw = put(surf, F["big"], dtx, (W - 8, y), GREEN if diff >= 0 else RED, anchor="topright")
                ch = cr_hora(s_, d)
                if ch and ch[1] > 0:
                    htx = f"{cr(ch[1])}/h"
                    hx = W - 8 - dw - 10
                    if hx - tw_(F["small"], htx) > 60 + bw + 8:
                        put(surf, F["small"], htx, (hx, y + 6), GREEN, anchor="topright")
        y += 26
    for txt, col, k in dia_lineas(d, now):
        if y > H - 17:
            break
        w = W - 16
        if k == "led":
            r = pygame.Rect(W - 86, y - 1, 80, 17)
            sure = time.time() < LEDB["sure"]
            draw_button(surf, r, "¿SEGURO?" if sure else "BORRAR", None, F["tiny"], filled=sure, compact=True)
            LEDB["r"] = r
            w = W - 104
        if k in ("amigos", "pax"):
            linea_mov(surf, F["small"], txt, 8, y, w, col, now)
        else:
            put(surf, F["small"], txt, (8, y), col, w)
        if k == "compras":
            COMPRAS["line"] = pygame.Rect(8, y - 1, W - 16, 17)
        y += 17

VIEWS[11] = view11_v1118

# ===============================================================================================================
# C. créditos por hora en SESIÓN TERMINADA · MASACRE · EVACUACIONES
# ===============================================================================================================
TGT = {"key": None, "t": None, "sh": None, "hu": None, "dsh": 0, "dhu": 0, "t0": 0, "seen": 0, "ship": ""}
_handle_note_v1118 = handle_note

def handle_note(kind, text):
    if kind == "masdone":
        p = (text or "").split("|")
        if len(p) >= 5:
            left = int(p[4]) if p[4].isdigit() else 0
            if left:
                aviso_num("masacre", "MASACRE: MISIÓN COMPLETA", f"{p[0]} · {p[3]} bajas · te quedan {left}", GREEN, 6)
            else:
                aviso_num("masacre", "MASACRE COMPLETADA", f"{p[3]} bajas de {p[1]} · vuelve a cobrar", GREEN, 8)
        return
    return _handle_note_v1118(kind, text)

# los avisos grandes de SESIÓN TERMINADA y DERRIBO: créditos por hora y resumen del combate
_xa_notes_v1118 = xa_notes

def xa_notes(d, now):
    _xa_notes_v1118(d, now)
    a = xa.get("a")
    if not isinstance(a, dict) or a.get("_v1118"):
        return
    a["_v1118"] = True
    try:
        tit = a.get("title") or ""
        if tit == "SESIÓN TERMINADA":
            ns = [t for _, k, t in (d or {}).get("notes") or [] if k == "sessend"]
            v = [float(x) for x in ns[-1].split("|")] if ns else []
            if len(v) > 1 and v[0] >= 1 and v[1] >= 600 and a.get("lines"):
                a["lines"][0] += f"  ·  {cr(v[0] * 3600 / v[1])} cr/h"
        elif tit.startswith("DERRIBO") and "SRV" not in tit and TGT["ship"] and time.time() - TGT["seen"] < 90:
            el = int(time.time() - TGT["t0"])
            L_ = list(a.get("lines") or [])
            ya = any(TGT["ship"].lower() in (x or "").lower() for x in L_)
            L_.append(("" if ya else f"{TGT['ship']} · ") + f"combate {el // 60}:{el % 60:02d}")
            a["lines"] = L_
            a["until"] = max(a.get("until", 0), time.time() + 5)
            TGT.update(key=None, ship="")
    except Exception as e:
        log_exc("aviso v1.1.18", e)

EVW = {"avisado": set()}

def evac_watch(d):
    pc = d.get("pcnow") or time.time()
    for p in (d.get("pax") or {}).get("list") or []:
        if not p.get("evac") or not p.get("exp"):
            continue
        quedan = p["exp"] - pc
        mid = p.get("id")
        if 0 < quedan < 1800 and mid not in EVW["avisado"]:
            EVW["avisado"].add(mid)
            aviso_num("evac30", "EVACUACIÓN: MENOS DE 30 MIN",
                      f"{p.get('n', 0)} pasajeros a {p.get('st') or p.get('sys') or '?'} · {int(quedan // 60)} min", RED, 8, "alarm")

def r_masacre(d, now):
    M = d.get("masacre") or []
    if not M:
        return "No llevas misiones de masacre"
    pend = [m for m in M if m[2] < m[3]]
    if not pend:
        return f"Masacre completada: {len(M)} misiones listas para cobrar"
    tot = sum(m[3] - m[2] for m in pend)
    return f"Masacre: te faltan {tot} bajas de {pend[0][1]}. " + ". ".join(f"{m[0]}: {m[2]} de {m[3]}" for m in pend[:4])

OIDO_PREG.insert(0, (("masacre",), r_masacre))

_view61_v1118 = VIEWS[61]

def view61_v1118(surf, d, flags, now):
    _view61_v1118(surf, d, flags, now)
    M = (d or {}).get("masacre") or []
    if not M:
        return
    rows = M[:3]
    bh = 18 + 17 * len(rows)
    r = pygame.Rect(4, H - 20 - bh, W - 8, bh)
    pygame.draw.rect(surf, BLACK, r)
    pygame.draw.rect(surf, GREEN, r, 1, border_radius=4)
    falta = sum(max(0, m[3] - m[2]) for m in M)
    put(surf, F["small"], "MASACRE" + (f" · faltan {falta} bajas" if falta else " · COMPLETADA, ve a cobrar"), (r.x + 6, r.y + 2), GREEN, r.w - 12)
    y = r.y + 18
    for giv, tgt, k, n, *_ in rows:
        put(surf, F["small"], f"{giv} -> {tgt}", (r.x + 6, y), WHITE if k < n else GREEN, r.w - 150)
        bx = pygame.Rect(r.right - 140, y + 2, 80, 10)
        pygame.draw.rect(surf, DIM, bx, 1)
        pygame.draw.rect(surf, GREEN, (bx.x + 2, bx.y + 2, int((bx.w - 4) * min(1, k / max(1, n))), bx.h - 4))
        put(surf, F["small"], f"{k}/{n}", (r.right - 6, y), GREEN if k >= n else ORANGE, anchor="topright")
        y += 17

VIEWS[61] = view61_v1118

# ===============================================================================================================
# D. COMBATE: ficha del objetivo con más datos
# ===============================================================================================================
def tgt_watch(d, now):
    t = d.get("target")
    if not t:
        return
    key = (t.get("stype"), t.get("pilot"))
    if key != TGT["key"]:
        TGT.update(key=key, t=t.get("t"), sh=t.get("shield"), hu=t.get("hull"), dsh=0, dhu=0, t0=now, seen=now,
                   ship=t.get("ship") or "?")
        return
    TGT["seen"] = now
    if t.get("t") == TGT["t"]:
        return
    TGT["t"] = t.get("t")
    ship = TGT["ship"]
    sh, hu = t.get("shield"), t.get("hull")
    if sh is not None:
        if TGT["sh"] is not None:
            TGT["dsh"] = max(0, TGT["sh"] - sh)
            if TGT["sh"] > 0 >= sh:
                aviso_num("tgtescudo", "ESCUDOS DEL OBJETIVO CAÍDOS", ship, BLUE, 4)
        TGT["sh"] = sh
    if hu is not None:
        if TGT["hu"] is not None:
            TGT["dhu"] = max(0, TGT["hu"] - hu)
            if TGT["hu"] >= 25 > hu:
                aviso_num("tgtcasco", "CASCO DEL OBJETIVO BAJO 25 %", f"{ship} · {hu:.0f} %", ORANGE, 4)
        TGT["hu"] = hu

def _baja(surf, x, y, w, v):
    if v and v >= 1:
        put(surf, F["small"], f"-{v:.0f}%", (x + w - 44, y + 1), RED, anchor="topright")

def view_combat(surf, d, flags, now):
    t = (d or {}).get("target")
    card = pygame.Rect(4, TOP + 2, W - 8, CARD6 - TOP - 4)
    pygame.draw.rect(surf, DIM, card, 1, border_radius=6)
    if not t:
        put(surf, F["big"], "SIN OBJETIVO", card.center, DIM, anchor="center")
    else:
        x, y = card.x + 8, card.y + 4
        cmdr = t.get("cmdr")
        mine = TGT["key"] == (t.get("stype"), t.get("pilot"))
        put(surf, F["big"], (t.get("ship") or "?").upper(), (x, y), ORANGE, card.w - 170)
        age = (d.get("pcnow") or 0) - (t.get("t") or 0) if t.get("t") and d.get("pcnow") else 0
        put(surf, F["small"], f"ESCANEO {t.get('scan', 0)}/3" + (f" · hace {age:.0f} s" if age >= 5 else ""),
            (card.right - 8, y + 4), ORANGE if age >= 30 else DIM, anchor="topright")
        y += 26
        if t.get("pilot"):
            w_ = put(surf, F["btn"], t["pilot"], (x, y), BLUE if cmdr else ORANGE, card.w - 170)
            if cmdr:
                put(surf, F["small"], " COMANDANTE", (x + w_ + 4, y + 4), BLUE)
            ia_ = t.get("inara") or {}
            if cmdr and ia_ and not ia_.get("none"):
                ally = my_squad(d) and ia_.get("squad", "").lower() == my_squad(d).lower()
                put(surf, F["small"], ("ALIADO · " if ally else "INARA: ") + inara_line(ia_, d, short=True),
                    (card.right - 8, y + 4), GREEN if ally else ORANGE, card.w - w_ - 120, anchor="topright")
            else:
                put(surf, F["small"], t.get("rank") or "", (card.right - 8, y + 4), DIM, anchor="topright")
        y += 24
        half = (card.w - 24) // 2
        bar(surf, x, y, half, "ESCUDO", t.get("shield"), BLUE)
        bar(surf, x + half + 8, y, half, "CASCO", t.get("hull"), RED if (t.get("hull") or 100) < 25 else ORANGE)
        if mine:
            _baja(surf, x, y, half, TGT["dsh"])
            _baja(surf, x + half + 8, y, half, TGT["dhu"])
        y += 18
        legal = t.get("legal") or ""
        ia2_ = t.get("inara") or {}
        tph_ = bool(cfg.get("cmdrpics", True)) and \
            (avatar_photo(surf, ia2_.get("avatar"), pygame.Rect(card.right - 62, card.bottom - 34, 56, 31)) or
             ship_photo(surf, {"type": t.get("stype"), "ship": t.get("ship") or ia2_.get("ship")}, {},
                        pygame.Rect(card.right - 62, card.bottom - 34, 56, 31)))
        rx = card.right - (68 if tph_ else 8)
        wanted = legal.lower() == "wanted"
        lw = put(surf, F["small"], ("BUSCADO" if wanted else legal.upper()) or "-", (x, y + 2), RED if wanted else GREEN)
        if t.get("bounty"):
            put(surf, F["small"], f"RECOMPENSA {t['bounty']:,} cr".replace(",", "."), (x + lw + 10, y + 2), RED, 200)
        if t.get("subsys"):
            sh = t.get("subhealth")
            put(surf, F["btn"], f"{t['subsys']}" + (f" {sh:.0f}%" if sh is not None else ""), (rx, y),
                RED if sh is not None and sh < 20 else ORANGE, card.w // 2 - 40, anchor="topright")
        y += 18
        fac, pw = t.get("faction"), t.get("power")
        if fac or pw:
            fw = 0
            if fac:
                fw = put(surf, F["small"], fac, (x, y), GREEN if es_mi_fac(fac) else DIM, rx - x - 120)
            if pw:
                put(surf, F["small"], ("  ·  " if fac else "") + pw, (x + fw, y), MERC, max(40, rx - x - fw - 4))
    for i, (txt, key) in enumerate(COMBAT_BTNS):
        draw_button(surf, c6_rect(i), txt, key.upper(), F["btn"], lit=flash.get((6, i), 0) > now, compact=True)

# ===============================================================================================================
# una vez por segundo desde el dibujo
# ===============================================================================================================
_render_v1118 = render
W1118 = {"t": 0.0}

def render(surf):
    r_ = _render_v1118(surf)
    now = time.time()
    if now - W1118["t"] >= 1:
        W1118["t"] = now
        try:
            with lock:
                d, rx = state["data"], state["rx"]
            if d and now - rx < 5:
                tgt_watch(d, now)
                evac_watch(d)
        except Exception as e:
            log_exc("v1.1.18", e)
    return r_
