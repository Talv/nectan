import string

from . import definitions


class TokenCoords(object):

    def __init__(self, line, pos):
        # self.filename = filename
        self.line = line
        self.pos = pos
    # def __str__(self):
    #     return ""
    #     return json.dumps(self.__dict__)

    def serialize(self):
        return {
            'line': self.line,
            'pos': self.pos,
        }


class Token(str):

    def __add__(self, other):
        ret = Token(str(self) + str(other))
        # ret.setFile(self.filename)
        ret.set(self.line, self.pos)
        return ret

    def setFile(self):
        # self.filename = filename
        pass

    def set(self, line=0, pos=0):
        self.line = line
        self.pos = pos

    def coords(self):
        return TokenCoords(self.line, self.pos)

    def containsOnly(self, chars):
        return len(self) and all([c in chars for c in self])


class LexState:
    InCode = 0
    InString = 1
    InChar = 2
    InComment = 3


def containsOnly(s, chars):
    return len(s) and all([c in chars for c in s])


def tokenize(buff):
    # chars
    symbols = string.punctuation.replace("_", "")
    digits = string.digits
    floating = digits + "."
    # hexal = string.hexdigits
    whitespace = string.whitespace
    # location
    line = 1
    pos = 1
    #
    currentToken = Token("")
    # currentToken.setFile(filename)
    currentToken.set(line, pos)
    #
    state = LexState.InCode
    #
    singleLineComment = True

    #
    def resetToken(c = ""):
        currentToken = Token(c)
        currentToken.set(line, pos)
        # currentToken.setFile(filename)
        return currentToken

    #
    for char in buff:
        pos += 1
        # start of string
        if state == LexState.InCode and char == '"':
            if currentToken != "":
                yield currentToken
            currentToken = resetToken('"')
            state = LexState.InString
        # part of string
        elif state == LexState.InString:
            currentToken += Token(char)
            # end of string
            if char == '"' and currentToken[-2] != "\\":
                yield currentToken
                currentToken = resetToken()
                state = LexState.InCode
        # comment //
        elif state == LexState.InCode and (currentToken == '/' and char == '/'):
            singleLineComment = True
            currentToken += Token(char)
            state = LexState.InComment
        # in comment
        elif state == LexState.InComment:
            if singleLineComment and char == "\n":
                # yield currentToken
                line += 1
                pos = 1
                currentToken = resetToken()
                state = LexState.InCode
            else:
                currentToken += Token(char)
        # symbols
        elif char in symbols:
            # float
            if char == "." and (len(currentToken) == 0 or currentToken.containsOnly(floating)):
                currentToken += Token(char)
            # operator
            elif currentToken + char in definitions.Operations.OPERATORS:
                currentToken = Token(currentToken + char)
                currentToken.set(line, pos)
            # separator
            else:
                if currentToken != "":
                    yield currentToken
                currentToken = resetToken(char)
        # non symbols
        else:
            # end of the symbol operator?
            if (currentToken.containsOnly(symbols) and
                (not currentToken.containsOnly(floating) or char not in floating)
            ):
                yield currentToken
                currentToken = resetToken()
            # whitespace
            if char in whitespace:
                if currentToken != "":
                    yield currentToken
                if char == "\n":
                    line += 1
                    pos = 1
                currentToken = resetToken()
            # int
            elif char in digits and currentToken.containsOnly(digits):
                currentToken += Token(char)
            # float
            elif char in floating and currentToken.containsOnly(floating):
                currentToken += Token(char)
            # hex todo
            # binary todo
            # rest
            else:
                currentToken += Token(char)

    if currentToken != "":
        yield currentToken
