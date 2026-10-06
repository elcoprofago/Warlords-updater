# Pendiente vista-aliada: el Army List tiene que coincidir con DarkValidator (reglas 1–25)

Anotado el 5/10/2026. Para el chequeo del Army List (`build.py`).

## Estado (6/10/2026): hecho en vista-aliada 1.0.3.0

- `RULES` con las 25 reglas en el orden del validador. Átomos nuevos `LAND` y `CARR`.
- `armeval` mira los 4 casilleros de Move Bonus igual que `Unit.TieneMoveBonus`: corta en el primer nulo, un byte
  mayor a 0x7f cuenta como '?' (Encoding.ASCII), descarta los no imprimibles, quita espacios y compara sin
  distinguir mayúsculas. El texto del Combat Bonus también lee los bytes mayores a 0x7f como '?'.
- `reglas_ref.py` transcribe ahora DarklordsValidator, reglas 1–25.
- `prueba_reglas.py` arma el parche, emula `armeval` y lo compara con `RulesEngine.Validate` del validador real
  (lo compila con dotnet) y con `reglas_ref.py`. Resultado del 6/10/2026, cero diferencias:
  - los 374 .ARM de `C:\Warlords3\ARMY`;
  - 15 casos de juguete con su control en el límite;
  - 20 000 casos sintéticos alrededor de cada umbral, con textos raros en Move Bonus y Combat Bonus.
- Control de la prueba: contra el parche anterior (1.0.2.0) da 96 diferencias sobre los .ARM reales.

El punto 5 (war3ed_ssg) quedó hecho en vista-aliada 1.0.4.0:
- `build.py` crea `TERRAIN\SUBTYPE\landing.STT` y `carrier.STT`.
- war3ed_ssg arma sus listas con los `*.STT` de esa carpeta.
- Comprobado el 6/10/2026 abriendo "Edit Army" y leyendo los combos:
  - los 4 de Move Bonus y el de Combat Bonus muestran `carrier` y `landing` (19 subtipos);
  - nada se guardó.
- El juego abre un `.STT` solo por nombre, para el texto de un Combat Bonus, así que agregarlos no cambia la partida.

## Objetivo

El usuario no toma decisiones técnicas: dice lo que desea. Lo que desea es que esta app **coincida con la
validación de DarkValidator** (`F:\source\repos\DarklordsValidator`). Una unidad rechazada por el validador se
rechaza acá; una aceptada, se acepta.

Cada app informa a su manera y con su propio grado de detalle. No hace falta copiar la forma de informar del
validador (números de regla, textos), solo el resultado.

## Qué cambió en las reglas (5/10/2026)

- La vieja 7b es ahora la **8**, y las siguientes se corren un número hasta la **25**.
- Reglas nuevas para ships: **8** y **21–25**.
- **Regla 5:** sin "mayor a 2". Cualquier volador con Power "trample" y Move > 20 la viola.
- **Regla 25:** usa el Move Bonus "carrier", que marca al barco de transporte. El .ARM no tiene un dato "Stack".
- **Definiciones corregidas** contra los .ARM reales:
  - volador: "fly" en cualquiera de los 4 casilleros;
  - terrestre: ni volador ni barco;
  - power: también Invisibility va sin valor;
  - move bonus: nombres reales del juego.

## Manifiesto vigente (5/10/2026)

El original está en `F:\source\repos\DarklordsValidator\manifiesto-reglas.txt`. Reglas y definiciones que usa la
validación:

