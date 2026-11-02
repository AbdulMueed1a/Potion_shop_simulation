# Player-Managed Potion Shop

### Simulation and Modeling Assignment
**Instructor:** Prof. Dr. Sania Bhatti  
**Department:** Department of Software Engineering, Mehran University of Engineering and Technology (MUET), Jamshoro  
**Group Members:**  
- Abdul Mueed (22SW058)  
- Abdul Aziz (22SW046)  

---

## Overview

This project is a Monte Carlo simulation of a single-period stochastic inventory system (the classic **Newsvendor Problem**), framed as an interactive fantasy potion shop. 

Each morning, the shopkeeper commits gold to brew a batch of potions before knowing the day's customer demand. Potions sold to NPC customers generate revenue, while unsold inventory at closing is cleared to a wholesaler at a discounted salvage price. If customer demand exceeds the prepared batch, potential sales are permanently lost.

The system evaluates batch decisions across simulated days and compares results against mathematical expectations derived from the discrete probability distributions.

---

## Economic Model & Parameters

### Baseline Configuration (`config.json`)

| Parameter | Value | Description |
| :--- | :--- | :--- |
| **Unit Cost ($c$)** | 30 gold | Production cost per finished potion (kit + bottle). |
| **Selling Price ($p$)** | 50 gold | Price paid by retail customers. |
| **Salvage Value ($s$)** | 10 gold | Clearance price paid by the wholesaler for unsold stock. |
| **Batch Step ($Q_{\text{step}}$)** | 10 potions | Discrete increment for inventory choices. |
| **Simulation Scope** | 30 runs $\times$ 1,000 days | Sample size for empirical distribution estimation. |

### Demand Structure

Daily demand is determined by a two-stage discrete random process:
1. **Day Type Draw:** A random roll selects the day category:
   - **Busy:** 35% probability
   - **Normal:** 45% probability
   - **Quiet:** 20% probability
2. **Conditional Demand Draw:** A second roll determines the exact demand quantity (ranging from 40 to 100 potions) conditioned on the drawn day type.

### Objective Functions

The model evaluates inventory quantities under two distinct metrics:

1. **Textbook Score (Profit with Opportunity Cost Penalty):**
   $$\text{Score} = \text{Cash Profit} - (p - c) \times \text{Unmet Demand}$$
   Subtracts the foregone margin on lost customer sales. Under baseline parameters, the optimal inventory level is **70 potions** (Theoretical Expectation: 931.00 gold; Simulated Average: 928.59 gold).

2. **Cash Profit (Net Realized Accounting Profit):**
   $$\text{Cash Profit} = (p \times \text{Sold}) - (c \times \text{Stock}) + (s \times \text{Unsold})$$
   Measures net gold without opportunity cost deductions. The empirical winner under baseline parameters is **60 potions**.

---

## Project Features

- **Interactive Web Interface (Django):** Adjust unit cost, selling price, salvage price, stock range, and full probability distributions on the fly with real-time validation.
- **Evidence & Audit Tables:** Displays batch comparisons, per-run distributions, daily audit trails, and paginated 100-row demand traces.
- **Pure-Python CLI Engine (`simulate.py`):** Self-contained, dependency-free simulation engine suitable for headless batch execution and CSV export.
- **Automated Verification:** 31 automated tests covering economics bounds, digit-boundary assignments, marginal distribution calculations, and CSRF/web validation.

---

## How to Run

### Prerequisites

- Python 3.10 or later

### Setup & Run Web Interface

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Initialize local environment settings:
   ```bash
   cp .env.example .env
   ```

4. Start the Django server:
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser. No external database or setup is required.

---

## Testing & CLI Usage

### Running the Test Suite

Execute the 31 automated tests:
```bash
python manage.py test -v 2
```

### Running the Standalone Simulation CLI

```bash
# Run standard baseline simulation
python simulate.py

# Evaluate a different retail price
python simulate.py --price 80 --out price80_results

# Evaluate custom inventory bounds
python simulate.py --stock-min 0 --stock-max 500 --stock-step 10
```

---

## Project Structure

```text
├── config.json            # Baseline model parameters and demand probability tables
├── manage.py              # Django management script
├── potionshop/            # Django application settings, routing, and WSGI entrypoint
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── pyproject.toml         # Project metadata and configuration
├── requirements.txt       # Project dependencies (Django 5.2.18)
├── simulate.py            # Standalone Monte Carlo simulation engine
├── simulator/             # Simulation web application
│   ├── configuration.py   # Input parsing and probability validation
│   ├── forms.py           # Web form definitions and constraints
│   ├── static/simulator/  # CSS stylesheet and JavaScript loading state
│   ├── templates/         # Django HTML templates and evidence tables
│   ├── tests.py           # Web route and validation tests
│   └── views.py           # Simulation execution and results view
└── test_simulation.py     # Core mathematical and economic unit tests
```
