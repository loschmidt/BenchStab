import numpy as np
from ._template import _TemplateCorrectInputTests
from benchstab.predictors.web import (
    mCSMPdbFile
)


class CorrectInputTests(_TemplateCorrectInputTests):

    async def test_defualt_pdbfile(self):
        self.pred = mCSMPdbFile
        results = await self.get_prediction(f"{self.input_folder}/1CSE.pdb L45G I")
        self.assertEqual(len(results), 1)
        self.assertTrue(results.loc[0, 'identifier'].id == f"{self.input_folder}/1CSE.pdb")
        self.assertTrue(results.loc[0, 'status'] == 'finished')
        self.assertNotEqual(float(results.loc[0, 'DDG']), np.nan)
