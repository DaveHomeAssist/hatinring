/* Runtime safety check for hostile data in the DC dashboard.
 *
 * React owns text interpolation in the DC runtime, so this check focuses on
 * the two contracts this repo controls: hostile data must not break out of the
 * data script, and the Component model must still parse and render with the
 * hostile record present.
 */
const fs = require('fs');

const file = process.argv[2];
const html = fs.readFileSync(file, 'utf8');

function fail(msg, code = 2) {
  console.log('FAIL: ' + msg);
  process.exit(code);
}

const match = html.match(/<script\b[^>]*\bdata-dc-script\b[^>]*>([\s\S]*?)<\/script>/);
if (!match) fail('dashboard script not found', 65);
const main = match[1];

if (main.toLowerCase().includes('</script')) fail('raw </script> survived in the DC script');
if (!main.includes('\\u003c')) fail('expected hostile < characters to be escaped as \\u003c');

class DCLogic {
  constructor() {
    this.props = { partyColors: 'Muted', density: 'Compact', accent: 'Sky blue' };
  }
  setState(next) {
    this.state = Object.assign({}, this.state || {}, next || {});
  }
}

let app;
try {
  const Component = new Function('DCLogic', main + '\nreturn Component;')(DCLogic);
  app = new Component();
  app.props = { partyColors: 'Muted', density: 'Compact', accent: 'Sky blue' };
  const vals = app.renderVals();
  if (app.all().length !== 1 || vals.rows.length !== 1) fail('hostile record did not render into the row model');
  if (!vals.rows[0].headline.includes('<script>')) fail('hostile headline did not round trip as inert data');
} catch (e) {
  fail('component threw -> ' + (e && e.message), 1);
}

console.log('PASS: hostile fields stay inside escaped data and the DC model renders');
process.exit(0);
