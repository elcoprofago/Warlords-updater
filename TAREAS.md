# Tareas del usuario

Cada tarea tiene un número fijo: no cambia aunque se resuelva. Las nuevas toman el número siguiente.
Esta es la lista completa. Las del Puente Warlords están en `puente-warlords\TAREAS.md` y figuran abajo en el
orden sugerido como «Puente 1», «Puente 2». El repo Votacion no tiene tareas propias: las de la Votación y el
Sorteo están acá (tarea 18).

## Orden sugerido
1. **Tarea 20** (sonido): actualizar el Monitor de IA y fijarte en la próxima partida.
   La **tarea 21** (tanda A/B de alianzas) empieza con la misma actualización del Monitor: se pueden hacer juntas.
2. **Puente 1** (reiniciar el router Huawei): hoy Nico no puede entrar por el Wi-Fi.
3. **Tarea 19** (Tailscale con Nico): antes de la próxima partida en red.
4. **Puente 2** (partida de prueba con el Puente 1.1.6.0). En la misma partida se hace la **tarea 18**
   (Votación y Sorteo): una sola partida sirve para las dos.
5. **Tarea 4** (rating de posiciones): la dejaste para otro momento.

# Pendientes

## 21. IA: tanda A/B de la destreza de alianzas (etapa 3, paso 3) (18/10/2026)
**Retomada (19/10/2026) con vista-aliada 1.0.39.0**, ya instalado en C:\Warlords3. Las tandas 22 a 24 son de
versiones anteriores y no cuentan.

La IA de prueba ahora tiene dos reglas nuevas: el héroe perseguido por un héroe enemigo con misión de asesinarlo
se refugia en una ciudad aliada bien defendida, y las pilas van a defender una ciudad aliada a punto de ser
atacada (si ninguna ciudad propia está en riesgo). Un equipo de 4 colores juega con la IA de prueba y el otro con
la original, y en la partida siguiente al revés.
1. En el Monitor de IA (tiene que decir **1.0.6**): **Ninguna**, marcá solo **Border_Alianzas**, Partidas: **8**,
   **Nueva tanda**. Podés dejar prendida la suspensión. En la bitácora, cada partida tiene que decir colores con IA
   de prueba **[0, 1, 3, 5]** o **[2, 4, 6, 7]**, alternados.
2. Al terminar, dos tandas más iguales de 8 (24 partidas en total). Avisame cuando terminen las tres.
Si mirás alguna partida: lo nuevo es ver una ciudad aliada defendida por ejércitos de dos colores (dos banderas)
cuando un enemigo se le acerca.
Resultado:

## 20. Sonido del juego: volvió a faltar (17/10/2026)
La partida en red del 17/10 se jugó sin sonido: la tanda del paso 7 de la tarea 1 lo volvió a dejar silenciado. El
arreglo de la 1.0.4 (borrar la marca del registro) no servía: Windows la guarda en su memoria y la vuelve a
escribir. Lo medí en esta PC y el Monitor de IA 1.0.5 lo hace de otra forma: al terminar cada tanda abre el juego
unos 8 segundos, le quita el silencio y lo cierra. Ya le devolví el sonido a tu juego.
1. Actualizá el Monitor de IA (botón Actualizar): tiene que decir 1.0.5.
2. En la próxima partida normal fijate si se oyen la música y los efectos.
3. Después de la tanda del paso 7 de la tarea 1, abrí el juego a mano: también tiene que oírse.
Si en algún caso no se oye, anotá cuál y avisame.
Resultado: (Claude, 18/10) medido después de la tanda 21: el juego abre sin silencio. Falta que lo confirmes de oído (pasos 2 y 3).

## 19. Tailscale: segunda conexión del Puente para Nico (17/10/2026)
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
Resultado:

## 18. Votación y Sorteo en la PC de Nico: datos de su instalación (17/10/2026)
Ya está comprobado (fotos de sus votacion.ver y sorteo.ver) que a la PC de Nico le llegan los votos y el cierre.
Lo que falla es cómo se ven las ventanas allá: en esta PC se actualizan bien. Hace falta saber cómo corre el juego
en su PC. Que Nico te mande:
1. El archivo **C:\Warlords3\dxcfg.ini** (abierto con el Bloc de notas, una foto alcanza).
2. Los archivos **OPENGL32.log** que tenía abiertos en el Bloc de notas: de qué carpeta son (foto de la barra de
   direcciones del Explorador) y su texto.
3. ~~Si el juego ocupa toda la pantalla o se ve en una ventana.~~ (Respondido 17/10: ocupa toda la pantalla, igual que en la PC del anfitrión; Nico cierra las ventanas a mano.)
4. ~~Administrador de tareas~~: ya no hace falta, lo reemplaza el registro de abajo.

**Registro de lo que hacen las ventanas (lo principal, 17/10/2026).** Votación 1.1.4 y Sorteo 1.1.3 anotan todo
lo que hacen en un archivo, y si la ventana se traba anotan en qué punto exacto quedó detenida.
1. En la PC de Nico **y en la tuya**: abrí el Actualizador y elegí la opción **11 (Votación)** y después la
   **12 (Sorteo)**. Al abrirlas, el título de la ventana tiene que decir **v1.1.4** (Votación) y **v1.1.3** (Sorteo).
   (En tu PC ya están instaladas; si el Actualizador dice que no hay nada nuevo, está bien.)
