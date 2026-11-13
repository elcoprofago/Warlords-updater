# Tareas del usuario

Cada tarea tiene un número fijo: no cambia aunque se resuelva. Las nuevas toman el número siguiente (hoy, la 205).
`- [ ]` pendiente, `- [x]` cumplida; las cumplidas pasan a «Hecho» con su fecha y resultado.
Esta es la lista completa. Las del Puente Warlords están en `puente-warlords\TAREAS.md` y figuran abajo en el
orden sugerido como «Puente 1», «Puente 2». El repo Votacion no tiene tareas propias: las de la Votación y el
Sorteo están acá (tarea 18).

## Orden sugerido
1. Con la notebook: **Puente 10** (net.ini) y **Puente 11** («Anfitrión» con la partida vieja abierta).
2. **Puente 7** (botón «Copiar IP», con lo que tiene que anotar Nico): en la próxima partida con él.
3. **Tarea 36** (revisar el borrador del Manual) y **tarea 42** (leer el anexo de la IA).
4. **Tarea 27** (misión de la trampa, con dos jugadores humanos).

# Pendientes

- [ ] **204.** Simulador de combate 1.0.43.0 (13/11/2026). Abrir Historial → Stats: las formaciones de la leyenda dicen solo el nombre de la unidad como se la conoce en el juego (por ejemplo «5 Archers», no «archers — Archers»), con cualquiera de los dos órdenes de los desplegables. Anotar lo que no coincida.
- [ ] **203.** Simulador de combate 1.0.42.0 (13/11/2026). Los botones tienen el estilo de INICIAR COMBATE (letra blanca en negrita con sombra) y el fondo de los escudos que pasaste: Carpeta del juego negro, INICIAR COMBATE cyan, Invertir atacante y defensor naranja, Historial verde y los dos Héroe blancos. En los fondos claros (cyan, naranja, blanco) la letra lleva un borde negro fino para que se lea. Probar que todos respondan al clic. Anotar lo que no convenza.
- [ ] **202.** Simulador de combate 1.0.41.0 (13/11/2026). 1) El botón dice «Historial (últimos 40)» y guarda hasta 40 combates. 2) En el Historial, entre «Ver ficha» y «Cerrar», hay tres botones nuevos: «Stats» abre una torta con las formaciones que ganaron (en cada combate cuenta la del bando que gana la mayoría de las peleas), cada una con su porcentaje, y arriba «La mejor»; «Exportar ficha» guarda como imagen la ficha del combate elegido; «Exportar gráfica» guarda la torta. Probar guardar una como PNG y otra como JPG y abrirlas. Anotar lo que no coincida.
- [ ] **201.** Simulador de combate 1.0.40.0 (13/11/2026). El recuadro del título TERRENO ahora es marrón claro (antes blanco); la letra sigue blanca con borde verde. Anotar lo que no convenza.
- [ ] **200.** Simulador de combate 1.0.39.0 (13/11/2026). Los títulos ATACANTE y DEFENSOR ya no tienen el recuadro blanco: la letra blanca con borde negro y sombra va directo sobre la franja de color. TERRENO conserva su recuadro. Anotar lo que no convenza.
- [ ] **199.** Simulador de combate 1.0.38.0 (13/11/2026). Mirar los títulos de los tres paneles: ATACANTE y DEFENSOR en Arial negrita blanca con borde negro y sombra, dentro de un recuadro blanco de borde fino oscuro; TERRENO igual, con el borde de la letra verde. Anotar lo que no convenza.
- [ ] **198.** Simulador de combate 1.0.37.0 (13/11/2026). Repetir dos veces un mismo combate (mismos ejércitos, terreno y sitio) y abrir el Historial: esas dos filas tienen que tener el mismo color de fondo; un combate distinto queda en blanco, y cada grupo de repetidos tiene su propio color. La fila elegida se sigue viendo en celeste. Anotar lo que no coincida.
- [ ] **197.** IA: freno de producción antes de la quiebra (vista-aliada 1.0.217.0, 13/11/2026). La computadora en prueba deja de fabricar ejércitos cuando lo que pagaría con todo el ejército fuera de las ciudades supera lo que cobra, con un margen del oro guardado; antes frenaba recién cuando ya gastaba más de lo que cobraba, y con muchas ciudades se quedaba sin oro y los ejércitos desertaban. 1) Actualizador, opción **9**: vista-aliada en **1.0.217.0** o posterior. 2) Monitor de IA → **Ninguna**, marcar **Scarpart** y **Kor**, Partidas **10**, **Nueva tanda**. 3) Mientras corre, no instalar otra versión del parche. Avisar cuando termine.
- [ ] **196.** Simulador de combate 1.0.36.0: cálculo más confiable (13/11/2026). Repetir el combate 18/19 de noche con 6000 peleas: ahora tiene que dar alrededor de 77 % para el atacante (antes 80,48 %), porque promedia 20 noches y en algunas el sorteo favorece al defensor. De día, alrededor de 80,4 %. Con 65 536 peleas el número es el exacto del juego y no cambia de una corrida a otra. Anotar lo que no coincida.
- [ ] **194.** Simulador de combate 1.0.35.0 (13/11/2026). Repetir el combate 18/19 (5 Sparks + 1 Sun Priests contra 5 Moonguard, Esfinge, Bannerman y Devourers, en hills, de noche): la ventana de combate ahora tiene que mostrar ganando al ATACANTE, igual que el porcentaje (≈80 %) y el Historial. En cualquier combate, el que gana en la ventana tiene que ser el mismo que figura como Ganador en el Historial. Anotar lo que no coincida.
- [ ] **193.** Simulador de combate 1.0.34.0 (13/11/2026). Abrir una ficha del Historial: termina en el RESULTADO (y los avisos, si hay); ya no aparece la «batalla de muestra». Anotar lo que no coincida.
- [ ] **192.** Simulador de combate 1.0.33.0 (13/11/2026). En el Historial, la columna se llama «Ganador» y cada fila dice solo ATACANTE (azul) o DEFENSOR (rojo) con su porcentaje. Abrir una ficha: el resultado empieza por el ganador («RESULTADO: DEFENSOR con 92 %») y sigue en gris lo del que perdió. Anotar lo que no coincida.
- [ ] **191.** Simulador de combate 1.0.32.0 (13/11/2026). Abrir el Historial: tiene barra de desplazamiento a la derecha, y en los combates que ganó el defensor (por ejemplo, el 14 y el 15) la columna Resultado dice «Gana el DEFENSOR» con su porcentaje. Anotar lo que no coincida.
- [x] **195.** IA: pilas que vuelven a su ciudad y no llegan (vista-aliada 1.0.216.0, 13/11/2026) — 13/11/2026: corrida en la tanda 164 (10 partidas completas). Las pilas llegan (ninguna trabada); la deserción de la nueva vino de fabricar más ejércitos de los que paga. Resultado en ia\PENDIENTE-ia-economia.md.
La versión nueva no cambia cómo juega la computadora: solo anota, al final de cada turno, dónde quedó cada pila que
iba de vuelta a su ciudad (a qué distancia y cuánto movimiento le sobró), para saber si no llega por lenta o porque
se queda quieta.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.216.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.

- [x] **187.** IA: la memoria del repliegue, corregida (vista-aliada 1.0.215.0, 13/11/2026) — 13/11/2026: corrida en la tanda 163 (10 partidas completas). El cambio ya actúa (6 veces) y las pilas vuelven a la ciudad. Resultado en ia\PENDIENTE-ia-economia.md.
En las tandas de la 186 el caso apareció (una computadora sin oro iba y venía entre atacar y volver), pero el cambio
de la 1.0.214.0 nunca actuaba por un error: la marca de «volviendo a la ciudad» se borraba antes de leerla. Corregido.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.215.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.

- [x] **186.** IA: repetir la tanda de la memoria del repliegue (vista-aliada 1.0.214.0, 12/11/2026) — 13/11/2026: corrida dos veces (tandas 161 y 162). El caso apareció en 1200 color 3, pero el cambio no actuó nunca por un error del parche; corregido en 1.0.215.0 (tarea 187). Resultado en ia\PENDIENTE-ia-economia.md.
En la tanda de la 185 no se dio el caso que el cambio corrige, así que hace falta otra igual.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.214.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.

- [x] **185.** IA: el repliegue por quiebra se sostiene (vista-aliada 1.0.214.0, 12/11/2026) — 12/11/2026: corrida en la tanda 160. El caso que corrige el cambio no apareció (evento 38 = 0); la nueva desertó 1 vez y la original 30. Se repite la tanda (tarea 186); resultado en ia\PENDIENTE-ia-economia.md.
Cambio: cuando a la computadora nueva se le acaba el oro, las pilas que ya volvían a su ciudad (y los grupos recién
armados con ejércitos sueltos) siguen volviendo aunque el planificador les proponga atacar; antes iban y venían sin
llegar y terminaban desertando. Hay que ver si deserta menos y si eso le cuesta partidas.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.214.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.

- [x] **184.** Ayuda emergente del enlace del clan (vista-aliada 1.0.213.0, 13/11/2026). En `C:\Warlords3`, actualizar el parche (opción 9) y abrir DarklordAV.exe: dejar el cursor sobre el enlace del clan (y, si no aparece nada, probar con clic derecho, como en los otros botones del menú): debe verse la ayuda «Click copies the link: paste it in your browser (Ctrl+V)». Hacer clic, salir, pegar en el navegador y comprobar la dirección. — 13/11/2026, cumplida: el clic derecho muestra la ayuda en el papiro, como los demás botones del menú; el clic izquierdo abre el navegador (el juego queda en blanco al perder el foco, igual que con Sorteo, Votación o el Comparador).

- [x] **183.** Aviso de enlace copiado (vista-aliada 1.0.212.0, 13/11/2026). En `C:\Warlords3`, actualizar el parche (opción 9) y abrir DarklordAV.exe: hacer clic en el enlace del clan: el texto debe cambiar a «Enlace copiado: pegalo en el navegador (Ctrl+V)» y seguir así mientras esté abierto el juego; que el texto entre entero y no se superponga con la versión. Salir, pegar en el navegador y comprobar la dirección. — 13/11/2026: el texto no cambia. Reemplazado por ayuda emergente en 1.0.213.0 (tarea 184).

- [x] **182.** Copiar el enlace del clan y base del faro más tenue (vista-aliada 1.0.211.0, 13/11/2026). En `C:\Warlords3`, actualizar el parche (opción 9) y abrir DarklordAV.exe: (a) hacer clic en el enlace del clan; salir del juego, abrir el navegador y pegar (Ctrl+V) en la barra de direcciones: debe aparecer `https://sites.google.com/view/plagacarriers`. Mirar también si al salir del juego quedó abierta una ventana del navegador con el sitio; (b) en una partida con **Day/Night** y un faro, de noche: la casilla del faro y sus vecinas, más tenues que antes; el haz, igual que en la 1.0.210.0. Anotar qué no anda o qué ajustar. — 13/11/2026: el enlace se copia; faro cerrado (tema terminado). Falta avisar que se copió: 1.0.212.0 (tarea 183).

- [x] **181.** Enlace del clan y faro a 8 casillas (vista-aliada 1.0.210.0, 12/11/2026). En `C:\Warlords3`, actualizar el parche (opción 9) y abrir DarklordAV.exe: (a) el enlace del clan debe verse un poco más abajo, separado del cuadro de opciones; hacer clic sobre él: debe abrirse el sitio en el navegador (el cursor puede no cambiar; lo que importa es el clic); (b) en una partida con **Day/Night** y un faro, de noche: el haz llega a unas 8 casillas y se apaga de a poco hacia la punta; la casilla del faro y sus vecinas se ven iluminadas como el centro de una ciudad, no más. Anotar qué no anda o qué ajustar. — 13/11/2026: aparece la mano sobre el enlace pero no se ve el navegador (el juego ocupa la pantalla); el faro, bien; base más tenue pedida. Ajustes en 1.0.211.0 (tarea 182).

- [x] **180.** Haz del faro más visible y enlace del clan (vista-aliada 1.0.209.0, 12/11/2026). En `C:\Warlords3`, actualizar el parche (opción 9) y abrir DarklordAV.exe: (a) en el menú principal, pasar el cursor por `https://sites.google.com/view/plagacarriers` y hacer clic: debe abrirse el sitio en el navegador; (b) en una partida con **Day/Night** y un faro, de noche: el haz debe verse claro sobre tierra y agua hasta 6 casillas, y girar un poco más lento que en la 1.0.207.0. Anotar si el cursor no cambia sobre el enlace (el del juego no siempre lo hace), si sigue sin abrir, o si el haz conviene más fuerte, más ancho o más lento. — 12/11/2026: el enlace seguía sin responder; el faro, visible. Ajustes en 1.0.210.0 (tarea 181).

