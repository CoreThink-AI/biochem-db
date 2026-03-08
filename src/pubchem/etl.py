""" Load and clean dataframes from PubChem TTL or CSV files (bulk downloads from ftp or advanced search) """
import gzip
import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from psycopg2 import errors
from . import db
from .constants import ENV, DATA_DIR
from .models import CompoundSMILES as Compound
from rdflib import term, Graph
from rdflib.parser import Parser, FileInputSource
from tqdm import tqdm

con = db.CONNECTION
name = 'compound_complexity'

CSV_DIR = DATA_DIR / 'csvs'
# DF_PATH = CSV_DIR / 'sorted_PubChem_compound_Complexity__from_000_to_160.csv'
DF_PATH = CSV_DIR / 'PubChem_compound_Complexity__from_000_to_224.csv.gz'
DEFAULT_BATCH_SIZE = 20_000


# from retrosynthesis.constants import DATA_DIR
# cids = []
# for line in open(DATA_DIR / 'eval_results/filtered_has_routes.ndjson'):
#     cids.append(json.loads(line))
# df = df.sort_values('best_num_steps', ascending=False)
# df = df.reset_index(drop=True)
# df['id'] = df['cid']
# df = df.set_index('id', drop=True)
# df.to_csv('filtered_has_routes.csv')


def clean_pubchem_df(df=DF_PATH):
    if isinstance(df, (str, Path)):
        df = read_pubchem_csv(df)
    columns = [c.strip().lower() for c in df.columns]
    columns[0] = 'cid'
    df.columns = columns
    df = df.drop_duplicates()
    for c in df.columns:
        if df[c].dtype == 'object':
            df[c] = [str(x) for x in df[c].fillna('')]
    df['id'] = df['cid']
    df = df.set_index('id', drop=True)
    df = df.sort_index()
    return df

def read_pubchem_csv(path=DF_PATH, *args, dtypes=None, keep_default_na=False, index_col=0, **kwargs):
    """ Load a csv or csv.gz containing PubChem records (~38 columns)

    >>> df = pd.read_csv(DATA_DIR / 'csvs' 'PubChem_compound_Complexity__from_000_to_224.csv.gz', index_col=0)
    <ipython-input-5-097a4ed07dbd>:1: DtypeWarning: Columns (0: annotation_content, 1: data_source, 2: molecular_weight) have mixed types. Specify dtype option on import or set low_memory=False.
      df = pd.read_csv('/home/hobs/code/corethink/pubchem/src/pubchem/data/csvs/PubChem_compound_Complexity__from_000_to_224.csv.gz', index_col=0)
    >>> df.info()
    df.info()
    <class 'pandas.DataFrame'>
    Index: 11963314 entries, 1 to 177896524
    Data columns (total 38 columns):
     #   Column                              Dtype  
    ---  ------                              -----  
     0   cid                                 int64  
     1   name                                str    
     ...   
     10  linked_bioassays                    object 
     ...
     15  polar_area                          float64
     16  complexity                          int64  
     ... 
     36  annotation_type_count               int64  
     37  create_date                         int64  
    dtypes: float64(5), int64(20), object(1), str(12)
    memory usage: 3.5+ GB

    """
    if dtypes is None:
        # if csv has already been cleaned:
        dtypes = dict(
            cid = np.int64,
            name = str,
            synonyms = str,
            molecular_formula = str,
            inchi = str,
            smiles = str,
            inchikey = str,
            iupac_name = str,
            mesh_headings = str,
            annotation_content = str,
            linked_bioassays = str,
            data_source = str,
            data_source_category = str,
            tagged_by_pubchem = str,
            molecular_weight = np.float64,
            polar_area = np.float64,
            complexity = np.int64,
            xlogp = str,
            heavy_atom_count = np.int64,
            h_bond_donor_count = np.int64,
            h_bond_acceptor_count = np.int64,
            rotatable_bond_count = np.int64,
            exact_mass = np.float64,
            monoisotopic_mass = np.float64,
            charge = np.int64,
            covalent_unit_count = np.int64,
            isotopic_atom_count = np.int64,
            total_atom_stereo_count = np.int64,
            defined_atom_stereo_count = np.int64,
            undefined_atom_stereo_count = np.int64,
            total_bond_stereo_count = np.int64,
            defined_bond_stereo_count = np.int64,
            undefined_bond_stereo_count = np.int64,
            linked_pubchem_literature_count = np.int64,
            linked_pubchem_patent_count = np.int64,
            linked_pubchem_patent_family_count = np.int64,
            annotation_type_count = np.int64,
            create_date = np.int64
            )
        # if csv is unclean (raw download from PubChem)
        dtypes.update({(k.replace('_', ' '), v) for k, v in dtypes.items()})
        dtypes.update({(k.title(), v) for k, v in dtypes.items()})
        dtypes.update({(k.upper(), v) for k, v in dtypes.items()})
        dtypes.update({(k.replace(' ', ''), v) for k, v in dtypes.items()})

    df = pd.read_csv(
        path,
        *args,
        dtype=dtypes,
        keep_default_na=keep_default_na,
        index_col=index_col,
        **kwargs
        )
    return clean_pubchem_df(df)


