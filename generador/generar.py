#!/usr/bin/env python3
"""Genera la pagina de plan de un cliente.
Uso: python3 generar.py plan.json [token]
- datos/ejercicios.json: copia de la pestaña Ejercicios del Sheet (sin datos de personas).
- plan.json: dias y ejercicios del cliente (solo ID de ejercicio + series/reps/RIR/descanso/nota).
- Salida: ../p/<token>/index.html. El token (largo y aleatorio) es el link privado del cliente.
Privacidad: la pagina lleva como mucho el primer nombre (campo opcional 'nombre'), nunca datos de salud, y pide que no la indexen los buscadores."""
import json, re, sys, html, secrets, pathlib, unicodedata

AQUI = pathlib.Path(__file__).parent
EJ = {e['id']: e for e in json.load(open(AQUI/'datos'/'ejercicios.json'))}
esc = html.escape

def yt(u):
    m = re.search(r'(?:v=|shorts/)([\w-]{11})', u or '')
    return m.group(1) if m else None

CSS = """:root{--bg:#0c0c0b;--card:#171614;--fg:#f2ede6;--muted:#9b9288;--line:#2c2925;--accent:#ff4b1f;--accent-fg:#fff;--soft:#201e1b;--warn:#3a2a14;--display:'Anton','Arial Narrow',sans-serif;--body:'Archivo','Helvetica Neue',Arial,sans-serif;--mono:'JetBrains Mono',Menlo,monospace;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 var(--body)}
main{max-width:640px;margin:0 auto;padding:20px 16px 48px}h1{font-family:var(--display);font-weight:400;font-size:1.9rem;line-height:1.15;margin:0 0 4px;text-wrap:balance;text-transform:uppercase;letter-spacing:.02em}h2{font-family:var(--display);font-weight:400;font-size:1.25rem;margin:28px 0 10px;text-transform:uppercase;letter-spacing:.06em;border-left:4px solid var(--accent);padding-left:10px}
.sub{color:var(--muted);margin:0 0 16px}.aviso{background:var(--warn);border-radius:8px;padding:10px 12px;font-size:.9rem;margin:0 0 20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:0 0 14px}.warm ol{margin:8px 0 0;padding-left:20px}.warm li{margin:4px 0}
.ex h3{margin:0 0 6px;font-size:1.05rem}.meta{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}.meta div{background:var(--soft);border-radius:8px;padding:8px;text-align:center;min-width:0}
.meta b{display:block;font-size:1rem;font-family:var(--mono)}.meta span{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}.nota{margin:8px 0;font-weight:600}.why{margin:8px 0}
details{margin-top:10px;border-top:1px solid var(--line);padding-top:10px}summary{cursor:pointer;font-weight:600;color:var(--accent);min-height:44px;display:flex;align-items:center}
.how{margin:8px 0 12px}.cuidado{font-size:.9rem;color:var(--muted);margin:0 0 12px}.video{position:relative;width:100%;aspect-ratio:16/9;background:#000;border-radius:8px;overflow:hidden}
.video iframe{position:absolute;inset:0;width:100%;height:100%;border:0}.vbtn{min-height:44px;padding:0 14px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--fg);font:inherit;margin-top:8px}
.enlace{font-size:.85rem;color:var(--muted);margin:8px 0 0}.enlace a{color:var(--accent)}.altnota{font-size:.9rem;color:var(--muted);margin:8px 0}.altw{margin-top:10px}.altbox{margin-top:8px;border:1px dashed var(--accent);border-radius:8px;padding:10px 12px}.altlab{font:700 .72rem/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}.altn{font-weight:700;margin:6px 0 2px}.altbox details{margin-top:6px;padding-top:0;border-top:0}.sinvideo{font-size:.9rem;color:var(--muted)}.pie{font-size:.85rem;color:var(--muted);margin-top:24px}
.tabs{display:grid;grid-template-columns:repeat(auto-fit,minmax(60px,1fr));gap:4px;margin:0 0 8px;padding:8px 0;position:sticky;top:0;z-index:5;background:var(--bg)}.tab{min-height:44px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);font:600 .8rem var(--body);padding:0 2px;cursor:pointer}.tab[aria-selected=true]{background:var(--accent);border-color:var(--accent);color:var(--accent-fg)}.js .dia{display:none}.js .dia.on{display:block}.dia{scroll-margin-top:64px}.dia>h2:first-child{margin-top:16px}
.mods{display:grid;grid-template-columns:repeat(auto-fit,minmax(0,1fr));gap:6px;margin:0 0 14px}.mods.m3 a,.mods.m3 span{font-size:.78rem;gap:4px;padding:0 4px}.mods a,.mods span{display:flex;align-items:center;justify-content:center;gap:6px;min-height:44px;border-radius:999px;border:1px solid var(--line);background:var(--card);color:var(--fg);font:700 .85rem var(--body);text-decoration:none}.mods .on{background:var(--accent);border-color:var(--accent);color:var(--accent-fg)}"""

