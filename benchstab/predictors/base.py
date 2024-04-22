import re
import os
import random
import string
import urllib3
import logging
import asyncio
import warnings
from dataclasses import dataclass, field
from typing import (
    Callable,
    List,
    Dict,
    Any,
    Union,
)

import requests
import aiohttp
import numpy as np

from benchstab.utils.dataset import PredictorDataset, DatasetRow
from benchstab.utils.html_parser import HTMLParser
from benchstab.utils import status
from benchstab.utils.exceptions import (
    HTMLParserError,
    PredictorError,
    DatasetError
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class PredictorFlags:
    """
    Class for storing predictor flags. The flags are used to control the behaviour of the predictor.
    """
    webkit: bool = False
    group_mutations: bool = False
    group_mutations_by: list[str] = field(default_factory=list)
    mutation_delimiter: str = ","


@dataclass
class BaseCredentials:
    """
    Base class for predictor credentials. The credentials are used to authenticate the user. The
    credentials are stored in a dictionary and sent as a POST request to the url specified in the
    credentials. The credentials class variable should be overwritten by the child class.
    """
    username: str = ""
    password: str = ""
    email: str = ""
    url: str  = ""

    def get_payload(self, **kwargs):
        """
        Create a dictionary of parameters to be sent as a POST request. This function should be
        implemented by the child class.

        
        :param kwargs: extra parameters
        :type kwargs: dict
        :return: dictionary of parameters
        :rtype: dict
        """
        return {
            'user': self.username,
            'pass': self.password
        }


@dataclass
class PredictorHeader:
    """
    Class for storing predictor headers. The predictor headers are used to identify the predictor.
    """
    name: str = ""
    input_type: str = ""
    classname: str = ""
    mutation_column: str = "mutation"

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, __value: object) -> bool:
        
        if isinstance(__value, str):
            return self.name.lower() == __value.lower()
        if not isinstance(__value, PredictorHeader):
            return False

        if 'Pdb' in self.classname and 'Pdb' in __value.classname:
            return self.name == __value.name
        return (
            self.name == __value.name
            and self.input_type == __value.input_type
        )

    def __ne__(self, __value: object) -> bool:
        return not self.__eq__(__value)

    def __hash__(self) -> int:
        return hash(self.name.lower())
    
    def __str__(self) -> str:
        return self.name


