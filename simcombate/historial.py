"""Historial de combates simulados: las últimas MAXIMO fichas, en un .json junto al .ini.
Cada ficha lleva el número del contador general de pruebas, la fecha y hora, la composición de los dos lados,
el campo y el resultado (porcentaje y batalla de muestra con sus caídas)."""
import json

MAXIMO = 20

def cargar(ruta):
    try:
        with open(ruta, encoding='utf-8') as f: h = json.load(f)
        return h if isinstance(h, list) else []
    except (OSError, ValueError): return []

def guardar(ruta, ficha):
    h = ([ficha] + cargar(ruta))[:MAXIMO]   # la más nueva primero
    try:
        with open(ruta, 'w', encoding='utf-8') as f: json.dump(h, f, ensure_ascii=False, indent=1)
    except OSError: pass
    return h
