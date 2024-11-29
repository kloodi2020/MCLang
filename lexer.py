import const
import error
import position

class Token:
    IDENTIFIER = "IDENTIFIER"
    KEYWORD = "KEYWORD"

    EOF = "EOF"

    EQ = "EQ"
    EE = "EE"
    NE = "NE"

    NOT = "NOT"

    INT = "INT"
    FLOAT = "FLOAT"
    
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"

    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LCURLY = "LCURLY"
    RCURLY = "RCURLY"

    def __init__(self, posRange, type, value = None):
        self.type = type
        self.value = value

        newPosRange = []
        for pos in posRange:
            newPosRange.append(pos.copy())

        self.posRange = newPosRange
        if len(self.posRange) < 2 or self.posRange[1] == None:
            self.posRange.append(self.posRange[0].copy())
            
            try:
                self.posRange[1].advance(self.posRange[1].ftxt[self.posRange[1].idx])
            except:
                pass
    
    def matches(self, type, value = None):
        if value: return self.type == type and self.value == value
        return self.type == type

    def __repr__(self):
        if self.value:
            return f"({self.type}: {self.value})"
        else:
            return f"({self.type})"

class Lexer:
    def __init__(self, fn, code):
        self.fn = fn
        self.code = code
        
        self.pos = position.Position(-1, 0, -1, fn, self.code)
        self.currentChar = None

        self.advance()
    
    def advance(self):
        self.pos.advance(self.currentChar)
        self.currentChar = self.code[self.pos.idx] if self.pos.idx < len(self.code) else None
    
    def lex(self):
        tokens = []

        while self.currentChar != None:
            if self.currentChar in " \t\n":
                self.advance()
            elif self.currentChar in const.DIGITS:
                tokens.append(self.makeNumber())
            elif self.currentChar in const.LETTERS:
                tokens.append(self.makeIdentifier())
            elif self.currentChar == "+":
                tokens.append(Token([self.pos], Token.ADD))
                self.advance()
            elif self.currentChar == "-":
                tokens.append(Token([self.pos], Token.SUB))
                self.advance()
            elif self.currentChar == "*":
                tokens.append(Token([self.pos], Token.MUL))
                self.advance()
            elif self.currentChar == "/":
                tokens.append(Token([self.pos], Token.DIV))
                self.advance()
            elif self.currentChar == "(":
                tokens.append(Token([self.pos], Token.LPAREN))
                self.advance()
            elif self.currentChar == ")":
                tokens.append(Token([self.pos], Token.RPAREN))
                self.advance()
            elif self.currentChar == "{":
                tokens.append(Token([self.pos], Token.LCURLY))
                self.advance()
            elif self.currentChar == "}":
                tokens.append(Token([self.pos], Token.RCURLY))
                self.advance()
            elif self.currentChar == "#":
                while self.currentChar != "\n":
                    self.advance()
            elif self.currentChar == "=":
                tokens.append(self.makeEquals())
            elif self.currentChar == "!":
                tokens.append(self.makeNotEquals())
            else:
                posStart = self.pos.copy()
                char = self.currentChar
                self.advance()

                return [], error.Error([posStart], error.Error.ILLEGAL_CHAR, f"\"{char}\"")

        tokens.append(Token([self.pos], Token.EOF))

        return tokens, None
    
    def makeNumber(self):
        numStr = ""
        dots = 0

        startPos = self.pos.copy()

        while self.currentChar != None and self.currentChar in const.DIGITS + ".":
            if self.currentChar == ".":
                if dots >= 1:
                    break

                dots += 1
                numStr += self.currentChar
            else:
                numStr += self.currentChar
            
            self.advance()
            
        if dots <= 0:
            return Token([startPos, self.pos], Token.INT, int(numStr))
        else:
            return Token([startPos, self.pos], Token.FLOAT, float(numStr))

    def makeIdentifier(self):
        idenStr = ""

        startPos = self.pos.copy()

        while self.currentChar != None and self.currentChar in const.LETTERS + "_":
            idenStr += self.currentChar
            
            self.advance()
            
        if idenStr in const.KEYWORDS:
            return Token([startPos, self.pos], Token.KEYWORD, idenStr)
        else:
            return Token([startPos, self.pos], Token.IDENTIFIER, idenStr)
    
    def makeEquals(self):
        tokenType = Token.EQ

        startPos = self.pos.copy()

        self.advance()
        if self.currentChar == "=":
            tokenType = Token.EE
            self.advance()
        
        return Token([startPos, self.pos], tokenType)

    def makeNotEquals(self):
        tokenType = Token.NOT

        startPos = self.pos.copy()

        self.advance()
        if self.currentChar == "=":
            tokenType = Token.NE
            self.advance()
        
        return Token([startPos, self.pos], tokenType)