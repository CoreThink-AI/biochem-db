
import duckdb
from typing import List

from app.models.molecule_models import Molecule, SearchMoleculesRequest


def search_molecules(
    request: SearchMoleculesRequest,
    conn: duckdb.DuckDBPyConnection,
) -> List[Molecule]:

    query = request.query.strip()
    limit = request.limit

    rows = conn.execute(
        """
        SELECT DISTINCT name, smiles, inchi, molecular_weight, formula, synonyms
        FROM molecules
        WHERE
            lower(name) LIKE lower(?) || '%'
            OR smiles LIKE ? || '%'
            OR EXISTS (
                SELECT 1 FROM UNNEST(synonyms) AS t(syn)
                WHERE lower(syn) LIKE lower(?) || '%'
            )
        ORDER BY
            CASE WHEN lower(name) LIKE lower(?) || '%' THEN 0 ELSE 1 END,
            name
        LIMIT ?
        """,
        [query, query, query, query, limit],
    ).fetchall()

    molecules = []
    for row in rows:
        name, smiles, inchi, mw, formula, synonyms = row
        molecules.append(
            Molecule(
                name=name,
                smiles=smiles,
                inchi=inchi,
                molecular_weight=mw,
                formula=formula,
                synonyms=synonyms if synonyms else [],
            )
        )
    return molecules


def get_molecule_by_smiles(
    smiles: str,
    conn: duckdb.DuckDBPyConnection,
) -> Molecule | None:
    row = conn.execute(
        "SELECT name, smiles, inchi, molecular_weight, formula, synonyms FROM molecules WHERE smiles = ?",
        [smiles],
    ).fetchone()

    if row:
        name, smiles_val, inchi, mw, formula, synonyms = row
        return Molecule(
            name=name,
            smiles=smiles_val,
            inchi=inchi,
            molecular_weight=mw,
            formula=formula,
            synonyms=synonyms if synonyms else [],
        )
    return None
