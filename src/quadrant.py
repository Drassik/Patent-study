"""Steps 5 & 6: Gartner-Style Magic Quadrant & Core Competence RTA (PW Slides 15–16).

Implements:
  - Step 5: Magic Quadrant assignment (Leaders, Challengers, Visionaries, Niche Players)
    and publication-quality 300-DPI bubble plot (X = Future Score, Y = Present Score,
    Bubble size = DOCDB families, Orange highlight = Recommended target/partner).
  - Step 6: Revealed Technological Advantage (RTA; Patel & Pavitt, 1997) and CPC breadth
    to support the Core Competence analysis (Prahalad & Hamel, 1990).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def assign_magic_quadrant(
    present_scores: pd.Series,
    future_scores: pd.Series,
    families: pd.Series,
    present_threshold: Optional[float] = None,
    future_threshold: Optional[float] = None,
    threshold_method: str = "median",
) -> Tuple[pd.DataFrame, float, float]:
    """Place scored firms onto the four Magic Quadrant cells (PW Slide 15).

    Quadrants:
      - Leaders       : present >= y_thr and future >= x_thr
      - Challengers   : present >= y_thr and future <  x_thr
      - Visionaries   : present <  y_thr and future >= x_thr
      - Niche Players : present <  y_thr and future <  x_thr
    """
    common = present_scores.index.intersection(future_scores.index).intersection(families.index)
    df = pd.DataFrame(
        {
            "present_score": present_scores.loc[common].astype(float),
            "future_score": future_scores.loc[common].astype(float),
            "families": families.loc[common].astype(int),
        }
    )
    if df.empty:
        raise ValueError("No overlapping firms across present_scores, future_scores, and families")

    if present_threshold is not None:
        y_thr = float(present_threshold)
    elif threshold_method == "mean":
        y_thr = float(df["present_score"].mean())
    else:
        y_thr = float(df["present_score"].median())

    if future_threshold is not None:
        x_thr = float(future_threshold)
    elif threshold_method == "mean":
        x_thr = float(df["future_score"].mean())
    else:
        x_thr = float(df["future_score"].median())

    def _label(row: pd.Series) -> str:
        hi_p = row["present_score"] >= y_thr
        hi_f = row["future_score"] >= x_thr
        if hi_p and hi_f:
            return "Leaders"
        if hi_p and not hi_f:
            return "Challengers"
        if not hi_p and hi_f:
            return "Visionaries"
        return "Niche Players"

    df["quadrant"] = df.apply(_label, axis=1)
    df.index.name = "firm"
    return df, x_thr, y_thr


def plot_magic_quadrant(
    quadrant_df: pd.DataFrame,
    x_thr: float,
    y_thr: float,
    recommended_firm: Optional[str] = None,
    client_firm: Optional[str] = "LEONARDO",
    title: str = "Flying Drones · Patent-Based Magic Quadrant (Team 28)",
    save_path: Optional[Path | str] = None,
) -> plt.Figure:
    """Render a publication-ready Magic Quadrant matching PW Slide 15 conventions."""
    fig, ax = plt.subplots(figsize=(10.5, 7.2))

    x = quadrant_df["future_score"]
    y = quadrant_df["present_score"]
    x_pad = max((x.max() - x.min()) * 0.14, 5.0)
    y_pad = max((y.max() - y.min()) * 0.14, 5.0)
    xlim = (x.min() - x_pad, x.max() + x_pad)
    ylim = (y.min() - y_pad, y.max() + y_pad)

    # Subtle quadrant shading matching PW Slide 15
    ax.axvspan(x_thr, xlim[1], ymin=(y_thr - ylim[0]) / (ylim[1] - ylim[0]), ymax=1.0, color="#d6eaf8", alpha=0.35, zorder=0)
    ax.axvspan(x_thr, xlim[1], ymin=0.0, ymax=(y_thr - ylim[0]) / (ylim[1] - ylim[0]), color="#fdebd0", alpha=0.45, zorder=0)
    ax.axvline(x_thr, color="#566573", ls="--", lw=1.1, zorder=1)
    ax.axhline(y_thr, color="#566573", ls="--", lw=1.1, zorder=1)

    # Bubble sizes proportional to sqrt(families) so giant portfolios do not obscure specialists
    fams = quadrant_df["families"].astype(float)
    sizes = 90.0 + 750.0 * (np.sqrt(fams) / max(np.sqrt(fams.max()), 1.0))

    colors = []
    for firm in quadrant_df.index:
        if recommended_firm is not None and firm == recommended_firm:
            colors.append("#e67e22")   # Orange = recommended target/partner (Slide 15 rule)
        elif client_firm is not None and firm == client_firm:
            colors.append("#2e86c1")   # Accent blue = Client (Leonardo)
        else:
            colors.append("#1b2631")   # Navy = other firms

    ax.scatter(x, y, s=sizes, c=colors, alpha=0.88, edgecolors="white", linewidths=1.2, zorder=3)

    for firm, row in quadrant_df.iterrows():
        label = f"{firm} ★" if firm == recommended_firm else (f"{firm} (Client)" if firm == client_firm else firm)
        weight = "bold" if firm in (recommended_firm, client_firm) else "normal"
        ax.annotate(
            label,
            (row["future_score"], row["present_score"]),
            xytext=(7, 5),
            textcoords="offset points",
            fontsize=8.5,
            fontweight=weight,
            color="#1b2631",
            zorder=4,
        )

    # Quadrant corner headings
    kw = dict(fontsize=9.5, fontweight="bold", color="#34495e", alpha=0.85)
    ax.text(xlim[0] + x_pad * 0.15, ylim[1] - y_pad * 0.25, "CHALLENGERS\n(high present · low future)", va="top", ha="left", **kw)
    ax.text(xlim[1] - x_pad * 0.15, ylim[1] - y_pad * 0.25, "LEADERS\n(high present · high future)", va="top", ha="right", **kw)
    ax.text(xlim[0] + x_pad * 0.15, ylim[0] + y_pad * 0.20, "NICHE PLAYERS\n(low present · low future)", va="bottom", ha="left", **kw)
    ax.text(xlim[1] - x_pad * 0.15, ylim[0] + y_pad * 0.20, "VISIONARIES\n(low present · high future)", va="bottom", ha="right", **kw)

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("Future score · completeness of vision →", fontsize=11, fontweight="bold")
    ax.set_ylabel("Present score · ability to execute →", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=12.5, fontweight="bold", pad=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    if save_path is not None:
        out = Path(save_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=300, bbox_inches="tight")
    return fig


def compute_revealed_technological_advantage(
    firm_cpc_counts: pd.DataFrame,
) -> pd.DataFrame:
    """Compute Revealed Technological Advantage (Patel & Pavitt, 1997) for Step 6 Core Competences.

    RTA_{f,c} = (P_{f,c} / sum_{c'} P_{f,c'}) / (sum_{f'} P_{f',c} / sum_{f',c'} P_{f',c'})

    Values > 1.0 indicate that firm f is relatively specialized in technology class c
    compared with the overall sector portfolio (hard-to-imitate technological competence).

    Parameters
    ----------
    firm_cpc_counts : DataFrame with index = firms, columns = CPC subclasses/groups, values = family counts
    """
    counts = firm_cpc_counts.astype(float)
    firm_totals = counts.sum(axis=1).replace(0.0, np.nan)
    class_totals = counts.sum(axis=0).replace(0.0, np.nan)
    grand_total = float(counts.to_numpy().sum())
    if grand_total <= 0:
        raise ValueError("firm_cpc_counts has zero total")

    firm_shares = counts.div(firm_totals, axis=0)
    sector_shares = class_totals / grand_total
    return firm_shares.div(sector_shares, axis=1).fillna(0.0)
