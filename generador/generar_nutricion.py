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
@media(max-width:420px){.opt{flex-direction:column}.opt img{width:100%;max-width:220px}}
.tabs.nut{grid-template-columns:repeat(auto-fit,minmax(78px,1fr))}.tabs.nut .tab{line-height:1.1;padding:4px 3px}.tabs.nut{position:static;grid-template-columns:repeat(3,1fr);gap:6px;padding:0;margin:0 0 12px}.tabs.nut .tab{min-height:62px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-size:.78rem}.tab .ti{font-size:1.4rem;line-height:1}
.chead{display:flex;align-items:center;gap:12px;margin:0 0 10px}.chead .ico{font-size:2rem;line-height:1;background:var(--soft);border-radius:12px;width:52px;height:52px;display:flex;align-items:center;justify-content:center;flex:none}.chead h3{margin:0}.chead small{color:var(--muted);font:500 .8rem var(--mono)}
.idea{background:var(--soft);border-radius:10px;padding:10px 12px;margin:0 0 8px;font-size:.92rem}.com .sub{font-size:.85rem}
.cifras b{color:var(--fg)}.op2{margin-top:10px;border-top:1px solid var(--line);padding-top:4px}.op2>summary{min-height:44px}.op2 .opt{border-top:0;margin-top:4px}
.rango b{font-size:1.02rem;white-space:nowrap}.rango i{font-style:normal;display:block;font-size:1.4rem;margin:0 0 2px}.reg li::marker{content:'✔ '}"""

ETIQ = ['Opción']
import re, unicodedata

def corto(c):
    """Nombre corto para el boton: el campo 'corto' si existe; si no, lo que va despues de ' · ' sin parentesis."""
    if c.get('corto'): return c['corto']
    n = c['nombre'].split('·', 1)[-1].strip()
    return re.sub(r'\s*\(.*?\)', '', n).strip() or c['nombre']

def hora(c):
    m = re.match(r'\s*(\d{1,2}):(\d{2})', c['nombre'])
    return str(int(m.group(1)) * 60 + int(m.group(2))) if m else ''

def emoji(c):
    n = (c.get('corto') or c['nombre']).lower()
    for k, e in (('pre', '🍌'), ('desayuno', '🍳'), ('media', '🍎'), ('colaci', '🍎'), ('almuerzo', '🍛'), ('merienda', '🥪'), ('cena', '🍽️'), ('club', '⚡'), ('gym', '⚡')):
        if k in n: return e
    return '🍴'

NJS = """(function(){var ts=document.querySelectorAll('.tab');if(!ts.length)return;document.documentElement.classList.add('js');
function show(id,tope){ts.forEach(function(t){t.setAttribute('aria-selected',t.dataset.t===id?'true':'false')});document.querySelectorAll('.dia').forEach(function(d){d.classList.toggle('on',d.id===id)});
try{history.replaceState(null,'','#'+id)}catch(e){}if(tope){var n=document.getElementById(id);if(n)n.scrollIntoView()}}
ts.forEach(function(t){t.addEventListener('click',function(){show(t.dataset.t,false)})});
var h=location.hash.slice(1),ini=ts[0].dataset.t,now=new Date(),m=now.getHours()*60+now.getMinutes(),ok=false;
ts.forEach(function(t){var x=t.dataset.h;if(!ok&&x!==''&&x!==undefined&&+x>=m-30){ini=t.dataset.t;ok=true}});
if(h&&document.getElementById(h))ini=h;show(ini,false)})();"""
def comida(c):
    hr, _, nm = c['nombre'].partition('·') if '·' in c['nombre'] else ('', '', c['nombre'])
    enf = f'<p class="idea">💡 <b>La idea:</b> {esc(c["enfoque"])}</p>' if c.get('enfoque') else ''
    nota = f'<p class="sub" style="margin:0 0 8px">{esc(c["nota"])}</p>' if c.get('nota') else ''
    ops = []
    for i, o in enumerate(c['opciones'], 1):
        img = f'<img src="{esc(o["img"])}" alt="Ejemplo del plato" loading="lazy">' if o.get('img') else ''
        ops.append(f'<div class="opt">{img}<div class="optt"><span class="optl">{ETIQ[0]} {i}</span><p class="plato">{esc(o["plato"])}</p><span class="cifras">🔥 <b>{o["kcal"]}</b> kcal · 💪 <b>{o["prot"]}</b> g de proteína</span></div></div>')
    resto = f'<details class="op2"><summary>Ver otra opción</summary>{"".join(ops[1:])}</details>' if len(ops) > 1 else ''
    cab = f'<div class="chead"><span class="ico">{emoji(c)}</span><div><h3>{esc(nm.strip())}</h3>' + (f'<small>🕒 {esc(hr.strip())}</small>' if hr.strip() else '') + '</div></div>'
    return f'<article class="card com">{cab}{enf}{nota}{ops[0]}{resto}</article>'

def guia(g):
    items = ''.join(f'<li><b>{esc(i["momento"])}:</b> {esc(i["texto"])}</li>' for i in g['items'])
    intro = f'<p class="sub" style="margin:0 0 6px">{esc(g["intro"])}</p>' if g.get('intro') else ''
    return f'<h2>{esc(g["titulo"])}</h2><section class="card">{intro}<ul class="reglas">{items}</ul></section>'

def pagina(p):
    saludo = f'Hola, {esc(p["nombre"])}. ' if p.get('nombre') else ''
    cal0, cal1 = p['calorias']; pr0, pr1 = p['proteina']
    reglas = ''.join(f'<li>{esc(r)}</li>' for r in p['reglas'])
    reg = ''.join(f'<li>{esc(r)}</li>' for r in p['registrar'])
    aviso = f'<p class="aviso">{esc(p["_aviso"])}</p>' if p.get('_aviso') else ''
    tabs, paneles = [], []
    for n, c in enumerate(p['comidas']):
        tabs.append(f'<button type="button" class="tab" role="tab" data-t="m{n}" data-h="{hora(c)}" aria-selected="false"><span class="ti">{emoji(c)}</span>{esc(corto(c))}</button>')
        paneles.append(f'<div class="dia" id="m{n}" role="tabpanel">{comida(c)}</div>')
    if p.get('guia'):
        tabs.append(f'<button type="button" class="tab" role="tab" data-t="mg" data-h="" aria-selected="false"><span class="ti">⚽</span>{esc(p["guia"].get("corto") or p["guia"]["titulo"])}</button>')
        paneles.append(f'<div class="dia" id="mg" role="tabpanel">{guia(p["guia"])}</div>')
    tabs.append('<button type="button" class="tab" role="tab" data-t="mr" data-h="" aria-selected="false"><span class="ti">📋</span>Reglas</button>')
    paneles.append(f'<div class="dia" id="mr" role="tabpanel"><h2>Reglas</h2><section class="card"><ul class="reglas">{reglas}</ul></section></div>')
    nav = f'<nav class="tabs nut" role="tablist" aria-label="Comidas">{"".join(tabs)}</nav>'
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Tu plan de nutrición</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><style>{G.CSS}{EXTRA}</style></head><body><main>
<h1>{saludo}Tu plan de nutrición ({esc(p["version"])})</h1><p class="sub">Primera revisión: {esc(p["revision"])}.</p>{aviso}
<nav class="mods" aria-label="Tu plan"><a href="../">🏋️ Entrenamiento</a><span class="on">🍽️ Nutrición</span></nav>
<h2>Tu punto de partida</h2>
<section class="card"><p style="margin:0">Para {esc(p["objetivo"])}, te propongo arrancar con:</p>
<div class="rango"><div><i>🔥</i><b>{cal0} a {cal1}</b><span>Calorías por día</span></div><div><i>💪</i><b>{pr0} a {pr1} g</b><span>Proteína por día</span></div></div>
<p class="sub" style="margin:0">Es un punto de partida: lo ajustamos con tu peso y cómo te sentís. No hace falta contar nada, los platos ya están pensados para que llegues.</p></section>
<h2>Tus comidas</h2>
{nav}{"".join(paneles)}
<p class="sub">Las cantidades son aproximadas y las fotos son solo de ejemplo.</p>
<h2>Qué registrar</h2><section class="card"><p style="margin:0">Esta semana anotá:</p><ul class="reg">{reg}</ul><p class="sub" style="margin:0">Eso nos dice si el punto de partida está bien o hay que ajustarlo. Un día suelto no cambia nada: miramos la tendencia.</p></section>
<h2>Próximo paso</h2><p>Nos vemos en la revisión el {esc(p["revision"])}. Si algo no te cierra antes, avisame.</p>
<p class="pie">Si algo no se ve o no se entiende, avisame por el chat.</p>
</main><script>{NJS}</script></body></html>'''

if __name__ == '__main__':
    p = json.load(open(sys.argv[1])); token = sys.argv[2]
    ETIQ[0] = p.get('etiqueta', 'Opción')
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
    # Dia tipo: merienda siempre; el pre-entreno se suma solo los dias de entrenamiento
    for sufijo, excluye in (('sin entrenar', 'Pre-entreno'), ('dia de entrenamiento', 'zzzzz')):
        for k in (0, 1):
            kc = sum(c['opciones'][k]['kcal'] for c in p['comidas'] if excluye not in c['nombre'])
            pr = sum(c['opciones'][k]['prot'] for c in p['comidas'] if excluye not in c['nombre'])
            ok = lo <= kc <= hi and plo <= pr <= phi
            print(f'Dia con la opcion {k+1} ({sufijo}): {kc} kcal, {pr} g proteina', 'OK' if ok else 'FUERA DE RANGO')
    dest.mkdir(parents=True, exist_ok=True)
    (dest/'index.html').write_text(pagina(p), encoding='utf-8')
    print(f'p/{sys.argv[2]}/nutricion/index.html')
