# Tareas del usuario

## [RESUELTA] IA: averiguar con qué se interrumpe una partida de 8 bandos en IA (13/10/2026)
1. Abrí Darklord.exe (el original) y empezá una partida con los 8 bandos manejados por la computadora.
2. Cuando estén corriendo los turnos, apretá una sola vez la tecla **Esc** y esperá unos segundos.
   - Si aparece la ventana "Interrupt Game" (la que te dejó pausar), anotá acá: "Fue Esc".
3. Si no apareció: hacé **un clic** con el botón izquierdo del mouse sobre el mapa y esperá.
   - Si aparece, anotá: "Fue el clic".
4. Si ninguna de las dos funcionó: minimizá el juego y volvé a abrirlo desde la barra de tareas (así lo
   hiciste la primera vez). Anotá si apareció la ventana.
Resultado: tecla tab + clic izq. o der.

## [RESUELTA] IA: probar el registro por turno (13/10/2026)
1. Abrí **DarklordAV.exe** (no el original) y empezá una partida con los 8 bandos manejados por la computadora,
   en cualquier escenario.
2. Dejala correr unos 3 turnos completos (que todos los colores hayan jugado 3 veces) y cerrá el juego.
3. Fijate si existe el archivo C:\Warlords3\DATA\IA.CSV. Anotá acá: "Existe" o "No existe".
   No hace falta abrirlo: lo reviso yo.
Resultado: existe

## [RESUELTA] IA: probar el registro de batallas (13/10/2026)
1. Abrí **DarklordAV.exe** y empezá una partida con los 8 bandos manejados por la computadora.
2. Dejala correr hasta que veas que hubo peleas (unos 8 a 10 turnos suele alcanzar) y cerrá el juego.
3. Fijate si existe el archivo C:\Warlords3\DATA\IA_BAT.CSV. Anotá acá: "Existe" o "No existe".
   No hace falta abrirlo: lo reviso yo.
Resultado: existe (60 batallas en 15 turnos; partida terminada, captura del Game Over compartida)

## IA: preparar las 3 partidas para las tandas (13/10/2026)
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

## IA: primera tanda de prueba (después del punto anterior)
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

## IA: tanda sin tocar nada (14/10/2026)
1. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\monitor.bat**, escribí el número del monitor donde
   querés ver el juego y Enter. Queda guardado; para cambiarlo, se vuelve a abrir monitor.bat.
2. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\tanda.bat** y no toques nada.
3. Cada partida tiene que empezar sola, sin apretar "Single Player", y verse en el monitor que elegiste.
Resultado:

## [RESUELTA] IA: ¿el juego se ve al abrirlo a mano? (14/10/2026)
Desde las 2:50 de hoy, cuando lo abro yo, el juego queda en una ventana totalmente blanca, incluso el
Darklord.exe original. Necesito saber si a vos te pasa lo mismo:
1. Abrí el juego con el acceso directo de siempre (Darklord.exe original) y apretá "Single Player".
2. Anotá acá si se ve el menú del juego o si la ventana queda blanca.
3. Hacé lo mismo con **DarklordAV.exe** y anotá lo mismo.
Resultado: los dos funcionan perfectamente abiertos a mano.
  (Claude: la ventana blanca la causaba la forma en que tanda.py apretaba "Single Player"; ya se corrigió.)

## IA: tanda en segundo plano (14/10/2026)
1. Si tenés el juego abierto, cerralo.
2. Hacé doble clic en **F:\source\repos\actualizador-warlords\ia\tanda.bat** y seguí usando la PC normalmente.
   Al empezar cada partida el juego puede aparecer un instante adelante; en unos segundos se pasa solo al monitor
   elegido con monitor.bat.
3. Fijate de vez en cuando que el juego siga avanzando en ese monitor aunque estés usando otra ventana.
4. Al terminar, anotá acá si las partidas dicen **ok** y si en algún momento el juego se quedó quieto o te molestó.
Resultado:

## IA: probar el Monitor de IA (14/10/2026)
Reemplaza a tanda.bat y monitor.bat.
1. Hacé doble clic en **F:\source
eposctualizador-warlords\ia\Monitor-IA.exe**.
2. Arriba aparece la tanda 4, que quedó a medias. Apretá **Retomar**: tiene que seguir con la partida 2.
   (Para una tanda nueva: poné la cantidad de partidas y apretá **Nueva tanda**.)
3. Mirá que la tabla de colores se vaya actualizando con los turnos y que el juego no suene.
   Probá destildar "Sonido del juego desactivado": el juego tiene que sonar a los pocos segundos.
4. Al terminar tiene que sonar la alarma y aparecer el informe abajo.
Anotá acá qué funcionó, qué no, y qué te gustaría cambiar o agregar.
Resultado:

## IA: rehacer las 3 partidas de las tandas con el mismo bando en los 8 colores (14/10/2026)
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

## IA: probar el interruptor "Suspender al terminar" del Monitor de IA (16/10/2026)
1. Abrí el Monitor: arriba a la derecha, a la izquierda de CPU y RAM, está el botón de MovilCode
   (al pasar el mouse dice "modo sleep"). Un clic lo prende (luz roja encendida) y otro lo apaga. Queda
   recordado para la próxima vez que abras el Monitor.
2. Con el interruptor prendido, al terminar una tanda la bitácora avisa y la PC se suspende a los 30 segundos.
   Si en esos 30 segundos lo apagás, se cancela. (Con la suspensión prendida no suena la alarma.)
3. Probalo con una tanda corta (Partidas: 1) y anotá si la PC se suspendió.
Resultado:

## IA: rating de posiciones, un grupo de tandas por mapa (16/10/2026)
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
