""" Directly queries pubchem API rather (using `src/biochem/pubchem` than local PostgreSQL database (using `src/biochem/db.py`) so that anyone can use it """ 
from biochem.constants import CID_DIR
from collections import abc
import json
import logging
import re
import requests
from pathlib import Path
import pubchempy as pc
import pandas as pd
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance as normalized_distance
# TODO: Use https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest#section=URL-based-API to get molecule data in serializable dictionaries rather than unserializable pubchempy objects


CRE_CAPITAL_CHAR = re.compile("[A-Z]")
log = logging.getLogger()


def get_compound_dict_pubchempy(cid):
    """ FIXME: use HTTP REST instead of pubchempy used here Query PubChem API to retrieve compound record as a dictionary """
    compound = pc.Compound.from_cid(cid)
    compound_dict = {k: v  for (k, v) in compound.to_dict().items() if k in ['_record'] or not k.startswith('_')}
    # compound_dict.update({pubchem2reasoner_dict.get(k, k): getattr(compound, k) for k in dir(compound) if not k.startswith('_')})
    # compound_dict['_record'] = compound._record
    return compound_dict


# def get_compound_dict(cid):
#     """ Use HTTP REST to retrieve compound record as a serializable dictionary """
#     compound = pc.Compound.from_cid(cid)
#     compound_dict = {k: getattr(compound, k) for k in dir(compound) if k in ['_record'] or not k.startswith('_')}
#     # compound_dict.update({pubchem2reasoner_dict.get(k, k): getattr(compound, k) for k in dir(compound) if not k.startswith('_')})
#     compound_dict['_record'] = compound._record
#     return compound_dict


def make_serializable(obj, force=False, depth=9):
    """ recursively coerce Mapping to dict, GeneratorType to list, date/time to isoformat str """
    # TODO: use dir(obj) to recurse deeper until you reach non-container objects
    if not depth:
        return obj
    if isinstance(obj, abc.Mapping):
        return {k: make_serializable(v) for (k, v) in dict(obj).items() if not callable(v)}
    if isinstance(obj, (GeneratorType, np.ndarray)):
        return [make_serializable(v) for v in obj if not callable(v)]
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if isinstance(obj, (dt.datetime, dt.date)):
        return obj.isoformat()
    if isinstance(
            obj,
            (bool, str, int, float, dict, list, tuple, NoneType)):
        return obj
    if force:
        return str(obj)
    return obj

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


def get_cid_path_ints(base_dir=CID_DIR):
    return [int(p.name.split('_')[-1]) for p in Path(base_dir).glob('CID_*')]


def dict_edit_distances(molecule_guess, pubchem_molecule):
    # zip(dir(pubchempy.Compound), response['molecule']))
    map_schema_reasoner2pubchem = {
        'name': 'name',
        'molecularWeight': 'molecular_weight',
        'smiles': 'connectivity_smiles',
        'yield': 'estimated_yield',
        # 'smiles': 'isomeric_smiles',
    }
    for k in molecule_guess:
        map_schema_reasoner2pubchem[k] = camelcase_to_snake_case(k)
        map_schema_reasoner2pubchem[homogenize(k)] = camelcase_to_snake_case(k)
    
    distances = {}
    annotations ={}
    for k, guess in molecule_guess.items():
        if k.startswith('_') and k not in ['_record']:
            continue
        k_pubchem = map_schema_reasoner2pubchem[k]
        if not k_pubchem in pubchem_molecule:
            continue
        truth = pubchem_molecule[k_pubchem]
        distances[k_pubchem] = normalized_distance(str(truth), str(guess))
        annotations[k + "_normalized_edit_distance"] = distances[k_pubchem]
        annotations[k + " "] = str(guess)
        annotations[k + '_'] = truth  # record the truth in the reasoner response dict
    molecule_guess.update(annotations)
    report = dict(
        distances={k: distances[k] for k in sorted(distances.keys())},
        molecule_guess={k: molecule_guess[k] for k in sorted(molecule_guess.keys())},
        annotations=annotations,
    )
    return report


def print_report_summary(report, with_ord=None):
    # print(f'== {cid} == {report["pubchem_report"]['connectivity_smiles']}' + '='*80)
    cid = report['pubchem_report']['cid']
    # print(">>> report['pubchem_report']['cid'])")
    # print(cid)
    print(f'#### `evaluate({cid}, with_ord={with_ord})["annotations"]`')
    print('```json')
    print(json.dumps(report['annotations'], indent=4))
    print('```')
    summary = report.get('summary')
    if summary:
        print(f'#### `evaluate({cid}, with_ord={with_ord})["summary"]`')
        print('```json')
        print(json.dumps(summary, indent=4))
        print('```')
    print()


def evaluate(cid=10297, with_ord=None):
    if cid is None:
        return evaluate(cid=get_cid_path_ints(), with_ord=with_ord)
    if isinstance(cid, (list, tuple)):
        reports = []
        if with_ord is None or with_ord == 'both':
            with_ord = (False, True)
        if not isinstance(with_ord, tuple):
            with_ord = (with_ord,)
        for i in cid:
            for wo in with_ord:
                try:
                    report = evaluate(cid=int(i), with_ord=wo)
                except Exception as err:
                    log.error(f'{err}')
                reports.append(report)  
            a = reports[-2]['distances']
            b = reports[-1]['distances']
            edit_distance_changes = {k: (b[k] - a[k]) for k in a}
            reports[-1]['edit_distance_changes'] = edit_distance_changes
            summary = dict(cid=i, edit_distance_changes=edit_distance_changes, annotations=reports[-1]['annotations'])
            reports[-1]['summary'] = summary
            summary_path =  (CID_DIR / f'CID_{i}') / 'base_reasoner+ord.summary.json'
            with open(summary_path, 'wt') as fout:
                json.dump(summary, fout, indent=4)
        return reports

    reasoning_path = (CID_DIR / f'CID_{cid}' / 'base_reasoner.json')
    if with_ord:
        reasoning_path =  reasoning_path.parent / 'base_reasoner+ord.json'
    reasoning = json.load(open(reasoning_path))
    cot = reasoning['response']
    if cid is None:
        cid = reasoning['cid']
    cid = int(cid)

    compound_dict = get_compound_dict_pubchempy(cid=cid)
    report = dict_edit_distances(cot['molecule'], compound_dict)
    report['pubchem_report'] = compound_dict
    report['cot'] = {k: cot[k] for k in sorted(cot)}
    report['cot']['prompts'] = prompts = [{k: p[k] for k in sorted(p)} for p in report['cot']['prompts']]
    responses = []
    report['reasoner_response'] = json.loads(prompts[-1]['response'])
    final_response = json.loads(report['cot']['prompts'][-1]['response'])
    # print(json.dumps(report, indent=4))
    if with_ord:
        print_report_summary(report, with_ord=with_ord)
    with open(Path(reasoning_path).with_suffix('.report.json'), 'wt') as fout:
        json.dump(report, fout, indent=4)
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
    reports = evaluate(None)
    changes = {r['summary']['cid']: r['summary']['edit_distance_changes'] for r in reports if 'summary' in r}
    df = pd.DataFrame(changes).T
    with open(CID_DIR / f'evaluation_report_{len(reports)/2}_cids.json', 'wt') as fout:
        json.dump(reports, fout, indent=4)
    with open(CID_DIR / f'edit_distance_changes_{len(df)}_cids.csv', 'wt') as fout:
        df.to_csv(fout)
    print(df.describe())



    
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

