#! /usr/bin/env python
import unittest
from solver import solve

class TestSolver(unittest.TestCase):
    def fn(self, solver):
        i = solver.choose((1, 2, 3))
        j = solver.choose((1, 2, 3))
        if j == 2:
            k = solver.choose((1, 2, 3))
        else:
            k = 0
        if i == j or j == k or i == k:
            solver.prune()
        return i, j, k

    def test_solver(self):
        self.assertEquals([(2, 1, 0), (3, 1, 0), (1, 3, 0), (2, 3, 0), (3, 2, 1), (1, 2, 3)], list(solve(self.fn)))
