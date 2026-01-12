"""Reproducible statistical analysis for the coffee soil-chemistry experiment.

This script reproduces the factorial ANOVA and Tukey HSD post-hoc tests reported in the manuscript.

Input (underlying data):
  - plot_level_data_90d.csv
    Plot-level dataset at 90 days after transplanting (0–20 cm), n=48 (12 treatments × 4 blocks).

Outputs:
  - supplementary_statistical_analysis_outputs.xlsx
    Includes ANOVA results and Tukey HSD outputs.

Requirements:
  Python 3.9+ with pandas, numpy, statsmodels, openpyxl.

Usage:
  python statistical_analysis_reproducible_from_csv.py
"""

import math
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import MultiComparison
from string import ascii_lowercase

INPUT_CSV = "plot_level_data_90d.csv"
OUTPUT_XLSX = "supplementary_statistical_analysis_outputs.xlsx"

INDICATORS = [
    "Ca/Mg", "Ca/K", "Mg/K", "Ca+Mg/K",
    "Ca/T (%)", "Mg/T (%)", "K/T (%)",
    "H+Al/T (%)", "Ca+Mg/T (%)", "V (%)"
]

def sig_code(p: float) -> str:
    if p <= 0.01:
        return "**"
    if p <= 0.05:
        return "*"
    return "ns"

def cld_from_tukey(rate_levels, means_dict, reject_pairs):
    """Greedy compact letter display for Tukey groupings."""
    sorted_rates = sorted(rate_levels, key=lambda r: means_dict[r], reverse=True)
    letter_sets = []
    letters_map = {r: "" for r in rate_levels}

    for r in sorted_rates:
        placed = False
        for i, s in enumerate(letter_sets):
            ok = True
            for rr in s:
                key = (r, rr) if (r, rr) in reject_pairs else (rr, r)
                if reject_pairs.get(key, False):
                    ok = False
                    break
            if ok:
                s.add(r)
                letters_map[r] += ascii_lowercase[i]
                placed = True
        if not placed:
            letter_sets.append({r})
            letters_map[r] += ascii_lowercase[len(letter_sets) - 1]

    # Second pass: add extra letters when possible
    for i, s in enumerate(letter_sets):
        letter = ascii_lowercase[i]
        for r in rate_levels:
            if letter in letters_map[r]:
                continue
            ok = True
            for rr in s:
                key = (r, rr) if (r, rr) in reject_pairs else (rr, r)
                if reject_pairs.get(key, False):
                    ok = False
                    break
            if ok:
                letters_map[r] += letter

    for r in rate_levels:
        letters_map[r] = "".join(sorted(set(letters_map[r]), key=lambda x: ascii_lowercase.index(x)))
    return letters_map

def main():
    df = pd.read_csv(INPUT_CSV)

    df["Source"] = pd.Categorical(df["Source"], categories=["OM-CF", "OM-TF", "MIN"], ordered=True)
    df["Rate"] = pd.Categorical(df["Rate"], categories=[2, 4, 6, 8], ordered=True)
    df["Block"] = pd.Categorical(df["Block"], categories=[1, 2, 3, 4], ordered=True)

    # ANOVA (Type II) + CV
    anova_rows = []
    for var in INDICATORS:
        d = df[["Block", "Source", "Rate", var]].copy()
        d[var] = pd.to_numeric(d[var], errors="coerce")
        d = d.dropna(subset=[var])

        model = smf.ols(f'Q("{var}") ~ C(Block) + C(Source)*C(Rate)', data=d).fit()
        aov = anova_lm(model, typ=2)

        p_source = float(aov.loc["C(Source)", "PR(>F)"])
        p_rate = float(aov.loc["C(Rate)", "PR(>F)"])
        p_inter = float(aov.loc["C(Source):C(Rate)", "PR(>F)"])

        mse = float(aov.loc["Residual", "sum_sq"] / aov.loc["Residual", "df"])
        mean = float(d[var].mean())
        cv = 100 * math.sqrt(mse) / mean if mean else np.nan

        anova_rows.append({
            "Indicator": var,
            "p(Source)": p_source, "Sig Source": sig_code(p_source),
            "p(Rate)": p_rate, "Sig Rate": sig_code(p_rate),
            "p(Source×Rate)": p_inter, "Sig Source×Rate": sig_code(p_inter),
            "CV (%)": cv
        })

    anova_df = pd.DataFrame(anova_rows)

    # Tukey within each Source across rates
    tukey_letters = []
    tukey_pairwise = []

    for var in INDICATORS:
        for src in ["OM-CF", "OM-TF", "MIN"]:
            sub = df[df["Source"] == src].copy()
            sub[var] = pd.to_numeric(sub[var], errors="coerce")
            sub = sub.dropna(subset=[var])

            mc = MultiComparison(sub[var], sub["Rate"])
            tuk = mc.tukeyhsd(alpha=0.05)

            # Pairwise table
            summ = pd.DataFrame(tuk.summary().data[1:], columns=tuk.summary().data[0])
            summ["Indicator"] = var
            summ["Source"] = src
            tukey_pairwise.append(summ)

            # Letters
            reject_pairs = {}
            for i, j, rej in zip(tuk._multicomp.pairindices[0], tuk._multicomp.pairindices[1], tuk.reject):
                g1 = int(tuk.groupsunique[i])
                g2 = int(tuk.groupsunique[j])
                reject_pairs[(g1, g2)] = bool(rej)

            means_dict = {r: float(sub[sub["Rate"] == r][var].mean()) for r in [2, 4, 6, 8]}
            letters = cld_from_tukey([2, 4, 6, 8], means_dict, reject_pairs)

            for r in [2, 4, 6, 8]:
                tukey_letters.append({
                    "Indicator": var,
                    "Rate (t ha−1)": r,
                    "Source": src,
                    "Letter": letters[r]
                })

    tukey_letters_df = pd.DataFrame(tukey_letters)
    tukey_pairwise_df = pd.concat(tukey_pairwise, ignore_index=True)

    table7 = (tukey_letters_df
              .pivot_table(index=["Indicator", "Rate (t ha−1)"], columns="Source", values="Letter", aggfunc="first")
              .reset_index()
              .rename(columns={"OM-CF": "OMF-CF", "OM-TF": "OMF-TF", "MIN": "MIN"}))

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="plot_level_data_90d")
        anova_df.to_excel(writer, index=False, sheet_name="Table4_ANOVA")
        table7.to_excel(writer, index=False, sheet_name="Table7_Tukey_letters")
        tukey_pairwise_df.to_excel(writer, index=False, sheet_name="Tukey_pairwise_pvalues")

    print("Done. Outputs written to:", OUTPUT_XLSX)

if __name__ == "__main__":
    main()
