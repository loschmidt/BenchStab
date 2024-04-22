from typing import Dict

import pandas as pd

from .base import _INPS
from benchstab.utils.structure import File


class INPSSequence(_INPS):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.data['url'] = self._url + '/inpsSuite/default/index2'

    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'sequence': row.fasta.to_octet_stream(),
            'mutations':  File(self.prepare_mutation(row), 'mutation.txt').to_plain_text(),
            'inps_chain': row['chain'],
            'inps': 'on',
            'submit': 'Submit job',
            '_formname': 'subtab/create'
        }
