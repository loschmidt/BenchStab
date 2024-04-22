import re
from urllib.parse import urlencode
from typing import Dict
import pandas as pd
from benchstab.predictors.base import (
    BaseAuthentication,
    BaseCredentials,
    PredictorFlags,
    BaseGetPredictor
)


class _Eris(BaseAuthentication, BaseGetPredictor):
    def __init__(
            self,
            login_settings: BaseCredentials = None,
            flags: PredictorFlags = None,
            backbone: str = None,
            prerelax: str = None,
            *args,
            **kwargs
    ) -> None:
        flags = flags or PredictorFlags(
            webkit=True, group_mutations_by=['pdb_id', 'chain']
        )
        super().__init__(login_settings=login_settings, flags=flags, *args, **kwargs)
        self.backbone = backbone or 'flexible'
        self.prerelax = prerelax or 'false'
        self._method = '1' if self.backbone == 'flexible' else '0'
        self._prerelax = 'true' if self.prerelax == 'yes' else 'false'
        self.data['url'] = "https://dokhlab.med.psu.edu/eris/submit3.php"
        self._credentials.url ="https://dokhlab.med.psu.edu/eris/login_check.php"

    async def __submit_handler(self, index, response, session):
        _text = await response.text()
        print(_text)
        self.data.loc[index, 'status'] = 'finished'
        return True

    async def default_post_handler(self, index, response, session):
        _text = await response.text()
        if not 'myPdbHash' in _text:
            return False
        _hash = re.search(r"myPdbHash = '(\w+)'", _text).group(1)
        _payload = {
            'method': self._method,
            'prerelax': self._prerelax,
            'hash': _hash,
            'mut': self.prepare_mutation(self.data.loc[index]),
            'emailFlag': 'false'
        }
        self.data.loc[index, 'status'] = 'waiting'
        self.data.loc[index, 'url'] = "https://dokhlab.med.psu.edu/eris/submit2sub.php?" + urlencode(_payload)
        self.data.loc[index, 'payload'].clear()

        print(_payload)
        _data = {'url': self.data.loc[index, 'url'], 'payload': _payload}
        print(self.data.loc[index, 'payload'])
        return await self.get(session, _data, self.__submit_handler, index)


class ErisPdbID(_Eris):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'pdbid': row['identifier'].id,
            'MAX_FILE_SIZE': '1000000',
            'uploadedfile': ''
        }


class ErisPdbFile(_Eris):
    def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'pdbid': '',
            'MAX_FILE_SIZE': '1000000',
            'uploadedfile': row['identifier'].to_octet_stream()
        }
