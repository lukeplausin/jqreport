import argparse
import datetime
import os
import yaml
import json
import sys
from .cognition import Cognition

# import dateutil.parser

DEFAULT_OUTPUT_FILE = "jqreport_{}.html".format(datetime.datetime.utcnow().isoformat())

def main():
    # CLI entrypoint
    parser = argparse.ArgumentParser(
        description='Build an HTML report from JSON or YAML data in seconds.')
    parser.add_argument('-f', '--input-file', dest='in_file',
        help='Input JSON or YAML file (you can also pipe data in).')
    parser.add_argument('-o', '--output-file', dest='out_file',
        default=DEFAULT_OUTPUT_FILE,
        help='Output HTML file. Default: {}'.format(DEFAULT_OUTPUT_FILE))

    # TODO - add other parameters to taste
    # Reorder => yes or no?
    # It might make sense to reorder keys based on size / alphabetical, or keep as is

    args = parser.parse_args()
    if args.in_file:
        with open(args.in_file, 'r') as f:
            source_data = yaml.safe_load(f)
    else:
        source_data = yaml.safe_load(sys.stdin)
    cog = Cognition(source_data)

    with open(args.out_file, 'w') as f:
        f.write(cog.render())

if __name__ == "__main__":
    main()
