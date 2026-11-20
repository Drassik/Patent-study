"""Step 2 Applicant Name Harmonization & Inventive Concentration Engine.

Addresses the PATSTAT 'name game' (Tutorial 11, Section 2) with a transparent,
multi-stage, zero-leakage entity resolution pipeline plus all six inventive
concentration metrics from Liston-Heyes & Pilkington (2004).

Stages of harmonization:
  1. Deep text normalization (Unicode NFKD, dotted legal forms, c/o & FKA stripping,
     parenthetical cleanup, comprehensive international legal-form dictionary).
  2. Institution-aware protection: universities, academies, institutes, and state bodies
     retain geographic tokens (e.g., BEIJING vs NANJING UNIVERSITY OF AERONAUTICS are
     never collapsed), while corporate subsidiaries drop regional branch suffixes.
  3. Distinctive corporate brand anchor discovery + typo merging (edit similarity on
     long distinctive anchors >= 9 chars, preventing short-word traps like NOKIA/NOKIAN).
  4. Joint-venture protection: names combining two distinct corporate brand anchors
     (e.g., NOKIA SIEMENS NETWORKS, SONY ERICSSON, FUJITSU TOSHIBA) stay separate.
  5. Optional domain corporate-tree consolidation from config/sector.yaml (Slide 9:
     'plus your own rules for subsidiaries', e.g. FINMECCANICA/SELEX -> LEONARDO).
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from math import comb
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import homogeneity_completeness_v_measure


# ------------------------------------------------------------------ Dictionaries
LEGAL_FORMS = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "COMPANIES",
    "LTD", "LIMITED", "LLC", "LP", "LLP", "PLC", "LIABILITY",
    "GMBH", "AG", "KG", "OHG", "MBH", "SE", "SA", "SAS", "SARL", "SPA", "SRL",
    "BV", "NV", "AB", "AS", "ASA", "OY", "OYJ", "CV", "KK", "KABUSHIKI",
    "KABUSHI", "KAISHA", "LTDA", "PTY", "BHD", "SDN", "PTE", "PVT", "THE",
    "AKTIENGESELLSCHAFT", "GESELLSCHAFT", "KOMMANDITGESELLSCHAFT",
    "HANDELSGESELLSCHAFT", "VERWALTUNGSGESELLSCHAFT", "SOCIETE", "SOC",
    "COMPAGNIE", "CIE", "ANONYME", "LIMITEE", "SNC", "SCPA", "SCA", "SAPA",
    "KGA", "KGAA", "EG", "EV", "UG", "VOF", "GCV", "SPOL", "SRO", "ZOO",
    "SP", "OOO", "ZAO", "OAO", "AO", "JSC", "OJSC", "PJSC",
    "HOLDING", "HOLDINGS", "GROUP", "GROUPE", "GRUPPE", "GRUPPO",
    "ET", "UND", "U", "AND", "OF", "DE", "DI", "DEL", "DELLA", "LA", "LE",
    "LES", "L", "D", "DER", "DES", "FUR", "FUER", "MIT", "IM", "A", "EN",
    "IN", "ON", "FOR", "TO", "BY", "AT", "DU", "ETABLISSEMENTS", "ETS",
    "FIRMA", "GEBR", "GEBRUDER", "KONINKLIJKE", "VERWALTUNG", "BETEILIGUNGS",
    "BETEILIGUNG", "STIFTUNG", "TRUST", "PARTNERS", "PARTNERSHIP",
}

GEO_TOKENS = {
    "USA", "US", "UK", "GB", "UNITED", "KINGDOM", "STATES", "AMERICA", "AMERICAS",
    "AMERICAN", "NORTH", "SOUTH", "EAST", "WEST", "EUROPE", "EUROPEAN", "EU",
    "ASIA", "PACIFIC", "APAC", "EMEA", "LATAM", "INTERNATIONAL", "INTL", "INT",
    "GLOBAL", "WORLDWIDE", "JAPAN", "JAPANESE", "NIPPON", "CHINA", "CHINESE",
    "BEIJING", "SHANGHAI", "SHENZHEN", "GUANGZHOU", "NANJING", "SUZHOU", "CHENGDU",
    "XI", "XIAN", "WUHAN", "HANGZHOU", "TIANJIN", "HARBIN", "CHANGSHA", "HEFEI",
    "DEUTSCHLAND", "GERMANY", "GERMAN", "MUENCHEN", "MUNICH", "BERLIN",
    "FRANKFURT", "HAMBURG", "STUTTGART", "KOELN", "FRANCE", "FRENCH", "PARIS",
    "LYON", "TOULOUSE", "ITALIA", "ITALY", "ITALIAN", "MILANO", "TORINO", "ROMA",
    "SCHWEIZ", "SUISSE", "SWITZERLAND", "SWISS", "ZURICH", "BASEL", "GENEVE",
    "CANADA", "CANADIAN", "KOREA", "KOREAN", "SEOUL", "SINGAPORE", "HONG", "KONG",
    "INDIA", "INDIAN", "TAIWAN", "AUSTRALIA", "AUSTRALIAN", "BRAZIL", "BRASIL",
    "MEXICO", "ESPANA", "SPAIN", "NEDERLAND", "NEDERLANDEN", "NETHERLANDS",
    "HOLLAND", "BELGIUM", "BELGIQUE", "BELGIE", "IRELAND", "IRISH", "SWEDEN",
    "SVENSKA", "FINLAND", "SUOMI", "NORWAY", "DENMARK", "DANMARK", "AUSTRIA",
    "OESTERREICH", "POLAND", "POLSKA", "RUSSIA", "ISRAEL", "TURKEY", "TURKIYE",
    "MAROC", "MOROCCO", "AFRICA", "MALAYSIA", "THAILAND", "VIETNAM", "INDONESIA",
    "PHILIPPINES", "CROLLES", "GRAETZ", "SZ", "GZ", "BJ", "SH",
    "CH", "DE", "FR", "IT", "JP", "CN", "KR", "NL", "SE", "FI", "NO", "DK",
    "BE", "AT", "ES", "CA", "AU",
}

# Chinese provinces and large cities, plus a few Japanese/Korean cities (added for the UAV dataset:
# without them, names like "GUANGDONG CROWNPOWER ..." used the province as if it were a brand)
GEO_TOKENS |= {
    "GUANGDONG", "JIANGSU", "ZHEJIANG", "SHANDONG", "SICHUAN", "HUBEI", "HUNAN", "HENAN", "HEBEI",
    "FUJIAN", "ANHUI", "SHAANXI", "SHANXI", "YUNNAN", "GUANGXI", "JIANGXI", "LIAONING", "JILIN",
    "HEILONGJIANG", "GUIZHOU", "GANSU", "HAINAN", "XINJIANG", "NINGXIA", "QINGHAI", "TIBET",
    "MONGOLIA", "CHONGQING", "QINGDAO", "XIAMEN", "NINGBO", "DONGGUAN", "FOSHAN", "ZHUHAI", "WUXI",
    "CHANGZHOU", "JINAN", "ZHENGZHOU", "KUNMING", "SHENYANG", "DALIAN", "FUZHOU", "NANCHANG",
    "TOKYO", "OSAKA", "BUSAN", "DAEJEON", "INCHEON",
}

INSTITUTION_MARKERS = {
    "UNIVERSITY", "UNIV", "UNIVERSITA", "UNIVERSITE", "UNIVERSITAT",
    "UNIVERSIDAD", "UNIVERSITEIT", "POLYTECHNIC", "POLYTECHNICAL", "COLLEGE",
    "ACADEMY", "MINISTRY", "GOVERNMENT", "ARMY", "NAVY", "AIRFORCE",
    "DEPARTMENT", "AGENCY", "COUNCIL", "COMMISSION", "HOSPITAL", "CLINIC",
    "PROVINCIAL", "MUNICIPAL",
}

RESEARCH_INSTITUTE_MARKERS = {"INSTITUTE", "INSTITUT", "INSTITUTO", "NATIONAL", "STATE"}

GENERIC_FIRST_TOKENS = LEGAL_FORMS | GEO_TOKENS | INSTITUTION_MARKERS | RESEARCH_INSTITUTE_MARKERS | {
    "RESEARCH", "FOUNDATION", "SCHOOL", "LABORATORY", "LABORATORIES",
    "GENERAL", "ROYAL", "FEDERAL", "CENTRAL", "FIRST", "SECOND", "THIRD", "NEW",
    "ADVANCED", "MODERN", "UNIVERSAL", "STANDARD", "TECH", "TECHNOLOGY",
    "TECHNOLOGIES", "TECHNICAL", "SYSTEM", "SYSTEMS", "SOLUTION", "SOLUTIONS",
    "SERVICE", "SERVICES", "DEVELOPMENT", "SCIENCE", "SCIENCES", "SCIENTIFIC",
    "INDUSTRIAL", "INDUSTRY", "INDUSTRIES", "CENTER", "CENTRE", "LAB", "LABS",
    "LABORATOIRE", "LABORATOIRES", "MANUFACTURING", "ENGINEERING", "ELECTRONIC",
    "ELECTRONICS", "ELECTRIC", "ELECTRICAL", "ENERGY", "POWER", "SOLAR", "AUTO",
    "AUTOMOTIVE", "MOTOR", "MOTORS", "AERO", "AEROSPACE", "AVIATION", "DEFENSE",
    "DEFENCE", "AIR", "SPACE", "FLIGHT", "DRONE", "DRONES", "UAV", "UNMANNED",
    "BIO", "BIOTECH", "MEDICAL", "HEALTH", "HEALTHCARE", "PHARMA",
    "PHARMACEUTICAL", "PHARMACEUTICALS", "CHEMICAL", "CHEMICALS", "CHEM",
    "MATERIAL", "MATERIALS", "METAL", "METALS", "STEEL", "OIL", "GAS", "DATA",
    "INFO", "INFORMATION", "DIGITAL", "SMART", "MICRO", "NANO", "OPTICAL",
    "OPTICS", "PRECISION", "QUALITY", "COMM", "COMMUNICATION", "COMMUNICATIONS",
    "TELECOM", "NETWORK", "NETWORKS", "MOBILE", "WIRELESS", "SOFTWARE", "MEDIA",
    "PRODUCT", "PRODUCTS", "EQUIPMENT", "MACHINE", "MACHINERY", "DEVICE",
    "DEVICES", "INSTRUMENT", "INSTRUMENTS", "CONTROL", "CONTROLS", "AUTOMATION",
    "ROBOT", "ROBOTICS", "SECURITY", "SAFETY", "ENVIRONMENTAL", "GREEN", "CLEAN",
    "BLUE", "RED", "WHITE", "BLACK", "GOLD", "STAR", "SUN", "APEX", "PRIME",
    "PRO", "SUPER", "ULTRA", "INTER", "TRANS", "MULTI", "OMNI", "POLY", "EURO",
    "AGRO", "AGRICULTURAL", "FOOD", "FOODS", "CONSUMER", "COMMERCIAL",
    "CORPORATE", "CAPITAL", "VENTURE", "VENTURES", "INVESTMENT", "FINANCIAL",
    "BANK", "INSURANCE", "ASSET", "PROPERTY", "PROPERTIES", "REAL", "ESTATE",
    "MANAGEMENT", "CONSULTING", "TRADING", "SUPPLY", "LOGISTICS", "TRANSPORT",
    "MARINE", "OCEAN", "WATER", "PAPER", "GLASS", "PLASTIC", "RUBBER", "TEXTILE",
    "FIBER", "BUREAU", "BOARD", "OFFICE", "AUTHORITY", "PUBLIC", "SINO",
    "DEUTSCHE", "DEUTSCHER", "NEDERLANDSE", "FINNISH", "BRITISH", "GRID",
    "ELECTRICITY", "AVIATION", "AIRCRAFT", "HELICOPTER", "SPACECRAFT",
}

DOTTED_FIXES: List[Tuple[str, str]] = [
    (r"\bS\.\s*P\.\s*A\.?", " SPA "),
    (r"\bS\.\s*R\.\s*L\.?", " SRL "),
    (r"\bS\.\s*A\.\s*S\.?", " SAS "),
    (r"\bS\.\s*A\.\s*R\.\s*L\.?", " SARL "),
    (r"\bS\.\s*A\.?", " SA "),
    (r"\bN\.\s*V\.?", " NV "),
    (r"\bB\.\s*V\.?", " BV "),
    (r"\bK\.\s*K\.?", " KK "),
    (r"\bU\.\s*K\.?", " UK "),
    (r"\bU\.\s*S\.\s*A\.?", " USA "),
    (r"\bU\.\s*S\.?", " US "),
    (r"\bR\s*&\s*D\b", " RD "),
    (r"\bG\.\s*M\.\s*B\.\s*H\.?", " GMBH "),
    (r"\bA\.\s*G\.?", " AG "),
    (r"\bA\s*/\s*S\b", " AS "),
    (r"\bCO\.\s*,?\s*LTD\.?", " CO LTD "),
    (r"\bC\s*/\s*O\b.*", " "),
    (r"\bFORMERLY\s+KNOWN\s+AS\b.*", " "),
    (r"\bF\s*/\s*K\s*/\s*A\b.*", " "),
    (r"\bD\s*/\s*B\s*/\s*A\b.*", " "),
    (r"\bA\s+DIVISION\s+OF\b.*", " "),
]

COMPANY_PREFIX_WRAPPERS = {"COMPAGNIE", "SOCIETE", "KONINKLIJKE", "ETABLISSEMENTS", "FIRMA"}

# Baseline dictionary from Tutorial 11 (kept for direct side-by-side benchmarking)
TUTORIAL_LEGAL_FORMS = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "LTD",
    "LIMITED", "LLC", "LP", "PLC", "GMBH", "AG", "KG", "MBH", "SE", "SA",
    "SAS", "SPA", "SRL", "BV", "NV", "AB", "AS", "ASA", "OY", "OYJ", "KK",
    "KABUSHIKI", "KAISHA", "LTDA", "PTY", "THE", "AKTIENGESELLSCHAFT",
    "GESELLSCHAFT",
}


def clean_with_tutorial_dictionary(name: str) -> str:
    """Tutorial 11 Method A baseline: uppercase, strip punctuation and boundary legal forms."""
    words = re.sub(r"[^A-Z0-9 ]", " ", str(name).upper()).split()
    while words and words[-1] in TUTORIAL_LEGAL_FORMS:
        words.pop()
    while words and words[0] in TUTORIAL_LEGAL_FORMS:
        words.pop(0)
    return " ".join(words)


def normalize_applicant_tokens(name: str) -> Tuple[List[str], bool]:
    """Normalize an applicant string into clean tokens plus an 'is_institution' flag."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii").upper()
    s_no_paren = re.sub(r"\([^)]*\)", " ", s)
    if re.sub(r"[^A-Z0-9]", "", s_no_paren):
        s = s_no_paren
    for pat, rep in DOTTED_FIXES:
        s = re.sub(pat, rep, s)
    # Collapse intra-word apostrophes (e.g. L'OREAL -> LOREAL)
    s = re.sub(r"([A-Z])'([A-Z])", r"\1\2", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    raw_tokens = s.split()
    if not raw_tokens:
        return [str(name).upper().strip()], False

    is_inst = any(t in INSTITUTION_MARKERS for t in raw_tokens) or (
        raw_tokens[0] in (GEO_TOKENS | RESEARCH_INSTITUTE_MARKERS)
        and any(t in RESEARCH_INSTITUTE_MARKERS for t in raw_tokens)
    )

    tokens = list(raw_tokens)
    while len(tokens) > 1 and tokens[-1] in LEGAL_FORMS:
        tokens.pop()
    while len(tokens) > 1 and tokens[0] in LEGAL_FORMS:
        tokens.pop(0)

    if is_inst:
        # Preserve geographic & distinguishing words for universities/institutes/state bodies
        # (e.g., BEIJING vs NANJING UNIVERSITY OF AERONAUTICS AND ASTRONAUTICS)
        core = [t for t in tokens if t not in {"OF", "THE", "AND", "FOR", "IN", "AT"} and not t.isdigit()]
    else:
        core = [t for t in tokens if t not in LEGAL_FORMS and not t.isdigit()]

    return (core if core else tokens), is_inst


def _match_domain_corporate_tree(
    normalized_str: str,
    domain_groups: Dict[str, Dict[str, Any]],
) -> Optional[str]:
    """Check if normalized applicant name matches an explicit UAV/aerospace corporate group."""
    padded = f" {normalized_str} "
    # Sort patterns longest-first so specific patterns win over shorter ones
    candidates: List[Tuple[int, str, str]] = []
    for canon, meta in domain_groups.items():
        for pat in meta.get("patterns", []):
            p_clean = re.sub(r"[^A-Z0-9 ]", " ", str(pat).upper()).strip()
            p_clean = " ".join(p_clean.split())
            if p_clean:
                candidates.append((len(p_clean), p_clean, canon))
    for _, pat, canon in sorted(candidates, reverse=True):
        if f" {pat} " in padded:
            return canon
    return None


def harmonize_applicant_names(
    names: Iterable[str],
    domain_groups: Optional[Dict[str, Dict[str, Any]]] = None,
    apply_domain_aliases: bool = False,
    min_anchor_freq: int = 2,
    typo_min_len: int = 9,
    typo_similarity_threshold: float = 0.90,
) -> Dict[str, str]:
    """Harmonize a corpus of PATSTAT applicant names into canonical organization keys.

    Parameters
    ----------
    names : Iterable of raw or PSN applicant strings
    domain_groups : Optional dict from config['domain_corporate_groups']
    apply_domain_aliases : If True, consolidate known corporate M&A trees (e.g.
        FINMECCANICA/SELEX -> LEONARDO, DA JIANG -> DJI). Keep False when benchmarking
        general algorithmic precision/recall on PATSTAT_500_label_datav4.csv.
    """
    unique_names = list(dict.fromkeys(str(n) for n in names))
    parsed = {n: normalize_applicant_tokens(n) for n in unique_names}

    # Step 1: Discover distinctive corporate brand anchors (skip institutions & generic prefixes)
    first_tok_counts: Counter[str] = Counter()
    standalone_anchors: set[str] = set()
    second_tok_brand_counts: Counter[Tuple[str, str]] = Counter()

    for n, (toks, is_inst) in parsed.items():
        if not toks or is_inst:
            continue
        non_geo = [t for t in toks if t not in GEO_TOKENS]
        if not non_geo:
            continue
        t0 = non_geo[0]
        if t0 not in GENERIC_FIRST_TOKENS and len(t0) >= 3:
            first_tok_counts[t0] += 1
            if len(non_geo) == 1:
                standalone_anchors.add(t0)
            elif len(non_geo) >= 2 and non_geo[1] not in GENERIC_FIRST_TOKENS and len(non_geo[1]) >= 4:
                second_tok_brand_counts[(t0, non_geo[1])] += 1

    brand_anchors = {t for t, c in first_tok_counts.items() if c >= min_anchor_freq} | standalone_anchors

    # Step 2: Merge rare typos among long distinctive brand anchors (e.g., STMICROELETRONICS -> STMICROELECTRONICS)
    anchor_order = sorted(brand_anchors, key=lambda x: (-first_tok_counts[x], -len(x), x))
    anchor_canonical: Dict[str, str] = {}
    for a in anchor_order:
        matched = None
        if len(a) >= typo_min_len:
            for canon in list(anchor_canonical.values()):
                if (
                    len(canon) >= typo_min_len
                    and a[:4] == canon[:4]
                    and abs(len(a) - len(canon)) <= 2
                    and SequenceMatcher(None, a, canon).ratio() >= typo_similarity_threshold
                ):
                    matched = canon
                    break
        anchor_canonical[a] = matched if matched else a

    canonical_brand_set = set(anchor_canonical.values())

    # Step 3: Assign each name to its canonical key
    mapping: Dict[str, str] = {}
    for n in unique_names:
        toks, is_inst = parsed[n]
        raw_upper = " ".join(re.sub(r"[^A-Z0-9 ]", " ", unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode("ascii").upper()).split())

        # Optional UAV/Aerospace corporate M&A tree consolidation (Slide 9 subsidiary rule)
        if apply_domain_aliases and domain_groups:
            domain_hit = _match_domain_corporate_tree(raw_upper, domain_groups)
            if domain_hit is not None:
                mapping[n] = domain_hit
                continue

        if is_inst:
            # Keep full normalized institutional name so geographically distinct universities never collide
            mapping[n] = " ".join(toks[:7])
            continue

        mapped = [anchor_canonical.get(t, t) for t in toks]
        non_geo = [t for t in mapped if t not in GEO_TOKENS]
        if not non_geo:
            non_geo = mapped

        t0 = non_geo[0]
        if t0 in canonical_brand_set:
            # Joint-venture guardrail: if position 1 or 2 is ALSO an established standalone corporate brand
            # (or a repeated non-generic partner brand like SONY ERICSSON), keep the JV separate!
            jv_partners = [
                t
                for t in non_geo[1:3]
                if t != t0
                and t not in GENERIC_FIRST_TOKENS
                and len(t) >= 4
                and (
                    t in standalone_anchors
                    or (t in canonical_brand_set and first_tok_counts[t] >= 3)
                )
            ]
            if jv_partners:
                mapping[n] = f"{t0} {jv_partners[0]}"
            else:
                mapping[n] = t0
            continue

        # Handle corporate wrapper prefixes (e.g. "COMPAGNIE IBM" -> "IBM")
        if len(non_geo) >= 2 and toks[0] in COMPANY_PREFIX_WRAPPERS:
            t1 = anchor_canonical.get(non_geo[1], non_geo[1])
            if t1 in canonical_brand_set:
                mapping[n] = t1
                continue

        # Otherwise retain up to 4 non-geo tokens (avoids collapsing unrelated generic firms like GENERAL ATOMICS vs GENERAL ELECTRIC)
        mapping[n] = " ".join(non_geo[:4])

    return mapping


# ------------------------------------------------------------------ Harmonization Evaluation
def _pairs_inside(group_sizes: Iterable[int]) -> int:
    return sum(comb(int(n), 2) for n in group_sizes)


def evaluate_harmonization(
    gold_groups: Sequence[Any],
    predicted_groups: Sequence[Any],
) -> Dict[str, float]:
    """Compute pairwise Precision, Recall, F1 + Homogeneity, Completeness, V-measure (Tutorial 11 §2.4)."""
    df = pd.DataFrame({"gold": list(gold_groups), "pred": list(predicted_groups)})
    tp = _pairs_inside(df.groupby(["gold", "pred"]).size())
    tp_fp = _pairs_inside(df.groupby("pred").size())
    tp_fn = _pairs_inside(df.groupby("gold").size())
    precision = tp / tp_fp if tp_fp else 1.0
    recall = tp / tp_fn if tp_fn else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    hom, comp, v_meas = homogeneity_completeness_v_measure(df["gold"], df["pred"])
    return {
        "groups_found": int(df["pred"].nunique()),
        "gold_groups": int(df["gold"].nunique()),
        "precision": float(precision),
        "recall": float(recall),
        "F1": float(f1),
        "homogeneity": float(hom),
        "completeness": float(comp),
        "V_measure": float(v_meas),
    }


# ------------------------------------------------------------------ Step 2 Concentration Measures
# Replicates Liston-Heyes & Pilkington (2004) + Tutorial 11 Section 3
def concentration_ratio(patents_per_firm: Sequence[float], k: int) -> float:
    """CR_k (%): share of total patents/families held by the k largest applicants."""
    arr = np.sort(np.asarray(patents_per_firm, dtype=float))[::-1]
    total = arr.sum()
    if total <= 0:
        return np.nan
    return float(arr[:k].sum() / total * 100.0)


def herfindahl_index(patents_per_firm: Sequence[float]) -> float:
    """Herfindahl-Hirschman Index: sum of squared shares (1/N = equal, 1 = monopoly)."""
    arr = np.asarray(patents_per_firm, dtype=float)
    total = arr.sum()
    if total <= 0:
        return np.nan
    shares = arr / total
    return float(np.sum(shares ** 2))


def coefficient_of_variation(patents_per_firm: Sequence[float]) -> float:
    """CV = sample std / mean of patents per firm."""
    arr = np.asarray(patents_per_firm, dtype=float)
    if len(arr) < 2 or arr.mean() == 0:
        return np.nan
    return float(arr.std(ddof=1) / arr.mean())


def lorenz_curve(patents_per_firm: Sequence[float]) -> Tuple[np.ndarray, np.ndarray]:
    """Return (cumulative share of firms, cumulative share of patents), smallest firm first."""
    x = np.sort(np.asarray(patents_per_firm, dtype=float))
    share_firms = np.arange(0, len(x) + 1) / len(x)
    share_patents = np.concatenate([[0.0], np.cumsum(x) / x.sum()])
    return share_firms, share_patents


def gini_coefficient(patents_per_firm: Sequence[float]) -> float:
    """Gini coefficient from the Lorenz curve (0 = equal, approaches 1 = monopoly)."""
    arr = np.asarray(patents_per_firm, dtype=float)
    if len(arr) == 0 or arr.sum() <= 0:
        return np.nan
    x, y = lorenz_curve(arr)
    area_under_lorenz = float(np.trapezoid(y, x)) if hasattr(np, "trapezoid") else float(np.trapz(y, x))
    return float(1.0 - 2.0 * area_under_lorenz)


def lotka_coefficient(patents_per_firm: Sequence[float]) -> Tuple[float, float]:
    """Slope L and p-value of log f(n) = c + L * log(n), where f(n) = firms with n patents."""
    counts = pd.Series(patents_per_firm).astype(int).value_counts().sort_index()
    counts = counts[counts.index > 0]
    if len(counts) < 2:
        return np.nan, np.nan
    res = stats.linregress(np.log(counts.index.to_numpy(dtype=float)), np.log(counts.to_numpy(dtype=float)))
    return float(res.slope), float(res.pvalue)


def six_concentration_measures(patents_per_firm: Sequence[float]) -> Dict[str, float]:
    """Compute all six Liston-Heyes & Pilkington (2004) inventive concentration measures."""
    hh = herfindahl_index(patents_per_firm)
    lotka_l, lotka_p = lotka_coefficient(patents_per_firm)
    return {
        "n_applicants": int(len(patents_per_firm)),
        "CR4_pct": concentration_ratio(patents_per_firm, 4),
        "CR8_pct": concentration_ratio(patents_per_firm, 8),
        "HH": hh,
        "numbers_equivalent_1_over_HH": float(1.0 / hh) if hh and hh > 0 else np.nan,
        "CV": coefficient_of_variation(patents_per_firm),
        "Gini": gini_coefficient(patents_per_firm),
        "Lotka_L": lotka_l,
        "Lotka_p_value": lotka_p,
    }
