""" Directly queries pubchem API rather (using `src/biochem/pubchem` than local PostgreSQL database (using `src/biochem/db.py`) so that anyone can use it """ 
from biochem.constants import ZYDUS_DIR
from collections import abc
import json
import logging
import re
import requests
from scipy import stats
import time
from pathlib import Path
import pubchempy as pc
import pandas as pd
from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance as normalized_distance
from pyxdameraulevenshtein import damerau_levenshtein_distance as edit_distance
from pyxdameraulevenshtein import damerau_levenshtein_distance_seqs as edit_distance_seqs
# TODO: Use https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest#section=URL-based-API to get molecule data in serializable dictionaries rather than unserializable pubchempy objects


CRE_CAPITAL_CHAR = re.compile("[A-Z]")
log = logging.getLogger()


def get_compound_dict_pubchempy(cid, max_retries=5, initial_wait=1):
    """ Query PubChem API to retrieve compound record as a dictionary with retry logic for 503 errors """
    wait_time = initial_wait
    
    for attempt in range(max_retries):
        try:
            compound = pc.Compound.from_cid(cid)
            compound_dict = {k: v  for (k, v) in compound.to_dict().items() if k in ['_record'] or not k.startswith('_')}
            return compound_dict
        except pc.ServerBusyError as e:
            if attempt < max_retries - 1:
                log.warning(f"PubChem ServerBusy for CID {cid}, attempt {attempt + 1}/{max_retries}. Waiting {wait_time}s...")
                time.sleep(wait_time)
                wait_time *= 2  # Exponential backoff
            else:
                log.error(f"PubChem ServerBusy for CID {cid} after {max_retries} attempts")
                raise
        except Exception as e:
            log.error(f"Error fetching CID {cid}: {e}")
            raise
    
    return None


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


def get_cid_path_ints(base_dir=ZYDUS_DIR):
    return [int(p.name.split('_')[-1]) for p in Path(base_dir).glob('CID_*')]


def pairup(a, b, metric=edit_distance, max_distance=None):
    # a = [x.lower() for x in report['molecule_guess'].keys()]
    # b = [x.lower() for x in report['pubchem_report'].keys()]
    A = a
    a = [x.lower() for x in A]
    b = [x.lower() for x in B]
    d = pd.DataFrame(pairwise_distances(a, b, metric=metric))
    df = pd.DataFrame(d.values, columns=B, index=A)

    best = {}
    for colnum, col in enumerate(df.columns):
        rownum = df[col].argmin()
        # print(round(df.values[rownum][colnum],2), colnum, col, rownum, df.index.values[rownum])
        best[col] = dict(dist=round(df.values[rownum][colnum],2), colnum=colnum, rownum=rownum, rowlabel=df.index.values[rownum])
    best = pd.DataFrame(best).T
    return best.sort_values('dist')[['dist', 'rowlabel']]


def pair_closest(a, b, with_index=None, with_distance=None, lower=None, max_distance=None):
    """ Create dictionary of closest matches between elements of a and elements of b

    >>> pair_closest(list('ABC'), list('BC'))
    {'A': 'B', 'B': 'B', 'C': 'C'}
    >>> pair_closest(list('ABC'), list('BC'), max_distance=0)
    {'A': None, 'B': 'B', 'C': 'C'}

    >>> seq = 'Goodbye moon , hello world !'.split()
    >>> pair_closest('Hell yea !'.split(), seq)
    {'Hell': 'hello', 'yea': '!', '!': '!'}
    >>> pair_closest('Hell yea !'.split(), seq, lower=True)
    {'Hell': 'hello', 'yea': '!', '!': '!'}
    >>> pair_closest('Hell yea !'.split(), seq, lower=False)
    {'Hell': 'hello', 'yea': '!', '!': '!'}
    >>> pair_closest('HELL YES !'.split(), seq, lower=False)
    {'HELL': '!', 'YES': '!', '!': '!'}
    >>> pair_closest('HELL YES !'.split(), seq, lower=False, max_distance=1)
    {'HELL': None, 'YES': None, '!': '!'}
    >>> pair_closest('HELL YES !'.split(), seq, lower=str.lower, max_distance=1)
    {'HELL': 'hello', 'YES': None, '!': '!'}
    >>> pair_closest('HELL YES !'.split(), seq, lower=True, with_distance=True, max_distance=1)
    {'HELL': {'value': 'hello', 'distance': 1}, 'YES': None, '!': {'value': '!', 'distance': 0}}
    >>> pair_closest('HELL YES !'.split(), seq, lower=True, with_index=True, with_distance=True)
    {'HELL': {'value': 'hello', 'index': 3, 'distance': 1}, 'YES': {'value': '!', 'index': 5, 'distance': 3}, '!': {'value': '!', 'index': 5, 'distance': 0}}
    """
    return {x: get_closest(x, b, with_index=with_index, with_distance=with_distance, lower=lower, max_distance=max_distance) for x in a}


