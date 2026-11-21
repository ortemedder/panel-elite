# Panel Elite v1.1 · parte 12: avisos y modo pantalla (lineas 10564-10805 del panel entero)
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
    if kind == "mktsell":                                # v1.1: venta de material de tu construccion
        try:
            col_sold(text)
        except Exception as e:
            log_exc("colonia venta", e)
        return
    if kind in ("paxin",):                               # v1.1: pasajeros
        try:
            pax_note(kind, text)
        except Exception as e:
            log_exc("pasajeros", e)
        return
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



# ========== big_cell: cadena de 2 etapas, cada una llama a la anterior ==========
# big_cell_base -> big_cell

def big_cell_base(S, cell, v, d, flags, now, r, font, how, extra=""):
    BIG.setdefault("rects", []).append((v, r))
    if v in (72, 150):
        BIG["fast"] = True          # mapa del sistema o plano a pie: se mueven
    if v == 150:
        pygame.draw.rect(S, DIM, r.inflate(-4, -4), 1, border_radius=6)
        lab = font.render("MAPA" + extra, True, DIM)
        S.blit(lab, (r.x + 10, r.y + 4))
        top = r.y + lab.get_height() + 6
        draw_map(S, pygame.Rect(r.x + 6, top, r.w - 12, r.bottom - 6 - top), d, now)
        return
    fn = view_navbig if v == 3 else view_orrery_big if v == 72 else VIEWS.get(v)
    sharp = bool(cfg.get("sharp")) and fn is not None
    if not sharp:
        big_cell_draw(cell, fn, d, flags, now)
    pygame.draw.rect(S, DIM, r.inflate(-4, -4), 1, border_radius=6)
    lab = font.render(str(MENU.get(v, v)).upper() + extra, True, DIM)
    S.blit(lab, (r.x + 10, r.y + 4))
    top = r.y + lab.get_height() + 6
    src = cell.subsurface((0, TOP, W, H - TOP))
    area = pygame.Rect(r.x + 4, top, r.w - 8, r.bottom - 3 - top)
    if sharp:
        if hi_cell(S, fn, d, flags, now, area, how):
            return
        big_cell_draw(cell, fn, d, flags, now)
    if how == "fill":
        big_fill(S, src, area)
        return
    sc = min(area.w / src.get_width(), area.h / src.get_height())
    size = (int(src.get_width() * sc), int(src.get_height() * sc))
    try:
        img = pygame.transform.smoothscale(src, size)
    except ValueError:
        img = pygame.transform.scale(src, size)
    y = area.y if how == "top" else area.centery - size[1] // 2
    S.blit(img, (area.centerx - size[0] // 2, y))

def big_cell(S, cell, v, d, flags, now, r, font, how, extra=""):
    if not BIG.get("rects"):
        BIG["cellmap"] = []
    if v != 150:
        top = r.y + font.size(str(MENU.get(v, v)).upper() + extra)[1] + 6
        BIG["cellmap"].append((v, pygame.Rect(r.x + 4, top, r.w - 8, r.bottom - 3 - top), how))
    return big_cell_base(S, cell, v, d, flags, now, r, font, how, extra)


# ========== big_go: cadena de 2 etapas, cada una llama a la anterior ==========
# big_go_base -> big_go

def big_go_base(surf):
    """Si toca redibujar la pantalla grande en este ciclo."""
    perf_update()
    if not hdmi_panel():
        return big_due()
    # modo PANEL: solo si el panel ha cambiado (sin contar el engranaje que gira)
    sig = pygame.image.tostring(surf.subsurface((0, 0, GEAR.x, H)), "RGB") + \
          pygame.image.tostring(surf.subsurface((GEAR.x, GEAR.bottom, W - GEAR.x, H - GEAR.bottom)), "RGB")
    changed = sig != BIG.get("psig")
    if changed:
        BIG["psig"] = sig
    if cfg.get("bigfps", "AUTO") != "AUTO" and not big_due():
        if changed:
            BIG["psig"] = None                 # que se dibuje en el siguiente ciclo permitido
        return False
    if changed or time.time() - BIG.get("plast", 0) > 5:
        BIG["plast"] = time.time()
        return True
    return False

def big_go(surf):
    WD["t"] = time.time()
    if not WD["on"]:
        WD["on"] = True
        threading.Thread(target=watchdog_loop, daemon=True, name="vigilante").start()
    return big_go_base(surf)


# ========== big_tap: cadena de 3 etapas, cada una llama a la anterior ==========
# big_tap_base -> big_tap_99j -> big_tap

def big_tap_base(xn, yn):
    """Toque en la HDMI (coordenadas 0..1)."""
    bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
    if hdmi_panel():
        sc = min(bw / W, bh / H)
        ox, oy = (bw - W * sc) / 2, (bh - H * sc) / 2
        px, py = (xn * bw - ox) / sc, (yn * bh - oy) / sc
        if 0 <= px < W and 0 <= py < H:
            on_tap(int(px), int(py))
        return
    for v, r in BIG.get("rects") or []:
        if r.collidepoint(xn * bw, yn * bh):
            ui["view"] = v if v in VIEWS else ui["view"]
            cfg["hdmi"] = "panel"; save_cfg(); TAP_EV.set()
            return
    cfg["hdmi"] = "panel"; save_cfg(); TAP_EV.set()      # sin cuadros (espera, atraque...): pasa a PANEL

def big_tap_99j(xn, yn):
    if not hdmi_panel():
        with lock:
            d_ = state["data"]
        bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
        if ops_on(d_) and mega_rect(bw, bh).collidepoint(xn * bw, yn * bh):
            mega_tap(); return
    big_tap_base(xn, yn)

def big_tap(xn, yn):
    if not hdmi_panel():
        bw, bh = BIG.get("w") or 1024, BIG.get("h") or 600
        X, Y = xn * bw, yn * bh
        for v, area, how in BIG.get("cellmap") or []:
            if not area.collidepoint(X, Y) or v not in VIEWS:
                continue
            px, py = cell_point(area, how, X, Y)
            if not (0 <= px < W and TOP <= py < H):
                break
            f0, v0 = dict(flash), ui["view"]
            ui["view"] = v
            on_tap(int(px), int(py))
            if flash != f0 or ui["view"] != v:          # ha tocado un boton: se queda en 4 CUADROS
                if ui["view"] == v:
                    ui["view"] = v0
                TAP_EV.set()
                return
            ui["view"] = v0
            break
    big_tap_99j(xn, yn)


# ========== carrier_dest: cadena de 2 etapas, cada una llama a la anterior ==========
# carrier_dest_base -> carrier_dest

def carrier_dest_base(d):
    """(tipo de foto, rotulo) si el destino es un portanaves: por el destino marcado o por el sistema final de la ruta."""
    own, sq = d.get("carrier") or {}, d.get("sqcarrier") or {}
    D = d.get("dest") or {}
    nm = (D.get("name") or "").upper()
    if nm and CALLSIGN.search(nm):
        if own.get("callsign") and own["callsign"].upper() in nm:
            return "fc", "TU PORTANAVES"
        if sq.get("system") and sq["system"] == d.get("system"):
            return "sq", "PORTANAVES DE ESCUADRÓN"
        return "fc", "PORTANAVES"
    end = d.get("routeend") or ((d.get("route") or [None])[-1])
    if d.get("route") and end:
        if own.get("system") and end[0] == own["system"]:
            return "fc", "TU PORTANAVES"
        if sq.get("system") and end[0] == sq["system"]:
            return "sq", "PORTANAVES DE ESCUADRÓN"
    return None, ""

def carrier_dest(d):
    k, lab = carrier_dest_base(d)
    if k:
        return k, lab
    D = d.get("dest") or {}
    di = d.get("dstinfo") or {}
    t = di.get("type")
    if D.get("name") and t:
        if t == "FleetCarrier":
            return "fc", "PORTANAVES"
        if "squadron" in t.lower():
            return "sq", "ESCUADRÓN"
        if t in ST_BG:
            return ST_BG[t], ST_TYPE.get(t, t).upper()
    return None, ""


