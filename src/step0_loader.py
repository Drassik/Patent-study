"""Step 0 family-universe loader for Team 28 (Flying Drones).

Ensures that Step 1, Step 1 Q4, Step 2, and downstream valuation notebooks all
operate on the EXACT same locked DOCDB family universe produced by Step 0
(Query_Calibration_Taxonomy_Audit.ipynb -> uav_final_query_families.csv).

When the locked CSV is not yet available (e.g., rapid TEST iteration on TIP),
falls back transparently to building the sector family IDs from config/sector.yaml
using both CPC and IPC core prefixes.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd


def find_locked_step0_csv(
    cfg: Dict[str, Any],
    override_path: Optional[Path | str] = None,
) -> Optional[Path]:
    """Locate the locked Step 0 family CSV from an explicit path or config candidates."""
    if override_path is not None:
        p = Path(override_path)
        if not p.exists():
            raise FileNotFoundError(f"Explicit Step 0 CSV path not found: {p}")
        return p
    for candidate in cfg.get("step0", {}).get("locked_families_csv_candidates", []):
        p = Path(candidate)
        if p.exists():
            return p
    return None


def load_locked_step0_families(csv_path: Path | str) -> pd.DataFrame:
    """Load and validate Samuele's locked Step 0 DOCDB family table.

    Expected columns:
      - docdb_family_id (int, required)
      - query_source (str, optional: e.g. 'core_classification', 'boundary_rescue')
    """
    path = Path(csv_path)
    df = pd.read_csv(path)
    if "docdb_family_id" not in df.columns:
        raise ValueError(
            f"Locked Step 0 CSV {path} must contain column 'docdb_family_id'; "
            f"found {list(df.columns)}"
        )
    out = df.copy()
    out["docdb_family_id"] = pd.to_numeric(out["docdb_family_id"], errors="coerce")
    if out["docdb_family_id"].isna().any():
        raise ValueError(f"Found missing/non-numeric docdb_family_id values in {path}")
    out["docdb_family_id"] = out["docdb_family_id"].astype("int64")
    if "query_source" not in out.columns:
        out["query_source"] = "locked_step0"
    out = out.drop_duplicates(subset=["docdb_family_id"]).reset_index(drop=True)
    return out[["docdb_family_id", "query_source"]]


def iter_batches(items: Sequence[int], batch_size: int = 5000) -> Iterable[List[int]]:
    """Yield deterministic batches of integer IDs to avoid SQL IN-clause limits on TIP."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    unique_ids = list(dict.fromkeys(int(x) for x in items))
    for start in range(0, len(unique_ids), batch_size):
        yield unique_ids[start : start + batch_size]


def filter_text_by_keywords(
    df: pd.DataFrame,
    positive_patterns: Sequence[str],
    negative_patterns: Sequence[str],
    title_col: str = "title",
    abstract_col: str = "abstract",
) -> pd.Series:
    """Apply calibrated positive AND NOT negative regex keyword gate on title + abstract."""
    pos_re = re.compile("|".join(f"(?:{p})" for p in positive_patterns), re.IGNORECASE)
    neg_re = re.compile("|".join(f"(?:{p})" for p in negative_patterns), re.IGNORECASE)
    combined = (
        df[title_col].fillna("").astype(str)
        + ". "
        + df[abstract_col].fillna("").astype(str)
    )
    has_pos = combined.str.contains(pos_re, regex=True, na=False)
    has_neg = combined.str.contains(neg_re, regex=True, na=False)
    return has_pos & ~has_neg


