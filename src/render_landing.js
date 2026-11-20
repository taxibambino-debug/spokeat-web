// Render a Design .dc.html artboard to static HTML: evaluates renderVals() and expands sc-for / {{ }}.
// Usage: node render_landing.js <in.dc.html>  -> prints JSON {head, body}
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');

const scriptM = src.match(/<script type="text\/x-dc"[^>]*>([\s\S]*?)<\/script>/);
class DCLogic { constructor() { this.props = {}; } }
const Component = new Function('DCLogic', scriptM[1] + '\nreturn Component;')(DCLogic);
const vals = new Component().renderVals();

const head = (src.match(/<helmet>([\s\S]*?)<\/helmet>/) || ['', ''])[1];
let body = src.slice(src.indexOf('</helmet>') + 9, src.indexOf('</x-dc>'));

function get(path, scope) {
  return path.trim().split('.').reduce((o, k) => (o == null ? undefined : o[k]), scope);
}
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function render(tpl, scope) {
  let out = '', i = 0;
  while (true) {
    const start = tpl.indexOf('<sc-for', i);
    if (start < 0) { out += interp(tpl.slice(i), scope); break; }
    out += interp(tpl.slice(i, start), scope);
    const openEnd = tpl.indexOf('>', start);
    const open = tpl.slice(start, openEnd + 1);
    // find matching close, accounting for nesting
    let depth = 1, j = openEnd + 1;
    while (depth > 0) {
      const nOpen = tpl.indexOf('<sc-for', j), nClose = tpl.indexOf('</sc-for>', j);
      if (nOpen >= 0 && nOpen < nClose) { depth++; j = nOpen + 7; } else { depth--; j = nClose + 9; }
    }
    const inner = tpl.slice(openEnd + 1, j - 9);
    const list = get(open.match(/list="\{\{(.*?)\}\}"/)[1], scope) || [];
    const as = open.match(/as="(\w+)"/)[1];
    for (const item of list) out += render(inner, Object.assign({}, scope, { [as]: item }));
    i = j;
  }
  return out;
}
function interp(s, scope) {
  return s.replace(/\{\{(.*?)\}\}/g, (_, p) => { const v = get(p, scope); return v == null ? '' : esc(v); });
}
process.stdout.write(JSON.stringify({ head, body: render(body, vals) }));
