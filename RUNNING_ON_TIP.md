# Running the Analysis on EPO TIP

This guide explains how to run the notebooks on the **EPO Technology Intelligence Platform (TIP)** to generate the final analysis outputs.

## Before You Start

1. **EPO TIP Account**: You need access to the EPO TIP with PATSTAT database
2. **Python Environment**: TIP provides Python 3.x with `sqlalchemy`, `pandas`, `matplotlib` pre-installed
3. **Course Materials**: You should have the course `tutorial_0` folder available on TIP (contains reference notebooks and helper functions)

---

## Step 1: Upload the Notebooks to TIP

### Option A: Upload Files via TIP UI
1. Log in to EPO TIP
2. Create a folder for Team 28: `team28_flying_drones/` (or similar)
3. Upload all files from this repository:
   - `step1/02_step1_flying_drones_team28.ipynb`
   - `q4/04_q4_patents_vs_secrecy_team28.ipynb`
   - `CPC_CODES_REFERENCE.md` (for reference during analysis)

### Option B: Clone This Repository on TIP
If TIP supports terminal access:
```bash
cd ~/projects
git clone https://github.com/Drassik/Patent-study.git
cd Patent-study
```

---

## Step 2: Run Step 1 Notebook (General Description)

### 2.1 Development Run (TEST environment)

1. Open `step1/02_step1_flying_drones_team28.ipynb` in TIP Jupyter
2. Check the configuration at the top:
   ```python
   ENV = "TEST"                 # Keep as TEST for now
   YEAR_MIN, YEAR_MAX = 2000, 2025
   USE_KEYWORDS = False         # Start without keywords (faster)
   ```
3. **Run all cells** (Kernel → Restart Kernel and Run All Cells)
4. Watch the output:
   - **Step 0 check** (Section 2.1b): Read the sample titles to verify the CPC definition catches real drones
   - **Figures**: Charts will display; check them for obvious errors
   - **Exports**: CSV tables will be saved to `outputs/step1_flying_drones/` (TEST files)

### 2.2 Review Step 0 Results

In **Section 2.1b** (Step 0 check), you'll see:
```
CPC codes: N families
keywords: N families (if enabled)
keywords only: N families
sector (union): N families
```

**Action items:**
- **Review sample titles** in the precision checks (Cells 7 and 8)
  - Cell 7: CPC code matches (should be real drones) ✓
  - Cell 8: Keywords-only matches (risky; check for false positives)
- **If keyword false positives** → edit `SECTOR_KEYWORDS` and re-run
- **If CPC doesn't catch enough** → check `CPC_CODES_REFERENCE.md` for alternative codes

### 2.3 Enable Keywords and Re-run (still TEST)

Once confident about the CPC definition:
```python
USE_KEYWORDS = True           # Now enable keywords
```
Re-run the notebook. The keyword search will be slower on PATSTAT, but only in TEST: it's still manageable.

### 2.4 Check TEST Outputs

