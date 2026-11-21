# Panel Elite v2.0 · parte 51: v2.0b14 — AJUSTES y lo que quedaba del MENÚ con la barra nueva (con PANTALLA v2)
#   12 AJUSTES, 124, 1244 OPCIONES, 160 PANTALLA, 161 ALERTAS, 162 CAMBIO AUTO, 163 SONIDO Y VOZ, 164 TECLAS, 1245 VERSIONES,
#   1246 PERMISOS, 121 LOG, 122 STREAM, 140/141 MANUAL, y también 77 CDSN, 78 ACTIVIDAD, 100 EN VIVO y 150 MAPA en el MENÚ.
#   Son botoneras y listas de ajustes: en vez de rehacerlas una a una, un ADAPTADOR dibuja la pantalla de siempre en
#   todo el hueco del MENÚ nuevo (1280x680, debajo de la barra nueva), nítida y con las letras a su tamaño, y pasa cada
#   toque a su punto de 480x320: cada botón hace exactamente lo mismo que antes. Así ya no queda ninguna pantalla del
#   MENÚ con la barra vieja ni con franjas.

LZ["adap"] = {}

def lz_adaptada(v, full=False):
    """full: pantallas que usan también la franja de arriba (CDSN, ACTIVIDAD): entera dentro del hueco."""
    y0 = 0 if full else TOP
    def fn(L, area, d, flags, now):
        vf = VIEWS.get(v)
        if vf is None:
            return lz_vacio(L, area, "pantalla no disponible")
        rr = L._r(area).clip(L.real.get_rect())
        if rr.w < 20 or rr.h < 20:
            return
        sx, sy = rr.w / W, rr.h / (H - y0)
        if full:                                       # igual en ancho y alto (nada ovalado), centrada
            sx = sy = min(sx, sy)
        k = min(sx, sy)
        xo = (rr.w - int(W * sx)) // 2
        size = (int(W * sx), int(H * sy) + 2)
        tmp = LZ["adap"].get(size)
        if tmp is None:
            LZ["adap"].clear()
            tmp = LZ["adap"][size] = pygame.Surface(size)
        tmp.fill(BLACK)
        keep = dict(F)
        F.update(hi_fonts(k))
        HI_PASS[0] = True
        try:
            vf(ScaledSurf(tmp, sx, sy), d, flags, now)
        finally:
            HI_PASS[0] = False
            F.clear(); F.update(keep)
        top = int(y0 * sy)
        L.real.blit(tmp, (rr.x + xo, rr.y), pygame.Rect(0, top, size[0], min(rr.h, size[1] - top)))
        lz_hit(area, "adap", area.x, area.y, area.w, area.h, y0)
    fn.__name__ = f"lz_adaptada_{v}"
    return fn

def _lz_adap(acc, X, Y):
    """Toque en una pantalla adaptada: al mismo punto de la pantalla de 480x320."""
    area = pygame.Rect(acc[1], acc[2], acc[3], acc[4])
    y0 = acc[5]
    if y0 == 0:                                       # entera: escala única y centrada
        k = min(area.w / W, area.h / H)
        area = pygame.Rect(area.x + (area.w - int(W * k)) // 2, area.y, int(W * k), area.h)
    ox = (X - area.x) * W / area.w
    oy = y0 + (Y - area.y) * (H - y0) / area.h
    on_tap(int(ox), int(oy))

LZ_ACC["adap"] = _lz_adap

LZ_ADAPTADAS = (12, 124, 1244, 160, 161, 162, 163, 164, 1245, 1246, 121, 122, 140, 141, 77, 78, 100, 150)
for _v in LZ_ADAPTADAS:
    if _v in VIEWS and _v not in LZ_PANEL:
        LZ_PANEL[_v] = lz_adaptada(_v, full=_v in (77, 78))
