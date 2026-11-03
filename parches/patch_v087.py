#!/usr/bin/env python3
# Parche v0.87: objetivos comunitarios cerrados (banda CERRADO, fuera a los 2 dias), supresor de escudo,
# pantalla de despedida con nitidez, EDSM bloqueado, bajas y derribos en un cuadro de la pantalla grande,
# combate de nave manda (sin MERCADO ni GALNET) y perfil de Inara del CMDR fijado. Va con el sender v0.87.
import re, shutil, sys, time
P = sys.argv[1] if len(sys.argv) > 1 else "/home/ortem/panel.py"
s = open(P, encoding="utf-8").read()
if "def draw_kill_cell" in s:
    sys.exit("Ya estaba aplicado")
if 'PANEL_VER = "v0.86' not in s:
    sys.exit("Este parche es para la v0.86")
shutil.copy(P, P + ".bak86")

def rep(old, new):
    global s
    if old not in s:
        sys.exit("No encuentro: " + old[:70])
    s = s.replace(old, new, 1)

# ---------- 1. objetivos comunitarios cerrados ----------
rep('''def cg_all(d):
    mine = [dict(g, me=True) for g in ((d or {}).get("mycg") or [])]
    names = {g["title"].lower() for g in mine}
    return mine + [g for g in cgoals["list"] if g["title"].lower() not in names]''', '''def cg_secs(exp):
    import calendar
    e = (exp or "").replace("Z", "")
    for txt, fmt in ((e[:19], "%Y-%m-%dT%H:%M:%S"), (e[:19], "%Y-%m-%d %H:%M:%S"), (e[:10], "%Y-%m-%d")):
        try:
            return calendar.timegm(time.strptime(txt, fmt)) - time.time()
        except ValueError:
            continue
    return None

CG_KEEP = 2 * 86400            # los cerrados se ven 2 dias y desaparecen

def cg_all(d):
    mine = [dict(g, me=True) for g in ((d or {}).get("mycg") or [])]
    names = {g["title"].lower() for g in mine}
    done = cgoals.setdefault("done", {})
    out = []
    for g in mine + [g for g in cgoals["list"] if g["title"].lower() not in names]:
        sec = cg_secs(g.get("expiry", ""))
        closed = bool(g.get("complete")) or (sec is not None and sec <= 0)
        if closed:
            t0 = done.setdefault(g["title"].lower(), time.time())
            gone = (-sec if sec is not None and sec <= 0 else time.time() - t0)
            if gone > CG_KEEP:
                continue
        out.append(dict(g, closed=closed))
    return [g for g in out if not g["closed"]] + [g for g in out if g["closed"]]

_CGF = {}

def cg_band(surf, r, g):
    """Ficha cerrada: velo oscuro y banda oblicua roja CERRADO."""
    veil = pygame.Surface((r.w, r.h)); veil.set_alpha(150); veil.fill(BLACK)
    surf.blit(veil, r.topleft)
    f = _CGF.get("f") or _CGF.setdefault("f", pygame.font.Font(None, 30))
    band = pygame.Surface((int(r.w * 0.7), 30), pygame.SRCALPHA)
    band.fill(RED)
    tx = f.render("CERRADO", True, WHITE)
    band.blit(tx, tx.get_rect(center=band.get_rect().center))
    band = pygame.transform.rotate(band, 10)
    surf.blit(band, band.get_rect(center=r.center).topleft)
    if g.get("me"):
        put(surf, F["small"], "cobra la recompensa", (r.centerx, r.bottom - 16), GREEN, anchor="center")''')
rep('''        info, col = f"{len(L)} activo{'s' if len(L) != 1 else ''} · actualizado " + time.strftime("%H:%M", time.localtime(cgoals["t"])), DIM''',
    '''        na = sum(1 for g in L if not g.get("closed"))
        info, col = f"{na} activo{'s' if na != 1 else ''} · actualizado " + time.strftime("%H:%M", time.localtime(cgoals["t"])), DIM''')
rep('''        elif g.get("text"):
            put(surf, F["small"], g["text"].replace("\\n", " "), (r.x + 8, r.y + 82), DIM, r.w - 16)
''', '''        elif g.get("text"):
            put(surf, F["small"], g["text"].replace("\\n", " "), (r.x + 8, r.y + 82), DIM, r.w - 16)
        if g.get("closed"):
            cg_band(surf, r, g)
''')

# ---------- 2. supresor de escudo (asi lo llama el juego en espanol) ----------
rep('''    if "emp" in n or "disrup" in n:''', '''    if "emp" in n or "disrup" in n or "supres" in n:''')

# ---------- 3. pantalla de despedida: sin nitidez alta (no se puede ampliar) ----------
rep('''def panel_hi():
    """El panel (pantalla pequena) dibujado a tamano grande: para la HDMI en modo PANEL y la web /panel."""
''', '''def panel_hi():
    """El panel (pantalla pequena) dibujado a tamano grande: para la HDMI en modo PANEL y la web /panel."""
    if ui.get("bye"):
        return None
''')

# ---------- 4. EDSM bloqueado ----------
rep('''    if ex.get("edsm_n"):
        put(surf, F["small"], f"EDSM: {ex['edsm_n']} cuerpos", (150, y), BLUE)''', '''    if ex.get("edsm_n"):
        put(surf, F["small"], f"EDSM: {ex['edsm_n']} cuerpos", (150, y), BLUE)
    elif ex.get("edsm_st") == "bloqueado":
        put(surf, F["small"], "EDSM bloqueado", (165, y), RED)
    elif ex.get("edsm_st") == "error":
        put(surf, F["small"], "EDSM sin respuesta", (165, y), ORANGE)''')
