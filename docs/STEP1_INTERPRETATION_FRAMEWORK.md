# Step 1 Interpretation Framework · Flying Drones (Team 28 · Client: Leonardo S.p.A.)

This document summarises the final `PROD` outputs of `notebooks/01_step1_general_description_team28.ipynb` and `notebooks/02_step1_q4_patents_vs_secrecy_team28.ipynb` executed on Samuele's locked Step 0 family roster (`data/raw/00_family_roster.csv`: **71,197 DOCDB families** across `2004–2025`, comprising `61,967` core and `9,230` boundary-rescue families).

All growth rates, shares, and comparisons below are computed strictly on the **complete priority window (`2004–2022`: 50,782 DOCDB families; 87,191 applications)**. Truncated priority years (`2023–2025`: `7,078`, `7,109`, and `6,221` families) are shaded in grey and never read as a market decline.

---

## Q1. How big is the field, and is it growing, flat, or declining?

- **Data inputs:** `outputs/step1_flying_drones/volume_per_year.csv`, `growth_summary.csv`, `sector_share_of_all_patents.csv`, `fig01_volume_per_year.png`, `fig03_growth_vs_all_patents.png`.
- **Headline finding (ready for Slides 3–4):**
  > Between 2004 and 2022 (the last non-truncated priority year), global flying-drone patenting reached **50,782 DOCDB families** (87,191 applications), expanding by **+4,846.6%** (**+24.20% CAGR**, from 133 to 6,579 families/year) compared with **+138.8%** (**+4.95% CAGR**) for global patenting overall. Annual families peaked in **2021 (6,989 families)**, while flying drones increased their share of all global patent families more than twenty-fold, from **0.013% (1.33 bps)** in 2004 to a **0.300% (30.01 bps)** peak in 2017 and **0.275% (27.53 bps)** in 2022 — confirming genuine technological expansion rather than aggregate patent inflation.
- **Course theory link:**
  - The steep post-2013 inflection reflects **technological paradigms & trajectories** (Dosi, 1982) and the **fluid-to-transitional phase** of the **Abernathy–Utterback (1975)** model: falling MEMS sensor, brushless motor, and lithium-polymer battery costs triggered rapid commercial experimentation and multirotor convergence.
  - A modest mean family size (**1.85 applications per family**, median `1.0`) paired with a **20.45% PCT share** and **81.86% single-office share** signals heavy national (especially Chinese) domestic filing alongside a smaller core of internationally protected inventions.
- **Methodological note (Technical Appendix):**
  - Unit of analysis: DOCDB family (1 invention = 1 count) dated by earliest priority year; applications shown side by side for filing breadth (`+8,718.3%`, `+28.26%` CAGR, peak 2018 at `11,669`).
  - Truncation: 2023–2025 shaded in grey and excluded from growth calculations due to the 18-month publication lag and PATSTAT ingestion/reclassification delay.

---

## Q2. Which technologies make up the field, and how is the mix shifting?

- **Data inputs:** `cpc_subclass_shares.csv`, `cpc_subclass_shift.csv`, `wipo_techn_sector_shares.csv`, `wipo_techn_field_shares.csv`, `fig04_cpc_subclass_mix.png`.
- **Headline finding:**
  > While dedicated airframe and UAV-equipment codes (`B64U`, **20.89%**; legacy `B64C`, **14.58%**; `B64D`, **9.43%**) anchor the sector, flying-drone innovation is a **multi-technology convergence system** spanning Mechanical Engineering (**57.49%** of WIPO fractional families), Instruments (**27.19%**), and Electrical Engineering (**12.69%**). Between `2004–2012` and `2018–2022`, fractional family shares shifted sharply away from standalone UAV airframes (`B64U`: **28.74% → 18.47%, −10.27 pp**) toward autonomous flight and trajectory control (`G05D`: **11.10% → 18.59%, +7.49 pp**), aircraft payload/equipment integration (`B64D`: **6.64% → 10.02%, +3.38 pp**), and climate/electric transport technologies (`Y02T`: **3.02% → 4.45%, +1.43 pp**), while air-traffic management (`G08G`: **4.05% → 2.98%, −1.07 pp**) grew more slowly than total volume.
