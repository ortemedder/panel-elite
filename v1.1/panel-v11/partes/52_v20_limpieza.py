# Panel Elite v2.0 · parte 52: v2.0 — LIMPIEZA SEGURA
#   - Sin pantalla pequeña de 3,5" (escribe a /dev/null): ya no se convierte la imagen de 480x320 a bytes en cada
#     vuelta para tirarla (menos CPU). Si alguien enchufa una de 3,5", sigue funcionando como antes.
#   - BGS_BTN (el botón BGS > que quitó la v1.1.8) quedó en Rect(0,0,0,0): tocar justo la esquina de arriba a la
#     izquierda en SISTEMAS abría el BGS en vez de volver. Fuera de la pantalla.
#   - _hace: la parte 26 reusó el nombre con otro significado («hace hace 20766 días» en COLONIZACIÓN > EN EL SISTEMA
#     y en el BGS de 480x320). Ahora entiende las dos formas: segundos (parte 10) o una hora del reloj (parte 26).
#   - MANUAL > PANTALLA GRANDE y PRIMEROS PASOS (ratón) al día con la v2.0.
#   Se queda: los modos 4 CUADROS / MIXTO / GRANDE y NITIDEZ, porque con 12 AJUSTES > PANTALLA v2 en NO el panel
#   vuelve a ser la v1.1.20b (la red de seguridad para la instalación universal), y el adaptador de AJUSTES.

_to_fb_bytes_v20 = to_fb_bytes

def to_fb_bytes(surf, bpp, stride):
    if SMALL.get("null"):
        return b""                                         # /dev/null: nada que convertir (igual que la vuelta anterior)
    return _to_fb_bytes_v20(surf, bpp, stride)

BGS_BTN = pygame.Rect(-100, -100, 0, 0)

def _hace(x):
    if x is None:
        return "?"
    if x > 1e9:                                            # una hora del reloj (parte 26): «hace 3 h»
        s = time.time() - x
        return f"hace {s / 86400:.0f} días" if s > 2 * 86400 else f"hace {s / 3600:.0f} h" if s > 5400 else "hace poco"
    return "?" if x < 0 else "ahora" if x < 60 else f"{int(x // 60)} min" if x < 3600 else \
        f"{x / 3600:.0f} h" if x < 172800 else f"{x / 86400:.0f} días"   # segundos (parte 10): «3 h»

# --- MANUAL al día ---------------------------------------------------------------------------------------------
_MAN_GRANDE_V20 = """
Con 12 AJUSTES > PANTALLA v2 en SÍ (de fábrica) la HDMI se dibuja a 1280x800 de verdad. En la de 7" de KORZO
(1024x600) se ve igual, un poco más pequeña y con dos franjas negras finas a los lados.
# Un solo modo
- TABLERO: los cuadros de datos que elige sola según la situación (abajo).
- MENÚ: toca la barra de arriba del tablero (o clic derecho, TAB o pulsación larga) y sale el MENÚ a pantalla entera.
  Vuelve solo al tablero a los 20 s sin tocar.
- Todos los botones del MENÚ hacen lo mismo que antes. Las listas largas se mueven con flechas ▲ ▼ o pasan de página
  al tocar.
# Tableros
- VIAJE: en vivo, navegación, exploración y sistema.
- APROXIMACIÓN (cerca de un planeta o anillo): sistema, exobiología y yacimientos.
- SUPERFICIE (aterrizado, SRV o a pie): exobiología, SRV y MAPA del recorrido. En el Rhino: yacimientos y minería.
- ATRACADO: en vivo, estación, mercado (o RESUMEN DEL DÍA) y GALNET, que alterna con CARGA/MISIÓN y OBJETIVOS COMUNITARIOS.
  Con pasajeros, el cuadro 4 enseña la CABINA.
- ATRAQUE: la estación a pantalla entera al conceder el atraque, con tu plataforma, el reloj y el altímetro en los puertos
  planetarios.
- COMBATE: combate, registro de combate y pips.
- COMBATE A PIE: EN VIVO, SRV / RHINO / A PIE y el MAPA.
# Si algo se ve raro
- 12 AJUSTES > PANTALLA v2 en NO: vuelve a la v1.1.20b (modos 4 CUADROS, MIXTO, GRANDE y NITIDEZ en AJUSTES > PANTALLA).
- Los avisos salen en las dos pantallas.
"""

for _i, _m in enumerate(MANUAL):
    if _m[0] == "PANT. GRANDE":
        MANUAL[_i] = (_m[0], _m[1], _MAN_GRANDE_V20)
    elif _m[0] == "INICIO":
        MANUAL[_i] = (_m[0], _m[1], _m[2].replace(
            "- Clic derecho o TAB: la pantalla HDMI cambia entre PANEL (los menús, para manejarlos con el ratón) y TABLERO (los cuadros de datos).",
            "- Clic derecho o TAB: abre el MENÚ en la HDMI (vuelve solo al tablero a los 20 s)."))
man["cache"] = None
