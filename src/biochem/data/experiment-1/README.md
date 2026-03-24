# Example prompts CID 10297

CC(C(C1=CC=CC=C1)O)N -> Phenylethanolamine

```python
>>> report['response']['prompts'][0]
```
```text
Identify the common name of this chemical compound from its SMILES structure.

SMILES: CC(C(C1=CC=CC=C1)O)N

Return ONLY the most common/standard name (e.g., "Aspirin", "Ibuprofen", "Paracetamol").
If it's not a well-known drug, return a descriptive chemical name.
```

```python
>>> report['response']['prompts'][1]
```
```text
Identify the common name of this chemical compound from its SMILES structure.

SMILES: CC(C(C1=CC=CC=C1)O)N

Return ONLY the most common/standard name (e.g., "Aspirin", "Ibuprofen", "Paracetamol").
If it's not a well-known drug, return a descriptive chemical name.
```

```python
>>> report['response']['prompts'][2]
```
```text
Analyze the chemical compound and provide comprehensive pharmaceutical data:

Compound: 1-Phenylethanolamine
SMILES: CC(C(C1=CC=CC=C1)O)N

Generate detailed analysis including all required fields:
- Chemical structure data (InChI, molecular weight, formula)
- Drug classification and target properties  
- Regulatory information
- Physical properties (melting point, boiling point, solubility)
- Pharmacokinetic parameters
- Safety profile
- All other required pharmaceutical properties

Ensure ALL fields are provided with realistic values.
```

```python
>>> report['response']['prompts'][3]
```
```text
Analyze the chemical compound and provide comprehensive pharmaceutical data:

Compound: 1-Phenylethanolamine
SMILES: CC(C(C1=CC=CC=C1)O)N



Generate detailed analysis including all required fields:
- Chemical structure data (InChI, molecular weight, formula)
- Drug classification and target properties  
- Regulatory information
- Physical properties (melting point, boiling point, solubility)
- Pharmacokinetic parameters
- Safety profile
- All other required pharmaceutical properties

Ensure ALL fields are provided with realistic values.
```

```python
>>> report['response']['prompts'][4]
```
```text
Generate comprehensive workflow data for pharmaceutical synthesis:

Compound: 1-Phenylethanolamine
Synthesis Routes: Route 1: Asymmetric reduction of acetophenone followed by nitrene C–H amination

Context from previous data: {'compound_name': '1-Phenylethanolamine', 'molecular_properties': {'name': '1-Phenylethanolamine', 'formula': 'C8H11NO', 'weight': 137.18, 'drug_class': 'Adrenergic agent scaffold (beta-phenylethanolamine derivative); not an approved drug substance on its own'}, 'existing_routes': [{'name': 'Asymmetric reduction of acetophenone followed by nitrene C–H amination', 'steps': 7, 'building_blocks': 8}]}


Provide complete workflow data with ALL required fields:
1. Route evaluation with scores and comparison metrics
2. Experimental planning with reagents, equipment, safety protocols
3. Process optimization with parameters and results
4. Tech transfer with documents, analytical methods, scale-up factors

Ensure every field is populated with realistic pharmaceutical industry data.
All analytical methods must include: name, wavelength, runtime, status, method.
```

```python
>>> report['response']['prompts'][5]
```
```text
Generate comprehensive workflow data for pharmaceutical synthesis:

Compound: 1-Phenylethanolamine
Synthesis Routes: Route 1: Asymmetric reduction of acetophenone followed by nitrene C–H amination

Context from previous data: {'compound_name': '1-Phenylethanolamine', 'molecular_properties': {'name': '1-Phenylethanolamine', 'formula': 'C8H11NO', 'weight': 137.18, 'drug_class': 'Adrenergic agent scaffold (beta-phenylethanolamine derivative); not an approved drug substance on its own'}, 'existing_routes': [{'name': 'Asymmetric reduction of acetophenone followed by nitrene C–H amination', 'steps': 7, 'building_blocks': 8}]}


Provide complete workflow data with ALL required fields:
1. Route evaluation with scores and comparison metrics
2. Experimental planning with reagents, equipment, safety protocols
3. Process optimization with parameters and results
4. Tech transfer with documents, analytical methods, scale-up factors

Ensure every field is populated with realistic pharmaceutical industry data.
All analytical methods must include: name, wavelength, runtime, status, method.
```

```python
>>> report['response']['prompts'][6]
```
```text
Enhance synthesis routes with comprehensive industrial parameters:

Compound: 1-Phenylethanolamine
Routes to enhance: [{'name': 'Asymmetric reduction of acetophenone followed by nitrene C–H amination', 'steps': 7, 'building_blocks': 8}]

Context data: {'compound_name': '1-Phenylethanolamine', 'molecular_properties': {'name': '1-Phenylethanolamine', 'formula': 'C8H11NO', 'weight': 137.18, 'drug_class': 'Adrenergic agent scaffold (beta-phenylethanolamine derivative); not an approved drug substance on its own'}, 'existing_routes': [{'name': 'Asymmetric reduction of acetophenone followed by nitrene C–H amination', 'steps': 7, 'building_blocks': 8}]}


For each route, provide ALL required fields including:
- Detailed reaction conditions (temperature, pressure, pH ranges)
- Comprehensive scoring (safety, green chemistry, cost, scalability)
- Process parameters (stirring, monitoring, control points)
- Risk assessment and advantages
- Equipment requirements and timing
- Complete route classification and confidence levels

Generate realistic industrial synthesis parameters for pharmaceutical manufacturing.
```

```python
>>> report['response']['prompts'][7]
```
```text
Enhance synthesis routes with comprehensive industrial parameters:

Compound: 1-Phenylethanolamine
Routes to enhance: [{'name': 'Asymmetric reduction of acetophenone followed by nitrene C–H amination', 'steps': 7, 'building_blocks': 8}]

Context data: {'compound_name': '1-Phenylethanolamine', 'molecular_properties': {'name': '1-Phenylethanolamine', 'formula': 'C8H11NO', 'weight': 137.18, 'drug_class': 'Adrenergic agent scaffold (beta-phenylethanolamine derivative); not an approved drug substance on its own'}, 'existing_routes': [{'name': 'Asymmetric reduction of acetophenone followed by nitrene C–H amination', 'steps': 7, 'building_blocks': 8}]}


For each route, provide ALL required fields including:
- Detailed reaction conditions (temperature, pressure, pH ranges)
- Comprehensive scoring (safety, green chemistry, cost, scalability)
- Process parameters (stirring, monitoring, control points)
- Risk assessment and advantages
- Equipment requirements and timing
- Complete route classification and confidence levels

Generate realistic industrial synthesis parameters for pharmaceutical manufacturing.
```
