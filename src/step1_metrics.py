"""Step 1 & Q4 (General Sector Description + Patents vs Secrecy) indicator functions.

All indicator functions operate on clean pandas DataFrames so they are:
  - 100% decoupled from PATSTAT SQL queries,
  - unit-tested on toy datasets with known exact answers (PW Slide 18 requirement),
  - directly reusable in both TIP notebooks and standalone reproducible scripts.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from src.config_loader import get_cpc_subclass_definition


# ------------------------------------------------------------------ Truncation & Growth (Q1)
def flag_truncated_years(
    df: pd.DataFrame,
    last_complete_year: int,
    year_col: str = "year",
) -> pd.DataFrame:
    """Add boolean column 'is_truncated' flagging incomplete recent priority/filing years."""
    out = df.copy()
    out["is_truncated"] = out[year_col] > int(last_complete_year)
    return out


def compute_growth_summary(
    volume_df: pd.DataFrame,
    sector_name: str,
    year_min: int,
    last_complete_year: int,
    benchmark_name: str = "all patents",
    levels: Sequence[str] = ("family", "application"),
) -> pd.DataFrame:
    """Compare sector vs benchmark (all patents) growth (%) and CAGR (%) over complete years.

    Parameters
    ----------
    volume_df : DataFrame with columns ['scope', 'level', 'series', 'year', 'n']
    """
    complete = volume_df[
        (volume_df["series"] == "all")
        & (volume_df["year"].between(year_min, last_complete_year))
    ]
    n_years = last_complete_year - year_min
    if n_years <= 0:
        raise ValueError("last_complete_year must exceed year_min")

    rows = []
    for lvl in levels:
        for scope_name in (benchmark_name, sector_name):
            sub = (
                complete[(complete["level"] == lvl) & (complete["scope"] == scope_name)]
                .set_index("year")["n"]
                .sort_index()
            )
            eff_start = year_min if year_min in sub.index and sub.get(year_min, 0) > 0 else (int(sub[sub > 0].index.min()) if not sub[sub > 0].empty else year_min)
            eff_end = last_complete_year if last_complete_year in sub.index else (int(sub.index.max()) if not sub.empty else last_complete_year)
            eff_years = max(eff_end - eff_start, 1)
            c_start = float(sub.get(eff_start, np.nan))
            c_end = float(sub.get(eff_end, np.nan))
            total_complete = float(sub.sum())
            peak_year = int(sub.idxmax()) if not sub.empty else None
            peak_val = float(sub.max()) if not sub.empty else np.nan
            growth_pct = ((c_end / c_start) - 1.0) * 100.0 if c_start and c_start > 0 else np.nan
            cagr_pct = (
                ((c_end / c_start) ** (1.0 / eff_years) - 1.0) * 100.0
                if c_start and c_start > 0 and c_end > 0
                else np.nan
            )
            rows.append(
                {
                    "level": lvl,
                    "scope": scope_name,
                    f"count_{year_min}": c_start,
                    f"count_{last_complete_year}": c_end,
                    "total_complete_window": total_complete,
                    "peak_complete_year": peak_year,
                    "peak_complete_count": peak_val,
                    f"growth_{year_min}_{last_complete_year}_pct": growth_pct,
                    f"cagr_{year_min}_{last_complete_year}_pct": cagr_pct,
                }
            )

    summary = pd.DataFrame(rows).set_index(["level", "scope"])
    return summary


def compute_sector_share_of_all_patents(
    volume_df: pd.DataFrame,
    sector_name: str,
    last_complete_year: int,
    benchmark_name: str = "all patents",
) -> pd.DataFrame:
    """Compute annual sector share (%) and basis points of global patents across complete years."""
    sub = volume_df[
        (volume_df["series"] == "all") & (volume_df["year"] <= last_complete_year)
    ]
    piv = sub.pivot_table(index=["level", "year"], columns="scope", values="n", aggfunc="sum")
    if sector_name not in piv.columns or benchmark_name not in piv.columns:
        raise ValueError(f"Expected scopes {sector_name!r} and {benchmark_name!r} in volume_df")
    out = piv[[sector_name, benchmark_name]].copy()
    out["sector_share_pct"] = (out[sector_name] / out[benchmark_name]) * 100.0
    out["sector_share_bps"] = out["sector_share_pct"] * 100.0
    return out.reset_index()


# ------------------------------------------------------------------ Fractional Counting (Q2 & Q3)
def compute_fractional_counts(
    pairs_df: pd.DataFrame,
    unit_col: str = "unit_id",
    category_col: str = "category",
    year_col: str = "year",
) -> pd.DataFrame:
    """Compute exact fractional counts where each distinct unit splits 1.0 equally across its categories.

    Example: a family classified in 4 distinct CPC subclasses contributes 0.25 to each subclass,
    guaranteeing that fractional counts across all categories sum exactly to the unit count.
    """
    dedup = pairs_df[[unit_col, category_col, year_col]].dropna().drop_duplicates()
    if dedup.empty:
        return pd.DataFrame(columns=[category_col, year_col, "n_frac"])
    k = dedup.groupby(unit_col)[category_col].transform("nunique")
    dedup = dedup.assign(weight=1.0 / k)
    return (
        dedup.groupby([category_col, year_col], as_index=False)["weight"]
        .sum()
        .rename(columns={"weight": "n_frac"})
    )


def pool_top_categories(
    df: pd.DataFrame,
    category_col: str,
    last_complete_year: int,
    top_n: int = 8,
    value_col: str = "n_frac",
    year_col: str = "year",
    other_label: str = "Other",
) -> pd.DataFrame:
    """Keep top N categories over complete years and pool all remaining categories into 'Other'."""
    complete = df[df[year_col] <= last_complete_year]
    top_cats = (
        complete.groupby(category_col)[value_col].sum().nlargest(top_n).index
    )
    out = df.copy()
    out[category_col] = out[category_col].where(out[category_col].isin(top_cats), other_label)
    return out.groupby([category_col, year_col], as_index=False)[value_col].sum()


def compute_share_table(counts_df: pd.DataFrame, other_label: str = "Other") -> pd.DataFrame:
    """Convert raw count table (rows = categories, cols = levels/roles) into 100%-normalized shares."""
    totals = counts_df.sum(axis=0).replace(0, np.nan)
    shares = counts_df.div(totals, axis=1) * 100.0
    sort_col = shares.columns[0]
    order = [c for c in shares.sort_values(sort_col, ascending=False).index if c != other_label]
    if other_label in shares.index:
        order.append(other_label)
    shares = shares.loc[order].copy()
    shares.loc["Total"] = shares.sum(axis=0)
    return shares


def compute_period_mix_shift(
    pooled_df: pd.DataFrame,
    category_col: str,
    early_window: Tuple[int, int],
    recent_window: Tuple[int, int],
    value_col: str = "n_frac",
    year_col: str = "year",
    cfg: Optional[Dict[str, Any]] = None,
    attach_cpc_definitions: bool = False,
) -> pd.DataFrame:
    """Quantify how the technology/geography share mix shifted between an early and recent period."""
    early = (
        pooled_df[pooled_df[year_col].between(*early_window)]
        .groupby(category_col)[value_col]
        .sum()
    )
    recent = (
        pooled_df[pooled_df[year_col].between(*recent_window)]
        .groupby(category_col)[value_col]
        .sum()
    )
    tbl = pd.DataFrame(
        {
            f"count_{early_window[0]}_{early_window[1]}": early,
            f"count_{recent_window[0]}_{recent_window[1]}": recent,
        }
    ).fillna(0.0)
    e_sum = tbl.iloc[:, 0].sum()
    r_sum = tbl.iloc[:, 1].sum()
    tbl[f"share_{early_window[0]}_{early_window[1]}_pct"] = (
        tbl.iloc[:, 0] / e_sum * 100.0 if e_sum > 0 else np.nan
    )
    tbl[f"share_{recent_window[0]}_{recent_window[1]}_pct"] = (
        tbl.iloc[:, 1] / r_sum * 100.0 if r_sum > 0 else np.nan
    )
    tbl["shift_pp"] = tbl.iloc[:, 3] - tbl.iloc[:, 2]
    tbl = tbl.sort_values(tbl.columns[3], ascending=False)
    if attach_cpc_definitions and cfg is not None:
        tbl["official_cpc_definition"] = [
            get_cpc_subclass_definition(cat, cfg) for cat in tbl.index
        ]
    return tbl


# ------------------------------------------------------------------ Geography (Q3)
def compute_applicant_inventor_gap(country_shares_df: pd.DataFrame) -> pd.DataFrame:
    """Compute Applicant share minus Inventor share (pp) at family level.

    Positive gap (>0) indicates net technology ownership inflow (foreign R&D or acquisitions);
    Negative gap (<0) indicates net R&D export (local inventors filing for foreign corporate owners).
    """
    if ("family", "applicant") not in country_shares_df.columns or (
        "family",
        "inventor",
    ) not in country_shares_df.columns:
        raise ValueError(
            "Expected MultiIndex columns ('family', 'applicant') and ('family', 'inventor')"
        )
    out = pd.DataFrame(
        {
            "applicant_share_pct": country_shares_df[("family", "applicant")],
            "inventor_share_pct": country_shares_df[("family", "inventor")],
        }
    )
    if "Total" in out.index:
        out = out.drop(index="Total")
    out["ownership_minus_rd_pp"] = out["applicant_share_pct"] - out["inventor_share_pct"]
    return out.sort_values("applicant_share_pct", ascending=False)


# ------------------------------------------------------------------ Q4: Patents vs Secrecy
def classify_uav_use_segment(
    family_cpc_df: pd.DataFrame,
    all_uav_family_ids: Iterable[int],
    military_prefixes: Sequence[str],
    dual_use_prefixes: Sequence[str],
    family_col: str = "docdb_family_id",
    cpc_col: str = "cpc_class_symbol",
) -> pd.DataFrame:
    """Assign each UAV DOCDB family to exactly one mutually exclusive use segment.

    Priority order:
      1. 'military' (warfare B64U2101/15-19 or weapons/missiles F41, F42B10/12/15)
      2. 'dual_use' (surveillance/ISR B64U2101/31, excluding military)
      3. 'civil_and_other' (all remaining UAV families)
    """
    all_ids = sorted(set(int(x) for x in all_uav_family_ids))
    clean = family_cpc_df[[family_col, cpc_col]].dropna().copy()
    clean["sym"] = clean[cpc_col].astype(str).str.replace(" ", "", regex=False).str.upper()

    mil_clean = tuple(p.replace(" ", "").upper() for p in military_prefixes)
    dual_clean = tuple(p.replace(" ", "").upper() for p in dual_use_prefixes)

    mil_ids = set(
        clean.loc[clean["sym"].str.startswith(mil_clean), family_col].astype(int).tolist()
    )
    dual_ids = (
        set(clean.loc[clean["sym"].str.startswith(dual_clean), family_col].astype(int).tolist())
        - mil_ids
    )

    records = []
    for fid in all_ids:
        if fid in mil_ids:
            seg = "military"
        elif fid in dual_ids:
            seg = "dual_use"
        else:
            seg = "civil_and_other"
        records.append({family_col: fid, "segment": seg})
    return pd.DataFrame(records)


def summarize_patenting_intensity(
    profiles_df: pd.DataFrame,
    group_col: str = "group",
) -> pd.DataFrame:
    """Summarize patenting intensity & international breadth indicators per group/benchmark.

    Expected columns in profiles_df (one row per DOCDB family in complete years):
      ['group', 'fid', 'year', 'family_size', 'n_offices', 'n_ip5', 'is_pct', 'is_granted']
    """
    rows = []
    for grp_name, g in profiles_df.groupby(group_col, sort=False):
        n = len(g)
        rows.append(
            {
                "group": grp_name,
                "families": int(n),
                "mean_family_size": float(g["family_size"].mean()) if n else np.nan,
                "median_family_size": float(g["family_size"].median()) if n else np.nan,
                "mean_offices": float(g["n_offices"].mean()) if n else np.nan,
                "pct_share_pct": float(g["is_pct"].mean() * 100.0) if n else np.nan,
                "multi_ip5_share_pct": float((g["n_ip5"] >= 2).mean() * 100.0) if n else np.nan,
                "single_office_share_pct": float((g["n_offices"] <= 1).mean() * 100.0) if n else np.nan,
                "grant_rate_pct": float(g["is_granted"].mean() * 100.0) if n else np.nan,
            }
        )
    return pd.DataFrame(rows).set_index("group")


def build_q4_interpretation_paragraph(
    intensity_df: pd.DataFrame,
    segment_counts: Dict[str, int],
    prime_vs_dji_df: Optional[pd.DataFrame] = None,
) -> str:
    """Generate a data-grounded English interpretation paragraph for Deck Step 1 (Q4).

    Never fabricates numbers: every statistic is pulled directly from PROD DataFrames.
    """
    total_uav = sum(segment_counts.values())
    mil_n = segment_counts.get("military", 0)
    dual_n = segment_counts.get("dual_use", 0)
    civ_n = segment_counts.get("civil_and_other", 0)
    mil_pct = (mil_n / total_uav * 100.0) if total_uav else 0.0
    dual_pct = (dual_n / total_uav * 100.0) if total_uav else 0.0
    civ_pct = (civ_n / total_uav * 100.0) if total_uav else 0.0

    lines = [
        "Appropriability & Patents vs. Secrecy (Data-Grounded Interpretation):",
        f"- Bifurcated appropriability regime across {total_uav:,} complete-window UAV DOCDB families: "
        f"Civil/Commercial accounts for {civ_pct:.1f}% ({civ_n:,}), Dual-Use ISR/Surveillance for "
        f"{dual_pct:.1f}% ({dual_n:,}), and explicit Military/Warfare for only {mil_pct:.1f}% ({mil_n:,}).",
    ]
    if "All flying drones" in intensity_df.index:
        u = intensity_df.loc["All flying drones"]
        lines.append(
            f"- Overall UAV patenting exhibits a mean family size of {u['mean_family_size']:.2f}, "
            f"{u['pct_share_pct']:.1f}% PCT usage, {u['multi_ip5_share_pct']:.1f}% >=2 IP5 coverage, "
            f"and {u['single_office_share_pct']:.1f}% single-office filings."
        )
    civil_key = next(
        (k for k in ("Civil & commercial drones", "Civil drones") if k in intensity_df.index),
        None,
    )
    if "Military drones" in intensity_df.index and civil_key is not None:
        m = intensity_df.loc["Military drones"]
        c = intensity_df.loc[civil_key]
        lines.append(
            f"- Military vs. Civil contrast: Military UAV families show {m['pct_share_pct']:.1f}% PCT share "
            f"and {m['multi_ip5_share_pct']:.1f}% >=2 IP5 coverage (vs. {c['pct_share_pct']:.1f}% PCT and "
            f"{c['multi_ip5_share_pct']:.1f}% >=2 IP5 in Civil drones), consistent with national-security "
            "secrecy orders and export-control constraints limiting foreign filings (Acosta et al., 2018; "
            "Cohen, Nelson & Walsh, 2000; Arundel, 2001)."
        )
    if prime_vs_dji_df is not None and not prime_vs_dji_df.empty and "families" in prime_vs_dji_df.columns:
        top3 = prime_vs_dji_df.sort_values("families", ascending=False).head(3)
        summary_str = ", ".join(f"{idx} ({int(r['families']):,})" for idx, r in top3.iterrows())
        lines.append(f"- Top corporate filers among tracked primes & commercial leaders: {summary_str}.")
    lines.append(
        "- Strategic takeaway for Leonardo S.p.A.: Civil and dual-use UAV segments are patent-intensive "
        "(driven by rapid commercial diffusion, platform competition, and cross-licensing), whereas core "
        "military payload/EW/stealth capabilities rely heavily on secrecy and lead-time (Teece, 1986). "
        "Consequently, PATSTAT provides high visibility into commercial/dual-use acquisition targets, "
        "while pure-defence capabilities are structurally under-represented in public patent counts."
    )
    return "\n".join(lines)
