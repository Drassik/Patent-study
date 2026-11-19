#!/usr/bin/env python3
"""One-command reproducible pipeline from cleaned extracts (PW Slide 18 requirement).

Usage:
  1. Offline reproducibility smoke-test (synthetic UAV data):
       python3 run_all.py --demo
  2. Full reproduction from cleaned TIP extracts in data/processed/:
       python3 run_all.py --data-dir data/processed --output-dir outputs/final

Expected cleaned CSV extracts inside --data-dir (exported from TIP notebooks):
  - families.csv           : docdb_family_id, priority_year, first_publn_year, is_pct, is_granted, family_size
  - applications.csv       : appln_id, docdb_family_id, appln_auth, appln_kind, appln_filing_year, granted
  - family_cpc.csv         : docdb_family_id, priority_year, cpc_class_symbol, cpc_subclass, cpc_group
  - family_applicants.csv  : docdb_family_id, psn_name, psn_sector, ctry
  - citations.csv          : citing_family, cited_family, citing_year
  - backward_citations.csv : docdb_family_id, cited_docdb_family_id
  - cited_cpc.csv          : cited_docdb_family_id, cpc_subclass
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config_loader import get_last_complete_year, load_config
from src.future_score import backtest_future_algorithms, compute_future_indicators_per_firm
from src.harmonize import harmonize_applicant_names, six_concentration_measures
from src.present_score import (
    DEFAULT_UAV_PRESENT_WEIGHTS,
    combine_present_score,
    compute_present_indicators_per_firm,
    rank_firms,
    run_ranking_robustness_check,
)
from src.quadrant import (
    assign_magic_quadrant,
    compute_revealed_technological_advantage,
    plot_magic_quadrant,
)
from src.step1_metrics import (
    classify_uav_use_segment,
    compute_fractional_counts,
    compute_period_mix_shift,
    pool_top_categories,
)


def _generate_synthetic_uav_extracts(seed: int = 42) -> Dict[str, pd.DataFrame]:
    """Generate a compact synthetic UAV dataset so Slide 18 reproducibility works offline."""
    rng = np.random.default_rng(seed)
    firms_raw = [
        ("SZ DJI TECHNOLOGY CO., LTD.", "COMPANY", "CN", 45, 0.35, 0.72),
        ("DA-JIANG INNOVATIONS SCIENCE", "COMPANY", "CN", 25, 0.35, 0.72),
        ("BOEING COMPANY", "COMPANY", "US", 30, 0.65, 0.80),
        ("INSITU INC.", "COMPANY", "US", 10, 0.65, 0.80),
        ("LEONARDO S.P.A.", "COMPANY", "IT", 16, 0.60, 0.78),
        ("FINMECCANICA S.P.A.", "COMPANY", "IT", 8, 0.60, 0.78),
        ("AIRBUS DEFENCE AND SPACE", "COMPANY", "FR", 26, 0.70, 0.82),
        ("SKYDIO INC.", "COMPANY", "US", 18, 0.55, 0.75),
        ("AUTEL ROBOTICS CO., LTD.", "COMPANY", "CN", 22, 0.45, 0.70),
        ("PARROT DRONES SAS", "COMPANY", "FR", 20, 0.60, 0.74),
        ("GENERAL ATOMICS AERONAUTICAL", "COMPANY", "US", 18, 0.40, 0.85),
        ("LOCKHEED MARTIN CORP.", "COMPANY", "US", 22, 0.50, 0.82),
        ("ELBIT SYSTEMS LTD.", "COMPANY", "IL", 15, 0.45, 0.76),
    ]
    core_subclasses = ["B64U", "G05D", "G06V", "G08G", "H04W", "B64C", "H01M"]
    hot_groups = ["G08G5/59", "G06V20/17", "G05D1/00", "B64U50/19", "B64U10/14", "B64U2101/31", "B64U2101/15"]

    fam_rows, app_rows, cpc_rows, applt_rows = [], [], [], []
    fid = 1000
    aid = 50000

    for raw_name, sector, ctry, n_fams, pct_p, grant_p in firms_raw:
        is_visionary = raw_name in ("SKYDIO INC.", "AUTEL ROBOTICS CO., LTD.")
        for _ in range(n_fams):
            fid += 1
            yr = int(rng.integers(2017, 2023) if is_visionary else rng.integers(2010, 2023))
            pub_yr = yr + 1
            is_pct = int(rng.random() < pct_p)
            n_off = int(rng.choice([1, 2, 3, 4], p=[0.4, 0.25, 0.2, 0.15] if ctry == "CN" else [0.2, 0.25, 0.3, 0.25]))
            offices = rng.choice(["CN", "US", "EP", "JP", "KR"], size=n_off, replace=False)
            any_granted = 0
            for auth in offices:
                aid += 1
                g_flag = "Y" if rng.random() < grant_p else "N"
                any_granted = max(any_granted, int(g_flag == "Y"))
                app_rows.append(
                    {
                        "appln_id": aid,
                        "docdb_family_id": fid,
                        "appln_auth": str(auth),
                        "appln_kind": "A ",
                        "appln_filing_year": yr,
                        "granted": g_flag,
                    }
                )
            fam_rows.append(
                {
                    "docdb_family_id": fid,
                    "priority_year": yr,
                    "first_publn_year": pub_yr,
                    "is_pct": is_pct,
                    "is_granted": any_granted,
                    "family_size": n_off,
                }
            )
            applt_rows.append(
                {
                    "docdb_family_id": fid,
                    "psn_name": raw_name,
                    "psn_sector": sector,
                    "ctry": ctry,
                }
            )
            chosen_groups = rng.choice(hot_groups, size=int(rng.integers(2, 4)), replace=False)
            for grp in chosen_groups:
                cpc_rows.append(
                    {
                        "docdb_family_id": fid,
                        "priority_year": yr,
                        "cpc_class_symbol": str(grp),
                        "cpc_subclass": str(grp)[:4],
                        "cpc_group": str(grp),
                    }
                )

    fams_df = pd.DataFrame(fam_rows)
    # Generate forward & backward citations respecting causality (citing_year >= cited_year)
    cit_rows, back_rows, cited_cpc_rows = [], [], []
    all_fids = fams_df["docdb_family_id"].tolist()
    pub_by_fid = fams_df.set_index("docdb_family_id")["first_publn_year"].to_dict()
    for target_fid in all_fids:
        t_pub = pub_by_fid[target_fid]
        n_cit = int(rng.poisson(2.2))
        for _ in range(n_cit):
            citing = int(rng.choice(all_fids))
            if citing != target_fid and pub_by_fid[citing] >= t_pub:
                cit_rows.append(
                    {"citing_family": citing, "cited_family": target_fid, "citing_year": int(pub_by_fid[citing])}
                )
                back_rows.append({"docdb_family_id": citing, "cited_docdb_family_id": target_fid})
        for sc in rng.choice(core_subclasses, size=2, replace=False):
            cited_cpc_rows.append({"cited_docdb_family_id": target_fid, "cpc_subclass": str(sc)})

    return {
        "families": fams_df,
        "applications": pd.DataFrame(app_rows),
        "family_cpc": pd.DataFrame(cpc_rows),
        "family_applicants": pd.DataFrame(applt_rows),
        "citations": pd.DataFrame(cit_rows).drop_duplicates(),
        "backward_citations": pd.DataFrame(back_rows).drop_duplicates(),
        "cited_cpc": pd.DataFrame(cited_cpc_rows).drop_duplicates(),
    }


def _load_extracts_from_dir(data_dir: Path) -> Dict[str, pd.DataFrame]:
    names = [
        "families",
        "applications",
        "family_cpc",
        "family_applicants",
        "citations",
        "backward_citations",
        "cited_cpc",
    ]
    out = {}
    for name in names:
        p = data_dir / f"{name}.csv"
        if not p.exists():
            raise FileNotFoundError(
                f"Expected cleaned extract {p}. Export extracts from TIP or run with --demo."
            )
        out[name] = pd.read_csv(p)
    return out


def run_pipeline(
    extracts: Dict[str, pd.DataFrame],
    output_dir: Path,
    min_families: int = 10,
    present_window: Tuple[int, int] = (2010, 2019),
    future_cutoff: int = 2022,
    backtest_cutoff: int = 2017,
) -> None:
    cfg = load_config()
    last_complete = get_last_complete_year(cfg)
    output_dir.mkdir(parents=True, exist_ok=True)

    fams = extracts["families"]
    apps = extracts["applications"]
    cpc = extracts["family_cpc"]
    applts = extracts["family_applicants"]
    cits = extracts["citations"]
    back_cits = extracts["backward_citations"]
    cited_cpc = extracts["cited_cpc"]

    # Step 1: CPC fractional mix & period shift + Q4 segmentation
    frac_cpc = compute_fractional_counts(cpc, "docdb_family_id", "cpc_subclass", "priority_year").rename(
        columns={"priority_year": "year"}
    )
    pooled_cpc = pool_top_categories(frac_cpc, "cpc_subclass", last_complete, top_n=8)
    shift_df = compute_period_mix_shift(
        pooled_cpc,
        "cpc_subclass",
        (int(fams["priority_year"].min()), min(int(fams["priority_year"].min()) + 5, last_complete - 4)),
        (last_complete - 4, last_complete),
        cfg=cfg,
        attach_cpc_definitions=True,
    )
    shift_df.to_csv(output_dir / "step1_cpc_mix_shift.csv")

    seg_df = classify_uav_use_segment(
        cpc,
        fams["docdb_family_id"].unique(),
        cfg["q4_secrecy"]["military_cpc_prefixes"],
        cfg["q4_secrecy"]["dual_use_cpc_prefixes"],
    )
    seg_df["segment"].value_counts().rename("families").to_csv(output_dir / "step1_q4_segment_counts.csv")

    # Step 2: Applicant harmonization & inventive concentration
    hmap = harmonize_applicant_names(
        applts["psn_name"].dropna().unique(),
        domain_groups=cfg["domain_corporate_groups"],
        apply_domain_aliases=True,
    )
    applts_h = applts.copy()
    applts_h["firm"] = applts_h["psn_name"].map(hmap)
    comp_only = applts_h[applts_h["psn_sector"].fillna("").str.upper().str.contains("COMPANY")]
    fam_firm = comp_only[["docdb_family_id", "firm"]].drop_duplicates()

    conc = pd.DataFrame(
        {
            "Raw PSN": six_concentration_measures(applts_h.groupby("psn_name")["docdb_family_id"].nunique().to_numpy()),
            "Harmonized": six_concentration_measures(applts_h.groupby("firm")["docdb_family_id"].nunique().to_numpy()),
        }
    )
    conc.to_csv(output_dir / "step2_concentration_comparison.csv")

    # Step 3: Present Value Score (Clarivate 4 dimensions + RRF + Spearman robustness)
    fams_win = fams[fams["priority_year"].between(*present_window)].copy()
    present_ind = compute_present_indicators_per_firm(
        families_df=fams_win,
        fam_firm_df=fam_firm,
        applications_df=apps,
        citations_df=cits,
        min_families=min_families,
        top_n_firms=15,
        citation_window_years=5,
        last_citation_year=2025,
    )
    present_ind["present_score_mean"] = combine_present_score(present_ind, DEFAULT_UAV_PRESENT_WEIGHTS, method="mean")
    present_ind["present_score_rrf"] = combine_present_score(present_ind, DEFAULT_UAV_PRESENT_WEIGHTS, method="rrf")
    present_ind["present_rank_rrf"] = rank_firms(present_ind["present_score_rrf"])
    present_ind.sort_values("present_rank_rrf").to_csv(output_dir / "step3_present_value_scores.csv")

    ranks_rob, spearman_rob = run_ranking_robustness_check(present_ind, DEFAULT_UAV_PRESENT_WEIGHTS, method="rrf")
    ranks_rob.to_csv(output_dir / "step3_robustness_ranks.csv")
    spearman_rob.to_csv(output_dir / "step3_robustness_spearman.csv")

    # Step 4: Future Value Score + Temporal Back-Test at backtest_cutoff
    scored_firms = list(present_ind.index)
    future_df = compute_future_indicators_per_firm(
        families_df=fams,
        fam_firm_df=fam_firm,
        family_cpc_df=cpc,
        backward_citations_df=back_cits,
        cited_family_cpc_df=cited_cpc,
        cutoff_year=future_cutoff,
        recent_window_years=3,
        firms_to_score=scored_firms,
    )
    future_df.sort_values("future_score", ascending=False).to_csv(output_dir / "step4_future_value_scores.csv")

    # Temporal back-test: freeze at backtest_cutoff, evaluate against post-T realized citations
    future_at_T = compute_future_indicators_per_firm(
        families_df=fams,
        fam_firm_df=fam_firm,
        family_cpc_df=cpc,
        backward_citations_df=back_cits,
        cited_family_cpc_df=cited_cpc,
        cutoff_year=backtest_cutoff,
        recent_window_years=3,
        firms_to_score=scored_firms,
    )
    post_T_cits = (
        cits[cits["citing_year"].between(backtest_cutoff + 1, backtest_cutoff + 5)]
        .merge(fam_firm, left_on="cited_family", right_on="docdb_family_id", how="inner")
        .groupby("firm")["citing_family"]
        .nunique()
        .reindex(scored_firms)
        .fillna(0.0)
    )
    bt_df = backtest_future_algorithms(future_at_T, post_T_cits, top_k=min(5, len(scored_firms)))
    bt_df.to_csv(output_dir / "step4_backtest_comparison.csv")

    # Step 5: Magic Quadrant (Present RRF vs Future Score)
    total_fams_firm = fam_firm.groupby("firm")["docdb_family_id"].nunique()
    quad_df, x_thr, y_thr = assign_magic_quadrant(
        present_scores=present_ind["present_score_rrf"],
        future_scores=future_df["future_score"],
        families=total_fams_firm,
    )
    quad_df.to_csv(output_dir / "step5_magic_quadrant.csv")

    # Highlight highest-future Visionary (or top non-client firm) as illustrative pick
    vis = quad_df[(quad_df["quadrant"] == "Visionaries") & (quad_df.index != "LEONARDO")]
    rec_firm = vis["future_score"].idxmax() if not vis.empty else quad_df.drop(index="LEONARDO", errors="ignore")["future_score"].idxmax()
    fig = plot_magic_quadrant(
        quad_df,
        x_thr=x_thr,
        y_thr=y_thr,
        recommended_firm=rec_firm,
        client_firm="LEONARDO" if "LEONARDO" in quad_df.index else None,
        save_path=output_dir / "fig_step5_magic_quadrant.png",
    )
    plt.close(fig)

    # Step 6: Core Competences RTA matrix (Patel & Pavitt, 1997)
    firm_cpc_mat = (
        fam_firm[fam_firm["firm"].isin(scored_firms)]
        .merge(cpc[["docdb_family_id", "cpc_subclass"]].drop_duplicates(), on="docdb_family_id", how="inner")
        .groupby(["firm", "cpc_subclass"])["docdb_family_id"]
        .nunique()
        .unstack(fill_value=0)
    )
    rta = compute_revealed_technological_advantage(firm_cpc_mat)
    rta.round(2).to_csv(output_dir / "step6_rta_core_competences.csv")

    print(f"Pipeline completed cleanly -> {output_dir}")
    print(f"  Scored firms : {len(scored_firms)} | Top Visionary/Target highlight: {rec_firm}")
    print(f"  Outputs saved: {len(list(output_dir.iterdir()))} files")


def main() -> None:
    parser = argparse.ArgumentParser(description="Team 28 Flying Drones reproducible pipeline (Steps 1–6).")
    parser.add_argument("--demo", action="store_true", help="Run on compact synthetic UAV dataset (offline verification).")
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"), help="Directory with cleaned TIP CSV extracts.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for generated tables and figures.")
    parser.add_argument("--min-families", type=int, default=10, help="Minimum DOCDB families gate for firm scoring.")
    args = parser.parse_args()

    if args.demo:
        extracts = _generate_synthetic_uav_extracts()
        out_dir = args.output_dir or Path("outputs/demo")
        run_pipeline(extracts, out_dir, min_families=5)
    else:
        extracts = _load_extracts_from_dir(args.data_dir)
        out_dir = args.output_dir or Path("outputs/final")
        run_pipeline(extracts, out_dir, min_families=args.min_families)


if __name__ == "__main__":
    main()
