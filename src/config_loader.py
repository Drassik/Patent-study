"""Configuration loader and official CPC/IPC taxonomy helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "sector.yaml"


def load_config(config_path: Optional[Path | str] = None) -> Dict[str, Any]:
    """Load and validate the central sector configuration YAML."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Sector config not found at {path}")
    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    required_sections = ("project", "time_window", "counting_rules", "step0", "q4_secrecy")
    missing = [sec for sec in required_sections if sec not in cfg]
    if missing:
        raise ValueError(f"Missing required sections in {path}: {missing}")
    return cfg


def get_last_complete_year(cfg: Dict[str, Any]) -> int:
    """Return the last non-truncated priority/filing year."""
    tw = cfg["time_window"]
    return int(tw["year_max"]) - int(tw["truncation_years"])


def get_cpc_subclass_definition(subclass: str, cfg: Dict[str, Any]) -> str:
    """Return the official CPC title for a 4-character subclass code."""
    code = str(subclass).strip().upper()[:4]
    if code == "OTHE" or str(subclass).strip().lower() == "other":
        return "All remaining co-classified CPC subclasses pooled"
    subclasses = cfg.get("cpc_definitions", {}).get("subclasses", {})
    return subclasses.get(code, "Check official CPC scheme (cooperativepatentclassification.org)")


def get_b64u_group_definition(group_code: str, cfg: Dict[str, Any]) -> str:
    """Return the official CPC title for a B64U main group prefix (e.g. 'B64U10/')."""
    normalized = str(group_code).replace(" ", "").upper()
    groups = cfg.get("cpc_definitions", {}).get("b64u_main_groups", {})
    for prefix, title in groups.items():
        if normalized.startswith(prefix):
            return title
    return "Check official CPC B64U scheme"
