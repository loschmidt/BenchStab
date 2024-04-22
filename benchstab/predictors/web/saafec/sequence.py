from typing import Dict

import pandas as pd

from benchstab.utils.structure import File
from .base import _SAAFEC


class SAAFECSequence(_SAAFEC):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'proteinsequence2': '',
            'sequencefile2': row.fasta.to_octet_stream(),
            'mutationfile': File(
                self.prepare_mutation(row), "mutation.txt"
            ).to_plain_text()
        }
