from typing import Dict

import pandas as pd

from .base import _PremPS


class PremPSPdbFile(_PremPS):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'example': '0',
            'pdb_id': '',
            'pdb_mol': self.pdb_mol,
            'bioassembly': self.bioassembly,
            'isPl': self.is_pl,
            'pdb_file': row['identifier'].to_octet_stream()
        }
