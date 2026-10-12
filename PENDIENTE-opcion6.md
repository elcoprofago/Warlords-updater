# Pendiente: la opción 6 (ACTUALIZAR TODO EL JUEGO) no debe pisar lo propio de cada PC

Decidido con el usuario el 12/10/2026 (sesión de puente-warlords). Todavía no está implementado.

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

**Sin decidir:** `SCENARIO` (mezcla escenarios de fábrica con propios; el usuario no lo mencionó). Propuesta:
copiar solo los que falten, sin pisar los existentes. Confirmarlo con el usuario.

## Cómo

`Descomprimir` ya acepta un filtro de «no pisar si existe» (lo usan las opciones 7, 8 y 10 con los `.ini`) y
devuelve lo conservado para mostrarlo. Para `Saves`, una pregunta S/N antes de descomprimir. Cambiar el texto
del aviso «reemplazará completamente el contenido» por lo que de verdad hace. Probar en una carpeta de juguete
con `W3_JUEGO` y un zip chico, con un elemento de control de cada clase (no se pisa / se pregunta / se
reemplaza). Después subir versión y `.\tools\compilar-actualizador.ps1 -Publicar`.