def get_closest(a, seq, max_distance=None, with_index=None, with_distance=None, lower=str.lower):
    """ Find the closest edit distance match for string a in sequence of strings seq

    >>> seq = '! hello world ?'.split()
    >>> get_closest('WORLD', seq, with_index=True, lower=False, max_distance=1)
    >>> get_closest('WORLD', seq, with_index=True, with_distance=True, max_distance=None)
    {'value': 'world', 'index': 2, 'distance': 0}
    >>> get_closest('WORLD', seq, with_index=True, with_distance=True, lower=False, max_distance=None)
    {'value': '!', 'index': 0, 'distance': 5}
    >>> get_closest('WORLD', seq, with_index=True, with_distance=True, lower=True, max_distance=None)
    {'value': 'world', 'index': 2, 'distance': 0}
    """
    if max_distance is None:
        max_distance = len(a) + 1
    A = a
    if lower:
        if not callable(lower):
            lower = str.lower
        a = lower(A)
    seq_lowered = list(seq)
    if lower:
        seq_lowered = [lower(x) for x in seq]

    """
    >>> damerau_levenshtein_distance_seqs('Sjöstedt', ['Sjöstedt', 'Sjostedt', 'Söstedt', 'Sjöedt'])
    [0, 1, 1, 2]
    """
    ans = sorted(zip(
        edit_distance_seqs(
            a,
            seq_lowered,
            max_distance=max_distance
            ),
        seq, range(len(seq)))
    )
    ans = [x for x in ans if x[0] <= max_distance]
    if len(ans):
        value = seq[ans[0][-1]]
        d = dict(value=value)
        if with_index:
            d['index'] = ans[0][-1]
        if with_distance:
            d['distance'] = ans[0][0]
        if len(d) == 1:
            return d['value']
        return d
    return None 


def dict_value_edit_distances(molecule_guess, pubchem_molecule, distance_metric=edit_distance):
    # zip(dir(pubchempy.Compound), response['molecule']))
    map_schema_reasoner2pubchem = {}
    for k in molecule_guess:
        map_schema_reasoner2pubchem[k] = k
    #     map_schema_reasoner2pubchem[k] = camelcase_to_snake_case(k)
    #     map_schema_reasoner2pubchem[homogenize(k)] = camelcase_to_snake_case(k)


    pairs = pair_closest(
        list(molecule_guess.keys()),
        list(pubchem_molecule.keys()),
        max_distance=2,
        lower=homogenize)
    pairs = {k: v for k, v in pairs.items() if v}
    map_schema_reasoner2pubchem.update(pairs)

    # for k in molecule_guess:
    #     map_schema_reasoner2pubchem[k] = camelcase_to_snake_case(k)
    #     map_schema_reasoner2pubchem[homogenize(k)] = camelcase_to_snake_case(k)

    map_schema_reasoner2pubchem.update({
        # 'name': 'name',
        'name': 'iupac_name',
        'molecularWeight': 'molecular_weight',
        'smiles': 'connectivity_smiles',
        'yield': 'estimated_yield',
        # 'smiles': 'isomeric_smiles',
    })
    # if 'id' in map_schema_reasoner2pubchem:
    #     del map_schema_reasoner2pubchem['id']
    distances = {}
    annotations ={}
    for k, guess in molecule_guess.items():
        if k.startswith('_') and k not in ['_record']:
            continue
        if k.endswith('_'):
            continue
        k_pubchem = map_schema_reasoner2pubchem[k]
        if not k_pubchem in pubchem_molecule or k_pubchem.endswith('_'):
            continue
        truth = pubchem_molecule[k_pubchem]
        distances[k_pubchem] = distance_metric(str(truth), str(guess))
        # annotations[k + "_normalized_edit_distance"] = distances[k_pubchem]
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


