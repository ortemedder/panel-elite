# Panel Elite v1.1 · parte 16: menús reordenados (v1.1.8)
#   9 FACCIÓN  -> submenú: SISTEMAS, BGS, RADAR, ACTIVIDAD, ESCUADRÓN, AMIGOS, OBJ. COMUNIDAD, RANGOS
#   7 EXPLORACIÓN -> solo exploración (6 botones)
#   11 RESUMEN DEL DÍA -> pestañas DÍA · GALNET · CALCULADORA
#   12 AJUSTES -> sin la calculadora

# --- 9 FACCIÓN: submenú ---
MENU[220] = "FACCIÓN"
PARENT[220] = 0
MENU[215] = "AMIGOS"
SUB9 = [("SISTEMAS", 192), ("BGS", 213), ("RADAR", 77), ("ACTIVIDAD", 78),
        ("ESCUADRÓN", 165), ("AMIGOS", 215), ("OBJ. COMUNIDAD", 132), ("RANGOS", 123)]
for _n, _v in SUB9:
    PARENT[_v] = 220

def view_sub9(surf, d, flags, now):
    for i, (name, v) in enumerate(SUB9):
        draw_button(surf, grid(i, 4, 2), str(i + 1), name, F["num"], lit=flash.get((9, i), 0) > now)

VIEWS[220] = view_sub9

def view_amigos(surf, d, flags, now):
    view_friends(surf, d, flags, now)
    pygame.draw.rect(surf, BLACK, (W - 200, TOP + 2, 196, 16))      # aquí no se vuelve a SESIÓN tocando

VIEWS[215] = view_amigos

# pestañas: SISTEMAS | BGS juntas; ESCUADRÓN | AMIGOS juntas; DÍA | GALNET | CALCULADORA
for _g in TABS:
    _g[:] = [t for t in _g if t[0] not in (132, 123, 192, 193, 213, 165)]
TABS[:] = [g for g in TABS if g]
for _g in TABS:
    if any(t == 11 for t, _ in _g):
        _g.append((211, "CALCULADORA"))
TABS.append([(192, "SISTEMAS"), (213, "BGS")])
TABS.append([(165, "ESCUADRÓN"), (215, "AMIGOS")])
PARENT[211] = 0

# la lista SISTEMAS ya tiene su pestaña BGS: fuera el botón de la v1.1.7
VIEWS[192] = _view192_v111
BGS_BTN = pygame.Rect(0, 0, 0, 0)

# --- 12 AJUSTES: la calculadora pasa al 11 ---
SET12[:] = [it for it in SET12 if not it or it[1] != 211]

# --- 7 EXPLORACIÓN: solo exploración ---
def view_sub7(surf, d, flags, now):
    for i, (n, name) in enumerate([("1", "EXPLORACIÓN"), ("2", "SISTEMA"), ("3", "EXOBIO"), ("4", "YACIM."), ("5", "DIARIO"),
                                   ("6", "ALIEN")]):
        draw_button(surf, grid(i, 3, 2), n, name, F["num"], lit=flash.get((7, i), 0) > now)

VIEWS[7] = view_sub7

# RADAR y ACTIVIDAD a pantalla completa: su botón vuelve al menú 9
def _full_v118(fn):
    def f(surf, d, flags, now):
        fn(surf, d, flags, now)
        r = FULL_BACK
        pygame.draw.rect(surf, BLACK, r, border_radius=4)
        pygame.draw.rect(surf, ORANGE, r, 1, border_radius=4)
        put(surf, F["btn"], "<", (r.centerx, r.y + 13), ORANGE, anchor="center")
        put(surf, F["tiny"], "MENÚ 9", (r.centerx, r.bottom - 6), ORANGE, anchor="center")
    return f

view_full = _full_v118(view_full)                         # se llama por su nombre desde la pantalla de espera y el render
VIEWS[77] = VIEWS[78] = view_full

_on_tap_v118 = on_tap

def on_tap(x, y):
    v = ui.get("view")
    if ui.get("idle_on"):
        return _on_tap_v118(x, y)
    if v == 0 and grid(8).collidepoint(x, y) and y > TOP:            # botón 9 del menú principal
        tap_flash((0, 8)); ui["view"] = 220; TAP_EV.set(); return
    if v == 220 and y > TOP:
        for i, (name, dest) in enumerate(SUB9):
            if grid(i, 4, 2).collidepoint(x, y):
                tap_flash((9, i)); ui["view"] = dest; ui["page4"] = 0
                if dest == 78:
                    ACT_GAL[0] = True
                if dest == 165:
                    ui["sqpage"] = 0
                TAP_EV.set(); return
        return
    if v == 7 and y > TOP:
        for i in range(6):
            if grid(i, 3, 2).collidepoint(x, y):
                tap_flash((7, i)); ui["view"] = 71 + i; TAP_EV.set(); return
        return
    if v in (77, 78) and FULL_BACK.inflate(10, 10).collidepoint(x, y):
        ui["view"] = 220; TAP_EV.set(); return
    if v == 215 and y > TOP:
        if SQ_BTN.collidepoint(x, y):
            tap_flash(("sqbtn",)); ui["view"] = 165; ui["sqpage"] = 0; TAP_EV.set()
        return
    return _on_tap_v118(x, y)
