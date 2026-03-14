from pydantic import BaseModel, Field
from typing import List, Optional
from .route_models import Route


class AnalyticalMethod(BaseModel):
    name: str = Field(..., description="Name of the analytical method (e.g., 'HPLC Purity Assay')")
    technique: str = Field(..., description="Analytical technique (e.g., 'HPLC-UV', 'GC-MS', 'NMR')")
    purpose: str = Field(..., description="What the method measures or confirms")
    analyte: Optional[str] = Field(None, description="Target analyte or compound being analyzed")
    conditions: Optional[str] = Field(None, description="Instrument conditions, column specs, mobile phase, etc.")
    acceptance_criteria: Optional[str] = Field(None, description="Pass/fail criteria for the method")
    reference_standards: Optional[List[str]] = Field(None, description="Reference standards required")
    sample_preparation: Optional[str] = Field(None, description="Sample preparation procedure")
    expected_results: Optional[str] = Field(None, description="Expected results and typical values")
    regulatory_guidance: Optional[str] = Field(None, description="Relevant ICH/USP/EP guidance")


class GetAnalyticalMethodsRequest(BaseModel):
    route: Route = Field(..., description="The synthesis route to generate analytical methods for")

    model_config = {
        "json_schema_extra": {
            "example": {
                "route": {
                    "source": "ORD — uspto-grants-2013_02 (DOI: 10.6084/m9.figshare.5104873.v1)",
                    "steps": [
                        {
                            "step_number": 1,
                            "description": (
                                "Methyl 2-(4-chlorophenyl)acetate (36.7 g, 199 mmol) and "
                                "paraformaldehyde (6.27 g, 209 mmol) were dissolved/suspended in "
                                "DMSO (400 mL) and treated with NaOMe (537 mg, 9.94 mmol). The "
                                "mixture was allowed to stir at room temperature for 2 hours to "
                                "completion by TLC analysis. The reaction was poured into ice-cold "
                                "water (700 mL) and neutralized with 1M HCl. The aqueous portion "
                                "was extracted with ethyl acetate (3×), dried over MgSO4, filtered, "
                                "and concentrated in vacuo. The pure product was isolated by silica "
                                "gel filtration (9:1 → 1:1 hexanes/EtOAc) to give methyl "
                                "2-(4-chlorophenyl)-3-hydroxypropanoate as a colorless oil (39.4 g, 92%)."
                            ),
                            "reagents": [
                                "Cl",
                                "ClC1=CC=C(C=C1)CC(=O)OC",
                                "C=O",
                                "CS(=O)C",
                                "C[O-].[Na+]",
                            ],
                            "conditions": (
                                "Temperature: room temperature (see notes_procedure); "
                                "Solvent: CS(=O)C; Catalyst: C[O-].[Na+]; "
                                "Source DOI: 10.6084/m9.figshare.5104873.v1"
                            ),
                            "expected_yield": 92.2,
                        },
                        {
                            "step_number": 2,
                            "description": (
                                "Methyl 2-(4-chlorophenyl)-3-hydroxypropanoate (39.4 g, 184 mmol) "
                                "was dissolved in DCM (500 mL) and treated with TEA (64.0 mL, "
                                "459 mmol). The solution was cooled to 0 °C and slowly treated with "
                                "MsCl (15.6 mL, 202 mmol), then stirred 30 minutes. The solution was "
                                "partitioned with 1N HCl, washed with diluted NaHCO3, dried over "
                                "MgSO4, filtered, and concentrated in vacuo. The product was isolated "
                                "by silica gel plug (9:1 hexanes/EtOAc) to give methyl "
                                "2-(4-chlorophenyl)acrylate as an oil (30.8 g, 85%)."
                            ),
                            "reagents": [
                                "ClC1=CC=C(C=C1)C(C(=O)OC)CO",
                                "C(C)N(CC)CC",
                                "CS(=O)(=O)Cl",
                                "ClCCl",
                            ],
                            "conditions": (
                                "Temperature: 0 °C; Solvent: ClCCl; "
                                "Source DOI: 10.6084/m9.figshare.5104873.v1"
                            ),
                            "expected_yield": 85.1,
                        },
                    ],
                    "reagents": [
                        "Cl",
                        "ClC1=CC=C(C=C1)CC(=O)OC",
                        "C=O",
                        "CS(=O)C",
                        "C[O-].[Na+]",
                        "ClC1=CC=C(C=C1)C(C(=O)OC)CO",
                        "C(C)N(CC)CC",
                        "CS(=O)(=O)Cl",
                        "ClCCl",
                    ],
                    "equipment": [
                        "Round-bottom flask",
                        "Magnetic stirrer with hotplate",
                        "Ice bath",
                        "Fritted filter / Büchner funnel (vacuum filtration)",
                        "Silica gel plug (column chromatography)",
                        "Rotary evaporator (in-vacuo concentration)",
                        "Analytical balance",
                        "TLC plates (reaction progress monitoring)",
                    ],
                    "safety_assessment": {
                        "hazardous_reagents": [
                            "Cl", "ClC1=CC=C(C=C1)CC(=O)OC", "C=O",
                            "CS(=O)C", "C[O-].[Na+]",
                            "ClC1=CC=C(C=C1)C(C(=O)OC)CO",
                            "C(C)N(CC)CC", "CS(=O)(=O)Cl", "ClCCl",
                        ],
                        "hazardous_steps": [
                            (
                                "Step 1: No safety notes recorded in ORD for reaction "
                                "ord-3b794dbd2fff401d8ced19f2ec0b62d5. "
                                "Refer to source DOI: 10.6084/m9.figshare.5104873.v1. "
                                "Procedure excerpt: Methyl 2-(4-chlorophenyl)acetate (36.7 g, "
                                "199 mmol) and paraformaldehyde were dissolved in DMSO..."
                            ),
                            (
                                "Step 2: No safety notes recorded in ORD for reaction "
                                "ord-79a147ea3d114f1f879bae9287ab38d2. "
                                "Refer to source DOI: 10.6084/m9.figshare.5104873.v1. "
                                "Procedure excerpt: Methyl 2-(4-chlorophenyl)-3-hydroxypropanoate "
                                "was dissolved in DCM, cooled to 0 °C and treated with MsCl..."
                            ),
                        ],
                        "explosive_intermediates": [],
                        "banned_solvents": [],
                        "ppe_requirements": [
                            "Chemical-resistant gloves (nitrile)",
                            "Safety goggles",
                            "Laboratory coat",
                            "Fume hood required — solvents present in ORD record: CS(=O)C, ClCCl",
                        ],
                    },
                    "regulatory_compliance": {
                        "reach_compliant": True,
                        "ich_compliant": True,
                        "notes": [
                            "ORD dataset: uspto-grants-2013_02",
                            "Source DOI: 10.6084/m9.figshare.5104873.v1",
                            "Final product SMILES: ClC1=CC=C(C=C1)C(C(=O)OC)=C",
                            "Regulatory applicability must be assessed per jurisdiction using the referenced publication.",
                        ],
                    },
                    "toxicology_report": {
                        "acute_oral_toxicity": (
                            "Product SMILES: ClC1=CC=C(C=C1)C(C(=O)OC)=C. "
                            "No acute oral toxicity recorded in ORD reaction "
                            "ord-79a147ea3d114f1f879bae9287ab38d2. "
                            "Refer to source publication (DOI: 10.6084/m9.figshare.5104873.v1) and applicable SDS."
                        ),
                        "skin_sensitization": (
                            "Solvents in ORD record: CS(=O)C, ClCCl. "
                            "Consult SDS for each compound listed in the reagents field."
                        ),
                        "mutagenicity": (
                            "No mutagenicity data recorded in ORD reaction "
                            "ord-79a147ea3d114f1f879bae9287ab38d2. "
                            "Refer to DOI: 10.6084/m9.figshare.5104873.v1 for full experimental characterisation."
                        ),
                        "hepatotoxicity": (
                            "No hepatotoxicity data recorded in ORD for product "
                            "ClC1=CC=C(C=C1)C(C(=O)OC)=C. "
                            "Consult the referenced patent/publication."
                        ),
                    },
                    "estimated_cycle_time": {
                        "total_time": (
                            "~12 hours (estimated from procedure text in ORD reactions "
                            "ord-3b794dbd2fff401d8ced19f2ec0b62d5, "
                            "ord-79a147ea3d114f1f879bae9287ab38d2; "
                            "DOI: 10.6084/m9.figshare.5104873.v1)"
                        ),
                        "max_temperature": "0 °C",
                        "expected_yield": 78.5,
                    },
                }
            }
        }
    }


class GetAnalyticalMethodsResponse(BaseModel):
    methods: List[AnalyticalMethod] = Field(..., description="List of recommended analytical methods")
    total: int = Field(..., description="Total number of methods returned")
    notes: Optional[str] = Field(None, description="Additional notes on analytical strategy")
