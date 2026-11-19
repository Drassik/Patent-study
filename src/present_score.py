"""Step 3: Present Value Score of Top Firms (Clarivate 4 Dimensions · Tutorial 40).

Implements the exact four present-value indicators and combination/robustness framework
taught in Innovation Management Tutorial 40 (Prof. Grazia Sveva Ascione):
  1. Volume        — Firm's share of sector DOCDB families in the scoring window (Ernst, 1998)
  2. Influence     — 5-year forward citations normalized by priority-year cohort mean
                     (Hall, Jaffe & Trajtenberg, 2001, 2005) + optional X/I blocking share
  3. Success       — Grant rate excluding PCT ('WO') and EP translations (kind 'T')
                     (Guellec & van Pottelsberghe, 2000)
  4. Globalization — Mean distinct national offices per family + optional Clarivate
                     quadrilateral share ({CN, EP, JP, US}) (Harhoff, Scherer & Vopel, 2003)

Combination methods:
  - 'mean': Weighted ratio-to-the-mean score (100 = average scored firm)
  - 'rrf' : Weighted Reciprocal Rank Fusion (Cormack et al., 2009; 100 = 1st on all metrics)
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


CORE_INDICATORS = ("volume", "influence", "success", "globalization")
DEFAULT_UAV_PRESENT_WEIGHTS: Dict[str, float] = {
    "influence": 0.35,
    "globalization": 0.25,
    "success": 0.20,
    "volume": 0.20,
}
QUADRILATERAL_OFFICES = frozenset({"CN", "EP", "JP", "US"})


def compute_family_forward_citations_norm(
    families_df: pd.DataFrame,
    citations_df: pd.DataFrame,
    window_years: int = 5,
    last_citation_year: int = 2025,
    cohort_cols: Sequence[str] = ("priority_year",),
) -> pd.Series:
    """Compute cohort-normalized forward citations within `window_years` of first publication.

    Parameters
    ----------
    families_df : DataFrame with ['docdb_family_id', 'priority_year', 'first_publn_year']
                  (+ optional 'cpc4' if cohort_cols includes 'cpc4')
    citations_df : DataFrame with ['citing_family', 'cited_family', 'citing_year']
    """
    fams = families_df.drop_duplicates("docdb_family_id").copy()
    pub_map = fams.set_index("docdb_family_id")["first_publn_year"]

    if citations_df.empty:
        raw_counts = pd.Series(dtype=float)
    else:
        fcit = citations_df[citations_df["citing_family"] != citations_df["cited_family"]].copy()
        fcit["cited_year"] = fcit["cited_family"].map(pub_map)
        fcit["lag"] = fcit["citing_year"] - fcit["cited_year"]
        raw_counts = (
            fcit[fcit["lag"].between(0, window_years)]
            .groupby("cited_family")["citing_family"]
            .nunique()
        )

    fwd = fams["docdb_family_id"].map(raw_counts).fillna(0.0)
    complete_mask = (fams["first_publn_year"] + window_years) <= last_citation_year
    fwd = fwd.where(complete_mask)

    group_keys = [fams[col] for col in cohort_cols]
    cohort_mean = fwd.groupby(group_keys).transform("mean")
    norm = (fwd / cohort_mean).where(cohort_mean > 0, 0.0).where(fwd.notna())
    norm.index = fams["docdb_family_id"].values
    return norm.rename(f"fwd{window_years}_norm")


def compute_present_indicators_per_firm(
    families_df: pd.DataFrame,
    fam_firm_df: pd.DataFrame,
    applications_df: pd.DataFrame,
    citations_df: pd.DataFrame,
    min_families: int = 10,
    top_n_firms: int = 20,
    citation_window_years: int = 5,
    last_citation_year: int = 2025,
    cohort_cols: Sequence[str] = ("priority_year",),
) -> pd.DataFrame:
    """Compute Volume, Influence, Success, Globalization (+ Quadrilateral share) per scored firm.

    Parameters
    ----------
    families_df     : ['docdb_family_id', 'priority_year', 'first_publn_year', ...]
    fam_firm_df     : ['docdb_family_id', 'firm'] (harmonized applicant names, companies only)
    applications_df : ['appln_id', 'docdb_family_id', 'appln_auth', 'appln_kind', 'granted']
    citations_df    : ['citing_family', 'cited_family', 'citing_year']
    """
    fams = families_df.drop_duplicates("docdb_family_id").copy()
    total_sector_families = len(fams)
    if total_sector_families == 0:
        raise ValueError("families_df is empty")

    # 1. Select firms passing the minimum portfolio gate
    ff = fam_firm_df[["docdb_family_id", "firm"]].drop_duplicates()
    ff = ff[ff["docdb_family_id"].isin(fams["docdb_family_id"])]
    firm_counts = ff.groupby("firm")["docdb_family_id"].nunique().sort_values(ascending=False)
    scored_firms = list(firm_counts[firm_counts >= min_families].head(top_n_firms).index)
    if not scored_firms:
        raise ValueError(f"No firms meet min_families={min_families}")

    # 2. Volume: share of all sector families in the scoring window
    volume = (firm_counts.reindex(scored_firms) / float(total_sector_families)).rename("volume")

    # 3. Influence: mean cohort-normalized forward citations
    fwd_norm = compute_family_forward_citations_norm(
        fams,
        citations_df,
        window_years=citation_window_years,
        last_citation_year=last_citation_year,
        cohort_cols=cohort_cols,
    )
    fams["fwd_norm"] = fams["docdb_family_id"].map(fwd_norm)
    ff_inf = ff[ff["firm"].isin(scored_firms)].merge(
        fams[["docdb_family_id", "fwd_norm"]], on="docdb_family_id", how="left"
    )
    influence = ff_inf.groupby("firm")["fwd_norm"].mean().reindex(scored_firms).rename("influence")

    # 4. National applications: exclude PCT ('WO') and EP translations (kind starting with 'T')
    apps = applications_df.drop_duplicates("appln_id").copy()
    apps = apps[apps["docdb_family_id"].isin(fams["docdb_family_id"])]
    kind_clean = apps["appln_kind"].fillna("").astype(str).str.strip().str.upper()
    national = apps[(apps["appln_auth"] != "WO") & (~kind_clean.str.startswith("T"))].copy()

    # Success: family-level mean grant rate across national offices (and application-level grant rate)
    fam_grant = national.groupby("docdb_family_id")["granted"].apply(lambda s: float((s == "Y").mean()))
    fams["fam_success"] = fams["docdb_family_id"].map(fam_grant)
    ff_suc = ff[ff["firm"].isin(scored_firms)].merge(
        fams[["docdb_family_id", "fam_success"]], on="docdb_family_id", how="left"
    )
    success = ff_suc.groupby("firm")["fam_success"].mean().reindex(scored_firms).rename("success")

    # 5. Globalization: mean distinct national offices per family + Clarivate quadrilateral share
    fam_offices = national.groupby("docdb_family_id")["appln_auth"].nunique()
    fam_quad = national.groupby("docdb_family_id")["appln_auth"].apply(
        lambda s: int(QUADRILATERAL_OFFICES.issubset(set(s)))
    )
    fams["n_offices"] = fams["docdb_family_id"].map(fam_offices).fillna(1.0)
    fams["quadrilateral"] = fams["docdb_family_id"].map(fam_quad).fillna(0).astype(int)

    ff_glob = ff[ff["firm"].isin(scored_firms)].merge(
        fams[["docdb_family_id", "n_offices", "quadrilateral"]], on="docdb_family_id", how="left"
    )
    globalization = ff_glob.groupby("firm")["n_offices"].mean().reindex(scored_firms).rename("globalization")
    quad_share = ff_glob.groupby("firm")["quadrilateral"].mean().reindex(scored_firms).rename("quadrilateral_share")

    result = pd.concat(
        [
            firm_counts.reindex(scored_firms).rename("families"),
            volume,
            influence,
            success,
            globalization,
            quad_share,
        ],
        axis=1,
    )
    result.index.name = "firm"
    return result


def combine_present_score(
    indicators_df: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
    method: str = "rrf",
    rrf_c: Optional[int] = None,
) -> pd.Series:
    """Combine firm-level indicators into a single Present Value Score (Tutorial 40 §8.5).

    Parameters
    ----------
    method :
      - 'mean' : 100 * sum_k w_k * (x_{f,k} / mean(x_k))   (100 = average scored firm)
      - 'rrf'  : 100 * sum_k w_k * (c + 1) / (c + rank_k)  (100 = 1st on every indicator)
    """
    w = pd.Series(weights if weights is not None else DEFAULT_UAV_PRESENT_WEIGHTS, dtype=float)
    w = w / w.sum()
    t = indicators_df[list(w.index)].astype(float)

    if method == "mean":
        means = t.mean(axis=0).replace(0.0, np.nan)
        return (100.0 * (t.div(means, axis=1) * w).sum(axis=1)).rename("present_score_mean")
    if method == "rrf":
        c = int(rrf_c) if rrf_c is not None else len(t)
        pos = t.rank(ascending=False, method="min")
        return (100.0 * (w * (c + 1.0) / (c + pos)).sum(axis=1)).rename("present_score_rrf")
    raise ValueError(f"Unknown combination method {method!r}; expected 'mean' or 'rrf'")


def rank_firms(scores: pd.Series) -> pd.Series:
    """Convert scores (higher = better) into integer ranks (1 = best)."""
    return scores.rank(ascending=False, method="min").astype(int)


def run_ranking_robustness_check(
    indicators_df: pd.DataFrame,
    base_weights: Optional[Dict[str, float]] = None,
    method: str = "rrf",
) -> Tuple[pd.DataFrame, pd.Series]:
    """Compare rankings across alternative weight schemes & leave-one-out checks (Tutorial 40 §9).

    Returns (ranks_by_scheme_df, spearman_corr_vs_base_series).
    """
    w_base = base_weights if base_weights is not None else DEFAULT_UAV_PRESENT_WEIGHTS
    cols = list(w_base.keys())
    schemes: Dict[str, Dict[str, float]] = {
        "base_uav_weights": w_base,
        "equal_weights": {k: 1.0 for k in cols},
        "size_first": {"influence": 0.15, "globalization": 0.25, "success": 0.20, "volume": 0.40},
        "impact_first": {"influence": 0.45, "globalization": 0.25, "success": 0.20, "volume": 0.10},
    }
    for k in cols:
        schemes[f"without_{k}"] = {j: 1.0 for j in cols if j != k}

    ranks = pd.DataFrame(
        {
            name: rank_firms(combine_present_score(indicators_df, w, method=method))
            for name, w in schemes.items()
        }
    )
    # Also include comparison against the alternative aggregation method (mean vs rrf)
    alt_method = "mean" if method == "rrf" else "rrf"
    ranks[f"alt_method_{alt_method}"] = rank_firms(
        combine_present_score(indicators_df, w_base, method=alt_method)
    )
    spearman = (
        ranks.corr(method="spearman")["base_uav_weights"]
        .drop(index="base_uav_weights")
        .rename("spearman_vs_base")
    )
    return ranks, spearman
