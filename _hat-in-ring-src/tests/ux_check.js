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

// ---------------------------------------------------------------------------
// Staleness banner (Phase 1). The build stamp baked into this page is
// 2026-06-13, so we drive staleness() with explicit "now" values rather than
// the wall clock — the check must not start passing/failing as time passes.
// ---------------------------------------------------------------------------
try {
  const at = (iso) => app.staleness(new Date(iso + 'T00:00:00Z'));

  if (app.STALE_AFTER_DAYS !== 2) fail('expected a 48h (2 whole day) staleness threshold, got ' + app.STALE_AFTER_DAYS);

  // Fresh: same day, next day, and exactly 2 days out are all NOT stale.
  if (at('2026-06-13') !== null) fail('banner shown on the build date itself');
  if (at('2026-06-14') !== null) fail('banner shown 1 day after the build date');
  if (at('2026-06-15') !== null) fail('banner shown at exactly the 2-day threshold');

  // Stale: 3+ days out.
  const stale = at('2026-06-16');
  if (stale === null) fail('banner NOT shown 3 days after the build date');
  if (stale.days !== 3) fail('expected days=3, got ' + stale.days);
  if (!/June 13, 2026/.test(stale.message)) fail('banner message omits the as-of date: ' + stale.message);
  if (!/\d+ days ago/.test(stale.message)) fail('banner message omits the age: ' + stale.message);

  const older = at('2026-07-13');
  if (older === null || older.days !== 30) fail('expected days=30 a month out, got ' + (older && older.days));

  // A clock skewed BEHIND the build date must never show the banner.
  if (at('2026-06-01') !== null) fail('banner shown for a client clock behind the build date');

  // The model flags the markup binds to must track staleness() for the REAL
  // clock. Asserted as a relationship, not a fixed value: this page's build
  // stamp is pinned in the past, so whether it is stale right now depends on
  // when the suite runs.
  const vals = app.renderVals();
  const live = app.staleness();
  if (vals.isStale !== (live !== null)) fail('renderVals().isStale disagrees with staleness()');
  if (live === null) {
    if (vals.staleMessage !== '') fail('staleMessage should be empty when fresh');
  } else if (vals.staleMessage !== live.message) {
    fail('staleMessage does not carry the staleness() message');
  }
} catch (e) {
  fail('staleness check threw -> ' + (e && e.message), 1);
}

// ---------------------------------------------------------------------------
// Timeline view (Phase 6). Drives the model directly — the track markers and the
// list are both derived from timelineEvents(), so this covers what renders.
// ---------------------------------------------------------------------------
try {
  const nav = app.renderVals().navTabs.map((t) => t.label);
  if (!nav.includes('Timeline')) fail('Timeline tab missing from nav: ' + nav.join(','));

  app.go('timeline');
  if (app.state.view !== 'timeline') fail('go(timeline) did not switch the view');
  const tv = app.renderVals();
  if (tv.isTimeline !== true) fail('isTimeline not set on the timeline view');
  if (tv.isField !== false) fail('field view still active alongside timeline');
  // sc-if has no negation, so the inverse flag must actually be the inverse.
  if (tv.hasTimeline === tv.isTimelineEmpty) fail('hasTimeline is not the inverse of isTimelineEmpty');

  if (!Array.isArray(app.TIMELINE)) fail('TIMELINE was not injected as an array');
  // With no filter applied every event must be present — this keeps the
  // per-row assertions below honest rather than vacuously true on an empty set.
  if (tv.tlRows.length !== app.TIMELINE.length) {
    fail('tlRows(' + tv.tlRows.length + ') != TIMELINE(' + app.TIMELINE.length + ') with filter=all');
  }

  // Newest first.
  const dates = tv.tlRows.map((r) => r.date);
  for (let i = 1; i < dates.length; i++) {
    if (dates[i] > dates[i - 1]) fail('timeline rows are not newest-first at index ' + i);
  }

  // Filters partition the set: all == up + down.
  const total = app.timelineEvents().length;
  app.setState({ tlFilter: 'up' });
  const up = app.timelineEvents().length;
  app.setState({ tlFilter: 'down' });
  const down = app.timelineEvents().length;
  if (up + down !== total) fail('up(' + up + ') + down(' + down + ') != all(' + total + ')');
  app.setState({ tlFilter: 'all' });
  if (app.timelineEvents().length !== total) fail('clearing the filter did not restore all moves');
  if (app.renderVals().tlFilters.length !== 3) fail('expected 3 timeline filter chips');

  // Every row is labelled for assistive tech and openable.
  for (const r of tv.tlRows) {
    if (!r.label || !/\d{4}-\d{2}-\d{2}/.test(r.label)) fail('timeline row has no dated aria-label: ' + r.label);
    if (typeof r.open !== 'function') fail('timeline row is not openable');
    if (!r.why) fail('timeline row has no explanation text');
    if (r.reconstructed && /Reconstructed/.test(r.why) === false) {
      fail('a reconstructed row does not say so: ' + r.why);
    }
  }

  // tlPos must stay in range and never divide by zero on a single-day span.
  if (app.tlPos('2026-06-13', '2026-06-13', '2026-06-13') !== 1) fail('tlPos did not handle a zero-width span');
  const mid = app.tlPos('2026-06-15', '2026-06-10', '2026-06-20');
  if (Math.abs(mid - 0.5) > 1e-9) fail('tlPos midpoint wrong: ' + mid);
  if (app.tlPos('2020-01-01', '2026-06-10', '2026-06-20') !== 0) fail('tlPos did not clamp below 0');
  if (app.tlPos('2030-01-01', '2026-06-10', '2026-06-20') !== 1) fail('tlPos did not clamp above 1');

  // Hash routing must round-trip the new view.
  app.go('field');
  if (app.state.view !== 'field') fail('could not navigate back to the field');
} catch (e) {
  fail('timeline check threw -> ' + (e && e.message), 1);
}

console.log('PASS ux: quick filters, clearing, sort model, staleness banner, and timeline OK');
process.exit(0);
