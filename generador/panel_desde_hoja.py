#!/usr/bin/env python3
"""Arma el panel de un cliente leyendo las pestañas de la hoja unica (exportadas a JSON como listas de filas).
Uso: python3 panel_desde_hoja.py planes.json clientes.json respuestas.json CODIGO ESTADO [--objetivo 'ganar músculo'] [--codigo-respuesta PRUEBA] [--aviso 'texto']
- planes.json     = Planes!A2:D (codigo, nombre, version, dia ...).
- clientes.json   = Clientes!A2:F (codigo, nombre, token, link, version vigente, proxima revision).
- respuestas.json = pestaña de respuestas del control de cuatro semanas, CON la fila de titulos.
- ESTADO          = mantener | investigar | ajustar (el que Lorenzo confirmo en la vista interna).
Las sesiones planificadas de cada control salen de Planes: dias distintos del plan en la version vigente x 4 semanas.
Cada control es una fila de respuestas; el panel se regenera con todos (C1, C2, ...). Solo primer nombre en la pagina."""
import json, re, sys, datetime
import generar as G, generar_panel as P

SEMANAS = 4
DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

def num(x):
    try: return float(str(x).replace(',', '.').strip())
    except ValueError: return None

def celda(f, i): return (f[i] if i < len(f) else '') or ''

def fecha(s):
    m = re.match(r'(\d+)/(\d+)/(\d+)', str(s))
    return datetime.date(int(m[3]), int(m[2]), int(m[1])) if m else None

def otras(txt):
    """'brazo 38, pecho 100,5' -> {'brazo': 38.0, 'pecho': 100.5}"""
    out = {}
    for n, v in re.findall(r'([A-Za-zÁÉÍÓÚáéíóúñÑ ]+?)\s*[:=]?\s*(\d+(?:[.,]\d+)?)', txt or ''):
        out[n.strip().lower()] = num(v)
    return out

def main(planes, clientes, resp, codigo, estado, objetivo=None, cod_resp=None, aviso=None):
    cli = next((c for c in clientes if celda(c, 0) == codigo), None)
    if not cli: sys.exit(f'No existe {codigo} en Clientes')
    version = str(celda(cli, 4)); token = celda(cli, 2)
    dias = {celda(f, 3).strip() for f in planes if celda(f, 0) == codigo and str(celda(f, 2)) == version and celda(f, 3).strip()}
    if not dias: sys.exit(f'Planes no tiene filas de {codigo} en la version {version}')
    planificadas = len(dias)*SEMANAS
    h = resp[0]; ix = lambda n: next(i for i, x in enumerate(h) if str(x).startswith(n))
    cod = (cod_resp or codigo).strip().upper()
    filas = sorted((f for f in resp[1:] if celda(f, ix('Código')).strip().upper() == cod), key=lambda f: fecha(celda(f, 0)) or datetime.date.min)
    if not filas: sys.exit(f'No hay respuestas con el codigo {cod}')
    ctrls = []
    for k, f in enumerate(filas, 1):
        g = lambda n: celda(f, ix(n))
        c = {'semana': f'C{k}', 'peso': [v for v in (num(g('Peso lunes')), num(g('Peso miércoles')), num(g('Peso viernes'))) if v is not None],
             'sesiones': int(num(g('Sesiones realizadas')) or 0), 'planificadas': planificadas,
             'adherencia': g('Comidas del plan').strip().lower(), 'rendimiento': g('Rendimiento').strip().lower(),
             'cintura': num(g('Cintura')), 'otras': otras(g('Otras medidas'))}
        for clave, n in (('sueno', 'Horas de sueño'), ('energia', 'Energía'), ('hambre', 'Hambre'), ('satisfaccion', 'Satisfacción')):
            v = num(g(n))
            if v is not None: c[clave] = v
        ctrls.append(c)
    ult = fecha(celda(filas[-1], 0))
    panel = {'nombre': celda(cli, 1).split()[0], 'version': f'V{version}' if version.isdigit() else version,
             'actualizado': f'{DIAS[ult.weekday()]} {ult.day} de {MESES[ult.month-1]}', 'estado': estado, 'controles': ctrls}
    if objetivo: panel['objetivo'] = objetivo
    if aviso: panel['_aviso'] = aviso
    return panel, token

if __name__ == '__main__':
    a = sys.argv[1:]; opt = {}
    while '--objetivo' in a or '--codigo-respuesta' in a or '--aviso' in a:
        for flag in ('--objetivo', '--codigo-respuesta', '--aviso'):
            if flag in a:
                i = a.index(flag); opt[flag] = a[i+1]; del a[i:i+2]
    planes, clientes, resp = (json.load(open(x)) for x in a[:3])
    panel, token = main(planes, clientes, resp, a[3], a[4], opt.get('--objetivo'), opt.get('--codigo-respuesta'), opt.get('--aviso'))
    assert panel['estado'] in P.ESTADOS, 'estado invalido'
    dest = G.AQUI.parent/'p'/token/'panel'; dest.mkdir(parents=True, exist_ok=True)
    (dest/'index.html').write_text(P.pagina(panel), encoding='utf-8')
    print(f'p/{token}/panel/index.html  ·  planificadas por control: {panel["controles"][0]["planificadas"]}')
