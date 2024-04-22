import pandas as pd

from .base import _BiosigAPIPredictor
from benchstab.utils.structure import File


class DDMutPdbID(_BiosigAPIPredictor):

    url = "https://biosig.lab.uq.edu.au/ddmut"

    def prepare_payload(self, row: pd.Series):
        return {
            'pdb_accession': row['identifier'].id,
            'mutations_list': File(self.prepare_mutation(row)).to_bytes()
        }


class Dynamut2PdbID(_BiosigAPIPredictor):
    
    url = "https://biosig.lab.uq.edu.au/dynamut2"
    
    def prepare_payload(self, row: pd.Series):
        return {
            'pdb_accession': row['identifier'].id,
            'mutations_list': File(self.prepare_mutation(row)).to_bytes()
        }
