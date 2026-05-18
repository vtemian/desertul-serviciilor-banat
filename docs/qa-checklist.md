# Local QA Checklist — Deșertul de servicii, Banat

Versioned QA checklist for the public web app under `web/`. Run via
`./.venv/bin/python scripts/qa_headless.py`. The harness serves `web/`
on port 8765 and drives a headless Chromium through every item below,
saving screenshots to `docs/qa-screenshots/`.

## Functional checks

- [ ] Map loads; 99 UAT polygons visible (`map.querySourceFeatures('uats')` ≥ 99).
- [ ] Composite view renders fills (initial `_color_composite` ≠ transparent on most UATs).
- [ ] Click on Timișoara → detail panel populated with `name`, composite score row.
- [ ] Click on a bottom-decile rural UAT (Beba Veche, Cenad, Dudeștii Vechi, Sânpetru Mare, or Gătaia) → detail panel populated.
- [ ] View toggle (composite → school → hospital) repaints WITHOUT JS error in console.
- [ ] Permalink: `#timisoara-tm` opens Timișoara detail. `#bogus-uat-tm` is silent (no JS error).
- [ ] EN toggle: every visible string switches (brand h1, view buttons, footer disclaimer).
- [ ] Mobile viewport (375×812): map fills, no horizontal overflow.

## Analytics

- [ ] Plausible event fires on view-change AND permalink (mocked, counted by route handler).

## Console hygiene

- [ ] No JS console errors at any point (CORS, MIME, missing data file, MapLibre warnings).

## Editorial / framing guardrails

- [ ] Footer disclaimer present in both languages.
- [ ] "desființare" appears only in the disclaimer denying it (grep on rendered DOM textContent).

## Artifacts

Screenshots committed under `docs/qa-screenshots/`:

- `desktop-composite.png` — initial load, RO, composite view.
- `desktop-en.png` — after EN language toggle.
- `mobile-composite.png` — 375×812 viewport.
