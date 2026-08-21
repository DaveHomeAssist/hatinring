# Prediction-market axis — verification gate and go/no-go

**Date:** 2026-08-21 · **Phase:** 4 (external reference axes) · **Status:** AWAITING DAVE
**Verified by:** Claude · **Decision owner:** Dave

Phase 4 is blocked on this gate by design: writing an integration against an
unverified API is wasted work and a possible terms violation. No Phase 4 code
has been written.

---

## Question 1 — do 2028 markets exist? **YES, on both venues.**

### Kalshi (`api.elections.kalshi.com/trade-api/v2`)

| Event ticker | Title | Contracts |
|---|---|---|
| `KXPRESNOMD-28` | 2028 Democratic presidential nominee | 47 |
| `KXPRESNOMR-28` | 2028 Republican presidential nominee | present |
| `KXPRESPARTY-2028` | 2028 Presidential Election winner (Party) | present |

### Polymarket (`gamma-api.polymarket.com`)

| Slug | Contracts | Volume |
|---|---|---|
| `democratic-presidential-nominee-2028` | 128 | ~$1.26B |
| `republican-presidential-nominee-2028` | present | — |
| `presidential-election-winner-2028` | present | — |

All three Polymarket events are among the **top-volume events on the entire
platform**, so this is not a thin novelty market.

## Question 2 — is the data retrievable? **YES, unauthenticated.**

Both APIs returned candidate-level probabilities over plain HTTPS with no key
and no account, fetched 2026-08-21:

| Candidate | Kalshi last | Polymarket |
|---|---|---|
| Alexandria Ocasio-Cortez | 0.18 | 0.1815 |
| Gavin Newsom | 0.16 | 0.1505 |
| Jon Ossoff | 0.16 | 0.1415 |
| Kamala Harris | 0.085 | 0.0745 |
| Pete Buttigieg | 0.049 | 0.0525 |
| Josh Shapiro | 0.045 | 0.0505 |
| Mark Kelly | 0.054 | 0.0295 |

Two independent venues agreeing this closely is itself a quality signal — and a
built-in sanity check we should keep (see *Recommended shape* below).

**Field mapping is clean.** Kalshi exposes the candidate name in
`yes_sub_title`, Polymarket in `groupItemTitle`; both match names already in
`config.yaml`'s watchlist for our top records. Kalshi price fields carry a
`_dollars` suffix in the current API version (`last_price_dollars`,
`yes_bid_dollars`, `yes_ask_dollars`) — the un-suffixed `last_price` is present
but null, which is the kind of detail that silently yields an all-empty artifact
if assumed rather than checked.

## Question 3 — do the terms permit daily retrieval and republication?

**NOT ANSWERED. This is the decision, and it is yours.**

I verified that the endpoints are public, unauthenticated, and technically
usable. I did **not** adjudicate either venue's terms of service, and I am not
in a position to give you a legal reading of them. What is technically open is
not automatically licensed for republication with attribution on a public site.

Before any Phase 4 code is written, you need to satisfy yourself on:

1. **Kalshi** — developer/API terms: is programmatic access for a
   non-commercial public display permitted, is there a rate limit or an
   attribution requirement, and is redistribution of quoted prices allowed?
2. **Polymarket** — same questions against its terms and any documented API
   policy.
3. **Attribution wording** each venue requires, if any, and whether a link back
   to the market is mandatory or merely good practice.
4. Whether displaying live betting odds on the site raises any concern for you
   independent of the terms — an editorial call, not a legal one.

If either venue is ambiguous, the plan's fallback stands: request written
clarification, and proceed with the other venue or with polling alone.

---

## Recommended shape, if you green-light it

- **Display-only, exactly like money.** Guardrail 4 becomes "Money, market odds,
  and polling are never folded into momentum," and a parity test asserts every
  candidate's score is byte-identical with and without `markets.json` present —
  the same test `financials` already has in
  `tests/test_latest_json_contract.py`.
- **Both venues, not one.** Store each separately and show them side by side.
  The cross-venue agreement above is a free correctness check; a single source
  that drifts has nothing to be caught against.
- **Explicit alias table in `config.yaml`.** Contract-to-candidate mapping is
  declared, never inferred. An unmapped contract is logged and omitted —
  attributing odds to the wrong person is the worst failure mode here.
- **Degrade, never fail.** A market fetch failure keeps the last good
  `markets.json` and logs, matching `money.refresh` and the Phase 3 feed
  handling. The daily run must not die because an exchange had an outage.
- **Publish additively** into `hatinring.v1` as a `markets` block, keyed by
  candidate id, alongside `financials`.

## Recommendation

**Go — conditional on your reading of item 3.** The technical case is as strong
as it gets: the markets exist, they are deeply liquid, the data is free and
unauthenticated, two venues corroborate each other, and the names map to records
we already track. The only open question is permission, and that is the one I
cannot answer for you.

If you would rather not depend on a commercial exchange at all, the polling half
of Phase 4 is independent of this decision and can proceed alone.

## Also needs your call (Phase 4, milestone 3)

The plan assumes polling comes from **Wikipedia's 2028 primary polling
wikitables**, with a hand-curated `data/polls_override.json` taking precedence.
That was flagged as unconfirmed in the plan and is still unconfirmed. Wikitable
structure changes without notice, so the parser must degrade to the last good
`polls.json` rather than fail the run. Confirm the source before that work
starts.
