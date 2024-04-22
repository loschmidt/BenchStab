from io import StringIO

import pandas as pd
from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor
)
from benchstab.utils import status


class _DDGun(BaseGetPredictor):
    """
    DDGun predictor class.

    Webserver:
        https://folding.biofold.org/cgi-bin/ddgun.cgi

    Accepted inputs:
        * PDB accession code
        * PDB structure file
        * Protein sequence

    Availability:
        |DDGun|

    Default configuration for :code:`DDGun` predictor defined in :code:`config.json` syntax is:
                
                .. code-block:: python
        
                    "ddgun": {
                        "wait_interval": 60,
                        "batch_size": 5
                    }
    
    Citation:
        Ludovica Montanucci and others, DDGun: an untrained predictor of protein stability changes upon amino acid variants, Nucleic Acids Research, Volume 50, Issue W1, 5 July 2022, Pages W222–W227, https://doi.org/10.1093/nar/gkac325
    """

    url = 'https://folding.biofold.org/ddgun'

    def __init__(
        self,
        data: pd.DataFrame,
        flags: PredictorFlags = None,
        wait_interval: int = 60,
        batch_size: int = 5,
        *args,
        **kwargs
    ) -> None:
        flags = flags or PredictorFlags(webkit=True)
        super().__init__(
            data=data,
            flags=flags,
            wait_interval=wait_interval,
            batch_size=batch_size,
            *args,
            **kwargs
        )
        self.data['url'] = 'https://folding.biofold.org/cgi-bin/ddgun.cgi'
        self.pred_type = '3D'
        self._db = 'uniclust30_2018_08'

    async def default_get_handler(self, index, response, session):
        _res = self.html_parser.with_xpath(
            xpath='//script[@id="load_table"]/@table_data', html=await response.text()
        )
        _data = pd.read_table(StringIO(_res), sep='\\s+')
        if _data.empty:
            return False
        self.data.loc[index, 'DDG'] = _data[f'S_DDG[{self.pred_type}]'].item()
        self.data.loc[index, 'url'] = response.url
        self.data.update_status(index, status.Finished())
        return True

    async def default_post_handler(self, index, response, session):
        _url = self.html_parser.with_xpath(
            xpath='//meta[@http-equiv="refresh"]/@content', html=await response.text()
        )
        if not 'find-ddgun-job' in _url:
            return False
        self.data.loc[index, 'url'] = _url[_url.index('url=')+4:]
        self.data.update_status(index, status.Waiting())
        return True
