#!/usr/bin/env python3
"""Arma la pagina de un cliente desde las pestañas Planes y Clientes del Sheet.
Uso: python3 desde_hoja.py planes.json clientes.json CODIGO [VERSION]
- planes.json  = valores de Planes!A2:M (lista de filas, columnas A..M).
- clientes.json = valores de Clientes!A2:F.
Convencion de Planes: Orden 'pie' = linea final de la pagina (se escribe en la Nota; no es un dia ni un ejercicio, ponerle el nombre de un dia que ya exista). Orden numerico = ejercicio principal; Orden 'cal' = calentamiento del dia
(la Nota de la 1ra fila 'cal' del dia es la nota de calentamiento). Columna M = ID de la alternativa.
Si el cliente no tiene token en Clientes, crea uno nuevo. Imprime JSON con token, ruta y link para guardar en Clientes."""
import json, sys, secrets
import generar as g

MATERIAL_CASA = 'una mesa robusta, una silla o banco, una mochila con peso, una toalla y botellas o garrafas con agua'
BASE = 'https://righi-loren08.github.io/lr-coaching-planes/p/'

def celda(f, i): return (f[i] if i < len(f) else '') or ''

def main(planes, clientes, codigo, version=None):
    cli = next((c for c in clientes if celda(c, 0) == codigo), None)
    if not cli: sys.exit(f'No existe el cliente {codigo} en Clientes')
    version = version or celda(cli, 4)
    if not version: sys.exit('Falta la version vigente (Clientes, columna E)')
    token = celda(cli, 2) or secrets.token_urlsafe(18)
    filas = [f for f in planes if celda(f, 0) == codigo and str(celda(f, 2)) == str(version)]
    if not filas: sys.exit(f'Planes no tiene filas de {codigo} version {version}')
    dias = {}
    nota_final = ''
    for f in filas:
        if str(celda(f, 4)).strip().lower() == 'pie':  # Orden 'pie': la Nota es una linea final de la pagina
            nota_final = celda(f, 11).strip()
            continue
        d = dias.setdefault(celda(f, 3), {'nombre': celda(f, 3), 'ejercicios': []})
        eid = celda(f, 5).strip()
        if eid not in g.EJ: sys.exit(f'ID de ejercicio inexistente: {eid!r} ({celda(f,3)})')
        if str(celda(f, 4)).strip().lower() == 'cal':
            c = d.setdefault('calentamiento', {'nota': celda(f, 11), 'ejercicios': []})
            c['ejercicios'].append(eid)
            continue
        it = {'id': eid, 'series': celda(f, 7), 'reps': celda(f, 8), 'rir': celda(f, 9), 'descanso': celda(f, 10)}
        if celda(f, 11): it['nota'] = celda(f, 11)
        if celda(f, 12): it['alt'] = celda(f, 12).strip()
        for k in ('series', 'reps', 'rir', 'descanso'):
            if str(it[k]) == '': sys.exit(f'Falta {k} en {eid} ({celda(f,3)})')
        d['ejercicios'].append((float(celda(f, 4) or 0), it))
    plan = {'version': f'V{version}' if str(version).isdigit() else str(version),
            'revision': celda(cli, 5) or 'a definir', 'dias': [], 'codigo': codigo}
    if nota_final: plan['nota_final'] = nota_final
    nombre = celda(cli, 1).split()[0] if celda(cli, 1) else ''
    if nombre: plan['nombre'] = nombre
    for d in dias.values():
        d['ejercicios'] = [it for _, it in sorted(d['ejercicios'], key=lambda x: x[0])]
        if d['nombre'].strip().lower().startswith('casa'):  # dias 'Casa · Superior: ...' van a la pestaña de entrenamiento en casa
            d['nombre'] = d['nombre'].split('·', 1)[1].strip() if '·' in d['nombre'] else d['nombre'].strip()[4:].strip(' :-')
            plan.setdefault('casa_dias', []).append(d)
        else:
            plan['dias'].append(d)
    if plan.get('casa_dias'): plan['casa_material'] = MATERIAL_CASA
    for d in plan['dias'] + plan.get('casa_dias', []):
        for it in d['ejercicios']:
            if it.get('alt') and it['alt'] not in g.EJ: sys.exit(f'Alternativa inexistente: {it["alt"]}')
            if not it.get('alt'): print('AVISO: sin alternativa en', it['id'], file=sys.stderr)
    dest = g.AQUI.parent / 'p' / token
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / 'nutricion' / 'index.html').exists(): plan['nutricion'] = True  # enlace a la nutricion bajo el mismo link
    (dest / 'index.html').write_text(g.pagina(plan), encoding='utf-8')
    if plan.get('casa_dias'):
        (dest / 'casa').mkdir(exist_ok=True)
        (dest / 'casa' / 'index.html').write_text(g.pagina(plan, casa=True), encoding='utf-8')
    elif (dest / 'casa').exists():  # si ya no hay sesiones de casa, se borra la pagina vieja
        import shutil; shutil.rmtree(dest / 'casa')
    print(json.dumps({'codigo': codigo, 'token': token, 'ruta': f'p/{token}/index.html', 'link': BASE + token + '/'}))

if __name__ == '__main__':
    a = sys.argv
    main(json.load(open(a[1])), json.load(open(a[2])), a[3], a[4] if len(a) > 4 else None)
