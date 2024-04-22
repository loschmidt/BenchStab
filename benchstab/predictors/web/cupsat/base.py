import pandas as pd

from benchstab.utils.aminoacids import Mapper
from benchstab.predictors.base import BasePostPredictor
from benchstab.utils import status


class _CUPSAT(BasePostPredictor):
    """
    CUPSAT predictor class.

    Webserver:
        https://cupsat.brenda-enzymes.org/resultall.jsp
    Accepted inputs:
        * PDB accession code
    Availability:
        |CUPSAT|

    Default configuration for :code:`CUPSAT` predictor defined in :code:`config.json` syntax is:
        
        .. code-block:: python

            "cupsat": {
                "experimental_method": "thermal",
                "batch_size": 20
            }

    Allowed :code:`experimental_method` values are:
        * `"thermal"` : Thermal stability
        * `"denaturants"` : Denaturants
    
    Citation
        Parthiban, V., Gromiha, M.M. and Schomburg, D., 2006. CUPSAT: prediction of protein stability upon point mutations. Nucleic acids research, 34(suppl_2), pp.W239-W242.
    """

    url = 'https://cupsat.brenda-enzymes.org'

    experimental_methods = {
        'thermal': 'thermal',
        'denaturants': 'denat',
    }

    def __init__(
        self,
        data: pd.DataFrame,
        experimental_method: str = 'thermal',
        batch_size: int = 20,
        *args,
        **kwargs
    ) -> None:
        super().__init__(data=data, batch_size=batch_size, *args, **kwargs)
        self.exp_method = _CUPSAT.experimental_methods[experimental_method]
        self.predictstab = 'one'
        self._url = 'https://cupsat.brenda-enzymes.org'
        self.base_url = self._url
        self.data['url'] = f'{self._url}/resultall.jsp'

    def prepare_payload(self, row: pd.Series):
        return {
            'pdbid': row['identifier'].id,
            'exp_method': self.exp_method,
            'predictstab': self.predictstab,
            'resno': self.prepare_mutation(row)[1:-1],
            'csform': 'exist',
            'chainid': row['chain'],
            'submit': 'Go'
        }

    async def default_post_handler(self, index, response, session):
        _res = self.html_parser.with_xpath(
            xpath='//*[@id="main"]/div[2]/div', html=await response.text(), index=None
        )
        if len(_res) < 2:
            return False

        mutations = []
        _pdb_id = self.data.loc[index, 'identifier']
        _chain = self.data.loc[index, 'chain']
        _orig_aa = self.data.loc[index, 'mutation'][:-1]

        for elem in _res[1:]:
            _aa = Mapper.three_to_one_letter(
                self.html_parser.with_xpath(xpath='./div[1]/text()', root=elem)
            )
            mutations.append(
                {
                    'identifier': _pdb_id,
                    'chain': _chain,
                    'mutation': _orig_aa + _aa,
                    'DDG': self.html_parser.with_xpath(xpath='./div[4]/text()', root=elem)
                }
            )
        self._prediction_results.append(pd.DataFrame(mutations))
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        return True
