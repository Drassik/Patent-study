"""Unit tests on toy datasets with known exact analytical answers (PW Slide 18 requirement).

Run locally with:
    python3 -m unittest discover -s tests -v
or with pytest:
    pytest -v
"""
from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.config_loader import (
    get_b64u_group_definition,
    get_cpc_subclass_definition,
    get_last_complete_year,
    load_config,
)
from src.future_score import (
    backtest_future_algorithms,
    compute_cross_layer_architecture_score,
    compute_future_indicators_per_firm,
    compute_hot_subfield_score,
    compute_novel_recombination_per_family,
    compute_originality_per_family,
)
from src.harmonize import (
    clean_with_tutorial_dictionary,
    coefficient_of_variation,
    concentration_ratio,
    evaluate_harmonization,
    gini_coefficient,
    harmonize_applicant_names,
    herfindahl_index,
    lotka_coefficient,
    six_concentration_measures,
)
from src.present_score import (
    combine_present_score,
    compute_family_forward_citations_norm,
    compute_present_indicators_per_firm,
    rank_firms,
    run_ranking_robustness_check,
)
from src.quadrant import (
    assign_magic_quadrant,
    compute_revealed_technological_advantage,
)
from src.step0_loader import (
    filter_text_by_keywords,
    iter_batches,
    load_locked_step0_families,
)
from src.step1_metrics import (
    build_q4_interpretation_paragraph,
    classify_uav_use_segment,
    compute_applicant_inventor_gap,
    compute_fractional_counts,
    compute_growth_summary,
    compute_period_mix_shift,
    compute_post_peak_decomposition,
    compute_sector_share_of_all_patents,
    compute_share_table,
    flag_truncated_years,
    pool_top_categories,
    summarize_patenting_intensity,
)


