#! /usr/bin/env python
import unittest

import solver

class TestSolver(unittest.TestCase):
    def test_queens(self):
        from examples.queens import queens
        solutions = list(solver.solve(queens, 5))
        self.assertTrue(solutions)
        self.assertIn([1, 3, 0, 2, 4], solutions)

    def test_diehardn(self):
        from examples.buckets import diehardn
        solutions = list(solver.solve(diehardn, 4, 3, 5))
        self.assertTrue(solutions)
        self.assertIn(['fill 5',
                       'pour 3 from 5 to 3',
                       'empty 3',
                       'pour 2 from 5 to 3',
                       'fill 5',
                       'pour 1 from 5 to 3',
                       'done 5 == 4'], solutions)
