"""A small, reproducible adaptation of the supplied newspaper inventory model.

Python 3.10+; standard library only. All business inputs live in config.json.
The primary objective preserves the notes' unmet-demand deduction. Cash profit
is reported separately so the deduction is never mistaken for a cash expense.
"""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics


def validate(c):
    """Reject invalid inputs instead of silently repairing probabilities."""
    integer_fields = ("unit_cost", "selling_price", "salvage_value", "bundle_size",
                      "days_per_run", "runs", "base_seed", "audit_days")
    for key in integer_fields:
        if type(c[key]) is not int:
            raise ValueError(f"{key} must be an integer")
    if not 0 <= c["salvage_value"] < c["unit_cost"] < c["selling_price"]:
        raise ValueError("Require 0 <= salvage_value < unit_cost < selling_price")
    for key in ("bundle_size", "days_per_run", "runs", "audit_days"):
        if c[key] <= 0:
            raise ValueError(f"{key} must be positive")
    if c["runs"] < 2:
        raise ValueError("Use at least two runs to calculate sampling variation")
    if c["audit_days"] > c["days_per_run"]:
        raise ValueError("audit_days cannot exceed days_per_run")
    values, types = c["demand_values"], c["day_types"]
    if (not values or any(type(x) is not int or x < 0 for x in values)
            or values != sorted(set(values))):
        raise ValueError("demand_values must be distinct, sorted nonnegative integers")
    for key in ("stock_min", "stock_max"):
        if key in c and (type(c[key]) is not int or c[key] < 0):
            raise ValueError(f"{key} must be a nonnegative integer")
    lower = c.get("stock_min", 0)
    upper = c.get("stock_max", ((max(values) + c["bundle_size"] - 1) // c["bundle_size"]) * c["bundle_size"])
    if lower > upper:
        raise ValueError("Stock minimum must not exceed stock maximum")
    if not types or any(not isinstance(x, str) or not x for x in types):
        raise ValueError("day_types must contain nonempty names")
    if len(types) != len(set(types)):
        raise ValueError("day_types must be distinct")
    rows = c["demand_percent_by_type"]
    if len(rows) != len(types) or len(c["day_type_percent"]) != len(types):
        raise ValueError("Every day type needs a probability and a demand row")
    for row, length in [(c["day_type_percent"], len(types))] + [
            (row, len(values)) for row in rows]:
        if len(row) != length or any(type(x) is not int or x < 0 for x in row):
            raise ValueError("Use nonnegative integer percentages of the right length")
        if sum(row) != 100:
            raise ValueError("Each probability distribution must sum to 100 percent")


def pick(labels, percentages, roll):
    """Inverse cumulative mapping: rolls are 1..100; display 100 as 00."""
    if type(roll) is not int or not 1 <= roll <= 100:
        raise ValueError("Random digit must be in 1..100 (100 displays as 00)")
    cumulative = 0
    for label, percent in zip(labels, percentages):
        cumulative += percent
        if roll <= cumulative:
            return label
    raise ValueError("Probability distribution does not cover the roll")


def generate_days(c, seed):
    """Two independent pseudo-random draws per day; no demand depends on stock."""
    rng = random.Random(seed)
    days = []
    for day in range(1, c["days_per_run"] + 1):
        day_roll, demand_roll = rng.randint(1, 100), rng.randint(1, 100)
        type_index = pick(range(len(c["day_types"])), c["day_type_percent"], day_roll)
        demand = pick(c["demand_values"], c["demand_percent_by_type"][type_index],
                      demand_roll)
        days.append({"day": day, "day_roll": day_roll, "demand_roll": demand_roll,
                     "day_type": c["day_types"][type_index], "demand": demand})
    return days


def daily_result(stock, demand, c):
    """Integer arithmetic keeps each day's monetary amounts exact."""
    if type(stock) is not int or type(demand) is not int or min(stock, demand) < 0:
        raise ValueError("Stock and demand must be nonnegative integers")
    sold = min(stock, demand)
    unsold, unmet = stock - sold, demand - sold
    revenue = c["selling_price"] * sold
    purchase_cost = c["unit_cost"] * stock
    recovery = c["salvage_value"] * unsold
    deduction = (c["selling_price"] - c["unit_cost"]) * unmet
    cash = revenue - purchase_cost + recovery
    return {"sold": sold, "unsold": unsold, "unmet": unmet, "revenue": revenue,
            "purchase_cost": purchase_cost, "recovery": recovery,
            "unmet_deduction": deduction, "cash_profit": cash,
            "textbook_score": cash - deduction}


def stock_options(c):
    """User-selected inclusive bounds; default to demand support if unspecified."""
    step = c["bundle_size"]
    lower = c.get("stock_min", 0)
    upper = c.get("stock_max", ((max(c["demand_values"]) + step - 1) // step) * step)
    return list(range(lower, upper + 1, step))


def demand_distribution(c):
    """Marginal P(D=d) = sum_t P(type=t) P(D=d | type=t)."""
    return [(d, sum(w * row[j] for w, row in zip(
        c["day_type_percent"], c["demand_percent_by_type"])) / 10000)
        for j, d in enumerate(c["demand_values"])]


def exact_metrics(stock, c):
    """Finite weighted sum, with no random sampling."""
    keys = ("textbook_score", "cash_profit", "unsold", "unmet")
    totals = {key: 0.0 for key in keys}
    for demand, probability in demand_distribution(c):
        result = daily_result(stock, demand, c)
        for key in keys:
            totals[key] += probability * result[key]
    return totals


def choose_best(rows, field):
    """Report all ties. Do not silently force a single winning stock quantity."""
    maximum = max(row[field] for row in rows)
    return [row["stock"] for row in rows
            if math.isclose(row[field], maximum, rel_tol=0, abs_tol=1e-9)]


def experiment(c):
    validate(c)
    options = stock_options(c)
    per_run, trace, first_days = [], [], []
    for run_index in range(c["runs"]):
        seed = c["base_seed"] + run_index
        days = generate_days(c, seed)
        if run_index == 0:
            first_days = days[:c["audit_days"]]
        trace.extend({"run": run_index + 1, "seed": seed, **day} for day in days)
        # Every stock quantity uses this same day's demand, within the same run.
        for stock in options:
            totals = {key: 0 for key in ("textbook_score", "cash_profit", "unsold", "unmet")}
            for day in days:
                result = daily_result(stock, day["demand"], c)
                for key in totals:
                    totals[key] += result[key]
            per_run.append({"run": run_index + 1, "seed": seed, "stock": stock,
                            **{key: value / len(days) for key, value in totals.items()}})
    summary = []
    for stock in options:
        rows = [row for row in per_run if row["stock"] == stock]
        exact = exact_metrics(stock, c)
        means = {key: statistics.mean(row[key] for row in rows) for key in exact}
        sd = statistics.stdev(row["textbook_score"] for row in rows)
        se = sd / math.sqrt(len(rows))
        summary.append({"stock": stock,
                        **{"sim_" + key: value for key, value in means.items()},
                        **{"exact_" + key: value for key, value in exact.items()},
                        "score_run_sd": sd, "score_standard_error": se,
                        "score_error": means["textbook_score"] - exact["textbook_score"]})
    winner = choose_best(summary, "sim_textbook_score")[0]
    audit = [{**day, "stock": winner, **daily_result(winner, day["demand"], c)}
             for day in first_days]
    wins = {q: 0 for q in options}
    for run in range(1, c["runs"] + 1):
        for q in choose_best([r for r in per_run if r["run"] == run], "textbook_score"):
            wins[q] += 1
    metadata = {"scenario": c["scenario"], "python_version": platform.python_version(),
                "random_generator": "Python random.Random (Mersenne Twister)",
                "seed_rule": "base_seed + zero-based run index",
                "first_seed": c["base_seed"], "last_seed": c["base_seed"] + c["runs"] - 1,
                "runs": c["runs"], "days_per_run": c["days_per_run"],
                "generated_day_scenarios": len(trace), "stock_options": options,
                "stock_day_evaluations": len(trace) * len(options),
                "sim_score_best": choose_best(summary, "sim_textbook_score"),
                "exact_score_best": choose_best(summary, "exact_textbook_score"),
                "exact_cash_best": choose_best(summary, "exact_cash_profit"),
                "sim_cash_best": choose_best(summary, "sim_cash_profit"),
                "run_score_wins_including_ties": wins,
                "audit_stock": winner,
                "audit_selection": "first simulated-score maximizer if tied",
                "input_basis": "Illustrative classroom adaptation of supplied notes, pp. 66-76"}
    return summary, per_run, trace, audit, metadata


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(out, c, result):
    out.mkdir(parents=True, exist_ok=True)
    summary, per_run, trace, audit, metadata = result
    for name, rows in (("summary.csv", summary), ("per_run.csv", per_run),
                       ("demand_trace.csv", trace), ("daily_audit.csv", audit)):
        write_csv(out / name, rows)
    write_csv(out / "exact_demand.csv", [dict(demand=d, probability=p)
                                         for d, p in demand_distribution(c)])
    mapping = []
    for roll in range(1, 101):
        mapping.append({"distribution": "day_type", "roll": roll,
                        "display_digit": f"{roll % 100:02}",
                        "outcome": pick(c["day_types"], c["day_type_percent"], roll)})
        for name, row in zip(c["day_types"], c["demand_percent_by_type"]):
            mapping.append({"distribution": name + " demand", "roll": roll,
                            "display_digit": f"{roll % 100:02}",
                            "outcome": pick(c["demand_values"], row, roll)})
    write_csv(out / "random_digit_mapping.csv", mapping)
    for name, data in (("config_used.json", c), ("metadata.json", metadata)):
        (out / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    files = [Path(__file__), out / "config_used.json"]
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    (out / "sha256.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parent
    parser.add_argument("--config", type=Path, default=root / "config.json")
    parser.add_argument("--out", type=Path, default=root / "results")
    parser.add_argument("--price", type=int, help="Optional selling-price sensitivity check")
    parser.add_argument("--stock-min", type=int, help="Minimum stock quantity")
    parser.add_argument("--stock-max", type=int, help="Maximum stock quantity")
    parser.add_argument("--stock-step", type=int, help="Increment between stock quantities")
    args = parser.parse_args()
    try:
        c = json.loads(args.config.read_text(encoding="utf-8"))
        if args.price is not None:
            c["selling_price"] = args.price
        for argument, key in ((args.stock_min, "stock_min"), (args.stock_max, "stock_max"), (args.stock_step, "bundle_size")):
            if argument is not None:
                c[key] = argument
        result = experiment(c)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    write_outputs(args.out, c, result)
    summary, _, _, _, metadata = result
    print(c["scenario"])
    print(f"{c['runs']} runs x {c['days_per_run']} days; {len(summary)} stock quantities")
    print(f"{'Stock':>5} {'Sim score':>12} {'Exact score':>12} {'Sim cash':>12} {'Error':>10}")
    for row in summary:
        print(f"{row['stock']:5d} {row['sim_textbook_score']:12.2f} "
              f"{row['exact_textbook_score']:12.2f} {row['sim_cash_profit']:12.2f} "
              f"{row['score_error']:10.2f}")
    print("Best textbook score (simulation / exact):",
          metadata["sim_score_best"], "/", metadata["exact_score_best"])
    print("Best cash profit (simulation / exact):",
          metadata["sim_cash_best"], "/", metadata["exact_cash_best"])
    print("Outputs:", args.out.resolve())


if __name__ == "__main__":
    main()
