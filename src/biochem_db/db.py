import logging
import pandas as pd
from pubchem.constants import PG_URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, MetaData, Table, Column, ForeignKey
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import text, select
from .models import CompoundComplexity

logging.basicConfig()
logsql = logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
ENGINE = create_engine(PG_URL, echo=True)
CONNECTION = ENGINE.connect()
Session = sessionmaker(bind=ENGINE)


def as_dict(obj):
    dct = dict(obj.__dict__)
    dct.pop('_sa_instance_state')  # no hidden sqlalchemy attributes
    return dct


def automap_models(engine=ENGINE):
    """ Create db.Compound and other orm table models """
    metadata = MetaData()
    metadata.reflect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()

    models = {}
    for k in dir(Base.classes):
        if k.startswith('_'):
            continue
        name = k.title().replace('_', '')
        globals()[name] = getattr(Base.classes, k)
        models[name] = globals()[name]
    return models

def select_df():
    stmnt = select(CompoundComplexity).where(CompoundComplexity.id == "1983")

def select_df_clunky(
        table='compound_complexity',
        columns='id cid name smiles complexity synonyms'.split(),
        id=None, 
        cid=None,
        name=None,
        smiles=None,
        where='',
        limit=10_000):
    where = [where]
    if not where[0]:
        where = []
    if id:
        where += [f'id = {id}']
    if cid:
        where += [f'cid = {cid}']
    if name:
        where += [f'name = \'{name}\'']
    if smiles:
        where += [f'smiles = {smiles}']
    if not columns or '*' in columns:
        columns = ['*']
    if not where:
        where += ['id >= 0']
    with ENGINE.connect() as connection:
        table = list(
            connection.execute(
                text(
                    f'SELECT {",".join(columns)}'
                    + f' FROM {table}'
                    + f' WHERE'
                    + f' {" AND ".join([clause for clause in where if clause])}' 
                    + f' LIMIT {limit}'
                    + ' ;'
                    )
                ).all()
            )
    if '*' in columns:
        columns = range(40)
    dfsql = pd.DataFrame(table, columns=columns)
    if len(dfsql) and 'id' in dfsql.columns:
        dfsql = dfsql.set_index('id', drop=True)
    return dfsql




locals().update(automap_models())
