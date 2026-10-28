# Player-Managed Potion Shop

Abdul Mueed (22SW058) and Abdul Aziz (22SW046).

A shop-management game prototype. You play the owner: buy ingredient-and-bottle kits, brew an opening batch, then sell to NPC customers. The batch decision commits gold before you know whether the day will be busy or quiet. At closing, a wholesaler buys excess stock at a discount.

The question is simple: how much should you brew before opening? Each simulated day is a separate one-day challenge. Ingredients are represented by a combined cost per finished potion; there is no separate recipe or ingredient-inventory system. The simulation compares your decision with alternative batch sizes under the same demand.
## Run

Use Python 3.10 or later. In this folder:

```
python -m pip install --no-index --find-links vendor -r requirements.txt
python manage.py runserver
```

Open http://127.0.0.1:8000/. No database setup, accounts, Node build or internet connection is required after extracting the included files. This is a local classroom demonstration.

The interface uses Django Template Language, local CSS and a small vanilla JavaScript loading state. There are no external fonts, assets or frontend dependencies. Simulation settings and demand probabilities expand with native disclosure controls. The page computes all results in Python. Edit inputs and choose Run simulation. Open Edit customer demand to change day names, day-type probabilities, demand quantities and the conditional probabilities using labeled input fields. Day-type probabilities and each conditional row must total 100 percent. The number of day types and demand outcomes comes from config.json. View result tables opens the stock comparison, per-run results, daily audit and full demand trace directly on the page. The trace uses 100 rows per page; pagination preserves your inputs. Change selling price to 80 to demonstrate the recommendation changes.

## Reproduce and test

```
python simulate.py
python manage.py test -v 2
python simulate.py --price 80 --out price80_results
python simulate.py --stock-min 0 --stock-max 500 --stock-step 10 --out wider_range_results
```

The baseline has 30 runs of 1,000 shop-day scenarios, evaluated for 11 batch quantities. There are 31 passing automated tests. Reported results come from actual execution. The finite expectation provides an exact benchmark.

Textbook-score winner: 70 potions, simulated score 928.59 gold versus exact 931.00. Cash-profit winner: 60 potions. These objectives differ because the textbook score subtracts foregone margin on unmet demand. The UI and guide make that distinction explicit.

## Files

PRESENTATION.pptx has seven editable slides with a chart. PRESENTATION.pdf provides offline viewing. REPORT.pdf records the model and verification. PRESENTER_GUIDE.pdf contains speaking notes and questions. config.json and the web form contain the inputs. simulate.py is the pure Python engine; simulator/ contains Django forms, routes, template, styles and web tests. results/ and verification/ contain actual evidence. vendor/ contains official dependency wheels.

This is a proposed game mechanic. Prices and demand probabilities adapt the supplied classroom example; no existing game or survey data is claimed. Closing clearance settles the one-day challenge. Carryover, production time and price-dependent demand are outside the model. Static documents describe the default configuration; changed inputs recompute the web results and tables. The separate CLI can still produce CSV evidence for reproducibility. Some evidence filenames retain `raid` from the earlier framing; each row now represents one shop day, with identical calculations.
You operate the shop: set Your crafting quantity within your chosen comparison range and step and select prices. Results and audit metrics reflect that choice. Best stock remains a benchmark rather than replacing your decision. The run-results and daily-audit tables use your selected quantity.


## Configuration and demo limits

`config.json` holds `bundle_size` and the preferred `default_stock`. The form and view share `simulator/configuration.py`. If the preferred stock is not a feasible batch, the initial selection uses the nearest feasible quantity (ties go lower). Submitted stock must match a feasible batch. Minimum stock, Maximum stock and Stock step are editable form inputs. Stock step uses the existing bundle_size config key; optional stock_min and stock_max keys also work in the CLI. A range from 0 to 500 with step 10 accepts a crafting quantity of 500. Quantities are min + n × step, up to the inclusive maximum. Without explicit bounds, the CLI derives an initial range from demand support. `potionshop/` contains Django settings and routes.

Web limits protect the synchronous classroom demo: at most 100,000 sampled shop days, 20 demand outcomes, 2,000 comparison quantities and 5,000,000 stock-day evaluations per request. There is no fixed upper stock-quantity or demand-quantity cap. Each run allows 20–5,000 days and an experiment 2–100 runs, subject to the total limit. These are interface guards, not economic assumptions; the CLI remains governed by the engine's model validation. Django also limits request bodies to 16 KiB. Time zone is UTC; the model uses shop-day indices, not wall-clock time.
