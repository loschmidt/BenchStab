import pandas as pd
from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor
)
from benchstab.utils import status


class _DeepDDG(BaseGetPredictor):
    """
    DeepDDG predictor class.

    Webserver:
        http://protein.org.cn/upload.ddg.php
    
    Accepted inputs:
        * PDB accession code
        * PDB structure file

    Default configuration for :code:`DeepDDG` predictor defined in :code:`config.json` syntax is:
                    
                    .. code-block:: python
            
                        "deepddg": {
                            "wait_interval": 120,
                            "batch_size": 5
                        }
    
    Citation:
        Huali Cao, Jingxue Wang, Liping He, Yifei Qi, and John Z. Zhang Journal of Chemical Information and Modeling 2019 59 (4), 1508-1514 DOI: https://doi.org/10.1021/acs.jcim.8b00697

    """

    url = 'http://protein.org.cn/ddg.html'

    def __init__(
        self,
        data: pd.DataFrame,
        flags: PredictorFlags = None,
        wait_interval: int = 120,
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
        self.data['url'] = 'http://protein.org.cn/upload.ddg.php'
        self.pred = 'nometa'
        self.mutation_type = 'selemut'
        self._url = 'http://protein.org.cn/'

    def format_mutation(self, data) -> str:
        return (
            f"{data.chain} "
            f"{data.mutation[0]} "
            f"{data.mutation[1:-1]} "
            f"{data.mutation[-1]}"
        )

    async def default_post_handler(self, index, response, session):
        _res = self.html_parser.with_xpath(
            xpath='//a/@href', html=await response.text()
        )
        self.data.update_status(index, status.Waiting())
        self.data.loc[index, 'url'] = _res
        return len(_res) > 0

    async def default_get_handler(self, index, response, session):
        _res = self.html_parser.with_xpath(
            xpath="//a[text() = 'Download']/@href", html=await response.text()
        )
        self.data.loc[index, 'url'] = self._url + _res
        return await self.get(
            session, self.data.loc[index], self.__extract_ddg_handler, index
        )

    async def __extract_ddg_handler(self, index, response, session):
        _text =  await response.text()
        _cond = 'ddG' in _text
        if _cond:
            results = _text.split('\n')
            if len(results) < 2:
                return False
            mutations = []
            for result in results[1:-1]:
                _data = result.split()
                mutations.append(
                    {
                        'identifier': self.data.loc[index, 'identifier'],
                        'chain': _data[0],
                        'mutation': _data[1] + _data[2] + _data[3],
                        'DDG': _data[-1]
                    }
                )
            self.data.update_status(index, status.Finished())
            self.data.loc[index, 'url'] = response.url
            self._prediction_results.append(pd.DataFrame(mutations))
        return _cond
