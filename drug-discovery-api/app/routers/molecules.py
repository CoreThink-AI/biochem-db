from fastapi import APIRouter, HTTPException, Depends, status
import duckdb

from app.models.molecule_models import SearchMoleculesRequest, SearchMoleculesResponse
from app.services.molecule_service import search_molecules
from app.db.database import get_db

router = APIRouter(prefix="/search-molecules", tags=["Molecules"])


@router.post(
    "",
    response_model=SearchMoleculesResponse,
    summary="Search molecules by name or SMILES prefix",
    description="""
Autocomplete / typeahead search for molecules.

Input: Beginning of a molecule name or SMILES string.

Output: List of matching molecules with SMILES, InChI, molecular weight, formula, and synonyms.

Examples:
- `"aspirin"` → returns Aspirin and similar named compounds
- `"CC(=O)"` → returns molecules whose SMILES starts with `CC(=O)`
- `"ibu"` → returns Ibuprofen
""",
)
async def search_molecules_endpoint(
    request: SearchMoleculesRequest,
    conn: duckdb.DuckDBPyConnection = Depends(get_db),
) -> SearchMoleculesResponse:
    try:
        molecules = search_molecules(request, conn)
        return SearchMoleculesResponse(
            molecules=molecules,
            query=request.query,
            total=len(molecules),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Molecule search failed: {str(e)}",
        )
