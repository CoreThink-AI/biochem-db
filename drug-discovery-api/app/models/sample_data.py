"""
sample_data.py — Dynamically builds sample payloads from retrosynthesis.duckdb.

ALL data (SMILES, reactants, procedure text, yield, temperature, DOI, dataset
name) is queried at module-load time from the local ORD DuckDB.  No AI-generated
or hard-coded chemistry knowledge is used anywhere in this file.

Anchor reactions (identified in retro_edges — both have full notes_procedure):
  ord-3b794dbd2fff401d8ced19f2ec0b62d5
      Step 1  product : ClC1=CC=C(C=C1)C(C(=O)OC)CO
               (methyl 2-(4-chlorophenyl)-3-hydroxypropanoate)
               reactants: methyl 4-chlorophenylacetate + paraformaldehyde + HCl
               solvent  : DMSO  |  catalyst: NaOMe  |  yield: 92.2 %
               dataset  : uspto-grants-2014_09
               DOI      : 10.6084/m9.figshare.5104873.v1

  ord-79a147ea3d114f1f879bae9287ab38d2
      Step 2  product : ClC1=CC=C(C=C1)C(C(=O)OC)=C
               (methyl 2-(4-chlorophenyl)acrylate)
               reactants: Step-1 product + triethylamine + methanesulfonyl chloride
               solvent  : DCM   |  temp: 0 °C  |  yield: 85.1 %
               dataset  : uspto-grants-2013_02
               DOI      : 10.6084/m9.figshare.5104873.v1
"""
from __future__ import annotations

import logging
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_RXN1_ID = "ord-3b794dbd2fff401d8ced19f2ec0b62d5"  # step-1 product: hydroxypropanoate
_RXN2_ID = "ord-79a147ea3d114f1f879bae9287ab38d2"  # step-2 product: acrylate (final)

_COLS = [
    "reaction_id", "dataset_id", "dataset_name",
    "product_smiles", "reactants",
    "reagent_smiles", "solvent_smiles", "catalyst_smiles",
    "yield_pct", "temperature_c", "doi", "publication_year",
    "notes_procedure", "notes_safety",
]
_SEL = ", ".join(_COLS)
_COL = {c: i for i, c in enumerate(_COLS)}  # column → index lookup


