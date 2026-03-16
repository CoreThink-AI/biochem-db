from fastapi import APIRouter, HTTPException, status

from app.models.route_models import (
    GetRoutesComparisonRequest,
    GetRoutesComparisonResponse,
    GetRoutesRequest,
    GetRoutesResponse,
)
from app.services.route_service import generate_comparison, generate_routes

router = APIRouter(prefix="/get-routes", tags=["Routes"])


@router.post(
    "",
    response_model=GetRoutesResponse,
    summary="Find retrosynthesis routes from the ORD database",
    description="""searches for retrosynthesis routes from the ORD database""",
)
async def get_routes(request: GetRoutesRequest) -> GetRoutesResponse:
    try:
        ord_routes, search_stats, note = await generate_routes(request)
        return GetRoutesResponse(
            routes=ord_routes,
            molecule_smiles=request.smiles,
            total_routes=len(ord_routes),
            search_stats=search_stats,
            note=note,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route generation failed: {exc}",
        )


@router.post(
    "/compare",
    response_model=GetRoutesComparisonResponse,
    summary="Compare beam-search vs A* retrosynthesis routes",
    description="""compares beam-search vs A* retrosynthesis routes""",
    openapi_extra={
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "example": {
                            "molecule_smiles": "CC(=O)Oc1ccccc1C(=O)O",
                            "beam_routes": ["... top-K ORDRoute objects ..."],
                            "astar_routes": ["... top-K ORDRoute objects ..."],
                            "beam_stats": {
                                "target_smiles": "CC(=O)Oc1ccccc1C(=O)O",
                                "max_depth": 4,
                                "beam_width": 25,
                                "per_node_limit": 200,
                                "top_k": 5,
                                "runtime_seconds": 1.842,
                                "nodes_explored": 98,
                                "reactions_queried": 98,
                                "routes_generated": 4312,
                                "avg_reactions_per_node": 44.0,
                            },
                            "astar_stats": {
                                "target_smiles": "CC(=O)Oc1ccccc1C(=O)O",
                                "max_depth": 4,
                                "max_nodes": 500,
                                "per_node_limit": 200,
                                "heuristic_weight": 0.5,
                                "top_k": 5,
                                "runtime_seconds": 3.217,
                                "nodes_explored": 500,
                                "reactions_queried": 500,
                                "routes_generated": 18420,
                                "states_pruned": 312,
                                "avg_reactions_per_node": 36.8,
                            },
                            "comparison": {
                                "faster_algorithm": "beam",
                                "beam_runtime_seconds": 1.842,
                                "astar_runtime_seconds": 3.217,
                                "time_diff_seconds": 1.375,
                                "beam_routes_found": 5,
                                "astar_routes_found": 5,
                                "beam_complete_routes": 2,
                                "astar_complete_routes": 3,
                                "beam_best_score": 2.15,
                                "astar_best_score": 2.48,
                                "score_advantage": 0.33,
                                "beam_nodes_explored": 98,
                                "astar_nodes_explored": 500,
                                "recommendation": "astar",
                                "recommendation_reason": "A* found 3 complete routes vs 2 for beam; A* best score 2.48 > beam 2.15",
                            },
                            "note": None,
                        }
                    }
                }
            }
        }
    },
)
async def compare_routes(request: GetRoutesComparisonRequest) -> GetRoutesComparisonResponse:
    try:
        return await generate_comparison(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison search failed: {exc}",
        )
