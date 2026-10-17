#!/usr/bin/env python3
"""Genera el panel (dashboard) de seguimiento de un cliente. Version 2 (17 de octubre de 2026).
Uso: python3 generar_panel.py panel.json TOKEN
- panel.json: primer nombre, version, estado, objetivo (opcional) y una lista de controles ('controles', o 'semanas' por compatibilidad).
- Salida: ../p/<TOKEN>/panel/index.html (mismo token que el plan de entrenamiento).
Privacidad: solo primer nombre; sin apellido, sin fotos, sin molestias ni comentarios (el repositorio es publico).
Las fotos y el detalle viven en la vista interna privada. Cada control se vuelve a generar con TODOS los anteriores: el historial no se pisa.
Campos de cada control: semana (etiqueta, ej. C1), peso [hasta 3], sesiones, planificadas, adherencia, rendimiento, sueno (opcional),
energia, hambre, satisfaccion (1 a 5, opcionales), cintura, otras (dict nombre -> cm, opcional)."""
import json, sys, html, math, pathlib
import generar as G
esc = html.escape
ADH = {'casi todas': 4, 'la mayoría': 3, 'la mitad': 2, 'pocas': 1}
ADH_PCT = {'casi todas': 0.9, 'la mayoría': 0.75, 'la mitad': 0.5, 'pocas': 0.25}   # aproximacion declarada, no medicion
RND = {'mejor': ('▲', 'Mejor'), 'igual': ('=', 'Igual'), 'peor': ('▼', 'Peor')}
SUBE_BIEN = {'ganar músculo': {'peso': 1, 'cintura': 0}, 'perder grasa': {'peso': -1, 'cintura': -1}, 'mantener': {'peso': 0, 'cintura': 0}}
ESTADOS = {'mantener': ('En rumbo', 'Lo que estás haciendo está funcionando. Seguimos igual.'),
           'investigar': ('Seguimos observando', 'Todavía no hay una tendencia clara. Por ahora no cambiamos nada.'),
           'ajustar': ('Vamos a ajustar', 'Con tus números de los últimos controles vamos a hacer un cambio. Te aviso por el chat.')}
OK = '#4cd18a'
NEU = '#d8d0c4'   # barras sin juicio (peso, cintura): ni logro ni alerta
EXTRA = f""":root{{--ok:{OK}}}
.estado{{border-left:4px solid var(--accent)}}.estado b{{font:400 1.6rem var(--display);text-transform:uppercase;letter-spacing:.04em}}
.kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0}}.kpis div{{background:var(--soft);border-radius:8px;padding:12px 6px;text-align:center}}
.kpis b{{display:block;font:700 1.25rem var(--mono)}}.kpis span{{font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}}
.kpis small{{display:block;font:500 .72rem var(--mono);margin-top:2px}}
.card h3{{margin:0 0 2px;font-size:1.05rem}}svg{{width:100%;height:auto;display:block}}.cap{{font-size:.8rem;color:var(--muted);margin:8px 0 0}}
.chips{{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}}.chip{{background:var(--soft);border-radius:8px;padding:8px 10px;text-align:center;min-width:64px}}
.chip b{{display:block;font:700 1.1rem var(--mono)}}.chip span{{font-size:.72rem;color:var(--muted)}}
.bien{{color:var(--ok)}}.mal{{color:var(--accent)}}.neu{{color:var(--fg)}}
.donuts{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}.donuts .card{{padding:12px 8px;text-align:center;margin:0}}.donuts h3{{font-size:.95rem}}
.donuts .cap{{font-size:.72rem}}
.tabla{{overflow-x:auto;margin-top:10px}}table{{border-collapse:collapse;width:100%;font:500 .85rem var(--mono)}}
th,td{{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}th:first-child,td:first-child{{text-align:left}}
th{{color:var(--muted);font-weight:500;font-size:.72rem;text-transform:uppercase;letter-spacing:.04em}}
.leyenda{{display:flex;gap:14px;flex-wrap:wrap;font-size:.78rem;color:var(--muted);margin-top:8px}}.leyenda i{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}}"""

def fmt(n, d=1):
    return f'{n:.{d}f}'.replace('.', ',') if n is not None else '–'

def signo(n, d=1):
    return ('+' if n > 0 else '') + fmt(n, d)

def prom(s):
    v = [x for x in s.get('peso', []) if x is not None]
    return round(sum(v)/len(v), 1) if len(v) >= 2 else None

def clase(delta, bueno, eps=0.05):
    """bueno: 1 si subir es bueno, -1 si bajar es bueno, 0 si es neutro."""
    if delta is None or abs(delta) < eps or bueno == 0: return 'neu'
    return 'bien' if delta*bueno > 0 else 'mal'

def donut(pct, centro, sub):
    r = 52; c = 2*math.pi*r; d = c*max(0, min(pct, 1))
    return (f'<svg viewBox="0 0 140 140" role="img" aria-label="{esc(centro)} {esc(sub)}" style="max-width:150px;margin:6px auto 0">'
            f'<circle cx="70" cy="70" r="{r}" fill="none" stroke="var(--accent)" stroke-width="16"/>'
            f'<circle cx="70" cy="70" r="{r}" fill="none" stroke="{OK}" stroke-width="16" stroke-dasharray="{d:.1f} {c:.1f}" transform="rotate(-90 70 70)"/>'
            f'<text x="70" y="76" text-anchor="middle" font-size="26" font-weight="700" fill="var(--fg)" font-family="JetBrains Mono,monospace">{esc(centro)}</text>'
            f'<text x="70" y="96" text-anchor="middle" font-size="11" fill="var(--muted)" font-family="JetBrains Mono,monospace">{esc(sub)}</text></svg>')

GOLD = '#ffc857'   # linea de tendencia: color propio, distinto de las barras y de verde/rojo
_n = [0]
GRAD = {NEU: ('#efe8dc', '#8a8379'), OK: ('#7ae8b0', '#2d9a66'), 'var(--accent)': ('#ff7a52', '#d93a12')}

def _barra(x, y, w, h, r, fill):
    r = min(r, w/2, h)
    return f'<path d="M{x:.1f},{y+h:.1f} L{x:.1f},{y+r:.1f} Q{x:.1f},{y:.1f} {x+r:.1f},{y:.1f} L{x+w-r:.1f},{y:.1f} Q{x+w:.1f},{y:.1f} {x+w:.1f},{y+r:.1f} L{x+w:.1f},{y+h:.1f} Z" fill="{fill}"/>'

def barras(vals, etiquetas, textos, lo=0, hi=None, color='var(--accent)', tendencia=False, ejey=True):
    _n[0] += 1; gid = f'g{_n[0]}'
    W, H, T, B = 600, 230, 34, 36; L = 46 if ejey else 8; R = 8
    n = len(vals); gap = 14; bw = (W-L-R-gap*(n+1))/n
    cs = [v for v in vals if v is not None]
    hi = hi if hi is not None else (max(cs) if cs else 1)
    full = H-T-B; c1, c2 = GRAD.get(color, (color, color))
    out = f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
    for k in range(4):                                   # grilla y etiquetas del eje
        yy = T + full*k/3
        out += f'<line x1="{L}" y1="{yy:.1f}" x2="{W-R}" y2="{yy:.1f}" stroke="var(--line)" stroke-width="1" opacity=".8"/>'
        if ejey:
            v = hi - (hi-lo)*k/3
            out += f'<text x="{L-8}" y="{yy+4:.1f}" text-anchor="end" font-size="13" fill="var(--muted)" font-family="JetBrains Mono,monospace">{fmt(v, 0 if (hi-lo) >= 6 else 1)}</text>'
    tops = []
    for i, v in enumerate(vals):
        x = L + gap + i*(bw+gap)
        if v is None:
            out += f'<text x="{x+bw/2:.1f}" y="{T+full/2}" text-anchor="middle" font-size="16" fill="var(--muted)">sin dato</text>'
        else:
            h = full*max(0.02, min((v-lo)/(hi-lo), 1)) if hi > lo else 0
            out += _barra(x, T+full-h, bw, h, 8, f'url(#{gid})')
            out += f'<text x="{x+bw/2:.1f}" y="{T+full-h-8:.1f}" text-anchor="middle" font-size="18" font-weight="700" fill="var(--fg)" font-family="JetBrains Mono,monospace">{esc(textos[i])}</text>'
            tops.append((x+bw/2, T+full-h))
        out += f'<text x="{x+bw/2:.1f}" y="{H-10}" text-anchor="middle" font-size="17" fill="var(--muted)" font-family="JetBrains Mono,monospace">{esc(etiquetas[i])}</text>'
    if tendencia and len(tops) >= 2:
        out += '<polyline points="' + ' '.join(f'{a:.1f},{b:.1f}' for a, b in tops) + f'" fill="none" stroke="{GOLD}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>'
        out += ''.join(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="6" fill="{GOLD}" stroke="var(--card)" stroke-width="3"/>' for a, b in tops)
    return f'<svg viewBox="0 0 {W} {H}" role="img">{out}</svg>'

def eje(vals, margen=1):
    cs = [v for v in vals if v is not None]
    if not cs: return (0, 1)
    lo, hi = math.floor(min(cs))-margen, math.ceil(max(cs))+margen
    while (hi-lo) % 3: hi += 1                        # 3 tramos iguales: etiquetas redondas
    return lo, hi

def pagina(p):
    S = p.get('controles') or p['semanas']
    obj = SUBE_BIEN.get(p.get('objetivo', ''), {'peso': 0, 'cintura': 0})
    V = S[-8:]; et = [s['semana'] for s in V]          # los graficos muestran los ultimos 8; las tablas, todos
    est = ESTADOS[p['estado']]
    pm = [prom(s) for s in S]; ult = [x for x in pm if x is not None]
    cin = [s.get('cintura') for s in S]; cinv = [x for x in cin if x is not None]

    # Desde que empezaste
    k = []
    if len(ult) >= 2:
        d = round(ult[-1]-ult[0], 1)
        k.append(f'<div><b>{fmt(ult[-1])}</b><span>Peso (kg)</span><small class="{clase(d, obj["peso"])}">{signo(d)} desde el inicio</small></div>')
    elif ult:
        k.append(f'<div><b>{fmt(ult[-1])}</b><span>Peso (kg)</span><small class="neu">punto de partida</small></div>')
    if len(cinv) >= 2:
        d = round(cinv[-1]-cinv[0], 1)
        k.append(f'<div><b>{fmt(cinv[-1])}</b><span>Cintura (cm)</span><small class="{clase(d, obj["cintura"])}">{signo(d)} desde el inicio</small></div>')
    elif cinv:
        k.append(f'<div><b>{fmt(cinv[-1])}</b><span>Cintura (cm)</span><small class="neu">punto de partida</small></div>')
    sr = sum(s['sesiones'] for s in S if s.get('sesiones') is not None); sp = sum(s.get('planificadas') or 0 for s in S if s.get('sesiones') is not None)
    k.append(f'<div><b>{sr}</b><span>Sesiones</span><small class="neu">de {sp} del plan</small></div>')
    kp = f'<div class="kpis">{"".join(k)}</div>'

    # Donuts de cumplimiento
    pct_s = (sr/sp) if sp else 0
    d1 = donut(pct_s, f'{round(pct_s*100)}%', f'{sr} de {sp}')
    ua = S[-1].get('adherencia')
    d2 = donut(ADH_PCT.get(ua, 0), f'≈{round(ADH_PCT.get(ua, 0)*100)}%', ua or 'sin dato')
    donuts = (f'<div class="donuts"><section class="card"><h3>Sesiones</h3>{d1}<p class="cap">Todo lo que va del plan. Verde: lo que hiciste. Rojo: lo que falta.</p></section>'
              f'<section class="card"><h3>Comidas del plan</h3>{d2}<p class="cap">Último control. Aproximado: sale de tu respuesta, no de una medición.</p></section></div>')

    # Peso
    lo, hi = eje([prom(s) for s in V])
    peso_g = barras([prom(s) for s in V], et, [fmt(prom(s)) if prom(s) is not None else '' for s in V], lo, hi, color=NEU, tendencia=True)
    difs = ''
    for a, b in zip(S, S[1:]):
        pa, pb = prom(a), prom(b)
        if pa is not None and pb is not None:
            d = round(pb-pa, 1)
            difs += f'<div class="chip"><b class="{clase(d, obj["peso"])}">{signo(d)}</b><span>{esc(b["semana"])} vs {esc(a["semana"])}</span></div>'
    nota_eje = '<p class="cap">Las barras no empiezan en cero, para que se vean los cambios chicos. La línea amarilla une los promedios.</p>'
    filas = ''.join(f'<tr><td>{esc(s["semana"])}</td>' + ''.join(f'<td>{fmt(x)}</td>' for x in (list(s.get('peso', [])) + [None]*3)[:3]) + f'<td><b>{fmt(prom(s))}</b></td></tr>' for s in S)
    tabla_peso = f'<div class="tabla"><table><tr><th>Control</th><th>Lun</th><th>Mié</th><th>Vie</th><th>Prom.</th></tr>{filas}</table></div>'
    peso = (f'<h2>Peso</h2><section class="card"><h3>Promedio por control (kg)</h3>{peso_g}'
            f'{"<div class=chips>"+difs+"</div>" if difs else ""}{nota_eje}</section>'
            f'<section class="card"><h3>Todos los pesajes</h3>{tabla_peso}<p class="cap">Miramos la tendencia entre controles, no un día suelto: el peso sube y baja por agua y comidas.</p></section>')

    # Medidas (cintura + otras), con cambio total
    nombres = ['Cintura'] + sorted({n.capitalize() for s in S for n in (s.get('otras') or {})})
    def val(s, n):
        return s.get('cintura') if n == 'Cintura' else next((v for k2, v in (s.get('otras') or {}).items() if k2.capitalize() == n), None)
    cab = ''.join(f'<th>{esc(s["semana"])}</th>' for s in S[-6:])
    fl = ''
    for n in nombres:
        vs = [val(s, n) for s in S]; vv = [x for x in vs if x is not None]
        if not vv: continue
        cambio = '–' if len(vv) < 2 else f'<span class="{clase(round(vv[-1]-vv[0],1), obj["cintura"] if n=="Cintura" else 0)}">{signo(round(vv[-1]-vv[0],1))}</span>'
        fl += f'<tr><td>{esc(n)}</td>' + ''.join(f'<td>{fmt(x)}</td>' for x in vs[-6:]) + f'<td>{cambio}</td></tr>'
    med = ''
    if fl:
        lo2, hi2 = eje(cin[-8:] if len(cin) else [None], 2) if cinv else (0, 1)
        gc = barras([s.get('cintura') for s in V], et, [fmt(s.get('cintura')) if s.get('cintura') is not None else '' for s in V], lo2, hi2, color=NEU, tendencia=True) if cinv else ''
        med = (f'<h2>Medidas</h2><section class="card"><h3>Cintura (cm)</h3>{gc}<p class="cap">Cada 4 semanas. El eje no empieza en cero.</p></section>'
               f'<section class="card"><h3>Todas tus medidas (cm)</h3><div class="tabla"><table><tr><th>Medida</th>{cab}<th>Cambio</th></tr>{fl}</table></div></section>')

    # Entrenamiento
    ses_g = barras([s.get('sesiones') for s in V], et, [f"{s.get('sesiones')}/{s.get('planificadas')}" if s.get('sesiones') is not None else '' for s in V],
                   0, max([s.get('planificadas') or 0 for s in V] + [1]), color=OK, ejey=False)
    rnd = ''.join(f'<div class="chip"><b class="{"bien" if s["rendimiento"]=="mejor" else "mal" if s["rendimiento"]=="peor" else "neu"}">{RND[s["rendimiento"]][0]}</b><span>{esc(s["semana"])} · {RND[s["rendimiento"]][1]}</span></div>' for s in S if s.get('rendimiento') in RND)
    entren = (f'<h2>Entrenamiento</h2><section class="card"><h3>Sesiones por control</h3>{ses_g}<p class="cap">Hechas sobre planificadas en cada período de cuatro semanas.</p></section>'
              f'<section class="card"><h3>Rendimiento frente al control anterior</h3><div class="chips">{rnd}</div></section>')

    # Alimentacion (historial)
    adh_g = barras([ADH.get(s.get('adherencia')) for s in V], et, [s.get('adherencia', '') for s in V], 0, 4, color=OK, ejey=False)
    alim = f'<h2>Alimentación</h2><section class="card"><h3>Comidas del plan que cumpliste</h3>{adh_g}</section>'

    # Como te sentiste
    sent = ''
    for clave_, nom in (('energia', 'Energía'), ('hambre', 'Hambre'), ('satisfaccion', 'Satisfacción')):
        if any(s.get(clave_) is not None for s in S):
            sent += f'<tr><td>{nom}</td>' + ''.join(f'<td>{s.get(clave_) if s.get(clave_) is not None else "–"}</td>' for s in S[-6:]) + '</tr>'
    sentido = f'<h2>Cómo te sentiste</h2><section class="card"><h3>De 1 a 5</h3><div class="tabla"><table><tr><th></th>{cab}</tr>{sent}</table></div></section>' if sent else ''

    # Sueno (solo si lo informo)
    sueno = ''
    if any(s.get('sueno') is not None for s in S):
        sueno = (f'<h2>Sueño</h2><section class="card"><h3>Horas por noche, en promedio</h3>'
                 f'{barras([s.get("sueno") for s in V], et, [fmt(s.get("sueno")) if s.get("sueno") is not None else "" for s in V], 0, 9, color=OK)}'
                 f'<p class="cap">Lo informás vos: es una estimación, no una medición.</p></section>')

    aviso = f'<p class="aviso">{esc(p["_aviso"])}</p>' if p.get('_aviso') else ''
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Tu panel de seguimiento</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet"><style>{G.CSS}{EXTRA}</style></head><body><main>
<h1>Hola, {esc(p["nombre"])}. Tu panel</h1><p class="sub">Plan {esc(p["version"])} · Actualizado el {esc(p["actualizado"])}.</p>{aviso}
<section class="card estado"><span class="sub" style="margin:0">Este control</span><br><b>{est[0]}</b><p style="margin:6px 0 0">{est[1]}</p></section>
<h2>Desde que empezaste</h2>{kp}{donuts}
{peso}{med}{entren}{alim}{sentido}{sueno}
<p class="leyenda"><span><i style="background:{OK}"></i>Verde: va bien o es lo logrado</span><span><i style="background:var(--accent)"></i>Rojo: lo que falta o conviene mirar</span></p>
<p class="pie">Si algo no se ve o no se entiende, avisame por el chat. Si sentís dolor (no cansancio), frená ese ejercicio y escribime sin esperar al próximo check-in.</p>
</main></body></html>'''

if __name__ == '__main__':
    p = json.load(open(sys.argv[1])); token = sys.argv[2]
    assert p['estado'] in ESTADOS, 'estado invalido'
    for s in (p.get('controles') or p['semanas']):
        assert s.get('adherencia') is None or s['adherencia'] in ADH, ('adherencia invalida', s)
        assert s.get('rendimiento') is None or s['rendimiento'] in RND, ('rendimiento invalido', s)
    dest = G.AQUI.parent/'p'/token/'panel'; dest.mkdir(parents=True, exist_ok=True)
    (dest/'index.html').write_text(pagina(p), encoding='utf-8')
    print(f'p/{token}/panel/index.html')
