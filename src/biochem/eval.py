from biochem.constants import CID_DIR
from biochem.db import select_df
from editdistance import distance
from pathlib import Path
import pubchempy as pc
import json
import re
import logging

CRE_CAPITAL_CHAR = re.compile("[A-Z]")
log = logging.getLogger()


def homogenize(name):
    return name.lower().replace('-', '').replace('_', '')

def _dash_lower(m):
    return "-" + m.group(0).lower()


def underscore_lower(m):
    return "_" + m.group(0).lower()


def camelcase_to_snake_case(opt):
    """ camelCase -> camel_case  AND  PascalCase -> pascal_case"""
    return CRE_CAPITAL_CHAR.sub(underscore_lower, opt)


def get_similar(d, k):
    """ [k for k in results['response']['molecule'].keys() if 'name' in k.lower()] """
    h = homogenize(k)
    subdict = {k2: v for (k2, v) in d.items() if h in homogenize(k2)}
    s = camelcase_to_snake_case(k)
    subdict.update({k2: v for (k2, v) in d.items() if s in camelcase_to_snake_case(k2)})
    return subdict


def get_cid_paths(base_dir=CID_DIR):
    return [int(p.name.split('_')[-1]) for p in Path(base_dir).glob('CID_*')]


def evaluate(cid=10297, with_ord=None):
    if cid is None:
        cid = get_cid_paths()
    if isinstance(cid, (list, tuple)):
        reports = []
        if with_ord is None or with_ord == 'both':
            with_ord = (False, True)
        if not isinstance(with_ord, tuple):
            with_ord = (with_ord,)
        for i in get_cid_paths():
            for wo in with_ord:
                try:
                    reports.append(evaluate(cid=int(i), with_ord=wo))
                except Exception as err:
                    log.error(f'{err}')
        return reports

    reasoning =  (CID_DIR / f'CID_{cid}' / 'base_reasoner.json')
    if with_ord:
        reasoning =  reasoning.parent / 'base_reasoner+ord.json'
    if isinstance(reasoning, (Path, str)):
        reasoning = json.load(open(reasoning))
    r = reasoning['response']
    if cid is None:
        cid = reasoning['cid']
    cid = int(cid)
    df = select_df(columns=None, limit=10, id=cid)
    m_ = df.iloc[0].to_dict()
    
    truth = {'molecule': m_}
    distances = {}
    m = r['molecule']
    for k in m_:
        if k in m:
            distances[k] = distance(str(m_[k]), str(m[k]))
            r['molecule'][k+'_'] = m_[k]  # record the truth in the reasoner response dict
        if k in r:
            distances[k] = distance(str(m_[k]), str(r[k]))
            r[k+'_'] = m_[k]  # record the truth in the reasoner response dict
    report = dict(distances=distances)
    
    # zip(dir(pubchempy.Compound), response['molecule']))
    map_schema_pubchem2reasoner = [
        ('name', 'compound_name'),
        ('molecular_weight', 'molecularWeight'),
        ('smiles', 'connectivity_smiles'),
        ('smiles', 'isomeric_smiles'),
    ]
    map_schema_pubchem2reasoner += [(camelcase_to_snake_case(k), k)]
    pubchem2reasoner_dict = dict(map_schema_pubchem2reasoner) 
    # map_schema_reasoner2pubchem = [(v, k) for (k, v) in map map_schema_pubchem2reasoner]
    compound = pc.Compound.from_cid(cid)
    compound_dict = {k: getattr(compound, k) for k in dir(compound) if k in ['_record'] or not k.startswith('_')}
    compound_dict.update({pubchem2reasoner_dict.get(k, k): getattr(compound, k) for k in dir(compound) if not k.startswith('_')})
    compound_dict['_record'] = compound._record

    truth['molecule'].update(compound_dict)


    truth['pubchem'] = compound_dict
    pubchem_distances = {}
    for k in compound_dict:
        if k.startswith('_') and k not in ['_record']:
            continue
        if k in m:
            r['molecule'][k+'_'] = compound_dict[k]  # record the truth in the reasoner response dict
            pubchem_distances[k] = distance(str(compound_dict[k]), str(m[k]))
        elif k in r:
            r[k+'_'] = compound_dict[k]  # record the truth in the reasoner response dict
            pubchem_distances[k] = distance(str(compound_dict[k]), str(r[k]))
        else:
            continue
        r['molecule'][k+'_'] = compound_dict[k]

    report['pubchem_distances'] = pubchem_distances
    print(report)
    return dict(truth=truth, report=report, response=r)


if __name__ == '__main__':
    cid_dirs = list(CID_DIR.glob('CID_1029*'))
    pairs = []
    for cid_dir in cid_dirs:
        pairs.append(( 
            json.load(open(cid_dir / 'base_reasoner.json')),
            json.load(open(cid_dir / 'base_reasoner+ord.json'))
            ))
        pairs[-1][0]['cid'] = int(cid_dir.name.split('_')[-1])
    evals = []
    for p in pairs:
        evals.append(evaluate(p[0]), evaluate(p[1]))

