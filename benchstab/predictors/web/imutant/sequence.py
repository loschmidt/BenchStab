import pandas as pd

from .base import _IMutant2, _IMutant3


class IMutant2Sequence(_IMutant2):
    def prepare_payload(self, row: pd.Series):
        return {
            'proteina': row.fasta.sequence,
            'posizione': row.fasta_mutation[1:-1],
            'newres': row.fasta_mutation[-1],
            'temp': row.temperature,
            'ph': row.ph,
            'email': '',
            'pred': self.pred,
            'submit': 'Submit'
        }


class IMutant3Sequence(_IMutant3):

    def __init__(self, data, *args, **kwargs) -> None:
        super().__init__(data, *args, **kwargs)
        self.pred_type = 'SEQ'

    def prepare_payload(self, row: pd.Series):
        return {
            'pred': self._pred,
            'qprd': self.pred_type,
            'proteina': row.fasta.sequence,
            'posizione': row.fasta_mutation[1:-1],
            'newres': row.fasta_mutation[-1],
            'temp': row.temperature,
            'ph': row.ph,
            'email': '',
            'kpred': self.kpred,
            'submit': 'Submit'
        }
