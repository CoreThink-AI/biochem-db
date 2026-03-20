# PubChem data models
from sqlalchemy import create_engine, Column, Integer, String, Float, Double
from sqlalchemy.orm import declarative_base


ORMBase = declarative_base()
class CompoundSMILES(ORMBase):
    __tablename__ = 'compound'  # Table name in the database
    id = Column(Integer, primary_key=True)
    smiles = Column(String)
    cid = Column(Integer)
    # preferred_iupac_name = Column(String)


class CompoundComplexity(ORMBase):
    """ psql table seems to have these columns 

    Verify types:
    ```python
    table,limit='compound_complexity',1
    with ENGINE.connect() as connection:
        table = list(
            connection.execute(
                text(
                    f'SELECT * '
                    + f' FROM {table}'
                    + f' WHERE true '
                    + f' LIMIT {limit}'
                    + ' ;'
                    )
                ).all()
            )
    types = [type(x) for x in table[0]]
    ```

    """
    __tablename__ = 'compound_complexity'  # Table name in the database
    id = Column(Integer, primary_key=True)
    cid = Column(Integer)
    name = Column(String)
    synonyms = Column(String)
    molecular_formula = Column(String)
    inchi = Column(String)
    smiles = Column(String)
    inchikey = Column(String)
    iupac_name = Column(String)
    mesh_headings = Column(String)
    annotation_content = Column(String)
    linked_bioassays = Column(String)
    data_source = Column(String)
    data_source_category = Column(String)
    tagged_by_pubchem = Column(String)
    molecular_weight = Column(Float)
    polar_area = Column(Float)
    complexity = Column(Integer)
    xlogp = Column(Float)
    heavy_atom_count = Column(Integer)
    h_bond_donor_count = Column(Integer)
    h_bond_acceptor_count = Column(Integer)
    rotatable_bond_count = Column(Integer)
    exact_mass = Column(String)
    monoisotopic_mass = Column(String)
    charge = Column(String)
    covalent_unit_count = Column(String)
    isotopic_atom_count = Column(String)
    total_atom_stereo_count = Column(String)
    defined_atom_stereo_count = Column(String)
    undefined_atom_stereo_count = Column(String)
    total_bond_stereo_count = Column(String)
    defined_bond_stereo_count = Column(String)
    undefined_bond_stereo_count = Column(String)
    linked_pubchem_literature_count = Column(String)
    linked_pubchem_patent_count = Column(String)
    linked_pubchem_patent_family_count = Column(String)
    annotation_type_count = Column(String)
    create_date = Column(String)