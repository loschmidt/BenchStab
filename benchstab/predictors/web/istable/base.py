from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor,
)
from benchstab.utils import status


class _iStable(BaseGetPredictor):
    """
    iStable predictor class.

    Webserver:
        http://predictor.nchu.edu.tw/iStable/
    
    Accepted inputs:
        * PDB accession code
        * Protein sequence
    
    Availability:
        |iStable|
        
    Default configuration for :code:`iStable` predictor defined in :code:`config.json` syntax is:
                        
        .. code-block:: python

            "istable": {
                "wait_interval": 60,
                "batch_size": 5
            }
    
    Citation:
        Chen, CW., Lin, J. & Chu, YW. iStable: off-the-shelf predictor integration for predicting protein stability changes. BMC Bioinformatics 14 (Suppl 2), S5 (2013). https://doi.org/10.1186/1471-2105-14-S2-S5
    """

    url = "http://predictor.nchu.edu.tw/iStable/"

    def __init__(
        self,
        data,
        flags: PredictorFlags = None,
        wait_interval: int = 60,
        batch_size: int = 5,
        *args,
        **kwargs
    ) -> None:
        super().__init__(
            data=data,
            flags=flags,
            wait_interval=wait_interval,
            batch_size=batch_size,
            *args,
            **kwargs
        )
        self._table_width = '65'
        self._table_row = '3'
        self._table_data = '6'

    async def retrieve_result(self, session, index) -> bool:
        if not self.data.is_blocking_status(index):
            return True
        return await self.post(
            session, self.data.loc[index], self.__default_post_handler, index
        )


    async def __default_post_handler(self, index, response, session):
        _html = await response.text()
        if self.html_parser.with_xpath(
            xpath='//img[@alt="loading"]',
            html=_html,
            index=None
        ):
            return False

        _res = self.html_parser.with_xpath(
            xpath=f'//table[@width="{self._table_width}%"]/tr[{self._table_row}]',
            html=_html,
            index=0
        )
        _ddg = self.html_parser.with_xpath(
            xpath=f'./td[{self._table_data}]/text()', root=_res
        )
        self.data.update_status(index, status.Processing())
        try:
            self.data.loc[index, 'DDG'] = float(_ddg)
        except ValueError:
            self.data.loc[index, 'DDG'] = _ddg
        except IndexError:
            return False
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        return True

    async def default_post_handler(self, index, response, session):
        _html = await response.text()

        if self.html_parser.with_xpath(
            xpath='//img[@alt="loading"]',
            html=_html,
            index=None
        ):
            self.data.update_status(index, status.Waiting())
            return True

        if self.html_parser.with_xpath(
            xpath=f'//table[@width="{self._table_width}%"]/tr[{self._table_row}]',
            html=await response.text(),
            index=None
        ):
            self.data.update_status(index, status.Processing())
            return True
        return False
