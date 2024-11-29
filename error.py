class Error:
    ILLEGAL_CHAR = "Illegal Character"
    INVALID_SYNTAX = "Invalid Syntax"

    def __init__(self, posRange, errName, details = None):
        self.errName = errName
        self.details = details

        newPosRange = []
        for pos in posRange:
            newPosRange.append(pos.copy())

        self.posRange = posRange
        if len(self.posRange) < 2 or self.posRange[1] == None:
            self.posRange.append(self.posRange[0])
    
    def __str__(self):
        result = f"At {self.posRange[0].fn}, line {self.posRange[0].ln + 1}:\n{self.posRange[0].ftxt.split("\n")[self.posRange[0].ln]}\n{self.errName}"
        if self.details:
            result += f": {self.details}"

        return result