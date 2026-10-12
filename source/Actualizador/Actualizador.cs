using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;

namespace Actualizador
{
    /// <summary>
    /// El menu y lo que hace cada opcion. Misma logica que el Actualizador.bat hasta la 1.0.0.10 (mismas
    /// direcciones, mismo PARCHES.txt, misma marca de parche instalado en &lt;juego&gt;\PARCHES\&lt;ID&gt;.txt).
    ///   W3_JUEGO        carpeta del juego en lugar de C:\Warlords3 (pruebas)
    ///   W3_PARCHES_URL  lista de parches en lugar de la publicada (pruebas; puede ser un archivo local)
    ///   W3_ESCRITORIO   carpeta de los accesos directos en lugar del Escritorio (pruebas)
    ///   W3_FULL_ZIP     zip local en lugar de bajar Warlords3_FULL.zip en la opcion 6 (pruebas)
    /// </summary>
    sealed class Actualizador
    {
        public static readonly string Version = typeof(Actualizador).Assembly.GetName().Version.ToString();

        const string Release = "https://github.com/elcoprofago/Warlords-updater/releases/download/Actualizador/";

        static readonly HttpClient http = CrearHttp();

        readonly Terminal t;
        readonly string juego, herramientas, temporal, escritorio, parchesUrl, fullZip;

        public Actualizador(Terminal terminal)
        {
            t = terminal;
            juego = Environment.GetEnvironmentVariable("W3_JUEGO") ?? @"C:\Warlords3";
            herramientas = Path.Combine(juego, "HERRAMIENTAS");
            temporal = Path.Combine(CarpetaDescargas(), "W3Updater");
            escritorio = Environment.GetEnvironmentVariable("W3_ESCRITORIO")
                         ?? Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
            parchesUrl = Environment.GetEnvironmentVariable("W3_PARCHES_URL") ?? Release + "PARCHES.txt";
            fullZip = Environment.GetEnvironmentVariable("W3_FULL_ZIP");
        }

        // ================================================================== menu

        public async Task Correr()
        {
            Directory.CreateDirectory(juego);
            Directory.CreateDirectory(temporal);
            while (true)
            {
                t.Limpiar();
                Banner();
                Menu();
                Prompt("actualizador");
                var opciones = Separar(await t.LeerLinea(Paleta.Texto));
                if (opciones.Count == 0) continue;

                var invalidas = opciones.Where(o => !int.TryParse(o, out int n) || n < 1 || n > 13).ToList();
                if (invalidas.Count > 0)
                {
                    Error("Opción inválida: " + string.Join(" ", invalidas) + ". Elige números del 1 al 13.");
                    await Pausa();
                    continue;
                }
                if (opciones.Contains("6") && opciones.Count > 1)
                {
                    Error("La opción 6 no puede combinarse con otras.");
                    await Pausa();
                    continue;
                }

                bool pausa = false;
                foreach (var o in opciones)
                {
                    switch (o)
                    {
                        case "1": await Paquete("ARMY", "ARMY", "army_url.txt"); pausa = true; break;
                        case "2": await Paquete("SPELL", "SPELL", "spells_url.txt"); pausa = true; break;
                        case "3": await Paquete("HERO", "HERO", "hero_url.txt"); pausa = true; break;
                        case "4": await Paquete("ESCENARIOS", "ESCEN", "escen_url.txt"); pausa = true; break;
                        case "5": await Paquete("ITEMS", "ITEMS", "items_url.txt"); pausa = true; break;
                        case "6": await TodoElJuego(); pausa = true; break;
                        case "7": await Herramienta("VALIDATOR", "DarkValidator.zip"); pausa = true; break;
                        case "8": await Herramienta("PGS-VISOR", "PGS-VISOR.zip"); pausa = true; break;
                        case "9": await Parches(); pausa = false; break;
                        case "10": await Herramienta("COMPLEMENTOS", "COMPLEMENTOS.zip"); pausa = true; break;
                        case "11": await AccesosDirectos(); pausa = false; break;
                        case "12": await JugarEnRed(); pausa = true; break;
                        case "13":
                            t.EscribirLinea();
                            Info("Saliendo...");
                            await Task.Delay(400);
                            return;
                    }
                }
                if (pausa) await Pausa();
            }
        }