JS = """(function(){var cur=null;document.querySelectorAll('details.ex-d').forEach(function(d){d.addEventListener('toggle',function(){var box=d.querySelector('.vslot');if(!box)return;
if(d.open){document.querySelectorAll('.vslot').forEach(function(b){if(b!==box)b.innerHTML=''});
if(!box.firstChild){var v=box.dataset.v,w=document.createElement('div');w.className='video';var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+v;f.title=box.dataset.t;f.allow='encrypted-media; picture-in-picture';f.allowFullscreen=true;f.referrerPolicy='strict-origin-when-cross-origin';w.appendChild(f);box.appendChild(w);
var r=document.createElement('button');r.type='button';r.className='vbtn';r.textContent='↻ Recargar video';r.onclick=function(){f.src=f.src};box.appendChild(r)}}else{box.innerHTML=''}})})})();
document.querySelectorAll('details.altw').forEach(function(d){d.addEventListener('toggle',function(){if(!d.open){d.querySelectorAll('.vslot').forEach(function(b){b.innerHTML=''});d.querySelectorAll('details.ex-d[open]').forEach(function(x){x.open=false})}})});
(function(){var ts=document.querySelectorAll('.tab');if(!ts.length)return;document.documentElement.classList.add('js');
function show(id,tope){ts.forEach(function(t){t.setAttribute('aria-selected',t.dataset.t===id?'true':'false')});document.querySelectorAll('.dia').forEach(function(d){d.classList.toggle('on',d.id===id)});
document.querySelectorAll('.vslot').forEach(function(b){b.innerHTML=''});document.querySelectorAll('details.ex-d[open],details.altw[open]').forEach(function(d){d.open=false});
try{history.replaceState(null,'','#'+id)}catch(e){}if(tope){var n=document.getElementById(id);if(n)n.scrollIntoView()}}
ts.forEach(function(t){t.addEventListener('click',function(){show(t.dataset.t,true)})});
var h=location.hash.slice(1),dias=['domingo','lunes','martes','miercoles','jueves','viernes','sabado'],hoy=dias[new Date().getDay()],ini=ts[0].dataset.t;
ts.forEach(function(t){if(t.dataset.k===hoy)ini=t.dataset.t});if(h&&document.getElementById(h))ini=h;show(ini,false)})();"""

def cuerpo(e):
    vid = yt(e['video'])
    video = (f'<div class="vslot" data-v="{vid}" data-t="{esc(e["nombre"])}"></div><p class="enlace">Si el video no carga: <a href="{esc(e["video"])}" target="_blank" rel="noopener noreferrer">abrilo en YouTube</a></p>' if vid
             else '<p class="sinvideo">Este ejercicio se explica con el texto de arriba.</p>' if 'sin video' in e['video']
             else '<p class="sinvideo">Video en preparación. Mientras tanto, seguí la explicación de arriba.</p>')
    cuidado = f'<p class="cuidado"><b>Ojo:</b> {esc(e["cuidado"])}</p>' if e['cuidado'] else ''
    return f'<p class="how">{esc(e["como"])}</p>{cuidado}{video}'

def tarjeta(i, it, casa=False):
    e = EJ[it['id']]
    nota = f'<p class="nota">{esc(it["nota"])}</p>' if it.get('nota') else ''
    alt = ''
    if it.get('alt'):
        a = EJ[it['alt']]
        alt = f'''<details class="altw"><summary>{'¿No tenés este material? Mirá la opción 2' if casa else '¿No tenés esta máquina? Mirá la opción 2'}</summary><div class="altbox"><span class="altlab">Opción 2 · misma zona</span><p class="altn">{esc(a["nombre"])}</p><p class="altnota">{'Usala si no tenés el material o este ejercicio no te sale. Mismas series, repeticiones y descanso.' if casa else 'Usala si no tenés esta máquina o está ocupada. Mismas series, repeticiones y descanso.'}</p><details class="ex-d alt"><summary>Cómo se hace y video</summary>{cuerpo(a)}</details></div></details>'''
    return f'''<article class="card ex"><h3>{i}. {esc(e["nombre"])}</h3>
<div class="meta"><div><b>{esc(it["series"])} × {esc(it["reps"])}</b><span>Series</span></div><div><b>{esc(it["rir"])}</b><span>Esfuerzo</span></div><div><b>{esc(it["descanso"])}</b><span>Descanso</span></div></div>
{nota}
<details class="ex-d"><summary>Cómo se hace y video</summary><p class="why">{esc(e["por_que"])}</p>{cuerpo(e)}</details>{alt}</article>'''

