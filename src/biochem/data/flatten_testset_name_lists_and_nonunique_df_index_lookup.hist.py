cd src
cd biochem_db/data/
ls -hal
import json
json.load(open('testset_name_lists.json'))
names = _
names['names']
names['name']
flattened = []
for k, v in names.items():
    for x in v:
        # if isinstance(x, (tuple, set, list)):
        #     flattened.extend(list(x))
        if isinstance(x, str):
            x = [x]
        flattened.extend(list(x))
        if not isinstance(x, list):
            print(type(x), str(x)[:20])
flattened
flattened = []
for k, v in names.items():
    print(k, type(v))
    for x in v:
        # if isinstance(x, (tuple, set, list)):
        #     flattened.extend(list(x))
        if isinstance(x, str):
            x = [x]
        flattened.extend(list(x))
        if not isinstance(x, list):
            print(type(x), str(x)[:20])
flattened = []
for k, v in names.items():
    print(k, type(v))
    for i, x in v.items():
        # if isinstance(x, (tuple, set, list)):
        #     flattened.extend(list(x))
        if not isinstance(x, list):
            print(type(x), str(x)[:20])
        if isinstance(x, str):
            x = [(x, i)]
        flattened.extend(list(zip(x, (i for k in range(1_000_000)))))
flattened
json.dump(flattened, open('testset_name_cid_pairs.json', 'w'))
df = pd.DataFrame(flattened)
import pandas as pd
df = pd.DataFrame(flattened)
df
df.columns = 'name cid'.split()
df.to_csv('filtered_has_routes_names.csv')
df['name'].nunique() / len(df['name']

df
df['name'].nunique() / len(df['name'])
df['name'].nunique()
len(df)
df.to_csv('testset_name_cid_pairs.csv')
df['cid'].nunique()
df.set_index('name')
df['name'].value_counts().sort_values()
dfuniq = df.set_index('name')
dfuniq['Pyridoxamine, dihydrochloride']
dfuniq.iloc['Pyridoxamine, dihydrochloride']
dfuniq.loc['Pyridoxamine, dihydrochloride']
dfuniq.loc['CHEMBL1161476']
type(dfuniq.loc['CHEMBL1161476'])
type(dfuniq.loc['Pyridoxamine, dihydrochloride'])
df.to_numpy()
type(dfuniq.loc['CHEMBL1161476'].to_numpy())
dfuniq.loc['CHEMBL1161476'].to_numpy()
dfuniq.loc['Pyridoxamine, dihydrochloride'].to_numpy()
dfuniq.loc['Pyridoxamine, dihydrochloride'].to_numpy().shape
dfuniq.loc['CHEMBL1161476'].to_numpy().shape
dfuniq.loc['CHEMBL1161476'].to_numpy().ndim
dfuniq.loc['Pyridoxamine, dihydrochloride'].to_numpy().ndim
hist -o -p -f flatten_testset_name_lists_and_nonunique_df_index_lookup.hist.ipy
dfuniq.loc['CHEMBL1161476'].to_numpy().flatten()
dfuniq.loc['Pyridoxamine, dihydrochloride'].to_numpy().flatten()
hist -o -p -f flatten_testset_name_lists_and_nonunique_df_index_lookup.hist.ipy
hist -f flatten_testset_name_lists_and_nonunique_df_index_lookup.hist.py
