from ._template import _TemplateCorrectInputTests
from benchstab.predictors.web import SRidePdbFile, SRidePdbID


class CorrectInputTests(_TemplateCorrectInputTests):

    async def test_default_pdbid(self):
        self.pred = SRidePdbID
        results = await self.get_prediction("1CSE L45G I")
        print(results)
        self.assertEqual(len(results), 2)
        self.assertTrue(results.loc[0, 'identifier'].id == '1CSE')
        self.assertTrue(results.loc[0, 'status'] == 'finished')
        self.assertTrue(results.loc[0, 'DDG'] == 'Stabilizing')

    async def test_default_pdbfile(self):
        self.pred = SRidePdbFile
        results = await self.get_prediction(f"{self.input_folder}/1CSE.pdb L45G I")
        print(results)
        self.assertEqual(len(results), 2)
        self.assertTrue('1CSE' in results.loc[0, 'identifier'].id)
        self.assertTrue(results.loc[0, 'status'] == 'finished')
        self.assertTrue(results.loc[0, 'DDG'] == 'Stabilizing')
