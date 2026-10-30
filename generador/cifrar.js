#!/usr/bin/env node
// Cifra con un codigo de acceso todas las paginas index.html de una carpeta (p/<token>/...).
// Uso: ACCESO=<codigo> node cifrar.js <carpeta>
// El codigo se lee de la variable de entorno del proceso (nunca se imprime ni se escribe en el repositorio).
// Cada pagina queda como una portada con un campo de codigo; el contenido real va cifrado (AES-256-GCM, clave PBKDF2-SHA256).
// El navegador descifra con WebCrypto y, si el codigo es correcto, muestra la pagina original en la misma direccion.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const ITER = 300000, MARCA = '<!--lr-protegido-->';
const NONCE = /^[a-z0-9]{6,24}$/.test(process.env.NONCE || '') ? process.env.NONCE : ''; // marca no secreta para que la hoja compruebe la publicacion

function cifrar(html, acceso) {
  const salt = crypto.randomBytes(16), iv = crypto.randomBytes(12);
  const clave = crypto.pbkdf2Sync(acceso, salt, ITER, 32, 'sha256');
  const c = crypto.createCipheriv('aes-256-gcm', clave, iv);
  const ct = Buffer.concat([c.update(html, 'utf8'), c.final(), c.getAuthTag()]);
  return Buffer.concat([salt, iv, ct]).toString('base64');
}

function portada(datos, token) {
  return `<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>LR Coaching</title>${MARCA}${NONCE ? '<!--lr-nonce:' + NONCE + '-->' : ''}
<style>
:root{--bg:#f6f7f9;--tx:#16181d;--mu:#5b6270;--ca:#fff;--ac:#1a56db;--er:#b42318;--bo:#d6dae1}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--tx:#eef0f4;--mu:#9aa2b1;--ca:#181b22;--ac:#6ea0ff;--er:#ff8a80;--bo:#2b303b}}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--tx);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:16px}
main{width:100%;max-width:380px;background:var(--ca);border:1px solid var(--bo);border-radius:16px;padding:28px 22px;text-align:center}
h1{font-size:1.25rem;margin:0 0 6px}p{margin:0 0 18px;color:var(--mu)}
input{width:100%;font:inherit;font-size:1.4rem;letter-spacing:.35em;text-align:center;padding:12px;border-radius:12px;border:1px solid var(--bo);background:var(--bg);color:var(--tx)}
input:focus{outline:2px solid var(--ac);outline-offset:1px}
button{width:100%;margin-top:12px;font:inherit;font-weight:600;padding:13px;border:0;border-radius:12px;background:var(--ac);color:#fff;min-height:48px}
button:disabled{opacity:.6}
#e{min-height:1.4em;margin:10px 0 0;color:var(--er);font-size:.95rem}
small{display:block;margin-top:14px;color:var(--mu)}
</style></head><body>
<main id="m"><h1>Tu plan de LR Coaching</h1><p>Escribí el código que te mandó Lorenzo.</p>
<form id="f" autocomplete="off"><input id="c" type="text" inputmode="numeric" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="Código de acceso" maxlength="12" autofocus>
<button id="b" type="submit">Entrar</button><div id="e" role="alert"></div></form>
<small>El código queda guardado en este celular para no pedirlo de nuevo.</small></main>
<noscript><p style="text-align:center">Necesitás activar JavaScript para ver tu plan.</p></noscript>
<script>
(function(){
var D=${JSON.stringify(datos)},K='lrk-'+${JSON.stringify(token)},I=${ITER};
function b64(s){var r=atob(s),a=new Uint8Array(r.length);for(var i=0;i<r.length;i++)a[i]=r.charCodeAt(i);return a}
function leer(){try{return localStorage.getItem(K)||''}catch(e){return ''}}
function guardar(c){try{localStorage.setItem(K,c)}catch(e){}}
function borrar(){try{localStorage.removeItem(K)}catch(e){}}
async function abrir(codigo){
  var raw=b64(D),salt=raw.slice(0,16),iv=raw.slice(16,28),ct=raw.slice(28);
  var base=await crypto.subtle.importKey('raw',new TextEncoder().encode(codigo),'PBKDF2',false,['deriveKey']);
  var key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:salt,iterations:I,hash:'SHA-256'},base,{name:'AES-GCM',length:256},false,['decrypt']);
  var buf=await crypto.subtle.decrypt({name:'AES-GCM',iv:iv},key,ct);
  return new TextDecoder().decode(buf);
}
function mostrar(html){document.open();document.write(html);document.close()}
var f=document.getElementById('f'),c=document.getElementById('c'),b=document.getElementById('b'),e=document.getElementById('e');
async function intentar(codigo,auto){
  if(!window.crypto||!crypto.subtle){e.textContent='Tu navegador no puede abrir esta página. Probá con Chrome o Safari actualizado.';return}
  b.disabled=true;e.textContent=auto?'':'Abriendo…';
  try{var html=await abrir(codigo);guardar(codigo);mostrar(html)}
  catch(x){b.disabled=false;if(auto)borrar();e.textContent=auto?'':'Código incorrecto. Probá de nuevo.';if(!auto)c.select()}
}
f.addEventListener('submit',function(ev){ev.preventDefault();var v=c.value.trim();if(v)intentar(v,false)});
var g=leer();if(g)intentar(g,true);
})();
</script></body></html>`;
}

function recorrer(dir, salida) {
  for (const n of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, n.name);
    if (n.isDirectory()) recorrer(p, salida);
    else if (n.name === 'index.html') salida.push(p);
  }
  return salida;
}

const carpeta = process.argv[2], acceso = process.env.ACCESO || '';
if (!carpeta || !fs.existsSync(carpeta)) { console.error('Falta la carpeta.'); process.exit(2); }
if (!/^[A-Za-z0-9]{4,12}$/.test(acceso)) { console.error('El codigo de acceso debe tener entre 4 y 12 letras o numeros.'); process.exit(2); }
const token = process.env.TOKEN || path.basename(path.resolve(carpeta));
let n = 0;
for (const f of recorrer(carpeta, [])) {
  const html = fs.readFileSync(f, 'utf8');
  if (html.includes(MARCA)) continue; // ya esta protegida: se regenera desde el origen, no se vuelve a cifrar
  fs.writeFileSync(f, portada(cifrar(html, acceso), token));
  n++;
}
console.log('Paginas protegidas: ' + n);
