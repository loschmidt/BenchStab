import pandas as pd
from typing import Union, Dict
from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor,
)
from benchstab.utils import status


class _BiosigAPIPredictor(BaseGetPredictor):
    """
    DDMut and Dynamut2 predictor class.

    Webserver:
        * DDMut:
            * https://biosig.lab.uq.edu.au/ddmut/api/prediction_list
        * Dynamut2:
            * https://biosig.lab.uq.edu.au/dynamut2/api/prediction_list

    Accepted inputs:
        * PDB accession code
        * PDB structure file
    
    Availability:
        * DDMut:
            |DDMut|
        * Dynamut2:
            |Dynamut2|

    Default configuration for :code:`DDMut` predictor defined in :code:`config.json` syntax is:
            
            .. code-block:: python
    
                "ddmut": {
                    "wait_interval": 60,
                    "batch_size": 10,
                    "max_retries": 100
                }
    
    Default configuration for :code:`Dynamut2` predictor defined in :code:`config.json` syntax is:

            .. code-block:: python

                "dynamut2": {
                    "wait_interval": 60,
                    "batch_size": 10,
                    "max_retries": 100
                }

    Citation: 
        * DDMut:
            Rodrigues, CHM, Pires, DEV, Ascher, DB. DynaMut2: Assessing changes in stability and flexibility upon single and multiple point missense mutations. Protein Science. 2021; 30: 60–69. https://doi.org/10.1002/pro.3942
        * Dynamut2:
            Yunzhuo Zhou and others, DDMut: predicting effects of mutations on protein stability using deep learning, Nucleic Acids Research, Volume 51, Issue W1, 5 July 2023, Pages W122–W128, https://doi.org/10.1093/nar/gkad472
    """
    def __init__(
            self,
            data: pd.DataFrame,
            flags: PredictorFlags = None,
            wait_interval: int = 60,
            batch_size: int = 10,
            *args,
            **kwargs
    ) -> None:
        flags = flags or PredictorFlags(
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
        self.data['url'] = \
            f"https://biosig.lab.uq.edu.au/{self._header.name.lower()}/api/prediction_list"

    def format_mutation(self, data: Union[str, Dict]) -> str:
        return f"{data.chain} {data.mutation}"

    async def retrieve_result(self, session, index) -> bool:
        if not self.data.is_blocking_status(index):
            return True
        return await self.get(
            session,
            self.data.loc[index],
            self.default_get_handler,
            index,
            data=self.data.loc[index, 'payload']
        )

    async def default_post_handler(self, index, response, session):
        _result = await response.json()
        _cond = 'job_id' in _result
        if _cond:
            self.data.loc[index, 'payload'].clear()
            self.data.update_status(index, status.Waiting())
            self.data.loc[index, 'payload']['job_id'] = _result['job_id']
        return _cond

    async def default_get_handler(self, index, response, session):
        _result = await response.json()
        if 'status' in _result and _result['status'] == 'RUNNING':
            return False

        if 'message' in _result and _result['message'] == 'Internal Server Error':
            return False
        mutations = []
        for i in range(len(self.data.loc[index, 'mutation'])):
            _i = str(i)
            if _i in _result:
                mutations.append(
                    {
                        'identifier': self.data.loc[index, 'identifier'],
                        'mutation': _result[_i]['mutation'],
                        'chain': _result[_i]['chain'],
                        'DDG': _result[_i]['prediction']
                    }
                )
        self._prediction_results.append(pd.DataFrame(mutations))
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        return True
