from __future__ import annotations

import asyncio
import logging
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.models.route_models import (
    AlgorithmComparisonSummary,
    AStarSearchStats,
    GetRoutesComparisonRequest,
    GetRoutesComparisonResponse,
    GetRoutesRequest,
    ORDRoute,
    ORDRouteMetrics,
    ORDSearchStats,
    ORDSynthesisStep,
    SearchAlgorithm,
)

logger = logging.getLogger(__name__)

def _load_retrosynth():
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "db" / "retrosynth.py"
        if candidate.exists():
            db_dir = str(candidate.parent)
            if db_dir not in sys.path:
                sys.path.insert(0, db_dir)
            import retrosynth  # noqa: PLC0415
            return retrosynth
    raise ImportError(
        "db/retrosynth.py not found — "
        "expected alongside the app/ directory in the project root."
    )


def _doi_url(doi: Optional[str]) -> Optional[str]:
    return f"https://doi.org/{doi}" if doi else None


def _scholar_url(doi: Optional[str]) -> Optional[str]:
    if not doi:
        return None
    return (
        "https://scholar.google.com/scholar?q="
        + urllib.parse.quote_plus(f"doi:{doi}")
    )


def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
        return None if (f != f) else f  # NaN check: NaN != NaN
    except (TypeError, ValueError):
        return None


def _safe_int(v: Any) -> Optional[int]:
    f = _safe_float(v)
    return None if f is None else int(f)


def _resolve_ord_db_path() -> str:
    from app.config import get_settings
    settings = get_settings()
    db_path = Path(settings.ord_db_path)

    if not db_path.is_absolute():
        # Try CWD first (normal uvicorn run from project root)
        cwd_candidate = Path.cwd() / db_path
        if cwd_candidate.exists():
            return str(cwd_candidate)
        # Walk up from this file
        here = Path(__file__).resolve()
        for parent in here.parents:
            candidate = parent / db_path
            if candidate.exists():
                return str(candidate)

    return str(db_path)


def _map_step(step_dc: Any, step_number: int, depth: int) -> ORDSynthesisStep:
    doi = step_dc.doi
    reactants = step_dc.reactants
    if isinstance(reactants, str):
        reactants = [r.strip() for r in reactants.split(";") if r.strip()]
    else:
        reactants = list(reactants) if reactants else []

    return ORDSynthesisStep(
        step_number=step_number,
        depth=depth,
        reaction_id=str(step_dc.reaction_id),
        product_smiles=str(step_dc.product_smiles),
        reactants=reactants,
        reagent_smiles=step_dc.reagent_smiles or None,
        solvent_smiles=step_dc.solvent_smiles or None,
        catalyst_smiles=step_dc.catalyst_smiles or None,
        yield_pct=_safe_float(step_dc.yield_pct),
        temperature_c=_safe_float(step_dc.temperature_c),
        pressure_atm=_safe_float(step_dc.pressure_atm),
        stirring_rpm=_safe_float(step_dc.stirring_rpm),
        source=step_dc.source or None,
        dataset_id=step_dc.dataset_id or None,
        dataset_name=step_dc.dataset_name or None,
        doi=doi or None,
        doi_url=_doi_url(doi),
        google_scholar_url=_scholar_url(doi),
        publication_year=_safe_int(step_dc.publication_year),
        notes_safety=step_dc.notes_safety or None,
        notes_procedure=step_dc.notes_procedure or None,
        step_score=_safe_float(step_dc.step_score) or 0.0,
    )


