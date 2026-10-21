# Eat Well

A dietary restaurant finder for the Pimoroni Tufty 2350 (Badger/Badgeware).
Pick a city, filter by diet, browse the results, and open a detail view with
cuisine, price, rating, neighborhood, and notes. Each detail screen also shows
a QR code that opens the restaurant in MapQuest when scanned.

A web companion with AI-powered natural-language search (Qwen3, running in the browser) is at https://eat-well-ai.view.fast/ — see the [Eat Well AI](https://github.com/Mike-Demo/eat-well-ai) repo.

## Cities

14 US metros, 557 curated spots:

- San Francisco, CA (36)
- Twin Cities, MN (39)
- Chicago, IL (42)
- New York, NY (39)
- Los Angeles, CA (40)
- Houston, TX (35)
- Phoenix, AZ (39)
- Philadelphia, PA (35)
- San Antonio, TX (42)
- San Diego, CA (39)
- Dallas, TX (40)
- San Jose, CA (36)
- Washington, DC (42)
- Miami, FL (53)

## Controls

UP/DOWN moves, A selects, B or C goes back.

Flow: city picker → diet filter → results list → detail view.

Diet filters: vegan, vegetarian, gluten-free, kosher, halal — each with its
own icon.

## Near me

The first row of the city picker detects your city over the network and
jumps to its guide if one exists. The badge has no GPS, so this uses
city-level IP geolocation (no API key needed). If the network is down or
your city isn't in the guide, you get a plain message and the manual picker
keeps working.

## Disclaimer

Menus and dietary practices change. The detail screen reminds you to verify
dietary needs directly with the restaurant. Listings were researched in
October 2026 and are a curated guide, not a live ranking.

## Package and preview

Package with Python 3 (no extra packages needed):

```sh
python3 scripts/package.py eat_well
```

This creates `dist/eat_well.zip`. Open that ZIP in
[Make](https://badge.select/make) via **Open file**, then choose **Run** for
a browser preview. Or copy the `eat_well` folder to the badge's `apps`
folder over USB (double-press RESET to mount the drive).

## Data

`eat_well/data/restaurants.json` holds the listings. To add a city, follow
the same JSON shape: `id`, `name`, `aliases` (for Near-me matching), and a
`restaurants` array with `name`, `cuisine`, `price`, `diets`, `area`,
`note`, and `rating` (null when unknown).

The app entry point is `eat_well/__init__.py`; `eat_well/icons.py` draws the
diet icons.

## Security audit triage — 2026-10-21

Parent: [Mike-Demo/eat-well#1](https://github.com/Mike-Demo/eat-well/issues/1).
This Markdown backlog is the fallback for a session without issue-creation
capability; the issue below is ready to file, not already created.

### Prioritized backlog

- **Confirmed findings: 0.** There are no confirmed findings to rank by
  severity, lower-trust reachability, or fix size/safety, no shared-root-cause
  groups, and no confirmed-finding remediation issues to create.
- **Needs validation: 1.** File the single checklist issue below. Its runtime
  impact remains unknown; do not assign severity or promote it to a confirmed
  finding before resolving the missing fact.
- **Rejected candidates: 3.** Do not reopen without new evidence:
  `make-qr-no-url-allowlist-phishing-qr`,
  `make-qr-unescaped-data-codegen-injection`,
  `unvalidated-restaurants-json-missing-key-crash`.

The supplied audit was static source inspection only: no code was executed
and no deployed endpoint was probed. This triage changes no app code and
does not claim runtime validation.

### Ready-to-file issue

**Title:** `[security][needs-validation] Audit leads to validate`

**Body:**

Parent audit: [Mike-Demo/eat-well#1](https://github.com/Mike-Demo/eat-well/issues/1).

- [ ] Validate **Near me: non-object JSON from ipwho.is raises uncaught
  AttributeError instead of degrading to a notice**.
  - Fingerprint: `locate-city-non-dict-json-uncaught-crash`.
  - Evidence / claimed root cause:
    [`locate_city()`](eat_well/__init__.py#L145-L157) calls
    `data.get('success')` and `data.get('city')` outside the try/except
    guarding `requests.get` and `resp.json()`, without checking that the
    parsed JSON is a dict. A non-object body therefore raises an uncaught
    `AttributeError`; the resulting session behavior is not established.
  - Exact missing fact: What the Badgeware run() loop does on the physical Tufty 2350 (and in badge.select) when update() raises an uncaught exception - terminate the app session, show a recoverable error card and resume, or restart - since runtime.md documents error cards only for the browser profile and states physical firmware is not tested by the kit.
  - Record the observed behavior separately for physical Tufty 2350 and
    badge.select, with runtime/firmware versions and reproduction evidence.
    Keep the lead open if either environment remains unvalidated. Only then
    decide whether a confirmed security finding and remediation issue are
    warranted; do not assign severity to this lead.
