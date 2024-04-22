from typing import Dict

import pandas as pd

from .base import _DeepDDG


class DeepDDGPdbID(_DeepDDG):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'identifier': '',
            'pdbdown': row['identifier'].id,
            'predtype': self.pred,
            'muttype': self.mutation_type,
            'mutlist': self.prepare_mutation(row),
            'email': ""
        }