- **Course theory link:**
  - UAVs behave as a **complex product system** (Cohen, Nelson & Walsh, 2000) combining airframe mechanics (`Transport`: 53.17%), embedded control/sensing (`Control`: 20.98%; `Measurement`: 5.28%), and software/comms (`Computer technology`: 3.70%; `Digital communication`: 1.92%).
  - Value migration from mechanical airframes (`B64U`) toward autonomy (`G05D`), payload integration (`B64D`), and propulsion/energy (`Y02T`) matches **architectural innovation** (Henderson & Clark, 1990): once multirotor hardware commoditizes, competitive differentiation moves to software, autonomy, and cross-layer integration (consistent with Zheng et al., 2026).
- **Client lens (Leonardo S.p.A.):**
  - Leonardo already holds deep aerospace/airframe and radar/sensor competences. Scouting targets in fast-rising control/autonomy (`G05D`), payload integration (`B64D`), and electric/hybrid endurance (`Y02T`, `B64U 50/`) directly addresses where technological value is migrating.

---

## Q3. Where is it happening? (IP5 Offices & Applicant vs. Inventor Geography)

- **Data inputs:** `office_application_shares.csv`, `ip5_families_over_time.csv`, `country_shares.csv`, `applicant_inventor_gap.csv`, `fig05_ip5_offices.png`, `fig06_applicant_countries_over_time.png`.
- **Headline finding:**
  > The IP5 offices (`CN`, `US`, `EP`, `JP`, `KR`) capture **76.5%** of all flying-drone applications, led by **CN (32.56%)**, **US (20.46%)**, **WO/PCT (11.43%)**, **KR (9.43%)**, **JP (7.43%)**, and **EP (6.64%)**. Among records with populated country metadata, fractional family ownership is led by **US (30.63%)**, **KR (27.15%)**, **CN (12.45%)**, **JP (8.42%)**, **DE (4.03%)**, **FR (2.73%)**, **GB (1.97%)**, and **IL (1.31%)**. Comparing applicant vs. inventor shares shows net ownership concentration in **KR (+8.27 pp: 27.15% applicant vs. 18.88% inventor)** and modest negative ownership-minus-R&D gaps in **US (−2.24 pp)** and **CN (−1.42 pp)**.
- **Critical data-quality note (must report in slide footnote & Technical Appendix):**
  - `person_ctry_code` coverage in PATSTAT is **45.2% for applicants** and **39.5% for inventors**. Chinese patent records disproportionately lack `person_ctry_code`, which visibly understates `CN` (12.45%) and inflates `KR` (27.15%) in applicant-country shares relative to filing-office shares where CNIPA leads at **32.56%**.
  - Always pair raw CNIPA volume with international filing breadth (`PCT`, `≥2 IP5` offices, `EP + US` filings): Chinese filings are high in volume but predominantly domestic single-office filings, whereas US and European portfolios exhibit higher multi-jurisdiction protection.

---

## Q4. Is the field patent-heavy, or does it rely on secrecy?

