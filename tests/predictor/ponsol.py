import numpy as np
from ._template import _TemplateCorrectInputTests
from benchstab.predictors.web import PONSol2Sequence


class CorrectInputTests(_TemplateCorrectInputTests):

    async def test_default_sequence(self):
        self.pred = PONSol2Sequence
        results = await self.get_prediction(f"{self.input_folder}/1CSE.fasta L45G I")
        self.assertEqual(len(results), 1)
        self.assertTrue('1CSE' in results.loc[0, 'identifier'].id)
        self.assertTrue(results.loc[0, 'status'] == 'finished')
        self.assertTrue(results.loc[0, 'DDG'] == 'decrease')
