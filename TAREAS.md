# Tareas del usuario

Cada tarea tiene un número fijo: no cambia aunque se resuelva. Las nuevas toman el número siguiente (hoy, la 80).
`- [ ]` pendiente, `- [x]` cumplida; las cumplidas pasan a «Hecho» con su fecha y resultado.
Esta es la lista completa. Las del Puente Warlords están en `puente-warlords\TAREAS.md` y figuran abajo en el
orden sugerido como «Puente 1», «Puente 2». El repo Votacion no tiene tareas propias: las de la Votación y el
Sorteo están acá (tarea 18).

## Orden sugerido
1. **Tarea 78** (tanda de los pozos vistos, en esta PC).
2. Con la notebook: **tarea 77** (pozos iguales en las dos PC), **Puente 10** (net.ini) y **Puente 11** («Anfitrión» con la partida vieja abierta).
3. **Puente 7** (botón «Copiar IP», con lo que tiene que anotar Nico): en la próxima partida con él.
4. **Tarea 36** (revisar el borrador del Manual) y **tarea 42** (leer el anexo de la IA).
5. **Tarea 27** (misión de la trampa, con dos jugadores humanos).

# Pendientes

- [ ] **78.** IA: ¿ya no cae en los pozos que ve? (vista-aliada 1.0.97.0, 30/10/2026)
Cambio: la computadora ya no camina por un pozo, remolino o trampa que su bando descubrió (tampoco para levantar el
ítem de un caído). Vos sí podés entrar a propósito, eligiendo esa casilla como destino.
1. Actualizador: instalá vista-aliada **1.0.97.0** en C:\Warlords3.
2. Monitor de IA → **Ninguna**, marcá solo **hex_pozos_PV_control** (la misma de la tarea 70), Partidas: **10**,
   **Nueva tanda**.
3. Avisame cuando termine. Si ves héroes que se quedan quietos junto a un pozo turno tras turno, anotalo acá.
Resultado:

- [ ] **77.** En red, los pozos tienen que ser los mismos en las dos PC (vista-aliada 1.0.97.0, 30/10/2026)
Cambio: hasta ahora, en una partida en red cada PC sorteaba sus propios pozos y remolinos. Ahora el anfitrión le
manda los suyos a los demás al empezar (igual que ciudades y ruinas), y si las PC llegan a diferir el juego lo
detecta como cualquier otra desincronización.
1. En **esta PC y en la notebook**: Actualizador, opción **9**; vista-aliada tiene que quedar **1.0.97.0**.
2. Partida **nueva** en red con **Hidden Ruins** y **Discover Ruins**; esta PC de anfitrión, la notebook se une.
3. Con un jugador de cada PC, caminá hasta descubrir un pozo o remolino. Anotá dónde está y fijate en la otra PC
   (si son aliados con vista aliada, o mirando más tarde con el otro jugador): tiene que estar **en la misma casilla**.
4. Mandá un ejército barato a un pozo ya descubierto: tiene que morir en las dos PC, con la misma tumba al lado.
5. Construí una trampa con un ejército con «trap» y que un ejército del otro jugador caiga en ella: tiene que morir en
   las dos PC.
6. Si en algún momento sale un aviso de partida desincronizada, anotá en qué paso.
Resultado:

- [ ] **42.** Leer el anexo «Cómo juega la computadora» (25/10/2026)
Abrí `manual\Anexo-IA.pdf` (22 páginas). Explica cómo ataca, defiende, explora, produce, hace diplomacia y cumple misiones la
computadora, y qué le agrega el parche. Cada afirmación dice si está VERIFICADO (en el código o en las tandas) o INFERIDO.
1. Marcá lo que no coincida con lo que viste jugando contra la computadora.
2. Fijate en el capítulo 16 («Lo que todavía no se sabe»): si querés que se investigue algo de ahí, decímelo.
Resultado:

- [ ] **36.** Revisar el borrador del Manual de uso (23/10/2026)
  1. Abrir `manual\Manual-Era-de-Alianzas.pdf`.
  2. Anotar lo que falte, sobre o esté mal explicado (capítulo y página) y pasármelo en una sesión.

- [ ] **27.** Misión dura: escoltar al equipo que desarma una trampa (22/10/2026)
Nueva misión de héroe, difícil: «Escort trap-disarming team to Afland02». Se cumple si **un ejército tuyo detona
la trampa** (muere, como siempre) y **después el héroe llega por tierra** a una casilla vecina (o a la de la trampa).
Volando o en barco no cuenta. Si la detona otro jugador, la misión fracasa. Solo te la ofrecen por trampas **de otro
jugador** que **ya descubriste**. Como la computadora todavía no construye trampas, hacen falta **dos jugadores
humanos en esta PC** (turnos alternados). Va con el mismo parche que la tarea 26 (paso 0 de esa tarea).
1. Partida nueva en esta PC con **dos jugadores humanos** (A y B), con misiones de héroe activadas, incluida la
   dificultad **Hard**.
2. Con A, construí una trampa (como en la tarea 26) en tierra, a unas 5 a 15 casillas de donde va a andar el héroe de B.
3. Con B, pasá al lado de la trampa hasta que salga «You have discovered the trap …».
4. Con el héroe de B pedí misiones **Hard** en un templo varias veces (o en turnos distintos): alguna vez tiene que
   salir «Escort trap-disarming team to Afland02» (con el nombre de esa trampa), y el texto «… must escort a
   trap-disarming team to the trap Afland02.».
5. Mandá a la trampa un ejército barato de B (no volador): tiene que morir y la misión seguir. Llevá el héroe de B
   caminando a una casilla al lado: la misión tiene que quedar **cumplida** y dar el premio.
6. Si podés, repetí con una segunda trampa y que la detone A (o un tercero): mientras le queden explosiones la misión
   de B sigue; cuando la gastan del todo (tres veces) sin B, tiene que **fracasar** al turno siguiente. Y otra vez llegando con el héroe volando: no tiene que cumplirse hasta que llegue por tierra.
7. Anotá abajo qué viste (si el nombre de la misión entra bien en su ventana).
Resultado:

# Hecho

- [x] **79.** De noche, los Zappers tienen que camuflarse (vista-aliada 1.0.98.0, 30/10/2026)
Lo que viste en la partida en red: los Zappers se veían normales de noche. Causa: su archivo (`ARMY\Zappers.ARM`)
trae el bono con el nombre viejo **camo**, y desde la 1.0.88.0 el parche solo reconocía **camouflg**. Ahora valen
los dos: no hace falta tocar ningún bando ni escenario.
1. En **esta PC y en la notebook**: Actualizador, opción **9**; vista-aliada tiene que quedar **1.0.98.0**.
2. Partida (puede ser la misma de la tarea 77) con **Day/Night**: de noche, un grupo **solo de Zappers**, quieto y
   fuera de una ciudad, tiene que verse verdoso y tenue, como en la tarea 57, mirado por otro jugador.
3. Con un héroe en el grupo, o un ejército sin el bono, tiene que verse normal (como siempre).
Resultado:
Resultado (30/10/2026): las armas camufladas se ven bien de noche.

- [x] **76.** El aviso de la pausa, sobre un papiro (vista-aliada 1.0.96.0, 30/10/2026)
Cambio: «Votacion en curso: partida en pausa» ahora va sobre el papiro de los cuadros de info (el de los pozos y
remolinos), en letra marrón oscura. Ya se vio en esta PC; falta verlo en una partida en red.
1. En **esta PC y en la notebook**: Actualizador, opción **9**; vista-aliada tiene que quedar **1.0.96.0**.
2. Partida en red; como anfitrión abrí la **Votación**.
3. Mirá el aviso en las dos PC: ¿se lee bien? ¿tapa algo que moleste?
Resultado (30/10/2026, usuario): se ve bien.

- [x] **72.** El Actualizador solo deja el juego completo en una carpeta vacía (29/10/2026)
Cambio (Actualizador 1.0.15.0 y juego completo nuevo): la opción 6 ahora trae también los archivos originales de GOG
que faltaban (`keys.w3`, `STRAT_L.BMP`, `STRAT_S.BMP`, los de `DATA`, los 10 bandos de fábrica y la música
`Track20.ogg`), y si falta DirectPlay ofrece activarlo. Ya se probó en esta PC en una carpeta vacía; falta ver
que el juego abra y juegue en red.
1. Esperá a que el Actualizador diga **v1.0.15.0** en el título (al abrirlo se actualiza solo).
2. En la notebook, creá una carpeta vacía, por ejemplo **C:\Prueba-W3**.
3. Para que el Actualizador use esa carpeta: en el Explorador escribí **%LOCALAPPDATA%** en la barra, creá la
   carpeta **Warlords3-Actualizador** (si no está) y adentro un **juego.txt** con una sola línea: `C:\Prueba-W3`.
   Al terminar la prueba borrá ese juego.txt para volver a tu carpeta de siempre.
4. Opción **6**. Si pregunta por DirectPlay, respondé **S** y aceptá el permiso de Windows.
5. Abrí **Darklord.exe** de esa carpeta: tiene que llegar al menú. Después uní la notebook a una partida en red.
Resultado:

- [x] **18.** Votación y Sorteo en red, con tu notebook como segundo jugador (29/10/2026; antes con Nico)
Ya está comprobado que a la otra PC le llegan los votos y el cierre; lo que falla es cómo se ven las ventanas allá
(en la PC anfitriona se ven bien). Votación 1.1.4 y Sorteo 1.1.3 anotan lo que hacen en un .log. Con la notebook no
dependés de que Nico mande nada. (Estaba mal marcada como cumplida el 26/10: nunca se hizo.)
1. En la notebook: Actualizador, opción **9** (parches: tiene que quedar vista-aliada **1.0.94.0**), después la
   **11 (Votación)** y la **12 (Sorteo)**: los títulos tienen que decir **v1.1.4** y **v1.1.3**.
2. Partida en red: esta PC de anfitrión, la notebook se une (Puente). Si el Puente dice «los archivos del juego no
   coinciden», es que falta el paso 1 en alguna de las dos.
3. Como anfitrión abrí la Votación y el Sorteo; mirá cómo se ven en la notebook y cerralos cuando terminen.
4. Al terminar, copiá de la notebook **C:\Warlords3\Herramientas\votacion.log** y **sorteo.log** a
   **F:\source\repos\actualizador-warlords\nico\** (un pendrive sirve) y anotá la hora en que abriste cada uno.
Resultado parcial (30/10/2026, usuario): la Votación se abre en la notebook unos segundos después, pero lo que hace
el anfitrión con los votos de cada color nunca se ve allá. Llegó el votacion.log de la notebook (prueba de las 01:58): la orden de abrir llega,
pero el juego de la PC anfitriona nunca manda los votos por la red. Lo medido está en
`parches\vista-aliada\PENDIENTE-mision-puentes-y-botones.md`, parte B, punto 3. Se arregla en el parche.

- [x] **71.** De noche, pozos y remolinos casi invisibles y sin lupa (28/10/2026)
Cambio (vista aliada 1.0.94.0): con Day/Night, en las vueltas de noche los pozos y remolinos ya descubiertos se ven
solo como una sombra de su forma (trampas y tumbas, igual que de día). Y de noche no hay lupa ni cuadro del botón
derecho en ruinas, pozos, remolinos y trampas. Las ciudades y los demás sitios (puertos, establos, altares) siguen
con su lupa. Ya instalado en C:\Warlords3 y publicado (29/10/2026).
1. (Hecho: instalado y publicado.)
2. En una partida con **Day/Night** y **Hidden Ruins**, con un pozo o remolino ya descubierto:
   - de día se ve como siempre y tiene lupa;
   - de noche se ve solo una sombra tenue y no hay lupa ni cuadro;
   - de noche, ni una ruina ni una trampa propia dan lupa ni cuadro (de día sí);
   - de noche, una ciudad, un puerto, un establo o un altar siguen con su lupa.
