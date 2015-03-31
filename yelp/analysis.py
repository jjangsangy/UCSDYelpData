import json

import pandas as pd
import numpy as np

__all__ = ['to_df']

def to_df(data, index='business_id'):

    df = pd.DataFrame(json.loads(i) for i in open(data).readlines())
    df.set_index(index, inplace=True)

    return df.applymap(lambda x: np.nan if any(x==y for y in ['', {}, []]) else x)
