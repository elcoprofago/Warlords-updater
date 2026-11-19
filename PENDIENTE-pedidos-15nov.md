# Pedidos y bugs del 15/11/2026 (partidas con Nico)

Recibidos mientras corría la tanda 170. Cada parte es independiente; se trabaja una por sesión.

## A. Bugs

1. **Cuelgue al mover aliados de una ruina (NA_159, turno 17).** Héroe del usuario explora una ruina, obtiene
   Red Knights (4, 3 y 2 en tres intentos con las mismas jugadas); al moverlos, el juego de Nico (otra PC) se cuelga,
   las tres veces. En el turno 29, con Dushdana, los mismos 2 aliados se movieron sin cuelgue.
   Material: `C:\Warlords\HISTORY\NA_159_30.SAV`, `NA_159_31.SAV`, `NA_159.FIN`.
   Primer paso: reproducir con el .SAV más cercano al turno 17 (si no hay, partir del 30/31 y comparar qué cambia
   entre el héroe del turno 17 y Dushdana: tipo de héroe, pila llena, casilla de destino, orden de red del movimiento
   de aliados nuevos). Bisecar contra Darklord.exe sin parche (regla 4) para saber si el cuelgue es nuestro.
2. **Íconos de armas en la zona oculta del mapa (NA_160, turno 21, PC de Nico: 4 GB RAM, W11).** La niebla muestra
   mosaicos de ejércitos repetidos (captura del usuario). Hipótesis a descartar: superficie de dibujo perdida
   por falta de memoria vs. un índice de imagen fuera de rango en nuestro código de vista aliada. Mirar primero si
   pasa en otra PC con el mismo .SAV.
3. **Hecho en vista-aliada 1.0.234.0.** Causa: la 3.ª pasada del dibujo (0x459fb0) pinta el borde del bosque que se
   derrama sobre la casilla vecina después de las obras; po_draw3 repinta las obras de esa casilla (prueba_faro_bosque.py,
   MAL 0). Prueba del usuario: TAREAS 236. 1.0.235.0: repintar la obra entera la dejaba
   demasiado encima; ahora solo la pieza de arriba (cúpula, linterna, almenas), sin sombra (TAREAS 237).
   1.0.236.0: el borde del bosque de la propia casilla cortaba el cuerpo en línea recta; ahora se repinta el cuerpo sin el
   pie (capas OD_ALTO, borde irregular de copas) (TAREAS 238).
   **Bosque tapa la cúpula del faro (NA_159).** La cúpula debe dibujarse siempre encima del bosque.
   Ver `PENDIENTE-faros-muros.md` (orden de dibujo del faro).

### Averiguado el 16/11/2026 (sin cambios en el código todavía)
- **A1.** No hay .SAV del turno 17: el más cercano es `C:\Warlords\NETSAVES\NA_159_23_pausa.SAV` (ruina sin
  explorar). Comparando con NA_159_30, la ruina del turno 29 es **Lororia Ruins (24,124)**, contenido 4. El cuelgue es
  en la PC remota y no se reproduce con una sola PC. Sin Nico: cargar NA_159_23_pausa, llevar al héroe del turno 17 a
  Lororia y ver dónde aparecen los aliados (¿casilla vecina con pozo, trampa, muro o puente?). Con Nico: repetirlo
  con Darklord.exe sin parche (regla 4).
- **A3.** Orden de dibujo de la vista (0x459790): la 1.ª pasada pinta terreno (bosque incluido), ruina, obras
  (po_draw) y sitio; la 2.ª pinta ejércitos quietos y en 0x459d54 po_draw2 llama a ob_draw, que repinta faro y torre
  desde las 9 celdas vecinas. Ambas pintan solo celdas sucias (+6 & 0x20) salvo redibujo completo. Leído así, el
  bosque no debería tapar la cúpula: falta una captura o la ubicación del faro tapado en NA_159 para ver qué pieza falla.
- **A2.** Sin empezar.

