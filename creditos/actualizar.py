r"""Actualiza por internet el estado de las personas y empresas de creditos.json.

Para cada nombre consulta fuentes públicas y abiertas:
  - Wikidata: si existe una ficha que coincida (persona del rubro juegos/arte/cine,
    o la empresa), si figura fallecida o disuelta, su sitio web oficial y, si la
    ficha lo publica, su correo oficial.
  - El sitio web oficial: si hoy responde.
  - Cada correo conocido: si su dominio sigue recibiendo correo (registros MX).

No busca ni deduce correos personales: solo informa los que la propia ficha
pública publica. Una persona sin ficha queda como «sin datos públicos», que no
quiere decir que no exista.

Uso:  python actualizar.py            (escribe estado.json y ESTADO.md)
"""
import json, re, subprocess, sys, time, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

VERSION = "1.0.0.0"
AQUI = Path(__file__).resolve().parent
UA = {"User-Agent": "creditos-warlords/" + VERSION + " (consulta de creditos)"}

# Descripción de la ficha que indica que es la persona del juego y no un homónimo
# Personas: cualquier ficha con el mismo nombre se lista, pero solo se da por
# CONFIRMADA si su descripción habla de videojuegos o la ficha está vinculada a
# Strategic Studies Group (Q615181) o Red Orb Entertainment (Q2642863).
RUBRO = re.compile(r".", re.I)
VIDEOJUEGO = re.compile(r"video ?game|game (designer|developer|programmer|producer|artist)|"
                        r"videojuego|computer game|wargame|software designer", re.I)
VINCULOS = {"Q615181", "Q2642863"}
# Nombre con que Wikidata registra cada empresa, cuando difiere del de los créditos
NOMBRE_WIKIDATA = {
    "Broderbund Software, Inc.": "Broderbund",
    "Microsoft Corporation": "Microsoft",
    "RAD Software": "RAD Game Tools",
    "Mpath Interactive (Mplayer)": "Mpath Interactive",
    "Society of Creative Anachronism": "Society for Creative Anachronism",
}
EMPRESA = re.compile(r"compan|publisher|developer|studio|school|society|organi|corporation|"
                     r"empresa|editora|desarrolladora|escuela|sociedad", re.I)


def pedir(url, intentos=6):
    for i in range(intentos):
        time.sleep(1.0)  # Wikidata limita a quien pide muy seguido (HTTP 429)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if i == intentos - 1 or e.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(int(e.headers.get("Retry-After") or 5 * (i + 1)) + 1)
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(5 * (i + 1))


def buscar_wikidata(nombre, filtro):
    q = urllib.parse.urlencode({"action": "wbsearchentities", "search": nombre, "language": "en",
                                "limit": 10, "format": "json"})
    res = pedir("https://www.wikidata.org/w/api.php?" + q)["search"]
    exactos = [r for r in res if r.get("label", "").lower() == nombre.lower()
               and filtro.search(r.get("description", ""))]
    return exactos


