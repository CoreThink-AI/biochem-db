from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db
from app.routers import routes, molecules, documents, analytical, ord, sample_data

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## Drug Discovery API

Synthesis route generation, pharmaceutical document automation, and ORD literature analytics.

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /get-routes` | Generate synthesis routes for a target molecule |
| `POST /search-molecules` | Autocomplete search for molecules by name or SMILES |
| `POST /generate-documents` | Generate GMP documents from a synthesis route (optionally enriched with ORD literature) |
| `POST /get-analytical-methods` | Recommend analytical methods for a synthesis route |
| `POST /analytics/ord-literature` | Resolve DOIs, Google Scholar URLs & open-access download links for a SMILES via ORD + CrossRef + Unpaywall |

### ORD Literature Analytics

The `/analytics/ord-literature` endpoint searches **2.37 million ORD reactions** stored locally
in DuckDB and surfaces peer-reviewed literature for any SMILES:

- `doi` — Digital Object Identifier of the source paper
- `google_scholar_url` — pre-populated `scholar.google.com/scholar?q=doi:{doi}` link
- `download_url` — open-access PDF URL null if closed-access
- `is_open_access` / `oa_status` — gold / green / hybrid / closed
- Full CrossRef metadata: title, authors, journal, year, volume, pages, abstract

The `POST /generate-documents` endpoint also accepts `target_smiles` to embed these
references directly inside each generated document (`literature` field).

""",
    openrouter_tags=[
        {"name": "Routes", "description": "Synthesis route generation"},
        {"name": "Molecules", "description": "Molecule search and lookup"},
        {"name": "Documents", "description": "Pharmaceutical document generation"},
        {"name": "Analytical Methods", "description": "Analytical method recommendations"},
        {
            "name": "Sample Data",
            "description": (
                "Ready-to-use sample request payloads for /generate-documents and "
                "/get-analytical-methods. Hit GET /sample-data/generate-documents or "
                "GET /sample-data/get-analytical-methods to get a complete, validated "
                "JSON body you can POST directly — no manual Route construction needed."
            ),
        },
        {
            "name": "Analytics – ORD Literature",
            "description": (
                "SMILES → DOI resolution using the local ORD DuckDB (2.37 M reactions). "
                "Enriched with CrossRef bibliographic metadata and Unpaywall open-access "
                "PDF download links. Google Scholar URLs constructed automatically."
            ),
        },
    ],
    lifespan=lifespan,
    docs_url="/docs",       
    redoc_url="/redoc",     
    openrouter_url="/openrouter.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
app.include_router(molecules.router)
app.include_router(documents.router)
app.include_router(analytical.router)
app.include_router(ord.router)
app.include_router(sample_data.router)


@app.get("/", tags=["Health"], summary="Health check")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"], summary="Detailed health check")
async def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "model": settings.ai_model,
    }
