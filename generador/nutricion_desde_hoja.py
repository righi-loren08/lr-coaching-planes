#!/usr/bin/env python3
"""Arma y escribe la pagina de nutricion de un cliente a partir de las filas de la pestaña "Nutricion" de la hoja.
Cada fila: [tipo, D, E, F, G, H] (ya filtradas por codigo y version). Tipos:
  objetivo      D = frase del objetivo ("ganar musculo, ...")
  calorias      D = minimo, E = maximo (ej. 2.000 y 2.200)
  proteina      D = minimo, E = maximo (g)
  regla         D = texto (maximo 4)
  registrar     D = texto
  etiqueta      D = palabra que encabeza cada opcion (por defecto "Opción")
  comida        D = nombre (con horario), E = nota, F = la idea (enfoque), G = nombre corto para el boton (opcional)
  opcion        D = plato en medidas caseras, E = imagen opcional (ej. img/desayuno-1.jpg, ya subida a p/<token>/nutricion/img/), G = kcal, H = proteina (g); pertenece a la ultima comida
  guia_titulo / guia_intro   D = texto (guia opcional, ej. dia de partido); en guia_titulo, E = nombre corto para el boton (opcional)
  guia_item     D = momento, E = texto
El orden de las filas es el orden de la pagina. Devuelve los avisos (lista de textos) y escribe p/<token>/nutricion/index.html."""
import re
import generar as G
import generar_nutricion as N

def armar(filas, nombre, version, revision):
    p = {'nombre': nombre, 'version': version, 'revision': revision, 'reglas': [], 'registrar': [], 'comidas': []}
    guia = {'items': []}
    c = lambda f, i: (f[i] if i < len(f) else '').strip() if isinstance(f[i] if i < len(f) else '', str) else str(f[i])
    for f in filas:
        t = c(f, 0).lower()
        if t == 'objetivo': p['objetivo'] = c(f, 1)
        elif t == 'calorias': p['calorias'] = [c(f, 1), c(f, 2)]
        elif t == 'proteina': p['proteina'] = [c(f, 1), c(f, 2)]
        elif t == 'regla': p['reglas'].append(c(f, 1))
        elif t == 'registrar': p['registrar'].append(c(f, 1))
        elif t == 'etiqueta': p['etiqueta'] = c(f, 1)
        elif t == 'comida': p['comidas'].append({'nombre': c(f, 1), 'nota': c(f, 2), 'enfoque': c(f, 3), 'corto': c(f, 4), 'opciones': []})
        elif t == 'opcion':
            if not p['comidas']: raise SystemExit('Nutricion: una opcion aparece antes de la primera comida.')
            try:
                op = {'plato': c(f, 1), 'kcal': int(float(c(f, 4).replace(',', '.'))), 'prot': int(float(c(f, 5).replace(',', '.')))}
                if c(f, 2):
                    if not re.fullmatch(r'img/[A-Za-z0-9_.-]{1,60}', c(f, 2)): raise SystemExit('Nutricion: nombre de imagen no valido.')
                    op['img'] = c(f, 2)
                p['comidas'][-1]['opciones'].append(op)
            except ValueError:
                raise SystemExit('Nutricion: kcal o proteina no son numeros en "' + c(f, 1)[:30] + '".')
        elif t == 'guia_titulo': guia['titulo'] = c(f, 1); guia['corto'] = c(f, 2)
        elif t == 'guia_intro': guia['intro'] = c(f, 1)
        elif t == 'guia_item': guia['items'].append({'momento': c(f, 1), 'texto': c(f, 2)})
        elif t: raise SystemExit('Nutricion: tipo de fila desconocido: ' + t)
    if guia.get('titulo') and guia['items']: p['guia'] = guia
    return p

def validar(p):
    for k in ('objetivo', 'calorias', 'proteina'):
        if not p.get(k): raise SystemExit('Nutricion: falta ' + k + '.')
    for k in ('calorias', 'proteina'):
        if not all(re.fullmatch(r'[0-9.]+', x) for x in p[k]): raise SystemExit('Nutricion: ' + k + ' debe ser un rango numerico.')
    if not p['comidas']: raise SystemExit('Nutricion: no hay comidas.')
    if not p['reglas'] or len(p['reglas']) > 4: raise SystemExit('Nutricion: hace falta entre 1 y 4 reglas.')
    if not p['registrar']: raise SystemExit('Nutricion: falta "que registrar".')
    for com in p['comidas']:
        if len(com['opciones']) != 2: raise SystemExit('Nutricion: cada comida lleva 2 opciones (' + com['nombre'] + ').')
        if not com['nombre'] or any(not o['plato'] for o in com['opciones']): raise SystemExit('Nutricion: falta nombre o plato.')
    avisos = []
    lo, hi = (float(x.replace('.', '')) for x in p['calorias']); plo, phi = (float(x.replace('.', '')) for x in p['proteina'])
    for suf, excluye in (('sin entrenar', ('Pre-entreno', 'Post-entreno')), ('dia de entrenamiento', ('zzzzz',))):
        for k in (0, 1):
            kc = sum(c['opciones'][k]['kcal'] for c in p['comidas'] if not any(x in c['nombre'] for x in excluye))
            pr = sum(c['opciones'][k]['prot'] for c in p['comidas'] if not any(x in c['nombre'] for x in excluye))
            if not (lo <= kc <= hi and plo <= pr <= phi):
                avisos.append(f'Dia con la opcion {k+1} ({suf}): {kc} kcal, {pr} g de proteina, fuera del rango')
    return avisos

def escribir(p, token):
    N.ETIQ[0] = p.get('etiqueta', 'Opción')
    dest = G.AQUI.parent / 'p' / token / 'nutricion'
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'index.html').write_text(N.pagina(p), encoding='utf-8')
