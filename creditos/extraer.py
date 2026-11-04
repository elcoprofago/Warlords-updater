r"""Extrae el listado de créditos de Warlords III: Darklords Rising.

Lee DATA\Credits.txt (créditos del juego) y eddata\Credits.txt (los del
editor, que difieren) de la instalación, y escribe creditos.json y LISTADO.md.

Uso:  python extraer.py [carpeta_del_juego]   (por defecto C:\Warlords3)
"""
import json, re, sys
from pathlib import Path

VERSION = "1.0.0.0"
AQUI = Path(__file__).resolve().parent

EMPRESAS = {
    "Strategic Studies Group": "Desarrolladora (copyright 1998, marca Warlords)",
    "Red Orb Entertainment": "Editora (división de Broderbund)",
    "Broderbund Software, Inc.": "Dueña de Red Orb; marcas Darklords Rising y Red Orb; QA",
    "Beta Breakers": "Testeo externo",
    "RAD Software": "Smacker (código de reproducción de video)",
    "Australian Film, Television and Radio School": "Lugar de filmación de los videos",
    "Society of Creative Anachronism": "Actores de los videos",
    "Costume Design Center": "Agradecimiento (vestuario)",
    "The Ancient and Medieval Martial Arts Society": "Agradecimiento",
    "Mpath Interactive (Mplayer)": "Juego en línea (README)",
    "Microsoft Corporation": "Marca Windows (aviso legal)",
}
# Textos que no son nombres de personas
NO_PERSONA = {"Broderbund Quality Assurance", "Beta Breakers", "also...",
              "and all the team from", "also", "Warlords III central!", "and"}
ALIAS_SECCION = "Testing & Thanks"
# Mismo crédito con otro nombre en el editor: se unifican bajo el primero
VARIANTES = {"Jonathan Dixon": "Jon Dixon", "Drew Garske": "Andrew Garske"}


def partir(texto):
    texto = texto.replace("&", ",").replace(" and ", ",")
    return [n.strip(" ,.") for n in texto.split(",") if n.strip(" ,.")]


def leer(archivo, fuente, personas, alias):
    seccion = None
    for linea in archivo.read_text(encoding="latin-1").splitlines():
        linea = linea.strip()
        if linea.startswith("#H:"):
            seccion = linea[3:].strip()
            continue
        if not linea.startswith(("#T:", "#S:")):
            continue
        t = re.sub(r"\s+", " ", linea[3:].strip())
        if linea.startswith("#S:"):
            m = re.match(r"Production Supervisor AFTRS (.+)", t)
            if m:
                anotar(personas, m.group(1), "Video: supervisor de producción (AFTRS)", fuente)
            m = re.match(r"The Ancient and Medieval Martial Arts Society, (.+)", t)
            if m:
                for n in partir(m.group(1)):
                    anotar(personas, n, "Video: agradecimiento", fuente)
            if t.startswith("Peter Radvan"):
                for n in partir(t):
                    anotar(personas, n, "Video: agradecimiento", fuente)
            continue
        if seccion == ALIAS_SECCION:
            for n in partir(t):
                if n not in NO_PERSONA:
                    alias.setdefault(n, set()).add(fuente)
            continue
        rol = seccion
        m = re.match(r"(?:Also )?Starring (.+) as (.+)", t) or re.match(r"(.+) as (.+)", t)
        if m and seccion == "Video Credits":
            anotar(personas, m.group(1), f"Actor en videos: {m.group(2)}", fuente)
            continue
        if t in ("Produced & Directed by", "Technical Director", "Digital Implementation",
                 "Lord Bane's Prosthetic Makeup"):
            leer.rol_pendiente = t
            continue
        m = re.match(r"(.+?)\s*(?::| - )\s*(.+)", t)
        if m:
            rol, t = f"{seccion}: {m.group(1).strip()}", m.group(2)
        elif getattr(leer, "rol_pendiente", None):
            rol = f"{seccion}: {leer.rol_pendiente}"
        if seccion == "Video Credits" and "Society of Creative" not in t:
            rol = "Actor en videos"
        if "Society of Creative" in t:
            continue
        for n in partir(t):
            if n not in NO_PERSONA:
                anotar(personas, n, rol, fuente)
    leer.rol_pendiente = None


def anotar(personas, nombre, rol, fuente):
    variante = nombre if nombre in VARIANTES else None
    nombre = VARIANTES.get(nombre, nombre)
    p = personas.setdefault(nombre, {"roles": [], "fuentes": []})
    if variante:
        p.setdefault("tambien_figura_como", [])
        if variante not in p["tambien_figura_como"]:
            p["tambien_figura_como"].append(variante)
    if rol not in p["roles"]:
        p["roles"].append(rol)
    if fuente not in p["fuentes"]:
        p["fuentes"].append(fuente)


