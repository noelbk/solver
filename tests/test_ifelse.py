#! /usr/bin/env python
import unittest
from solver import solve

def ifany_if(solver):
    if solver.if_any():
        c = solver.choose(range(5))
        if c == 3:
            solver.prune()
        return c
    if solver.else_none():
        return "else"

def ifany_else(solver):
    if solver.if_any():
        solver.prune()
    if solver.else_none():
        return "else"

def ifany_else2(solver):
    if solver.if_any():
        if solver.if_any():
            solver.choose(range(5))
            if solver.if_any():
                solver.choose(range(5))
                solver.prune()
            if solver.else_none():
                solver.prune()
        if solver.else_none():
            return ifany_if(solver)
    if solver.else_none():
        return "else"

def ifany_none(solver):
    if solver.if_any():
        solver.prune()
    if solver.else_none():
        solver.prune()

class TestSolverIfElse(unittest.TestCase):
    def test_solver_ifelse(self):
        self.assertEquals([0, 1, 2, 4], list(solve(ifany_if)))
        self.assertEquals(["else"], list(solve(ifany_else)))
        self.assertEquals([0, 1, 2, 4], list(solve(ifany_else2)))
        self.assertEquals([], list(solve(ifany_none)))

if __name__ == '__main__':
    unittest.main()
