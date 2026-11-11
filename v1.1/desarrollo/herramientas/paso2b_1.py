#!/usr/bin/env python3
"""Paso 2b-1: handle_note (6 versiones) y big_mode (5 versiones) en una sola version cada una."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aplanar import aplanar
P = sys.argv[1]
t = open(P, encoding="utf-8").read()

NOTA = r'''
# ---------- avisos del sender (handle_note): una sola version, por etapas ----------
def _nota_caza(kind, text):
    """Base + caza lanzado: COMBATE + CAZA."""
    _nota_base(kind, text)
    if ui.get("view") in (6, 9) and fighter_out(state.get("data")) and kind in ("underattack", "fighter", "combatmusic"):
        ui["view"] = 191

def _nota_musica(kind, text):
    """Musica de combate: no abre COMBATE dentro de la estacion, al atracar o recien despegado."""
    if kind == "underattack":
        CMB["att"] = time.time()
    if kind == "combatmusic":
        ok, why = combat_music_ok(text)
        if not ok:
            plog(f"Música de combate ({text}) sin abrir COMBATE: {why}")
            return
    _nota_caza(kind, text)

def handle_note(kind, text):
    now = time.time()
    if kind == "loadgame":                               # tras cargar la partida: 4 CUADROS
        LGB["t"] = now
    if kind == "died":                                   # caja negra
        try:
            caja_dump("nave destruida")
        except Exception as e:
            log_exc("caja negra", e)
    k = (kind, text)                                     # repetidos seguidos: uno solo
    if REPN["k"] == k and now - REPN["t"] < 3:
        REPN["n"] += 1; REPN["t"] = now
        return
    if REPN["n"]:
        plog(f"  (lo anterior, {REPN['k'][0]}: repetido ×{REPN['n'] + 1})")
    REPN.update(k=k, t=now, n=0)
    if kind == "underattack":                            # te atacan al atracar o despegar: sin cambiar de pantalla
        d = state.get("data") or {}
        st = (d.get("station") or {}).get("status")
        if d.get("Flags", 0) & 3 or st in ("SOLICITADO", "CONCEDIDO", "ATRACADO") or time.time() - UNDK["t"] < 60:
            v0 = ui.get("view")
            _nota_musica(kind, text)
            if ui.get("view") != v0:
                ui["view"] = v0
                plog("Te atacan al atracar o despegar: aviso sin cambiar a COMBATE")
            return
    _nota_musica(kind, text)
'''

MODO = r'''
# ---------- modo de la pantalla grande (big_mode): una sola version ----------
def big_mode(d, flags):
    m = _big_mode_base(d, flags)
    if fighter_out(d) and m not in ("COMBATE A PIE", "ATRAQUE"):
        m = "COMBATE"                                    # caza lanzado: no se quita el modo combate
    if m == "ATRACADO" and ((d or {}).get("colonia") or {}).get("dock"):
        if BIGCOL.get("m") != "COLONIZACIÓN":
            plog("Colonización: pantalla grande en modo COLONIZACIÓN")
        BIGCOL["m"] = "COLONIZACIÓN"
        return "COLONIZACIÓN"
    BIGCOL["m"] = m
    if alt_now(d) is not None:
        if m == "APROXIMACIÓN":
            return "APROXIMACIÓN + ALTÍMETRO"
        if m == "SUPERFICIE" and not (d.get("Flags2", 0) & 1) and not flags & (1 << 26):
            return "SUPERFICIE + ALTÍMETRO"
        if m == "ATRACADO":
            return "PUERTO PLANETARIO"
    if m == "SUPERFICIE" and flags & (1 << 26) and _geo(d)[0] is not None:
        return "SUPERFICIE + VELOCÍMETRO"
    return m
'''
t = aplanar(t, "handle_note", "_nota_base", NOTA)
t = aplanar(t, "big_mode", "_big_mode_base", MODO)
open(P, "w", encoding="utf-8").write(t)
print("OK paso 2b-1: handle_note y big_mode aplanados")