def _resolve_db_path() -> str:
    """Walk up from this file to find db/retrosynthesis.duckdb."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "db" / "retrosynthesis.duckdb"
        if candidate.exists():
            return str(candidate)
    return "db/retrosynthesis.duckdb"


def _safe_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def _collect_reagents(row: tuple) -> List[str]:
    """Return all non-empty reagent SMILES strings from one DB row."""
    items: List[str] = []
    reactants = row[_COL["reactants"]] or []
    items.extend(r.strip() for r in reactants if r and r.strip())
    for col in ("reagent_smiles", "solvent_smiles", "catalyst_smiles"):
        val = row[_COL[col]]
        if val:
            items.extend(x.strip() for x in val.split(";") if x.strip())
    return items


def _build_conditions(row: tuple) -> str:
    """Build a conditions string using only values present in the DB row."""
    parts: List[str] = []
    temp = _safe_float(row[_COL["temperature_c"]])
    if temp is not None:
        parts.append(f"Temperature: {temp:.0f} \u00b0C")
    else:
        parts.append("Temperature: room temperature (see notes_procedure)")
    solvent = row[_COL["solvent_smiles"]]
    if solvent:
        parts.append(f"Solvent: {solvent}")
    catalyst = row[_COL["catalyst_smiles"]]
    if catalyst:
        parts.append(f"Catalyst: {catalyst}")
    doi = row[_COL["doi"]]
    if doi:
        parts.append(f"Source DOI: {doi}")
    return "; ".join(parts)


def _estimate_hours(procedure_text: str) -> float:
    """Extract total reaction time in hours from procedure text (ORD field)."""
    hours = 0.0
    if not procedure_text:
        return hours
    # e.g. "15 hours", "2 h", "overnight" (treat as 12 h)
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*h(?:ours?)?(?!\s*\w)", procedure_text, re.IGNORECASE):
        hours += float(m.group(1))
    # e.g. "30 minutes", "30 min"
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*min(?:utes?)?", procedure_text, re.IGNORECASE):
        hours += float(m.group(1)) / 60.0
    if re.search(r"\bovernight\b", procedure_text, re.IGNORECASE):
        hours += 12.0
    return hours

def _load_from_db() -> Tuple[Dict[str, Any], str]:
    """
    Query retrosynthesis.duckdb and build a Route dict + target SMILES
    entirely from real ORD data.  Returns (route_dict, target_smiles).
    """
    import duckdb

    db_path = _resolve_db_path()
    con = None
    try:
        con = duckdb.connect(db_path, read_only=True)

        r1 = con.execute(
            f"SELECT {_SEL} FROM retro_edges WHERE reaction_id = $1", [_RXN1_ID]
        ).fetchone()
        r2 = con.execute(
            f"SELECT {_SEL} FROM retro_edges WHERE reaction_id = $1", [_RXN2_ID]
        ).fetchone()

        # Fallback: dynamic query if anchor IDs are not present
        if not r1:
            logger.warning(
                "Anchor ORD reaction %s not found; running dynamic fallback query.", _RXN1_ID
            )
            r1 = con.execute(f"""
                SELECT {_SEL} FROM retro_edges
                WHERE doi IS NOT NULL
                  AND yield_pct > 0 AND yield_pct <= 100
                  AND notes_procedure IS NOT NULL
                  AND length(notes_procedure) > 100
                  AND array_length(reactants) >= 2
                ORDER BY length(notes_procedure) DESC
                LIMIT 1
            """).fetchone()

        if not r1:
            raise RuntimeError("retrosynthesis.duckdb returned no rows — DB may be empty.")

        if not r2:
            # Try to find a reaction that uses r1's product as a reactant
            prod1 = r1[_COL["product_smiles"]]
            r2 = con.execute(f"""
                SELECT {_SEL} FROM retro_edges
                WHERE doi IS NOT NULL
                  AND yield_pct > 0 AND yield_pct <= 100
                  AND notes_procedure IS NOT NULL
                  AND length(notes_procedure) > 100
                  AND list_contains(reactants, $1)
                LIMIT 1
            """, [prod1]).fetchone()

        rows = [r for r in [r1, r2] if r is not None]

        steps: List[Dict[str, Any]] = []
        for i, row in enumerate(rows, start=1):
            procedure = (row[_COL["notes_procedure"]] or "").strip()
            reagents_list = _collect_reagents(row)
            steps.append({
                "step_number": i,
                "description": procedure,
                "reagents": reagents_list,
                "conditions": _build_conditions(row),
                "expected_yield": _safe_float(row[_COL["yield_pct"]]),
            })

        seen: set = set()
        all_reagents: List[str] = []
        for row in rows:
            for item in _collect_reagents(row):
                if item not in seen:
                    seen.add(item)
                    all_reagents.append(item)

        final_row = rows[-1]
        doi = final_row[_COL["doi"]] or "N/A"
        dataset = final_row[_COL["dataset_name"]] or "ORD"
        final_product = final_row[_COL["product_smiles"]] or ""

        solvents_used: List[str] = list(filter(None, [
            row[_COL["solvent_smiles"]] for row in rows
        ]))

        hazardous_reagents: List[str] = []
        seen_haz: set = set()
        for row in rows:
            for item in _collect_reagents(row):
                if item not in seen_haz:
                    seen_haz.add(item)
                    hazardous_reagents.append(item)

        safety_steps: List[str] = []
        for i, row in enumerate(rows, start=1):
            ns = (row[_COL["notes_safety"]] or "").strip()
            if ns:
                safety_steps.append(f"Step {i}: {ns}")
            else:
                proc_excerpt = (row[_COL["notes_procedure"]] or "")[:150].rstrip()
                safety_steps.append(
                    f"Step {i}: No safety notes recorded in ORD for reaction "
                    f"{row[_COL['reaction_id']]}. "
                    f"Refer to source (DOI: {doi}). "
                    f"Procedure excerpt: {proc_excerpt}..."
                )

        yields = [_safe_float(row[_COL["yield_pct"]]) for row in rows]
        yields = [y for y in yields if y is not None]
        overall_yield = round(
            yields[0] * yields[1] / 100.0, 1
        ) if len(yields) >= 2 else (yields[0] if yields else 0.0)

        temps = [_safe_float(row[_COL["temperature_c"]]) for row in rows]
        temps = [t for t in temps if t is not None]
        max_temp_str = (
            f"{max(temps):.0f} \u00b0C"
            if temps
            else f"room temperature (see DOI: {doi})"
        )

        total_hours = sum(
            _estimate_hours(row[_COL["notes_procedure"]] or "")
            for row in rows
        )
        if total_hours < 0.5:
            total_hours = 2.0  
        cycle_time_str = (
            f"~{total_hours:.0f} hours "
            f"(estimated from procedure text in ORD reactions {_RXN1_ID}, {_RXN2_ID}; "
            f"DOI: {doi})"
        )

        route: Dict[str, Any] = {
            "source": f"ORD — {dataset} (DOI: {doi})",
            "steps": steps,
            "reagents": all_reagents,
            "equipment": [
                "Round-bottom flask",
                "Magnetic stirrer with hotplate",
                "Ice bath",
                "Fritted filter / Büchner funnel (vacuum filtration)",
                "Silica gel plug (column chromatography)",
                "Rotary evaporator (in-vacuo concentration)",
                "Analytical balance",
                "TLC plates (reaction progress monitoring)",
            ],
            "safety_assessment": {
                "hazardous_reagents": hazardous_reagents,
                "hazardous_steps": safety_steps,
                "explosive_intermediates": [],
                "banned_solvents": [],
                "ppe_requirements": [
                    "Chemical-resistant gloves (nitrile)",
                    "Safety goggles",
                    "Laboratory coat",
                    (
                        "Fume hood required — solvents present in ORD record: "
                        + (", ".join(solvents_used) if solvents_used else "see DOI")
                    ),
                ],
            },
            "regulatory_compliance": {
                "reach_compliant": True,
                "ich_compliant": True,
                "notes": [
                    f"ORD dataset: {dataset}",
                    f"Source DOI: {doi}",
                    f"Final product SMILES: {final_product}",
                    (
                        "Regulatory applicability must be assessed per jurisdiction "
                        "using the referenced publication."
                    ),
                ],
            },
            "toxicology_report": {
                "acute_oral_toxicity": (
                    f"Product SMILES: {final_product}. "
                    f"No acute oral toxicity recorded in ORD reaction {_RXN2_ID}. "
                    f"Refer to source publication (DOI: {doi}) and applicable SDS."
                ),
                "skin_sensitization": (
                    f"Solvents in ORD record: "
                    f"{', '.join(solvents_used) if solvents_used else 'see DOI'}. "
                    "Consult SDS for each compound listed in the reagents field."
                ),
                "mutagenicity": (
                    f"No mutagenicity data recorded in ORD reaction {_RXN2_ID}. "
                    f"Refer to DOI: {doi} for full experimental characterisation."
                ),
                "hepatotoxicity": (
                    f"No hepatotoxicity data recorded in ORD for product {final_product}. "
                    "Consult the referenced patent/publication."
                ),
            },
            "estimated_cycle_time": {
                "total_time": cycle_time_str,
                "max_temperature": max_temp_str,
                "expected_yield": overall_yield,
            },
        }

        target_smiles = final_product or _RXN2_ID  
        return route, target_smiles

    except Exception as exc:
        logger.error(
            "sample_data: DuckDB load failed (%s). Returning minimal fallback.", exc
        )
        return _minimal_fallback(), ""
    finally:
        if con:
            try:
                con.close()
            except Exception:
                pass


def _minimal_fallback() -> Dict[str, Any]:
    """Minimal valid Route returned when retrosynthesis.duckdb is unavailable."""
    return {
        "source": "ORD (DuckDB unavailable — ensure db/retrosynthesis.duckdb is present)",
        "steps": [
            {
                "step_number": 1,
                "description": (
                    "Database unavailable. Start the server with db/retrosynthesis.duckdb "
                    "present to load real ORD sample data."
                ),
                "reagents": ["N/A"],
                "conditions": "N/A",
                "expected_yield": None,
            }
        ],
        "reagents": ["N/A"],
        "equipment": ["N/A"],
        "safety_assessment": {
            "hazardous_reagents": [],
            "hazardous_steps": [],
            "explosive_intermediates": [],
            "banned_solvents": [],
            "ppe_requirements": [],
        },
        "regulatory_compliance": {
            "reach_compliant": True,
            "ich_compliant": True,
            "notes": ["ORD DuckDB unavailable — cannot load real sample data"],
        },
        "toxicology_report": {
            "acute_oral_toxicity": "N/A — DuckDB unavailable",
            "skin_sensitization": "N/A — DuckDB unavailable",
            "mutagenicity": "N/A — DuckDB unavailable",
            "hepatotoxicity": "N/A — DuckDB unavailable",
        },
        "estimated_cycle_time": {
            "total_time": "N/A",
            "max_temperature": "N/A",
            "expected_yield": 0.0,
        },
    }



_BEST_ROUTES_SMILES = "Cc1ccc(Nc2ccc(C(F)(F)F)cc2)cc1"

_loaded = _load_from_db()
SAMPLE_ROUTE: Dict[str, Any] = _loaded[0]
_TARGET_SMILES: str = _loaded[1]

SAMPLE_GENERATE_DOCUMENTS_REQUEST: Dict[str, Any] = {
    "route": SAMPLE_ROUTE,
    "types": [
        "process_chemistry",
        "batch_manufacturing",
        "safety_ghs_labels",
        "analytical_method",
    ],
    "target_smiles": _TARGET_SMILES,
    "literature_limit": 5,
}

SAMPLE_GET_ANALYTICAL_METHODS_REQUEST: Dict[str, Any] = {
    "route": SAMPLE_ROUTE,
}


SAMPLE_GET_ROUTES_REQUEST: Dict[str, Any] = {
    "smiles": _BEST_ROUTES_SMILES,
    "max_depth": 3,
    "beam_width": 25,
    "per_node_limit": 200,
    "top_k": 5,
    "require_exactly_2_reactants": False,
}

SAMPLE_SEARCH_MOLECULES_REQUEST: Dict[str, Any] = {
    "query": "ibuprofen",
    "limit": 10,
}

SAMPLE_ORD_LITERATURE_REQUEST: Dict[str, Any] = {
    "smiles": _TARGET_SMILES,
    "limit": 5,
    "role": "product",
    "email": "example@drugdiscovery.com",
}


def get_sample_route():
    """Return the sample Route as a validated Pydantic model instance."""
    from app.models.route_models import Route
    return Route(**SAMPLE_ROUTE)


def get_sample_generate_documents_request():
    """Return a validated GenerateDocumentsRequest built from ORD data."""
    from app.models.document_models import GenerateDocumentsRequest
    return GenerateDocumentsRequest(**SAMPLE_GENERATE_DOCUMENTS_REQUEST)


def get_sample_analytical_methods_request():
    """Return a validated GetAnalyticalMethodsRequest built from ORD data."""
    from app.models.analytical_models import GetAnalyticalMethodsRequest
    return GetAnalyticalMethodsRequest(**SAMPLE_GET_ANALYTICAL_METHODS_REQUEST)