        void Banner()
        {
            string[][] letras =
            {
                new[] { "██╗    ██╗", "██║    ██║", "██║ █╗ ██║", "██║███╗██║", "╚███╔███╔╝", " ╚══╝╚══╝ " },   // W
                new[] { " █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝" },             // A
                new[] { "██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝" },             // R
                new[] { "██╗     ", "██║     ", "██║     ", "██║     ", "███████╗", "╚══════╝" },             // L
                new[] { " ██████╗ ", "██╔═══██╗", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ " },       // O
                new[] { "██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝" },             // R
                new[] { "██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ " },             // D
                new[] { "███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝" },             // S
            };
            string[] i = { "██╗", "██║", "██║", "██║", "██║", "╚═╝" };
            Color[] fuego =
            {
                Color.FromArgb(0xFF, 0x4D, 0x4D), Color.FromArgb(0xFF, 0x62, 0x47), Color.FromArgb(0xFF, 0x78, 0x42),
                Color.FromArgb(0xFF, 0x8E, 0x3C), Color.FromArgb(0xFF, 0xA4, 0x36), Color.FromArgb(0xFF, 0xBA, 0x30),
            };
            t.EscribirLinea();
            for (int f = 0; f < 6; f++)
                t.EscribirLinea(
                    new Tramo("  " + string.Concat(letras.Select(l => l[f])), fuego[f], true),
                    new Tramo("   " + i[f] + i[f] + i[f], Paleta.Violeta, true));
            t.EscribirLinea(
                new Tramo("  D A R K L O R D S   R I S I N G", Paleta.Naranja, true),
                new Tramo("  ·  ", Paleta.Tenue),
                new Tramo("A C T U A L I Z A D O R", Paleta.Cian, true));
            t.EscribirLinea(
                new Tramo("  v" + Version, Paleta.Verde, true),
                new Tramo("  ·  juego en ", Paleta.Tenue),
                new Tramo(juego, Paleta.Texto),
                new Tramo("  ·  elcoprofago@gmail.com | 2026", Paleta.Tenue));
            t.EscribirLinea();
        }

        void Menu()
        {
            string dHerr = "→ " + herramientas;
            Encabezado("ELIGE LAS ACTUALIZACIONES", "puedes elegir varias separadas por espacio");
            Opcion(1, "ARMY", "→ ejércitos");
            Opcion(2, "SPELL", "→ hechizos");
            Opcion(3, "HERO", "→ héroes");
            Opcion(4, "ESCENARIOS", "");
            Opcion(5, "ITEMS", "");
            Opcion(6, "*** ACTUALIZAR TODO EL JUEGO ***", "sola, no se combina", Paleta.Rojo);
            Opcion(7, "VALIDATOR", dHerr);
            Opcion(8, "PGS-VISOR", dHerr);
            Opcion(9, "PARCHES", "→ " + juego);
            Opcion(10, "COMPLEMENTOS", dHerr);
            Opcion(11, "CREAR ACCESOS DIRECTOS AL ESCRITORIO", "");
            Opcion(12, "JUGAR EN RED", "→ " + Path.Combine(herramientas, "PuenteWarlords"));
            Opcion(13, "SALIR", "", Paleta.Tenue);
            Cierre();
        }

        // ================================================================== opciones

        /// <summary>Opciones 1 a 5: un zip de la release que se descomprime sobre la carpeta del juego.</summary>
        async Task Paquete(string nombre, string zip, string recursoUrl)
        {
            Titulo(nombre);
            var archivo = Path.Combine(temporal, zip + ".zip");
            if (!await Bajar(LeerUrls(recursoUrl), archivo)) return;
            bool ok = await Descomprimir(archivo, juego) != null;
            Borrar(archivo);
            if (ok) Ok(nombre + " actualizado correctamente.");
        }

        /// <summary>
        /// Opcion 6: el juego completo (Warlords3_FULL.zip) sobre la carpeta del juego. Reemplaza el contenido del
        /// juego, pero no pisa lo propio de cada PC (ver <see cref="NoPisar"/>), copia de SCENARIO solo lo que
        /// falta y pregunta antes de pisar partidas de Saves. Lo que no viene en el zip no se toca.
        /// </summary>
        async Task TodoElJuego()
        {
            Titulo("ACTUALIZAR TODO EL JUEGO");
            t.EscribirLinea();
            t.EscribirLinea(new Tramo("  ", Paleta.Texto),
                new Tramo($"  Se reemplazarán los archivos del juego en {juego}  ", Color.White, true, Paleta.FondoAviso));
            Info("No se pisan: tus bandos (PGS), escenarios propios, partidas, opciones del juego, parches,");
            Info("herramientas ni la configuración de esta PC. De SCENARIO solo se agrega lo que falta.");
            t.EscribirLinea();
            if (!await SiNo("¿Confirmas la operación? "))
            {
                Aviso("Operación cancelada.");
                return;
            }
            var archivo = fullZip ?? Path.Combine(temporal, "Warlords3_FULL.zip");
            if (fullZip == null && !await Bajar(LeerUrls("fullupdate_url.txt"), archivo)) return;

            bool pisarSaves = true;
            int saves = PartidasQuePisaria(archivo);
            if (saves > 0)
                pisarSaves = await SiNo($"El paquete trae {saves} partida(s) de Saves que ya tienes. ¿Las reemplazo? ");

            var conservados = await Descomprimir(archivo, juego, null, dest =>
            {
                var rel = dest.Substring(Path.GetFullPath(juego).TrimEnd('\\').Length + 1);
                return NoPisar(rel) || (!pisarSaves && EnCarpeta(rel, "Saves"));
            });
            if (fullZip == null) Borrar(archivo);
            if (conservados == null) return;
            foreach (var g in conservados.GroupBy(r => r.Contains('\\') ? r.Substring(0, r.IndexOf('\\')) : "(raíz)",
                         StringComparer.OrdinalIgnoreCase).OrderBy(g => g.Key, StringComparer.OrdinalIgnoreCase))
                Info($"Se conservaron {g.Count()} archivo(s) tuyos en {g.Key}.");
            Ok("JUEGO COMPLETO ACTUALIZADO.");
        }

        async Task<bool> SiNo(string pregunta)
        {
            t.Escribir(new Tramo("  " + pregunta, Paleta.Amarillo, true), new Tramo("(S/N): ", Paleta.Tenue));
            var r = (await t.LeerLinea(Paleta.Texto)).Trim().ToUpperInvariant();
            return r == "S" || r == "SI" || r == "SÍ" || r == "Y" || r == "YES";
        }

        int PartidasQuePisaria(string zip)
        {
            try
            {
                using (var z = ZipFile.OpenRead(zip))
                    return z.Entries.Count(e => e.Name.Length > 0 && EnCarpeta(e.FullName.Replace('/', '\\'), "Saves")
                                                && File.Exists(Path.Combine(juego, e.FullName.Replace('/', '\\'))));
            }
            catch (Exception) { return 0; }   // zip roto: lo informa Descomprimir
        }

        static bool EnCarpeta(string rel, params string[] carpetas) =>
            carpetas.Any(c => rel.StartsWith(c + "\\", StringComparison.OrdinalIgnoreCase));

        static readonly HashSet<string> RaizPropia = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "HISTORY.DAT", "AREA.DAT", "STRAT_L.BMP", "STRAT_S.BMP", "keys.w3", "update_log.txt", "DarklordAV.exe" };
        static readonly HashSet<string> DataPropia = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "PREF.DAT", "OPTIONS.DAT", "OPT101.DAT", "OPTIONS.NET", "OPT101.NET", "NETSTAT.TXT", "VECTOR.TXT", "VMOVEALL.TXT" };