## B. Guardado al pausar
**Hecho en vista-aliada 1.0.225.0.** El guardado ya existía, pero solo en la PC que pedía la pausa, y al cargarlo en red
el juego decía «no todos los jugadores pueden unirse». Ahora cada PC guarda al recibir el aviso de pausa (PP_PKT 1, con
el eco incluido), desde tl_idle (pp_save), con el mismo nombre `<partida>_<turno>_pausa`. Prueba: prueba_pausa.py
(MAL 0) y prueba_botones.py. Falta publicar después de la tanda 170 y la prueba del usuario (TAREAS 224).
Pedido original:
La pausa manual (PZ_MANUAL, `parches/vista-aliada/build.py` ~línea 10950) no guarda. Al entrar en pausa, guardar la
partida como hace el guardado automático del turno.

## C. Cuenta regresiva sonora al fin del turno
**Hecho en vista-aliada 1.0.224.0 (cr_tick en 0x4c1074; prueba_cuentaturno.py TODO OK). Falta publicar cuando
termine la tanda 170 (publicar-parche compara con C:\Warlords3) y la prueba del usuario (TAREAS 223).**
Que la cuenta regresiva sonora de los informes suene también en los últimos 5 s del turno (vencimiento en
[0x4ff7a8], ver build.py ~10936), y que los números se vean junto al cursor.
Aclaración del usuario: hoy la cuenta solo se activa mientras se consultan los informes; jugando en el mapa
(moviendo, etc.) nada avisa. Tiene que sonar y verse en cualquier pantalla del turno.

## D. Visor de historia: bloquear partidas en curso
- Una partida que no terminó (ni por final normal ni por decreto) no se puede ver en el Visor.
- Excepción: partidas marcadas "de prueba". La marca la decide una Votación con el voto favorable de **todos** los
  humanos, y viaja dentro del .SAV.

### D2. Menú «Mociones de votación» (definido por el usuario el 15/11)
**Etapa 1 hecha en vista-aliada 1.0.226.0** (submenú de mociones, moción en TL_OPEN y `--mocion N` a votacion.exe,
«Partida a prueba» por unanimidad de humanos → bloque 'MOCI' en el .SAV y P en el mapa con `RUINS\prueba.pcx`),
herramientas 1.0.0.4 (Votación 1.1.5 muestra la moción) y Visor de historia 1.0.22.0 (no abre partidas sin .FIN ni
marca P). Pruebas: prueba_mociones.py y prueba_botones.py (MAL 0). Falta publicar vista-aliada y herramientas después de
la tanda 170, y la prueba del usuario (TAREAS 225).
**Etapas 2 a 4 hechas en vista-aliada 1.0.227.0** (herramientas 1.0.0.5 con Votación 1.1.7): aprobación por más SÍ que
NO según Votación (humanos + votos virtuales), salvo «Partida a prueba» (unanimidad humana). Early end termina como
acuerdo (hi_acu) en todas las PC; Disqualification (submenú de colores, solo humanos vivos, `--bando N`) y Re-entry
(humano eliminado → bando de la computadora vivo con menos puntos, 0x440840/0x5643c8) se aplican en mo_round al final
de la ronda; Anything goes es una declaración (bandera en 'MOCI', V con `RUINS\valetodo.pcx`). Paquete TL_OPEN de 12
bytes. prueba_mociones.py y prueba_botones.py: MAL 0. Prueba del usuario: TAREAS 226.
**Marcas por letra, vista-aliada 1.0.231.0** (pedido 15/11; herramientas 1.0.0.6 con Votación 1.1.8): las mociones no
siempre se cumplen solas (el pase a humano lo hace el anfitrión a mano), así que se ven con letras en la esquina del
mapa, después del marco (mo_pdraw en 0x4c1b92/0x4c1d42/0x4c1ef2): P (bit 1), F de Early end (bit 4, ya no llama a
hi_acu: los detalles van con «acuerdo:» en el chat), V (bit 2) y C de la moción nueva 6 «Championship» (bit 8).
Free vote no lleva letra. Prueba del usuario: TAREAS 229.
**Textos en inglés (pedido 15/11):** menú, mociones, colores, avisos de pausa y votación, Lighthouse, Compare, Game
over, y Votación. Faltan: las órdenes por chat (el analizador depende de 'atac'/'mand'), los textos del Visor de
historia, y revisar si los PCX del juego tienen texto en castellano.
En el menú de comandos, un submenú (como el de Build) con mociones predeterminadas; elegir una abre la Votación
ya cargada con esa moción, y al cerrarse con resultado afirmativo el programa aplica la acción sola:
1. Partida «a prueba» → pone la marca P (y habilita el Visor en curso).
2. Finalización → termina la partida en forma anticipada (como el decreto).
3. Descalificación de un jugador → el humano pasa a jugador del sistema.
4. «Vale todo» → partida sin fair play.
5. «Enganche» (de engancharse) → un humano eliminado que quiere seguir jugando en la misma partida recibe el color
   del sistema con menos puntaje en ese momento (como `sides list`, color → human).
