from itertools import zip_longest

import pandas as pd
from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor
)
from benchstab.utils import status


class _INPS(BaseGetPredictor):
    """
    INPS predictor class.

    Webserver:
        https://inpsmd.biocomp.unibo.it
    
    Accepted inputs:
        * PDB accession code
        * Protein sequence
    
    Availability:
        |INPS|

    Default configuration for :code:`INPS` predictor defined in :code:`config.json` syntax is:
                    
        .. code-block:: python

            "inps": {
                "wait_interval": 60,
                "batch_size": 10
            }
    
    Citation:
        Castrense Savojardo and others, INPS-MD: a web server to predict stability of protein variants from sequence and structure, Bioinformatics, Volume 32, Issue 16, August 2016, Pages 2542–2544, https://doi.org/10.1093/bioinformatics/btw192
    """

    url = "https://inpsmd.biocomp.unibo.it/welcome/default/index"

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
            webkit=True,
            group_mutations=True,
            group_mutations_by=['identifier', 'chain'],
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
        self._url = 'https://inpsmd.biocomp.unibo.it'

    async def __retrieve_formkey_handler(self, index, response, session):
        self.data.loc[index, 'payload']['_formkey'] = self.html_parser.with_xpath(
            xpath='//*[@id="content"]/div[5]/form/div/input[1]/@value', html=await response.text()
        )
        return len(self.data.loc[index, 'payload']['_formkey']) > 0

    async def send_query(self, session, index):
        if await self.get(
            session, self.data.loc[index], self.__retrieve_formkey_handler, index
        ):
            return await super().send_query(session, index)
        return False

    async def default_post_handler(self, index, response, session):
        for _resp in response.history:
            if _resp.status == 303:
                self.data.update_status(index, status.Waiting())
                self.data.loc[index, 'url'] = self._url + _resp.headers['Location'].replace(
                    'job_summary', 'display_result_link.load'
                )
                return True
        return False

    async def __extract_ddg_handler(self, index, response, session):
        _data = self.html_parser.with_xpath(
            xpath='//div[@class="resultrow"]/div[@class="tablecell"]/span/text()',
            html=await response.text(),
            index=None
        )
        if len(_data) < 2:
            self.data.update_status(index, status.Failed())
            return False

        mutations = []
        for mut, ddg in zip_longest(_data[::2], _data[1::2], fillvalue=None):
            mutations.append(
                {
                    'identifier': self.data.loc[index, 'identifier'],
                    'chain': self.data.loc[index, 'chain'],
                    'mutation': mut,
                    'DDG': ddg
                }
            )
        self._prediction_results.append(pd.DataFrame(mutations))
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        return True

    async def default_get_handler(self, index, response, session):
        self.data.loc[index, 'url'] = self._url + self.html_parser.with_xpath(
            xpath='//a/@href', html=await response.text()
        )
        return await self.get(
            session, self.data.loc[index], self.__extract_ddg_handler, index
        )
