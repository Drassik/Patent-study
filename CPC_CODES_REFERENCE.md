# CPC Codes Reference · Flying Drones (Team 28)

## Main Sector Definition: Flying Drones (Unmanned Aerial Vehicles)

| CPC Code | Official Title | Usage | Notes |
|---|---|---|---|
| `B64U` | **Unmanned aerial vehicles (UAVs)** | Primary code | Dedicated subclass introduced in 2023; EPO reclassified older documents into it |
| `B64C39/024` | **Aircraft of the remote-controlled vehicle type (RPV)** | Legacy code | Main pre-2023 code for drones; widely used in historical data |
| `B64C2201` | **Former indexing scheme for UAVs** | Legacy code | Moved to B64U in 2023; kept as safety net for non-reclassified documents |

### CPC Code Hierarchy for Drones (B64U subcodes)
- `B64U` = General UAV classification
  - `B64U10/` = Characteristics of UAVs
  - `B64U20/` = Control systems and operational modes
  - `B64U30/` = UAVs with particular shapes or configurations
  - `B64U40/` = Propulsion systems
  - `B64U50/` = Payload or equipment
  - `B64U60/` = Ground support systems
  - `B64U70/` = Launching/landing
  - `B64U80/` = Power supply systems
  - `B64U90/` = Associated systems and methods
  - `B64U2101/` = **Use codes (purpose-based classification)**

---

## Military Drones: Use Codes (B64U2101)

The B64U2101 series classifies UAVs by their **intended use**. These are **not** mutually exclusive classifications.

| CPC Code | Official Title | Purpose |
|---|---|---|
| `B64U2101/15` | **For conventional or electronic warfare** | Electronic attack, jamming, EW operations |
| `B64U2101/16` | **For controlling, capturing or immobilising other vehicles** | Swarm control, interception, disabling |
| `B64U2101/17` | **For detecting, disrupting or countering communications** | Signal intelligence, communications disruption |
| `B64U2101/18` | **For dropping bombs; for firing ammunition** | Armed strikes, ordnance delivery |
| `B64U2101/19` | **For use as targets or decoys** | Training, target simulation, decoy operations |

### Note on Military Classification
- These codes indicate the **stated use** in the patent document
- Not all military drones may be classified with these codes (generic codes may be used instead)
- **Precision risk**: CPC assignment is based on the title/abstract; some civil patents might be co-classified with military codes if they mention dual-use technologies

---

## Dual-Use (Surveillance): Use Code (B64U2101)

| CPC Code | Official Title | Purpose |
|---|---|---|
| `B64U2101/31` | **For surveillance, inspection or monitoring** | Civil and military surveillance; includes civilian monitoring, inspection, data collection |

---

## Related Military/Weapons Classifications (Co-classifications)

| CPC Code | Official Title | Relevance |
|---|---|---|
| `F41` | **General or ordnance** | Weapons systems; co-classification indicates armed drone capability |
| `F42B10/` | **Projectiles or missiles characterised by aerodynamic features** | Missile design; indicates precision-guided ordnance |
| `F42B12/` | **Projectiles or missiles characterised by the warhead** | Warhead design; indicates armed capability |
| `F42B15/` | **Self-propelled projectiles or missiles** | Autonomous weapons; indicates advanced targeting |

---

## Benchmark Fields: Similar Technologies

### Manned Aircraft (for comparison)
| CPC Code | Official Title | Notes |
|---|---|---|
| `B64C` | **Aircraft: characteristics, construction, operation** | Parent class for all aircraft; includes manned and other aircraft types |
| `B64D` | **Equipment specifically designed for aircraft** | Supports systems for aircraft operation |

**Note for analysis**: Exclude all drone families (`B64U`, `B64C39/024`, `B64C2201`) from the manned aircraft benchmark to avoid overlap.

### Autonomous Road Vehicles (for comparison)
| CPC Code | Official Title | Notes |
|---|---|---|
| `B60W60/` | **Automated driving vehicles** | Autonomous ground vehicles; similar technology maturity and regulatory landscape |