def _map_route(
    route_dc: Any,
    is_best: bool = False,
    reasoning: Optional[Dict] = None,
) -> ORDRoute:
    metrics_raw = route_dc.get_metrics()
    metrics = ORDRouteMetrics(
        num_steps=metrics_raw["num_steps"],
        avg_yield=_safe_float(metrics_raw["avg_yield"]) or 0.0,
        avg_temp=_safe_float(metrics_raw["avg_temp"]) or 0.0,
        has_safety_concerns=bool(metrics_raw["has_safety_concerns"]),
        num_reactants=metrics_raw["num_reactants"],
        complete=metrics_raw["complete"],
        yields_available=metrics_raw.get("yields_available", 0),
        temps_available=metrics_raw.get("temps_available", 0),
    )

    steps = [
        _map_step(s, step_number=i + 1, depth=i + 1)
        for i, s in enumerate(route_dc.steps)
    ]

    max_depth_reached = max((s.depth for s in steps), default=0)

    return ORDRoute(
        source="ORD",
        target_smiles=route_dc.target_smiles,
        score=_safe_float(route_dc.score) or 0.0,
        is_best=is_best,
        is_complete=len(route_dc.open_molecules) == 0,
        steps=steps,
        open_molecules=list(route_dc.open_molecules),
        metrics=metrics,
        max_depth_reached=max_depth_reached,
        selection_reasoning=reasoning if is_best else None,
    )


def _run_beam_search(
    smiles: str,
    db_path: str,
    max_depth: int,
    beam_width: int,
    per_node_limit: int,
    top_k: int,
    require_exactly_2_reactants: bool,
) -> Tuple[List[Any], Any, Optional[Any], Optional[Dict]]:
    rs = _load_retrosynth()

    retro = rs.OrdRetroSynth(duckdb_path=db_path)
    retro.stats = rs.SearchStats(
        target_smiles=smiles,
        max_depth=max_depth,
        beam_width=beam_width,
        per_node_limit=per_node_limit,
    )

    all_routes = retro.build_routes(
        target_smiles=smiles,
        max_depth=max_depth,
        beam_width=beam_width,
        per_node_limit=per_node_limit,
        require_exactly_2_reactants=require_exactly_2_reactants,
    )

    
    routes_with_steps = [r for r in all_routes if r.steps]

    best_dc, reasoning = None, None
    if routes_with_steps:
        best_dc, reasoning = retro.select_best_route(routes_with_steps)

    return routes_with_steps[:top_k], retro.stats, best_dc, reasoning


async def generate_routes(
    request: GetRoutesRequest,
) -> Tuple[List[ORDRoute], Optional[ORDSearchStats], Optional[str]]:
    db_path = _resolve_ord_db_path()

    try:
        routes_dc, stats_dc, best_dc, reasoning = await asyncio.to_thread(
            _run_beam_search,
            request.smiles,
            db_path,
            request.max_depth,
            request.beam_width,
            request.per_node_limit,
            request.top_k,
            request.require_exactly_2_reactants,
        )
    except Exception as exc:
        logger.error(
            "ORD beam-search failed for SMILES '%s': %s", request.smiles, exc
        )
        raise

    search_stats: Optional[ORDSearchStats] = None
    if stats_dc:
        sd = stats_dc.to_dict()
        search_stats = ORDSearchStats(
            target_smiles=sd["target_smiles"],
            max_depth=sd["max_depth"],
            beam_width=sd["beam_width"],
            per_node_limit=sd["per_node_limit"],
            top_k=request.top_k,
            runtime_seconds=round(sd["runtime_seconds"], 3),
            nodes_explored=sd["nodes_explored"],
            reactions_queried=sd["reactions_queried"],
            routes_generated=sd["routes_generated"],
            avg_reactions_per_node=round(sd["avg_reactions_per_node"], 2),
        )

    best_id = id(best_dc) if best_dc is not None else None
    ord_routes: List[ORDRoute] = []

    for route_dc in routes_dc:
        is_best = id(route_dc) == best_id
        ord_routes.append(
            _map_route(
                route_dc,
                is_best=is_best,
                reasoning=reasoning if is_best else None,
            )
        )

    ord_routes.sort(key=lambda r: (not r.is_best, -r.score))

    note: Optional[str] = None
    if not ord_routes:
        note = (
            f"No retrosynthesis routes found in the ORD database for "
            f"'{request.smiles}' at max_depth={request.max_depth}. "
            "The retro_edges table uses exact SMILES matching — try a "
            "simpler fragment or increase max_depth / beam_width."
        )

    return ord_routes, search_stats, note

