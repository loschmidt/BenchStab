import pandas as pd
from typing import Union, Dict
from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor
)
from benchstab.utils import status


class _mCSM(BaseGetPredictor):
    """
    mCSM predictor class.

    Webserver:
        https://biosig.lab.uq.edu.au/mcsm/stability
    
    Accepted inputs:
        * PDB structure file

    Availability:
        |mCSM|

    Default configuration for :code:`mCSM` predictor defined in :code:`config.json` syntax is:
                        
        .. code-block:: python

            "mcsm": {
                "wait_interval": 60,
                "batch_size": 5
            }

    Citation:
        Douglas E. V. Pires and others, mCSM: predicting the effects of mutations in proteins using graph-based signatures, Bioinformatics, Volume 30, Issue 3, February 2014, Pages 335–342, https://doi.org/10.1093/bioinformatics/btt691
    """

    url = 'https://biosig.lab.uq.edu.au/mcsm/stability'

    def __init__(
        self,
        data: pd.DataFrame,
        flags: PredictorFlags = None,
        wait_interval: int = 60,
        batch_size: int = 5,
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
        self.data['url'] = "https://biosig.lab.uq.edu.au/mcsm/stability_prediction_list"

    def format_mutation(self, data: Union[str, Dict]) -> str:
        return f"{data.chain} {data.mutation}"

    async def default_post_handler(self, index, response, session):
        await response.text()
        if response.status == 200:
            self.data.loc[index, 'url'] = response.url
            self.data.update_status(index, status.Waiting())
            return True
        return False

    def __rename(self, row):
        newname = row['Wild Residue'] \
                + str(row['Residue Position']) \
                + row['Mutant Residue']
        return newname

    async def default_get_handler(self, index, response, session):
        _data = self.html_parser.with_pandas(
            html=await response.text()
        )
        _data['mutation'] = _data.apply(self.__rename, axis=1)
        _data['identifier'] = self.data.loc[index, 'identifier']
        _data = _data.drop(
            [
                'Index',
                'PDB File',
                'Residue Position',
                'Mutant Residue',
                'Wild Residue',
                'RSA (%)',
                'Outcome'
            ], axis=1
        ).rename({'Predicted ΔΔG': 'DDG', 'Chain': 'chain'}, axis=1)
        self._prediction_results.append(_data)
        self.data.loc[index, 'url'] = response.url
        self.data.update_status(index, status.Finished())

        return True
