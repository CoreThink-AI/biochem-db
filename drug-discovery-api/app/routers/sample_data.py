from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any, Dict

from app.models.sample_data import (
    SAMPLE_ROUTE,
    SAMPLE_GENERATE_DOCUMENTS_REQUEST,
    SAMPLE_GET_ANALYTICAL_METHODS_REQUEST,
    SAMPLE_GET_ROUTES_REQUEST,
    SAMPLE_SEARCH_MOLECULES_REQUEST,
    SAMPLE_ORD_LITERATURE_REQUEST,
    _BEST_ROUTES_SMILES,
    _TARGET_SMILES,
)

router = APIRouter(prefix="/sample-data", tags=["Sample Data"])


@router.get(
    "/get-routes",
    summary="Sample request body for POST /get-routes",
    description=(
        "Returns a ready-to-use GetRoutesRequest payload — POST it directly to "
        "`/get-routes`.\n\n"
        f"Uses SMILES `{_BEST_ROUTES_SMILES}` *(N-(4-methylphenyl)-4-(trifluoromethyl)aniline)* "
        "— the molecule with the most direct retrosynthesis routes in `retro_edges` (862 entries), "
        "guaranteeing a real response.\n\n"
        "Parameters: `max_depth=3`, `beam_width=25`, `per_node_limit=200`, `top_k=5`."
    ),
    response_class=JSONResponse,
)
def sample_get_routes() -> Dict[str, Any]:
    return SAMPLE_GET_ROUTES_REQUEST


@router.get(
    "/search-molecules",
    summary="Sample request body for POST /search-molecules",
    description=(
        "Returns a ready-to-use SearchMoleculesRequest payload — POST it directly to "
        "`/search-molecules`.\n\n"
        "Query: `ibuprofen` — a named entry in `drug_discovery.duckdb`.\n\n"
        "You can replace `query` with any molecule name prefix (e.g. `aspirin`, `paracetamol`) "
        "or a SMILES prefix (e.g. `CC(=O)`)."
    ),
    response_class=JSONResponse,
)
def sample_search_molecules() -> Dict[str, Any]:
    return SAMPLE_SEARCH_MOLECULES_REQUEST


@router.get(
    "/generate-documents",
    summary="Sample request body for POST /generate-documents",
    description=(
        "Returns a fully-populated GenerateDocumentsRequest — POST it directly to "
        "`/generate-documents`.\n\n"
        "Includes:\n"
        "- `route` built from real ORD reactions in `retrosynthesis.duckdb`\n"
        "- `types`: process_chemistry, batch_manufacturing, safety_ghs_labels, analytical_method\n"
        f"- `target_smiles`: `{_TARGET_SMILES}` (final product from the ORD chain)\n"
        "- `literature_limit`: 5 (enriches each document with ORD literature references)"
    ),
    response_class=JSONResponse,
)
def sample_generate_documents() -> Dict[str, Any]:
    return SAMPLE_GENERATE_DOCUMENTS_REQUEST


@router.get(
    "/get-analytical-methods",
    summary="Sample request body for POST /get-analytical-methods",
    description=(
        "Returns a fully-populated GetAnalyticalMethodsRequest — POST it directly to "
        "`/get-analytical-methods`.\n\n"
        "Contains a complete ORD Route with real reagent SMILES, procedure text, "
        "yield percentages, temperature, and DOI sourced from `retrosynthesis.duckdb`."
    ),
    response_class=JSONResponse,
)
def sample_analytical_methods() -> Dict[str, Any]:
    return SAMPLE_GET_ANALYTICAL_METHODS_REQUEST


@router.get(
    "/ord-literature",
    summary="Sample request body for POST /analytics/ord-literature",
    description=(
        "Returns a ready-to-use ORDSmilesLookupRequest — POST it directly to "
        "`/analytics/ord-literature`.\n\n"
        f"Uses SMILES `{_TARGET_SMILES}` (methyl 2-(4-chlorophenyl)acrylate — "
        "the Step 2 product of the ORD sample chain, with 12 reactions in `retro_edges`).\n\n"
        "Response will include DOI, CrossRef bibliographic metadata, Google Scholar URL, "
        "and Unpaywall open-access download link."
    ),
    response_class=JSONResponse,
)
def sample_ord_literature() -> Dict[str, Any]:
    return SAMPLE_ORD_LITERATURE_REQUEST


@router.get(
    "/route",
    summary="Bare Route object (building block for generate-documents / get-analytical-methods)",
    description=(
        "Returns the raw Route object sourced from `retrosynthesis.duckdb` at startup.\n\n"
        "This is the `route` field embedded inside the payloads at "
        "`/sample-data/generate-documents` and `/sample-data/get-analytical-methods`.\n\n"
        "2-step ORD chain:\n"
        "- Step 1: methyl 4-chlorophenylacetate + paraformaldehyde → "
        "methyl 2-(4-chlorophenyl)-3-hydroxypropanoate (92 % yield, DMSO)\n"
        "- Step 2: hydroxypropanoate + TEA + MsCl → "
        "methyl 2-(4-chlorophenyl)acrylate (85 % yield, 0 °C, DCM)\n\n"
        "Source DOI: `10.6084/m9.figshare.5104873.v1`"
    ),
    response_class=JSONResponse,
)
def sample_route() -> Dict[str, Any]:
    return SAMPLE_ROUTE