3. Decime si la sombra se ve demasiado o muy poco (se ajusta fácil).
Resultado:

- [x] **70.** IA: tanda con los pozos a la vista de todos (28/10/2026)
En la guardada de la 69 nadie veía ningún pozo, así que no se pudo medir si la IA entra en los que ve. Armé
**Tanda_hex_pozos_PV_control**: la misma partida, con los 9 pozos ya descubiertos por todos los colores.
1. Monitor de IA → **Ninguna**, marcá solo **hex_pozos_PV_control** (tiene que aparecer «(control)»),
   Partidas: **10**, **Nueva tanda**.
2. Avisame cuando termine.
Resultado: pude observar que algun heroe cayo en un pozo y dejo un item, los demas heroes que ven el item "en terreno" intentan levantarlo, pero caen en el pozo sin darse cuenta. (detectan el item, pero no el pozo, entiendo que si no han detectado a tiempo el pozo, siempre estara oculto, no asi el item)

- [x] **68.** Validator y PGS-Visor abren tu juego de C:\Warlords (27/10/2026)
Cambio: DarklordsValidator 1.0.7 y PGS-Visor 1.0.1.0 toman la carpeta del juego de donde están instalados
(HERRAMIENTAS), como el Puente. Antes abrían siempre C:\Warlords3.
1. Abrí el Actualizador: opción **7** y después opción **8**.
2. Abrí Darklords Validator desde C:\Warlords\HERRAMIENTAS y tocá abrir unidad: tiene que abrir en C:\Warlords\ARMY.
3. Abrí PGS-Visor desde la misma carpeta: la lista de bandos tiene que ser la de C:\Warlords.

- [x] **60.** IA: probar la luz roja de partida parada del Monitor (26/10/2026, después de la 47)
Cambio: en el Monitor de IA, el círculo de RAM ya no está; en su lugar hay una luz que se pone **roja** cuando la
partida está parada (pausada en el juego, esperando algo tuyo, o la tanda detenida sin terminar): titila con
fundido entre rojo oscuro y rojo vivo y suena la alarma una vez. Mientras juega queda rojo oscuro, como apagada. Se enciende a los 45 segundos sin movimiento. Va en el Monitor **1.0.18** (publicado).
1. Abrí el Monitor y apretá Actualizar; tiene que decir 1.0.18.
2. Arrancá una tanda corta (Partidas: 1). Mientras juega, la luz tiene que estar rojo oscuro, quieta, con el rótulo «En curso».
3. Pausá el juego (o dejalo esperando algo tuyo) un minuto: suena la alarma y la luz titila en rojo con «Parada».
4. Seguí la partida: en pocos segundos vuelve a rojo oscuro quieto.
5. Control: apretá Cortar; la luz titila con «Detenida», sin sonar (la cortaste vos), hasta que la retomes o empieces otra.

- [x] **75.** Votación y Sorteo en red con vista-aliada 1.0.95.0 (30/10/2026)
Arreglo: el juego que no tiene el foco (porque la Votación o el Sorteo están al frente) se pausaba entero, también
la red, y por eso la notebook nunca veía los votos ni los números. Ahora sigue mandando y recibiendo. Ya probado en
esta PC con el Sorteo al frente: el juego levantó todo lo que el Sorteo escribió.
1. En **esta PC y en la notebook**: Actualizador, opción **9**; vista-aliada tiene que quedar **1.0.95.0**.
2. Partida en red: esta PC de anfitrión, la notebook se une.
3. Como anfitrión abrí el **Sorteo** y sorteá dos o tres números: en la notebook tienen que aparecer a los pocos
   segundos, sin cerrar nada. Cerralo.
4. Abrí la **Votación** y marcá algunos votos: en la notebook tienen que verse al rato. Cerrala.
5. Si algo no se ve en la notebook, copiá de la notebook **C:\Warlords3\Herramientas\votacion.log** y **sorteo.log** a
   **F:\source\repos\actualizador-warlords\Nico\**.
Resultado (30/10/2026, usuario): todo funciona. La Votación y el Sorteo se abren casi a la vez en las dos
PC; el espectador ve todo lo que hace el anfitrión; las dos partidas se pausan en el mismo punto del reloj del turno,
con el aviso previo; el reporte de eventos muestra el resultado de la votación del turno anterior. Único pedido: el
aviso de la pausa se veía poco sobre el mapa (se arregla en la tarea 76).

- [x] **74.** Sorteo 1.1.4: ¿el juego del anfitrión levanta lo que escribe el Sorteo? (30/10/2026)
El 1.1.4 anota en el sorteo.log del anfitrión cada estado que escribe y si el juego ya se había llevado el anterior.
1. En **esta PC y en la notebook**: Actualizador, opción **9** (herramientas tiene que quedar **1.0.0.3**) y después
   la **12 (Sorteo)**: el título tiene que decir **v1.1.4** en las dos.
2. Partida en red: esta PC de anfitrión, la notebook se une.
3. Como anfitrión abrí el Sorteo, sorteá una vez, esperá unos 10 segundos y cerralo. Anotá la hora.
4. Copiá **C:\Warlords3\Herramientas\sorteo.log** de **esta PC** a
   **F:\source\repos\actualizador-warlords\Nico\anfitrion-sorteo.log**, y el de la **notebook** a
   **F:\source\repos\actualizador-warlords\Nico\sorteo.log** (reemplazá el viejo).
Resultado (30/10/2026): llegaron los .log de la notebook. Con el Sorteo y la Votación abiertos nunca
apareció un .ver allá; solo el «cerrado» final, igual que en el anfitrión. Causa encontrada y arreglada en
vista-aliada 1.0.95.0 (tarea 75).

- [x] **73.** ¿El juego se queda quieto mientras la Votación o el Sorteo están al frente? (30/10/2026)
Es para saber por qué la notebook no ve los votos (tarea 18). Se hace en **una sola PC**, sin red, en una partida
local. Tarda 5 minutos.
1. Abrí el Explorador en **C:\Warlords3\Herramientas** y poné la vista **Detalles** (columna «Fecha de
   modificación»). Dejá esa ventana a un costado, donde la veas.
2. Abrí el juego, **New Game** hasta la pantalla de preparación, y apretá el botón grande del **Sorteo** (abajo a la
   derecha). Se abre el Sorteo encima.
3. **Sin tocar el juego**, sorteá 2 o 3 números en el Sorteo. Mirá en el Explorador (F5 para refrescar) la hora de
   **sorteo.ver**. Anotá: ¿cambia a cada número sorteado, o queda quieta?
4. Ahora hacé **un clic en la ventana del juego** (que el juego quede al frente, el Sorteo sigue abierto) y esperá
   5 segundos. F5 en el Explorador: ¿cambió la hora de **sorteo.ver**? ¿Hay un **sorteo.op** que antes no se iba?
5. Cerrá el Sorteo y salí del juego.
Resultado (30/10/2026): no hizo falta, lo medí yo en esta PC. Sin el foco el juego se pausa a propósito y no
levanta el .op; con el juego al frente, sí. Arreglado en vista-aliada 1.0.95.0 (tarea 75).

- [x] **69.** IA: guardada de Hexagon con pozos, para medir cuánto cae la IA en ellos (27/10/2026)
Ninguna guardada de tanda tiene pozos: los pozos y remolinos se reparten solo al empezar una partida nueva con
**Hidden Ruins**, y las de Hexagon se armaron con esa opción apagada.
1. En **C:\Warlords3\DarklordAV.exe** (la carpeta de pruebas: tiene la 1.0.91.0, la que registra las caídas), partida nueva en **Hexagon** igual que Tanda_hex_alianzas (30 turnos, 2000 puntos, Shared
   Cities, Diplomacy, equipos 013 contra 457, el bando simple en todos los colores, un color en Humano), pero con
   **Hidden Ruins activada** y, en Viewing Options, **Discover hidden ruins as you pass**.
2. Guardala en el turno 1, sin jugar, como **Tanda_hex_pozos_control** y avisame. Yo reviso que tenga pozos.
3. Cuando te confirme: Monitor de IA → **Ninguna**, marcá solo **hex_pozos_control** (tiene que aparecer
   «(control)»), Partidas: **10**, **Nueva tanda**.
Resultado (Claude, 28/10/2026): hecha; tandas 97 a 99 sobre Tanda_hex_pozos_control (20 partidas: 13 completas,
6 colgadas, 1 cortada). 9 pozos, ninguno visible al empezar; solo 2 caídas, en pozos ocultos. Sigue la 70.

- [x] **67.** Cerrar el Monitor de IA para que lo actualice. Hecho el 27/10/2026: cerrado; Monitor 1.0.19 compilado y publicado.

- [x] **66.** Revisar las capturas en el Manual (vista aliada 1.0.90.0, 27/10/2026)
El Manual trae ahora la captura de cada programa: Puente Warlords (capítulo II, «Jugar en red»), Monitor de IA, y en
el capítulo XV DarkValidator, DarkCompare, Visor PGS, Sorteo y Votación.
1. En el Actualizador (C:\Warlords), opción **9**: instalá vista-aliada 1.0.90.0.
2. Abrí C:\Warlords\Manual-Era-de-Alianzas.pdf y mirá cada captura: que se lea y esté en su lugar.
3. Anotá lo que quieras cambiar (tamaño, otra captura, otro lugar).
Cumplida (marcada por el usuario, anotada 27/10/2026).

- [x] **62.** Probar el borrado de archivos viejos y el Manual nuevo (vista aliada 1.0.89.0, 26/10/2026)
Cambios: al arrancar, DarklordAV.exe borra los archivos de bonos que ya no van (camo.STT, nighmare.STT,
bridge.STT), así todas las PC tienen la misma lista de bonos y no hay mezcla de versiones en red. El Manual trae el
capítulo nuevo «El día y la noche» (noche, camuflaje «camouflg», monstruos) y está al día hasta esta versión.
1. ~~Cerrá el juego y avisame~~: hecho, la 1.0.89.0 está instalada en C:\Warlords3 y publicada.
2. Abrí DarklordAV.exe una vez y cerralo. En C:\Warlords3\TERRAIN\SUBTYPE ya no tienen que estar camo.STT,
   nighmare.STT ni bridge.STT; camouflg.STT sí.
3. En el editor, en los Move Bonus de la lista tiene que aparecer **camouflg** y ya no **camo**.
4. Abrí C:\Warlords3\Manual-Era-de-Alianzas.pdf, capítulo VIII «El día y la noche». Anotá lo que quieras cambiar.
Cumplida (marcada por el usuario, anotada 27/10/2026).

- [x] **59.** Probar el efecto noche de monstruos, demonios y no muertos (vista aliada 1.0.87.0, 26/10/2026)
Cambio: de noche, toda unidad cuyo tipo tenga la clase **monster**, **demon** o **undead** (en Edit Army Data, sus
Army Subtypes) gana +2 en una sola cosa, sorteada: fuerza, hits, su bono de combate (solo si tiene uno) o su
habilidad especial (solo si ya tiene una, ej. trample 1 pasa a trample 3). No hay que asignar nada en el editor.
Hay un sorteo por noche: dura toda esa noche, en todos los combates, y cambia la noche siguiente. De día, nada.
Los héroes no. Orcos, dragones y el resto, tampoco.
1. Ya está instalada en C:\Warlords3. Abrí DarklordAV.exe y una partida con **Day/Night** marcado que tenga
   demonios, no muertos o monstruos (por ejemplo Giant Wolves, Wargs, Griffons).
2. De noche, antes de atacar con esas unidades, mirá las probabilidades del combate; hacé lo mismo de día con un
   ataque parecido: de noche tienen que dar mejor para ellas.
3. Al pelear de noche, mirá la ficha de batalla: la fuerza o los hits pueden aparecer con +2 (si el sorteo cayó en
   su bono o su habilidad, no se ve en la ficha, solo en el resultado).
