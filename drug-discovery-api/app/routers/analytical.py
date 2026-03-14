from fastapi import APIRouter, HTTPException, status

from app.models.analytical_models import GetAnalyticalMethodsRequest, GetAnalyticalMethodsResponse
from app.services.analytical_service import get_analytical_methods

router = APIRouter(prefix="/get-analytical-methods", tags=["Analytical Methods"])


@router.post(
    "",
    response_model=GetAnalyticalMethodsResponse,
    summary="Get analytical methods for a synthesis route",
    description="""
Recommend analytical methods appropriate for the given synthesis route.

**Input:** A synthesis route object (from `/get-routes`).

**Output:** A list of analytical methods, each including:
- Technique (HPLC-UV, GC-MS, NMR, ICP-OES, Karl Fischer, etc.)
- Purpose (what is being measured)
- Instrument conditions (column, mobile phase, gradient, detector)
- Acceptance criteria
- Reference standards required
- Sample preparation procedure
- Relevant ICH/USP/EP guidance

**Typical methods returned:**
- Identity (NMR, MS)
- Purity assay (RP-HPLC)
- Related substances (HPLC impurity profile)
- Residual solvents (GC-HS per ICH Q3C)
- Water content (Karl Fischer)
- Chiral purity (if stereocenters present)
- Elemental impurities (ICP-MS per ICH Q3D if metal catalysts used)
- In-process controls
        """,
)
async def get_analytical_methods_endpoint(
    request: GetAnalyticalMethodsRequest,
) -> GetAnalyticalMethodsResponse:
    try:
        methods, notes = await get_analytical_methods(request.route)
        return GetAnalyticalMethodsResponse(
            methods=methods,
            total=len(methods),
            notes=notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytical method generation failed: {str(e)}",
        )
