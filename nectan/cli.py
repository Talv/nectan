import argparse
import os
from . import parser
from .deobfuscator import Deobfuscator
from .obfuscator import Obfuscator
from .linter import Linter
from .symbol_provider import SymbolProvider
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

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
        help="Ignore file size limit of 500kb"
    )
    optParser.add_argument(
        "--include",
        metavar="include",
        type=str,
        nargs='+',
        help="Directories to look for includes"
    )
    params = optParser.parse_args()
    if os.stat(params.file).st_size < 500000 or params.ignore_filesize:
        ln = Linter(params.include)
        ln.lintFile(params.file)
    else:
        print("galaxylint cannot handle such a big file cause of performance issues.")
        print("filesize = %d ; current limit = %d" % (os.stat(params.file).st_size, 500000))


def symbol():
    optParser = argparse.ArgumentParser(description="Galaxy symbol information provider")
    optParser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1"
    )
    params = optParser.parse_args()
    sm = SymbolProvider("./sc2-sources")
    sm.index()


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


def obfuscator():
    optParser = argparse.ArgumentParser(description="Galaxy code obfuscator")
    optParser.add_argument(
        "--version",
        action = "version",
        version = "%(prog)s 0.1"
    )
    optParser.add_argument(
        "inputfile",
        metavar = "inputfile",
        type = str,
        help = "Source file to obfuscate"
    )
    optParser.add_argument(
        "-w", "--overwrite",
        action = "store_true",
        help = "Overwrite original file"
    )
    optParser.add_argument(
        "--output",
        dest = "outfile",
        metavar = "FILENAME",
        help = "Output filename"
    )
    optParser.add_argument(
        "-i",
        action = "append",
        dest = "includes",
        metavar = "DIR",
        nargs = "+",
        help = "Directory to lookup for includes"
    )
    optParser.add_argument(
        "-m", "--merge",
        action = "store_true",
        dest = "merge",
        # default = True,
        help = "Merge all includes into single file"
    )
    params = optParser.parse_args()

    obf = Obfuscator(params)
    obf.obfuscate(params.inputfile)
