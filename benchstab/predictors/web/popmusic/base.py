import hashlib
import re
from dataclasses import dataclass
import pandas as pd
from benchstab.utils.structure import File
from benchstab.utils.aminoacids import Mapper
from benchstab.predictors.base import (
    BaseAuthentication,
    BaseCredentials,
    PredictorFlags,
    BaseGetPredictor,
)
from benchstab.utils import status


@dataclass
class PoPMuSiCCredentials(BaseCredentials):
    def get_payload(self, csrf):
        return {
            "_csrf_token": csrf,
            "_username": self.username,
            "_password": self.password,
            "_submit": "Login",
        }


class _PoPMuSiC(BaseAuthentication, BaseGetPredictor):
    """
    PoPMuSiC predictor class.

    Webserver:
        https://soft.dezyme.com
    
    Accepted inputs:
        * PDB structure file
    
    Availability:
        |PoPMuSiC|

    Default configuration for :code:`PoPMuSiC` predictor defined in :code:`config.json` syntax is:

        .. code-block:: python

            "popmusic": {
                "wait_interval": 60,
                "batch_size": 5,
                "max_retries": 100,
                "username": "",
                "password": ""
            }   
    
    Citation:
        Yves Dehouck and others, Fast and accurate predictions of protein stability changes upon mutations using statistical potentials and neural networks: PoPMuSiC-2.0, Bioinformatics, Volume 25, Issue 19, October 2009, Pages 2537–2543, https://doi.org/10.1093/bioinformatics/btp445
    """

    url = "https://soft.dezyme.com"

    credentials = PoPMuSiCCredentials

    def __init__(
        self,
        flags: PredictorFlags = None,
        batch_size: int = 5,
        wait_interval: int = 60,
        *args,
        **kwargs,
    ) -> None:
        flags = flags or PredictorFlags(
            webkit=True,
            group_mutations=True,
            group_mutations_by=["identifier"],
            mutation_delimiter="\n",
        )
        super().__init__(
            flags=flags, wait_interval=wait_interval, batch_size=batch_size, *args, **kwargs
        )
        self.data["url"] = "https://soft.dezyme.com/login"
        self.data["csrf"] = ""
        self.data["mutfile_name"] = ""
        self.data["mutation_id"] = ""
        self.data["result_id"] = ""
        self.data["result_token"] = ""
        self.data["mutfile_token"] = ""
        self._credentials.url = "https://soft.dezyme.com/login_check"

    async def __csrf_handler(self, index, response, session):
        self.data.update_status(index, status.Authenticaton())
        self.data.loc[index, "csrf"] = self.html_parser.with_xpath(
            xpath="//input[@name='_csrf_token']/@value", html=await response.text(), index=None
        )
        self.data.loc[index, "url"] = "https://soft.dezyme.com/mutfile/list"
        return True

    # FIXME does not match signature of parent class
    async def login(self, session, index):
        if await self.get(
            session, self.data.loc[index], self.__csrf_handler, index
        ):
            return await super().login(
                session, index, login_extra={"csrf": self.data.loc[index, "csrf"]}
            )
        return False

    async def __open_submission(self, index, response, session):
        mutfile_token = self.html_parser.with_xpath(
            xpath="//input[@name='form[_token]']/@value", html=await response.text()
        )
        self.data.update_status(index, status.Processing())
        self.data.loc[index, "url"] = "https://soft.dezyme.com/mutfile/upload"
        _name = (
            str(
                int(
                    hashlib.sha1(
                        self.prepare_mutation(self.data.loc[index]).encode("utf-8")
                    ).hexdigest(),
                    16,
                )
            )
            + ".txt"
        )
        self.data.loc[index, "mutfile_name"] = _name
        self.data.loc[index, "payload"].update(
            {
                "form[pdbName]": self.data.loc[index, "identifier"].id,
                "form[pathFile]": f"C:\\fakepath\\{_name}.txt",
                "form[file]": File(
                    self.prepare_mutation(self.data.loc[index]), _name
                ).to_plain_text(),
                "form[pdbType]": "public",
                "form[_token]": mutfile_token,
            }
        )
        return True

    def format_mutation(self, data) -> str:
        return (
            f"{data.chain + data.mutation[1:-1]} "
            f"{Mapper.one_to_three_letter(data.mutation[0])} "
            f"{Mapper.one_to_three_letter(data.mutation[-1])}"
        )

    async def __submit_request(self, index, response, session):
        _text = await response.text()
        if response.status != 200:
            return False
        _protein_id = re.search(r"queryChoicePdb\(\"(\d+)\"", _text).group(1)
        _token = self.html_parser.with_xpath(
            xpath="//input[@name='queryProcessForm[_token]']/@value", html=_text
        )
        self.data.loc[index, "url"] = "https://soft.dezyme.com/query/build/pop"
        _payload = {
            "pdbId": _protein_id,
            "mutfileId": self.data.loc[index, "mutation_id"],
            "queryProcessForm[mode]": "file",
            "queryProcessForm[_token]": _token,
        }
        _data = {"payload": _payload, "url": "https://soft.dezyme.com/query/build/pop"}
        return await self.post(session, _data, self.__submission_handler, index)

    async def __submission_handler(self, index, response, session):
        if response.status != 200:
            return False
        self.data.loc[index, "url"] = response.url
        self.data.update_status(index, status.Waiting())
        return True

    async def default_post_handler(self, index, response, session):
        _href = None
        _filename = self.data.loc[index, "mutfile_name"]
        for _td in self.html_parser.with_xpath(
            xpath=".//tr[@class='mutfile']", html=await response.text(), index=None
        ):
            _name = _td.find(".//input[@name='mutfileForm[name]']")
            if _name is not None and _name.attrib["value"] == _filename:
                _href = _td.find(".//a[@class='process-action']").attrib["href"]
                self.data.loc[index, "mutfile_token"] = _td.find(
                    ".//input[@id='deleteForm__token']"
                ).value
                break
        if _href is None:
            return False
        self.data.loc[index, "url"] = "https://soft.dezyme.com" + _href + "/pop"
        self.data.loc[index, "mutation_id"] = _href.rsplit("/", 2)[-1]
        return await self.get(
            session, self.data.loc[index], self.__submit_request, index
        )

    async def send_query(self, session, index):
        if await self.get(session, self.data.loc[index], self.__open_submission, index):
            return await super().send_query(session, index)
        return False

    async def __extract_results(self, index, response, session):
        _text = await response.text()
        _rows = _text.split(re.search(r"----+.*", _text).group(0), 2)[-1].split("\n")
        records = []
        for row in filter(None, _rows):
            _row = row.split()
            _res = {
                "identifier": self.data.loc[index, "identifier"],
                "chain": _row[0],
                "mutation": (
                    Mapper.three_to_one_letter(_row[2])
                    + _row[1]
                    + Mapper.three_to_one_letter(_row[3])
                ),
                "DDG": _row[-1],
            }
            records.append(_res)
        self.data.loc[index, 'url'] = response.url
        return records

    async def __delete(self, index, response, session):
        _data = {
            "url": (
                "https://soft.dezyme.com/result/delete/"
                f"{self.data.loc[index, 'result_id']}.json"
            ),
            "payload": {
                "form[id]": self.data.loc[index, "result_id"],
                "form[_token]": self.data.loc[index, "result_token"],
            },
        }
        if await self.post(session, _data, self.async_default_callback, index):
            return False
        _data = {
            "url": (
                "https://soft.dezyme.com/mutfile/delete/"
                f"{self.data.loc[index, 'mutation_id']}.json"
            ),
            "payload": {
                "deleteForm[id]": self.data.loc[index, "mutation_id"],
                "deleteForm[_token]": self.data.loc[index, "mutfile_token"],
            },
        }
        return not await self.post(session, _data, self.async_default_callback, index)

    async def default_get_handler(self, index, response, session):
        _data = []
        for _tr in reversed(
            self.html_parser.with_xpath(
                xpath=".//table[@id='results']/tbody/tr", html=await response.text(), index=None
            )
        ):
            _result_id = _tr.attrib["id"]
            _pdb = _tr.find(".//div[@class='wrapper']").text.replace(".pdb", "")
            if _pdb == self.data.loc[index, "identifier"].id:
                if _tr.find(".//td[@class='results inProcess']") is not None:
                    return False
                self.data.loc[index, "result_id"] = _result_id.split('_')[-1]
                self.data.loc[index, "result_token"] = _tr.find(
                    ".//form[@class='delete']/input[@id='form__token']"
                ).value
                _payload = {
                    "url": "https://soft.dezyme.com/result/download/"
                    + _result_id
                    + ".pop"
                }
                _data = await self.get(session, _payload, self.__extract_results, index)
                break
        self._prediction_results.append(pd.DataFrame(_data).drop_duplicates())
        self.data.update_status(index, status.Finished())
        return await self.__delete(index, response, session)
