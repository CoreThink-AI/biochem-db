import duckdb
from pathlib import Path
from typing import Generator
from app.config import get_settings

# Seed dataset of common pharmaceutical molecules
SEED_MOLECULES = [
    {"name": "Aspirin", "smiles": "CC(=O)Oc1ccccc1C(=O)O", "inchi": "InChI=1S/C9H8O4/c1-6(10)13-8-5-3-2-4-7(8)9(11)12/h2-5H,1H3,(H,11,12)", "molecular_weight": 180.16, "formula": "C9H8O4", "synonyms": ["Acetylsalicylic acid", "Aspro", "ASA"]},
    {"name": "Ibuprofen", "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O", "inchi": "InChI=1S/C13H18O2/c1-9(2)8-11-4-6-12(7-5-11)10(3)13(14)15/h4-7,9-10H,8H2,1-3H3,(H,14,15)", "molecular_weight": 206.29, "formula": "C13H18O2", "synonyms": ["Brufen", "Advil", "Nurofen"]},
    {"name": "Paracetamol", "smiles": "CC(=O)Nc1ccc(O)cc1", "inchi": "InChI=1S/C8H9NO2/c1-6(10)9-7-2-4-8(11)5-3-7/h2-5,11H,1H3,(H,9,10)", "molecular_weight": 151.16, "formula": "C8H9NO2", "synonyms": ["Acetaminophen", "Tylenol", "Panadol"]},
    {"name": "Caffeine", "smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C", "inchi": "InChI=1S/C8H10N4O2/c1-10-4-9-6-5(10)7(13)12(3)8(14)11(6)2/h4H,1-3H3", "molecular_weight": 194.19, "formula": "C8H10N4O2", "synonyms": ["1,3,7-Trimethylxanthine", "Guaranine"]},
    {"name": "Metformin", "smiles": "CN(C)C(=N)NC(=N)N", "inchi": "InChI=1S/C4H11N5/c1-9(2)4(7)8-3(5)6/h1-2H3,(H4,5,6,7,8)", "molecular_weight": 129.16, "formula": "C4H11N5", "synonyms": ["Glucophage", "Fortamet"]},
    {"name": "Atorvastatin", "smiles": "CC(C)c1n(CC[C@@H](O)C[C@@H](O)CC(=O)O)c(C(=O)Nc2ccccc2F)c(-c2ccc(F)cc2)c1-c1ccc(F)cc1", "inchi": None, "molecular_weight": 558.64, "formula": "C33H35FN2O5", "synonyms": ["Lipitor"]},
    {"name": "Omeprazole", "smiles": "CC1=CN=C(C(=C1OC)C)CS(=O)c1nc2ccc(OC)cc2[nH]1", "inchi": None, "molecular_weight": 345.42, "formula": "C17H19N3O3S", "synonyms": ["Prilosec", "Losec"]},
    {"name": "Amoxicillin", "smiles": "CC1(C)S[C@@H]2[C@H](NC(=O)[C@@H](N)c3ccc(O)cc3)C(=O)N2[C@H]1C(=O)O", "inchi": None, "molecular_weight": 365.40, "formula": "C16H19N3O5S", "synonyms": ["Amoxil", "Trimox"]},
    {"name": "Warfarin", "smiles": "CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O", "inchi": None, "molecular_weight": 308.33, "formula": "C19H16O4", "synonyms": ["Coumadin", "Jantoven"]},
    {"name": "Fluoxetine", "smiles": "CNCCC(c1ccccc1)Oc1ccc(cc1)C(F)(F)F", "inchi": None, "molecular_weight": 309.33, "formula": "C17H18F3NO", "synonyms": ["Prozac", "Sarafem"]},
    {"name": "Sertraline", "smiles": "CNC1CCC(c2ccc(Cl)c(Cl)c2)c2ccccc21", "inchi": None, "molecular_weight": 306.23, "formula": "C17H17Cl2N", "synonyms": ["Zoloft"]},
    {"name": "Diazepam", "smiles": "CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21", "inchi": None, "molecular_weight": 284.74, "formula": "C16H13ClN2O", "synonyms": ["Valium"]},
    {"name": "Alprazolam", "smiles": "Cc1nnc2n1-c1ccc(Cl)cc1C(=O)N=C2c1ccccc1", "inchi": None, "molecular_weight": 308.77, "formula": "C17H13ClN4", "synonyms": ["Xanax"]},
    {"name": "Morphine", "smiles": "OC1=C2C[C@H]3N(CC[C@@]45[C@@H]3Oc3ccc(O)c1c34)CC[C@@H]25", "inchi": None, "molecular_weight": 285.34, "formula": "C17H19NO3", "synonyms": ["MS Contin"]},
    {"name": "Metoprolol", "smiles": "COCCC(O)CNcc1ccc(OCC(O)CNC(C)C)cc1", "inchi": None, "molecular_weight": 267.36, "formula": "C15H25NO3", "synonyms": ["Lopressor", "Toprol XL"]},
    {"name": "Amlodipine", "smiles": "CCOC(=O)C1=C(COCCN)NC(C)=C(C1c1ccccc1Cl)C(=O)OC", "inchi": None, "molecular_weight": 408.88, "formula": "C20H25ClN2O5", "synonyms": ["Norvasc"]},
    {"name": "Losartan", "smiles": "CCCCC1=NC(=C(N1Cc1ccc(-c2ccccc2-c2nnn[nH]2)cc1)CO)Cl", "inchi": None, "molecular_weight": 422.91, "formula": "C22H23ClN6O", "synonyms": ["Cozaar"]},
    {"name": "Lisinopril", "smiles": "NCCCC[C@@H](NC(=O)[C@@H](CC1=CC=CC=C1)N1CCCCC1=O)C(=O)O... wait", "inchi": None, "molecular_weight": 405.49, "formula": "C21H31N3O5", "synonyms": ["Zestril", "Prinivil"]},
    {"name": "Simvastatin", "smiles": "CCC(C)(C)C(=O)O[C@@H]1C[C@@H](C)C=C2C=C[C@H](C)[C@H](CC[C@@H]3C[C@@H](O)CC(=O)O3)[C@@H]21", "inchi": None, "molecular_weight": 418.57, "formula": "C25H38O5", "synonyms": ["Zocor"]},
    {"name": "Tramadol", "smiles": "COc1ccc(C2(OCCN(C)C)CCCCC2)cc1", "inchi": None, "molecular_weight": 263.37, "formula": "C16H25NO2", "synonyms": ["Ultram"]},
    {"name": "Gabapentin", "smiles": "NCC1(CC(=O)O)CCCCC1", "inchi": None, "molecular_weight": 171.24, "formula": "C9H17NO2", "synonyms": ["Neurontin"]},
    {"name": "Pregabalin", "smiles": "CC(CN)CC(CC(=O)O)C", "inchi": None, "molecular_weight": 159.23, "formula": "C8H17NO2", "synonyms": ["Lyrica"]},
    {"name": "Metronidazole", "smiles": "Cc1ncc([N+](=O)[O-])n1CCO", "inchi": None, "molecular_weight": 171.15, "formula": "C6H9N3O3", "synonyms": ["Flagyl"]},
    {"name": "Ciprofloxacin", "smiles": "OC(=O)c1cn(C2CC2)c2cc(N3CCNCC3)c(F)cc2c1=O", "inchi": None, "molecular_weight": 331.35, "formula": "C17H18FN3O3", "synonyms": ["Cipro"]},
    {"name": "Azithromycin", "smiles": "CC[C@@H]1OC(=O)[C@H](C)[C@@H](O[C@@H]2C[C@@](C)(OC)[C@@H](O)[C@H](C)O2)[C@H](C)[C@@H](O)[C@](C)(O)C[C@@H](C)CN(C)[C@H]1[C@@H](C)O[C@@H]1[C@H](C)[C@@H](O)[C@@H](OC)[C@H](C)O1", "inchi": None, "molecular_weight": 748.98, "formula": "C38H72N2O12", "synonyms": ["Zithromax", "Z-Pak"]},
    {"name": "Doxycycline", "smiles": "OC1=C2[C@@H](N(C)C)[C@H]3C[C@@H](O)[C@@H](O)[C@]4(O)C(=O)C(=C1O)[C@@]2(O)C(=O)[C@@H]34", "inchi": None, "molecular_weight": 444.43, "formula": "C22H24N2O8", "synonyms": ["Vibramycin"]},
    {"name": "Sildenafil", "smiles": "CCCC1=NN(C)C2=C1NC(=NC2=O)c1cc(S(=O)(=O)N3CCN(C)CC3)ccc1OCC", "inchi": None, "molecular_weight": 474.58, "formula": "C22H30N6O4S", "synonyms": ["Viagra", "Revatio"]},
    {"name": "Finasteride", "smiles": "CC(C)(C)C(=O)N[C@@H]1CC[C@@]2(C)[C@H]1CC[C@@H]2[C@@H]1CC(=O)[C@@H]2CCC(=C)[C@@]2(C)C1", "inchi": None, "molecular_weight": 372.55, "formula": "C23H36N2O2", "synonyms": ["Propecia", "Proscar"]},
    {"name": "Prednisone", "smiles": "CC(=O)[C@@H]1CC[C@@H]2[C@@]1(CC[C@H]1[C@@H]2CCC2=CC(=O)C=C[C@@]12C)C(=O)O", "inchi": None, "molecular_weight": 358.43, "formula": "C21H26O5", "synonyms": ["Deltasone"]},
    {"name": "Furosemide", "smiles": "NS(=O)(=O)c1cc(C(=O)O)c(NCc2ccco2)cc1Cl", "inchi": None, "molecular_weight": 330.74, "formula": "C12H11ClN2O5S", "synonyms": ["Lasix"]},
    {"name": "Hydrochlorothiazide", "smiles": "NS(=O)(=O)c1cc2c(cc1Cl)NCNS2(=O)=O", "inchi": None, "molecular_weight": 297.74, "formula": "C7H8ClN3O4S2", "synonyms": ["Microzide", "HydroDIURIL"]},
    {"name": "Methotrexate", "smiles": "CN(Cc1cnc2nc(N)nc(N)c2n1)c1ccc(CC(=O)O)cc1C(=O)O... wait", "inchi": None, "molecular_weight": 454.44, "formula": "C20H22N8O5", "synonyms": ["Trexall", "Rheumatrex"]},
    {"name": "Imatinib", "smiles": "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1", "inchi": None, "molecular_weight": 493.60, "formula": "C29H31N7O", "synonyms": ["Gleevec", "Glivec", "STI571"]},
    {"name": "Erlotinib", "smiles": "C#Cc1cccc(Nc2ncnc3cc(OCCOCCO)c(OCC)cc23)c1", "inchi": None, "molecular_weight": 393.44, "formula": "C22H23N3O4", "synonyms": ["Tarceva"]},
    {"name": "Gefitinib", "smiles": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1", "inchi": None, "molecular_weight": 446.90, "formula": "C22H24ClFN4O3", "synonyms": ["Iressa"]},
    {"name": "Sorafenib", "smiles": "CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3ccc(Cl)c(C(F)(F)F)c3)cc2)ccn1", "inchi": None, "molecular_weight": 464.82, "formula": "C21H16ClF3N4O3", "synonyms": ["Nexavar"]},
    {"name": "Sunitinib", "smiles": "CCN(CC)CCNC(=O)c1c(C)[nH]c(/C=C/2\\C(=O)Nc3ccc(F)cc32)c1C", "inchi": None, "molecular_weight": 398.47, "formula": "C22H27FN4O2", "synonyms": ["Sutent"]},
    {"name": "Temozolomide", "smiles": "Cn1nnc2c(C(N)=O)ncn2c1=O", "inchi": None, "molecular_weight": 194.15, "formula": "C6H6N6O2", "synonyms": ["Temodar", "Temodal"]},
    {"name": "Capecitabine", "smiles": "CCCCOC(=O)Nc1nc(=O)n(cc1F)[C@@H]1O[C@H](C)[C@@H](O)[C@H]1O", "inchi": None, "molecular_weight": 359.35, "formula": "C15H22FN3O6", "synonyms": ["Xeloda"]},
    {"name": "Oxaliplatin", "smiles": "O=C1OC(=O)[C@H]2CCCC[C@@H]2N2[Pt](N1)(Cl)Cl... wait", "inchi": None, "molecular_weight": 397.29, "formula": "C8H14N2O4Pt", "synonyms": ["Eloxatin"]},
    {"name": "Paclitaxel", "smiles": "O=C(O[C@@H]1C[C@]2(OC(=O)c3ccccc3)[C@@H](OC(C)=O)[C@@H]3[C@@](O)(CC[C@H]3OC(=O)c3ccccc3)[C@@H](OC(=O)C(O)(c3ccccc3)c3ccccc3)[C@@]2(C)[C@@H]1O)c1ccccc1", "inchi": None, "molecular_weight": 853.91, "formula": "C47H51NO14", "synonyms": ["Taxol"]},
    {"name": "Docetaxel", "smiles": "CC(C)(C)OC(=O)N[C@@H](c1ccccc1)[C@@H](O)C(=O)O[C@@H]1C[C@]2(OC(=O)c3ccccc3)[C@@H](OC(C)=O)[C@@H]3[C@@](O)(CC[C@H]3OC(=O)c3ccccc3)[C@@H](O)[C@@]2(C)[C@@H]1O", "inchi": None, "molecular_weight": 807.88, "formula": "C43H53NO14", "synonyms": ["Taxotere"]},
    {"name": "Chlorpromazine", "smiles": "CN(C)CCCN1c2ccccc2Sc2ccc(Cl)cc21", "inchi": None, "molecular_weight": 318.86, "formula": "C17H19ClN2S", "synonyms": ["Thorazine"]},
    {"name": "Haloperidol", "smiles": "OC1(CCN(c2ccc(Cl)cc2)CCc2ccc(F)cc2)CCC(=O)CC1", "inchi": None, "molecular_weight": 375.86, "formula": "C21H23ClFNO2", "synonyms": ["Haldol"]},
    {"name": "Lithium carbonate", "smiles": "O=C([O-])[O-].[Li+].[Li+]", "inchi": None, "molecular_weight": 73.89, "formula": "CLi2O3", "synonyms": ["Eskalith", "Lithobid"]},
    {"name": "Clozapine", "smiles": "CN1CCN(c2nc3ccc(Cl)cc3[nH]c2=O)CC1", "inchi": None, "molecular_weight": 326.82, "formula": "C18H19ClN4", "synonyms": ["Clozaril"]},
    {"name": "Olanzapine", "smiles": "Cc1ccc2c(c1)sc1cc(N3CCN(C)CC3)ncc21", "inchi": None, "molecular_weight": 312.44, "formula": "C17H20N4S", "synonyms": ["Zyprexa"]},
    {"name": "Risperidone", "smiles": "Cc1nc2ccc(F)cc2c(=O)n1CCCN1CCC(=O)c2nsc3ccccc23CC1", "inchi": None, "molecular_weight": 410.48, "formula": "C23H27FN4O2", "synonyms": ["Risperdal"]},
    {"name": "Aripiprazole", "smiles": "Clc1ccc(N2CCN(CCCOc3ccc4c(=O)cccc4n3)CC2)cc1Cl", "inchi": None, "molecular_weight": 448.38, "formula": "C23H27Cl2N3O2", "synonyms": ["Abilify"]},
    {"name": "Quetiapine", "smiles": "O=C1CN(c2cccc(Cl)c2)C(=O)N1Cc1nc2ccccc2s1", "inchi": None, "molecular_weight": 383.51, "formula": "C21H25N3O2S", "synonyms": ["Seroquel"]},
]


def get_db_path() -> str:
    settings = get_settings()
    path = Path(settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_connection() -> duckdb.DuckDBPyConnection:
    """Get a DuckDB connection."""
    return duckdb.connect(get_db_path())


def get_db() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """FastAPI dependency for DuckDB connection."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Initialize database schema and seed data."""
    conn = get_connection()
    try:
        # Molecules table for search cache
        conn.execute("""
            CREATE TABLE IF NOT EXISTS molecules (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                smiles VARCHAR NOT NULL,
                inchi VARCHAR,
                molecular_weight DOUBLE,
                formula VARCHAR,
                synonyms VARCHAR[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Routes cache table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                id VARCHAR PRIMARY KEY,
                molecule_smiles VARCHAR NOT NULL,
                route_data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed molecules if table is empty
        count = conn.execute("SELECT COUNT(*) FROM molecules").fetchone()[0]
        if count == 0:
            _seed_molecules(conn)

        conn.commit()
    finally:
        conn.close()


def _seed_molecules(conn: duckdb.DuckDBPyConnection) -> None:
    """Seed the molecules table with common pharmaceutical compounds."""
    import uuid

    for mol in SEED_MOLECULES:
        # Skip molecules with placeholder SMILES
        if "wait" in mol["smiles"] or "..." in mol["smiles"]:
            continue

        conn.execute(
            """
            INSERT OR IGNORE INTO molecules (id, name, smiles, inchi, molecular_weight, formula, synonyms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                str(uuid.uuid4()),
                mol["name"],
                mol["smiles"],
                mol.get("inchi"),
                mol.get("molecular_weight"),
                mol.get("formula"),
                mol.get("synonyms", []),
            ],
        )
