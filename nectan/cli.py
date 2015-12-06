import argparse
# import parser as gparser
from . import parser


def linter():
    optParser = argparse.ArgumentParser(description="SC2 Galaxy code linter")
    optParser.add_argument(
        "--version",
        action = "version",
        version = "%(prog)s 0.1"
    )
    optParser.add_argument(
        "--file",
        metavar = "file",
        type = str,
        help = "Filename of the galaxy script you wish to lint"
    )
    params = optParser.parse_args()
    prs = parser.Parser("./", False)
    prs.parseFile(params.file)

# if __name__ == "__main__":
#     linter()
