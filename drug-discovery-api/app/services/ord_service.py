from __future__ import annotations
import duckdb
from pathlib import Path
from app.config import get_settings

import logging
import re
import urllib.parse
from typing import List, Optional, Tuple

import httpx

from app.models.ord_models import LiteratureReference

logger = logging.getLogger(__name__)

CROSSREF_API_BASE = "https://api.crossref.org/works"
UNPAYWALL_API_BASE = "https://api.unpaywall.org/v2"
DEFAULT_EMAIL = "drugdiscovery-api@example.com"
HTTP_TIMEOUT = 12.0

def _google_scholar_url(doi: Optional[str], title: Optional[str] = None) -> str:
    if doi:
        query = f"doi:{doi}"
    elif title:
        query = title
    else:
        return "https://scholar.google.com/scholar"
    return f"https://scholar.google.com/scholar?q={urllib.parse.quote_plus(query)}"

def _crossref_doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}"

def _get_ord_connection():
    settings = get_settings()
    db_path = Path(settings.ord_db_path)
    if not db_path.is_absolute():
        cwd_path = Path.cwd() / db_path
        if cwd_path.exists():
            db_path = cwd_path
        else:
            
            here = Path(__file__).resolve()
            for parent in here.parents:
                candidate = parent / db_path
                if candidate.exists():
                    db_path = candidate
                    break

    return duckdb.connect(str(db_path), read_only=True)

def _query_ord_db(
    smiles: str,
    limit: int,
    role_filter: Optional[str],
) -> Tuple[List[dict], int]:
    safe = smiles.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{safe}%"

    role_col_map = {
        "product":  "product_smiles",
        "reactant": "reactant_smiles",
        "reagent":  "reagent_smiles",
        "catalyst": "catalyst_smiles",
        "solvent":  "solvent_smiles",
    }

    if role_filter and role_filter in role_col_map:
        col = role_col_map[role_filter]
        where_clause = f"{col} LIKE $1 ESCAPE '\\'"
        role_case = f"'{role_filter}'"
        params_where = [pattern]
    else:
        where_clause = """(
               product_smiles  LIKE $1 ESCAPE '\\'
            OR reactant_smiles LIKE $1 ESCAPE '\\'
            OR reagent_smiles  LIKE $1 ESCAPE '\\'
            OR catalyst_smiles LIKE $1 ESCAPE '\\'
            OR solvent_smiles  LIKE $1 ESCAPE '\\'
        )"""
        role_case = """
            CASE
                WHEN product_smiles  LIKE $1 ESCAPE '\\' THEN 'product'
                WHEN reactant_smiles LIKE $1 ESCAPE '\\' THEN 'reactant'
                WHEN reagent_smiles  LIKE $1 ESCAPE '\\' THEN 'reagent'
                WHEN catalyst_smiles LIKE $1 ESCAPE '\\' THEN 'catalyst'
                WHEN solvent_smiles  LIKE $1 ESCAPE '\\' THEN 'solvent'
                ELSE 'unknown'
            END
        """
        params_where = [pattern]

    count_sql = f"""
        SELECT COUNT(*)
        FROM ord
        WHERE doi IS NOT NULL
          AND {where_clause}
    """
    select_sql = f"""
        WITH ranked AS (
            SELECT
                doi,
                {role_case}                          AS role,
                COUNT(*)                              AS reaction_count,
                ANY_VALUE(reaction_id)                AS reaction_id,
                ANY_VALUE(dataset_name)               AS dataset_name,
                MAX(publication_year)                 AS publication_year,
                ANY_VALUE(reaction_smiles)            AS reaction_smiles,
                ROW_NUMBER() OVER (
                    PARTITION BY doi
                    ORDER BY COUNT(*) DESC
                ) AS rn
            FROM ord
            WHERE doi IS NOT NULL
              AND {where_clause}
            GROUP BY doi, role
        )
        SELECT doi, role, reaction_count, reaction_id,
               dataset_name, publication_year, reaction_smiles
        FROM ranked
        WHERE rn = 1
        ORDER BY reaction_count DESC
        LIMIT {limit}
    """
    conn = _get_ord_connection()
    try:
        total = conn.execute(count_sql, params_where).fetchone()[0]
        rows_raw = conn.execute(select_sql, params_where).fetchall()
        cols = ["doi", "role", "reaction_count", "reaction_id",
                "dataset_name", "publication_year", "reaction_smiles"]
        rows = [dict(zip(cols, r)) for r in rows_raw]
        return rows, total
    except Exception as exc:
        logger.error("DuckDB ORD query failed: %s", exc)
        return [], 0
    finally:
        conn.close()

