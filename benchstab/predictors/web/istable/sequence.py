from typing import Dict

import pandas as pd

from .base import _iStable


class iStableSequence(_iStable):
    def __init__(self, data, *args, **kwargs) -> None:
        super().__init__(data, *args, **kwargs)
        self.data['url'] = 'http://predictor.nchu.edu.tw/iStable/indexSeq.php'
        self.data.DDG = self.data.DDG.astype(str)

    def prepare_payload(self, row: pd.Series) -> Dict:
        _mut = self.prepare_mutation(row)
        return {
            'jobname': '',
            'wildtype': _mut[0],
            'position': _mut[1:-1],
            'mutant': _mut[-1],
            'temp': row.temperature,
            'ph': row.ph,
            'seq': row.fasta
        }
