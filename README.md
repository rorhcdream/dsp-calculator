# DSP Calculator

Given a target material and target rate for production, it calculates:
* Target rates for recipe ingredients
* Required number of buildings to reach the target rates

This is mainly for calculating early game recipes because it shows all required materials recursively to Ore level, but you can also calculate in higher level by disabling some recipes in the `recipes.yaml`.

## Setup & Run

Requires Python 3.x

Install dependencies:
```bash
pip install -r requirements.txt
```

Run:
```bash
python main.py
```

## Note

Some recipes and some materials can be missing.
