import numpy as np
from ._template import _TemplateCorrectInputTests
from benchstab.predictors.web import AutoMutePdbID


class CorrectInputTests(_TemplateCorrectInputTests):
    
    def setUp(self) -> None:
        super().setUp()
        self.pred = AutoMutePdbID

    async def test_default(self):
        results = await self.get_prediction("1CSE L45G I")
        self.assertEqual(len(results), 1)
        self.assertTrue(results.loc[0, 'identifier'].id == '1CSE')
        self.assertTrue(results.loc[0, 'status'] == 'finished')
        self.assertNotEqual(float(results.loc[0, 'DDG']), np.nan)
