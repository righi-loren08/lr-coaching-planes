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

CSS = """:root{--bg:#0c0c0b;--card:#171614;--fg:#f2ede6;--muted:#9b9288;--line:#2c2925;--accent:#ff4b1f;--accent-2:#ff8a5c;--accent-fg:#0c0c0b;--soft:#201e1b;--warn:#3a2a14;--display:'Anton','Arial Narrow',sans-serif;--body:'Archivo','Helvetica Neue',Arial,sans-serif;--mono:'JetBrains Mono',Menlo,monospace;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 var(--body)}
main{max-width:640px;margin:0 auto;padding:20px 16px 48px;display:flex;flex-direction:column;gap:20px}
.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.head{display:flex;flex-direction:column;gap:14px}.top{display:flex;align-items:center;justify-content:space-between;gap:12px}.logo{font:400 1.25rem var(--display);letter-spacing:.03em;text-transform:uppercase}.logo b{font-weight:400;color:var(--accent)}.ver{font:500 .7rem var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.mods{display:grid;grid-template-columns:repeat(var(--n,3),minmax(0,1fr));gap:6px;padding:4px;background:var(--card);border:1px solid var(--line);border-radius:999px}.mods a,.mods span{display:flex;align-items:center;justify-content:center;min-height:44px;padding:0 4px;border-radius:999px;color:var(--fg);font:600 .8rem/1.1 var(--body);text-decoration:none;text-align:center}.mods.m4 a,.mods.m4 span{font-size:.7rem}.mods .on{background:var(--accent);color:var(--accent-fg);font-weight:700}
.hola{margin:0;color:var(--muted);font-size:.9rem}.aviso{background:var(--warn);border-radius:10px;padding:10px 12px;font-size:.9rem;margin:0}
.eyebrow{font:500 .7rem var(--mono);letter-spacing:.18em;text-transform:uppercase;color:var(--accent-2)}
h1,.dt{font:400 clamp(2rem,11vw,2.75rem)/1 var(--display);letter-spacing:.01em;text-transform:uppercase;text-wrap:balance;overflow-wrap:break-word;margin:0}.dt em,h1 em{font-style:normal;color:var(--accent)}
h2{font:400 1.75rem/1.1 var(--display);margin:0;text-transform:uppercase;letter-spacing:.03em;border-left:4px solid var(--accent);padding-left:12px}h2.dt{border:0;padding:0}
.hero{display:flex;flex-direction:column;gap:10px;padding-top:4px}
.stats{display:grid;grid-template-columns:repeat(var(--n,2),minmax(0,1fr));border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin-top:6px}.stats div{padding:14px 0 14px 14px;border-left:1px solid var(--line);min-width:0}.stats div:first-child{padding-left:0;border-left:0}.stats b{display:block;font:500 1.3rem/1.2 var(--mono);white-space:nowrap}.stats span{font:500 .62rem var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.sub{color:var(--muted);margin:0;font-size:.9rem}.sub b{color:var(--fg)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.callout{padding:12px 14px;border-radius:10px;background:var(--soft);border-left:3px solid var(--accent);font-size:.9rem;line-height:1.55}.callout .lab{display:block;font:500 .62rem var(--mono);letter-spacing:.14em;text-transform:uppercase;color:var(--accent-2);margin-bottom:4px}.callout p{margin:0}.callout p+p{margin-top:6px}
.warm{display:flex;flex-direction:column;gap:12px}.wh{display:flex;align-items:center;justify-content:space-between;gap:12px}.wh h3{margin:0;font:400 1.125rem var(--display);letter-spacing:.05em;text-transform:uppercase}.wh span{font:500 .7rem var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--accent-2)}
.warm ol{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px;font-size:.875rem;counter-reset:w}.warm li{display:flex;gap:10px;counter-increment:w}.warm li::before{content:counter(w,decimal-leading-zero);font:500 .75rem var(--mono);color:var(--accent-2);padding-top:2px}.warm p{margin:0;font-size:.8rem;color:var(--muted)}
.ex{display:flex;flex-direction:column;gap:14px;padding:18px 16px}.exh{display:flex;align-items:flex-start;gap:14px}.exn{font:400 2.5rem/1 var(--display);color:var(--accent);min-width:34px}.exh h3{margin:2px 0 2px;font-size:1.125rem;line-height:1.25}.mus{font:500 .62rem var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.sr{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}.sr b{font:700 2.1rem/1 var(--mono);white-space:nowrap}.sr span{font-size:.8rem;color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{display:inline-flex;align-items:center;min-height:32px;padding:0 12px;border-radius:999px;border:1px solid var(--line);background:var(--soft);font-size:.8rem;font-weight:600}
.why{margin:0 0 8px}.how{margin:8px 0 12px}.cuidado{font-size:.9rem;color:var(--muted);margin:0 0 12px}.video{position:relative;width:100%;aspect-ratio:16/9;background:#000;border-radius:10px;overflow:hidden}
.video iframe{position:absolute;inset:0;width:100%;height:100%;border:0}.vbtn{min-height:44px;padding:0 14px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--fg);font:inherit;margin-top:8px}
.enlace{font-size:.85rem;color:var(--muted);margin:8px 0 0}.enlace a{color:var(--accent-2)}.sinvideo{font-size:.9rem;color:var(--muted)}
summary{cursor:pointer;list-style:none}summary::-webkit-details-marker{display:none}
.acts{display:flex;flex-wrap:wrap;gap:8px}.acts>details{flex:1 1 calc(50% - 4px);min-width:0}.acts>details[open]{flex-basis:100%;order:2}
.acts>details>summary{min-height:48px;border-radius:12px;display:flex;align-items:center;justify-content:center;gap:8px;font:600 .875rem var(--body);border:1px solid var(--line);color:var(--fg)}.acts>details.ex-d>summary{background:var(--accent);border-color:var(--accent);color:var(--accent-fg);font-weight:700}.acts>details[open]>summary{margin-bottom:12px}
.altbox{border:1px dashed var(--accent);border-radius:12px;padding:12px}.altlab{font:700 .65rem/1 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--accent-2)}.altn{font-weight:700;margin:6px 0 2px}.altnota{font-size:.9rem;color:var(--muted);margin:0 0 10px}.altbox details>summary{min-height:44px;display:flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:12px;font:600 .875rem var(--body)}.altbox details[open]>summary{margin-bottom:12px}
.tabs{display:grid;grid-template-columns:repeat(auto-fit,minmax(52px,1fr));gap:6px;position:sticky;top:0;z-index:5;background:var(--bg);padding:8px 0;margin:-8px 0}
.tab{min-height:56px;border:1px solid var(--line);border-radius:12px;background:var(--card);color:var(--fg);display:flex;flex-direction:column;align-items:center;justify-content:center;font:inherit;padding:0 2px;cursor:pointer}.tab .d1{font:500 .62rem var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}.tab .d2{font:400 1.25rem/1.1 var(--display)}.tab[aria-selected=true]{background:var(--fg);border-color:var(--fg);color:var(--bg)}.tab[aria-selected=true] .d1{color:var(--bg)}
.js .dia{display:none}.js .dia.on{display:flex;flex-direction:column;gap:20px}.dia{scroll-margin-top:72px;display:flex;flex-direction:column;gap:20px}
.foot{display:flex;flex-direction:column;gap:6px;border-top:1px solid var(--line);padding-top:14px}.foot .l{font:500 .62rem var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}.foot b{font-size:.95rem}.pie{font-size:.85rem;color:var(--muted);margin:0}"""

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