```
1- ningún terrestre puede tener movimientos mayor a 25
2- ningún terrestre con Power "trample" puede tener movimientos mayor a 15
3- ningún terrestre con Power "Siege" mayor a 2 puede tener movimientos mayor a 17
4- ningún volador puede tener movimientos mayor a 40
5- ningún volador con Power "trample" puede tener movimientos mayor a 20
6- ningún volador con Power "Siege" mayor a 2 puede tener movimientos mayor a 22.
7- ningún ship puede tener movimientos mayor a 30
8- ningún ship con move bonus "landing" puede tener movimientos mayor a 12
9- ningún volador con Strength mayor a 3 o hits mayor a 1 puede costar (setup) menos de 600 ni tener Upkeep menor a 10 ni producirse en menos de 3 turnos
10- ningún volador con Strength mayor a 6 o hits mayor a 2 puede costar (setup) menos de 800 ni tener Upkeep menor a 15 ni producirse en menos de 4 turnos
11- ningún volador con Strength mayor a 8 o hits mayor a 3 puede costar (setup) menos de 1000 ni tener Upkeep menor a 20 ni producirse en menos de 5 turnos
12- ningún terrestre con Strength mayor a 3 o hits mayor a 1 puede costar (setup) menos de 300 ni tener Upkeep menor a 5 ni producirse en menos de 2 turnos
13- ningún terrestre con Strength mayor a 6 o hits mayor a 2 puede costar (setup) menos de 400 ni tener Upkeep menor a 10 ni producirse en menos de 3 turnos
14- ningún terrestre con Strength mayor a 8 o hits mayor a 3 puede costar (setup) menos de 500 ni tener Upkeep menor a 15 ni producirse en menos de 4 turnos
15- ningún volador con Power o Combat Bonus puede tener Cost menor de 600 ni tener Upkeep menor a 10
16- ningún volador con Power y Combat Bonus puede tener Cost menor de 800 ni tener Upkeep menor a 15
17- ningún volador con Power mayor a 4 puede tener Cost menor de 1000 ni tener Upkeep menor a 20
18- ningún terrestre con Power o Combat Bonus puede tener Cost menor de 150 ni tener Upkeep menor a 4
19- ningún terrestre con Power y Combat Bonus puede tener Cost menor de 300 ni tener Upkeep menor a 8
20- ningún terrestre con Power mayor a 4 puede tener Cost menor de 500 ni tener Upkeep menor a 12.
21- ningún ship con Power o Combat Bonus puede tener Cost menor de 400 ni tener Upkeep menor a 8
22- ningún ship con Power y Combat Bonus puede tener Cost menor de 600 ni tener Upkeep menor a 12
23- ningún ship con Power mayor a 4 puede tener Cost menor de 800 ni tener Upkeep menor a 18
24- ningún ship con Move Bonus "landing" puede tener Cost menor de 1000 ni tener Upkeep menor a 17
25- ningún ship con Move Bonus "carrier" puede tener Cost menor de 1200 ni tener Upkeep menor a 34

volador: unidad voladora, con Move Bonus "fly" en cualquiera de sus cuatro casilleros de Move Bonus.
terrestre: unidad de tierra, la que no es volador ni barco (ship).
barco (ship): unidad de agua, que no puede transitar por tierra, pero puede contar con "landing" (desembarco en costa) y con bonus "carrier" (barcos de transporte).
power: bono especial de poder. Puede no tener valor (los de tipo "slayer": Dragonslayer, Humanslayer, etc., e Invisibility) o tener un valor de +1 a +7 (ej. Life Drain +5). "Power mayor a N" compara ese valor; un Power sin valor no es mayor a ningún N.
move bonus: hasta cuatro por unidad. Cada uno es el nombre de un subtipo de terreno del juego ("cavern", "desert", "desertdk", "dungeon", "forest", "hills", "ice", "lava", "lthills", "marsh", "mntns", "open", "plains", "road", "wall", "water", "woods"), o "fly" (vuelo), o uno propio del parche: "landing" (desembarco en costa, solo barcos) o "carrier" (barco de transporte, solo barcos). Las mayúsculas no importan.
combat bonus: bono de combate, referido al lugar, con valores. (Ej. Field +2, City +1, Desert +2, etc.).
```

## Datos del .ARM que usa la validación

- Ship: existe `ARMY\<Filename>.SHP`.
- Move Bonus: 4 casilleros de 9 bytes en **0xB2, 0xBB, 0xC4 y 0xCD**. Se descartan los vacíos y "none", y se
  compara sin distinguir mayúsculas.
- Strength 0x9A, Move 0x9B, Hits 0x9C, Turns 0x9D, Upkeep 0x9E, Cost 0xE2 (uint16), Setup 0xE4 (uint16).
- Combat Bonus: nombre en 0xD6 (9 bytes), valor en 0xDF. "None +0" cuenta como vacío.
- Power: código en 0xE6, valor en 0xE8. Sin valor: códigos 13, 16, 44–47, 49, 50 y 55. Código 57 ("None") o
  valor 0 cuentan como vacío.

## Cómo lograrlo en el parche vista-aliada (estado al 5/10/2026)

El chequeo del Army List ("Army List: unidades no permitidas por el validador", `build.py` desde la línea ~994) es
código de máquina dentro del juego. No puede usar el código del validador: tiene que **transcribir** las reglas, y
la coincidencia se comprueba con una prueba contra el validador.

