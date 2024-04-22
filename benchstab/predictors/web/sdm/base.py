import pandas as pd

from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor
)
from benchstab.utils import status


class _SDM(BaseGetPredictor):
    """
    SDM predictor class.

    Webserver:
        http://marid.bioc.cam.ac.uk/sdm2/prediction
    
    Accepted inputs:
        * PDB structure file
        * PDB accession code
    
    Availability:
        |SDM|

    Default configuration for :code:`SDM` predictor defined in :code:`config.json` syntax is:
                        
        .. code-block:: python

            "sdm": {
                "wait_interval": 60,
                "batch_size": 10
            }
    
    Citation:
        Arun Prasad Pandurangan and others, SDM: a server for predicting effects of mutations on protein stability, Nucleic Acids Research, Volume 45, Issue W1, 3 July 2017, Pages W229–W235, https://doi.org/10.1093/nar/gkx439
    """

    url = "http://marid.bioc.cam.ac.uk/sdm2/prediction"

    def __init__(
        self,
        data: pd.DataFrame,
        flags: PredictorFlags = None,
        batch_size: int = 10,
        wait_interval: int = 60,
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
        self.prediction_type = 'regression'
        self.__url = "http://marid.bioc.cam.ac.uk"
        self.data['url'] = self.__url + "/sdm2/stability_prediction_list"

    def format_mutation(self, data: str) -> str:
        return f"{data.chain} {data.mutation}"

    async def default_get_handler(self, index, response, session):
        _data = self.html_parser.with_pandas(await response.text())
        _cond = (
            not _data.empty
            and 'Outcome' in _data.columns
            and 'Running' not in _data['Outcome'].values
        )
        if _cond:
            _cols = {'Chain ID': 'chain', 'Mutation': 'mutation', 'Predicted ΔΔG': 'DDG'}
            _data = _data[_cols.keys()].rename(_cols, axis=1)
            _data['identifier'] = self.data.loc[index, 'identifier']
            self._prediction_results.append(_data)
            self.data.update_status(index, status.Finished())
            self.data.loc[index, 'url'] = response.url
        return _cond

    async def default_post_handler(self, index, response, session):
        _url = self.html_parser.with_xpath(
            xpath='//meta[@http-equiv="refresh"]/@content', html=await response.text()
        )
        _cond = 'job_id' in _url
        if _cond:
            _url = _url[_url.index('; ')+2:]
            self.data.loc[index, 'url'] = self.__url + _url
            self.data.update_status(index, status.Waiting())
        return _cond
