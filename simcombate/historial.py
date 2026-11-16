"""Historial de combates simulados: todas las fichas desde el último reset del contador, en un .json junto al .ini.
La ventana Historial muestra las últimas MAXIMO; Stats cuenta todas (pedido del usuario, 16/11/2026).
Cada ficha lleva el número del contador general de pruebas, la fecha y hora, la composición de los dos lados,
el campo y el resultado (porcentaje y batalla de muestra con sus caídas)."""
import json

MAXIMO = 40

def cargar(ruta):
    try:
        with open(ruta, encoding='utf-8') as f: h = json.load(f)
        return h if isinstance(h, list) else []
    except (OSError, ValueError): return []

def guardar(ruta, ficha):
    h = [ficha] + cargar(ruta)   # la más nueva primero; sin tope (el tope es solo de lo que se muestra)
    try:
        with open(ruta, 'w', encoding='utf-8') as f: json.dump(h, f, ensure_ascii=False, indent=1)
    except OSError: pass
    return h

def borrar(ruta):
    """El reset del contador limpia también los registros."""
    try:
        with open(ruta, 'w', encoding='utf-8') as f: json.dump([], f)
    except OSError: pass
