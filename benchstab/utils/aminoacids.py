import pandas as pd


class Mapper:
    """
    Aminoacid mapper class.
    It maps aminoacid one letter code to three letter code and vice versa. It also provides
    information about aminoacid properties. The information is based on the IMGT Aide-memoire
    for aminoacids. 
    
    Url: https://www.imgt.org/IMGTeducation/Aide-memoire/_UK/aminoacids/IMGTclasses.html


    Full table of aminoacid properties is as follows:

    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |    | Three letters   | One letter   | Polarity   | Charge    | Chemical P. | Volume     | Hydropathy   |
    +====+=================+==============+============+===========+=============+============+==============+
    |  0 | ALA             | A            | Non-Polar  | Uncharged | Aliphatic   | Very small | Hydrophobic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |  1 | ARG             | R            | Polar      | Positive  | Basic       | Large      | Hydrophilic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |  2 | ASN             | N            | Polar      | Uncharged | Amide       | Small      | Hydrophilic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |  3 | ASP             | D            | Polar      | Negative  | Acidic      | Small      | Hydrophilic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |  4 | ASX             | B            | Polar      | Uncharged | Aliphatic   | Medium     | Hydrophilic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |  5 | CYS             | C            | Non-Polar  | Uncharged | Sulfur      | Small      | Hydrophobic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |  6 | GLU             | E            | Polar      | Negative  | Acidic      | Medium     | Hydrophilic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |  7 | GLN             | Q            | Polar      | Uncharged | Amide       | Medium     | Hydrophilic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |  8 | GLY             | G            | Non-Polar  | Uncharged | Aliphatic   | Very small | Neutral      |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    |  9 | HIS             | H            | Polar      | Positive  | Basic       | Medium     | Neutral      |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 10 | ILE             | I            | Non-Polar  | Uncharged | Aliphatic   | Large      | Hydrophobic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 11 | LEU             | L            | Non-Polar  | Uncharged | Aliphatic   | Large      | Hydrophobic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 12 | LYS             | K            | Non-Polar  | Positive  | Basic       | Large      | Hydrophilic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 13 | MET             | M            | Non-Polar  | Uncharged | Sulfur      | Large      | Hydrophobic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 14 | PHE             | F            | Non-Polar  | Uncharged | Aromatic    | Very large | Hydrophobic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 15 | PRO             | P            | Non-Polar  | Uncharged | Aliphatic   | Small      | Neutral      |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 16 | SER             | S            | Polar      | Uncharged | Hydroxyl    | Very small | Neutral      |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 17 | THR             | T            | Polar      | Uncharged | Hydroxyl    | Small      | Neutral      |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 18 | TRP             | W            | Non-Polar  | Uncharged | Aromatic    | Very large | Hydrophobic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 19 | TYR             | Y            | Non-Polar  | Uncharged | Aromatic    | Very large | Neutral      |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    | 20 | VAL             | V            | Non-Polar  | Uncharged | Aliphatic   | Medium     | Hydrophobic  |
    +----+-----------------+--------------+------------+-----------+-------------+------------+--------------+
    """
    map = pd.DataFrame(
        [
            {
                "three_letters": "ALA",
                "one_letter": "A",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Aliphatic",
                "volume": "Very small",
                "hydropathy": "Hydrophobic"
            },
            {
                "three_letters": "ARG",
                "one_letter": "R",
                "polarity": "Polar",
                "charge": "Positive",
                "chemical": "Basic",
                "volume": "Large",
                "hydropathy": "Hydrophilic",
            },
            {
                "three_letters": "ASN",
                "one_letter": "N",
                "polarity": "Polar",
                "charge": "Uncharged",
                "chemical": "Amide",
                "volume": "Small",
                "hydropathy": "Hydrophilic",
            },
            {
                "three_letters": "ASP",
                "one_letter": "D",
                "polarity": "Polar",
                "charge": 'Negative',
                "chemical": "Acidic",
                "volume": "Small",
                "hydropathy": "Hydrophilic",
            },
            {
                "three_letters": "ASX",
                "one_letter": "B",
                "polarity": "Polar",
                "charge": "Uncharged",
                "chemical": "Aliphatic",
                "volume": "Medium",
                "hydropathy": "Hydrophilic",
            },
            {
                "three_letters": "CYS",
                "one_letter": "C",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Sulfur",
                "volume": "Small",
                "hydropathy": "Hydrophobic"
            },
            {
                "three_letters": "GLU",
                "one_letter": "E",
                "polarity": "Polar",
                "charge": "Negative",
                "chemical": "Acidic",
                "volume": "Medium",
                "hydropathy": "Hydrophilic",
            },
            {
                "three_letters": "GLN",
                "one_letter": "Q",
                "polarity": "Polar",
                "charge": "Uncharged",
                "chemical": "Amide",
                "volume": "Medium",
                "hydropathy": "Hydrophilic",
            },
            {
                "three_letters": "GLY",
                "one_letter": "G",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Aliphatic",
                "volume": "Very small",
                "hydropathy": "Neutral"
            },
            {
                "three_letters": "HIS",
                "one_letter": "H",
                "polarity": "Polar",
                "charge": "Positive",
                "chemical": "Basic",
                "volume": "Medium",
                "hydropathy": "Neutral"
            },
            {
                "three_letters": "ILE",
                "one_letter": "I",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Aliphatic",
                "volume": "Large",
                "hydropathy": "Hydrophobic"
            },
            {
                "three_letters": "LEU",
                "one_letter": "L",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Aliphatic",
                "volume": "Large",
                "hydropathy": "Hydrophobic"
            },
            {
                "three_letters": "LYS",
                "one_letter": "K",
                "polarity": "Non-Polar",
                "charge": "Positive",
                "chemical": "Basic",
                "volume": "Large",
                "hydropathy": "Hydrophilic",
            },
            {
                "three_letters": "MET",
                "one_letter": "M",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Sulfur",
                "volume": "Large",
                "hydropathy": "Hydrophobic"
            },
            {
                "three_letters": "PHE",
                "one_letter": "F",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Aromatic",
                "volume": "Very large",
                "hydropathy": "Hydrophobic"
            },
            {
                "three_letters": "PRO",
                "one_letter": "P",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Aliphatic",
                "volume": "Small",
                "hydropathy": "Neutral"
            },
            {
                "three_letters": "SER",
                "one_letter": "S",
                "polarity": "Polar",
                "charge": "Uncharged",
                "chemical": "Hydroxyl",
                "volume": "Very small",
                "hydropathy": "Neutral"
            },
            {
                "three_letters": "THR",
                "one_letter": "T",
                "polarity": "Polar",
                "charge": "Uncharged",
                "chemical": "Hydroxyl",
                "volume": "Small",
                "hydropathy": "Neutral"
            },
            {
                "three_letters": "TRP",
                "one_letter": "W",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Aromatic",
                "volume": "Very large",
                "hydropathy": "Hydrophobic"
            },
            {
                "three_letters": "TYR",
                "one_letter": "Y",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Aromatic",
                "volume": "Very large",
                "hydropathy": "Neutral"
            },
            {
                "three_letters": "VAL",
                "one_letter": "V",
                "polarity": "Non-Polar",
                "charge": "Uncharged",
                "chemical": "Aliphatic",
                "volume": "Medium",
                "hydropathy": "Hydrophobic"
            },
        ]
    )

    @classmethod
    def three_to_one_letter(cls, aminoacid: str) -> str:
        """
        Converts three letter aminoacid code to one letter aminoacid code.

        :param aminoacid: three letter aminoacid code
        :type aminoacid: str
        :return: one letter aminoacid code
        :rtype: str
        """
        return cls.map.loc[cls.map.three_letters == aminoacid, 'one_letter'].item()

    @classmethod
    def one_to_three_letter(cls, aminoacid: str) -> str:
        """
        Converts one letter aminoacid code to three letter aminoacid code.

        :param aminoacid: one letter aminoacid code
        :type aminoacid: str
        :return: three letter aminoacid code
        :rtype: str
        """
        return cls.map.loc[cls.map.one_letter == aminoacid, 'three_letters'].item()

    @classmethod
    def get_polarity(cls, aminoacid: str):
        """
        Returns aminoacid polarity.

        :param aminoacid: one letter aminoacid code
        :type aminoacid: str
        :return: aminoacid polarity
        :rtype: str
        """
        return cls.map.loc[cls.map.one_letter == aminoacid, 'polarity'].item()

    @classmethod
    def get_charge(cls, aminoacid: str):
        """
        Returns aminoacid charge.

        :param aminoacid: one letter aminoacid code
        :type aminoacid: str
        :return: aminoacid charge
        :rtype: str
        """
        return cls.map.loc[cls.map.one_letter == aminoacid, 'charge'].item()

    @classmethod
    def get_chemical_properties(cls, aminoacid: str):
        """
        Returns aminoacid chemical properties.

        :param aminoacid: one letter aminoacid code
        :type aminoacid: str
        :return: aminoacid chemical properties
        :rtype: str
        """
        return cls.map.loc[cls.map.one_letter == aminoacid, 'chemical'].item()

    @classmethod
    def get_volume_size(cls, aminoacid: str):
        """
        Returns aminoacid volume size.

        :param aminoacid: one letter aminoacid code
        :type aminoacid: str
        :return: aminoacid volume size
        :rtype: str
        """
        return cls.map.loc[cls.map.one_letter == aminoacid, 'volume'].item()
    
    @classmethod
    def get_hydropathy(cls, aminoacid: str):
        """
        Returns aminoacid hydropathy.

        :param aminoacid: one letter aminoacid code
        :type aminoacid: str
        :return: aminoacid hydropathy
        :rtype: str
        """
        return cls.map.loc[cls.map.one_letter == aminoacid, 'hydropathy'].item()