def navmods(activo, nut, casa, donde, fuerza=False):
    """Botones de modulos: Entrenamiento | Nutricion | Fuerza | Casa. donde = carpeta de la pagina actual ('gym','nut','casa','fuerza')."""
    dest = {'gym': '', 'nut': 'nutricion/', 'fuerza': 'fuerza/', 'casa': 'casa/'}
    pre = '' if donde == 'gym' else '../'
    ruta = {k: ('' if k == donde else pre + v) for k, v in dest.items()}
    etq = {'gym': '🏋️ ' + ('Hipertrofia' if fuerza else 'Gimnasio' if casa else 'Entrenamiento'), 'nut': '🍽️ Nutrición', 'fuerza': '💪 Fuerza', 'casa': '🏠 En casa'}
    orden = ['gym'] + (['nut'] if nut else []) + (['fuerza'] if fuerza else []) + (['casa'] if casa else [])
    if len(orden) < 2: return ''
    b = ''.join(f'<span class="on">{etq[k]}</span>' if k == activo else f'<a href="{ruta[k]}">{etq[k]}</a>' for k in orden)
    return f'<nav class="mods{" m3" if len(orden) >= 3 else ""}" aria-label="Tu plan">{b}</nav>'

def pagina(plan, casa=False, fuerza=False):
    out = []
    tabs = []
    dias = plan['casa_dias'] if casa else plan['fuerza_dias'] if fuerza else plan['dias']
    for n, d in enumerate(dias):
        corto = d['nombre'].split(':')[0].strip()
        clave = ''.join(ch for ch in unicodedata.normalize('NFD', corto.lower()) if unicodedata.category(ch) != 'Mn')
        tabs.append(f'<button type="button" class="tab" role="tab" data-t="d{n}" data-k="{esc(clave)}" aria-selected="false">{esc(corto)}</button>')
        out.append(f'<div class="dia" id="d{n}" role="tabpanel"><h2>{esc(d["nombre"])}</h2>')
        c = d.get('calentamiento')
        if c:
            li = ''.join(f'<li>{esc(EJ[x]["nombre"].replace(" (calentamiento)",""))}</li>' for x in c['ejercicios'])
            out.append(f'<section class="card warm"><b>Calentamiento del día</b><p class="sub" style="margin:4px 0 0">{esc(c["nota"])}</p><ol>{li}</ol></section>')
        for i, it in enumerate(d['ejercicios'], 1):
            out.append(tarjeta(i, it, casa))
        out.append('</div>')
    nav = f'<nav class="tabs" role="tablist" aria-label="Sesiones">{"".join(tabs)}</nav>' if len(tabs) > 1 else ''
    saludo = f'Hola, {esc(plan["nombre"])}. ' if plan.get('nombre') else ''
    aviso = f'<p class="aviso">{esc(plan["_aviso"])}</p>' if plan.get('_aviso') else ''
    tiene_casa = bool(plan.get('casa_dias'))
    tiene_fuerza = bool(plan.get('fuerza_dias'))
    donde = 'casa' if casa else 'fuerza' if fuerza else 'gym'
    nut = navmods(donde, plan.get('nutricion'), tiene_casa, donde, tiene_fuerza)
    titulo = 'Tu entrenamiento en casa' if casa else 'Tu bloque de fuerza' if fuerza else 'Tu plan de hipertrofia' if tiene_fuerza else 'Tu plan de entrenamiento'
    intro = (f'<p class="sub">Usalo cuando no puedas ir al gimnasio: hacé la sesión de casa ese mismo día (la de tren superior si te perdés lunes o jueves; la de tren inferior si te perdés martes o viernes). No hace falta recuperar el día perdido.</p><p class="sub"><b>Necesitás:</b> {esc(plan["casa_material"])}.</p>' if casa and plan.get('casa_material') else '')
    if fuerza and plan.get('fuerza_intro'): intro = f'<p class="sub">{esc(plan["fuerza_intro"])}</p>'
    final = f'<p class="sub">{esc(plan["nota_final"])}</p>' if plan.get('nota_final') else ''
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{titulo}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><style>{CSS}</style></head><body><main>
<h1>{saludo}{titulo} ({esc(plan["version"])})</h1><p class="sub">Primera revisión: {esc(plan["revision"])}.</p>{aviso}
{nut}{intro}{nav}{"".join(out)}
{final}<p class="pie">Si algo no se ve o no se entiende, avisame por el chat. Si sentís dolor (no cansancio), frená ese ejercicio y escribime.</p>
</main><script>{JS}</script></body></html>'''

if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    token = sys.argv[2] if len(sys.argv) > 2 else secrets.token_urlsafe(18)
    for d in plan['dias']:
        for it in d['ejercicios']:
            assert it['id'] in EJ, it['id']
            if it.get('alt'):
                assert it['alt'] in EJ and it['alt'] != it['id'], ('alt invalida', it['id'])
                m, n = EJ[it['id']], EJ[it['alt']]
                if m['musculo'].split()[0] != n['musculo'].split()[0] or not yt(n['video']):
                    print('AVISO: revisar alternativa', it['id'], '->', it['alt'], '(distinto musculo o sin video)')
            else:
                print('AVISO: sin alternativa en', it['id'])
    dest = AQUI.parent/'p'/token
    dest.mkdir(parents=True, exist_ok=True)
    (dest/'index.html').write_text(pagina(plan), encoding='utf-8')
    print(f'p/{token}/index.html')
