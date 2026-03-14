## DUMMY
import json
import re
from typing import Any
from app.config import get_settings

settings = get_settings()

_client: Any | None = None


def get_ai_client() -> Any:
    global _client
    if _client is None:
        _client = None
    return _client


def _get_mock_response() -> dict:
    return {
        "routes": [
            {
                "source": "Mock AI Generated (Local Mode)",
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Acetylation of salicylic acid with acetic anhydride",
                        "reagents": ["Salicylic acid (1.0 eq)", "Acetic anhydride (1.2 eq)", "H3PO4 (cat.)"],
                        "conditions": "Temperature: 85°C, Time: 20 min, neat",
                        "expected_yield": 92.0
                    },
                    {
                        "step_number": 2,
                        "description": "Purification by recrystallization from ethanol",
                        "reagents": ["Ethanol (recrystallization solvent)"],
                        "conditions": "Temperature: 25°C, Time: 2 h, ambient pressure",
                        "expected_yield": 95.0
                    }
                ],
                "reagents": ["Salicylic acid", "Acetic anhydride", "Phosphoric acid", "Ethanol"],
                "equipment": [
                    "250 mL round-bottom flask",
                    "Reflux condenser", 
                    "Rotary evaporator",
                    "Ice bath",
                    "Vacuum filtration setup"
                ],
                "safety_assessment": {
                    "hazardous_reagents": ["Acetic anhydride — GHS05 Corrosive, GHS02 Flammable"],
                    "hazardous_steps": ["Step 1: Exothermic — control addition rate"],
                    "explosive_intermediates": [],
                    "banned_solvents": [],
                    "ppe_requirements": ["Chemical-resistant gloves", "Safety goggles", "Lab coat", "Fume hood"]
                },
                "regulatory_compliance": {
                    "reach_compliant": True,
                    "ich_compliant": True,
                    "notes": ["No SVHC substances. ICH Q3C Class 3 solvents only."]
                },
                "toxicology_report": {
                    "acute_oral_toxicity": "Category 5 — low hazard, LD50 > 2000 mg/kg",
                    "skin_sensitization": "Low sensitization risk",
                    "mutagenicity": "Negative — no Ames-positive structural alerts",
                    "hepatotoxicity": "Low hepatotoxicity concern"
                },
                "estimated_cycle_time": {
                    "total_time": "4 hours",
                    "max_temperature": "85°C",
                    "expected_yield": 85.0
                }
            }
        ]
    }


def _get_mock_document() -> str:
    return """# Process Chemistry Development Report

    ## Executive Summary
    This document outlines the process development for the synthesis of the target compound (Mock Data - Local Mode).

    ## Chemistry Overview
    - **Target Compound:** Aspirin (Acetylsalicylic acid)
    - **Molecular Weight:** 180.16 g/mol
    - **Formula:** C9H8O4

    ## Process Description
    The synthesis involves a two-step process:
    1. Acetylation of salicylic acid
    2. Purification by recrystallization

    ## Safety Considerations
    - Handle acetic anhydride in a fume hood
    - Use appropriate PPE
    - Control exotherm during acetylation

    ## Quality Control
    - Purity by HPLC: ≥99.0%
    - Melting point: 135-136°C
    - Assay: 99.5-100.5%

    *Note: This is mock data generated in local mode without API connection.*"""

def _get_mock_analytical_methods() -> list:
    return [
        {
            "name": "HPLC Purity Assay",
            "technique": "RP-HPLC-UV",
            "purpose": "Quantitative purity determination of the final API",
            "analyte": "Active pharmaceutical ingredient",
            "conditions": "Column: C18 (150x4.6mm, 5um); Mobile phase A: 0.1% TFA in H2O; B: MeCN; Gradient: 5->95% B over 15 min; Flow: 1.0 mL/min; UV: 254 nm",
            "acceptance_criteria": "Purity >= 99.0% (area normalization)",
            "reference_standards": ["USP Reference Standard"],
            "sample_preparation": "Dissolve 10 mg in 10 mL MeCN:H2O (50:50)",
            "expected_results": "Single peak at ~8.5 min",
            "regulatory_guidance": "ICH Q2(R1)"
        },
        {
            "name": "NMR Identification",
            "technique": "1H NMR",
            "purpose": "Structural confirmation",
            "analyte": "Active pharmaceutical ingredient",
            "conditions": "400 MHz, CDCl3, 25°C",
            "acceptance_criteria": "All chemical shifts within ±0.05 ppm of reference",
            "reference_standards": ["Authentic reference material"],
            "sample_preparation": "Dissolve 10 mg in 0.7 mL CDCl3",
            "expected_results": "Characteristic signals matching structure",
            "regulatory_guidance": "ICH Q2(R1)"
        }
    ]

def _extract_json(text: str) -> Any:
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        return json.loads(json_match.group(1))
    text = text.strip()
    return json.loads(text)


async def call_ai_for_json(
    prompt: str,
    system: str | None = None,
    max_retries: int = 2,
) -> Any:
    return _get_mock_response()


async def call_ai_for_text(
    prompt: str,
    system: str | None = None,
) -> str:
    return _get_mock_document()
