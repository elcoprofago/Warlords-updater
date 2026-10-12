# Pendiente: la opción 6 (ACTUALIZAR TODO EL JUEGO) no debe pisar lo propio de cada PC

Decidido con el usuario el 12/10/2026 (sesión de puente-warlords).

**Estado:** la parte de la opción 6 está hecha en el Actualizador 1.0.7.0 (`TodoElJuego` y `NoPisar` en
`Actualizador.cs`), probada en carpeta de juguete con `W3_JUEGO` + `W3_FULL_ZIP`. `tools\publicar-full.ps1`
hecho y probado con `-Prueba` (12/10/2026): zip nuevo de 6207 archivos (322 MB) contra 6398 del publicado;
los 191 que deja afuera son todos de la lista «nunca se pisa» (raíz, `DATA`, `.ini`, `.TMP`, `.lnk`,
`Netsaves`, `GOG`, `HERRAMIENTAS`, `Randscen`, `SCENARIO\_BACK`); no agrega nada. `hooks\pre-commit` bloquea
cambiar `NoPisar` sin cambiar el script. **Publicado** el 12/10/2026 (SHA-256 `3BBDABE4…748D7`), verificado bajándolo de nuevo. Nada pendiente.

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
  `DATA`: `PREF.DAT`, `OPTIONS.DAT`, `OPT101.DAT`, `OPTIONS.NET`, `OPT101.NET`, `NETSTAT.TXT`, `VECTOR.TXT`,
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
