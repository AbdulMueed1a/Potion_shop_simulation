# Frontend verification

27 October 2026

- Rendering engine: django.template.backends.django.DjangoTemplates, unchanged.
- Existing Python views, forms, context, CSRF middleware and named routes retained.
- Django system check: no issues. Existing suite: 31 tests passed, including validation, CSRF, exports and batch-size regressions.
- Managed browser preview starts the actual Django development server.
- Desktop browser: default page, stock 40 submission (score 320.77; benchmark 70), invalid price error, reset, simulation settings, demand probabilities and shop-rules navigation verified.
- Local CSS and JavaScript load; loading state appears on submission and clears after the server response. No external fonts or assets.
- Responsive CSS uses 1050, 780 and 460 px breakpoints, with an independently scrollable chart. The available browser controls did not expose viewport resizing, so narrow-screen visual behavior has not been browser-verified.
- The project has no authentication-dependent pages or permission-specific UI.

## Demand input fields

- Replaced the editable JSON textarea with Django fields for day names, day-type percentages, demand quantities and conditional percentages. Field counts follow the configured model.
- Browser verified: Edit customer demand opens the editor; demand quantity labels update while typing; valid edits submit from the external Apply button and recalculate the score (875.37 for the tested changed distribution); a 101% day-type total returns a Django validation error with entered values preserved.
- Existing test methods now also check missing fields, out-of-range probabilities, invalid totals, duplicate quantities/names, and a complete round trip of edited inputs through page rendering and evidence export. All 31 tests pass.

## On-page evidence and configurable stock range

- Removed the web download route and button. Stock summaries, per-run results for the selected batch, its daily audit, and the full demand trace render in Django templates. The CLI still writes reproducible local CSV evidence.
- The trace uses 100 rows per page. Browser verification confirmed page 2 shows rows 101-200 and preserves chosen stock 500 and the 0-500 range.
- Browser run: minimum 0, maximum 500, step 10, chosen stock 500, default 30 x 1000 days. Mean score/cash -7441.55, exact score -7438.00; best in that range 70.
- The model accepts explicit stock_min/stock_max and bundle_size as its comparison step. No fixed upper quantity cap. Web workload guards: 2000 quantities and 5000000 stock-day evaluations, with clear validation errors; existing day/run limits also remain.
- 31 tests pass. Checks cover custom ranges, an offset minimum, a single quantity, stock one million, daily audits for the selected stock, missing/invalid inputs, CSRF and input-preserving table pagination.
