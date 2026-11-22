from collections.abc import Callable
from pathlib import Path
from epo.tipdata.patstat import PatstatClient
from epo.tipdata.patstat.database.models import (
    TLS201_APPLN,
    TLS202_APPLN_TITLE,
    TLS203_APPLN_ABSTR,
    TLS209_APPLN_IPC,
    TLS224_APPLN_CPC,
)
import pandas as pd
from sqlalchemy import func, or_
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract(
    patstat: PatstatClient,
    ids: list[int],
    out_path: Path,
    query: Callable[[list[int]], object],
    chunk_size: int = 5000,
) -> pd.DataFrame:
    if out_path.exists():
        print(f"[CACHE] Loading {out_path.name}")
        return pd.read_csv(out_path)

    chunks = [
        df
        for start in range(0, len(ids), chunk_size)
        if not (df := patstat.df(query(ids[start : start + chunk_size]))).empty
    ]

    df_out = pd.concat(chunks, ignore_index=True).drop_duplicates() if chunks else pd.DataFrame()
    df_out.to_csv(out_path, index=False)
    print(f"[SAVED] {out_path.name}: {len(df_out):,} rows")
    return df_out


def extract_family_roster(db, patstat: PatstatClient, cfg: dict, raw_dir: Path) -> pd.DataFrame:
    out_path = raw_dir / "00_family_roster.csv"
    if out_path.exists():
        print(f"[CACHE] Loading {out_path.name}")
        return pd.read_csv(out_path)

    meta, q_cfg, w_cfg = cfg["metadata"], cfg["query"], cfg["window"]

    def base_query(*columns):
        return db.query(*columns).select_from(TLS201_APPLN).filter(
            TLS201_APPLN.ipr_type == meta["ipr_type"],
            TLS201_APPLN.appln_id < meta["max_valid_appln_id"],
            TLS201_APPLN.earliest_filing_year.between(w_cfg["year_min"], w_cfg["year_max"]),
        )

    # 1. Strato CORE (CPC + IPC)
    schemes = [
        (TLS224_APPLN_CPC, TLS224_APPLN_CPC.cpc_class_symbol, q_cfg["core_cpc_prefixes"]),
        (TLS209_APPLN_IPC, TLS209_APPLN_IPC.ipc_class_symbol, q_cfg["core_ipc_prefixes"]),
    ]
    core_dfs = [
        patstat.df(
            base_query(TLS201_APPLN.docdb_family_id)
            .join(model, model.appln_id == TLS201_APPLN.appln_id)
            .filter(or_(*(func.replace(col, " ", "").like(p) for p in [*q_cfg["core_shared_prefixes"], *prefixes])))
            .distinct()
        )
        for model, col, prefixes in schemes
    ]
    df_core = pd.concat(core_dfs, ignore_index=True).drop_duplicates().assign(stratum="core")

    # 2. Strato BOUNDARY_RESCUE
    q_boundary = (
        base_query(
            TLS201_APPLN.docdb_family_id,
            TLS202_APPLN_TITLE.appln_title.label("title"),
            TLS203_APPLN_ABSTR.appln_abstract.label("abstract"),
        )
        .join(TLS202_APPLN_TITLE, TLS202_APPLN_TITLE.appln_id == TLS201_APPLN.appln_id)
        .join(TLS203_APPLN_ABSTR, TLS203_APPLN_ABSTR.appln_id == TLS201_APPLN.appln_id)
        .join(TLS224_APPLN_CPC, TLS224_APPLN_CPC.appln_id == TLS201_APPLN.appln_id)
        .filter(
            TLS202_APPLN_TITLE.appln_title_lg == "en",
            TLS203_APPLN_ABSTR.appln_abstract_lg == "en",
            or_(*(func.replace(TLS224_APPLN_CPC.cpc_class_symbol, " ", "").like(g) for g in q_cfg["boundary_subgroups"])),
        )
    )

    pos_kw = "(?:" + "|".join(q_cfg["pos_keywords"]) + ")"
    neg_kw = "(?:" + "|".join(q_cfg["neg_keywords"]) + ")"

    df_b = (
        patstat.df(q_boundary)
        .drop_duplicates(subset=["docdb_family_id"], keep="first")
        .query("docdb_family_id not in @df_core.docdb_family_id")
    )
    text = df_b["title"].fillna("") + ". " + df_b["abstract"].fillna("")
    keep = text.str.contains(pos_kw, case=False, na=False) & ~text.str.contains(neg_kw, case=False, na=False)

    df_rescue = df_b.loc[keep, ["docdb_family_id"]].assign(stratum="boundary_rescue")

    # 3. Unione e salvataggio
    df_roster = pd.concat([df_core, df_rescue], ignore_index=True)
    df_roster.to_csv(out_path, index=False)
    print(f"[SAVED] {out_path.name}: {len(df_core):,} core + {len(df_rescue):,} rescue = {len(df_roster):,} families")
    return df_roster


def main():
    patstat = PatstatClient(env="PROD")
    cfg = load_config(PROJECT_ROOT / "config/sector.yaml")

    raw_dir = PROJECT_ROOT / "data/raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    df_roster = extract_family_roster(patstat.orm(), patstat, cfg, raw_dir)
    # family_ids = df_roster["docdb_family_id"].tolist()


if __name__ == "__main__":
    main()