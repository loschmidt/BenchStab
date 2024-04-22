import re
from typing import Dict, Union

from benchstab.utils.structure import File
from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor
)
from benchstab.utils import status


class _PremPS(BaseGetPredictor):
    """
    PremPS predictor class.

    Webserver:
        https://lilab.jysw.suda.edu.cn/research/PremPS/
    
    Accepted inputs:
        * PDB structure file
        * PDB accession code

    Availability:
        |PremPS|

    Default configuration for :code:`PremPS` predictor defined in :code:`config.json` syntax is:

        .. code-block:: python

            "premps": {
                "wait_interval": 60,
                "batch_size": 5,
                "pdb_model": "bioassembly",
                "max_retries": 100
            }
        
    Citation:
        Chen Y, Lu H, Zhang N, Zhu Z, Wang S, et al. (2020) PremPS: Predicting the impact of missense mutations on protein stability. PLOS Computational Biology 16(12): e1008543. https://doi.org/10.1371/journal.pcbi.1008543
    """

    url = 'https://lilab.jysw.suda.edu.cn/research/PremPS/'

    pdb_models = {
        'asymmetric unit': 'asu',
        'bioassembly': 'bio',
    }

    def __init__(
        self,
        data,
        pdb_model: str = "bioassembly",
        batch_size: int = 5,
        wait_interval: int = 60,
        flags: PredictorFlags = None,
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
            batch_size=batch_size,
            wait_interval=wait_interval,
            *args,
            **kwargs
        )
        self.data['url'] = 'https://lilab.jysw.suda.edu.cn/research/PremPS/'
        self.pdb_mol = _PremPS.pdb_models[pdb_model]
        self.bioassembly = "1"
        self.is_pl = "1"
        self.data['csrf'] = ""
        self.headers['Referer'] = "https://lilab.jysw.suda.edu.cn/research/PremPS/"

    def format_mutation(self, data: Union[str, Dict]) -> str:
        return f"{data.chain}\t{data.mutation[:-1]}\t{data.mutation[-1]}"

    async def send_query(self, session, index):
        if await self.get(session, self.data.loc[index], self.__csrf_handler, index):
            return await super().send_query(session, index)
        return False

    async def default_get_handler(self, index, response, session):
        _text = await response.text()
        if 'This page will reload automatically in 30 seconds' in _text:
            return False
        _df = self.html_parser.with_pandas(_text, index=1)
        _df = _df.rename(
            {'Mutation': 'mutation', 'Mutated Chain': 'chain', 'ΔΔG': 'DDG'}, axis=1
        )
        _df = _df.drop(['Structure', 'Location'], axis=1)
        _df['identifier'] = self.data.loc[index, 'identifier']
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        self._prediction_results.append(_df)
        return True

    async def __save_mutations_handler(self, index, response, session):
        _text = await response.text()
        if not 'Job submitted' in _text:
            return False
        self.data.update_status(index, status.Waiting())
        self.data.loc[index, 'url'] = str(response.url)
        return True

    async def __save_partners_handler(self, index, response, session):
        _text = await response.text()
        if 'Select Mutations' not in _text:
            return False

        self.data.loc[index, 'url'] = str(response.url).replace('set_mutations', 'save_mutations')
        self.data.loc[index, 'payload'] = self.make_form(
            {
                'csrfmiddlewaretoken': self.data.loc[index, 'csrf'],
                'mode': '',
                'muta_file': File(
                    self.prepare_mutation(self.data.loc[index]), "mutations.txt"
                ).to_plain_text()
            }
        )
        return await self.post(session, self.data.loc[index], self.__save_mutations_handler, index)

    async def default_post_handler(self, index, response, session):
        _text = await response.text()
        self.data.update_status(index, status.Processing())
        self.data.loc[index, 'url'] = str(response.url).replace('set_partners', 'save_partners')
        session.headers['Referer'] = str(response.url)
        chains = re.search(
            r"var chain_data = {'chain_models': \[([\w_,\s']*)\],", _text
        ).group(1).replace("'", "").split(',')

        _muts = [mut['chain'] for mut in self.data.loc[index, 'mutation']]
        _payload = {'csrfmiddlewaretoken': self.data.loc[index, 'csrf']}

        for _index, chain in enumerate(chains):
            if  chain[0] in _muts:
                _muts.remove(chain[0])
                _payload[f'chains.{_index + 1}'] = f"{chain.strip()}.P1"
            else:
                _payload[f'chains.{_index + 1}'] = f"{chain.strip()}.no"

        _data = {'url': self.data.loc[index, 'url'], 'payload': _payload}
        return await self.post(session, _data, self.__save_partners_handler, index)

    async def __csrf_handler(self, index, response, session):
        _text = await response.text()
        if 'csrftoken' not in response.cookies:
            return False
        _csrf = response.cookies['csrftoken'].value
        self.data.loc[index, 'payload']['csrfmiddlewaretoken'] = _csrf
        self.data.loc[index, 'csrf'] = _csrf
        self.data.loc[index, 'url'] = 'https://lilab.jysw.suda.edu.cn/research/PremPS/upload_pdb'
        return True