def combine_pubchem_csvs(path_glob=CSV_DIR.glob('PubChem*.csv')):
    if path_glob is None:
        path_glob = CSV_DIR.glob('PubChem*.csv')
    #print(list(path_glob))
    dfs = []
    for p in sorted(path_glob):
        print(p)
        dfs.append(clean_pubchem_df(p))
    df = pd.concat(dfs, axis=0)

    df = df \
        .sort_values('cid') \
        .drop_duplicates() \
        .reset_index(drop=True)
    df['id'] = df['cid']
    df = df.set_index('id', drop=True)
    return df

    # if path_glob is None:
    #     path_glob = CSV_DIR.glob('PubChem*.csv')
    # #print(list(path_glob))
    # dfs = []
    # for p in path_glob:
    #     print(p)
    #     df = clean_pubchem_df(p)
    #     print(df.head().T)
    #     dfs.append(df)


def load_df_into_db(df, batch_size=DEFAULT_BATCH_SIZE, table='compound_pathways', engine=db.ENGINE):
    """ Normalize column names and types and create or overwrite database table with new data """
    total = len(df) // batch_size + 1
    # replace any existing table with first batch from csv
    df.iloc[0:batch_size].to_sql(
        name=name, con=con, if_exists='replace')
    for b in tqdm(range(1, total), total=total):
        df.iloc[b * batch_size:(b + 1) * batch_size].to_sql(
            name=name, con=con, if_exists='append')


print('CONNECTION.info', db.CONNECTION.info)


def create_table(table_class=Compound):
    table_class.metadata.create_all(db.ENGINE)


def load_batch_into_table(batch, table_class=Compound):
    sess = db.Session()

    try:
        sess.bulk_insert_mappings(mapper=table_class, mappings=batch)
        sess.commit()
    except (errors.IntegrityError, errors.UniqueViolation) as err:
        print(err)
        print(f'SKIPPING {batch[0]["cid"]}...{batch[-1]["cid"]}')
    return sess.close()


def update_table_with_batch(batch, table_class=Compound):
    sess = db.Session()
    try:
        sess.execute(update(table_class), batch)
        sess.commit()
    except (errors.IntegrityError, errors.UniqueViolation) as err:
        print(err)
        print(f'SKIPPING {batch[0]["cid"]}...{batch[-1]["cid"]}')
    return sess.close()


def normalize_name(name):
    return name.lower().replace(
        '"', '').replace(
        "'", '').replace(
        ' ', '_').replace(
        '-', '_')

