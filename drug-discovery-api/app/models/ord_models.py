from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class LiteratureReference(BaseModel):
    """A citable literature reference associated with a SMILES / reaction."""

    doi: Optional[str] = Field(
        None,
        description="Digital Object Identifier, e.g. '10.1126/science.abb9325'",
    )
    ord_reaction_id: Optional[str] = Field(
        None,
        description="ORD reaction identifier, e.g. 'ord-abc123'",
    )
    role_in_reaction: Optional[str] = Field(
        None,
        description="Role of the queried SMILES in the reaction: "
                    "'reactant' | 'product' | 'reagent' | 'catalyst' | 'solvent' | 'unknown'",
    )

    title: Optional[str] = Field(None, description="Paper / article title")
    authors: Optional[List[str]] = Field(
        None, description="Author list in 'Last, First' format"
    )
    journal: Optional[str] = Field(None, description="Journal or book title")
    year: Optional[int] = Field(None, description="Publication year")
    volume: Optional[str] = Field(None, description="Journal volume")
    issue: Optional[str] = Field(None, description="Journal issue")
    pages: Optional[str] = Field(None, description="Page range, e.g. '1234-1240'")
    publisher: Optional[str] = Field(None, description="Publisher name")
    abstract: Optional[str] = Field(
        None, description="Abstract snippet (first 500 chars) if available"
    )

    crossref_url: Optional[str] = Field(
        None,
        description="Canonical CrossRef DOI URL, e.g. 'https://doi.org/10.1126/...'",
    )
    google_scholar_url: Optional[str] = Field(
        None,
        description="Google Scholar search URL pre-populated with the DOI or title",
    )
    download_url: Optional[str] = Field(
        None,
        description="Open-access PDF download URL resolved via Unpaywall "
                    "(null if no open-access version found)",
    )
    is_open_access: Optional[bool] = Field(
        None,
        description="True if an open-access version exists (from Unpaywall)",
    )
    oa_status: Optional[str] = Field(
        None,
        description="Open-access status: 'gold' | 'hybrid' | 'bronze' | 'green' | 'closed'",
    )

    dataset_id: Optional[str] = Field(
        None,
        description="ORD dataset the reaction belongs to, e.g. 'ord_dataset-abc123'",
    )
    reaction_smiles: Optional[str] = Field(
        None,
        description="Full reaction SMILES from ORD, e.g. 'CC>>CCO'",
    )


class ORDSmilesLookupRequest(BaseModel):
    """Request body for looking up literature references via ORD for a given SMILES."""

    smiles: str = Field(
        ...,
        min_length=1,
        description="SMILES string of the molecule to look up",
    )
    limit: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of literature references to return",
    )
    role: Optional[str] = Field(
        None,
        description="Filter by role in reaction: "
                    "'reactant' | 'product' | 'reagent' | 'catalyst' | 'solvent'",
    )
    email: Optional[str] = Field(
        None,
        description="E-mail address passed to the Unpaywall API (improves rate-limit). "
                    "Falls back to a generic address if omitted.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "limit": 10,
                "role": "product",
                "email": "researcher@example.com",
            }
        }
    }


class ORDSmilesLookupResponse(BaseModel):
    smiles: str = Field(..., description="Input SMILES string (echoed back)")
    total_reactions_found: int = Field(
        ...,
        description="Total ORD reactions found that contain this SMILES",
    )
    references: List[LiteratureReference] = Field(
        ...,
        description="De-duplicated literature references with DOI, Google Scholar URL, "
                    "CrossRef metadata, and (where available) open-access download link",
    )
    total_references: int = Field(
        ...,
        description="Number of unique references returned (≤ limit)",
    )
    sources_queried: List[str] = Field(
        default_factory=list,
        description="External APIs that were queried: 'ORD', 'CrossRef', 'Unpaywall'",
    )
    note: Optional[str] = Field(
        None,
        description="Additional context, warnings, or fallback notes",
    )