PLAY = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 4v16l13-8z"/></svg>'

def tarjeta(i, it, casa=False):
    e = EJ[it['id']]
    nota = f'<div class="callout">{esc(it["nota"])}</div>' if it.get('nota') else ''
    alt = ''
    if it.get('alt'):
        a = EJ[it['alt']]
        alt = f'''<details class="altw"><summary>Ver alternativa</summary><div class="altbox"><span class="altlab">Opción 2 · misma zona</span><p class="altn">{esc(a["nombre"])}</p><p class="altnota">{'Usala si no tenés el material o este ejercicio no te sale. Mismas series, repeticiones y descanso.' if casa else 'Usala si no tenés esta máquina o está ocupada. Mismas series, repeticiones y descanso.'}</p><details class="ex-d alt"><summary>Cómo se hace y video</summary>{cuerpo(a)}</details></div></details>'''
    tiene_video = bool(yt(e['video']))
    boton = f'<details class="ex-d"><summary>{PLAY + "Ver video" if tiene_video else "Cómo se hace"}</summary><p class="why">{esc(e["por_que"])}</p>{cuerpo(e)}</details>'
    return f'''<article class="card ex"><div class="exh"><div class="exn">{i}</div><div><h3>{esc(e["nombre"])}</h3><div class="mus">{esc(e.get("musculo",""))}</div></div></div>
<div class="sr"><b>{esc(it["series"])} × {esc(it["reps"])}</b><span>series × repeticiones</span></div>
<div class="chips"><span class="chip">{esc(it["rir"])}</span><span class="chip">Descanso {esc(it["descanso"])}</span></div>
{nota}
<div class="acts">{boton}{alt}</div></article>'''

