import json
from . import lexer

class Node(object):

    def __init__(self):
        self._coords = None
        self._parent = None

    def getChildsVarNames(self):
        l = list()
        for x in list(name for name in dir(self) if not name.startswith("_")):
            var = getattr(self, x)
            if isinstance(var, Node):
                l.append(x)
            elif isinstance(var, list) and len(var) and isinstance(var[0], Node):
                l.append(x)
            else:
                continue
        return l

    def setParent(self, parent, recursive=True):
        self._parent = parent
        if recursive:
            for x in self.getChildsVarNames():
                var = getattr(self, x)
                if isinstance(var, Node):
                    var = [var]
                for item in var:
                    if isinstance(item, Node):
                        item.setParent(self, recursive)

    def getParent(self, parentType=None):
        if not self._parent:
            return None
        elif parentType:
            if isinstance(self._parent, parentType):
                return self._parent
            else:
                return self._parent.getParent(parentType)
        else:
            return self._parent

    def getAncestor(self, ancestorType):
        if not self._parent:
            return None
        elif isinstance(self._parent, ancestorType):
            return self._parent
        else:
            return self._parent.getAncestor(ancestorType)

    # def getRootParent(self):
    #     return self.getParent(File)

    def hasParent(self, parent):
        return True if self.getParent(None, parent) else False

    def getChildren(self):
        l = list()
        for x in self.getChildsVarNames():
            var = getattr(self, x)
            if isinstance(var, list):
                l += var
            else:
                l.append(var)
        return l

    def replaceChild(self, oldChild, newChild):
        for x in self.getChildsVarNames():
            var = getattr(self, x)
            if var == oldChild:
                setattr(self, x, newChild)
                newChild.setParent(self)
                return True
            elif isinstance(var, list):
                setattr(self, x, [newChild if element == oldChild else element for element in var])
                newChild.setParent(self)
                return True
                # for element in var:
                #     if element == oldChild:
                #         var.re
        return False

    def pack(self):
        dump = {}
        # dump["id"] = self.__class__.__name__
        dump["id"] = str(self)
        dump["coords"] = str(self._coords)
        for key in list(name for name in dir(self) if not name.startswith("_")):
            var = getattr(self, key)
            if callable(var):
                continue
            if isinstance(var, Node):
                dump[key] = var.pack()
            elif isinstance(var, list):
                dump[key] = list()
                for x in var:
                    if isinstance(x, Node):
                        dump[key].append(x.pack())
                    elif isinstance(x, lexer.TokenCoords):
                        dump[key].append(x.serialize())
                    else:
                        dump[key].append(str(x))
            else:
                dump[key] = str(var)
        return dump

    def dump(self):
        return json.dumps(self.pack(), sort_keys = False, indent = 4)


class SymbolDefinition(Node):
    def __init__(self, name):
        self.name = name

    def serialize(self):
        cont = None
        parentSym = self.getParent(SymbolDefinition)
        if parentSym:
            cont = parentSym.name
        return {
            'name': self.name,
            'kind': self.__class__.__name__,
            'container': cont,
            'location': self._coords.serialize(),
            'file': self.getParent(File).name
        }



class Container(Node):

    def __init__(self, name = "", childs = None):
        # super().__init__()
        Node.__init__(self)
        self.name = name
        self.indirectlyMapped = False
        if not childs:
            childs = list()
        self.childs = childs


class File(Container):
    pass


class Namespace(Container):
    pass


class Class(Container, SymbolDefinition):

    def __init__(self):
        Container.__init__(self)
        SymbolDefinition.__init__(self, "")


class Struct(Container, SymbolDefinition):

    def __init__(self):
        Container.__init__(self)
        SymbolDefinition.__init__(self, "")


class FunctionDefinition(Container, SymbolDefinition):

    def __init__(self):
        Container.__init__(self)
        SymbolDefinition.__init__(self, "")
        # self.modifiers = list()
        self.isNative = False
        self.isStatic = False
        self.isPrivate = False
        self.isPrototype = False
        self.type = None
        self.arguments = list()


class Block(Container):
    pass


class Statement(Node):
    pass


class Include(Container):

    def __init__(self, filename = None):
        super().__init__()
        self.filename = filename


