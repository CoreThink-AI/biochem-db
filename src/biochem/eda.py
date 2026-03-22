from pubchem.etl import read_pubchem_csv


def find_names(df=None, verbose=False):
    if df is None:
        df = read_pubchem_csv()
    df.drop_duplicates(subset=None, keep='first', inplace=True, ignore_index=False)
    if verbose:
        print(df['name'].nunique())
        print(df['name'].count())
        print((df['name'].str.len() == 0).sum())
        counts = df['name'].value_counts()
        # print(counts)
        print(counts[counts > 1])
    name_columns = [c for c in df.columns if 'name' in c or 'syn' in c]
    print(name_columns)
    names = df['name synonyms iupac_name'.split()]
    # there are multiple primary names

    for c, sep in dict(name=';', synonyms='|').items():
        names[c] = names[c].str.split(sep)
    return df, names




def explore_names(names, verbose=False):
    if verbose:
        print(names[(names['name'].str.len() > 100) | (names['synonyms'].str.len() > 100)].sample(100))
    


    if verbose:
        count_names = names['name'].str.len()
        print(count_names.describe())
        print('max', count_names.max())
        count_synonyms = names['synonyms'].str.len()
        print(count_synonyms.describe())
    return names


def names_as_rowwise_dicts(names):
    for i, row in names.iterrows():
        names_dicts[i] = {}
        for c in 'name synonyms'.split():
            names_dicts[i].update({f'{c.rstrip("s")}_{k}': s for k, s in enumerate(row[c])})


def map_names_to_cid(names_dict):
    return names
    # df = {}
    # for c in 'name synonyms'.split():
    #     for i, row in names[c].items():
    #         colname = f'{c.rstrip("s")}_{}'
    #         df.get(colname + str(i), {})
    #         .update({f'{c.rstrip("s")}_{k}': s for k, s in enumerate(row[c])})

    