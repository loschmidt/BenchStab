import pandas as pd

from benchstab.utils.structure import File
from .base import _SDM


class SDMPdbID(_SDM):
    def prepare_payload(self, row: pd.Series):
        return {
            'wild': '',
            'pdb_code': row['identifier'].id,
            'mutation_list': File(
                self.prepare_mutation(row), 'mutation.txt'
            ).to_octet_stream(),
            'pred_type': self.prediction_type
        }