# Types

class RootType(Node):

    def __init__(self):
        super().__init__()
        self.dimensions = list()
        self.arguments = list()


class BuiltinType(RootType):

    def __init__(self):
        super().__init__()
        self.name = None


class UserType(RootType):

    def __init__(self):
        super().__init__()
        self.identifier = None


#

# class Variable(SymbolDefinition, Node):

#     def __init__(self, name = None):
#         Node.__init__(self)
#         SymbolDefinition.__init__(self, name)
#         self.modifiers = None
#         self.type = None


class ArgumentDefinition(SymbolDefinition, Node):

    def __init__(self, name = None):
        Node.__init__(self)
        SymbolDefinition.__init__(self, name)
        self.type = None
        self.isReference = False


class VariableDeclaration(SymbolDefinition, Statement):

    def __init__(self, name = None):
        Node.__init__(self)
        SymbolDefinition.__init__(self, name)
        # self.dimensions = list()
        self.type = None
        self.modifiers = None
        self.initialization = None


class Typedef(SymbolDefinition, Statement):
    def __init__(self, name=None):
        Node.__init__(self)
        SymbolDefinition.__init__(self, name)
        self.type = None


#

class If(Node):

    def __init__(self):
        super().__init__()
        self.condition = None
        self.ifTrue = None
        self.ifFalse = None

#


class Loop(Container):
    def __init__(self):
        super(Loop, self).__init__("loop")
        self.condition = None


class While(Loop):
    def __init__(self):
        super().__init__()


class DoWhile(Loop):
    def __init__(self):
        super().__init__()


class For(Loop):
    def __init__(self):
        super().__init__()
        self.init = None
        self.next = None


#


class Value(Node):

    def __init__(self, value = None):
        super().__init__()
        self.value = value


class NullValue(Value):

    def __init__(self):
        super().__init__("null")


class Identifier(Value):

    def __init__(self, value = None):
        Value.__init__(self, value)
        self._symbol = None


class CustomValue(Value):

    def __init__(self, value = None):
        Value.__init__(self, value)


class StringValue(CustomValue):

    def __init__(self, value = None):
        CustomValue.__init__(self, value)


class LogicalValue(CustomValue):

    def __init__(self, value = None):
        CustomValue.__init__(self, value)


class NumericValue(CustomValue):

    def __init__(self, value = None):
        CustomValue.__init__(self, value)


class IntegerValue(NumericValue):

    def __init__(self, value = None):
        NumericValue.__init__(self, value)


class FixedValue(NumericValue):

    def __init__(self, value = None):
        NumericValue.__init__(self, value)


#

class Return(Statement):

    def __init__(self):
        super().__init__()
        self.expr = None


class Continue(Statement):
    pass


class Break(Statement):
    pass

#

class Expression(Statement):
    pass


class Operation(Expression):

    def __init__(self, operator = None):
        super().__init__()
        self.operator = operator


class PrefixOp(Operation):

    def __init__(self, operator = None):
        Operation.__init__(self, operator)
        self.value = None


class PostfixOp(Operation):

    def __init__(self, operator = None):
        Operation.__init__(self, operator)
        self.value = None


class InfixOp(Operation):

    def __init__(self, operator = None):
        Operation.__init__(self, operator)
        self.lvalue = None
        self.rvalue = None


class BinaryOp(InfixOp):

    def __init__(self, operator = None):
        InfixOp.__init__(self, operator)


class AssignmentOp(InfixOp):

    def __init__(self, operator = None):
        InfixOp.__init__(self, operator)


class SelectionOp(InfixOp):

    def __init__(self, operator = "."):
        InfixOp.__init__(self, operator)


class TernaryOp(PrefixOp):

    def __init__(self):
        PrefixOp.ifTrue = None
        PrefixOp.ifFalse = None


class FunctionCall(PostfixOp):

    def __init__(self, arguments = None):
        if not arguments:
            arguments = list()
        PostfixOp.__init__(self, "()")
        self.arguments = arguments


class ArraySubscript(PostfixOp):

    def __init__(self):
        PostfixOp.__init__(self, "[]")
        self.indexExpr = None
