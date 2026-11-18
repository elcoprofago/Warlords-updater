using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Management;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Win32;

namespace Actualizador
{
    /// <summary>
    /// Opcion 16: diagnostico de video, hecho por el propio exe (antes era un .bat con PowerShell, que el antivirus
    /// bloqueaba). Solo lee: placa y driver, resolucion y escala, archivos de video del juego y sus .ini, modos de
    /// compatibilidad. El informe va al Escritorio y se manda por correo con FormSubmit (formsubmit.co), que reenvia
    /// a la direccion sin cuenta ni claves dentro del exe; la primera vez FormSubmit pide activarlo desde ese correo.
    /// Pruebas: W3_DIAG_DESTINO reemplaza el correo destino.
    /// </summary>
    static class Diagnostico
    {
        public const string Correo = "elcoprofago@gmail.com";

        public static string Informe(string juego)
        {
            var o = new StringBuilder();
            void L(string s = "") => o.AppendLine(s);

            L("DIAGNOSTICO DE VIDEO WARLORDS - ACTUALIZADOR VERSION " + Actualizador.Version);
            L("Fecha: " + DateTime.Now.ToString("yyyy-MM-dd HH:mm"));
            L("Equipo: " + Environment.MachineName);
            L();
            using (var cv = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion"))
                L("Windows: build " + cv?.GetValue("CurrentBuildNumber") + " (" + cv?.GetValue("DisplayVersion") + ")");
            Wmi("SELECT TotalPhysicalMemory FROM Win32_ComputerSystem",
                m => L($"RAM: {Convert.ToDouble(m["TotalPhysicalMemory"]) / (1L << 30):N1} GB"));
            L();
            L("== PLACAS DE VIDEO ==");
            Wmi("SELECT * FROM Win32_VideoController", g =>
            {
                L("- " + g["Name"]);
                L("  Driver: " + g["DriverVersion"] + "  fecha " + Fecha(g["DriverDate"] as string));
                L($"  Modo actual: {g["CurrentHorizontalResolution"]}x{g["CurrentVerticalResolution"]}, " +
                  $"{g["CurrentBitsPerPixel"]} bits, {g["CurrentRefreshRate"]} Hz");
            });
            L();
            L("== PANTALLAS Y ESCALA ==");
            foreach (var s in Screen.AllScreens)
                L($"- {s.DeviceName} {s.Bounds.Width}x{s.Bounds.Height}{(s.Primary ? " (principal)" : "")}");
            using (var k = Registry.CurrentUser.OpenSubKey(@"Control Panel\Desktop\WindowMetrics"))
            {
                var dpi = k?.GetValue("AppliedDPI");
                L(dpi is int d ? $"Escala de Windows: {Math.Round(d / 96.0 * 100)} %  (AppliedDPI {d})"
                               : "Escala de Windows: no se pudo leer");
            }
            L();
            L("== CARPETAS DEL JUEGO ==");
            var carpetas = new List<string>();
            if (File.Exists(Path.Combine(juego, "Darklord.exe"))) carpetas.Add(juego);
            foreach (var u in DriveInfo.GetDrives().Where(u => u.DriveType == DriveType.Fixed && u.IsReady))
                foreach (var n in new[] { "Warlords", "Warlords3", "Warlords 3" })
                {
                    var p = Path.Combine(u.RootDirectory.FullName, n);
                    if (File.Exists(Path.Combine(p, "Darklord.exe")) &&
                        !carpetas.Any(c => string.Equals(Path.GetFullPath(c), Path.GetFullPath(p), StringComparison.OrdinalIgnoreCase)))
                        carpetas.Add(p);
                }
            if (carpetas.Count == 0) L("No se encontro Darklord.exe en X:\\Warlords ni X:\\Warlords3");
            foreach (var p in carpetas)
            {
                L("--- " + p);
                foreach (var a in new[] { "Darklord.exe", "DarklordAV.exe", "ddraw.dll", "winmm.dll", "dxcfg.exe" })
                {
                    var r = Path.Combine(p, a);
                    if (!File.Exists(r)) { L("  " + a + "  NO ESTA"); continue; }
                    var i = new FileInfo(r);
                    L($"  {a}  {i.Length} bytes  {i.LastWriteTime:yyyy-MM-dd}  md5 {Md5(r)}  ver {FileVersionInfo.GetVersionInfo(r).FileVersion}");
                }
                foreach (var a in new[] { "SCREEN.INI", "VIDEO.INI", "dxcfg.ini", "ddraw.ini" })
                {
                    var r = Path.Combine(p, a);
                    if (!File.Exists(r)) continue;
                    L("  [" + a + "]");
                    foreach (var x in File.ReadAllLines(r)) L("    " + x);
                }
            }
            L();
            L("== MODOS DE COMPATIBILIDAD DEL JUEGO ==");
            bool hay = false;
            foreach (var raiz in new[] { Registry.CurrentUser, Registry.LocalMachine })
                using (var k = raiz.OpenSubKey(@"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"))
                    foreach (var n in k?.GetValueNames() ?? new string[0])
                        if (n.IndexOf("warlord", StringComparison.OrdinalIgnoreCase) >= 0 ||
                            n.IndexOf("darklord", StringComparison.OrdinalIgnoreCase) >= 0 ||
                            n.IndexOf("war3", StringComparison.OrdinalIgnoreCase) >= 0)
                        { L("- " + n + " = " + k.GetValue(n)); hay = true; }
            if (!hay) L("Ninguno");
            return o.ToString();

            void Wmi(string consulta, Action<ManagementBaseObject> cada)
            {
                try
                {
                    using (var b = new ManagementObjectSearcher(consulta))
                        foreach (var m in b.Get()) cada(m);
                }
                catch (Exception ex) { L("  (no se pudo consultar: " + ex.Message + ")"); }
            }
        }

        static string Fecha(string wmi) =>
            wmi != null && wmi.Length >= 8 ? $"{wmi.Substring(0, 4)}-{wmi.Substring(4, 2)}-{wmi.Substring(6, 2)}" : "?";

        static string Md5(string archivo)
        {
            using (var md5 = MD5.Create())
            using (var f = File.OpenRead(archivo))
                return BitConverter.ToString(md5.ComputeHash(f)).Replace("-", "").Substring(0, 12);
        }

        // cliente propio: FormSubmit solo acepta pedidos que parecen de un navegador
        static readonly HttpClient http = CrearHttp();

        static HttpClient CrearHttp()
        {
            var h = new HttpClient { Timeout = TimeSpan.FromSeconds(60) };
            h.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64)");
            return h;
        }