- **Data inputs:** `outputs/q4_secrecy/q4_patenting_intensity.csv`, `q4_defence_primes_vs_commercial.csv`, `q4_applicant_sector_mix.csv`, `military_precision_sample.csv`, `fig01_q4_patenting_intensity.png`, `fig02_q4_primes_vs_commercial.png`, `q4_argued_paragraph.txt`.
- **Core thesis — A Bifurcated Appropriability Regime (50,782 complete-window families):**
  Flying drones are **neither uniformly patent-heavy nor uniformly secrecy-reliant**; appropriability splits sharply along the **civil/dual-use vs. military boundary**:
  1. **Civil & Dual-Use UAVs are patent-heavy (commercial competition & platform ecosystems):** Civil/Commercial accounts for **95.73% (48,614 families)** and Dual-Use ISR/Surveillance for **2.06% (1,046 families)**. Commercial leaders — **DJI (1,631)**, **State Grid Corp of China (724)**, **Autel Robotics (424)**, **Alphabet (278)**, **XAG (244)**, **Skydio (111)** — and Chinese universities (**Beihang 362**, **NUAA 314**, **Northwestern Polytechnical 293**) file aggressively to secure freedom to operate, block rivals, and build cross-licensing portfolios (Cohen, Nelson & Walsh, 2000).
  2. **Pure Military UAVs rely heavily on secrecy and lead-time:** Explicit warfare-classified UAV families (`B64U 2101/15–19`, `F41`, `F42B`) represent only **2.21% (1,122 families)**, far below defence's ~40–50% share of the global UAV market. Defence primes hold dramatically fewer public UAV families than DJI alone: **Boeing (571)**, **Textron (256)**, **Airbus (254)**, **BAE Systems (162)**, **RTX Raytheon (152)**, **Lockheed Martin (147)**, **Thales (90)**, **AeroVironment (83)**, **IAI (65)**, **Northrop Grumman (50)**, **Leonardo (25)**, **Elbit (16)**, **General Atomics (12)**, and **Baykar (0)** — reflecting state **Invention Secrecy Acts** (Gross, 2023), ITAR/EU dual-use export controls, and battlefield reverse-engineering risk (Arundel, 2001; Acosta et al., 2018).
  3. **Positive Selection Effect in Military PCT & External Benchmarks:** Military UAV families exhibit higher international filing rates (**30.93% PCT**, **21.93% ≥2 IP5**, **70.05% grant rate**) than civil drones (**20.05% PCT**, **15.86% ≥2 IP5**, **59.46% grant rate**). This reflects **positive selection**: truly classified defence capabilities never enter PATSTAT at all (leaving military share at just 2.21%), while the small subset primes do patent are export-oriented systems filed internationally, whereas civil averages are diluted by high-volume domestic Chinese filings. Against external benchmarks, overall UAV multi-office protection (**16.14% ≥2 IP5**, **81.86% single-office**) trails both **Manned Aircraft** (`66,608` families: **36.04% ≥2 IP5**, `57.68%` single-office) and **Autonomous Road Vehicles** (`18,829` families: **49.67% ≥2 IP5**, `47.91%` single-office).
- **Strategic takeaway for Leonardo S.p.A. (Teece, 1986):**
  - Weak/asymmetric patent appropriability in defence shifts value capture toward **specialized complementary assets** (defence procurement relationships, EASA/military airworthiness certification, sovereign manufacturing, C4ISR integration) — assets Leonardo already controls.
  - PATSTAT scouting is therefore highly effective for identifying **civil/dual-use technology specialists** (autonomy, swarming, sensing, endurance) that Leonardo can acquire or partner with, while recognising that pure-defence rivals' classified capabilities are structurally understated in public patent counts.

---

## Q4b. Diagnosing the Post-2018 Filing Slowdown (Dr. Giacomo Masali Feedback)

During the November 18 tutoring review, Dr. Giacomo Masali noted that citing **secrecy** to explain an observed post-2018 decline in UAV patent filings is a **receivable hypothesis**, provided it is tested empirically by checking **which specific countries, offices, and CPC codes** declined. Section 6 of `notebooks/02_step1_q4_patents_vs_secrecy_team28.ipynb` decomposes the `avg 2016–2018` vs. `avg 2019–2022` complete-year change (`post2018_decomp_*.csv`, `fig03_post2018_diagnostic.png`):

1. **Global Headline — No Global Collapse Once IPC + Boundary Rescue Are Included:**
   - Total global families actually continued growing after 2018, peaking in **2021 (6,989 families)** (`Civil +7.90%`, `Military +17.41%`, `Dual-use −1.63%` between `2016–2018` and `2019–2022`). Earlier CPC-only views overstated a post-2018 dip by missing Asian IPC-only filings.
