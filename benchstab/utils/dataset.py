import logging
from time import time
from importlib import import_module

import pandas as pd

from . import status as st
from .exceptions import DatasetError


class DatasetRow(pd.Series):

    @property
    def _constructor(self):
        return DatasetRow

    @property
    def _constructor_expanddim(self):
        return PredictorDataset

    @property
    def fasta(self):
        """
        Get fasta sequence from the dataset's row.
        
        :return: fasta sequence
        :rtype: str
        """
        _fasta = self["fasta"]

        if _fasta is None:
            raise DatasetError(
                "Fasta sequence could not be inferred from the input protein.",
            )
        return _fasta

    @property
    def ph(self):
        """
        Get pH from the dataset's row.
        
        :return: pH
        :rtype: str
        """
        return str(self["ph"])

    @property
    def temperature(self):
        """
        Get temperature from the dataset's row.
        
        :return: temperature
        :rtype: str
        """
        return str(self["temperature"])

    @property
    def mutation(self):
        """
        Get mutation from the dataset's row.
        
        :return: mutation
        :rtype: str
        """
        _mutation = self["mutation"]

        if _mutation is None:
            raise DatasetError(
                "Mutation could not be inferred from the input protein.",
            )
        return _mutation
    
    @property
    def fasta_mutation(self):
        """
        Get fasta mutation from the dataset's row.
        
        :return: fasta mutation
        :rtype: str
        """
        _mutation = self["fasta_mutation"]

        if _mutation is None:
            raise DatasetError(
                "Mutation could not be inferred from the input protein.",
            )
        return _mutation

    def __getitem__(self, key):
        _item = super().__getitem__(key)
        if _item is None:
            raise DatasetError(
                f'Failed to preprocess {key} from the input protein.',
            )
        return _item


class PredictorDataset(pd.DataFrame):
    """
    Wrapper around pandas.DataFrame with additional methods.
    """
    blocking_statuses = [
        v() for v in import_module('benchstab.utils.status').__dict__.values()
        if 'benchstab.utils.status.' in str(v) and v.blocking
    ]
    update_statuses = [*blocking_statuses, st.NotStarted()]

    @classmethod
    def concat(cls, *args, **kwargs):
        """ Wrappper around pandas.concat, casting it back to PredictorDataset.
        """
        return cls(pd.concat(*args, **kwargs))

    @property
    def _constructor(self):
        return PredictorDataset

    @property
    def _constructor_sliced(self):
        return DatasetRow

    @property
    def logger(self):
        """  
        Getter for the logger.
        """
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._logger = logging.getLogger(self.__class__.__name__)

    def start_timer(self, index):
        """
        Start the timer for the prediction.

        :param index: index of the row
        :type index: int
        """
        self.loc[index, "_start_time"] = time()

    def update_status(self, index, status):
        """
        Update status of the prediction. If prediction succeeded/failed, stop the timer.

        :param index: index of the row to update
        :type index: int
        :param status: new status
        :type status: str
        """
        self.loc[index, "status"] = status
        if not self.is_blocking_status(index) and self.loc[index, "_start_time"]:
            _time = time() - self.loc[index, "_start_time"]
            self.loc[index, "Elapsed Time (sec.)"] = float(f"{_time:.2f}")

        _processed = self[
            ~self.status.isin(self.update_statuses)
        ].shape[0]
        _mutation = self.loc[index, "mutation"]

        if isinstance(_mutation, list):
            _mutation = ",".join([m.mutation for m in _mutation])

        self._logger.info(
            'INFO: %s (%d/%d): Status change in "%s":"%s" to "%s".',
            self._logger.name,
            _processed,
            self.shape[0],
            self.loc[index, "identifier"],
            _mutation,
            status
        )

    def format_to_output(self, verbose: int = 0):
        """
        Format the dataset to output format.

        :param verbose: verbosity level
        :type verbose: int
        :return: formatted dataset
        :rtype: PredictorDataset
        """
        _df = self.copy()
        _final_column_list = [
            'identifier',
            'mutation',
            'chain',
            'DDG',
            'status',
            'predictor',
            'input_type',
            'url', 
            "Elapsed Time (sec.)",            
        ]

        if verbose == 2:
            _df['status_message'] = _df['status'].apply(lambda x: x.message)
            _final_column_list.append('status_message')

        return _df.drop(
            [col for col in _df.columns if '_to_delete' in col], axis=1
        )[_final_column_list].drop_duplicates()

    def is_blocking_status(self, index):
        """
        Check if the status is blocking.

        :param index: index of the row
        :type index: int
        :return: True if the status is blocking, False otherwise
        :rtype: bool
        """
        return self.loc[index, "status"] in self.blocking_statuses

    def get_sequence(self, index):
        """
        Get fasta sequence from the dataset.

        :param index: index of the row
        :type index: int
        :return: fasta sequence
        :rtype: str
        """
        _fasta = self.loc[index, "fasta"]

        if _fasta is None or _fasta.sequecne is None:
            raise DatasetError(
                "Fasta sequence could not be inferred from the input protein.",
            )

        return _fasta
