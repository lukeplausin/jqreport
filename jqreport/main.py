import argparse
import datetime

# import dateutil.parser

DEFAULT_OUTPUT_FILE = "jqreport_{}.html".format(datetime.datetime.utcnow().isoformat())

def main():
    # CLI entrypoint
    parser = argparse.ArgumentParser(
        description='Build an HTML report from JSON or YAML data in seconds.')
    parser.add_argument('-f', '--input-file', dest='in_file',
        help='Input JSON or YAML file (you can also pipe data in).')
    parser.add_argument('-o', '--output-file', dest='out_file',
        help='Output HTML file. Default: {}'.format(DEFAULT_OUTPUT_FILE))

    # TODO - add other parameters to taste

    args = parser.parse_args()
    in_file = args.in_file
    out_file = args.out_file
    print(f"{in_file} => {out_file}")


if __name__ == "__main__":
    main()
