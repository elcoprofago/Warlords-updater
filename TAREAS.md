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
Resultado:

## IA: primera tanda de prueba (después del punto anterior)
1. Con las 3 partidas guardadas, hacé doble clic en
   **F:\source\repos\actualizador-warlords\ia\tanda.bat**.
2. El programa abre el juego, que carga solo cada partida y la juega hasta el final. Son 3 partidas seguidas.
   No toques la PC mientras corre: la ventana negra va mostrando el avance.
   Fijate en el primer turno: el bando que guardaste en Humano tiene que jugar solo.
3. Al terminar, la ventana muestra un informe. Anotá acá si las 3 partidas dicen **ok** y cuántos minutos tardó
   cada una. Si alguna dice otra cosa, anotá cuál y qué se veía en pantalla en ese momento.
Resultado:

