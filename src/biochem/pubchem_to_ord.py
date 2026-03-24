#!/usr/bin/env python3
"""
Parse PubChem Manufacturing data and create Open Reaction Database (ORD) records.

Note: CID 702 is Ethanol, not Ethanal (which is Acetaldehyde, CID 177)
"""

import json
import re
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import time


@dataclass
class ORDCompound:
    """Represents a compound in an ORD reaction."""
    name: str
    smiles: str
    pubchem_cid: Optional[int] = None
    role: str = "reactant"  # reactant, product, catalyst, solvent


@dataclass
class ORDReaction:
    """Simplified ORD reaction record."""
    reaction_id: str
    description: str
    reactants: List[ORDCompound]
    products: List[ORDCompound]
    catalysts: List[ORDCompound]
    conditions: Dict[str, str]
    reference: Optional[str] = None

    def to_dict(self):
        """Convert to dictionary format."""
        return {
            "reaction_id": self.reaction_id,
            "description": self.description,
            "reactants": [asdict(r) for r in self.reactants],
            "products": [asdict(p) for p in self.products],
            "catalysts": [asdict(c) for c in self.catalysts],
            "conditions": self.conditions,
            "reference": self.reference
        }


class PubChemORDConverter:
    """Convert PubChem manufacturing data to ORD records."""

    def __init__(self, json_file_path: str):
        """Initialize with path to PubChem JSON file."""
        with open(json_file_path, 'r') as f:
            self.data = json.load(f)

        # Cache for SMILES lookups
        self.smiles_cache = {}

        # Extract product info from the main record
        self.product_cid = self.data['Record']['RecordNumber']
        self.product_name = self.data['Record']['RecordTitle']
        self.product_smiles = self._extract_product_smiles()

    def _extract_product_smiles(self) -> str:
        """Extract SMILES for the main product from the JSON."""
        sections = self.data['Record']['Section']

        for section in sections:
            if section.get('TOCHeading') == 'Names and Identifiers':
                if 'Section' in section:
                    for subsection in section['Section']:
                        if subsection.get('TOCHeading') == 'Computed Descriptors':
                            if 'Section' in subsection:
                                for desc_section in subsection['Section']:
                                    if desc_section.get('TOCHeading') == 'SMILES':
                                        if 'Information' in desc_section:
                                            for info in desc_section['Information']:
                                                if 'Value' in info and 'StringWithMarkup' in info['Value']:
                                                    return info['Value']['StringWithMarkup'][0]['String']
        return ""

    def get_smiles_from_pubchem(self, compound_name: str = None, cid: int = None) -> Optional[str]:
        """
        Fetch SMILES from PubChem API by name or CID.

        Args:
            compound_name: Name of the compound
            cid: PubChem CID

        Returns:
            SMILES string or None
        """
        # Check cache first
        cache_key = f"{compound_name}_{cid}"
        if cache_key in self.smiles_cache:
            return self.smiles_cache[cache_key]

        try:
            time.sleep(0.2)  # Rate limiting

            if cid:
                url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/IsomericSMILES/JSON"
            elif compound_name:
                url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/property/IsomericSMILES/JSON"
            else:
                return None

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            smiles = data['PropertyTable']['Properties'][0]['SMILES']

            # Cache the result
            self.smiles_cache[cache_key] = smiles
            return smiles

        except Exception as e:
            print(f"Error fetching SMILES for {compound_name or cid}: {e}")
            return None

    def extract_manufacturing_section(self) -> List[Dict]:
        """Extract the Manufacturing section from PubChem JSON."""
        sections = self.data['Record']['Section']

        for section in sections:
            if section.get('TOCHeading') == 'Use and Manufacturing':
                if 'Section' in section:
                    for subsection in section['Section']:
                        if subsection.get('TOCHeading') == 'Methods of Manufacturing':
                            return subsection.get('Information', [])
        return []

    def extract_compounds_from_markup(self, markup_data: Dict) -> List[Tuple[str, Optional[int]]]:
        """
        Extract compound names and CIDs from PubChem markup.

        Returns:
            List of (compound_name, cid) tuples
        """
        compounds = []

        if 'Markup' in markup_data:
            text = markup_data['String']
            for markup in markup_data['Markup']:
                if markup.get('Type') == 'PubChem Internal Link':
                    start = markup['Start']
                    length = markup['Length']
                    compound_name = text[start:start+length]

                    # Extract CID from Extra field (e.g., "CID-702")
                    cid = None
                    extra = markup.get('Extra', '')
                    cid_match = re.search(r'CID-(\d+)', extra)
                    if cid_match:
                        cid = int(cid_match.group(1))

                    compounds.append((compound_name, cid))

        return compounds

    def parse_reaction_from_text(self, text: str, markup_data: Dict, reference: str = None) -> List[ORDReaction]:
        """
        Parse chemical reactions from manufacturing text.

        Args:
            text: Manufacturing method description
            markup_data: Markup data with compound links
            reference: Citation reference

        Returns:
            List of ORDReaction objects
        """
        reactions = []

        # Extract all compounds mentioned
        compounds = self.extract_compounds_from_markup(markup_data)

        # Pattern 1: Direct hydration of ethylene
        # Ethylene + Water -> Ethanol
        if 'direct catalytic hydration of ethylene' in text.lower():
            reactants = []
            products = []
            catalysts = []

            # Find ethylene and water as reactants
            for name, cid in compounds:
                if name.lower() in ['ethylene']:
                    smiles = self.get_smiles_from_pubchem(cid=cid)
                    if smiles:
                        reactants.append(ORDCompound(name, smiles, cid, "reactant"))
                elif name.lower() in ['water']:
                    smiles = self.get_smiles_from_pubchem(cid=cid)
                    if smiles:
                        reactants.append(ORDCompound(name, smiles, cid, "reactant"))
                elif name.lower() in ['phosphoric acid']:
                    smiles = self.get_smiles_from_pubchem(cid=cid)
                    if smiles:
                        catalysts.append(ORDCompound(name, smiles, cid, "catalyst"))

            # Product is ethanol
            products.append(ORDCompound(
                self.product_name,
                self.product_smiles,
                self.product_cid,
                "product"
            ))

            # Extract conditions
            conditions = {}
            temp_match = re.search(r'(\d+)\s*-\s*(\d+)\s*°C', text)
            if temp_match:
                conditions['temperature'] = f"{temp_match.group(1)}-{temp_match.group(2)} °C"

            pressure_match = re.search(r'(\d+)\s*-\s*(\d+)\s*MPa', text)
            if pressure_match:
                conditions['pressure'] = f"{pressure_match.group(1)}-{pressure_match.group(2)} MPa"

            if 'catalyst' in text.lower():
                conditions['catalyst_type'] = 'phosphoric acid on support'

            reaction = ORDReaction(
                reaction_id=f"ethanol_synthesis_direct_hydration",
                description="Direct catalytic hydration of ethylene to ethanol",
                reactants=reactants,
                products=products,
                catalysts=catalysts,
                conditions=conditions,
                reference=reference
            )
            reactions.append(reaction)

        # Pattern 2: Indirect hydration via ethyl sulfate
        # Ethylene + H2SO4 -> Ethyl sulfate -> Ethanol
        elif 'indirect hydration of ethylene' in text.lower() or 'sulfuric acid' in text.lower():
            reactants = []
            products = []
            catalysts = []

            # Find reactants
            for name, cid in compounds:
                if name.lower() in ['ethylene']:
                    smiles = self.get_smiles_from_pubchem(cid=cid)
                    if smiles:
                        reactants.append(ORDCompound(name, smiles, cid, "reactant"))
                elif name.lower() in ['water']:
                    smiles = self.get_smiles_from_pubchem(cid=cid)
                    if smiles:
                        reactants.append(ORDCompound(name, smiles, cid, "reactant"))
                elif name.lower() in ['sulfuric acid']:
                    smiles = self.get_smiles_from_pubchem(cid=cid)
                    if smiles:
                        reactants.append(ORDCompound(name, smiles, cid, "reactant"))

            # Product is ethanol
            products.append(ORDCompound(
                self.product_name,
                self.product_smiles,
                self.product_cid,
                "product"
            ))

            # Extract conditions
            conditions = {}
            temp_match = re.search(r'(\d+)\s*-?\s*(\d+)?\s*°C', text)
            if temp_match:
                if temp_match.group(2):
                    conditions['temperature'] = f"{temp_match.group(1)}-{temp_match.group(2)} °C"
                else:
                    conditions['temperature'] = f"{temp_match.group(1)} °C"

            pressure_match = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*MPa', text)
            if pressure_match:
                conditions['pressure'] = f"{pressure_match.group(1)}-{pressure_match.group(2)} MPa"

            conditions['method'] = 'indirect hydration via ethyl sulfate intermediate'

            reaction = ORDReaction(
                reaction_id=f"ethanol_synthesis_indirect_hydration",
                description="Indirect hydration of ethylene via ethyl sulfate to ethanol",
                reactants=reactants,
                products=products,
                catalysts=catalysts,
                conditions=conditions,
                reference=reference
            )
            reactions.append(reaction)

        # Pattern 3: Oxidation of methane
        elif 'oxidation of methane' in text.lower():
            reactants = []
            products = []

            for name, cid in compounds:
                if name.lower() == 'methane':
                    smiles = self.get_smiles_from_pubchem(cid=cid)
                    if smiles:
                        reactants.append(ORDCompound(name, smiles, cid, "reactant"))

            # Add oxygen as reactant (not in markup but implied)
            oxygen_smiles = self.get_smiles_from_pubchem(compound_name='oxygen')
            if oxygen_smiles:
                reactants.append(ORDCompound('oxygen', oxygen_smiles, 977, "reactant"))

            products.append(ORDCompound(
                self.product_name,
                self.product_smiles,
                self.product_cid,
                "product"
            ))

            reaction = ORDReaction(
                reaction_id=f"ethanol_synthesis_methane_oxidation",
                description="Oxidation of methane to ethanol",
                reactants=reactants,
                products=products,
                catalysts=[],
                conditions={'method': 'oxidation'},
                reference=reference
            )
            reactions.append(reaction)

        return reactions

    def analyze_manufacturing_and_create_ord(self) -> List[ORDReaction]:
        """
        Main function to analyze manufacturing data and create ORD records.

        Returns:
            List of ORDReaction objects
        """
        manufacturing_info = self.extract_manufacturing_section()

        all_reactions = []

        for info in manufacturing_info:
            # Get the text and reference
            if 'Value' not in info or 'StringWithMarkup' not in info['Value']:
                continue

            markup_data = info['Value']['StringWithMarkup'][0]
            text = markup_data['String']

            # Get reference
            reference = None
            if 'Reference' in info and info['Reference']:
                reference = info['Reference'][0]

            # Parse reactions from this text
            reactions = self.parse_reaction_from_text(text, markup_data, reference)
            all_reactions.extend(reactions)

        return all_reactions

    def save_ord_records(self, reactions: List[ORDReaction], output_file: str):
        """Save ORD records to a JSON file."""
        ord_data = {
            "metadata": {
                "source": "PubChem",
                "product_cid": self.product_cid,
                "product_name": self.product_name,
                "product_smiles": self.product_smiles,
                "total_reactions": len(reactions)
            },
            "reactions": [r.to_dict() for r in reactions]
        }

        with open(output_file, 'w') as f:
            json.dump(ord_data, f, indent=2)

        print(f"Saved {len(reactions)} ORD reactions to {output_file}")