def ficha(qid):
    e = pedir(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json")["entities"][qid]
    c = e.get("claims", {})

    def valores(prop):
        out = []
        for s in c.get(prop, []):
            v = s.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(v, dict) and "time" in v:
                v = v["time"].lstrip("+")[:10]
            elif isinstance(v, dict) and "id" in v:
                v = v["id"]
            if v:
                out.append(v)
        return out

    return {
        "qid": qid,
        "url": f"https://www.wikidata.org/wiki/{qid}",
        "descripcion": e.get("descriptions", {}).get("en", {}).get("value", ""),
        "fallecimiento": valores("P570"),
        "disolucion": valores("P576"),
        "sitio_web": valores("P856"),
        "correo": [v.removeprefix("mailto:") for v in valores("P968")],
        "wikipedia": e.get("sitelinks", {}).get("enwiki", {}).get("title"),
        "vinculada_al_juego": bool(VINCULOS & set(json.dumps(c).split('"'))),
    }


def web_responde(url):
    try:
        req = urllib.request.Request(url, headers=UA, method="GET")
        with urllib.request.urlopen(req, timeout=20) as r:
            return f"responde ({r.status})"
    except urllib.error.HTTPError as e:
        return f"responde con error {e.code}"
    except Exception as e:
        return f"no responde ({type(e).__name__})"


def dominio_recibe_correo(correo):
    dominio = correo.split("@")[-1]
    try:
        r = subprocess.run(["nslookup", "-type=MX", dominio], capture_output=True, text=True,
                           timeout=30, errors="replace")
        mx = re.findall(r"mail exchanger = (\S+)", r.stdout)
        if not mx and r.returncode != 0 and "Non-existent" not in r.stdout + r.stderr                 and "No existe" not in r.stdout + r.stderr:
            return f"no se pudo consultar (nslookup salió con {r.returncode})"
        return f"el dominio recibe correo ({', '.join(mx)})" if mx else "el dominio NO tiene servidor de correo"
    except Exception as e:
        return f"no se pudo consultar ({type(e).__name__})"


def evaluar(nombre, filtro, es_empresa):
    try:
        cand = buscar_wikidata(nombre, filtro)
    except Exception as e:
        return {"estado": f"ERROR de consulta ({type(e).__name__}): no verificado"}
    if not cand:
        return {"estado": "sin datos públicos"}
    fichas = []
    for c in cand[:3]:
        try:
            f = ficha(c["id"])
        except Exception as e:
            f = {"qid": c["id"], "error": type(e).__name__}
        for w in f.get("sitio_web", [])[:1]:
            f["sitio_web_estado"] = web_responde(w)
        f["correo_estado"] = {m: dominio_recibe_correo(m) for m in f.get("correo", [])}
        fichas.append(f)
        time.sleep(0.5)
    if not es_empresa:
        for f in fichas:
            f["confirmada"] = bool(f.get("vinculada_al_juego") or VIDEOJUEGO.search(f.get("descripcion", "")))
        conf = [f for f in fichas if f["confirmada"]]
        if not conf:
            return {"estado": f"sin datos públicos confirmados ({len(fichas)} homónimo/s sin relación "
                              "comprobada con el juego)", "fichas": fichas}
        fichas = conf + [f for f in fichas if not f["confirmada"]]
    f0 = fichas[0]
    if es_empresa:
        estado = (f"disuelta ({', '.join(f0['disolucion'])})" if f0.get("disolucion") else "activa según Wikidata")
    else:
        estado = (f"fallecida ({', '.join(f0['fallecimiento'])})" if f0.get("fallecimiento") else "con ficha pública, sin fecha de fallecimiento")
    if len([f for f in fichas if es_empresa or f.get("confirmada")]) > 1:
        estado += f" — OJO: {len(fichas)} fichas posibles, revisar cuál es"
    return {"estado": estado, "fichas": fichas}


def main():
    print(f"ACTUALIZAR CREDITOS - VERSION {VERSION}")
    datos = json.loads((AQUI / "creditos.json").read_text(encoding="utf-8"))
    out = {"fecha": date.today().isoformat(), "version": VERSION, "personas": [], "empresas": [], "correos": []}
    for i, p in enumerate(datos["personas"], 1):
        print(f"[{i}/{len(datos['personas'])}] {p['nombre']}")
        out["personas"].append({"nombre": p["nombre"], "roles": p["roles"], **evaluar(p["nombre"], RUBRO, False)})
    for e in datos["empresas"]:
        nombre = NOMBRE_WIKIDATA.get(e["nombre"], e["nombre"])
        print(f"[empresa] {nombre}")
        out["empresas"].append({"nombre": e["nombre"], **evaluar(nombre, EMPRESA, True)})
    for c in datos["correos"]:
        out["correos"].append({"correo": c["correo"], "estado": dominio_recibe_correo(c["correo"])})

    (AQUI / "estado.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    L = [f"# Estado actual de los créditos — {out['fecha']}", "",
         f"Generado por `actualizar.py` VERSIÓN {VERSION}. Fuentes: Wikidata, el sitio oficial y DNS. "
         "«Sin datos públicos» no significa que la persona no exista: solo que no tiene ficha pública. "
         "Que un sitio web «responda» no prueba que siga siendo de esa empresa (puede estar revendido o redirigido).", ""]
    for titulo, lista in (("Empresas", out["empresas"]), ("Personas", out["personas"])):
        L += [f"## {titulo}", "", "| Nombre | Estado | Ficha | Sitio web | Correo oficial |", "|---|---|---|---|---|"]
        for x in lista:
            fs = x.get("fichas", [{}])
            f = fs[0]
            web = "; ".join(f"{w} ({f.get('sitio_web_estado', '')})" for w in f.get("sitio_web", [])[:1])
            mail = "; ".join(f"{m} ({s})" for m, s in f.get("correo_estado", {}).items())
            ref = " ".join(f"[{g['qid']}]({g['url']})" for g in fs if g.get("url"))
            L.append(f"| {x['nombre']} | {x['estado']} | {ref} | {web} | {mail} |")
        L.append("")
    L += ["## Correos hallados en el juego", ""] + [f"- {c['correo']}: {c['estado']}" for c in out["correos"]] + [""]
    (AQUI / "ESTADO.md").write_text("\n".join(L), encoding="utf-8")
    errores = sum("ERROR" in x["estado"] for x in out["personas"] + out["empresas"])
    print(f"Listo: ESTADO.md ({errores} consultas con error)")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
