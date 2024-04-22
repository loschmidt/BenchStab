from typing import Dict

import pandas as pd
from benchstab.predictors.base import BasePostPredictor
from benchstab.utils import status


class _AutoMute(BasePostPredictor):
    """
    Auto-Mute predictor class.

    Webserver:
        http://binf.gmu.edu/automute/AUTO-MUTE_Stability_ddG.html
    Accepted inputs:
        * PDB accession code
    
    Avalability:
        |Automute|
        
    Default configuration for :code:`AutoMute` predictor defined in :code:`config.json` syntax is:

    Allowed :code:`model_type` values are:

        .. code-block:: python

            "automute": {
                "model_type": "svm",
                "batch_size": 20
            }

    Citation
        Majid Masso, Iosif I. Vaisman, AUTO-MUTE: web-based tools for predicting stability changes in proteins due to single amino acid replacements, Protein Engineering, Design and Selection, Volume 23, Issue 8, August 2010, Pages 683–687, https://doi.org/10.1093/protein/gzq042
    """
    url = "http://binf.gmu.edu/automute/AUTO-MUTE_Stability_ddG.html"

    model_types = {
        'reptree': '1',
        'svm': '2',
    }

    def __init__(
        self,
        data,
        model_type: str = 'svm',
        batch_size: int = 20,
        *args,
        **kwargs
    ) -> None:
        super().__init__(
            data, batch_size=batch_size, *args, **kwargs
        )
        self.base_url = "http://binf.gmu.edu/automute/AUTO-MUTE_Stability_ddG.html"
        self.data['url'] = "http://binf.gmu.edu/automute/stability_ddG_server.php"
        self.pred = _AutoMute.model_types[model_type]

    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'pdb1': row['identifier'].id,
            'chn1': row['chain'],
            'mut1': row['mutation'],
            't1': row.temperature,
            'p1': row.ph,
            'pred': self.pred,
            'submit': 'Submit Request'
        }

    async def default_post_handler(self, index, response, session):
        _res = self.html_parser.with_xpath(
            xpath='/html/body/div/table/tbody/tr', html=await response.text(), index=None
        )
        if len(_res) < 2:
            return False
        mutations = []
        for elem in _res[1:]:
            mutations.append({
                'identifier': self.data.loc[index, 'identifier'],
                'chain': self.html_parser.with_xpath(root=elem, xpath='./td[2]/text()'),
                'mutation': self.html_parser.with_xpath(root=elem, xpath='./td[3]/text()'),
                'DDG':  self.html_parser.with_xpath(root=elem, xpath='./td[4]/text()')
            })
        self._prediction_results.append(pd.DataFrame(mutations))
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        return True
