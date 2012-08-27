#!/usr/bin/env python
from llvm import *
from llvm.core import *
from llvm.ee import *  
from parse import AWOT

# How much space do we allocate our program
BUF_SIZE = 4096

class Compiler:
    def optimize_loop(self, loop, builder):

        nested_loop = any(map(lambda l : l[0] == '[',loop))
        if loop == [["-"]]:
            pv = builder.load(self.point)
            p = builder.gep(self.buf,[self.zero, pv])
            builder.store(self.zero, p)        
            return True
        elif not nested_loop:
            # flatten
            flat_loop = sum(loop,[])
            ios =  flat_loop.count(".") + flat_loop.count(",")
            if ios == 0 and flat_loop.count("<") == flat_loop.count(">"):
                changes = dict()
                pos = 0
                changes[0] = 0
                for a in flat_loop:
                    if a == "<":               
                        pos -= 1
                        if pos not in changes:
                            changes[pos] = 0
                    elif a == ">":
                        pos += 1
                        if pos not in changes:
                            changes[pos] = 0
                    elif a == "+":
                        changes[pos] += 1
                    elif a == "-":
                        changes[pos] -= 1
                if changes[0] >= 0:
                    # infinite loop?
                    return False
                else:
                    debug = False
                    #for k in changes:
                    #    if k < -34:
                    #        pv = builder.load(self.point)
                    #        res = builder.icmp(IPRED_ULT, pv, Constant.int(Type.int(), -k)) 
                    #        val = builder.select(res, Constant.int(Type.int(), 65), Constant.int(Type.int(), 66))
                    #        builder.call(self.printchar, (val,))

                    #    #    print loop
                    #    #    #return False
                    # loop variable
                    pv = builder.load(self.point)
                    p = builder.gep(self.buf,[self.zero, pv])
                    c_v = builder.load(p)
                    if changes[0] != -1:
                        multiple = builder.udiv(c_v,Constant.int( Type.int(), -changes[0]))
                    builder.store(self.zero, p)
                    for k in changes:
                        if changes[k] == 0 or k == 0:
                            continue
                        if k > 0:
                            po = builder.add(pv, Constant.int(Type.int(), k))
                        else:
                            po = builder.sub(pv, Constant.int(Type.int(), -k))
                        #if debug:
                        #    print po
                        p = builder.gep(self.buf,[self.zero, po])
                        v = builder.load(p)
                        # how complicated is this loop?
                        if changes[0] != -1:
                            delta = builder.mul(multiple, Constant.int(Type.int(), changes[k]))        
                            new_v = builder.add(v, delta)
                        elif changes[k] == 1:
                            new_v = builder.add(v, c_v)
                        elif changes[k] == -1:
                            new_v = builder.sub(v, c_v)
                        else:
                            delta = builder.mul(c_v, Constant.int(Type.int(), changes[k]))        
                            new_v = builder.add(v, delta)                            

                        #    print v
                        #    print new_v
                        #    print p
                        #    print self.block_count
                        builder.store(new_v, p)
                        
                    return True
        return False
    def compile(self,prog):
        ast = AWOT().parse(prog).asList()
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
            num = Constant.int( Type.int(), len(c)) 
            if c[0] == '[':
                c = list(c)[1:-1]
                if self.optimize_loop(c,builder):
                    continue
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

                self.build_func(c, func_builder)

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
            elif c[0] == ">":
                v = builder.load(self.point)
                res = builder.add(v, num)
                builder.store(res, self.point)
            elif c[0] == "<":
                v = builder.load(self.point)
                res = builder.sub(v, num)
                builder.store(res, self.point)
            elif c[0] == "+":
                pv = builder.load(self.point)
                p = builder.gep(self.buf,[self.zero, pv])
                v = builder.load(p)
                res = builder.add(v, num)
                builder.store(res, p)
            elif c[0] == "-":
                pv = builder.load(self.point)
                p = builder.gep(self.buf,[self.zero, pv])
                v = builder.load(p)
                res = builder.sub(v, num)
                builder.store(res, p)
            elif c[0] == '.':
                pv = builder.load(self.point)
                p = builder.gep(self.buf,[self.zero, pv])
                v = builder.load(p)
                builder.call(self.printchar, (v,))

if __name__ == "__main__":
    import sys
    prog = sys.stdin.read()
    c = Compiler()
    c.compile(prog)
    #print c.module
    ee = ExecutionEngine.new(c.module)
    retval = ee.run_function(c.main, [])
    print ""
    print "returned", retval.as_int()
