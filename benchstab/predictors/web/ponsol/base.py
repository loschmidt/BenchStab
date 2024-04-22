from benchstab.predictors.base import (
    BasePostPredictor,
    PredictorFlags
)
from benchstab.utils import status

class _PONSol2(BasePostPredictor):
    """
    PONSol2 predictor class.

    Webserver:
        http:///139.196.42.166:8010/PON-Sol2/
    
    Accepted inputs:
        * Protein sequence

    Availability:
        |PONSol2|

    Default configuration for :code:`PONSol2` predictor defined in :code:`config.json` syntax is:
                        
        .. code-block:: python

            "ponsol2": {
                "batch_size": 5,
                "max_retries": 100
            }
    
    Citation:
        Int. J. Mol. Sci. 2021, 22(15), 8027; https://doi.org/10.3390/ijms22158027
    """

    url = 'http://139.196.42.166:8010/PON-Sol2/'

    def __init__(
        self,
        flags: PredictorFlags = None,
        batch_size: int = 5,
        max_retries: int = 100,
        *args,
        **kwargs
    ):
        flags = flags or PredictorFlags(
            webkit=True,
            group_mutations=True,
            group_mutations_by=["identifier"],
            mutation_delimiter='\n'
        )
        super().__init__(
            flags=flags, max_retries=max_retries, batch_size=batch_size, *args, **kwargs
        )
        self.data['csrf'] = ""
    
    async def __csrf_handler(self, index, response, session):
        self.data.loc[index, "csrf"] = self.html_parser.with_xpath(
            xpath="//input[@name='csrfmiddlewaretoken']/@value", html=await response.text(), index=0
        )
        self.data.update_status(index, status.Waiting())
        self.data.loc[index, "url"] = "http://139.196.42.166:8010/PON-Sol2/predict/seq/"
        self.data.loc[index, "payload"].update({'csrfmiddlewaretoken': self.data.loc[index, "csrf"]})
        return True

    async def send_query(self, session, index: int, *args, **kwargs):
        if await self.get(session, self.data.loc[index], self.__csrf_handler, index):
            kwargs['ssl'] = True
            return await super().send_query(session, index, *args, **kwargs)

    async def default_post_handler(self, index, response, session):
        _res = self.html_parser.with_pandas(html=await response.text())

        _res['identifier'] = self.data.loc[index, 'identifier']
        _res['chain'] = self.data.loc[index, 'chain']
        _res.rename(columns={'Prediction result': 'DDG', 'Variation': 'mutation'}, inplace=True)
        _res.drop('Remark', axis=1, inplace=True)

        self.data.update_status(index, status.Finished())
        self._prediction_results.append(_res)
        return True