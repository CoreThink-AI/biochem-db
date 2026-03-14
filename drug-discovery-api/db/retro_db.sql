-- duckdb ord.duckdb

DESCRIBE SELECT * FROM read_parquet('ord_reactions.parquet');
──────────────────┬─────────────┬─────────┬─────────┬─────────┬─────────┐
│   column_name    │ column_type │  null   │   key   │ default │  extra  │
│     varchar      │   varchar   │ varchar │ varchar │ varchar │ varchar │
├──────────────────┼─────────────┼─────────┼─────────┼─────────┼─────────┤
│ reaction_id      │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ dataset_id       │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ dataset_name     │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ reaction_smiles  │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ reactant_smiles  │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ reagent_smiles   │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ solvent_smiles   │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ catalyst_smiles  │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ num_reactants    │ INTEGER     │ YES     │ NULL    │ NULL    │ NULL    │
│ num_reagents     │ INTEGER     │ YES     │ NULL    │ NULL    │ NULL    │
│ num_solvents     │ INTEGER     │ YES     │ NULL    │ NULL    │ NULL    │
│ product_smiles   │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ yield_pct        │ FLOAT       │ YES     │ NULL    │ NULL    │ NULL    │
│ conversion_pct   │ FLOAT       │ YES     │ NULL    │ NULL    │ NULL    │
│ num_products     │ INTEGER     │ YES     │ NULL    │ NULL    │ NULL    │
│ temperature_c    │ FLOAT       │ YES     │ NULL    │ NULL    │ NULL    │
│ pressure_atm     │ FLOAT       │ YES     │ NULL    │ NULL    │ NULL    │
│ stirring_rpm     │ FLOAT       │ YES     │ NULL    │ NULL    │ NULL    │
│ doi              │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ created_by       │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ publication_year │ INTEGER     │ YES     │ NULL    │ NULL    │ NULL    │
│ notes_procedure  │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ notes_safety     │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
├──────────────────┴─────────────┴─────────┴─────────┴─────────┴─────────┤
│ 23 rows                                                      6 columns │
└────────────────────────────────────────────────────────────────────────┘


SELECT *
  FROM read_parquet('ord_reactions.parquet')
  LIMIT 1;
