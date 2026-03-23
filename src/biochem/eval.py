from biochem.constants import CID_DIR
# from biochem.db import select_df
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance as normalized_distance
from pathlib import Path
import pubchempy as pc
import json
import re
import logging

CRE_CAPITAL_CHAR = re.compile("[A-Z]")
log = logging.getLogger()


def get_compound_dict(cid):
    """ Query PubChem API to retrieve compound record as a dictionary """
    compound = pc.Compound.from_cid(cid)
    compound_dict = {k: getattr(compound, k) for k in dir(compound) if k in ['_record'] or not k.startswith('_')}
    # compound_dict.update({pubchem2reasoner_dict.get(k, k): getattr(compound, k) for k in dir(compound) if not k.startswith('_')})
    compound_dict['_record'] = compound._record
    return compound_dict


def get_compound_dict_from_db(cid):
    df = select_df(columns=None, limit=10, id=cid)
    return df.iloc[0].to_dict()



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


def dict_edit_distances(m, pubchem_molecule):
    # zip(dir(pubchempy.Compound), response['molecule']))
    map_schema_reasoner2pubchem = {
        'name': 'name',
        'molecularWeight': 'molecular_weight',
        'smiles': 'connectivity_smiles',
        'yield': 'estimated_yield',
        # 'smiles': 'isomeric_smiles',
    }
    for k in m:
        map_schema_reasoner2pubchem[k] = camelcase_to_snake_case(k)
        map_schema_reasoner2pubchem[homogenize(k)] = camelcase_to_snake_case(k)
    
    distances = {}
    annotations ={}
    for k, guess in m.items():
        if k.startswith('_') and k not in ['_record']:
            continue
        k_pubchem = map_schema_reasoner2pubchem[k]
        if not k_pubchem in pubchem_molecule:
            continue
        truth = pubchem_molecule[k_pubchem]
        distances[k_pubchem] = normalized_distance(str(truth), str(guess))
        annotations[k + '_'] = truth  # record the truth in the reasoner response dict
    m.update(annotations)
    report = dict(
        distances={k: distances[k] for k in sorted(distances.keys())},
        molecule={k: m[k] for k in sorted(m.keys())},
    )
    return report


# def dict_edit_distances_pubchem(m, m_):
#     for k in m_:
#         if k in m:
#             r['molecule'][k+'_'] = compound_dict[k]  # record the truth in the reasoner response dict
#             pubchem_distances[k] = distance(str(compound_dict[k]), str(m[k]))
#         elif k in r:
#             r[k+'_'] = compound_dict[k]  # record the truth in the reasoner response dict
#             pubchem_distances[k] = distance(str(compound_dict[k]), str(r[k]))
#         else:
#             continue
#         r['molecule'][k+'_'] = compound_dict[k]
#     return r



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
    cot = reasoning['response']
    if cid is None:
        cid = reasoning['cid']
    cid = int(cid)
    
    # map_schema_reasoner2pubchem = [(v, k) for (k, v) in map map_schema_pubchem2reasoner]
    compound_dict = get_compound_dict(cid=cid)
    # print(json.dumps(compound_dict, indent=4))
    report = dict_edit_distances(cot['molecule'], compound_dict)
    report['pubchem_report'] = compound_dict
    report['cot'] = {k: cot[k] for k in sorted(cot)}
    report['cot']['prompts'] = prompts = [{k: p[k] for k in sorted(p)} for p in report['cot']['prompts']]
    responses = []

    # for i, p in enumerate(prompts):
    #     print(i, type(p), len(p), p.keys())
    #     r = p['response']
    #     responses.append({k: r[k] for k in sorted(r)})
    #     # r = json.dumps(p['response'], indent=4)
    report['reasoner_response'] = json.loads(prompts[-1]['response'])
    final_response = json.loads(report['cot']['prompts'][-1]['response'])
    # print(json.dumps(report, indent=4))
    print(f'== {cid} = {report["pubchem_report"]['connectivity_smiles']}' '='*80)
    print(json.dumps(report['distances'], indent=4))
    return report


def review_cot(cid):
    results = evaluate(cid=10297)
    print(dumps(report['response']['prompts'][-1]['response'], indent=4))
    print(json.dumps(report['response']['prompts'][-1]['response'], indent=4))
    print(json.loads(report['response']['prompts'][-1]['response']))
    print(json.dumps(json.loads(report['response']['prompts'][-1]['response']), indent=4))
    report['response']['prompts'][-1].keys()
    report['response']['prompts'][-1]['user_prompt']
    smiles = ""
    print(f"=== CID {cid} == {smiles} ==" + "=" * (80 - len(smiles)))
    for i, p in enumerate(report['response']['prompts']):
        print(f"=== HUMAN PROMPT {i:2d}" + "=" * 82)
        print(p['user_prompt'])
        print(f"----- LLM response {i:2d}" + "-" * 80)
    for p in report['response']['prompts']:
        print(p['user_prompt'])



if __name__ == '__main__':
    report = evaluate(None)
    report = evaluate(None, with_ord=)
    
    # cid_dirs = list(CID_DIR.glob('CID_1029*'))
    # pairs = []
    # for cid_dir in cid_dirs:
    #     pairs.append(( 
    #         json.load(open(cid_dir / 'base_reasoner.json')),
    #         json.load(open(cid_dir / 'base_reasoner+ord.json'))
    #         ))
    #     pairs[-1][0]['cid'] = int(cid_dir.name.split('_')[-1])
    # evals = []
    # for p in pairs:
    #     evals.append(evaluate(p[0]), evaluate(p[1]))

