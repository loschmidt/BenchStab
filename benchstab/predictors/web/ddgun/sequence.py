from typing import Dict

import pandas as pd

from .base import _DDGun


class DDGunSequence(_DDGun):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pred_type = 'SEQ'

    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'db': self._db,
            'structure': '',
            'spdb': '',
            'pdbid': '',
            'pdbfile': '',
            'chain': '',
            'seqs': row.fasta.sequence,
            'seqfile': '',
            'vars': self.prepare_mutation(row),
            'email': ''
        }
