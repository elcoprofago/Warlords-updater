# Puntos de victoria (PV) y podio del juego original

Leído del código de Darklord.exe (13/10/2026) y comparado con una partida real de 8 bandos IA, 15 turnos.

## PV de cada bando (rutina 0x440840)

Solo para bandos en juego (registro del jugador +0 y +1 distintos de 0); los eliminados tienen 0.

    PV = ciudades + héroes vivos + oro_ajustado / 100      (división entera, resultado entre 0 y 100)

- **ciudades**: ciudades del bando que no están arrasadas (rutina 0x4407d0: dueño en +0xa5, +0xa4 > 0).
- **héroes vivos**: ejércitos vivos del bando en la ranura 0x10.
- **oro_ajustado**: el oro si es menor que 600; 600 si está entre 600 y 1000; por encima de 1000,
  600 + (oro − 1000) / 10. En la práctica, el oro casi no suma: 1 PV cada 100 de oro hasta 600 y después
  casi nada.

Los PV quedan en la tabla de palabras 0x5643c8 + bando*2, y las ciudades en 0x536b20 + bando*2.

## Podio (rutina 0x482d77, pantalla "Game Over!")

- **Ordena por la condición de victoria del escenario** ([0x560e52]):
  - 0 o 2: por PV;
  - 1: por ciudades;
  - 3: por oro.
- El orden es de mayor a menor, por inserción estable, recorriendo los bandos por número de color. Si dos
  bandos empatan en el criterio, queda primero el de número de color menor. **No hay otro criterio de desempate.**
- **Empate:** el bando empatado con el anterior **comparte su puesto**. En pantalla se le deja el número en
  blanco, y el puesto siguiente salta. Ejemplo: 1, (1), 3, 4, (4), 6.
- **"A copy of the results"**: el mismo cuadro se escribe en EMail_Results.Txt (formato
  `%d. %-16s %-16s VPs: %-3d Cities: %-3d Gold: %ld`, o sin número si es un empate).

## Comprobación con la partida del 13/10/2026 (15 turnos; naranja y rojo eliminados)

| Bando      | PV | Ciudades | Oro | Héroes que hacen falta para cerrar la cuenta |
|------------|----|----------|-----|-----------------------------------------------|
| Nirndorf   | 14 | 12       | 150 | 1 |
| Nordheim   | 14 | 12       | 135 | 1 |
| Wistenport | 7  | 6        | 76  | 1 |
| Gallia     | 5  | 3        | 164 | 1 |
| Skellheim  | 5  | 4        | 164 | 0 |
| Drakenburg | 4  | 3        | 5   | 1 |

La cuenta cierra en los seis bandos con 0 o 1 héroe. IA.CSV muestra 0 o 1 héroe por bando al empezar el turno 15; la
pantalla final es posterior, así que la comparación es por cantidad plausible, no exacta. Los puestos que muestra la pantalla (1, en blanco, 3, 4,
en blanco, 6) coinciden con la regla de empates.

## Para la base de pruebas

- El ganador de una partida es el primer puesto según la condición de victoria del escenario.
- Con empate en el primer puesto hay varios ganadores. Que el desempate por color decida quién figura arriba es
  un artefacto: no debe contarse como victoria de una IA sobre la otra.
- Como ganar ciudades pesa casi todo y el oro casi nada, las destrezas que suben ciudades son las que mueven el
  podio.