        /// <summary>
        /// Opcion 6: lo que, si ya existe en esta PC, no se pisa (PENDIENTE-opcion6.md). <paramref name="rel"/> es
        /// relativo a la carpeta del juego. Los .ini de CAMPAIGN, Ereg y edpicts son contenido del juego (Rules*.ini):
        /// esos se reemplazan; los demas .ini son configuracion de la PC.
        /// </summary>
        static bool NoPisar(string rel)
        {
            if (EnCarpeta(rel, "PGS", "Randscen", "Netsaves", "Email", "HERRAMIENTAS", "GOG", "__support", "PARCHES", "SCENARIO"))
                return true;
            string nombre = Path.GetFileName(rel), ext = Path.GetExtension(rel);
            bool enRaiz = rel.IndexOf('\\') < 0;
            if (enRaiz && (RaizPropia.Contains(nombre) || nombre.StartsWith("unins000.", StringComparison.OrdinalIgnoreCase)))
                return true;
            if (string.Equals(Path.GetDirectoryName(rel), "DATA", StringComparison.OrdinalIgnoreCase) && DataPropia.Contains(nombre))
                return true;
            if (ext.Equals(".lnk", StringComparison.OrdinalIgnoreCase) || ext.Equals(".tmp", StringComparison.OrdinalIgnoreCase))
                return true;
            return ext.Equals(".ini", StringComparison.OrdinalIgnoreCase) && !EnCarpeta(rel, "CAMPAIGN", "Ereg", "edpicts");
        }

