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

    Loop = Forward()
    Expr = IncDP|DecDP|IncB|DecB|OutB|ReadB|Loop
    Loop << Group(Start + ZeroOrMore(Expr) + End)
    Program = ZeroOrMore(Expr)
    def parse(self,prog):
        return self.Program.parseString(prog)