def _run_astar_search(
    smiles: str,
    db_path: str,
    max_depth: int,
    max_nodes: int,
    per_node_limit: int,
    top_k: int,
    heuristic_weight: float,
    require_exactly_2_reactants: bool,
) -> Tuple[List[Any], Any, Optional[Any], Optional[Dict]]:
    rs = _load_retrosynth()

    retro = rs.AStarRetroSynth(duckdb_path=db_path)

    all_routes = retro.build_routes_astar(
        target_smiles=smiles,
        max_depth=max_depth,
        max_nodes=max_nodes,
        per_node_limit=per_node_limit,
        top_k=top_k,
        heuristic_weight=heuristic_weight,
        require_exactly_2_reactants=require_exactly_2_reactants,
    )

    routes_with_steps = [r for r in all_routes if r.steps]

    best_dc, reasoning = None, None
    if routes_with_steps:
        best_dc, reasoning = retro.select_best_route(routes_with_steps)

    return routes_with_steps, retro.astar_stats, best_dc, reasoning

def _recommend_algorithm(
    beam_rt: float,
    astar_rt: float,
    beam_complete: int,
    astar_complete: int,
    beam_score: Optional[float],
    astar_score: Optional[float],
    beam_nodes: int,
    astar_nodes: int,
) -> Tuple[SearchAlgorithm, str]:
    astar_pts = beam_pts = 0
    reasons: List[str] = []

    # Complete routes are the primary signal
    if astar_complete > beam_complete:
        astar_pts += 3
        reasons.append(f"A* found {astar_complete} complete routes vs {beam_complete} for beam")
    elif beam_complete > astar_complete:
        beam_pts += 3
        reasons.append(f"beam found {beam_complete} complete routes vs {astar_complete} for A*")

    # Best route score quality
    if beam_score is not None and astar_score is not None:
        if astar_score > beam_score + 0.1:
            astar_pts += 2
            reasons.append(f"A* best score {astar_score:.2f} > beam {beam_score:.2f}")
        elif beam_score > astar_score + 0.1:
            beam_pts += 2
            reasons.append(f"beam best score {beam_score:.2f} > A* {astar_score:.2f}")

    # Node efficiency
    if beam_nodes > 0 and astar_nodes < beam_nodes * 0.5:
        astar_pts += 1
        reasons.append(f"A* more node-efficient ({astar_nodes} vs {beam_nodes} nodes)")
    elif astar_nodes > 0 and beam_nodes < astar_nodes * 0.5:
        beam_pts += 1
        reasons.append(f"beam more node-efficient ({beam_nodes} vs {astar_nodes} nodes)")

    if astar_pts > beam_pts:
        return SearchAlgorithm.ASTAR, "; ".join(reasons) or "A* overall better performance"
    if beam_pts > astar_pts:
        return SearchAlgorithm.BEAM, "; ".join(reasons) or "beam overall better performance"

    # Tie → prefer faster
    if beam_rt <= astar_rt:
        return SearchAlgorithm.BEAM, "tie broken by speed — beam was faster"
    return SearchAlgorithm.ASTAR, "tie broken by speed — A* was faster"


