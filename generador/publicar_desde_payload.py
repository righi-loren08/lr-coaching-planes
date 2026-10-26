#!/usr/bin/env python3
"""Publica la pagina de un plan a partir del aviso que manda la hoja (repository_dispatch).
Lee el aviso del archivo del evento (GITHUB_EVENT_PATH). No usa variables de entorno con el contenido porque GitHub
muestra las variables en el registro de la ejecucion y el repositorio es publico. Tambien acepta PAYLOAD (para pruebas locales).
Campos: codigo, version, token, nombre (solo primer nombre), revision, planes (texto JSON con filas
[A, C, D, E, F, H, I, J, K, L, M] de la pestaña Planes: codigo, version, dia, orden, id, series, reps, rir, descanso, nota, alt)."""
import json, os, re, sys
import desde_hoja, nutricion_desde_hoja

def leer_aviso():
    if os.environ.get('PAYLOAD'): return json.loads(os.environ['PAYLOAD'])
    with open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8') as f: return json.load(f)['client_payload']

def main():
    try:
        p = leer_aviso()
        codigo, version, token = str(p['codigo']), str(p['version']), str(p['token'])
        nombre, revision = str(p.get('nombre', '')), str(p.get('revision', ''))
        filas = json.loads(p['planes']) if isinstance(p['planes'], str) else p['planes']
    except Exception:
        sys.exit('El aviso de la hoja llego incompleto o mal armado.')
    if not re.fullmatch(r'[A-Za-z0-9-]{1,12}', codigo): sys.exit('Codigo de cliente no valido.')
    if not re.fullmatch(r'[0-9]{1,3}', version): sys.exit('Version no valida.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{20,64}', token): sys.exit('Token del link no valido.')
    if not filas or len(filas) > 400: sys.exit('Cantidad de filas del plan no valida.')
    planes = []
    for f in filas:
        f = [str(x) for x in f] + [''] * (11 - len(f))
        # A=codigo, C=version, D=dia, E=orden, F=id ... se reconstruyen las 13 columnas de la hoja
        planes.append([f[0], '', f[1], f[2], f[3], f[4], '', f[5], f[6], f[7], f[8], f[9], f[10]])
    clientes = [[codigo, nombre, token, '', version, revision]]
    # La nutricion se arma primero: asi la pagina del entrenamiento ya incluye el enlace a la nutricion.
    nut = p.get('nutricion')
    if nut:
        try: nut = json.loads(nut) if isinstance(nut, str) else nut
        except Exception: sys.exit('Las filas de nutricion llegaron mal armadas.')
        if len(nut) > 150: sys.exit('Cantidad de filas de nutricion no valida.')
        if not revision: sys.exit('Falta la fecha de la proxima revision.')
        pn = nutricion_desde_hoja.armar(nut, nombre, 'V' + version, revision)
        avisos = nutricion_desde_hoja.validar(pn)
        for a in avisos: print('AVISO nutricion:', a, file=sys.stderr)
        nutricion_desde_hoja.escribir(pn, token)
    desde_hoja.main(planes, clientes, codigo, version)

if __name__ == '__main__':
    main()
