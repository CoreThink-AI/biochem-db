from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from .route_models import Route
from .ord_models import LiteratureReference


class DocumentType(str, Enum):
    PROCESS_CHEMISTRY = "process_chemistry"
    BATCH_MANUFACTURING = "batch_manufacturing"
    TECH_TRANSFER = "tech_transfer"
    ANALYTICAL_METHOD = "analytical_method"
    SAFETY_GHS_LABELS = "safety_ghs_labels"
    SAFETY_PROCESS_SUMMARY = "safety_process_summary"
    SAFETY_EMERGENCY_RESPONSE = "safety_emergency_response"
    SAFETY_WASTE_DISPOSAL = "safety_waste_disposal"


DOCUMENT_TYPE_DESCRIPTIONS = {
    DocumentType.PROCESS_CHEMISTRY: "Process Chemistry document — detailed reaction mechanisms, optimization data, and scale-up considerations",
    DocumentType.BATCH_MANUFACTURING: "Batch Manufacturing Record (BMR) — GMP-compliant step-by-step manufacturing instructions",
    DocumentType.TECH_TRANSFER: "Technology Transfer Package — all information required to transfer the synthesis to another site",
    DocumentType.ANALYTICAL_METHOD: "Analytical Method document — HPLC, NMR, and other characterization methods",
    DocumentType.SAFETY_GHS_LABELS: "GHS safety labels for all reagents and intermediates",
    DocumentType.SAFETY_PROCESS_SUMMARY: "Safety Data Sheet — process safety summary",
    DocumentType.SAFETY_EMERGENCY_RESPONSE: "Safety Data Sheet — emergency response procedures",
    DocumentType.SAFETY_WASTE_DISPOSAL: "Safety Data Sheet — waste disposal guidelines",
}


class GenerateDocumentsRequest(BaseModel):
    route: Route = Field(..., description="The synthesis route to generate documents for")
    types: List[DocumentType] = Field(
        ...,
        description="List of document types to generate",
        min_length=1
    )
    # ── Optional ORD literature enrichment ────────────────────────────────
    target_smiles: Optional[str] = Field(
        None,
        description=(
            "SMILES of the target molecule.  When provided, each generated document "
            "will be enriched with `literature` — a list of ORD-sourced references "
            "(DOI, CrossRef metadata, Google Scholar URL, Unpaywall download link)."
        ),
    )
    literature_limit: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of literature references to attach per document (default 5)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "route": {
                    "source": "Literature",
                    "steps": [
                        {
                            "step_number": 1,
                            "description": "Acetylation of salicylic acid with acetic anhydride (H3PO4 cat.) at 50 °C for 15 min, quenched with ice-cold water.",
                            "reagents": ["Salicylic acid (10.0 g, 72.4 mmol)", "Acetic anhydride (8.2 mL, 1.2 eq)", "Phosphoric acid 85% (5 drops, cat.)"],
                            "conditions": "Temperature: 50 °C; Time: 15 min; Quench: ice-cold water (0 °C); Atmosphere: open; Fume hood required",
                            "expected_yield": 85.0,
                        },
                        {
                            "step_number": 2,
                            "description": "Recrystallisation of crude aspirin from hot ethanol / water mixture; cool to 0 °C, filter, wash with ice-cold water, dry at 40 °C.",
                            "reagents": ["Crude acetylsalicylic acid (from Step 1)", "Ethanol 95% (15 mL)", "Distilled water (40 mL)"],
                            "conditions": "Temperature: 50–55 °C (dissolve) → 0 °C (crystallise); Time: 2 h; Drying: 40 °C vacuum oven, 12 h",
                            "expected_yield": 92.0,
                        },
                    ],
                    "reagents": ["Salicylic acid", "Acetic anhydride", "Phosphoric acid (cat.)", "Ethanol 95%", "Distilled water"],
                    "equipment": ["250 mL round-bottom flask", "Ice bath", "Magnetic stirrer/hotplate", "Büchner funnel", "Vacuum oven 40 °C"],
                    "safety_assessment": {
                        "hazardous_reagents": [
                            "Acetic anhydride — GHS05 Corrosive, GHS07 Irritant; reacts with water; flash point 49 °C",
                            "Salicylic acid — GHS07 Irritant; LD50 oral rat 891 mg/kg",
                            "Phosphoric acid 85% — GHS05 Corrosive; causes severe burns",
                            "Ethanol 95% — GHS02 Flammable; flash point 13 °C",
                        ],
                        "hazardous_steps": [
                            "Step 1 quench: add water dropwise to acetic anhydride at 0 °C — highly exothermic",
                            "Step 1: acetic anhydride vapours — fume hood mandatory",
                        ],
                        "explosive_intermediates": [],
                        "banned_solvents": [],
                        "ppe_requirements": ["Nitrile gloves ≥0.3 mm", "Safety goggles / face shield", "Lab coat", "Closed-toe shoes", "Fume hood"],
                    },
                    "regulatory_compliance": {
                        "reach_compliant": True,
                        "ich_compliant": True,
                        "notes": [
                            "Ethanol — ICH Q3C Class 3 solvent; within PDE limits",
                            "No SVHC in REACH Annex XIV identified",
                            "Salicylic acid impurity — monitor by HPLC; limit ≤0.1%",
                        ],
                    },
                    "toxicology_report": {
                        "acute_oral_toxicity": "GHS Category 4; aspirin LD50 oral rat 200 mg/kg",
                        "skin_sensitization": "Not classified as sensitiser; salicylic acid impurity — mild sensitiser",
                        "mutagenicity": "Negative Ames test; no ICH M7 structural alerts",
                        "hepatotoxicity": "Dose-dependent hepatotoxicity at overdose levels; low risk at synthesis scale",
                    },
                    "estimated_cycle_time": {
                        "total_time": "~15 hours (1 h reaction + 1 h workup + 2 h recrystallisation + 12 h drying)",
                        "max_temperature": "55 °C",
                        "expected_yield": 78.0,
                    },
                },
                "types": ["process_chemistry", "batch_manufacturing", "safety_ghs_labels", "analytical_method"],
                "target_smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "literature_limit": 5,
            }
        }
    }


class Document(BaseModel):
    type: DocumentType = Field(..., description="Document type")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Full document content in Markdown format")
    sections: List[str] = Field(default_factory=list, description="List of section headings in the document")

    # ── ORD literature references ──────────────────────────────────────────
    literature: Optional[List[LiteratureReference]] = Field(
        None,
        description=(
            "Literature references sourced from the Open Reaction Database (ORD) "
            "for the target molecule SMILES.  Each entry includes the DOI, "
            "CrossRef bibliographic metadata, a Google Scholar URL, and—where "
            "available—an open-access PDF download link resolved via Unpaywall."
        ),
    )
    literature_total: Optional[int] = Field(
        None,
        description="Total number of ORD reactions found for the target SMILES (may exceed len(literature))",
    )


class GenerateDocumentsResponse(BaseModel):
    documents: List[Document] = Field(..., description="Generated documents")
    total: int = Field(..., description="Number of documents generated")
