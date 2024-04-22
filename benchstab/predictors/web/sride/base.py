from benchstab.utils.aminoacids import Mapper
from benchstab.predictors.base import (
    PredictorFlags,
    BasePostPredictor,
)
from benchstab.utils import status


class _SRide(BasePostPredictor):
    """
    SRide predictor class.

    Webserver:
        https://sride.enzim.hu/index.php

    Accepted inputs:
        * PDB accession code
        * PDB structure file
    
    Availability:
        |SRide|

    Default configuration for :code:`SRide` predictor defined in :code:`config.json` syntax is:
                            
        .. code-block:: python

            "sride": {
                "batch_size": 10,
                "SC_check": true,
                "Hp": 20,
                "E_value": 0.001,
                "cons_score": 6,
                "N_maxseq": 50,
                "LRO": 0.02
            }

    Citation:
        Csaba Magyar and others, SRide: a server for identifying stabilizing residues in proteins, Nucleic Acids Research, Volume 33, Issue suppl_2, 1 July 2005, Pages W303–W305, https://doi.org/10.1093/nar/gki409
    """

    url = "https://sride.enzim.hu/index.php"

    def __init__(
        self,
        data,
        flags: PredictorFlags = None,
        e_value='0.001',
        cons_score='6',
        iro='0.02',
        hp='20',
        sc_check='yes',
        n_maxseq='50',
        *args,
        **kwargs
    ) -> None:
        flags = flags or PredictorFlags(
            webkit=True, group_mutations=True, group_mutations_by=['identifier', 'chain']
        )
        super().__init__(data=data, flags=flags, *args, **kwargs)
        self.config = {
            'stabc': sc_check,
            'hpval': hp,
            'conscore': cons_score,
            'eval': e_value,
            'iroval': iro,
            'nhom': n_maxseq,
            'send': 'SUBMIT',
            'step': '1'
        }
        self.data['url'] = self.url

    async def default_post_handler(self, index, response, session):
        _text = await response.text()
        df = self.html_parser.with_pandas(_text, index=0, pandas_args={'header': 0})
        df['identifier'] = self.data.loc[index, 'identifier']
        df['chain'] = self.data.loc[index, 'chain']
        df['DDG'] = 'Stabilizing'
        df['mutation'] = df.apply(
            lambda row: (
                f"{Mapper.three_to_one_letter(row['Residue'][:3])}"
                f"{row['Residue'][4:]}"
                f"{Mapper.three_to_one_letter(row['Residue'][:3])}"
            ),
            axis=1
        )
        df = df.drop(['Residue', 'SR'], axis=1)
        self.data.loc[index, 'url'] = response.url
        self.data.update_status(index, status.Finished())
        self._prediction_results.append(df)
        return True
