from typing import Dict

import pandas as pd

from .base import _DeepDDG


class DeepDDGPdbFile(_DeepDDG):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'identifier': row['identifier'].to_octet_stream(),
            'pdbdown': '',
            'predtype': self.pred,
            'muttype': self.mutation_type,
            'mutlist': self.prepare_mutation(row),
            'email': ""
        }