def evaluate(cid=10297, with_ord=None, experiment_path=ZYDUS_DIR / 'experiment-3'):
    if experiment_path is None:
        raise NotImplementedError("return all df, report pairs for all experiments")
    if cid is None:
        return evaluate(cid=get_cid_path_ints(), with_ord=with_ord)
    if isinstance(experiment_path, int):
        experiment_path = ZYDUS_DIR / f'experiment-{experiment_path}'
    if not isinstance(experiment_path, Path):
        raise NotImplementedError("run evaluate() on a list of `experiment_path`s (directories)")

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
                    reports.append(report) 
                except Exception as err:
                    log.error(err)
                    raise(err)
            a = reports[-2]['distances']
            b = reports[-1]['distances']
            edit_distance_changes = {k: (b[k] - a[k]) for k in a}
            reports[-1]['edit_distance_changes'] = edit_distance_changes
            summary = dict(cid=i, edit_distance_changes=edit_distance_changes, annotations=reports[-1]['annotations'])
            reports[-1]['summary'] = summary
            summary_path =  (experiment_path / f'CID_{i}') / 'base_reasoner+ord.summary.json'
            with open(summary_path, 'wt') as fout:
                json.dump(summary, fout, indent=4)
        return reports

    reasoning_path = (experiment_path / f'CID_{cid}' / 'base_reasoner.json')
    if with_ord:
        reasoning_path =  reasoning_path.parent / 'base_reasoner+ord.json'
    reasoning = json.load(open(reasoning_path))
    cot = reasoning['response']
    if cid is None:
        cid = reasoning['cid']
    cid = int(cid)

    compound_dict = get_compound_dict_pubchempy(cid=cid)
    report = dict_value_edit_distances(cot['molecule'], compound_dict)
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


def get_experiment_paths(experiment_number=None, zydus_dir=ZYDUS_DIR):
    """ Get sorted list of absolute paths to experiment-1 ... experiment-N directories 

    >>> get_experiment_paths()
    [PosixPath('...reasoner/experiment-1'),
     PosixPath('...reasoner/experiment-2'),
     PosixPath('...reasoner/experiment-3')]
    """
    assert zydus_dir.is_dir(), "zydus_dir must be a valid path to a directory"
    paths = []
    for p in zydus_dir.glob('experiment*'):
        if not p.is_dir():
            continue
        match = re.match(r'^experiment[-]?([0-9]+)$', p.name)
        if match:
            if experiment_number is None or match.groups()[-1] == str(experiment_number):
                paths.append(p)
    return sorted(paths)


def get_df_reports(experiment_number=None, zydus_dir=ZYDUS_DIR):
    paths = get_experiment_paths(experiment_number=experiment_number, zydus_dir=zydus_dir)
    reports_dict = {}
    for p in paths:
        reports = evaluate(None)
        changes = {r['summary']['cid']: r['summary']['edit_distance_changes'] for r in reports if 'summary' in r}
        df = pd.DataFrame(changes).T
        reports_dict[p.name] = dict(df=df, reports=reports)
    return reports_dict