4. Control: orcos o dragones pelean igual de día y de noche.
Cumplida (anotada en Hecho 27/10/2026).

- [x] **65.** Arreglar la resolución en C:\Warlords con la opción 6 (27/10/2026)
El juego completo no traía la configuración de video (dxcfg.ini, SCREEN.INI, VIDEO.INI): por eso en C:\Warlords se
veía con otra resolución. Ya la trae; donde esos archivos existen no los toca, así que no cambia nada a nadie que
ya tenga su juego bien.
Ya pasé a C:\Warlords tu configuración de video, tus partidas (Saves, Netsaves), mapas de Randscen y opciones
del juego (27/10/2026). La opción 6 ya no hace falta.
1. Abrí el juego desde el Escritorio: tiene que verse igual que el de C:\Warlords3 y tener tus partidas.
Resultado (27/10/2026): cumplida. Los archivos propios ya estaban pasados a C:\Warlords.

- [x] **64.** Instalar el juego para jugar en red en C:\Warlords, con el Actualizador (26/10/2026)
Desde ahora C:\Warlords3 es solo para pruebas (ahí instalo yo cada versión antes de publicarla). Para jugar en red
usás C:\Warlords, actualizado con el Actualizador como el resto del clan. En esta PC el Actualizador ya apunta ahí:
lo dice arriba del menú («juego en C:\Warlords»). A los demás jugadores no les cambia nada.
1. Bajá y abrí el Actualizador **1.0.14.0** (bajalo de GitHub, release «Ejecutable», como siempre).
   Arriba tiene que decir «v1.0.14.0 · juego en C:\Warlords».
2. Opción **6** (juego completo): instala todo en C:\Warlords.
3. Opción **9** (parches): instalá vista-aliada (1.0.89.0) y herramientas.
4. Opción **15** (accesos directos): rehace los del Escritorio apuntando a C:\Warlords. Para jugar, usá esos.
5. Abrí DarklordAV.exe desde el Escritorio y comprobá que arranca.
5b. Opción **13** (Jugar en red): instala el Puente 1.1.9.0 en C:\Warlords\HERRAMIENTAS. Abrilo: en la lista de
   ejecutables del juego tiene que aparecer DarklordAV.exe, y al entrar a una partida tiene que abrir el de C:\Warlords
   (el Puente ahora toma la carpeta del juego de donde está instalado).
6. Tus bandos, escenarios y partidas guardadas siguen en C:\Warlords3: si querés alguno para jugar, avisame.
Resultado (27/10/2026): cumplida. Juego completo, parches y Puente instalados en C:\Warlords.

- [x] **63.** Preparar capturas de las herramientas para el Manual (26/10/2026)
El Manual va a llevar una captura de la ventana de cada una: DarkCompare (comparador), DarkValidator, Monitor de IA,
Votación y Sorteo.
1. Sacá una captura de cada ventana (tecla Win+Shift+S, o Impr Pant) con algo cargado, no vacía.
2. Guardalas en F:\source\repos\actualizador-warlords\manual\img\capturas, con el nombre del programa
   (comparador.png, validator.png, monitor-ia.png, votacion.png, sorteo.png).
3. Avisame: las pongo en su capítulo y armo el Manual de nuevo.
Resultado (27/10/2026): cumplida, con siete capturas (sumaste Puente Warlords y Visor PGS). Ya están en el Manual (vista aliada 1.0.90.0): ver la 66.

- [x] **61.** Renombrar el bono de camuflaje en tus escenarios: «camo» pasa a ser «camouflg» (vista aliada 1.0.88.0, 26/10/2026)
Cambio: el bono se llama ahora **camouflg** (8 letras, el máximo del editor), más claro en el editor y en el comparador.
Un escenario que tenga «camo» en un Move Bonus deja de camuflar hasta que lo cambies.
1. Cerrá el juego y avisame: lo instalo en C:\Warlords3 y lo publico (ahora no se puede: el juego abierto bloquea DarklordAV.exe).
2. En el editor, abrí cada escenario que use el camuflaje, y en los Move Bonus donde decía **camo** elegí **camouflg**. Guardá.
3. De noche, el grupo con ese bono tiene que verse verdoso como antes.
4. Si en la lista de bonos sigue apareciendo **camo**, es el archivo viejo: podés borrar `C:\Warlords3\TERRAIN\SUBTYPE\camo.STT`.
Resultado (26/10/2026): marcada cumplida; la instalación, la publicación y el borrado del archivo viejo siguen en la 62.

- [x] **58.** Probar camo en ciudades y Día/Noche con Hidden Map (vista aliada 1.0.85.0, 26/10/2026)
Cambios: dentro de una ciudad el grupo «camo» se ve normal (la ciudad está iluminada). Y Día/Noche ya se puede
marcar junto con Hidden Map: de noche, lo no explorado sigue negro y lo explorado se oscurece con los halos; una
ciudad, ruina o sitio que todavía no exploraste no alumbra (para que su halo no delate dónde está).
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe con el escenario de la tarea 51.
2. En Viewing Options marcá **Hidden Map** y **Day/Night**: las dos tienen que quedar marcadas.
3. De noche: lo no explorado negro, lo explorado oscuro con halos. Mirá el borde de lo explorado cerca de una ciudad
   enemiga que no viste: no tiene que aparecer un halo saliendo del negro.
4. Meté el grupo «camo» en una ciudad de noche: se tiene que ver normal; al salir, verdoso otra vez.
5. Mirá también el minimapa y el Army Report de noche.
Resultado (26/10/2026): se ve perfecto en modo Hidden Map.

- [x] **57.** Probar el camuflaje más verde (vista aliada 1.0.84.0, 26/10/2026)
Cambio: la paleta del juego no tiene grises verdosos, así que la figura camuflada mezcla tonos de verde oscuro con
los grises y oliva de antes; de conjunto tiene que leerse como gris verdoso, con la misma opacidad.
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe con el escenario de la tarea 51 y **Day/Night** marcado.
2. De noche, mirá el grupo «camo»: tiene que verse más verdoso que en la 56, sin quedar moteado feo.
3. Si queda moteado o muy verde, anotalo: se vuelve a la 1.0.83.0 o se ajusta la mezcla.
Resultado (26/10/2026): quedó perfecto.

- [x] **56.** Probar el camuflaje verdoso, corregido (vista aliada 1.0.83.0, 26/10/2026)
Cambio: se corrigió por qué salía la mancha blanca. Ahora el grupo camuflado de noche tiene que verse en grises y
verde oliva apagados, del tono del pasto (globito incluido).
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe con el escenario de la tarea 51 y **Day/Night** marcado.
2. De noche, mirá el grupo «camo» desde otro jugador: tiene que costar distinguirlo del pasto o del bosque.
3. Anotá si lo querés más o menos visible.
Resultado (26/10/2026): se ve bien, también la opacidad; pidió el gris más verdoso → tarea 57.

- [x] **55.** Probar el camuflaje verdoso (vista aliada 1.0.82.0, 26/10/2026)
Cambio: el grupo camuflado de noche ya no es gris oscuro: es un gris verdoso del tono del pasto, con poco contraste,
para que se confunda con el terreno (globito incluido).
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe con el escenario de la tarea 51 y **Day/Night** marcado.
2. De noche, mirá el grupo «camo» desde otro jugador: tiene que costar distinguirlo del pasto o del bosque.
3. Anotá si lo querés más o menos visible.
Resultado (26/10/2026): mancha blanca, como en la 53 (error de escala de la paleta) → tarea 56.

- [x] **54.** Probar el camuflaje en gris apagado (vista aliada 1.0.81.0, 26/10/2026)
Cambio: el grupo camuflado de noche ya no es una mancha blanca: se ve la figura de siempre, con su detalle, pero
toda en gris oscuro (globito incluido).
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe con el escenario de la tarea 51 y **Day/Night** marcado.
2. De noche, el grupo solo de unidades «camo» tiene que verse como una figura gris apagada, no blanca ni invisible.
3. Anotá si lo querés más claro o más oscuro.
4. Army Report de noche: el grupo camuflado de otro jugador no tiene que figurar; de día, sí.
Resultado (26/10/2026): se veía gris, pero muy oscuro y fácil de ver → gris verdoso del tono del pasto, tarea 55.

- [x] **53.** Probar la silueta clara del camuflaje (vista aliada 1.0.80.0, 26/10/2026)
Cambio: el grupo camuflado de noche ya no queda casi invisible: se ve como una silueta gris clara sobre el terreno
(globito incluido, en gris).
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe con el escenario de la tarea 51 y **Day/Night** marcado.
2. De noche, el grupo solo de unidades «camo» tiene que distinguirse, pero apagado y gris.
3. Anotá si lo querés más visible o menos.
4. Army Report de noche: el grupo camuflado de otro jugador no tiene que figurar; de día, sí.
Resultado (26/10/2026): se veía mal, una mancha blanca → figura en gris apagado, tarea 54.

- [x] **52.** Probar el camuflaje al 30 % y el Army Report (vista aliada 1.0.79.0, 26/10/2026)
Cambio: de noche, el grupo camuflado quieto ya no se dibuja gris encima del terreno: queda una silueta al 30 %
(se ve el terreno a través), y eso incluye el globito del color del equipo, su barra y sus iconos. Y el **Army
Report** de noche ya no muestra dónde están los grupos camuflados de los demás (los tuyos y los de un aliado con
vista aliada, sí).
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe con el escenario de la tarea 51 y **Day/Night** marcado.
2. De noche: el grupo solo de unidades «camo» tiene que verse tenue, globito incluido (no del color del equipo).
3. Abrí el **Army Report** siendo otro jugador (o con un enemigo «camo»): de noche ese grupo no tiene que figurar
   en el mapita; de día, sí.
Resultado (26/10/2026): el globito ya se ve gris, pero los grupos «camo» de noche no se veían → silueta más clara, tarea 53.

- [x] **50.** Probar la luz de tus ejércitos al 50 % (vista aliada 1.0.78.0, 26/10/2026)
Cambio: de noche, la casilla de tus ejércitos y la de al lado ya no quedan casi a pleno brillo: quedan al 45 %
(el escalón más cercano al 50 % sin pasarlo) y desde ahí se oscurecen hacia afuera. Ciudades, ruinas, sitios y
puentes siguen como estaban.
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe y una partida con **Day/Night** marcado.
2. En una vuelta par (de noche), mirá un ejército tuyo lejos de las ciudades: su halo tiene que verse más apagado
   que el de una ciudad. En el minimapa, igual.
3. Anotá si te gusta así o si lo querés más claro (55 %) o más oscuro.
Resultado (26/10/2026): se ve bien, queda mejor así.

- [x] **51.** Probar el bono «camo» (camuflaje) (vista aliada 1.0.78.0, 26/10/2026)
Cambio: bono de movimiento nuevo **camo** (el editor muestra el nombre del archivo, y esos nombres no pueden pasar de
8 letras: por eso «camo» y no «camouflage»). De noche, un grupo cuyas unidades tienen **todas** ese bono se dibuja
con un filtro gris al 60 %, banderín del color del equipo incluido. De día, nada. Un grupo con un héroe, o con alguna
unidad sin el bono, se ve normal. El grupo mientras camina (la animación del paso) se ve normal; queda gris al pararse.
1. Abrí war3ed_av.exe (el editor; si estaba abierto, cerralo y volvelo a abrir) y en **Edit Army Data** poné
   **camo** en uno de los Move Bonus de un tipo de unidad (por ejemplo los Scouts). Guardá el escenario.
2. Abrí ese escenario con DarklordAV.exe y **Day/Night** marcado. Armá un grupo solo de esas unidades.
3. De noche: ese grupo tiene que verse gris (también el banderín de color). Uno mezclado con otras unidades, no.
4. De día: tiene que verse normal.
5. Mirá también un grupo enemigo con ese bono, si lo hay: tiene que verse gris igual.
Resultado (26/10/2026): el bono funciona; el globito seguía del color del equipo y se pidió bajar a 30 % → tarea 52.

