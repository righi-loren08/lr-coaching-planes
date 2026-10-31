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
EXTRA = """.tabs.nut{position:static;grid-template-columns:repeat(3,minmax(0,1fr));padding:0;margin:0;gap:6px}.tabs.nut .tab{min-height:48px;border-radius:12px;font:600 .8rem/1.1 var(--body);text-align:center;padding:0 4px}.tabs.nut .tab.extra{background:transparent;border:1px dashed var(--accent)}.tabs.nut .tab .x2{font:500 .56rem var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--accent-2)}.tabs.nut .tab[aria-selected=true]{background:var(--fg);border:1px solid var(--fg);color:var(--bg)}.tabs.nut .tab[aria-selected=true] .x2{color:var(--bg)}
.mh{display:flex;flex-direction:column;gap:4px}.mh small{font:500 .7rem var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);padding-left:16px}
.opt{display:flex;flex-direction:column;gap:14px;padding:18px 16px}.optl{font:500 .7rem var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--accent-2)}.opt img{width:100%;max-width:320px;height:auto;border-radius:10px;background:var(--soft)}.plato{margin:0;font-size:1rem;line-height:1.55}
.cifras{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--line);padding-top:14px}.cifras div{display:flex;flex-direction:column;gap:2px}.cifras div+div{padding-left:14px;border-left:1px solid var(--line)}.cifras b{font:700 1.75rem/1 var(--mono)}.cifras span{font:500 .62rem var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.op2>summary{min-height:48px;border-radius:12px;border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font:600 .875rem var(--body)}.op2[open]>summary{margin-bottom:14px}
.tl{list-style:none;margin:0;padding:0;counter-reset:t}.tl li{display:flex;gap:12px;position:relative;padding:0 0 14px;counter-increment:t}.tl li:not(:last-child)::before{content:'';position:absolute;left:19px;top:42px;bottom:2px;width:2px;background:var(--line)}.tl .td{flex:none;width:40px;height:40px;border-radius:50%;background:var(--soft);display:flex;align-items:center;justify-content:center;font:500 .85rem var(--mono);color:var(--accent-2)}.tl .td::before{content:counter(t)}.tl b{display:inline}.tl small{color:var(--muted);font:500 .78rem var(--mono)}.tl p{margin:2px 0 0;font-size:.92rem}
ul.reglas,ul.reg{list-style:none;padding:0;margin:8px 0;display:flex;flex-direction:column;gap:10px}ul.reglas li,ul.reg li{padding-left:22px;position:relative}ul.reglas li::before,ul.reg li::before{content:'';position:absolute;left:2px;top:.55em;width:8px;height:8px;border-radius:50%;background:var(--accent)}"""

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

def es_extra(c):
    n = (c.get('corto') or c['nombre']).lower()
    n = n.split('·')[-1].strip()
    return n.startswith('pre') or n.startswith('post')

NJS = """(function(){var ts=document.querySelectorAll('.tab');if(!ts.length)return;document.documentElement.classList.add('js');
function show(id,tope){ts.forEach(function(t){t.setAttribute('aria-selected',t.dataset.t===id?'true':'false')});document.querySelectorAll('.dia').forEach(function(d){d.classList.toggle('on',d.id===id)});
try{history.replaceState(null,'','#'+id)}catch(e){}if(tope){var n=document.getElementById(id);if(n)n.scrollIntoView()}}
ts.forEach(function(t){t.addEventListener('click',function(){show(t.dataset.t,false)})});
var h=location.hash.slice(1),ini=ts[0].dataset.t,now=new Date(),m=now.getHours()*60+now.getMinutes(),ok=false;
ts.forEach(function(t){var x=t.dataset.h;if(!ok&&x!==''&&x!==undefined&&+x>=m-30){ini=t.dataset.t;ok=true}});
if(h&&document.getElementById(h))ini=h;show(ini,false)})();"""
def comida(c):
    hr, _, nm = c['nombre'].partition('·') if '·' in c['nombre'] else ('', '', c['nombre'])
    enf = f'<div class="callout"><span class="lab">La idea</span>{esc(c["enfoque"])}</div>' if c.get('enfoque') else ''
    nota = f'<p class="sub">{esc(c["nota"])}</p>' if c.get('nota') else ''
    ops = []
    for i, o in enumerate(c['opciones'], 1):
        img = f'<img src="{esc(o["img"])}" alt="Ejemplo del plato" loading="lazy">' if o.get('img') else ''
        ops.append(f'<div class="card opt"><span class="optl">{ETIQ[0]} {i}</span>{img}<p class="plato">{esc(o["plato"])}</p><div class="cifras"><div><b>{o["kcal"]}</b><span>kcal</span></div><div><b>{o["prot"]} g</b><span>de proteína</span></div></div></div>')
    resto = f'<details class="op2"><summary>Ver otra opción</summary>{"".join(ops[1:])}</details>' if len(ops) > 1 else ''
    cab = f'<div class="mh"><h2>{esc(nm.strip())}</h2>' + (f'<small>{esc(hr.strip())}</small>' if hr.strip() else '') + '</div>'
    return f'{cab}{enf}{nota}{ops[0]}{resto}'

