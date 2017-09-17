>This package is no longer developed. Instead of trying to refactor existing codebase, I've decided to rewrite it in Typescript.\
>**Replacement: [plaxtony](https://github.com/Talv/plaxtony)**

# nectan
Python package providing utilities do deal with SC2 galaxy script. It can parse it into AST structure. And perform further tasks.

Features:
- code linting
- obfuscation
- deobfuscation
- indexing for code autocompletion (in IDE).

Source code of this package is somewhat messy.. as it was my training ground for learning python and understanding principles of building an AST.

## Installation

1. Install [Python](http://python.org/download/) and [pip](http://www.pip-installer.org/en/latest/installing.html).

1. Install `nectan` by typing the following in a terminal:
   ```
   [sudo] pip install https://github.com/Talv/nectan/archive/master.zip
   ```

## Usage

### Linter

```
usage: galaxylint [-h] [--version] [--file file]

SC2 Galaxy code linter

optional arguments:
  -h, --help   show this help message and exit
  --version    show program's version number and exit
  --file file  Filename of the galaxy script you wish to lint
```

### Obfuscator

```
usage: galaxyobf [-h] [--version] [-w] [--output FILENAME] [-i DIR [DIR ...]]
                 [-m]
                 inputfile

Galaxy code obfuscator

positional arguments:
  inputfile          Source file to obfuscate

optional arguments:
  -h, --help         show this help message and exit
  --version          show program's version number and exit
  -w, --overwrite    Overwrite original file
  --output FILENAME  Output filename
  -i DIR [DIR ...]   Directory to lookup for includes
  -m, --merge        Merge all includes into single file
```

### Deobfuscator

```
usage: galaxydeobf [-h] [--version] [-w] [--output FILENAME]
                   [--tstrings TriggerStrings] [--gstrings GameStrings]
                   inputfile

Galaxy code deobfuscator

positional arguments:
  inputfile             Source file to obfuscate

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -w, --overwrite       Overwrite original file
  --output FILENAME     Output filename
  --tstrings TriggerStrings
                        Path to TriggerStrings.txt
  --gstrings GameStrings
                        Path to GameStrings.txt
```