- [x] **49.** Probar la noche de 8 escalones y el minimapa de noche (vista aliada 1.0.77.0, 26/10/2026)
Cambios: la oscuridad tiene 8 escalones y el más oscuro queda al 20 % del brillo; de noche el minimapa también se
oscurece, con los mismos halos que el mapa.
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe y una partida con **Day/Night** marcado.
2. En una vuelta par (de noche): el minimapa tiene que verse oscuro, con zonas claras alrededor de tus ciudades,
   ejércitos, ruinas, sitios y puentes, en los mismos lugares que en el mapa grande.
3. Pasá a la vuelta siguiente (de día): el minimapa tiene que volver a verse claro. Anotá si en algún cambio de
   vuelta quedó con el brillo de la vuelta anterior.
4. Mové un ejército de noche: en el minimapa la zona clara tiene que seguirlo.
**Resultado (26/10/2026):** bien, «es lo que quería lograr»; el minimapa reproduce bien el efecto.

- [x] **48.** Probar la noche nueva (vista aliada 1.0.76.0, 26/10/2026)
Cambios: la zona iluminada ahora también se oscurece un poco, la oscuridad tiene 6 escalones (antes 4) y el halo de
tus ejércitos, ruinas, sitios y puentes es redondo; el de las ciudades sigue cuadrado.
1. Ya está instalada en C:\Warlords3: abrí DarklordAV.exe y una partida con **Day/Night** marcado.
2. En una vuelta par (de noche), mirá cerca de tus ejércitos y de una ruina o sitio: el halo tiene que verse redondo.
3. Contame si la luz quedó bien de oscura y si el degradé se ve suave o con escalones marcados.
Resultado (26/10/2026): pediste 8 escalones con el más oscuro al 20 % y la noche también en el minimapa; va en la 49.

- [x] **46.** Probar el día y la noche (vista aliada 1.0.75.0, 26/10/2026)
Actualizá con la opción de vista aliada y empezá una partida nueva con DarklordAV.exe. En Customize Options marcá
**Day/Night** (columna derecha de Viewing Options): Hidden Map se tiene que desmarcar sola. Ya en el juego:
  1. En el menú, View Game Options tiene que mostrar «Day/Night» marcado.
  2. Una vuelta sí y otra no, el mapa se oscurece, con un halo de luz alrededor de tus ciudades, ruinas, sitios,
     puentes y tus ejércitos; los ejércitos enemigos no dan luz. Anotá si la primera vuelta es de día o de noche.
  3. Al mover un ejército de noche, la luz lo sigue sin dejar manchas ni cuadros mal pintados.
  4. Contame si la noche se ve demasiado oscura, demasiado clara o bien.
**Resultado (26/10/2026):** anda bien. Vueltas impares de día, pares de noche; sin cuadros mal pintados al mover; el
reporte se ve bien. Pediste la luz más oscura, uno o dos escalones más y halo redondo en ejércitos y sitios: tarea 48.

- [x] **45.** Probar el daño nuevo de las trampas (vista aliada 1.0.72.0, 26/10/2026)
Ahora una trampa en tierra mata entre el 40 y el 80 % de la pila (al azar, distinto en cada explosión) y paraliza al
resto: el grupo se frena, no se mueve más ese turno y, si su movimiento es 9 o más, tiene 5 pasos menos hasta su turno
siguiente. La mina submarina sigue hundiendo todo.
1. Cuando termine la tanda de la tarea 44 (con el juego cerrado), avisame: instalo y publico la 1.0.73.0 (trae también el arreglo del paso 5).
2. Después, en una partida: poné una trampa y hacé pasar por ella una pila de 6 o más unidades que no vuelen.
   Tienen que morir algunas (entre la mitad, más o menos, y casi todas) y las que quedan, quedarse quietas.
3. Al turno siguiente las sobrevivientes tienen que moverse normal.
4. Que pase por la misma trampa otra pila: la segunda explosión tiene que dar otra proporción.
5. La 1.0.73.0 trae además el arreglo de los recortes del mapa al derribar un puente (lo que anotaste en la 40):
   derribá un puente (con misión o sin ella) y reconstruí otro. Al cerrarse los carteles, el mapa tiene que verse
   entero, sin pedazos recortados ni pixelados, sin tener que pasar el mouse.
Resultado: el daño nuevo por porcentajes aleatorios funciona bien. 

- [x] **37.** Comprobar que la opción 9 instala el Manual (24/10/2026)
Desde vista-aliada 1.0.69.0 (ya publicada), el parche instala también el Manual de uso.
1. En otra PC del clan, abrí el Actualizador y elegí la opción **9** → vista-aliada.
2. Fijate que aparezca `C:\Warlords3\Manual-Era-de-Alianzas.pdf` y que abra.
Resultado: el manual queda instalado con el actualizador. 

- [x] **47.** IA: tanda de control con blanco y negro intercambiados de lugar (26/10/2026)
Lo mismo que la 44, ahora con el blanco (el que sigue ganando) en el lugar del negro, que es su espejo.
1. Abrí el Monitor de IA: tiene que decir **1.0.17** (si dice otra, apretá Actualizar).
2. **Ninguna**, marcá solo **hex_espejo_control** (tiene que aparecer «(control)»), Partidas: **6**,
   **Tandas automatizadas** con serie de **5**, **Nueva tanda** (30 partidas, unas 9 horas).
3. Avisame cuando termine: la analizo.
Hecha (27/10/2026, tandas 89 a 95, 41 partidas completas; una cortada): el blanco, desde el lugar del negro, ganó 2
de 41 (antes 8 de 25) y quedó eliminado 4 veces; el negro, desde el del blanco, 0. Ganó el amarillo: 34 de 41.

- [x] **44.** IA: tanda de control con amarillo y verde intercambiados de lugar (25/10/2026)
Sirve para saber si el amarillo gana por el lugar donde arranca o por jugar segundo: en esta guardada el amarillo sale
desde el lugar del verde y el verde desde el del amarillo.
1. Abrí el Monitor de IA: tiene que decir **1.0.17** (si dice otra, apretá Actualizar).
2. **Ninguna**, marcá solo **hex_lugar_control** (tiene que aparecer «(control)»), Partidas: **6**,
   **Tandas automatizadas** con serie de **5**, **Nueva tanda** (30 partidas, unas 9 horas).
3. Avisame cuando termine: la analizo.
Hecha (26/10/2026, tandas 82 a 86, 30 partidas sin cuelgues): el amarillo, desde el lugar del verde, ganó 1 de 30
(antes 17 de 25). Su ventaja era el lugar, no jugar segundo.

- [x] **40.** Probar la misión de destruir un puente y las trampas de 2 explosiones (vista aliada 1.0.70.0, 24/10/2026) — hecha el 26/10/2026
Todos actualizan antes con el Actualizador (opción del parche vista aliada).
1. Con un héroe, aceptá una misión «destruir el puente…». Pasá 2 o 3 turnos: la línea naranja del minimapa
   tiene que apuntar siempre al mismo puente, y al llegar el puente tiene que estar ahí.
2. Elegir la opción de destruir el puente no tiene que colgar el juego.
3. Poné una trampa (de tierra y una submarina): explota 2 veces y a la tercera ya no está.
Resultado: las trampas ahora explotan 2 veces. La mision se completa bien, aunque con algunos problemas de renderizado menores (parte del escenario queda con imagenes recortadas o pixeladas), que se corrigen de inmediato con el sobrevuelo del mouse en dicho sector.
(Claude, 26/10) Causa: al derribar o reconstruir un puente, el parche dibujaba el mapa con el diálogo todavía
abierto; al cerrarse, el diálogo reponía la imagen vieja y el juego no la repintaba. Corregido en 1.0.73.0 (tarea 45, paso 5).

- [x] **43.** IA: tanda de control en Hexagon, el mismo perfil en los seis colores (Monitor de IA 1.0.17, 25/10/2026)
Sirve para saber si blanco y amarillo ganan por el lugar o por los perfiles (en la tanda 41 ganaron 29 de 30).
1. Abrí el Monitor de IA: tiene que decir **1.0.17** (si dice otra, apretá Actualizar). Vista aliada sigue en 1.0.71.0.
2. **Ninguna**, marcá solo **hex_control** (tiene que aparecer «(control)»), Partidas: **6**,
   **Tandas automatizadas** con serie de **5**, **Nueva tanda** (30 partidas, unas 9 horas).
3. La bitácora tiene que mostrar en cada partida «perfiles blanco <- blanco, amarillo <- amarillo, …» (cada uno conserva
   el suyo, que es el mismo en todos) y ninguna «victoria aliada».
4. Avisame cuando termine: la analizo.
Hecha (25/10/2026, tandas 76 a 80): 25 partidas válidas y 5 colgadas. Con el mismo perfil en los seis colores
ganaron otra vez solo blanco (8) y amarillo (17): el desnivel es del lugar o del orden de turno, no de los perfiles.

- [x] **39.** Pedirle a Microsoft que deje de marcar el Actualizador como virus (24/10/2026)
En la PC de tu amigo, Edge/Defender bloquea `Actualizador-v.1.0.13.0.exe.zip` con «Se ha detectado un virus».
Es un falso positivo: lo corrige Microsoft, no nosotros. El envío lo hacés vos desde tu PC; tu amigo solo
tiene que hacer el paso 6.
1. ~~Nombre de la amenaza~~ — hecho: **`Trojan:Script/Wacatac.H!ml`** (24/10/2026 15:50, en la PC de tu amigo).
   El «!ml» quiere decir que lo marcó la inteligencia artificial de Defender por parecido, no una firma de virus real.
2. En tu PC, tomá el **zip** (es lo que Defender bloqueó):
   `F:\source\repos\actualizador-warlords\Actualizador-v.1.0.13.0.exe.zip`.
3. Entrá a https://www.microsoft.com/wdsi/filesubmission, iniciá sesión con tu cuenta Microsoft y elegí
   **Software developer**.
4. Producto: **Microsoft Defender Antivirus**. Subí el zip. Marcá **Incorrectly detected as malware**.
   En «Detection name» poné `Trojan:Script/Wacatac.H!ml`. En comentarios: «Updater for the game Warlords III, made by
   me, downloads game files from GitHub. False positive.»
5. Anotá abajo el número de envío. Microsoft responde por mail, en general en 1 a 3 días.
6. Cuando digan que está corregido, avisale a tu amigo que en su PC vaya a Seguridad de Windows → Actualizaciones de protección
   → **Buscar actualizaciones**, y vuelva a bajar el zip.
Resultado (25/10/2026): enviado, https://www.microsoft.com/en-us/wdsi/submission/aeea912a-5a2b-4e54-b98c-41a4bcb2c446
  Microsoft ya no detecta nada ni en el zip ni en el .exe (en la nube y con definiciones 1.461.190.0). El
  veredicto final de su analista figura «Pending». Paso 6 (tu amigo actualiza Defender y vuelve a bajar el zip):
  sin confirmar.

- [x] **41.** IA: tanda de personalidades en Hexagon (Monitor de IA 1.0.16 y vista aliada 1.0.71.0, 25/10/2026)
Cada partida cambia los perfiles de color, así cada perfil juega una vez desde cada lugar del mapa.
1. Abrí el Actualizador y aplicá **vista aliada 1.0.71.0**. Después abrí el Monitor de IA: tiene que decir **1.0.16** (si dice otra, apretá Actualizar).
   Antes, el juego aliaba a todas las computadoras contra el humano, y en una tanda no hay humanos: por eso terminaba en el turno 3 con «victoria aliada». Las tandas de prueba quedaron anuladas.
2. **Ninguna**, marcá solo **hex_perfiles_SR** (tiene que aparecer «(perfiles)»), Partidas: **6**,
   **Tandas automatizadas** con serie de **5**, **Nueva tanda** (30 partidas, unas 9 horas).
