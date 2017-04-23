import argparse
import os
from . import parser
from .deobfuscator import Deobfuscator


def linter():
    optParser = argparse.ArgumentParser(description="SC2 Galaxy code linter")
    optParser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1"
    )
    optParser.add_argument(
        "--file",
        metavar="file",
        type=str,
        help="Filename of the galaxy script you wish to lint"
    )
    optParser.add_argument(
        "--ignore-filesize",
        action="store_true",
        help="Ignore file size limit of 10kb"
    )
    params = optParser.parse_args()
    prs = parser.Parser("./", False)
    if os.stat(params.file).st_size < 50000 or params.ignore_filesize:
        prs.parseFile(params.file)
    else:
        print("galaxylint cannot handle such a big file cause of performance issues.")
        print("filesize = %d ; current limit = %d" % (os.stat(params.file).st_size, 50000))


def deobfuscator():
    optParser = argparse.ArgumentParser(description="Galaxy code deobfuscator")
    optParser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1"
    )
    optParser.add_argument(
        "inputfile",
        metavar="inputfile",
        type=str,
        help="Source file to obfuscate"
    )
    optParser.add_argument(
        "-w", "--overwrite",
        action="store_true",
        help="Overwrite original file"
    )
    optParser.add_argument(
        "--output",
        dest="outfile",
        metavar="FILENAME",
        help="Output filename"
    )
    optParser.add_argument(
        "--tstrings",
        dest="tstrings",
        metavar="TriggerStrings",
        help="Path to TriggerStrings.txt"
    )
    optParser.add_argument(
        "--gstrings",
        dest="gstrings",
        metavar="GameStrings",
        help="Path to GameStrings.txt"
    )
    params = optParser.parse_args()

    d = Deobfuscator(params)
    d.deobfuscate(params.inputfile)
