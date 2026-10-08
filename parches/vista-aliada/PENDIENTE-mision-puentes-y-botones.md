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

**Hecho el 7/10/2026 (vista-aliada 1.0.13.0)** — cuevas `qb_*` y `br_canon` / `br_city` en `build.py`; prueba
`prueba_misionpuente.py` (41 casos, contra el Darklord.exe original donde corresponde).
- Es el tipo 10 del original ("Destroying an Enemy Site") con objetivo = código canónico del puente
  (0x2000 + y·128 + x de su casilla menor) en lugar del índice de un sitio. Los códigos de puente no chocan con
  índices de sitio, y todo lo que lee el tipo 10 se revisó.
- Generador 0x45ec40: en dificultad Average (la única que tiene el tipo 10 en el original) suma a los sitios los
  puentes enteros con la misma distancia al héroe (3Q+14 .. 4Q+34) y el mismo filtro de dueño (0x461080). La ciudad
  dueña de un puente sale de `br_city`, copia de la regla de 0x440f60 para un sitio (la viva más cercana, primero
  las de la misma región); comprobado igual a la original en 400 mapas al azar. Sin ciudad viva, es de nadie.
- Cumplida: el botón de arrasar puente ahora pasa por 0x4955d0, como un sitio, que avisa a la misión
  (0x461a60, evento 6) antes de mandar la orden por la red. Premio, puntaje y nivel: los del original.
- Fracasada: si el puente objetivo deja de estar entero antes (lo derriba otro), igual que un sitio arrasado.
  Si ya estaba cumplida, sigue cumplida.
- Guardar y cargar: la misión activa vive en 0x55edc4 + jugador·16, dentro del bloque que guarda el SAV.
- Sin puentes que ofrecer, el generador da exactamente lo mismo que el original. Desde 1.0.21.0 vale también para
  los jugadores de la computadora (parte D, paso 1).

**Diferencias con el plan**
- Los textos ("Destroying a Bridge", "%s must destroy %s, near %s." y "%s must destroy %s.") van como cadenas del
  exe, igual que los demás textos de puentes, no en WAR3AV.RES.

**Nombres propios de los puentes (1.0.22.0)**
- Hasta 1.0.21.0 la misión decía "the bridge near Zardoria". Ya se cumplía solo con ese puente (derribar otro no
  cuenta; está probado), pero el puente no tenía nombre, y eso no es la mecánica del juego: una misión nombra el
  sitio o la ciudad. Pedido del usuario (8/10/2026): que los puentes tengan nombre como los demás sitios.
- `br_name(código, mayúscula)` arma el nombre con el generador del juego, 0x4374a0, el mismo de las ciudades y
  ruinas del mapa al azar, y con la gramática nueva `DATA\BRIDNAME.TXT`. Sus sílabas son las de
  `RANDOM\Grass\cityname.txt`, con " Bridge", " Crossing" o " Span" al final: "Holthor Bridge", "Zendoria Crossing".
- La semilla sale de la casilla menor del puente. El mismo puente, entero o derribado, da el mismo nombre desde
  cualquier casilla, en cualquier momento y en todas las máquinas. El azar de la partida ([0x500bf4], [0x500bf8]) se
  guarda y se repone. Límite conocido: el nombre depende solo de la posición, así que dos mapas con un puente en el
  mismo lugar le dan el mismo nombre.
- Se usa en los cinco lugares que decían "the bridge":
  - misión: "Hero must destroy Holthor Bridge, near Zardoria.";
  - diálogo de arrasar;
  - aviso "… is in ruins!";
  - "Rebuilding …";
  - registro de la IA.
- Sin el archivo, o con una gramática rota, vuelve a "the bridge" / "The bridge".
- Prueba: `prueba_nombrepuente.py`. Corre el generador, el azar y la lectura de archivos reales del juego; solo
  simula las llamadas a Windows. 21 casos. Falta verlo en partida.
