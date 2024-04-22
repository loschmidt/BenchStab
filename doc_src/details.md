(details)=
# Details

(cli-arguments)=
## CLI arguments

```bash
benchstab [-h] [--include INCLUDE] [--exclude EXCLUDE] [--pred-type TYPE1 TYPE2] 
                [--config CONFIG] [--source SOURCE] [--output OUTPUT] [--verbose] [--quiet] [--skip-header] [--output OUTPUT] [--list-predictors] [--permissive] [--dry-run]
```

Description of the arguments:

- `--include INCLUDE` allows the user to specify a subset of predictors, separated by a comma, from which the predictions will be acquired.
- `--exclude EXCLUDE` allows the user to specify the subset of predictors, separated by a comma, excluded in the process of acquiring predictions. If both `--include` and `--exclude` are supplied, `--exclude` will be ignored.
- `--pred-type` allows the user to define which protein formats will be used as inputs to the predictor. fo Possible `Type` options are (by default, all options are allowed):
  - `sequence` - allow sequential predictors.
  - `structure` - allow structural predictors, PDB accession code is always preferred before PDB files.
- `--config CONFIG` predictor configuration file in `.json` format. For a more detailed description, please refer to section [Accepted file formats](#accepted-file-formats)
- `--source SOURCE` mutation file, has to obey a specific format defined in the section [Accepted file formats](#accepted-file-formats). If not supplied, the application will attempt to read from stdin.
- `--verbose` adds full logging of preprocessing errors and warnings, dataset summary and real-time prediction status updates. This will also include the `status_message` field in the results, providing more detailed information about the prediction status.
- `--quiet` disables all logging except for the prediction results and critical errors. Overrides the `--verbose` option.
- `--output OUTPUT` file path, where the folder with results will be created. If not supplied, the application will not attempt to store the prediction results.
- `--permissive` if enabled, exceptions in mutation file parsing will be fatal.
- `--list-predictors` lists all implemented predictor clients.
- `--dry-run` if enabled, the application will not attempt to acquire predictions, but will only parse the mutation file and print the selected predictors to the console.
- `--skip-header` If enabled, the application will skip the first line of the provided mutation file.

If neither `--include` nor `--exclude` are supplied, the application will acquire predictions from all implemented predictors.

(output)=
### Output

During preprocessing, if the `--verbose [1|2]` option is enabled, if any problems are found in the mutation file, the application will log them along with their severity to the console. The severity levels are as follows:

- `INFO` – information about the mutation file.
- `WARNING` – row in the mutation file contains invalid data, but the application will still attempt to acquire the prediction. Warnings are usually raised if:
  - the provided PDB file, or PDB file from RCSB failed the BioPython's validation.
  - in case of rows with PDB ID, the modified position does not match the sequence from UniProt.
  - in case of rows with PDB ID, the modified position does not match the sequence from RCSB.
  - in case of rows with PDB file, the modified position does not match the sequence in the PDB file.
- `ERROR` - fatal errors that will prevent the application from acquiring the prediction.

If any errors are found, the application will raise an exception at the end of the preprocessing. If you wish to skip the invalid records and continue with the rest of the dataset, pass `--permissive` as an argument.

By default, BenchStab prints the prediction results to stdout in `csv` format. Together with the results, the application provides a short summary of the preprocessed dataset. If the `--verbose [1|2]` option is enabled, the application will also print the prediction status to the console. If the user provides a path via `--output` parameter, the BenchStab's output is also saved to a folder with the name `predictorclient_YYMMDD_HHMMSS` in the user-specified location. The folder will contain the following files:

- `results.csv` – exact copy of results printed to stdout. Contains the results of the prediction in `csv` format. The file contains the following columns:

  - `identifier` – protein identifier
  - `mutation` – mutation in the format `original_amino_acid$position$mutated_amino_acid`
  - `chain` – the chain identifier (only in the case of protein structures)
  - `DDG` – predicted change in Gibbs free energy
  - `status` – predictor's job status. Possible values are:
    - `finished` – prediction has finished successfully
    - `waiting` – the program was terminated while waiting for resolution
    - `timeout` – prediction timed out, no results were acquired
    - `processing` – the program was terminated while processing
    - `response parsing failed` – failed to parse the predictor's HTML response
    - `connection failed` – failed to connect to the predictor's webserver
    - `other failure` – unexpected errors
    - `failed` – predictor has failed to acquire the prediction, most likely due to the invalid protein/chain/mutation combination
    - Or a custom, predictor-specific error message
  - `status_message` – additional information about the prediction status. Populated only if `--verbose 2` option is enabled
  - `predictor` – predictor name
  - `input_type` – type of predictor based on an accepted protein input format. Possible values are:
    - `PdbID` – predictor accepts PDB accession codes.
    - `PdbFile` – predictor accepts PDB files.
    - `Sequence` – predictor accepts protein sequences.
  - `url` – URL of the results page on the predictor's website. Populated only for job-based predictors. Useful if the user wants to extract additional information, check why the prediction failed or look at results in case of a timeout.
  - `Elapsed Time (sec.)` – time elapsed between querying the predictor and the acquisition of the results.

  Example of the `results.csv` file:

  ```bash
  identifier,mutation,chain,DDG,status,predictor,input_type,url,Elapsed Time (sec.)
  1CSE,L45G,I,-2.5,finished,DDGun,Sequence,https://folding.biofold.org/cgi-bin/find-ddgun-job.cgi?njob=515416&wdir=ddgun-2de6fb21-6884-11ee-a05a-3d86aaaaaaaa,60.82
  1CSE,L45A,I,-1.4,finished,DDGun,Sequence,https://folding.biofold.org/cgi-bin/find-ddgun-job.cgi?njob=515418&wdir=ddgun-2df7a2c2-6884-11ee-8b65-3d8e38e38e38,60.79
  1CSE,L45G,I,,predictor not available,IMutant3,Sequence,http://gpcr.biocomp.unibo.it/cgi/predictors/I-Mutant3.0/I-Mutant3.0.cgi,0.0
  1CSE,L45A,I,,predictor not available,IMutant3,Sequence,http://gpcr.biocomp.unibo.it/cgi/predictors/I-Mutant3.0/I-Mutant3.0.cgi,0.0
  1CSE,L45G,I,Decrease,finished,iStable,Sequence,http://predictor.nchu.edu.tw/iStable/indexSeq.php,3.01
  1CSE,L45A,I,Decrease,finished,iStable,Sequence,http://predictor.nchu.edu.tw/iStable/indexSeq.php,2.97
  1CSE,L45G,I,-5.74,finished,IMutant2,Sequence,https://folding.biofold.org/i-mutant//www-data/output/Mut35437/output.html,60.64
  1CSE,L45A,I,-4.46,finished,IMutant2,Sequence,https://folding.biofold.org/i-mutant//www-data/output/Mut35442/output.html,60.66
  1CSE,L45G,I,-2.3847425,finished,Mupro,Sequence,http://mupro.proteomics.ics.uci.edu/cgi-bin/predict.pl,2.62
  1CSE,L45A,I,-2.358147,finished,Mupro,Sequence,http://mupro.proteomics.ics.uci.edu/cgi-bin/predict.pl,2.02
  ```

- `preprocessed_input.csv` – contains the processed mutation file in `csv` format. The file is identical to the input mutation file, except for the addition of the following columns:

  - `identifier` – protein identifier
  - `mutation` – mutation in the format `original_amino_acid$position$mutated_amino_acid`.
  - `fasta_mutation` - mutation in the format `original_amino_acid$position$mutated_amino_acid` adjusted to the acquired sequence. This is useful in case of sequential predictors, where the mutation position is adjusted to the acquired sequence. In case of structural predictors, this field is unused.
  - `chain` – chain identifier (only in case of protein structures)
  - `ph` – pH value of the environment (optional)
  - `temperature` – temperature of the environment (optional)
  - `fasta` – protein sequence in FASTA format

  Example of the `preprocessed_input.csv` file (fasta sequence is shortened by `...` in the markdown):

  ```bash
  identifier,mutation,chain,fasta_mutation,fasta,ph,temperature
  1C52,M69H,A,M69H,QADGAKIYA...,7,25
  1C52,M69A,A,M69A,QADGAKIYA...,7,25
  ```

- `summary.json` - contains the dataset summary in `json` format. The summary contains the following fields:

  - `mutations` - number of mutations in the dataset.
  - `identifiers` - number of proteins in the dataset.
  - `avg_mut` - average number of mutations per protein.
  - `mut_positive` - number of mutant amino acids with positive charge\`.
  - `mut_negative` - number of mutant amino acids with negative charge.
  - `mut_no_charge` - number of mutant amino acids with no charge.
  - `mut_acidic` - number of mutant amino acids with acidic properties\`.
  - `mut_basic"` - number of mutant amino acids with basic properties.
  - `mut_balanced` - number of m utant amino acids with balanced properties.
  - `mut_polar` - number of polar mutant amino acids.
  - `mut_nonpolar` - number of non-polar mutant amino acids.

  Example of the `summary.json` file:

  ```json
  {
      "mutations": 2,
      "identifiers": 2,
      "avg_mut": 1.0,
      "mut_positive": 0,
      "mut_negative": 0,
      "mut_no_charge": 2,
      "mut_acidic": 0,
      "mut_basic": 0,
      "mut_balanced": 0,
      "mut_polar": 0,
      "mut_nonpolar": 2
  }
  ```
(more-usage-example)=
### More usage examples

Minimal example: acquire prediction from all predictors (since no `--exclude` or `--include` parameters are supplied) on entry specified through pipe and print them to stdout:

```bash
echo 1CSE L45G I | benchstab
```

The option `--pred-type` can be used to further specify the type of the selected predictor used based on the input format. This is useful for predictors that accept both sequential and structural inputs. By default, the predictor client will only acquire predictions from structural predictors. If you wish to acquire sequential predictors, you have to specify the `--pred-type` option:

```
echo 1CSE L45G I | benchstab --pred-type sequence
```

There is also a possibility of allowing multiple input types for predictors at once. For example, if you wish to acquire predictions from both sequential and structural predictors, you can use the following command:

```bash
echo 1CSE L45G I | benchstab --pred-type sequence structure
```

There are multiple ways to specify the input file:

```bash
# as a file path argument
benchstab --source input.csv 
# as a stdin input
echo 1CSE L45G I\n1CSE L45A I | benchstab 
# or as a file through stdin
benchstab < input.csv
```

Where the example mutation file `input.csv` can look like this:

```bash
1CSE,L45G,I
1CSE,L45A,I
```

For the exact definition of the mutation file format, please refer to the [Accepted file formats](#accepted-file-formats) section.

`benchstab` will always export the results to stdout in `csv` format. If you wish to save the results to a file, you can use the `--output` option or redirect the stdout to a file (without `--verbose` option):

```bash
# save results to a file
benchstab --output results.csv < input.txt
# redirect stdout to a file
benchstab < input.txt > results.csv
```

By default, `predictor` manager operates in a strict mode, which means that it will raise an exception if any errors are found in the mutation file. If you wish to skip the invalid records and continue with the filtered dataset, pass `permissive=False` as a parameter in the preprocessor's constructor.

```bash
benchstab --include automute --permissive < input.csv
```

If you wish to limit the amount of used predictor clients:

```bash
# acquire predictions from all predictors except `Automute` and `Cupsat`
benchstab --exclude automute cupsat < input.csv
# acquire predictions from `Automute` and `Cupsat` only
benchstab --include automute cupsat < input.csv
```

You can pass your own set of options to the predictor client. For example, if you wish to pass the login parameters to the `PopMusic` predictor:

- First, you have to create a config file in `json` format (e.g., `config.json`):

```json
{
    "popmusic": {
        "username": "your_email",
        "password": "your_password"
    }
}
```

- and then pass it to the predictor client as `--config` option:

```bash
benchstab --config config.json --include popmusic < input.csv
```

For a more detailed description of the predictor client's options, please refer to the [Configuration file](#configuration-file) section.

By default, the application will only print the prediction results to stdout. If you wish to see the preprocessing errors and warnings, dataset summary and real-time prediction status updates, you can use the `--verbose` option. Besides `0` which is deafault option, the `--verbose` option accepts 2 additional values:

- `1` – adds full logging of preprocessing errors and warnings and dataset summary. Real-time prediction status updates are displayed in a single line in the console.
  ```bash
  echo 1THQ F55A A\n1CSE L45G I | benchstab --verbose 1 --include mupro --pred-type sequence
  # Using above command with verbosity level set to "1" will display the following output after the status change:
    INFO:iStableSequence (1/2): Status change in "1THQ":"F55A" to "finished".
  # After another status change, the previous output is wiped out and replaced by new information:
    INFO:iStableSequence (2/2): Status change in "1CSE":"L45G" to "finished".
  ```
- `2` – adds full logging of preprocessing errors and warnings, dataset summary and real-time prediction status updates.
  ```bash
  echo 1THQ F55A A\n1CSE L45G I | benchstab --verbose 2 --include mupro --pred-type sequence
  # Using above command with verbosity level set to "2" will display the following output after the status change:
    INFO:iStableSequence (1/2): Status change in "1THQ":"F55A" to "finished".
  # After another change, the previous reports are preserved:
    INFO:iStableSequence (1/2): Status change in "1THQ":"F55A" to "finished".
    INFO:iStableSequence (2/2): Status change in "1CSE":"L45G" to "finished".
  ```

An example of a cascade acquisition of protein sequence from PDB ID is mentioned in [Accepted file formats](#accepted-file-formats). The sequence acquired from UniProt fails the validation, but the sequence acquired from RCSB is valid:

```bash
echo 1THQ F55A A | benchstab.exe --include mupro --verbose 1 --pred-type sequence
```
(python-library)=
## Python library

(example-usage-of-benchstab)=
### Example usage of BenchStab

```python
    from benchstab import BenchStab
    
    client = BenchStab(input_file="input.txt")
    results = client()
```

(example-usage-of-preprocessor-singular-predictor)
### Example usage of preprocessor/singular predictor

```python
    import asyncio
    from benchstab import Preprocessor
    from benchstab.predictors.web import INPSPdbID

    data = Preprocessor(input="data.txt").parse()
    pred = INPSPdbID(data=data)
    results = asyncio.get_event_loop().run_until_complete(pred.compute())
```

Preprocessor:

1. By default, the `Preprocessor` class uses the flag `permissive=True`, which raises an exception at the end of the preprocessing, if any errors were found. This is to prevent the submission of invalid proteins/mutations to predictor servers, which can lead to slowdowns in the prediction acquisition process. If you wish to skip the invalid records and continue with the filtered dataset, pass `permissive=False` as a parameter in the preprocessor's constructor.
1. By not setting the parameter `outfolder` (or setting it as `None), the `Preprocessor\` will not attempt to save the processed dataset.
1. As an `input` parameter, the preprocessor accepts 3 different types:
   1. File path (`str`).
   1. `\n`-separated string mimicking the file (`str`).
   1. Input rows as a string list elements (`List[str]`).

(accepted-file-formats)=
## Accepted file formats

(mutation-file)=
### Mutation file

The predictor client accepts a single file with proteins and their mutations in `.txt`, `.csv` or `.tsv` format. Currently, only `space`, `tab`, `comma` and `semicolon` symbols are supported as column separators. The column structure of the mutation file has to be strictly adhered to, and it is defined as:

```
$identifier $mutation $chain ?ph ?temperature
```

where `identifier`, `mutation`, and `chain` (only in case of protein structures – PDB ID or file) params are required, while `ph` + `temperature` are optional. Accepted protein inputs are:

- PDB accession code (e.g., `1CSE`)
  - If a user provides PDB accession code, the application will attempt to also acquire the protein sequence firstly from UniProt, and if that fails, from RCSB. This allows the user the option to acquire sequential predictions by providing only the PDB accession code.
    - If the sequence does not exist in UniProt, or the adjusted mutation does not match the acquired sequence, the application will raise a warning. Since the sequence length and positions sometimes differ between UniProt and RCSB, the application will adjust the mutation position. For example, if the mutation `L45G` is provided, but the sequence acquired from UniProt is shorter by 2 amino acids, the application will adjust the mutation to `L43G` before validating. Both mutations are kept in the dataset and used based on the predictor\`s input type.
    - If preprocessor fails to acquire the sequence from UniProt, it will attempt to acquire it from RCSB. If the provided mutation does not match the sequence acquired from RCSB, the application will raise a warning.
    - If preprocessor fails to acquire the sequence from both UniProt and RCSB, dataset won\`t contain the sequence record. This will lead to the failure of all sequential predictors on a given record.
- UniProt accession code (e.g., `P05067`)
- path to a PDB structural file (`.pdb`), for example `./1CSE.pdb`.
  - When needed, the sequence is inferred from the PDB file. If the mutated position does not match the sequence, the application will raise a warning and all sequential predictors will automatically fail on this record.
  - BenchStab extracts the sequence from the `seqres` part of the PDB file via BioPython's `SeqIO` module. This approach assumes that the sequence indexing in the PDB file starts at `0`. If the sequence indexing starts at a different number, the user has to manually adjust the mutation position in the mutation file. Otherwise, the application will raise a warning and all sequential predictors will automatically fail on this record.
- path to a FASTA sequence file (`.fasta`). for example `./1CSE.fasta`.
- Raw fasta sequence without header (e.g., `TEFGSELKSFPEVVGKTVDQAREYFTLHYPQYNVYFLPEGSPVTLDLRYNRVRVFYNPGTNVVNHVPHVG`)

Different protein identifiers can be combined, so the final mutation file `muts.txt` can look like this:

```
1CSE L45G I
P05067 A1B
./1CSE.pdb L45A I
./1CSE.fasta F10I
TEFGSELKSFPEVVGKTVDQAREYFTLHYPQYNVYFLPEGSPVTLDLRYNRVRVFYNPGTNVVNHVPHVG L45G
```

(configuration-file)=
### Configuration file

The configuration file is in `.json` format and contains both general and predictor-specific settings. The configuration file is optional, and if not supplied, the application will use the default settings. An example of a configuration file (e.g., `config.json`) could be:

```json
{
    //General settings
    "wait_interval": 60,
    "max_retries": 100,
    "batch_size": 5,
    //Predictor-specific configuration
    "popmusic": {
        "username": "email@email.com",
        "password": "very strong password"
    },
    "ddgun": { "max_retries": 10 },
    "automute": { "model_type": "svm" },
    "premps": {} // this can be repeated for every predictor
}
```

- General:
  - `"max_retries"` Maximum amount of times to check the job's status before timing out.
  - `"wait_interval"` Time (in seconds) between each job status check.
  - `"batch_size"` maximum concurrent requests sent to the predictor.
    - Be careful, setting this parameter too high might cause denial of service attacks in case of some predictors.
    - If `-1` is passed, all requests will be sent at once.
- Predictor-specific: They are unique to the source implementation of each specific predictor. You can find them described in the `benchstab/predictors/web/<predictor_name>` subfolder.

The predictor settings are applied in the following order:

1. Default predictor settings.
1. General settings in the configuration file.
1. Predictor-specific settings in the configuration file.

So the predictor-specific settings have the highest priority and always overwrite all other options. Each predictor has its own set of unique default settings, you can view their definition in:

- `.json` format, specified in README located in predictor's subfolder – `benchstab/predictors/web/<predictor_name>`.
- `python` format, defined in base predictor implementation found in `benchstab/predictors/web/<predictor_name>/base.py`.

(steps-for-implementing-new-predictor)=
## Steps for implementing new predictor

- Create a new folder in `benchstab/predictors/web/` with the name of the predictor. In this folder:
  - Create a file `base.py` for the predictor's general implementation.
    ```python
    class _PremPS(BaseGetPredictor):
      ...
    ```
  - Depending on the input format accepted by the predictor, create files `id.py`, `file.py` and `sequence.py` in the created folder. These files will contain the predictor's implementations for each format, inherited from the `base.py` file. Usually, these files will only contain the `prepare_payload` method, and sometimes the `format_mutation` method.
    - `prepare_payload` processes the DatasetRow object and returns a dictionary with the payload for the POST request.
    - `format_mutation` is used to format the mutation in the format accepted by the predictor. This method is optional, and if not implemented, the mutation will be formatted as `original_amino_acid$position$mutated_amino_acid`. If the mutation format is the same for every input format, it is recommended to implement this method in the `base.py` file.
    ```python
    class PremPSPdbID(_PremPS):
      def prepare_payload(self, row: pd.Series) -> Dict:
        return {
            'example': '0',
            'pdb_id': row['identifier'].id,
            'pdb_mol': self.pdb_mol,
            'bioassembly': self.bioassembly,
            'isPl': self.is_pl,
            'pdb_file': ''
        }
    ```
  - Create a new file `__init__.py` importing all implementations, e.g.:
    ```python
    from .id import PremPSPdbID
    from .file import PremPSPdbFile
    ```
- Implement the `base` class by adhering to all necessary steps described in the section about [simple](#a-predictors-with-instant-results) predictors.
  - If the implemented predictor employs prediction queues or uses jobs, you will also have to follow the steps in the section about [job-based](#b-job-based-predictors) predictors.
  - If the implemented predictor requires authentication, also follow the steps in the section about [authentication](#c-predictors-requiring-authentication) predictors.
- Include the predictor in the `benchstab/predictors/web/__init__.py` file.
  ```python
  from .premps import PremPSPdbID, PremPSPdbFile
  ```
- The base predictor class will have to inherit from the `BasePostPredictor` class.
  ```python
  class _DUET(BasePostPredictor):
    ...
  ```
- The `BasePostPredictor` implements the logic for sending a POST request to the predictor's webserver. To execute your logic before sending the POST request, you can override the `send_query` method and add your code.
  ```python
  class _DUET(BasePostPredictor):
    ...
    async def send_query(self, session, index: int, *args, **kwargs):
      # do something
      return await super().send_query(session, index, *args, **kwargs)
  ```

(a-predictors-with-instant-results)=
### A. Predictors with instant results

- Each call of `send_query` calls a `get_post_handler`, which is used to parse the response and set the adequate status. This method is not implemented in the base class and has to be implemented in the predictor's implementation.
  ```python
    async def default_post_handler(self, index, response, session):
        # It is an asynchronous request, so we have to await the response
        # Use the custom HTML parser to parse the response, if possible
        _res = self.html_parser.with_xpath(
            xpath="//div[@class = 'span4']/div[@class = 'well']", html=await response.text()
        )
        _duet = self.html_parser.with_xpath(xpath='./font[3]/text()', root=_res)
        _ddg = re.findall(r'[\-+]?\d*\.\d+', _duet)
        # If the response does not contain the following string, the prediction has failed
        if not _ddg:
            self.data.update_status(index, status.Failed())
            return False
        # Set the prediction results
        self.data.loc[index, 'DDG'] = float(_ddg[0])
        # Change the status to finished
        # If you are implementing the predictor with jobs, you should set the status to blocking – Processing/Waiting
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        return True
  ```

(b-job-based-predictors)=
### B. Job-based predictors

- The base predictor class will also have to inherit from the `BaseGetPredictor` class (no need to inherit from `BasePostPredictor` anymore).
  ```python
  class _PremPS(BaseGetPredictor):
    ...
  ```
- The `BastGetPredictor` implements the loop in which the predictor will check the status of the job. The loop will run until the job is finished or the maximum number of retries is reached. The loop will also check if the job has timed out. If the job has timed out, the predictor will raise a `TimeoutError` exception. The maximum number of retries and the wait interval between each status check can be set in the predictor's configuration file.
  - By default, it will check the status of the job and wait for the specified amount of time between each check. If you wish to add extra operations before or after the status check, you can override the `retrieve_result` method and implement your logic.
    ```python
    class _PremPS(BaseGetPredictor):
      ...
      async def retrieve_result(self, session, index) -> Response:
        # do something
        return await super().retrieve_result(session, index)
    ```
  - Usually, the dataset's method `is_blocking_status` is used to determine if the status is blocking.
- Each call of `retrieve_results` calls a `get_default_handler`, which is used to parse the response and set the adequate status. This method is not implemented in the base class and has to be implemented in the predictor's implementation.
  ```python
    async def default_get_handler(self, index, response, session):
        # It is an asynchronous request, so we have to await the response
        _text = await response.text()
        # If the response contains the following string, the job is still running
        if 'This page will reload automatically in 30 seconds' in _text:
            return False
        # Use the custom HTML parser to parse the response, if possible
        _df = self.html_parser.with_pandas(_text, index=1)
        # Format the DataFrame to match the output format
        _df = _df.rename(
            {'Mutation': 'mutation', 'Mutated Chain': 'chain', 'ΔΔG': 'DDG'}, axis=1
        )
        _df = _df.drop(['Structure', 'Location'], axis=1)
        _df['identifier'] = self.data.loc[index, 'identifier']
        # Update status
        self.data.update_status(index, status.Finished())
        self.data.loc[index, 'url'] = response.url
        # Append the results to the list of results
        self._prediction_results.append(_df)
        # Return True to stop the loop
        return True
  ```

(c-predictors-requiring-authentication)=
### C. Predictors requiring authentication

- The base predictor class will also have to inherit from `BaseAuthPredictor` class.
  ```python
  class _PoPMuSiC(BaseAuthentication, BaseGetPredictor):
    # Optional, only if the custom authentication payload is required
    credentials = PoPMuSiCCredentials
    ...
  ```
- If your predictor requires a custom authentication payload, different from the one provided by `BaseCredentials` implemented in `predictors.base`, you will have to create your own custom `credentials` class. This class has to inherit from `BaseCredentials` and implement the `get_payload` method, which will return a dictionary with the authentication payload.
  ```python
  @dataclass
  class PoPMuSiCCredentials(BaseCredentials):
    def get_payload(self, csrf):
      return {
        "_csrf_token": csrf,
        "_username": self.username,
        "_password": self.password,
        "_submit": "Login",
      }
  ```
- If you need to process your authentication request (e.g., process CSRF token), you can do so in `login_handler`. By default, it will only check if the authentication was successful by checking the response's status code. If you need to process the response further, you can override this method.
  ```python
  class _PoPMuSiC(BaseAuthentication, BaseGetPredictor):
    ...
    async def login_handler(self, response: Response) -> bool:
      return response.status_code == 200
  ```
- Authentication is usually the first step in the prediction acquisition process. If you wish to add extra operations before the authentication, you can override the `login` method and implement your logic.
  ```python
  class _PoPMuSiC(BaseAuthentication, BaseGetPredictor):
    ...
    async def login(self, session, index) -> bool:
      # do something
      return await super().login(session, index)

    async def login_handler(self, response: Response) -> bool:
      return response.status_code == 200
  ```
