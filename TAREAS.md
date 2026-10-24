# Tareas del usuario

Cada tarea tiene un número fijo: no cambia aunque se resuelva. Las nuevas toman el número siguiente (hoy, la 40).
`- [ ]` pendiente, `- [x]` cumplida; las cumplidas pasan a «Hecho» con su fecha y resultado.
Esta es la lista completa. Las del Puente Warlords están en `puente-warlords\TAREAS.md` y figuran abajo en el
orden sugerido como «Puente 1», «Puente 2». El repo Votacion no tiene tareas propias: las de la Votación y el
Sorteo están acá (tarea 18).

## Orden sugerido
- **Tarea 39** (Defender bloquea el Actualizador): primero, ya mismo.
- **Tarea 38** (guardada con personalidades): cuando puedas; la ronda nueva espera a eso.
1. **Tarea 36** (revisar el borrador del Manual): ya la estás haciendo.
2. **Tarea 37** (el Manual llega con la opción 9): la próxima vez que alguien del clan actualice.
3. **Tarea 27** (misión de la trampa, con dos jugadores humanos).
4. En la próxima partida en red: **tarea 18** (Votación y Sorteo) y **Puente 7** (botón «Copiar IP»).

# Pendientes

- [ ] **39.** Pedirle a Microsoft que deje de marcar el Actualizador como virus (24/10/2026)
En la PC de tu amigo, Edge/Defender bloquea `Actualizador-v.1.0.13.0.exe.zip` con «Se ha detectado un virus».
Es un falso positivo: lo corrige Microsoft, no nosotros. El envío lo hacés vos desde tu PC; tu amigo solo
tiene que hacer el paso 6 (y el 1, si puede).
1. Opcional: pedile a tu amigo que abra **Seguridad de Windows → Protección antivirus y contra amenazas → Historial de protección**
   y te pase el **nombre de la amenaza** (algo como `Trojan:Win32/...`).
   La foto de las descargas de Edge no lo muestra. Si no lo consigue, seguí igual.
2. En tu PC, tomá el `.exe` de `F:\source\repos\actualizador-warlords\Actualizador-v.1.0.13.0.exe`.
3. Entrá a https://www.microsoft.com/wdsi/filesubmission, iniciá sesión con tu cuenta Microsoft y elegí
   **Software developer**.
4. Producto: **Microsoft Defender Antivirus**. Subí el `.exe`. Marcá **Incorrectly detected as malware**.
   En «Detection name» poné el nombre del paso 1, o dejalo vacío. En comentarios: «Updater for the game Warlords III, made by
   me, downloads game files from GitHub. False positive.»
5. Anotá abajo el número de envío. Microsoft responde por mail, en general en 1 a 3 días.
6. Cuando digan que está corregido, avisale a tu amigo que en su PC vaya a Seguridad de Windows → Actualizaciones de protección
   → **Buscar actualizaciones**, y vuelva a bajar el zip.
Resultado:

- [ ] **38.** IA: guardada de Hexagon con personalidades distintas (24/10/2026)
Para la ronda nueva: todo igual en los 8 colores salvo la personalidad.
1. Abrí el juego y empezá una partida nueva en **Hexagon** con los **8 colores** en IA, **sin alianzas**, el
   **mismo bando** (.PGS) en todos, con **«AI Chooses Personalities» apagado** y límite de **4 puntos**.
2. A cada color asignale sus 4 puntos según el perfil que quieras (blanco: poder de ataque; amarillo: movimiento;
   naranja: héroes y mercenarios baratos; y los demás).
3. Guardala en el turno 1 como **Tanda_hex_personalidad**.
4. Anotá abajo, color por color, los puntos exactos que le diste (por ejemplo «blanco: Very Strong + Fast»).
Resultado:

- [ ] **37.** Comprobar que la opción 9 instala el Manual (24/10/2026)
Desde vista-aliada 1.0.69.0 (ya publicada), el parche instala también el Manual de uso.
1. En otra PC del clan, abrí el Actualizador y elegí la opción **9** → vista-aliada.
2. Fijate que aparezca `C:\Warlords3\Manual-Era-de-Alianzas.pdf` y que abra.
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


- [ ] **18.** Votación y Sorteo en la PC de Nico: datos de su instalación (17/10/2026)
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


# Hecho

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
