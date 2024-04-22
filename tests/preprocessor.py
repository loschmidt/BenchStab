import unittest
from benchstab.preprocessor import Preprocessor
from benchstab.utils.exceptions import PreprocessorError


FOLDER_PATH = "./tests"


class WrongInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prep = Preprocessor("")

    def test_default(self):
        _input = "GIBBERISH"
        with self.assertRaisesRegex(
            PreprocessorError, 'Line "GIBBERISH" is in wrong format.*'
        ):
            self.prep.parse_line(_input)

    def test_wrong_pdb_id(self):
        # Too long
        _input = "1CSEG L45G I"
        with self.assertRaisesRegex(
            PreprocessorError, "Invalid sequence/structure format.*"
        ):
            self.prep.parse_line(_input)
        # Too short
        _input = "1CS L45G I"
        with self.assertRaisesRegex(
            PreprocessorError, "Invalid sequence/structure format.*"
        ):
            self.prep.parse_line(_input)
        # Not alpha-numeric
        _input = "1CS! L45G I"
        with self.assertRaisesRegex(
            PreprocessorError, "Invalid sequence/structure format.*"
        ):
            self.prep.parse_line(_input)
        # Non-existing protein
        _input = "GGGG L45G I"
        with self.assertRaisesRegex(
            PreprocessorError, 'Entry with ID "GGGG" does not exist'
        ):
            self.prep.parse_line(_input)

    def test_wrong_pdb_file(self):
        # Non-existing PDB file
        _input = "gibberish.pdb L45G I"
        with self.assertRaisesRegex(
            FileNotFoundError, r".*No such file or directory.*"
        ):
            self.prep.parse_line(_input)
        # Incorrect PDB file
        _input = f"{FOLDER_PATH}/inputs/invalid_pdb.pdb L45G I"
 
        with self.assertLogs(level='ERROR') as log:
            res = self.prep.parse_line(_input)
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn('No proteins found in', log.output[0])
        self.assertIsNone(res)

    def test_wrong_fasta(self):
        # Non-existing fasta file
        _input = "gibberish.fasta L45G I"
        with self.assertRaisesRegex(
            FileNotFoundError, r".*No such file or directory.*"
        ):
            self.prep.parse_line(_input)
        # Incorrect PDB file
        _input = f"{FOLDER_PATH}/inputs/invalid_fasta.fasta L45G I"
        with self.assertRaisesRegex(
            PreprocessorError, r".*failed the BioPython PDB structural check.*"
        ):
            self.prep.parse_line(_input)
        _input = "P05067@ L45G I"
        with self.assertRaisesRegex(
            PreprocessorError, r"Invalid sequence/structure format.*"
        ):
            self.prep.parse_line(_input)
        _input = """
            MLPGLAL@@LLLAAWTA L45G I
        """
        with self.assertRaisesRegex(
            PreprocessorError, r"Invalid sequence/structure format.*"
        ):
            self.prep.parse_line(_input)

    def test_wrong_mutation_general(self):
        # Missing position
        _input = "1CSE LG I"
        with self.assertRaisesRegex(
            PreprocessorError, r'.*Mutation "LG" has invalid format.*'
        ):
            self.prep.parse_line(_input)
        _input = "1CSE LSG I"
        # Invalid position - not a number
        with self.assertRaisesRegex(
            PreprocessorError, r'.*Mutation "LSG" has invalid format*'
        ):
            self.prep.parse_line(_input)

    def test_wrong_mutation_fasta(self):
        # Position larger than the sequence
        _input = "TEFGSELKSFPEVVGKTVDQAREYFTLHYPQYNVYFLPEGSPVTLDLRYNRVRVFYNPGTNVVNHVPHVG L1000G I"
        with self.assertLogs(level='ERROR') as log:
            res = self.prep.parse_line(_input)
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn('Invalid resiude position in mutation', log.output[0])
        self.assertIsNone(res.mutation)
        # Position is negative
        _input = "P01051 L-1000G I"
        with self.assertLogs(level='ERROR') as log:
            res = self.prep.parse_line(_input)
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn('Invalid resiude position in mutation', log.output[0])
        self.assertIsNone(res.mutation)
        # WT aminoacid at position N in FASTA does not match the aminoacid stated in mutation
        _input = f"{FOLDER_PATH}/inputs/1CSE.fasta A45G I"
        with self.assertLogs(level='ERROR') as log:
            res = self.prep.parse_line(_input)
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn(
                'Provided WT-residue "A" in position "45" does not match the "L"',
                log.output[0]
            )
        self.assertIsNone(res.mutation)

    def test_wrong_mutation_structure(self):
        # Position larger than the sequence
        _input = "1CSE L1000G I"
        with self.assertLogs(level='WARNING') as log:
            result = self.prep.parse_line(_input)
            self.assertEqual(len(log.output), 2)
            self.assertEqual(len(log.records), 2)
            self.assertFalse([r for r in log.records if r.levelname == 'ERROR'])
        self.assertIsNone(result.fasta_mutation)

        # Position is negative
        _input = "1CSE L-1000G I"
        with self.assertLogs(level='WARNING') as log:
            result = self.prep.parse_line(_input)
            self.assertEqual(len(log.output), 2)
            self.assertEqual(len(log.records), 2)
            self.assertFalse([r for r in log.records if r.levelname == 'ERROR'])
        self.assertIsNone(result.fasta_mutation)

        # WT aminoacid at position N in FASTA does not match the aminoacid stated in mutation
        _input = "1CSE A45G I"
        with self.assertLogs(level='WARNING') as log:
            result = self.prep.parse_line(_input)
            self.assertEqual(len(log.output), 2)
            self.assertEqual(len(log.records), 2)
            self.assertFalse([r for r in log.records if r.levelname == 'ERROR'])
        self.assertIsNone(result.fasta_mutation)


    def test_wrong_chain(self):
        # Invalid chain format
        _input = f"{FOLDER_PATH}/inputs/1CSE.pdb L45G BESTCHAINEVER"
        with self.assertLogs(level='ERROR') as log:
            res = self.prep.parse_line(_input)
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn(
                'Chain "BESTCHAINEVER" is invalid for structure/sequence',
                log.output[0]
            )
        self.assertIsNone(res)
        # Non-Existing chain
        _input = f"{FOLDER_PATH}/inputs/1CSE.pdb L45G U"
        with self.assertLogs(level='ERROR') as log:
            res = self.prep.parse_line(_input)
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn(
                'Chain "U" is invalid for structure/sequence',
                log.output[0]
            )
        self.assertIsNone(res)


class CorrectInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prep = Preprocessor("")

    def test_csv_comma_input(self):
        self.prep.input = f"{FOLDER_PATH}/inputs/input_comma.csv"
        self.prep.header = True
        result = self.prep.parse()
        self.assertEqual(result["identifier"].item().id, "1CSE")
        self.assertEqual(result["mutation"].item(), "L45G")
        self.assertEqual(result['chain'].item(), "I")

    def test_csv_semicolon_input(self):
        self.prep.input = f"{FOLDER_PATH}/inputs/input_semicolon.csv"
        self.prep.header = True
        result = self.prep.parse()
        self.assertEqual(result["identifier"].item().id, "1CSE")
        self.assertEqual(result["mutation"].item(), "L45G")
        self.assertEqual(result['chain'].item(), "I")

    def test_tsv_input(self):
        self.prep.input = f"{FOLDER_PATH}/inputs/input.tsv"
        self.prep.header = True
        result = self.prep.parse()
        self.assertEqual(result["identifier"].item().id, "1CSE")
        self.assertEqual(result["mutation"].item(), "L45G")
        self.assertEqual(result['chain'].item(), "I")

    def test_txt_space_input(self):
        self.prep.input = f"{FOLDER_PATH}/inputs/input.txt"
        self.prep.header = True
        result = self.prep.parse()
        self.assertEqual(result["identifier"].item().id, "1CSE")
        self.assertEqual(result["mutation"].item(), "L45G")
        self.assertEqual(result['chain'].item(), "I")

    def test_basic_input_pdbid(self):
        _input = "1CSE L45G I"
        result = self.prep.parse_line(_input)
        self.assertEqual(result.identifier.id, "1CSE")
        self.assertEqual(result.mutation, "L45G")
        self.assertEqual(result.chain, "I")

    def test_basic_input_pdbfile(self):
        _input = f"{FOLDER_PATH}/inputs/1CSE.pdb L45G I"
        result = self.prep.parse_line(_input)
        self.assertEqual(result.identifier.id, f"{FOLDER_PATH}/inputs/1CSE.pdb")
        self.assertEqual(result.mutation, "L45G")
        self.assertEqual(result.chain, "I")

    def test_basic_input_fastafile(self):
        _input = f"{FOLDER_PATH}/inputs/1CSE.fasta L45G I"
        result = self.prep.parse_line(_input)
        self.assertIn("1CSE", result.identifier.id)
        self.assertEqual(result.mutation, "L45G")
        self.assertEqual(
            result.identifier.sequence,
            "TEFGSELKSFPEVVGKTVDQAREYFTLHYPQYNVYFLPEGSPVTLDLRYNRVRVFYNPGTNVVNHVPHVG"
        )

    def test_basic_input_uniprotid(self):
        _input = f"P05067 M1A I"
        result = self.prep.parse_line(_input)
        self.assertIn("P05067", result.identifier.id)
        self.assertEqual(
            result.identifier.sequence,
            (
                'MLPGLALLLLAAWTARALEVPTDGNAGLLAEPQIAMFCGRLNMHMNVQNGKWDSDPSGTK'
                'TCIDTKEGILQYCQEVYPELQITNVVEANQPVTIQNWCKRGRKQCKTHPHFVIPYRCLVG'
                'EFVSDALLVPDKCKFLHQERMDVCETHLHWHTVAKETCSEKSTNLHDYGMLLPCGIDKFR'
                'GVEFVCCPLAEESDNVDSADAEEDDSDVWWGGADTDYADGSEDKVVEVAEEEEVAEVEEE'
                'EADDDEDDEDGDEVEEEAEEPYEEATERTTSIATTTTTTTESVEEVVREVCSEQAETGPC'
                'RAMISRWYFDVTEGKCAPFFYGGCGGNRNNFDTEEYCMAVCGSAMSQSLLKTTQEPLARD'
                'PVKLPTTAASTPDAVDKYLETPGDENEHAHFQKAKERLEAKHRERMSQVMREWEEAERQA'
                'KNLPKADKKAVIQHFQEKVESLEQEAANERQQLVETHMARVEAMLNDRRRLALENYITAL'
                'QAVPPRPRHVFNMLKKYVRAEQKDRQHTLKHFEHVRMVDPKKAAQIRSQVMTHLRVIYER'
                'MNQSLSLLYNVPAVAEEIQDEVDELLQKEQNYSDDVLANMISEPRISYGNDALMPSLTET'
                'KTTVELLPVNGEFSLDDLQPWHSFGADSVPANTENEVEPVDARPAADRGLTTRPGSGLTN'
                'IKTEEISEVKMDAEFRHDSGYEVHHQKLVFFAEDVGSNKGAIIGLMVGGVVIATVIVITL'
                'VMLKKKQYTSIHHGVVEVDAAVTPEERHLSKMQQNGYENPTYKFFEQMQN'
            )
        )
        self.assertEqual(result.mutation, "M1A")

    def test_basic_input_sequence(self):
        _input = "MLPGLALLLLAAWTA M1A I"
        result = self.prep.parse_line(_input)
        self.assertEqual(result.identifier.sequence, "MLPGLALLLLAAWTA")
        self.assertEqual(result.mutation, "M1A")


if __name__ == "__main__":
    unittest.main()
