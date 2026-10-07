# Pendiente vista-aliada: misión "derribar un puente" y botones de Votación / Sorteo

Anotado el 7/10/2026, después de publicar vista-aliada 1.0.12.0 (Cabotage). Es el plan para la próxima sesión.
Todo se hace en `build.py` (DarklordAV.exe / WAR3AV.RES / *.STT). Nunca se tocan Darklord.exe, DATA\War3.RES ni
Sagetext.tex. La versión que muestra el juego sigue en v.1.0.3 (`VERSION = '1.0.3'`).

Pedido del usuario (textual, resumido): *"Primero empecemos por lo mas simple> derribar puentes, incluye esa accion
como nuevo 'objetivo' en la lista de misiones para heroes. La programacion de la IA la haremos despues"* y, sobre los
programas: *"lo mejor es el sistema de ventana superpuesta, aunque si seria necesario un mecanismo de pausado, ya que
una votacion puede demandar deliberacion y tiempo ... Los botones bien pueden ir en cualquiera de las botoneras que ya
trae el juego por default."*

---

## A. Misión de héroe "derribar un puente"

**Qué tiene que pasar:** al pedir misión ("Get Quest", tecla q), entre los objetivos posibles aparece
"derribar el puente de X" (un puente enemigo o neutral alcanzable). Al razearlo el héroe, la misión se cumple con
puntaje, nivel y recompensa como las demás.

**Lo que ya se sabe**
- Tipos de misión en Sagetext.tex: entre ellos "Destroying an Enemy Site" (textos 0x3137 / 0x3166) — el modelo a copiar.
- Textos de objetivo: "%s must destroy the enemy Site of %s." (0x3707) y "%s must destroy the enemy Site %s." (0x3750).
  Otros tipos: razear ciudad / templo, capturar, saquear, matar héroe.
- Interfaz: "Get Quest" / "Show Quest" (q / Q). Errores "No Easy/Average/Hard Quests Available!".
- Puentes: casilla de clase agua, estructura `([+3]&7)==1`, sin 0x4000; existe el estado "razeado".
- Razeo de puentes ya implementado en el parche (1.0.6+, cuevas `br_*`; el efecto se aplica en `br_razeapply`).
- Razeo de sitios: cadena 0x4d5e30(sitio, jugador). La IA razea sitios en 0x40d565.

**Lo que falta averiguar (primero, enumerando todo de una pasada — regla 3)**
1. El generador de misiones: tabla de tipos, cómo elige tipo y dificultad (Easy/Average/Hard), cómo elige el
   objetivo y dónde guarda la misión en el registro del héroe (tipo + referencia al objetivo).
2. La comprobación de "misión cumplida" del tipo "destruir sitio": dónde se llama y con qué datos.
3. Recompensa y puntaje por tipo.
4. Si la misión se guarda en el SAV: un objetivo "puente" tiene que sobrevivir a guardar y cargar.
5. Cómo se arma el texto de la misión (índices de Sagetext) para sumar el texto nuevo en WAR3AV.RES.

**Plan**
- Tipo nuevo (o subtipo de "destruir sitio") cuyo objetivo es una casilla de puente (x, y).
- Elegir puentes no razeados, de dueño enemigo o sin dueño, con la misma lógica de distancia que los sitios.
- En `br_razeapply`: si el que razea es el héroe con esa misión y ese puente, marcarla cumplida por el mismo camino que
  "destruir sitio".
- Texto nuevo, p. ej. "%s must destroy the bridge at %s." — por WAR3AV.RES, no Sagetext.tex.
- Si un puente objetivo deja de existir por otra vía (lo razea otro, se reconstruye), la misión se comporta como
  "sitio ya destruido" en el original.

**Prueba (emulación desde un SAV, con controles)**
- Pedir misión con puentes disponibles → aparece el tipo puente.
- Control: sin puentes en el mapa → nunca aparece y las demás misiones salen igual que en el original.
- Razear el puente objetivo → cumplida. Controles: razear otro puente, o razearlo otro héroe → no cumplida.
- Guardar y cargar con la misión activa.

---

## B. Botones para abrir Votación y Sorteo como ventanas superpuestas

**Los programas**
- Votación: `F:\source\repos\Votacion` (PyQt5). Local, una máquina, 8 paneles de jugador sí/no.
  `config.ini [Pantalla] preferida`. Ejecutable `dist\votacion.exe` (PyInstaller, 62,9 MB).
- Sorteo: `F:\source\repos\Sorteo` (PyQt5). `dist\sorteo.exe` y `dist\sorteo\sorteo.exe` + assets.
  `abrir.vbs` → `exe.bat` → `pythonw sorteo.py`.
- Ninguno de los dos es repo git.