- Hasta 1.0.20.0 la IA no recibía misiones de puente. Lo anotado acá entonces ("si un jugador humano pasa a ser de
  la computadora con una misión de puente activa, la IA lee bien el lugar pero no lo derriba") era incompleto: el
  camino de la IA (0x40d963 y 0x40d450) además leía la tabla de sitios con el código del puente como índice, fuera
  de rango. Quedó resuelto en la parte D, paso 1.

---

## B. Botones para abrir Votación y Sorteo como ventanas superpuestas

**Los programas**
- Votación: `F:\source\repos\Votacion` (PyQt5). Local, una máquina, 8 paneles de jugador sí/no.
  `config.ini [Pantalla] preferida`. Ejecutable `dist\votacion.exe` (PyInstaller, 62,9 MB).
- Sorteo: `F:\source\repos\Sorteo` (tkinter + PIL, no PyQt5). `dist\sorteo.exe` y `dist\sorteo\sorteo.exe` + assets.
  `abrir.vbs` → `exe.bat` → `pythonw sorteo.py`.
- Los dos son repos git desde el 7/10/2026 (ver "Hecho el 7/10/2026: versión en el título", al final).

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

**Hecho el 7/10/2026 (vista-aliada 1.0.14.0, Votación 1.1.0, Sorteo 1.1.0)**

En el juego (`build.py`, cuevas `tl_*`; prueba `prueba_botones.py`, emulada, con controles):
- **Votación:** línea nueva "Votacion" en el menú de partida (diálogo 35), debajo de "Chat Mode"; las demás líneas se
  corren 16 px. Solo el anfitrión (máquina 0, también en partida de un jugador) la tiene activa; en las otras PC sale
  gris y no hace nada. 1.0.15.0: el menú al abrirse (0x4bce20) no habilitaba la zona (0x4dcec0(0x1a, 0|2)) y por eso
  no se resaltaba ni respondía al clic (`tl_menuinit`).
- **Sorteo:** botón "Draw Lots" (id 97, copia del botón Chat id 80) en la pantalla de preparación (diálogo 7),
  arriba de Chat, en (6, 430). Deshabilitado fuera del anfitrión. 1.0.15.0: en vez de la moneda de BUTT_STD lleva el
  ícono del programa Sorteo (`sorteo_icono.png`, 16×16) sobre el marco de la moneda: hoja nueva
  `SETS\Fantasy\sorteo.pcx` (20×80, 4 cuadros: normal, apretado, deshabilitado, puntero encima; paleta de BUTT_STD),
  archivo 166 de la tabla de archivos del RES. 1.0.16.0: a pedido del usuario ("muy pequeño, al menos el triple"),
  64×60 con el ícono de 64 px entero y fondo transparente (índice 11), abajo a la derecha en (567, 409), junto al
  murciélago. En la esquina de antes (6, 430) no entra: entre el borde y el panel del 4º jugador hay ~30 px, y a 64
  taparía el marco y el retrato (control 4 en (48, 409)). Chat (80) aparece ahí debajo solo en red (0x46f321:
  `0x4dd390() > 1`). El usuario eligió dejarlo grande junto al murciélago. Los estados van apilados cada `alto` píxeles, como los botones 32×33 de
  BUTT_STD.
- Al apretarlos, el anfitrión manda por red el paquete 0x2a0 (abrir; dato = 0 votación, 1 sorteo) con 0x4dd3b0, que
  también vuelve a la propia máquina. Cada PC, al recibirlo (gancho en el receptor 0x4b6a22, solo si lo manda la
  máquina 0), abre `Herramientas\votacion.exe` / `sorteo.exe`: el anfitrión con `--operador`; las demás con
  `--espectador <8 cifras>`, en 1 los bandos activos, humanos y de esa PC. Si no está el programa, un cartel
  "No se pudo abrir Herramientas\...".
- Estado: cada 250 ms (gancho en la función ociosa 0x4dea40) el anfitrión mueve `Herramientas\<prog>.op` a `.env`, lo
  lee (hasta 255 bytes) y lo manda como paquete 0x2a1; cada PC lo escribe en `Herramientas\<prog>.ver` (vía `.vtmp` y
  mover, para no dejarlo a medias). Un exe sin el parche ignora los tipos mayores que 0x209.
- No toca la simulación: no cambia nada del estado de la partida, solo archivos de `Herramientas\`.

En los programas (cada uno con `prueba_partida.py`, y probados compilados lanzándolos desde otra carpeta):
- Votación: `VOT <sesión> <libre|auto|cerrado> <n.º votación automática> <n.º reset> <8 votos s/n/->`.
- Sorteo: `SOR <sesión> <libre|sorteando|resultado|cerrado> <evento> <número 1-8 o - de cada bando>`.
- Operador: escribe `.op` en cada cambio y cada 3 s; al cerrar escribe "cerrado". Espectador: lee `.ver` cada 300 ms,
  copia votos/números, reloj y tambores; botones sin clic (salvo el de monitor en Votación); sus bandos con marco
  dorado; se cierra con el "cerrado" de su sesión. Ventanas encima de todo, una sola por PC (mutex; si ya está
  abierta, se la trae al frente). Sin argumentos, funcionan como antes.
- Sorteo: cursores e ícono ahora se buscan junto al programa (`resource_path`), no en la carpeta actual.

**Lo que falta de B**
1. **Instalar los programas en `C:\Warlords3\Herramientas\`** de cada PC: entrada en `parches.txt` del actualizador.
   Los repos Votacion y Sorteo no tienen remoto ni releases todavía; hace falta uno para publicar los exe.
   Hasta entonces, el botón muestra el cartel "No se pudo abrir...".
2. **Prueba real en red** (dos PC con DarklordAV.exe): no se pudo hacer acá. Lo emulado y probado: menú, botón,
   paquetes, archivos, y los dos programas con archivos simulados. Sin probar: el viaje real por la red y que la
   ventana quede encima del juego en ventana (GOG dxcfg).

---

## C. Pausa mientras se vota

**Estado al 7/10/2026 (vista-aliada 1.0.17.0):** hecho y probado en emulación (`prueba_pausa.py`, 0 MAL). Falta la
prueba real (ver abajo). Origen: el usuario probó "Votacion" en un jugador: *"arranca y se ve bien sobre la pantalla del
juego, pero creo que la partida no queda pausada"*.

**Lo medido en el código del juego (no en una partida real)**
- La cuenta regresiva del turno la lleva **cada PC por su cuenta**, con su propio reloj: vencimiento en `[0x4ff7a8]`
  (se fija al empezar el turno en 0x4c0f70 = ahora + límite·30 s; `[0x53c38f] >> 3` = límite en medios minutos).
  Al vencer, la PC del jugador de turno manda el fin de turno (0x4c0fe0 en el bucle principal; 0x4c10c0 / 0x4c1250
  dentro de los diálogos, con 20 s de gracia en `[0x5885cc]`). El anfitrión no manda el reloj.
- El límite se puede cambiar en partida (diálogo 0x46b640), pero toca opciones de la partida: no se usó.
- Partida por minutos: fin en `[0x5032f8+0x4c]` (-1 si no hay), también con el reloj de cada PC.
- Teclado y mouse llegan solo por mensajes de Windows (no hay DirectInput ni GetAsyncKeyState); el juego tiene 6
  bucles que llaman a DispatchMessageA.
- Los turnos de la IA no tienen reloj: siguen corriendo durante la pausa. Así queda: no hace falta pausarlos
  (usuario, 7/10/2026; ver D).

**Qué hace "pausada" (las dos cosas: reloj y órdenes)**
- La orden de abrir la Votación (TL_OPEN 0, que ya llegaba a todas las PC) pausa; el estado que manda el anfitrión
  cada 3 s (TL_STATE) la mantiene, y "cerrado" la levanta. Si el estado deja de llegar 60 s (programa colgado o
  matado), cada PC se reanuda sola. Si el anfitrión no tiene el programa, manda "cerrado" enseguida.
- En pausa, cada PC corre hacia adelante el vencimiento del turno, la gracia y el fin de la partida por minutos:
  el reloj en pantalla queda quieto.
- En pausa, el despacho de mensajes descarta teclas y botones del mouse (el movimiento pasa). No se deshabilita la
  ventana: al cerrarse la Votación, Windows no le devolvería el foco.
- Aviso en pantalla "Votacion en curso: partida en pausa" (renglón de mensajes del juego, 0x4c2790) mientras dure.
- Sorteo no pausa (se usa antes de la partida). Un estado sin orden de abrir (un .op viejo) no pausa, y al abrir se
  borran .op y .env viejos.
- Nada de esto viaja como estado de partida ni se guarda: no puede desincronizar turnos.

**Sin verificar (no se puede desde acá)**
1. Partida real: que el aviso se vea donde se dibujan los mensajes del juego, y que con la Votación encima no quede
   ningún clic que pase al juego.
2. Red real con dos PC: que todas pausen y reanuden juntas (la diferencia es la demora de red, décimas de segundo).
3. Prueba sugerida al usuario: límite de 1 minuto, abrir la Votación más de un minuto y cerrarla; el turno tiene que
   seguir con el tiempo que le quedaba. Control: sin votación vence al minuto, como siempre.

**Confirmado por el usuario en partida real (7/10/2026, 1.0.17.0):** con límite de 1 minuto el turno vence a tiempo
sin votación (control), y con la votación abierta la partida queda en pausa; el cartel se ve bien. Falta la red real
con dos PC (punto 2).

---

## E. Resultado de la votación en el "Events Report"

**Estado al 7/10/2026 (vista-aliada 1.0.18.0):** hecho y probado en emulación (`prueba_votoinforme.py`, 0 MAL).
Falta verlo en una partida real (ver abajo). Pedido del usuario (7/10/2026): que el reporte de eventos diga, por
ejemplo, "Resultados votacion: 5 por el SI, 3 por el NO".

**Lo medido en el código (Darklord.exe original)**
- Registro de suceso, 0x1c bytes: +0 tipo (que es también la prioridad), +2 jugador, +4 parámetro, +6 nombre[16],
  +0x16/+0x18/+0x1a tres words. (La nota anterior decía "prioridad, jugador, tipo": el tipo y la prioridad son el
  mismo campo.) Alta: 0x498910(tipo, jugador, parámetro, nombre, w1, w2, w3); quedan los 2 de mayor tipo por jugador.
- Ronda en curso: tabla 0x572788 (8 jugadores x 2). En las partidas en red guardadas están los 8 bandos activos: no
  hay ranuras libres, por eso las votaciones van en una tabla aparte.
- Fin de ronda 0x4989d0: agrega a HISTORY.DAT cabecera 0x48 (+0 tamaño del bloque, +0x44 cantidad de renglones),
  dueños de ciudades y renglones; después 0x4988d0 vacía la tabla (también al empezar partida, desde 0x42de63).
- Informe 0x499450: rondas pasadas desde HISTORY.DAT (por tamaño y cantidad de cada cabecera) y la actual desde la
  tabla. Lo usan el Events Report (0x4b39d8) y otro reporte (0x46b799) que solo cuenta el tipo 0xe del jugador.
- Dibujo 0x4b3ec0: hasta 11 renglones por ronda, en el orden del búfer; nada en la ronda 1. Renglón 0x4b4110:
  escudo del jugador y `switch` por tipo (0..0x12); con un tipo mayor el original solo dibuja el escudo.
- .SAV: 0x439a00 guarda (HISTORY.DAT y la tabla en 0x498c40) y termina con 0x18 bytes de 0x4fae68; 0x439e..
  carga y tolera que falte el final. El original ignora lo que sobre después.

**Qué hace**
- Al recibir un estado de la Votación (antes de pz_state, solo con la orden de abrir dada): si cambió la sesión,
  descarta lo pendiente; si cambió el número de reinicios, anota lo pendiente; guarda los conteos de s y n si hay
  al menos un voto; con "cerrado", anota. O sea: cada votación con votos se anota cuando se reinicia o cuando se
  cierra el programa. El cierre de emergencia (sesión "-") y un programa muerto sin cerrar no anotan nada.
- Anotar = un renglón tipo 0x13, jugador 8 (desde 1.0.19.0, el bando que la abrió; ver abajo), SI en +0x16, NO en +0x18, en `vt_tab` (hasta 8 por ronda).
- Al terminar la ronda, esos renglones se escriben en HISTORY.DAT **antes** que los sucesos de la ronda (para que
  entren en los 11 renglones), con el tamaño y la cantidad de la cabecera corregidos; el informe los suma también a
  la ronda en curso. El renglón se dibujaba sin escudo, donde va el texto de los demás (con escudo desde 1.0.19.0).
- La tabla de la ronda en curso se guarda al final del .SAV ('VOTA', cantidad, tabla) y se carga si está; un .SAV
  viejo o roto la carga vacía.
- Sin votaciones, HISTORY.DAT y el informe quedan idénticos byte a byte a los del original (probado).

**Límites aceptados**
- La ronda 1 no se muestra nunca (así es el juego).
- Con muchos sucesos, las votaciones (que van primero) pueden dejar afuera sucesos de la ronda: se ven 11 renglones.
- Si una votación se cierra justo en el cambio de ronda, una PC puede anotarla en una ronda y otra en la siguiente.
- HISTORY.DAT con renglones 0x13 abierto con el Darklord.exe original: ese renglón sale solo como un escudo.

**Verificado por el usuario en partida (7/10/2026, 1.0.18.0):** el renglón sale bien ("Resultados votacion: 4 por
el SI, 4 por el NO"). Observó que el texto parecía corrido a la derecha respecto de los demás. En realidad está en
la misma x que el texto de los demás: lo que faltaba era el escudo a su izquierda.

**1.0.19.0: el escudo de quien abrió la votación.** Solo el anfitrión abre la Votación (tl_sendopen chequea
0x4dd3a0) y la orden (TL_OPEN) no dice qué bando la abrió. Por eso el dueño es el primer bando activo, humano
(word +0xe2 == -1) y de la máquina 0 (byte +3) al recibir la orden de abrir (`vt_open`, desde tr_open). Todas las PC
ven la misma tabla de bandos, así que todas calculan el mismo. Queda fijo en `vt_owner` para los reinicios y el
cierre de esa sesión. vt_commit lo pone en +2. vt_line dibuja el escudo 0x69+jugador como un suceso común, y para un
jugador fuera de 0..7 no dibuja escudo; es el caso de los renglones con jugador 8 de los .SAV de 1.0.18.0, y de una
anfitriona sin humanos. Probado en `prueba_votoinforme.py`: el escudo es idéntico al de un suceso común del mismo
bando en el original, con controles (otra máquina, IA, bando inactivo, cambio después de abrir).

**Sin verificar (no se puede desde acá)**
1. Partida real con 1.0.19.0: que el renglón de la votación lleve el escudo del anfitrión.

## F. Título del menú principal como imagen (1.0.19.0)

Pedido del usuario (7/10/2026): reemplazar el texto del parche en la primera pantalla por `titulo.pcx` (lo dejó
en `DarkCompare\assets\`; se incorporó a `parches\vista-aliada\titulo.pcx`).

- El texto era el control 19 del diálogo 1 (Sagetext (1,0), fuente 6). Ahora queda vacío (TEXTS en build.py).
- La imagen va pintada en los fondos. Hay tres según la resolución: archivo 1 `picts\startup` (640x480), 138
  `startup1` (800x600) y 139 `startup2` (1024x768), con el diálogo corrido (0,0), (80,60) y (192,144). En WAR3AV.RES
  esos registros pasan a `picts\startav`, `startav1` y `startav2`, archivos nuevos que build.py arma desde los
  originales; no se toca ningún archivo original.
- Va centrada en x 322 del diálogo, arriba (y 5), con 56 de alto. La transparencia sale del dorado sobre blanco,
  y el color se lleva a la paleta compartida de los tres fondos.
- Medido: los tres fondos solo cambian en el recuadro del título (x 129..515, y 5..59 del diálogo). El marco está
  en la misma posición en los tres, pero sus píxeles no son idénticos (~8% difiere): el control es de alineación.
- Sin verificar: verlo en el juego en las tres resoluciones.
- Usuario (7/10/2026): el título de 1.0.19.0 "quedó muy bien" y el escudo de la votación se ve mejor. Pidió la
  imagen nueva `DarkCompare\assets\Imagen2.pcx` (537x91, degradé vertical de amarillo pálido a naranja, sin
  sombra), que reemplaza a `titulo.pcx` en el repo (1.0.20.0). Con ese degradé, la transparencia anterior
  ((R - B) / 170) dejaba casi transparentes los brillos de arriba. Ahora usa el color lleno de cada fila: ver
  build.py. Va a 60 de alto desde y 3 (360 de ancho; recuadro cambiado x 142..501, y 3..62 del diálogo).

## D. Programar la IA

Criterios que da el usuario por lo que ve jugar a la IA: razea sitios o ciudades (a) porque una misión del héroe se
lo pide y (b) por razones militares (cercanía o lejanía del enemigo, su debilidad o fortaleza, recursos de la zona,
terreno) o políticas (estado diplomático).

Orden de trabajo:
1. que los héroes de la IA tomen y cumplan misiones de puente — **hecho, 1.0.21.0**;
2. que la IA razee puentes por criterio estratégico — **hecho, 1.0.23.0**;
3. que reconstruya puentes y use Landing, Carrier y Cabotage activamente.

Los efectos pasivos de esos bonos ya valen para la IA. Las acciones nuevas (razear por su cuenta o reconstruir
puentes, convoyes) no las usa.

**Lo averiguado de la IA (7/10/2026)**
- Despachador de metas del grupo (~0x40cc3f): meta = código/1000, objetivo = código%1000; la meta sale de 0x41eda0
  (o de 0x41cb10). Tabla 0x40d02c: 1 formar en ciudad 0x40db40; 2 ruina 0x40d050; 3 ciudad neutral 0x40d9f0(t,3);
  4 objeto 0x40d5b0; 5 héroe 0x40dd00; 6 misión 0x40d6d0; 7 ciudad enemiga 0x40d9f0(t,7); 8 sitio 0x40d450(t,0);
  9 reconstruir 0x40dbf0.
- **Corrección (8/10/2026): la IA original sí arrasa por criterio propio.** Lo anotado acá antes ("solo arrasa
  sitios por misión; el paso 2 es lógica nueva") era falso, y contradecía lo que el usuario ya había dicho arriba
  por haberlo visto jugar: la computadora arrasa por conveniencia, no solo por misiones, y aprovecha descuidos
  (una ciudad vacía) aun de quien no es su enemigo. El error fue tomar por ausente lo que no estaba en los caminos
  que miré. La lógica existe y es la que hay que descifrar y extender a los puentes:
  - **Arrasar una ciudad recién tomada: 0x41f4b0(ciudad, bandera)**, llamada en 0x4c5296 al capturar (línea de
    depuración "Attack City ... Raze [%d]"; ahí raze = [esp+0x1e] sale de la misión si la hay, y si no de
    0x41f4b0; 0x4b9510(ciudad, jugador, ...) la aplica). **Confirmada emulándola (8/10/2026)**; lo que sigue ya
    tiene las correcciones de esa emulación:
    - r = 0x4deb20(1, 20, 0). Si [0x53c393] & 6 == 0 (opción de arrasar apagada) → no.
    - c = byte [0x561ef9 + p·0x49a], p = [0x4fb0ec]: **temperamento arrasador** del jugador, 0..4. Lo inicia
      0x472568; 0x41f410 lo pone en 1 con 1 en 20 si todos los vivos tienen 0; 0x41e290 también lo usa (30 vs 15).
    - bandera = (word [0x54fe6c + líder·0x1c] & 0x3c00) >> 10, líder = [0x56ea92 + p·0x4f0]: el **grupo de IA**
      al que pertenece el líder (0 = ninguno, es decir, la ciudad no la tomó un grupo con plan). Si c == 0 y
      bandera == 0 → no.
    - si = (c == 0 ? −2 : 0); +1 si hay bandera y la ciudad no era neutral (dueño byte [0x537ed1 + ciudad·0xde]
      != 8; el registro de ciudad mide 0xde, no 0x76); +1 si su valor 0x4d5bd0(ciudad) < 150 (producción de sus 4
      ranuras / 3).
    - Vecinas: las 12 de [0x564ea6 + (ciudad·12 + i)·14] (0x50 = ninguna), distancia en el byte +4; solo vivas a
      distancia 1..30, peso 2 si está a menos de 15, si no 1. **Bug del original:** la distancia se lee de la fila
      de la vecina, no de la de la ciudad tomada (la emulación lo confirma); no se tocó. propias += peso si son mías; enemigas += peso si el
      dueño no es neutral y 0x49c1c0(dueño) dice hostil. si = si − propias + enemigas.
    - +1 si tengo más de 5 ciudades, +1 más si más de 15.
    - Si c es 1..3 y r == 1 → c + 1. Si r ≥ 19 → no. **Arrasa si c + si ≥ 5.**
    - En criollo: arrasa la ciudad que no le rinde, rodeada de enemigos y lejos de lo propio, con más ganas si ya
      es grande y según su temperamento, con algo de azar.
  - Sitios: el único camino encontrado de la IA a la orden de arrasar sitio (0x4b9550) es el de la misión
    (0x40d450 modo 10, por 0x40d963; la meta 8, evaluador de sitios 0x41d2c0, llama con modo 0 y solo visita).
    Los otros llamadores son el truco "Burn baby burn" (0x456431) y la red (0x4b7f02). Si el usuario ve a la IA
    arrasar sitios sin misión, hay otro camino que todavía no encontré: no darlo por inexistente.
  - Las cadenas "Raze Site/Raze Cy/Occupy Cy Cost" de 0x435b..0x435e son del evaluador de costo de misiones, no de
    la estrategia.
- Estado de trabajo de la IA: [0x5020d4] = plan del grupo (+6 meta, +8 objetivo, +0xc grupo); [0x5020d0] =
  ranura; [0x4fb0ec] = jugador de la IA. Registro de depuración: sprintf [0x5a9bec] a 0x564d90 + 0x427520.
- 0x4974a0 (distancia) es euclídea truncada: la diagonal vale 1. 0x40e400(sx,sy,x,y): a distancia 1 ataca al que
  ocupa (x,y) solo si es humano (o [0x560e52] == 5), declarando la guerra; sin nadie, o propio, devuelve 0.
- 0x4a65d0(jugador,x,y): distancia en el mapa por jugador [0x587168+p*4][x*160+y], 0 = sin camino; lo llena
  0x4a6920(ranura). La usa el evaluador de misiones 0x41e8a0 (por 0x435fd0) para decidir si la persigue.
- "Quest City" ([0x561efe + jugador*0x49a]): bug del original, guarda el byte bajo del objetivo de cualquier misión
  (también de sitio) como si fuera una ciudad. Con un puente pasa lo mismo que con un sitio; no se tocó.

**Paso 1 hecho (1.0.21.0).** qb_gen ya no se limita a humanos. ai_brname (0x40d963) escribe el nombre del puente
en el registro de la IA (desde 1.0.22.0; antes "the bridge"). ai_brq (0x40d450, código ≥ 0x2000): elige la cabecera más cercana (vecina de una casilla del
puente; no puente, no agua, no montaña sin camino), va como a un sitio y, parado ahí, derriba con 0x4955d0 (cumple
la misión). Con ejércitos ajenos encima ataca con 0x40e400 y no derriba; con propios encima espera. Prueba:
`prueba_iapuente.py` (29 casos; los sitios comparados con el original). Falta verlo en partida: que el evaluador
0x41e8a0 elija perseguir la misión depende de 0x4a65d0 en la casilla del puente, que no se emuló.

**Paso 2 hecho (1.0.23.0): la IA derriba puentes por la misma cuenta que 0x41f4b0.**
- Momento: al terminar de mover una pila de la IA, en 0x4c4d3a (final de 0x4c4a10(x, y, bandera), justo antes de
  la orden 0x146 de fin de pila). Ahí entra ai_brraze. Tiene que ser antes: 0x146 (0x4b9020 → 0x4dd3b0 → 0x4df3c0
  → 0x4dfa10) se aplica en el acto por 0x4df400 y vacía la pila (0x485c70 pone 0x56ea90/92 en 0). Así la orden de
  derribar (0x18d) sale por la red antes que la de fin de pila, en el mismo orden en todas las máquinas.
- Condiciones (todas): turno de la IA ([0x4fb0ec] == [0x537ce8]), jugador no humano, opción de arrasar encendida
  ([0x53c393] & 6), pila con líder vivo; bandera (grupo del líder) o temperamento distintos de 0, como el original;
  el líder parado en la cabecera de un puente intacto (br_find); ningún ejército, ni propio, sobre el puente; el
  destino de la pila no está a 1 casilla del puente (lo va a cruzar o es una misión) ni el puente queda "adelante"
  (alguna casilla del puente más cerca del destino que la pila, distancia de rey); la ciudad dueña del puente
  (br_city) no es propia ni de alguien no hostil (aliado o en paz): si es neutral vale, sin el +1 de bandera.
- Cuenta, igual que 0x41f4b0 pero desde la casilla canónica del puente: si = (c == 0 ? −2 : 0) + 1 (el puente no
  produce: equivale a valor < 150); +1 si hay bandera y la ciudad dueña no es neutral; las 12 ciudades vivas más
  cercanas a distancia 1..30 (0x4974a0), peso 2 si < 15, propias restan, hostiles suman; +1 con más de 5 ciudades
  propias, +1 más con más de 15; r = 0x4deb20(1, 20, 0), y c + 1 si c es 1..3 y r == 1; r ≥ 19 → no; **derriba si
  c + si ≥ 5**. El azar se pide solo cuando el puente ya pasó todas las condiciones, como en el original.
- Derriba con 0x4955d0(código) y pausa 0x4275b0(2000) para que se vea.
- Prueba: `prueba_iarazea.py` (62 controles: ~45 casos armados, 3000 al azar contra un modelo en Python, las
  rutinas reales 0x4974a0 y 0x49c1c0 emuladas). **Falta verlo en partida.**

Defectos encontrados y corregidos en el mismo paso:
- **ai_brq leía el líder tarde.** Al llegar a la cabecera, el derribo de la misión pasaba por 0x4955d0, que lee el
  líder de [0x56ea92] recién ahí; si la pila ya se había vaciado por 0x146 la misión podía no acreditarse. Ahora
  guarda el líder al entrar (ai_brlead), como el original en [esp+0x12], y llama 0x461a60(6, líder, 0, 0, código, 1)
  y 0x4b9550(código, jugador) como el camino de Raze Site. `prueba_iapuente.py` tiene el caso de pila vaciada.
- **0x435d53 (evaluador de costo de misiones, "Raze Site") con código de puente leía fuera de la imagen** en
  1.0.21.0 y 1.0.22.0: buscaba el sitio en 0x55acb6 + código·150 (registro de sitio de 150 bytes), unos 0x6b6704;
  podía colgar el juego o leer basura cuando la IA evaluaba una misión de puente. qb_ailoc3 ahora saca x, y del
  código del puente.

Lo que queda como en el original: con temperamento 0 la IA no acepta misiones de arrasar, tampoco de puente
("Not Accepted"). Quest City sigue con su bug (ver arriba).

**Próximo paso (3):** que la IA reconstruya puentes y use Landing, Carrier y Cabotage. Igual que en el paso 2,
empezar por la lógica que el juego ya tiene: la meta 9 (reconstruir, 0x40dbf0) y cómo la IA elige embarcar.

Pausar los turnos de la IA **no se hace** (decisión del usuario, 7/10/2026): durante esos turnos nadie propone una
votación, porque todos miran lo que hace el sistema. Además, el Reglamento del Ranking del Clan, que es el que
establece la votación, no prevé pausar los movimientos del sistema.

## G. Para otro momento: el actualizador

Pedido del usuario (7/10/2026), sin fecha: revisar el actualizador del juego y adaptarlo a todo lo que cambió en el
parche y en los dos programas complementarios (Votacion y Sorteo). Hoy los dos programas no tienen remoto ni
releases, así que el actualizador no los puede instalar (ver B).

---

## Respuestas del usuario (7/10/2026) y decisión técnica

Respuestas (resumidas):
1. Votación: todos ven la ventana; cada PC tiene el programa en una subcarpeta de Warlords. La opera uno solo; lo
   importante es que cada jugador vea si su voto quedó cargado por sí o por no.
2. Cualquier jugador puede pedir votación y pausa. Si eso puede desestabilizar la partida, el jugador solo anuncia el
   pedido y la activa el anfitrión.
3. Los programas van en todas las PC por el actualizador. Para él, **el mayor riesgo es que se desincronice la partida
   y se pierdan turnos**; el cómo queda a mi criterio (compartir pantalla por GameRanger, o que cada PC abra su copia a
   pedido del anfitrión vía Warlords).

Decisión:
- **Cada PC abre su propia copia, a pedido del anfitrión.** Compartir pantalla por GameRanger depende de un tercero
  que el parche no controla ni puede verificar.
- **Una sola autoridad: el anfitrión.** Cualquier jugador aprieta "Pedir votación"; eso solo le avisa al anfitrión
  ("X pide votación"). El anfitrión abre la votación y la pausa. Nunca dos máquinas cambian el estado a la vez.
- **Nada de lo nuevo viaja como estado de partida.** Los pedidos, la apertura y el estado de los votos viajan por un
  canal que no forma parte de la simulación (el chat o los mensajes entre jugadores del propio juego, a confirmar),
  así no hay nada que pueda desincronizar turnos. La pausa, por el mecanismo que el juego ya tenga para cambiar el
  límite de tiempo en partida, si existe (ver C): ese camino ya viene sincronizado por el original.
- Si el juego no tiene un canal de mensajes en partida que sirva, se reconsidera antes de tocar el protocolo de red,
  y se le explica al usuario.

Cambios en los programas (no son repos git; se los versiona primero):
- Votación: un modo **operador** (el del anfitrión, el actual) que publica el estado de los 8 paneles, y un modo
  **espectador** (los demás) que lo muestra de solo lectura, con el voto de cada uno resaltado.
- Sorteo: igual, el anfitrión sortea y los demás ven el resultado en vivo.
- El exe parcheado hace de puente: lee el estado que escribe el programa del anfitrión, lo manda por el canal de
  mensajes, y en cada PC lo deja donde lo lee su copia en modo espectador.

Distribución: entrada nueva en `parches.txt` que instala ambos en una subcarpeta de `C:\Warlords3`
(p. ej. `Herramientas\`), con config.ini por PC.

Lo primero a averiguar en la sesión que toque B/C:
1. ¿Hay chat o mensajes entre jugadores en partida y en la pantalla previa? Formato, largo máximo, si el anfitrión
   los reenvía.
2. ¿El límite de tiempo se puede cambiar en partida, y quién lo cambia?
3. ¿Dónde se ve "quién es el anfitrión" en el exe?

## Segunda ronda de respuestas (7/10/2026)

- El juego tiene chat en partida ("rudimentario y básico, pero existe"): es el canal candidato.
- La orden de abrir votación o sorteo sale del Warlords del anfitrión hacia los demás. Los jugadores hablan por audio
  (WhatsApp, Discord) durante la partida, así que **el pedido de votación no hace falta implementarlo**: no hay botón
  "Pedir votación". El problema real es que hasta ahora solo veía el sorteo o la votación quien corría el programa.
- Para los no anfitriones, modo solo lectura (ven, no ejecutan). Hay permiso pleno para modificar ambos programas.
- La integración con el actualizador, más adelante.

## Hecho el 7/10/2026: versión en el título

- Votacion y Sorteo son repos git desde hoy (solo locales, sin remoto todavía; hará falta uno con releases para
  distribuirlos por el actualizador). `VERSION = "1.0.0"` en `votacion.py` / `sorteo.py`; el título muestra
  "Sistema de Votación v1.0.0" y "Sorteo v1.0.0" (verificado leyendo el título de la ventana del exe compilado).
- `compilar.ps1` en cada repo: Votación con `py -3.14` (PyQt5 5.15.11 instalado ahí), Sorteo con `py -3.10`.
  Chequea el código de salida y que el exe se haya regenerado.
- `hooks/pre-commit` (core.hooksPath hooks): bloquea cambios en el .py, `assets/` o el .spec sin subir VERSION; recuerda
  correr `compilar.ps1`. Probado en caliente en un clon: bloquea .py y asset sin VERSION, pasa con VERSION y con otro
  archivo (control).
- Ojo para lanzarlo desde el juego: Sorteo carga cursores e ícono con rutas relativas al directorio actual
  (`@assets/flecha.cur`, `assets/icono.ico`); hay que lanzarlo con el directorio de trabajo en su carpeta (o pasar
  esas rutas a `resource_path`). `sorteo.spec` genera además `dist\sorteo\sorteo.exe`.
