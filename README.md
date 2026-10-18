# Patent study · Team 28 · Flying drones (client: Leonardo)

Project Work for Innovation Management 2026/27, Politecnico di Torino. The notebooks run on the EPO Technology Intelligence Platform (TIP) against PATSTAT, and build on the course tutorials in [graziasveva/innovation-management-datascience26](https://github.com/graziasveva/innovation-management-datascience26).

| Folder | Content |
|---|---|
| `step1/` | `02_step1_flying_drones_team28.ipynb`: the course Step 1 notebook adapted to flying drones (CPC B64U, B64C39/024, B64C2201 plus keywords), with a Step 0 precision check and CSV/PNG export |
| `q4/` | `04_q4_patents_vs_secrecy_team28.ipynb`: Step 1, question 4, "Is the field patent-heavy, or does it rely on secrecy?" (drones split into military / dual-use / civil, compared with manned aircraft and autonomous road vehicles) |

## How to run on TIP
1. Upload the notebook into TIP, next to the course `tutorial_0` folder (or clone this repo in a TIP terminal).
2. Run with `ENV = "TEST"` first (Kernel → Restart Kernel and Run All Cells), check the precision samples.
3. Set `ENV = "PROD"` and run again for the final numbers. Outputs go to `outputs/...` as CSV and PNG.

The sector definition (CPC codes, keywords) is shared by all questions: change it in one place and keep the notebooks consistent.