def rename_table(old, new=None, table='compound'):
    if not new:
        new = normalize_table_name(old)
    sql = text(f'ALTER TABLE {table} RENAME "{old}" TO "{new}" ;'


def load_graph_into_db(graph, table_class=Compound, batch_size=1000):
    num_loaded = 0
    for batch in tqdm(yield_batches(graph, batch_size=batch_size), total=len(graph)):
        records = [tripple_to_record(t) for t in batch]
        # print(records[0], '...', records[-1])
        load_batch_into_table(records, table_class=table_class)
        num_loaded += len(records)
        print(num_loaded)
    return num_loaded


def load_graph_from_ttl(filepath):
    filepath = Path(filepath)
    parser = Parser()
    graph = Graph()
    opener = open
    if filepath.suffix == '.gz':
        opener = gzip.open
    with opener(filepath) as fin:
        rdfsource = FileInputSource(tqdm(fin))
        graph.parse(rdfsource)
    print('graph:', graph)
    print('len(graph):', len(graph), '# num nodes')
    # print('predicate:', next(iter(graph.predicates())), '# edges type')
    # print('[n for n in graph][:5]:', '\n', '\n'.join([str(n) for n in graph][:5]))
    # edge = next(iter(graph))
    # print('first edge:', edge)
    # print('   ', edge[0].split('/')[-1], edge[1].split('/')[-1], edge[2].split('/')[-1])
    return graph


def uri2id(s):
    """ TODO: create regexes for each ID prefix and format 

    >>> uri2id(' / CID 0012_345 / ')
    12345
    >>> 
    """
    s = s.strip('/').split('/')[-1].strip().strip('"').strip('"').strip()
    return s


def simplify_uris(tripple):
    """ remove the URL and retain only the "filename" information

    >>> tripple = (
    ...     term.URIRef('http://rdf.ncbi.nlm.nih.gov/pubchem/compound/CID134277473'),
    ...     term.URIRef('http://rdf.ncbi.nlm.nih.gov/pubchem/vocabulary#smiles'),
    ...     term.Literal('CC1([C@H]2CC[C@@]1(C3=NN=C(C=C23)C4=C(C=CC=C4F)F)[C@@H]5CN(CCO5)C(=O)NC6(CC6)CO)C'),
    ... )
    >>> simplify_uris(tripple)
    """
    d = dict(
        subj=uri2id(tripple[0]),
        pred=uri2id(tripple[1]),
        obj=uri2id(tripple[2]),
    )
    d['subj_type'], d['subj_value'] = re.match(r'^\s*([a-zA-Z]*)[^-0-9]*([-0-9]*)', d['subj']).groups()
    d['pred_type'], d['pred_value'] = d['pred'].split('#')
    d['obj_type'], d['obj_value'] = str(type(d['obj'])), d['obj']

    numified = {}
    for k, v in d.items():
        try:
            numified[k] = int(v)
        except ValueError:
            try:
                numified[k] = float(v)
            except ValueError:
                numified[k] = v
    return numified


def tripple_to_record(tripple):
    d = simplify_uris(tripple)
    record = {
        'id': d['subj_value'],
        'cid': d['subj_value'],
        d['pred_value']: d['obj'],
    }
    return record


def yield_batches(graph, batch_size, prefix='http://rdf.ncbi.nlm.nih.gov/pubchem/compound/CID'):
    batch = []
    for i, tripple in enumerate(graph):
        batch.append(tripple)
        if not (i + 1) % batch_size:
            yield batch
            batch = []
    yield batch


# def validate_similes(tripple):
#     for k, v in d.items():
#         if len(v) > 1:
#             print(f'{k} had {len(v)}, f'SMILES found for CID{k}')
#         elif not len(v):
#             pass
#             # print(f'NO SMILES FOUND for {k}!!!')
#         else:
#             batch.append({'id': int(k), 'cid': int(k), 'smiles': str(v[0])})
#     return batch
def load_smiles():
    total_loaded = 0
    paths = list(Path('data').glob(f'pc_compound2smiles_*.ttl.gz'))
    for i, filepath in enumerate(paths):
        print(f'Loading {i+1}/{len(paths)} TTL file: {filepath}')
        graph = load_graph_from_ttl(filepath=filepath)
        num_loaded = load_graph_into_db(graph, table_class=Compound, batch_size=DEFAULT_BATCH_SIZE)
        print(f'finished loading {num_loaded} from {filepath} for a total of {total_loaded}')
        del graph


def load_preferred_iupac_name():
    """ Internation Union of Pure and Applied Chemistry https://iupac.org/what-we-do/databases/ """
    total_loaded = 0
    paths = list(Path('data').glob(f'pc_compound2preferred_iupac_name_*.ttl.gz'))
    total_paths = len(paths)
    for i, filepath in enumerate(paths):
        print(f'Loading {i+1}/{total_paths} TTL file: {filepath}')
        graph = load_graph_from_ttl(filepath=filepath)
        num_loaded = load_graph_into_db(graph, table_class=Compound, batch_size=DEFAULT_BATCH_SIZE)
        print(f'finished loading {num_loaded} from {filepath} for a total of {total_loaded}')
        del graph



