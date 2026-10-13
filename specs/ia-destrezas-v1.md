# IA de los bandos — destrezas, primera versión

## Objective
Que los bandos manejados por la IA de Darklord.exe (Warlords 3) jueguen mejor por destreza, no por recibir más
recursos. Es para el clan Plaga Carriers, que hoy le saca ventaja fácil a la IA porque deambula, se desangra en
ataques chicos y arma mal sus grupos. La IA es la misma en single y multi player, así que la mejora vale para ambos.

El éxito se mide con números, no a ojo: en tandas automáticas de partidas en escenarios fijos, los colores con la
IA de prueba superan claramente a los colores con la IA original. Esta primera versión monta esa base de medición
y ataca las tres fallas que el usuario marcó como más graves; las demás vienen en versiones siguientes con la
misma prueba.

## Requirements

### Base de pruebas
1. Cada color puede jugar con la IA original o con la IA de prueba, elegido por un archivo de configuración
   (DATA\IA.INI). Sin ese archivo, el juego se comporta exactamente como el original en todos los colores.
2. Un programa auxiliar juega partidas en tanda sin nadie delante: arranca el juego, abre una partida nueva con los
   8 colores en IA en uno de los escenarios Scarpart, Hexagon o TomeLand (C:\Warlords3\SCENARIO), sin alianzas,
   4 colores con IA original y 4 con IA de prueba; la deja correr hasta que termine (cartel "Game Over" por
   turnos/tiempo o un ganador) o hasta un tope de turnos; cierra el juego y sigue con la próxima.
3. Entre partidas de una tanda se rota qué colores/posiciones de partida tienen cada IA, de modo que en el total
   cada IA haya ocupado cada posición la misma cantidad de veces.
4. Cada turno y por cada bando se registra: oro, ciudades, unidades (cantidad y por tipo), héroes vivos, batallas
   (atacante, defensor, lugar, composición, resultado) y la IA que lo maneja. Todo se acumula en ia\datos.db
   (SQLite) junto con la partida, el escenario, la asignación de IA y el resultado final (VPs, ciudades, oro y
   puesto del cartel "Game Over").
5. Se documenta cómo calcula el juego los VPs y el orden del podio, incluidos los empates, a partir del código del
   exe, y se verifica contra el cartel final de partidas reales de la tanda.
6. Un informe resume una tanda: por IA, promedio de VPs, ciudades, oro y unidades al final, partidas ganadas, y la
   cantidad de "turnos sin progreso" (req. 7) y de "ataques desangrantes" (req. 8).

### Destreza 1 — objetivo claro, con oportunismo
7. Cada grupo de la IA de prueba tiene un objetivo útil (tomar o construir una ciudad, reforzar un sector,
   reagrupar en un punto, alejarse de un vecino más fuerte) y avanza hacia él turno a turno; no retrocede sobre
   sus pasos salvo por una amenaza concreta a sus ciudades o porque el objetivo resultó inalcanzable, y en ese caso
   cambia de objetivo en vez de volver a vagar. Se registra como "turno sin progreso" cada turno en que un grupo no
   se acerca a su objetivo ni lo cumple.
8. Si en su camino (dentro de su movimiento del turno) hay un blanco que puede vencer con alta probabilidad —un
   héroe débil, un grupo chico, una ciudad mal defendida— lo ataca y luego retoma su objetivo.
9. Un bando de la IA de prueba no explora indefinidamente: la exploración es un objetivo con fin (una ruina o zona
   concreta), no un estado permanente.

### Destreza 2 — no desangrarse en ataques chicos
10. La IA de prueba no ataca si su estimación de victoria es baja, salvo un sondeo deliberado: como máximo un
    grupo chico y barato, para ver fuerzas ocultas, y no repetido contra el mismo blanco mientras la información
    siga vigente.
11. Después de perder dos ataques contra el mismo blanco, deja de mandar grupos de a uno: reúne fuerzas en un
    punto cercano y solo vuelve a atacar con un grupo que supere claramente al defensor y cuya composición sea
    distinta de la que perdió; si el blanco no es vital, puede cambiar de objetivo. Se registra como "ataque
    desangrante" cada ataque perdido que repite blanco y composición de uno anterior perdido.

### Destreza 3 — combinar armas y ordenar el combate
12. Al formar un grupo de ataque, la IA de prueba busca eficiencia, no grupos completos: en las primeras fases
    prioriza cantidad; cuando hay héroes poderosos en juego (fase final), calidad.
13. Antes de cada batalla, ordena el grupo según el rival: las unidades más expuestas a las ventajas del defensor
    van atrás. Ejemplo de referencia: dragón + 5 elefantes contra 8 Moonguards (+7 de misiles contra voladores) →
    primero los elefantes, el dragón al final.