def navmods(activo, nut, casa, donde, fuerza=False):
    """Botones de modulos: Hipertrofia | Nutricion | Fuerza | En casa. donde = carpeta de la pagina actual ('gym','nut','casa','fuerza')."""
    dest = {'gym': '', 'nut': 'nutricion/', 'fuerza': 'fuerza/', 'casa': 'casa/'}
    pre = '' if donde == 'gym' else '../'
    ruta = {k: ('' if k == donde else pre + v) for k, v in dest.items()}
    etq = {'gym': 'Hipertrofia' if fuerza else 'Gimnasio' if casa else 'Entrenamiento', 'nut': 'Nutrición', 'fuerza': 'Fuerza', 'casa': 'En casa'}
    orden = ['gym'] + (['nut'] if nut else []) + (['fuerza'] if fuerza else []) + (['casa'] if casa else [])
    if len(orden) < 2: return ''
    b = ''.join(f'<span class="on" aria-current="page">{etq[k]}</span>' if k == activo else f'<a href="{ruta[k]}">{etq[k]}</a>' for k in orden)
    return f'<nav class="mods{" m4" if len(orden) >= 4 else ""}" style="--n:{len(orden)}" aria-label="Tu plan">{b}</nav>'

def cabecera(plan, nav, ver):
    """Marca + version + botones de modulos + saludo (comun a todas las paginas)."""
    hola = f'<p class="hola">Hola, {esc(plan["nombre"])}.</p>' if plan.get('nombre') else ''
    return f'<header class="head"><div class="top"><div class="logo">L<b>R</b> Coaching</div><div class="ver">Plan {esc(ver)}</div></div>{nav}{hola}</header>'

def resaltar(t):
    """Titulo en mayusculas por CSS; la ultima palabra va en el color de marca."""
    p = esc(t.strip()).rsplit(' ', 1)
    return f'{p[0]} <em>{p[1]}</em>' if len(p) == 2 else f'<em>{p[0]}</em>' if p[0] else ''

DIAS3 = {'lunes': 'Lun', 'martes': 'Mar', 'miercoles': 'Mié', 'jueves': 'Jue', 'viernes': 'Vie', 'sabado': 'Sáb', 'domingo': 'Dom'}
def sinacento(t): return ''.join(ch for ch in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(ch) != 'Mn')