        /// <summary>Manda el informe por correo. Devuelve null si salio, o el motivo.</summary>
        public static async Task<string> Enviar(string informe)
        {
            var destino = Environment.GetEnvironmentVariable("W3_DIAG_DESTINO") ?? Correo;
            var datos = new FormUrlEncodedContent(new Dictionary<string, string>
            {
                ["_subject"] = "Diagnostico de video Warlords - " + Environment.MachineName,
                ["_template"] = "box",
                ["_captcha"] = "false",
                ["equipo"] = Environment.MachineName,
                ["informe"] = informe,
            });
            using (var pedido = new HttpRequestMessage(HttpMethod.Post, "https://formsubmit.co/ajax/" + destino) { Content = datos })
            {
                pedido.Headers.Accept.ParseAdd("application/json");
                // FormSubmit rechaza pedidos sin pagina de origen
                pedido.Headers.Referrer = new Uri("https://github.com/elcoprofago/Warlords-updater");
                pedido.Headers.TryAddWithoutValidation("Origin", "https://github.com");
                using (var r = await http.SendAsync(pedido))
                {
                    var cuerpo = await r.Content.ReadAsStringAsync();
                    if (r.IsSuccessStatusCode && cuerpo.Contains("\"success\":\"true\"")) return null;
                    if (cuerpo.Contains("Activation"))
                        return "el envío automático todavía no está activado (falta aceptar el correo de activación en " + destino + ")";
                    return $"el servicio de correo respondió {(int)r.StatusCode}: " +
                           (cuerpo.Length > 200 ? cuerpo.Substring(0, 200) : cuerpo);
                }
            }
        }
    }
}
