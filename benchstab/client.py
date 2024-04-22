import os
import json
import logging
from datetime import datetime
from contextlib import suppress
from importlib import import_module
from typing import List, Dict, Any, Union

import asyncio
import pandas as pd

from .preprocessor import Preprocessor
from .utils.dataset import PredictorDataset
from .utils.exceptions import BenchStabError
from .utils.structure import Fasta


class BenchStab:
    """
    The BenchStab class is responsible for managing the predictors. It
    selects the predictors based on the input data and runs them. The results
    are returned as a pandas DataFrame. If an outfolder is specified, the
    results will be saved there as a CSV file.
    """
    predictor_dict = {
        k: v for k, v in import_module('benchstab.predictors.web').__dict__.items()
    }
    sequence_predictors = [v.header() for k, v in predictor_dict.items() if 'Sequence' in k]
    pdbid_predictors = [v.header() for k, v in predictor_dict.items() if 'PdbID' in k]
    pdbfile_predictors = [v.header() for k, v in predictor_dict.items() if 'PdbFile' in k]

    def __init__(
        self,
        input_file: Union[str, pd.DataFrame],
        outfolder: str = None,
        predictor_config: Dict[str, Any] = None,
        include: List[str] = None,
        exclude: List[str] = None,
        allow_struct_predictors: bool = True,
        allow_sequence_predictors: bool = True,
        verbosity: int = 0,
        permissive: bool = False,
        *args,
        **kwargs,
    ) -> None:
        include = include or []
        exclude = exclude or []
        if include and exclude:
            exclude = []
        predictor_config = predictor_config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.INFO)

        self._allow_sequence = allow_sequence_predictors
        self._allow_struct = allow_struct_predictors

        self._global_config = {
            k: v for k, v in predictor_config.items() if not isinstance(v, dict)
        }
        self._local_config = {
            k.lower(): v for k, v in predictor_config.items() if isinstance(v, dict)
        }

        self.period = 60
        if 'wait_interval' in self._global_config:
            self.period = self._global_config['wait_interval']

        self._include = [x.lower() for x in include]
        self._exclude = [x.lower() for x in exclude]
        self.filter_predictors()
        if not self.sequence_predictors + self.pdbfile_predictors + self.pdbid_predictors:
            raise BenchStabError(
                (
                    "No predictors found after applying include/exclude lists. "
                    "Please check your configuration."
                )
            )
        self._verbosity = verbosity
        self.outfolder = outfolder
        if self.outfolder is not None:
            self.outfolder = os.path.join(
                outfolder,
                f"BenchStab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            os.mkdir(self.outfolder)
        if not isinstance(input_file, PredictorDataset):
            self._preprocessor = Preprocessor(
                input_file,
                outfolder=self.outfolder,
                permissive=permissive,
                verbosity=verbosity,
                *args,
                **kwargs,
            )
            self._data = None
        else:
            self._data = input_file
        self.predictors = []

    def filter_predictors(self):
        """
        Filter the predictors based on the include and exclude lists. If the
        include list is specified, only the predictors in the include list
        will be selected. If the exclude list is specified, the predictors in
        the exclude list will be removed from the list of predictors. If both
        lists are specified, the exclude list will be ignored.
        """
        if self._include:
            self.sequence_predictors = [] if not self._allow_sequence else list(
                filter(lambda x: x in self._include, BenchStab.sequence_predictors)
            )
            self.pdbid_predictors = [] if not self._allow_struct else list(
                filter(lambda x: x in self._include, BenchStab.pdbid_predictors)
            )
            self.pdbfile_predictors = [] if not self._allow_struct else list(
                filter(lambda x: x in self._include, BenchStab.pdbfile_predictors)
            )
            return
        self.sequence_predictors = [] if not self._allow_sequence else list(
            set(BenchStab.sequence_predictors) - set(self._exclude)
        )
        self.pdbid_predictors = [] if not self._allow_struct else list(
            set(BenchStab.pdbid_predictors) - set(self._exclude)
        )
        self.pdbfile_predictors = [] if not self._allow_struct else list(
            set(BenchStab.pdbfile_predictors) - set(self._exclude)
        )

    def __map(self, row):
        """
        Map the predictors to the input data. If the input data is a Fasta
        object, only sequence predictors will be selected. If the input data
        is a Pdb object, only structure predictors will be selected. If the
        input data is a PdbFile object, both sequence and structure predictors
        will be selected.

        
        :param row: A row of the input data.
        :type row: pandas.Series
        :return: A list of selected predictors.
        :rtype: list
        """
        if isinstance(row['identifier'], Fasta):
            if self._allow_sequence:
                return self.sequence_predictors
            return []
        _preds = []
        if self._allow_sequence:
            _preds += self.sequence_predictors
        if self._allow_struct:
            if row.identifier.source == 'rcsb':
                _preds += list(set(self.pdbid_predictors).union(set(self.pdbfile_predictors)))
            elif row.identifier.source == 'file':
                _preds += self.pdbfile_predictors
        if not _preds:
            return None
        return _preds

    def save_results(self, results: pd.DataFrame):
        """
        Save the results to a CSV file in the outfolder.

        
        :param results: The results to be saved.
        :type results: pandas.DataFrame
        """

        if self.outfolder is None:
            return False
        results.to_csv(os.path.join(self.outfolder, "results.csv"))
        return True

    def gather_results(self):
        """
        Gather the results from the predictors.
        """
        return pd.concat([pred.get_results() for pred in self.predictors])


    async def __periodically_gather_results(self):
        """
        Gather the results from the predictors. The results are concatenated
        and saved to a CSV file in the outfolder.
        """
        try:
            while True:
                results = self.gather_results()
                self.save_results(results)
                await asyncio.sleep(self.period)
        except asyncio.CancelledError:
            return True

    async def __run(self):
        """
        Run the predictors asynchronously and gather the results. The results
        are returned as a pandas DataFrame.

        Returns:
        :return: The results as a pandas DataFrame.
        :rtype: pandas.DataFrame
        """
        pred_tasks = asyncio.gather(
            *[pred.compute() for pred in self.predictors]
        )

        if self.outfolder is not None:
            result_snapshot = asyncio.ensure_future(self.__periodically_gather_results())
            pred_tasks.add_done_callback(result_snapshot.cancel)
            with suppress(asyncio.CancelledError):
                _results = await asyncio.gather(
                    pred_tasks, result_snapshot
                )
        else:
            _results = await asyncio.gather(pred_tasks)

        return _results[0]


    def __call__(self, dry_run=False) -> Union[pd.DataFrame, None]:
        """
        Run the predictor manager. If dry_run is True, the manager will only
        print the list of selected predictors and return None. Otherwise, it
        will run the selected predictors and return the results as a pandas
        DataFrame. If an outfolder is specified, the results will be saved
        there as a CSV file. If the input is a PredictorDataset, the manager
        will not run the preprocessor and will use the PredictorDataset as
        input. Otherwise, the manager will run the preprocessor and use the
        preprocessed data as input.

        
        :param dry_run: If True, the manager will only print the list of
            selected predictors and return None. Defaults to False.
        :type dry_run: bool
        :return: The results as a pandas DataFrame.
        :rtype: pandas.DataFrame
        """

        # If the PredictorDataset was supplied, there is no need to run the preprocessor
        if self._data is None:
            self._data = self._preprocessor.parse()
        _summary = Preprocessor.create_summary(self._data, self._verbosity, self.outfolder)

        # Save the summary to the outfolder if specified and print it to the console if verbosity
        if self.outfolder is not None:
            with open(os.path.join(self.outfolder, 'summary.json'), 'w', encoding='utf-8') as file:
                json.dump(_summary, file, ensure_ascii=False, indent=4)
        # Assign the predictors to the input data and drop the rows with no predictors assigned
        self._data['predictor_map'] = self._data.apply(self.__map, axis=1).dropna()
        self._data = self._data.loc[self._data.predictor_map.notna()]
        self._data = self._data.explode(['predictor_map'])

        if self._data.empty:
            raise BenchStabError(
                (
                    "No valid predictors found for the supplied dataset. "
                    "Please check your configuration."
                )
            )

        # Create the predictor objects
        for pred in self._data['predictor_map'].unique():
            _local_config = {}
            if pred.name.lower() in self._local_config:
                _local_config = self._local_config[pred.name.lower()]
            self.predictors.append(
                BenchStab.predictor_dict[pred.classname](
                    data=self._data.loc[self._data['predictor_map'] == pred],
                    verbosity=self._verbosity,
                    **dict(self._global_config, **_local_config)
                )
            )
        # Only print the list of selected predictors if dry_run is True
        if dry_run:
            self.logger.info("List of selected predictors:")
            for pred in self.predictors:
                self.logger.info(
                    'Included predictor: "%s", input type: "%s"',
                    pred._header.name, pred._header.input_type
                )
            self.logger.info("Dry run finished.")
            return None

        # Run the predictors asynchronously and concatenate the results

        loop = asyncio.get_event_loop()
        results = [
            res for res in loop.run_until_complete(self.__run())
            if not isinstance(res, bool) and res is not None
        ]
        if results:
            results = pd.concat(results)
        return results
