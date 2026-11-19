# Team 28 · Flying Drones Patent Study (Client: Leonardo S.p.A.)

Project Work for **Innovation Management (`01TXIWS`, A.Y. 2026/27)**, MSc in Data Science and Engineering, Politecnico di Torino.

- **Lecturer:** Prof. Grazia Sveva Ascione
- **Tutor:** Dr. Giacomo Masali (`giacomo.masali@polito.it`)
- **Student Tutor:** Fatima Syeda Wasti
- **Team 28:** Omar Boujendar (350435, Spokesperson), Beybin Cicek (351818), Elena Rossi (349342), Samuele Tommasi (361788), Parsa Teimouri (358965)
- **Submission deadline:** Sunday 20 December 2026 (Deck + Technical Appendix, GitHub tag `v1.0-submission`, 10-minute pitch video)

---

## Repository Layout (Aligned with PW Kick-Off Slide 18)

```text
Patent-study/
├── config/
│   └── sector.yaml                                   # Single source of truth: CPC/IPC codes, keywords, windows, benchmarks, corporate trees
├── src/
│   ├── config_loader.py                              # Load & validate config/sector.yaml + official CPC definitions
│   ├── step0_loader.py                               # Load locked Step 0 CSV (uav_final_query_families.csv) or fallback TIP query
│   ├── step1_metrics.py                              # Pure pandas/numpy indicator functions for Step 1 (Q1–Q4)
│   ├── harmonize.py                                  # Step 2 applicant name harmonizer + 6 Liston-Heyes & Pilkington (2004) metrics
│   ├── present_score.py                              # Step 3 Present Value Score (Clarivate 4 dims, Mean vs RRF, Spearman robustness)
│   ├── future_score.py                               # Step 4 Future Value Algorithm (baselines + UAV cross-layer + temporal back-test)
│   └── quadrant.py                                   # Steps 5–6 Magic Quadrant plot & Revealed Technological Advantage (Patel & Pavitt)
├── notebooks/
│   ├── 01_step1_general_description_team28.ipynb     # Unified Step 1 (Q1 Volume/Growth, Q2 Tech Mix, Q3 Geography)
│   ├── 02_step1_q4_patents_vs_secrecy_team28.ipynb   # Unified Step 1 Q4 (Patents vs Secrecy, Benchmarks, Defence Primes vs DJI)
│   └── 03_step2_harmonization_benchmark.ipynb        # Step 2 Harmonization gold-standard benchmark + UAV concentration starter
├── tests/
│   └── test_indicators.py                            # Unit tests on toy datasets with known analytical answers (Steps 0–6)
├── docs/
│   ├── STEP1_INTERPRETATION_FRAMEWORK.md             # Theory-grounded Step 1 slide narrative & verified academic references
│   ├── LEONARDO_CLIENT_AND_PEST_ANALYSIS.md          # Mandatory Step 2 PEST analysis (cited 2024–2026 sources) & Leonardo profile
│   └── DECK_20_SLIDES_BLUEPRINT.md                   # Exact 20-slide deck plan, A4 appendix checklist & 10-min pitch storyboard
├── run_all.py                                        # One-command reproducible pipeline (Steps 1–6 from cleaned extracts or --demo)
├── Query_Calibration_Taxonomy_Audit.ipynb            # Step 0 query calibration & stratified 100-family precision audit (Samuele)
├── CPC_CODES_REFERENCE.md                            # Verified official CPC/IPC definitions & Step 0 precision diagnosis
└── requirements.txt                                  # Reproducible Python dependencies
```

*(Legacy exploration files `step1/`, `q4/`, and `step1_geo.ipynb` remain preserved until the team freezes the final Step 0 dataset and merges into `main`.)*

---

## Quick Start

### 1. Local Verification (No TIP Access Needed)
Run all unit tests on toy data with known analytical answers and verify end-to-end Steps 1–6 reproducibility:
```bash
python3 -m unittest discover -s tests -v
python3 run_all.py --demo
```

### 2. Running Step 1 & Step 2 on EPO TIP
1. Clone or pull the repo in your TIP JupyterLab terminal:
   ```bash
   git clone git@github.com:Drassik/Patent-study.git
   cd Patent-study
   ```
2. Place Samuele's finalized Step 0 family list at `data/uav_core_boundary_validation/uav_final_query_families.csv` (columns: `docdb_family_id, query_source`).
   - Both `notebooks/01_step1_general_description_team28.ipynb` and `notebooks/02_step1_q4_patents_vs_secrecy_team28.ipynb` auto-detect this CSV so every slide shares the **exact same DOCDB family universe**.
   - If the CSV is absent, they fall back automatically to the audited two-tier CPC/IPC + keyword query defined in `config/sector.yaml`.
3. Set `ENV = "TEST"` first to verify execution, then switch to `ENV = "PROD"` and run all cells.
4. Outputs (CSVs, high-DPI PNGs, and auto-populated summary texts) are written to `outputs/step1_flying_drones/` and `outputs/q4_secrecy/` (excluded from Git per Slide 18).

---

## Step 2 Harmonization Benchmark (`PATSTAT_500_label_datav4.csv`)

Evaluated locally on Prof. Ascione's official Tutorial 11 gold standard (3,192 PATSTAT names across 481 organizations) with zero hardcoded brand names (`apply_domain_aliases=False`):

| Method | Groups Found (Gold: 481) | Pairwise Precision | Pairwise Recall | Pairwise F1 | V-Measure |
|---|---:|---:|---:|---:|---:|
| Raw PSN (no harmonisation) | 3,192 | 1.0000 | 0.0000 | 0.0000 | 0.7449 |
| Method A (Tutorial 11 Dictionary) | 3,010 | 0.9952 | 0.0022 | 0.0045 | 0.7496 |
| **Team 28 Multi-Stage Harmonizer (`src/harmonize.py`)** | **614** | **0.9746** | **0.9220** | **0.9476** | **0.9697** |

When applied to Team 28's UAV dataset with `apply_domain_aliases=True`, `src/harmonize.py` additionally preserves university/state-enterprise geography (keeping `BEIHANG UNIVERSITY` separate from `NANJING UNIVERSITY OF AERONAUTICS`, and `CASC` separate from `CASIC`), protects joint ventures (`NOKIA SIEMENS NETWORKS`), and consolidates corporate M&A trees (e.g., `FINMECCANICA` / `SELEX` / `ALENIA` / `AGUSTAWESTLAND` → `LEONARDO`; `DA-JIANG` / `SZ DJI` → `DJI`).

---

## References
- Course tutorials: [graziasveva/innovation-management-datascience26](https://github.com/graziasveva/innovation-management-datascience26)
- Official CPC scheme: https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions/table
- Step 1 interpretation & full academic bibliography: `docs/STEP1_INTERPRETATION_FRAMEWORK.md`
