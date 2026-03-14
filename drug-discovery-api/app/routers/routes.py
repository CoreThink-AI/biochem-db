from fastapi import APIRouter, HTTPException, status

from app.models.route_models import GetRoutesRequest, GetRoutesResponse
from app.services.route_service import generate_routes

router = APIRouter(prefix="/get-routes", tags=["Routes"])


@router.post(
    "",
    response_model=GetRoutesResponse,
    summary="Find retrosynthesis routes from the ORD database",
    description="""
Identify synthesis pathways for a target molecule by running a **beam-search
over 2.37 million reactions** in the Open Reaction Database (ORD) stored locally
in DuckDB.

### How depth works

```
depth 0  →  target SMILES
depth 1  →  reactions whose product == target  (direct precursors)
depth 2  →  reactions for each depth-1 precursor
depth N  →  continues recursively up to max_depth
```

Each distinct pathway through the search tree is returned as one **ORDRoute**.
Routes are ranked by a composite scorer (yield · temperature · step count ·
safety · completeness).  The top-scoring route is flagged `is_best: true`.

### Key request parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_depth` | 4 | Maximum recursive depth |
| `beam_width` | 25 | Candidate routes kept per depth level |
| `per_node_limit` | 200 | Max ORD reactions fetched per product SMILES |
| `top_k` | 5 | Routes returned in the response |
| `require_exactly_2_reactants` | false | Restrict to bimolecular reactions only |

### Per-step fields

Every step in a route includes:
- `reaction_id` — ORD reaction identifier
- `product_smiles` / `reactants` — SMILES (the reaction itself)
- `reagent_smiles` / `solvent_smiles` / `catalyst_smiles` — conditions
- `yield_pct` / `temperature_c` — quantitative data where available
- `doi` + `doi_url` — source publication DOI
- `google_scholar_url` — pre-built `scholar.google.com/scholar?q=doi:…` link
- `notes_procedure` — full experimental procedure text from ORD
- `depth` — which retrosynthetic level this step sits at (1 = closest to target)

### `open_molecules`

Molecules in this list still need a synthesis route — they were not resolved
within the given `max_depth`.  An empty list means the route is **complete**
(`is_complete: true`).

### `search_stats`

Runtime diagnostics: nodes explored, reactions queried, total routes
generated before pruning, and wall-clock time.
""",
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