## Constraints
- Todo cambio es un parche binario a Darklord.exe (1997, x86, sin red neuronal), generado por
  parches\vista-aliada\build.py, en la línea de los parches existentes (ai_move, ai_conv, ai_free...).
- Las rutinas del juego (combate, decisiones) se pueden ejecutar emuladas con unicorn sobre el estado de un .SAV
  (prueba_emulada.py, prueba_ia*.py) para medir sin jugar.
- Una partida por vez en la PC (no se pueden correr simultáneas). PC: Ryzen 5 5600G, 47 GB RAM.
- La partida debe poder grabarse/registrarse sin intervención humana (lo escribe el propio parche).
- Bandos usados en las tandas: los mejores bandos probados por el clan, 2000 puntos; en modalidad sin voladores,
  sin voladores para todos. La IA sigue eligiendo sus propios puntos de personalidad como hoy.
- Los .PGS definen el bando (regulares, aliados, orden, oro, stack, maná, héroes, barcos), no la personalidad.
- Repo: actualizador-warlords; los commits se hacen desde Windows 10.

## Out of scope
- Que la IA arme su propio bando en "Edit Sides" (lo siguen haciendo los humanos).
- Cambiar cómo la IA reparte los puntos de personalidad; transcribir la matriz de fases y los perfiles del clan.
- Las destrezas 4 a 7 (economía, cuidado del héroe, lectura de reportes y terreno/retirada, salir del aislamiento):
  versiones siguientes, en ese orden, con la misma prueba.
- Construir puertos de salida (sacrificando una ciudad y oro): es una regla nueva del juego para todos, propuesta
  aparte.
- Estrategias concertadas entre IA aliadas y diplomacia de la IA.
- Memoria entre partidas y optimizador de parámetros (etapas 7 y 9 del plan).
- Partidas en mapas aleatorios para la medición.

## Edge cases to handle
- **Sin DATA\IA.INI o con un valor inválido** → ese color usa la IA original; el valor inválido se anota en el registro.
- **El juego se cuelga o no avanza de turno en un tiempo tope** → el auxiliar lo cierra, marca la partida como
  fallida en datos.db y sigue con la siguiente.
- **Partida que no termina** → se corta en el tope de turnos y se usa el estado de ese turno como resultado.
- **Un bando eliminado** → sus turnos siguientes no se registran; en el resultado figura eliminado y en qué turno.
- **Grupo sin objetivo alcanzable (isla sin voladores ni puerto)** → no cuenta como turno sin progreso para la
  destreza 1, pero se registra como "aislado" (insumo para la destreza 7 futura).
- **Empates en VPs** → se registran como el juego los ordena (req. 5).
- **Tanda interrumpida** → las partidas completas ya están en datos.db; al reanudar sigue desde la siguiente.

## Definition of done
- [ ] Sin DATA\IA.INI, una partida con semilla y escenario fijos produce el mismo resultado que el exe original.
- [ ] Con IA.INI, cada color usa la IA indicada (verificado en el registro).
- [ ] El auxiliar juega una tanda de al menos 3 partidas seguidas sin intervención y las deja en ia\datos.db.
- [ ] La rotación de posiciones queda balanceada en el total de la tanda.
- [ ] El cálculo de VPs y podio está documentado y coincide con el cartel "Game Over" en las partidas de la tanda.
- [ ] Un cuelgue simulado (proceso detenido) se detecta, se marca como fallido y la tanda sigue.
- [ ] Una prueba emulada del ejemplo dragón + 5 elefantes contra 8 Moonguards muestra a la IA de prueba con los
      elefantes primero.
- [ ] En 20 partidas (Scarpart, Hexagon, TomeLand), los colores con IA de prueba promedian al menos 20% más VPs y
      20% más ciudades que los de IA original, y ganan más de la mitad de las partidas.
- [ ] En esas 20 partidas, la IA de prueba tiene menos "turnos sin progreso" y menos "ataques desangrantes" que la
      original.
- [ ] El usuario revisó una muestra chica de partidas (TAREAS.md) y no vio nada anormal.

## Open questions
- Tecla real de "Interrupt Game" (prueba pendiente en TAREAS.md).
- Por qué en una misma partida un color parece "inteligente" y otro "tonto": ¿nivel de dificultad por bando,
  personalidad o azar? Se investiga en la etapa de medición.
- Qué bandos exactos usar en cada escenario (los mejores probados del clan): pedirlos al usuario al armar la tanda.
- Si el auxiliar puede iniciar la partida por el parche o tiene que recorrer los menús.
