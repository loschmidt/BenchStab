import pandas as pd

from .base import _IMutant3
from benchstab.predictors.base import PredictorFlags


class IMutant3PdbFile(_IMutant3):
    def __init__(self, data, flags: PredictorFlags = None, *args, **kwargs) -> None:
        flags = flags or PredictorFlags(
            webkit=True, group_mutations_by=['identifier', 'chain', 'mutation']
        )
        super().__init__(data, flags=flags, *args, **kwargs)
        self.pred_type = 'PDB'
        self.webkit = True

    def prepare_payload(self, row: pd.Series):
        return {
            'pred': self._pred,
            'qprd': self.pred_type,
            'proteina': '',
            'pdbfile': row['identifier'].to_octet_stream(),
            'posizione': row['mutation'][1:-1],
            'newres': row['mutation'][-1],
            'temp': row.temperature,
            'ph': row.ph,
            'email': '',
            'kpred': self.kpred,
            'submit': 'Submit'
        }
