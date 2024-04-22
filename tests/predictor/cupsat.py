import numpy as np
from benchstab.predictors.web import CUPSATPdbID
from ._template import _TemplateCorrectInputTests


class CorrectInputTests(_TemplateCorrectInputTests):

    def setUp(self) -> None:
        super().setUp()
        self.pred = CUPSATPdbID

    async def test_default(self):
        results = await self.get_prediction("1CSE L45G I")
        self.assertTrue(len(results) > 0)
        self.assertEqual(
            len([val for val in results.identifier.values if val.id != '1CSE']), 0
        )
        self.assertEqual(
            len([val for val in results.status.values if val != 'finished']), 0
        )
        self.assertTrue(
            np.nan not in [float(val) for val in results.DDG.values]
        )
