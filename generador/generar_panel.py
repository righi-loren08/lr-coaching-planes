#!/usr/bin/env python3
"""Genera el panel (dashboard) de seguimiento de un cliente.
Uso: python3 generar_panel.py panel.json TOKEN
- panel.json: primer nombre, version, estado de la ultima semana y una lista de semanas con los datos del check-in.
- Salida: ../p/<TOKEN>/panel/index.html (mismo token que el plan de entrenamiento).
Privacidad: solo primer nombre; sin apellido, sin fotos, sin molestias ni comentarios. Peso y medidas son numeros. Las fotos y el detalle
viven en la vista interna privada, nunca aca (el repositorio es publico).
Cada semana se vuelve a generar con TODAS las semanas anteriores: el historial no se pisa."""
import json, sys, html, pathlib
import generar as G
esc = html.escape
ADH = {'casi todas': 4, 'la mayoría': 3, 'la mitad': 2, 'pocas': 1}
RND = {'mejor': ('▲', 'Mejor'), 'igual': ('=', 'Igual'), 'peor': ('▼', 'Peor')}
ESTADOS = {'mantener': ('En rumbo', 'Lo que estás haciendo está funcionando. Seguimos igual.'),
           'investigar': ('Seguimos observando', 'Todavía no hay una tendencia clara. Por ahora no cambiamos nada.'),
           'ajustar': ('Vamos a ajustar', 'Con tus números de las últimas semanas vamos a hacer un cambio. Te aviso por el chat.')}
EXTRA = """.estado{border-left:4px solid var(--accent)}.estado b{font:400 1.5rem var(--display);text-transform:uppercase;letter-spacing:.04em}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}.kpis div{background:var(--soft);border-radius:8px;padding:10px;text-align:center}
.kpis b{display:block;font:700 1.1rem var(--mono)}.kpis span{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.card h3{margin:0 0 2px;font-size:1.05rem}svg{width:100%;height:auto;display:block}.cap{font-size:.8rem;color:var(--muted);margin:6px 0 0}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.chip{background:var(--soft);border-radius:8px;padding:8px 10px;text-align:center;min-width:64px}
.chip b{display:block;font:700 1.1rem var(--mono)}.chip span{font-size:.72rem;color:var(--muted)}.up b{color:var(--accent)}"""

def semana_etiqueta(s): return s['semana']

def peso_prom(s):
    v = [x for x in s.get('peso', []) if x is not None]
    return round(sum(v)/len(v), 1) if len(v) >= 2 else None

