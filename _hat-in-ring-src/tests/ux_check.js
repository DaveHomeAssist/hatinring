/* Anticipatory UX regression check for the DC powered dashboard.
 *
 * This exercises the quick filter and sort logic directly on the generated
 * Component class. It avoids the retired init()/DOM API while still catching
 * stale model regressions before the daily pipeline can publish.
 */
const fs = require('fs');

const file = process.argv[2];
const html = fs.readFileSync(file, 'utf8');

function fail(msg, code = 2) {
  console.log('FAIL: ' + msg);
  process.exit(code);
}

function loadComponent(src) {
  const match = src.match(/<script\b[^>]*\bdata-dc-script\b[^>]*>([\s\S]*?)<\/script>/);
  if (!match) fail('dashboard script not found', 65);

  class DCLogic {
    constructor() {
      this.props = { partyColors: 'Muted', density: 'Compact', accent: 'Sky blue' };
    }
    setState(next) {
      this.state = Object.assign({}, this.state || {}, next || {});
    }
  }

  const Component = new Function('DCLogic', match[1] + '\nreturn Component;')(DCLogic);
  const app = new Component();
  app.props = { partyColors: 'Muted', density: 'Compact', accent: 'Sky blue' };
  return app;
}

let app;
try {
  app = loadComponent(html);
} catch (e) {
  fail('component threw while loading -> ' + (e && e.message), 1);
}

try {
  const all = app.all();
  const vals = app.renderVals();
  const first = app.filteredField().length;

  app.setQuick('movers');
  const movers = app.filteredField().length;
  const expectedMovers = app.all().filter((x) => app.isMover(x)).length;

  app.setQuick('declared');
  const declared = app.filteredField().length;
  const expectedDeclared = app.all().filter((x) => x.tier >= 4).length;

  app.setQuick('front');
  const front = app.filteredField().length;
  const expectedFront = app.all().filter((x) => x.pollLead).length;

  app.setQuick('front');
  const cleared = app.filteredField().length;

  app.sortBy('name');
  const sortedByName = app.filteredField();

  if (first !== all.length) fail('first visit does not show all rows (' + first + '/' + all.length + ')');
  if (movers !== expectedMovers) fail('Movers filter (' + movers + ') != isMover count (' + expectedMovers + ')');
  if (declared !== expectedDeclared) fail('In the ring filter (' + declared + ') != tier >= 4 count (' + expectedDeclared + ')');
  if (front !== expectedFront) fail('Poll leaders filter (' + front + ') != pollLead count (' + expectedFront + ')');
  if (cleared !== all.length) fail('second click on quick filter did not clear back to all rows');
  if (vals.quickChips.length !== 3) fail('expected 3 quick filter chips, got ' + vals.quickChips.length);
  if (!sortedByName.length || sortedByName[0].name.localeCompare(sortedByName[sortedByName.length - 1].name) > 0) {
    fail('name sort did not produce ascending row order');
  }
} catch (e) {
  fail('dashboard logic threw -> ' + (e && e.message), 1);
}

console.log('PASS ux: quick filters, clearing, and sort model OK');
process.exit(0);
