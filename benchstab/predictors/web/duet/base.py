import re

import pandas as pd
from benchstab.predictors.base import (
    PredictorFlags,
    BasePostPredictor,
)
from benchstab.utils import status


class _DUET(BasePostPredictor):
    """
    DUET predictor class.

    Webserver:
        https://biosig.lab.uq.edu.au/duet/stability_prediction
    
    Accepted inputs:
        * PDB accession code
        * PDB structure file
    
    Availability:
        |DUET|
        
    Default configuration for :code:`DUET` predictor defined in :code:`config.json` syntax is:
                    
                    .. code-block:: python
            
                        "duet": {
                            "batch_size": 1
                        }
    
    Citation:
        Douglas E.V. Pires and others, DUET: a server for predicting effects of mutations on protein stability using an integrated computational approach, Nucleic Acids Research, Volume 42, Issue W1, 1 July 2014, Pages W314–W319, https://doi.org/10.1093/nar/gku411
    
    """

    url = 'https://biosig.lab.uq.edu.au/duet/stability'

    def __init__(
            self,
            data: pd.DataFrame,
            flags: PredictorFlags = None,
            batch_size: int = 1,
            *args,
            **kwargs
    ) -> None:
        flags = flags or PredictorFlags(webkit=True, group_mutations_by=['identifier', 'chain', 'mutation'])
        super().__init__(
            data=data,
            flags=flags,
            batch_size=batch_size,
            *args,
            **kwargs
        )
        self.data['url'] = 'https://biosig.lab.uq.edu.au/duet/stability_prediction'
        self.run_type = 'single'

    async def default_post_handler(self, index, response, session):
        _res = self.html_parser.with_xpath(
            xpath="//div[@class = 'span4']/div[@class = 'well']", html=await response.text()
        )
        _duet = self.html_parser.with_xpath(xpath='./font[3]/text()', root=_res)
        _ddg = re.findall(r'[\-+]?\d*\.\d+', _duet)
        if not _ddg:
            self.data.update_status(index, status.Failed())
            return False
        self.data.loc[index, 'DDG'] = float(_ddg[0])
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        return True