2. Jueguen una partida en red como siempre y abrí, como anfitrión, la Votación y el Sorteo; cerralos cuando
   terminen, igual que la vez pasada.
3. Cuando termine la partida, que Nico te mande estos dos archivos (son de texto; mandarlos como archivo, no foto):
   **C:\Warlords3\Herramientas\votacion.log** y **C:\Warlords3\Herramientas\sorteo.log**.
   (Si su juego está en otra carpeta, son los que están junto a votacion.exe y sorteo.exe.)
4. Copiá los dos archivos de Nico a **F:\source\repos\actualizador-warlords\nico\** (creá la carpeta) y anotá acá
   la hora aproximada en que abriste cada programa. Tus propios .log también sirven: dejalos donde están.
Resultado:

## 1. IA: tandas de control con alianzas fijas (etapa 3, paso 2) (16/10/2026)
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

## 4. IA: rating de posiciones, un grupo de tandas por mapa (16/10/2026) — postergada por vos
Reemplaza a la "etapa 2 en Scarpart": Scarpart ya está medido (32 partidas). Para cada mapa que falta:
1. Armá la partida guardada como la vez anterior: los 8 bandos en Computadora, sin alianzas, **el mismo .PGS en
   todos los colores**, 30 turnos. Pasá un bando a Humano y guardala como **Tanda_<mapa>** (por ejemplo
   Tanda_Hexagon). Si el mapa tiene menos de 8 lugares, también sirve.
2. En el Banco de pruebas, **Guardadas**: marcá solo esa partida. Partidas: **30**. **Nueva tanda**.
   (30 partidas por mapa alcanzan, como en Scarpart; pueden ser también 5 tandas de 6.)
3. Anotá abajo qué mapa quedó hecho, y dónde arranca cada color (cuadrantes I a IX, como en Scarpart): con eso
   completo la columna "Posición de arranque" del cuadro.
4. El PDF para la página del Clan: en el Banco de pruebas 1.0.2 (botón Actualizar), **Exportar PDF de un mapa…**,
   elegí el mapa y dónde guardarlo. El de Scarpart ya se puede sacar.
Resultado:

# Resueltas

## 16. [REABIERTA COMO LA 20] Sonido del juego: comprobar que volvió (17/10/2026)
El banco de pruebas silenciaba DarklordAV.exe y Windows lo recordaba, así que también quedaba mudo en las partidas
normales. Ya le borré esa marca y el Monitor de IA 1.0.4 la borra al terminar cada partida.
1. (Hecho: la 1.0.4 está compilada y publicada.)
2. Abrí DarklordAV.exe y empezá una partida normal: tiene que oírse la música.
3. Si no se oye: clic derecho en el parlante de la barra de tareas → **Abrir el mezclador de volumen** y fijate si
   DarklordAV tiene el parlante tachado. Anotá acá lo que veas.

## 2. [RESUELTA] IA: probar el interruptor "Suspender al terminar" del Monitor de IA (16/10/2026)
1. Abrí el Monitor: arriba a la derecha, a la izquierda de CPU y RAM, está el botón de MovilCode
   (al pasar el mouse dice "modo sleep"). Un clic lo prende (luz roja encendida) y otro lo apaga. Queda
   recordado para la próxima vez que abras el Monitor.
2. Con el interruptor prendido, al terminar una tanda la bitácora avisa y la PC se suspende a los 30 segundos.
   Si en esos 30 segundos lo apagás, se cancela. (Con la suspensión prendida no suena la alarma.)
3. Probalo en la primera tanda de la tarea 1 (prendé el interruptor antes de apretar Nueva tanda) y anotá si la
   PC se suspendió al terminar.
Resultado:

## 3. [UNIDA A LA TAREA 18] Herramientas 1.0.0.1: probar en partida que el espectador no pueda volver al Warlords (16/10/2026)
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

## 17. [RESUELTA] Nico: actualizar Votación y Sorteo (17/10/2026)
El puente frenó la partida porque la PC de Nico tiene otra versión de votacion.exe y sorteo.exe (con versiones
distintas el espectador se queda trabado, por eso el puente las compara).
1. En la PC de Nico, abrí el Actualizador y elegí la opción **11 (Votación)** y después la **12 (Sorteo)**.
2. Volvé a armar la partida: ya no tienen que aparecer esos dos archivos en el cartel.
   (El renglón de COMBAT.DAT se arregla en el puente; hasta entonces puede seguir apareciendo.)
Resultado: (Claude: hecho; la partida del 17/10 arrancó y se jugó completa por el Puente.)


## 5. [RESUELTA] IA: averiguar con qué se interrumpe una partida de 8 bandos en IA (13/10/2026)
1. Abrí Darklord.exe (el original) y empezá una partida con los 8 bandos manejados por la computadora.
2. Cuando estén corriendo los turnos, apretá una sola vez la tecla **Esc** y esperá unos segundos.
   - Si aparece la ventana "Interrupt Game" (la que te dejó pausar), anotá acá: "Fue Esc".
