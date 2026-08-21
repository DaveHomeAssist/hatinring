/* Headless check for _hat-in-ring-src/review.html (the local review admin page).
 *
 * The page is the only thing standing between a queued item and a hand-edited
 * decisions file, so its VALIDATION is what matters: it must refuse a queue it
 * does not understand, and it must be structurally incapable of exporting a
 * malformed review_decisions.json.
 *
 * Runs the page's real inline script against a minimal DOM shim — no browser,
 * no jsdom dependency, same spirit as tests/dashboard_smoke.js.
 */
const fs = require('fs');

const file = process.argv[2];
const html = fs.readFileSync(file, 'utf8');

function fail(msg, code = 2) { console.log('FAIL: ' + msg); process.exit(code); }

// ---- minimal DOM shim ----------------------------------------------------
function makeNode(tag) {
  return {
    tagName: (tag || '').toUpperCase(),
    children: [], attrs: {}, _text: '', hidden: false, disabled: false,
    files: null,
    get textContent() { return this._text; },
    set textContent(v) { this._text = String(v == null ? '' : v); this.children = []; },
    setAttribute(k, v) { this.attrs[k] = String(v); },
    getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
    appendChild(c) { this.children.push(c); return c; },
    remove() {},
    addEventListener(type, fn) { (this._h || (this._h = {}))[type] = fn; },
    click() { if (this._h && this._h.click) this._h.click(); },
  };
}
const byId = {};
['file', 'reload', 'export', 'clear', 'errors', 'list', 'count', 'status']
  .forEach((id) => { byId[id] = makeNode('div'); });

global.document = {
  getElementById: (id) => byId[id] || null,
  createElement: (tag) => makeNode(tag),
  body: makeNode('body'),
};
global.location = { protocol: 'file:' };        // suppress the auto-fetch
global.fetch = () => Promise.reject(new Error('no network in tests'));
global.FileReader = function () {};
global.Blob = function () {};
global.URL = { createObjectURL: () => 'blob:x', revokeObjectURL() {} };

// ---- load the page's script ----------------------------------------------
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) fail('no inline script found in review.html', 65);
try {
  new Function(m[1])();
} catch (e) {
  fail('review.html script threw on load -> ' + (e && e.message), 1);
}
const R = global.__reviewInternals;
if (!R) fail('review.html did not expose its test seam', 65);

const ok = (rid, over) => Object.assign({
  name: 'Alpha Candidate', headline: 'Alpha weighs a 2028 run',
  url: 'https://example.invalid/a', source: 'Politico', date: '2026-06-10',
  keys: ['consideringQuote'], rid: rid, kind: 'discovery',
}, over || {});

try {
  // ---- queue validation --------------------------------------------------
  if (R.validateQueue([ok('aaaaaaaaaaaa')]).length !== 0) fail('a valid queue item was rejected');
  if (R.validateQueue({}).length === 0) fail('a non-array queue was accepted');

  const missing = R.validateQueue([{ name: 'x', rid: 'aaaaaaaaaaaa' }]);
  if (!missing.some((e) => /missing required field 'headline'/.test(e))) {
    fail('missing required fields were not reported: ' + missing.join(' | '));
  }

  // The headline requirement of this phase: unknown fields hard-fail rather
  // than being silently ignored, because a mis-rendered queue means a wrong
  // human decision.
  const drift = R.validateQueue([ok('aaaaaaaaaaaa', { surprise: 'new field' })]);
  if (!drift.some((e) => /unknown field 'surprise'/.test(e))) {
    fail('schema drift was not reported: ' + drift.join(' | '));
  }
  if (!drift.some((e) => /out of date/.test(e))) fail('drift error does not explain itself');

  if (!R.validateQueue([ok('aaaaaaaaaaaa', { kind: 'weird' })]).some((e) => /unknown kind/.test(e))) {
    fail('an unknown kind was accepted');
  }
  if (!R.validateQueue([ok('NOTAHEX')]).some((e) => /malformed rid/.test(e))) {
    fail('a malformed rid was accepted');
  }
  const norid = ok('x'); delete norid.rid;
  if (!R.validateQueue([norid]).some((e) => /no rid/.test(e))) fail('an item with no rid was accepted');
  // optional extras are allowed
  if (R.validateQueue([ok('aaaaaaaaaaaa', { note: 'confirm first', fec_id: 'P00000001' })]).length !== 0) {
    fail('documented optional fields (note/fec_id) were rejected');
  }

  // ---- a bad queue loads NOTHING and says so -----------------------------
  R.load([ok('aaaaaaaaaaaa', { surprise: 1 })], 'test');
  let st = R.state();
  if (st.items.length !== 0) fail('an invalid queue was partially loaded');
  if (!st.errorsShown) fail('an invalid queue did not surface a visible error');

  // ---- a good queue loads and drives the export gate ---------------------
  R.load([ok('aaaaaaaaaaaa'), ok('bbbbbbbbbbbb', { name: 'Bravo' })], 'test');
  st = R.state();
  if (st.items.length !== 2) fail('a valid queue did not load');
  if (st.errorsShown) fail('a valid queue still showed an error');
  if (!st.exportDisabled) fail('export was enabled with zero decisions');

  R.decide('aaaaaaaaaaaa', 'confirm');
  if (R.state().exportDisabled) fail('export still disabled after a decision');

  R.decide('bbbbbbbbbbbb', 'dismiss');
  const out = R.buildDecisions();
  if (out.length !== 2) fail('expected 2 decisions, got ' + out.length);
  // Exactly the shape reconcile_review() consumes.
  for (const d of out) {
    if (Object.keys(d).sort().join(',') !== 'action,rid') {
      fail('decision has wrong shape: ' + JSON.stringify(d));
    }
    if (!/^(confirm|dismiss)$/.test(d.action)) fail('bad action: ' + d.action);
    if (!/^[0-9a-f]{12}$/.test(d.rid)) fail('bad rid: ' + d.rid);
  }
  // deterministic order
  if (out[0].rid > out[1].rid) fail('decisions are not emitted in a stable order');

  // ---- the export gate cannot be bypassed --------------------------------
  if (R.validateDecisions([{ rid: 'aaaaaaaaaaaa' }]).length === 0) fail('a decision with no action was accepted');
  if (R.validateDecisions([{ rid: 'zz', action: 'confirm' }]).length === 0) fail('a malformed rid was accepted');
  if (R.validateDecisions([{ rid: 'aaaaaaaaaaaa', action: 'maybe' }]).length === 0) fail('an invalid action was accepted');
  if (R.validateDecisions([{ rid: 'aaaaaaaaaaaa', action: 'confirm', extra: 1 }]).length === 0) {
    fail('a decision with an extra field was accepted');
  }
  if (R.validateDecisions([
    { rid: 'aaaaaaaaaaaa', action: 'confirm' },
    { rid: 'aaaaaaaaaaaa', action: 'dismiss' },
  ]).length === 0) fail('duplicate rids were accepted');
  if (R.validateDecisions([]).length !== 0) fail('an empty decision set was rejected');
} catch (e) {
  fail('review check threw -> ' + (e && e.message), 1);
}

console.log('PASS review: queue validation, schema-drift hard-fail, and export gating OK');
process.exit(0);
