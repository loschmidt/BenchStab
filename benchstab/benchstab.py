import os
import sys
import json
import signal
from argparse import ArgumentParser
from functools import partial

import pandas as pd

from benchstab.client import BenchStab
from benchstab.utils.exceptions import BenchStabError

def signal_handler(sig, frame, client):
    """
    Signal handler for SIGINT and SIGTERM signals.
    """
    signal.signal(sig, signal.SIG_IGN)
    save_results(client)
    sys.exit(0)

def save_results(client, results = None):
    """
    Save results to file or print them to stdout.
    If the output file is not specified, the results will be printed to stdout.

    
    :param client: BenchStab instance
    :type client: BenchStab
    :param results: Results to save
    :type results: pd.DataFrame
    """
    if results is None:
        results = client.gather_results()

    with pd.option_context(
        'display.max_rows', None,
        'display.max_columns', None,
        'display.width', 2000,
        'display.float_format', '{:20,.2f}'.format,
        'display.max_colwidth', None
    ):
        if not client.save_results(results):
            print(results.to_csv(index=False, lineterminator='\n'))

def dump_predictors():
    """
    Print all available predictors to stdout. 
    """
    _text = [
        "List of supported SEQUENCE predictors:",
        "\t" + ", ".join([x.name for x in BenchStab.sequence_predictors]),
        "List of supported PDB_ID predictors:",
        "\t" + ", ".join([x.name for x in BenchStab.pdbid_predictors]),
        "List of supported PDB_FILE predictors:",
        "\t" + ", ".join([x.name for x in BenchStab.pdbfile_predictors]),
    ]
    print("\n".join(_text))


def main():
    """
    Main function of the application, which parses the arguments and runs the BenchStab client.
    """

    print(
        (
            "=====================================================================================\n"
            "Thank you for using BenchStab! If you like our tool, please consider citing our work:\n"
            "> Velecký, J., Berezný M., Musil M., Damborsky J., Bednar, D., Mazurenko, S., 2024:\n"
            "BenchStab: a tool for automated querying the web-based stability predictors.\n"
            "=====================================================================================\n"
        )
    )
    parser = ArgumentParser(
        prog="benchstab.py",
        description= \
        "\nMulti-Client application for efficient acquisition of thermodynamical values from protein stability prediction servers.\n"
    )
    parser.add_argument(
        "--include",
        "-i",
        nargs='+',
        default=[],
        help="allows the user to specify a subset of predictors, separated by a comma, from which the predictions will be acquired."
    )
    parser.add_argument(
        "--exclude",
        "-e",
        nargs='+',
        default=[],
        help="Subset of predictors, separated by space, excluded in the process of acquiring predictions. If both include and exclude are supplied, exclude will be ignored."
    )
    parser.add_argument(
        '--pred-type',
        '-t',
        nargs='+',
        help='Specifies which variations of predictors should be used. Available options: sequence, structure.',
        default=['structure', 'sequence'],
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Config file, with predictor parameters in .json format. For exact structure, please refer to the documentation."
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default=None,
        help="Mutation file, where has to be in required format: '(pdb_id|fasta_file|pdb_file) MUT CHAIN'."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="File path, where folder with results will be created. If not supplied, application will not attempt to store the prediction results."
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Prints additional information about the process of acquiring predictions."
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppresses all output except for errors. Overrides --verbose."
    )
    parser.add_argument(
        "--list-predictors",
        "-l",
        help="List all available predictors.",
        action="store_true"
    )
    parser.add_argument(
        "--permissive",
        "-p",
        help="Performs a permissive run, where errors are ignored and application will attempt to acquire predictions from all available predictors.",
        action="store_true"
    )
    parser.add_argument(
        "--dry-run",
        help="Performs a dry run, without actually sending any requests to the servers.",
        action="store_true"
    )
    parser.add_argument(
        "--skip-header",
        help="Skip header in input file.",
        action="store_true"
    )
    args = parser.parse_args()

    # Full tracebacks are printed only when verbose is set to 2
    if args.verbose < 2:
        sys.tracebacklimit = 0

    if args.list_predictors:
        dump_predictors()
        sys.exit(0)

    # Setting verbostity level (default is 1)
    verbosity = 1
    if args.verbose:
        verbosity = 2
    # Overriding verbosity level if quiet is set
    if args.quiet:
        verbosity = 0


    _config = args.config
    _input = args.source

    if _input is None:
        if sys.stdin.isatty():
            raise BenchStabError(
                (
                    "benchstab: error: Missing mutation file."
                    " Please provide mutation file either through console"
                    " standard input or by using the following argument : --source/-s."
                )
            )
        _input = sys.stdin.read()
    elif not os.path.isfile(_input):
        raise BenchStabError(
            f'benchstab: error: path "{_input}" defined by --source/-s does not exist.'
        )

    if isinstance(_config, str):
        try:
            if os.path.isfile(_config):
                with open(_config, 'r', encoding='utf-8') as f:
                    _config = json.load(f)
            else:
                _config = json.loads(_config)
        except json.JSONDecodeError as exc:
            raise BenchStabError(
                f'benchstab: error: Invalid JSON format in config file: {_config}'
            ) from exc

    client = BenchStab(
        input_file=_input,
        predictor_config=_config,
        include=list(set(args.include)) or None,
        exclude=list(set(args.exclude)) or None,
        allow_sequence_predictors='sequence' in args.pred_type,
        allow_struct_predictors='structure' in args.pred_type,
        outfolder=args.output,
        permissive=args.permissive,
        verbosity=verbosity,
        skip_header=args.skip_header
    )

    signal.signal(signal.SIGINT, partial(signal_handler, client=client))
    signal.signal(signal.SIGTERM, partial(signal_handler, client=client))

    out = client(dry_run=args.dry_run)

    if args.dry_run:
        return

    save_results(client, out)


if __name__ == "__main__":
    main()
