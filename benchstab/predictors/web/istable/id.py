from typing import Dict, List

import pandas as pd

from .base import _iStable


class iStablePdbID(_iStable):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.data['url'] = 'http://predictor.nchu.edu.tw/istable/indexPDB.php'
        self._table_width = '85'
        self._table_row = '5'
        self._table_data = '9'

    def format_mutation(self, data: str) -> List[str]:
        return [
            ','.join([
                data.chain,
                data.mutation[0],
                data.mutation[1:-1],
                data.mutation[1:-1]
            ]),
            data.mutation[-1]
        ]

    def prepare_payload(self, row: pd.Series) -> Dict:
        _mut = self.prepare_mutation(row)
        return {
            'pdbid': row['identifier'].id,
            'pred': _mut[0],
            'mutant': _mut[1],
            'temp': row.temperature,
            'ph': row.ph,
            'seq': ''
        }
