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


if __name__ == "__main__":
    unittest.main()
