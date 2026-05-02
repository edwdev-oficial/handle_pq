import pandas as pd

from handle_pq.utils import (
    handle_json
)

def get(df):
    df_normal_itens = handle_json.read_json('normal_itens')
    return pd.merge(
        df,
        df_normal_itens,
        on=['Descrição'],
        how='left'
    )