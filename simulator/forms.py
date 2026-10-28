from django import forms
from simulate import validate
from . import configuration

# Limits keep the synchronous local demo responsive; they are not model inputs.
MAX_SCENARIOS = 100_000
MAX_DEMAND_OUTCOMES = 20
MAX_STOCK_DAY_EVALUATIONS = 5_000_000
MAX_COMPARISONS = 2000


class ExperimentForm(forms.Form):
    chosen_stock = forms.IntegerField(label="Your crafting quantity", min_value=0)
    stock_min = forms.IntegerField(label="Minimum stock", min_value=0)
    stock_max = forms.IntegerField(label="Maximum stock", min_value=0)
    bundle_size = forms.IntegerField(label="Stock step", min_value=1)
    unit_cost = forms.IntegerField(label="Ingredients + bottle / potion (gold)", min_value=1)
    selling_price = forms.IntegerField(label="Selling price (gold)", min_value=1)
    salvage_value = forms.IntegerField(label="Closing clearance / potion (gold)", min_value=0)
    days_per_run = forms.IntegerField(label="Shop days per run", min_value=20, max_value=5000)
    runs = forms.IntegerField(label="Independent runs", min_value=2, max_value=100)
    base_seed = forms.IntegerField(label="Starting seed", min_value=0, max_value=2147483647)

    def __init__(self, *args, config=None, **kwargs):
        self.config = configuration.defaults() if config is None else config
        super().__init__(*args, **kwargs)
        self.fields["chosen_stock"].initial = configuration.default_stock(self.config)
        self.fields["chosen_stock"].widget.attrs["step"] = "any"

        values = configuration.initial(self.config)
        # Demand controls live below the main form and use native HTML form ownership.
        def add_field(name, field):
            field.initial = values[name]
            field.widget.attrs["form"] = "experiment-form"
            if name.startswith("demand_"):
                field.widget.attrs["data-demand-index"] = name.removeprefix("demand_")
            self.fields[name] = field

        for j in range(len(self.config["demand_values"])):
            add_field(f"demand_{j}", forms.IntegerField(
                label=f"Outcome {j + 1} (potions)", min_value=0))
        for i, name in enumerate(self.config["day_types"]):
            add_field(f"day_name_{i}", forms.CharField(label=f"Day type {i + 1} name", max_length=32))
            add_field(f"day_chance_{i}", forms.IntegerField(
                label=f"Day type {i + 1} probability (%)", min_value=0, max_value=100))
            for j in range(len(self.config["demand_values"])):
                add_field(f"chance_{i}_{j}", forms.IntegerField(
                    label=f"{name}: outcome {j + 1} probability (%)", min_value=0, max_value=100))

    @property
    def demand_fields(self):
        return [self[f"demand_{j}"] for j in range(len(self.config["demand_values"]))]

    @property
    def demand_profiles(self):
        return [{"name": self[f"day_name_{i}"], "probability": self[f"day_chance_{i}"],
                 "outcomes": [{"quantity": self[f"demand_{j}"].value(),
                               "field": self[f"chance_{i}_{j}"]}
                              for j in range(len(self.config["demand_values"]))]}
                for i in range(len(self.config["day_types"]))]

    def clean(self):
        data = super().clean()
        if self.errors:
            return data
        try:
            config = self.config.copy()
            for key in ("unit_cost", "selling_price", "salvage_value", "days_per_run", "runs", "base_seed", "stock_min", "stock_max", "bundle_size"):
                config[key] = data[key]
            config["demand_values"] = [data[f"demand_{j}"] for j in range(len(self.config["demand_values"]))]
            config["day_types"] = [data[f"day_name_{i}"] for i in range(len(self.config["day_types"]))]
            config["day_type_percent"] = [data[f"day_chance_{i}"] for i in range(len(self.config["day_types"]))]
            config["demand_percent_by_type"] = [
                [data[f"chance_{i}_{j}"] for j in range(len(config["demand_values"]))]
                for i in range(len(config["day_types"]))]
            if sum(config["day_type_percent"]) != 100:
                raise ValueError("Day-type probabilities must total 100%.")
            for name, row in zip(config["day_types"], config["demand_percent_by_type"]):
                if sum(row) != 100:
                    raise ValueError(f"{name} demand probabilities must total 100%.")
            validate(config)
            scenarios = config["days_per_run"] * config["runs"]
            option_count = (config["stock_max"] - config["stock_min"]) // config["bundle_size"] + 1
            if option_count > MAX_COMPARISONS:
                raise ValueError(f"The web demo displays at most {MAX_COMPARISONS:,} stock quantities. Increase the stock step; the quantity itself has no fixed upper bound.")
            if scenarios > MAX_SCENARIOS:
                raise ValueError(f"Use at most {MAX_SCENARIOS:,} shop-day scenarios")
            if scenarios * option_count > MAX_STOCK_DAY_EVALUATIONS:
                raise ValueError(f"This comparison requires {scenarios * option_count:,} stock-day evaluations. The web demo allows {MAX_STOCK_DAY_EVALUATIONS:,} per request. Increase the stock step or reduce days/runs.")
            selected = data["chosen_stock"]
            if not (config["stock_min"] <= selected <= config["stock_max"]) or (selected - config["stock_min"]) % config["bundle_size"]:
                raise ValueError("Your crafting quantity must be inside the comparison range and match its stock step.")
            if len(config["demand_values"]) > MAX_DEMAND_OUTCOMES:
                raise ValueError(f"Demand is limited to {MAX_DEMAND_OUTCOMES} outcomes")
            data["config"] = config
        except (ValueError, TypeError, KeyError) as error:
            raise forms.ValidationError(str(error))
        return data
