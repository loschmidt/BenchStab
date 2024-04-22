import re
from benchstab.predictors.base import (
    BaseGetPredictor
)
from benchstab.utils import status


class _IMutant3(BaseGetPredictor):
    """
    I-Mutant3 predictor class.

    Webserver:
        http://gpcr.biocomp.unibo.it/cgi/predictors/I-Mutant3.0/I-Mutant3.0.cgi
    
    Accepted inputs:
        * PDB accession code
        * PDB structure file
        * Protein sequence
    
    Availability:
        |IMutant3|
        
    Default configuration for :code:`I-Mutant3` predictor defined in :code:`config.json` syntax is:
                    
        .. code-block:: python

            "imutant3": {
                "wait_interval": 60,
                "batch_size": 10
            }
    
    Citation:
        N/A
    """

    url = 'http://gpcr2.biocomp.unibo.it/cgi/predictors/I-Mutant3.0/I-Mutant3.0.cgi'

    def __init__(
        self,
        data,
        wait_interval: int = 60,
        batch_size: int = 10,
        *args,
        **kwargs
    ) -> None:
        super().__init__(
            data=data,
            wait_interval=wait_interval,
            batch_size=batch_size,
            *args,
            **kwargs
        )
        self.data['url'] = 'http://gpcr.biocomp.unibo.it/cgi/predictors/I-Mutant3.0/I-Mutant3.0.cgi'
        self._pred = '1'
        self.pred_type = ''
        self.kpred = 'ddg2'

    async def default_post_handler(self, index, response, session) -> bool:
        self.data.loc[index, 'url'] = self.html_parser.with_xpath(
            xpath="//a[contains(@href, 'output.html')]/@href", html=await response.text()
        )
        self.data.update_status(index, status.Waiting())
        return len(self.data.loc[index, 'url']) > 0

    async def default_get_handler(self, index, response, session) -> bool:
        _res = [
            t.strip()
            for t in self.html_parser.with_xpath(
                xpath='//pre[contains(text(), "Prediction")]/text()',
                html=await response.text()
            )
            if 'DDG' in t
        ]
        if _res:
            _ddg = re.findall(r'[\-+]?\d*\.\d+', _res[0])[0]
            self.data.loc[index, 'DDG'] = float(_ddg)
            self.data.update_status(index, status.Finished())
            self.data.loc[index, 'url'] = response.url
        return len(_res) > 0


class _IMutant2(_IMutant3):
    """
    I-Mutant2 predictor class.

    Webserver:
        https://folding.biofold.org/cgi-bin/i-mutant2.0.cgi
    
    Accepted inputs:
        * PDB accession code
        * Protein sequence
    
    Availability:
        |IMutant2|

    Default configuration for :code:`I-Mutant2` predictor defined in :code:`config.json` syntax is:
                        
        .. code-block:: python

            "imutant2": {
                "wait_interval": 60,
                "batch_size": 5
            }

    Citation:
        Emidio Capriotti and others, I-Mutant2.0: predicting stability changes upon mutation from the protein sequence or structure, Nucleic Acids Research, Volume 33, Issue suppl_2, 1 July 2005, Pages W306–W310, https://doi.org/10.1093/nar/gki375
    """

    url = "https://folding.biofold.org/i-mutant/i-mutant2.0.html"

    def __init__(self, data, *args, **kwargs) -> None:
        super().__init__(data, *args, **kwargs)
        self.data['url'] = 'https://folding.biofold.org/cgi-bin/i-mutant2.0.cgi'
        self.pred = 'ddg'

    async def default_get_handler(self, index, response, session) -> bool:
        _response = self.html_parser.with_xpath(
            xpath="//td[@width='70%']/div/pre/text()", html=await response.text()
        )
        _results = re.search(r'Position.*\n.*25', _response)
        finished = _results is not None

        if finished:
            _headers, _data = _results.group(0).split('\n')
            _index = _headers.split().index('DDG')
            _ddg = _data.split()[_index]
            self.data.loc[index, 'DDG'] = float(_ddg)
            self.data.update_status(index, status.Finished())
            self.data.loc[index, 'url'] = response.url

        return finished
