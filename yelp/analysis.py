import json
import os

from os.path import isfile

import pandas as pd
import numpy as np

__all__ = ['to_df']

def to_df(data, index='business_id'):
    nyans  = lambda x: np.nan if any(x==y for y in ['', {}, []]) else x
    stream = (json.loads(i) for i in open(data).readlines())
    return pd.DataFrame(stream).set_index(index).applymap(nyans)
