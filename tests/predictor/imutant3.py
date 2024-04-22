import numpy as np
from ._template import _TemplateCorrectInputTests
from benchstab.predictors.web import (
    IMutant3PdbFile,
    IMutant3PdbID,
    IMutant3Sequence
)


class CorrectInputTests(_TemplateCorrectInputTests):

    async def test_default_pdbid(self):
        self.pred = IMutant3PdbID
        results = await self.get_prediction("1CSE L45G I")
        self.assertEqual(len(results), 1)
        self.assertTrue(results.loc[0, 'identifier'].id == '1CSE')
        self.assertTrue(results.loc[0, 'status'] == 'finished')
        self.assertNotEqual(float(results.loc[0, 'DDG']), np.nan)

    async def test_defualt_pdbfile(self):
        self.pred = IMutant3PdbFile
        results = await self.get_prediction(f"{self.input_folder}/1CSE.pdb L45G I")
        self.assertEqual(len(results), 1)
        self.assertTrue(results.loc[0, 'identifier'].id == '1CSE')
        self.assertTrue(results.loc[0, 'status'] == 'finished')
        self.assertNotEqual(float(results.loc[0, 'DDG']), np.nan)

    async def test_default_sequence(self):
        self.pred = IMutant3Sequence
        results = await self.get_prediction(f"{self.input_folder}/1CSE.fasta L45G I")
        self.assertEqual(len(results), 1)
        self.assertTrue(results.loc[0, 'identifier'].id == '1CSE')
        self.assertTrue(results.loc[0, 'status'] == 'finished')
        self.assertNotEqual(float(results.loc[0, 'DDG']), np.nan)
