import pandas as pd

from handle_pq.utils import (
    handle_json
)
from handle_pq.database.database import get_collection_normal_itens

def get(df):
    col_normal_itens = get_collection_normal_itens()
    df_normal_itens = pd.DataFrame(col_normal_itens.find().to_list())
    df_normal_itens.drop(columns=['_id'], inplace=True)
    return pd.merge(
        df,
        df_normal_itens,
        on=['Descrição'],
        how='left'
    )