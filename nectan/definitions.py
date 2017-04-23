
class Instructions():
    CONTAINERS = ["struct"] # , "class", "namespace", "enrichment", "property"
    FUNC_MODS = ["static", "native"] # "private", "public"
    VAR_MODS = ["const", "static"] # "private", "public"
    FLOW = ["if", "else", "case", "default", "continue", "break"]
    LOOPS = ["for", "do", "while"] # "switch"
    INCLUDE = ["include"] # using
    OTHER = ["return"] # "template"
    SPECIAL_TYPES = ["arrayref", "structref", "funcref"]
    TYPES = [
        "abilcmd", "actor", "actorscope", "aifilter", "animfilter", "bank", "bool", "byte", "camerainfo", "char", "color", "doodad", "fixed", "handle", "int", "marker", "order", "playergroup", "point", "region", "revealer", "sound", "soundlink", "string", "text", "timer", "transmissionsource", "trigger", "unit", "unitfilter", "unitgroup", "unitref", "void", "wave", "waveinfo", "wavetarget", "arrayref", "structref", "funcref"
    ]
    BOOL = ["true", "false"]
    NULL = ["null"]
    KEYWORDS = CONTAINERS + FUNC_MODS + VAR_MODS + FLOW + LOOPS + INCLUDE + OTHER + TYPES + BOOL + NULL


class Operations():
    PREFIX = ["-", "+", "~", "!", "++", "--"]
    POSTFIX = ["++", "--"]
    RESOLUTION = ["::"]
    SELECTION = ["."]
    MULTIPLICATION = ["*", "/", "%"]
    ADDITION = ["+", "-"]
    BITWISE = ["|", "&", "^", "<<", ">>"]
    RELATION = ["<", "<=", ">", ">="]
    EQUALITY = ["==", "!="]
    TERNARY = ["?", ":"]

    TYPECAST = ["(type)"]
    FUNCTION_CALL = ["()"]
    ARRAY_SUBSCRIPT = ["[]"]

    ASSIGNMENT = [
        "=",
        "+=", "-=",
        "/=", "*=", "%=",
        "<<=", ">>=",
        "&=", "^=", "|="
    ]

    LOGICAL = ["&&", "||"]

    INFIX = RESOLUTION + SELECTION + MULTIPLICATION + ADDITION + BITWISE + RELATION + EQUALITY + LOGICAL + ASSIGNMENT # + TERNARY

    OPERATORS = PREFIX + INFIX + POSTFIX

    # PRECEDENCE = [
    #     RESOLUTION,
    #     SELECTION,
    #     MULTIPLICATION,
    #     ADDITION,

    #     LOGICAL,
    #     TERNARY,
    #     ASSIGNMENT
    # ]
    PRECEDENCE = [
        {
            "InfixOp": RESOLUTION
        },
        {
            "InfixOp": SELECTION,
            "PostfixOp": POSTFIX + FUNCTION_CALL + ARRAY_SUBSCRIPT
        },
        {
            "PrefixOp": PREFIX # + TYPECAST
        },
        {
            "InfixOp": MULTIPLICATION
        },
        {
            "InfixOp": ADDITION
        },
        {
            "InfixOp": BITWISE
        },
        {
            "InfixOp": RELATION
        },
        {
            "InfixOp": EQUALITY
        },
        {
            "InfixOp": ["&"]
        },
        {
            "InfixOp": ["^"]
        },
        {
            "InfixOp": ["|"]
        },
        {
            "InfixOp": ["&&"]
        },
        {
            "InfixOp": ["||"]
        },
        {
            "InfixOp": TERNARY
        },
        {
            "InfixOp": ASSIGNMENT
        }
    ]


#
# ERRORS
#

class ParseError(RuntimeError):

    def __init__(self, filename, line, pos, msg):
        self.filename = filename
        self.line = line
        self.pos = pos
        self.msg = msg
        print("%s:%d:%d: parse error, %s" % (filename, line, pos, msg))


class SemanticError(RuntimeError):

    def __init__(self, node, msg):
        print("SemanticError: %s" % msg)


#
#
#

class CodePrinter(object):

    def generate(self, rootNode):
        raise NotImplementedError()