1. **Tabla `RULES`** (`build.py`, línea ~1024): 19 entradas con la numeración vieja.
   - Insertar la regla **8** después de la 7: `[['SHIP'], ['LAND'], ['M>12']]`, con un átomo nuevo `LAND`.
   - Regla 5: quitar `['PV2']`. Queda `[['FLY'], ['HP'], ['TRS'], ['M>20']]`.
   - Agregar 21–25 al final, en orden. Las 21–23 tienen la misma forma que las 15–17 y 18–20, con `SHIP` en
     lugar de `FLY`/`TERR`:
     - 24: `[['SHIP'], ['LAND'], ['C<1000', 'U<17']]`;
     - 25: `[['SHIP'], ['CARR'], ['C<1200', 'U<34']]`, con otro átomo nuevo `CARR`.
   - `armeval` devuelve una máscara de 32 bits (bit i = regla i+1): 25 reglas entran. Revisar todo lo que
     consume la máscara (`armcheck` y el dibujo del icono) por si asume 19 bits.
2. **Átomo `FLY`.** `armeval` escanea solo el primer casillero de Move Bonus (`lea esi, [ebx + 0xb2]` + `al_scan`).
   - Tiene que mirar los cuatro (0xB2, 0xBB, 0xC4 y 0xCD, 9 bytes cada uno). El desembarco libre ("Landing", más
     abajo en `build.py`) ya recorre los cuatro casilleros con `+0xb2 + k*9`.
   - `FLY` se prende si alguno es "fly", `LAND` si alguno es "landing" y `CARR` si alguno es "carrier". Siempre
     sin distinguir mayúsculas: `al_scan` ya baja a minúsculas.
   - Power sin valor: la tabla `ptab` sale de `reglas_ref.NOVALUE`, que ya incluye Invisibility (16).
3. **`reglas_ref.py`** transcribe en Python las reglas viejas. Hay que pasarlo a las 25 reglas y a los 4
   casilleros, o reemplazar la comparación por una contra el validador mismo (prueba de abajo).
4. **Versión.** `hooks/pre-commit` bloquea un cambio en `parches/vista-aliada/` si no sube la VERSION de
   vista-aliada en `parches/parches.txt` en el mismo commit. No cuentan los `.md` ni los `prueba*.py`.
5. **Editor war3ed_ssg.** Falta que "landing" y "carrier" aparezcan como Move Bonus en sus combos editables.
   - Hoy se escriben a mano.
   - El juego ignora los nombres de Move Bonus que no conoce, así que "carrier" no cambia nada en partida.
   - Un barco que de verdad lleve 16 unidades es otro asunto, pendiente del parche. Lo investigado indica que el
     motor asume como máximo 8 por casilla en muchos lugares.

Para que la prueba principal compare contra el validador mismo, alcanza un programa de consola chico que
referencie `F:\source\repos\DarklordsValidator\DarklordsValidator.csproj` y escriba, por cada .ARM, los números
de regla que da `RulesEngine.Validate(new Unit(ruta))`. Esa salida se compara con la máscara de `armeval`
(emulado, como en `prueba_emulada.py`).

Orden de trabajo: primero DarkCompare y EditorPGS, cada uno en su sesión; después este parche.

## Cómo probarlo

Reglas globales 5 y 6: caso de juguete con control.

- **Prueba principal: coincidencia con el validador.** Sobre todos los .ARM de `C:\Warlords3\ARMY` (373 al
  5/10/2026) y sobre los casos de juguete, esta app y DarkValidator tienen que aceptar y rechazar exactamente las
  mismas unidades. Cero diferencias.
- Casos de juguete: para cada regla nueva o cambiada, un .ARM que la viole y uno idéntico justo en el límite
  (control, no debe violarla). Por ejemplo:
  - ship con "landing" y Move 13 viola la 8; con Move 12, no;
  - ship con "carrier" y Cost 1199 viola la 25; con Cost 1200 y Upkeep 34, no;
  - volador con Trample +1 y Move 21 viola la 5; con Move 20, no.
- "fly", "landing" o "carrier" en el segundo, tercero o cuarto casillero, o en mayúsculas, se detectan igual que
  en el primero.
- Para el .SHP de un caso de juguete alcanza un archivo vacío llamado como el campo Filename.
- Con los .ARM al 5/10/2026, el validador rechaza:
  - los barcos barge (8, 24), RoyalNav (8, 21, 24), Trirreme (8, 24), boneship, elem_wtr y kraken (21);
  - los voladores FU_power y MC_Gri (5).
  - RoyalNav, Trirreme y barge tienen "landing" solo para probar. Volverán a sus valores anteriores, así que esos
    resultados cambian cuando eso pase.
