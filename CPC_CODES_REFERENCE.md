# CPC & IPC Codes Reference · Flying Drones (Team 28)

Verified against the official EPO/USPTO Cooperative Patent Classification (CPC) and WIPO IPC schemes (`https://www.cooperativepatentclassification.org/cpcSchemeAndDefinitions/table`).

---

## 1. Main Sector Definition & Step 0 Taxonomy Audit (Nov 18 Diagnosis)

### Tier 1 — Unconditional Aerial-Exclusive Core (`CPC ∪ IPC`)
| Scheme | Code | Official Title | Role in Step 0 |
|---|---|---|---|
| CPC / IPC | `B64U` | **Unmanned aerial vehicles [UAVs]; equipment therefor** | Dedicated UAV subclass introduced in 2023; IPC `B64U` recovers CN/JP/KR families lacking CPC reclassification |
| CPC only | `B64C 39/024` | **Aircraft of the remote-controlled vehicle type, i.e. RPV** | Primary pre-2023 CPC home for UAVs |
| CPC only | `B64C 2201` | **Former indexing scheme for UAVs** | Moved to `B64U` in 2023; kept as safety net for non-reclassified records |
| CPC | `G08G 5/57` | **Air traffic control / guidance specifically for unmanned aircraft** | Exclusively aerial UAVs |
| CPC | `G08G 5/27` | **Air traffic control for managing network coverage (e.g. transmission connections for UAVs)** | Exclusively aerial UAVs |

### Tier 2 — Boundary Rescue (Requires Calibrated Positive UAV Keywords AND NOT Negative Keywords)
| Scheme | Code | Official Title | Why Keyword-Gated (Not Unconditional Core) |
|---|---|---|---|
| IPC | `B64C 39/02` | **Aircraft not otherwise provided for — characterised by special use** | **Critical audit finding:** Unlike CPC `B64C 39/024` (RPVs), IPC `B64C 39/02` includes manned special-use aircraft. Placing IPC `B64C 39/02` in unconditional Core reduced Core precision to 51.4% (37/72) in the Nov 18 audit. Moving IPC-only `B64C 39/02` into keyword-gated Boundary Rescue preserves historical CN/JP/KR UAV recovery while eliminating manned-aircraft noise. |
| CPC | `G05D 1/228` | **Command input arrangements located on-board unmanned vehicles** | Covers **all** unmanned vehicles (ground UGVs, marine USVs/AUVs, and aerial UAVs). Gating by aerial UAV keywords prevents ground/marine robotics contamination. |
| CPC | `G05D 1/` & `G08G 5/` | **Autonomous vehicle control / Air traffic management** | High-purity boundary subgroups (e.g. `G08G 5/59` geofencing 72.0% purity, `G08G 5/55` 62.9% purity) rescued with calibrated positive/negative regex (92.9% precision in Nov 18 audit). |

---

## 2. Official `B64U` Main Group Hierarchy (Corrected)

| CPC Main Group | Official CPC Title |
|---|---|
| `B64U 10/00` | **Type of UAV** (rotorcrafts, multirotors, quadcopters, VTOL, fixed-wing, tethered, lighter-than-air, ornithopters, MAVs) |
| `B64U 20/00` | **Constructional aspects of UAVs** (airframes, foldable structures, stealth shells, payload mounts; excludes lift means in 30/00) |
| `B64U 30/00` | **Means for producing lift; empennages; arrangements thereof** (wings, rotors, ducted fans) |
| `B64U 40/00` | **On-board mechanical arrangements for adjusting control surfaces or rotors; in-flight adjustment of base configuration** |
| `B64U 50/00` | **Propulsion; power supply** (motors, power transmission, batteries, fuel cells, solar, in-flight charging) |
| `B64U 60/00` | **Undercarriages** (landing gear, skids, shock absorbers) |
| `B64U 70/00` | **Launching, take-off, or landing arrangements** (catapults, arresting nets, automated docking stations) |
| `B64U 80/00` | **Transport or storage specially adapted for UAVs** (carrying cases, mobile hangars) |
| `B64U 2101/00` | **Indexing scheme: UAVs characterised by intended use** (warfare, surveillance, delivery, agriculture, inspection) |
| `B64U 2201/00` | **Indexing scheme: UAV control, navigation, and communication aspects** |

---

## 3. Step 1 Q4: Military, Dual-Use & Benchmark Codes

### Military UAV Codes (Mutually Exclusive Priority 1)
- `B64U 2101/15`: For conventional or electronic warfare
- `B64U 2101/16`: For controlling, capturing or immobilising other vehicles (counter-UAS / swarm interception)
- `B64U 2101/17`: For detecting, disrupting or countering communications (SIGINT / EW)
- `B64U 2101/18`: For dropping bombs; for firing ammunition
- `B64U 2101/19`: For use as targets or decoys
- Co-classifications with `F41` (Weapons) and `F42B 10/`, `F42B 12/`, `F42B 15/` (Guided projectiles / warheads / missiles)

### Dual-Use (Surveillance / ISR) Code (Priority 2, excluding Military)
- `B64U 2101/31`: For surveillance, inspection or monitoring

### External Benchmarks (Excluding all UAV families)
- **Manned aircraft:** `B64C`, `B64D` (minus all locked UAV families)
- **Autonomous road vehicles:** `B60W 60/` (automated driving vehicles, minus all locked UAV families)

---

## 4. Academic Literature Basis for Query & Vocabulary

Per Prof. Ascione's guidance on grounding sector vocabulary and classification choices in academic literature:
- **Zheng, X., Chen, X., Zhang, P., & Liu, F. (2026).** *Evolutionary pathways and future trends of civil UAV technologies: A patent-based data-driven analysis.* Inventions, 11(6), 117. (`doi:10.3390/inventions11060117`) — Maps civil UAV trajectories across `B64U`/`B64C` into autonomy, swarm intelligence, and low-altitude networked systems.
- **Journal of Open Innovation (2020).** *Analysis of technological trends and technological portfolio of unmanned aerial vehicle.* J. Open Innov. Technol. Mark. Complex., 6(3), 48. (`doi:10.3390/joitmc6030048`) — Combines `B64C` aeronautical classifications with UAV keywords to evaluate technological portfolios.
- **Choe, W. B. (2023).** *Analysis of technology trends in unmanned aerial vehicles using patent information.* J. Korean Soc. Nondestructive Testing, 6(3), 336–347. (`doi:10.31818/JKNST.2023.09.6.3.336`) — Quantifies UAV classification concentration and structural shifts.
- **Acosta, M., Coronado, D., & Marín, R. (2018).** *Patents and dual-use technology: An empirical study of the world's largest defence companies.* Defence and Peace Economics, 29(7), 821–839. — PATSTAT empirical baseline for defence vs. dual-use patenting propensity.
