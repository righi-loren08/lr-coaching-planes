#!/usr/bin/env python3
"""Genera la pagina del plan de nutricion de un cliente.
Uso: python3 generar_nutricion.py nutricion.json TOKEN
- nutricion.json: primer nombre, version, revision, objetivo, rango de calorias y de proteina,
  comidas (cada una con 2 opciones: plato en medidas caseras, kcal, proteina y una imagen opcional),
  reglas (maximo 4) y que registrar.
- Salida: ../p/<TOKEN>/nutricion/index.html (mismo token que el plan de entrenamiento).
- Las imagenes van en ../p/<TOKEN>/nutricion/img/ y se nombran en el json.
Privacidad: la pagina lleva solo el primer nombre y ningun dato de salud. Las cuentas (gasto, formula) viven en la capa interna, no aca."""
import json, sys, html, pathlib
import generar as G

esc = html.escape
EXTRA = """.rango{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.rango div{background:var(--soft);border-radius:8px;padding:10px;text-align:center}
.rango b{display:block;font:700 1.15rem var(--mono)}.rango span{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.com h3{margin:0 0 4px;font-size:1.05rem}.opt{display:flex;gap:12px;align-items:flex-start;margin:12px 0 0;padding-top:12px;border-top:1px solid var(--line)}
.opt:first-of-type{border-top:0}.opt img{width:132px;height:auto;border-radius:8px;flex:none;background:var(--soft)}.optt{min-width:0}.optl{font:700 .72rem/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
.plato{margin:6px 0}.cifras{font:500 .8rem var(--mono);color:var(--muted)}ul.reglas,ul.reg{padding-left:20px;margin:8px 0}ul.reglas li,ul.reg li{margin:6px 0}
@media(max-width:420px){.opt{flex-direction:column}.opt img{width:100%;max-width:220px}}"""

def comida(c):
    nota = f'<p class="sub" style="margin:0 0 6px">{esc(c["nota"])}</p>' if c.get('nota') else ''
    ops = []
    for i, o in enumerate(c['opciones'], 1):
        img = f'<img src="{esc(o["img"])}" alt="Ejemplo del plato" loading="lazy">' if o.get('img') else ''
        ops.append(f'<div class="opt">{img}<div class="optt"><span class="optl">Opción {i}</span><p class="plato">{esc(o["plato"])}</p><span class="cifras">≈ {o["kcal"]} kcal · {o["prot"]} g de proteína</span></div></div>')
    return f'<article class="card com"><h3>{esc(c["nombre"])}</h3>{nota}{"".join(ops)}</article>'

def pagina(p):
    saludo = f'Hola, {esc(p["nombre"])}. ' if p.get('nombre') else ''
    cal0, cal1 = p['calorias']; pr0, pr1 = p['proteina']
    reglas = ''.join(f'<li>{esc(r)}</li>' for r in p['reglas'])
    reg = ''.join(f'<li>{esc(r)}</li>' for r in p['registrar'])
    aviso = f'<p class="aviso">{esc(p["_aviso"])}</p>' if p.get('_aviso') else ''
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Tu plan de nutrición</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><style>{G.CSS}{EXTRA}</style></head><body><main>
<h1>{saludo}Tu plan de nutrición ({esc(p["version"])})</h1><p class="sub">Primera revisión: {esc(p["revision"])}.</p>{aviso}
<h2>Tu punto de partida</h2>
<section class="card"><p style="margin:0">Para {esc(p["objetivo"])}, te propongo arrancar con:</p>
<div class="rango"><div><b>{cal0} a {cal1}</b><span>Calorías por día</span></div><div><b>{pr0} a {pr1} g</b><span>Proteína por día</span></div></div>
<p class="sub" style="margin:0">Es un punto de partida, no una cifra exacta: lo ajustamos con tu peso y cómo te sentís. No hace falta contar nada al detalle: los platos de abajo ya están pensados para que llegues.</p></section>
<h2>Tus comidas</h2>
{"".join(comida(c) for c in p["comidas"])}
<p class="sub">Las cantidades son aproximadas y las fotos son solo de ejemplo.</p>
<h2>Reglas</h2><section class="card"><ul class="reglas">{reglas}</ul></section>
<h2>Qué registrar</h2><section class="card"><p style="margin:0">Esta semana anotá:</p><ul class="reg">{reg}</ul><p class="sub" style="margin:0">Eso nos dice si el punto de partida está bien o hay que ajustarlo. Un día suelto no cambia nada: miramos la tendencia.</p></section>
<h2>Próximo paso</h2><p>Nos vemos en la revisión el {esc(p["revision"])}. Si algo no te cierra antes, avisame.</p>
<p class="pie">Si algo no se ve o no se entiende, avisame por el chat.</p>
</main></body></html>'''

if __name__ == '__main__':
    p = json.load(open(sys.argv[1])); token = sys.argv[2]
    assert len(p['reglas']) <= 4, 'maximo 4 reglas'
    lo, hi = (float(x.replace('.', '')) for x in p['calorias']); plo, phi = (float(x) for x in p['proteina'])
    dest = G.AQUI.parent/'p'/token/'nutricion'
    for c in p['comidas']:
        assert len(c['opciones']) == 2, ('cada comida lleva 2 opciones', c['nombre'])
        a, b = c['opciones']
        if abs(a['kcal']-b['kcal']) > 0.2*max(a['kcal'], b['kcal']) or abs(a['prot']-b['prot']) > 0.35*max(a['prot'], b['prot']):
            print('AVISO: opciones con aporte distinto en', c['nombre'])
        for o in c['opciones']:
            if o.get('img') and not (dest/o['img']).exists():
                print('AVISO: falta la imagen', o['img'])
    # Dia tipo: sin pre-entreno (usa merienda) y con pre-entreno; opcion 1 todo el dia y opcion 2 todo el dia
    for sufijo, excluye in (('con merienda', 'Pre-entreno'), ('con pre-entreno', 'Merienda')):
        for k in (0, 1):
            kc = sum(c['opciones'][k]['kcal'] for c in p['comidas'] if not c['nombre'].startswith(excluye))
            pr = sum(c['opciones'][k]['prot'] for c in p['comidas'] if not c['nombre'].startswith(excluye))
            ok = lo <= kc <= hi and plo <= pr <= phi
            print(f'Dia con la opcion {k+1} ({sufijo}): {kc} kcal, {pr} g proteina', 'OK' if ok else 'FUERA DE RANGO')
    dest.mkdir(parents=True, exist_ok=True)
    (dest/'index.html').write_text(pagina(p), encoding='utf-8')
    print(f'p/{sys.argv[2]}/nutricion/index.html')