        /// <summary>
        /// Opciones 7, 8 y 10: un zip de la release que va a &lt;juego&gt;\HERRAMIENTAS, unico alojamiento de
        /// DarkCompare, DarklordsValidator, EditorPGS, votacion y sorteo. Si el zip trae la carpeta HERRAMIENTAS\
        /// en la raiz (COMPLEMENTOS.zip) se le quita, para que no quede HERRAMIENTAS\HERRAMIENTAS. Los .ini que ya
        /// existen no se pisan: son la configuracion de cada PC (votacion.ini guarda la pantalla del jugador).
        /// </summary>
        async Task Herramienta(string nombre, string zip)
        {
            Titulo(nombre);
            var archivo = Path.Combine(temporal, zip);
            if (!await Bajar(new[] { Release + zip }, archivo)) return;
            var conservados = await Descomprimir(archivo, herramientas,
                rel => rel.StartsWith(@"HERRAMIENTAS\", StringComparison.OrdinalIgnoreCase) ? rel.Substring(13) : rel,
                dest => string.Equals(Path.GetExtension(dest), ".ini", StringComparison.OrdinalIgnoreCase));
            Borrar(archivo);
            if (conservados == null) return;
            foreach (var c in conservados) Info($"Se conservó tu {c} (la configuración de esta PC no se pisa).");
            Ok($"{nombre} actualizado en {herramientas}");
        }

        /// <summary>
        /// Opcion 12: Puente Warlords (repo puente-warlords). Deja el cliente en HERRAMIENTAS\PuenteWarlords, o lo
        /// actualiza si PuenteWarlords.txt de la release dice una version mas nueva, y lo abre. Como 7, 8 y 10:
        /// no pisa los .ini (puente.ini guarda el nombre y la clave del jugador).
        /// </summary>
        async Task JugarEnRed()
        {
            Titulo("JUGAR EN RED");
            var exe = Path.Combine(herramientas, "PuenteWarlords", "PuenteWarlords.exe");
            var instalada = File.Exists(exe) ? FileVersionInfo.GetVersionInfo(exe).FileVersion : null;
            var lista = Path.Combine(temporal, "PuenteWarlords.txt");
            string publicada = null;
            if (await Bajar(new[] { Release + "PuenteWarlords.txt" }, lista, sinCache: true, mostrarArchivo: "versión publicada"))
            {
                publicada = File.ReadAllText(lista).Trim();
                Borrar(lista);
            }
            bool bajar = publicada != null && (instalada == null
                || !System.Version.TryParse(instalada, out var vi) || !System.Version.TryParse(publicada, out var vp) || vp > vi);
            if (bajar)
            {
                var archivo = Path.Combine(temporal, "PuenteWarlords.zip");
                if (!await Bajar(new[] { Release + "PuenteWarlords.zip" }, archivo)) return;
                var conservados = await Descomprimir(archivo, herramientas, null,
                    dest => string.Equals(Path.GetExtension(dest), ".ini", StringComparison.OrdinalIgnoreCase));
                Borrar(archivo);
                if (conservados == null) return;
                Ok($"Puente Warlords v{publicada} en {Path.GetDirectoryName(exe)}");
            }
            else if (instalada == null) return;   // no se pudo bajar y no hay ninguno
            else if (publicada == null) Aviso($"No se pudo ver si hay versión nueva; se abre la que tienes (v{instalada}).");
            else Info($"Tienes la última versión (v{instalada}).");
            Process.Start(new ProcessStartInfo(exe) { WorkingDirectory = Path.GetDirectoryName(exe), UseShellExecute = true });
            Ok("Se abrió Puente Warlords.");
        }

        // ------------------------------------------------------------------ 9 PARCHES
        // PARCHES.txt (asset de la release "Actualizador"), una linea por parche:
        //   ID|VERSION|SHA256 del zip|URL del zip|DESCRIPCION
        // La version instalada de cada parche queda en <juego>\PARCHES\<ID>.txt

        sealed class Parche { public string Id, Version, Sha, Url, Descripcion; }

        async Task Parches()
        {
            Titulo("PARCHES");
            var lista = Path.Combine(temporal, "PARCHES.txt");
            if (!await Bajar(new[] { parchesUrl }, lista, sinCache: true, mostrarArchivo: "lista de parches"))
            {
                await Pausa();
                return;
            }
            var parches = File.ReadAllLines(lista)
                .Where(l => l.Trim().Length > 0 && !l.StartsWith("#"))
                .Select(l => l.Split('|'))
                .Where(c => c.Length >= 4)
                .Select(c => new Parche { Id = c[0].Trim(), Version = c[1].Trim(), Sha = c[2].Trim(), Url = c[3].Trim(), Descripcion = c.Length > 4 ? c[4].Trim() : c[0].Trim() })
                .ToList();

            while (true)
            {
                t.Limpiar();
                t.EscribirLinea();
                Encabezado("PARCHES DISPONIBLES", "");
                if (parches.Count == 0)
                {
                    Linea("No hay parches publicados todavía.", Paleta.Tenue);
                    Cierre();
                    await Pausa();
                    return;
                }
                int ancho = Math.Min(56, parches.Max(p => p.Descripcion.Length));
                for (int n = 0; n < parches.Count; n++)
                {
                    var p = parches[n];
                    var inst = VersionInstalada(p.Id);
                    var (marca, estado, color) = inst == null ? ("○", "no instalado", Paleta.Tenue)
                        : inst == p.Version ? ("●", "instalado", Paleta.Verde)
                        : ("◆", $"tienes la v{inst}, hay versión nueva", Paleta.Amarillo);
                    var desc = p.Descripcion.Length > ancho ? p.Descripcion.Substring(0, ancho - 1) + "…" : p.Descripcion.PadRight(ancho);
                    t.EscribirLinea(
                        new Tramo("  │ ", Paleta.Tenue),
                        new Tramo($"{n + 1,3}  ", Paleta.Cian, true),
                        new Tramo(desc, Paleta.Texto),
                        new Tramo($"  v{p.Version,-9}", Paleta.Violeta),
                        new Tramo($" {marca} {estado}", color, true));
                }
                Opcion(0, "VOLVER", "", Paleta.Tenue);
                Cierre();
                Prompt("parches");
                var sel = (await t.LeerLinea(Paleta.Texto)).Trim();
                if (sel == "0" || sel == "") return;
                if (!int.TryParse(sel, out int k) || k < 1 || k > parches.Count)
                {
                    Error("Opción inválida.");
                    await Pausa("ENTER para continuar");
                    continue;
                }
                await InstalarParche(parches[k - 1]);
                await Pausa("ENTER para continuar");
            }
        }

        async Task InstalarParche(Parche p)
        {
            Titulo($"PARCHE {p.Id} v{p.Version}");
            var archivo = Path.Combine(temporal, $"PARCHE-{p.Id}.zip");
            if (!await Bajar(new[] { p.Url }, archivo, sinCache: true)) return;

            // El zip tiene que ser exactamente el publicado: si no coincide no se toca el juego
            string hash;
            using (new Actividad(t, "Verificando que sea el archivo publicado (SHA-256)..."))
                hash = await Task.Run(() =>
                {
                    using (var s = File.OpenRead(archivo))
                    using (var sha = SHA256.Create())
                        return BitConverter.ToString(sha.ComputeHash(s)).Replace("-", "");
                });
            if (!string.Equals(hash, p.Sha, StringComparison.OrdinalIgnoreCase))
            {
                Error("El archivo descargado no coincide con el publicado. No se instala.");
                Borrar(archivo);
                return;
            }
            Ok("Archivo verificado.");

            bool ok = await Descomprimir(archivo, juego) != null;
            Borrar(archivo);
            if (!ok) return;
            Directory.CreateDirectory(Path.Combine(juego, "PARCHES"));
            // mismo contenido que escribia el .bat (">archivo echo version"): la version y un salto de linea
            File.WriteAllText(Path.Combine(juego, "PARCHES", p.Id + ".txt"), p.Version + "\r\n");
            Ok($"Parche {p.Id} v{p.Version} instalado correctamente.");
        }

        string VersionInstalada(string id)
        {
            var f = Path.Combine(juego, "PARCHES", id + ".txt");
            if (!File.Exists(f)) return null;
            try { return File.ReadLines(f).FirstOrDefault()?.Trim() ?? ""; }
            catch (IOException) { return ""; }
        }

        // ------------------------------------------------------------------ 11 ACCESOS DIRECTOS

        sealed class Programa
        {
            public string Exe, Nombre, Descripcion;
            public int Opcion;   // la opcion del menu que lo instala
        }

        static readonly Programa[] Programas =
        {
            new Programa { Exe = "DarkCompare.exe", Nombre = "DarkCompare", Descripcion = "Comparador de armas", Opcion = 10 },
            new Programa { Exe = "DarklordsValidator.exe", Nombre = "Darklords Validator", Descripcion = "Validador de unidades", Opcion = 7 },
            new Programa { Exe = "EditorPGS.exe", Nombre = "PGS-Visor", Descripcion = "Visor de bandos (.PGS)", Opcion = 8 },
            new Programa { Exe = "votacion.exe", Nombre = "Votación", Descripcion = "Votación de la partida", Opcion = 10 },
            new Programa { Exe = "sorteo.exe", Nombre = "Sorteo", Descripcion = "Sorteo de bandos", Opcion = 10 },
            new Programa { Exe = @"PuenteWarlords\PuenteWarlords.exe", Nombre = "Puente Warlords", Descripcion = "Jugar en red", Opcion = 12 },
        };

        async Task AccesosDirectos()
        {
            while (true)
            {
                t.Limpiar();
                t.EscribirLinea();
                Encabezado("CREAR ACCESOS DIRECTOS AL ESCRITORIO", "puedes elegir varios separados por espacio");
                for (int n = 0; n < Programas.Length; n++)
                {
                    var p = Programas[n];
                    bool instalado = File.Exists(Path.Combine(herramientas, p.Exe));
                    bool tiene = File.Exists(Acceso(p));
                    var (estado, color) = !instalado ? ($"no instalado (opción {p.Opcion})", Paleta.Tenue)
                        : tiene ? ("● ya está en el escritorio", Paleta.Verde)
                        : ("○ sin acceso directo", Paleta.Amarillo);
                    t.EscribirLinea(
                        new Tramo("  │ ", Paleta.Tenue),
                        new Tramo($"{n + 1,3}  ", instalado ? Paleta.Cian : Paleta.Tenue, true),
                        new Tramo(p.Nombre.PadRight(21), instalado ? Paleta.Texto : Paleta.Tenue, true),
                        new Tramo(p.Descripcion.PadRight(25), Paleta.Tenue),
                        new Tramo(estado, color, true));
                }
                t.EscribirLinea(new Tramo("  │ ", Paleta.Tenue), new Tramo("  T  ", Paleta.Cian, true), new Tramo("TODOS LOS INSTALADOS", Paleta.Texto, true));
                Opcion(0, "VOLVER", "", Paleta.Tenue);
                Cierre();
                Prompt("accesos");
                var sel = Separar((await t.LeerLinea(Paleta.Texto)).ToUpperInvariant());
                if (sel.Count == 0 || sel.Contains("0")) return;

                List<Programa> elegidos;
                if (sel.Contains("T"))
                    elegidos = Programas.Where(p => File.Exists(Path.Combine(herramientas, p.Exe))).ToList();
                else
                {
                    var malas = sel.Where(s => !int.TryParse(s, out int k) || k < 1 || k > Programas.Length).ToList();
                    if (malas.Count > 0)
                    {
                        Error("Opción inválida: " + string.Join(" ", malas));
                        await Pausa("ENTER para continuar");
                        continue;
                    }
                    elegidos = sel.Select(s => Programas[int.Parse(s) - 1]).Distinct().ToList();
                }

                t.EscribirLinea();
                if (elegidos.Count == 0)
                    Aviso($"No hay programas instalados en {herramientas}. Bájalos con las opciones 7, 8, 10 o 12.");
                foreach (var p in elegidos)
                {
                    var exe = Path.Combine(herramientas, p.Exe);
                    if (!File.Exists(exe))
                    {
                        Aviso($"{p.Nombre} no está instalado: bájalo con la opción {p.Opcion}.");
                        continue;
                    }
                    try
                    {
                        CrearAcceso(Acceso(p), exe, p.Descripcion);
                        Ok($"Acceso directo creado: {p.Nombre}");
                    }
                    catch (Exception ex)
                    {
                        Error($"No se pudo crear el acceso directo de {p.Nombre}: {ex.Message}");
                    }
                }
                await Pausa("ENTER para continuar");
            }
        }

        string Acceso(Programa p) => Path.Combine(escritorio, p.Nombre + ".lnk");

        static void CrearAcceso(string lnk, string exe, string descripcion)
        {
            var tipo = Type.GetTypeFromProgID("WScript.Shell");
            object shell = Activator.CreateInstance(tipo), acceso = null;
            try
            {
                acceso = tipo.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { lnk });
                var ta = acceso.GetType();
                void Poner(string prop, string valor) => ta.InvokeMember(prop, BindingFlags.SetProperty, null, acceso, new object[] { valor });
                Poner("TargetPath", exe);
                Poner("WorkingDirectory", Path.GetDirectoryName(exe));
                Poner("IconLocation", exe + ",0");
                Poner("Description", descripcion);
                ta.InvokeMember("Save", BindingFlags.InvokeMethod, null, acceso, null);
            }
            finally
            {
                if (acceso != null) Marshal.FinalReleaseComObject(acceso);
                Marshal.FinalReleaseComObject(shell);
            }
            if (!File.Exists(lnk)) throw new IOException("Windows no lo guardó");
        }