async def _enrich_doi_crossref(doi: str, client: httpx.AsyncClient) -> dict:
    url = f"{CROSSREF_API_BASE}/{urllib.parse.quote(doi, safe='')}"
    try:
        r = await client.get(url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        item = r.json().get("message", {})

        title_list = item.get("title", [])
        title = title_list[0] if title_list else None

        authors = [
            f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
            for a in item.get("author", [])
        ] or None

        container = item.get("container-title", [])
        journal = container[0] if container else item.get("publisher")

        year = None
        for date_key in ("published-print", "published-online", "issued"):
            parts = item.get(date_key, {}).get("date-parts", [[]])
            if parts and parts[0]:
                year = parts[0][0]
                break

        abstract_raw = item.get("abstract", "") or ""
        abstract = re.sub(r"<[^>]+>", "", abstract_raw)[:500] or None

        return {
            "title":     title,
            "authors":   authors,
            "journal":   journal,
            "year":      year,
            "volume":    item.get("volume"),
            "issue":     item.get("issue"),
            "pages":     item.get("page"),
            "publisher": item.get("publisher"),
            "abstract":  abstract,
        }
    except Exception as exc:
        logger.debug("CrossRef failed for %s: %s", doi, exc)
        return {}



async def _resolve_unpaywall(
    doi: str,
    email: str,
    client: httpx.AsyncClient,
) -> Tuple[Optional[str], Optional[bool], Optional[str]]:
    url = (
        f"{UNPAYWALL_API_BASE}/{urllib.parse.quote(doi, safe='')}?"
        f"email={urllib.parse.quote(email)}"
    )
    try:
        r = await client.get(url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        best = data.get("best_oa_location") or {}
        dl_url = best.get("url_for_pdf") or best.get("url")
        return dl_url, data.get("is_oa"), data.get("oa_status")
    except Exception as exc:
        logger.debug("Unpaywall failed for %s: %s", doi, exc)
        return None, None, None

async def lookup_smiles_literature(
    smiles: str,
    limit: int = 10,
    role: Optional[str] = None,
    email: Optional[str] = None,
) -> Tuple[List[LiteratureReference], int, List[str], Optional[str]]:
    contact_email = email or DEFAULT_EMAIL
    sources: List[str] = ["ORD (DuckDB)"]
    note: Optional[str] = None

    doi_rows, total_reactions = _query_ord_db(smiles, limit, role)

    if not doi_rows:
        note = (
            f"No ORD reactions found containing SMILES '{smiles}'. "
            "Try a shorter fragment or check for stereochemistry / salt variants."
        )
        return [], 0, sources, note
    import asyncio

    async with httpx.AsyncClient(
        headers={"User-Agent": "DrugDiscoveryAPI/1.0"},
        follow_redirects=True,
    ) as client:
        cr_tasks = [_enrich_doi_crossref(row["doi"], client) for row in doi_rows]
        uw_tasks = [_resolve_unpaywall(row["doi"], contact_email, client) for row in doi_rows]

        cr_results = await asyncio.gather(*cr_tasks, return_exceptions=True)
        uw_results = await asyncio.gather(*uw_tasks, return_exceptions=True)
    
    cr_ok = any(isinstance(r, dict) and r for r in cr_results)
    uw_ok = any(isinstance(r, tuple) and r[0] is not None for r in uw_results)
    if cr_ok:
        sources.append("CrossRef")
    if uw_ok:
        sources.append("Unpaywall")

    refs: List[LiteratureReference] = []
    for idx, row in enumerate(doi_rows):
        doi = row["doi"]

        meta: dict = cr_results[idx] if isinstance(cr_results[idx], dict) else {}
        oa = uw_results[idx] if isinstance(uw_results[idx], tuple) else (None, None, None)
        dl_url, is_oa, oa_status = oa

        year = meta.get("year") or row.get("publication_year")

        ref = LiteratureReference(
            doi=doi,
            ord_reaction_id=row.get("reaction_id"),
            role_in_reaction=row.get("role", "unknown"),
            title=meta.get("title"),
            authors=meta.get("authors"),
            journal=meta.get("journal"),
            year=year,
            volume=meta.get("volume"),
            issue=meta.get("issue"),
            pages=meta.get("pages"),
            publisher=meta.get("publisher"),
            abstract=meta.get("abstract"),
            crossref_url=_crossref_doi_url(doi),
            google_scholar_url=_google_scholar_url(doi, meta.get("title")),
            download_url=dl_url,
            is_open_access=is_oa,
            oa_status=oa_status,
            dataset_id=row.get("dataset_name"),
            reaction_smiles=row.get("reaction_smiles"),
        )
        refs.append(ref)

    return refs, total_reactions, sources, note
