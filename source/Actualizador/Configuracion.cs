using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Actualizador
{
    /// <summary>
    /// Boton de configuracion (engranaje, picts\cfg.ico) y actualizacion del propio Actualizador desde la release
    /// "Ejecutable" de GitHub, donde tools\compilar-actualizador.ps1 -Publicar sube Actualizador-v.X.exe.
    /// La version nueva se baja junto a la actual, se verifica que diga la version esperada, se abre con
    /// --reemplaza "&lt;exe viejo&gt;" y la nueva borra el exe viejo apenas este se cierra (regla 12: no es un
    /// respaldo; volver atras es bajar otra version de la release).
    /// Pruebas:
    ///   W3_VERSION_FINGIDA   la version propia que se compara (para forzar "hay version nueva")
    ///   W3_PRUEBA_ACTUALIZAR 1: al abrir, busca e instala sin preguntar (sin ventanas)
    /// </summary>
    static class Configuracion
    {
        public const string Creditos = "RA Sistemas & Claude © 2026 || elcoprofago@gmail.com";
        const string ApiRelease = "https://api.github.com/repos/elcoprofago/Warlords-updater/releases/tags/Ejecutable";
        const string Descarga = "https://github.com/elcoprofago/Warlords-updater/releases/download/Ejecutable/";

        static readonly HttpClient http = CrearHttp();

        static HttpClient CrearHttp()
        {
            var h = new HttpClient { Timeout = TimeSpan.FromMinutes(5) };
            h.DefaultRequestHeaders.UserAgent.ParseAdd("Warlords3-Actualizador/" + Actualizador.Version);
            return h;
        }

        public static Version Propia =>
            Version.TryParse(Environment.GetEnvironmentVariable("W3_VERSION_FINGIDA") ?? "", out var v)
                ? v : new Version(Actualizador.Version);

        /// <summary>La version mas alta publicada, o null si no se pudo consultar.</summary>
        public static async Task<Version> Publicada()
        {
            var json = await http.GetStringAsync(ApiRelease);
            return Regex.Matches(json, @"""name""\s*:\s*""Actualizador-v\.(\d+\.\d+\.\d+\.\d+)\.exe""")
                        .Cast<Match>().Select(m => new Version(m.Groups[1].Value)).DefaultIfEmpty(null).Max();
        }

        /// <summary>Baja la version, la verifica y la abre reemplazando a esta. Devuelve el error o null.</summary>
        public static async Task<string> Instalar(Version v, IProgress<string> progreso)
        {
            var actual = Application.ExecutablePath;
            var nombre = $"Actualizador-v.{v}.exe";
            var destino = Path.Combine(Path.GetDirectoryName(actual), nombre);
            if (string.Equals(destino, actual, StringComparison.OrdinalIgnoreCase)) return "ya estás usando " + nombre;
            var parcial = destino + ".descarga";
            try
            {
                progreso?.Report("Bajando " + nombre + "...");
                using (var r = await http.GetAsync(Descarga + nombre, HttpCompletionOption.ResponseHeadersRead))
                {
                    if (!r.IsSuccessStatusCode) return $"la descarga devolvió {(int)r.StatusCode}";
                    using (var s = await r.Content.ReadAsStreamAsync())
                    using (var f = File.Create(parcial))
                        await s.CopyToAsync(f);
                }
                var dice = FileVersionInfo.GetVersionInfo(parcial).FileVersion;
                if (dice != v.ToString())
                {
                    File.Delete(parcial);
                    return $"el archivo bajado dice versión {dice ?? "(ninguna)"}, no {v}";
                }
                if (File.Exists(destino)) File.Delete(destino);
                File.Move(parcial, destino);
            }
            catch (Exception ex)
            {
                try { if (File.Exists(parcial)) File.Delete(parcial); } catch { }
                return ex.Message;
            }
            progreso?.Report("Abriendo la versión " + v + "...");
            var psi = new ProcessStartInfo(destino, "--reemplaza \"" + actual + "\"")
                      { UseShellExecute = false, WorkingDirectory = Path.GetDirectoryName(destino) };
            foreach (var prueba in new[] { "W3_PRUEBA_ACTUALIZAR", "W3_VERSION_FINGIDA", "W3_TRANSCRIPCION", "W3_ENTRADA" })
                psi.EnvironmentVariables.Remove(prueba);
            Process.Start(psi);
            return null;
        }

        static Task borrado = Task.CompletedTask;

        /// <summary>Al cerrar: si el borrado del exe viejo sigue en curso, lo espera (hasta 30 s).</summary>
        public static void EsperarBorrado() => borrado.Wait(30000);

        /// <summary>Al arrancar con --reemplaza: borra el exe viejo cuando su proceso termina.</summary>
        public static void BorrarViejo(string[] args)
        {
            int i = Array.IndexOf(args, "--reemplaza");
            if (i < 0 || i + 1 >= args.Length) return;
            var viejo = args[i + 1];
            if (string.Equals(Path.GetFullPath(viejo), Application.ExecutablePath, StringComparison.OrdinalIgnoreCase)) return;
            if (!Path.GetFileName(viejo).StartsWith("Actualizador", StringComparison.OrdinalIgnoreCase)) return;
            borrado = Task.Run(() =>
            {
                for (int n = 0; n < 60 && File.Exists(viejo); n++)
                {
                    try { File.Delete(viejo); } catch { Thread.Sleep(500); }
                }
            });
        }
    }

    /// <summary>La ventanita que abre el engranaje.</summary>
    sealed class VentanaConfiguracion : Form
    {
        readonly Label estado;
        readonly Button buscar;
        Version nueva;

        public VentanaConfiguracion(Icon icono)
        {
            Text = "CONFIGURACIÓN · VERSIÓN " + Actualizador.Version;
            Icon = icono;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = MinimizeBox = false;
            StartPosition = FormStartPosition.CenterParent;
            ClientSize = new Size(440, 190);
            BackColor = Color.FromArgb(0x26, 0x22, 0x3A);   // violeta oscuro: se distingue del fondo de la terminal
            ForeColor = Paleta.Texto;
            Font = new Font("Segoe UI", 10f);

            Controls.Add(new Label
            {
                Text = "Actualizador de Warlords III\nVERSIÓN " + Actualizador.Version,
                Location = new Point(16, 14), Size = new Size(408, 44), ForeColor = Paleta.Cian,
            });
            buscar = new Button
            {
                Text = "Buscar actualización", Location = new Point(16, 66), Size = new Size(200, 32),
                FlatStyle = FlatStyle.Flat, BackColor = Color.FromArgb(0x3A, 0x33, 0x58), ForeColor = Paleta.Texto,
            };
            buscar.FlatAppearance.BorderColor = Paleta.Violeta;
            buscar.FlatAppearance.MouseOverBackColor = Color.FromArgb(0x4A, 0x41, 0x70);
            buscar.Click += async (s, e) => await Pulsar();
            Controls.Add(buscar);
            estado = new Label { Location = new Point(16, 106), Size = new Size(408, 44), ForeColor = Paleta.Tenue };
            Controls.Add(estado);
            Controls.Add(new Label
            {
                Text = Configuracion.Creditos, UseMnemonic = false, Location = new Point(16, 160), Size = new Size(408, 20),
                ForeColor = Paleta.Tenue, Font = new Font("Segoe UI", 8.5f),
            });
        }

        async Task Pulsar()
        {
            buscar.Enabled = false;
            try
            {
                if (nueva == null)
                {
                    estado.ForeColor = Paleta.Tenue;
                    estado.Text = "Consultando GitHub...";
                    Version v;
                    try { v = await Configuracion.Publicada(); }
                    catch (Exception ex) { Mostrar("No se pudo consultar: " + ex.Message, Paleta.Rojo); return; }
                    if (v == null) { Mostrar("No se encontró ninguna versión publicada.", Paleta.Rojo); return; }
                    if (v <= Configuracion.Propia) { Mostrar("Tienes la última versión (v" + Actualizador.Version + ").", Paleta.Verde); return; }
                    nueva = v;
                    Mostrar("Hay una versión nueva: v" + v + ".", Paleta.Amarillo);
                    buscar.Text = "Descargar e instalar";
                    return;
                }
                var error = await Configuracion.Instalar(nueva, new Progress<string>(m => Mostrar(m, Paleta.Tenue)));
                if (error != null) { Mostrar("No se pudo actualizar: " + error, Paleta.Rojo); return; }
                Application.Exit();
                Environment.Exit(0);
            }
            finally { buscar.Enabled = true; }
        }

        void Mostrar(string texto, Color color)
        {
            estado.Text = texto;
            estado.ForeColor = color;
        }
    }
}
