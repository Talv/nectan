import hashlib
import copy
import random
import re
import os
import ast as past
from . import ast, parser, symtable, utils
from .printers.pretty import PrettyPrinter


def parseTriggerStrings(filename):
    with open(filename, 'r') as f:
        content = f.read()
        stringTable = {}
        for x in re.findall(r'\s?(?:[^\/]+\/){2}([^=]+)=(.*)', content):
            stringTable[x[0]] = re.sub(r'\W', '_', x[1]).rstrip('_')
        return stringTable


def parseGameStrings(filename):
    with open(filename, 'r') as f:
        content = f.read()
        stringTable = {}
        for x in re.findall(r'\s([^=]+)=(.*)', content):
            stringTable[x[0]] = x[1]
        return stringTable


class Deobfuscator(object):
    def __init__(self, options):
        self.parser = parser.Parser(None, False)
        self.options = options
        self.triggerDefinitions = dict()
        self.prototypesTable = dict()
        f = open(os.path.join(os.path.dirname(__file__), "words.txt"))
        self.words = f.read().split("\n")
        f.close()

    def restoreSymbolNames(self, smTable, tsTable=None):
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
                lsTable = smTable.entries[node.name].entries
                lsTable["testConds"] = lsTable.pop(node.arguments[0].name)
                node.arguments[0].name = "testConds"
                lsTable["runActions"] = lsTable.pop(node.arguments[1].name)
                node.arguments[1].name = "runActions"

            # detect trigger initializers
            if (
                isinstance(node, ast.FunctionDefinition) and
                len(node.childs) >= 2 and len(node.childs) < 6 and
                (
                    isinstance(node.childs[0], ast.AssignmentOp) and
                    isinstance(node.childs[0].rvalue, ast.FunctionCall) and
                    node.childs[0].rvalue.value.value == 'TriggerCreate'
                ) and
                (
                    isinstance(node.childs[1], ast.FunctionCall) and
                    node.childs[1].value.value == 'TriggerEnable'
                )
               ):
                newName = node.childs[0].lvalue._symbol.node.name + "_Init"
                node.name = newName
                smTable.entries[newName] = smTable.entries.pop(key)

            #
            if tsTable:
                tsmatch = re.match(r'(\w+_)(\w+)', node.name)
                try:
                    hashKey = tsmatch.group(2)[:8]
                    if hashKey in tsTable:
                        newName = tsmatch.group(1) + tsTable[hashKey]
                        if (
                            len(hashKey) < len(tsmatch.group(2)) and
                            isinstance(node, ast.FunctionDefinition)
                           ):
                            newName += "_Func"
                        node.name = newName
                        if newName in smTable:
                            assert(0)
                        smTable.entries[newName] = smTable.entries.pop(key)
                        self.prototypesTable[key] = node
                except AttributeError:
                    pass

            if re.match(r'^[l1I]+$', node.name):
                prefix = ""
                if isinstance(node, ast.VariableDeclaration):
                    if isinstance(node.getParent(), ast.File):
                        prefix = "gv"
                    elif isinstance(node.getParent(), ast.Struct):
                        prefix = "sv"
                    else:
                        prefix = "lv"
                elif isinstance(node, ast.Struct):
                    prefix = "gs"
                elif isinstance(node, ast.FunctionDefinition):
                    if node.name in self.triggerDefinitions:
                        prefix = "th"
                    else:
                        prefix = "gf"
                    self.prototypesTable[node.name] = node
                elif isinstance(node, ast.Typedef):
                    prefix = "td"
                if len(prefix):
                    prefix += "_"

                failCounter = 0
                while True:
                    sha1 = abs(
                        int(hashlib.sha1(node.name.encode()).hexdigest(), 16) %
                        (10 ** 8)
                    )
                    newName = prefix + self.words[
                        (sha1 + failCounter) % len(self.words)
                    ]
                    if newName in smTable:
                        failCounter += 1
                        if failCounter > 100:
                            assert(0)
                        continue
                    else:
                        break

                smTable.entries[newName] = smTable.entries.pop(node.name)
                node.name = newName

            #
            self.restoreSymbolNames(smTable[node.name], tsTable)

    def decodeBinaryExpression(self, node):
        def evaluateNumer(nodeValue):
            if isinstance(nodeValue, ast.BinaryOp):
                newValue = self.decodeBinaryExpression(nodeValue)
            elif isinstance(nodeValue, ast.IntegerValue):
                newValue = nodeValue
            elif (
                isinstance(nodeValue, ast.PrefixOp) and
                nodeValue.operator == '-' and
                isinstance(nodeValue.value, ast.IntegerValue)
               ):
                newValue = copy.copy(nodeValue.value)
                newValue.value = -(newValue.value)
            elif (
                isinstance(nodeValue, ast.PrefixOp) and
                nodeValue.operator == '~' and
                isinstance(nodeValue.value, ast.IntegerValue)
               ):
                newValue = copy.copy(nodeValue.value)
                newValue.value = ~(newValue.value)
            else:
                return False
            return newValue

        nlValue = evaluateNumer(node.lvalue)
        nrValue = evaluateNumer(node.rvalue)

        if (
            isinstance(nlValue, ast.IntegerValue) and
            isinstance(nrValue, ast.IntegerValue) and
            node.operator in ["+", "-", "^", "|"]
        ):
            r = eval(
                "(" + str(nlValue.value) + ")" + node.operator +
                "(" + str(nrValue.value) + ")"
            )
            # print(
            #     "(" + str(nlValue.value) + ")" + node.operator +
            #     "(" + str(nrValue.value) + ") = " + str(r)
            # )
            return ast.IntegerValue(r)
        else:
            return None

    def astDeobfuscate(self, rootNode):
        def visitor(walker, node):
            if isinstance(node, ast.Identifier) and node._symbol:
                node.value = node._symbol.node.name
            if isinstance(node, ast.FunctionDefinition) and node.isPrototype:
                if node.name in self.prototypesTable:
                    node.arguments = self.prototypesTable[node.name].arguments
                    node.name = self.prototypesTable[node.name].name
            elif isinstance(node, ast.StringValue):
                node.value = bytes(re.sub(r'\\x0([0-9A-Fa-f]{2})', '\\x\\g<1>', node.value), "utf-8").decode("unicode_escape")
                if (
                    re.match(r'^[l1I]+$', node.value) and
                    node.value in self.triggerDefinitions
                   ):
                    node.value = self.triggerDefinitions[node.value].name
            elif isinstance(node, ast.BinaryOp) and node.operator in ["+", "-", "^", "|"]:
                decoded = self.decodeBinaryExpression(node)
                if decoded:
                    node.getParent().replaceChild(node, decoded)
                    return
            walker.walk()

        utils.NodeWalker(rootNode, visitor)

    def embedStringExternals(self, rootNode, gameStrings):
        def visitor(walker, node):
            if (
                isinstance(node, ast.FunctionCall) and
                node.value.value == "StringExternal" and
                isinstance(node.arguments[0], ast.StringValue) and
                re.match(r'^Param\/Value\/', node.arguments[0].value)
               ):
                node.value.value = "StringToText"
                node.arguments[0].value = gameStrings[node.arguments[0].value]
            walker.walk()

        utils.NodeWalker(rootNode, visitor)

    def deobfuscate(self, filename):
        ast = self.parser.parseFile(filename)
        ast.setParent(None)

        smTable = symtable.Symbol(ast)
        symtable.mapSymbols(ast, smTable)

        tsTable = None
        if self.options.tstrings:
            tsTable = parseTriggerStrings(self.options.tstrings)

        gsTable = None
        if self.options.gstrings:
            gsTable = parseGameStrings(self.options.gstrings)

        self.restoreSymbolNames(smTable, tsTable)
        self.astDeobfuscate(ast)

        if gsTable:
            self.embedStringExternals(ast, gsTable)

        pnt = PrettyPrinter()
        prettyScript = pnt.generate(ast)

        outfname = None
        if self.options.outfile:
            outfname = self.options.outfile

        if outfname:
            outfile = open(outfname, 'w')
            outfile.write(prettyScript)
            outfile.close()
        else:
            print(prettyScript)
