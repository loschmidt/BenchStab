import platform
import unittest

import asyncio

from benchstab.preprocessor import Preprocessor
from benchstab.predictors.base import BasePredictor
from benchstab.utils.dataset import PredictorDataset
import asyncio


if 'Windows' in platform.system():
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class _TemplateCorrectInputTests(unittest.IsolatedAsyncioTestCase):

    input_folder = "tests/inputs"

    def setUp(self) -> None:
        self.parser = Preprocessor("", verbose=False)
        self.config = {
            'wait_interval': 60,
            'verbose': False,
            'max_retries': 10
        }
        self.pred = BasePredictor

    async def get_prediction(self, data_input):
        return await self.pred(
            data=PredictorDataset(self.parser.parse_line(data_input, ' ').to_dict(), index=[0]),
            **self.config
        ).compute()
