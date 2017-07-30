import random
from .. import ast
from .. import definitions


class PrettyPrinter(definitions.CodePrinter):

    def __init__(self):
        self.script = ""
        self.indent = 0

    def escapeString(self, s):
        return s.translate(str.maketrans({
            "\"": r"\"",
            "\\": r"\\"
        }))

    def indentInc(self):
        self.indent += 4

    def indentDec(self):
        self.indent -= 4
        if self.indent < 0:
            self.indent = 0

    def append(self, scr):
        if len(self.script) and self.script[-1] == "\n":
            self.script += ' ' * self.indent
        self.script += scr

    def newline(self):
        self.script += "\n"

    def processContainer(self, nodeContainer, semicolon=False):
        if not isinstance(nodeContainer, ast.File):
            self.append("{")
            self.newline()
            self.indentInc()
        for val in nodeContainer.childs:
            self.processNode(val)
            if isinstance(val, ast.Statement):
                self.append(";")
                self.newline()
        if not isinstance(nodeContainer, ast.File):
            # self.newline()
            self.indentDec()
            self.append("}")
        if semicolon:
            self.append(";")
        self.newline()

    def processNode(self, node):
        if isinstance(node, ast.File) or isinstance(node, ast.Block):
            self.processContainer(node)
        elif isinstance(node, ast.Include):
            self.append("include \"%s\"" % node.filename)
            self.newline()
        elif isinstance(node, ast.FunctionDefinition):
            if not node.isPrototype:
                self.newline()
            if node.isNative:
                self.append("native ")
            if node.isStatic:
                self.append("static ")
            self.processNode(node.type)
            self.append(" " + node.name + "(")
            for i, x in enumerate(node.arguments):
                self.processNode(x)
                if len(node.arguments) > i + 1:
                    self.append(", ")
            self.append(")")
            if node.isPrototype:
                self.append(";")
                self.newline()
            else:
                self.append(" ")
                self.processContainer(node)
        elif isinstance(node, ast.Struct):
            self.newline()
            self.append("struct %s " % node.name)
            self.processContainer(node, True)
        elif isinstance(node, ast.VariableDeclaration):
            if node.modifiers:
                self.append(' '.join(node.modifiers))
                self.append(' ')
            self.processNode(node.type)
            self.append(" " + node.name)
            if node.initialization:
                self.append(" = ")
                self.processNode(node.initialization)
        elif isinstance(node, ast.ArgumentDefinition):
            self.processNode(node.type)
            self.append(" " + node.name)
        elif isinstance(node, ast.RootType):
            if isinstance(node, ast.BuiltinType):
                self.append(node.name)
            elif isinstance(node, ast.UserType):
                self.processNode(node.identifier)
            for dm in node.dimensions:
                self.append("[")
                self.processNode(dm)
                self.append("]")
            if node.arguments:
                self.append("<")
                for i, x in enumerate(node.arguments):
                    self.processNode(x)
                    if len(node.arguments) > i + 1:
                        self.append(",")
                self.append(">")
        elif isinstance(node, ast.Break):
            self.append("break")
        elif isinstance(node, ast.Continue):
            self.append("continue")
        elif isinstance(node, ast.Return):
            self.append("return")
            if node.expr:
                self.append(" ")
                self.processNode(node.expr)
        elif isinstance(node, ast.InfixOp):
            if isinstance(node.getParent(), ast.BinaryOp):
                self.append("(")
            self.processNode(node.lvalue)
            if node.operator in ['.']:
                self.append("%s" % node.operator)
            else:
                self.append(" %s " % node.operator)
            self.processNode(node.rvalue)
            if isinstance(node.getParent(), ast.BinaryOp):
                self.append(")")
        elif isinstance(node, ast.PrefixOp):
            if isinstance(node.getParent(), ast.BinaryOp):
                self.append("(")
            self.append(node.operator)
            if not isinstance(node.value, (ast.CustomValue, ast.Identifier)):
                self.append("(")
            self.processNode(node.value)
            if not isinstance(node.value, (ast.CustomValue, ast.Identifier)):
                self.append(")")
            if isinstance(node.getParent(), ast.BinaryOp):
                self.append(")")
        elif isinstance(node, ast.Identifier):
            self.append(node.value)
        elif isinstance(node, ast.IntegerValue):
            self.append("%d" % node.value)
        elif isinstance(node, ast.FixedValue):
            self.append(("%f" % node.value).rstrip('0'))
            if self.script[-1] == '.':
                self.append('0')
        elif isinstance(node, ast.LogicalValue):
            if node.value:
                self.append("true")
            else:
                self.append("false")
        elif isinstance(node, ast.StringValue):
            self.append("\"%s\"" % self.escapeString(node.value))
        elif isinstance(node, ast.NullValue):
            self.append("null")
        elif isinstance(node, ast.FunctionCall):
            self.processNode(node.value)
            self.append("(")
            for i, x in enumerate(node.arguments):
                self.processNode(x)
                if len(node.arguments) > i + 1:
                    self.append(", ")
            self.append(")")
        elif isinstance(node, ast.ArraySubscript):
            self.processNode(node.value)
            self.append("[")
            self.processNode(node.indexExpr)
            self.append("]")
        elif isinstance(node, ast.If):
            self.append("if (")
            self.processNode(node.condition)
            self.append(") ")
            # self.append("if ) { ")
            self.processNode(node.ifTrue)
            # if isinstance(node.ifFalse, ast.If):
            if node.ifFalse:
                self.append("else ")
                self.processNode(node.ifFalse)
            # self.append(" } ")
        elif isinstance(node, ast.For):
            self.append("for (")
            self.processNode(node.init)
            self.append("; ")
            self.processNode(node.condition)
            self.append("; ")
            self.processNode(node.next)
            self.append(") ")
            self.processContainer(node)
        elif isinstance(node, ast.While):
            self.append("while (")
            self.processNode(node.condition)
            self.append(") ")
            self.processContainer(node)
        elif isinstance(node, ast.DoWhile):
            self.append("do")
            self.processContainer(node)
            self.append("while (")
            self.processNode(node.condition)
            self.append(");")
            self.newline()
        elif isinstance(node, ast.Typedef):
            self.append("typedef ")
            self.processNode(node.type)
            self.append(" ")
            self.append(node.name)
        elif isinstance(node, ast.File):
            self.append()
        elif not node:
            return
        else:
            print("print: unkown node - " + str(node))

    def generate(self, rootNode):
        self.script = ""
        self.indent = 0
        self.processNode(rootNode)
        return self.script
