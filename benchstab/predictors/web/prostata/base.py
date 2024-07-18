
from benchstab.predictors.base import (
    BasePostPredictor,
    PredictorFlags,
)
from benchstab.utils import status


class _Prostata(BasePostPredictor):
    """
    ProStata predictor class.

    Webserver:
        https://prostata.airi.net/
    
    Accepted inputs:
        * Protein sequence
        * Mutation
    
    Availability:
        |ProStata|
    
    Default configuration for :code:`ProStata` predictor defined in :code:`config.json` syntax is:
                            
            .. code-block:: python
    
                "prostata": {
                    "batch_size": 10
                }
    
    Citation:
        Dmitriy Umerenkov, Fedor Nikolaev, Tatiana I Shashkova, Pavel V Strashnov, Maria Sindeeva, Andrey Shevtsov, Nikita V Ivanisenko, Olga L Kardymon, PROSTATA: a framework for protein stability assessment using transformers, Bioinformatics, Volume 39, Issue 11, November 2023, btad671, https://doi.org/10.1093/bioinformatics/btad671
    """
    url = "https://prostata.airi.net/"

    def __init__(
        self,
        data,
        batch_size: int = 5,
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
        self.data['url'] = "https://prostata.airi.net/api/upload"

    def prepare_payload(self, row):
        return {
            'protein': row.fasta.sequence,
            'mutation': row.fasta_mutation,
        }

    async def default_post_handler(self, index, response, session):
        _res = await response.json()
        try:
            self.data.loc[index, 'DDG'] = float(_res['number'])
            self.data.update_status(index, status.Finished())
        except (IndexError, ValueError):
            self.data.update_status(index, status.Failed())
            return False
        return True
