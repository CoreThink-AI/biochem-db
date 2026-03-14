from fastapi import APIRouter, HTTPException, status

from app.models.document_models import GenerateDocumentsRequest, GenerateDocumentsResponse
from app.services.document_service import generate_documents

router = APIRouter(prefix="/generate-documents", tags=["Documents"])


@router.post(
    "",
    response_model=GenerateDocumentsResponse,
    summary="Generate pharmaceutical documents from a synthesis route",
    description="""
Generate GMP-compliant pharmaceutical documents from a synthesis route.

Input: A synthesis route object (from `/get-routes`) and a list of document types.

Available document types:
| Type | Description |
|------|-------------|
| `process_chemistry` | Detailed process chemistry development report |
| `batch_manufacturing` | GMP Batch Manufacturing Record (BMR) with operator checkboxes |
| `tech_transfer` | Technology Transfer Package with CPP/CQA tables and FMEA |
| `analytical_method` | Analytical Methods Document with full instrument conditions |
| `safety_ghs_labels` | GHS safety labels for all reagents and intermediates |
| `safety_process_summary` | Safety Data Sheet — process safety summary |
| `safety_emergency_response` | Safety Data Sheet — emergency response procedures |
| `safety_waste_disposal` | Safety Data Sheet — waste disposal guidelines |

Output: Generated documents in Markdown format, one per requested type.

""",
)
async def generate_documents_endpoint(
    request: GenerateDocumentsRequest,
) -> GenerateDocumentsResponse:
    try:
        documents = await generate_documents(request)
        return GenerateDocumentsResponse(
            documents=documents,
            total=len(documents),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document generation failed: {str(e)}",
        )
