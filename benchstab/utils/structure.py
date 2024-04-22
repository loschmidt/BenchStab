import os
import re
import string
import random
import logging
import warnings
import requests
from io import StringIO, TextIOWrapper, BufferedReader, BytesIO
from typing import List, Union, Dict, Tuple

from Bio import SeqIO, BiopythonParserWarning
from Bio.PDB import PDBParser
from Bio.PDB.PDBExceptions import PDBConstructionWarning

from .exceptions import PreprocessorError


class File:
    """
    Base class for all file types.
    Contains methods for converting the file to different formats, as well as
    methods for fetching files from URLs and opening files.
    """
    _rcsb_url = ""
    _uniprot_url = ""

    def __init__(self, file: str = "", name: str = "") -> None:
        self.file = file
        self.name = name
        self.filename = self.name

    def __to_multipart(self, content_type: str) -> Dict[str, Union[str, bytes, StringIO]]:
        """
        Convert the file to a multipart (from-data) file. If the file does not exist,
        create a temporary file. The final format depends on the content type.

        :param content_type: content type of the file. Allowed types:
            - text/plain
            - application/octet-stream
        :type content_type: str
        :return: multipart file
        :rtype: dict
        """
        _data = {}
        if os.path.exists(self.file):
            _config = {
                'file': self.file,
                'mode': 'rb' if 'octet-stream' in content_type else 'r'
            }
            if 'text/plain' in content_type:
                _config['encoding'] = 'utf-8'
            _data['value'] = open(**_config)
            _index = self.file.index('\\') if '\\' in self.file else 0
            _data['filename'] = self.file[_index + 1:]
        else:
            _data['filename'] = self.filename
            if 'text/plain' in content_type:
                _data['value'] = str(self.file)
            else:
                _data['value'] = self.to_bytes() if isinstance(self.file, str) else self.file
        _data['content_type'] = content_type
        return _data

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def to_bytes(self) -> bytes:
        """
        Convert the file to BytesIO.

        :return: file as bytes
        :rtype: BytesIO object
        """
        return BytesIO(bytes(self.file, encoding='utf-8'))

    def to_octet_stream(self) -> Dict[str, Union[str, bytes, StringIO]]:
        """
        Convert the file to an octet-stream.

        :return: file as octet-stream
        :rtype: bytes
        """
        return self.__to_multipart('application/octet-stream')

    def to_plain_text(self) -> Dict[str, Union[str, bytes, StringIO]]:
        """
        Convert the file to plain text.

        :return: file as plain text
        :rtype: str
        """
        return self.__to_multipart('text/plain')

    @classmethod
    def get_from_url_by_id(cls, url: str, **kwargs) -> requests.Response:
        """
        Get the file from a URL by ID. Raise an exception if the file does not exist.

        :param id: ID
        :type id: str
        :param url: URL
        :type url: str
        :return: file
        :rtype: requests.Response
        :raises PreprocessorError: if the record does not exist
        """
        resp = requests.get(url=url.format(**kwargs), timeout=15)
        id = kwargs.get('id', 'unknown')
        if resp.status_code == 404:
            raise PreprocessorError(f'Entry with ID "{id}" does not exist in {url.format(id=id)}.')
        elif resp.status_code != 200:
            raise PreprocessorError(f'Failed to retrieve protein with ID "{id}" from {url.format(id=id)}.')
        return resp

    @classmethod
    def open(
        cls, file_path: str, mode: str = 'r', encoding: str = 'utf-8'
    ) -> Union[TextIOWrapper, BufferedReader]:
        """
        Open a file. Raise an exception if the file does not exist.

        :param file_path: file path
        :type file_path: str
        :param mode: file mode
        :type mode: str
        :param encoding: file encoding
        :type encoding: str
        :return: file
        :rtype: Union[TextIOWrapper, BufferedReader]
        :raises FileNotFoundError: if the file does not exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'File path "{file_path}" does not exist.')
        return open(file_path, mode, encoding=encoding)


class Fasta(File):
    """
    FASTA file class.
    Contains methods for extracting FASTA sequences from different sources.
    """
    __refs__ = {}
    _sifts_url = "https://www.ebi.ac.uk/pdbe/api/mappings/uniprot/{id}"
    _rcsb_url = "https://www.rcsb.org/fasta/entry/{id}"
    _uniprot_url = "https://rest.uniprot.org/uniprotkb/{id}.fasta"
    _rcsb_polymer_instance_url = (
        "https://data.rcsb.org/rest/v1/core/polymer_entity_instance/{id}/{chain}"
    )
    logger = logging.getLogger(__name__)

    @classmethod
    def _find_delimiter(cls, header: str):
        _delim = re.search(r'[^\w*;.#_\-]', header, re.IGNORECASE)
        return _delim.group(0) if _delim is not None else None

    @classmethod
    def create(cls, datapoint: str):
        """
        Determine the FASTA sequence format and return a FASTA object.

        :param datapoint: FASTA string or file path
        :type datapoint: str
        :return: FASTA object
        :rtype: Fasta
        :raises PreprocessorError: if the sequence is invalid
        """
        if datapoint.endswith('.fasta'):
            return Fasta.from_file(datapoint)
        # Uniprot ID regex defined in https://www.wikidata.org/wiki/Property:P352
        elif re.search(
                r'^([OPQ][0-9][A-Z0-9]|[A-NR-Z][0-9][A-Z])[A-Z0-9][A-Z0-9][0-9]([A-Z][A-Z0-9][A-Z0-9][0-9])?$',
                datapoint,
                flags=re.IGNORECASE
        ) is not None:
            return Fasta.from_uniprot(datapoint)
        # Fasta sequence regex defined by https://blast.ncbi.nlm.nih.gov/doc/blast-topics/
        elif re.search(
                r'^[ABCDEFGHIKLMNPQRSTUVWYZX*\-]+$',
                datapoint,
                flags=re.IGNORECASE
        ) is not None:
            _header = ">TEMPORARYHEADER A"
            return Fasta(datapoint, 'A', _header, datapoint)
        else:
            raise PreprocessorError(f"Invalid sequence/structure format - {datapoint}")

    @classmethod
    def from_uniprot(cls, datapoint):
        """
        Extract the FASTA sequence from the Uniprot database.

        :param datapoint: Uniprot ID
        :type datapoint: str
        :return: FASTA object
        :rtype: Fasta
        """
        return cls.from_file(
            StringIO(cls.get_from_url_by_id(url=cls._uniprot_url, id=datapoint).text)
        )

    @classmethod
    def __get_author_residue_number_offset(cls, pdb_id: str, chain: str) -> List[str]:
        """
        Get the author residue number start from the RCSB database.

        :param pdb_id: PDB ID
        :type pdb_id: str
        :param chain: chain ID
        :type chain: str
        :return: author residue number offset
        :rtype: List[str]
        """
        r = cls.get_from_url_by_id(
            cls._rcsb_polymer_instance_url, id=pdb_id, chain=chain
        ).json()

        if not 'rcsb_polymer_entity_instance_container_identifiers' in r:
            return None
        _mapping = r['rcsb_polymer_entity_instance_container_identifiers']

        if 'auth_to_entity_poly_seq_mapping' not in _mapping:
            return None
        _mapping = _mapping['auth_to_entity_poly_seq_mapping']

        if not _mapping:
            return None
        return _mapping


    @classmethod
    def __fasta_offsets_from_sifts(cls, pdb_id: str, chain: str) -> Dict[str, Union[str, List[str], int]]:
        """ 
        Get the offset between the PDB and Uniprot FASTA sequences.

        :param pdb_id: PDB ID
        :type pdb_id: str
        :param chain: chain ID
        :type chain: str
        :return: Uniprot ID, PDB offsets, Uniprot start, Uniprot end
        :rtype: Dict[str, Union[str, List[str], int]]
        """
        r = cls.get_from_url_by_id(cls._sifts_url, id=pdb_id).json()

        _metadata = {
            'uniprot_id': None,
            'pdb_offsets': None,
            'uniprot_start': 0,
        }
        for _id, data in r[pdb_id.lower()]['UniProt'].items():
            for mapping in data['mappings']:
                if mapping['chain_id'] == chain:
                    _metadata['uniprot_id'] = _id
                    _metadata['uniprot_start'] = mapping['unp_start']
                    _rcsb_chain = mapping['struct_asym_id']
                    _pdb_start = mapping['start']['residue_number']
                    _pdb_end = mapping['end']['residue_number']
                    break

        _metadata['pdb_offsets'] = cls.__get_author_residue_number_offset(pdb_id, _rcsb_chain)
        _metadata['pdb_offsets'] = _metadata['pdb_offsets'][_pdb_start - 1:_pdb_end]
        return _metadata

    @classmethod
    def from_uniprot_by_pdb_id(cls, pdb_id: str, chain: str):
        """
        Extract the FASTA sequence from the Uniprot database.

        :param pdb_id: PDB ID
        :type pdb_id: str
        :param chain: chain ID
        :type chain: str
        :return: FASTA object
        :rtype: Fasta
        :raises PreprocessorError: if the chain is invalid for the structure
        :raises PreprocessorError: if the structure is not mapped to Uniprot
        """
        if pdb_id in cls.__refs__:
            return cls.__refs__[pdb_id]

        _metadata = cls.__fasta_offsets_from_sifts(pdb_id, chain)

        if _metadata['uniprot_id'] is not None:
            _fasta = cls.from_uniprot(_metadata['uniprot_id'])
            # If there is missing record for author's mapping in the RCSB,
            # generate custom offsets starting from 0
            if _metadata['pdb_offsets'] is None:
                _metadata['pdb_offsets'] = range(1, len(_fasta.sequence) + 1)
            _fasta.offsets =  {
                pos: idx + _metadata['uniprot_start']
                for idx, pos in enumerate(_metadata['pdb_offsets'])
            }
            _fasta.chain = chain
            return _fasta
        raise PreprocessorError(
            f'Chain "{chain}" is invalid for structure/sequence "{pdb_id}"/"{_metadata["uniprot_id"]}",'
            f' or the structure is not mapped to Uniprot.'
        )

    @classmethod
    def from_rcsb_by_pdb_id(cls, pdb_id: str, chain: str):
        """
        Extract the FASTA sequence from the RCSB PDB database.

        :param pdb_id: PDB ID
        :type pdb_id: str
        :param chain: chain ID
        :type chain: str
        :return: FASTA object
        :rtype: Fasta
        :raises PreprocessorError: if the chain is invalid for the structure
        :raises PreprocessorError: if the structure is not mapped to PDB
        """
        if pdb_id in cls.__refs__:
            return cls.__refs__[pdb_id]
        _metadata = cls.__fasta_offsets_from_sifts(pdb_id, chain)
        _results = list(
            filter(
                None, cls.get_from_url_by_id(cls._rcsb_url, id=pdb_id).text.split(">")
            )
        )
        for fasta in _results:
            header, sequence = list(filter(None, fasta.split("\n")))
            # Regex looking for fasta header separator
            # Allowed separators - https://www.ncbi.nlm.nih.gov/genbank/fastaformat/
            _delim = cls._find_delimiter(header)

            if _delim is None:
                return Fasta(sequence, 'A', header, pdb_id)
            _chains = header.split(_delim)[1]
            _chains = re.sub(r'chain[s]?', '', _chains, flags=re.IGNORECASE)
            # Check if there are multiple chains in the single FASTA header
            _chains = list(filter(None, _chains.split(',')))
            # If there is missing record for author's mapping in the RCSB,
            # generate custom offsets starting from 0
            if _metadata['pdb_offsets'] is None:
                _metadata['pdb_offsets'] = range(1, len(sequence) + 1)
            _offsets =  {pos: idx for idx, pos in enumerate(_metadata['pdb_offsets'])}
            # Find if the chain is in the header
            for _chain in _chains:
                if re.search(chain, cls.extract_chain(_chain.strip())) is not None:
                    return Fasta(sequence, chain, header, pdb_id, _offsets)
        raise PreprocessorError(
            f'Chain "{chain}" is invalid for structure/sequence "{pdb_id}", or the sequence is not mapped to PDB.'
        )

    @classmethod
    def from_file(cls, file_path):
        """
        Extract the FASTA sequence from a FASTA file.

        :param file_path: FASTA file path
        :type file_path: str
        :return: FASTA object
        :rtype: Fasta
        :raises PreprocessorError: if the structure is invalid by BioPython standards
        :raises PreprocessorError: if the file does not contain any sequences
        """
        if file_path in cls.__refs__:
            return cls.__refs__[file_path]

        warnings.filterwarnings("error")
        warnings.simplefilter('ignore', PDBConstructionWarning)
        try:
            _fasta = SeqIO.read(file_path, 'fasta')
            _delim = cls._find_delimiter(_fasta.description)

            if _delim is None:
                _id = 'TEMPORARYID'
            else:
                _id = _fasta.description.split(_delim)[0].replace('>', '')
                # Uniprot records have 'sp' prefix
                if _id == 'sp':
                    _id = _fasta.description.split(_delim)[1].replace('>', '')
        except (KeyError, ValueError) as exc:
            raise PreprocessorError(
                f'The sequence found in "{file_path}" failed the BioPython PDB structural check.'
            ) from exc
        except IndexError as exc:
            raise PreprocessorError(
                f'Missing Name info in FASTA "{file_path}" header.'
            ) from exc
        warnings.resetwarnings()
        return Fasta(str(_fasta.seq), 'A', _fasta.description, _id.replace('>', ''))

    @classmethod
    def from_pdb_file(cls, file_path: str, chain: str):
        """
        Extract the FASTA sequence from a PDB file.

        :param file_path: PDB file path
        :type file_path: str
        :param chain: chain ID
        :type chain: str
        :return: FASTA object
        :rtype: Fasta
        :raises PreprocessorError: if the structure is invalid by BioPython standards
        :raises PreprocessorError: if the chain is invalid for the structure
        :raises PreprocessorError: if the file does not contain any sequences
        """
        try:
            records = list(SeqIO.parse(file_path, 'pdb-seqres'))
        except (KeyError, ValueError) as exc:
            raise PreprocessorError(
                f'The sequence found in "{file_path}" failed the BioPython PDB structural check.'
            ) from exc

        # Check if the file contains any sequences. If not it is probably a invalid PDB file.
        if not records:
            raise PreprocessorError(
                f'No proteins found in "{file_path}".',
            )

        for record in records:
            _delim = cls._find_delimiter(record.id)
            _id, _chain = record.id.split(_delim)
            if cls.extract_chain(_chain) == chain:
                return Fasta(str(record.seq), _chain, record.id, _id)

        raise PreprocessorError(
            f'Chain "{chain}" is invalid for structure/sequence "{file_path}".'
        )

    @classmethod
    def extract_chain(cls, chain):
        """
        Extract the chain ID from the FASTA header.

        :param chain: chain ID
        :type chain: str
        :return: chain ID
        :rtype: str
        """
        chain = chain.strip()
        if 'auth' in chain:
            chain = re.search(r'auth (\w)', chain).group(1)
        # Check if the chain is a single letter
        if re.match(r'^[A-Z]$', chain, flags=re.IGNORECASE) is not None:
            return chain.upper()
        return None

    def __init__(
        self,
        sequence: str,
        chain: str,
        header: str,
        name: str = None,
        offsets: Dict[int, int] = None
    ) -> None:
        super().__init__()
        self.id = name
        self.chain = chain
        self.sequence = sequence
        self.file = '>' + header + '\n' + sequence
        self.header = header
        self.offsets = offsets or list(range(0, len(sequence), 1))
        self.name = self.id or self.file
        self.filename = self.name if '.fasta' in self.name else self.name + '.fasta'

    def __hash__(self) -> int:
        return hash(self.sequence)

    def __repr__(self) -> str:
        return self.sequence

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, self.__class__):
            return False
        return self.sequence == __o.sequence

    def __ne__(self, __o: object) -> bool:
        return not self == __o

    def __lt__(self, other):
        if isinstance(other, File):
            return self.name < other.name
        return self.name < other


class PDB(File):
    """
    PDB file class.
    Contains methods for extracting PDB structures from different sources.
    """
    __refs__ = {}
    _rcsb_url = "https://files.rcsb.org/download/{id}.pdb"
    logger = logging.getLogger(__name__)

    @classmethod
    def create(cls, pdb: str):
        """
        Determine the PDB structure format and return a PDB object

        :param pdb: PDB structure or file path
        :type pdb: str
        :return: PDB object
        :rtype: PDB
        """
        # If PDB object exists, return its reference
        if pdb in cls.__refs__:
            return cls.__refs__[pdb]
        # Check if structural file was passed 
        if pdb.endswith(".pdb"):
            _pdb = PDB.from_file(pdb)
        # Check if PDB entry has a valid format
        elif re.search(r'^\w{4}$', pdb, flags=re.IGNORECASE) is not None:
            _pdb = PDB.from_id(pdb)
        else:
            return None
        cls.__refs__[_pdb.name] = _pdb
        return _pdb

    @classmethod
    def from_id(cls, pdb_id: str):
        """
        Fetch the PDB record from the RCSB PDB database, process it and return a PDB object.

        :param pdb_id: PDB ID
        :type pdb_id: str
        :return: PDB object
        :rtype: PDB
        """
        pdb = cls.from_file(
            StringIO(cls.get_from_url_by_id(cls._rcsb_url, id=pdb_id).text)
        )
        pdb.name = pdb.id = pdb_id
        pdb.source = 'rcsb'
        return pdb

    @classmethod
    def from_file(cls, file_handle: Union[str, StringIO]):
        """
        Process the PDB file and return a PDB object.
        Log a warning if the structure is faulty by BioPython standards.
        Raise an exception if the structure is invalid by BioPython standards.

        :param file_handle: PDB file handle
        :type file_handle: Union[str, StringIO]
        :return: PDB object
        :rtype: PDB
        :raises PreprocessorError: if the structure is invalid by BioPython standards
        """

        # If file_handle is a StringIO object, try to get the file name
        if isinstance(file_handle, StringIO):
            file_name = file_handle.name if hasattr(file_handle, 'name') else 'unknown'
        else:
            file_name = file_handle

        # Read the file to check if it is a valid PDB structure
        try:
            warnings.simplefilter('ignore', PDBConstructionWarning)
            warnings.simplefilter('error', BiopythonParserWarning)
            struct = PDBParser(PERMISSIVE=False).get_structure(
                id=''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
                file=file_handle
            )
        except BiopythonParserWarning as exc:
            raise PreprocessorError(
                f'The structure found in "{file_name}" failed the BioPython PDB structural check.'
            ) from exc
        finally:
            warnings.resetwarnings()

        # Read the file again to avoid the Biopython warning
        if isinstance(file_handle, StringIO):
            file_handle.seek(0)
            _file = file_handle.read()
        else:
            with open(file_handle, 'r', encoding='utf-8') as f:
                _file = f.read()
        return PDB(_file, file_name, source='file', chains=struct.get_chains())

    def __init__(
            self,
            pdb_file: str,
            pdb_id: str = None,
            source: str = "file",
            chains: List[str] = None
    ) -> None:
        super().__init__()
        self.file = pdb_file
        self.id = pdb_id
        self.name = self.id or self.file
        self.filename = self.name if 'pdb' in self.name else self.name + '.pdb'
        self.source = source
        self.chains = chains or ['A']

    def __lt__(self, other):
        if isinstance(other, File):
            return self.name < other.name
        return self.name < other

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, self.__class__):
            return False
        if self.id is not None:
            return self.id == __o.id
        return self.file == __o.file

    def __ne__(self, __o: object) -> bool:
        return not self == __o
