# Pendiente: la opción 6 (ACTUALIZAR TODO EL JUEGO) no debe pisar lo propio de cada PC

Decidido con el usuario el 12/10/2026 (sesión de puente-warlords).

**Estado:** la parte de la opción 6 está hecha en el Actualizador 1.0.7.0 (`TodoElJuego` y `NoPisar` en
`Actualizador.cs`), probada en carpeta de juguete con `W3_JUEGO` + `W3_FULL_ZIP`. `tools\publicar-full.ps1`
hecho y probado con `-Prueba` (12/10/2026): zip nuevo de 6207 archivos (322 MB) contra 6398 del publicado;
los 191 que deja afuera son todos de la lista «nunca se pisa» (raíz, `DATA`, `.ini`, `.TMP`, `.lnk`,
`Netsaves`, `GOG`, `HERRAMIENTAS`, `Randscen`, `SCENARIO\_BACK`); no agrega nada. `hooks\pre-commit` bloquea
cambiar `NoPisar` sin cambiar el script. **Publicado** el 12/10/2026 (SHA-256 `3BBDABE4…748D7`), verificado bajándolo de nuevo. Republicado el 16/10/2026 (6206 archivos, SHA-256 `D4C586EC…3875B2`) con `ARMYbarcaza.ARM` y `RoyalNav.ARM` editados por el usuario; `DATACOMBAT.DAT` pasó a «nunca se pisa» (lo graba el juego junto con `PREF.DAT`, Actualizador 1.0.8.0). Nada pendiente.

**Lo que trae el zip actual** (6550 entradas, listado leyendo solo el índice del zip por HTTP): trae
`HISTORY.DAT`, `AREA.DAT`, `STRAT_*.BMP`, los 8 de `DATA` de la lista, `Netsaves`, `Email`, `HERRAMIENTAS`,
`GOG`, `__support`, `keys.w3`, `DarklordAV.exe`, `unins000.*`, `update_log.txt`, un `.lnk`, dos `.TMP`,
`Randscen` y `SCENARIO\_BACK` (respaldos de quien lo armó). No trae `PGS`, `Saves` ni `PARCHES`.

**Criterio de los `.ini`:** «todos los `.ini`» se aplicó a todos salvo los de `CAMPAIGN`, `Ereg` y `edpicts`,
que son contenido del juego (`Rules*.ini`) y se reemplazan (confirmado por el usuario, 12/10/2026). Los de `SCENARIO` quedan cubiertos por «solo lo que falta».

## Hoy

`TodoElJuego()` (`source/Actualizador/Actualizador.cs`) baja `Warlords3_FULL.zip` y lo descomprime encima de
`C:\Warlords3`, pisando todo lo que venga en el zip. No borra: lo que no viene en el zip sobrevive. El
riesgo son los archivos que el zip trae con el mismo nombre. Del contenido del zip (454 MB) todavía no se
sacó la lista: hacerlo primero (enumerar antes de iterar) para saber qué de lo siguiente trae de verdad.

## Qué hacer con cada cosa, si ya existe en la PC

**Nunca se pisa:**
- `PGS`: bandos personalizados (usuario).
- `Randscen`: no se pisa, y además no se usa en red (usuario).
- Lo que escribe el juego al jugar: `HISTORY.DAT`, `AREA.DAT`, `STRAT_L.BMP`, `STRAT_S.BMP` de la raíz; en
  `DATA`: `PREF.DAT`, `COMBAT.DAT`, `OPTIONS.DAT`, `OPT101.DAT`, `OPTIONS.NET`, `OPT101.NET`, `NETSTAT.TXT`, `VECTOR.TXT`,
  `VMOVEALL.TXT`. También `Netsaves` y `Email`.
- Lo propio de cada instalación: todos los `.ini`, `keys.w3`, `HERRAMIENTAS`, `GOG`, `__support`,
  `unins000.*`, `update_log.txt`, `.lnk` y `.TMP`.
- `PARCHES` y `DarklordAV.exe`: la versión de cada parche está anotada en `PARCHES\<ID>.txt`; si el zip trae
  un `DarklordAV.exe` más viejo, quedaría el viejo con la anotación del nuevo.

**Se pregunta antes de pisar:**
- `Saves`: puede tener partidas de prueba (usuario).

