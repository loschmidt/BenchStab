from typing import Dict
import pandas as pd
from benchstab.predictors.base import PredictorFlags
from .base import _PONSol2

class PONSol2Sequence(_PONSol2):

    def __init__(
            self, *args, **kwargs
        ):
        super().__init__(*args, **kwargs)
        self.data['url'] = "http://139.196.42.166:8010/PON-Sol2/input/sequence/"

    def prepare_payload(self, row) -> Dict:
        return {
            'csrfmiddlewaretoken': row.csrf,
            'seq': row.fasta.sequence,
            'aa': self.prepare_mutation(row),
            'mail': self._credentials.email
        }
