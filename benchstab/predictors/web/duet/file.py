from typing import Dict

import pandas as pd

from .base import _DUET


class DUETPdbFile(_DUET):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'wild': row['identifier'].to_octet_stream(),
            'pdb_code': '',
            'mutation': self.prepare_mutation(row),
            'chain': row['chain'],
            'run': self.run_type,
            'mutation_sys': '',
            'chain_sys': ''
        }