2. **Real Decline Concentrated in Western/International Filings & Mature Airframe/Camera Classes:**
   - **By filing office:** Sharp declines occurred in **US (−24.92%, −469.8 families/yr)** and **WO/PCT (−25.00%, −351.3/yr)**, with mild dips in **JP (−4.23%)** and **EP (−3.94%)**, while **CN (+13.59%, +473.0/yr)** and **KR (+22.87%, +196.8/yr)** grew strongly.
   - **By CPC subclass:** Declines concentrated in standalone UAV airframe/hardware (**`B64U`: −16.54%, −700.0/yr**), aerial cameras/imaging (**`H04N`: −29.95%, −118.0/yr**), and air-traffic control (**`G08G`: −14.69%, −90.4/yr**), while electric/green transport (**`Y02T`: +64.97%, +341.8/yr**), ground/docking installations (**`B64F`: +31.92%, +112.6/yr**), autonomous control (**`G05D`: +13.30%, +249.1/yr**), **`B64C` (+10.44%)**, and **`B64D` (+9.10%)** expanded.
   - **By known applicant country:** US fell **−31.05%** (`−326.1/yr`); KR rose **+22.93%** (`+181.4/yr`) and JP rose **+13.91%** (`+38.3/yr`). (The recorded `CN` country-tag drop of `−44.53%` contrasts with `+13.59%` CNIPA office growth and reflects rising missing `person_ctry_code` rates in recent Chinese records.)
3. **Synthesis Across the Three Mechanisms:**
   - The post-2018 divergence is **not** a uniform secrecy collapse; rather, it reflects **both** (a) **Western/international filing tightening and defence-secrecy/export-control effects** (`US` and `WO/PCT` both down `~25%`) **and** (b) **Abernathy–Utterback airframe dominant-design maturity** (`B64U` and `H04N` cooling while R&D pivots to autonomy `G05D`, docking `B64F`, and green propulsion `Y02T`), alongside sustained domestic Asian volume (`CN`, `KR`).

---

## Verified References (Author–Year Style for Deck & Appendix)

- **Abernathy, W. J., & Utterback, J. M. (1975).** A dynamic model of process and product innovation. *Omega*, 3(6), 639–656.
- **Acosta, M., Coronado, D., & Marín, R. (2018).** Patents and dual-use technology: An empirical study of the world's largest defence companies. *Defence and Peace Economics*, 29(7), 821–839.
- **Arundel, A. (2001).** The relative effectiveness of patents and secrecy for appropriation. *Research Policy*, 30(4), 611–624.
- **Choe, W. B. (2023).** Analysis of technology trends in unmanned aerial vehicles using patent information. *Journal of the Korean Society of Nondestructive Testing*, 6(3), 336–347. doi:10.31818/JKNST.2023.09.6.3.336
- **Cohen, W. M., Nelson, R. R., & Walsh, J. P. (2000).** Protecting their intellectual assets: Appropriability conditions and why U.S. manufacturing firms patent (or not). *NBER Working Paper No. 7552*.
- **Dosi, G. (1982).** Technological paradigms and technological trajectories. *Research Policy*, 11(3), 147–162.
- **Gross, D. P. (2023).** The hidden costs of securing innovation: The manifold impacts of compulsory invention secrecy. *Management Science*, 69(4), 2318–2338.
- **Henderson, R. M., & Clark, K. B. (1990).** Architectural innovation: The reconfiguration of existing product technologies and the failure of established firms. *Administrative Science Quarterly*, 35(1), 9–30.
- **Teece, D. J. (1986).** Profiting from technological innovation: Implications for integration, collaboration, licensing and public policy. *Research Policy*, 15(6), 285–305.
- **Zheng, X., Chen, X., Zhang, P., & Liu, F. (2026).** Evolutionary pathways and future trends of civil UAV technologies: A patent-based data-driven analysis. *Inventions*, 11(6), 117. doi:10.3390/inventions11060117
- **Journal of Open Innovation (2020).** Analysis of technological trends and technological portfolio of unmanned aerial vehicle. *J. Open Innov. Technol. Mark. Complex.*, 6(3), 48. doi:10.3390/joitmc6030048
