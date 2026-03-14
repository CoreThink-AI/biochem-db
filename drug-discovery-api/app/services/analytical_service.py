## DUMMY
from typing import List

from app.models.route_models import Route
from app.models.analytical_models import AnalyticalMethod


def _parse_method(method_data: dict) -> AnalyticalMethod:
    return AnalyticalMethod(
        name=method_data.get("name", "Unknown"),
        technique=method_data.get("technique", ""),
        purpose=method_data.get("purpose", ""),
        analyte=method_data.get("analyte"),
        conditions=method_data.get("conditions"),
        acceptance_criteria=method_data.get("acceptance_criteria"),
        reference_standards=method_data.get("reference_standards"),
        sample_preparation=method_data.get("sample_preparation"),
        expected_results=method_data.get("expected_results"),
        regulatory_guidance=method_data.get("regulatory_guidance"),
    )


def _get_dummy_analytical_methods() -> List[dict]:
    """Return dummy analytical methods for demonstration purposes."""
    return [
        {
            "name": "HPLC Purity Assay",
            "technique": "RP-HPLC-UV",
            "purpose": "Determine assay and related substances of the target molecule",
            "analyte": "Target API",
            "conditions": "C18 column, 0.1% TFA in water/acetonitrile gradient, 1.0 mL/min, 25°C, 210 nm",
            "acceptance_criteria": "Purity ≥ 99.0% by area normalization",
            "reference_standards": ["Primary reference standard", "Working standard"],
            "sample_preparation": "Dissolve sample in mobile phase, filter through 0.45 μm filter",
            "expected_results": "Single main peak with retention time ~5.2 minutes",
            "regulatory_guidance": "ICH Q2(R1), USP <621>"
        },
        {
            "name": "Identity Confirmation",
            "technique": "1H-NMR 400 MHz",
            "purpose": "Confirm molecular structure and identity",
            "analyte": "Target API",
            "conditions": "400 MHz, CDCl3 solvent, 25°C, 64 scans",
            "acceptance_criteria": "Spectral match with reference standard",
            "reference_standards": ["Reference standard for NMR"],
            "sample_preparation": "Dissolve 10 mg in 0.7 mL CDCl3",
            "expected_results": "Chemical shifts and coupling patterns matching reference",
            "regulatory_guidance": "ICH Q6B"
        },
        {
            "name": "Residual Solvents",
            "technique": "GC-HS",
            "purpose": "Quantify residual solvents per ICH Q3C",
            "analyte": "Residual solvents",
            "conditions": "Headspace GC, DB-624 column, temperature program 40-200°C",
            "acceptance_criteria": "Below ICH Q3C limits",
            "reference_standards": ["Solvent standards"],
            "sample_preparation": "Direct headspace analysis",
            "expected_results": "Solvent peaks within quantification range",
            "regulatory_guidance": "ICH Q3C"
        },
        {
            "name": "Water Content",
            "technique": "Karl Fischer Titration",
            "purpose": "Determine water content",
            "analyte": "Water",
            "conditions": "Coulometric KF titration, methanol solvent",
            "acceptance_criteria": "Water content ≤ 0.5% w/w",
            "reference_standards": ["KF reagent"],
            "sample_preparation": "Direct injection of dissolved sample",
            "expected_results": "KF titration endpoint reached",
            "regulatory_guidance": "USP <467>"
        }
    ]


async def get_analytical_methods(route: Route) -> tuple[List[AnalyticalMethod], str | None]:
    """
    Generate dummy analytical method recommendations for the given synthesis route.
    Returns (methods, notes).
    """
    # Get dummy methods
    dummy_methods = _get_dummy_analytical_methods()
    methods = [_parse_method(m) for m in dummy_methods]
    notes = "Dummy analytical methods generated for demonstration purposes. AI-powered recommendations have been disabled."
    
    return methods, notes
