#!/usr/bin/env python3
"""Genera la pagina de plan de un cliente.
Uso: python3 generar.py plan.json [token]
- datos/ejercicios.json: copia de la pestaña Ejercicios del Sheet (sin datos de personas).
- plan.json: dias y ejercicios del cliente (solo ID de ejercicio + series/reps/RIR/descanso/nota).
- Salida: ../p/<token>/index.html. El token (largo y aleatorio) es el link privado del cliente.
Privacidad: la pagina lleva como mucho el primer nombre (campo opcional 'nombre'), nunca datos de salud, y pide que no la indexen los buscadores."""
import json, re, sys, html, secrets, pathlib

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
.sinvideo{font-size:.9rem;color:var(--muted)}.pie{font-size:.85rem;color:var(--muted);margin-top:24px}"""

JS = """(function(){var cur=null;document.querySelectorAll('details.ex-d').forEach(function(d){d.addEventListener('toggle',function(){var box=d.querySelector('.vslot');if(!box)return;
if(d.open){document.querySelectorAll('.vslot').forEach(function(b){if(b!==box)b.innerHTML=''});
if(!box.firstChild){var v=box.dataset.v,w=document.createElement('div');w.className='video';var f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+v;f.title=box.dataset.t;f.allow='encrypted-media; picture-in-picture';f.allowFullscreen=true;f.referrerPolicy='strict-origin-when-cross-origin';w.appendChild(f);box.appendChild(w);
var r=document.createElement('button');r.type='button';r.className='vbtn';r.textContent='↻ Recargar video';r.onclick=function(){f.src=f.src};box.appendChild(r)}}else{box.innerHTML=''}})})})();"""

def tarjeta(i, it):
    e = EJ[it['id']]
    vid = yt(e['video'])
    video = (f'<div class="vslot" data-v="{vid}" data-t="{esc(e["nombre"])}"></div>' if vid
             else '<p class="sinvideo">Este ejercicio se explica con el texto de arriba.</p>' if 'sin video' in e['video']
             else '<p class="sinvideo">Video en preparación. Mientras tanto, seguí la explicación de arriba.</p>')
    cuidado = f'<p class="cuidado"><b>Ojo:</b> {esc(e["cuidado"])}</p>' if e['cuidado'] else ''
    nota = f'<p class="nota">{esc(it["nota"])}</p>' if it.get('nota') else ''
    return f'''<article class="card ex"><h3>{i}. {esc(e["nombre"])}</h3>
<div class="meta"><div><b>{esc(it["series"])} × {esc(it["reps"])}</b><span>Series</span></div><div><b>{esc(it["rir"])}</b><span>Esfuerzo</span></div><div><b>{esc(it["descanso"])}</b><span>Descanso</span></div></div>
{nota}<p class="why">{esc(e["por_que"])}</p>
<details class="ex-d"><summary>Cómo se hace y video</summary><p class="how">{esc(e["como"])}</p>{cuidado}{video}</details></article>'''

def pagina(plan):
    out = []
    for d in plan['dias']:
        out.append(f'<h2>{esc(d["nombre"])}</h2>')
        c = d.get('calentamiento')
        if c:
            li = ''.join(f'<li>{esc(EJ[x]["nombre"].replace(" (calentamiento)",""))}</li>' for x in c['ejercicios'])
            out.append(f'<section class="card warm"><b>Calentamiento del día</b><p class="sub" style="margin:4px 0 0">{esc(c["nota"])}</p><ol>{li}</ol></section>')
        for i, it in enumerate(d['ejercicios'], 1):
            out.append(tarjeta(i, it))
    saludo = f'Hola, {esc(plan["nombre"])}. ' if plan.get('nombre') else ''
    aviso = f'<p class="aviso">{esc(plan["_aviso"])}</p>' if plan.get('_aviso') else ''
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Tu plan de entrenamiento</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><style>{CSS}</style></head><body><main>
<h1>{saludo}Tu plan de entrenamiento ({esc(plan["version"])})</h1><p class="sub">Primera revisión: {esc(plan["revision"])}.</p>{aviso}
{"".join(out)}
<p class="pie">Si algo no se ve o no se entiende, avisame por el chat. Si sentís dolor (no cansancio), frená ese ejercicio y escribime.</p>
</main><script>{JS}</script></body></html>'''

if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    token = sys.argv[2] if len(sys.argv) > 2 else secrets.token_urlsafe(18)
    for d in plan['dias']:
        for it in d['ejercicios']: assert it['id'] in EJ, it['id']
    dest = AQUI.parent/'p'/token
    dest.mkdir(parents=True, exist_ok=True)
    (dest/'index.html').write_text(pagina(plan), encoding='utf-8')
    print(f'p/{token}/index.html')