3. Si no apareció: hacé **un clic** con el botón izquierdo del mouse sobre el mapa y esperá.
   - Si aparece, anotá: "Fue el clic".
4. Si ninguna de las dos funcionó: minimizá el juego y volvé a abrirlo desde la barra de tareas (así lo
   hiciste la primera vez). Anotá si apareció la ventana.
Resultado: tecla tab + clic izq. o der.

## 6. [RESUELTA] IA: probar el registro por turno (13/10/2026)
1. Abrí **DarklordAV.exe** (no el original) y empezá una partida con los 8 bandos manejados por la computadora,
   en cualquier escenario.
2. Dejala correr unos 3 turnos completos (que todos los colores hayan jugado 3 veces) y cerrá el juego.
3. Fijate si existe el archivo C:\Warlords3\DATA\IA.CSV. Anotá acá: "Existe" o "No existe".
   No hace falta abrirlo: lo reviso yo.
Resultado: existe

## 7. [RESUELTA] IA: probar el registro de batallas (13/10/2026)
1. Abrí **DarklordAV.exe** y empezá una partida con los 8 bandos manejados por la computadora.
2. Dejala correr hasta que veas que hubo peleas (unos 8 a 10 turnos suele alcanzar) y cerrá el juego.
3. Fijate si existe el archivo C:\Warlords3\DATA\IA_BAT.CSV. Anotá acá: "Existe" o "No existe".
   No hace falta abrirlo: lo reviso yo.
Resultado: existe (60 batallas en 15 turnos; partida terminada, captura del Game Over compartida)

## 8. [RESUELTA] IA: preparar las 3 partidas para las tandas (13/10/2026)
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

## 9. [RESUELTA] IA: primera tanda de prueba (después del punto anterior)
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

## 10. [RESUELTA] IA: tanda sin tocar nada (14/10/2026)
1. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\monitor.bat**, escribí el número del monitor donde
   querés ver el juego y Enter. Queda guardado; para cambiarlo, se vuelve a abrir monitor.bat.
2. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\tanda.bat** y no toques nada.
3. Cada partida tiene que empezar sola, sin apretar "Single Player", y verse en el monitor que elegiste.
Resultado: (Claude: cumplida de hecho: las tandas 6 a 17, 96 partidas, corrieron solas con el Monitor de IA.)

## 11. [RESUELTA] IA: ¿el juego se ve al abrirlo a mano? (14/10/2026)
Desde las 2:50 de hoy, cuando lo abro yo, el juego queda en una ventana totalmente blanca, incluso el
Darklord.exe original. Necesito saber si a vos te pasa lo mismo:
1. Abrí el juego con el acceso directo de siempre (Darklord.exe original) y apretá "Single Player".
2. Anotá acá si se ve el menú del juego o si la ventana queda blanca.
3. Hacé lo mismo con **DarklordAV.exe** y anotá lo mismo.
Resultado: los dos funcionan perfectamente abiertos a mano.
  (Claude: la ventana blanca la causaba la forma en que tanda.py apretaba "Single Player"; ya se corrigió.)

## 12. [RESUELTA] IA: tanda en segundo plano (14/10/2026)
1. Si tenés el juego abierto, cerralo.
2. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\tanda.bat** y seguí usando la PC normalmente.
   Al empezar cada partida el juego puede aparecer un instante adelante; en unos segundos se pasa solo al monitor
   elegido con monitor.bat.
3. Fijate de vez en cuando que el juego siga avanzando en ese monitor aunque estés usando otra ventana.
4. Al terminar, anotá acá si las partidas dicen **ok** y si en algún momento el juego se quedó quieto o te molestó.
Resultado: (Claude: cumplida de hecho: las tandas 6 a 17, 96 partidas, corrieron solas con el Monitor de IA.)

## 13. [RESUELTA] IA: probar el Monitor de IA (14/10/2026)
Reemplaza a tanda.bat y monitor.bat.
1. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\Monitor-IA.exe**.
2. Arriba aparece la tanda 4, que quedó a medias. Apretá **Retomar**: tiene que seguir con la partida 2.
   (Para una tanda nueva: poné la cantidad de partidas y apretá **Nueva tanda**.)
3. Mirá que la tabla de colores se vaya actualizando con los turnos y que el juego no suene.
   Probá destildar "Sonido del juego desactivado": el juego tiene que sonar a los pocos segundos.
4. Al terminar tiene que sonar la alarma y aparecer el informe abajo.
Anotá acá qué funcionó, qué no, y qué te gustaría cambiar o agregar.
Resultado: (Claude: cumplida de hecho: las tandas 6 a 17, 96 partidas, corrieron solas con el Monitor de IA.)

## 14. [RESUELTA] IA: rehacer las 3 partidas de las tandas con el mismo bando en los 8 colores (14/10/2026)
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

## 15. [UNIDA A LA TAREA 1] IA: probar el registro de alianzas, refugios, puentes y convoyes (vista-aliada 1.0.33.0) (16/10/2026)
Pasó a ser el paso 3 de la tarea 1.
