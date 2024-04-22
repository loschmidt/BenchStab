from typing import Dict

import pandas as pd

from .base import _DDGun


class DDGunPdbFile(_DDGun):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'db': self._db,
            'structure': '',
            'spdb': '',
            'pdbid': '',
            'pdbfile': row['identifier'].to_octet_stream(),
            'chain': row['chain'],
            'seqs': '',
            'seqfile': '',
            'vars': self.prepare_mutation(row),
            'email': ''
        }
