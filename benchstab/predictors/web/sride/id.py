from typing import Dict

import pandas as pd

from .base import _SRide


class SRidePdbID(_SRide):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return dict({'chain': row['chain'], 'pdbid': row['identifier'].id}, **self.config)
