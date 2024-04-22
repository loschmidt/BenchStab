from typing import Dict

import pandas as pd

from .base import _DDGun


class DDGunPdbID(_DDGun):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'db': self._db,
            'structure': '',
            'spdb': '',
            'pdbid': row['identifier'].id,
            'pdbfile': '',
            'chain': row['chain'],
            'seqs': '',
            'seqfile': '',
            'vars': self.prepare_mutation(row),
            'email': ''
        }
