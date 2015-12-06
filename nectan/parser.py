import traceback
import copy
import string
import re
import copy
import os

from . import definitions
from . import ast
from . import lexer


class OperationHolder(object):

    def __init__(self, descriptor):
        # should be None or ast.Operation
        self.descriptor = descriptor

    def getPrecedenceValue(self):
        opType = self.descriptor.__class__.__bases__[0].__name__
        if opType == "Operation":
            opType = self.descriptor.__class__.__name__
        for i, row in enumerate(definitions.Operations.PRECEDENCE):
            if not opType in row:
                continue
            if self.descriptor.operator in row[opType]:
                return i
        return None

    def getOperator(self):
        return self.descriptor.operator


class Parser(object):

    def __init__(self, incPath = "./", parseIncludes = True):
        self.parseIncludes = parseIncludes
        self.incPath = list()
        self.prevToken = None
        if isinstance(incPath, list):
            self.incPath.extend(incPath)
        elif isinstance(incPath, str):
            self.incPath.append(incPath)

    def dropToken(self):
        self.prevToken = self.tokens.pop(0)
        return copy.copy(self.prevToken)

    def addIncludePath(self, path):
        if path[-1] != "/":
            path = path + "/"
        self.incPath.append(path)

    def readfile(self, filename):
        # absoulte path
        if filename[0] != "/":
            for path in self.incPath:
                fullFilename = path + filename
                if not os.path.isfile(fullFilename):
                    filename = fullFilename
        try:
            f = open(filename)
            content = f.read()
            f.close()
            return content
        except FileNotFoundError:
            raise Exception("Required file '%s' hasn't been found. Include paths %s" % (filename, self.incPath))

    def parseError(self, msg):
        try:
            token = self.tokens[0]
        except IndexError:
            token = self.prevToken
        return definitions.ParseError(self.rootNode.name, token.line, token.pos, msg)

    def raiseError(self, msg):
        raise self.parseError(msg)

    def currentCoords(self):
        if not len(self.tokens):
            return None
        return self.tokens[0].coords()

    def createNode(self, node, coords = None):
        if not isinstance(node, ast.Node):
            assert(0)
        if not coords:
            node._cords = self.currentCoords()
        return node

    def isFunction(self):
        index = 0
        while self.tokens[index] in definitions.Instructions.FUNC_MODS:
            index += 1 # mods
        if (self.tokens[index] not in definitions.Instructions.TYPES and
            self.isIllegal(self.tokens[index])
        ):
            return False
        index += 1 # type

        if self.isIllegal(self.tokens[index]):
            return False
        index += 1 # name

        if len(self.tokens) > index and self.tokens[index] == "(":
            return True
        return False

    def isDeclaration(self):
        index = 0

        # modifiers
        while self.tokens[index] in definitions.Instructions.VAR_MODS:
            index += 1

        # type name
        if self.isIllegal(self.tokens[index]):
            return False
        index += 1

        # array?
        while self.tokens[index] == "[":
            while self.tokens[index] != "]":
                index += 1
            index += 1

        # type args?
        while self.tokens[index] == "<":
            while self.tokens[index] != ">":
                index += 1
            index += 1

        # var name
        if self.isIllegal(self.tokens[index]):
            return False
        index += 1

        if self.tokens[index] != "," and self.tokens[index] != ";" and self.tokens[index] != "=":
            return False
        return True

    def isKeyword(self, name):
        if name in definitions.Instructions.KEYWORDS:
            return True
        else:
            return False

    def isIllegal(self, name):
        if not re.match("[a-zA-Z0-9_]+", name):
            return True
        else:
            return False

    def checkIdentifier(self, name):
        if self.isKeyword(name):
            self.raiseError("Expected identifier, found '%s' (keyword)" % name)
        elif self.isIllegal(name):
            self.raiseError("Expected identifier, found '%s' (illegal characters)" % name)
        else:
            return True

    def parseIdentifier(self):
        if self.tokens[0] in definitions.Instructions.KEYWORDS:
            self.raiseError("Identifier '%s' cannot be a keyword '%s'" %
                (self.tokens[0], self.tokens[0]) )
        node = self.createNode( ast.Identifier() )
        node.value = self.dropToken()
        return node

    def parseValue(self):
        node = None

        if self.tokens[0] in string.punctuation:
            self.raiseError("Expected value, found '%s' (unrecognized operator?)" % self.tokens[0])

        if self.tokens[0][0] in string.digits: # 0123456789 0b01 0xAA
            allowedChars = list( x for x in (string.digits + string.hexdigits + ".x") )
            if False in (c in allowedChars for c in self.tokens[0]):
                self.raiseError("Expected constant number, found illegal characters")
            if "." in self.tokens[0]:
                node = self.createNode(ast.FixedValue())
                node.value = float(self.dropToken())
            else:
                node = self.createNode(ast.IntegerValue())
                if self.tokens[0].startswith("0b"):
                    base = 2
                elif self.tokens[0].startswith("0x"):
                    base = 16
                else:
                    base = 10
                node.value = int(self.dropToken(), base = base)
        elif self.tokens[0][0] == '"':
            node = self.createNode(ast.StringValue(
                self.dropToken()[1:-1]
            ))
            # @TODO decode string (unescape)
        elif self.tokens[0] in definitions.Instructions.BOOL:
            if self.tokens[0] == "true":
                node = self.createNode(ast.LogicalValue(True))
            elif self.tokens[0] == "false":
                node = self.createNode(ast.LogicalValue(False))
            else:
                self.raiseError("??")
            self.dropToken()
        elif self.tokens[0] in definitions.Instructions.NULL:
            node = self.createNode(ast.NullValue())
            self.dropToken()
        else:
            node = self.parseIdentifier()

        return node

    def buildExpressionTree(self, expressions):
        def getOpsByPrecedence(exprList):
            # keysOp = list()
            operations = list()
            for i, x in enumerate(exprList):
                if isinstance(x, OperationHolder):
                    operations.append(x)
            operations = sorted(operations, key = lambda operation: operation.getPrecedenceValue())
            return operations

        while len(expressions) > 1:
            for op in getOpsByPrecedence(expressions):
                opIndex = expressions.index(op)
                if isinstance(op.descriptor, ast.InfixOp):
                    try:
                        if not isinstance(expressions[opIndex - 1], (ast.Value, ast.Operation)):
                            self.raiseError("lvalue not found or not valid")
                        if not isinstance(expressions[opIndex + 1], (ast.Value, ast.Operation)):
                            self.raiseError("rvalue not found or not valid")
                    except IndexError:
                        self.raiseError("lvalue or rvalue of the expression has not been found")
                    if op.descriptor.operator in definitions.Operations.TERNARY:
                        self.raiseError("TODO: ternary")
                    else:
                        if op.descriptor.operator in definitions.Operations.RESOLUTION:
                            value = self.createNode( ast.ScopeResolutionOp(op.descriptor.operator), op.descriptor._coords )
                        elif op.descriptor.operator in definitions.Operations.SELECTION:
                            value = self.createNode( ast.SelectionOp(op.descriptor.operator), op.descriptor._coords )
                        elif op.descriptor.operator in definitions.Operations.ASSIGNMENT:
                            value = self.createNode( ast.AssignmentOp(op.descriptor.operator), op.descriptor._coords )
                        else:
                            value = self.createNode( ast.BinaryOp(op.descriptor.operator), op.descriptor._coords )
                        value.lvalue = expressions[opIndex - 1]
                        value.rvalue = expressions[opIndex + 1]
                    opIndex -= 1
                    expressions.pop(opIndex)
                    expressions.pop(opIndex)
                    expressions.pop(opIndex)
                    expressions.insert(opIndex, value)
                elif isinstance(op.descriptor, ast.PrefixOp):
                    try:
                        if not isinstance(expressions[opIndex + 1], (ast.Value, ast.Operation)):
                            self.raiseError("rvalue not valid")
                    except IndexError:
                        self.raiseError("rvalue not found")
                    if op.descriptor.operator in definitions.Operations.TYPECAST:
                        self.raiseError("TODO typecast")
                    else:
                        value = op.descriptor
                        value.value = expressions[opIndex + 1]
                    expressions.pop(opIndex)
                    expressions.pop(opIndex)
                    expressions.insert(opIndex, value)
                elif isinstance(op.descriptor, ast.PostfixOp):
                    try:
                        if not isinstance(expressions[opIndex - 1], (ast.Value, ast.Operation)):
                            self.raiseError("lvalue not valid")
                    except IndexError:
                        self.raiseError("lvalue not found")
                    value = op.descriptor
                    value.value = expressions[opIndex - 1]
                    #
                    opIndex -= 1
                    expressions.pop(opIndex)
                    expressions.pop(opIndex)
                    expressions.insert(opIndex, value)
                else:
                    self.raiseError("Unknown operation descriptor")
            # break
        # print(expressions[0].p())
        return expressions[0]

    def parseExpression(self, endDelimeter):
        def exprListContainsOnlyOp(expressions, operator):
            for x in expressions:
                if isinstance(x, str) and x != operator:
                    return False
            return True
        expressions = list()

        # list nodes
        while len(self.tokens):
            # nested = False
            if self.tokens[0] in endDelimeter:
                break

            # nested expression
            if self.tokens[0] == "(":
                # nested = True
                self.dropToken()
                expressions.append( self.parseExpression([")"]) )
                if self.tokens[0] != ")":
                    self.raiseError("Expected end of expression ')'")
                self.dropToken()
                # check if it's cast
                # if isinstance(expressions[-1], ast.Identifier):
                #     self.parseValue()
                #     self.raiseError("cast?")
            else:
                node = None
                # prefix operator
                if self.tokens[0] in definitions.Operations.PREFIX:
                    node = self.createNode( ast.PrefixOp(self.dropToken() ) )
                    node = OperationHolder( node )
                    expressions.append( node )

                if self.tokens[0] == "(":
                    self.dropToken()
                    expressions.append(self.parseExpression([")"]))
                    if self.tokens[0] != ")":
                        self.raiseError("Expected end of expression ')'")
                    self.dropToken()
                # value
                else:
                    value = self.parseValue()
                    expressions.append( value )

                node = None
                # postfix operator
                if self.tokens[0] in definitions.Operations.POSTFIX:
                    node = self.createNode( ast.PostfixOp(self.dropToken()) )
                    expressions.append(OperationHolder(node))
                else:
                    while self.tokens[0] in ["(", "["]:
                        # function call
                        if self.tokens[0] == "(":
                            self.dropToken()
                            node = self.createNode( ast.FunctionCall() )

                            while self.tokens[0] != ")":
                                node.arguments.append( self.parseExpression([",", ")"]) )
                                if self.tokens[0] == ",":
                                    self.dropToken()
                                elif self.tokens[0] == ")":
                                    break
                                else:
                                    self.raiseError("")
                            self.dropToken()
                        # array subscript
                        elif self.tokens[0] == "[":
                            self.dropToken()
                            node = self.createNode(ast.ArraySubscript())
                            node.indexExpr = self.parseExpression( ["]"] )
                            if self.tokens[0] != "]":
                                self.raiseError("array subscript should end with ']'")
                            self.dropToken()
                        expressions.append(OperationHolder(node))

            # infix operator inbetween
            if self.tokens[0] in definitions.Operations.INFIX:
                expressions.append(
                    OperationHolder( self.createNode(ast.InfixOp(self.dropToken())) )
                )
            elif self.tokens[0] in endDelimeter:
                break
            # elif nested and isinstance(expressions[-1], Identifier):
            #     self.raiseError("TODO: cast")
            else:
                self.raiseError("Couldn't evaluate expression - unexpected '%s'" % self.tokens[0])

        # build a tree
        if len(expressions):
            return self.buildExpressionTree(expressions)
        else:
            return None

    def parseType(self):
        # TODO check identifier
        if not re.match("[a-zA-Z0-9_]+", self.tokens[0]):
            self.raiseError("Not allowed symbol in the typename '%s'" % self.tokens[0])

        if self.tokens[0] in definitions.Instructions.TYPES:
            node = self.createNode( ast.BuiltinType() )
            node.name = self.dropToken()
        else:
            node = self.createNode( ast.UserType() )
            node.identifier = self.parseIdentifier()

        # args
        if (self.tokens[0] == "<" and
            node.name in definitions.Instructions.SPECIAL_TYPES
        ):
            self.dropToken()
            # while self.tokens[0] != ">":
            while True:
                node.arguments.append(self.parseType())
                if self.tokens[0] == ",":
                    self.dropToken()
                    continue
                elif self.tokens[0] == ">":
                    self.dropToken()
                    break
                else:
                    self.raiseError("Excepted '>' or ','. Found '%s'" % self.tokens[0])

        # array
        while self.tokens[0] == "[":
            self.dropToken()
            node.dimensions.append(self.parseExpression(["]"]))
            if self.dropToken() != "]":
                self.raiseError("Array definition must end with ']'")

        return node

    def parseDeclaration(self, stripSemicolon = False, limit = -1):
        declarations = list()
        modifiers = list()

        while self.tokens[0] in definitions.Instructions.VAR_MODS:
            modifiers.append(self.dropToken())

        # type
        nodeType = self.parseType()

        # list of declared variables
        i = 0
        while len(self.tokens):
            if limit != -1 and i > limit:
                self.raiseError("Only %d variable declaration possible at once" % (limit))
            item = self.createNode( ast.VariableDeclaration() )
            item.modifiers = copy.copy(modifiers)
            item.type = nodeType

            # name
            # if self.tokens[0] in definitions.Instructions.KEYWORDS:
            #     self.raiseError("Variable name cannot contain keyword")
            self.checkIdentifier(self.tokens[0])
            item.name = self.dropToken()

            # value
            if self.tokens[0] == "=":
                self.dropToken()
                item.initialization = self.parseExpression([",", ";"])

            # append
            declarations.append(item)

            if self.tokens[0] == ";":
                if stripSemicolon:
                    self.dropToken()
                break
            elif self.tokens[0] == ",":
                self.dropToken()
                i += 1
                continue
            else:
                self.raiseError("Variable declaration must end with ';' instead found '%s'" % self.tokens[0])

        if limit == 1:
            return declarations[0]
        return declarations

    def parseIf(self):
        node = self.createNode( ast.If() )

        if self.tokens[0] != "if":
            self.raiseError("Expected 'if' keyword")
        self.dropToken()

        if self.tokens[0] != "(":
            self.raiseError("Expected '('")
        self.dropToken()

        node.condition = self.parseExpression([")"])

        if self.tokens[0] != ")":
            self.raiseError("Expected ')'")
        self.dropToken()

        node.ifTrue = self.parseBlockOrStatement()
        if self.tokens[0] == "else":
            self.dropToken()
            node.ifFalse = self.parseBlockOrStatement()
        return node

    def parseWhile(self):
        node = self.createNode(ast.While())

        self.dropToken()

        if self.tokens[0] != "(":
            self.raiseError("Expected '('")
        self.dropToken()

        node.condition = self.parseExpression([")"])
        if self.tokens[0] != ")":
            self.raiseError("Expected ')'")
        self.dropToken()

        self.parseContainer(node)

        return node

    def parseFor(self):
        node = self.createNode(ast.For())

        self.dropToken()

        if self.tokens[0] != "(":
            self.raiseError("Expected '('")
        self.dropToken()

        node.init = self.parseExpression([";"])
        if self.tokens[0] != ";":
            self.raiseError("Expected ';' after init statement")
        self.dropToken()

        node.condition = self.parseExpression([";"])
        if self.tokens[0] != ";":
            self.raiseError("Expected ';' after condition statement")
        self.dropToken()

        node.next = self.parseExpression([")"])
        if self.tokens[0] != ")":
            self.raiseError("Expected ')' after next statement")
        self.dropToken()

        self.parseContainer(node)

        return node

    def parseArgument(self):
        arg = self.createNode( ast.ArgumentDefinition() )

        while self.tokens[0] in definitions.Instructions.VAR_MODS:
            arg.modifiers.append(self.dropToken())

        arg.type = self.parseType()
        if self.tokens[0] == "&":
            arg.isReference = True
            self.dropToken()
        self.checkIdentifier(self.tokens[0])
        arg.name = self.dropToken()

        return arg

    def parseFunction(self):
        node = self.createNode( ast.FunctionDefinition() )

        while self.tokens[0] in definitions.Instructions.FUNC_MODS:
            if self.tokens[0] == "native":
                node.isNative = True
            elif self.tokens[0] == "static":
                node.isStatic = True
            elif self.tokens[0] == "private":
                node.isPrivate = True
            elif self.tokens[0] == "public":
                node.isPrivate = False
            else:
                self.raiseError("unhandled modifier \"%s\"" % self.tokens[0])
            self.dropToken()
            # node.modifiers.append(self.dropToken())
        node.type = self.parseType()
        self.checkIdentifier(self.tokens[0])
        node.name = self.dropToken()
        self.dropToken()
        while True:
            if self.tokens[0] == ")":
                self.dropToken()
                break
            arg = self.parseArgument()
            node.arguments.append(arg)
            if self.tokens[0] == ")":
                continue
            elif self.tokens[0] == ",":
                self.dropToken()
                continue
            else:
                self.raiseError("Expected end of argument definition, found %s" % self.tokens[0])

        # body
        if self.tokens[0] == "{":
            self.parseContainer(node)
        elif self.tokens[0] == ";":
            self.dropToken()
            node.isPrototype = True
        return node

    def parseClassStruct(self):
        node = None
        if self.tokens[0] == "class":
            node = self.createNode( ast.Class() )
        if self.tokens[0] == "struct":
            node = self.createNode( ast.Struct() )
        else:
            assert(0)
        self.dropToken()

        self.checkIdentifier(self.tokens[0])
        node.name = self.dropToken()

        self.parseContainer(node)

        if self.tokens[0] != ";":
            self.raiseError("Struct declaration must end with ';'")
        self.dropToken()

        return node

    def parseContainer(self, block = None):
        # statements = list()
        if not block:
            block = self.createNode( ast.Block() )
        if self.tokens[0] != "{":
            self.raiseError("Block must start with '{'")
        self.dropToken()
        while len(self.tokens) and self.tokens[0] != "}":
            result = self.parseStatement()
            if isinstance(result, list):
                block.childs += result
            elif result:
                block.childs.append(result)
        try:
            if self.tokens[0] != "}":
                self.raiseError("Block must end with '}', instead found %s", self.tokens[0])
        except IndexError:
            self.raiseError("Block must end with '}'")
        self.dropToken()
        return block
        # return statements

    def parseInclude(self):
        self.dropToken()
        if self.tokens[0][0] != "\"" or self.tokens[0][-1] != "\"":
            self.raiseError("filename must be wrapped with \"")
        node = self.createNode(ast.Include(self.dropToken()[1:-1]))

        if self.parseIncludes:
            ps = Parser()
            ps.parseFile(node.filename + ".galaxy", node)

        return node

    def parseReturn(self):
        self.dropToken()
        node = self.createNode(ast.Return())
        if self.tokens[0] != ";":
            node.expr = self.parseExpression([";"])
        return node

    def parseStatement(self):
        node = None
        checkSemicolon = False

        while self.tokens[0][0:2] == "//":
            self.dropToken()
            return None

        if self.tokens[0] == "include":
            node = self.parseInclude()
        # elif self.tokens[0] == "namespace":
        #     node = self.parseNamespace()
        # elif self.tokens[0] == "template":
        #     node = self.parseTemplate()
        # elif self.tokens[0] == "class":
        #     node = self.parseClassStruct()
        elif self.tokens[0] == "struct":
            node = self.parseClassStruct()
        # elif self.tokens[0] == "enrich":
        #     node = self.parseEnrichment()
        # elif self.tokens[0] == "property":
        #     node = self.parseProperty()
        elif self.tokens[0] == "return":
            node = self.parseReturn()
            checkSemicolon = True
        elif self.tokens[0] == "continue":
            self.dropToken()
            node = self.createNode(ast.Continue())
            checkSemicolon = True
        elif self.tokens[0] == "break":
            self.dropToken()
            node = self.createNode(ast.Break())
            checkSemicolon = True
        elif self.tokens[0] == "if":
            node = self.parseIf()
        elif self.tokens[0] == "for":
            node = self.parseFor()
        elif self.tokens[0] == "while":
            node = self.parseWhile()
        elif self.isFunction():
            node = self.parseFunction()
        elif self.isDeclaration():
            node = self.parseDeclaration()
            checkSemicolon = True
        else:
            node = self.parseExpression([";"])
            checkSemicolon = True
            # self.raiseError("TODO: statements")

        if checkSemicolon:
            if self.tokens[0] != ";":
                self.raiseError("Expected ';' at end of the statement")
            self.dropToken()
        return node

    def parseBlockOrStatement(self):
        if self.tokens[0] == "{":
            return self.parseContainer()
        else:
            return self.parseStatement()

    def parseFile(self, filename, rootNode = None):
        self.tokens = list(lexer.tokenize(
            self.readfile(filename)
        ))

        if not rootNode:
            self.rootNode = self.createNode(ast.File(filename))
        else:
            self.rootNode = rootNode

        try:
            try:
                while len(self.tokens):
                    result = self.parseStatement()
                    if isinstance(result, ast.Node):
                        self.rootNode.childs.append( result )
                    elif isinstance(result, list):
                        self.rootNode.childs += result
                    # else:
                    #     self.raiseError("?")
            except IndexError as e:
                # print(traceback.format_exc())
                raise self.parseError(str(e)) from e
        except definitions.ParseError as e:
            pass

        return self.rootNode
