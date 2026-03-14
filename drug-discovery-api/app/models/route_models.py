from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ORDSynthesisStep(BaseModel):
    step_number: int = Field(..., description="1-based step index in this route")
    depth: int = Field(..., description="Depth level in the retrosynthesis tree (0 = target)")

    reaction_id: str = Field(..., description="ORD reaction identifier, e.g. 'ord-abc123'")
    product_smiles: str = Field(..., description="SMILES of the molecule this step produces")
    reactants: List[str] = Field(..., description="SMILES of all reactants consumed in this step")

    reagent_smiles: Optional[str] = Field(None, description="Reagent SMILES (dot-separated list)")
    solvent_smiles: Optional[str] = Field(None, description="Solvent SMILES")
    catalyst_smiles: Optional[str] = Field(None, description="Catalyst SMILES")
    yield_pct: Optional[float] = Field(None, description="Reported yield (%)", ge=0, le=100)
    temperature_c: Optional[float] = Field(None, description="Reaction temperature (°C)")
    pressure_atm: Optional[float] = Field(None, description="Reaction pressure (atm)")
    stirring_rpm: Optional[float] = Field(None, description="Stirring speed (rpm)")

    source: Optional[str] = Field(None, description="Data source, e.g. 'ord'")
    dataset_id: Optional[str] = Field(None, description="ORD dataset identifier")
    dataset_name: Optional[str] = Field(None, description="Human-readable dataset name")
    doi: Optional[str] = Field(None, description="DOI of the source publication")
    doi_url: Optional[str] = Field(None, description="https://doi.org/{doi}")
    google_scholar_url: Optional[str] = Field(
        None, description="Google Scholar search URL: scholar.google.com/scholar?q=doi:{doi}"
    )
    publication_year: Optional[int] = Field(None, description="Publication year")

    notes_safety: Optional[str] = Field(None, description="Safety notes from ORD")
    notes_procedure: Optional[str] = Field(None, description="Experimental procedure text")

    step_score: float = Field(0.0, description="Step-level score from the retrosynthesis scorer")
class ORDRouteMetrics(BaseModel):
    num_steps: int = Field(..., description="Total number of synthesis steps")
    avg_yield: float = Field(..., description="Average step yield (%) across steps with yield data")
    avg_temp: float = Field(..., description="Average reaction temperature (°C) across steps with temp data")
    has_safety_concerns: bool = Field(..., description="True if any step has non-empty notes_safety")
    num_reactants: int = Field(..., description="Total reactant count across all steps")
    complete: bool = Field(..., description="True if all open molecules are resolved")
    yields_available: int = Field(0, description="Number of steps with yield data")
    temps_available: int = Field(0, description="Number of steps with temperature data")
class ORDRoute(BaseModel):
    source: str = Field("ORD", description="Always 'ORD' for database-backed routes")
    target_smiles: str = Field(..., description="Target molecule SMILES")
    score: float = Field(..., description="Cumulative route score (higher = better)")
    is_best: bool = Field(False, description="True for the highest-scoring route in the response")
    is_complete: bool = Field(False, description="True when open_molecules is empty")

    steps: List[ORDSynthesisStep] = Field(..., description="Ordered retrosynthetic steps (step 1 = last reaction)")
    open_molecules: List[str] = Field(
        default_factory=list,
        description="SMILES that still need a synthesis route (empty = fully resolved)"
    )
    metrics: ORDRouteMetrics = Field(..., description="Route quality metrics")
    max_depth_reached: int = Field(..., description="Maximum depth level reached in this route")

    selection_reasoning: Optional[Dict[str, Any]] = Field(
        None, description="Scoring breakdown used to select this as the best route"
    )
class ORDSearchStats(BaseModel):
    target_smiles: str
    max_depth: int
    beam_width: int
    per_node_limit: int
    top_k: int
    runtime_seconds: float
    nodes_explored: int
    reactions_queried: int
    routes_generated: int
    avg_reactions_per_node: float
class RouteConstraints(BaseModel):
    max_steps: Optional[int] = Field(None, description="Maximum number of synthesis steps", ge=1, le=20)
    target_yield: Optional[float] = Field(None, description="Target yield percentage", ge=0.0, le=100.0)
    max_molecular_weight: Optional[float] = Field(None, description="Maximum molecular weight in g/mol", gt=0)
    exclude_azides: bool = Field(False, description="Exclude routes using azide reagents")
    exclude_heavy_metals: bool = Field(False, description="Exclude routes using heavy metal catalysts")
    exclude_explosive_intermediates: bool = Field(False, description="Exclude routes with explosive intermediates")