def pagina(plan, casa=False, fuerza=False):
    out = []
    tabs = []
    dias = plan['casa_dias'] if casa else plan['fuerza_dias'] if fuerza else plan['dias']
    tiene_casa = bool(plan.get('casa_dias'))
    tiene_fuerza = bool(plan.get('fuerza_dias'))
    for n, d in enumerate(dias):
        corto, _, resto = d['nombre'].partition(':')
        corto = corto.strip(); titulo = resto.strip() or corto
        clave = sinacento(corto.split('·')[-1].strip())
        d3 = DIAS3.get(clave)
        tabs.append(f'<button type="button" class="tab" role="tab" data-t="d{n}" data-k="{esc(clave)}" aria-selected="false" aria-label="{esc(corto)}"><span class="d1">{esc(d3 or corto[:4])}</span><span class="d2">{n+1}</span></button>')
        eyebrow = corto + (' · Hipertrofia' if tiene_fuerza and not casa and not fuerza else '')
        ej = d['ejercicios']
        def _n(x):
            m = re.match(r'\d+', str(x).strip()); return int(m.group()) if m else 0
        series = sum(_n(x['series']) for x in ej)
        out.append(f'<div class="dia" id="d{n}" role="tabpanel"><div class="hero"><div class="eyebrow">{esc(eyebrow)}</div><h2 class="dt">{resaltar(titulo)}</h2><div class="stats"><div><b>{len(ej)}</b><span>Ejercicios</span></div><div><b>{series}</b><span>Series</span></div></div></div>')
        c = d.get('calentamiento')
        if c:
            li = ''.join(f'<li><span>{esc(EJ[x]["nombre"].replace(" (calentamiento)",""))}</span></li>' for x in c['ejercicios'])
            vu = re.search(r'(\d+)\s+vueltas?', c.get('nota', ''))
            chip = f'<span>{vu.group(1)} vueltas</span>' if vu else ''
            out.append(f'<section class="card warm"><div class="wh"><h3>Calentamiento</h3>{chip}</div><ol>{li}</ol><p>{esc(c["nota"])}</p></section>')
        for i, it in enumerate(ej, 1):
            out.append(tarjeta(i, it, casa))
        out.append('</div>')
    nav = f'<nav class="tabs" role="tablist" aria-label="Sesiones">{"".join(tabs)}</nav>' if len(tabs) > 1 else ''
    aviso = f'<p class="aviso">{esc(plan["_aviso"])}</p>' if plan.get('_aviso') else ''
    donde = 'casa' if casa else 'fuerza' if fuerza else 'gym'
    mods = navmods(donde, plan.get('nutricion'), tiene_casa, donde, tiene_fuerza)
    titulo = 'Tu entrenamiento en casa' if casa else 'Tu bloque de fuerza' if fuerza else 'Tu plan de hipertrofia' if tiene_fuerza else 'Tu plan de entrenamiento'
    intro = ''
    if casa and plan.get('casa_material'):
        intro = f'<div class="callout"><span class="lab">Cuándo usarlo</span><p>Usalo cuando no puedas ir al gimnasio: hacé la sesión de casa ese mismo día (la de tren superior si te perdés lunes o jueves; la de tren inferior si te perdés martes o viernes). No hace falta recuperar el día perdido.</p><p><b>Necesitás:</b> {esc(plan["casa_material"])}.</p></div>'
    if fuerza and plan.get('fuerza_intro'): intro = f'<div class="callout"><span class="lab">Cómo funciona este bloque</span><p>{esc(plan["fuerza_intro"])}</p></div>'
    final = f'<p class="sub">{esc(plan["nota_final"])}</p>' if plan.get('nota_final') else ''
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{titulo}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><style>{CSS}</style></head><body><main>
<h1 class="vh">{titulo} ({esc(plan["version"])})</h1>{cabecera(plan, mods, plan["version"])}{aviso}
{intro}{nav}{"".join(out)}
{final}<footer class="foot"><span class="l">Próxima revisión</span><b>{esc(plan["revision"])}</b><p class="pie">Si algo no se ve o no se entiende, avisame por el chat. Si sentís dolor (no cansancio), frená ese ejercicio y escribime.</p></footer>
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
