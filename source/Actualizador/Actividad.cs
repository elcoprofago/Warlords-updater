using System;
using System.Diagnostics;
using System.Windows.Forms;

namespace Actualizador
{
    /// <summary>
    /// Una linea viva que se reescribe sola: spinner "/ - \ |" cada 120 ms mientras un proceso espera
    /// (conectar, verificar), y barra de bloques [████░░░░] 50 % cuando se sabe cuanto falta (bajar, descomprimir).
    /// Mismo estilo que las barras de PostOCRNormalizer.
    /// </summary>
    sealed class Actividad : IDisposable
    {
        static readonly string[] Giro = { "/", "-", "\\", "|" };
        const int AnchoBarra = 32;

        readonly Terminal term;
        readonly Linea linea;
        readonly Timer reloj = new Timer { Interval = 120 };
        readonly Stopwatch cronometro = Stopwatch.StartNew();
        int giro;
        string texto;
        long hecho, total = -1;
        bool enBytes;
        string detalle;
        bool terminada;

        public Actividad(Terminal term, string textoEspera)
        {
            this.term = term;
            texto = textoEspera;
            linea = term.LineaViva();
            reloj.Tick += (s, e) => { giro = (giro + 1) % Giro.Length; Dibujar(); };
            reloj.Start();
            Dibujar();
        }

        /// <summary>Sin barra: solo el texto y el spinner.</summary>
        public void Esperar(string textoEspera)
        {
            texto = textoEspera;
            total = -1;
            Dibujar();
        }

        /// <summary>Bytes bajados de un total (total &lt;= 0: desconocido, se muestra solo lo bajado).</summary>
        public void Bytes(long bajados, long totalBytes)
        {
            if (hecho == 0 && bajados > 0) cronometro.Restart();
            hecho = bajados;
            total = totalBytes > 0 ? totalBytes : 0;
            enBytes = true;
        }

        /// <summary>Avance generico (por ejemplo archivos descomprimidos).</summary>
        public void Avance(long actual, long de, string detalleAvance)
        {
            hecho = actual;
            total = Math.Max(1, de);
            enBytes = false;
            detalle = detalleAvance;
        }

        void Dibujar()
        {
            if (terminada) return;
            string spin = Giro[giro];
            if (total < 0)
            {
                term.Reescribir(linea,
                    new Tramo("    " + texto + " ", Paleta.Texto),
                    new Tramo(spin, Paleta.Cian, true));
                return;
            }
            if (total == 0)
            {
                term.Reescribir(linea,
                    new Tramo("    " + Mb(hecho) + " MB", Paleta.Texto),
                    new Tramo("   " + Velocidad(), Paleta.Tenue),
                    new Tramo("  " + spin, Paleta.Cian, true));
                return;
            }
            term.Reescribir(linea, Barra(spin));
        }

        Tramo[] Barra(string spin)
        {
            double frac = Math.Min(1.0, (double)hecho / total);
            int lleno = Math.Min(AnchoBarra, (int)Math.Round(frac * AnchoBarra));
            int pct = (int)Math.Round(frac * 100);
            string cifras = enBytes ? $"{Mb(hecho),7} / {Mb(total)} MB" : detalle ?? $"({hecho}/{total})";
            var color = pct >= 100 ? Paleta.Verde : Paleta.Cian;
            return new[]
            {
                new Tramo("    [", Paleta.Tenue),
                new Tramo(new string('█', lleno), color),
                new Tramo(new string('░', AnchoBarra - lleno), Paleta.BarraVacia),
                new Tramo("] ", Paleta.Tenue),
                new Tramo($"{pct,3}%", Paleta.Amarillo, true),
                new Tramo("  " + cifras, Paleta.Texto),
                new Tramo(enBytes ? "  " + Velocidad() : "", Paleta.Tenue),
                new Tramo(spin == null ? "" : "  " + spin, Paleta.Cian, true),
            };
        }

        string Velocidad()
        {
            double s = cronometro.Elapsed.TotalSeconds;
            return s < 0.5 || hecho == 0 ? "" : $"{hecho / s / 1048576.0:0.0} MB/s";
        }

        public static string Mb(long bytes) => (bytes / 1048576.0).ToString("0.0");

        /// <summary>Deja la barra quieta (sin spinner) donde llego, o borra la linea si no hubo barra.</summary>
        public void Terminar()
        {
            if (terminada) return;
            reloj.Stop();
            if (total > 0) term.Reescribir(linea, Barra(null));
            else if (total == 0) term.Reescribir(linea, new Tramo("    " + Mb(hecho) + " MB", Paleta.Texto));
            else term.Reescribir(linea, new Tramo("    " + texto, Paleta.Tenue));
            terminada = true;
        }

        public void Dispose()
        {
            Terminar();
            reloj.Dispose();
        }
    }
}