3. Las partidas no tienen que terminar con «victoria aliada». La bitácora tiene que mostrar en cada partida «perfiles blanco <- …»: es el perfil que recibe cada color.
4. Avisame cuando termine: la analizo.
Resultado: (usuario, 25/10) terminó la serie: tandas 65 a 69, 30 partidas, todas válidas (30 turnos). (Claude, 25/10) gana el perfil negro
(Artificer + Devout): 10 de 30, con más PV y una sola eliminación; los demás, entre 2 y 6. La ubicación pesa más que el
perfil: 29 de 30 las ganó quien arrancó en el lugar amarillo o el blanco, y ahí negro ganó las 10 veces que le tocó.
Detalle en ia\PENDIENTE-entrenamiento-ia.md.

- [x] **38.** IA: guardada de Hexagon con personalidades distintas (24/10/2026)
Resultado: (usuario, 25/10) guardada como **Tanda_hex_perfiles** (el nombre largo no entraba): 6 colores, mismo bando,
sin alianzas, sin ruinas ni misiones, **5 puntos** (con 4 no se podían igualar). Blanco: Very Strong + Very Fast;
amarillo: Immovable; rojo: Legendary + Famous + Merchant + Rich; verde: Renowned + Engineer + Heroic + Rich; azul:
Disciplined + Strong; negro: Artificer + Devout. (Claude, 25/10) los 6 perfiles están en la guardada tal cual;
ya sé dónde se escriben (detalle en ia\PENDIENTE-entrenamiento-ia.md).

- [x] **35.** Actualizador 1.0.13.0: la opción 9 exige haber corrido la 6 (23/10/2026)
Desde esta versión, la opción 9 (PARCHES) no deja instalar nada en una PC donde no se corrió antes la opción 6
(ACTUALIZAR TODO EL JUEGO) con esta versión o una posterior; vale también para tu PC. Y avisa, arriba de la lista de
parches, si hay un juego completo más nuevo que el instalado o si el juego completo publicado quedó atrás de algún parche.
1. Abrí el Actualizador (se actualiza solo a la 1.0.13.0) y elegí **9**: tiene que decir que antes hay que instalar
   el juego completo (opción 6).
2. Elegí **6** y confirmá. No pisa tus bandos, escenarios propios, partidas ni opciones. Al final probablemente avise
   «vuelve a instalarlo con la opción 9» para vista-aliada.
3. Elegí **9**: ahora tiene que mostrar la lista, sin avisos arriba. Si vista-aliada figura como no instalado, instalalo.
4. Abrí DarklordAV.exe y comprobá que el juego anda como siempre.
Anotá acá lo que viste en cada paso.
Resultado (usuario, 24/10/2026): todo funciona como lo esperado. 

- [x] **34.** Mapas al azar: que salgan también los ítems personalizados (23/10/2026)
Desde vista-aliada 1.0.68.0 (ya instalada en C:\Warlords3), cada mapa al azar sortea sus 32 ítems entre todos los de `ITEMS` (originales y
personalizados), en vez de usar las cuatro listas fijas de `RANDOM\Grass`. El juego no admite más de 40 ítems
por partida (32 + 8 especiales), así que en cada partida sale una parte distinta. Los 8 especiales no cambian:
solo los traen `Item1.dat` y `Item2.dat` (los últimos 8 nombres de cada uno). Los ítems de vuelo (con «fly» en el
nombre: bootfly, potfly, FlyShoot) no entran al sorteo, y los quitaste también de las cuatro listas.
1. Abrí el juego con **DarklordAV.exe** y empezá dos partidas con mapa al azar (Random), una después de la otra.
2. En cada una, abrí la lista de ítems del juego (o explorá ruinas): tienen que aparecer ítems personalizados, y
   la lista de una partida tiene que ser distinta de la de la otra. No tiene que aparecer ningún ítem de vuelo.
3. Si el juego se cierra o da error al crear el mapa, anotalo acá.
Resultado (usuario, 24/10/2026): ahora salen loso items personalizados

- [x] **32.** Monitor de IA: barra deslizante horizontal en la bitácora (23/10/2026)
0. Ya está: Monitor 1.0.13 compilado en `ia\Monitor-IA.exe` y publicado (23/10/2026).
1. Abrí el Monitor de IA: el título tiene que decir «Monitor 1.0.13». Achicá la ventana a lo ancho.
2. Debajo del texto de la bitácora tiene que haber una barra horizontal: arrastrala y tienen que verse las líneas
   largas completas, sin ensanchar la ventana.
Resultado (usuario, 24/10/2026): ya aparece la barra

- [x] **4.** IA: rating de posiciones, un grupo de tandas por mapa (16/10/2026) — postergada por vos
Reemplaza a la "etapa 2 en Scarpart": Scarpart ya está medido (32 partidas). Para cada mapa que falta:
1. Armá la partida guardada como la vez anterior: los 8 bandos en Computadora, sin alianzas, **el mismo .PGS en
   todos los colores**, 30 turnos. Pasá un bando a Humano y guardala como **Tanda_<mapa>** (por ejemplo
   Tanda_Hexagon). Si el mapa tiene menos de 8 lugares, también sirve.
2. En el Monitor de IA (antes «Banco de pruebas»), **Guardadas**: marcá solo esa partida. Partidas: **30**. **Nueva tanda**.
   (30 partidas por mapa alcanzan, como en Scarpart; pueden ser también 5 tandas de 6.)
3. Anotá abajo qué mapa quedó hecho, y dónde arranca cada color (cuadrantes I a IX, como en Scarpart): con eso
   completo la columna "Posición de arranque" del cuadro.
4. El PDF para la página del Clan: en el Monitor de IA, **Exportar PDF de un mapa…**,
   elegí el mapa y dónde guardarlo. El de Scarpart ya se puede sacar.
Resultado (usuario, 24/10/2026): el pdf exportado se ve bien.

- [x] **33.** IA: repetir la serie sin ruinas para confirmar (23/10/2026)
La serie de la tarea 30 dio por primera vez ventaja a la IA de prueba, pero puede ser azar. Otra serie igual lo decide.
1. Abrí el Monitor de IA (1.0.13): **Ninguna**, marcá solo **hex_alianzas_SR**, Partidas: **10**, **Tandas
   automatizadas** con serie de **6**, **Nueva tanda**. La bitácora tiene que decir «Bandos: hex_alianzas_SR común»
   y «equipos 013|457». Son unas 18 horas; si se corta, **Retomar** con las que falten.
2. Avisame cuando termine.
Resultado: (Claude, 24/10) corrió con 6 partidas por tanda (tandas 47 a 52, 36 válidas, parche 1.0.68.0). Esta vez la IA de prueba pierde 11 a 24 (-6,3 ± 4,8 PV por equipo): la ventaja de la 30 fue azar. Juntando las dos series sin ruinas: +2,0 ± 3,0, sin ventaja. Detalle en ia\PENDIENTE-entrenamiento-ia.md.

- [x] **31.** Lupa y botón derecho sobre pozos, remolinos y trampas (22/10/2026)
Ahora funcionan como ruinas y sitios: al pasar el mouse por un pozo, remolino o trampa **que ya ves en el mapa**, el
cursor se vuelve lupa, y con el **botón derecho** se abre un cuadro con el nombre y el tipo; en la trampa, además,
cuántas explosiones le quedan («Explosions left: 2 of 3») o que está gastada. Lo que no descubriste no muestra lupa.
0. Ya está: vista-aliada 1.0.65.0 quedó instalada en C:\Warlords3 (22/10/2026).
1. En una partida contra la computadora, sin ningún ejército elegido, pasá el mouse por un pozo que ya hayas
   descubierto: el cursor tiene que ser la lupa. Botón derecho: cuadro con el nombre (por ejemplo «The Well of
   Souls») y el texto del pozo.
2. Lo mismo con un remolino (la lupa tiene que salir en cualquiera de sus 9 casillas) y con una trampa tuya: el
   número de explosiones que le quedan.
3. Control: en una casilla vacía, en una ruina y en una ciudad, todo tiene que seguir como antes.
Resultado: (23/10) marcada cumplida por vos.

- [x] **22.** Órdenes por chat a un aliado de la computadora (19/10/2026)
Ya se le pueden dar órdenes a un aliado de la computadora escribiendo en la barra de chat de la partida. Solo lo ve
ese aliado: los enemigos no se enteran.
**Desde vista-aliada 1.0.66.0** (ya instalada en C:\Warlords3, 23/10/2026) la orden puede empezar con **punto** en
vez de «#»: `.3 ataca ...` (el punto se escribe sin AltGr). El «#» sigue valiendo.
**Antes:** el actualizador (opción 9) tiene que ofrecer vista-aliada **1.0.41.0** o posterior, en todas las PC.
**(Claude, 22/10) Esperando:** nunca la publiqué; lo publicado sigue siendo la 1.0.39.0. Y no conviene publicar la de
hoy: trae los pozos, que todavía no están sincronizados en red. Te aviso acá cuando haya una versión publicada.
1. Partida en red (o solo en tu PC) con al menos un bando de la computadora aliado tuyo y Diplomacy activada.
2. Mirá qué número tiene ese bando (1 a 8, en el orden de los colores de la partida). Supongamos que es el 3.
3. En la barra de chat escribí, de a uno:
   - `.3 ataca NOMBRE-DE-CIUDAD` (el nombre tal cual aparece en el mapa, por ejemplo una ciudad enemiga cercana);
   - `.3 ataca a 5` (el número del bando enemigo; también vale su nombre);
   - `.3 mandame refuerzos`.
   Después de cada una tiene que aparecer en el chat, con el color del aliado, «Ok, ataco ...» o «Ok, te mando
   refuerzos».
4. Escribí `.3 hola`: tiene que contestar con la lista de órdenes. A un bando de la computadora que no es tu aliado
   tiene que contestar «No somos aliados».
5. En los dos turnos siguientes del aliado, fijate si sus pilas cercanas (las que llegan en 2 turnos) van a esa
   ciudad o vienen a tu ciudad más cercana. Si en red jugaba otro humano, preguntale si vio algo de las órdenes
   (no tendría que haber visto nada).
Resultado: funciona bien, pero los mensajes "pedeterminados" deben incluir otras ordenes: "dame oro" "razea x" (ciudad, puente)
(Claude, 23/10) Anotado como pedido: sumar a las órdenes «dame oro» y «razeá X» (ciudad o puente).

- [x] **30.** IA: serie en Hexagon con bandos idénticos y sin ruinas (22/10/2026)
Igual que la 25, pero sobre la guardada sin ruinas (las 47 exploradas, vacías y sin guardián).
1. Abrí el Monitor de IA: **Ninguna**, marcá solo **hex_alianzas_SR**, Partidas: **10**, **Tandas automatizadas**
   con serie de **6**, **Nueva tanda**. La bitácora tiene que decir «Bandos: hex_alianzas_SR común» y «equipos 013|457».
2. Avisame cuando termine: la analizo contra las tandas 35 a 40 (mismo armado, con ruinas).
Resultado: (Claude, 23/10) corrió completa (tandas 41 a 46, 58 válidas). Sin ruinas el mapa queda parejo (013 gana 28 de 58). La IA de prueba gana 35 a 23 (+7,1 ± 3,7 PV por equipo): a favor, pero todavía no es concluyente. Detalle en ia\PENDIENTE-entrenamiento-ia.md.

- [x] **28.** Revisar el Monitor de IA 1.0.12 (22/10/2026)
Abrí `ia\Monitor-IA.exe` (ya está compilado). El título tiene que decir «Monitor 1.0.12». Fijate que tenga:
a) el botón de configuración nuevo, a la derecha de los semáforos, que cambia de imagen al pasar el mouse y al
apretarlo; b) la barra verde «Serie» arriba de las de Tanda y Partida; c) el interruptor «modo sleep» un poco
más grande. Si falta algo, decime cuál.