6. Otras, a incorporar.
El resultado sigue apareciendo en el informe de eventos, como hoy.
Primer paso: ver cómo la Votación actual (TL_*, build.py) guarda la moción y el resultado, y dónde se engancha el
submenú (dialogo de Build como modelo).

#### Diseño (15/11, tras estudiar el código)
- Hoy: «Votacion» del menú de partida (diálogo 35, VOTE_HOT) → `tl_disp` → `tl_sendopen(0)` → TL_OPEN (carga:
  herramienta, dword) → en cada PC `tl_recv` → `vt_open`/`pz_open` y `tl_idle` abre `votacion.exe --operador` o
  `--espectador <mascara>`. El estado vuelve como texto "VOT <sesión> <fase> ..." (`vt_state`); al "cerrado" se
  anota SI/NO en vt_tab (informe de eventos, tipo 0x13) y se guarda en el .SAV como bloque 'VOTA' (después vienen
  'POZO', 'OBRA'...). votacion.exe (repo `F:\source\repos\Votacion`, 1.1.4) no sabe de mociones.
- Submenú: como Build (`bm_open`, BM_DLG/BM_RES, modo BM_ON con los mismos manejadores del diálogo): un diálogo
  MO_DLG copia del 35 con un renglón por moción + «Votación libre» (la de hoy), abierto al elegir «Votacion».
- Moción elegida: va en la carga de TL_OPEN (segundo dword; un parche viejo la ignora) → MO_CUR en todas las PC;
  votacion.exe la recibe en la línea de comandos (`--mocion N`) y muestra su texto.
- Al cerrarse con resultado afirmativo (P: SI = humanos activos y NO = 0), cada PC aplica la acción en el mismo
  punto (vt_commit), así no desincroniza. El renglón del informe dice qué moción fue.
- Marca P: bloque nuevo del .SAV ('MOCI', banderas) detrás de los existentes; el Visor lo busca al final del .SAV.
- Etapas: 1) submenú + moción a votacion.exe + P (marca, dibujo, Visor); 2) Finalización; 3) Descalificación y
  Enganche (bando humano ↔ sistema); 4) Vale todo.

- Con la marca, el mapa principal muestra una **P** mayúscula, Arial Bold, verde claro con borde rojo, en el ángulo
  superior izquierdo.
- El Visor (`ia\visor-historia`) lee la marca y el estado de terminada (ver `PENDIENTE-partidas-terminadas.md`) y
  solo abre una partida en curso si está marcada.
- 1.0.232.0: mociones Special tournament (bit 0x10, T azul/dorado, RUINS	orneo.pcx) y Void game (bit 0x20, A gris/negro,
  RUINSnulada.pcx). Las mociones de solo bit van en MO_SOLOBIT y las letras en MO_MARCAS (agregar una nueva = una
  entrada en cada tabla + su hoja con _letra). Visor 1.0.23.0: letras junto al nombre (tabla MARCAS) y abre A como P.
- 1.0.269.0 (pedido del usuario, 19/11/2026): una segunda aprobación de la misma moción con marca la **quita** (mo_apply
  hace `xor` en vez de `or`, para P y para las de MO_SOLOBIT; Descalificación y Enganche no cambian). Para que un mismo
  cierre no se aplique dos veces (vt_state llama a mo_apply en cada estado «cerrado» con votos), mo_apply pone MO_CUR
  en 0 (libre) apenas lo lee. prueba_mociones.py: «segunda aprobación», con controles (segunda rechazada, cierre
  repetido, otra marca intacta). Prueba del usuario: TAREAS 271.