class BasePredictor:
    """
    Base class for predictors. The class is responsible for the following:
        1. Sending the query to the predictor.
        2. Retrieving the results from the predictor.
        3. Aggregating the results.
        4. Returning the results as a PredictorDataset.
    """
    url = ""

    aggr_columns = {'mutation', 'fasta_mutation', 'chain'}
    # Redefine the credentials class variable in the child class if needed
    credentials = BaseCredentials


    @classmethod
    async def is_available_async(cls, url: str) -> str:
        """
        Check if the predictor is available. This is done by sending a GET request to the specified url.
        If the request is successful, the predictor is available.


        :param url: url of the predictor
        :type url: str
        :return: status of the predictor. 'Available' if the predictor is available, 'Offline' otherwise
        :rtype: str
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10, ssl=False) as response:
                    if response.status == 200:
                        return "Available"
                    return "Offline"
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            return "Offline"


    @classmethod
    def is_available(cls, url: str) -> str:
        """
        Check if the predictor is available. This is done by sending a GET request to the specified url.
        If the request is successful, the predictor is available.

        
        :param url: url of the predictor
        :type url: str
        :return: status of the predictor. 'Available' if the predictor is available, 'Offline' otherwise
        :rtype: str
        """
        try:
            r = requests.get(url, timeout=10, verify=False)
            if r.status_code == 200:
                return "Available"
            return "Offline"
        except requests.exceptions.RequestException:
            return "Offline"


    @classmethod
    def header(cls):
        """
        Return the header of the predictor. The header is used to identify the predictor.

        
        :return: predictor header
        :rtype: PredictorHeader
        """
        _name, _type, _ = re.split(r"(Sequence|PdbID|PdbFile)", cls.__name__, maxsplit=1)
        _mut = 'fasta_mutation' if 'Sequence' == _type else 'mutation'
        return PredictorHeader(_name, _type, cls.__name__, _mut)

    @classmethod
    async def async_default_callback(
        cls, index: int, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ):
        """
        Default callback function for the GET request. It checks if the request was successful
        and updates the status of the row accordingly.

        
        :param index: index of the row
        :type index: int
        :param response: response of the GET request
        :type response: aiohttp.ClientResponse
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :return: True if the request was successful, False otherwise
        :rtype: bool
        """
        return response.status != 200

    def __init__(
            self,
            data: PredictorDataset,
            flags: PredictorFlags = None,
            outfolder: str = None,
            username: str = "",
            email: str = "generic@email.com",
            password: str = "",
            wait_interval: int = 60,
            batch_size: int = -1,
            verbosity: int = 0,
            *args,
            **kwargs
    ) -> None:

        # Some predictors raise ResourceWarning, due to unclosed connections.
        # This seems to be a bug in aiohttp. It does not affect the flow of the program
        # and can be safely ignored.
        warnings.simplefilter('ignore', ResourceWarning)

        self.flags = flags or PredictorFlags(group_mutations_by=['identifier', 'chain', 'mutation'])
        self.html_parser = HTMLParser()
        self._header = self.__class__.header()
        self.results = data
        self.data = data.copy()

        self.logger = logging.getLogger(self._header.classname)
        self.logger.setLevel(logging.ERROR)

        if verbosity == 2:
            _handler = logging.StreamHandler()
            _formatter = logging.Formatter('%(message)s')
            _handler.setFormatter(_formatter)
        if verbosity == 1:
            # Force windows to display ANSI escape codes properly
            os.system("")
            # Create a handler to overwrite the previous line
            _handler = logging.StreamHandler()
            # Create a formatter to delete the previous line and replace it with the new one
            # The individual ANISI escape codes are:
            #   \r - carriage return
            #   \x1b[80D - move the cursor 80 characters to the left
            #   \x1b[1A - move the cursor 1 line up, since logger adds newlines by itself
            #   \x1b[K - clear the line
            _formatter = logging.Formatter('\r\x1b[80D\x1b[1A\x1b[K%(message)s')
            _handler.setFormatter(_formatter)
        if verbosity > 0:
            self.logger.setLevel(logging.INFO)
            self.logger.handlers.clear()
            self.logger.propagate = False
            self.logger.addHandler(_handler)

        self.data.logger = self.logger
        self.batch_size = batch_size

        self.data["_start_time"] = 0.0
        self.data["Elapsed Time (sec.)"] = 0.0

        self.data["status"] = status.NotStarted()
        self.data['timeout'] = 0
        self.data['DDG'] = np.nan

        self.data['predictor'] = self._header.name
        self.data['input_type'] = self._header.input_type
        self.boundary = (
            '----WebKitFormBoundary' + ''.join(
                random.sample(string.ascii_letters + string.digits, 16)
            )
        )
        self.headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/107.0.0.0 Safari/537.36'
            )
        }
        self._credentials = self.__class__.credentials(username, password, email)
        self._prediction_results = []
        self._verbosity = verbosity
        self._wait_interval = wait_interval

    def process_result(self, index: int, mutation: str, chain: str, result: Any) -> None:
        _results = self.data.loc[index].copy()
        _results
        self.data.update_status(index, status.Finished())
        self._prediction_results.append(result)

    def format_mutation(self, data: Union[str, Dict, DatasetRow]) -> str:
        """
        Format the mutation to the format required by the predictor. This function should be
        implemented by the child class.

        
        :param data: mutation
        :type data: Union[str, Dict, DatasetRow]
        :return: formatted mutation
        :rtype: str
        """
        return data[self._header.mutation_column]

    def prepare_mutation(self, row: DatasetRow) -> str:
        """
        Prepare the mutation to be sent to the predictor.
        
        This function performs the following steps:
            1. Convert the mutation to the format required by the predictor.
            2. Group the mutations if needed.
        
        
        :param row: row of the dataset
        :type row: DatasetRow
        :return: mutation
        :rtype: str
        """
        if isinstance(row[self._header.mutation_column], str):
            return self.format_mutation(row)
        elif isinstance(row[self._header.mutation_column], list):
            return f"{self.flags.mutation_delimiter}".join(
                [self.format_mutation(mut) for mut in row[self._header.mutation_column]]
            )
        return row[self._header.mutation_column]

    async def send_query(
        self, session: aiohttp.ClientSession, index: int, *args, **kwargs
    ) -> bool:
        """
        Send the query to the predictor. This function should be implemented by the child class.

        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param index: index of the row
        :type index: int
        :return: True if the query was sent successfully, False otherwise
        :rtype: bool
        """
        return await self.post(
            session,
            self.data.loc[index],
            BasePredictor.async_default_callback,
            index,
            *args,
            **kwargs
        )

    async def retrieve_result(self, session: aiohttp.ClientSession, index: int) -> bool:
        """
        Retrieve the results of the prediction.
        This function should be implemented by the child class.

        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param index: index of the row
        :type index: int
        :return: True if the prediction was successful, False otherwise
        :rtype: bool
        """
        return True

    def __prepare_payload(self, row: DatasetRow) -> Dict:
        """
        Wrapper around the prepare_payload function. It catches any exceptions
        and updates the status of the row accordingly.

        
        :param row: row of the dataset
        :type row: DatasetRow
        :return: payload
        :rtype: dict
        """
        try:
            return self.prepare_payload(row)
        except DatasetError as exc:
            self.data.update_status(
                row.name, status.ParsingFailed(message=f"{exc.__class__.__name__}: {exc}")
            )
            return {}


    def prepare_payload(self, row: DatasetRow) -> Dict:
        """ 
        Prepare the payload to be sent to the predictor.
        This function should be implemented by the child class.

        
        :param row: row of the dataset
        :type row: DatasetRow
        :return: payload
        :rtype: dict
        """
        return {}

    def get_results(self) -> PredictorDataset:
        """
        Get the results of the prediction.

        :return: prediction results
        :rtype: PredictorDataset
        """
        if self._prediction_results:
            _res = PredictorDataset.concat(self._prediction_results)
            _res = _res.merge(
                self.data,
                how='right',
                on=self.flags.group_mutations_by,
                suffixes=(None, '_to_delete')
            )
        else:
            if self.flags.group_mutations:
                _res = self.data.explode(['mutation'])
                _res = PredictorDataset.concat(
                    [_res.drop(['mutation'], axis=1), _res.mutation.apply(DatasetRow)], axis=1
                )
                _res = _res.loc[:, ~_res.columns.duplicated()]
                _res.rename(columns={0: 'mutation'}, inplace=True)
            else:
                _res = self.data.copy(deep=True)
        return _res.format_to_output(self._verbosity)

    def _aggregate(self, data) -> List[Dict[Any, Any]]:
        """
        Helper function aggregating the data into a list of dictionaries.

        :param data: data to be aggregated
        :type data: PredictorDataset
        :return: aggregated data
        :rtype: list[DatasetRow]
        """
        return [row for _, row in data.iterrows()]

    def setup(self) -> None:
        """
        Set up the dataset. This includes grouping mutations, creating the payload, etc.
        """
        if self.flags.group_mutations:
            _data_cols = BasePredictor.aggr_columns - set(self.flags.group_mutations_by)

            _mutations = self.data \
                .groupby(self.flags.group_mutations_by)[list(_data_cols)] \
                .apply(self._aggregate) \
                .reset_index(name='mutation')
            _fasta_mutations = self.data \
                .groupby(self.flags.group_mutations_by)[list(_data_cols)] \
                .apply(self._aggregate) \
                .reset_index(name='fasta_mutation')

            self.data = self.data \
                .drop(['mutation', 'fasta_mutation'], axis=1) \
                .groupby(self.flags.group_mutations_by) \
                .head(1) \
                .merge(_mutations, how='left', on=self.flags.group_mutations_by) \
                .merge(_fasta_mutations, how='left', on=self.flags.group_mutations_by)
            
            # As the dataset was re-created, we need to re-apply the logger
            self.data.logger = self.logger
        self.data['payload'] = self.data.apply(self.__prepare_payload, axis=1)

    async def __exception_wrapper(
        self,
        func: Callable,
        index: int = None,
        *args, **kwargs
    ) -> bool:
        """
        Wrapper around the async functions. It catches any exceptions
        and updates the status of the row accordingly. If the exception is
        HTMLParserError with permissive=True, it returns False, otherwise it returns True.

        
        :param func: function to be executed
        :type func: Callable
        :param index: index of the row
        :type index: int
        :return: True if the function was executed successfully, False otherwise
        :rtype: bool
        """
        _status = None
        _retval = True
        try:
            _retval = await func(index=index, *args, **kwargs)
        except HTMLParserError as e:
            if e.permissive:
                return False
            else: 
                _status = status.ParsingFailed(message=f"{e.__class__.__name__}: {e}")
        except (PredictorError, DatasetError) as e:
            _status = f"{e.__class__.__name__}: {e}"
        except aiohttp.ClientConnectionError as exc:
            _status = status.ConnectionFailed(message=f"{exc.__class__.__name__}: {exc}")
        except (IndexError, ValueError, AttributeError) as exc:
            _status = status.ParsingFailed(message=f"{exc.__class__.__name__}: {exc}")
        except Exception as exc:
            _status = status.Failed(message=f"{exc.__class__.__name__}: {exc}")
        if _status is not None and index is not None:
            self.data.update_status(index, _status)
        return _retval

    async def login(
            self, session: aiohttp.ClientSession, index: int, login_extra: Dict[str, Any] = None
    ) -> bool:
        """
        Login to the predictor. This function should be implemented by the child class.
        
        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param index: index of the row
        :type index: int
        :param login_extra: extra parameters for the login function
        :type login_extra: dict
        :return: True if the login was successful, False otherwise
        :rtype: bool
        """
        return True

    async def _queue_prediction(self, queue):
        """
        Create a queue of tasks to be executed in parallel. The queue is created from the
        indices of the dataset. The queue is filled until it reaches the batch_size. If the
        queue is full, the function waits for the queue to be emptied. If the dataset is
        exhausted, the function returns.

        
        :param queue: queue of tasks
        :type queue: asyncio.Queue
        """
        _index_list = iter(self.data.index.tolist())
        while True:
            if queue.full():
                await asyncio.sleep(self._wait_interval)
                continue
            index = next(_index_list, None)
            if index is None:
                break
            await queue.put(index)
            await asyncio.sleep(0.1)

    async def compute(self):
        """ 
        The main function of the predictor.
        
        It is responsible for the following:
            #. Check if the predictor is available (if not, return immediately).
            #. Set up the dataset (group mutations, etc.)
            #. Create a queue of tasks to be executed in parallel.
            #. Create a queue of workers to execute the tasks.
            #. Wait for all tasks to be completed (join the queue).
            #. Return the results as a PredictorDataset.

        :return: prediction results
        :rtype: PredictorDataset
        """
        if await self.is_available_async(self.url) == "Offline":
            self.logger.warning(
                "WARNING:%s(0/%d): Predictor is not available. Please try again later.",
                self._header.classname, len(self.data)
            )
            self.data['status'] = status.PredictorNotAvailable()
            return self.data.format_to_output(self._verbosity)

        self.setup()
        if self.batch_size < 1 or self.batch_size > len(self.data):
            self.batch_size = len(self.data)
        queue = asyncio.Queue(maxsize=self.batch_size)
        _preds = [
            asyncio.create_task(self._run_prediction(queue)) for _ in range(self.batch_size)
        ]
        _queue = [asyncio.create_task(self._queue_prediction(queue))]
        await asyncio.gather(*_queue)
        await queue.join()
        for pred in _preds:
            pred.cancel()
        _res = self.get_results()
        return _res

    async def _run_prediction(self, queue):
        """
        Run the prediction. This function is executed in parallel by the workers.
        
        It takes an index from the queue and executes the following steps:
            #. Login to the predictor.
            #. Send the query to the predictor.
            #. Retrieve the results from the predictor.

        :param queue: queue of tasks
        :type queue: asyncio.Queue
        """
        while True:
            index = await queue.get()
            async with aiohttp.ClientSession(
                headers=self.headers,
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                connector = aiohttp.TCPConnector(force_close=True)
            ) as session:
                self.data.start_timer(index)
                if not await self.login(session, index):
                    queue.task_done()
                    continue
                if not await self.send_query(session, index):
                    queue.task_done()
                    continue
                while not await self.retrieve_result(session, index):
                    if self.data.loc[index, 'timeout'] == 0:
                        self.data.update_status(index, status.Timeout())
                        break
                    self.data.loc[index, 'timeout'] -= 1
                    await asyncio.sleep(self._wait_interval)
                queue.task_done()

    def make_form(self, payload):
        """
        Create a multipart form from a dictionary of parameters. 
        Since the current version (==3.8.5) of aiohttp does not support
        assigning a custom boundary to the FormData object directly, we need to create
        a custom MultipartWriter and assign it to the FormData object.
        
        :param payload: dictionary of parameters
        :type payload: dict
        :return: multipart form
        :rtype: aiohttp.FormData
        """
        if not self.flags.webkit:
            return payload
        _payload = aiohttp.FormData()
        _payload._writer = aiohttp.MultipartWriter("form-data", boundary=self.boundary)
        _payload._is_multipart = True
        for key, value in payload.items():
            if isinstance(value, dict):
                _payload.add_field(key, **value)
            else:
                _payload.add_field(key, value)
        return _payload

    async def __get(
        self,  session: aiohttp.ClientSession, callback: Callable, index: int, *args, **kwargs
    ) -> bool:
        """
        Wrapper around the aiohttp GET request. It catches any exceptions
        and updates the status of the row accordingly.

        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param callback: callback function
        :type callback: Callable
        :param index: index of the row
        :type index: int
        :return: result of the callback function
        :rtype: bool
        """
        async with session.get(*args, **kwargs, ssl=False) as response:
            _retcode = await callback(index, response, session)
            #session.cookie_jar.update_cookies(response.cookies)
            return _retcode

    async def get(
        self,
        session: aiohttp.ClientSession,
        dataset: Union[DatasetRow, Dict],
        callback: Callable,
        index: int = None,
        *args,
        **kwargs
    ) -> bool:
        """
        Send a GET request to the predictor. The request is sent to the url specified in the
        dataset. The response is handled by the callback function. The callback function
        should return True if the request was successful, False otherwise. If the callback
        function is not specified, the default callback function is used.

        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param dataset: dataset
        :type dataset: Union[DatasetRow, Dict]
        :param callback: callback function
        :type callback: Callable
        :param index: index of the row
        :type index: int
        :return: result of the callback function
        :rtype: bool
        """
        kwargs['url'] = dataset['url']
        return await self.__exception_wrapper(
            self.__get, session=session, callback=callback, index=index, *args, **kwargs
        )

    async def __post(
        self,  session: aiohttp.ClientSession, callback: Callable, index: int, *args, **kwargs
    ) -> bool:
        """
        Wrapper around the aiohttp POST request. It catches any exceptions
        and updates the status of the row accordingly.

        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param callback: callback function
        :type callback: Callable
        :param index: index of the row
        :type index: int
        :return: result of the callback function
        :rtype: bool
        """
        async with session.post(timeout=None, *args, **kwargs) as response:
            return await callback(index, response, session)

    async def post(
        self,
        session: aiohttp.ClientSession,
        dataset: Union[DatasetRow, Dict],
        callback: Callable,
        index: int = None,
        *args,
        **kwargs
    ) -> bool:
        """
        Send a POST request to the predictor. The request is sent to the url specified in the
        dataset. The response is handled by the callback function. The callback function
        should return True if the request was successful, False otherwise. If the callback
        function is not specified, the default callback function is used.

        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param dataset: dataset
        :type dataset: Union[DatasetRow, Dict]
        :param callback: callback function
        :type callback: Callable
        :param index: index of the row
        :type index: int
        :return: result of the callback function
        """
        kwargs['data'] = dataset['payload']
        kwargs['url'] = dataset['url']
        return await self.__exception_wrapper(
            self.__post, session=session, callback=callback, index=index, *args, **kwargs
        )


class BasePostPredictor(BasePredictor):
    """
    Base class for predictors that require a POST request. The POST request is sent to the url
    specified in the dataset. The response is handled by the default_post_handler.
    """
    async def send_query(
        self, session: aiohttp.ClientSession, index: int, *args, **kwargs
    ) -> bool:
        """
        Send the query to the predictor. If the predictor is a form-data predictor, the query is
        sent as a multipart form. Otherwise, it is sent as a JSON object.

        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param index: index of the row
        :type index: int
        :return: True if the query was sent successfully, False otherwise
        :rtype: bool
        """
        _data = {
            'payload': self.make_form(self.data.loc[index, 'payload']),
            'url': self.data.loc[index, 'url']
        }
        return await self.post(
            session, _data, self.default_post_handler, index, *args, **kwargs
        )

    async def default_post_handler(
        self, index: int, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ):
        """
        Default callback function for the POST request. It checks if the request was successful
        and updates the status of the row accordingly.

        
        :param index: index of the row
        :type index: int
        :param response: response of the POST request
        :type response: aiohttp.ClientResponse
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :return: True if the request was successful, False otherwise
        :rtype: bool
        """
        return True


class BaseAuthentication(BasePostPredictor):
    """
    Base class for predictors that require authentication. The authentication is done by sending
    a POST request to the url specified in the credentials. The response is handled by the login_handler.
    """
    async def login(
            self, session: aiohttp.ClientSession, index: int, login_extra: Dict[str, Any] = None
    ) -> bool:
        """
        Login to the predictor. The login is done by sending a POST request to the url specified
        in the credentials. The response is handled by the login_handler function. The login_handler
        function should return True if the login was successful, False otherwise. The function uses the
        credentials specified in the credentials class variable.

        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param index: index of the row
        :type index: int
        :param login_extra: extra parameters for the login function
        :type login_extra: dict
        :return: True if the login was successful, False otherwise
        :rtype: bool
        """
        login_extra = login_extra or {}
        _data = {
            'payload': self._credentials.get_payload(**login_extra),
            'url': self._credentials.url
        }
        return await self.post(session, _data, self.login_handler, index)

    async def login_handler(
        self, index: int, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ) -> bool:
        """
        Default callback function for the login request. It checks if the login was successful
        and updates the status of the row accordingly.

        
        :param index: index of the row
        :type index: int
        :param response: response of the login request
        :type response: aiohttp.ClientResponse
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :return: True if the login was successful, False otherwise
        :rtype: bool
        """
        return not await BasePredictor.async_default_callback(index, response, session)


class BaseGetPredictor(BasePostPredictor):
    """
    Base class for predictors that require a GET request. The GET request is sent to the url
    specified in the dataset. The response is handled by the default_get_handler.
    """
    def __init__(
            self, max_retries: int = 100,  *args, **kwargs
        ):
        super().__init__(*args, **kwargs)
        self.data['timeout'] = max_retries

    async def retrieve_result(
        self, session: aiohttp.ClientSession, index: int
    ) -> bool:
        """
        Retrieve the results of the prediction. The results are retrieved by sending a GET request
        to the url specified in the dataset. IF the datapoint is already processed, the function returns True,
        otherwise it returns the result of the default_get_handler function.

        
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :param index: index of the row
        :type index: int
        :return: True if the request was successful, False otherwise
        :rtype: bool
        """
        if not self.data.is_blocking_status(index):
            return True
        return await self.get(session, self.data.loc[index], self.default_get_handler, index)

    async def default_get_handler(
        self, index: int, response: aiohttp.ClientResponse, session: aiohttp.ClientSession
    ) -> bool:
        """
        Default callback function for the GET request. It checks if the request was successful
        and updates the status of the row accordingly.

        
        :param index: index of the row
        :type index: int
        :param response: response of the GET request
        :type response: aiohttp.ClientResponse
        :param session: aiohttp session
        :type session: aiohttp.ClientSession
        :return: True if the request was successful, False otherwise
        :rtype: bool
        """
        return True
