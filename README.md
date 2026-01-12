# Coffee soil cation-balance analysis (ANOVA + Tukey)

This repository contains the reproducible code used to analyse the field experiment reported in:
"Mineral and organo-mineral fertilisation alters soil Ca–Mg–K balance and base saturation during early coffee establishment".

## What this code does
- Runs factorial ANOVA (3 × 4) with randomized complete blocks.
- Runs Tukey HSD post-hoc tests within each planting fertiliser source across organic rates.
- Exports results to an Excel file used to populate Tables 4–7.

## Input data
This code expects the file:
- `plot_level_data_90d.csv`

The dataset is openly available on Zenodo:
https://doi.org/10.5281/zenodo.18200463

Download `plot_level_data_90d.csv` from Zenodo and place it in the same directory as the script.

## How to run
### 1) Create a virtual environment (recommended)
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run the analysis
```bash
python statistical_analysis_reproducible_from_csv.py
```

## Outputs
The script generates:
- `supplementary_statistical_analysis_outputs.xlsx`

Sheets include:
- `Table4_ANOVA` (p-values and CV)
- `Table7_Tukey_letters` (compact letter display for Tukey groupings)
- `Tukey_pairwise_pvalues` (full Tukey pairwise results)
- `plot_level_data_90d` (input dataset)

## Licence
MIT License (see `LICENSE`).
