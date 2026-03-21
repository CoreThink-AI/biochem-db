from biochem.constants import CID_DIR
from biochem.db import select_df
from editdistance import distance
from pathlib import Path
import json
import re




def evaluate(cid=10297, with_ord=None):
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
    truth = df.iloc[0].to_dict()
    report = {}
    m = r['molecule']
    for k in ['inchi']:
        report[k] = distance(truth[k], m[k])
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

