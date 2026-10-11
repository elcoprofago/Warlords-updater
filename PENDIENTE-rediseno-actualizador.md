# Pendiente: rediseño del actualizador

Anotado el 11/10/2026, al terminar el botón del Comparador en Edit Side (vista-aliada 1.0.26.0, DarkCompare 1.0.0.5).
Es el plan para una sesión nueva. Frase para retomar: *"Seguimos con PENDIENTE-rediseno-actualizador.md"*.

## Pedido del usuario (textual)

> quiero "rediseñar" ese actualizador, que no esta ya a la altura del parche (quiero mejoar interfaz, mas colores y
> fuentes -ver captura-, a las barras de progreso en las descargas quiero cambiarlas al estilo de las barras que
> implementaste en el repo PostOCRnormalizer, y agregarle el spin indicando que un proceso esta esperando).

Las capturas que mandó: dos terminales oscuras con salida en colores, con las fuentes **"Código fuente Pro"**
(Source Code Pro) y **"JetBrains Mono"**.

## Estado actual

- `source\Actualizador.bat` (464 líneas), compilado a exe con Bat To Exe Converter 4.2
  (`tools\compilar-actualizador.ps1`, que también prueba y publica en la release "Ejecutable"). La versión sale de
  `source\banner.txt` (hoy `V. 1.0.0.10`). Los `*_url.txt` de `source\` van embebidos en el exe.
- Menú (líneas 76-135): 1 ARMY, 2 SPELL, 3 HERO, 4 ESCENARIOS, 5 ITEMS, 6 ACTUALIZAR TODO EL JUEGO (no se combina
  con otras), 7 NUEVA VERSION DEL VALIDATOR, 8 PGS-VISOR, 9 PARCHES, 10 COMPLEMENTOS, 11 SALIR. Varias opciones
  separadas por espacio.
- Rutinas: `:FULLUPDATE`, `:UPDATE`, `:VALIDATOR`, `:VISOR`, `:COMPLEMENTOS`, `:DESCARGAR_A`, `:PARCHES`,
  `:PARCHES_MENU`, `:INSTALAR_PARCHE` (lee `PARCHES.txt` de la release "Actualizador": `id|versión|archivos|texto`,
  y marca cada parche instalado). El hook `hooks\pre-commit` bloquea cambios en `parches\<id>\` sin subir su versión.
- Colores hoy: solo `color 0E/0A/0C/07` de cmd (toda la consola cambia de color a la vez, no por línea).

## Barras y spinner de PostOCRNormalizer (a copiar)

`F:\source\repos\PostOCRNormalizer\MainWindow.xaml.cs`:
- línea 55-66: barra estilo consola `OCR [████░░░░] 50% (3/6)` (`new string('█', lleno) + new string('░', resto)`);
- líneas 28-35 y 1182-1210: spinner `/ - \ |` cada 120 ms, que reescribe la misma línea (`overwrite: true`) y se
  detiene al terminar.
Es WPF; copiarlo es llevar el código al repo nuevo (no queda vínculo con PostOCRNormalizer: regla 9, código
copiado no es contrato).

## Decisión técnica tomada (11/10/2026)

Rehacerlo como programa WinForms de **.NET Framework 4.8** (viene con Windows 10/11: los jugadores no instalan
nada), con aspecto de terminal:
- fondo oscuro, texto en colores por línea (no la consola entera), fuente JetBrains Mono o Source Code Pro
  **embebida** en el exe (licencia OFL, se puede redistribuir) para no depender de que esté instalada;
- descargas con barra de bloques `[████░░░░] 50%` + MB bajados / total, y spinner mientras espera (conectar,
  descomprimir);
- las mismas 11 opciones y la misma lógica (URLs, PARCHES.txt, marca de instalado, HERRAMIENTAS, carpeta del
  juego), sin cambiar el formato de lo publicado: los parches y zips de la release siguen igual.

## Lo que falta averiguar primero (enumerar de una pasada)

1. Recorrer el .bat entero y anotar cada efecto: qué baja, de dónde, adónde descomprime, qué borra o pisa, qué
   archivos de marca escribe y dónde (`%DOWNLOADS%\W3Updater`, `%JUEGO%`), cómo detecta la carpeta del juego.
2. Cómo se compila sin el SDK de .NET (en esta máquina el SDK está en Windows 10; para Framework 4.8 alcanza con
   `csc.exe` de `C:\Windows\Microsoft.NET\Framework64\v4.0.30319` o con el SDK y `net48`).
3. Cómo se publica hoy el exe (release "Ejecutable", nombre `Actualizador-v.<VERSION>.exe`) y si algo baja ese
   nombre fijo (para no romper el enlace de descarga).

## Pruebas (reglas 5 y 6)

Como en la prueba de herramientas 1.0.0.0: el actualizador nuevo contra una carpeta de juego de prueba y un
PARCHES.txt local, con controles (un archivo que no debe tocarse, un parche ya instalado que debe seguir
"instalado", un archivo bloqueado que debe dar error y permitir reintentar). Comparar el resultado con el del .bat
viejo sobre la misma carpeta (referencia sana, regla 4).