        // ================================================================== descargar y descomprimir

        static HttpClient CrearHttp()
        {
            var h = new HttpClient(new HttpClientHandler { AutomaticDecompression = DecompressionMethods.None })
            { Timeout = Timeout.InfiniteTimeSpan };
            h.DefaultRequestHeaders.UserAgent.ParseAdd("Warlords3-Actualizador/" + Version);
            return h;
        }

        sealed class ErrorHttp : Exception
        {
            public readonly int Codigo;
            public ErrorHttp(int codigo) : base("error " + codigo) { Codigo = codigo; }
        }

        /// <summary>Baja la primera direccion que funcione. Al fallar una, prueba la siguiente.</summary>
        async Task<bool> Bajar(IList<string> urls, string archivo, bool sinCache = false, string mostrarArchivo = null)
        {
            if (urls.Count == 0)
            {
                Error("Falta la dirección de descarga.");
                return false;
            }
            for (int i = 0; i < urls.Count; i++)
            {
                if (i > 0) Aviso("La dirección principal falló. Probando la alternativa...");
                Info("Descargando " + (mostrarArchivo ?? Path.GetFileName(archivo)) + "...");
                try
                {
                    await BajarUna(urls[i], archivo, sinCache);
                    return true;
                }
                catch (Exception ex)
                {
                    Borrar(archivo);
                    Error(Explicar(ex, mostrarArchivo ?? Path.GetFileName(archivo)));
                }
            }
            return false;
        }

