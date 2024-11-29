from lexer import Token
import position
import error
import const

class NumberNode:
    def __init__(self, token):
        self.token = token

        self.posRange = self.token.posRange
    
    def __repr__(self):
        return f"{self.token.value}"

class StringNode:
    def __init__(self, token):
        self.token = token

        self.posRange = self.token.posRange
    
    def __repr__(self):
        return f"\"{self.token.value}\""

class BinOpNode:
    def __init__(self, left, operation, right):
        self.left = left
        self.operation = operation
        self.right = right

        self.posRange = [self.left.posRange[0], self.right.posRange[1]]
    
    def __repr__(self):
        return f"({self.left} {self.operation} {self.right})"

class IfNode:
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

        self.posRange = [self.cond.posRange[0], self.body.posRange[1]]
    
    def __repr__(self):
        return f"if {self.cond} {self.body}"

class UnaryOpNode:
    def __init__(self, value, operation):
        self.operation = operation

        self.value = value

        self.posRange = [self.value.posRange[0], self.operation.posRange[1]]

    def __repr__(self):
        return f"{self.operation} {self.value}"

class CodeBlockNode:
    def __init__(self, body):
        self.body = body

        if len(self.body) > 0:
            self.posRange = [self.body[0].posRange, self.body[-1].posRange]
        else:
            self.posRange = [position.Position(0, 0, 0, "", ""), position.Position(0, 0, 0, "", "")]

    def __repr__(self):
        return "{" + f"{self.body}" + "}"

class FunctionNode:
    def __init__(self, name, body):
        self.name = name
        self.body = body

        self.posRange = [self.name.posRange[0], self.body.posRange[1]]

    def __repr__(self):
        return f"func {self.name.value}() {self.body}"

class VarAccessNode:
    def __init__(self, name):
        self.name = name

        self.posRange = self.name.posRange

    def __repr__(self):
        return f"{self.name.value}"

class VarAssignNode:
    def __init__(self, name, value):
        self.name = name
        self.value = value

        self.posRange = [self.name.posRange[0], self.value.posRange[1]]
    
    def __repr__(self):
        return f"{self.name.value} = {self.value}"

class CallNode:
    def __init__(self, value, args):
        self.value = value
        self.args = args

        self.posRange = self.value.posRange
    
    def __repr__(self):
        return f"{self.value}({self.args})"

class ParseResult:
    def __init__(self):
        self.node = None
        self.error = None
    
    def register(self, other):
        if isinstance(other, ParseResult):
            if other.error: self.error = other.error
            return other.node
        return other
    
    def success(self, node):
        self.node = node
        return self
    
    def failure(self, error):
        self.error = error
        return self

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tokenIdx = -1

        self.advance()
    
    def advance(self):
        self.tokenIdx += 1

        if self.tokenIdx < len(self.tokens):
            self.currentTok = self.tokens[self.tokenIdx]
        
        return self.currentTok

    def parse(self):
        result = self.codeBlock(False)

        return result

    def factor(self):
        result = ParseResult()

        token = self.currentTok

        node = None

        if token.type in (Token.INT, Token.FLOAT):
            self.advance()
            node = NumberNode(token)
        elif token.matches(Token.STRING):
            self.advance()
            node = StringNode(token)
        elif token.matches(Token.SUB):
            self.advance()
            node = UnaryOpNode(self.expr(), token)
        elif token.matches(Token.IDENTIFIER):
            self.advance()
            node = VarAccessNode(token)
        elif token.matches(Token.LPAREN):
            self.advance()

            expr = self.expr()
            if expr.error:
                return expr

            if self.currentTok.type != Token.RPAREN:
                return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Expected )"))
        
            self.advance()

            node = expr.node

        if node == None:
            return result.failure(error.Error(token.posRange, error.Error.INVALID_SYNTAX, "Expected int or float or string or identifier or ("))

        return node

    def binOp(self, finder, opTokens):
        result = ParseResult()

        left = result.register(finder())

        while self.currentTok.type in opTokens:
            opToken = self.currentTok
            self.advance()
            right = result.register(finder())
            if type(right).__name__ == "StringNode":
                return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Operations with strings are not supported"))
            if type(left).__name__ == "StringNode":
                return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Operations with strings are not supported"))

            left = BinOpNode(left, opToken, right)
        
        return result.success(left)

    def term(self):
        return self.binOp(self.factor, (Token.MUL, Token.DIV))

    def expr(self):
        return self.compExpr()
    
    def compExpr(self):
        result = ParseResult()

        opTok = self.currentTok
        if opTok.matches(Token.NOT):
            self.advance()

            expr = self.expr()
            if expr.error:
                return expr
            
            return result.success(UnaryOpNode(expr.node, opTok))

        return self.binOp(self.arithExpr, (Token.EE, Token.NE))

    def arithExpr(self):
        return self.binOp(self.term, (Token.ADD, Token.SUB))
    
    def codeBlock(self, curly = True):
        result = ParseResult()

        if self.currentTok.matches(Token.LCURLY) or not curly:
            if curly:
                self.advance()
            
            endType = Token.RCURLY
            if not curly:
                endType = Token.EOF
            
            body = []

            while not self.currentTok.matches(endType):
                action = self.action()
                if action.error:
                    return action
                
                body.append(action.node)
            
            if curly:
                self.advance()

            return result.success(CodeBlockNode(body))
        else:
            return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Expected {"))

    def action(self):
        result = ParseResult()

        if self.currentTok.matches(Token.KEYWORD, "func"):
            self.advance()

            if not self.currentTok.matches(Token.IDENTIFIER):
                return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Expected identifier"))
            
            name = self.currentTok

            self.advance()
            if not self.currentTok.matches(Token.LPAREN):
                return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Expected ("))
            self.advance()
            if not self.currentTok.matches(Token.RPAREN):
                return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Expected )"))
            
            self.advance()

            body = self.codeBlock()
            if body.error:
                return body
            
            return result.success(FunctionNode(name, body.node))
        elif self.currentTok.matches(Token.KEYWORD, "if"):
            self.advance()

            cond = self.expr()
            if cond.error:
                return cond

            body = self.codeBlock()
            if body.error:
                return body
            
            return result.success(IfNode(cond.node, body.node))
        elif self.currentTok.matches(Token.IDENTIFIER):
            name = self.currentTok
            
            self.advance()

            if self.currentTok.matches(Token.LPAREN):
                self.advance()
                
                args = []
                if name.value in const.BUILTINFUNC:
                    while not self.currentTok.matches(Token.RPAREN):
                        arg = self.expr()
                        if arg.error:
                            return arg
                        
                        args.append(arg.node)

                        if not (self.currentTok.matches(Token.COMMA) or self.currentTok.matches(Token.RPAREN)):
                            return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Expected , or )"))
                        
                        if self.currentTok.matches(Token.RPAREN):
                            break
                        else:
                            self.advance()
                else:
                    if not self.currentTok.matches(Token.RPAREN):
                        return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Expected )"))
                
                self.advance()

                return result.success(CallNode(VarAccessNode(name), args))

            if not self.currentTok.matches(Token.EQ):
                return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Expected ="))

            self.advance()

            value = self.expr()
            if value.error:
                return value
            
            return result.success(VarAssignNode(name, value.node))

        return result.failure(error.Error(self.currentTok.posRange, error.Error.INVALID_SYNTAX, "Expected func or if or identifier"))