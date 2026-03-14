from pydantic import BaseModel, Field
from typing import List, Optional


class Molecule(BaseModel):
    name: str = Field(..., description="Common name or IUPAC name")
    smiles: str = Field(..., description="SMILES notation")
    inchi: Optional[str] = Field(None, description="InChI string")
    molecular_weight: Optional[float] = Field(None, description="Molecular weight in g/mol")
    formula: Optional[str] = Field(None, description="Molecular formula")
    synonyms: Optional[List[str]] = Field(None, description="Alternative names and trade names")


class SearchMoleculesRequest(BaseModel):
    query: str = Field(
        ...,
        description="Beginning of a SMILES string or molecule name for autocomplete search",
        min_length=1,
        max_length=500
    )
    limit: int = Field(20, description="Maximum number of results to return", ge=1, le=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "aspirin",
                "limit": 10
            }
        }
    }


class SearchMoleculesResponse(BaseModel):
    molecules: List[Molecule] = Field(..., description="List of matching molecules")
    query: str = Field(..., description="The original search query")
    total: int = Field(..., description="Total number of matches found")
