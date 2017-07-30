from . import ast
from . import definitions
from . import utils
from . import parser
from . import symtable
# import json
# import pprint
# import pyaml
# pp = pprint.PrettyPrinter(indent=2, width=80)

class Linter(object):
    def __init__(self, includes=None):
        if not includes:
            includes = ["./"]
        self.parser = parser.Parser(includes, True)

    def lintFile(self, filename):
        ast = self.parser.parseFile(filename)
        ast.setParent(None)

        smTable = symtable.Symbol(ast)
        symtable.mapSymbols(ast, smTable)

        # self.printSymbols(smTable)

        # pp.pprint(smTable.pack())
        # print(pyaml.dump(smTable.pack()))

        # f = open("ast.json", mode="w")
        # f.write(ast.dump())
        # f.close()

    def printSymbols(self, smTable, indent=0):
        for key in smTable.entries:
            node = smTable.entries[key].node

            # skip natives
            if (
                isinstance(node, ast.FunctionDefinition) and
                node.isNative
            ):
                continue
            # includes
            # if node.getAncestor(ast.Include):
            #     print("\nFILE: %s" % node.name)
            #     indent += 2

            #
            print((' ' * indent) + "%s: %s" % (node.__class__.__name__, node.name), end='')
            if isinstance(node, ast.FunctionDefinition):
                print("(", end='')
                for i, x in enumerate(node.arguments):
                    print("%s" % x.name, end='')
                    if len(node.arguments) > i + 1:
                        print(", ", end='')
                print(');', end='')
                if node.isPrototype:
                    print(' [NOT DECLARED]', end='')
            print()
            self.printSymbols(smTable.entries[key], indent=indent+2)
