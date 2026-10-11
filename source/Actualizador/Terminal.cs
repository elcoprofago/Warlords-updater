using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Actualizador
{
    /// <summary>Un tramo de texto de un solo color.</summary>
    sealed class Tramo
    {
        public string Texto;
        public Color Color;
        public bool Negrita;
        public Color? Fondo;

        public Tramo(string texto, Color color, bool negrita = false, Color? fondo = null)
        {
            Texto = texto ?? "";
            Color = color;
            Negrita = negrita;
            Fondo = fondo;
        }
    }

    sealed class Linea
    {
        public readonly List<Tramo> Tramos = new List<Tramo>();
        public int Largo => Tramos.Sum(t => t.Texto.Length);
    }

    /// <summary>
    /// Pantalla con aspecto de consola: cada tramo de texto con su propio color (no toda la consola de un color,
    /// como el "color 0A" de cmd), letra monoespaciada, y una sola linea de entrada con cursor al final.
    /// Las lineas largas se cortan al ancho de la ventana. La rueda del raton y RePag/AvPag recorren lo anterior.
    /// </summary>
    sealed class Terminal : Control
    {
        const int MaxLineas = 3000;
        const int Margen = 12;

        readonly List<Linea> lineas = new List<Linea> { new Linea() };
        readonly Font letra, letraNegrita;
        readonly Timer parpadeo = new Timer { Interval = 530 };
        float anchoCelda;
        int altoCelda;
        int desplazamiento;          // filas subidas desde el final (0 = pegado abajo)
        bool cursorVisible = true;

        // entrada en curso
        Tramo tramoEntrada;
        TaskCompletionSource<string> esperaEntrada;
        readonly Queue<string> entradaGuionada;

        public Terminal(Font letra, Font letraNegrita, IEnumerable<string> entradaGuionada = null)
        {
            this.letra = letra;
            this.letraNegrita = letraNegrita;
            this.entradaGuionada = new Queue<string>(entradaGuionada ?? Enumerable.Empty<string>());
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint |
                     ControlStyles.ResizeRedraw | ControlStyles.Selectable, true);
            BackColor = Paleta.Fondo;
            Cursor = Cursors.IBeam;
            using (var g = CreateGraphics())
            {
                var s = TextRenderer.MeasureText(g, new string('M', 40), letra, Size.Empty, Flags);
                anchoCelda = s.Width / 40f;
                altoCelda = s.Height;
            }
            parpadeo.Tick += (s, e) => { cursorVisible = !cursorVisible; if (tramoEntrada != null) Invalidate(); };
            parpadeo.Start();
        }

        const TextFormatFlags Flags = TextFormatFlags.NoPadding | TextFormatFlags.NoPrefix | TextFormatFlags.SingleLine |
                                      TextFormatFlags.NoClipping | TextFormatFlags.PreserveGraphicsClipping;

        public Size TamanoPara(int columnas, int filas) =>
            new Size((int)Math.Ceiling(anchoCelda * columnas) + 2 * Margen, altoCelda * filas + 2 * Margen);

        int Columnas => Math.Max(20, (int)((ClientSize.Width - 2 * Margen) / anchoCelda));
        int FilasVisibles => Math.Max(1, (ClientSize.Height - 2 * Margen) / altoCelda);

        /// <summary>Todo el texto escrito hasta ahora (para la transcripcion de las pruebas).</summary>
        public string Texto => historial + string.Join(Environment.NewLine, lineas.Select(l => string.Concat(l.Tramos.Select(t => t.Texto))));
        readonly StringBuilder historial = new StringBuilder();

        // ------------------------------------------------------------------ escribir

        public void Escribir(string texto, Color color, bool negrita = false)
        {
            var partes = (texto ?? "").Replace("\r", "").Split('\n');
            for (int i = 0; i < partes.Length; i++)
            {
                if (i > 0) NuevaLinea();
                if (partes[i].Length > 0) lineas[lineas.Count - 1].Tramos.Add(new Tramo(partes[i], color, negrita));
            }
            Cambio();
        }

        public void Escribir(params Tramo[] tramos)
        {
            foreach (var t in tramos) lineas[lineas.Count - 1].Tramos.Add(t);
            Cambio();
        }

        public void EscribirLinea(string texto, Color color, bool negrita = false)
        {
            Escribir(texto, color, negrita);
            NuevaLinea();
            Cambio();
        }

        public void EscribirLinea(params Tramo[] tramos)
        {
            Escribir(tramos);
            NuevaLinea();
            Cambio();
        }

        public void EscribirLinea() { NuevaLinea(); Cambio(); }

        /// <summary>Abre una linea que despues se reescribe en el lugar (barras de progreso, spinner).</summary>
        public Linea LineaViva()
        {
            var l = lineas[lineas.Count - 1];
            if (l.Tramos.Count > 0) { NuevaLinea(); l = lineas[lineas.Count - 1]; }
            NuevaLinea();
            Cambio();
            return l;
        }

        public void Reescribir(Linea linea, params Tramo[] tramos)
        {
            linea.Tramos.Clear();
            linea.Tramos.AddRange(tramos);
            Cambio();
        }

        public void Limpiar()
        {
            historial.AppendLine(string.Join(Environment.NewLine, lineas.Select(l => string.Concat(l.Tramos.Select(t => t.Texto)))));
            historial.AppendLine("=================================================== (pantalla limpiada)");
            lineas.Clear();
            lineas.Add(new Linea());
            desplazamiento = 0;
            Cambio();
        }

        void NuevaLinea()
        {
            lineas.Add(new Linea());
            if (lineas.Count > MaxLineas) lineas.RemoveRange(0, lineas.Count - MaxLineas);
        }

        void Cambio()
        {
            desplazamiento = 0;
            Invalidate();
        }

        // ------------------------------------------------------------------ leer

        /// <summary>Espera una linea del teclado (ENTER). El texto tipeado queda en pantalla con el color dado.</summary>
        public Task<string> LeerLinea(Color color)
        {
            tramoEntrada = new Tramo("", color, true);
            lineas[lineas.Count - 1].Tramos.Add(tramoEntrada);
            esperaEntrada = new TaskCompletionSource<string>();
            var tarea = esperaEntrada.Task;
            Cambio();
            EsperandoEntrada?.Invoke(this, EventArgs.Empty);
            if (entradaGuionada.Count > 0)
            {
                var guion = entradaGuionada.Dequeue();
                BeginInvoke(new Action(() => { tramoEntrada.Texto = guion; Confirmar(); }));
            }
            else if (Guionado)
            {
                // las pruebas se quedaron sin respuestas: se cierra en vez de esperar para siempre
                BeginInvoke(new Action(() => FindForm()?.Close()));
            }
            return tarea;
        }

        /// <summary>Corre con respuestas fijas (pruebas): sin respuestas pendientes, cierra la ventana.</summary>
        public bool Guionado { get; set; }

        public event EventHandler EsperandoEntrada;

        void Confirmar()
        {
            var t = esperaEntrada;
            var texto = tramoEntrada.Texto;
            tramoEntrada = null;
            esperaEntrada = null;
            NuevaLinea();
            Cambio();
            t?.SetResult(texto);
        }

        protected override bool IsInputKey(Keys keyData) => true;

        protected override void OnKeyPress(KeyPressEventArgs e)
        {
            if (tramoEntrada == null) return;
            if (e.KeyChar == '\r') Confirmar();
            else if (e.KeyChar == '\b') { if (tramoEntrada.Texto.Length > 0) tramoEntrada.Texto = tramoEntrada.Texto.Substring(0, tramoEntrada.Texto.Length - 1); }
            else if (e.KeyChar == 27) tramoEntrada.Texto = "";
            else if (e.KeyChar >= ' ' && tramoEntrada.Texto.Length < 200) tramoEntrada.Texto += e.KeyChar;
            else return;
            cursorVisible = true;
            Cambio();
            e.Handled = true;
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            if (e.KeyCode == Keys.PageUp) Desplazar(FilasVisibles - 1);
            else if (e.KeyCode == Keys.PageDown) Desplazar(-(FilasVisibles - 1));
            else if (e.Control && e.KeyCode == Keys.V && tramoEntrada != null)
            {
                var pegado = Clipboard.ContainsText() ? Clipboard.GetText() : "";
                pegado = pegado.Replace("\r", " ").Replace("\n", " ");
                tramoEntrada.Texto = (tramoEntrada.Texto + pegado);
                if (tramoEntrada.Texto.Length > 200) tramoEntrada.Texto = tramoEntrada.Texto.Substring(0, 200);
                Cambio();
            }
            else { base.OnKeyDown(e); return; }
            e.Handled = true;
        }

        protected override void OnMouseWheel(MouseEventArgs e) => Desplazar(e.Delta / 40);

        protected override void OnMouseDown(MouseEventArgs e) { Focus(); base.OnMouseDown(e); }

        void Desplazar(int filas)
        {
            int total = Filas().Count;
            desplazamiento = Math.Max(0, Math.Min(Math.Max(0, total - FilasVisibles), desplazamiento + filas));
            Invalidate();
        }

        // ------------------------------------------------------------------ dibujar

        /// <summary>Las filas de pantalla: cada linea cortada al ancho (linea, primer caracter).</summary>
        List<KeyValuePair<Linea, int>> Filas()
        {
            int cols = Columnas;
            var filas = new List<KeyValuePair<Linea, int>>(lineas.Count + 8);
            foreach (var l in lineas)
            {
                int largo = l.Largo;
                if (l == lineas[lineas.Count - 1] && tramoEntrada != null) largo++;   // lugar del cursor
                int n = Math.Max(1, (largo + cols - 1) / cols);
                for (int i = 0; i < n; i++) filas.Add(new KeyValuePair<Linea, int>(l, i * cols));
            }
            // la ultima linea vacia (donde sigue la escritura) no ocupa lugar si no hay entrada
            if (tramoEntrada == null && filas.Count > 1 && lineas[lineas.Count - 1].Tramos.Count == 0) filas.RemoveAt(filas.Count - 1);
            return filas;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.Clear(BackColor);
            int cols = Columnas;
            var filas = Filas();
            int visibles = FilasVisibles;
            int primera = Math.Max(0, filas.Count - visibles - desplazamiento);
            int y = Margen;
            for (int f = primera; f < filas.Count && f < primera + visibles; f++, y += altoCelda)
            {
                var linea = filas[f].Key;
                int desde = filas[f].Value, hasta = desde + cols, pos = 0;
                foreach (var t in linea.Tramos)
                {
                    int ini = Math.Max(desde, pos), fin = Math.Min(hasta, pos + t.Texto.Length);
                    if (fin > ini)
                    {
                        int x = Margen + (int)Math.Round((ini - desde) * anchoCelda);
                        var texto = t.Texto.Substring(ini - pos, fin - ini);
                        if (t.Fondo.HasValue)
                            using (var b = new SolidBrush(t.Fondo.Value))
                                g.FillRectangle(b, x, y - 1, (int)Math.Round(texto.Length * anchoCelda), altoCelda);
                        DibujarTexto(g, texto, t, x, y);
                    }
                    pos += t.Texto.Length;
                }
                // cursor de bloque al final de la entrada
                if (tramoEntrada != null && linea == lineas[lineas.Count - 1] && cursorVisible && Focused)
                {
                    int c = linea.Largo;
                    if (c >= desde && c < hasta)
                        using (var b = new SolidBrush(Paleta.Cursor))
                            g.FillRectangle(b, Margen + (int)Math.Round((c - desde) * anchoCelda), y, (int)Math.Ceiling(anchoCelda), altoCelda - 2);
                }
            }
            // indicador de que hay texto mas abajo
            if (desplazamiento > 0)
                TextRenderer.DrawText(g, "▼ más abajo (AvPág)", letra, new Point(ClientSize.Width - Margen - (int)(19 * anchoCelda), ClientSize.Height - altoCelda - 4), Paleta.Tenue, Flags);
        }

        /// <summary>
        /// Los bloques llenos (█) y sombreados (░) se pintan como celdas enteras: asi se tocan entre filas y
        /// columnas (el titulo y las barras quedan macizos); el resto del texto, con la fuente.
        /// </summary>
        void DibujarTexto(Graphics g, string texto, Tramo t, int x0, int y)
        {
            var fuente = t.Negrita ? letraNegrita : letra;
            int i = 0;
            while (i < texto.Length)
            {
                bool bloque = texto[i] == '█' || texto[i] == '░';
                int j = i;
                while (j < texto.Length && (texto[j] == '█' || texto[j] == '░') == bloque) j++;
                int x = x0 + (int)Math.Round(i * anchoCelda);
                if (bloque)
                {
                    for (int k = i; k < j; k++)
                    {
                        int xa = x0 + (int)Math.Round(k * anchoCelda), xb = x0 + (int)Math.Round((k + 1) * anchoCelda);
                        using (var b = new SolidBrush(texto[k] == '█' ? t.Color : Color.FromArgb(150, t.Color)))
                            if (texto[k] == '█') g.FillRectangle(b, xa, y - 1, xb - xa, altoCelda);
                            else g.FillRectangle(b, xa, y + altoCelda / 4, xb - xa - 1, altoCelda / 2);
                    }
                }
                else TextRenderer.DrawText(g, texto.Substring(i, j - i), fuente, new Point(x, y), t.Color, Flags);
                i = j;
            }
        }

        protected override void OnGotFocus(EventArgs e) { base.OnGotFocus(e); Invalidate(); }
        protected override void OnLostFocus(EventArgs e) { base.OnLostFocus(e); Invalidate(); }

        protected override void Dispose(bool disposing)
        {
            if (disposing) parpadeo.Dispose();
            base.Dispose(disposing);
        }
    }

    /// <summary>Colores de la pantalla (oscura, al estilo de las terminales de Linux).</summary>
    static class Paleta
    {
        public static readonly Color Fondo = Color.FromArgb(0x0E, 0x10, 0x16);
        public static readonly Color Texto = Color.FromArgb(0xD8, 0xDE, 0xE9);
        public static readonly Color Tenue = Color.FromArgb(0x6B, 0x72, 0x89);
        public static readonly Color Rojo = Color.FromArgb(0xFF, 0x55, 0x55);
        public static readonly Color Verde = Color.FromArgb(0x50, 0xFA, 0x7B);
        public static readonly Color Amarillo = Color.FromArgb(0xF1, 0xFA, 0x8C);
        public static readonly Color Naranja = Color.FromArgb(0xFF, 0xB8, 0x6C);
        public static readonly Color Azul = Color.FromArgb(0x6C, 0xB6, 0xFF);
        public static readonly Color Cian = Color.FromArgb(0x8B, 0xE9, 0xFD);
        public static readonly Color Magenta = Color.FromArgb(0xFF, 0x79, 0xC6);
        public static readonly Color Violeta = Color.FromArgb(0xBD, 0x93, 0xF9);
        public static readonly Color BarraVacia = Color.FromArgb(0x3A, 0x3F, 0x50);
        public static readonly Color Cursor = Color.FromArgb(0xC0, 0x50, 0xFA, 0x7B);
        public static readonly Color FondoAviso = Color.FromArgb(0x4A, 0x14, 0x1A);
    }
}
