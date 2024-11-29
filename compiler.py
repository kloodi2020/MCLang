from lexer import Token
import const
import os

fileTemplates = {
    "load.mcfunction": "scoreboard objectives add MClangVars dummy {\"text\": \"MCLang Variables\"}\nscoreboard objectives add MClangTemp dummy {\"text\": \"MCLang Temp\"}\n"
}

class Compiler:
    def __init__(self, projFolder, namespace):
        self.projFolder = projFolder
        self.namespace = namespace

        self.codeBlocks = []
        self.functions = []

        self.tempInner = 0
        self.resultInner = 0

        self.condNot = False

        self.count = 0

    def visit(self, node):
        method = getattr(self, f"visit_{type(node).__name__}", self.noVisitMethod)
    
        return method(node)
    
    def findToken(self, list, token):
        idx = 0
        for item in list:
            if isinstance(item, Token):
                if item.matches(token.type, token.value):
                    return idx
            idx += 1
        
        raise ValueError(f"{token} is not in list")

    def noVisitMethod(self, node):
        raise Exception(f"No visit method defined for {type(node).__name__}")
    
    def writeFile(self, name, text):
        with open(self.projFolder + os.sep + name, "w") as file:
            if name in fileTemplates:
                file.write(fileTemplates[name])
            file.write(text)

    def visit_CodeBlockNode(self, node):
        self.codeBlocks.append(node)

        code = ""
        for inst in node.body:
            code += self.visit(inst)
            code += "\n"
        
        code = code[:-1]

        return code

    def visit_FunctionNode(self, node):
        self.functions.append(node.name)
        code = self.visit(node.body)

        self.writeFile(f"{node.name.value}.mcfunction", code)

        return code

    def visit_NumberNode(self, node):
        return f"{node.token.value}"
    
    def visit_CallNode(self, node):
        if len(node.args) > 0:
            funcName = node.value.name.value
            if funcName in const.BUILTINFUNC:
                if funcName == "print":
                    comp = "{}"
                    before = ""
                    if type(node.args[0]).__name__ == "NumberNode":
                        comp = "{\"text\":\"" + self.visit(node.args[0]) + "\"}"
                    elif type(node.args[0]).__name__ == "VarAccessNode":
                        comp = "{\"score\": {\"name\":\"" + node.args[0].name.value + "\",\"objective\":\"MClangVars\"}}"
                    elif type(node.args[0]).__name__ == "BinOpNode":
                        before = self.visit(node.args[0])
                        comp = "{\"score\": {\"name\":\"a\",\"objective\":\"MClangTemp\"}}"
                    return f"{before}\ntellraw @a {comp}"
        else:
            return f"function {self.namespace}:{node.value.name.value}"
    
    def visit_VarAccessNode(self, node):
        return f"{node.name.value} MClangVars"
    
    def visit_VarAssignNode(self, node):
        if type(node.value).__name__ == "BinOpNode":
            self.resultInner = 0
            return f"{self.visit(node.value)}\nscoreboard players operation {node.name.value} MClangVars = {const.LETTERS[self.resultInner]} MClangTemp"
        return f"scoreboard players set {node.name.value} MClangVars {self.visit(node.value)}"
    
    def visit_UnaryOpNode(self, node):
        if node.operation.matches(Token.NOT):
            self.condNot = True
            return self.visit(node.value)
        elif node.operation.matches(Token.SUB):
            return f"-{self.visit(node.value)}"

    def visit_IfNode(self, node):
        self.count += 1
        fileName = f"if_{self.count}"
        
        self.writeFile(fileName + ".mcfunction", self.visit(node.body))

        return f"{self.visit(node.cond)} run function {self.namespace}:{fileName}"

    def visit_BinOpNode(self, node):
        signOp = ""
        exType = ""
        opType = "expr"

        code = ""

        if node.operation.matches(Token.ADD):
            signOp = "+="
            opType = "expr"
        elif node.operation.matches(Token.SUB):
            signOp = "-="
            opType = "expr"
        elif node.operation.matches(Token.MUL):
            signOp = "*="
            opType = "expr"
        elif node.operation.matches(Token.DIV):
            signOp = "/="
            opType = "expr"
        elif node.operation.matches(Token.EE):
            signOp = "="
            exType = "if"
            opType = "comp"
        elif node.operation.matches(Token.NE):
            signOp = "="
            exType = "unless"
            opType = "comp"
        
        if self.condNot:
            if exType == "unless":
                exType = "if"
            else:
                exType = "unless"

        if type(node.left).__name__ == "NumberNode":
            code += f"scoreboard players set {const.LETTERS[self.tempInner]} MClangTemp {self.visit(node.left)}\n"
        elif type(node.left).__name__ == "VarAccessNode":
            code += f"scoreboard players operation {const.LETTERS[self.tempInner]} MClangTemp = {self.visit(node.left)}\n"
        elif type(node.left).__name__ == "BinOpNode":
            self.tempInner += 1
            self.resultInner += 1
            code += f"{self.visit(node.left)}\n"

        if type(node.right).__name__ == "NumberNode":
            code += f"scoreboard players set {const.LETTERS[self.tempInner + 1]} MClangTemp {self.visit(node.right)}\n"
            if opType == "expr":
                code += f"scoreboard players operation {const.LETTERS[self.tempInner]} MClangTemp {signOp} {const.LETTERS[self.tempInner + 1]} MClangTemp\n"
        elif type(node.right).__name__ == "VarAccessNode":
            code += f"scoreboard players operation {const.LETTERS[self.tempInner]} MClangTemp = {self.visit(node.right)}\n"
        elif type(node.right).__name__ == "BinOpNode":
            self.tempInner += 1
            self.resultInner += 1
            code += f"{self.visit(node.right)}\n"
            if opType == "expr":
                code += f"scoreboard players operation {const.LETTERS[self.resultInner]} MClangTemp {signOp} {const.LETTERS[self.tempInner]} MClangTemp\n"
        
        if opType == "comp" and self.tempInner <= 0:
            code += f"execute {exType} score {const.LETTERS[self.tempInner]} MClangTemp {signOp} {const.LETTERS[self.tempInner + 1]} MClangTemp"

        if code.endswith("\n"):
            code = code[:-1]

        if self.tempInner > 0:
            self.tempInner -= 1
        
        return code