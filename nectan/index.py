import logging
import copy
from . import ast
from . import utils
from . import parser
from . import definitions
from .printers.pretty import PrettyPrinter

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
pp = PrettyPrinter()

def getSymbolName(node: ast.SymbolDefinition):
    return node.name


def prepareCompletion(node: ast.SymbolDefinition):
    detail = None
    if hasattr(node, 'type'):
        detail = pp.generate(node.type)

    kind = node.__class__.__name__
    if isinstance(node, ast.VariableDeclaration) and 'const' in node.modifiers:
        kind = 'Constant'

    return {
        'name': node.name,
        'kind': kind,
        'location': node._coords.serialize(),
        'detail': detail,
    }


class Document(object):
    def __init__(self, uri):
        self.uri = uri
        self.tree = None
        self.definitions = {}

    def getSymbols(self):
        pass


class DefinitionCollector(utils.NodeWalkerEx):
    def __init__(self, idf: Document):
        self.idf = idf
        self.scopes = []
        super().__init__(self.idf.tree)

    def visitor(self, node: ast.Node):
        if not isinstance(node, ast.SymbolDefinition):
            # don't dive into functions past variables declarations
            if len(self.scopes) and isinstance(node.getParent(), ast.FunctionDefinition):
                return
            self.walk()
        else:
            symname = getSymbolName(node)
            self.scopes.append(symname)

            self.idf.definitions['::'.join(self.scopes)] = node
            self.walk()
            self.scopes.pop()


class ReferenceMapper(utils.NodeWalkerEx):
    # def __init__(self, idf: Document, allDefinitions):
        # self.idf = idf
    def __init__(self, contNode: ast.Container, allDefinitions):
        self.scopes = []
        self.selectionScopes = []
        self.allDefinitions = allDefinitions
        self.reports = []
        self.contNode = contNode
        super().__init__(contNode)

    def mapIdentifier(self, identifier: ast.Identifier):
        sym = None
        parentScope = None

        if len(self.selectionScopes) and len(self.selectionScopes[0]):
            # parentScope = ""
            for x in reversed(self.selectionScopes[0]):
                parentScope = x
                # print(x)
                # print(x.name)

        # local
        if not sym:
            if not parentScope:
                fullname = '::'.join(self.scopes + [identifier.value])
            else:
                fullname = parentScope.name + '::' + identifier.value
            if fullname in self.allDefinitions:
                sym = self.allDefinitions[fullname]
        
        # global
        if not sym:
            fullname = identifier.value
            if fullname in self.allDefinitions:
                sym = self.allDefinitions[fullname]

        if sym:
            identifier._symbol = sym
        else:
            # print(identifier.pack())
            # print(identifier.getParent(ast.File).name)
            # if identifier.getParent(ast.FunctionDefinition):
            #     print(identifier.getParent(ast.FunctionDefinition).name)
            # print(self.selectionScopes)
            # print("referenced underclared symbol '%s'" % identifier.value)
            self.reports.append(definitions.SemanticError(identifier, "referenced underclared symbol '%s'" % identifier.value))

    def seekDeepIdentifier(self, node):
        if isinstance(node, ast.Identifier):
            return node
        elif isinstance(node, ast.ArraySubscript):
            return self.seekDeepIdentifier(node.value)
        elif isinstance(node, ast.SelectionOp):
            return self.seekDeepIdentifier(node.rvalue)
        else:
            return None

    def mapNodeContainerIfNeeded(self, node):
        pcont = node.getParent(ast.File)
        if pcont != self.contNode and not pcont.indirectlyMapped:
            pcont.indirectlyMapped = True
            ReferenceMapper(pcont, self.allDefinitions)

    def visitor(self, node: ast.Node):
        if isinstance(node, ast.Identifier):
            self.mapIdentifier(node)
            self.walk()
        elif isinstance(node, ast.SelectionOp):
            selectionEntered = False
            if not isinstance(node.getParent(), (ast.SelectionOp)):
                self.selectionScopes.insert(0, list())
                selectionEntered = True
            self.walk()
            if selectionEntered:
                self.selectionScopes.pop(0)
        elif isinstance(node, ast.SymbolDefinition):
            self.scopes.append(getSymbolName(node))
            self.walk()
            self.scopes.pop()
        else:
            self.walk()

        if isinstance(node.getParent(), ast.SelectionOp) and not isinstance(node, ast.SelectionOp):
            sym = None
            if isinstance(node, ast.Identifier):
                sym = node._symbol
            else:
                try:
                    sym = self.seekDeepIdentifier(node)._symbol
                except AttributeError:
                    pass
            if sym:
                if isinstance(sym.type, ast.UserType):
                    self.mapNodeContainerIfNeeded(sym.type.identifier)
                    symType = sym.type.identifier._symbol
                elif isinstance(sym.type, ast.BuiltinType) and sym.type.name in definitions.Instructions.SPECIAL_TYPES:
                    self.mapNodeContainerIfNeeded(sym.type.arguments[0].identifier)
                    symType = sym.type.arguments[0].identifier._symbol
                else:
                    symType = sym
                
                try:
                    self.mapNodeContainerIfNeeded(symType)
                except AttributeError:
                    print("AE[1]")
                    print(node.dump())
                    print(sym.dump())
                    # print(symType.dump())

                self.selectionScopes[0].insert(0, symType)


