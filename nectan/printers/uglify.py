import random
from .. import ast
from .. import definitions


class UglifyPrinter(definitions.CodePrinter):

    LINE_LENGTH = 128

    def __init__(self):
        self.script = ""
        self.currentLine = ""

    def append(self, scr):
        if (len(self.currentLine) + len(scr)) > UglifyPrinter.LINE_LENGTH:
            self.script += self.currentLine + "\n"
            self.currentLine = ""
        if len(self.currentLine) == 0:
            self.currentLine += scr.lstrip()
        else:
            self.currentLine += scr

    def processContainer(self, nodeContainer):
        if not isinstance(nodeContainer, ast.File):
            self.append("{")
        for val in nodeContainer.childs:
            self.processNode(val)
            if isinstance(val, ast.Statement):
                self.append(";")
        if not isinstance(nodeContainer, ast.File):
            self.append("}")

    def processNode(self, node):
        if isinstance(node, ast.File) or isinstance(node, ast.Block):
            self.processContainer(node)
        elif isinstance(node, ast.Include):
            self.append("include \"%s\" " % node.filename)
        elif isinstance(node, ast.FunctionDefinition):
            if node.isNative:
                self.append("native ")
            if node.isStatic:
                self.append("static ")
            self.processNode(node.type)
            self.append(" " + node.name + "(")
            for i, x in enumerate(node.arguments):
                self.processNode(x)
                if len(node.arguments) > i + 1:
                    self.append(",")
            self.append(")")
            if node.isPrototype:
                self.append(";")
            else:
                self.processContainer(node)
        elif isinstance(node, ast.Struct):
            self.append("struct " + node.name)
            self.processContainer(node)
        elif isinstance(node, ast.VariableDeclaration):
            self.processNode(node.type)
            self.append(" " + node.name)
            if node.initialization:
                self.append("=")
                self.processNode(node.initialization)
        elif isinstance(node, ast.ArgumentDefinition):
            self.processNode(node.type)
            self.append(" " + node.name)
        elif isinstance(node, ast.RootType):
            if isinstance(node, ast.BuiltinType):
                self.append(node.name)
            elif isinstance(node, ast.UserType):
                self.processNode(node.identifier)
            if node.arguments:
                self.append("<")
                for i, x in enumerate(node.arguments):
                    self.processNode(x)
                    if len(node.arguments) > i + 1:
                        self.append(",")
                self.append(">")
        elif isinstance(node, ast.Return):
            self.append("return")
            if node.expr:
                self.append(" ")
                self.processNode(node.expr)
        elif isinstance(node, ast.InfixOp):
            if isinstance(node.getParent(), ast.BinaryOp):
                self.append("(")
            self.processNode(node.lvalue)
            self.append(node.operator)
            self.processNode(node.rvalue)
            if isinstance(node.getParent(), ast.BinaryOp):
                self.append(")")
        elif isinstance(node, ast.PrefixOp):
            self.append("(")
            self.append(node.operator)
            self.processNode(node.value)
            self.append(")")
        elif isinstance(node, ast.Identifier):
            self.append(node.value)
        elif isinstance(node, ast.NumericValue):
            if random.SystemRandom().randint(1, 100) >= 80:
                self.append(str(node.value))
            else:
                self.append("0x%X" % node.value)
        elif isinstance(node, ast.LogicalValue):
            if node.value:
                self.append("true")
            else:
                self.append("false")
        elif isinstance(node, ast.StringValue):
            escapedString = ""
            for char in node.value:
                escapedString += "\\x%X" % ord(char)
            self.append("\"%s\"" % escapedString)
        elif isinstance(node, ast.FunctionCall):
            self.processNode(node.value)
            self.append("(")
            for i, x in enumerate(node.arguments):
                self.processNode(x)
                if len(node.arguments) > i + 1:
                    self.append(",")
            self.append(")")
        elif isinstance(node, ast.ArraySubscript):
            self.processNode(node.value)
            self.append("[")
            self.processNode(node.indexExpr)
            self.append("]")
        elif isinstance(node, ast.If):
            self.append("if(")
            self.processNode(node.condition)
            self.append(")")
            # self.append("if ) { ")
            self.processNode(node.ifTrue)
            # self.append(" } ")
        elif isinstance(node, ast.File):
            self.append()
        elif not node:
            return
        else:
            print("print: unkown node - " + str(node))

    def generate(self, rootNode):
        self.processNode(rootNode)
        self.script += self.currentLine
        self.currentLine = ""
        return self.script