async def generate_comparison(
    request: GetRoutesComparisonRequest,
) -> GetRoutesComparisonResponse:
    db_path = _resolve_ord_db_path()

    try:
        (beam_routes_dc, beam_stats_dc, beam_best_dc, beam_reasoning), \
        (astar_routes_dc, astar_stats_dc, astar_best_dc, astar_reasoning) = \
            await asyncio.gather(
                asyncio.to_thread(
                    _run_beam_search,
                    request.smiles,
                    db_path,
                    request.max_depth,
                    request.beam_width,
                    request.per_node_limit,
                    request.top_k,
                    request.require_exactly_2_reactants,
                ),
                asyncio.to_thread(
                    _run_astar_search,
                    request.smiles,
                    db_path,
                    request.max_depth,
                    request.max_nodes,
                    request.per_node_limit,
                    request.top_k,
                    request.heuristic_weight,
                    request.require_exactly_2_reactants,
                ),
            )
    except Exception as exc:
        logger.error("Comparison search failed for SMILES '%s': %s", request.smiles, exc)
        raise

    def _map_routes(routes_dc, best_dc, reasoning):
        best_id = id(best_dc) if best_dc is not None else None
        mapped = [
            _map_route(r, is_best=(id(r) == best_id), reasoning=reasoning if id(r) == best_id else None)
            for r in routes_dc
        ]
        mapped.sort(key=lambda r: (not r.is_best, -r.score))
        return mapped

    beam_routes = _map_routes(beam_routes_dc, beam_best_dc, beam_reasoning)
    astar_routes = _map_routes(astar_routes_dc, astar_best_dc, astar_reasoning)

    # Build beam stats
    beam_stats: Optional[ORDSearchStats] = None
    if beam_stats_dc:
        sd = beam_stats_dc.to_dict()
        beam_stats = ORDSearchStats(
            target_smiles=sd["target_smiles"],
            max_depth=sd["max_depth"],
            beam_width=sd["beam_width"],
            per_node_limit=sd["per_node_limit"],
            top_k=request.top_k,
            runtime_seconds=round(sd["runtime_seconds"], 3),
            nodes_explored=sd["nodes_explored"],
            reactions_queried=sd["reactions_queried"],
            routes_generated=sd["routes_generated"],
            avg_reactions_per_node=round(sd["avg_reactions_per_node"], 2),
        )

    astar_stats: Optional[AStarSearchStats] = None
    if astar_stats_dc:
        sd = astar_stats_dc.to_dict()
        astar_stats = AStarSearchStats(
            target_smiles=sd["target_smiles"],
            max_depth=sd["max_depth"],
            max_nodes=sd["max_nodes"],
            per_node_limit=sd["per_node_limit"],
            heuristic_weight=sd["heuristic_weight"],
            top_k=request.top_k,
            runtime_seconds=round(sd["runtime_seconds"], 3),
            nodes_explored=sd["nodes_explored"],
            reactions_queried=sd["reactions_queried"],
            routes_generated=sd["routes_generated"],
            states_pruned=sd["states_pruned"],
            avg_reactions_per_node=round(sd["avg_reactions_per_node"], 2),
        )

    beam_rt = beam_stats.runtime_seconds if beam_stats else 0.0
    astar_rt = astar_stats.runtime_seconds if astar_stats else 0.0
    beam_complete = sum(1 for r in beam_routes if r.is_complete)
    astar_complete = sum(1 for r in astar_routes if r.is_complete)
    beam_best_score = beam_routes[0].score if beam_routes else None
    astar_best_score = astar_routes[0].score if astar_routes else None

    score_advantage: Optional[float] = None
    if beam_best_score is not None and astar_best_score is not None:
        score_advantage = round(astar_best_score - beam_best_score, 4)

    recommendation, rec_reason = _recommend_algorithm(
        beam_rt, astar_rt,
        beam_complete, astar_complete,
        beam_best_score, astar_best_score,
        beam_stats.nodes_explored if beam_stats else 0,
        astar_stats.nodes_explored if astar_stats else 0,
    )

    comparison = AlgorithmComparisonSummary(
        faster_algorithm=SearchAlgorithm.BEAM if beam_rt <= astar_rt else SearchAlgorithm.ASTAR,
        beam_runtime_seconds=round(beam_rt, 3),
        astar_runtime_seconds=round(astar_rt, 3),
        time_diff_seconds=round(abs(beam_rt - astar_rt), 3),
        beam_routes_found=len(beam_routes),
        astar_routes_found=len(astar_routes),
        beam_complete_routes=beam_complete,
        astar_complete_routes=astar_complete,
        beam_best_score=beam_best_score,
        astar_best_score=astar_best_score,
        score_advantage=score_advantage,
        beam_nodes_explored=beam_stats.nodes_explored if beam_stats else 0,
        astar_nodes_explored=astar_stats.nodes_explored if astar_stats else 0,
        recommendation=recommendation,
        recommendation_reason=rec_reason,
    )

    note: Optional[str] = None
    if not beam_routes and not astar_routes:
        note = (
            f"No retrosynthesis routes found for '{request.smiles}' at "
            f"max_depth={request.max_depth}. Try increasing max_depth, "
            "beam_width, max_nodes, or using a simpler fragment."
        )

    return GetRoutesComparisonResponse(
        molecule_smiles=request.smiles,
        beam_routes=beam_routes,
        astar_routes=astar_routes,
        beam_stats=beam_stats,
        astar_stats=astar_stats,
        comparison=comparison,
        note=note,
    )
