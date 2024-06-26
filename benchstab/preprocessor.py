import logging
import os
import re
from dataclasses import dataclass
from typing import Union, TextIO, List, Dict, Any

from .utils.aminoacids import Mapper
from .utils.dataset import PredictorDataset
from .utils.exceptions import PreprocessorError
from .utils.structure import PDB, Fasta

@dataclass
class PreprocessorRow:
    identifier: Union[PDB, Fasta] = None
    mutation: str = None
    chain: str = None
    fasta: Fasta = None
    fasta_mutation: str = None
    ph: float = 7.0
    temperature: float = 25.0

    def to_dict(self):
        """
        Converts the PreprocessorRow object to a dictionary.
        
        :return: Dictionary containing the PreprocessorRow object
        :rtype: Dict[str, Any]
        """
        return self.__dict__

    def is_valid(self) -> bool:
        """
        Check if the PreprocessorRow object is valid.
        
        :return: True if the PreprocessorRow object is valid, False otherwise
        :rtype: bool
        """
        return self.identifier is not None and self.mutation is not None


class Preprocessor:

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    def __init__(
        self,
        input: Union[str, list, TextIO],
        outfolder: str = None,
        permissive: bool = True,
        verbosity: int = 0,
        skip_header: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """
        Preprocessor class is used to parse the input file and create a dataset 
        that can be used by the predictor.
        
        The input file can be in the following formats:
            * PDB identifier, mutation and chain
            * Fasta identifier, mutation, pH and temperature
            * PDB identifier, mutation, pH and temperature
            * Fasta identifier, mutation and chain

        The class can also generate a summary of the dataset.

        The summary includes the following information:
            * Number of mutations
            * Number of proteins
            * Average number of mutations per protein
            * Number of mutations with positive charge
            * Number of mutations with negative charge
            * Number of mutations with no charge
            * Number of mutations with acidic chemical properties
            * Number of mutations with basic chemical properties
            * Number of mutations with aromatic chemical properties
            * Number of mutations with aliphatic chemical properties
            * Number of mutations with hydroxyl chemical properties
            * Number of mutations with sulfur chemical properties
            * Number of mutations with amide chemical properties
            * Number of mutations with non-polar chemical properties
            * Number of mutations with polar chemical properties

        :param input: Input file containing the protein identifier, mutation and chain
        :type input: Union[str, list, TextIO]
        :param outfolder: Folder where the preprocessed input will be saved
        :type outfolder: str
        :param permissive: If True, the preprocessing script will continue if it encounters an error
        :type permissive: bool
        :param verbosity: Verbosity level
        :type verbosity: int
        :param skip_header: If True, the header in the input file will be skipped
        :type skip_header: bool
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.INFO)
        self.input = input
        self.outfolder = outfolder
        self._chain = None
        self.verbosity = verbosity
        self.permissive = permissive
        self.skip_header = skip_header
        self._c_errors = 0
        self._c_warnings = 0

        # Set preprocessing logger for PDB and Fasta
        PDB.logger = self.logger
        Fasta.logger = self.logger

    @classmethod
    def print_summary(cls, summary, logger: logging.Logger = None):
        """
        Print the summary generated by create_summary to stdout
        using the provided logger or the default logger.

        :param summary: Summary to be printed
        :type summary: Dict[str, str]
        :param logger: Logger to be used for printing the summary
        :type logger: logging.Logger
        :return: None
        :rtype: None
        """
        logger = logger or cls.logger
        _message = [
            "\nDataset Summary:",
            f"\tNumber of mutations: {summary['mutations']}",
            f"\tTotal number of proteins: {summary['identifiers']}",
            f"\tAverage number of mutations per identifier: {summary['avg_mut']}",
            f"\tMutations with positive charge: {summary['mut_positive']}",
            f"\tMutations with negative charge: {summary['mut_negative']}",
            f"\tMutations with no charge: {summary['mut_no_charge']}",
            f"\tMutations with acidic chemical properties: {summary['mut_acidic']}",
            f"\tMutations with amide chemical properties: {summary['mut_amide']}",
            f"\tMutations with aliphatic chemical properties: {summary['mut_aliphatic']}",
            f"\tMutations with basic chemical properties: {summary['mut_basic']}",
            f"\tMutations with sulfur chemical properties: {summary['mut_sulfur']}",
            f"\tMutations with hydroxyl chemical properties: {summary['mut_hydroxyl']}",
            f"\tPolar mutations: {summary['mut_polar']}",
            f"\tNon-polar mutations: {summary['mut_nonpolar']}\n"
        ]
        logger.info("\n".join(_message))


    @classmethod
    def create_summary(
        cls,
        data: PredictorDataset,
        verbose: bool = True,
        outfolder: str = None,
        logger: logging.Logger = None
    ) -> Dict[str, str]:
        """
        Create a summary of the dataset.
        
        The summary includes the following information:
            * Number of mutations
            * Number of proteins
            * Average number of mutations per protein
            * Number of mutations with positive charge
            * Number of mutations with negative charge
            * Number of mutations with no charge
            * Number of mutations with acidic chemical properties
            * Number of mutations with basic chemical properties
            * Number of mutations with aromatic chemical properties
            * Number of mutations with aliphatic chemical properties
            * Number of mutations with hydroxyl chemical properties
            * Number of mutations with sulfur chemical properties
            * Number of mutations with amide chemical properties
            * Number of mutations with non-polar chemical properties
            * Number of mutations with polar chemical properties

        :param data: Dataset to be summarized
        :type data: PredictorDataset
        :param verbosity: If True, the summary will be printed to stdout
        :type verbosity: bool
        :param outfolder: If provided, the summary will be saved to a file in the provided folder
        :type outfolder: str
        :param logger: Logger to be used for printing the summary
        :type logger: logging.Logger
        :return: Dictionary with the summary
        :rtype: Dict[str, str]
        """
        if not verbose and outfolder is None:
            return None

        logger = logger or cls.logger

        _charge = data.apply(
            lambda x: Mapper.get_charge(x["mutation"][-1]), axis=1
        ).value_counts()
        _chemical = data.apply(
            lambda x: Mapper.get_chemical_properties(x["mutation"][-1]), axis=1
        ).value_counts()
        _polarity = data.apply(
            lambda x: Mapper.get_polarity(x["mutation"][-1]), axis=1
        ).value_counts()
        summary = {
            "mutations": len(data),
            "identifiers": len(data.identifier.unique()),
            "avg_mut": data.groupby(["identifier", "chain"]).value_counts().describe()['mean'],
            "mut_positive": _charge.get("Positive", 0),
            "mut_negative": _charge.get("Negative", 0),
            "mut_no_charge": _charge.get("Uncharged", 0),
            "mut_acidic": _chemical.get("Acidic", 0),
            "mut_basic": _chemical.get("Basic", 0),
            "mut_aromatic": _chemical.get("Aromatic", 0),
            "mut_aliphatic": _chemical.get("Aliphatic", 0),
            "mut_hydroxyl": _chemical.get("Hydroxyl", 0),
            "mut_sulfur": _chemical.get("Sulfur", 0),
            "mut_amide": _chemical.get("Amide", 0),
            "mut_nonpolar": _polarity.get("Non-Polar", 0),
            "mut_polar": _polarity.get("Polar", 0),
        }
        if verbose:
            cls.print_summary(summary, logger)
        return {key: str(value) for key, value in summary.items()}

    def parse_fasta(self, data: str) -> PreprocessorRow:
        """
        Parse the line containing the fasta identifier and the mutation.
        
        If the fasta identifier is valid, return:
            * Fasta object.
            * mutation in the format WT_RESIUDE + POSITION + MUT_RESIDUE.
            * pH (default: 7.0 if not supplied).
            * temperature (default: 25.0 if not supplied).

        :param data: Line containing the fasta identifier and the mutation
        :type data: str
        :return: Dictionary containing the fasta object, mutation, pH and temperature
        :rtype: PreprocessorRow
        """

        # Check if line has all needed components
        if not 1 < len(data) < 5:
            raise PreprocessorError(
                f'Line "{" ".join(data)}" is in wrong format.'
                ' Accepted format is "PROTEIN_IDENTIFIER MUTATION [PH] [TEMPERATURE]".'
            )

        _has_chain = False
        record = PreprocessorRow()
        record.identifier = Fasta.create(data[0])
        record.mutation = self.parse_fasta_mutation(
            data[1], record.identifier, permissive=False
        )
        # Assign chain if provided
        if len(data) > 2 and Fasta.extract_chain(data[2]) is not None:
            _has_chain = True
            record.identifier.chain = Fasta.extract_chain(data[2])
        record.chain = record.identifier.chain
        record.fasta_mutation = record.mutation
        record.fasta = record.identifier


        # Assign pH if provided
        if len(data) > 2 + _has_chain:
            try:
                record.ph = float(data[2])
            except ValueError as exc:
                raise PreprocessorError(
                    f'Invalid pH value "{data[2]}" in line "{" ".join(data)}".'
                ) from exc
        # Assign temperature if provided
        if len(data) == 4 + _has_chain:
            try:
                record.temperature = float(data[3])
            except ValueError as exc:
                raise PreprocessorError(
                    f'Invalid temperature value "{data[3]}" in line "{" ".join(data)}".'
                ) from exc

        return record

    def extract_fasta_from_pdb(
            self, identifier: PDB, chain: str, source: str
    ) -> Fasta:
        """
        Extract fasta record from PDB file.

        :param identifier: PDB identifier
        :type identifier: PDB
        :param chain: Chain identifier
        :type chain: str
        :param source: Source of the PDB file.Accepted values are:
            * file
            * rcsb
            * uniprot
        :type source: str
        :return: Fasta record
        :rtype: Fasta
        """
        sources = {
            "file": Fasta.from_pdb_file,
            "rcsb": Fasta.from_rcsb_by_pdb_id,
            "uniprot": Fasta.from_uniprot_by_pdb_id
        }
        return self.__exception_wrapper(sources[source], identifier.name, chain)

    def parse_fasta_mutation(
        self, mutation: str, fasta: Fasta, permissive: bool = True
    ) -> str:
        """
        Wraps the __parse_fasta_mutation function in a try/except block. If the mutation
        string is not valid, the function will raise a PreprocessorError with the permissive
        flag set to True. This flag indicates that the error is not critical and that
        the preprocessing script can continue.

        :param mutation: Mutation string to be parsed
        :type mutation: str
        :param fasta: Fasta record
        :type fasta: Fasta
        :return: Mutation string in the format WT_RESIUDE + POSITION + MUT_RESIDUE
        :rtype: str
        """
        return self.__exception_wrapper(
            self.__parse_fasta_mutation, mutation, fasta, permissive=permissive
        )

    def parse_struct(self, data: List[str]) -> Union[PreprocessorRow, None]:
        """
        Parse the line containing the protein identifier, the mutation and the chain.
        
        If the protein identifier is valid, return:
            * PDB object
            * mutation in the format WT_RESIUDE + POSITION + MUT_RESIDUE
            * chain
            * fasta object
            * pH (default: 7.0 if not supplied)
            * temperature (default: 25.0 if not supplied)
        
        :param data: Line containing the protein identifier, the mutation and the chain
        :type data: List[str]
        :return: Dictionary containing the PDB object, mutation, chain, fasta object, pH and temperature
        :rtype: PreprocessorRow
        """
        # Check if line has all needed components
        if not (2 < len(data) < 6):
            raise PreprocessorError(
                f'Line "{" ".join(data)}" is in wrong format.'
                ' Accepted format is "PROTEIN_IDENTIFIER MUTATION CHAIN [PH] [TEMPERATURE]".'
            )

        # Parse the protein and mutation
        record = PreprocessorRow()
        record.identifier = PDB.create(data[0])
        record.mutation = self.parse_mutation(data[1])
        record.chain = data[2]
        # Extract fasta record from PDB file/Uniprot DB
        _source = record.identifier.source
        # First try to extract fasta from uniprot
        if record.identifier.source == "rcsb":
            _source = "uniprot"
        # Extract fasta from PDB file/Uniprot
        record.fasta = self.extract_fasta_from_pdb(record.identifier, record.chain, _source)
        record.fasta_mutation = self.parse_fasta_mutation(
            record.mutation, record.fasta, permissive=True
        )
        # If fasta record could not be extracted from Uniprot DB, try to extract it from RCSB
        if record.fasta_mutation is None and record.identifier.source == "rcsb":
            record.fasta = self.extract_fasta_from_pdb(record.identifier, record.chain, "rcsb")
            record.fasta_mutation = self.parse_fasta_mutation(
                record.mutation, record.fasta, permissive=True
            )
        # If faste record could not be extracted from PDB file, then file is probably invalid
        if record.fasta is None and record.identifier.source == "file":
            return None
        # Assign pH if provided
        if len(data) > 3:
            try:
                record.ph = float(data[3])
            except ValueError as exc:
                raise PreprocessorError(
                    f'Invalid pH value "{data[3]}" in line "{" ".join(data)}".'
                ) from exc
        # Assign temperature if provided
        if len(data) == 4:
            try:
                record.temperature = float(data[4])
            except ValueError as exc:
                raise PreprocessorError(
                    f'Invalid temperature value "{data[4]}" in line "{" ".join(data)}".'
                ) from exc
        return record

    def parse_mutation(self, mutation: str) -> str:
        """
        Parse the mutation string and check if it is valid.

        :param mutation: Mutation string to be parsed
        :type mutation: str
        :return: Mutation string in the format WT_RESIUDE + POSITION + MUT_RESIDUE
        :rtype: str
        """
        try:
            _residue = mutation[0]
            _mutated_aa = mutation[-1]
        # Invalid mutation format
        except ValueError as exc:
            raise PreprocessorError(
                (
                    f'Mutation "{mutation}" has invalid format.'
                    'Only accepted format is: WT_RESIUDE + POSITION + MUT_RESIDUE.'
                )
            ) from exc
        # Invalid Wild Type residue
        if _residue not in Mapper.map.one_letter.values:
            raise PreprocessorError(
                (
                    f'Invalid mutation "{mutation}".' 
                    f'WT "{_residue}" is not a valid amino acid.'
                )
            )
        # Invalid mutated residue
        if _mutated_aa not in Mapper.map.one_letter.values:
            raise PreprocessorError(
                (
                    f'Invalid mutation "{mutation}".' 
                    f'Mutant "{_mutated_aa}" is not a valid amino acid.'
                )
            )
        return mutation

    def __parse_fasta_mutation(
            self, mutation: str, fasta: Fasta, permissive: bool = False
        ) -> str:
        """
        Parse the mutation string and check if it is valid. If the mutation is valid,
        return the mutation string in the format WT_RESIUDE + POSITION + MUT_RESIDUE.

        As this function also handles the parsing of the mutation string for the fasta
        record extracted from PDBs, it is possible that the mutation string is not valid.
        In this case, the function will raise a PreprocessorError with the permissive
        flag set to True. This flag indicates that the error is not critical and that
        the preprocessing script can continue.

        :param mutation: Mutation string to be parsed
        :type mutation: str
        :param fasta: Fasta record
        :type fasta: Fasta
        :param permissive: If True, the function will raise a PreprocessorError with the permissive flag set to True
        :type permissive: bool
        :return: Mutation string in the format WT_RESIUDE + POSITION + MUT_RESIDUE
        :rtype: str
        """
        try:
            _residue = mutation[0]
            _position = fasta.offsets[mutation[1:-1]]
            _position -= 1
            _mutated_aa = mutation[-1]
            _mut = _residue + str(_position + 1) + _mutated_aa
        # Invalid mutation format
        except ValueError as exc:
            raise PreprocessorError(
                (
                    f'Mutation "{mutation}" has invalid format.'
                    'Only accepted format is: WT_RESIUDE + POSITION + MUT_RESIDUE.'
                )
            ) from exc
        except KeyError as exc:
            raise PreprocessorError(
                (
                    f'Unable to extract fasta sequence for mutation "{mutation}".' 
                    f'The position "{mutation[1:-1]}" is not a valid position.'
                ),
                permissive=permissive
            ) from exc
        # Unable to extract fasta sequence
        except AttributeError as exc:
            if permissive:
                return None
            raise PreprocessorError(
                (
                    f'Unable to extract fasta sequence for mutation "{mutation}".'
                    ' The structure/sequence might be corrupted.'
                ),
                permissive=permissive
            ) from exc
        # Invalid WT-residue
        if fasta.sequence[_position] != _residue:
            raise PreprocessorError(
                (
                    f'Provided WT-residue "{_residue}" in position "{_position + 1}"'
                    f' does not match the "{fasta.sequence[_position]}"'
                    f' found in structure/sequence "{fasta.id}".'
                ),
                permissive=permissive
            )
        # Invalid mutated residue
        if _mutated_aa not in Mapper.map.one_letter.values:
            raise PreprocessorError(
                (
                    f'Invalid mutation "{mutation}".'
                    f' "{_mutated_aa}" is not a valid amino acid.'
                )
            )
        return _mut

    def parse_line(self, line: str, sep: str = None) -> Union[PreprocessorRow, None]:
        """
        Parse the line containing the protein identifier and mutation (chain).
        
        If the protein identifier is valid, return:
            * PDB object
            * mutation in the format WT_RESIUDE + POSITION + MUT_RESIDUE
            * chain
            * fasta object
            * pH (default: 7.0 if not supplied)
            * temperature (default: 25.0 if not supplied)
        
        :param line: Line containing the protein identifier, the mutation and the chain
        :type line: str
        :param sep: Column separator
        :type sep: str
        :return: Dictionary containing the PDB/Fasta object, mutation, chain, fasta object, pH and temperature
        :rtype: Union[PreprocessorRow, None]
        """
        # Remove any comments from line
        if '#' in line:
            line, _ = line.split("#", 2)
        # Skip empty lines
        if not line:
            return None

        data: List[str] = line.strip().split(sep)
        # Check if it is possible to create a PDB object from the first column
        struct = PDB.create(data[0])
        # If not, try to create a Fasta object
        if struct is None:
            return self.parse_fasta(data)
        return self.parse_struct(data)

    def __exception_wrapper(self, func: callable, *args, **kwargs):
        """
        Wrap the function call in a try/except block. If the function raises a PreprocessorError
        or FileNotFoundError, the function will return None and the error will be logged.
        If the function raises any other exception, the exception will be raised.

        :param func: Function to be wrapped
        :type func: callable
        :return: Function result or None
        :rtype: Union[None, Any]
        """
        try:
            return func(*args, **kwargs)
        except (PreprocessorError, FileNotFoundError) as exc:
            if exc.permissive:
                self._c_warnings += 1
                self.logger.warning(exc)
            else:
                self._c_errors += 1
                self.logger.error(exc)
            return None

    def parse(self) -> PredictorDataset:
        """
        Initiates the mutation file parsing process.
        """
        if isinstance(self.input, list):
            lines = self.input
        elif isinstance(self.input, str):
            if os.path.isfile(self.input):
                with open(self.input, "r", encoding="utf-8") as file:
                    lines = file.readlines()
            else:
                lines = re.split(r'\\r\\n|\\n|\r\n|\n', self.input)
        else:
            lines = self.input.readlines()
        proteins = []

        # Identify the column separator
        _sep = None
        for line in lines:
            if "#" in line:
                line, _ = line.split("#", 2)

            _sep = re.search('[,;\t ]+', line)
            if _sep is not None:
                break
        if _sep is None:
            raise PreprocessorError(
                (
                    'Input file is in wrong format.'
                    ' Accepted line separators are " ", ",", ";" and "\\t".'
                )
            )

        _sep = _sep.group(0)
        for line in lines[int(self.skip_header):]:
            _protein = self.__exception_wrapper(self.parse_line, line, _sep)
            # Skip invalid lines
            if _protein is None or not _protein.is_valid():
                continue
            _protein = _protein.to_dict()
            proteins.append(_protein)

        if self.verbosity:
            self.logger.info(
                'The preprocessing script encountered "%s"  errors and "%s" warnings during preprocessing.',
                self._c_errors, self._c_warnings
            )
        if self._c_errors > 0 and not self.permissive:
            raise PreprocessorError(
                (
                    f'Preprocessor found "{self._c_errors}" errors.'
                    ' If you still wish to proceed, address the errors,'
                    ' or rerun the script with "--permissive" option active.'
                )
            )

        df = PredictorDataset(list(filter(None, proteins)))
        if self.outfolder is not None:
            df.to_csv(os.path.join(self.outfolder, "preprocessed_input.csv"))
        return df