def guia(g):
    filas = []
    for i in g['items']:
        tit, _, det = i['momento'].partition(' · ')
        d = f' <small>{esc(det)}</small>' if det else ''
        filas.append(f'<li><span class="td"></span><div><b>{esc(tit)}</b>{d}<p>{esc(i["texto"])}</p></div></li>')
    intro = f'<p class="sub" style="margin:0 0 10px">{esc(g["intro"])}</p>' if g.get('intro') else ''
    return f'<h2>{esc(g["titulo"])}</h2><section class="card">{intro}<ol class="tl">{"".join(filas)}</ol></section>'

def pagina(p):
    cal0, cal1 = p['calorias']; pr0, pr1 = p['proteina']
    reglas = ''.join(f'<li>{esc(r)}</li>' for r in p['reglas'])
    reg = ''.join(f'<li>{esc(r)}</li>' for r in p['registrar'])
    aviso = f'<p class="aviso">{esc(p["_aviso"])}</p>' if p.get('_aviso') else ''
    fijas, extras, paneles = [], [], []
    for n, c in enumerate(p['comidas']):
        ex = es_extra(c)
        t = f'<button type="button" class="tab{" extra" if ex else ""}" role="tab" data-t="m{n}" data-h="{hora(c)}" aria-selected="false"><span>{esc(corto(c))}</span>{"<span class=x2>Extra</span>" if ex else ""}</button>'
        (extras if ex else fijas).append(t)
        paneles.append(f'<div class="dia" id="m{n}" role="tabpanel">{comida(c)}</div>')
    if p.get('guia'):
        fijas.append(f'<button type="button" class="tab" role="tab" data-t="mg" data-h="" aria-selected="false"><span>{esc(p["guia"].get("corto") or p["guia"]["titulo"])}</span></button>')
        paneles.append(f'<div class="dia" id="mg" role="tabpanel">{guia(p["guia"])}</div>')
    fijas.append('<button type="button" class="tab" role="tab" data-t="mr" data-h="" aria-selected="false"><span>Reglas</span></button>')
    paneles.append(f'<div class="dia" id="mr" role="tabpanel"><h2>Reglas</h2><section class="card"><ul class="reglas">{reglas}</ul></section></div>')
    nav = f'<nav class="tabs nut" role="tablist" aria-label="Comidas">{"".join(fijas + extras)}</nav>'
    mods = G.navmods("nut", True, p.get("casa"), "nut", p.get("fuerza"))
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Tu plan de nutrición</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><style>{G.CSS}{EXTRA}</style></head><body><main>
{G.cabecera(p, mods, p["version"])}{aviso}
<div class="hero"><div class="eyebrow">Tu plan de comidas</div><h1>{G.resaltar(p["objetivo"])}</h1>
<div class="stats"><div><b>{cal0}–{cal1}</b><span>Calorías por día</span></div><div><b>{pr0}–{pr1} g</b><span>Proteína por día</span></div></div></div>
<p class="sub">Es un punto de partida: lo ajustamos con tu peso y cómo te sentís. No hace falta contar nada, los platos ya están pensados para que llegues.</p>
{nav}{"".join(paneles)}
<p class="sub">Las cantidades son aproximadas y las fotos son solo de ejemplo.</p>
<h2>Qué registrar</h2><section class="card"><p style="margin:0">Esta semana anotá:</p><ul class="reg">{reg}</ul><p class="sub">Eso nos dice si el punto de partida está bien o hay que ajustarlo. Un día suelto no cambia nada: miramos la tendencia.</p></section>
<footer class="foot"><span class="l">Próxima revisión</span><b>{esc(p["revision"])}</b><p class="pie">Si algo no te cierra antes, avisame. Si algo no se ve o no se entiende, avisame por el chat.</p></footer>
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
    # Dia tipo: las comidas fijas siempre; el pre-entreno y el post-entreno (extras) se suman solo los dias de entrenamiento
    for sufijo, excluye in (('sin entrenar', ('Pre-entreno', 'Post-entreno')), ('dia de entrenamiento', ('zzzzz',))):
        for k in (0, 1):
            kc = sum(c['opciones'][k]['kcal'] for c in p['comidas'] if not any(x in c['nombre'] for x in excluye))
            pr = sum(c['opciones'][k]['prot'] for c in p['comidas'] if not any(x in c['nombre'] for x in excluye))
            ok = lo <= kc <= hi and plo <= pr <= phi
            print(f'Dia con la opcion {k+1} ({sufijo}): {kc} kcal, {pr} g proteina', 'OK' if ok else 'FUERA DE RANGO')
    dest.mkdir(parents=True, exist_ok=True)
    (dest/'index.html').write_text(pagina(p), encoding='utf-8')
    print(f'p/{sys.argv[2]}/nutricion/index.html')
