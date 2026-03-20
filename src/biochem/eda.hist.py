from pubchem.etl import read_pubchem_csv

def find_names():
    df = read_pubchem_csv()
    df['name'].nunique()
    df['name'].count()
    (df['name'].str.len() == 0).sum()
    counts = df['name'].value_counts()
    print(counts[counts > 1])
    df[[c for c in df.columns if 'name' in c or 'syn' in c]]
    names = df['name synonyms iupac_name'.split()]
    return df, names


def explore_names():
    df, names = find_names()
    print(names[(names['name'].str.len() > 100) | (names['synonyms'].str.len() > 100)].sample(100))

    # there are multiple primary names
    for c, sep in dict(name=';', synonyms='|').items():
        names[c] = names[c].str.split(sep)

    count_names = names['name'].str.len()
    print(count_names.describe())
    count_names
    print('max', count_names.max())
    count_synonyms = names['synonyms'].str.len()
    print(count_synonyms.describe())
    return df, names, count_names, count_synonyms


    