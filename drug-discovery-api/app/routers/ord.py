from fastapi import APIRouter, HTTPException, status

from app.models.ord_models import ORDSmilesLookupRequest, ORDSmilesLookupResponse
from app.services.ord_service import lookup_smiles_literature

router = APIRouter(prefix="/analytics", tags=["Analytics – ORD Literature"])


@router.post(
    "/ord-literature",
    response_model=ORDSmilesLookupResponse,
    summary="Resolve literature references (DOI + download links) for a SMILES via ORD",
    description="""
### Response fields (per reference)

- `doi` — Digital Object Identifier
- `title` / `authors` / `journal` / `year` — CrossRef metadata
- `crossref_url` — canonical `https://doi.org/…` link
- `google_scholar_url` — `https://scholar.google.com/scholar?q=doi:{doi}`
- `download_url` — open-access PDF URL (null if not available)
- `is_open_access` / `oa_status` — Unpaywall OA status
- `ord_reaction_id` — originating ORD reaction identifier
- `role_in_reaction` — role of the SMILES in the reaction (reactant / product / reagent…)
""",
)
async def ord_literature_lookup(
    request: ORDSmilesLookupRequest,
) -> ORDSmilesLookupResponse:
    try:
        references, total_reactions, sources, note = await lookup_smiles_literature(
            smiles=request.smiles,
            limit=request.limit,
            role=request.role,
            email=request.email,
        )
        return ORDSmilesLookupResponse(
            smiles=request.smiles,
            total_reactions_found=total_reactions,
            references=references,
            total_references=len(references),
            sources_queried=sources,
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
            detail=f"ORD literature lookup failed: {exc}",
        )
