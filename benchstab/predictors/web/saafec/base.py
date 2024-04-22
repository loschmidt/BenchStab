from typing import Dict, Union

from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor
)
from benchstab.utils import status


class _SAAFEC(BaseGetPredictor):
    """
    SAAFEC predictor class.

    Webserver:
        http://compbio.clemson.edu/SAAFEC-SEQ/
    
    Accepted inputs:
        * Protein sequence
    
    Availability:
        |SAAFEC|

    Default configuration for :code:`SAAFEC` predictor defined in :code:`config.json` syntax is:

        .. code-block:: python

            "saafec": {
                "wait_interval": 60,
                "batch_size": 5
            }

    Citation:
        Li, G.; Panday, S.K.; Alexov, E. SAAFEC-SEQ: A Sequence-Based Method for Predicting the Effect of Single Point Mutations on Protein Thermodynamic Stability. Int. J. Mol. Sci. 2021, 22, 606. https://doi.org/10.3390/ijms22020606
    """

    url = 'http://compbio.clemson.edu/SAAFEC-SEQ/'

    def __init__(
        self,
        data,
        flags: PredictorFlags = None,
        batch_size: int = 5,
        wait_interval: int = 60,
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
            batch_size=batch_size,
            wait_interval=wait_interval,
            *args,
            **kwargs
        )
        self.data['url'] = 'http://compbio.clemson.edu/SAAFEC-SEQ/proc_multiple_mutation.php'

    async def default_post_handler(self, index, response, session):
        self.data.loc[index, 'url'] = self.html_parser.with_xpath(
            xpath='//a/@href', html=await response.text()
        )
        self.data.update_status(index, status.Waiting())
        return True

    async def default_get_handler(self, index, response, session):
        _df = self.html_parser.with_pandas(await response.text())
        _df['mutation'] = _df['Wildetype Residue'] \
                        + _df['Position'].astype(str) \
                        + _df['Mutant Residue']
        _df['identifier'] = self.data.loc[index, 'identifier']
        _df['chain'] = self.data.loc[index, 'chain']
        _df = _df.drop(
            ['Predicted Effect', 'Position', 'Wildetype Residue', 'Mutant Residue'], axis=1
        ).rename({'ddG (unit)': 'DDG'}, axis=1)
        self._prediction_results.append(_df)
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        return True

    def format_mutation(self, data: Union[str, Dict]) -> str:
        return f"{data.fasta_mutation[0]} {data.fasta_mutation[1:-1]} {data.fasta_mutation[-1]}"
