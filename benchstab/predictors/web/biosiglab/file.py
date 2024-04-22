import pandas as pd

from .base import _BiosigAPIPredictor
from benchstab.utils.structure import File


class Dynamut2PdbFile(_BiosigAPIPredictor):
    
    url = "https://biosig.lab.uq.edu.au/dynamut2"

    def prepare_payload(self, row: pd.Series):
        return {
            'pdb_file': row['identifier'].to_bytes(),
            'mutations_list': File(self.prepare_mutation(row)).to_bytes()
        }


class DDMutPdbFile(_BiosigAPIPredictor):

    url = "https://biosig.lab.uq.edu.au/ddmut"

    def prepare_payload(self, row: pd.Series):
        return {
            'pdb_file': row['identifier'].to_bytes(),
            'mutations_list': File(self.prepare_mutation(row)).to_bytes()
        }