- [x] **179.** IA: repliegue por quiebra (vista-aliada 1.0.208.0, 12/11/2026) — 12/11/2026: corrida en las tandas 158 y 159 (1.0.213.0). El repliegue anduvo donde se activó, pero las dos deserciones de la nueva fueron de pilas que no cubre; resultado en ia\PENDIENTE-ia-economia.md.
Cambio: cuando a la computadora nueva el mantenimiento le supera al ingreso y el oro se le acaba, las pilas que
estaban paradas yendo a ciudades neutrales, ruinas, ítems o misiones vuelven a su ciudad más cercana. Hay que ver si
deserta menos y si eso le cuesta partidas.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.208.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
- [x] **178.** Haz giratorio del faro (vista-aliada 1.0.207.0, 12/11/2026). En `C:\Warlords3`, actualizar el parche (opción 9) y abrir una partida con **Day/Night** que tenga un faro (por ejemplo BUILD01.SAV, o levantar uno con *Build*). En una vuelta de noche, mirar el faro unos segundos: (a) su casilla y las vecinas quedan siempre iluminadas; (b) un haz en forma de embudo, de unas 6 casillas, gira en el sentido de las agujas del reloj e ilumina tierra y agua al pasar; (c) el resto del mapa no parpadea ni se pone lento. Anotar si la vuelta es muy rápida o muy lenta (se ajusta), y si el haz debería ser más ancho o más angosto. — 12/11/2026: el usuario lo vio casi imperceptible y un poco rápido; corregido en 1.0.209.0 (tarea 180).
- [x] **177.** Botón de la torre (vista-aliada 1.0.206.0, 12/11/2026). En `C:\Warlords3`, actualizar el parche (opción 9) y en una partida pasar el mouse o hacer clic en el botón de la torre de la botonera: el texto debe decir «Build /Rebuild - Repair». El menú que abre sigue igual.
- [ ] **190.** Simulador de combate 1.0.31.0: historial de combates (13/11/2026). Simular 2 o 3 combates distintos y apretar «Historial (últimos 20)…» (junto a Invertir). Cada fila tiene que mostrar el mismo número que el contador de PRUEBAS, con la fecha y la hora. Doble clic en una: se abre su ficha con el campo, las tropas de cada lado, el resultado y la batalla de muestra con las unidades caídas tachadas en rojo. Cerrar y volver a abrir el Simulador: el historial sigue ahí. Anotar lo que no coincida.
- [ ] **189.** Simulador de combate 1.0.30.0: contador de pruebas (13/11/2026). Arriba a la derecha, el contador retro con la leyenda «PRUEBAS» suma 1 por cada simulación. Cerrar y volver a abrir: sigue el mismo número. En Configuración → «Contador de pruebas», elegir «Reset mes»: la leyenda dice «PRUEBAS (reset mes)»; «Poner en cero» pide confirmación y lo deja en 000000. Anotar lo que no coincida.
- [ ] **188.** Simulador de combate 1.0.29.0: barcos y topes de pila (13/11/2026). Abrir el Simulador (se actualiza solo con el engranaje). (a) Terreno de agua, 3 gnollcav de cada lado; al defensor ponerle el barco `lancha` (F1 V2) y al atacante `warship`: el atacante tiene que ganar casi siempre (≈98 %). Cambiar la lancha del defensor por `warship`: queda parejo. Con un barco más fuerte que todas las tropas sale un aviso de que no cambia nada; es así en el juego (embarcada, cada unidad pelea con el menor entre su fuerza y la del barco). (b) Sitio «Ciudad»: el defensor admite hasta 32 unidades y debajo dice «entran 32»; con 33 da error. (c) En agua con `lndcraft` (Landing) el tope baja a 5; con `barcaza` (Carrier) el defensor admite 24. (d) En tierra, con un volador (por ejemplo `airship`) en la pila, el tope baja a 6; en la ciudad, 6 voladores y 24 más (30) entran y 31 no. (e) Cada vez que un lado pasa su tope, junto a su botón «Héroe…» titila despacio una luz roja con «tope excedido 9 / 8» (unidades / tope); al corregir la cantidad se apaga y queda el contador en gris («8 / 8»). Debajo de FACTOR y COSTO solo van el Factor medio y el tope con su motivo, sin cortarse. Anotar lo que no coincida.
- [ ] **176.** Torre, enlace del clan y grupos SHIFT (vista-aliada 1.0.205.0, 12/11/2026). En `C:\Warlords3`, actualizar el parche (opción 9) y abrir DarklordAV.exe: (a) en el menú principal, debajo del cuadro de opciones, debe verse `https://sites.google.com/view/plagacarriers` con el color y la letra de las opciones, del tamaño de los checks; un clic la abre en el navegador; (b) en una partida, una torre de vigía despeja la niebla a 4 casillas (antes 5) y de noche alumbra menos; (c) seleccionar ejércitos distintos y apretar SHIFT+1, SHIFT+2… SHIFT+9; luego 1, 2… 9: cada número debe volver a seleccionar su grupo. Anotar lo que no ande. El muro queda sin Life Drain hasta la opinión del clan. — 12/11/2026: el usuario informó que el enlace no abría; corregido en 1.0.209.0 (tarea 180).
- [x] **175.** Muro sin Life Drain (vista-aliada 1.0.204.0, 12/11/2026). En `C:\Warlords3`, actualizar el parche (opción 9) y restaurar BUILD01.SAV. Atacar varias veces una pila sobre un muro de piedra o a 1 casilla de él: el muro ya no le quita golpes a los atacantes (siguen Missiles, Acid y Fortify +3 y Life Ward +3). En el Simulador 1.0.25.0, el muro dice «Missiles +3, Acid +3, Fortify +3». Anotar si sigue desparejo y para qué lado.
- [x] **173.** Manual con obras y defensas (vista-aliada 1.0.201.0, 11/11/2026). Abrí `C:\Warlords3\Manual-Era-de-Alianzas.pdf` y leé el capítulo nuevo **XVII «Obras y defensas»**: torres, faros y murallas, los bonos de cada edificio en combate, el Life Ward y la ventana de victoria solo para el atacante. Fijate también la fila nueva en «Novedades de un vistazo» (capítulo I). Anotá lo que esté mal o quieras cambiar.
- [ ] **170.** Ventana de victoria solo para el atacante (vista-aliada 1.0.199.0, 11/11/2026). En `C:\Warlords` de las dos PC, actualizar el parche y jugar en red con DarklordAV.exe. (a) Un humano ataca y gana una ciudad del otro humano: la ventana de ocupar / saquear / pillar / arrasar tiene que aparecer **solo** en la PC del atacante. En la PC del atacado se sigue viendo la ventana de combate, pero no la de victoria. (b) Lo que elija el atacante (por ejemplo, arrasar) tiene que verse igual en las dos PC. (c) Control: en una partida de una sola PC, al ganar una ciudad la ventana sigue apareciendo. Anotar lo que no coincida.
- [x] **172.** Simulador de combate 1.0.21.0 y vista-aliada 1.0.200.0 (11/11/2026). (a) En el simulador (opción del Actualizador, o «Buscar actualización» en Configuración), en TERRENO elegir «Edificio del defensor»: Faro, Torre de vigía o Muralla, y comparar el % con «Ninguna» (los edificios tienen que bajar el % del atacante; la muralla, mucho más). (b) En el juego (`C:\Warlords3`, parche actualizado): una unidad común parada sobre una torre o un faro propio tiene que mostrar en su informe la fuerza +1 en violeta, y pelear con ese +1 al ser atacada. Antes de esta versión el +1 se mostraba pero **no se aplicaba en el combate**. Anotar lo que no coincida.
- [x] **169.** Life Ward de los edificios (vista-aliada 1.0.198.0, 11/11/2026). En `C:\Warlords3`, actualizar el parche. Cada punto de Life Ward anula un punto del Life Drain del atacante, sin dar golpes de más. Lo tienen los defensores: en una ciudad, su tamaño (1, 2 o 3); en una torre de vigía +2; en un faro +1; sobre un muro propio o pegado a él +3; si se juntan, vale el mayor. (a) Atacar con un grupo que tenga Life Drain una pila en una ciudad de tamaño 3: en la pantalla de combate, los defensores tienen que pelear con sus golpes (hits) completos. (b) Control: la misma pila atacada en campo abierto pierde golpes por el Life Drain. (c) Ciudad de tamaño 1 contra Life Drain +3: los defensores pierden 2 golpes (nunca menos de 1). (d) Torre (+2) y faro (+1), lo mismo. Anotar lo que no coincida.
- [x] **168.** Bonos del muro (vista-aliada 1.0.197.0, 11/11/2026; desde la 1.0.197.0: Missiles, Acid y Fortify +3, Life Drain +1). En `C:\Warlords3`, actualizar el parche y restaurar BUILD01.SAV. (a) Atacar un bloque **vacío** del muro rojo con el ejército blanco: en la pantalla de combate, los arqueros del muro pelean con +3 Missiles, +3 Acid, +3 Fortify y +1 Life Drain sumados a lo suyo (el Life Drain se nota en que las unidades blancas pelean con 1 hit menos, nunca menos de 1). (b) Poner una pila roja **sobre** el muro o **pegada** a él (también en diagonal) y atacarla: tiene que perder bastante menos que la misma pila atacada lejos del muro (a 2 casillas o más). Comparar las probabilidades que da el juego antes de atacar en los dos casos. (c) Control: cuando la pila roja ataca desde el muro, no recibe los bonos (son solo para defender). Anotar lo que no coincida, y si el muro resulta demasiado fuerte (casi imposible de tomar) o demasiado débil.
- [x] **171.** IA: tanda de confirmación, sin cambios (vista-aliada 1.0.192.0 o posterior, 11/11/2026)
La computadora nueva volvió a ganarle a la original, pero por muy poco. Una tanda más con la misma versión dice si
es de verdad o fue suerte.
1. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
2. Mientras corre, no instales otra versión del parche. Avisame cuando termine. — **Hecho 11/11/2026:** tandas 154 y 155 (20 partidas ok). La nueva volvió a ganar en las dos.
- [x] **174.** IA: ahorrar para reconstruir puentes (vista-aliada 1.0.203.0, 11/11/2026)
Cambio: cuando un puente derribado le abriría camino pero no le alcanza el oro, la computadora nueva deja de comprar
tipos de unidad y de agrandar ciudades hasta juntar lo que cuesta reconstruirlo. Hay que ver si reconstruye y si eso
le cuesta partidas.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.203.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, tildá **serie de 2**, **Nueva tanda**.
3. Mientras corre la serie, no instales otra versión del parche. Avisame cuando termine. — **Hecho 12/11/2026:** tandas 156 y 157 (1.0.204.0, 20 partidas ok). La nueva reconstruyó 3 puentes (antes 1 en 20 partidas) y los colores que ahorraron terminaron mejor que el resto. El ahorro queda.
- [x] **166.** Atacar el muro vacío con un clic (vista-aliada 1.0.186.0, 11/11/2026). **Hecho 11/11/2026:** el héroe blanco atacó el bloque vacío del muro rojo y lo destruyó; no queda rastro del bloque. En las dos PC, actualizar el parche y restaurar BUILD01.SAV. Con el ejército blanco pegado a un bloque **vacío** del muro rojo, aparecen las espadas: hacer clic. Tiene que empezar la batalla contra los arqueros del muro (hasta 24). Probar al costado y en diagonal del bloque. Si no empieza, anotar si apareció algún cartel y si el grupo se movió.
- [x] **165.** Cursor de espadas sobre el muro (vista-aliada 1.0.184.0, 10/11/2026). En las dos PC, actualizar el parche y restaurar BUILD01.SAV. Con el héroe blanco elegido, pasar el mouse sobre un bloque del muro rojo **pegado** al grupo (también en diagonal): tiene que aparecer el cursor de espadas. Hacer clic: tiene que empezar la batalla contra los arqueros del muro. Controles: a dos casillas o más, el cursor no cambia; sobre un muro propio o de un bando en paz, tampoco. Anotar lo que no coincida.
- [x] **164.** Muros en diagonal y trampas (vista-aliada 1.0.183.0, 10/11/2026). En `C:\Warlords3` (y en `C:\Warlords` de las dos PC para la red), actualizar el parche y jugar con DarklordAV.exe. (a) Restaurar BUILD01_8.SAV o murallas01_9.SAV: el héroe del blanco ya no tiene que poder pasar en diagonal entre dos bloques del muro rojo (antes se colaba por la esquina, sin pisar ningún bloque); tiene que frenarse delante o atacar un bloque. El dueño y sus aliados pasan igual. (b) Una trampa doble fuera de una ciudad tiene que explotar **dos veces** (primer ejército y segundo ejército); en una ciudad, una sola vez. Las trampas ya gastadas de muros03_6.SAV siguen gastadas: probar con trampas nuevas. (c) Construir con el Blade Runner en una partida **nueva** (ver 163 d). Anotar lo que no coincida.
- [x] **163.** Muros y trampas (vista-aliada 1.0.182.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche y jugar con DarklordAV.exe. (a) Atacar con un ejército un bloque de muro enemigo **sin ejércitos encima**: tiene que aparecer el cursor de espadas y la batalla contra los arqueros del muro, también en partidas **sin Diplomacy** (ahí todos los bandos están en guerra). (b) Un ejército enemigo que va por un camino cortado por un muro ajeno tiene que frenarse delante del muro; ya no pasa ni se lo queda. Con Diplomacy y los bandos en paz, el muro lo frena sin pelear. (c) Trampas: en la prueba de laboratorio explotan 2 veces fuera de una ciudad y 1 sola vez dentro de una ciudad (así se pidió el 4/11/2026). Si una trampa fuera de ciudad explotó una sola vez, anotar dónde estaba (casilla, ¿al lado de una ciudad, de un camino, de un muro?), si el segundo ejército la pisó en el mismo turno o en otro, y si era de un jugador humano o de la computadora. (d) Muros en red: en esta PC, `C:\Warlords\ARMY\bladerun.ARM` (la carpeta donde se guardan muros02/muros03) es la versión vieja, **sin «build»**; el de `C:\Warlords3` y el paquete ARMY publicado sí lo traen. Correr la **opción 1** del Actualizador sobre `C:\Warlords` en esta PC (y sobre la carpeta que use la notebook), y después probar de nuevo «Stone Wall» con el Blade Runner en el grupo. **Ojo:** cada partida guardada lleva adentro su propia copia de las armas: muros03 se creó con el bladerun viejo y ahí nunca va a poder construir; hay que empezar una partida nueva.
- [x] **162.** Faro, Actualizador y Puente (10/11/2026). (a) Juego (vista-aliada 1.0.181.0): en la botonera «Build» el renglón dice «Faro»; de noche, la luz de un faro costero sale en abanico (un cuarto de vuelta) hacia donde está la mayor parte del agua, ya no en todas las direcciones. (b) Actualizador 1.0.16.0: la opción 4 dice «→ nuevos escenarios personalizados»; en la opción 9, si falta correr la 6, el aviso sale en rojo: «Primero la opción 6, después la 9.». (c) Puente 1.1.20.0 (se actualiza con la opción 13): el fondo de la consola es negro. Anotar lo que no coincida.
- [x] **159.** Reparar el muro (vista-aliada 1.0.179.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche y jugar con DarklordAV.exe: (a) dañar un muro de piedra propio atacándolo con otro bando sin derribarlo (que mueran algunos de los 24 defensores); (b) con un grupo propio en ese bloque o al lado, abrir la botonera «Build» (la torrecita): el último renglón, «Repair Wall», está encendido; (c) apretarlo: el diálogo dice «Repairing a stone wall» y un costo proporcional a los defensores muertos (la mitad del precio del muro si murieron 12); confirmar y anotar el oro antes y después; (d) atacar de nuevo ese bloque: vuelve a defenderse con 24; (e) control: con el muro sin daño, o sin oro suficiente, «Repair Wall» está apagado. Con varios bloques dañados al alcance, cada clic ofrece el siguiente. Anotar lo que no coincida.
- [x] **158.** Longbows, portón oscuro, banderas en caminos y reintegro (vista-aliada 1.0.178.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche y jugar con DarklordAV.exe: (a) atacar un muro de piedra de un bando que tenga Longbows (por ejemplo, el amarillo del set estándar): la batalla muestra Longbows defendiendo; un bando sin Longbows sigue defendiendo con Archers; (b) el portón abierto deja ver la entrada negra; (c) las banderas sobre el muro aparecen solo en bloques que tienen camino; (d) anotar el oro, derribar con Raze un muro de piedra propio y una empalizada propia: cada uno devuelve el 75 % de lo que costó construirlo (torre y faro no devuelven nada). Anotar lo que no coincida.
- [x] **157.** Puertas en todo el muro y Raze de torres y faros (vista-aliada 1.0.177.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche y jugar con DarklordAV.exe: (a) cada bloque de muro de piedra, haya camino o no, muestra el arco con el portón y las dos banderas animadas; el portón se abre cuando un ejército está a 1 casilla y se cierra al alejarse; mirar también un tramo en diagonal; (b) con un ejército propio dentro de una torre de vigía o un faro propios, o al lado, Raze se enciende y pregunta «Are you sure you want to raze the watchtower …?» (o «the lighthouse …»); al confirmar desaparece, y con él la luz y la vista que daba; (c) control: la torre o el faro de otro bando no se ofrecen. Anotar lo que no coincida.
- [x] **156.** Raze sobre muros e informe en la torre (vista-aliada 1.0.176.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche y jugar con DarklordAV.exe: (a) con un ejército propio dentro de un bloque de muro propio o al lado, apretar el botón Raze de la barra del grupo: tiene que aparecer «Are you sure you want to raze the stone wall …?»; confirmar: el bloque desaparece. Con varios bloques al alcance, cada Raze ofrece el siguiente; (b) lo mismo desde el menú de órdenes (clic derecho) y con la tecla; (c) abrir el informe de una unidad común (no héroe) dentro de una torre o un faro: la casilla violeta de fuerza muestra la fuerza +1; fuera de la torre, vacía; un héroe no recibe el +1. Anotar lo que no coincida.
- [x] **155.** Muros propios, Raze y luz del faro (vista-aliada 1.0.175.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche y jugar con DarklordAV.exe: (a) mover un ejército propio sobre un bloque de muro propio, con puerta y sin puerta: debe entrar y quedarse; (b) lo mismo con un ejército de un aliado; (c) un enemigo no debe poder atravesarlo; (d) con un ejército parado sobre su muro o al lado, usar Raze: anotar si aparece la ventana de confirmación («Are you sure… raze… stone wall?»), qué botón se apretó y si el bloque desaparece; (e) la luz del faro llega a 6 casillas sobre el mar. Si Raze sigue sin hacer nada, anotar exactamente los pasos (menú o tecla, dónde estaba el ejército).
- [x] **154.** Atacar un muro de piedra enemigo (vista-aliada 1.0.174.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche y jugar con DarklordAV.exe, con dos bandos en guerra: (a) el bando A construye un muro de piedra; (b) con un grupo del bando B, elegir como destino una casilla del muro: el grupo debe llegar al lado y atacarla; la batalla muestra arqueros del bando A defendiendo (24 si el muro está entero); (c) después de la batalla no deben quedar arqueros sueltos en el mapa, ni sumarse a las estadísticas ni avisar sus muertes; (d) atacar varias veces el mismo bloque: los arqueros que murieron no vuelven, y cuando mueren los 24 el bloque desaparece y se puede pasar; (e) con el bando en paz, el muro no se puede atacar. Anotar si el grupo entra o no a la casilla cuando cae el muro, y lo que se vea mal en el informe de la batalla.
- [x] **152.** Luz de los faros y derribar muros propios (vista-aliada 1.0.172.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche y jugar con DarklordAV.exe: (a) de noche, un faro debe alumbrar hacia el mar 5 casillas, cada vez más tenue, y hacia tierra solo la casilla vecina, con niebla o sin ella; una torre de vigía alumbra 3 casillas; (b) parar un grupo propio sobre una casilla de muro propio (o al lado) y elegir «Raze» (menú o tecla): el cartel debe nombrar el muro y su dirección («the stone wall to the north», «here», etc.); al aceptar, el bloque desaparece y se puede pasar por ahí; (c) con varios bloques alrededor, cada «Raze» ofrece el siguiente; (d) un muro ajeno no se puede derribar así. Anotar lo que se vea mal.
- [x] **151.** Puertas en diagonal y banderas animadas (vista-aliada 1.0.169.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche: (a) construir un muro de piedra en diagonal que cruce un camino: la puerta debe verse como un arco en el medio del tramo (no en las torres), con portón que se abre al acercar un grupo; (b) la torre de vigía y el faro deben llevar la bandera animada de las ciudades, del color del dueño; (c) encima de cada puerta del muro deben flamear dos banderas; (d) las banderas de los fuertes deben verse un poco más chicas. Anotar lo que se vea mal (sobre todo si las banderas no se mueven o dejan rastros).
- [x] **150.** Sombras, torre de vigía y portón (vista-aliada 1.0.168.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche: (a) construir muros de piedra en varias direcciones, también en diagonal y en L: la sombra no debe tener cortes en ningún tramo; (b) construir una torre de vigía: debe verse de piedra como el muro, en gris azulado, con almenas, puerta, ventana y un banderín del color del bando dueño (si otro bando la toma, el banderín cambia de color); (c) acercar un grupo a una puerta del muro: el portón se abre ya a una casilla de distancia y se cierra cuando el grupo se aleja. Anotar lo que se vea mal.
- [x] **153.** IA: menos grupos de abandonados y conteo de los grupos de ataque (vista-aliada 1.0.173.0). Hecho 11/11/2026: tandas 152 y 153 (18 partidas). La computadora nueva vuelve a quedar arriba de la original, por poco (puesto 2,84 contra 2,92). Queda el tope de 4.
- [x] **149.** Calzada del muro de piedra (vista-aliada 1.0.167.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche y construir un muro de piedra: el piso de arriba del muro y de las torres debe verse con las losas de piedra de las ciudades, más chicas y en perspectiva. Anotar lo que se vea mal.
- [x] **148.** Sombra y puerta del muro de piedra (vista-aliada 1.0.166.0, 10/11/2026). En `C:\Warlords3`, actualizar el parche: (a) la sombra del muro debe verse pareja y oscura, sin rejilla; (b) en la puerta sobre un camino, los ladrillos a los dos lados del arco deben seguir sin corte, también cuando el muro sigue en diagonal. Anotar lo que se vea mal.
- [x] **147.** Muro de piedra, puerta y menú de construir (vista-aliada 1.0.165.0, 9/11/2026). En `C:\Warlords3`, actualizar el parche y jugar con DarklordAV.exe: (a) construir un muro de piedra y mirar que sea gris amarronado, dos hileras más bajo, con algún ladrillo más oscuro y la sombra más oscura; (b) construir un muro que cruce un camino: esa casilla debe mostrar un arco con portón de madera cerrado; mover un grupo a esa casilla: el portón se ve abierto mientras el grupo está ahí y se cierra al irse; (c) abrir el menú Build: los renglones deben verse juntos y centrados, como en el menú de la ciudad. Anotar lo que se vea mal.
- [x] **146.** Colocar obras con vista previa (vista-aliada 1.0.164.0, 9/11/2026). En `C:\Warlords3`, actualizar el
  parche y elegir un grupo con constructor. Botón de la torrecita → **Road**, **Bridge**, **Watchtower**,
  **Lighthouse** o **Stone Wall**: la ventana se cierra y no aparece el diálogo de flechas. (a) Al pasar el mouse por
  la casilla del grupo o por una de las 8 de alrededor, se ve la pieza en transparencia (el puente, de orilla a
  orilla) y el cursor de «mover»; más lejos o donde no se puede, flecha y nada dibujado. (b) Un clic construye ahí y
  cobra, sin preguntar; se puede seguir poniendo piezas (por ejemplo, muros seguidos) mientras alcance el oro.
  (c) Clic derecho termina el modo. (d) **Port** sigue como antes, con el diálogo. Anotar acá lo que se vea mal
  (mejor con captura).
  Resultado:

- [x] **144.** Probar los arreglos del 9/11 (vista-aliada 1.0.161.0). En `C:\Warlords3`, actualizar el parche.
  (a) Clic derecho sobre un grupo: «Build Trap» vuelve a estar en el menú de órdenes, en el botón de antes.
  (b) Botón de la torrecita: la lista de construcciones ya no debe tener espacio libre grande debajo, y Trap ya no
  aparece ahí. (c) Muros: ya no deben verse entrecortados ni con torres sueltas de más; un muro aislado es una
  sola torre. El gris es más claro, parecido al de las ciudades. Anotar acá lo que se vea mal (mejor con captura).
- [x] **143.** Probar el muro nuevo (vista-aliada 1.0.161.0). En `C:\Warlords3`, actualizar el parche. (a) Parar un
  grupo con constructor sobre un camino y construir un muro de piedra: ahora se puede, y queda como puerta (pasan
  tus ejércitos y los de tus aliados). (b) Mirar que el muro tenga más o menos el alto de una ruina y que ya no tenga
  manchas blancas ni verdes, ni rayas tipo código de barras, y que la calzada de arriba sea gris oscuro con la textura del camino. (c) Mirar que el frente se parezca al de la ruina: hiladas de ladrillos que siguen al muro también en diagonal, una línea oscura bajo la calzada y almenas cuadradas claras arriba; en cada casilla una torre redonda de ladrillos con almenas (también en las puntas de los tramos, que ya no deben verse con rayas). Anotar acá lo que se vea mal (mejor con captura).
- [x] **142.** Probar la botonera de construir (vista-aliada 1.0.153.0). En `C:\Warlords3`, actualizar el parche y
  elegir un grupo con constructor. Apretar el botón de la torrecita (almena roja, a la izquierda de «pasar turno»):
  debe abrir una lista con Rebuild City/Site, Road, Bridge, Port, Watchtower, Lighthouse, Stone Wall y Trap. Mirar:
  (a) que solo se puedan elegir las obras posibles en esa casilla (las otras, en gris); (b) que al elegir una se
  abra la ventana de construir esa obra, y que repetir el mismo renglón pase a otro lugar o dirección; (c) que el
  clic derecho en el mapa ya no muestre «Build» ni «Build Trap»; (d) que reconstruir una ciudad arrasada siga
  funcionando. Anotar acá lo que falle (mejor con captura).
- [ ] **141.** Probar los gráficos nuevos de las obras y el muro en 8 direcciones (vista-aliada 1.0.152.0). En
  `C:\Warlords3`, actualizar el parche con el Actualizador y abrir una partida con un grupo que tenga constructor.
  Apretar construir varias veces: después de la torre (y el faro, a orillas del agua) aparecen 8 opciones de muro,
  cada una con su flechita (N, NE, E, SE, S, SO, O, NO). Levantar varios bloques seguidos en distintas direcciones,
  incluida una diagonal. Mirar: (a) que cada bloque quede unido con el anterior, sin cortes; (b) que el tramo de
  norte a sur se vea con buen ancho; (c) que la torre y el faro se vean enteros, asomando sobre la casilla de arriba,
  también después de mover un ejército por encima o al costado; (d) la empalizada. Anotar acá lo que se vea mal
  (mejor con una captura).
- [x] **140.** Puerta en el muro solo para aliados (vista-aliada 1.0.151.0, 9/11/2026)
Construir un muro y, con la misma unidad parada encima, un camino (la «puerta»): debe costar el **25 % de fundar
una ciudad** (el muro sigue costando el 50 %). Probar en Warlords3 que por la puerta pasan **tus** ejércitos y los
de un **aliado**, y que un enemigo o la computadora no pasan (tienen que rodear o quedarse).

- [x] **139.** Muro de piedra (vista-aliada 1.0.150.0, 9/11/2026)
Con una unidad con «Build» en tierra libre, al seguir apretando construir aparece **«Building a stone wall»**
(después de la torre y el faro). Cuesta la mitad de fundar una ciudad (no lo habías dicho; decime si querés otro).
Probar en Warlords3:
- que se dibuje el muro en la casilla y que **ningún ejército** (tuyo, aliado, enemigo ni de la computadora) pueda
  pasar por ella;
- que con la misma unidad parada en el muro se pueda construir un **camino** encima (cuesta el doble que en montaña)
  y que, con el camino, ya se pueda pasar;
- que se conserve al guardar y cargar.
Nota: el muro se dibuja como un tramo horizontal; si lo ponés en una fila vertical, decime cómo se ve.

- [ ] **138.** Tope de 3 pausas por jugador (vista-aliada 1.0.149.0, 9/11/2026)
En una partida en red con otra PC (las dos con la 1.0.149.0): desde una PC, **Pausa** y **Espacio** para reanudar,
tres veces. La cuarta vez, **Pausa** no hace nada en esa PC. Desde la otra PC todavía tiene que poder pausar 3 veces.
Guardá, cargá la partida y comprobá que la cuenta sigue (la PC que ya usó sus 3 no puede pausar).

- [x] **137.** Torres y faros (vista-aliada 1.0.148.0, 9/11/2026)
Una unidad con «Build» parada en tierra libre (sin camino, ciudad ni sitio) ofrece, al seguir apretando el botón
de construir: camino, **torre de vigía** y, si hay agua al lado, **faro costero**. Cada uno cuesta la mitad de
fundar una ciudad. Probar en Warlords3, con niebla activada:
- que se dibuje en la casilla y descubra el mapa alrededor (torre 5 casillas, faro 6), también para tu aliado;
- que los defensores parados ahí ganen +1 de fuerza en combate;
- que si un enemigo entra en la casilla, la obra pase a ser suya;
- que se conserve al guardar y cargar la partida, y en una partida en red.
Decime si el precio (la mitad de una ciudad) te parece bien o cuánto querés que cueste.

- [ ] **136.** Trampas sobre trampas gastadas y constructores en red (vista-aliada 1.0.147.0, 9/11/2026)
**Trampas.** Ahora se puede sembrar una trampa nueva encima de una gastada (el agujero con humo), sea tuya o de
otro jugador, también dentro de una ciudad. La nueva es tuya, queda oculta y cuesta lo mismo que una trampa común.
Apilar dos trampas en la misma casilla ya se podía desde la 1.0.124.0, con estas condiciones:
- la de abajo tiene que ser **tuya** y **seguir activa** (le queda al menos una explosión);
- hay que tener al líder del grupo **parado sobre ella**;
- en una **ciudad** no se apila (lo pediste el 4/11: una sola trampa por casilla de ciudad);
- el tope es 2.
Si cuando no pudiste se daba alguna de esas condiciones, contame cuál, y la cambio.
**NA_157:** la tabla de pozos y trampas estaba llena (64 de 64, con 49 trampas). Desde la **1.0.147.0**, con la
tabla llena, la trampa nueva toma el lugar de una trampa gastada de cualquier parte del mapa (ese agujero desaparece).
**Constructores en red.** Una partida guarda su propia copia de las armas del momento en que se creó; la carpeta
ARMY nueva solo vale para partidas **nuevas**. En dia-noche3.SAV (la del 8/11) y en NA_157 no hay ninguna unidad con «build»:
ni Dwarf Sappers, ni Royal Sappers, ni Scavens, etc. Y las Archers de esa partida no traen el bono.
Ojo: en ARMY\goblins.ARM, «build» quedó como bono de **combate** y no como de **movimiento**: así no construye.
1. Actualizador, opción **9**: vista-aliada tiene que quedar en **1.0.147.0**, en todas las PC.
2. Trampas: sembrá una, hacela explotar hasta que quede el agujero con humo, y sembrá otra encima. Tiene que
   cobrarse y quedar oculta para los demás.
3. Constructores: empezá una partida **nueva** (en red), con un bando que tenga alguna de esas unidades. Con el
   líder del grupo sobre pasto, en el menú de órdenes tiene que aparecer «Build».
Resultado:

- [ ] **42.** Leer el anexo «Cómo juega la computadora» (25/10/2026)
Abrí `manual\Anexo-IA.pdf` (22 páginas). Explica cómo ataca, defiende, explora, produce, hace diplomacia y cumple misiones la
computadora, y qué le agrega el parche. Cada afirmación dice si está VERIFICADO (en el código o en las tandas) o INFERIDO.
15. Marcá lo que no coincida con lo que viste jugando contra la computadora.
16. Fijate en el capítulo 16 («Lo que todavía no se sabe»): si querés que se investigue algo de ahí, decímelo.
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
17. Partida nueva en esta PC con **dos jugadores humanos** (A y B), con misiones de héroe activadas, incluida la
   dificultad **Hard**.
18. Con A, construí una trampa (como en la tarea 26) en tierra, a unas 5 a 15 casillas de donde va a andar el héroe de B.
19. Con B, pasá al lado de la trampa hasta que salga «You have discovered the trap …».
20. Con el héroe de B pedí misiones **Hard** en un templo varias veces (o en turnos distintos): alguna vez tiene que
   salir «Escort trap-disarming team to Afland02» (con el nombre de esa trampa), y el texto «… must escort a
   trap-disarming team to the trap Afland02.».
21. Mandá a la trampa un ejército barato de B (no volador): tiene que morir y la misión seguir. Llevá el héroe de B
   caminando a una casilla al lado: la misión tiene que quedar **cumplida** y dar el premio.
22. Si podés, repetí con una segunda trampa y que la detone A (o un tercero): mientras le queden explosiones la misión
   de B sigue; cuando la gastan del todo (tres veces) sin B, tiene que **fracasar** al turno siguiente. Y otra vez llegando con el héroe volando: no tiene que cumplirse hasta que llegue por tierra.
23. Anotá abajo qué viste (si el nombre de la misión entra bien en su ventana).
Resultado:

# Hecho

- [x] **167.** Muro dañado (vista-aliada 1.0.192.0, 11/11/2026; desde la 1.0.192.0 el humo es nuboso y más blanco (antes a rayas); la muralla es gris azulado suave, mezclado con el pardo de antes, con puertas marrones y la abierta negra; antes el daño era un dibujo de torre redonda y quedaba raro sobre tramos rectos y puertas). Lo que hay que ver ahora: el daño sigue la forma real del bloque (almenas que faltan, con el pasto visible detrás; agujeros y grietas solo sobre la piedra) y no pasa a las torres vecinas sanas. En `C:\Warlords3`, actualizar el parche y restaurar BUILD01.SAV. Atacar un bloque del muro rojo con un ejército chico, que mate algunos arqueros y pierda (o se retire). Según los arqueros muertos que acumula el bloque, la torre tiene que verse: con 6 a 11, almenas rotas y grietas; con 12 a 17, además manchas de hollín y **humo animado** que sube; con 18 a 23, más daño y más humo. Con 24, el bloque cae y no queda nada. Reparar el bloque (botón «Build», renglón 7) lo tiene que dejar sano otra vez. En red, las dos PC tienen que ver el mismo daño. Anotar lo que se vea mal (por ejemplo, el humo cortado arriba). — **Hecho 11/11/2026:** el daño, el humo nuboso (1.0.192.0) y el color de la muralla se ven y se comportan bien.
- [x] **161.** Pausa en red, otra vez (vista-aliada 1.0.181.0, 10/11/2026). En las dos PC, opción 9 del Actualizador (parche 1.0.181.0 o posterior) y partida en red con DarklordAV.exe. Pausar desde el menú del disquete y apretar Espacio (o Esc) en una PC: esa PC tiene que salir de la pausa; anotar si la otra sale sola. Si sigue sin salir: anotar si el puntero del mouse se mueve y si Windows dice que el juego «no responde». Hecho 10/11/2026: en red con la notebook, Espacio/Esc levantan la pausa; el mouse nunca dejó de funcionar.
- [x] **160.** Red: pausa y elegir unidades en la notebook (vista-aliada 1.0.180.0, 10/11/2026). En las dos PC, actualizar el parche (opción 6) y abrir una partida en red con DarklordAV.exe. (a) Pausa: pausar desde el menú del disquete; el cartel dice «Partida en pausa: Espacio o Esc reanuda». Apretar Espacio (o Esc) en una PC: esa PC sale de la pausa en el acto; anotar si la otra también sale sola o si hay que apretar Espacio también en ella. (b) Unidades: anotar en cuál PC no se pueden elegir (¿solo la notebook?, ¿es la anfitriona o la invitada?), si pasa desde el primer turno o después de algo (pausa, construir, clic derecho), y si en esa misma notebook se pueden elegir en una partida de un solo jugador (sin red). Con eso alcanza para ubicar la falla. Hecho 10/11/2026: (b) la notebook ya elige unidades; (a) la pausa siguió sin levantarse con Espacio ni Esc → sigue en la 161.
- [x] **145.** IA: los ejércitos abandonados vuelven a jugar (9/11/2026)
Desde la 1.0.162.0 la computadora en prueba (la nueva) vuelve a mover a los ejércitos que había dejado quietos
fuera de las ciudades: al empezar su turno los junta y les da una tarea (atacar, explorar o volver a una ciudad).
La original sigue igual. Es el primer cambio de juego de esta serie: hay que ver si gana más o menos.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.162.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**. Una tanda alcanza.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado: tandas 150 y 151 (19 partidas completas). Hecho 10/11/2026: los ejércitos abandonados vuelven a moverse (los quietos bajaron a menos de la mitad), pero la computadora nueva pasó de ganarle a la original a perder (puesto 3,07 contra 2,64; 4,1 ciudades contra 5,0). Lo corrijo yo; ver ia\PENDIENTE-ia-economia.md, paso 4.9.

- [x] **135.** IA: cuántos ejércitos quedan «huérfanos» fuera de las ciudades (9/11/2026)
La 1.0.145.0 no cambia cómo juega la computadora: solo anota, de los ejércitos que la computadora dejó de mover,
cuántos quedaron sin grupo (nunca más los mueve) y cuántos tienen grupo pero no les tocó jugar.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.145.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**. Una tanda alcanza.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado (9/11/2026): tandas 148 y 149 (las de la 1.0.161.0), 10 partidas. Casi todos los ejércitos que la
computadora deja de mover quedaron sin grupo: nunca más los mueve. Cuestan el 4 % del ingreso en la original y el 8 %
en la nueva. Próximo: que vuelvan a jugar (tarea 145).

- [x] **130.** IA: quién mueve a los ejércitos que quedan fuera de las ciudades sin tarea (8/11/2026)
La 1.0.141.0 no cambia cómo juega la computadora: solo anota, de los ejércitos que terminan el turno fuera de una
ciudad sin tarea, si les tocó jugar y quién los movió. Con eso se sabe cuáles están ociosos de verdad.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.141.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**. Una tanda alcanza.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado (9/11/2026): tanda 147, 10 partidas. Casi todo lo que se paga de más por ejércitos afuera sin tarea
(5 % del ingreso en la original, 8 % en la nueva) es de pilas que la computadora ni siquiera mueve en su turno.
Próximo: ver por qué las saltea.

- [x] **134.** Pergamino de alianza como columna propia, del tamaño del escudo (8/11/2026)
1. Actualizador: opción **9** (vista-aliada **1.0.144.0** o posterior) y Visor de historia **1.0.20.0** o posterior.
2. Terminá una partida con dos bandos aliados (o abrí `NA_2_36.SAV` en el Visor y el botón del resultado).
3. En la ventana del final, el pergamino tiene que aparecer a la derecha del nombre del bando, alineado como una
   columna más y de la misma altura que el escudo, no como superíndice. VPs, Armas, CITIES y GOLD se corren a la
   derecha sin pisarse.
Resultado (8/11/2026): pergamino en columna propia, del alto del escudo; confirmado por el usuario.

- [x] **133.** Visor de historia: fecha, Armas y alianzas en el resultado (8/11/2026)
1. Actualizador: Visor de historia **1.0.21.0** o posterior (el título de la ventana lo dice).
2. Abrí una partida terminada de `Warlords\HISTORY` (por ejemplo `NA_2_36.SAV`) y el botón del resultado.
3. Tiene que decir arriba «Partida finalizada» con la fecha, en letra Microsoft Sans Serif negra normal, la columna **Armas** entre VPs y CITIES, el
   pergamino de alianza al lado del escudo de los que terminaron aliados (en NA_2: Coprofagos y Dog Tribe) y abajo
   «corresponde a la partida "NA_2"».
4. Las armas y alianzas salen de la última guardada de esa partida en HISTORY; la fecha, de cuándo se escribió el
   archivo `.FIN`. Fijate si los números te parecen razonables para cómo terminó.
Resultado (8/11/2026): fecha, Armas, alianzas y nombre de la partida en el Visor; título en Microsoft Sans Serif negra (1.0.21.0). Confirmado por el usuario.

- [x] **132.** Sello nuevo de Army List (8/11/2026)
1. Actualizador: opción **9** (vista-aliada **1.0.143.0** o posterior).
2. Army List en un bando sin unidades prohibidas: arriba a la derecha tiene que verse el sello dorado «CERTIFIED» con
   la estrella azul en el centro, en lugar de la medalla. Fijate si se lee bien a ese tamaño.
Resultado (8/11/2026): el sello «CERTIFIED» se ve muy bien; es el resultado esperado.

- [x] **131.** Sello de Army List en un bando con unidades prohibidas (8/11/2026)
1. Actualizador: opción **9** (vista-aliada **1.0.142.0** o posterior).
2. Abrí la partida guardada donde viste el sello en un bando con armas fuera de regla, y Army List.
3. Pasá con las flechas de un bando con medalla a ese bando: la medalla tiene que desaparecer, y en su lugar quedar el
   fondo del pergamino, sin manchas. Volvé al bando anterior: la medalla vuelve.
4. Abrí Army List directamente en el bando con unidades prohibidas (cerrá y volvé a abrir estando en su turno, o
   elegilo primero): no tiene que haber medalla.
Resultado (8/11/2026): el sello aparece y desaparece según el bando; corregido.

- [x] **129.** Ventana de fin de partida (8/11/2026)
1. Actualizador: opción **9** (vista-aliada **1.0.140.0** o posterior).
2. Terminá una partida en red (o cargá una a punto de terminar) hasta que aparezca la ventana con la tabla de bandos.
3. Arriba tiene que decir «Partida finalizada» con la fecha de hoy (por ejemplo 8/11/2026), en letra chica dorada.
4. La tabla tiene la columna **Armas** entre VPs y CITIES, con la cantidad de unidades vivas de cada bando. Fijate
   que los nombres largos de los bandos no se pisen con la columna VPs.
5. Los bandos que terminaron aliados entre sí llevan el pergamino de alianza (el de Diplomacia), chiquito, arriba a
   la derecha del escudo. Los que no tienen aliados, no.
6. Abajo, centrado y encima del botón Done: «corresponde a la partida "NOMBRE"», con el nombre de la partida.
Resultado (8/11/2026): ventana de fin con fecha, Armas, pergamino de alianza y nombre de la partida; confirmado por el usuario.

- [x] **128.** Comparador en el libro, Pausa y sello de Army List (8/11/2026)
1. Actualizador: opción **9** (vista-aliada **1.0.139.0** o posterior) y opción **10** (DarkCompare **1.0.0.6** o
   posterior).
2. Libro: el menú tiene que mostrar **Comparador** debajo de Side Lists. Al elegirlo se abre el Comparador.
   Terminá el turno con el Comparador abierto: se tiene que cerrar solo cuando empieza el turno siguiente.
3. Disquete: ya no están **Chat Mode** ni **EMail Statistics**; en el lugar de Chat Mode está **Pausa**.
4. En una partida en red con otra PC: **Pausa** en una de las dos. En las dos aparece arriba «Partida en pausa:
   Espacio reanuda» y no se puede jugar. Revisá en `Warlords3\NETSAVES` que haya una partida guardada con
   `_pausa` en el nombre. Apretá **Espacio** en cualquiera de las dos: se reanuda en ambas.
5. Army List: en un bando sin unidades prohibidas por el Validador, arriba a la derecha se ve la medalla. En uno con
   alguna unidad marcada con círculo rojo, la medalla no aparece. Cambiá de bando con las flechas y fijate que
   aparezca y desaparezca según corresponda.
Resultado (8/11/2026): Comparador en el libro, Pausa y sello de Army List; confirmado por el usuario.

- [x] **127.** IA: qué hacen sus ejércitos fuera de las ciudades (8/11/2026)
La 1.0.138.0 no cambia cómo juega la computadora: solo anota qué tarea tenía cada ejército que termina el turno
fuera de una ciudad. Con eso se sabe cuánto se ahorraría guardando en una ciudad solo a los que no tienen nada que hacer.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.138.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**. Una tanda alcanza.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado: (8/11/2026): tanda 145, 9 partidas completas (una se colgó al empezar, sin datos). De los ejércitos de la IA que terminan el turno fuera de una ciudad, 6 o 7 de cada 10 no tenían ninguna tarea registrada; el ahorro posible con ellos es grande (4 % del ingreso en la IA original, 7,6 % en la nueva). Antes de cambiar nada falta saber quién mueve a esos ejércitos: lo averiguo yo en el código.

- [x] **126.** IA: medir cuánto pagan sus ejércitos fuera de las ciudades (8/11/2026)
La 1.0.137.0 no cambia cómo juega la computadora: solo anota, cada turno, cuánto mantenimiento pagan sus ejércitos que
no están en una ciudad (adentro pagan un tercio). Con eso se decide si conviene que deje en las ciudades a los que no
tienen nada que hacer. Solo en las tandas.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.137.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**. Una tanda alcanza.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado (8/11/2026): tanda 144 completa (10 partidas). Los ejércitos de la IA fuera de ciudad pagan el 35 % del mantenimiento; dejarlos en una ciudad ahorraría hasta el 8,5 % del ingreso (15 % al final de la partida en la IA nueva): la idea sigue.


- [x] **125.** IA: freno de producción más flojo (7/11/2026)
La 1.0.136.0 deja salir más tropas que la 1.0.135.0: cuenta la unidad nueva por lo que paga en la ciudad (un tercio)
y frena recién cuando el mantenimiento pasaría del 100 % de lo que el bando cobra (antes, 90 %). Solo en las tandas.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.136.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**. Si podés, dos tandas
   seguidas (20 partidas), como la vez pasada.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado (8/11/2026, tandas 142-143): la computadora quedó mejor ubicada que con el freno anterior (puesto 2,95 contra 3,08 de la original). Las deserciones que volvieron son de bandos que venían perdiendo ciudades, no de fabricar de más. Se queda esta versión.

- [x] **124.** IA: que la computadora no fabrique más tropas de las que puede pagar (6/11/2026)
La 1.0.135.0 hace que una ciudad de la IA nueva no saque la unidad lista si el mantenimiento del ejército pasaría del
90 % de lo que el bando cobra por turno; la unidad espera en la ciudad hasta que alcance. Solo en las tandas.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.135.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado (Claude, 7/11/2026: tandas 140 y 141, 20 partidas): 0 deserciones en la IA nueva (antes 31), pero
perdió la ventaja de puesto (3,10 contra 3,13 de la original). Se afloja el freno en la próxima versión.

- [x] **123.** IA: que la computadora ahorre oro (6/11/2026)
La 1.0.134.0 hace que la IA nueva no compre tipos de unidad ni agrande ciudades si se queda sin reserva para pagar
sus tropas. Solo en las tandas.
1. ~~Cerrá el juego y avisame~~ — hecho: la 1.0.134.0 está publicada (6/11/2026).
2. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.134.0** o posterior.
3. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
4. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado: tanda 138 (1.0.134.0, 10 partidas completas). Hecho 6/11/2026: la IA nueva casi nunca se queda sin oro (turnos con menos de 50: 12 % → 1 %) y termina mejor ubicada; falta frenar la producción, que sigue llevando a la quiebra a algún bando. Ver ia\PENDIENTE-ia-economia.md.

- [x] **121.** IA: ver en qué gasta el oro, compra por compra (6/11/2026)
La 1.0.133.0 anota, solo en las tandas, cada vez que un color gana o gasta oro y en qué.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.133.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado: tanda 137 (1.0.133.0, 10 partidas completas). Hecho 6/11/2026: el oro se va sobre todo en comprar tipos de unidad para las ciudades (61 %); ver ia\PENDIENTE-ia-economia.md, paso 4.1.

- [x] **122.** Simulador de combate en la notebook (6/11/2026)
La 1.0.20.0 arranca con cualquier partida de SAVES y tiene una flecha ▲/▼ que pliega juntos atacante, defensor y terreno.
1. Abrí el simulador, ícono de engranaje → **Buscar actualización**: tiene que instalar la **1.0.20.0** o posterior.
2. Tiene que cargar solo (arriba a la derecha dice cuántas armas hay) sin el error nro. 2.
3. Plegá con ▲ (esquina del panel de terreno) el tablero, y con la otra ▲ los resultados: el tablero entero tiene que entrar en la pantalla. Al cerrar y abrir, lo
   plegado se recuerda.
Resultado: marcada cumplida por el usuario el 6/11/2026.

- [x] **120.** En red: el que es atacado ve la ventana de combate (5/11/2026)
En el turno simultáneo de los humanos, cuando otro jugador te ataca, ahora se te abre la misma ventana de combate que
ve él. Hacen falta dos PC con humanos (por ejemplo, vos y Nico).
1. Actualizador, opción **9**, en las dos PC: vista-aliada tiene que estar en **1.0.132.0** o posterior.
2. Partida en red, los dos humanos. En el turno simultáneo, uno ataca un ejército o una ciudad del otro.
3. En la PC del **atacado**: ¿se abrió la ventana de combate, con el mismo resultado que vio el atacante?
4. Cerrala y seguí jugando un par de turnos: la partida no tiene que «desincronizarse» (las dos PC tienen que ver
   lo mismo en el mapa: ejércitos, ciudades, oro). Anotá si pasa algo raro.
5. Control: un ataque de la **computadora** en su turno se tiene que ver igual que antes.
Resultado: hecho 6/11/2026. Rojo (esta PC) atacó una ciudad del Blanco (notebook): en la notebook se vio el combate en tiempo real y después la ventana de las 4 opciones de la ciudad (ocupar, pillaje, saqueo, arrasar). Al elegir una, el juego responde «ya no sos el dueño de esta ciudad»: el vencido no decide nada y ve lo que hace el enemigo. Se deja así, a pedido del usuario.

- [x] **110.** IA: medir en qué gasta el oro (5/11/2026)
La 1.0.130.0 anota, solo en las tandas, cuánto oro entra y cuánto se paga de mantenimiento cada turno.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.130.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado: tandas 135 y 136 (1.0.132.0, 19 partidas completas). Hecho 6/11/2026: la IA gasta casi todo lo que le sobra; ver ia\PENDIENTE-ia-economia.md, paso 2.

- [x] **111.** Simulador de combate: comparar el «Factor» con DarkCompare (5/11/2026)
El simulador calcula el Factor de cada arma con la misma cuenta que DarkCompare. Para confirmar que da lo mismo:
1. Abrí DarkCompare con la carpeta `C:\Warlords3\ARMY`.
2. Buscá estas armas y anotá su Factor: **Fire Dragon** (FireDrag) tiene que decir **52,2**; **Mountain Wyrm**
   (AmeWyrm) **49,7**; **Wyverns** **46,2**.
Resultado: cumplida (5/11/2026).

- [x] **119.** Simulador de combate 1.0.12.0: relámpago, bola dorada, botón azul, configuración y actualización (5/11/2026)
1. Bajá el simulador de https://github.com/elcoprofago/Simulador-Combate/releases (Simulador-Combate.exe) y abrilo; el título dice **VERSIÓN 1.0.12.0**. Con «INICIAR COMBATE» se abre la ventana de combate (la 1.0.9.0 se colgaba ahí); apretándolo de nuevo con la pelea abierta no se abre otra, se trae al frente la que está. Armá una pelea (tropas, barco, héroe, terreno), cerrá el simulador y abrilo: tiene que aparecer igual.
2. «INICIAR COMBATE» es azul como el escudo azul del juego (más oscuro en los bordes, con brillo), con letra blanca y sombra.
2b. La barra de Velocidad tiene la bola dorada del Visor de historia (se arrastra o se hace clic en el riel).
3. El panel de arriba tiene el fondo de mármol, con el título, la casilla de ordenar y «Carpeta del juego…».
4. Arriba a la derecha está el engranaje de configuración: abre «Configuración — VERSIÓN 1.0.12.0» con «Buscar actualización», los créditos y el correo. «Buscar actualización» tiene que decir que ya tenés la última.
5. Armá una pelea con Blue Dragons (budragon) que mate: el relámpago suena con Lightning.wav.
6. Después de que se publique el parche Alianzas nuevo, en el juego el relámpago también suena con Lightning.wav (el ácido sigue con el zumbido de antes).
Resultado: cumplida (5/11/2026).

- [x] **118.** Simulador de combate: fondo de mármol y rebordes dorados (5/11/2026)
1. En `F:\source\repos\actualizador-warlords\simcombate` escribí `python tablero.py`; el título dice **VERSIÓN 1.0.6.0**.
2. El fondo de la ventana es la textura de mármol del juego, en mosaico.
3. Los paneles, los botones y el cuadro de resultados tienen el reborde dorado del Visor de historia.
4. Las letras de los recuadros FACTOR TOTAL son blancas.
5. «Carpeta del juego…» está al lado de la casilla de ordenar, no en el extremo derecho, y la ventana es más angosta.
Resultado: cumplida (5/11/2026).

- [x] **116.** Simulador de combate: efectos iguales a los del juego (5/11/2026)
1. En `F:\source\repos\actualizador-warlords\simcombate` escribí `python tablero.py`; el título dice
   **VERSIÓN 1.0.4.0**.
2. Armá peleas contra gnolls con cada una de estas tropas de atacante y mirá el efecto cuando matan:
   - Elephants: la roca que se deshace en polvo.
   - Assassins: la daga con sangre.
   - Moonguard: las flechas.
   - Blue Dragons (budragon): el relámpago (contra tropas de más de una vida, un relámpago corto que les quita la mitad).
   - Black Dragons (bkdragon): el ácido.
   - Fire Dragons (firedrag) contra Red Dragons: la calavera.
   - Una tropa sin poder: la explosión.
3. Cada golpe que quita una vida muestra las chispas sobre la tropa golpeada.
4. Hacé la misma pelea en el juego y anotá cualquier diferencia (tropa, qué muestra el juego y qué el simulador).
Resultado: cumplida (5/11/2026).

- [x] **115.** Simulador de combate: efectos por poder, vidas y arrastre (5/11/2026)
   **Los efectos de esta tarea quedaron viejos: probarlos con la 116.** Las vidas (paso 4) y el arrastre (paso 5) siguen valiendo.
1. En `F:\source\repos\actualizador-warlords\simcombate` escribí `python tablero.py`; el título dice
   **VERSIÓN 1.0.3.0**.
2. Atacante: Elephants y Moonguard; defensor: gnolls y un dragón azul (budragon, Lightning). **INICIAR COMBATE**.
3. Fijate: los elefantes muestran el polvo («Trample») con su sonido; los Moonguard, flechas; el dragón azul,
   relámpago. Los dragones negros (bkdragon) tienen Acid. Ojo: el Red Dragons de este juego (rddragon) tiene el
   poder Chaos, no Acid: pelea con espada.
4. Las vidas: puntos verdes/rojos grandes debajo de las dos tropas que pelean, y más grandes en los casilleros.
5. En el tablero, agarrá el «☰ 2» de una fila y soltalo sobre la fila 1: las dos se cambian de lugar en el orden de
   pelea.
6. Anotá si algún efecto no es el que muestra el juego real (tropa y qué efecto debería tener).
Resultado: cumplida (5/11/2026).

- [x] **114.** Simulador de combate: probar los cambios del 5/11 (5/11/2026)
1. En `F:\source\repos\actualizador-warlords\simcombate` escribí `python tablero.py`; el título dice
   **VERSIÓN 1.0.2.0**. Ya no está la fila de carpeta y partida ni «Ciudades del bando».
2. Armá dos pilas y fijate el **FACTOR TOTAL** de cada lado, en el recuadro claro de borde dorado.
3. Marcá y desmarcá «Ordenar las armas por NOMBRE COMÚN»: las listas cambian de orden y lo elegido queda.
4. Apretá «Invertir atacante y defensor»: los dos lados se cambian (armas, cantidades, barco y héroe).
5. **INICIAR COMBATE**: la batalla se ve en el cuadro del dragón del juego, atacante a la izquierda, defensor a la
   derecha y el duelo en el medio, con la espada, la calavera y el relámpago del juego. Probá también «Grande».
6. Anotá qué más querés que se parezca al juego (por ejemplo, el tablero con fondos y botones del juego).
Resultado: cumplida (5/11/2026).

- [x] **113.** Simulador de combate: probar la ventana de combate (5/11/2026)
1. En `F:\source\repos\actualizador-warlords\simcombate` escribí `python tablero.py`; el título dice
   **VERSIÓN 1.0.1.0**.
2. Armá una batalla y apretá **INICIAR COMBATE**: se abre la ventana de combate con las imágenes del juego,
   defensor arriba y atacante abajo, en el orden en que pelean.
3. Mirá la batalla: la unidad que pelea tiene marco dorado, cada golpe pone roja una de sus vidas (cuadritos verdes)
   y la que cae queda tachada. Al final aparecen el ganador y los sobrevivientes (y los muertos, según «Resultados»).
4. Probá el subpanel visual: velocidad, «Efectos», «Sonido» (golpes y muertes con los sonidos de la carpeta FX del
   juego), tamaño «Grande» y «Saltar al final».
5. Anotá si los sonidos te parecen los que usa el juego en cada caso y qué le falta para parecerse a la pelea real.
Resultado: cumplida (5/11/2026).

- [x] **112.** Simulador de combate: probar el tablero (5/11/2026)
1. Abrí una consola en `F:\source\repos\actualizador-warlords\simcombate` y escribí `python tablero.py`.
2. El título dice **SIMULADOR DE COMBATE — VERSIÓN 1.0.0.0** y arriba a la derecha aparece la cantidad de armas,
   barcos, clases, ítems y hechizos.
3. Armá una batalla que conozcas del juego: en cada lado elegí armas y cantidades (el casillero 1 pelea primero),
   un héroe con «Héroe…» si querés, el terreno, y apretá **INICIAR COMBATE**.
4. Fijate si el % y la batalla de muestra te parecen razonables; anotá lo que falte o moleste en el tablero.
Resultado: cumplida (5/11/2026).

- [x] **109.** Visor de historia: ver el «% de mapa explorado» (4/11/2026)
1. Abrí el Visor de historia → configuración → **Actualizar versión**: tiene que quedar en **1.0.18.0**.
2. Abrí una partida con mapa oculto (por ejemplo `ABN_000_29`): arriba aparece «Explorado: xx %» con el
   bando elegido en el minimapa; al tocar otro escudo, cambia el número.
3. Abrí una partida sin mapa oculto: ese renglón no aparece.
4. **Exportar PDF…** de la partida oculta: debajo de los datos, una tabla con cada bando y su porcentaje.
Resultado: cumplida (5/11/2026).

- [x] **108.** IA: medir cuántas veces se le desbandan tropas por falta de oro (4/11/2026)
La 1.0.129.0 anota, solo en las tandas, cada ejército que deserta porque el bando se quedó sin oro.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.129.0** o posterior.
2. Monitor de IA → **Ninguna**, marcá **Scarpart** y **Kor**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre, no instales otra versión del parche. Avisame cuando termine.
Resultado: (Claude, 5/11/2026: tandas 133 y 134, 52 tropas desertaron en 7 casos, siempre con oro 0 y en un
bando que ya estaba perdiendo sus ciudades. Es raro y viene de perder ciudades, no de gastar de más. 3 partidas de
la 134 se colgaron al empezar; la 133 no tuvo ninguna.)

- [x] **106.** Créditos del juego: revisar el listado y, cuando quiera, actualizar el estado (4/11/2026)
  - El listado de todas las personas, empresas y correos de los créditos está en `creditos\LISTADO.md`.
  - El estado actual consultado por internet está en `creditos\ESTADO.md` (última corrida: 4/11/2026).
  - Para volver a consultarlo: abrir una consola en `F:\source\repos\actualizador-warlords\creditos` y
    escribir `python actualizar.py`. Tarda unos 5 minutos y reescribe `ESTADO.md`.
  - Donde diga «OJO: varias fichas posibles», abrir los enlaces y ver cuál es la persona del juego.

- [x] **117.** Simulador de combate: chispas en cada golpe y recuadro del Factor (5/11/2026)
1. En `F:\source\repos\actualizador-warlords\simcombate` escribí `python tablero.py`; el título dice **VERSIÓN 1.0.5.0**.
2. Los recuadros FACTOR TOTAL: fondo negro, letra arena con sombra gris.
3. Elefantes contra gnolls, **INICIAR COMBATE**: cada golpe muestra sus chispas con su sonido; los golpes que quitan
   varias vidas muestran tantas chispas seguidas.
4. Anotá si algo no coincide con el juego.
Resultado: hecho 5/11/2026, «funciona perfecto, ahora sí se ve como en el juego real».
- [x] **100.** IA: convoyes con barcos que solo tienen Carrier (4/11/2026)
Cambio: la prueba de la tarea 90 estuvo mal armada: el barco tenía Landing y Carrier juntos, y así siempre conviene
desembarcar en una playa. Ahora las guardadas **Scarpart_CA** y **Kor_CA** traen el barco con **Carrier solo**, como se
arman los bandos de verdad. La misma serie mide además por qué la computadora nunca reconstruye un puente
derribado: la 1.0.121.0 anota, solo en las tandas, qué la frena cada vez.
6. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.121.0** o posterior.
7. Monitor de IA → **Ninguna**, marcá **Scarpart**, **Kor**, **Scarpart_CA** y **Kor_CA**, Partidas: **10**, tildá
   **serie de 2**, **Nueva tanda**.
8. Mientras corre la serie, no instales otra versión del parche. Avisame cuando termine.
Resultado: (Claude, 4/11/2026: tandas 131 y 132 con la 1.0.128.0, 20 partidas.
Puentes: la computadora casi nunca reconstruye porque **no le alcanza el oro**: reconstruir cuesta lo mismo que
fundar una ciudad (800 en esas partidas) y la computadora suele tener unas 150 monedas; solo el 4 % de los turnos
llega a 800. De 818 veces en que tenía un puente derribado a mano, 770 fueron por el oro. Las dos veces que pasó
todos los controles, una lo reconstruyó (la primera reconstrucción registrada). El puente que viste destruir al
héroe blanco (partida de Kor de la segunda serie, turnos 18 y 21) fue el criterio nuevo de defensa: derribar un
puente que amenaza una ciudad propia.
Convoyes: con Carrier solo, la computadora armó 2 convoyes (antes, ninguno). Se analiza aparte.)

- [x] **107.** Monitor de IA 1.0.22: actualizarlo cuando termine la tanda en curso (4/11/2026)
  - No se pudo publicar porque el Monitor estaba abierto corriendo la tanda 131.
  - Cuando termine: cerrar el Monitor y avisarme «publicá el Monitor 1.0.22».
  - Después, abrirlo y tocar Actualizar. Ver que la lista «Todas las tandas» tenga barra para bajar, y que al
    plegar el panel Tanda (flechita ▼) aparezca grande el cronómetro de la serie.
  Resultado: (Claude, 4/11/2026) publicado el Monitor de IA 1.0.22.


- [x] **77.** En red, los pozos tienen que ser los mismos en las dos PC (vista-aliada 1.0.97.0, 30/10/2026)
Cambio: hasta ahora, en una partida en red cada PC sorteaba sus propios pozos y remolinos. Ahora el anfitrión le
manda los suyos a los demás al empezar (igual que ciudades y ruinas), y si las PC llegan a diferir el juego lo
detecta como cualquier otra desincronización.
9. En **esta PC y en la notebook**: Actualizador, opción **9**; vista-aliada tiene que quedar **1.0.97.0**.
10. Partida **nueva** en red con **Hidden Ruins** y **Discover Ruins**; esta PC de anfitrión, la notebook se une.
11. Con un jugador de cada PC, caminá hasta descubrir un pozo o remolino. Anotá dónde está y fijate en la otra PC
   (si son aliados con vista aliada, o mirando más tarde con el otro jugador): tiene que estar **en la misma casilla**.
12. Mandá un ejército barato a un pozo ya descubierto: tiene que morir en las dos PC, con la misma tumba al lado.
13. Construí una trampa con un ejército con «trap» y que un ejército del otro jugador caiga en ella: tiene que morir en
   las dos PC.
14. Si en algún momento sale un aviso de partida desincronizada, anotá en qué paso.
Resultado (4/11/2026): cumplida, según el usuario. verificado, mismos pozos en mismos lugares

- [x] **105.** Trampa en una ciudad: una sola explosión, sin apilar; Visor abre roads02 (vista-aliada 1.0.126.0, Visor de historia 1.0.16.0, 4/11/2026)
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.126.0**.
2. Abrí **roads02.sav** (Warlords3) y repetí el ataque a la ciudad roja con la trampa: al conquistarla explota una vez y la trampa desaparece.
3. Sembrá una trampa en una ciudad propia y quedate encima: «Build Trap» tiene que quedar desactivado (no se apila).
4. Control: en el campo se siguen apilando dos.
5. Visor de historia: tiene que decir **VERSIÓN 1.0.16.0** y abrir **roads02.sav** (muestra las votaciones).
Resultado (4/11/2026): marcada cumplida. Además, con dos trampas en la ciudad y las demás casillas llenas, las unidades nuevas aparecen sobre las minas sin hacerlas explotar (lo deseado); aclarado en el Manual de vista-aliada 1.0.127.0.

- [x] **101.** Trampa sobre un altar: los bendecidos no quedan paralizados (vista-aliada 1.0.122.0, 4/11/2026)
Cambio: los ejércitos que tienen la cruz celeste del altar ya no quedan paralizados al sobrevivir a una trampa,
igual que en combate. Morir, mueren igual (del 40 al 80 % del grupo).
1. Cuando termine la serie de la tarea 100: Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.122.0**.
2. En una partida de prueba (Warlords3), poné una trampa (bono «trap») en la casilla de un altar y mandá a ella un
   grupo de varios ejércitos que no estén bendecidos.
3. Al explotar: los que sobreviven, ¿tienen la cruz celeste y movimiento normal en el turno siguiente, sin la
   marca de paralizados?
4. Control: una trampa en una casilla común, con otro grupo: los que sobreviven sí quedan paralizados.
Resultado (4/11/2026): marcada cumplida por el usuario.

- [x] **99.** Minimapa de «City Improvements», «Acerca de» legible y trucos desactivados (vista-aliada 1.0.120.0, 4/11/2026)
Cambio: el minimapa de «City Improvements» (y el de las otras pantallas que muestran el mapa chico) ya no dibuja la
calavera de la ciudad convertida en puerto. En el «Acerca de», la versión, la fecha y los créditos van con la misma
letra clara que «Version 1.0.3». Los trucos que se escriben en el chat («If I were a rich man», «Burn baby burn»,
«Not easy being green» y los demás) ya no hacen nada: el mensaje queda como un mensaje común.
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.120.0**.
2. Cargá la partida de la 98. Construí defensas en una ciudad (comando de mejoras) y mirá el minimapa de «City
   Improvements»: ¿desapareció la calavera de la ciudad vieja?
3. Botón del disquete → «Acerca de»: ¿la versión, la fecha y los créditos se leen claros, con la misma letra que
   «Version 1.0.3»? Si no, sacá una captura.
4. Escribí en el chat alguno de los trucos (por ejemplo «Not easy being green»): no tiene que pasar nada raro.
Resultado: 

- [x] **104.** Trampa en una ciudad: se ve encima y explota al conquistarla (vista-aliada 1.0.125.0, 4/11/2026)
Cambios: la trampa se dibuja encima de la ciudad (debajo de los ejércitos). Y el ejército que gana una ciudad y entra
a la casilla de la trampa la hace explotar en ese momento.
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.125.0**.
2. Abrí **roads02.sav** (Warlords3): ¿se ve la mina sobre la ciudad roja?
3. Repetí el ataque del héroe azul: al ganar y entrar a la casilla, ¿explota enseguida?
4. Control: una trampa en el campo se ve como antes, y los ejércitos parados sobre ella se ven encima de la mina.
Resultado (4/11/2026): explotó al conquistar y paralizó al atacante; se vio el humo. Las demás explosiones no se podían consultar → en 1.0.126.0 la ciudad tiene una sola (tarea 105).

- [x] **103.** Trampas: más baratas, apiladas de a dos y dentro de ciudades (vista-aliada 1.0.124.0, 4/11/2026)
Cambios: la trampa cuesta la cuarta parte de fundar una ciudad (menos si un héroe tuyo abarata las ciudades). Parado
sobre tu propia trampa podés sembrar otra encima, como mucho dos por casilla (también minas submarinas): la casilla
explota hasta cuatro veces. Las trampas ya se podían poner en una ciudad: falta verlo en el juego.
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.124.0**.
2. Partida de prueba (Warlords3), con un grupo que tenga el bono «trap»: abrí **Build Trap**. ¿El costo del diálogo
   es la cuarta parte de lo que cuesta fundar una ciudad?
3. Sin moverte, volvé a abrir **Build Trap** y confirmá: ¿se cobra otra vez, **no explota**, y la lupa sobre la
   casilla dice «Two stacked mines. Explosions left: 4 of 4»?
4. Una tercera vez: **Build Trap** tiene que estar apagado (tope de 2).
5. Mandá un grupo enemigo a pisarla cuatro veces (en turnos o pasos distintos): ¿explota las cuatro, y después queda
   como agujero con humo?
6. Ciudades: llevá el grupo a una casilla de una ciudad tuya y sembrá una trampa.
   Contame: ¿se puede?, ¿se ve la mina sobre la ciudad o la tapa la ciudad?, y qué pasa cuando un enemigo
   **conquista** esa ciudad y entra en la casilla (¿explota después del combate?).
7. Control: en el agua (mina submarina), los pasos 3 y 4 igual, con «Two stacked sea mines».
Resultado (4/11/2026): se apilan bien y Build Trap se apaga con la segunda; el costo es el adecuado; en una
ciudad se puede, pero la ciudad la tapaba; al conquistar la ciudad (roads02.sav) el héroe quedó sobre la trampa sin
que explotara, recién al salir y volver. Las dos fallas se arreglaron en 1.0.125.0 (tarea 104).
- [x] **102.** «Acerca de» legible, otra vez (vista-aliada 1.0.123.0, 4/11/2026)
Cambio: en la 1.0.120.0 los datos del parche salían encimados y oscuros. Ahora cada renglón va completo y centrado
en la letra clara de los créditos: «Patch vista-aliada 1.0.123.0, Nov 4, 2026», «Credits: @elCoprofago» y
«Anthropic Claude, 2026».
1. Actualizá vista-aliada a la 1.0.123.0 (opción del Actualizador).
2. Abrí DarklordAV.exe → botón del disquete → «Acerca de».
3. ¿Los tres renglones se leen claros, sin encimarse con otro texto? Si no, sacá una captura.
Resultado (4/11/2026): se ve y se lee bien.

- [x] **90.** IA: ¿cuántos convoyes arma y por qué no más? (vista-aliada 1.0.108.0, 3/11/2026)
Cambio: en la tarea 89 se contaron solo los convoyes que ordena la rutina nueva de la IA (ninguno); los que el
juego arma solo, como los del amarillo que viste, no se anotaban. La 1.0.108.0 anota, solo en las tandas, todo
convoy que se forme y, cada vez que la rutina nueva pudo armar uno y no lo hizo, por qué. Las guardadas sin convoy (Scarpart y Kor) entran para comparar con la misma
versión.
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.108.0**.
2. Monitor de IA → **Ninguna**, marcá **Scarpart**, **Kor**, **Scarpart_CR** y **Kor_CR**, Partidas: **10**, tildá
   **serie de 2**, **Nueva tanda**.
3. Mientras corre la serie, no instales otra versión del parche. Avisame cuando termine.
Resultado: (Claude, 4/11/2026: tandas 129 y 130 con la 1.0.120.0, 20 partidas, 8 con convoy posible. Ningún
convoy formado por ninguna vía. En 187 ocasiones en que la computadora pudo intentarlo, 164 no lo hizo porque el
destino no tenía un puerto cerca: un convoy solo atraca en puertos, y casi siempre iba a desembarcar en una playa.
Prueba mal armada (usuario): el barco tenía Landing y Carrier juntos, y con Landing siempre conviene la playa; se
repite con Carrier solo en la tarea 100.
Puntos y ciudades: iguales a las partidas sin convoy. El amarillo (1.0.106.0, visto en directo por el usuario):
eran barcos enlazados; como en esas partidas la rutina de la IA no ordenó ninguno, se enlazaron al chocar con un
barco propio lleno en un movimiento común, no a propósito.)

- [x] **98.** Ciudad convertida en puerto: sin calavera ni mejora equivocada, y el «Acerca de» nuevo (vista-aliada 1.0.119.0, 4/11/2026)
Cambio: la ciudad convertida en puerto ya no aparece en el minimapa, y la pantalla de ciudades no la toma por una
ciudad arrasada. Lo que pasó en la 97: al tocar ahí, el juego no encontraba una ciudad para reconstruir y, como
hace siempre que se toca un lugar sin ciudad, abría la mejora de defensas de tu ciudad más cercana (la del sur).
Eso último es del juego original y sigue igual. Además, en el botón del disquete → «Acerca de», en lugar de la
memoria van el parche, su versión y fecha, y los créditos.
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.119.0**.
2. Cargá la partida de la 97 (o convertí otra ciudad en puerto). En el minimapa, ¿desapareció la calavera?
3. Tocá donde estaba la ciudad vieja como hiciste en la 97: ¿ya no ofrece reconstruirla?
4. Botón del disquete → «Acerca de»: ¿se lee «Patch vista-aliada  1.0.119.0, Nov 4, 2026», «Credits:
   @elCoprofago» y «Anthropic Claude, 2026», y no hay líneas cortadas? Si algo se ve raro, sacá una captura.
Resultado:
4/11/2026: el minimapa principal ya no muestra la calavera. Quedaba la calavera en el minimapa de «City
Improvements», y el «Acerca de» se veía bien pero con los valores muy oscuros. Además pediste desactivar los trucos
del chat. Todo eso va en la 99.
- [x] **97.** Convertir una ciudad propia en puerto, y el puente nuevo más caro (vista-aliada 1.0.118.0, 3/11/2026)
Cambio: el renglón del menú de órdenes ahora se llama **Build**. Con cualquier grupo parado en una ciudad tuya que
toque agua (no hace falta constructor), ofrece **City into a port**: la ciudad desaparece y en el agua de al lado
queda un puerto «Port <nombre de la ciudad>». Cuesta el doble de lo que tu bando paga por fundar una ciudad. No se
ofrece si es tu última ciudad. Además, el puente nuevo cuesta ahora por casilla 30 % de una ciudad sobre agua y
60 % sobre lava (lo que pediste en la 96).
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.118.0**.
2. En Warlords3, con un grupo dentro de una ciudad tuya junto al agua (que no sea la única que tenés), elegí
   **Build**. Si en el grupo hay un constructor y te ofrece primero un camino o un puente, contestá **No** y volvé a
   elegir **Build** hasta que aparezca «City into a port».
3. Aceptá: ¿el oro baja el doble de lo que cuesta fundar una ciudad? ¿La ciudad desaparece del todo (nombre,
   ruinas, bandera)? ¿Cómo se ven las 4 casillas donde estaba? Tendrían que parecerse al terreno de alrededor; si
   algo se ve raro, sacá una captura.
4. ¿Aparece el puerto en el agua de al lado? ¿Se puede embarcar y desembarcar ahí? ¿Qué nombre muestra?
5. Guardá, salí y volvé a cargar la partida: ¿sigue igual (sin ciudad, con el puerto)?
6. Puente nuevo sobre agua de una casilla: ¿cuesta 30 % de una ciudad? (Sobre lava, 60 %.)
7. Si podés, en red con otra PC: ¿la conversión se ve igual en las dos?
Resultado (4/11/2026): la ciudad se convirtió en puerto con su nombre y su imagen, operable; el precio quedó más
equilibrado. Dos fallas: en el minimapa la ciudad vieja seguía como calavera (ciudad arrasada), y al pedir reconstruirla
la pantalla de ciudades ofrecía subir defensas y las subió a +3 en otra ciudad, bien al sur. Arreglado en 1.0.119.0
(tarea 98).

- [x] **96.** Construir un puente sobre agua y derribarlo (vista-aliada 1.0.117.0, 3/11/2026)
El renglón del menú de órdenes ahora se llama **Road/Bridge**. Parado en la orilla con un Dwarf Sappers o Peasants
(con el bono «build»), si en línea recta hay de 1 a 8 casillas de agua o lava que terminan en tierra, ofrece un
puente en esa dirección (flecha roja; texto «Building a bridge»). Precio por casilla: 15 % de una ciudad sobre agua,
25 % sobre lava; se cobra entero.
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.117.0**.
2. En Warlords3, con un constructor en la orilla de un lago o río, elegí **Road/Bridge**. Si ofrece primero un camino
   en tu casilla, contestá **No** y volvé a elegir **Road/Bridge**: pasa a la dirección siguiente.
3. Aceptá el puente: ¿se ve entero, con sus dos puntas, y se puede cruzar?
4. Con otra unidad al lado del puente, **Raze**: ¿se derriba entero y quedan dibujados solo los restos de las dos
   orillas (no en medio del agua)? Después **Build** (reconstruir): ¿vuelve entero?
5. Si podés, probá uno largo (4 o más casillas). Si el precio te parece caro o barato, decime cuánto.
Resultado (3/11/2026): se construye bien, sea tramo corto o largo, las flechitas rojas se ven bien, se destruye como los otros puentes, y el rebuild lo regenera entero al costo correcto. Lo unico a modificar es la tarifa, que se presenta muy barata: cambiamos el costo de cada casilla a 30% sobre agua y 60% sobre lava (hecho en la 1.0.118.0, se prueba en la 97).
- [x] **95.** Precio del camino según el terreno (vista-aliada 1.0.116.0, 3/11/2026)
Cambio: cada casilla cuesta una fracción fija de lo que **ese bando** paga por fundar una ciudad: **25 %** en
montaña, **15 %** en colinas, desierto, hielo/nieve y piso de mazmorra, **5 %** en los demás terrenos. Los
atributos que abaratan la ciudad (como Artificer) abaratan el camino en la misma proporción.
1. Ya está instalada en C:\Warlords3. En otra PC: Actualizador, opción **9**; vista-aliada **1.0.116.0**.
2. Mirá cuánto le cuesta a tu bando fundar una ciudad (Rebuild City/Site) y pedí caminos: en montaña tiene que
   costar la cuarta parte; en colinas, 15 %; en llanura o bosque, 5 %. Al aceptar, el oro baja eso mismo.
3. Repetilo con un bando **con Artificer** y otro **sin Artificer**: el del Artificer tiene que pagar menos.
Resultado (3/11/2026, partida roads02): rojo con Artificer, blanco con Engineering y azul sin nada pagaron cada
uno un precio distinto por casilla de camino en montaña. Sin cuelgues.
- [x] **94.** Camino en montaña a un cuarto del precio de una ciudad (vista-aliada 1.0.113.0, 3/11/2026)
1. Ya está instalada en C:\Warlords3. En otra PC: Actualizador, opción **9**; vista-aliada **1.0.113.0**.
2. Con el mismo bando de antes (ciudad a 800 con Artificer), pedí un camino en una montaña vecina: el diálogo
   tiene que decir **200gp**, y al aceptar el oro tiene que bajar 200.
Resultado (3/11/2026): reemplazada por la 95 (precio en porcentaje según el terreno).
- [x] **93.** Menú de la torre: «Rebuild City/Site» (vista-aliada 1.0.112.0, 3/11/2026)
1. Ya está instalada en C:\Warlords3. En otra PC: Actualizador, opción **9**; vista-aliada **1.0.112.0**.
2. En una partida, tocá el botón de la torre: el renglón que decía «Build City/Site» tiene que decir
   **«Rebuild City/Site»**, y al elegirlo tiene que hacer lo mismo que antes.
Resultado (3/11/2026): el menú dice «Rebuild City/Site». El camino en montaña costaba 400 (la mitad de una ciudad de
800 con Artificer): pedido bajarlo a un cuarto (tarea 94).

- [x] **92.** Flecha en el diálogo del camino; dónde dice «build» la torre (vista-aliada 1.0.111.0, 3/11/2026)
Cambio: el diálogo «Building a road» muestra una **flecha roja** (del propio juego) hacia la montaña elegida, en
vez de la palabra north/east/south/west. Cuando el camino va donde está parado el grupo, no hay flecha.
1. Ya está instalada en C:\Warlords3. En otra PC: Actualizador, opción **9**; vista-aliada **1.0.111.0**.
2. Repetí la 91 (camino en montaña vecina): en el diálogo tiene que verse la flecha apuntando a la montaña; con
   **No** y otro **Build Road**, la flecha tiene que girar a la montaña siguiente.
3. El «build» de la torre: no encuentro ningún otro texto «Build» que el juego muestre (el que tenía el archivo
   ya dice «Rebuild»). Sacá una **captura de pantalla** donde se vea ese «build» y guardala en
   `F:\source\repos\actualizador-warlords\captura-build.png`; con eso lo ubico.
Resultado (3/11/2026): las flechas rojas quedaron excelentes. El «build» era el renglón «Build City/Site» del menú de
la torre (tarea 93). Pedido: bajar el precio del camino en montaña. El minimapa no muestra el paso nuevo: si es
mucho trabajo, queda así.

- [x] **91.** Abrir un paso de montaña con un camino (vista-aliada 1.0.110.0, 3/11/2026)
Cambio: un grupo con una unidad con el bono **Build** que no pueda poner camino donde está parado (porque ya hay
camino) puede ponerlo en una **montaña vecina** (arriba, derecha, abajo o izquierda). Con camino, la montaña se
cruza. Precio: la mitad de lo que cuesta fundar una ciudad, por casilla. Así se abre un paso: camino, avanzar,
camino…
1. Ya está instalada en C:\Warlords3. En otra PC: Actualizador, opción **9**; vista-aliada tiene que quedar
   **1.0.110.0**. Fijate que el botón de la torre (reconstruir ciudades) ahora diga **Rebuild** y se lea entero.
2. Partida **contra la computadora** con el bando que tiene **Build** en Dwarf Sappers y Peasants (tarea 88).
3. Llevá el grupo hasta el pie de una montaña y poné un camino donde está parado (como en la 88).
4. Abrí el menú de órdenes: **Build Road** tiene que seguir encendido. Elegilo: tiene que salir «Building a road
   north» (o east, south, west: la dirección de la montaña) con el precio.
5. Si hay más de una montaña al lado, decí **No** y volvé a elegir **Build Road**: tiene que ofrecer la siguiente
   dirección.
6. Aceptá: el camino tiene que aparecer **sobre la montaña**, el oro bajar en ese precio, y el grupo tiene que
   poder **entrar** en esa casilla. Seguí 2 o 3 casillas montaña adentro: el camino tiene que verse continuo.
Resultado (3/11/2026): el camino sobre montaña alta funciona bien y el diálogo se entiende. Pedido: flechas en vez
de las palabras (hecho en la tarea 92). El botón de la torre **sigue diciendo «build»** (ver tarea 92).

- [x] **89.** IA: ¿usa los barcos de convoy? (paso 5.1 de PENDIENTE-ia-innovaciones, 3/11/2026)
Cambio: armé dos guardadas nuevas, **Scarpart_CR** y **Kor_CR**, iguales a Scarpart y Kor pero con el barco de los 8
bandos con los bonos **Landing** y **Carrier**. En 648 partidas la computadora nunca armó un convoy porque ninguna
guardada traía ese barco; ahora se va a ver si lo hace y si le conviene.
1. Actualizador, opción **9**: vista-aliada tiene que estar en **1.0.106.0** (no hace falta instalar nada nuevo).
2. Monitor de IA → **Ninguna**, marcá solo **Scarpart_CR** y **Kor_CR**, Partidas: **10**, tildá **serie de 2**,
   **Nueva tanda** (dos tandas de 10, una tras otra).
3. Mientras corre la serie, no instales otra versión del parche. Avisame cuando termine.
Resultado:
Resultado: (Claude, 3/11/2026: tandas 127 y 128, 20 partidas. El juego sí tomó los bonos: la computadora partió 62
veces un grupo que no entraba en el barco, cosa que antes nunca había pasado. La rutina nueva no ordenó ningún
convoy; los que se arman solos (el usuario vio al amarillo usarlos varias veces) no se contaban. Se miden en la
1.0.108.0: tarea 90.)

- [x] **88.** Construir un camino en el juego (vista-aliada 1.0.106.0, 3/11/2026)
Cambio: un grupo con una unidad que tenga el bono de movimiento **Build** puede poner un camino en la casilla donde
está parado, pagando en oro según el terreno (llanura barata, colinas más cara). No se puede en agua, montaña, ni
donde ya hay camino, ciudad o sitio. El camino empalma solo con los caminos y puentes vecinos. La computadora no
construye. Puentes, pasos de montaña y la conversión de ciudad en puerto vienen después.
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.106.0**.
2. Abrí el editor **war3ed_av.exe** → Edit Army Data, y a **Dwarf Sappers** y a **Peasants** de tu bando ponéles
   **Build** en un **Move Bonus** libre. Guardá el bando.
3. Empezá una partida **contra la computadora** con ese bando y juntá un grupo con Dwarf Sappers o Peasants.
4. Llevalo a una llanura sin camino y abrí el menú de órdenes del grupo: el último renglón, **Build Road**, tiene que
   estar encendido. Fijate también que **todos los renglones del menú se lean bien, sin encimarse** (ahora son 13).
5. Elegilo: tiene que salir «Building a road» con el precio; aceptá. El camino tiene que aparecer bajo el grupo, el
   oro bajar en ese precio, y el grupo moverse más rápido por ahí.
6. Hacé un tramo de 3 o 4 casillas, con una curva y pegado a un camino que ya exista: tiene que verse **continuo**,
   sin cortes ni piezas que no empalmen.
7. Controles: sobre un camino, en una ciudad, en un barco y con un grupo **sin** esas unidades, Build Road tiene que
   estar apagado.
8. Guardá, salí y volvé a cargar: los caminos nuevos tienen que seguir ahí.
Resultado (usuario, 3/11/2026): los caminos nuevos se construyen y se muestran bien. Pasos de montaña y puentes todavía no se pueden: es lo esperado, vienen en las etapas siguientes de PENDIENTE-construcciones.

- [x] **87.** IA: ¿va a cortar el puente que amenaza su ciudad? (vista-aliada 1.0.105.0, 2/11/2026)
Cambio: la computadora (solo la IA de prueba en las tandas) ahora busca los puentes por donde un enemigo en guerra
puede llegar a una ciudad suya, y manda una pila a cortarlo. Antes esperaba a pasar por casualidad junto al puente, y
eso casi nunca ocurría (tarea 86).
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.105.0**.
2. Monitor de IA → **Ninguna**, marcá solo **Borderlands**, Partidas: **10**, **Nueva tanda**.
3. Mientras corre la tanda, no instales otra versión del parche. Avisame cuando termine.
Resultado: (Claude, 3/11/2026: tandas 124 a 126, 30 partidas: la computadora cortó 51 puentes para defender sus
ciudades, antes 0; los puntos no bajaron. Cumplida.)

- [x] **86.** IA: ¿por qué no corta puentes? (vista-aliada 1.0.103.0, 2/11/2026)
Cambio: en las tandas, cada vez que una pila de la computadora termina junto a un puente y no lo corta, el juego anota
el motivo. No cambia cómo juega: solo mide.
1. Cortá la tanda que está corriendo (la 122: repite una medición que ya se hizo, no suma) con el botón del Monitor
   y cerrá el juego; avisame: instalo y publico la 1.0.103.0 (con el juego abierto no se puede).
2. Cuando te avise que está publicada: Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.103.0**.
3. Monitor de IA → **Ninguna**, marcá solo **Borderlands**, Partidas: **10**, **Nueva tanda**.
4. Mientras corre la tanda, no instales otra versión del parche. Avisame cuando termine.
Resultado: 2/11/2026, tanda 123: 10 partidas válidas, 0 derribos. Solo 12 veces una pila quedó junto a un puente sin cortarlo, y las 12 el puente era su camino (motivo 2).

- [x] **81.** IA: ¿corta puentes para defenderse? (vista-aliada 1.0.99.0, 1/11/2026)
Cambio: la computadora ahora derriba un puente cuando un enemigo en guerra está por cruzarlo hacia una ciudad suya
(antes no lo hacía nunca: en ~600 partidas, 0 derribos). En la tanda lo usan solo los colores con la IA de prueba,
así se compara con la de siempre en las mismas partidas.
1. Actualizador, opción **9**: vista-aliada tiene que quedar **1.0.99.0** en C:\Warlords3.
2. Monitor de IA → **Ninguna**, marcá solo **Borderlands** (no Border_Alianzas), Partidas: **10**, **Nueva tanda**.
3. Avisame cuando termine. Si ves un puente que se cae solo con un ejército enemigo cerca, anotá el turno.
Resultado: hecho 2/11/2026. Tandas 117 a 119 (25 partidas válidas; la 119 se cortó porque se instaló la 1.0.101.0 a mitad de tanda): **ningún derribo**, ni de la IA de prueba. Hubo guerra en las 25. Sigue la tarea 86, que mide por qué no se activa.

- [x] **85.** Ver en el Visor cómo terminó la partida (Visor de historia 1.0.15.0, 2/11/2026). Después de la 84. Hecho 2/11/2026.
Cambio: en el panel de arriba del Visor hay un botón **«Resultado»**. Se activa solo si al lado del .SAV está el
`.FIN` de la partida (las que están en `HISTORY`). El cartel imita el del juego («Game Over!», SIDE / VPs / CITIES / GOLD).
Ojo: el `.FIN` lo escribe solo el parche 1.0.101.0 o posterior. La partida «eventos2» de la PC anfitriona se jugó en
`C:\Warlords`, que tenía un DarklordAV.exe anterior: pasó a HISTORY pero sin `.FIN`. Las pruebas, en `C:\Warlords3`.
1. Actualizá el Visor: ruedita → «Actualizar versión». Si sale «Failed to remove temporary directory» y otro cartel de
   error (es el defecto de la versión vieja, corregido en la 1.0.7.0), cerralos y abrí el Visor de nuevo a mano. El
   título tiene que decir **VERSIÓN 1.0.15.0**.
2. Abrí con «Abrir…» un .SAV de `C:\Warlords3\HISTORY` de una partida jugada con 1.0.101.0. El botón «Resultado»
   tiene que estar activo.
3. Partida que terminó con victoria (p. ej. «eventos03»): ventana «Resultado», el mismo cartel que mostró el juego, sin
   botón Done: «Victory!» / «Total victory!» con la imagen del castillo, o «Game Over!» con puestos, VPs, ciudades y oro.
4. Partida cerrada con `acuerdo:` (tarea 84, p. ej. «eventos02»): ventana «Final por acuerdo», el papiro del juego con el
   texto en letra manuscrita negra, a la izquierda, y debajo del título, en letra chica bermellón,
   «Terminada por acuerdo/votación al N.º turno».
   En el panel de arriba, «Victoria:» y «Último guardado:» tienen que quedar más cerca del medio.
5. Abrí un .SAV de `SAVES` o `NETSAVES`: el botón tiene que quedar gris.
6. «Abrir…» tiene que arrancar en `HISTORY`; después de abrir una partida de otra carpeta, la próxima vez arranca ahí.
7. El ícono del Visor (el .exe, la barra de tareas y las ventanas) es un trofeo dorado sobre un escudo rojo, con una espada entera y otra quebrada detrás (guerra, alianzas y traiciones).
8. El subtítulo «EVENTS FOR TURN …» del panel de eventos sale más chico y en dorado oscuro.
9. La próxima vez que actualices el Visor (desde la 1.0.7.0 en adelante) no tiene que salir ningún cartel de error.

- [x] **84.** Cómo terminó la partida: archivo .FIN y «acuerdo:» por chat (vista-aliada 1.0.101.0, 2/11/2026). Hecho 2/11/2026.
Cambio: al pasar una partida a HISTORY, el juego deja al lado un archivo `<partida>.FIN` que dice cómo terminó (podio,
victoria aliada o acuerdo). Y para cerrar una partida de común acuerdo, cualquiera escribe en el chat
`acuerdo: <lo que acordaron>`. El Visor lo muestra desde la 1.0.6.0 (tarea 85).
1. En **las dos PC**: Actualizador, opción **9**; vista-aliada tiene que quedar **1.0.101.0**.
2. Partida en red corta. En la PC anfitriona escribí en el chat: `acuerdo: empate entre Rojo y Azul`.
3. La otra PC tiene que ver ese mensaje en el chat como cualquier otro.
4. En la PC donde lo escribiste: en `HISTORY` tienen que estar los .SAV de la partida y `<partida>.FIN`. Abrí el .FIN
   con el Bloc de notas: dice `cierre=acuerdo`, el turno y `texto=empate entre Rojo y Azul`.
5. Mirá la otra PC: anotá si la partida quedó en `NETSAVES` (esperado) o pasó a `HISTORY`.
6. Si en algún momento juegan una partida hasta la victoria, abrí su .FIN: `cierre=podio` o `cierre=aliada` y una
   línea `bando=` por bando. Anotá si los puntos coinciden con los del cartel del juego.
Resultado:

- [x] **83.** Partidas terminadas a la carpeta HISTORY (vista-aliada 1.0.100.0). Hecho 2/11/2026: partida en red a 4 turnos, «victoria por más puntos»; se creó HISTORY en las dos PC y la partida salió de NETSAVES en ambas.

- [x] **82.** Probar el Visor de historia 1.0.4.0 (1/11/2026)
1. Abrí `F:\source\repos\actualizador-warlords\ia\Visor-Historia.exe` y con «Abrir…» elegí un .SAV de una partida real del ranking
   (carpeta SAVES del Warlords actualizado, no la de Warlords3: ahí están las de prueba).
2. Arriba: nombre, turnos, victoria, mapa y «Último guardado» tienen que coincidir con la partida.
3. Abrí la misma partida en el juego, Historia de sucesos: compará algunos turnos (sucesos, ciudades del minimapa).
   Los colores del terreno son aproximados; lo que importa es lo explorado y las ciudades.
4. Escribí un nombre de ciudad en «Buscar» (abajo a la izquierda): los turnos con coincidencias se marcan en dorado en la barra.
5. Probá «Exportar PDF…» y abrí lo que genera.
6. Pasá el mouse por los botones: se ponen naranja suave.
7. Ruedita (abajo a la derecha): elegí «Textura», una imagen cualquiera, Aceptar; el fondo de la ventana pasa a
   mosaico. Volvé a «Color liso» y probá otro color. Al cerrar y abrir el visor tiene que recordar lo elegido.
8. Luces arriba a la derecha: con una partida de un jugador se enciende «Single»; con una de NETSAVES, «Multi».
   (Las del ranking guardadas en SAVES encienden «Single»: el juego las guarda así.)
9. Minimapa: compará con el mapa de la misma partida en el juego. El agua es celeste, los cerros grises y los
   bosques verdes. Anotá si alguna mancha verde no es bosque en el juego, o si falta algún bosque.
Resultado (2/11/2026): tildada por el usuario, sin observaciones anotadas.

- [x] **80.** Visor de historia: ¿el texto de los sucesos es igual al del juego? (1/11/2026)
Resultado (1/11/2026): capturas del History of Events de dia-noche4, rondas 1, 3, 8 y 10. Los 26 renglones
coinciden letra por letra con `ia\historia.py`.

- [x] **78.** IA: ¿ya no cae en los pozos que ve? (vista-aliada 1.0.97.0, 30/10/2026; hecha el 1/11/2026)
Cambio: la computadora ya no camina por un pozo, remolino o trampa que su bando descubrió (tampoco para levantar el
ítem de un caído). Vos sí podés entrar a propósito, eligiendo esa casilla como destino.
1. Actualizador: instalá vista-aliada **1.0.97.0** en C:\Warlords3.
2. Monitor de IA → **Ninguna**, marcá solo **hex_pozos_PV_control** (la misma de la tarea 70), Partidas: **10**,
   **Nueva tanda**.
3. Avisame cuando termine. Si ves héroes que se quedan quietos junto a un pozo turno tras turno, anotalo acá.
Resultado: (Claude) tanda 114, con 1.0.98.0: 9 partidas válidas (1 colgada). **0 caídas** en pozos ya vistos;
en la tanda 105, con la IA de antes, fueron 5 (17 muertos). El PV no bajó: 11.5 contra 11.8, una diferencia de
-0.3 ± 0.4, dentro del azar.

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
