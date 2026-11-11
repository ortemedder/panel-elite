# Panel Elite v1.1 — depuración

Proyecto nuevo y aparte. La v1.0b20 (original/panel_v1.0b20.py, GitHub panel-elite, etiqueta v1.0b20) NO se toca.

## Estado (paso 1 de 5, 10/11/2026)
- [x] Copia de referencia de la v1.0b20 y datos de prueba.
- [x] herramientas/capturar.py: dibuja las 60 pantallas con datos fijos y compara versiones.
  - 52 salen idénticas en dos ejecuciones; 8 cambian solas (dependen de datos vivos: 77 RADAR, 78 ACTIVIDAD, 121 LOG, 124/1244 AJUSTES, 160 PANTALLA, 192/193 FACCIÓN). Hay que fijar sus datos antes de compararlas.
- [x] Las 8 pantallas que cambiaban solas ya están fijadas (red, rendimiento, log, GALNET, objetivos): 3 capturas seguidas de la b20 salen 60 de 60 iguales.
- [x] Paso 2a: herramientas/limpiar_muertas.py quita las 23 versiones de funciones que nunca se usan (279 líneas). v11/panel.py: 60 de 60 pantallas iguales a la b20.
- [x] Paso 2b-1: handle_note (6 versiones) y big_mode (5) en una sola cada una (herramientas/aplanar.py + paso2b_1.py).
  - Comprobado: 60 de 60 pantallas iguales y herramientas/equivalencia.py con casos al azar: big_mode 400 de 400, handle_note 500 de 500 iguales a la b20.
- [x] Paso 2b-2: herramientas/nombres_unicos.py. Ya NINGUNA funcion esta definida dos veces: las 75 versiones anteriores se llaman nombre__1, nombre__2… (on_tap__1…__15, render__1…__14, view_navx__1…). Las que solo quedaban en VIEWS y se sobrescribian, fuera (view_sub7__1, view_sub12__1, view_viajes__1, view_colonia__1). 12.230 lineas.
  - Comprobado: 60 de 60 pantallas iguales; equivalencia.py ahora tambien con 600 toques al azar en las 60 pantallas: big_mode 400/400, handle_note 500/500, on_tap 600/600 iguales a la b20.
- [x] Paso 2b-3: herramientas/juntar_cadenas.py. Las 34 cadenas tienen nombres que dicen de que parche es cada etapa (render_base -> render_b3 -> … -> render) y llaman directamente a la anterior: ya no hay alias. Las 24 que se podian mover estan juntas al final, cada una con su indice (render 15 etapas, on_tap 16…).
  - Comprobado: 60/60 pantallas, big_mode 400/400, handle_note 500/500, on_tap 600/600 iguales a la b20.
- [ ] Paso 2c (opcional, a mano): fundir etapas pequeñas cuando se lea mejor una sola funcion.
- [x] Paso 3: herramientas/dividir.py. v11/panel.py es ahora un cargador pequeño y el codigo esta en v11/partes/ en 14 archivos que se cargan en orden en el mismo espacio de nombres (igual que un solo archivo): 00 inicio y menus, 01 red y tactil, 02 exploracion, 03 navegacion y versiones, 04 ajustes y espera, 05 pantalla grande, 06 galnet/objetivos/voz, 07 alertas y combate, 08 v0.92-v0.99, 09 faccion, 10 radar/colonizacion/viajes, 11 relojes/altimetro/velocidad, 12 avisos y modo de pantalla, 13 cadenas (render, on_tap...).
  - Comprobado: unidas, las partes son identicas al archivo del paso 2b-3 (guardado en original/panel_v11_un_archivo.py). 60/60 pantallas, big_mode 400/400, handle_note 500/500, on_tap 600/600 iguales a la b20.
  - Pendiente (mas adelante, con calma): ir moviendo funciones a la parte de su tema; ahora cada parte sigue el orden historico.
