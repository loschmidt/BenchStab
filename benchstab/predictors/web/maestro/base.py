from typing import Dict, Union
import time
import re

import pandas as pd
from benchstab.utils.exceptions import PredictorError
from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor,
)
from benchstab.utils import status


class _Maestro(BaseGetPredictor):
    """
    Maestro predictor class.

    Webserver:
        https://pbwww.services.came.sbg.ac.at/maestro/web

    Accepted inputs:
        * PDB accession code
    
    Availability:
        |Maestro|

    Default configuration for :code:`Maestro` predictor defined in :code:`config.json` syntax is:

        .. code-block:: python

            "maestro": {
                "wait_interval": 60,
                "batch_size": 1
            }
        
    Citation:
        Laimer, J., Hofer, H., Fritz, M. et al. MAESTRO - multi agent stability prediction upon point mutations. BMC Bioinformatics 16, 116 (2015). https://doi.org/10.1186/s12859-015-0548-6
    """

    url = 'https://pbwww.services.came.sbg.ac.at/maestro/web'
    
    def __init__(
            self,
            data,
            flags: PredictorFlags = None,
            wait_interval: int = 60,
            batch_size: int = 1,
            model: str = '-1',
            *args,
            **kwargs
    ) -> None:
        flags = flags or PredictorFlags(
            webkit=True,
            group_mutations=True,
            group_mutations_by=['identifier'],
            mutation_delimiter='\n'
        )
        super().__init__(
            data=data,
            flags=flags,
            wait_interval=wait_interval,
            batch_size=batch_size,
            *args,
            **kwargs
        )
        self.config = {
            'selected-task': 'evaluate',
            'selected-model': model,
            'selected-bu': '',
            'emailHidden': ''
        }
        self.is_file = 'false'
        self.is_bu = 'false'
        self.data['url'] = 'https://pbwww.services.came.sbg.ac.at/api/maestro/mae/selectPdb'
        self.data['jobid'] = ""

    def format_mutation(self, data: Union[str, Dict]) -> str:
        return f"{data.mutation[:-1]}.{data.chain}{{{data.mutation[-1]}}}"

    def prepare_payload(self, row: pd.Series) -> Dict:
        return {'text-input': row['identifier'].id}

    async def send_query(self, session, index, *args, **kwargs):
        if await self.post(session, self.data.loc[index], self.__retrieve_jobid_handler, index):
            return await self.post(
                session, self.data.loc[index], self.default_post_handler, index
            )
        return False

    async def retrieve_result(self, session, index):
        if not self.data.is_blocking_status(index):
            return True
        return await self.get(
            session,
            self.data.loc[index],
            self.default_get_handler,
            index,
            data={'timestamp': int(time.time())}
        )

    async def default_get_handler(self, index, response, session):
        _resp = await response.text()
        if 'Specific mutations evaluation' not in _resp:
            return False
        _data = self.html_parser.with_pandas(html=_resp)
        _mut_column = "1 substitution"
        if len(_data) > 1:
            _mut_column = f"{len(_data)} substitutions"

        _data = _data \
            .rename({f'{_mut_column}': 'mutation', 'ΔΔGpred.': 'DDG'}, axis=1) \
            .drop(['cpred.'], axis=1)
        _data['chain'] = _data['mutation'].apply(
            lambda x: re.search(r'\.(\w)\{', x).group(1)
        )
        _data['mutation'] = _data['mutation'].apply(
            lambda x: ''.join(re.search(r'(\w*).\w\{(\w)}', x).groups())
        )
        _data['identifier'] = self.data.loc[index, 'identifier']

        self._prediction_results.append(_data)
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        return True

    async def default_post_handler(self, index, response, session):
        _resp = await response.json()
        if not _resp['status'] == 'success':
            return False
        self.data.loc[index, 'url'] = (
            "https://pbwww.services.came.sbg.ac.at/api/maestro/workflow/getResult/"
            f"{self.data.loc[index, 'jobid']}"
        )
        return True

    async def __retrieve_jobid_handler(self, index, response, session):
        _resp = await response.json()
        if _resp['status'] != 'success':
            raise PredictorError(
                _resp['error'] if 'error' in _resp else 'Error initializing job'
            )
        self.data.update_status(index, status.Waiting())
        self.data.loc[index, 'jobid'] = _resp['id']
        self.data.loc[index, 'url'] = \
            'https://pbwww.services.came.sbg.ac.at/api/maestro/mae/evaluate'
        self.data.loc[index, 'payload'] = self.make_form(
            {
                'mutation-input': self.prepare_mutation(self.data.loc[index]),
                'mutationtype': 'single',
                'ph': self.data.loc[index].ph,
                'selected-chain': '*',
                'pdbId': self.data.loc[index, 'identifier'].id,
                'isFile': self.is_file,
                'isBu': self.is_bu,
                'jobId': _resp['id'],
                **self.config
            }
        )

        return True