class Index(object):
    def __init__(self, workspace="./"):
        self.documents = {}
        self.pars = parser.Parser("./", False)

    def addFile(self, filename):
        try:
            tree = self.pars.parseFile(filename)
            tree.setParent(None)

            self.documents[filename] = Document(filename)
            self.reindex(self.documents[filename], tree)
        except definitions.ParseError as e:
            logging.debug("couldn't parse %s, err: %s, line: %d, pos: %d", filename, e.msg, e.line, e.pos)

    def reindex(self, idf: Document, tree):
        logging.debug("indexing %s", idf.uri)
        idf.tree = tree
        idf.definitions = {}
        DefinitionCollector(idf)

    # def mapReferences(self, idf: Document):
    #     ReferenceMapper(idf, self.getDefinitions())

    def lint(self, filename):
        reports = []
        
        try:
            tree = self.pars.parseFile(filename)
            tree.setParent(None)
            if filename in self.documents:
                self.reindex(self.documents[filename], tree)
        except definitions.ParseError as e:
            reports.append(e.serialize())

        for x in ReferenceMapper(self.documents[filename].tree, self.getDefinitions()).reports:
            reports.append(x.serialize())
        
        return reports

    def getDefinitions(self, filename=None):
        defs = {}
        if filename:
            defs.update(self.documents[filename].definitions.copy())
        else:
            for uri in self.documents:
                defs.update(self.documents[uri].definitions.copy())
        return defs

    def getCompletions(self, filename, line, pos):
        completions = []
        symNames = {}

        for uri in self.documents:
            for name in self.documents[uri].definitions:
                sym = self.documents[uri].definitions[name]

                if uri != filename and (
                    not isinstance(sym.getParent(), ast.File) and
                    not isinstance(sym.getParent(), ast.Struct)
                ):
                    continue
                if isinstance(sym, ast.FunctionDefinition) and sym.isStatic and uri != filename:
                    continue
                if sym.name in symNames:
                    continue

                symNames[sym.name] = True
                completions.append(prepareCompletion(sym))

        return completions

    def getSignatures(self, symbolName):
        signatures = []

        defs = self.getDefinitions()
        if symbolName in defs:
            definition = defs[symbolName]
            if isinstance(definition, ast.FunctionDefinition):
                tmpDef = copy.copy(definition)
                tmpDef.childs = []
                tmpDef.isPrototype = True
                sign = {
                    'label': pp.generate(tmpDef),
                    'docs': "",
                    'parameters': [],
                }
                for arg in definition.arguments:
                    sign['parameters'].append({
                        'label': pp.generate(arg),
                        'docs': "",
                    })
                
                signatures.append(sign)

        return signatures

    def provideDefinition(self, symbolName):
        defs = self.getDefinitions()
        if symbolName in defs:
            return defs[symbolName].serialize()
        return None
