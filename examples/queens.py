#! /usr/bin/env python

from solver import solve

def queens(solver, n):
    board = []
    for row in range(n):
        col = solver.choose(range(n))
        if attacked(board, row, col):
            solver.prune()
        board.append(col)
    return board

def attacked(board, row, col):
    for prev_row, prev_col in enumerate(board):
        if prev_col == col \
           or (prev_col + prev_row == col + row) \
           or (prev_col - prev_row == col - row):
            return True
    return False

def fmt_board(queens):
    s = ""
    n = len(queens)
    for row in range(n):
        for col in range(n):
            c = '.'
            if col == queens[row]:
                c = 'Q'
            s += c
        s += '\n'
    return s

if __name__ == '__main__':
    import sys
    n = 8
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    for board in solve(queens, n):
        print fmt_board(board)
        print
