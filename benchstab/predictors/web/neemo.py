from typing import Dict

import pandas as pd
from lxml import html
from benchstab.utils.aminoacids import Mapper
from benchstab.predictors.base import (
    PredictorFlags,
    BaseGetPredictor
)

# TODO implementation is failing, needs to be finished

class NeEMO(BaseGetPredictor):
    def __init__(self, data: pd.DataFrame, flags: PredictorFlags = None, *args, **kwargs) -> None:
        flags = flags or PredictorFlags(
            webkit=True,
            group_mutations=True,
            group_mutations_by=['identifier', 'chain'],
            mutation_delimiter='#'
        )
        super().__init__(data=data, flags=flags, *args, **kwargs)
        self.data['url'] = 'http://protein.bio.unipd.it/neemo/NeemoProcess.jsp'
        self.blocking_statuses = ['waiting', 'processing']

    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'pdbcode': row['identifier'].id,
            'chain': row['chain'],
            'pdbfile':row['identifier'].to_octet_stream(),
            'Process PDB': 'Odeslat'
        }

    async def default_post_handler(self, index, response, session):
        _text = await response.text()
        _cond = 'The process is still running' in _text
        if _cond:
            if 'NeemoProcess.jsp' in self.data.loc[index, 'url']:
                self.data.loc[index, 'status'] = 'processing'
            else:
                self.data.loc[index, 'status'] = 'waiting'
            _tree = html.fromstring(_text)
            _url = _tree.xpath('//meta[@http-equiv="refresh"]/@content')[0]
            self.data.loc[index, 'url'] = _url[_url.index('URL=')+4:]
        return _cond

    async def retrieve_result(self, session, index) -> bool:
        if not self.data.is_blocking_status(index):
            return True
        if self.data.loc[index, 'status'] == 'processing':
            await self.get(session, self.data.loc[index], self.__processing_handler, index)
        if self.data.loc[index, 'status'] == 'waiting':
            await self.get(session, self.data.loc[index], self.__waiting_handler, index)
        return False

    async def __waiting_handler(self, index, response, session):
        _text = await response.text()
        _tree = html.fromstring(_text) 
        _data = _tree.xpath('//div[@id="content"]/table/tr/td/pre/text()')
        if len(_data) < 2:
            return False
        print(_text)
        print(response.url)
        mutations = []
        for prediciton in _data[1:]:
            prediciton = prediciton.split()[-1]
            _mut = (
                self.data.loc[index, 'fasta'].sequence[prediciton[0]]
                + prediciton[0]
                + Mapper.three_to_one_letter(prediciton[1])
            )
            mutations.append(
                {
                    'identifier': self.data.loc[index, 'identifier'],
                    'chain': self.data.loc[index, 'chain'],
                    'mutation': _mut
                }
            )
        return True

    async def __processing_handler(self, index, response, session):
        _text = await response.text()
        _tree = html.fromstring(_text)
        if _tree.xpath('//button[@name="mutatebutton"]'):
            _backid = _tree.xpath('//input[@name="backid"]/@value')[0]
            _dir = _tree.xpath('//input[@name="dir"]/@value')[0]
            _seq = _tree.xpath('//input[@name="sequence"]/@value')[0]
            _pdbfile = _tree.xpath('//input[@name="pdbfile"]/@value')[0]
            self.data.loc[index, 'url'] = 'http://protein.bio.unipd.it/neemo/NeEMO.jsp'
            _payload = {
                'emailaddress': '',
                'name': '',
                'dir': _dir,
                'chain': self.data.loc[index, 'chain'],
                'backid': _backid,
                'sequence': _seq,
                'mutationtext': self.prepare_mutation(self.data.loc[index]) + '#',
                'mutationquick': '',
                'pdb_file': _pdbfile,
                'temp': self.data.loc[index, 'temperature'],
                'ph': self.data.loc[index, 'ph'],
                'Submit Query': 'Odeslat'
            }
            _data = {
                'url': self.data.loc[index, 'url'],
                'payload': self.make_form(_payload)
            }
            return await self.post(session, _data, self.default_post_handler, index)
        return False
