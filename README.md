# Player-Managed Potion Shop

Abdul Mueed (22SW058) and Abdul Aziz (22SW046)

A Monte Carlo inventory simulation game prototype built with Django. The player operates a potion shop: purchase ingredient kits, brew an opening batch of potions each morning, and sell them to customers throughout the day. Excess stock is sold to a wholesaler at closing at a discount.

The simulation models the classic single-period newsvendor problem under uncertain demand, comparing chosen batch sizes against optimal benchmarks.

---

## Live Demo & Deployment

This project is configured for deployment on **Vercel** using Vercel's zero-configuration Django support.

### Deploying to Vercel

1. Push this repository to GitHub, GitLab, or Bitbucket.
2. In the [Vercel Dashboard](https://vercel.com), select **Add New...** -> **Project** and import the repository.
3. In **Environment Variables**, configure:
   - `DJANGO_SECRET_KEY`: A cryptographically secure random string.
   - `DJANGO_DEBUG`: `False`
   - `DJANGO_ALLOWED_HOSTS`: `.vercel.app` (or your production domain)
4. Click **Deploy**. Vercel detects `manage.py`, builds static files into `STATIC_ROOT`, and serves the application via serverless WSGI functions.

---

## Local Setup

### Prerequisites

- Python 3.10, 3.11, or 3.12

### Installation

1. Clone or extract the repository:
   ```bash
   cd raid_shop_submission
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Offline note: `vendor/` contains pre-downloaded wheels that can be installed without an internet connection using `pip install --no-index --find-links vendor -r requirements.txt`).*

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Modify `.env` if needed (defaults work out of the box for local development).

5. Start the development server:
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser. No database migrations, user accounts, or Node builds are required.

---

## Testing & CLI Simulation

### Automated Test Suite

Run the 31 automated unit and web tests:
```bash
python manage.py test -v 2
```

### Standalone CLI Engine

Run the simulation directly from the terminal without the web interface:
```bash
# Baseline run using config.json defaults
python simulate.py

# Custom selling price
python simulate.py --price 80 --out price80_results

# Wider inventory comparison range
python simulate.py --stock-min 0 --stock-max 500 --stock-step 10 --out wider_range_results
```

---

## How the Model Works

Each day is an independent, single-period inventory challenge.

### Economic Parameters (Default)

| Parameter | Value | Description |
| :--- | :--- | :--- |
| **Unit Cost** | 30 gold | Cost to brew one potion (kit + bottle). |
| **Selling Price** | 50 gold | Price paid by retail NPC customers. |
| **Salvage Value** | 10 gold | Clearance price paid by the wholesaler at closing for unsold potions. |
| **Step / Bundle Size** | 10 potions | Batch resolution for inventory choices. |

### Objective Functions

1. **Textbook Score**:
   $$\text{Cash Profit} - (\text{Selling Price} - \text{Unit Cost}) \times \text{Unmet Demand}$$
   Penalizes missed customer demand by subtracting the foregone margin. The theoretical and simulated winner under default settings is **70 potions** (expected score: 931.00 gold; simulated: 928.59 gold).

2. **Cash Profit**:
   $$\text{Revenue} - \text{Purchase Cost} + \text{Salvage Recovery}$$
   Measures raw net gold earned without opportunity cost penalties. The winner under default settings is **60 potions**.

---

## Repository Structure

```text
├── config.json            # Baseline economic values and demand probability distributions
├── manage.py              # Django management script
├── potionshop/            # Django project settings, routes, and WSGI configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── pyproject.toml         # Python project metadata and Vercel entrypoint declaration
├── requirements.txt       # Production dependencies (Django 5.2.18)
├── results/               # Baseline simulation data, CSV traces, and SHA256 checksums
├── simulate.py            # Standalone Monte Carlo simulation engine
├── simulator/             # Django application
│   ├── configuration.py   # Shared config parser and validation rules
│   ├── forms.py           # Web forms for interactive input validation
│   ├── static/simulator/  # Vanilla CSS and JS loading state
│   ├── templates/         # DTL templates and evidence tables
│   ├── tests.py           # Web test suite
│   └── views.py           # View handling simulation runs, pagination, and tables
├── test_simulation.py     # Engine unit tests
├── vendor/                # Bundled wheels for offline installation
└── verification/          # Output verification logs and console outputs
```