class TestConfigAndLoader(unittest.TestCase):
    def test_config_loads_and_official_b64u_titles_are_accurate(self):
        cfg = load_config()
        self.assertEqual(cfg["project"]["team"], "Team 28")
        self.assertEqual(cfg["project"]["lecturer"], "Prof. Grazia Sveva Ascione")
        self.assertEqual(get_last_complete_year(cfg), 2022)
        self.assertIn("Unmanned aerial vehicles", get_cpc_subclass_definition("B64U", cfg))
        self.assertIn("Constructional", get_b64u_group_definition("B64U20/00", cfg))
        self.assertIn("Propulsion", get_b64u_group_definition("B64U50/19", cfg))
        self.assertIn("Transport or storage", get_b64u_group_definition("B64U80/00", cfg))

    def test_locked_step0_csv_loader_and_batching(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "uav_final_query_families.csv"
            pd.DataFrame(
                {
                    "docdb_family_id": [101, 102, 102, 103],
                    "query_source": ["core_classification", "boundary_rescue", "boundary_rescue", "core_classification"],
                }
            ).to_csv(p, index=False)
            loaded = load_locked_step0_families(p)
            self.assertEqual(len(loaded), 3)
            self.assertEqual(loaded["docdb_family_id"].tolist(), [101, 102, 103])

        batches = list(iter_batches([1, 2, 2, 3, 4, 5], batch_size=2))
        self.assertEqual(batches, [[1, 2], [3, 4], [5]])

    def test_keyword_gate_excludes_underwater_and_ground_vehicles(self):
        cfg = load_config()
        df = pd.DataFrame(
            {
                "title": [
                    "Autonomous quadcopter delivery platform",
                    "Unmanned underwater vehicle (AUV) sonar drone",
                    "Autonomous driving road vehicle perception",
                    "Multirotor UAV battery docking station",
                ],
                "abstract": [
                    "A flying aerial vehicle with foldable arms.",
                    "Submersible autonomous marine drone.",
                    "Lane keeping for highway cars.",
                    "Automated recharging pad for unmanned aircraft.",
                ],
            }
        )
        mask = filter_text_by_keywords(
            df,
            cfg["step0"]["positive_keywords"],
            cfg["step0"]["negative_keywords"],
        )
        self.assertEqual(mask.tolist(), [True, False, False, True])


class TestStep1Metrics(unittest.TestCase):
    def test_fractional_counts_sum_exactly_to_unit_count(self):
        # Family 1 in 2 classes (0.5 each), Family 2 in 4 classes (0.25 each), Family 3 in 1 class (1.0)
        # Duplicate row (1, 'B64U', 2020) must be deduplicated before splitting
        pairs = pd.DataFrame(
            {
                "unit_id": [1, 1, 1, 2, 2, 2, 2, 3],
                "category": ["B64U", "B64U", "G05D", "B64U", "G05D", "H04N", "G06V", "B64U"],
                "year": [2020, 2020, 2020, 2020, 2020, 2020, 2020, 2020],
            }
        )
        res = compute_fractional_counts(pairs)
        by_cat = res.set_index("category")["n_frac"].to_dict()
        self.assertAlmostEqual(sum(by_cat.values()), 3.0, places=9)
        self.assertAlmostEqual(by_cat["B64U"], 0.5 + 0.25 + 1.0, places=9)
        self.assertAlmostEqual(by_cat["G05D"], 0.5 + 0.25, places=9)
        self.assertAlmostEqual(by_cat["H04N"], 0.25, places=9)
        self.assertAlmostEqual(by_cat["G06V"], 0.25, places=9)

    def test_growth_summary_and_truncation_exclusion(self):
        # Sector grows 100 -> 400 (+300%) over 2010..2020 (10 yrs -> CAGR = 4^(1/10)-1 = 14.8698%)
        # Truncated year 2023 drops to 10 and MUST NOT pollute complete-window growth or totals
        vol = pd.DataFrame(
            [
                {"scope": "all patents", "level": "family", "series": "all", "year": 2010, "n": 1000},
                {"scope": "all patents", "level": "family", "series": "all", "year": 2020, "n": 2000},
                {"scope": "all patents", "level": "family", "series": "all", "year": 2023, "n": 200},
                {"scope": "Flying drones", "level": "family", "series": "all", "year": 2010, "n": 100},
                {"scope": "Flying drones", "level": "family", "series": "all", "year": 2020, "n": 400},
                {"scope": "Flying drones", "level": "family", "series": "all", "year": 2023, "n": 10},
            ]
        )
        flagged = flag_truncated_years(vol, last_complete_year=2020)
        self.assertTrue(flagged.loc[flagged["year"] == 2023, "is_truncated"].all())
        self.assertFalse(flagged.loc[flagged["year"] == 2020, "is_truncated"].any())

        g = compute_growth_summary(vol, "Flying drones", 2010, 2020, levels=("family",))
        self.assertAlmostEqual(g.loc[("family", "Flying drones"), "growth_2010_2020_pct"], 300.0, places=6)
        self.assertAlmostEqual(g.loc[("family", "all patents"), "growth_2010_2020_pct"], 100.0, places=6)
        expected_cagr = (4.0 ** (1.0 / 10.0) - 1.0) * 100.0
        self.assertAlmostEqual(g.loc[("family", "Flying drones"), "cagr_2010_2020_pct"], expected_cagr, places=6)
        self.assertEqual(g.loc[("family", "Flying drones"), "total_complete_window"], 500.0)

        share_df = compute_sector_share_of_all_patents(vol, "Flying drones", last_complete_year=2020)
        s2020 = share_df.loc[share_df["year"] == 2020, "sector_share_pct"].iloc[0]
        self.assertAlmostEqual(s2020, 20.0, places=6)

    def test_pool_top_and_share_table_and_period_shift(self):
        df = pd.DataFrame(
            [
                {"subclass": "B64U", "year": 2010, "n_frac": 50.0},
                {"subclass": "G05D", "year": 2010, "n_frac": 30.0},
                {"subclass": "H04N", "year": 2010, "n_frac": 20.0},
                {"subclass": "B64U", "year": 2020, "n_frac": 40.0},
                {"subclass": "G05D", "year": 2020, "n_frac": 50.0},
                {"subclass": "H04N", "year": 2020, "n_frac": 10.0},
            ]
        )
        pooled = pool_top_categories(df, "subclass", last_complete_year=2022, top_n=2)
        self.assertEqual(set(pooled["subclass"]), {"B64U", "G05D", "Other"})

        piv = pooled.groupby("subclass")["n_frac"].sum().to_frame("family")
        shares = compute_share_table(piv)
        self.assertAlmostEqual(shares.loc["Total", "family"], 100.0, places=9)
        self.assertEqual(shares.index[-2], "Other")

        shift = compute_period_mix_shift(pooled, "subclass", (2010, 2012), (2019, 2022), cfg=load_config(), attach_cpc_definitions=True)
        self.assertAlmostEqual(shift.loc["G05D", "shift_pp"], 20.0, places=6)
        self.assertAlmostEqual(shift.loc["B64U", "shift_pp"], -10.0, places=6)
        self.assertIn("Unmanned aerial vehicles", shift.loc["B64U", "official_cpc_definition"])

    def test_applicant_inventor_gap(self):
        cols = pd.MultiIndex.from_tuples([("family", "applicant"), ("family", "inventor")])
        tbl = pd.DataFrame([[40.0, 35.0], [30.0, 35.0], [100.0, 100.0]], index=["US", "CN", "Total"], columns=cols)
        gap = compute_applicant_inventor_gap(tbl)
        self.assertAlmostEqual(gap.loc["US", "ownership_minus_rd_pp"], 5.0)
        self.assertAlmostEqual(gap.loc["CN", "ownership_minus_rd_pp"], -5.0)

    def test_q4_segmentation_intensity_and_narrative(self):
        cpc_df = pd.DataFrame(
            {
                "docdb_family_id": [1, 1, 2, 3],
                "cpc_class_symbol": ["B64U2101/15", "B64U2101/31", "B64U2101/31", "B64U  10/14"],
            }
        )
        # Family 1 has both military and dual-use -> must be classified ONLY as military
        seg = classify_uav_use_segment(
            cpc_df,
            all_uav_family_ids=[1, 2, 3, 4],
            military_prefixes=["B64U2101/15", "F41"],
            dual_use_prefixes=["B64U2101/31"],
        ).set_index("docdb_family_id")["segment"]
        self.assertEqual(seg.to_dict(), {1: "military", 2: "dual_use", 3: "civil_and_other", 4: "civil_and_other"})

        profiles = pd.DataFrame(
            [
                {"group": "All flying drones", "fid": 1, "year": 2020, "family_size": 1, "n_offices": 1, "n_ip5": 1, "is_pct": 0, "is_granted": 1},
                {"group": "All flying drones", "fid": 2, "year": 2020, "family_size": 3, "n_offices": 3, "n_ip5": 2, "is_pct": 1, "is_granted": 0},
                {"group": "Military drones", "fid": 1, "year": 2020, "family_size": 1, "n_offices": 1, "n_ip5": 1, "is_pct": 0, "is_granted": 1},
                {"group": "Civil drones", "fid": 2, "year": 2020, "family_size": 3, "n_offices": 3, "n_ip5": 2, "is_pct": 1, "is_granted": 0},
            ]
        )
        summ = summarize_patenting_intensity(profiles)
        self.assertAlmostEqual(summ.loc["All flying drones", "mean_family_size"], 2.0)
        self.assertAlmostEqual(summ.loc["All flying drones", "pct_share_pct"], 50.0)
        self.assertAlmostEqual(summ.loc["All flying drones", "multi_ip5_share_pct"], 50.0)
        self.assertAlmostEqual(summ.loc["All flying drones", "single_office_share_pct"], 50.0)

        para = build_q4_interpretation_paragraph(summ, {"military": 1, "dual_use": 1, "civil_and_other": 2})
        self.assertIn("25.0%", para)
        self.assertIn("Leonardo S.p.A.", para)
        self.assertIn("limiting foreign filings", para)

        # Positive-selection branch when military PCT > civil PCT (as observed on PROD)
        summ_prod_like = summ.copy()
        summ_prod_like.loc["Military drones", "pct_share_pct"] = 30.7
        summ_prod_like.loc["Civil drones", "pct_share_pct"] = 20.4
        para_sel = build_q4_interpretation_paragraph(summ_prod_like, {"military": 2, "dual_use": 2, "civil_and_other": 96})
        self.assertIn("positive selection effect", para_sel)

    def test_post_2018_decomposition_contributions_sum_to_100(self):
        # Toy country series: CN drops from 100/yr (2016-18) to 60/yr (2019-22) -> -40
        # US drops from 50/yr to 40/yr -> -10; EP stays flat at 30/yr -> 0.
        # Total net change = -50 -> CN explains 80%, US explains 20%, EP explains 0%.
        rows = []
        for y in range(2016, 2019):
            rows += [{"ctry": "CN", "year": y, "n": 100}, {"ctry": "US", "year": y, "n": 50}, {"ctry": "EP", "year": y, "n": 30}]
        for y in range(2019, 2023):
            rows += [{"ctry": "CN", "year": y, "n": 60}, {"ctry": "US", "year": y, "n": 40}, {"ctry": "EP", "year": y, "n": 30}]
        dec = compute_post_peak_decomposition(pd.DataFrame(rows), category_col="ctry")
        self.assertAlmostEqual(dec.loc["CN", "abs_change_avg"], -40.0, places=9)
        self.assertAlmostEqual(dec.loc["CN", "pct_change_avg"], -40.0, places=9)
        self.assertAlmostEqual(dec.loc["CN", "share_of_net_change_pct"], 80.0, places=9)
        self.assertAlmostEqual(dec.loc["US", "share_of_net_change_pct"], 20.0, places=9)
        self.assertAlmostEqual(dec.loc["EP", "share_of_net_change_pct"], 0.0, places=9)
        self.assertAlmostEqual(dec["share_of_net_change_pct"].sum(), 100.0, places=9)


class TestStep2HarmonizeAndConcentration(unittest.TestCase):
    def test_harmonizer_preserves_jvs_universities_and_substrings(self):
        cfg = load_config()
        names = [
            "LEONARDO S.P.A.",
            "FINMECCANICA S.P.A.",
            "SELEX ES S.P.A.",
            "SZ DJI TECHNOLOGY CO., LTD.",
            "DA-JIANG INNOVATIONS SCIENCE AND TECHNOLOGY",
            "BEIHANG UNIVERSITY",
            "BEIJING UNIVERSITY OF AERONAUTICS AND ASTRONAUTICS",
            "NANJING UNIVERSITY OF AERONAUTICS AND ASTRONAUTICS",
            "NOKIA CORPORATION",
            "NOKIA MOBILE PHONES (U.K.) LIMITED",
            "NOKIAN TYRES PLC.",
            "NOKIA SIEMENS NETWORKS S.P.A.",
            "SIEMENS AG",
            "SONY CORPORATION",
            "TRANSONYCHA LIMITED",
            "STMICROELECTRONICS LIMITED",
            "STMICROELETRONICS CROLLES 2",
            "CHINA AEROSPACE SCIENCE AND TECHNOLOGY CORPORATION",
            "CHINA AEROSPACE SCIENCE AND INDUSTRY CORPORATION",
        ]
        m_domain = harmonize_applicant_names(names, domain_groups=cfg["domain_corporate_groups"], apply_domain_aliases=True)
        # Corporate M&A consolidation
        self.assertEqual(m_domain["LEONARDO S.P.A."], "LEONARDO")
        self.assertEqual(m_domain["FINMECCANICA S.P.A."], "LEONARDO")
        self.assertEqual(m_domain["SELEX ES S.P.A."], "LEONARDO")
        self.assertEqual(m_domain["SZ DJI TECHNOLOGY CO., LTD."], "DJI")
        self.assertEqual(m_domain["DA-JIANG INNOVATIONS SCIENCE AND TECHNOLOGY"], "DJI")
        self.assertEqual(m_domain["BEIHANG UNIVERSITY"], m_domain["BEIJING UNIVERSITY OF AERONAUTICS AND ASTRONAUTICS"])
        # Distinct universities & Chinese aerospace SOEs MUST stay distinct
        self.assertNotEqual(
            m_domain["BEIJING UNIVERSITY OF AERONAUTICS AND ASTRONAUTICS"],
            m_domain["NANJING UNIVERSITY OF AERONAUTICS AND ASTRONAUTICS"],
        )
        self.assertNotEqual(
            m_domain["CHINA AEROSPACE SCIENCE AND TECHNOLOGY CORPORATION"],
            m_domain["CHINA AEROSPACE SCIENCE AND INDUSTRY CORPORATION"],
        )
        # JV, substring & typo protections
        self.assertEqual(m_domain["NOKIA CORPORATION"], m_domain["NOKIA MOBILE PHONES (U.K.) LIMITED"])
        self.assertNotEqual(m_domain["NOKIA CORPORATION"], m_domain["NOKIAN TYRES PLC."])
        self.assertNotEqual(m_domain["NOKIA CORPORATION"], m_domain["NOKIA SIEMENS NETWORKS S.P.A."])
        self.assertNotEqual(m_domain["SONY CORPORATION"], m_domain["TRANSONYCHA LIMITED"])
        self.assertEqual(m_domain["STMICROELECTRONICS LIMITED"], m_domain["STMICROELETRONICS CROLLES 2"])

    def test_evaluation_metrics_exact_tutorial_example(self):
        # Exact toy example from Tutorial 11 §2.4:
        # Gold: {NOKIA, NOKIA CORP, NOKIA OYJ} (3 pairs) and {NOKIAN TYRES} (0 pairs)
        # Pred: merges all 4 -> 6 pairs, 3 TP -> Precision = 0.5, Recall = 1.0, F1 = 2/3
        res = evaluate_harmonization([1, 1, 1, 2], ["A", "A", "A", "A"])
        self.assertAlmostEqual(res["precision"], 0.5, places=9)
        self.assertAlmostEqual(res["recall"], 1.0, places=9)
        self.assertAlmostEqual(res["F1"], 2.0 / 3.0, places=9)
        self.assertEqual(clean_with_tutorial_dictionary("SIEMENS AG"), "SIEMENS")

    def test_six_concentration_measures_on_equal_and_concentrated_toy_data(self):
        # 10 equal firms with 5 patents each: HH = 0.1, 1/HH = 10, CR4 = 40%, CV = 0, Gini = 0
        equal = [5] * 10
        m_eq = six_concentration_measures(equal)
        self.assertAlmostEqual(m_eq["HH"], 0.1, places=9)
        self.assertAlmostEqual(m_eq["numbers_equivalent_1_over_HH"], 10.0, places=9)
        self.assertAlmostEqual(m_eq["CR4_pct"], 40.0, places=9)
        self.assertAlmostEqual(m_eq["CR8_pct"], 80.0, places=9)
        self.assertAlmostEqual(m_eq["CV"], 0.0, places=9)
        self.assertAlmostEqual(m_eq["Gini"], 0.0, places=9)
        self.assertTrue(math.isnan(m_eq["Lotka_L"]))

        # Exact Lotka's law distribution f(n) = 100 / n^2 -> slope L must equal -2.0
        lotka_data = [1] * 100 + [2] * 25 + [5] * 4 + [10] * 1
        slope, pval = lotka_coefficient(lotka_data)
        self.assertAlmostEqual(slope, -2.0, places=6)
        self.assertLess(pval, 0.01)

        # Highly concentrated toy sector: one giant with 91 patents + 9 firms with 1 patent each
        giant = [91] + [1] * 9
        self.assertAlmostEqual(concentration_ratio(giant, 4), 94.0, places=6)
        self.assertAlmostEqual(herfindahl_index(giant), 0.91**2 + 9 * 0.01**2, places=9)
        self.assertGreater(gini_coefficient(giant), 0.8)
        self.assertGreater(coefficient_of_variation(giant), 2.5)


class TestSteps3To6ValuationAndQuadrant(unittest.TestCase):
    def test_present_score_mean_vs_rrf_and_wo_translation_exclusion(self):
        # Tutorial 40 worked intuition: Giant X dominates volume but average elsewhere; Specialist Y leads on 3/4
        df = pd.DataFrame(
            {
                "volume": [0.44, 0.06, 0.10, 0.10],
                "influence": [1.0, 1.5, 1.0, 0.5],
                "success": [0.70, 0.90, 0.65, 0.55],
                "globalization": [2.0, 3.5, 2.5, 1.5],
            },
            index=["GIANT_X", "SPECIALIST_Y", "MID_Z", "SMALL_W"],
        )
        equal_w = {"volume": 0.25, "influence": 0.25, "success": 0.25, "globalization": 0.25}
        s_mean = combine_present_score(df, equal_w, method="mean")
        s_rrf = combine_present_score(df, equal_w, method="rrf")
        # Mean rewards Giant X's massive volume skew; RRF puts Specialist Y #1!
        self.assertEqual(rank_firms(s_mean)["GIANT_X"], 1)
        self.assertEqual(rank_firms(s_rrf)["SPECIALIST_Y"], 1)

        ranks_df, spearman = run_ranking_robustness_check(df, equal_w, method="rrf")
        self.assertIn("equal_weights", ranks_df.columns)
        self.assertIn("alt_method_mean", spearman.index)

        # Verify WO and kind 'T' translations are excluded from Success & Globalization
        fams = pd.DataFrame(
            [
                {"docdb_family_id": 1, "priority_year": 2015, "first_publn_year": 2016},
                {"docdb_family_id": 2, "priority_year": 2015, "first_publn_year": 2016},
            ]
        )
        ff = pd.DataFrame([{"docdb_family_id": 1, "firm": "FIRM_A"}, {"docdb_family_id": 2, "firm": "FIRM_B"}])
        apps = pd.DataFrame(
            [
                # Family 1: EP granted + US not granted + WO (ignored) + ES kind T translation (ignored) -> success = 0.5, offices = 2
                {"appln_id": 10, "docdb_family_id": 1, "appln_auth": "EP", "appln_kind": "A ", "granted": "Y"},
                {"appln_id": 11, "docdb_family_id": 1, "appln_auth": "US", "appln_kind": "A ", "granted": "N"},
                {"appln_id": 12, "docdb_family_id": 1, "appln_auth": "WO", "appln_kind": "W ", "granted": "N"},
                {"appln_id": 13, "docdb_family_id": 1, "appln_auth": "ES", "appln_kind": "T ", "granted": "Y"},
                # Family 2: CN granted -> success = 1.0, offices = 1
                {"appln_id": 20, "docdb_family_id": 2, "appln_auth": "CN", "appln_kind": "A ", "granted": "Y"},
            ]
        )
        cits = pd.DataFrame(
            [
                {"citing_family": 901, "cited_family": 1, "citing_year": 2018},  # lag 2 <= 5
                {"citing_family": 902, "cited_family": 1, "citing_year": 2019},  # lag 3 <= 5
                {"citing_family": 903, "cited_family": 1, "citing_year": 2024},  # lag 8 > 5 (excluded)
                {"citing_family": 904, "cited_family": 2, "citing_year": 2017},  # lag 1 <= 5
            ]
        )
        # Cohort mean fwd5 for 2015 = (2 + 1) / 2 = 1.5 -> Firm A = 2/1.5 = 4/3, Firm B = 1/1.5 = 2/3
        ind = compute_present_indicators_per_firm(fams, ff, apps, cits, min_families=1, top_n_firms=5)
        self.assertAlmostEqual(ind.loc["FIRM_A", "success"], 0.5, places=9)
        self.assertAlmostEqual(ind.loc["FIRM_A", "globalization"], 2.0, places=9)
        self.assertAlmostEqual(ind.loc["FIRM_A", "influence"], 4.0 / 3.0, places=9)
        self.assertAlmostEqual(ind.loc["FIRM_B", "influence"], 2.0 / 3.0, places=9)

    def test_future_score_originality_recombination_and_no_leakage_backtest(self):
        # Originality: citing 2 classes equally (0.5, 0.5) -> 1 - (0.25 + 0.25) = 0.5
        bc = pd.DataFrame([{"docdb_family_id": 10, "cited_docdb_family_id": 1}, {"docdb_family_id": 10, "cited_docdb_family_id": 2}])
        cc = pd.DataFrame([{"cited_docdb_family_id": 1, "cpc_subclass": "B64U"}, {"cited_docdb_family_id": 2, "cpc_subclass": "G05D"}])
        orig = compute_originality_per_family(bc, cc)
        self.assertAlmostEqual(orig.loc[10], 0.5, places=9)

        # Novel recombination: 2015 introduces (A, B) -> 1.0; 2016 repeats (A, B) -> 0.0; 2016 adds (A, C) -> 1/3 or 1.0
        cpc = pd.DataFrame(
            [
                {"docdb_family_id": 1, "priority_year": 2015, "cpc_subclass": "B64U", "cpc_group": "A"},
                {"docdb_family_id": 1, "priority_year": 2015, "cpc_subclass": "G05D", "cpc_group": "B"},
                {"docdb_family_id": 2, "priority_year": 2016, "cpc_subclass": "B64U", "cpc_group": "A"},
                {"docdb_family_id": 2, "priority_year": 2016, "cpc_subclass": "G05D", "cpc_group": "B"},
                {"docdb_family_id": 3, "priority_year": 2016, "cpc_subclass": "B64U", "cpc_group": "A"},
                {"docdb_family_id": 3, "priority_year": 2016, "cpc_subclass": "G06V", "cpc_group": "C"},
                {"docdb_family_id": 3, "priority_year": 2016, "cpc_subclass": "G08G", "cpc_group": "D"},
            ]
        )
        rec = compute_novel_recombination_per_family(cpc)
        self.assertAlmostEqual(rec.loc[1], 1.0, places=9)
        self.assertAlmostEqual(rec.loc[2], 0.0, places=9)
        self.assertAlmostEqual(rec.loc[3], 1.0, places=9)

        # Cross-layer score: fam 3 bridges 3 distinct layers (B64U, G06V, G08G) -> (3-1)/2 = 1.0
        cl = compute_cross_layer_architecture_score(cpc)
        self.assertAlmostEqual(cl.loc[3], 1.0, places=9)
        self.assertAlmostEqual(cl.loc[1], 0.5, places=9)

        # Backtest perfect ranking -> Spearman = 1.0, Precision@2 = 1.0, NDCG@2 = 1.0
        scores_T = pd.DataFrame(
            {"originality": [0.1, 0.5, 0.9], "future_score": [10.0, 50.0, 90.0]},
            index=["F1", "F2", "F3"],
        )
        realized = pd.Series([5.0, 20.0, 100.0], index=["F1", "F2", "F3"])
        bt = backtest_future_algorithms(scores_T, realized, candidate_columns=("originality", "future_score"), top_k=2)
        self.assertAlmostEqual(bt.loc["future_score", "spearman_rho"], 1.0, places=9)
        self.assertAlmostEqual(bt.loc["future_score", "precision_at_2"], 1.0, places=9)
        self.assertAlmostEqual(bt.loc["future_score", "ndcg_at_2"], 1.0, places=9)

    def test_magic_quadrant_and_patel_pavitt_rta(self):
        pres = pd.Series([90, 90, 20, 20], index=["L", "C", "V", "N"])
        fut = pd.Series([90, 20, 90, 20], index=["L", "C", "V", "N"])
        fams = pd.Series([100, 80, 30, 15], index=["L", "C", "V", "N"])
        qdf, x_thr, y_thr = assign_magic_quadrant(pres, fut, fams)
        self.assertEqual(qdf["quadrant"].to_dict(), {"L": "Leaders", "C": "Challengers", "V": "Visionaries", "N": "Niche Players"})

        # Exact RTA arithmetic (Patel & Pavitt 1997):
        # Firm A: 8 in G05D, 2 in B64U (80% in G05D). Firm B: 2 in G05D, 8 in B64U (20% in G05D).
        # Sector total: 10 in G05D (50%), 10 in B64U (50%).
        # RTA(A, G05D) = 0.80 / 0.50 = 1.60; RTA(A, B64U) = 0.20 / 0.50 = 0.40
        mat = pd.DataFrame({"G05D": [8, 2], "B64U": [2, 8]}, index=["FIRM_A", "FIRM_B"])
        rta = compute_revealed_technological_advantage(mat)
        self.assertAlmostEqual(rta.loc["FIRM_A", "G05D"], 1.6, places=9)
        self.assertAlmostEqual(rta.loc["FIRM_A", "B64U"], 0.4, places=9)
        self.assertAlmostEqual(rta.loc["FIRM_B", "B64U"], 1.6, places=9)


if __name__ == "__main__":
    unittest.main()
