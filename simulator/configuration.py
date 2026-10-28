"""Shared configuration for the form and views; no Django imports."""
import json
from pathlib import Path
from simulate import stock_options

ROOT = Path(__file__).resolve().parent.parent


def defaults():
    return json.loads((ROOT / "config.json").read_text())


def default_stock(config):
    """Nearest feasible batch to the configured preference; ties go lower."""
    return min(stock_options(config), key=lambda stock: abs(stock - config["default_stock"]))


def initial(config):
    """Flatten model settings into ordinary HTML form values."""
    values = {k: config[k] for k in (
        "unit_cost", "selling_price", "salvage_value", "days_per_run", "runs", "base_seed")}
    options = stock_options(config)
    values.update(chosen_stock=default_stock(config), bundle_size=config["bundle_size"],
                  stock_min=config.get("stock_min",0), stock_max=config.get("stock_max",options[-1]))
    for j, demand in enumerate(config["demand_values"]):
        values[f"demand_{j}"] = demand
    for i, name in enumerate(config["day_types"]):
        values[f"day_name_{i}"] = name
        values[f"day_chance_{i}"] = config["day_type_percent"][i]
        for j, chance in enumerate(config["demand_percent_by_type"][i]):
            values[f"chance_{i}_{j}"] = chance
    return values