---

## Defence Prime Companies (for applicant analysis)

### Major Prime Contractors (Defense & Aerospace)
| Company | PATSTAT Name Patterns | Relevance |
|---|---|---|
| **Leonardo** (Italian) | `LEONARDO S.p.A`, `FINMECCANICA`, `SELEX`, `ALENIA`, `AGUSTAWESTLAND` | Client for this project; major European defence prime |
| **Lockheed Martin** (US) | `LOCKHEED MARTIN` | US defence prime; largest segment in military UAVs |
| **Northrop Grumman** (US) | `NORTHROP GRUMMAN` | US defence prime; Global Hawk, MQ-4C developer |
| **Raytheon / RTX** (US) | `RAYTHEON` | US defence & aerospace; Tomahawk missiles, advanced systems |
| **Boeing** (US) | `BOEING` | US aerospace; diverse drone portfolio |
| **Airbus** (European) | `AIRBUS` | European aerospace; civilian and defence UAVs |
| **BAE Systems** (UK) | `BAE SYSTEMS` | UK defence prime; tactical UAVs |
| **Thales** (French) | `THALES` | French defence; sensors and systems |
| **General Atomics** (US) | `GENERAL ATOMICS` | US prime; Predator, Reaper developers |
| **Elbit Systems** (Israeli) | `ELBIT` | Israeli defence; tactical UAVs |
| **Israel Aerospace Industries** (Israeli) | `ISRAEL AEROSPACE` | Israeli aerospace; diverse UAV portfolio |
| **AeroVironment** (US) | `AEROVIRONMENT` | US civil/military; small tactical UAVs |

### Civilian Benchmark
| Company | PATSTAT Name Patterns | Relevance |
|---|---|---|
| **DJI** (Chinese) | `SZ DJI`, `DJI TECHNOLOGY`, `DA-JIANG` | World's largest commercial drone manufacturer |

---

## Data Quality Notes

### Completeness Issues
1. **CPC Reclassification (2023)**: Documents published before 2023 may use `B64C39/024` or `B64C2201` instead of `B64U`
2. **Use Codes (B64U2101)**: Not assigned to every military drone; many use generic `B64U` codes
3. **Name Harmonisation**: Companies appear under multiple names in PATSTAT; patterns are approximate

### Truncation (Incomplete Years)
- **Last 3 priority years** are incomplete in PATSTAT (documents still in pipeline, not yet reclassified)
- **Last 1 publication year** is incomplete
- Excluded from growth analysis; shaded in grey in figures

### Sectoral Classification (`psn_sector`)
- Values: `COMPANY`, `UNIVERSITY`, `GOV NON-PROFIT`, `INDIVIDUAL`, `HOSPITAL`, `UNKNOWN`
- Some applicants have no entry in `tls207_pers_appln` (missing from applicant mix)
- Coverage % is reported; if low, mention in technical appendix

---

## References

- **EPO CPC Scheme** (official): https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions/table
- **PATSTAT Documentation**: EPO internal; access via TIP
- **Course Material**: `graziasveva/innovation-management-datascience26` (GitHub)

---

## Verification Checklist

Before running PROD analysis:

- [ ] **B64U codes verified** against official CPC scheme (https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions/table)
- [ ] **Military use codes (B64U2101/15–19)** cover the intended scope
- [ ] **Dual-use code (B64U2101/31)** includes surveillance without misclassifying civil-only drones
- [ ] **Defence primes** name patterns checked against sample PATSTAT results (false positives?)
- [ ] **Benchmarks** (manned aircraft, road vehicles) confirmed to exclude drone families
- [ ] **Step 0 precision check** in `02_step1_flying_drones_team28.ipynb` confirms CPC definitions catch real drones
- [ ] **Military precision check** in `04_q4_patents_vs_secrecy_team28.ipynb` (Section 2.1) confirms military titles are actually military

---

*Last updated: 2026-10-18*
*Team: 28 (Beybin Çiçek, Boujendar Omar, Nina, Parsa, Samu)*