def fetch_fallback_step0_families_tip(
    patstat: Any,
    db: Any,
    cfg: Dict[str, Any],
    include_boundary_rescue: bool = True,
    batch_size: int = 3000,
) -> pd.DataFrame:
    """Build the Step 0 DOCDB family universe live on TIP from config/sector.yaml.

    Implements the audited 2-tier query:
      1. Core Classification (unconditional): CPC core prefixes UNION IPC core prefixes (B64U).
         IPC B64C 39/02 and CPC G05D 1/228 are deliberately routed to Boundary Rescue so manned
         special-use aircraft and non-aerial UGVs do not contaminate Core precision.
      2. Boundary Rescue (optional, default True): non-core families in G05D 1/, G08G 5/, and
         IPC B64C 39/02 whose English title or abstract matches calibrated positive UAV keywords
         and does not match negative keywords.
    """
    from epo.tipdata.patstat.database.models import (
        TLS201_APPLN,
        TLS202_APPLN_TITLE,
        TLS203_APPLN_ABSTR,
        TLS209_APPLN_IPC,
        TLS224_APPLN_CPC,
    )
    from sqlalchemy import func, or_

    year_min = int(cfg["time_window"]["year_min"])
    year_max = int(cfg["time_window"]["year_max"])
    ipr_type = cfg["counting_rules"]["ipr_type"]
    s0 = cfg["step0"]

    def _prefix_cond(col, prefixes):
        clean = func.replace(col, " ", "")
        return or_(*(clean.like(p.replace(" ", "") + "%") for p in prefixes))

    # Tier 1a: Core CPC
    q_cpc = (
        db.query(TLS201_APPLN.docdb_family_id.label("docdb_family_id"))
        .select_from(TLS224_APPLN_CPC)
        .join(TLS201_APPLN, TLS224_APPLN_CPC.appln_id == TLS201_APPLN.appln_id)
        .filter(
            TLS201_APPLN.ipr_type == ipr_type,
            TLS201_APPLN.earliest_filing_year.between(year_min, year_max),
            _prefix_cond(TLS224_APPLN_CPC.cpc_class_symbol, s0["core_cpc_prefixes"]),
        )
        .distinct()
    )
    core_cpc = patstat.df(q_cpc)

    # Tier 1b: Core IPC (e.g. B64U — recovers CN/JP/KR reclassification lag without B64C39/02 noise)
    core_ipc_prefixes = s0.get("core_ipc_prefixes", [])
    if core_ipc_prefixes:
        q_ipc = (
            db.query(TLS201_APPLN.docdb_family_id.label("docdb_family_id"))
            .select_from(TLS209_APPLN_IPC)
            .join(TLS201_APPLN, TLS209_APPLN_IPC.appln_id == TLS201_APPLN.appln_id)
            .filter(
                TLS201_APPLN.ipr_type == ipr_type,
                TLS201_APPLN.earliest_filing_year.between(year_min, year_max),
                _prefix_cond(TLS209_APPLN_IPC.ipc_class_symbol, core_ipc_prefixes),
            )
            .distinct()
        )
        core_ipc = patstat.df(q_ipc)
    else:
        core_ipc = pd.DataFrame(columns=["docdb_family_id"])

    core_ids = set(
        pd.concat([core_cpc, core_ipc], ignore_index=True)["docdb_family_id"]
        .dropna()
        .astype("int64")
        .tolist()
    )
    parts = [
        pd.DataFrame(
            {"docdb_family_id": sorted(core_ids), "query_source": "core_classification"}
        )
    ]

    if not include_boundary_rescue:
        return parts[0]

    # Tier 2: Boundary Rescue (CPC boundary + IPC B64C39/02 gated by UAV keywords)
    cand_frames = []
    if s0.get("boundary_cpc_prefixes"):
        q_bcpc = (
            db.query(TLS201_APPLN.docdb_family_id.label("docdb_family_id"))
            .select_from(TLS224_APPLN_CPC)
            .join(TLS201_APPLN, TLS224_APPLN_CPC.appln_id == TLS201_APPLN.appln_id)
            .filter(
                TLS201_APPLN.ipr_type == ipr_type,
                TLS201_APPLN.earliest_filing_year.between(year_min, year_max),
                _prefix_cond(TLS224_APPLN_CPC.cpc_class_symbol, s0["boundary_cpc_prefixes"]),
            )
            .distinct()
        )
        cand_frames.append(patstat.df(q_bcpc))

    if s0.get("boundary_ipc_prefixes"):
        q_bipc = (
            db.query(TLS201_APPLN.docdb_family_id.label("docdb_family_id"))
            .select_from(TLS209_APPLN_IPC)
            .join(TLS201_APPLN, TLS209_APPLN_IPC.appln_id == TLS201_APPLN.appln_id)
            .filter(
                TLS201_APPLN.ipr_type == ipr_type,
                TLS201_APPLN.earliest_filing_year.between(year_min, year_max),
                _prefix_cond(TLS209_APPLN_IPC.ipc_class_symbol, s0["boundary_ipc_prefixes"]),
            )
            .distinct()
        )
        cand_frames.append(patstat.df(q_bipc))

    if cand_frames:
        cand_all = (
            pd.concat(cand_frames, ignore_index=True)["docdb_family_id"]
            .dropna()
            .astype("int64")
            .unique()
        )
        cand_non_core = [int(x) for x in cand_all if int(x) not in core_ids]
        text_frames = []
        for batch in iter_batches(cand_non_core, batch_size=batch_size):
            q_txt = (
                db.query(
                    TLS201_APPLN.docdb_family_id.label("docdb_family_id"),
                    TLS202_APPLN_TITLE.appln_title.label("title"),
                    TLS203_APPLN_ABSTR.appln_abstract.label("abstract"),
                )
                .select_from(TLS201_APPLN)
                .outerjoin(TLS202_APPLN_TITLE, TLS202_APPLN_TITLE.appln_id == TLS201_APPLN.appln_id)
                .outerjoin(TLS203_APPLN_ABSTR, TLS203_APPLN_ABSTR.appln_id == TLS201_APPLN.appln_id)
                .filter(
                    TLS201_APPLN.docdb_family_id.in_(batch),
                    TLS201_APPLN.ipr_type == ipr_type,
                    TLS201_APPLN.earliest_filing_year.between(year_min, year_max),
                    or_(
                        TLS202_APPLN_TITLE.appln_title_lg == "en",
                        TLS203_APPLN_ABSTR.appln_abstract_lg == "en",
                    ),
                )
            )
            chunk = patstat.df(q_txt)
            if chunk is not None and not chunk.empty:
                text_frames.append(chunk)

        if text_frames:
            raw_txt = pd.concat(text_frames, ignore_index=True)
            mask = filter_text_by_keywords(
                raw_txt,
                positive_patterns=s0["positive_keywords"],
                negative_patterns=s0["negative_keywords"],
            )
            rescued_ids = sorted(
                set(raw_txt.loc[mask, "docdb_family_id"].dropna().astype("int64").tolist())
                - core_ids
            )
            if rescued_ids:
                parts.append(
                    pd.DataFrame(
                        {"docdb_family_id": rescued_ids, "query_source": "boundary_rescue"}
                    )
                )

    return pd.concat(parts, ignore_index=True).drop_duplicates("docdb_family_id").reset_index(drop=True)


def get_step0_families(
    patstat: Any,
    db: Any,
    cfg: Dict[str, Any],
    override_csv_path: Optional[Path | str] = None,
    include_boundary_rescue: bool = True,
) -> Tuple[pd.DataFrame, str]:
    """Return (families_df, source_description) using locked CSV if present, else live query."""
    csv_path = find_locked_step0_csv(cfg, override_path=override_csv_path)
    if csv_path is not None:
        df = load_locked_step0_families(csv_path)
        return df, f"locked_csv:{csv_path}"
    df = fetch_fallback_step0_families_tip(
        patstat=patstat,
        db=db,
        cfg=cfg,
        include_boundary_rescue=include_boundary_rescue,
    )
    return df, "live_yaml_query"