**Se reemplaza:**
- `CAMPAIGN`: nadie del clan personalizó campañas (usuario).
- `ESCEN`: trae los escenarios nuevos ya editados e instalados (usuario).
- Las carpetas que la spec de puente-warlords dejó «sin clasificar» (`ADVISOR`, `BANEREVG`, `BANESDEM`,
  `DRAKDUM`, `HOK`, `THALAS`, `SSGData`, `MUSIC`, `VIDEO`, `FONTS`, `WORLD`, `Ereg`, `Editors`, `eddata`,
  `edpicts`) y los editores (`war3ed*.exe`, `war3cmpn.exe`): se incluyen en la descarga completa (usuario).
- El resto del contenido del juego: `ARMY`, `HERO`, `ITEMS`, `SPELL`, `CITY`, `TERRAIN`, `RUINS`, `SITES`,
  `SHIELD`, `FLAGS`, `PICTS`, `FX`, `RANDOM`, `SETS`, `CPGS`, el resto de `DATA`, `Darklord.exe`, `.dll` y
  datos de la raíz.

**Se copia solo lo que falta, sin pisar lo existente:**
- `SCENARIO`: mezcla escenarios de fábrica con propios (propuesta aceptada por el usuario, 12/10/2026).

## Quién arma `Warlords3_FULL.zip`

Hoy lo arma el usuario a mano desde su `C:\Warlords3` y lo sube a la release `Actualizador` de
`Warlords-updater`; la opción 6 solo lo baja y lo descomprime. Decidido: un script
`tools\publicar-full.ps1` que lo arme desde `C:\Warlords3`, publique y verifique bajando de nuevo, como
`publicar-parche.ps1`. Tiene que dejar afuera lo que «nunca se pisa» de la lista de arriba: así lo personal
del que lo arma no llega a nadie. `Saves` tampoco va (son las partidas de prueba de quien lo arma). De
`PGS` y `SCENARIO` van solo los archivos que ya trae el zip actual (los de fábrica que eligió el usuario), no
los bandos ni escenarios propios de su PC; `CAMPAIGN` va entera. La opción 6 decide en cada PC qué pisa. Antes de reemplazar el
zip actual, comparar su lista contra la del zip nuevo: lo que tenga el actual y no el nuevo se le muestra al
usuario antes de publicar, porque ese zip es su criterio de qué es esencial.

## Cómo

`Descomprimir` ya acepta un filtro de «no pisar si existe» (lo usan las opciones 7, 8 y 10 con los `.ini`) y
devuelve lo conservado para mostrarlo. Para `Saves`, una pregunta S/N antes de descomprimir. Cambiar el texto
del aviso «reemplazará completamente el contenido» por lo que de verdad hace. Probar en una carpeta de juguete
con `W3_JUEGO` y un zip chico, con un elemento de control de cada clase (no se pisa / se pregunta / se
reemplaza). Después subir versión y `.\tools\compilar-actualizador.ps1 -Publicar`.

## Parte B: desfase entre la opción 6 y los parches (pedido del usuario, 23/10/2026)

**Problema:** `Warlords3_FULL.zip` es una foto de `C:\Warlords3` del día en que se publica; cada parche
(opción 9) publicado después lo deja atrás. Pasó con `RANDOM\Grass` (vista-aliada 1.0.68.0): se corrigió
republicando el zip el 23/10/2026 (5766 archivos, 320 MB, SHA-256 `CBE2534C…09E065`, verificado). Desde ese
día `publicar-full.ps1` deja afuera toda carpeta `back` (`ITEMS`, `HERO`, `SPELL`: experimentos del usuario,
el juego no las usa). Hoy zip y parches coinciden.

**Lo que pidió el usuario:**
1. Que **el propio actualizador** advierta qué quedó viejo (el zip de la opción 6 frente a los parches, o
   lo instalado frente a lo publicado).
2. Que **impida instalar la opción 9 sin haber corrido antes la 6** en esa PC.

