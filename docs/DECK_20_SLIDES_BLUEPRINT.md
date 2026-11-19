# 20-Slide Deck, Technical Appendix & 10-Minute Pitch Blueprint (Team 28)

Aligned strictly with **PW Kick-Off Slides 17, 18, 19, 20, and 24**:
* **Hard deadline:** Sunday **20 December 2026** (all 3 deliverables uploaded together).
* **Deliverable 1:** `Team28_FlyingDrones_deck.pdf` — **20 slides** main deck + **A4 11pt Technical Appendix** (≤10 figures/tables).
* **Deliverable 2:** GitHub repository URL + exact commit hash of tag `v1.0-submission`.
* **Deliverable 3:** `Team28_FlyingDrones_pitch.mp4` — **≤10:00 hard limit**, 1080p, voice-over by all 5 members, **zero code on slides**.

---

## Part 1 — Exact 20-Slide Main Deck Plan

| Slide # | Section | Title / Core Message (1 Message per Slide) | Visual / Table Source | Owner |
|---:|---|---|---|---|
| **1** | Intro | **Title Slide:** Team 28 · Flying Drones (Client: Leonardo S.p.A.) · All 5 names + student IDs · GitHub URL + `v1.0-submission` commit hash | Clean cover (Slide 17 mandatory fields) | All |
| **2** | Intro | **Executive Summary & The Client's 3 Questions:** Upfront answer for Leonardo's Board (sector trajectory, rising subfields, recommended target & deal type) | 3-box summary answering Client Q1–Q3 | Omar / Beybin |
| **3** | Step 1 | **Sector Scale & Growth:** Flying drones outpaced global patenting by `[PROD]`× (2004–2022, 2023–2025 shaded truncated) | `fig01_volume_per_year.png` + `fig03_growth_vs_all_patents.png` | Beybin |
| **4** | Step 1 | **Technology Mix & Shift:** From airframes (`B64U`/`B64C`) toward autonomy (`G05D`), vision (`G06V`) & UTM (`G08G`) | `fig04_cpc_subclass_mix.png` + top CPC table w/ official titles | Beybin |
| **5** | Step 1 | **Global Footprint (IP5 & Countries):** IP5 concentration, CN volume vs. US/EU international breadth, applicant vs. inventor gap | `fig05_ip5_offices.png` + `country_shares.csv` | Beybin / Parsa |
| **6** | Step 1 | **Patents vs. Secrecy (Bifurcated Appropriability):** Civil/dual-use is patent-heavy; pure defence (~40–50% of market $) is secrecy-reliant (Cohen et al. 2000; Arundel 2001; Acosta et al. 2018) | `fig01_q4_patenting_intensity.png` + `fig02_q4_primes_vs_commercial.png` + argued paragraph | Beybin |
| **7** | Step 2 | **Inventive Concentration:** Is the field consolidating? HHI, 1/HHI, CR4/CR8, Gini, Lotka before vs. after name harmonization (Liston-Heyes & Pilkington 2004) | `concentration_raw_vs_harmonized.csv` + HHI/CR4 trend chart | Omar / Nina |
| **8** | Step 2 | **Incumbents vs. New Entrants:** Top harmonized players (firm/university/startup, country, status) + entry & disappearance rates | Top applicants table + entry/exit plot | Omar / Nina |
| **9** | Step 2 | **Fastest-Growing Subfields:** Which CPC groups / NLP abstract topics are accelerating ahead of the curve? | Subfield growth map (size today vs. 5-yr growth %) | Samuele / Omar |
| **10** | Step 2 | **Mandatory PEST Analysis (Leonardo Lens):** EASA SORA 2.5 / U-space, FAA Part 108, US NDAA DJI ban, $84B–$96B market, Edge-AI & C-UAS | Clean 4-row PEST table from `docs/LEONARDO_CLIENT_AND_PEST_ANALYSIS.md` | Beybin / Omar |
| **11** | Step 3 | **Present Value Methodology (Clarivate 4 Dimensions):** Volume, cohort-normalized 5-yr Influence, Success (excl. WO/T), Globalization; why RRF (Cormack et al. 2009) prevents DJI volume skew | 4-pillar summary + weight rationale | Team |
| **12** | Step 3 | **Present Value Results & Robustness:** Top firms ranked on Present Score + Spearman weight-sensitivity & Mean vs. RRF check | `step3_present_value_scores.csv` + contribution bar chart + Spearman summary | Team |
| **13** | Step 4 | **Future Value Algorithm (Original Design):** Scoring recent filings via Hot-Subfield Lead + Novel CPC Recombination + UAV Cross-Layer Architecture + Originality + Early PCT | Visual architecture diagram (zero raw code!) | Samuele / Beybin |
| **14** | Step 4 | **Temporal Back-Test Proof (Freeze at T):** Proving Team 28's Future Score beats individual literature baselines on realized 5-yr post-T citations (Spearman ρ, Precision@K, NDCG@K) | `step4_backtest_comparison.csv` bar chart | Samuele / Beybin |
| **15** | Step 5 | **The Magic Quadrant (Centrepiece):** Top harmonized UAV players mapped on Present Score (Y) vs. Future Score (X), bubble = families, recommended target highlighted in orange | `fig_step5_magic_quadrant.png` | All |
| **16** | Step 6 | **Target Selection & Core Competences:** Why this firm (quadrant position, not fame) + Access to markets (CPC breadth), Customer value, Hard to imitate (RTA > 1, Patel & Pavitt 1997; citation centrality) | `step6_rta_core_competences.csv` heatmap + competence bullets | Beybin / Parsa |
| **17** | Step 6 | **Recommendation — Acquire or Partner (Teece, 1986):** Fit with Leonardo's Falco/AWHero/Eurodrone/LBA Systems & complementary assets + **3 data-backed arguments** | Strategic fit matrix + 3 numbered data arguments | Omar / Beybin |
| **18** | Step 6 | **Key Risks & Mitigations:** **2 concrete risks** (e.g., Freedom to Operate / DJI patent thicket; Export controls / valuation & integration risk) + mitigations | 2-column Risk / Mitigation table | Parsa / Nina |
| **19** | Wrap-Up | **Closing the Loop — Direct Answers to Leonardo's Board:** Final go/no-go decision answering the Client's 3 questions | Decision callout slide | Omar |
| **20** | Governance | **References, Contribution Statement & GenAI Usage Disclosure:** Author–year bibliography + transparent team split + exact AI usage disclosure (Slide 17 mandatory) | Compact 3-block governance slide | All |