def generate_markdown_report(experiment_number=1):
    df, reports = get_experiment_reports(experiment_number)
    markdown = []
    markdown.append(f"# Evaluation Report: {experiment_name}")
    markdown.append("")
    markdown.append(f"**Total CIDs Evaluated:** {len(df)}")
    markdown.append(f"**Total Reports Generated:** {len(reports)}")
    markdown.append("")
    
    distance_improvements = df.mean()    
    mean_distance_improvement = distance_improvements.mean()

    markdown.append("## Overall Performance Score")
    markdown.append("")
    markdown.append(f"### {mean_distance_improvement:.2f}")
    markdown.append("")
    markdown.append("")
    
    markdown.append("## Statistical Summary")
    markdown.append("")
    markdown.append("Edit distance changes (with ORD vs without ORD):")
    markdown.append("")
    markdown.append("```")
    markdown.append(df.describe().to_string())
    markdown.append("```")
    markdown.append("")
    
    markdown.append("### Mean Edit Distance Changes and P-Values")
    markdown.append("")
    markdown.append("| Metric | Mean Change | P-Value |")
    markdown.append("|--------|-------------|---------|")
    
    for metric in means.index:
        if metric in df.columns:
            mean_val = means[metric]
            t_stat, p_value = stats.ttest_1samp(df[metric].dropna(), 0)
            markdown.append(f"| {metric} | {mean_val:.6f} | {p_value:.4f} |")
    markdown.append("")
    
    markdown.append("## Individual CID Summaries")
    markdown.append("")
    
    for report in reports:
        if 'summary' not in report:
            continue
        summary = report['summary']
        cid = summary['cid']
        markdown.append(f"### CID {cid}")
        markdown.append("")
        
        markdown.append("**Edit Distance Changes:**")
        markdown.append("")
        markdown.append("| Metric | Change |")
        markdown.append("|--------|--------|")
        for metric, value in summary['edit_distance_changes'].items():
            markdown.append(f"| {metric} | {value:.6f} |")
        markdown.append("")
        
        if 'annotations' in summary:
            markdown.append("**Key Annotations:**")
            markdown.append("")
            annotations = summary['annotations']
            for key in ['smiles_normalized_edit_distance', 'inchi_normalized_edit_distance', 
                       'molecular_formula_normalized_edit_distance', 'molecular_weight_normalized_edit_distance']:
                if key in annotations:
                    markdown.append(f"- **{key}**: {annotations[key]}")
            markdown.append("")
    
    return "\n".join(markdown)


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
    experiment_number = -1  # 'last' | 'all'
    if sys.argv[1:]:
        experiment_number = int(sys.argv[1])
    paths = get_experiment_paths(experiment_number)
    experiment_name, experiment_path = None, None
    if not experiment_number:
        raise RuntimeError(f'Invalid experiment number: {experiment_number}')
    experiment_path = ZYDUS_DIR / f'experiment-{experiment_number}'
    experiment_name = experiment_path.name        
    if experiment_number < 0:
        experiment_path = paths[experiment_number]
        experiment_name = experiment_path.name
    
    reports, df = evaluate(experiment_path=experiment_path)
    with open(ZYDUS_DIR / f'evaluation_report_{len(reports)/2}_cids.json', 'wt') as fout:
        json.dump(reports, fout, indent=4)
    with open(ZYDUS_DIR / f'edit_distance_changes_{len(df)}_cids.csv', 'wt') as fout:
        df.to_csv(fout)
    
    markdown_content = generate_markdown_report(df, reports, experiment_name)
    markdown_path = ZYDUS_DIR / f'evaluation_report_{experiment_name}_{len(df)}_cids.md'
    with open(markdown_path, 'wt') as fout:
        fout.write(markdown_content)
    
    print(f"\n{'='*80}")
    print(f"Evaluation complete for {experiment_name}")
    print(f"{'='*80}")
    print(df.describe())
    print(f"\nMarkdown report saved to: {markdown_path}")



    
    # ZYDUS_DIRs = list(ZYDUS_DIR.glob('CID_1029*'))
    # pairs = []
    # for ZYDUS_DIR in ZYDUS_DIRs:
    #     pairs.append(( 
    #         json.load(open(ZYDUS_DIR / 'base_reasoner.json')),
    #         json.load(open(ZYDUS_DIR / 'base_reasoner+ord.json'))
    #         ))
    #     pairs[-1][0]['cid'] = int(ZYDUS_DIR.name.split('_')[-1])
    # evals = []
    # for p in pairs:
    #     evals.append(evaluate(p[0]), evaluate(p[1]))