After successful TEST run, examine the outputs in `outputs/step1_flying_drones/`:
- `step0_counts_TEST.csv`: Family counts by definition part
- `volume_per_year_TEST.csv`: Families and applications per year
- `growth_TEST.csv`: Growth rates vs. all patents
- `cpc_subclass_shares_TEST.csv`: CPC mix (you'll need to fill the "definition" column from the CPC scheme)
- `fig_*.png`: All figures

**Important for the deck:**
- In `cpc_subclass_shares_TEST.csv`, the last column "definition" is empty
- Fill it with official CPC titles from https://www.cooperativepatentclassification.org
- Example: `B64U` → "Unmanned aerial vehicles (UAVs)"

---

## Step 3: Switch to PROD and Generate Final Numbers

### 3.1 Update Configuration
```python
ENV = "PROD"                  # Switch to production
USE_KEYWORDS = True           # Keep keywords enabled
```

### 3.2 Run All Cells (PROD)

**Warning**: The PROD run searches the entire PATSTAT database; it may take **several minutes to over an hour** depending on the keyword search complexity. On TIP, this typically runs in the background.

Re-run: Kernel → Restart Kernel and Run All Cells

### 3.3 PROD Outputs

New files will be generated with `_PROD` suffix:
- `*_PROD.csv` tables (final numbers)
- `fig_*.png` (final figures)

The `_TEST.csv` files are overwritten (or check git to keep the TEST runs for comparison).

---

## Step 4: Run Q4 Notebook (Patents vs. Secrecy)

### 4.1 Development Run (TEST)

1. Open `q4/04_q4_patents_vs_secrecy_team28.ipynb`
2. Keep `ENV = "TEST"` and `LAST_COMPLETE_YEAR` as configured
3. Run all cells
4. Review Section 2.1 (military precision check):
   - Read sample titles of military drone families
   - Remove or tighten any overly broad codes (e.g., `F41` catches too much)

### 4.2 Key Outputs (TEST)

Watch for:
- **Section 4**: `q4_indicators_TEST.csv` → compare drones vs. benchmarks
- **Section 5**: Growth curves and drone split (military/dual-use/civil)
- **Section 6**: Applicant sectors → who files drone patents?
- **Section 7**: Defence primes → how many families by Leonardo, Lockheed, etc.?

### 4.3 Switch to PROD

```python
ENV = "PROD"
```
Re-run the notebook. Final numbers go to `outputs/q4_secrecy/*_PROD.csv` and figures.

---

## Step 5: Download Outputs and Build Slides

### 5.1 Download from TIP

On TIP, right-click the `outputs/` folder → **Download**. This creates a `.zip` with all CSVs and PNGs.

### 5.2 Use CSVs and Figures in Your Deck

All tables are ready for the presentation deck:

| Notebook | CSV Table | Deck Section |
|---|---|---|
| **Step 1** | `volume_per_year_PROD.csv` | "How big is the sector?" |
| | `growth_PROD.csv` | Growth rates |
| | `cpc_subclass_shares_PROD.csv` | Technology mix (with definitions filled) |
| | `wipo_techn_sector_shares_PROD.csv` | WIPO sectors breakdown |
| | `office_shares_PROD.csv` | Geography (IP5 offices) |
| | `country_shares_PROD.csv` | Applicant and inventor countries |
| **Q4** | `q4_indicators_PROD.csv` | "Is it patent-heavy?" |
| | `q4_families_per_year_PROD.csv` | Drones vs. benchmarks growth |
| | `q4_applicant_sectors_PROD.csv` | Who files? (company vs. government) |
| | `q4_defence_primes_PROD.csv` | Defence primes patent counts |

---

## Step 6: Technical Appendix (Important!)

Include in your deck's technical appendix:

### Data Source & Completeness
- **Database**: PATSTAT (EPO), snapshot from [DATE OF TIP ACCESS]
- **Families**: All families with earliest priority year between 2000–[LAST_COMPLETE_YEAR]
- **Unit**: Families (one invention = one count at family level); counted by earliest priority year
- **IPR Type**: Patents of Invention (PI) only; utility models excluded
- **Incomplete years**: Last [TRUNCATED_YEARS] years are not included in growth analysis (shaded grey in figures)

### Sector Definition
See `CPC_CODES_REFERENCE.md` in the project repo for official definitions.

**Flying Drones**: Families with CPC codes:
- `B64U` — Unmanned aerial vehicles (main code since 2023)
- `B64C39/024` — Aircraft of remote-controlled vehicle type (pre-2023)
- `B64C2201` — Former UAV indexing scheme (legacy)
- Keywords (if used): "unmanned aerial vehicle", "unmanned aircraft", "aerial drone", etc.

**Step 0 precision check** (in notebook): [NUMBER] families found. Sample review confirmed [STATEMENT ABOUT PRECISION].

### Methodology
- **Fractional counting**: Each family divided equally among its applicants, inventors, CPC classes (shares sum to 100%)
- **Family size**: Number of applications protecting the same invention (at family level)
- **PCT**: International applications filed through the Patent Cooperation Treaty
- **IP5**: European (EP), US, Chinese (CN), Japanese (JP), Korean (KR) patent offices

### Limitations
- **Secrecy is unmeasured**: PATSTAT contains published patents only; secret patents, R&D, and market size are not observable
- **CPC assignment**: Based on title/abstract; some false positives/negatives possible
  - Military codes (B64U2101/15–19) are not assigned to every military drone; some use generic `B64U`
  - Weapons codes (F41, F42B) catch related technologies but may include non-drone patents
- **Name matching**: Applicant names are approximate; one company may have multiple names (name harmonisation needed for Step 2)
- **Benchmark comparison**: Manned aircraft and road vehicles are coarse comparisons; sector-specific context is needed

### Suggested Next Steps
- **Step 2** (patenting strategy): Name harmonisation to group applicants correctly
- **Step 3** (technical depth): IPC/technology field analysis in detail
- **External sources**: Interviews, procurement data, market reports (Leonardo, defence agencies) for a complete picture

---

## Troubleshooting

### Error: "TLS201_APPLN table not found"
- TIP must have active PATSTAT database connection
- Check with your TIP administrator

### Error: "Query timeout" (large dataset)
- The keyword search on PROD can be slow
- Try disabling keywords first: `USE_KEYWORDS = False`
- Or run on a smaller year range: `YEAR_MIN, YEAR_MAX = 2015, 2025`

### Missing outputs folder after run
- Check TIP's file system; the notebook creates `outputs/step1_flying_drones/` and `outputs/q4_secrecy/`
- If missing, check for errors in notebook execution

### Figures not displaying (matplotlib issues)
- TIP should handle `plt.show()` automatically
- Check cell outputs for any warnings

---

## Timeline Estimate

- **Setup**: 5 min
- **TEST run (Step 1, no keywords)**: 5–10 min
- **Review & precision check**: 10 min
- **TEST run (Step 1, with keywords)**: 10–15 min
- **PROD run (Step 1)**: 15–30 min
- **TEST run (Q4)**: 5–10 min
- **PROD run (Q4)**: 10–20 min
- **Total**: ~1–2 hours (mostly waiting for PROD database queries)

---

## Team Notes

- **Beybin**: CPC codes and definitions (✓ completed in `CPC_CODES_REFERENCE.md`)
- **Omar, Nina, Parsa, Samu**: Running on TIP, reviewing outputs, building deck slides
- Coordinate: Share TEST outputs with team for feedback before final PROD run

---

*Last updated: 2026-10-18*
*Reference: Course tutorial, PATSTAT documentation, EPO TIP user guide*