rep('''        msg = "Consultando EDSM..." if ex.get("edsm_st") == "consultando" else "Nada destacable escaneado aún"''',
    '''        msg = {"consultando": "Consultando EDSM...", "bloqueado": "EDSM bloqueado (¿fútbol?) · reintento cada 10 min"}.get(
            ex.get("edsm_st"), "Nada destacable escaneado aún")''')

# ---------- 5. bajas y derribos: en un cuadro de la pantalla grande ----------
rep('''    elif xa.get("a") and now < xa["a"]["until"]:''', '''    elif xa.get("a") and now < xa["a"]["until"] and not kill_in_cell(xa["a"]):''')
rep('''    BIG["fast"] = False
''', '''    BIG["fast"] = False
    BIG["rects"] = []
''')
rep('''def big_cell(S, cell, v, d, flags, now, r, font, how, extra=""):
''', '''def big_cell(S, cell, v, d, flags, now, r, font, how, extra=""):
    BIG.setdefault("rects", []).append((v, r))
''')
rep('''        render_big()
        draw_hpcrit(BIG["surf"], time.time())''', '''        render_big()
        draw_kill_cell(time.time())
        draw_hpcrit(BIG["surf"], time.time())''')

# ---------- 6. combate de nave manda ----------
rep('''FIGHT_KINDS = ("underattack", "shields_down", "kill", "deploy", "interdicted")''',
    '''FIGHT_KINDS = ("underattack", "shields_down", "kill", "deploy", "interdicted", "hull", "combatmusic")''')
rep('''def big_mode(d, flags):
    f2 = d.get("Flags2", 0)
    if in_fight(d):
        return "COMBATE A PIE"''', '''def big_mode(d, flags):
    f2 = d.get("Flags2", 0)
    if in_fight(d):
        return "COMBATE A PIE"
    if not f2 & 1 and time.time() - fight["t"] < FIGHT_SECS:
        return "COMBATE"                     # combate de nave: manda aunque el juego diga atracado''')

# ---------- 7. Inara del CMDR fijado ----------
rep('''            xa["a"] = dict(until=now + 5, col=ORANGE, title="COMANDANTE FIJADO", big=p[0],
                           lines=[" · ".join(x for x in (p[1], p[2]) if x), "posible PvP"])''',
    '''            ia_ = ((d or {}).get("target") or {}).get("inara") or {}
            l2_ = inara_line(ia_, d) if ia_ and not ia_.get("none") else "posible PvP"
            xa["a"] = dict(until=now + 6, col=ORANGE, title="COMANDANTE FIJADO", big=p[0],
                           lines=[" · ".join(x for x in (p[1], p[2]) if x), l2_])''')
rep('''            put(surf, F["small"], t.get("rank") or "", (card.right - 8, y + 4), DIM, anchor="topright")''',
    '''            ia_ = t.get("inara") or {}
            if cmdr and ia_ and not ia_.get("none"):
                ally = my_squad(d) and ia_.get("squad", "").lower() == my_squad(d).lower()
                put(surf, F["small"], ("ALIADO · " if ally else "INARA: ") + inara_line(ia_, d, short=True),
                    (card.right - 8, y + 4), GREEN if ally else ORANGE, card.w - w_ - 120, anchor="topright")
            else:
                put(surf, F["small"], t.get("rank") or "", (card.right - 8, y + 4), DIM, anchor="topright")''')

CODE = r'''
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

'''
rep("\ndef render(surf):", CODE + "\ndef render(surf):")

rep('''# Enlace energético''', '''# Novedades v0.87
- Objetivos comunitarios cerrados: al final, tapados con una banda roja CERRADO («cobra la recompensa» si participaste); desaparecen a los 2 días.
- En la pantalla grande, las bajas a pie salen en el cuadro SRV / A PIE y los derribos en nave en el cuadro 3, sin tapar los demás.
- En combate de nave la pantalla grande pasa a COMBATE (sin MERCADO ni GALNET), también en Operations.
- CMDR fijado: con Inara salen su escuadrón, rango de combate y nave (ALIADO en verde si es de tu escuadrón). Se guarda 72 horas.
- EDSM: si no responde por los bloqueos de LaLiga sale «EDSM bloqueado (¿fútbol?)» y el sender lo reintenta cada 10 minutos.
# Enlace energético''')
rep('    ("0.86", "Salud < 30 %: pantalla roja; cierre en 3 s; copiloto en azul; arreglo del falso MENÚ PRINCIPAL al morir"),\n',
    '    ("0.86", "Salud < 30 %: pantalla roja; cierre en 3 s; copiloto en azul; arreglo del falso MENÚ PRINCIPAL al morir"),\n'
    '    ("0.87", "Objetivos CERRADOS, bajas en un cuadro, combate de nave manda, Inara del CMDR fijado, EDSM y arreglos"),\n')
s = re.sub(r'PANEL_VER = "v0\.86[^"]*"', 'PANEL_VER = "v0.87 · ' + time.strftime("%d/%m/%Y %H:%M") + '"', s)
open(P, "w", encoding="utf-8").write(s)
print("OK v0.87  (copia en " + P + ".bak86)")