**Hecho (23/10/2026, Actualizador 1.0.13.0):** `publicar-full.ps1` publica junto al zip `FULL.txt` (SHA-256
del zip y `ID|VERSION` de cada parche cuyos archivos van en el zip; la versión se comprueba comparando esos
archivos contra el zip del parche publicado, porque `publicar-parche.ps1` no escribe `PARCHES\<ID>.txt` en
`C:\Warlords3`). La opción 6 baja `FULL.txt`, rechaza un zip con otro SHA, y al terminar deja
`PARCHES\_juego-completo.txt` con el SHA y borra la anotación de los parches que el zip pisó con otra versión.
La opción 9 se niega sin esa marca, y avisa si el SHA instalado no es el publicado o si `FULL.txt` trae un
parche más viejo que el de `PARCHES.txt`. Probado en carpeta de juguete (5 casos, con control) y
`publicar-full.ps1 -Prueba` contra `C:\Warlords3` (pasa limpio) y contra un juego con un archivo del parche
alterado (lo marca). Prueba del usuario: tarea 35.

**Datos con que se empezó:** `TodoElJuego()` y la opción 9 en `source/Actualizador/Actualizador.cs`; las versiones
de cada parche en `parches/parches.txt` (con `ARCHIVOS`) y en `PARCHES\<ID>.txt` de cada PC. Hay que decidir
cómo sabe el actualizador que la 6 ya corrió (por ejemplo, una anotación en `PARCHES\` al terminar la 6, con
la fecha/SHA del zip) y cómo compara la fecha del zip contra la de cada parche (la release `Actualizador`
da la fecha de subida del asset). Probar en carpeta de juguete (`W3_JUEGO`, `W3_FULL_ZIP`) con control.

## Parte C: qué archivos de `C:\Warlords3` se pueden borrar (pedido del usuario, 23/10/2026)

Primera pasada (falta compararla contra `GOG\goggame-galaxyFileList.ini`, 3653 archivos de la instalación GOG):
- No los usa el juego: `GOG`, `__support` (subcarpetas vacías), `unins000.*` (desinstalador), `directplay.cmd`
  (se corre una vez), el `.lnk`, `support.ico`, las carpetas `back`.
- Los trajo GOG pero **hacen falta**: `ddraw.dll` + `dxcfg.exe`/`dxcfg.ini` (video en Windows 10/11),
  `winmm.dll` + `libogg/libvorbis*.dll` (música `MUSIC\Track*.ogg` en lugar del CD).
- Del usuario, no del juego: `HERRAMIENTAS`, `PARCHES`.
No se borró nada.

**Comparación contra la lista de GOG (23/10/2026):** `C:\Warlords3` tiene 6188 archivos; 2551 no son de GOG. Casi
todos son contenido del clan (ARMY, HERO, ITEMS, SPELL, ESCEN, PGS, SCENARIO, MUSIC\Track01 y 21-28, SITES F*,
SSGData, archivos de los parches) o lo que escribe el juego al jugar, y hacen falta. De GOG faltan 173: `__redist`
(158, instaladores de DirectX/VC que GOG borra al terminar) y unos pocos sin importancia; al juego no le falta nada.
Se puede borrar sin afectar el juego (unos 8 MB en total):
- `unins000.dat/.exe/.ini/.msg` (desinstalador de GOG, 2,6 MB), `support.ico`, `GOG\` (0,4 MB), `__support\`
  (4 carpetas vacías), el `.lnk` de la raíz si no se usa, `directplay.cmd` (activa DirectPlay en Windows; ya se
  corrió en esta PC, pero hace falta en una PC nueva: conviene no borrarlo de quien arma el zip).
- Las carpetas back: `HERO\back` (85, 3,3 MB), `SPELL\back` (46), `SCENARIO\_BACK` (86, 1,5 MB), `eddata\__BACK` (2).
Decide el usuario (son suyos, no del juego):
- `Scarpart.w3s` de la raíz (28/2/2026, 1,6 MB): **distinto** del de `ESCEN`; el juego carga los de `ESCEN`.
- `DATA\IA*.CSV` e `IA.INI` (registros de las pruebas de IA), `Saves` (32, 12 MB), `Netsaves` (11, 4 MB), `Randscen`.

**Borrado (23/10/2026, pedido del usuario):** `unins000.*`, `support.ico`, `GOG\`, `__support\` y las carpetas back
(`HERO\back`, `SPELL\back`, `SCENARIO\_BACK`, `eddata\__BACK`). Quedan el `.lnk`, `directplay.cmd` y lo de «decide
el usuario». El zip se republicó sin `support.ico` ni `eddata\__BACK` (5763 archivos), para que la opción 6 no
los vuelva a poner; `publicar-full.ps1` ahora reconoce también `__BACK` como carpeta back.
