"""
JSON encoder that is able to serialize numpy scalars.
"""

import json
import numpy as np


class NumpyJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that is able to serialize numpy scalars.
    """

    def default(self, o):
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.integer):
            return int(o)
        return json.JSONEncoder.default(self, o)
