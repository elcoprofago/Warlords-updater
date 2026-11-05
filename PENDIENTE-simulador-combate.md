# Simulador de combate

Pedido del usuario (5/11/2026): un programa aparte que enfrenta dos pilas (atacante y defensor) y muestra la batalla
animada como el juego, para ver quién gana.

## Decisión central: el combate lo resuelve el propio exe, emulado

No se reescribe la fórmula de combate a mano (sería una aproximación y se desactualiza con cada parche). Se ejecuta
el código real de `DarklordAV.exe` con unicorn, como ya hacen `prueba_emulada.py` y `prueba_ia*.py`:

- `0x464ac0` arma la ficha de batalla (unidades, fight order, terreno, ciudad, puente, héroes; llama a `0x467240`
  por unidad y `0x468440` por grupo: habilidades, bono de combate, noche/nightmare, Bridge, Banding).
- `0x464ea0` pelea (llama 19 veces a `0x4deb20`, el dado) y deja el resultado; `0x469ed0` es el armado+pelea real.
- `0x464a30` es el cálculo de probabilidades del propio juego (arma + pelea varias veces): sirve de control.

Ventajas: el resultado es el del juego, incluidas las reglas de vista-aliada, y una pelea emulada tarda
milisegundos, así que se pueden correr 1000 batallas y mostrar el % de victoria además de una batalla animada.

Base del estado: una partida guardada (`.SAV`) cualquiera; el simulador escribe en memoria las dos pilas, el
terreno de la casilla, la ciudad (defensas), día/noche y la cantidad de ciudades de cada bando, y llama a las rutinas.

## Pregunta del usuario: ¿un imperio con pocas ciudades pelea peor?

Sin responder todavía. Ni la pelea ni el armado leen a simple vista una tabla de ciudades, pero leen campos del
registro de cada bando (`0x55cb72`, `0x55cc22..0x55cc2e`, `0x55f030..0x55f048`) que hay que identificar.
Método (regla 4 y 5): misma batalla emulada 10 000 veces con el bando dueño de 40 ciudades y de 2; si el % no cambia,
no hay tal factor. Control: cambiar algo que sí cuenta (una unidad más) tiene que mover el %.

## Etapas
1. **Motor**: `simcombate/motor.py` — carga exe + .SAV, arma dos pilas sintéticas, llama a `0x464ac0`/`0x464ea0`,
   devuelve la secuencia de muertes. Prueba: coincidir con `0x464a30` y con una batalla real del registro de IA.
   Medir el efecto de cantidad de ciudades (pregunta de arriba).
2. **Datos**: armas del `ARMY\*.ARM` activo (orden alfabético), héroes, ítems, hechizos por héroe, barcos, terrenos;
   coeficiente de cada arma tomado de DarkCompare (mismo cálculo; DarkCompare es otro repo: se lee el `.ARM`, no se
   lo enlaza). Coeficiente de héroe: nivel, fuerza, hits, movimiento, ítems + plus fijo si tiene magias.
3. **Tablero** (ventana de comandos): dos paneles gemelos atacante/defensor con check de héroe y cantidad, grilla
   de 8 casilleros numerados (= fight order) con desplegables, desplegable de barco, visor del coeficiente,
   subpanel de héroe (nivel 1-10, habilidades aprendidas, magias del héroe, ítems), subpanel de terreno
   (agua/tierra, tipo, camino/puente/ciudad, día/noche, defensas 1-3, ciudades del bando), subpanel visual
   (velocidad, efectos, sonido, tamaño, resultados: sobrevivientes y muertos / solo sobrevivientes) y botón
   INICIAR COMBATE. Título con «VERSIÓN x.y.z.w» (regla 19).
4. **Ventana de combate**: las dos filas de unidades con sus imágenes del juego, tachando una por una según la
   secuencia del motor, con los sonidos del juego; luego la ventana de resultados.
5. **Aspecto del juego**: fondos, marcos, botones y fuentes sacados de los recursos del juego (PCX/FNT).
6. Publicar como herramienta del Actualizador (como el Visor de historia).

## Estado
- 5/11/2026: plan escrito; ubicadas las rutinas. Próximo paso: etapa 1 (motor).
