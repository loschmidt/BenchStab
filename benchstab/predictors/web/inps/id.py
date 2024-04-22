from typing import Dict

import pandas as pd

from .base import _INPS
from benchstab.utils.structure import File


class INPSPdbID(_INPS):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.data['url'] = self._url + '/inpsSuite/default/index3D'

    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'structure': row['identifier'].to_octet_stream(),
            'mutations':  File(self.prepare_mutation(row), 'mutation.txt').to_plain_text(),
            'inps_chain': row['chain'],
            'inps3d': 'on',
            'submit': 'Submit job',
            '_formname': 'subtab/create'
        }
