using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Drawing.Text;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace Actualizador
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            try { ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12 | (SecurityProtocolType)12288; }
            catch (NotSupportedException) { ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12; }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new Ventana());
        }
    }

    /// <summary>
    /// La ventana: solo la terminal. Variables de entorno para las pruebas (como W3_JUEGO del .bat viejo):
    ///   W3_ENTRADA       respuestas separadas por "|" en lugar del teclado; al acabarse, cierra
    ///   W3_TRANSCRIPCION archivo donde queda todo el texto de la pantalla al cerrar
    ///   W3_CAPTURA       prefijo de PNG: una captura de la ventana cada vez que espera una respuesta
    /// </summary>
    sealed class Ventana : Form
    {
        readonly Terminal term;
        int capturas;

        public Ventana()
        {
            var (normal, negrita) = Fuentes.Cargar(11f);
            var guion = Environment.GetEnvironmentVariable("W3_ENTRADA");
            term = new Terminal(normal, negrita, guion?.Split('|')) { Dock = DockStyle.Fill, Guionado = guion != null };
            Controls.Add(term);
            Text = "Actualizador de Warlords III · v" + Actualizador.Version;
            BackColor = Paleta.Fondo;
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = term.TamanoPara(100, 38);
            var area = Screen.FromPoint(Cursor.Position).WorkingArea;
            if (Height > area.Height) Height = area.Height;
            if (Width > area.Width) Width = area.Width;
            MinimumSize = new Size(480, 320);

            var captura = Environment.GetEnvironmentVariable("W3_CAPTURA");
            if (captura != null)
                term.EsperandoEntrada += (s, e) =>
                {
                    try
                    {
                        term.Refresh();
                        using (var bmp = new Bitmap(term.Width, term.Height))
                        {
                            term.DrawToBitmap(bmp, new Rectangle(Point.Empty, term.Size));
                            bmp.Save($"{captura}_{++capturas:00}.png", ImageFormat.Png);
                        }
                    }
                    catch (Exception ex) { File.AppendAllText(captura + "_error.txt", ex + Environment.NewLine); }
                };
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            // barra de titulo oscura (Windows 10 2004+ y 11; en los demas no hace nada)
            int si = 1;
            try { DwmSetWindowAttribute(Handle, 20, ref si, 4); } catch { }
        }

        protected override async void OnShown(EventArgs e)
        {
            base.OnShown(e);
            term.Focus();
            try
            {
                await new Actualizador(term).Correr();
            }
            catch (Exception ex)
            {
                term.EscribirLinea("[-] Error inesperado: " + ex.Message, Paleta.Rojo, true);
                term.Escribir("    ENTER para cerrar ", Paleta.Tenue);
                await term.LeerLinea(Paleta.Texto);
            }
            Close();
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            var transcripcion = Environment.GetEnvironmentVariable("W3_TRANSCRIPCION");
            if (transcripcion != null) File.WriteAllText(transcripcion, term.Texto);
            base.OnFormClosed(e);
            Environment.Exit(0);   // corta descargas en curso
        }

        [DllImport("dwmapi.dll")]
        static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int value, int size);
    }

    /// <summary>JetBrains Mono, embebida en el exe (licencia OFL, fuentes\OFL-JetBrainsMono.txt).</summary>
    static class Fuentes
    {
        static readonly PrivateFontCollection coleccion = new PrivateFontCollection();

        public static (Font normal, Font negrita) Cargar(float puntos)
        {
            try
            {
                Agregar("JetBrainsMono-Regular.ttf");
                Agregar("JetBrainsMono-Bold.ttf");
                var familia = coleccion.Families[0];
                return (new Font(familia, puntos, FontStyle.Regular), new Font(familia, puntos, FontStyle.Bold));
            }
            catch
            {
                return (new Font("Consolas", puntos), new Font("Consolas", puntos, FontStyle.Bold));
            }
        }

        static void Agregar(string recurso)
        {
            byte[] datos;
            using (var s = typeof(Fuentes).Assembly.GetManifestResourceStream(recurso))
            using (var m = new MemoryStream())
            {
                s.CopyTo(m);
                datos = m.ToArray();
            }
            // la memoria queda reservada mientras viva el programa: GDI+ y GDI la siguen leyendo
            IntPtr p = Marshal.AllocCoTaskMem(datos.Length);
            Marshal.Copy(datos, 0, p, datos.Length);
            coleccion.AddMemoryFont(p, datos.Length);
            // GDI (TextRenderer) solo ve la fuente si tambien se registra asi, privada para este proceso
            uint n = 0;
            AddFontMemResourceEx(p, (uint)datos.Length, IntPtr.Zero, ref n);
        }

        [DllImport("gdi32.dll")]
        static extern IntPtr AddFontMemResourceEx(IntPtr pbFont, uint cbFont, IntPtr pdv, [In] ref uint pcFonts);
    }
}