def main():
    """Example usage."""
    # Path to the PubChem JSON file
    json_file = "ethanal_702.json"

    # Create converter
    converter = PubChemORDConverter(json_file)

    print(f"Product: {converter.product_name} (CID {converter.product_cid})")
    print(f"Product SMILES: {converter.product_smiles}")
    print()

    # Analyze manufacturing data and create ORD records
    print("Analyzing manufacturing methods...")
    reactions = converter.analyze_manufacturing_and_create_ord()

    print(f"\nFound {len(reactions)} reactions:")
    for i, reaction in enumerate(reactions, 1):
        print(f"\n{i}. {reaction.description}")
        print(f"   Reaction ID: {reaction.reaction_id}")
        print(f"   Reactants:")
        for r in reaction.reactants:
            print(f"     - {r.name}: {r.smiles} (CID {r.pubchem_cid})")
        print(f"   Products:")
        for p in reaction.products:
            print(f"     - {p.name}: {p.smiles} (CID {p.pubchem_cid})")
        if reaction.catalysts:
            print(f"   Catalysts:")
            for c in reaction.catalysts:
                print(f"     - {c.name}: {c.smiles} (CID {c.pubchem_cid})")
        if reaction.conditions:
            print(f"   Conditions: {reaction.conditions}")
        if reaction.reference:
            print(f"   Reference: {reaction.reference}")

    # Save to file
    output_file = "ord_reactions.json"
    converter.save_ord_records(reactions, output_file)

    print(f"\n✓ ORD records saved to {output_file}")


if __name__ == "__main__":
    main()