        async Task BajarUna(string url, string archivo, bool sinCache)
        {
            Borrar(archivo);
            using (var act = new Actividad(t, "Conectando con GitHub..."))
            {
                if (!url.StartsWith("http", StringComparison.OrdinalIgnoreCase))
                {
                    // archivo local (solo pruebas, como el W3_PARCHES_URL del .bat)
                    act.Esperar("Copiando " + url + "...");
                    await Task.Run(() => File.Copy(url, archivo, true));
                    return;
                }
                if (sinCache) url += (url.Contains("?") ? "&" : "?") + "t=" + Guid.NewGuid().ToString("N");

                var corte = new CancellationTokenSource();
                HttpResponseMessage resp;
                corte.CancelAfter(TimeSpan.FromSeconds(60));
                try { resp = await http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, corte.Token); }
                catch (TaskCanceledException) { throw new TimeoutException(); }
                using (resp)
                // si GitHub deja de mandar datos 60 s seguidos se corta (cerrar la respuesta aborta la lectura)
                using (corte.Token.Register(() => resp.Dispose()))
                {
                    if (!resp.IsSuccessStatusCode) throw new ErrorHttp((int)resp.StatusCode);
                    long total = resp.Content.Headers.ContentLength ?? 0;
                    act.Bytes(0, total);
                    long n = 0;
                    using (var origen = await resp.Content.ReadAsStreamAsync())
                    using (var destino = new FileStream(archivo, FileMode.Create, FileAccess.Write, FileShare.None, 1 << 16, true))
                    {
                        var buf = new byte[1 << 16];
                        while (true)
                        {
                            corte.CancelAfter(TimeSpan.FromSeconds(60));
                            int r;
                            try { r = await origen.ReadAsync(buf, 0, buf.Length); }
                            catch (Exception) when (corte.IsCancellationRequested) { throw new TimeoutException(); }
                            if (r == 0) break;
                            await destino.WriteAsync(buf, 0, r);
                            n += r;
                            act.Bytes(n, total);
                        }
                    }
                    if (total > 0 && n != total) throw new IOException($"la descarga se cortó ({Actividad.Mb(n)} de {Actividad.Mb(total)} MB)");
                }
            }
        }

        static string Explicar(Exception ex, string archivo)
        {
            if (ex is ErrorHttp h)
                return h.Codigo == 404
                    ? $"No se pudo descargar {archivo}: no está publicado en GitHub (error 404)."
                    : $"No se pudo descargar {archivo}: GitHub respondió con error {h.Codigo}.";
            if (ex is TimeoutException) return $"No se pudo descargar {archivo}: GitHub no responde (se esperó 60 segundos).";
            if (ex is HttpRequestException) return $"Sin conexión con GitHub: {(ex.InnerException ?? ex).Message}";
            return $"No se pudo descargar {archivo}: {ex.Message}";
        }

        /// <summary>
        /// Descomprime pisando lo que haya (como Expand-Archive -Force). Devuelve los archivos conservados
        /// (que no se pisaron por <paramref name="conservar"/>), o null si fallo.
        /// </summary>
        async Task<List<string>> Descomprimir(string zip, string destino, Func<string, string> mapear = null, Func<string, bool> conservar = null)
        {
            Info("Descomprimiendo en " + destino + "...");
            using (var act = new Actividad(t, "Abriendo el paquete..."))
            {
                var progreso = new Progress<long[]>(p => act.Avance(p[0], p[1], $"({p[2]}/{p[3]} archivos)"));
                try
                {
                    return await Task.Run(() => Extraer(zip, destino, mapear, conservar, progreso));
                }
                catch (Exception ex)
                {
                    act.Terminar();
                    Error("No se pudo descomprimir: " + ex.Message);
                    if (ex is EnUso) Aviso("Cierra el juego y las herramientas, y vuelve a intentarlo.");
                    return null;
                }
            }
        }

        sealed class EnUso : IOException
        {
            // 0x80070020: lo tiene abierto otro programa (el juego o una herramienta)
            public EnUso(string archivo, Exception causa)
                : base($"no se pudo escribir {archivo}: " + ((causa.HResult & 0xFFFF) == 0x20 ? "está abierto en otro programa." : causa.Message), causa) { }
        }

        static List<string> Extraer(string zip, string destino, Func<string, string> mapear, Func<string, bool> conservar, IProgress<long[]> progreso)
        {
            var conservados = new List<string>();
            string raiz = Path.GetFullPath(destino).TrimEnd('\\') + "\\";
            Directory.CreateDirectory(raiz);
            using (var z = ZipFile.OpenRead(zip))
            {
                var archivos = z.Entries.Where(e => e.Name.Length > 0).ToList();
                long total = Math.Max(1, archivos.Sum(e => e.Length)), hecho = 0;
                int i = 0;
                var reloj = Stopwatch.StartNew();
                foreach (var e in z.Entries)
                {
                    string rel = e.FullName.Replace('/', '\\');
                    if (mapear != null) rel = mapear(rel);
                    if (string.IsNullOrEmpty(rel)) continue;
                    string dest = Path.GetFullPath(Path.Combine(raiz, rel));
                    if (!dest.StartsWith(raiz, StringComparison.OrdinalIgnoreCase))
                        throw new InvalidDataException("el paquete trae una ruta inválida: " + e.FullName);
                    if (e.Name.Length == 0) { Directory.CreateDirectory(dest); continue; }

                    Directory.CreateDirectory(Path.GetDirectoryName(dest));
                    if (conservar != null && File.Exists(dest) && conservar(dest))
                        conservados.Add(rel);
                    else
                    {
                        try
                        {
                            if (File.Exists(dest)) File.SetAttributes(dest, File.GetAttributes(dest) & ~FileAttributes.ReadOnly);
                            e.ExtractToFile(dest, true);
                        }
                        catch (Exception ex) when (ex is IOException || ex is UnauthorizedAccessException)
                        {
                            throw new EnUso(dest, ex);
                        }
                    }
                    hecho += e.Length;
                    i++;
                    if (reloj.ElapsedMilliseconds > 60 || i == archivos.Count)
                    {
                        progreso.Report(new[] { hecho, total, i, (long)archivos.Count });
                        reloj.Restart();
                    }
                }
            }
            return conservados;
        }

        IList<string> LeerUrls(string recurso)
        {
            using (var s = typeof(Actualizador).Assembly.GetManifestResourceStream(recurso))
            {
                if (s == null) return new string[0];
                using (var r = new StreamReader(s))
                    return r.ReadToEnd().Split('\n').Select(l => l.Replace(" ", "").Trim()).Where(l => l.Length > 0).Take(2).ToList();
            }
        }

        static void Borrar(string archivo)
        {
            try { if (File.Exists(archivo)) File.Delete(archivo); } catch (IOException) { } catch (UnauthorizedAccessException) { }
        }

        static string CarpetaDescargas()
        {
            try
            {
                var id = new Guid("374DE290-123F-4565-9164-39C4925E467B");
                if (SHGetKnownFolderPath(ref id, 0, IntPtr.Zero, out IntPtr p) == 0)
                    try { return Marshal.PtrToStringUni(p); } finally { Marshal.FreeCoTaskMem(p); }
            }
            catch { }
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads");
        }

        [DllImport("shell32.dll")]
        static extern int SHGetKnownFolderPath(ref Guid rfid, uint flags, IntPtr token, out IntPtr path);

        static List<string> Separar(string linea) =>
            linea.Split(new[] { ' ', ',', ';', '\t' }, StringSplitOptions.RemoveEmptyEntries).ToList();

        // ================================================================== pantalla

        void Encabezado(string titulo, string nota)
        {
            t.EscribirLinea(
                new Tramo("  ┌─[ ", Paleta.Tenue),
                new Tramo(titulo, Paleta.Amarillo, true),
                new Tramo(" ]", Paleta.Tenue),
                new Tramo(nota.Length > 0 ? "  " + nota : "", Paleta.Tenue));
            t.EscribirLinea("  │", Paleta.Tenue);
        }

        void Opcion(int n, string texto, string nota, Color? color = null)
        {
            t.EscribirLinea(
                new Tramo("  │ ", Paleta.Tenue),
                new Tramo($"{n,3}  ", color ?? Paleta.Cian, true),
                new Tramo(texto.PadRight(40), color ?? Paleta.Texto, true),
                new Tramo(nota, Paleta.Tenue));
        }

        void Linea(string texto, Color color) => t.EscribirLinea(new Tramo("  │ ", Paleta.Tenue), new Tramo("     " + texto, color));

        void Cierre()
        {
            t.EscribirLinea("  │", Paleta.Tenue);
            t.EscribirLinea("  └" + new string('─', 60), Paleta.Tenue);
            t.EscribirLinea();
        }

        void Prompt(string lugar)
        {
            t.Escribir(new Tramo("  w3", Paleta.Texto, true), new Tramo(" " + lugar + "(", Paleta.Tenue),
                new Tramo(DateTime.Now.ToString("HH:mm"), Paleta.Violeta), new Tramo(") ", Paleta.Tenue),
                new Tramo("> ", Paleta.Rojo, true));
        }

        void Titulo(string texto)
        {
            t.EscribirLinea();
            t.EscribirLinea(new Tramo("  ━━━ ", Paleta.Magenta), new Tramo(texto, Paleta.Magenta, true),
                new Tramo(" " + new string('━', Math.Max(4, 54 - texto.Length)), Paleta.Magenta));
        }

        void Info(string texto) => t.EscribirLinea(new Tramo("  [*] ", Paleta.Azul, true), new Tramo(texto, Paleta.Texto));
        void Ok(string texto) => t.EscribirLinea(new Tramo("  [+] ", Paleta.Verde, true), new Tramo(texto, Paleta.Verde, true));
        void Aviso(string texto) => t.EscribirLinea(new Tramo("  [!] ", Paleta.Amarillo, true), new Tramo(texto, Paleta.Amarillo));
        void Error(string texto) => t.EscribirLinea(new Tramo("  [-] ", Paleta.Rojo, true), new Tramo(texto, Paleta.Rojo, true));

        async Task Pausa(string texto = "ENTER para volver al menú")
        {
            t.EscribirLinea();
            t.Escribir("  " + texto + " ", Paleta.Tenue);
            await t.LeerLinea(Paleta.Texto);
        }
    }
}
