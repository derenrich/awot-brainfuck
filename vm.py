from llvm import *
from llvm.core import *
from llvm.ee import *  
from parse import AWOT

# How much do we allocate our program
BUF_SIZE = 2048


class Compiler:
    def compile(self,prog):
        ast = AWOT().parse(prog)
        self.module = Module.new('awot_module')

        self.one = Constant.int( Type.int(), 1) 
        self.zero = Constant.int( Type.int(), 0) 
        self.block_count = 0

        # allocate our buffer
        int_arr = Type.array(Type.int(),BUF_SIZE)
        self.buf = self.module.add_global_variable(int_arr,'buf')
        self.buf.section = ".data"        
        self.buf.initializer = Constant.array(Type.int(), [self.zero] * BUF_SIZE)

        # our global pointer
        self.point = self.module.add_global_variable(Type.int(),'point')
        self.point.initializer = self.zero
        self.point.section = ".data"

        # setup a putchar function
        self.printchar = Function.new(self.module, Type.function(Type.int(), [Type.int()]), 'putchar')

        # setup our main function
        self.main = self.module.add_function(Type.function(Type.int(),[]), "main")
        bb = self.main.append_basic_block("entry")    
        builder = Builder.new(bb)
        self.build_func(ast,builder)
        # return value is the current memory cell
        pv = builder.load(self.point)
        p = builder.gep(self.buf, [self.zero, pv])
        v = builder.load(p)
        builder.ret(v)
    def build_func(self, ast, builder):
        for c in ast:
            if len(c) > 1:
                new_func = self.module.add_function(Type.function(Type.void(), []), "func_"+str(self.block_count))
                self.block_count += 1        
                main_block = new_func.append_basic_block("entry")
                body_block = new_func.append_basic_block("body")
                end_block = new_func.append_basic_block("end")
                ret_block = new_func.append_basic_block("ret")
                builder.call(new_func, ())

                func_builder = Builder.new(main_block)
                pv = func_builder.load(self.point)
                p = func_builder.gep(self.buf, [self.zero, pv])
                v = func_builder.load(p)
                b = func_builder.icmp(IPRED_UGT, v, self.zero)
                func_builder.cbranch(b, body_block, ret_block) 

                func_builder.position_at_end(body_block)

                self.build_func(c[1:-1], func_builder)

                func_builder.branch(end_block)
                func_builder.position_at_end(end_block)
                pv = func_builder.load(self.point)
                p = func_builder.gep(self.buf, [self.zero, pv])
                v = func_builder.load(p)
                b = func_builder.icmp(IPRED_UGT, v, self.zero)
                func_builder.cbranch(b, body_block, ret_block)                     

                func_builder.position_at_end(ret_block)
                func_builder.ret_void()
                new_func.verify()
            elif c == ">":
                v = builder.load(self.point)
                res = builder.add(v, self.one)
                builder.store(res, self.point)
            elif c == "<":
                v = builder.load(self.point)
                res = builder.sub(v, self.one)
                builder.store(res, self.point)
            elif c == "+":
                pv = builder.load(self.point)
                p = builder.gep(self.buf,[self.zero, pv])
                v = builder.load(p)
                res = builder.add(v, self.one)
                builder.store(res, p)
            elif c == "-":
                pv = builder.load(self.point)
                p = builder.gep(self.buf,[self.zero, pv])
                v = builder.load(p)
                res = builder.sub(v, self.one)
                builder.store(res, p)
            elif c == '.':
                pv = builder.load(self.point)
                p = builder.gep(self.buf,[self.zero, pv])
                v = builder.load(p)
                builder.call(self.printchar, (v,))



#hw=">++[<+++++++++++++>-]<[[>+>+<<-]>[<+>-]++++++++[>++++++++<-]>.[-]<<>++++++++++[>++++++++++[>++++++++++[>++++++++++[>++++++++++[>++++++++++[>++++++++++[-]<-]<-]<-]<-]<-]<-]<-]++++++++++."



if __name__ == "__main__":
    import sys
    prog = sys.stdin.read()
    c = Compiler()
    c.compile(prog)
    print c.module
    ee = ExecutionEngine.new(c.module)
    #retval = ee.run_function(c.main, [])
    #print "returned", retval.as_int()
