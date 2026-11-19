"""Step 4: Future Value Score Algorithm & Temporal Back-Testing Harness (PW Slide 14).

Grants and forward citations do not exist yet for recent filings. This module implements
both the standard literature forward-looking baselines AND Team 28's composite UAV
forward-looking algorithm, together with a strict no-leakage temporal back-test
(freeze time at cutoff T, predict 5-year post-T realized impact, benchmark vs baselines).

Implemented indicators (all computable at filing/publication time without future data):
  1. Originality (Trajtenberg, Henderson & Jaffe, 1997):
       1 - sum_c s_c^2 over CPC subclasses of backward-cited families.
  2. Novel CPC Recombination (Fleming, 2001; Verhoeven, Bakker & Veugelers, 2016):
       Share of CPC subclass/group pairs co-occurring on a family that NEVER co-occurred
       in the sector strictly before its priority year.
  3. Cross-Layer Architectural Recombination (Team 28 UAV construct):
       Captures convergence across distinct UAV functional layers:
       Airframe (B64U/B64C) x Autonomy/Control (G05D) x Vision/Sensing (G06V/G06T/G01S/H04N)
       x Comms/UTM (G08G/H04W/H04B) x Energy/Docking (H01M/H02J/B64U50/70).
  4. Early Filing in Hot Subfields (Course construct, Tutorial Nov 9):
       Share of a firm's recent families entering CPC groups in the top quartile of
       trailing growth velocity (strictly computed using years <= T).
  5. Recent Filing Momentum & Early PCT Commitment:
       Firm's share of recent filings relative to historical baseline + early PCT rate.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


# Functional architecture layers of a Flying Drone system (for Cross-Layer Recombination)
UAV_FUNCTIONAL_LAYERS: Dict[str, Tuple[str, ...]] = {
    "airframe_propulsion": ("B64U", "B64C", "B64D", "B64F"),
    "autonomy_control": ("G05D", "G05B"),
    "perception_sensing": ("G06V", "G06T", "G01S", "G01C", "H04N"),
    "comms_utm_swarm": ("G08G", "H04W", "H04B", "H04L"),
    "energy_power": ("H01M", "H02J", "B60L"),
}


def compute_originality_per_family(
    backward_citations_df: pd.DataFrame,
    cited_family_cpc_df: pd.DataFrame,
) -> pd.Series:
    """Trajtenberg, Henderson & Jaffe (1997) Originality: 1 - sum(s_c^2) over cited CPC subclasses.

    Parameters
    ----------
    backward_citations_df : ['docdb_family_id', 'cited_docdb_family_id']
    cited_family_cpc_df   : ['cited_docdb_family_id', 'cpc_subclass']
    """
    if backward_citations_df.empty or cited_family_cpc_df.empty:
        return pd.Series(dtype=float, name="originality")

    merged = backward_citations_df[["docdb_family_id", "cited_docdb_family_id"]].merge(
        cited_family_cpc_df[["cited_docdb_family_id", "cpc_subclass"]].drop_duplicates(),
        on="cited_docdb_family_id",
        how="inner",
    )
    if merged.empty:
        return pd.Series(dtype=float, name="originality")

    counts = merged.groupby(["docdb_family_id", "cpc_subclass"]).size().rename("cnt").reset_index()
    counts["share"] = counts["cnt"] / counts.groupby("docdb_family_id")["cnt"].transform("sum")
    hhi = counts.assign(s2=counts["share"] ** 2).groupby("docdb_family_id")["s2"].sum()
    return (1.0 - hhi).rename("originality")


def compute_novel_recombination_per_family(
    family_cpc_df: pd.DataFrame,
    family_year_col: str = "priority_year",
    code_col: str = "cpc_group",
) -> pd.Series:
    """Fleming (2001) / Verhoeven et al. (2016) Novel CPC Recombination indicator.

    For each family filed in year t, computes the fraction of its unordered CPC pairs (a, b)
    that NEVER co-occurred in any sector family with priority_year < t (strictly causal).
    Families with fewer than 2 distinct codes receive 0.0.
    """
    df = family_cpc_df[["docdb_family_id", family_year_col, code_col]].dropna().drop_duplicates()
    if df.empty:
        return pd.Series(dtype=float, name="novel_recombination")

    fam_years = df.groupby("docdb_family_id")[family_year_col].min().sort_values()
    fam_codes = df.groupby("docdb_family_id")[code_col].apply(lambda s: sorted(set(s.astype(str))))

    seen_pairs: set[Tuple[str, str]] = set()
    scores: Dict[int, float] = {}

    # Process strictly year by year so same-year families cannot leak into each other
    for year, fids_in_year in fam_years.groupby(fam_years).groups.items():
        year_pairs: set[Tuple[str, str]] = set()
        for fid in fids_in_year:
            codes = fam_codes.get(fid, [])
            if len(codes) < 2:
                scores[int(fid)] = 0.0
                continue
            pairs = list(combinations(codes, 2))
            novel_cnt = sum(1 for p in pairs if p not in seen_pairs)
            scores[int(fid)] = novel_cnt / float(len(pairs))
            year_pairs.update(pairs)
        seen_pairs.update(year_pairs)

    return pd.Series(scores, name="novel_recombination")


def compute_cross_layer_architecture_score(
    family_cpc_df: pd.DataFrame,
    subclass_col: str = "cpc_subclass",
) -> pd.Series:
    """Team 28 UAV construct: fraction of distinct UAV functional layers bridged by a family.

    Rewards families integrating across distinct system layers (e.g. Airframe + Autonomy +
    Vision + Comms/UTM) rather than narrow single-layer incremental tweaks.
    """
    df = family_cpc_df[["docdb_family_id", subclass_col]].dropna().drop_duplicates().copy()
    if df.empty:
        return pd.Series(dtype=float, name="cross_layer_score")

    def _map_layer(code: str) -> Optional[str]:
        c = str(code).replace(" ", "").upper()[:4]
        for layer, prefixes in UAV_FUNCTIONAL_LAYERS.items():
            if any(c.startswith(p) for p in prefixes):
                return layer
        return None

    df["layer"] = df[subclass_col].map(_map_layer)
    n_layers = (
        df.dropna(subset=["layer"])
        .groupby("docdb_family_id")["layer"]
        .nunique()
    )
    # Normalize to [0, 1] where bridging >= 3 distinct layers = 1.0 (1 layer = 0.0)
    all_fids = df["docdb_family_id"].unique()
    raw = pd.Series(all_fids).map(n_layers).fillna(1.0)
    raw.index = all_fids
    score = ((raw - 1.0) / 2.0).clip(lower=0.0, upper=1.0)
    return score.rename("cross_layer_score")


def compute_hot_subfield_score(
    family_cpc_df: pd.DataFrame,
    cutoff_year: int,
    recent_span: int = 3,
    past_span: int = 3,
    family_year_col: str = "priority_year",
    group_col: str = "cpc_group",
) -> pd.Series:
    """Course construct: score each family in [cutoff_year - recent_span + 1, cutoff_year]
    by its exposure to CPC subfields in the top quartile of trailing growth (strictly <= cutoff_year).
    """
    df = family_cpc_df[["docdb_family_id", family_year_col, group_col]].dropna().drop_duplicates()
    if df.empty:
        return pd.Series(dtype=float, name="hot_subfield_score")

    rec_start = cutoff_year - recent_span + 1
    past_end = rec_start - 1
    past_start = past_end - past_span + 1

    recent_cnt = (
        df[df[family_year_col].between(rec_start, cutoff_year)]
        .groupby(group_col)["docdb_family_id"]
        .nunique()
    )
    past_cnt = (
        df[df[family_year_col].between(past_start, past_end)]
        .groupby(group_col)["docdb_family_id"]
        .nunique()
    )
    # Smoothed growth velocity (Laplace smoothing +1 avoids division by zero on emerging groups)
    all_groups = recent_cnt.index.union(past_cnt.index)
    velocity = (recent_cnt.reindex(all_groups, fill_value=0) + 1.0) / (
        past_cnt.reindex(all_groups, fill_value=0) + 1.0
    ) - 1.0

    # Percentile rank of each CPC group's trailing growth velocity in [0, 1]
    vel_pct = velocity.rank(pct=True)

    target = df[df[family_year_col].between(rec_start, cutoff_year)].copy()
    target["vel_pct"] = target[group_col].map(vel_pct).fillna(0.0)
    return target.groupby("docdb_family_id")["vel_pct"].max().rename("hot_subfield_score")


def compute_future_indicators_per_firm(
    families_df: pd.DataFrame,
    fam_firm_df: pd.DataFrame,
    family_cpc_df: pd.DataFrame,
    backward_citations_df: pd.DataFrame,
    cited_family_cpc_df: pd.DataFrame,
    cutoff_year: int,
    recent_window_years: int = 3,
    firms_to_score: Optional[Sequence[str]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """Compute firm-level Future Value indicators & composite score using ONLY data <= cutoff_year.

    Parameters
    ----------
    families_df : ['docdb_family_id', 'priority_year', 'is_pct'] (optional 'text_novelty')
    fam_firm_df : ['docdb_family_id', 'firm']
    family_cpc_df : ['docdb_family_id', 'priority_year', 'cpc_subclass', 'cpc_group']
    """
    # Strictly enforce causal cutoff_year to guarantee zero temporal leakage
    fams = families_df[families_df["priority_year"] <= cutoff_year].drop_duplicates("docdb_family_id").copy()
    cpc = family_cpc_df[family_cpc_df["priority_year"] <= cutoff_year].copy()
    rec_start = cutoff_year - recent_window_years + 1
    recent_fids = set(fams.loc[fams["priority_year"].between(rec_start, cutoff_year), "docdb_family_id"])

    orig = compute_originality_per_family(backward_citations_df, cited_family_cpc_df)
    recomb = compute_novel_recombination_per_family(cpc, family_year_col="priority_year", code_col="cpc_group")
    cross_layer = compute_cross_layer_architecture_score(cpc, subclass_col="cpc_subclass")
    hot_sub = compute_hot_subfield_score(cpc, cutoff_year=cutoff_year, recent_span=recent_window_years)

    fams["originality"] = fams["docdb_family_id"].map(orig).fillna(0.0)
    fams["novel_recombination"] = fams["docdb_family_id"].map(recomb).fillna(0.0)
    fams["cross_layer_score"] = fams["docdb_family_id"].map(cross_layer).fillna(0.0)
    fams["hot_subfield_score"] = fams["docdb_family_id"].map(hot_sub).fillna(0.0)
    if "is_pct" not in fams.columns:
        fams["is_pct"] = 0.0

    ff = fam_firm_df[["docdb_family_id", "firm"]].drop_duplicates()
    ff = ff[ff["docdb_family_id"].isin(fams["docdb_family_id"])]
    if firms_to_score is not None:
        ff = ff[ff["firm"].isin(firms_to_score)]

    ff_recent = ff[ff["docdb_family_id"].isin(recent_fids)].merge(
        fams[
            [
                "docdb_family_id",
                "originality",
                "novel_recombination",
                "cross_layer_score",
                "hot_subfield_score",
                "is_pct",
            ]
        ],
        on="docdb_family_id",
        how="left",
    )

    # Recent momentum: share of the firm's total <= cutoff_year portfolio filed in the recent window
    total_by_firm = ff.groupby("firm")["docdb_family_id"].nunique()
    recent_by_firm = ff_recent.groupby("firm")["docdb_family_id"].nunique()
    momentum = (recent_by_firm / total_by_firm.replace(0, np.nan)).fillna(0.0).rename("recent_momentum")

    agg = ff_recent.groupby("firm").agg(
        recent_families=("docdb_family_id", "nunique"),
        originality=("originality", "mean"),
        novel_recombination=("novel_recombination", "mean"),
        cross_layer_score=("cross_layer_score", "mean"),
        hot_subfield_score=("hot_subfield_score", "mean"),
        recent_pct_commitment=("is_pct", "mean"),
    )
    firm_index = list(firms_to_score) if firms_to_score is not None else sorted(total_by_firm.index)
    out = agg.reindex(firm_index).fillna(0.0)
    out["recent_families"] = out["recent_families"].astype(int)
    out["recent_momentum"] = momentum.reindex(firm_index).fillna(0.0)

    # Optional text-based novelty (Kelly et al. 2021 / Arts et al. 2021) if precomputed
    has_text = "text_novelty" in fams.columns
    if has_text:
        tn = (
            ff[ff["docdb_family_id"].isin(recent_fids)]
            .merge(fams[["docdb_family_id", "text_novelty"]], on="docdb_family_id", how="left")
            .groupby("firm")["text_novelty"]
            .mean()
        )
        out["text_novelty"] = tn.reindex(firm_index).fillna(0.0)

    # Normalize each component to [0, 100] via percentile/min-max across scored firms, then blend
    default_w = {
        "hot_subfield_score": 0.25,
        "novel_recombination": 0.20,
        "cross_layer_score": 0.20,
        "originality": 0.15,
        "recent_momentum": 0.10,
        "recent_pct_commitment": 0.10,
    }
    w = pd.Series(weights if weights is not None else default_w, dtype=float)
    w = w[[k for k in w.index if k in out.columns]]
    w = w / w.sum()

    scaled = pd.DataFrame(index=out.index)
    for col in w.index:
        s = out[col].astype(float)
        span = s.max() - s.min()
        scaled[col] = ((s - s.min()) / span * 100.0) if span > 0 else 50.0

    out["future_score"] = (scaled * w).sum(axis=1)
    out.index.name = "firm"
    return out


# ------------------------------------------------------------------ Temporal Back-Test (Slide 14)
def _ndcg_at_k(pred_scores: pd.Series, realized_values: pd.Series, k: int = 5) -> float:
    common = pred_scores.index.intersection(realized_values.index)
    if len(common) == 0:
        return np.nan
    k_eff = min(k, len(common))
    order = pred_scores.loc[common].sort_values(ascending=False).index[:k_eff]
    ideal = realized_values.loc[common].sort_values(ascending=False).index[:k_eff]
    discounts = 1.0 / np.log2(np.arange(2, k_eff + 2))
    rel_pred = np.maximum(realized_values.loc[order].to_numpy(dtype=float), 0.0)
    rel_ideal = np.maximum(realized_values.loc[ideal].to_numpy(dtype=float), 0.0)
    dcg = float(np.sum(rel_pred * discounts))
    idcg = float(np.sum(rel_ideal * discounts))
    return (dcg / idcg) if idcg > 0 else 0.0


def backtest_future_algorithms(
    firm_scores_at_T: pd.DataFrame,
    realized_post_T_outcome: pd.Series,
    candidate_columns: Sequence[str] = (
        "originality",
        "novel_recombination",
        "hot_subfield_score",
        "cross_layer_score",
        "future_score",
    ),
    top_k: int = 5,
) -> pd.DataFrame:
    """Evaluate Team 28's composite Future Score vs individual literature baselines at cutoff T.

    Metrics against realized post-T outcomes (e.g., 5-year post-T forward citations or family growth):
      - Spearman rank correlation (rho) & p-value
      - Precision@K (overlap between predicted top-K and realized top-K)
      - NDCG@K (graded ranking quality for top acquisition/partner picks)
    """
    common = firm_scores_at_T.index.intersection(realized_post_T_outcome.index)
    y_true = realized_post_T_outcome.loc[common].astype(float)
    k_eff = min(top_k, len(common))
    true_top_k = set(y_true.sort_values(ascending=False).index[:k_eff])

    rows = []
    for col in candidate_columns:
        if col not in firm_scores_at_T.columns:
            continue
        y_pred = firm_scores_at_T.loc[common, col].astype(float)
        if y_pred.nunique() < 2 or y_true.nunique() < 2:
            rho, pval = np.nan, np.nan
        else:
            res = spearmanr(y_pred, y_true)
            rho, pval = float(res.statistic), float(res.pvalue)
        pred_top_k = set(y_pred.sort_values(ascending=False).index[:k_eff])
        prec_at_k = len(pred_top_k & true_top_k) / float(k_eff) if k_eff > 0 else np.nan
        ndcg = _ndcg_at_k(y_pred, y_true, k=k_eff)
        rows.append(
            {
                "algorithm": col,
                "spearman_rho": rho,
                "p_value": pval,
                f"precision_at_{k_eff}": prec_at_k,
                f"ndcg_at_{k_eff}": ndcg,
            }
        )
    return pd.DataFrame(rows).set_index("algorithm").sort_values("spearman_rho", ascending=False)
