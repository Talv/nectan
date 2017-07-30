from . import ast
from . import definitions
from . import utils


class Symbol(object):

    def __init__(self, node=None):
        self.entries = dict()
        self.node = node

    def __iter__(self):
        return self.entries.iterkeys()

    def __contains__(self, key):
        return key in self.entries

    def __getitem__(self, key):
        return self.entries[key]

    def append(self, name, node):
        if (
            name not in self.entries or
            (
                isinstance(self.entries[name].node, ast.FunctionDefinition) or
                isinstance(self.entries[name].node, ast.VariableDeclaration)
            )
        ):
            if name in self.entries and isinstance(self.entries[name].node, ast.FunctionDefinition) and not self.entries[name].node.isPrototype:
                pass
            else:
                self.entries[name] = node
        else:
            # print(self.entries[name].node.pack())
            print(self.entries[name].node.getParent(ast.File).name)
            print("")
            # print(node.node.pack())
            print(node.node.getParent(ast.File).name)
            print("")
            raise definitions.SemanticError(
                node, "symbol redeclared '%s'" % name)

    def pack(self):
        r = {}
        for x in self.entries:
            r[x] = self.entries[x].pack()
        return {
            'node': self.node,
            'entries': r
        }


def mapSymbols(rootNode, rootSmTable):
    smTables = list()
    scopeSelectors = list()

    def enterScope(sym):
        smTables.insert(0, sym)

    def leaveScope():
        smTables.pop(0)

    def register(node):
        sym = Symbol(node)
        smTables[0].append(node.name, sym)
        return sym

    def retrieveSymbol(name):
        # if len(selectedScope):
        #     if name in selectedScope[0]:
        #         return selectedScope[0][name]
        if len(scopeSelectors) and len(scopeSelectors[0]):
            if name in scopeSelectors[0][0]:
                return scopeSelectors[0][0][name]
        else:
            for x in smTables:
                if name in x:
                    return x[name]
        return False

    def mapIdentifier(identifier):
        symbol = retrieveSymbol(identifier.value)
        if not symbol:
            # return None
            # @TODO warning?
            print(identifier.pack())
            print(identifier.getParent(ast.File).name)
            if identifier.getParent(ast.FunctionDefinition):
                print(identifier.getParent(ast.FunctionDefinition).name)
            print("referenced underclared symbol '%s'" % identifier.value)
            # raise definitions.SemanticError(identifier, "referenced underclared symbol '%s'" % identifier.value)
        identifier._symbol = symbol
        return symbol

    def seekDeepIdentifier(node):
        if isinstance(node, ast.Identifier):
            return node
        elif isinstance(node, ast.ArraySubscript):
            return seekDeepIdentifier(node.value)
        elif isinstance(node, ast.SelectionOp):
            return seekDeepIdentifier(node.rvalue)
        else:
            return None

    def visitorDefMapper(walker, node):
        if not isinstance(node, ast.File):
            if isinstance(node, ast.SymbolDefinition):
                sym = register(node)
            # if isinstance(node, ast.Container):
                enterScope(sym)
                walker.walk()
                leaveScope()
        walker.walk()

    def visitorRefMapper(walker, node):
        if not isinstance(node, ast.File):
            # if isinstance(node, ast.Container):
            if isinstance(node, ast.SymbolDefinition):
                enterScope(smTables[0][node.name])
                walker.walk()
                leaveScope()
            elif isinstance(node, ast.SelectionOp):
                # print(node.lvalue)
                selectionEntered = False
                if not isinstance(node.getParent(), (ast.SelectionOp)):
                    scopeSelectors.insert(0, list())
                    selectionEntered = True
                walker.walk()
                if selectionEntered:
                    scopeSelectors.pop(0)
                # awaitingSelectorSym.insert(0, True)
                # walker.walk(node.lvalue)
                # sym = awaitingSelectorSym.pop(0)
                # if isinstance(sym.node.type, ast.UserType):
                #     selectedScope.insert(0, sym.node.type.identifier._symbol)
                #     walker.walk(node.rvalue)
                #     selectedScope.pop(0)
                # else:
                #     # TODO ??
                #     walker.walk(node.rvalue)
                # sym = mapIdentifier(node.lvalue)
                # if isinstance(sym.node.type, ast.UserType):
                #     selectedScope.insert(0, sym.node.type.identifier._symbol)
                #     walker.walk()
                #     selectedScope.pop(0)
                # else:
                #     walker.walk()
            elif isinstance(node, ast.Identifier):
                # if not node._symbol:
                #     mapIdentifier(node)
                sym = mapIdentifier(node)
                # if len(awaitingSelectorSym):
                #     awaitingSelectorSym[0] = sym
                walker.walk()
            else:
                walker.walk()

            #
            if isinstance(node.getParent(), ast.SelectionOp) and not isinstance(node, ast.SelectionOp):
                sym = None
                if isinstance(node, ast.Identifier):
                    sym = node._symbol
                # elif isinstance(node, ast.ArraySubscript):
                #     sym = node.value._symbol
                #     if isinstance(node.value, ast.ArraySubscript):
                #         avalue = node.value._s
                #     sym = node.value._symbol
                else:
                    try:
                        sym = seekDeepIdentifier(node)._symbol
                    except AttributeError:
                        pass
                    # assert(0)
                if sym:
                    if isinstance(sym.node.type, ast.UserType):
                        sym = sym.node.type.identifier._symbol
                    elif isinstance(sym.node.type, ast.BuiltinType) and sym.node.type.name in definitions.Instructions.SPECIAL_TYPES:
                        sym = sym.node.type.arguments[0].identifier._symbol
                    scopeSelectors[0].insert(0, sym)
        else:
            walker.walk()

    smTables.append(rootSmTable)
    utils.NodeWalker(rootNode, visitorDefMapper)
    utils.NodeWalker(rootNode, visitorRefMapper)