┌──────────────────────┬──────────────────────┬──────────────────────┬─────────────────┬──────────────────────┬──────────────────────┬────────────────┬──────────────────────┬───────────────┬───┬────────────────┬──────────────┬───────────────┬──────────────┬──────────────┬─────────┬────────────┬──────────────────┬──────────────────────┬──────────────┐
│     reaction_id      │      dataset_id      │     dataset_name     │ reaction_smiles │   reactant_smiles    │    reagent_smiles    │ solvent_smiles │   catalyst_smiles    │ num_reactants │ … │ conversion_pct │ num_products │ temperature_c │ pressure_atm │ stirring_rpm │   doi   │ created_by │ publication_year │   notes_procedure    │ notes_safety │
│       varchar        │       varchar        │       varchar        │     varchar     │       varchar        │       varchar        │    varchar     │       varchar        │     int32     │   │     float      │    int32     │     float     │    float     │    float     │ varchar │  varchar   │      int32       │       varchar        │   varchar    │
├──────────────────────┼──────────────────────┼──────────────────────┼─────────────────┼──────────────────────┼──────────────────────┼────────────────┼──────────────────────┼───────────────┼───┼────────────────┼──────────────┼───────────────┼──────────────┼──────────────┼─────────┼────────────┼──────────────────┼──────────────────────┼──────────────┤
│ ord-56b1f4bfeebc4b…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ NULL            │ CCOC1=C(C=C2C(=C1)…  │ C(=O)([O-])[O-].[C…  │ NULL           │ C1=CC=C(C=C1)P(C2=…  │       2       │ … │      NULL      │      1       │     110.0     │     NULL     │     NULL     │ NULL    │ NULL       │       NULL       │ To a solution of e…  │ NULL         │
├──────────────────────┴──────────────────────┴──────────────────────┴─────────────────┴──────────────────────┴──────────────────────┴────────────────┴──────────────────────┴───────────────┴───┴────────────────┴──────────────┴───────────────┴──────────────┴──────────────┴─────────┴────────────┴──────────────────┴──────────────────────┴──────────────┤
│ 1 rows                                                                                                                                                                                                                                                                                                                                 23 columns (19 shown) │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

D CREATE OR REPLACE VIEW ord AS SELECT * FROM read_parquet('ord_reactions.parquet');
D 
D CREATE TABLE ord_tbl AS SELECT * FROM ord;
100% ▕██████████████████████████████████████▏ (00:00:02.86 elapsed)     


D SELECT COUNT(*) AS n_reactions FROM ord_tbl;
┌────────────────┐
│  n_reactions   │
│     int64      │
├────────────────┤
│    2376120     │
│ (2.38 million) │
└────────────────┘


D SELECT reactant_smiles, num_reactants
  FROM ord
  WHERE reactant_smiles IS NOT NULL
  LIMIT 5;
┌─────────────────────────────────────────────────────────────────────────┬───────────────┐
│                             reactant_smiles                             │ num_reactants │
│                                 varchar                                 │     int32     │
├─────────────────────────────────────────────────────────────────────────┼───────────────┤
│ CCOC1=C(C=C2C(=C1)N=CC(=C2NC3=C(C=C(C=C3)F)F)C(=O)OCC)Br; CC(C)N1CCNCC1 │             2 │
│ C1=CC=C(C=C1)I; CN1C=NC2=C1C=C(C(=C2F)N)C(=O)OC                         │             2 │
│ C1=CC=C(C=C1)I; CN1C=NC2=C1C=C(C(=C2F)N)C(=O)OC                         │             2 │
│ C1=CC=C(C=C1)I; CN1C=NC2=C1C=C(C(=C2F)N)C(=O)OC                         │             2 │
│ CC1=NC(=C(C=C1)OC2=CC(=NC=C2)Cl)C; C1=CC(=CC=C1N)S(=O)(=O)N             │             2 │
└─────────────────────────────────────────────────────────────────────────┴───────────────┘

D CREATE OR REPLACE VIEW retro_edges AS
  SELECT
    reaction_id,
    dataset_id,
    dataset_name,
    product_smiles,
    str_split(reactant_smiles, '.') AS reactants,
    reagent_smiles,
    solvent_smiles,
    catalyst_smiles,
    yield_pct,
    temperature_c,
    pressure_atm,
    stirring_rpm,
    doi,
    publication_year,
    notes_safety,
    notes_procedure
  FROM ord
  WHERE product_smiles IS NOT NULL
    AND reactant_smiles IS NOT NULL;
D select * from retro_edges limit 10;
┌──────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┬────────────────┬──────────────────────┬───────────┬───────────────┬──────────────┬──────────────┬─────────┬──────────────────┬──────────────┬────────────────────────────────────────────────────────────────────────┐
│     reaction_id      │      dataset_id      │     dataset_name     │    product_smiles    │      reactants       │    reagent_smiles    │ solvent_smiles │   catalyst_smiles    │ yield_pct │ temperature_c │ pressure_atm │ stirring_rpm │   doi   │ publication_year │ notes_safety │                            notes_procedure                             │
│       varchar        │       varchar        │       varchar        │       varchar        │      varchar[]       │       varchar        │    varchar     │       varchar        │   float   │     float     │    float     │    float     │ varchar │      int32       │   varchar    │                                varchar                                 │
├──────────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼────────────────┼──────────────────────┼───────────┼───────────────┼──────────────┼──────────────┼─────────┼──────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────┤
│ ord-56b1f4bfeebc4b…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CCOC1=C(C=C2C(=C1)…  │ ['CCOC1=C(C=C2C(=C…  │ C(=O)([O-])[O-].[C…  │ NULL           │ C1=CC=C(C=C1)P(C2=…  │     65.39 │         110.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │ To a solution of ethyl 6-bromo-4-(2,4-difluorophenylamino)-7-ethoxyq…  │
│ ord-1169cbe9fa064a…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CN1C=NC2=C1C=C(C(=…  │ ['C1=CC=C(C=C1)I; …  │ C(=O)([O-])[O-].[C…  │ COC1=CC=CC=C1  │ CC1(C2=C(C(=CC=C2)…  │     57.47 │         100.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │ 9,9-Dimethyl-4,5-bis(diphenylphosphino)xanthene (441 mg, 0.76 mmol) …  │
│ ord-13992005c22d46…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CN1C=NC2=C1C=C(C(=…  │ ['C1=CC=C(C=C1)I; …  │ C(=O)([O-])[O-].[C…  │ COC1=CC=CC=C1  │ CC1(C2=C(C(=CC=C2)…  │     65.43 │         100.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │ 9,9-Dimethyl-4,5-bis(diphenylphosphino)xanthene (389 mg, 0.67 mmol) …  │
│ ord-a36b48917c9942…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CN1C=NC2=C1C=C(C(=…  │ ['C1=CC=C(C=C1)I; …  │ C(=O)([O-])[O-].[C…  │ COC1=CC=CC=C1  │ CC1(C2=C(C(=CC=C2)…  │     75.07 │         100.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │ 9,9-Dimethyl-4,5-bis(diphenylphosphino)xanthene (389 mg, 0.67 mmol) …  │
│ ord-5fc624fd97b743…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CC1=NC(=C(C=C1)OC2…  │ ['CC1=NC(=C(C=C1)O…  │ C(=O)([O-])[O-].[C…  │ CC(=O)N(C)C    │ CC1(C2=C(C(=CC=C2)…  │     46.32 │         150.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │  3-(2-chloropyridin-4-yloxy)-2,6-dimethylpyridine (6.47 g, 27.57 mmo…  │
│ ord-c34e3f2a76e446…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CC1=NC(=C(C=C1)OC2…  │ ['CC1=NC(=C(C=C1)O…  │ C(=O)([O-])[O-].[C…  │ CC(=O)N(C)C    │ CC1(C2=C(C(=CC=C2)…  │     76.03 │         130.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │ XANTPHOS (2.466 g, 4.26 mmol) was added to 3-(2-chloropyridin-4-ylox…  │
│ ord-5853dba4038641…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CC1=NC(=C(C=C1)OC2…  │ ['CC1=NC(=C(C=C1)O…  │ C(=O)([O-])[O-].[C…  │ CC(=O)N(C)C    │ CC1(C2=C(C(=CC=C2)…  │     40.86 │         130.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │  3-(2-chloropyridin-4-yloxy)-2,6-dimethylpyridine (2 g, 8.52 mmol), …  │
│ ord-0c597cbe494049…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CC1=NC(=C(C=C1)OC2…  │ ['CC1=NC(=C(C=C1)O…  │ C(=O)([O-])[O-].[C…  │ CC(=O)N(C)C    │ CC1(C2=C(C(=CC=C2)…  │     62.38 │         130.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │ XANTPHOS (1.603 g, 2.77 mmol) was added to 3-(2-chloropyridin-4-ylox…  │
│ ord-b3c4a680709749…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CC(=O)N1CCN(CC1)C2…  │ ['C1=C(C=NC=C1Br)B…  │ C(=O)([O-])[O-].[C…  │ NULL           │ CC1(C2=C(C(=CC=C2)…  │     31.78 │         140.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │ 3,5-dibromopyridine (1.233 g, 5.20 mmol), 1-(piperazin-1-yl)ethanone…  │
│ ord-fa122fe6774f45…  │ ord_dataset-000055…  │ 750 AstraZeneca EL…  │ CN1CC(OC2=C(C1)C=C…  │ ['CN1CC(OC2=C(C1)C…  │ C(=O)([O-])[O-].[C…  │ COCCOC         │ C1CCC(CC1)P(C2CCCC…  │     41.47 │         100.0 │         NULL │         NULL │ NULL    │             NULL │ NULL         │ [Reactants], 8-chloro-4-methyl-2-phenyl-2,3,4,5-tetrahydropyrido[3,2…  │
├──────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┴────────────────┴──────────────────────┴───────────┴───────────────┴──────────────┴──────────────┴─────────┴──────────────────┴──────────────┴────────────────────────────────────────────────────────────────────────┤
│ 10 rows                                                                                                                                                                                                                                                                                                                                             16 columns │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
D 


 
CREATE OR REPLACE VIEW reactions AS
  SELECT
    reaction_id,
    'ord'           AS source,
    dataset_id,
    dataset_name,
    reaction_smiles,
    reactant_smiles,
    reagent_smiles,
    solvent_smiles,
    catalyst_smiles,
    product_smiles,
    num_reactants,
    num_reagents,
    num_solvents,
    num_products,
    yield_pct,
    conversion_pct,
    temperature_c,
    pressure_atm,
    stirring_rpm,
    doi,
    publication_year,
    notes_procedure,
    notes_safety
  FROM ord
  WHERE reaction_smiles IS NOT NULL
     OR (reactant_smiles IS NOT NULL AND product_smiles IS NOT NULL);
 
 
CREATE OR REPLACE VIEW retro_edges AS
  SELECT
    reaction_id,
    source,
    dataset_id,
    dataset_name,
    product_smiles,
    str_split(reactant_smiles, '; ')   AS reactants,
    reagent_smiles,
    solvent_smiles,
    catalyst_smiles,
    yield_pct,
    temperature_c,
    pressure_atm,
    stirring_rpm,
    doi,
    publication_year,
    notes_procedure,
    notes_safety
  FROM reactions
  WHERE product_smiles   IS NOT NULL
    AND reactant_smiles  IS NOT NULL;


CREATE OR REPLACE VIEW molecules AS 
  SELECT
    CAST(cid AS VARCHAR)  AS mol_id,
    'pubchem'             AS mol_source,
    smiles,
    inchikey,
    iupac_name            AS name,
    molecular_formula,
    molecular_weight,
    exact_mass,
    xlogp3,
    hbond_donors,
    hbond_acceptors,
    rotatable_bonds,
    tpsa,
    total_charge,
    heavy_atom_count,
    complexity
  FROM pubchem
  WHERE smiles IS NOT NULL

  UNION ALL
 
  SELECT
    reaction_id           AS mol_id,
    source || '_product'  AS mol_source,
    product_smiles        AS smiles,
    NULL                  AS inchikey,
    NULL                  AS name,
    NULL                  AS molecular_formula,
    NULL                  AS molecular_weight,
    NULL                  AS exact_mass,
    NULL                  AS xlogp3,
    NULL                  AS hbond_donors,
    NULL                  AS hbond_acceptors,
    NULL                  AS rotatable_bonds,
    NULL                  AS tpsa,
    NULL                  AS total_charge,
    NULL                  AS heavy_atom_count,
    NULL                  AS complexity
  FROM reactions
  WHERE product_smiles IS NOT NULL
    AND product_smiles NOT IN (SELECT smiles FROM pubchem WHERE smiles IS NOT NULL);

 
SELECT 'pubchem'   AS tbl, COUNT(*) AS n FROM pubchem
UNION ALL
SELECT 'ord'       AS tbl, COUNT(*) AS n FROM ord
UNION ALL
SELECT 'reactions' AS tbl, COUNT(*) AS n FROM reactions
UNION ALL
SELECT 'retro_edges' AS tbl, COUNT(*) AS n FROM retro_edges;
┌─────────────┬─────────┐
│     tbl     │    n    │
│   varchar   │  int64  │
├─────────────┼─────────┤
│ pubchem     │  444786 │
│ ord         │ 2376120 │
│ reactions   │ 2375951 │
│ retro_edges │ 2375899 │
└─────────────┴─────────┘

D SELECT *
  FROM read_csv_auto('CID-SMILES.gz', delim='\t', compression='gzip')
  LIMIT 10;
┌─────────┬───────────────────────────────────────────┐
│ column0 │                  column1                  │
│  int64  │                  varchar                  │
├─────────┼───────────────────────────────────────────┤
│       1 │ CC(=O)OC(CC(=O)[O-])C[N+](C)(C)C          │
│       2 │ CC(=O)OC(CC(=O)O)C[N+](C)(C)C             │
│       3 │ C1=CC(C(C(=C1)C(=O)O)O)O                  │
│       4 │ CC(CN)O                                   │
│       5 │ C(C(=O)COP(=O)(O)O)N                      │
│       6 │ C1=CC(=C(C=C1[N+](=O)[O-])[N+](=O)[O-])Cl │
│       7 │ CCN1C=NC2=C(N=CN=C21)N                    │
│       8 │ CCC(C)(C(C(=O)O)O)O                       │
│       9 │ C1(C(C(C(C(C1O)O)OP(=O)(O)O)O)O)O         │
│      11 │ C(CCl)Cl                                  │
├─────────┴───────────────────────────────────────────┤
│ 10 rows                                   2 columns │
└─────────────────────────────────────────────────────┘
D DESCRIBE
  SELECT *
  FROM read_csv_auto('CID-SMILES.gz', delim='\t', compression='gzip');
┌─────────────┬─────────────┬─────────┬─────────┬─────────┬─────────┐
│ column_name │ column_type │  null   │   key   │ default │  extra  │
│   varchar   │   varchar   │ varchar │ varchar │ varchar │ varchar │
├─────────────┼─────────────┼─────────┼─────────┼─────────┼─────────┤
│ column0     │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ column1     │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
└─────────────┴─────────────┴─────────┴─────────┴─────────┴─────────┘

CREATE TABLE pubchem_smiles AS
  SELECT
      column0 AS cid,
      column1 AS smiles
  FROM read_csv_auto(
      'CID-SMILES.gz',
      delim='\t',
      compression='gzip'
  );

SELECT count(*) FROM pubchem_smiles LIMIT 10;
┌──────────────────┐
│   count_star()   │
│      int64       │
├──────────────────┤
│    123506060     │
│ (123.51 million) │
└──────────────────┘

D show tables;
┌────────────────┐
│      name      │
│    varchar     │
├────────────────┤
│ molecules      │
│ ord            │
│ pubchem        │
│ pubchem_smiles │
│ reactions      │
│ retro_edges    │
│ src_ord        │
│ src_pubchem    │
└────────────────┘
D 



D  SELECT 
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name IN (
        'eval_smiles'
    )
    ORDER BY table_name, ordinal_position;
┌─────────────┬─────────────┬──────────────────┬───────────┬─────────────┬────────────────┐
│ table_name  │ column_name │ ordinal_position │ data_type │ is_nullable │ column_default │
│   varchar   │   varchar   │      int32       │  varchar  │   varchar   │    varchar     │
├─────────────┼─────────────┼──────────────────┼───────────┼─────────────┼────────────────┤
│ eval_smiles │ cid         │                1 │ BIGINT    │ YES         │ NULL           │
│ eval_smiles │ smiles      │                2 │ VARCHAR   │ YES         │ NULL           │
│ eval_smiles │ source      │                3 │ VARCHAR   │ YES         │ NULL           │
└─────────────┴─────────────┴──────────────────┴───────────┴─────────────┴────────────────┘
D SELECT 
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name IN (
        'molecules'
    )
    ORDER BY table_name, ordinal_position;
┌────────────┬───────────────────┬──────────────────┬───────────┬─────────────┬────────────────┐
│ table_name │    column_name    │ ordinal_position │ data_type │ is_nullable │ column_default │
│  varchar   │      varchar      │      int32       │  varchar  │   varchar   │    varchar     │
├────────────┼───────────────────┼──────────────────┼───────────┼─────────────┼────────────────┤
│ molecules  │ mol_id            │                1 │ VARCHAR   │ YES         │ NULL           │
│ molecules  │ mol_source        │                2 │ VARCHAR   │ YES         │ NULL           │
│ molecules  │ smiles            │                3 │ VARCHAR   │ YES         │ NULL           │
│ molecules  │ inchikey          │                4 │ VARCHAR   │ YES         │ NULL           │
│ molecules  │ name              │                5 │ VARCHAR   │ YES         │ NULL           │
│ molecules  │ molecular_formula │                6 │ VARCHAR   │ YES         │ NULL           │
│ molecules  │ molecular_weight  │                7 │ FLOAT     │ YES         │ NULL           │
│ molecules  │ exact_mass        │                8 │ DOUBLE    │ YES         │ NULL           │
│ molecules  │ xlogp3            │                9 │ FLOAT     │ YES         │ NULL           │
│ molecules  │ hbond_donors      │               10 │ SMALLINT  │ YES         │ NULL           │
│ molecules  │ hbond_acceptors   │               11 │ SMALLINT  │ YES         │ NULL           │
│ molecules  │ rotatable_bonds   │               12 │ SMALLINT  │ YES         │ NULL           │
│ molecules  │ tpsa              │               13 │ FLOAT     │ YES         │ NULL           │
│ molecules  │ total_charge      │               14 │ SMALLINT  │ YES         │ NULL           │
│ molecules  │ heavy_atom_count  │               15 │ SMALLINT  │ YES         │ NULL           │
│ molecules  │ complexity        │               16 │ FLOAT     │ YES         │ NULL           │
├────────────┴───────────────────┴──────────────────┴───────────┴─────────────┴────────────────┤
│ 16 rows                                                                            6 columns │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
D SELECT 
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name IN (
        'ord'
    )
    ORDER BY table_name, ordinal_position;
┌────────────┬──────────────────┬──────────────────┬───────────┬─────────────┬────────────────┐
│ table_name │   column_name    │ ordinal_position │ data_type │ is_nullable │ column_default │
│  varchar   │     varchar      │      int32       │  varchar  │   varchar   │    varchar     │
├────────────┼──────────────────┼──────────────────┼───────────┼─────────────┼────────────────┤
│ ord        │ reaction_id      │                1 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ dataset_id       │                2 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ dataset_name     │                3 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ reaction_smiles  │                4 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ reactant_smiles  │                5 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ reagent_smiles   │                6 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ solvent_smiles   │                7 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ catalyst_smiles  │                8 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ num_reactants    │                9 │ INTEGER   │ YES         │ NULL           │
│ ord        │ num_reagents     │               10 │ INTEGER   │ YES         │ NULL           │
│ ord        │ num_solvents     │               11 │ INTEGER   │ YES         │ NULL           │
│ ord        │ product_smiles   │               12 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ yield_pct        │               13 │ FLOAT     │ YES         │ NULL           │
│ ord        │ conversion_pct   │               14 │ FLOAT     │ YES         │ NULL           │
│ ord        │ num_products     │               15 │ INTEGER   │ YES         │ NULL           │
│ ord        │ temperature_c    │               16 │ FLOAT     │ YES         │ NULL           │
│ ord        │ pressure_atm     │               17 │ FLOAT     │ YES         │ NULL           │
│ ord        │ stirring_rpm     │               18 │ FLOAT     │ YES         │ NULL           │
│ ord        │ doi              │               19 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ created_by       │               20 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ publication_year │               21 │ INTEGER   │ YES         │ NULL           │
│ ord        │ notes_procedure  │               22 │ VARCHAR   │ YES         │ NULL           │
│ ord        │ notes_safety     │               23 │ VARCHAR   │ YES         │ NULL           │
├────────────┴──────────────────┴──────────────────┴───────────┴─────────────┴────────────────┤
│ 23 rows                                                                           6 columns │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
D SELECT 
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name IN (
        'pubchem'
    )
    ORDER BY table_name, ordinal_position;
┌────────────┬─────────────────────┬──────────────────┬───────────┬─────────────┬────────────────┐
│ table_name │     column_name     │ ordinal_position │ data_type │ is_nullable │ column_default │
│  varchar   │       varchar       │      int32       │  varchar  │   varchar   │    varchar     │
├────────────┼─────────────────────┼──────────────────┼───────────┼─────────────┼────────────────┤
│ pubchem    │ cid                 │                1 │ INTEGER   │ YES         │ NULL           │
│ pubchem    │ smiles              │                2 │ VARCHAR   │ YES         │ NULL           │
│ pubchem    │ iupac_name          │                3 │ VARCHAR   │ YES         │ NULL           │
│ pubchem    │ inchi               │                4 │ VARCHAR   │ YES         │ NULL           │
│ pubchem    │ inchikey            │                5 │ VARCHAR   │ YES         │ NULL           │
│ pubchem    │ molecular_formula   │                6 │ VARCHAR   │ YES         │ NULL           │
│ pubchem    │ molecular_weight    │                7 │ FLOAT     │ YES         │ NULL           │
│ pubchem    │ exact_mass          │                8 │ DOUBLE    │ YES         │ NULL           │
│ pubchem    │ monoisotopic_weight │                9 │ DOUBLE    │ YES         │ NULL           │
│ pubchem    │ xlogp3              │               10 │ FLOAT     │ YES         │ NULL           │
│ pubchem    │ hbond_acceptors     │               11 │ SMALLINT  │ YES         │ NULL           │
│ pubchem    │ hbond_donors        │               12 │ SMALLINT  │ YES         │ NULL           │
│ pubchem    │ rotatable_bonds     │               13 │ SMALLINT  │ YES         │ NULL           │
│ pubchem    │ tpsa                │               14 │ FLOAT     │ YES         │ NULL           │
│ pubchem    │ total_charge        │               15 │ SMALLINT  │ YES         │ NULL           │
│ pubchem    │ heavy_atom_count    │               16 │ SMALLINT  │ YES         │ NULL           │
│ pubchem    │ complexity          │               17 │ FLOAT     │ YES         │ NULL           │
│ pubchem    │ source_file         │               18 │ VARCHAR   │ YES         │ NULL           │
├────────────┴─────────────────────┴──────────────────┴───────────┴─────────────┴────────────────┤
│ 18 rows                                                                              6 columns │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
D SELECT 
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name IN (
        'reactions'
    )
    ORDER BY table_name, ordinal_position;
┌────────────┬──────────────────┬──────────────────┬───────────┬─────────────┬────────────────┐
│ table_name │   column_name    │ ordinal_position │ data_type │ is_nullable │ column_default │
│  varchar   │     varchar      │      int32       │  varchar  │   varchar   │    varchar     │
├────────────┼──────────────────┼──────────────────┼───────────┼─────────────┼────────────────┤
│ reactions  │ reaction_id      │                1 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ source           │                2 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ dataset_id       │                3 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ dataset_name     │                4 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ reaction_smiles  │                5 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ reactant_smiles  │                6 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ reagent_smiles   │                7 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ solvent_smiles   │                8 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ catalyst_smiles  │                9 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ product_smiles   │               10 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ num_reactants    │               11 │ INTEGER   │ YES         │ NULL           │
│ reactions  │ num_reagents     │               12 │ INTEGER   │ YES         │ NULL           │
│ reactions  │ num_solvents     │               13 │ INTEGER   │ YES         │ NULL           │
│ reactions  │ num_products     │               14 │ INTEGER   │ YES         │ NULL           │
│ reactions  │ yield_pct        │               15 │ FLOAT     │ YES         │ NULL           │
│ reactions  │ conversion_pct   │               16 │ FLOAT     │ YES         │ NULL           │
│ reactions  │ temperature_c    │               17 │ FLOAT     │ YES         │ NULL           │
│ reactions  │ pressure_atm     │               18 │ FLOAT     │ YES         │ NULL           │
│ reactions  │ stirring_rpm     │               19 │ FLOAT     │ YES         │ NULL           │
│ reactions  │ doi              │               20 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ publication_year │               21 │ INTEGER   │ YES         │ NULL           │
│ reactions  │ notes_procedure  │               22 │ VARCHAR   │ YES         │ NULL           │
│ reactions  │ notes_safety     │               23 │ VARCHAR   │ YES         │ NULL           │
├────────────┴──────────────────┴──────────────────┴───────────┴─────────────┴────────────────┤
│ 23 rows                                                                           6 columns │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
D SELECT 
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name IN (
        'pubchem_smiles'
    )
    ORDER BY table_name, ordinal_position;
┌────────────────┬─────────────┬──────────────────┬───────────┬─────────────┬────────────────┐
│   table_name   │ column_name │ ordinal_position │ data_type │ is_nullable │ column_default │
│    varchar     │   varchar   │      int32       │  varchar  │   varchar   │    varchar     │
├────────────────┼─────────────┼──────────────────┼───────────┼─────────────┼────────────────┤
│ pubchem_smiles │ cid         │                1 │ BIGINT    │ YES         │ NULL           │
│ pubchem_smiles │ smiles      │                2 │ VARCHAR   │ YES         │ NULL           │
└────────────────┴─────────────┴──────────────────┴───────────┴─────────────┴────────────────┘
D SELECT 
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name IN (
        'retro_edges'
    )
    ORDER BY table_name, ordinal_position;
┌─────────────┬──────────────────┬──────────────────┬───────────┬─────────────┬────────────────┐
│ table_name  │   column_name    │ ordinal_position │ data_type │ is_nullable │ column_default │
│   varchar   │     varchar      │      int32       │  varchar  │   varchar   │    varchar     │
├─────────────┼──────────────────┼──────────────────┼───────────┼─────────────┼────────────────┤
│ retro_edges │ reaction_id      │                1 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ source           │                2 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ dataset_id       │                3 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ dataset_name     │                4 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ product_smiles   │                5 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ reactants        │                6 │ VARCHAR[] │ YES         │ NULL           │
│ retro_edges │ reagent_smiles   │                7 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ solvent_smiles   │                8 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ catalyst_smiles  │                9 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ yield_pct        │               10 │ FLOAT     │ YES         │ NULL           │
│ retro_edges │ temperature_c    │               11 │ FLOAT     │ YES         │ NULL           │
│ retro_edges │ pressure_atm     │               12 │ FLOAT     │ YES         │ NULL           │
│ retro_edges │ stirring_rpm     │               13 │ FLOAT     │ YES         │ NULL           │
│ retro_edges │ doi              │               14 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ publication_year │               15 │ INTEGER   │ YES         │ NULL           │
│ retro_edges │ notes_procedure  │               16 │ VARCHAR   │ YES         │ NULL           │
│ retro_edges │ notes_safety     │               17 │ VARCHAR   │ YES         │ NULL           │
├─────────────┴──────────────────┴──────────────────┴───────────┴─────────────┴────────────────┤
│ 17 rows                                                                            6 columns │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
D SELECT 
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name IN (
        'src_ord'
    )
    ORDER BY table_name, ordinal_position;
┌────────────┬──────────────────┬──────────────────┬───────────┬─────────────┬────────────────┐
│ table_name │   column_name    │ ordinal_position │ data_type │ is_nullable │ column_default │
│  varchar   │     varchar      │      int32       │  varchar  │   varchar   │    varchar     │
├────────────┼──────────────────┼──────────────────┼───────────┼─────────────┼────────────────┤
│ src_ord    │ reaction_id      │                1 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ dataset_id       │                2 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ dataset_name     │                3 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ reaction_smiles  │                4 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ reactant_smiles  │                5 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ reagent_smiles   │                6 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ solvent_smiles   │                7 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ catalyst_smiles  │                8 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ num_reactants    │                9 │ INTEGER   │ YES         │ NULL           │
│ src_ord    │ num_reagents     │               10 │ INTEGER   │ YES         │ NULL           │
│ src_ord    │ num_solvents     │               11 │ INTEGER   │ YES         │ NULL           │
│ src_ord    │ product_smiles   │               12 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ yield_pct        │               13 │ FLOAT     │ YES         │ NULL           │
│ src_ord    │ conversion_pct   │               14 │ FLOAT     │ YES         │ NULL           │
│ src_ord    │ num_products     │               15 │ INTEGER   │ YES         │ NULL           │
│ src_ord    │ temperature_c    │               16 │ FLOAT     │ YES         │ NULL           │
│ src_ord    │ pressure_atm     │               17 │ FLOAT     │ YES         │ NULL           │
│ src_ord    │ stirring_rpm     │               18 │ FLOAT     │ YES         │ NULL           │
│ src_ord    │ doi              │               19 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ created_by       │               20 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ publication_year │               21 │ INTEGER   │ YES         │ NULL           │
│ src_ord    │ notes_procedure  │               22 │ VARCHAR   │ YES         │ NULL           │
│ src_ord    │ notes_safety     │               23 │ VARCHAR   │ YES         │ NULL           │
├────────────┴──────────────────┴──────────────────┴───────────┴─────────────┴────────────────┤
│ 23 rows                                                                           6 columns │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
D SELECT 
        table_name,
        column_name,
        ordinal_position,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name IN (
        'src_pubchem'
    )
    ORDER BY table_name, ordinal_position;
┌─────────────┬─────────────────────┬──────────────────┬───────────┬─────────────┬────────────────┐
│ table_name  │     column_name     │ ordinal_position │ data_type │ is_nullable │ column_default │
│   varchar   │       varchar       │      int32       │  varchar  │   varchar   │    varchar     │
├─────────────┼─────────────────────┼──────────────────┼───────────┼─────────────┼────────────────┤
│ src_pubchem │ cid                 │                1 │ INTEGER   │ YES         │ NULL           │
│ src_pubchem │ smiles              │                2 │ VARCHAR   │ YES         │ NULL           │
│ src_pubchem │ iupac_name          │                3 │ VARCHAR   │ YES         │ NULL           │
│ src_pubchem │ inchi               │                4 │ VARCHAR   │ YES         │ NULL           │
│ src_pubchem │ inchikey            │                5 │ VARCHAR   │ YES         │ NULL           │
│ src_pubchem │ molecular_formula   │                6 │ VARCHAR   │ YES         │ NULL           │
│ src_pubchem │ molecular_weight    │                7 │ FLOAT     │ YES         │ NULL           │
│ src_pubchem │ exact_mass          │                8 │ DOUBLE    │ YES         │ NULL           │
│ src_pubchem │ monoisotopic_weight │                9 │ DOUBLE    │ YES         │ NULL           │
│ src_pubchem │ xlogp3              │               10 │ FLOAT     │ YES         │ NULL           │
│ src_pubchem │ hbond_acceptors     │               11 │ SMALLINT  │ YES         │ NULL           │
│ src_pubchem │ hbond_donors        │               12 │ SMALLINT  │ YES         │ NULL           │
│ src_pubchem │ rotatable_bonds     │               13 │ SMALLINT  │ YES         │ NULL           │
│ src_pubchem │ tpsa                │               14 │ FLOAT     │ YES         │ NULL           │
│ src_pubchem │ total_charge        │               15 │ SMALLINT  │ YES         │ NULL           │
│ src_pubchem │ heavy_atom_count    │               16 │ SMALLINT  │ YES         │ NULL           │
│ src_pubchem │ complexity          │               17 │ FLOAT     │ YES         │ NULL           │
│ src_pubchem │ source_file         │               18 │ VARCHAR   │ YES         │ NULL           │
├─────────────┴─────────────────────┴──────────────────┴───────────┴─────────────┴────────────────┤
│ 18 rows                                                                               6 columns │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
D 