#!/usr/bin/env python3
"""Publica el panel de seguimiento de un cliente a partir del aviso que manda la hoja (repository_dispatch).
Lee el JSON de la variable de entorno PAYLOAD (no se imprime nunca: el repositorio es publico).
Campos: codigo, token, version, nombre (solo primer nombre), estado (mantener|investigar|ajustar, el que confirmo Lorenzo),
objetivo (opcional), dias (texto JSON: nombres de los dias del plan vigente), encabezado y filas (texto JSON: SOLO las columnas
que muestra el panel de la pestaña de respuestas; nunca molestias, comentarios ni cargas)."""
import json, os, re, sys
import generar as G, generar_panel as P, panel_desde_hoja as H

def main():
    try:
        p = json.loads(os.environ['PAYLOAD'])
        codigo, token, version = str(p['codigo']), str(p['token']), str(p['version'])
        nombre, estado, objetivo = str(p['nombre']).strip(), str(p['estado']).strip().lower(), str(p.get('objetivo', '')).strip()
        dias = json.loads(p['dias']) if isinstance(p['dias'], str) else p['dias']
        encabezado = json.loads(p['encabezado']) if isinstance(p['encabezado'], str) else p['encabezado']
        filas = json.loads(p['filas']) if isinstance(p['filas'], str) else p['filas']
    except Exception:
        sys.exit('El aviso de la hoja llego incompleto o mal armado.')
    if not re.fullmatch(r'[A-Za-z0-9-]{1,12}', codigo): sys.exit('Codigo de cliente no valido.')
    if not re.fullmatch(r'[0-9]{1,3}', version): sys.exit('Version no valida.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{20,64}', token): sys.exit('Token del link no valido.')
    if not nombre: sys.exit('Falta el nombre del cliente.')
    if estado not in P.ESTADOS: sys.exit('Estado no valido (mantener, investigar o ajustar).')
    if objetivo and objetivo not in P.SUBE_BIEN: sys.exit('Objetivo no valido.')
    if not dias or len(dias) > 14: sys.exit('Cantidad de dias del plan no valida.')
    if not filas or len(filas) > 120 or len(encabezado) > 20: sys.exit('Cantidad de controles no valida.')
    planes = [[codigo, '', version, str(d)] for d in dias]
    clientes = [[codigo, nombre, token, '', version, '']]
    resp = [[str(x) for x in encabezado]] + [[str(x) for x in f] for f in filas]
    panel, tok = H.main(planes, clientes, resp, codigo, estado, objetivo or None)
    dest = G.AQUI.parent / 'p' / token / 'panel'
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'index.html').write_text(P.pagina(panel), encoding='utf-8')

if __name__ == '__main__':
    main()
