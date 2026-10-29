# Pendiente: el Actualizador tiene que dejar el juego completo en una PC limpia (29/10/2026)

Pedido del usuario: el Actualizador debe ser **autosuficiente**. Hoy, con la opción 6 (sola o con la 9), la
instalación queda incompleta. Instalar con el instalador de GOG resolvería lo que falta, pero agrega archivos
de GOG que el juego no necesita: se prefiere que lo resuelva el Actualizador.

## Lo que se vio
- **DirectPlay:** en la notebook del usuario faltaba (es una característica de Windows que viene desactivada).
  Sin DirectPlay el juego no juega en red. El usuario lo instaló a mano el 29/10/2026. El Actualizador no lo
  revisa ni lo instala.
- **Archivos que faltaban** en la PC del usuario cuando el juego pasó a otra carpeta: los puso a mano; la
  opción 6 no los cubrió. **No se sabe todavía cuáles eran.**
- Relacionado (puente-warlords, `PENDIENTE-estabilidad.md`): los OBSOLETOS de vista-aliada recién se borran al
  abrir `DarklordAV.exe`; el Puente compara antes y avisa diferencias.

## Próximos pasos
1. Enumerar de una vez qué necesita el juego para correr: comparar una instalación de GOG limpia (o su
   instalador, extraído aparte con innoextract, sin instalarlo) contra lo que trae `Warlords3_FULL.zip` (su
   índice, ver `PENDIENTE-opcion6.md`). Lo que el juego usa y el zip no trae es lo que falta.
2. Separar lo que es de GOG y el juego no usa (`GOG`, `__support`, `unins000.*`, etc.), para no traerlo.
3. DirectPlay: que el Actualizador lo detecte y lo active
   (`dism /online /enable-feature /featurename:DirectPlay /all`, con permiso de administrador).
4. Probar en una carpeta vacía que la opción 6 sola deje el juego abriendo y jugando en red.

## Avance (29/10/2026)
- **Instalador de GOG:** `E:\GAMES2\DARKLORDS\SETUP\setup_warlords_iii_darklords_rising_1.02_(33560).exe`.
  innoextract 1.9 bajado al scratchpad de la sesión; correrlo lo frenó el bloqueo automático de permisos
  (programa bajado de internet). Falta el permiso del usuario para listarlo/extraerlo.
- **Qué le falta al zip** (índice de `Warlords3_FULL.zip` publicado contra `C:\Warlords3`, sin distinguir
  mayúsculas): 191 archivos, todos de la lista «nunca se pisa». Fuera de PGS, Saves, Netsaves, Randscen,
  HERRAMIENTAS y PARCHES: `AREA.DAT`, `HISTORY.DAT`, `STRAT_L.BMP`, `STRAT_S.BMP`, `keys.w3`, `INTRO.INI`,
  `NET.INI`, `DarklordAV.exe`, `update_log.txt`, el `.lnk`, `desktop.ini`, dos `.tmp` y en `DATA`:
  `COMBAT.DAT`, `IA.INI`, `NETSTAT.TXT`, `OPT101.DAT/.NET`, `OPTIONS.DAT/.NET`, `PREF.DAT`, `VECTOR.TXT`,
  `VMOVEALL.TXT`. El zip no trae nada que la PC no tenga.
- **Causa:** `publicar-full.ps1` confunde «no pisar» con «no publicar». Pero `Extraer` solo conserva los que
  **ya existen** (`File.Exists(dest) && conservar(dest)`), así que publicar un valor inicial de esos archivos
  no pisa nada en ninguna PC: en una PC limpia los deja, en las demás se conservan (como ya se hace con
  `dxcfg.ini`, `SCREEN.INI`, `VIDEO.INI`).
- **DirectPlay:** hecho en el código (`DirectPlay()` en `Actualizador.cs`): al terminar la opción 6 y antes de
  abrir el Puente (13), si falta `SysWOW64\dplayx.dll` ofrece activarlo con `dism ... /all /norestart`
  elevado (3010 = reiniciar). Compila; sin publicar todavía. En esta PC (DirectPlay activo, CBS estado 112)
  `dplayx.dll` está en SysWOW64 y no en System32; **no se midió una PC con DirectPlay apagado** (control
  pendiente: la notebook antes de activarlo ya no sirve, lo activó el usuario).

## Próximo paso
Con el listado de GOG: de esa lista de 191, publicar como valor inicial los que GOG instala, **tomados del
instalador de GOG** (no de la PC de quien arma el zip, que tiene su historial y sus opciones), y no los
propios (`IA.INI`, `update_log.txt`, `.lnk`, `.tmp`, `desktop.ini`). `DarklordAV.exe` lo pone el parche
vista-aliada. Después compilar y publicar el Actualizador, y probar en carpeta vacía (paso 4).
