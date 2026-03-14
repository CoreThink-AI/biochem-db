## Table of Contents

- [Endpoints](#endpoints)
- [Local Development](#local-development)
- [Docker](#docker)
- [Google Cloud Run Deployment](#google-cloud-run-deployment)
- [Swagger / UI Testing](#swagger--ui-testing)
- [Project Structure](#project-structure)

---

# Drug Discovery API

FastAPI service for synthesis route generation and pharmaceutical document automation.

## Endpoints

### `POST /get-routes`

Generate synthesis routes for a target molecule.

**Request**

```json
{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "mol_format": null,
  "inchi": null,
  "constraints": {
    "max_steps": 5,
    "target_yield": 70.0,
    "max_molecular_weight": 500.0,
    "exclude_azides": false,
    "exclude_heavy_metals": true,
    "exclude_explosive_intermediates": true
  }
}
```

| Field                                           | Type   | Required | Description                              |
| ----------------------------------------------- | ------ | -------- | ---------------------------------------- |
| `smiles`                                      | string | ✅       | SMILES string of target molecule         |
| `mol_format`                                  | string | —       | MOL format (TBD)                         |
| `inchi`                                       | string | —       | InChI string                             |
| `constraints.max_steps`                       | int    | —       | Max synthesis steps (1–20)              |
| `constraints.target_yield`                    | float  | —       | Target overall yield %                   |
| `constraints.max_molecular_weight`            | float  | —       | Max intermediate MW (g/mol)              |
| `constraints.exclude_azides`                  | bool   | —       | Exclude azide reagents                   |
| `constraints.exclude_heavy_metals`            | bool   | —       | Exclude Pd/Pt/Rh catalysts               |
| `constraints.exclude_explosive_intermediates` | bool   | —       | Exclude peroxides, diazonium salts, etc. |

**Response**

```json
{
  "routes": [
    {
      "source": "AI Generated",
      "steps": [
        {
          "step_number": 1,
          "description": "Acetylation of salicylic acid with acetic anhydride",
          "reagents": ["Salicylic acid (1.0 eq)", "Acetic anhydride (1.2 eq)", "H3PO4 (cat.)"],
          "conditions": "Temperature: 85°C, Time: 20 min, neat",
          "expected_yield": 92.0
        }
      ],
      "reagents": ["Salicylic acid", "Acetic anhydride", "Phosphoric acid"],
      "equipment": ["250 mL round-bottom flask", "Reflux condenser", "Rotary evaporator"],
      "safety_assessment": {
        "hazardous_reagents": ["Acetic anhydride — GHS05 Corrosive, GHS02 Flammable"],
        "hazardous_steps": ["Step 1: Exothermic — control addition rate"],
        "explosive_intermediates": [],
        "banned_solvents": [],
        "ppe_requirements": ["Chemical-resistant gloves", "Safety goggles", "Lab coat"]
      },
      "regulatory_compliance": {
        "reach_compliant": true,
        "ich_compliant": true,
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
  ],
  "molecule_smiles": "CC(=O)Oc1ccccc1C(=O)O",
  "total_routes": 2
}
```

---

### `POST /search-molecules`

Autocomplete / typeahead search for molecules by name or SMILES prefix.

**Request**

```json
{
  "query": "aspirin",
  "limit": 10
}
```

| Field     | Type   | Required | Description                         |
| --------- | ------ | -------- | ----------------------------------- |
| `query` | string | ✅       | Name prefix or SMILES prefix        |
| `limit` | int    | —       | Max results (default: 20, max: 100) |

**Response**

```json
{
  "molecules": [
    {
      "name": "Aspirin",
      "smiles": "CC(=O)Oc1ccccc1C(=O)O",
      "inchi": "InChI=1S/C9H8O4/...",
      "molecular_weight": 180.16,
      "formula": "C9H8O4",
      "synonyms": ["Acetylsalicylic acid", "Aspro", "ASA"]
    }
  ],
  "query": "aspirin",
  "total": 1
}
```

---

### `POST /generate-documents`

Generate GMP-compliant pharmaceutical documents from a synthesis route.

**Request**

```json
{
  "route": { "...route object from /get-routes..." },
  "types": [
    "process_chemistry",
    "batch_manufacturing",
    "tech_transfer",
    "analytical_method",
    "safety_ghs_labels",
    "safety_process_summary",
    "safety_emergency_response",
    "safety_waste_disposal"
  ]
}
```

| Document Type                 | Description                                              |
| ----------------------------- | -------------------------------------------------------- |
| `process_chemistry`         | Process Chemistry Development Report                     |
| `batch_manufacturing`       | GMP Batch Manufacturing Record (BMR) with operator steps |
| `tech_transfer`             | Technology Transfer Package with CPP/CQA tables and FMEA |
| `analytical_method`         | Analytical Methods with full instrument conditions       |
| `safety_ghs_labels`         | GHS safety labels for all reagents                       |
| `safety_process_summary`    | SDS — Process safety summary                            |
| `safety_emergency_response` | SDS — Emergency response procedures                     |
| `safety_waste_disposal`     | SDS — Waste disposal guidelines                         |

**Response**

```json
{
  "documents": [
    {
      "type": "process_chemistry",
      "title": "Process Chemistry Development Report",
      "content": "## Executive Summary\n\n...",
      "sections": ["Executive Summary", "Chemistry Overview", "..."]
    }
  ],
  "total": 1
}
```

---

### `POST /get-analytical-methods`

Recommend ICH-compliant analytical methods for the synthesis route.

**Request**

```json
{
  "route": { "...route object from /get-routes..." }
}
```

**Response**

```json
{
  "methods": [
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
    }
  ],
  "total": 8,
  "notes": "Prioritise identity and purity methods for initial characterisation..."
}
```

### Setup

```bash
cd drug-discovery-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

The API is now available at:

- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc
- **Health check:** http://localhost:8080/health
