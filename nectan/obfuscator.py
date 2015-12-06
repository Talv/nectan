import copy
import random
from . import ast
from . import definitions
from . import utils
from . import parser
from . import symtable
from .printers import uglify


class Obfuscator(object):

    RANDOM_OPERATIONS = ["-", "+", "^"]

    def __init__(self, options):
        self.triggerDefinitions = dict()
        self.integerValues = list()
        self.parser = parser.Parser()
        self.options = options

        if self.options.includes:
            self.parser.addIncludePath(self.options.includes)

    def generateUglyName(self, attempt = 0):
        r = "l"
        mlen = attempt % 10
        r += ''.join(
            random.SystemRandom().choice("lI1")
            # random.SystemRandom().choice("_l")
            # for _ in range(1, random.SystemRandom().randint(1, 20))
            for _ in range(mlen, mlen + 4)
        )
        return r

    def uglifySymbols(self, smTable):
        for key in set(smTable.entries.keys()):
            node = smTable.entries[key].node

            # skip natives
            if (
                isinstance(node, ast.FunctionDefinition) and
                node.isNative
            ):
                continue
            # skip includes
            if node.getAncestor(ast.Include):
                continue

            # detect trigger functions by checking for: bool fn(bool, bool)
            # this way is more reliable than hooking for input to TriggerCreate etc.
            if (
                isinstance(node, ast.FunctionDefinition) and
                (
                    isinstance(node.type, ast.BuiltinType) and
                    node.type.name == "bool"
                ) and
                (
                    len(node.arguments) == 2 and
                    (
                        isinstance(node.arguments[0].type, ast.BuiltinType) and
                        node.arguments[0].type.name == "bool"
                    ) and
                    (
                        isinstance(node.arguments[1].type, ast.BuiltinType) and
                        node.arguments[1].type.name == "bool"
                    )
                )
            ):
                self.triggerDefinitions[node.name] = node

            #
            for attempt in range(1000):
                newName = self.generateUglyName(attempt)
                if newName not in smTable.entries:
                    break
            node.name = newName
            smTable.entries[newName] = smTable.entries.pop(key)

            #
            self.uglifySymbols(smTable[newName])

    def astObfuscate(self, rootNode):
        def visitor(walker, node):
            if isinstance(node, ast.Identifier):
                node.value = node._symbol.node.name
            elif isinstance(node, ast.StringValue):
                if node.value in self.triggerDefinitions:
                    node.value = self.triggerDefinitions[node.value].name
            elif isinstance(node, ast.IntegerValue):
                self.integerValues.append(node)
            walker.walk()

        utils.NodeWalker(rootNode, visitor)

    def generateExpression(self, result, depth):
        operation = self.RANDOM_OPERATIONS[random.SystemRandom().randint(0, len(self.RANDOM_OPERATIONS) - 1)]
        if depth == 0:
            if result >= 0:
                node = ast.IntegerValue(result)
            else:
                node = ast.PrefixOp("-")
                node.value = ast.IntegerValue(abs(result))
        else:
            node = ast.BinaryOp(operation)
            if operation == "-" or operation == "+" or operation == "^":
                numA = random.SystemRandom().randint(0, 0xFFFFFFFF >> 1)
                if operation == "-":
                    numB = numA - result
                elif operation == "+":
                    numB = result - numA
                elif operation == "^":
                    numB = result ^ numA
            node.lvalue = self.generateExpression(numA, depth - 1)
            node.rvalue = self.generateExpression(numB, depth - 1)
        return node

    def obfuscate(self, filename):
        # @TODO natives list load
        # @TODO native constants embed
        # @TODO option to embed includes
        # @TODO proxy natives calls into funcref array?
        ast = self.parser.parseFile(filename)
        ast.setParent(None)

        f = open("ast.json", mode="w")
        f.write(ast.dump())
        f.close()

        smTable = symtable.Symbol(ast)
        symtable.mapSymbols(ast, smTable)

        self.uglifySymbols(smTable)
        self.astObfuscate(ast)

        for val in self.integerValues:
            replaceResult = val.getParent().replaceChild(
                val, self.generateExpression(val.value, random.SystemRandom().randint(3, 5))
            )
            if not replaceResult:
                assert(0)

        printer = uglify.UglifyPrinter()
        obfuscatedScript = printer.generate(ast)
        outFilename = None
        if self.options.outfile:
            outFilename = self.options.outfile
        elif self.options.overwrite:
            outFilename = self.options.inputfile

        if outFilename:
            outFile = open(outFilename, 'w')
            outFile.write(obfuscatedScript)
            outFile.close()
        else:
            print(obfuscatedScript)
