# Step 1 Interpretation Framework · Flying Drones (Team 28 · Client: Leonardo S.p.A.)

This guide turns the PROD outputs of `notebooks/01_step1_general_description_team28.ipynb` and `notebooks/02_step1_q4_patents_vs_secrecy_team28.ipynb` into clear, defensible narratives for Deck Step 1 (PW Slides 11 & 17, 20% of grade tied to integration with lecture topics).

Replace every `[PROD: ...]` bracket with the exact value printed by the notebooks after running `ENV = "PROD"` on the locked Step 0 family CSV (`uav_final_query_families.csv`). Never report truncated years (`2023–2025`) as a market decline.

---

## Q1. How big is the field, and is it growing, flat, or declining?

- **Data inputs:** `outputs/step1_flying_drones/volume_per_year.csv`, `growth_summary.csv`, `sector_share_of_all_patents.csv`, `fig01_volume_per_year.png`, `fig03_growth_vs_all_patents.png`.
- **Headline template:**
  > Between 2004 and 2022 (the last non-truncated priority year), global flying-drone patenting reached `[PROD: total_complete_window]` DOCDB families, expanding by `[PROD: sector_growth]%` (`[PROD: sector_cagr]%` CAGR) compared with `[PROD: all_patents_growth]%` (`[PROD: all_patents_cagr]%` CAGR) for global patenting overall. Flying drones increased their share of all global patent families from `[PROD: share_2004]%` in 2004 to `[PROD: share_2022]%` in 2022, confirming genuine technological expansion rather than mere aggregate patent inflation.
- **Course theory link:**
  - Connect the steep post-2013 inflection to **technological paradigms & trajectories** (Dosi, 1982) and the **fluid-to-transitional phase** of the **Abernathy–Utterback (1975)** model: falling MEMS sensor, brushless motor, and lithium-polymer battery costs triggered rapid commercial experimentation and multirotor convergence.
  - Explain the **application-to-family ratio** (`[PROD: avg_applns_per_family]`) and **PCT share** (`[PROD: pct_share]%`): a modest family size combined with a surge in domestic filings signals heavy national (especially Chinese) patenting alongside a smaller core of internationally protected inventions.
- **Methodological note (Technical Appendix):**
  - Unit of analysis: DOCDB family (1 invention = 1 count) dated by earliest priority year; applications shown side by side for filing breadth.
  - Truncation: 2023–2025 shaded in grey and excluded from growth calculations due to the 18-month publication lag and PATSTAT ingestion/reclassification delay.

---

## Q2. Which technologies make up the field, and how is the mix shifting?

- **Data inputs:** `cpc_subclass_shares.csv`, `cpc_subclass_shift.csv`, `wipo_techn_sector_shares.csv`, `wipo_techn_field_shares.csv`, `fig04_cpc_subclass_mix.png`.
- **Headline template:**
  > While dedicated airframe and UAV-equipment codes (`B64U`, `[PROD: B64U_share]%`; legacy `B64C`, `[PROD: B64C_share]%`) anchor the sector, flying-drone innovation is a **multi-technology convergence system**. Between `2004–2012` and `2018–2022`, fractional patent shares shifted by `[PROD: G05D_shift_pp]` pp in flight/autonomous control (`G05D`), `[PROD: G08G_shift_pp]` pp in unmanned traffic management (`G08G`), and `[PROD: G06V_H04N_shift_pp]` pp in computer vision, imaging, and wireless links (`G06V`, `H04N`, `H04W`).
- **Course theory link:**
  - Frame UAVs as a **complex product system** (Hobday; Cohen, Nelson & Walsh, 2000) spanning mechanical airframes (`Mechanical engineering`), embedded sensors/navigation (`Instruments`), and autonomy/comms/AI (`Electrical engineering` in WIPO sectors).
  - Relate the shift from mechanical airframes (`B64C`/`B64U`) toward autonomy (`G05D`), perception (`G06V`/`G06T`), and UTM (`G08G`) to **modular/architectural innovation** (Henderson & Clark, 1990): hardware commoditizes first, while value migrates to software, autonomy, payload integration, and swarm/BVLOS systems (consistent with Zheng et al., 2026).
- **Client lens (Leonardo S.p.A.):**
  - Leonardo already holds deep aerospace/airframe and radar/sensor competences. Scouting targets in fast-rising co-classification layers (autonomous flight control `G05D`, vision/target recognition `G06V`, UTM/counter-UAS `G08G`/`F41H`, and energy/docking `B64U 50`/`70`) addresses where differentiation is moving.

---

## Q3. Where is it happening? (IP5 Offices & Applicant vs. Inventor Geography)

- **Data inputs:** `office_application_shares.csv`, `ip5_families_over_time.csv`, `country_shares.csv`, `applicant_inventor_gap.csv`, `fig05_ip5_offices.png`, `fig06_applicant_countries_over_time.png`.
- **Headline template:**
  > The IP5 offices (`CN`, `US`, `EP`, `JP`, `KR`) capture `[PROD: ip5_share]%` of all flying-drone applications. Geographically, `[PROD: top1_ctry]` leads fractional family ownership at `[PROD: top1_share]%`, followed by `[PROD: top2_ctry]` (`[PROD: top2_share]%`) and `[PROD: top3_ctry]` (`[PROD: top3_share]%`). Comparing applicant vs. inventor countries reveals `[PROD: gap_finding]` (net ownership concentration vs. cross-border R&D hubs).
- **Important analytical nuance (CN volume vs. global breadth):**
  - Always pair raw CNIPA volume with international filing breadth (PCT / ≥2 IP5 offices / EP + US filings). Chinese filings are high in volume—and partially undercounted if IPC `B64U` / `B64C` lags are ignored—but a high fraction remain domestic single-office filings, whereas US and European families exhibit higher multi-jurisdiction protection.
  - Report missing-country coverage explicitly (`Applicant country coverage: [PROD]%`; `Inventor country coverage: [PROD]%`) in the Technical Appendix.

---

## Q4. Is the field patent-heavy, or does it rely on secrecy?

- **Data inputs:** `outputs/q4_secrecy/q4_patenting_intensity.csv`, `q4_defence_primes_vs_commercial.csv`, `q4_applicant_sector_mix.csv`, `fig01_q4_patenting_intensity.png`, `fig02_q4_primes_vs_commercial.png`, `q4_argued_paragraph.txt`.
- **Core thesis — A Bifurcated Appropriability Regime:**
  Flying drones are **neither uniformly patent-heavy nor uniformly secrecy-reliant**; appropriability splits sharply along the **civil/dual-use vs. military boundary**:
  1. **Civil & Dual-Use UAVs are patent-heavy (commercial competition & platform ecosystems):** Commercial leaders (e.g., DJI, Autel, Parrot, XAG) and Chinese universities file aggressively to secure freedom to operate, block rivals, and build cross-licensing portfolios—matching the strategic patenting motives identified in complex technologies by **Cohen, Nelson & Walsh (2000)**.
  2. **Pure Military UAVs rely heavily on secrecy and lead-time:** Explicit warfare-classified UAV families (`B64U 2101/15–19`, `F41`, `F42B`) represent only `[PROD: mil_share]%` of total UAV patent families, far below defence's economic weight in the global UAV market. Defence primes (Leonardo, Lockheed Martin, Northrop Grumman, General Atomics, Elbit, Baykar) hold noticeably fewer public UAV families than DJI alone, and military families exhibit `[PROD: mil_pct_share]%` PCT / `[PROD: mil_single_office]%` single-office shares—consistent with state **Invention Secrecy Acts**, ITAR/EU dual-use export controls, and reverse-engineering risk on the battlefield (**Arundel, 2001**; **Acosta et al., 2018**; **Gross, 2023**).
  3. **Benchmark comparison:** Contrasting flying drones with **Manned Aircraft** (`B64C`/`B64D`) and **Autonomous Road Vehicles** (`B60W 60/`) separates aerospace-specific secrecy effects from general autonomous-systems patenting intensity.
- **Strategic takeaway for Leonardo S.p.A. (Teece, 1986):**
  - Under Teece's (1986) *Profiting from Innovation* framework, weak/asymmetric patent appropriability in defense shifts value capture toward **specialized complementary assets** (defense procurement relationships, airworthiness certification, sovereign manufacturing, C4ISR integration)—assets Leonardo already controls.
  - Therefore, patent scouting on PATSTAT is highly effective for identifying **civil/dual-use technology specialists** (autonomy, swarming, sensing, endurance) that Leonardo can acquire or partner with, while recognizing that pure-defense competitors' classified capabilities will be systematically understated in public patent counts.

---

## Q4b. Diagnosing the Post-2018 Filing Slowdown (Dr. Giacomo Masali Feedback)

During the November 18 tutoring review, Dr. Giacomo Masali noted that citing **secrecy** to explain an observed post-2018 decline in UAV patent filings is a **receivable hypothesis**, provided it is tested empirically by checking **which specific countries and CPC codes** declined. Section 6 of `notebooks/02_step1_q4_patents_vs_secrecy_team28.ipynb` decomposes the `2016–2018` vs. `2019–2022` complete-year change (`post2018_decomp_*.csv`, `fig03_post2018_diagnostic.png`) to discriminate among **three competing mechanisms**:

1. **Mechanism A — Defence Secrecy & Geopolitical Tightening (Secrecy Hypothesis):**
   - *Empirical test:* Did **Military UAV codes** (`B64U 2101/15–19`, `F41`, `F42B`) and **Western/allied defence jurisdictions (`US`, `EP`, `IL`)** decline disproportionately faster after 2018, accompanied by rising single-office shares / falling PCT rates?
   - *Theory link:* Compulsory invention secrecy orders (Gross, 2023), export controls (ITAR / EU Dual-Use), and asymmetric battlefield reverse-engineering shift defence firms from patents to secrecy and lead-time (Arundel, 2001; Acosta et al., 2018).
2. **Mechanism B — Airframe Dominant Design Lock-In (Abernathy–Utterback Maturity):**
   - *Empirical test:* Did mechanical airframe classes (`B64U 10/`, `20/`, `30/`, `B64C`) peak around 2018 while software, autonomy, vision, and UTM classes (`G05D`, `G06V`, `G08G`, `H04W`) remained resilient or kept growing?
   - *Theory link:* Once the quadcopter/multirotor dominant design crystallized (Abernathy & Utterback, 1975), incremental airframe patenting plateaued while R&D pivoted to architectural/software layers (Henderson & Clark, 1990).
3. **Mechanism C — Country-Specific Filing Policy & Reclassification Lag (China CNIPA Effect):**
   - *Empirical test:* What exact percentage of the total `2016–2018 -> 2019–2022` net change (`share_of_net_change_pct`) comes from **China (`CN`)** alone vs. `US`/`EP`/`JP`/`KR`?
   - *Context:* China phased out local patent-filing subsidies (2018–2021) and tightened CNIPA "irregular patent" scrutiny, causing aggregate CN filing counts to cool across multiple hardware sectors, compounded by IPC→CPC reclassification lags (addressed by Samuele's `CPC ∪ IPC` union).

> **Slide discipline:** Report whichever combination the `PROD` decomposition tables actually prove (exact `share_of_net_change_pct` by office, country, CPC subclass, and military/dual-use/civil segment) rather than asserting secrecy without disaggregating the drop.

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