class GetRoutesRequest(BaseModel):
    smiles: str = Field(..., description="SMILES string of the target molecule", min_length=1)
    mol_format: Optional[str] = Field(None, description="MOL format of the molecule (TBD)")
    inchi: Optional[str] = Field(None, description="InChI string of the molecule")
    constraints: Optional[RouteConstraints] = Field(None, description="Route generation constraints")

    max_depth: int = Field(
        4, ge=1, le=8,
        description="Maximum retrosynthetic depth (number of recursive reaction steps). "
                    "Depth 1 = direct precursors only; depth 4 (default) explores four levels deep."
    )
    beam_width: int = Field(
        25, ge=1, le=100,
        description="Beam width for beam-search: how many candidate routes to keep at each depth level."
    )
    per_node_limit: int = Field(
        200, ge=1, le=500,
        description="Maximum ORD reactions to retrieve per product SMILES node."
    )
    top_k: int = Field(
        5, ge=1, le=25,
        description="Number of top-ranked routes to return."
    )
    require_exactly_2_reactants: bool = Field(
        False,
        description="If True, only keep reaction steps that have exactly 2 reactants (bimolecular reactions)."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "max_depth": 4,
                "beam_width": 25,
                "per_node_limit": 200,
                "top_k": 5,
                "constraints": {
                    "max_steps": 5,
                    "target_yield": 75.0,
                    "max_molecular_weight": 500.0,
                    "exclude_azides": False,
                    "exclude_heavy_metals": True,
                    "exclude_explosive_intermediates": True
                }
            }
        }
    }
class SynthesisStep(BaseModel):
    step_number: int = Field(..., description="Step number in the synthesis sequence")
    description: str = Field(..., description="Description of the synthesis step")
    reagents: List[str] = Field(..., description="List of reagents used in this step")
    conditions: str = Field(..., description="Reaction conditions (temperature, solvent, time, etc.)")
    expected_yield: Optional[float] = Field(None, description="Expected yield for this step (%)", ge=0.0, le=100.0)
class SafetyAssessment(BaseModel):
    hazardous_reagents: List[str] = Field(..., description="List of hazardous reagents with hazard classification")
    hazardous_steps: List[str] = Field(..., description="Steps requiring special safety precautions")
    explosive_intermediates: List[str] = Field(..., description="Intermediates with explosive potential")
    banned_solvents: List[str] = Field(..., description="Solvents classified as banned or restricted (ICH Q3C)")
    ppe_requirements: List[str] = Field(..., description="Required personal protective equipment")
class RegulatoryCompliance(BaseModel):
    reach_compliant: bool = Field(..., description="REACH (EU chemicals regulation) compliance")
    ich_compliant: bool = Field(..., description="ICH guidelines compliance")
    notes: List[str] = Field(..., description="Regulatory compliance notes and flags")
class ToxicologyReport(BaseModel):
    acute_oral_toxicity: str = Field(..., description="Predicted acute oral toxicity classification (GHS)")
    skin_sensitization: str = Field(..., description="Skin sensitization prediction")
    mutagenicity: str = Field(..., description="Mutagenicity prediction (Ames test)")
    hepatotoxicity: str = Field(..., description="Hepatotoxicity prediction")
class EstimatedCycleTime(BaseModel):
    total_time: str = Field(..., description="Total estimated synthesis time (e.g., '12 hours', '3 days')")
    max_temperature: str = Field(..., description="Maximum temperature required (e.g., '120°C')")
    expected_yield: float = Field(..., description="Overall expected yield (%)", ge=0.0, le=100.0)
class Route(BaseModel):
    source: str = Field(..., description="Route origin: 'AI Generated' or 'Literature'")
    steps: List[SynthesisStep] = Field(..., description="Step-by-step synthesis procedure")
    reagents: List[str] = Field(..., description="Complete list of required reagents and chemicals")
    equipment: List[str] = Field(..., description="Required laboratory equipment")
    safety_assessment: SafetyAssessment = Field(..., description="Safety analysis of the route")
    regulatory_compliance: RegulatoryCompliance = Field(..., description="Regulatory compliance check")
    toxicology_report: ToxicologyReport = Field(..., description="Toxicology predictions")
    estimated_cycle_time: EstimatedCycleTime = Field(..., description="Time and yield estimates")
class GetRoutesResponse(BaseModel):
    routes: List[ORDRoute] = Field(
        default_factory=list,
        description="ORD database-backed retrosynthesis routes, ranked by score (best first). "
                    "Each route is a beam-search pathway through the retro_edges table."
    )
    molecule_smiles: str = Field(..., description="Input SMILES string (echoed back)")
    total_routes: int = Field(..., description="Total number of routes returned")
    search_stats: Optional[ORDSearchStats] = Field(
        None, description="Beam-search runtime statistics"
    )
    note: Optional[str] = Field(
        None,
        description="Informational message, e.g. when no ORD routes were found for this SMILES."
    )