def linea(pts, etiquetas, unidad):
    W, H, L, R, T, B = 600, 230, 36, 30, 34, 36
    ys = [p for p in pts if p is not None]
    if len(ys) < 2: return '<p class="cap">Todavía hay pocos datos para dibujar la tendencia. Con 2 semanas ya aparece.</p>'
    lo, hi = min(ys), max(ys); pad = max((hi-lo)*0.3, 0.5); lo, hi = lo-pad, hi+pad
    n = len(pts); X = lambda i: L + (W-L-R)*(i/(n-1 if n > 1 else 1)); Y = lambda v: T + (H-T-B)*(1-(v-lo)/(hi-lo))
    seg = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(pts) if v is not None)
    dots = ''.join(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="5" fill="var(--accent)"/><text x="{X(i):.1f}" y="{Y(v)-12:.1f}" text-anchor="middle" font-size="19" fill="var(--fg)" font-family="JetBrains Mono,monospace">{v}</text>' for i, v in enumerate(pts) if v is not None)
    lab = ''.join(f'<text x="{X(i):.1f}" y="{H-10}" text-anchor="middle" font-size="17" fill="var(--muted)" font-family="JetBrains Mono,monospace">{esc(e)}</text>' for i, e in enumerate(etiquetas))
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Peso promedio por semana en {unidad}"><line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" stroke="var(--line)"/><polyline points="{seg}" fill="none" stroke="var(--accent)" stroke-width="3" stroke-linejoin="round"/>{dots}{lab}</svg>'

def barras(vals, maxs, etiquetas, textos):
    W, H, T, B = 600, 200, 30, 36; n = len(vals); gap = 12; bw = (W-gap*(n+1))/n
    out = ''
    for i, (v, m) in enumerate(zip(vals, maxs)):
        x = gap + i*(bw+gap); full = H-T-B
        if v is None:
            out += f'<text x="{x+bw/2:.1f}" y="{T+full/2}" text-anchor="middle" font-size="17" fill="var(--muted)">sin dato</text>'
        else:
            h = full*min(v/m, 1) if m else 0
            out += f'<rect x="{x:.1f}" y="{T}" width="{bw:.1f}" height="{full}" rx="6" fill="var(--soft)"/><rect x="{x:.1f}" y="{T+full-h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="6" fill="var(--accent)"/><text x="{x+bw/2:.1f}" y="{T-6}" text-anchor="middle" font-size="19" fill="var(--fg)" font-family="JetBrains Mono,monospace">{esc(textos[i])}</text>'
        out += f'<text x="{x+bw/2:.1f}" y="{H-10}" text-anchor="middle" font-size="17" fill="var(--muted)" font-family="JetBrains Mono,monospace">{esc(etiquetas[i])}</text>'
    return f'<svg viewBox="0 0 {W} {H}" role="img">{out}</svg>'

def pagina(p):
    S = p['semanas']; et = [s['semana'] for s in S]
    est = ESTADOS[p['estado']]
    pm = [peso_prom(s) for s in S]
    ult = [x for x in pm if x is not None]
    kp = ''
    if len(ult) >= 2:
        d = round(ult[-1]-ult[0], 1)
        kp = f'<div class="kpis"><div><b>{ult[0]}</b><span>Primera semana</span></div><div><b>{ult[-1]}</b><span>Última semana</span></div><div><b>{"+" if d>0 else ""}{d}</b><span>Cambio (kg)</span></div></div>'
    ses = barras([s.get('sesiones') for s in S], [s.get('planificadas') or 0 for s in S], et, [f"{s.get('sesiones')}/{s.get('planificadas')}" if s.get('sesiones') is not None else '' for s in S])
    adh = barras([ADH.get(s.get('adherencia')) for s in S], [4]*len(S), et, [s.get('adherencia', '') for s in S])
    rnd = ''.join(f'<div class="chip {"up" if s.get("rendimiento")=="mejor" else ""}"><b>{RND[s["rendimiento"]][0]}</b><span>{esc(s["semana"])} · {RND[s["rendimiento"]][1]}</span></div>' for s in S if s.get('rendimiento') in RND)
    con_sueno = [s for s in S if s.get('sueno') is not None]
    sueno = ''
    if con_sueno:
        sueno = f'<h2>Sueño</h2><section class="card"><h3>Horas por noche, en promedio</h3>{barras([s.get("sueno") for s in S], [9]*len(S), et, [str(s.get("sueno")) if s.get("sueno") is not None else "" for s in S])}<p class="cap">Lo informás vos: es una estimación, no una medición.</p></section>'
    med = ''
    if p.get('medidas'):
        filas = ''.join(f'<div class="chip"><b>{esc(str(m["cintura"]))} cm</b><span>{esc(m["semana"])} · cintura</span></div>' for m in p['medidas'] if m.get('cintura') is not None)
        if filas: med = f'<h2>Medidas</h2><section class="card"><h3>Cada 4 semanas</h3><div class="chips">{filas}</div></section>'
    aviso = f'<p class="aviso">{esc(p["_aviso"])}</p>' if p.get('_aviso') else ''
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Tu panel de seguimiento</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><style>{G.CSS}{EXTRA}</style></head><body><main>
<h1>Hola, {esc(p["nombre"])}. Tu panel</h1><p class="sub">Plan {esc(p["version"])} · Actualizado el {esc(p["actualizado"])}.</p>{aviso}
<section class="card estado"><span class="sub" style="margin:0">Esta semana</span><br><b>{est[0]}</b><p style="margin:6px 0 0">{est[1]}</p></section>
<h2>Peso</h2><section class="card"><h3>Promedio semanal (kg)</h3>{kp}{linea(pm, et, "kg")}<p class="cap">Miramos la tendencia de varias semanas, no un día suelto: el peso sube y baja por agua y comidas.</p></section>
<h2>Entrenamiento</h2><section class="card"><h3>Sesiones realizadas</h3>{ses}</section>
<section class="card"><h3>Rendimiento frente a la semana anterior</h3><div class="chips">{rnd}</div></section>
<h2>Alimentación</h2><section class="card"><h3>Comidas del plan que cumpliste</h3>{adh}</section>
{sueno}{med}
<p class="pie">Si algo no se ve o no se entiende, avisame por el chat. Si sentís dolor (no cansancio), frená ese ejercicio y escribime sin esperar al próximo check-in.</p>
</main></body></html>'''

if __name__ == '__main__':
    p = json.load(open(sys.argv[1])); token = sys.argv[2]
    assert p['estado'] in ESTADOS, 'estado invalido'
    for s in p['semanas']:
        assert s.get('adherencia') is None or s['adherencia'] in ADH, ('adherencia invalida', s)
        assert s.get('rendimiento') is None or s['rendimiento'] in RND, ('rendimiento invalido', s)
    dest = G.AQUI.parent/'p'/token/'panel'; dest.mkdir(parents=True, exist_ok=True)
    (dest/'index.html').write_text(pagina(p), encoding='utf-8')
    print(f'p/{token}/panel/index.html')
