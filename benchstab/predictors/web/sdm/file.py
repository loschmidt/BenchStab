import pandas as pd

from benchstab.utils.structure import File
from .base import _SDM


class SDMPdbFile(_SDM):
    def prepare_payload(self, row: pd.Series):
        return {
            'pdb_code': '',
            'wild': row['identifier'].to_octet_stream(),
            'mutation_list': File(
                self.prepare_mutation(row), 'mutation.txt'
            ).to_octet_stream(),
            'pred_type': self.prediction_type
        }
