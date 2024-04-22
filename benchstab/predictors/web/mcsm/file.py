import pandas as pd

from .base import _mCSM
from benchstab.utils.structure import File


class mCSMPdbFile(_mCSM):
    def prepare_payload(self, row: pd.Series):
        return {
            "wild": row['identifier'].to_octet_stream(),
            "mutation_list": File(
                self.prepare_mutation(row), "mutation.txt"
            ).to_plain_text(),
        }