---

## Part 2 — Technical Appendix Checklist (A4, 11pt, ≤10 Figures/Tables)

1. **A1. Step 0 Query Construction & Precision Validation:** Core (`CPC ∪ IPC`) vs. Boundary Rescue definition, why IPC `B64C 39/02` and `G05D 1/228` are keyword-gated, stratified 100-family manual validation table (`n=100` + 20 double-annotated, Cohen's kappa, Cochran & Wilson 95% CIs).
2. **A2. Methodological Conventions:** DOCDB family vs. application unit, earliest priority year vs. 3-dating sensitivity chart (`fig02_dating_conventions.png`), 3-year truncation window, fractional counting formula, missing-country coverage rates.
3. **A3. Applicant Name Harmonization Audit:** Multi-stage algorithm description, `PATSTAT_500_label_datav4.csv` gold-standard benchmark table (`F1 = 0.948` vs. Method A `0.005`), UAV corporate M&A consolidation list (Leonardo, DJI, Boeing, Lockheed, Airbus, etc.).
4. **A4. Present & Future Score Mathematical Formulas:** Exact formulas for Volume, cohort-normalized Influence, Success (excl. `WO` & kind `T`), Globalization, RRF vs. Mean, Originality, Novel Recombination, Cross-Layer Architecture, Hot-Subfield Velocity, RTA, and full Temporal Back-Test protocol.
5. **A5. Reproducibility & Pipeline Architecture:** Exact repo layout (`config/sector.yaml`, `src/`, `notebooks/`, `tests/`, `run_all.py`), PATSTAT snapshot date, unit-test summary, and commit hash of `v1.0-submission`.
6. **A6. Complete Author–Year Academic Bibliography.**

---

## Part 3 — 10-Minute Pitch Video Allocation (Slide 19 Rule: Every Member Speaks)

| Segment | Time | Slides | Speaker | Goal |
|---|---|---|---|---|
| **Hook** | `0:00 – 1:00` | 1–2 | Omar | Frame the client (Leonardo S.p.A.) and the 3 investment-bank questions |
| **Landscape (Step 1)** | `1:00 – 3:00` | 3–6 | Beybin | Size/growth, tech convergence, geography, and bifurcated patent vs. secrecy regime |
| **Competition (Step 2)** | `3:00 – 5:00` | 7–10 | Nina | Concentration, entrants, hot subfields, and PEST forces (EASA SORA 2.5, NDAA, defence budgets) |
| **Scoring & Quadrant (Steps 3–5)** | `5:00 – 8:00` | 11–15 | Samuele | Present RRF score, original Future algorithm + back-test proof, and Magic Quadrant reveal |
| **Recommendation (Step 6)** | `8:00 – 10:00` | 16–19 | Parsa + Omar | Core competences (RTA), Acquire/Partner decision for Leonardo, 3 arguments, 2 risks, crisp close |

---

## Part 4 — Contribution & GenAI Usage Statement Template (Slide 17 Mandatory)

* **Contribution Statement:** Clearly list each member's concrete deliverables matching actual GitHub commit history (`Samuele Tommasi`: Step 0 calibration & valuation back-test; `Beybin Cicek`: Step 1 Q1–Q4 pipeline, interpretations, PEST & harmonization module; `Omar Boujendar`: spokesperson coordination, Step 2 competitive landscape & strategic narrative; `Elena Rossi`: Step 2 harmonization audit & competitive analysis; `Parsa Teimouri`: geography/core competence analysis & pitch synthesis).
* **Generative AI Usage Statement:** Disclose honestly that generative AI tools were used strictly as coding/debugging and drafting assistants (boilerplate SQLAlchemy/pandas refactoring, unit test scaffolding, and prose editing); all classification codes were verified against official EPO/WIPO CPC schemes, all 100 validation families were manually annotated by team members, all PATSTAT PROD numbers were produced reproducibly on EPO TIP, and all external market/regulatory sources were independently verified.
