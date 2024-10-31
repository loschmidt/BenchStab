<p align="center">
	<img alt="BenchStab logo" src="https://loschmidt.chemi.muni.cz/benchstab/logo.png" style="width: 50%;">
</p><p align="center">
	<a href="https://doi.org/10.1093/bioinformatics/btae553" target="_blank" ><img alt="Journal article" src="https://img.shields.io/badge/DOI-10.1093%2Fbioinformatics%2Fbtae553-blue"></a>
	<a href="https://x.com/loschmidtl" target="_blank"><img alt="X (formerly Twitter) Follow" src="https://img.shields.io/twitter/follow/loschmidtl" style="max-width: 100%;"></a>
</p>

**BenchStab** is a *command-line* (CLI) tool for querying predictors of protein stability on the web.

This is a quick guide. For further details, please continue to the [detailed documentation](https://loschmidt.chemi.muni.cz/benchstab/details.html).

## Citing

If you use our tool, please cite our paper:

> Velecký, J., Berezný M., Musil M., Damborsky J., Bednar, D., Mazurenko, S., 2024: BenchStab: a tool for automated querying the web-based stability predictors. *Bioinformatics* 40(9)

Kindly cite also all the underlying [predictors](https://loschmidt.chemi.muni.cz/benchstab/predictors.html) you use via this tool.

## Installation

Install using pip from this repository:

```bash
pip install git+https://github.com/loschmidt/BenchStab.git
```

Tested environments:

- macOS 14.4.1 / pip / Python 3.9.6
- RHEL 9.4 / pip / Python 3.9.18
- Windows 11 / pip / Python 3.9.13
- Windows 10 / anaconda / Python 3.9.19

Check the installation was successful by listing all available predictors:

```bash
benchstab -l
```

### Troubleshooting

<strong> 'benchstab' is not recognized as an internal or external command, operable program or batch file. </strong>

Once the package is successfully installed, the executable is located in Python's `Scripts/` directory. Please, add this directory to your `PATH` environment variable or use the Python installer with "Add Python to PATH" ([Windows](https://docs.python.org/3/using/windows.html#finding-the-python-executable)).

This problem is preceded by the following warning message from `pip`:\
`WARNING: The script benchstab.exe is installed in 'Path/To/Your/Python/Installation/Scripts' which is not on PATH.`

## Quick usage

- *"I investigate a specific mutation, and I want to see whether the popular predictors agree on its effect on the protein stability"*:

```bash
echo 1CSE L45G I | benchstab
```
The application will acquire predictions from all implemented predictors and print the results to stdout in `csv` format.

- *"I have a [dataset](https://loschmidt.chemi.muni.cz/benchstab/details.html#mutation-file) prepared, and I want to query structural variants of my three favorite predictors and save the results to a file"*:

`dataset.csv`:

```bash
1CSE,L45G,I
1CSE,L45A,I
2Q98,H173A,A
1MJC,F31S,A
```

The command:
```bash
benchstab --include automute cupsat ddgun --pred-type structure --source dataset.csv --output path_to_results_folder/
```
The results will be saved to a folder named `benchstab_YYMMDD_HHMMSS` in a file `results.csv`. For more information about the output, please refer to the [BenchStab output](https://loschmidt.chemi.muni.cz/benchstab/details.html#output) section.

## Quick Python usage

- *"I investigate a specific mutation, and I want to see whether the popular predictors agree on its effect on the protein stability"*:

```python
from benchstab import BenchStab

client = BenchStab(input_file="input.txt")
results = client()
```

- *"I have a [dataset](https://loschmidt.chemi.muni.cz/benchstab/details.html#mutation-file) prepared, and I want to query structural variants of my three favorite predictors and save the results to a file"*:

```python
from benchstab import BenchStab

client = BenchStab(
  input_file='dataset.csv',
  include=["automute", "cupsat", "ddgun"],
  output="path_to_results_folder/"
)
results = client()
```

The results will be saved in the same manner as in the CLI example.
