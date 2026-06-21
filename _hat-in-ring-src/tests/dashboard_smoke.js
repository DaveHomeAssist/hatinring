/* Headless smoke test for the DC powered dashboard.
 *
 * The current dashboard is a DC component, not the older global init()
 * script. This harness loads the generated component class, stubs the small
 * DCLogic surface it needs, and checks the first visit data contract.
 *
 * Usage:  node dashboard_smoke.js <path-to-built-index.html>
 */
const fs = require('fs');

const file = process.argv[2];
if (!file) { console.log('FAIL: no HTML path given'); process.exit(64); }
const html = fs.readFileSync(file, 'utf8');

function loadComponent(src) {
  const match = src.match(/<script\b[^>]*\bdata-dc-script\b[^>]*>([\s\S]*?)<\/script>/);
  if (!match) { console.log('FAIL: could not find the DC dashboard script'); process.exit(65); }

  class DCLogic {
    constructor() {
      this.props = { partyColors: 'Muted', density: 'Compact', accent: 'Sky blue' };
    }
    setState(next) {
      this.state = Object.assign({}, this.state || {}, next || {});
    }
  }

  try {
    const Component = new Function('DCLogic', match[1] + '\nreturn Component;')(DCLogic);
    const instance = new Component();
    instance.props = { partyColors: 'Muted', density: 'Compact', accent: 'Sky blue' };
    return instance;
  } catch (e) {
    console.log('FAIL: component script did not evaluate -> ' + (e && e.message));
    process.exit(66);
  }
}

let app;
try {
  app = loadComponent(html);
  const all = app.all();
  const filtered = app.filteredField();
  const vals = app.renderVals();

  if (!all.length) { console.log('FAIL: no records parsed from SEED'); process.exit(2); }
  if (filtered.length !== all.length) {
    console.log(`FAIL: board shows ${filtered.length} rows but there are ${all.length} records`);
    process.exit(3);
  }
  if (!vals || vals.rows.length !== all.length) {
    console.log('FAIL: renderVals rows do not match the record count');
    process.exit(4);
  }
  if (vals.navTabs.length !== 3 || vals.stats.length !== 6 || vals.tiers.length !== 6) {
    console.log('FAIL: expected nav, stat, and tier models were not produced');
    process.exit(5);
  }
  if (!vals.asOf || vals.asOf === 'June 14, 2026') {
    console.log('FAIL: asOf is missing or still hardcoded to the stale redesign date');
    process.exit(6);
  }
} catch (e) {
  console.log('FAIL: render model threw -> ' + (e && e.message));
  process.exit(1);
}

console.log(`PASS: first-visit render model OK — rows=${app.filteredField().length} records=${app.all().length}`);
process.exit(0);