- [x] **26.** Construir una trampa en el juego (21/10/2026)
Un grupo con una unidad que tenga el bono **Trap** puede construir una trampa oculta donde está parado, al costo de
fundar una ciudad. Desde la 1.0.60.0 la trampa es una **mina** (bola de hierro con puntas), se puede construir
**en cualquier lugar**: tierra, camino, puente, ciudad, ruina, sitio y **agua** (con la unidad embarcada). En el agua
es una **mina submarina** (azul) que al explotar **no deja rastro**. La de tierra **explota tres veces** (mata a quien entre, también a vos). Después de cada
explosión se ve un **agujero con humo** hasta el turno siguiente de quien cayó; si le quedan explosiones, después
vuelve la mina. Después de la tercera, el agujero con humo queda **para todos** hasta el final. Vos y tus aliados
con vista aliada la ven siempre; los demás, solo después de descubrirla o de caer en ella. La computadora todavía no
las construye. **Solo en esta PC, no en red.**
0. Ya está: vista-aliada 1.0.60.0 quedó instalada en C:\Warlords3 (22/10/2026).
1. Abrí el editor **war3ed_av.exe** (en C:\Warlords3) y a una unidad barata de tu bando (no un héroe) ponele **Trap**
   como **Combat Bonus**. Guardá el bando. (Tus pikemen, lightinf, half_bra, FU_halfe y Zappers ya lo tienen ahí.)
2. Empezá una partida nueva **contra la computadora** con ese bando, y comprá o juntá esa unidad.
3. Llevá un grupo con esa unidad a una casilla de tierra y abrí el menú de órdenes del grupo: al final tiene que estar
   **«Build Trap»** encendido. También en un camino, un puente, una ciudad, una ruina y embarcado en el agua. Solo se
   apaga donde ya hay una trampa, un pozo o un remolino.
4. Elegilo: sale la ventana de reconstruir con «Building a trap» y el costo de una ciudad. Si no te alcanza el oro, el
   OK queda apagado. Con oro, dale OK: tiene que descontarse el oro y aparecer la **mina** en esa casilla.
5. Sacá el grupo y volvé a entrar con otro ejército barato tuyo: tiene que morir y verse **el agujero con humo**.
   Terminá el turno: al volver a tu turno tiene que verse **otra vez la mina**. Repetilo: el segundo y el tercero
   también mueren; después del **tercero queda el agujero con humo para siempre**, y lo ve también el otro jugador
   (si hay uno humano), y un cuarto ejército pasa sin morir. Probá lo mismo con una trampa **sobre un puente**.
   En el **agua**: construila embarcado, alejate y entrá con otro barco tuyo: se hunde todo el barco, la mina
   submarina **no deja humo ni agujero**, y al turno siguiente se vuelve a ver; después de la tercera desaparece. Con el sonido del juego encendido tiene que oírse **la explosión (Burst) junto con el grito**
   de muerte de héroe. El aviso tiene que nombrar la trampa con la **ciudad más cercana y un número**, por ejemplo
   «Your army fell into the trap Afland01!»; una segunda trampa junto a la misma ciudad, «…Afland02!». En esa casilla
   ya no se puede construir otra, ni después de gastada.
6. Guardá con la mina explotada una o dos veces (con el humo a la vista y también después), salí y volvé a cargar: tiene que seguir, con los usos que le quedaban.
7. Anotá abajo qué viste (en especial si el renglón «Build Trap» queda mal ubicado o tapa algo del menú, y si la
   explosión y el grito suenan bien juntos o preferís el grito un poco después).
Resultado: todo funciona perfecto!

- [x] **24.** Pozos, remolinos y trampas: verlos y caer en el juego (20/10/2026)
Los pozos (en tierra) y remolinos (en el agua) ocultos ya se generan, se descubren al pasar, matan al que cae y ahora
se dibujan. El pozo ya lleva tu dibujo (picts\pozo.PCX). Cada vez que muere un grupo en un pozo aparece al lado una tumba, una lápida o una cruz.
**Solo en esta PC, no en red** (todavía cada PC armaría sus propios pozos). En C:\Warlords3 ya está la 1.0.56.0,
que trae los nombres y el remolino nuevo.
**Cambio de 1.0.60.0:** los remolinos salen solo en mar abierto, a dos casillas o más de cualquier costa (ya no en
ríos). Vale en partidas nuevas; las ya empezadas conservan los suyos. Revisá en una partida nueva que no aparezcan pegados a la costa.
**Cambio de 1.0.56.0:** el remolino tiene su dibujo propio (la espiral que aprobaste), de unas dos casillas de ancho
y girando. Mirá que se vea entero y parejo sobre el agua, que junto a la costa no se pinte sobre la tierra, y que
**solo mate la casilla del medio** (las de alrededor se cruzan sin riesgo).
**Cambio de 1.0.52.0:** cada pozo y remolino tiene **nombre** (por ejemplo «the Well of Souls», «the Maelstrom of
Kor»), y los avisos lo dicen: «You have discovered the Well of Souls!», «Your army fell into the Well of Souls!».
**Cambio de 1.0.50.0:** se descubre en **1 de cada 5 pasos** (antes 1 de cada 10).
**Cambios de 1.0.49.0 (tu prueba del 21/10):** los remolinos salen el doble que los pozos; pozos, remolinos y trampas
se descubren solo a **una casilla** (antes, con el radio de visión del grupo); un grupo de **solo voladores no
descubre** nada. Construir trampas se prueba en la tarea 26.
1. Abrí DarklordAV.exe y empezá una partida nueva **contra la computadora**, en un mapa al azar, con **Hidden Ruins**
   activada y, en Viewing Options, **Discover hidden ruins as you pass**.
2. Al empezar: mirá la zona de tu capital. Si en esa región tocó un pozo, tiene que verse el dibujo del pozo
   en esa casilla. Si no ves ninguno, seguí al paso 3.
3. Mové ejércitos por tierra y barcos por el agua unos turnos. Cuando descubras uno tiene que salir el aviso «You
   have discovered the Well of …!» (o el nombre de un remolino) y quedar dibujado. El remolino tiene que verse **girando**.
4. Mandá a propósito un ejército barato (no voladores) a un pozo descubierto, eligiendo esa casilla como destino:
   tiene que morir, salir «Your army fell into the Well of …!» y sonar el grito de muerte de héroe. Además tiene que
   aparecer una tumba, lápida o cruz a 2 casillas o menos del pozo (nunca encima). Si tirás otro ejército, otra más,
   en otra casilla (desde 1.0.63.0: tumba = montículo con piedra; cruz = montículo con cruz; la tercera = cruz sin montículo, con sombra y ramos de flores acostados al pie). Si tenés un barco
   descartable, lo mismo con un remolino («Your army was swallowed by the Maelstrom of …!»).
5. Si podés, probá también con un grupo que tenga un **volador**: el volador tiene que sobrevivir y quedarse ahí.
6. Guardá la partida, salí y volvé a cargarla: los pozos y remolinos descubiertos y las tumbas tienen que seguir
   dibujados.
7. Anotá abajo qué viste (y si algún dibujo queda mal ubicado, tapa algo o parpadea).
Resultado:

- [x] **25.** IA: Hexagon con menos azar (20/10/2026)
Las tandas 25 a 34 no alcanzaron para demostrar nada: hay demasiado azar entre partidas. Esta vez todos juegan en
condiciones idénticas y sin ruinas ocultas.
1. Armá un bando simple con el editor de bandos: sin maná, el mismo héroe y los mismos regulares en todos los colores
   (lo que te parezca necesario para que no haya dados de más).
2. Armá en **Hexagon** una partida guardada igual que Tanda_hex_alianzas (30 turnos, 2000 puntos, Shared Cities,
   Diplomacy, los mismos equipos 013 contra 457, un bando en Humano), pero con ese bando en todos los colores.
   **Sin ruinas ocultas** (Hidden Ruins apagada; el juego no tiene opción para quitar las ruinas). Guardala como **Tanda_hex_simple** y avisame: te digo cuándo
   correr la tanda.