- [x] Paso 4 (preparado): instalar_v11.sh instala la v1.1 en ~/panel-v11 copiando tus ajustes y datos; cambiar_panel.sh v11 / b20 cambia cual arranca el servicio (con un ajuste de systemd que se quita al volver). PANEL_VER = "v1.0b20 · v1.1 prueba". 60/60 pantallas iguales.
- [x] Paso 4 (en la Pi): probada en la Pi 4 de Ortem y en la Pi 3 de KORZO; único fallo (ACTIVIDAD, deque/dict) arreglado.
- [x] Paso 5 (11/11/2026): v1.1 DEFINITIVA. PANEL_VER "v1.1", sender v1.0b13, actualizar_v11.sh (versión completa con copia del código anterior), subir_v11.sh (repo panel-elite-v11), parte 14_novedades_v11.py con lo nuevo.
  - Comprobado: big_mode 400/400, handle_note 500/500, on_tap 594/600 (las 6 distintas son de 12 AJUSTES, que ahora tiene 4 filas con CALCULAR). Pantallas distintas de la b20 solo donde hay cambios: 0 (aviso de sender), 12, 160 (RELOJ), 161/163 (avisos nuevos), 1244, 1245, 141 (novedades).
- [ ] v1.1.x: arranque más rápido, revisar las pantallas que más CPU gastan (SISTEMA primero), ordenar funciones por temas.

## Cifras de la v1.0b20
- 12669 líneas, 590 funciones, 57 definidas varias veces.

## Funciones definidas varias veces (veces · nombre · líneas)
16 · on_tap · 424 7605 8087 8644 9101 9364 9748 10202 10504 10607 11101 11240 11475 11777 12100 12383
15 · render · 8319 8763 9131 9739 10194 10463 11079 11149 11230 11580 11721 12088 12368 12627 12654
6 · handle_note · 202 8681 12127 12323 12584 12647
5 · view_navx · 2115 7146 7262 7512 7848
5 · big_mode · 3694 8673 11249 12075 12617
4 · draw_idle · 2930 9930 10134 10175
3 · voice_say · 4830 7987 8150
3 · vj_btn · 8490 8801 10894
3 · view_viajes · 8514 8804 10899
3 · view_pol · 1973 8706 8940
3 · view_mining · 1030 7674 7708
3 · view_fac · 9027 9247 9451
3 · idle_crawl · 2892 9075 9209
3 · fac_watch · 9699 10286 11891
3 · draw_fac_screen · 9802 11771 12176
3 · carrier_kind · 7034 7162 7592
3 · big_tap · 7877 8096 8296
2 · voz_txt · 8141 12417
2 · voice_ok · 4827 7982
2 · view_sub7 · 1126 10341
2 · view_sub124 · 2677 10412
2 · view_sub12 · 2708 4447
2 · view_pp · 2036 7730
2 · view_market · 1710 7453
2 · view_explo · 879 7836
2 · view_evlist · 6048 11184
2 · view_colonia · 10989 11300
2 · view_changelog · 2480 7641
2 · stream_snap · 4812 11954
2 · render_big · 3714 11744
2 · pueblo_estado · 10398 10573
2 · plog · 4536 12603
2 · perf_update · 6265 8218
2 · perf_side · 6304 9945
2 · perf_parts · 6287 8232
2 · mega_watch · 7302 8049
2 · mega_left · 7298 8030
2 · hold_rect · 10154 10227
2 · fac_states · 9013 9427
2 · fac_rows · 9005 9441
2 · draw_xa · 3437 10954
2 · draw_mega · 7317 8064
2 · draw_hold · 10157 10230
2 · draw_alt · 12005 12510
2 · draw_alert · 2951 10946
2 · draw_act_screen · 10059 12239
2 · combat_music_ok · 12112 12316
2 · col_pend · 11217 11452
2 · col_here · 11285 11793
2 · carrier_dest · 7089 7196
2 · carrier_bg · 7046 7177
2 · big_go · 6310 8131
2 · big_cell · 3640 8276
2 · bgs_lines · 8690 8895
2 · act_enabled · 10125 10256
2 · act_bg · 10045 12199
2 · _hace · 10570 11297
