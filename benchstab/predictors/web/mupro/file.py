import pandas as pd

from .base import _MUpro


class MuproPdbFile(_MUpro):
    def prepare_payload(self, row: pd.Series):
        _mutation = self.prepare_mutation(row)
        return {
            'input_text': row.fasta.sequence,
            'upfile': row['identifier'].to_octet_stream(),
            'position': _mutation[1:-1],
            'org_aa': _mutation[0],
            'rep_aa': _mutation[-1],
            'input_name': '',
        }