def correos_en_metadatos(juego):
    patron = re.compile(rb"[A-Za-z0-9._%+-]{2,}@[A-Za-z0-9-]{2,}(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,6}")
    hallados = {}
    for f in juego.rglob("*"):
        if not f.is_file() or f.suffix.lower() in (".exe", ".dll") or f.stat().st_size > 5_000_000:
            continue
        if any(p.lower() in ("saves", "netsaves") for p in f.relative_to(juego).parts):
            continue
        for m in patron.finditer(f.read_bytes()):
            c = m.group().decode("ascii")
            if c.startswith("local-part@"):
                continue
            # descarta basura binaria: el dominio tiene que tener letras de verdad
            if not re.fullmatch(r"[a-z0-9.-]+\.(com|net|org|au|edu|gov)", c.split("@")[1]):
                continue
            hallados.setdefault(c, set()).add(str(f.relative_to(juego)))
    return hallados


def escribir_listado(d):
    L = [f"# Créditos de {d['juego']}", "",
         f"Generado por `extraer.py` {VERSION} desde `{d['origen']}` "
         "(`DATA/Credits.txt` = créditos del juego; `eddata/Credits.txt` = los del editor, que difieren un poco).", "",
         f"## Personas ({len(d['personas'])})", "", "| # | Nombre | Rol en el juego | Figura en |", "|---|---|---|---|"]
    for i, p in enumerate(d["personas"], 1):
        n = p["nombre"] + (f" (también «{', '.join(p['tambien_figura_como'])}»)" if p.get("tambien_figura_como") else "")
        L.append(f"| {i} | {n} | {'; '.join(p['roles'])} | {', '.join(p['fuentes'])} |")
    L += ["", f"## Alias de testers ({len(d['alias'])})", "",
          "Sección «Testing & Thanks», solo en los créditos del juego: apodos de jugadores del sitio *Warlords III Central*, sin nombre real.", "",
          ", ".join(a["alias"] for a in d["alias"]), "",
          f"## Empresas e instituciones ({len(d['empresas'])})", "", "| Nombre | Rol |", "|---|---|"]
    L += [f"| {e['nombre']} | {e['rol']} |" for e in d["empresas"]]
    L += ["", "## Correos electrónicos", "",
          "En los créditos no figura ningún correo. En los metadatos de los archivos del juego aparece uno solo:", "",
          "| Correo | Dónde | Qué es |", "|---|---|---|"]
    L += [f"| {c['correo']} | {', '.join(c['archivos'])} | Firma «Maz & Kilgore, 208 W. 30th #701, New York» en la etiqueta INFO del WAV: autores de sonidos del esquema «Utopia» de Windows 95 (©1995 Microsoft) reutilizados por el juego. No es nadie de los créditos. |" for c in d["correos"]]
    L += ["", "Otros datos de contacto (README.TXT, Ereg/EREG32.INI), todos de 1998: http://www.redorb.com, http://www.warlords3.com, http://www.mpath.com, "
          "Red Orb Technical Correspondence, P.O. Box 6125, Novato, CA 94948-6125; teléfonos (415) 382-4777 y (415) 382-4745 (Broderbund), 1-800-615-4286 (registro).", ""]
    (AQUI / "LISTADO.md").write_text("\n".join(L), encoding="utf-8")


def main():
    juego = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Warlords3")
    print(f"EXTRAER CREDITOS - VERSION {VERSION}")
    personas, alias = {}, {}
    leer(juego / "DATA" / "Credits.txt", "juego", personas, alias)
    leer(juego / "eddata" / "Credits.txt", "editor", personas, alias)
    correos = correos_en_metadatos(juego)
    datos = {
        "juego": "Warlords III: Darklords Rising (1998)",
        "origen": str(juego),
        "personas": [{"nombre": n, **d} for n, d in sorted(personas.items(), key=lambda x: x[0].split()[-1] + x[0])],
        "alias": [{"alias": a, "fuentes": sorted(f)} for a, f in alias.items()],
        "empresas": [{"nombre": n, "rol": r} for n, r in EMPRESAS.items()],
        "correos": [{"correo": c, "archivos": sorted(a)} for c, a in correos.items()],
    }
    (AQUI / "creditos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    escribir_listado(datos)
    print(f"{len(personas)} personas, {len(alias)} alias, {len(EMPRESAS)} empresas, {len(correos)} correos")


if __name__ == "__main__":
    main()
