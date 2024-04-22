import re

from benchstab.predictors.base import (
    PredictorFlags,
    BasePostPredictor,
)
from benchstab.utils import status


class _MUpro(BasePostPredictor):
    """
    MUpro predictor class.

    Webserver:
        http://mupro.proteomics.ics.uci.edu/
    
    Accepted inputs:
        * PDB structure file
        * Protein sequence
    
    Availability:
        |MUpro|

    Default configuration for :code:`MUpro` predictor defined in :code:`config.json` syntax is:
                        
        .. code-block:: python

            "mupro": {
                "batch_size": 10
            }
    
    Citation:
        Cheng, J., Randall, A. and Baldi, P. (2006), Prediction of protein stability changes for single-site mutations using support vector machines. Proteins, 62: 1125-1132. https://doi.org/10.1002/prot.20810
    """

    url = "http://mupro.proteomics.ics.uci.edu/"

    def __init__(
        self,
        data,
        batch_size: int = 10,
        flags: PredictorFlags = None,
        *args,
        **kwargs
    ) -> None:
        flags = flags or PredictorFlags(
            webkit=True,
            group_mutations_by=['identifier', 'chain', 'mutation']
        )
        super().__init__(
            data=data, flags=flags, batch_size=batch_size, *args, **kwargs)
        self.data['url'] = "http://mupro.proteomics.ics.uci.edu/cgi-bin/predict.pl"

    async def default_post_handler(self, index, response, session):
        _res = self.html_parser.with_xpath(
            xpath='///html/body/text()[10]', html=await response.text()
        )
        try:
            _ddg = re.findall(r'[\-+]?\d*\.\d+', _res)
            self.data.loc[index, 'DDG'] = float(_ddg[0])
            self.data.update_status(index, status.Finished())
            self.data.loc[index, 'url'] = response.url
        except IndexError:
            return False
        return True
