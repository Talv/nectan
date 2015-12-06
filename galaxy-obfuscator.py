# import nectan.parser
import nectan.obfuscator
import argparse


def main():
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

    obf = nectan.obfuscator.Obfuscator(params)
    obf.obfuscate(params.inputfile)


if __name__ == "__main__":
    main()
