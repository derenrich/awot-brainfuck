from pyparsing import Literal,Forward,ZeroOrMore,OneOrMore,Group

class AWOT:
    IncDP = Literal(">")
    DecDP = Literal("<")
    IncB = Literal("+")
    DecB = Literal("-")
    OutB = Literal(".")
    ReadB = Literal(",")    
    Start = Literal("[")
    End = Literal("]")
    # capture repeats
    ShiftL = Group(OneOrMore(IncDP))
    ShiftR = Group(OneOrMore(DecDP))
    Add = Group(OneOrMore(IncB))
    Sub = Group(OneOrMore(DecB))
    Loop = Forward()
    Expr = ShiftL|ShiftR|Add|Sub|Group(OutB)|ReadB|Loop
    Loop << Group(Start + ZeroOrMore(Expr) + End)
    Program = ZeroOrMore(Expr)
    def parse(self,prog):
        return self.Program.parseString(prog)

if __name__ == "__main__":
    import sys
    prog = sys.stdin.read()
    a = AWOT()
    print a.parse(prog)