Resultado: (usuario, 21/10) hecha, pero guardada sobre **Tanda_hex_alianzas** (no Tanda_hex_simple): bando nuevo más
simple, sin maná, casi el mismo héroe, mismos bandos, **sin ruinas ocultas** (corrección del usuario, 21/10: no "sin
ruinas", esa opción no existe; las ruinas están, todas visibles); dos grupos de aliados intercalados en el mapa.
(usuario, 21/10) los colores quedaron intercalados igual que antes (equipos 013|457).
(Este número era 24, repetido con la de pozos: pasó a 25.)
(Claude, 21/10) Revisada: los equipos 013|457 y las opciones están bien. Pero el **blanco no tiene el mismo bando**
que los demás: tiene 3 unidades más (Peasants, Clay Golems y Moonguard, en los lugares 13, 14 y 15), que en
amarillo, rojo, verde, azul y negro están vacíos. Todo lo demás es idéntico.
3. Abrí Tanda_hex_alianzas y dejá el blanco con el mismo bando que los otros (sacale esas 3 unidades, o cargale
   a todos el mismo .PGS). Volvé a pasar un bando a Humano y guardala con el mismo nombre. Avisame y la reviso.
   (usuario, 21/10) hecho. (Claude, 21/10) revisada: bandos iguales en los 6 colores, equipos 013|457. Seguí con el 4.
   (usuario, 21/10) corriendo con **10 partidas** por tanda en vez de 8 (60 en total, unas 18 horas).
   (Claude, 22/10) terminada: tandas 35 a 40, 60 partidas, sobre Tanda_hex_alianzas **con las ruinas activas**
   (la versión sin ruinas se armó después). La serie sin ruinas es la tarea 30.
4. Cuando te confirme que está bien: abrí el Monitor de IA y tocá **Actualizar** (tiene que pasar a la versión
   **1.0.10** o posterior; sin ella la tanda se armaría mal). Después: **Ninguna**, marcá solo **hex_alianzas** (tiene que
   aparecer «(alianzas)»), Partidas: **8** (corriste 10), **Tandas automatizadas** con serie de **6**, **Nueva tanda**. La
   bitácora tiene que decir «Bandos: hex_alianzas común» y «equipos 013|457». Son unas 15 horas; si se corta,
   **Retomar** con las que falten.
   (Claude, 22/10) En curso: tandas 35 a 39 completas (10 partidas cada una); la 40, la última, va por la partida 7.

- [x] **29.** Bonos ordenados en el editor y habilidad «Bridge» (22/10/2026)
**Resultado (22/10/2026):** el editor nuevo funciona bien.
Ahora **Bridge** es una habilidad especial (Bridge +1, +2, +3…: suma a la fuerza cuando se pelea sobre un puente en
pie); **Trap** es un Combat Bonus y ya no un Move Bonus; Landing, Carrier y Cabotage son solo Move Bonus. Para que
el editor lo muestre así hay un editor nuevo, **war3ed_av.exe** (el war3ed_ssg.exe de siempre no se tocó).
0. Ya está: vista-aliada 1.0.57.0 quedó instalada en C:\Warlords3 (22/10/2026). Cerrá war3ed_ssg.exe y usá **war3ed_av.exe**.
1. Abrí **war3ed_av.exe** → Edit Army Data de una unidad. En los cuatro Move Bonus **no** tienen que estar «bridge» ni
   «trap» (sí landing, carrier, cabotage). En Combat Bonus **no** tienen que estar landing, carrier, cabotage ni
   bridge (sí «trap»). En Special Ability tiene que estar **«Bridge +N»** donde antes decía «Giantslayer +N».
2. Las unidades que tenían «bridge» como Combat Bonus hay que pasarlas a la habilidad: Special Ability «Bridge +N» y
   el número. **Nautilus** tiene hoy Combat Bonus bridge +5 **y** Lightning +5: una unidad tiene una sola habilidad
   especial, así que elegí cuál de las dos le queda.
3. En una partida, una unidad con Bridge peleando sobre un puente en pie: en el detalle de la batalla tiene que sumar
   su valor; fuera del puente, o en un puente derribado, no. Los héroes no la usan.
Resultado:

- [x] **23.** IA: tanda A/B de alianzas en Hexagon (20/10/2026)
En Borderlands un equipo arranca con ventaja del mapa; Hexagon da a cada bando casi la misma ubicación y los mismos
recursos, así que mide mejor si las reglas de alianzas ayudan al bloque. (Los mapas al azar no igualan las
condiciones: descartados.)
1. Armá una partida guardada en **Hexagon** igual que Tanda_Border_Alianzas: el mismo .PGS en todos los colores, 30
   turnos, 2000 puntos, **Shared Cities** y **Diplomacy** activadas, y **dos equipos aliados del mismo tamaño** desde
   el arranque (Hexagon no admite 8 bandos: repartí los que admita en dos mitades). Elegí los equipos para que las
   dos mitades queden en posiciones equivalentes del mapa. Pasá un bando a Humano antes de guardar.
   Guardala como **Tanda_Hex_Alianzas**.
2. En el Monitor de IA: **Ninguna**, marcá solo **Hex_Alianzas** (tiene que aparecer «(alianzas)»), Partidas: **8**,
   **Tandas automatizadas** con serie de **6**. **Nueva tanda**. La bitácora tiene que mostrar los dos equipos
   alternándose con la IA de prueba.
3. Avisame cuando terminen las 6 (48 partidas; a unos 18 minutos por partida son unas 15 horas). Si una tanda se corta: **Retomar** con la serie de las que falten.
Resultado: (Claude, 20/10) las 6 tandas (29 a 34) completas y analizadas; detalle en ia\PENDIENTE-entrenamiento-ia.md.

- [x] **1.** IA: tandas de control con alianzas fijas (etapa 3, paso 2) (16/10/2026)
Mide cuánto se refugia y defiende en común la IA de hoy, antes de enseñarle nada.
1. Armá dos partidas guardadas nuevas, igual que las del rating (el mismo .PGS X-12 en los 8 colores, 30 turnos,
   2000 puntos), pero con **Shared Cities** y **Diplomacy** activadas y estos dos equipos de 4 aliados desde el
   arranque (los repartos dejan los equipos parejos según las partidas ya jugadas):
   - **Scarpart**: blanco, amarillo, rojo y azul contra naranja, verde, celeste y negro.
     Guardala como **Tanda_Scarpart_Alianzas**.
   - **The Borderlands**: blanco, naranja, verde y negro contra amarillo, rojo, azul y celeste.
     Guardala como **Tanda_Borderlands_Alianzas**.
   Como siempre, pasá un bando a Humano antes de guardar.
2. Prueba de 1 partida (decidido 16/10/2026: las guardadas no se tocan; se ve si el juego vuelve vigentes las
   alianzas propuestas). Actualizá el Monitor de IA (botón Actualizar, versión 1.0.3). En **Guardadas** apretá
   **Ninguna** y marcá solo **Scar_Alianzas** (por ahora aparece sin la marca "(alianzas)", porque las alianzas
   todavía son propuestas). Partidas: **1**. **Nueva tanda**.
   Si querés probar también la tarea 2, prendé el interruptor de suspensión antes de apretar Nueva tanda.
3. Cuando termine, avisame: reviso en el registro si las alianzas pasaron a vigentes y los registros nuevos
   (refugios, puentes, convoyes). Si salió bien, sigue una tanda de **6** con las dos guardadas.
4. Con mi OK, seguí con más tandas iguales hasta **32 partidas** en total (16 por mapa).
Resultado: paso 1 hecho (16/10/2026). Guardadas como **Tanda_Scar_Alianzas** y **Tanda_Border_Alianzas** (no
entran nombres más largos), las dos con blanco, amarillo, rojo y azul contra negro, verde, celeste y naranja.
  (Claude: los bandos son iguales en los 8 colores. Las alianzas quedaron como propuestas mutuas, todavía no
  vigentes. Por pedido tuyo no se tocan: la prueba del paso 2 dice si el juego las vuelve vigentes.)
Resultado paso 2-3 (16/10/2026): partida 118 jugada. El juego volvió vigentes las alianzas solo, en el turno 3, y
duraron hasta el final. Pero no hubo refugios ni banderas dobles: el parche exigía Hidden Map para compartir
ciudades. Corregido en **vista-aliada 1.0.34.0** (ya publicado e instalado): con el mapa visible, toda ciudad de un
aliado se comparte. La partida 118 cuenta solo como prueba.
5. Tanda de **6** con **Border_Alianzas** solamente (Scarpart tiene las ciudades muy separadas, como notaste).
   En el Monitor de IA: **Ninguna**, marcá solo **Border_Alianzas**, Partidas: **6**, **Nueva tanda**.
   Si mirás alguna partida, fijate si las ciudades de un aliado muestran dos banderas. Avisame al terminar.
Resultado paso 5 (17/10/2026): hecho, se ven todas las banderas. Tarea 2 también cumplida.
6. (Es el paso 4, ajustado: Scarpart queda afuera, así que son 16 partidas, todas en Borderlands. Faltan 10, en
   tandas cortas de día, por pedido tuyo del 17/10/2026: una de **6** y otra de **4**.) Tanda de **6** con
   **Border_Alianzas**: en el Monitor de IA, **Ninguna**, marcá solo **Border_Alianzas**, Partidas: **6**,
   **Nueva tanda**. Podés dejar prendida la suspensión. Avisame al terminar.
Resultado paso 6 (17/10/2026, tanda 20): 5 partidas válidas; la primera se colgó en el turno 25 con el equipo
negro-verde-celeste-naranja ya eliminado (no cuenta). Igual que la tanda anterior: alianzas firmes todo el juego,
pero ningún refugio en ciudad aliada ni defensas conjuntas.
7. Como se perdió una partida, en vez de 4 va otra de **6** (faltan 5 válidas y las partidas van de a pares):
   Partidas: **6**, el resto igual que el paso 6. Avisame al terminar.
(17/10/2026, corrección de Claude: el paso 7 figuraba como hecho, pero la base de datos del Monitor no tiene
ninguna tanda después de la 20, que es la del paso 6 y terminó a las 14:05. El paso 7 sigue pendiente.)
Resultado paso 7: hecho (tanda 21, 17/10). 4 partidas ok y la que cerraste a mano en el turno 30 (cuenta: su
resultado sale de los turnos). Se perdieron 2: una cortada en el turno 20 y una colgada con solo aliados vivos (el
cartel «victoria aliada»). Control completo: 16 partidas válidas, 2467 gana 9 y 0135 gana 7. Refugios en ciudad
aliada: 0; defensas con más de un color: 0. La IA original no usa las alianzas: el paso 2 de la etapa 3 está
cerrado. No tenés nada más que hacer en esta tarea.

- [x] **21.** IA: tanda A/B de la destreza de alianzas (etapa 3, paso 3) (18/10/2026)
**Retomada (19/10/2026) con vista-aliada 1.0.39.0**, ya instalado en C:\Warlords3. Las tandas 22 a 24 son de
versiones anteriores y no cuentan.

La IA de prueba ahora tiene dos reglas nuevas: el héroe perseguido por un héroe enemigo con misión de asesinarlo
se refugia en una ciudad aliada bien defendida, y las pilas van a defender una ciudad aliada a punto de ser
atacada (si ninguna ciudad propia está en riesgo). Un equipo de 4 colores juega con la IA de prueba y el otro con
la original, y en la partida siguiente al revés.
1. En el Monitor de IA (tiene que decir **1.0.8**; si dice menos: ruedita → **Buscar actualización**, cuando no
   haya una tanda corriendo): **Ninguna**, marcá solo **Border_Alianzas**, Partidas: **8**. En **Controles** tildá
   **Tandas automatizadas**, serie de **2** tandas (la primera de las tres ya está: tanda 25, 19/10). La serie
   no cuenta las tandas ya corridas: siempre se pone las que faltan. **Nueva tanda**. Podés dejar prendida la
   suspensión: se suspende recién al terminar la última. En la bitácora, cada partida tiene que decir colores con IA de prueba
   **[0, 1, 3, 5]** o **[2, 4, 6, 7]**, alternados, y entre tanda y tanda «Serie: tanda 1 de 2 terminada; arranca
   la siguiente».
2. Avisame cuando terminen las tres (24 partidas en total). Si una tanda se corta, la serie se detiene: apretá
   **Retomar** con el check tildado y la serie de las que falten.
Si mirás alguna partida: lo nuevo es ver una ciudad aliada defendida por ejércitos de dos colores (dos banderas)
cuando un enemigo se le acerca.
Resultado: (Claude, 19/10) la tanda 25 (8 partidas) está analizada. **La serie de 2 no llegó a correr**: en la
base no hay ninguna tanda después de la 25 (la última partida terminó 12:35) y no hay un juego abierto. Falta
repetir el paso 1 (serie de 2 → serían las tandas 26 y 27). El Monitor ya usa el juego 1.0.43.0; para esta prueba
da igual (lo nuevo no actúa en estas partidas), queda anotado en la base.

(Claude, 20/10) Serie completa con las tandas 27 y 28 (24 partidas): tarea terminada. Resultado: empate (12 victorias
cada IA); detalle en ia\PENDIENTE-entrenamiento-ia.md.

- [x] **20.** Sonido del juego: volvió a faltar (17/10/2026)
La partida en red del 17/10 se jugó sin sonido: la tanda del paso 7 de la tarea 1 lo volvió a dejar silenciado. El
arreglo de la 1.0.4 (borrar la marca del registro) no servía: Windows la guarda en su memoria y la vuelve a
escribir. Lo medí en esta PC y el Monitor de IA 1.0.5 lo hace de otra forma: al terminar cada tanda abre el juego
unos 8 segundos, le quita el silencio y lo cierra. Ya le devolví el sonido a tu juego.
1. Actualizá el Monitor de IA (botón Actualizar): tiene que decir 1.0.5.
2. En la próxima partida normal fijate si se oyen la música y los efectos.
3. Después de la tanda del paso 7 de la tarea 1, abrí el juego a mano: también tiene que oírse.
Si en algún caso no se oye, anotá cuál y avisame.
Resultado: (Claude, 18/10) medido después de la tanda 21: el juego abre sin silencio. Falta que lo confirmes de oído (pasos 2 y 3).
Resultado (usuario, 20/10/2026): cumplida.

- [x] **19.** Tailscale: segunda conexión del Puente para Nico (17/10/2026)
El router Movistar no deja abrir el puerto, así que si se corta el Wi-Fi del servidor el Puente sigue por
Tailscale. Tu servidor ya escucha ahí (dirección 100.77.65.99). El Actualizador 1.0.12.0 trae la opción
**14 TAILSCALE**, que instala y configura Tailscale. Accesos directos pasó a la 15 y Salir a la 16.
1. En tu PC: abrí https://login.tailscale.com/admin/machines con tu cuenta. En la fila de **desktop-liifpj1**
   (100.77.65.99) tocá los tres puntitos «…», elegí **Share…** y copiá el enlace. Mandáselo a Nico por WhatsApp.
2. En la PC de Nico: el Actualizador se actualiza solo a 1.0.12.0. Nico elige la **13** (trae el Puente 1.1.6.0)
   y después la **14**. La 14 instala Tailscale (acepta el permiso de administrador), abre el navegador para que
   entre con su cuenta (Google o Microsoft sirven; es gratis) y le pide que pegue tu enlace. Al final tiene que
   decir **«El servidor del Puente responde por Tailscale»**.
3. Si en algún paso aparece un mensaje en rojo, Nico saca una foto y me la pasás.
   (La instalación y el inicio de sesión no se pudieron probar acá porque esta PC ya tiene Tailscale; la PC de
   Nico es la primera prueba de esa parte.)
Resultado (usuario, 20/10/2026): cumplida.

- [x] **16.** Sonido del juego: comprobar que volvió (17/10/2026) — superada por la 20, ya resuelta
El banco de pruebas silenciaba DarklordAV.exe y Windows lo recordaba, así que también quedaba mudo en las partidas
normales. Ya le borré esa marca y el Monitor de IA 1.0.4 la borra al terminar cada partida.
1. (Hecho: la 1.0.4 está compilada y publicada.)
2. Abrí DarklordAV.exe y empezá una partida normal: tiene que oírse la música.
3. Si no se oye: clic derecho en el parlante de la barra de tareas → **Abrir el mezclador de volumen** y fijate si
   DarklordAV tiene el parlante tachado. Anotá acá lo que veas.

- [x] **2.** IA: probar el interruptor "Suspender al terminar" del Monitor de IA (16/10/2026)
1. Abrí el Monitor: arriba a la derecha, a la izquierda de CPU y RAM, está el botón de MovilCode
   (al pasar el mouse dice "modo sleep"). Un clic lo prende (luz roja encendida) y otro lo apaga. Queda
   recordado para la próxima vez que abras el Monitor.
2. Con el interruptor prendido, al terminar una tanda la bitácora avisa y la PC se suspende a los 30 segundos.
   Si en esos 30 segundos lo apagás, se cancela. (Con la suspensión prendida no suena la alarma.)
3. Probalo en la primera tanda de la tarea 1 (prendé el interruptor antes de apretar Nueva tanda) y anotá si la
   PC se suspendió al terminar.
Resultado: cumplida (17/10/2026, anotado en el paso 5 de la tarea 1).

- [x] **3.** Herramientas 1.0.0.1: probar en partida que el espectador no pueda volver al Warlords (16/10/2026) — unida a la tarea 18
Votación 1.1.3 y Sorteo 1.1.2 ya están instalados en C:\Warlords3\Herramientas de esta PC. Hace falta otra PC
con los mismos .exe (copiá votacion.exe y sorteo.exe de esa carpeta a la misma carpeta de la otra PC).
1. Partida por Puente Warlords entre las dos PC. Desde la anfitriona, abrí la **Votación**.
2. En la otra PC (espectador) la Votación tiene que aparecer adelante y seguir lo que se vota en la anfitriona.
3. En el espectador intentá volver al juego: clic sobre el juego, Alt+Tab, tecla Windows. En menos de un
   segundo la Votación tiene que volver adelante.
4. Cerrá la Votación en la anfitriona: en el espectador se cierra sola y el juego tiene que seguir normal
   (que no quede minimizado, en negro ni colgado).
5. Repetí 1 a 4 con **Draw Lots** (Sorteo).
Anotá si todo anduvo; si algo falló, en qué paso y qué se vio. Con el OK, lo publico para todos los jugadores.
Resultado: (17/10, partida con Nico) falló el paso 2: Votación y Sorteo quedaron quietos en la pantalla inicial y no
se cerraron solos en el paso 4. Se sigue en la tarea 18.

- [x] **17.** Nico: actualizar Votación y Sorteo (17/10/2026)
El puente frenó la partida porque la PC de Nico tiene otra versión de votacion.exe y sorteo.exe (con versiones
distintas el espectador se queda trabado, por eso el puente las compara).
1. En la PC de Nico, abrí el Actualizador y elegí la opción **11 (Votación)** y después la **12 (Sorteo)**.
2. Volvé a armar la partida: ya no tienen que aparecer esos dos archivos en el cartel.
   (El renglón de COMBAT.DAT se arregla en el puente; hasta entonces puede seguir apareciendo.)
Resultado: (Claude: hecho; la partida del 17/10 arrancó y se jugó completa por el Puente.)

- [x] **5.** IA: averiguar con qué se interrumpe una partida de 8 bandos en IA (13/10/2026)
1. Abrí Darklord.exe (el original) y empezá una partida con los 8 bandos manejados por la computadora.
2. Cuando estén corriendo los turnos, apretá una sola vez la tecla **Esc** y esperá unos segundos.
   - Si aparece la ventana "Interrupt Game" (la que te dejó pausar), anotá acá: "Fue Esc".
3. Si no apareció: hacé **un clic** con el botón izquierdo del mouse sobre el mapa y esperá.
   - Si aparece, anotá: "Fue el clic".
4. Si ninguna de las dos funcionó: minimizá el juego y volvé a abrirlo desde la barra de tareas (así lo
   hiciste la primera vez). Anotá si apareció la ventana.
Resultado: tecla tab + clic izq. o der.

- [x] **6.** IA: probar el registro por turno (13/10/2026)
1. Abrí **DarklordAV.exe** (no el original) y empezá una partida con los 8 bandos manejados por la computadora,
   en cualquier escenario.
2. Dejala correr unos 3 turnos completos (que todos los colores hayan jugado 3 veces) y cerrá el juego.
3. Fijate si existe el archivo C:\Warlords3\DATA\IA.CSV. Anotá acá: "Existe" o "No existe".
   No hace falta abrirlo: lo reviso yo.
Resultado: existe

- [x] **7.** IA: probar el registro de batallas (13/10/2026)
1. Abrí **DarklordAV.exe** y empezá una partida con los 8 bandos manejados por la computadora.
2. Dejala correr hasta que veas que hubo peleas (unos 8 a 10 turnos suele alcanzar) y cerrá el juego.
3. Fijate si existe el archivo C:\Warlords3\DATA\IA_BAT.CSV. Anotá acá: "Existe" o "No existe".
   No hace falta abrirlo: lo reviso yo.
Resultado: existe (60 batallas en 15 turnos; partida terminada, captura del Game Over compartida)

- [x] **8.** IA: preparar las 3 partidas para las tandas (13/10/2026)
Hace falta una partida guardada por escenario, en el turno 1, con los 8 bandos manejados por la computadora.
Para cada escenario (Scarpart, Hexagon y TomeLand):
1. Abrí **DarklordAV.exe** y empezá una partida nueva en ese escenario:
   - los 8 bandos en Computadora, sin alianzas;
   - los bandos (.PGS) que te parezcan los mejores del clan, 2000 puntos;
   - fin de la partida por turnos con puntos de victoria, por ejemplo **30 turnos**.
2. Apenas empiece, pasá un bando a Humano y guardá la partida con este nombre exacto:
   **Tanda_Scarpart**, **Tanda_Hexagon** o **Tanda_TomeLand**, según el escenario.
   Después ya podés salir sin volver ese bando a Computadora: al cargar la partida en una tanda, el juego pasa
   solo a Computadora los bandos que estén en Humano.
Resultado: hecho (los mapas Hexagon y Tomeland no tienen casillas para 8 jugadores, asi que se reemplazaron por "The Boderlands" y "Kor")

- [x] **9.** IA: primera tanda de prueba (después del punto anterior)
1. Con las 3 partidas guardadas, hacé doble clic en
   **F:\source\repos\actualizador-warlords\ia\tanda.bat**.
2. El programa abre el juego, que carga solo cada partida y la juega hasta el final. Son 3 partidas seguidas.
   No toques la PC mientras corre: la ventana negra va mostrando el avance.
   Fijate en el primer turno: el bando que guardaste en Humano tiene que jugar solo.
3. Al terminar, la ventana muestra un informe. Anotá acá si las 3 partidas dicen **ok** y cuántos minutos tardó
   cada una. Si alguna dice otra cosa, anotá cuál y qué se veía en pantalla en ese momento.
Resultado: las 3 dieron OK. 26, 7 y 2.8 minutos respectivamente.
  (Claude: según la ventana, 26,0, 27,1 y 22,8 minutos. Cada partida hubo que arrancarla con el botón "Single Player";
  se corrigió en la versión 1.0.31.0, ver el punto siguiente.)

- [x] **10.** IA: tanda sin tocar nada (14/10/2026)
1. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\monitor.bat**, escribí el número del monitor donde
   querés ver el juego y Enter. Queda guardado; para cambiarlo, se vuelve a abrir monitor.bat.
2. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\tanda.bat** y no toques nada.
3. Cada partida tiene que empezar sola, sin apretar "Single Player", y verse en el monitor que elegiste.
Resultado: (Claude: cumplida de hecho: las tandas 6 a 17, 96 partidas, corrieron solas con el Monitor de IA.)

- [x] **11.** IA: ¿el juego se ve al abrirlo a mano? (14/10/2026)
Desde las 2:50 de hoy, cuando lo abro yo, el juego queda en una ventana totalmente blanca, incluso el
Darklord.exe original. Necesito saber si a vos te pasa lo mismo:
1. Abrí el juego con el acceso directo de siempre (Darklord.exe original) y apretá "Single Player".
2. Anotá acá si se ve el menú del juego o si la ventana queda blanca.
3. Hacé lo mismo con **DarklordAV.exe** y anotá lo mismo.
Resultado: los dos funcionan perfectamente abiertos a mano.
  (Claude: la ventana blanca la causaba la forma en que tanda.py apretaba "Single Player"; ya se corrigió.)

- [x] **12.** IA: tanda en segundo plano (14/10/2026)
1. Si tenés el juego abierto, cerralo.
2. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\tanda.bat** y seguí usando la PC normalmente.
   Al empezar cada partida el juego puede aparecer un instante adelante; en unos segundos se pasa solo al monitor
   elegido con monitor.bat.
3. Fijate de vez en cuando que el juego siga avanzando en ese monitor aunque estés usando otra ventana.
4. Al terminar, anotá acá si las partidas dicen **ok** y si en algún momento el juego se quedó quieto o te molestó.
Resultado: (Claude: cumplida de hecho: las tandas 6 a 17, 96 partidas, corrieron solas con el Monitor de IA.)

- [x] **13.** IA: probar el Monitor de IA (14/10/2026)
Reemplaza a tanda.bat y monitor.bat.
1. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\Monitor-IA.exe**.
2. Arriba aparece la tanda 4, que quedó a medias. Apretá **Retomar**: tiene que seguir con la partida 2.
   (Para una tanda nueva: poné la cantidad de partidas y apretá **Nueva tanda**.)
3. Mirá que la tabla de colores se vaya actualizando con los turnos y que el juego no suene.
   Probá destildar "Sonido del juego desactivado": el juego tiene que sonar a los pocos segundos.
4. Al terminar tiene que sonar la alarma y aparecer el informe abajo.
Anotá acá qué funcionó, qué no, y qué te gustaría cambiar o agregar.
Resultado: (Claude: cumplida de hecho: las tandas 6 a 17, 96 partidas, corrieron solas con el Monitor de IA.)

- [x] **14.** IA: rehacer las 3 partidas de las tandas con el mismo bando en los 8 colores (14/10/2026)
Las tandas no arman bandos: cargan las partidas guardadas Tanda_Scarpart, Tanda_Borderlands y Tanda_Kor tal
como quedaron. Para que todos los colores jueguen con el mismo bando hay que volver a guardar esas 3 partidas.
Para cada escenario (Scarpart, The Borderlands y Kor):
1. Abrí **DarklordAV.exe** y empezá una partida nueva en ese escenario, igual que la vez anterior:
   - los 8 bandos en Computadora, sin alianzas;
   - **el mismo .PGS cargado en los 8 colores** (el mismo archivo, no uno parecido);
   - 2000 puntos y fin por turnos con puntos de victoria (30 turnos).
2. Apenas empiece, pasá un bando a Humano y guardá la partida con el **mismo nombre de antes**
   (Tanda_Scarpart, Tanda_Borderlands o Tanda_Kor), aceptando reemplazar la anterior.
3. Anotá acá qué .PGS usaste. Después la tanda se larga como siempre, con **ia\tanda.bat**.
Resultado: nobre del bando: X-12.pgs

- [x] **15.** IA: probar el registro de alianzas, refugios, puentes y convoyes (vista-aliada 1.0.33.0) (16/10/2026) — unida a la tarea 1
Pasó a ser el paso 3 de la tarea 1.
