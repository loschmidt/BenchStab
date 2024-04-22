from typing import Dict

import pandas as pd

from .base import _SRide


class SRidePdbFile(_SRide):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return dict(
            {'chain': row['chain'], 'pdbid': '', 'pdbfile': row['identifier'].to_octet_stream()},
            **self.config
        )
