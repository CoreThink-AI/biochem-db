# Corethink sprint plan week 12of52

- akhil git@github.com:corethink-ai/zydus-reasoner
- hobson git@github.com:corethink-ai/biochem-db

### Hobson

1. [X] experiment-1 branch on biochem-db
2. [X] in eval.py fix pubchempy api calls that return objects that can't be serialized; use puchem API directly with requests with header: "accept: application/json"
3. [X] add make_serializable() to eval.py
4. [X] ~~in eval.py create function to output formatted NL markdown report of prompt-response pairs for CID 10297 and share with Akhil on slack~~
5. [ ] P-value for accuracy change in markdown report
6. [ ] try to run Akhil's experiment-1 code for a small set of molecules (need AWS keys; and LLM key though openrouter will probably work)
7. [X] manually add more compound key-pairs to editdistance calculation
8. [X] improve automatic pairing of dict keys between pubchem json and generated json from zydus-reasoner LLM response schema
9. [ ] add normalization of smiles to eval.py
1. [X] (with akhil?) add NxN edit distance metric on reactants, finding pairing between two lists and ignoring others in accuracy/error score

1. find Manufacturing section on pubchem for 10297 and add function in eval.py function to retrieve it
2. include manufacturing text for all 62 CIDs in `report.json` files in CID folders

### Akhil

1. document what you've done as experiment-1 and run evaluation report on all 62 CIDs and create summary statistics report that we can rerun after every experiment
2. iterate on the prompt using a small number of CIDs and a small/fast LLM, reviewing the stats each time you try something
3. phrase extractor graphical annotation app for chemical names, starting with 1000 names and expanding to see how many are practical

#### 1. experiment-1 report

- [X] `data/experiment-1/README.md` Summary of this experiment: beam_width, max_depth, llm_model, an example CoT (responses) and accuracy report for CID 10927, summary of the prompt
- [X] copy and archive the 62 compound prompt+response files for the 2 prompt templates, the ORD reaction pathway subgraphs as json dictionaries in the `CID_####/` folders, then never touch that folder again
- [X] `data/experiment-1/README.md` Notes to yourself about key fixes/bugs/changes/improvements you needed to do to get it working or modularize/parameterize the code
- [X] `git clone git@github.com:corethink/biochem-db` , `uv venv -p 3.12`, `source .venv/bin/activate`, `checkout main -b experiment-1`, `uv pip install -e .` (and document whatever steps worked for you in the `README.md` file
- [X] (Hobson also did this and posted to slack) create function `compute_stats` to compute descriptive statistics on `report['differences']` that is output by ``evaluate(None)`` (like `pandas.DataFrame.describe`) on the eval report json files by adding a function in `biochem-db/src/biochem/eval.py`

- [-] merge your `eval.describe()` into main biochem-db

#### 2. experiment-2

- [X] json in prompt
- [X] waiting for 72 chemicals to complete
- [X] run eval.py on experiment-2 data
- [X] review summary.json and maybe a few _ files
- [X] generate markdown - pending(Akhil)

#### 3. experiment-3

- [X] single-prompt reasoning CoT: f"Here is a summary of the record for CID {cid} from PubChem: named {name}, SMILES {smiles}, inchi {inchi}."
- [X] Adjust the model to `gpt-oss-120B ` or  any close to 5.1 in size & free utilization
- [X] single number metric for performance/accuracy in markdown report
  weighted averages : smiles / 40%, inchi /30%, molecular formula/20%, molecular weight/10%

#### 4. experiment-4

- [ ] Adjust the promts based on the reactions order - split into smaller sections and capture the promtpt
- [ ] Here is the complete json record from ORD for the chemical reaction that we need to use to synthesize this chemical compound: CID {cid} {name}."
- [ ] retrieve all ORD information about each reaction in a workflow for a given chemical product (drug)
- [ ] put one reaction's information in the prompt (including reactants, product, and any conditions like temperature)
- [ ] create `experiment-2` data folder and git branch to change python code to json within the cot prompting run the prompting on 10927.
- [ ] create `experiment-2` branch and folder on the zydus-reasoner repo

- review the
- Eliminate first prompt to compute chemical name and instead provide the names and synonyms from pubchem
- convert recommended ORD reaction pathway to json within prompt at appropriate point in reasoning workflow
- to a single recommended pathway and create a natural language template for displaying it for the LLM prompting and yourself, if you want to include dictionaries or lists

- [ ] Akhil: in eval.py match reactants in two lists M and N length with MxN editdistance calculation