**Lo que ya se sabe del juego**
- Corre en ventana gracias a GOG dxcfg/ddraw.dll (`C:\Warlords3\dxcfg.ini`, presentation=windowed), así que otra
  ventana puede quedar encima sin minimizar el juego.
- El exe importa CreateProcessA (se usa en 0x4d6714) y WinExec (0x479864, lanzador de MPlayNow): lanzar un programa
  desde un botón no necesita importaciones nuevas.
- WndProc 0x479170. WM_ACTIVATEAPP en 0x4792ab solo avisa al objeto [0x4fd08c] con 0x6003.
- Minimizar: 0x4deb10 (ShowWindow SW_MINIMIZE sobre [0x589818+0x3c]). Solo se permite si la palabra
  [0x5899fa]==1 (a través de 0x4dd390). Lo llaman 0x425cff, 0x44c86e, 0x46eb49, 0x4ab11c y 0x4bd613.
  [0x5899fa] se fija en 0x4793f8, lo incrementa el código de red y se compara en 0x4dfa86: probablemente es la
  cantidad de máquinas de la partida.
  Con ventanas superpuestas no hace falta habilitar minimizar en multijugador.

**Lo que falta averiguar**
1. Las botoneras: qué barra tiene lugar libre, cómo se definen los botones (recurso en War3.RES → copia en WAR3AV.RES,
   o tabla en el exe), cómo se despacha el clic.
   - Sorteo se usa antes de la partida, así que su botón va en una pantalla previa (configuración de partida o lobby).
   - Votación va en una barra de la partida.
2. Ruta de los programas en cada PC: propuesta `C:\Warlords3\Herramientas\votacion.exe` y `...\sorteo.exe`, o una
   línea en un .ini del parche. Si no está, el botón avisa en vez de fallar callado.
3. Distribución: 50–60 MB cada uno. Como entrada aparte en `parches.txt`, o solo en la máquina de quien opera.

**Plan**
- Botón → CreateProcessA de la ruta configurada; si el programa ya está abierto, traer su ventana al frente en vez de
  abrir otra.
- Que la ventana quede encima del juego (topmost): desde el lanzador con SetWindowPos o desde el propio programa
  (Qt `WindowStaysOnTopHint`). Se decide al probar con el juego en ventana.

---

## C. Pausa mientras se vota

**Lo que ya se sabe**
- El límite de tiempo por turno existe en multijugador. Textos en Sagetext: "You may change your time limit...",
  "No Limit", "30 sec's", "1 min", "%d min's", "%d minutes have elapsed!".

**Lo que falta averiguar**
1. Dónde corre la cuenta regresiva del turno y si cada máquina la lleva por su cuenta o la manda el anfitrión.
2. Qué comando de red existe para cambiar el límite o avisar a los demás (el texto "You may change your time limit..."
   sugiere que se puede cambiar en partida).

**Plan**
- Al abrir Votación, detener la cuenta del turno (o sumarle el tiempo que esté abierta) en **todas** las máquinas.
  Al cerrarla, se reanuda.
- Si el reloj lo lleva cada máquina, hace falta un mensaje de red ("pausa / reanudar"). Si lo manda el anfitrión,
  alcanza con pausarlo ahí.
- Mientras dura la pausa, mostrar un cartel "Votación en curso" a todos, para que nadie crea que el juego se colgó.
- Prueba: dos instancias en red local (o emulación del manejador de red) con límite de 1 minuto. Abrir la votación
  más de un minuto: el turno no vence. Control: sin votación, el turno vence igual que en el original.

---

## D. Diferido: programar la IA (otra sesión)

Criterios que da el usuario por lo que ve jugar a la IA: razea sitios o ciudades (a) porque una misión del héroe se
lo pide y (b) por razones militares (cercanía o lejanía del enemigo, su debilidad o fortaleza, recursos de la zona,
terreno) o políticas (estado diplomático).

Para después:
- que los héroes de la IA tomen y cumplan misiones de puente;
- que la IA razee puentes por criterio estratégico (punto de partida: la decisión de razear sitio en 0x40d565);
- que reconstruya puentes y use Landing, Carrier y Cabotage activamente.

Los efectos pasivos de esos bonos ya valen para la IA. Las acciones nuevas (razear o reconstruir puentes, convoyes)
no las usa.

---

## Datos que hacen falta del usuario

1. Votación: ¿la maneja una sola persona en su PC (los 8 paneles en una pantalla), o cada jugador vota desde la suya?
   Hoy el programa es local, de una sola máquina.
2. ¿Quién puede apretar el botón de votación y pausar la partida: cualquier jugador, o solo el anfitrión?
3. ¿Los programas van en todas las PC (por el actualizador, 50–60 MB cada uno) o solo en la de quien los maneja?
