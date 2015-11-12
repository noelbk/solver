#! /usr/bin/env python

from solver import solve

class Success(Exception):
    pass

def diehardn(solver, target, *sizes):
    buckets = [0] * len(sizes)
    moves = []
    visited = set()

    def choose_bucket():
        return solver.choose(range(len(sizes)))

    def put(b, value):
        buckets[b] = value
        if buckets[b] == target:
            moves.append("done %s == %s" % (sizes[b], target))
            raise Success()

    def empty(b):
        moves.append("empty %s" % sizes[b])
        put(b, 0)

    def fill(b):
        moves.append("fill %s" % sizes[b])
        put(b, sizes[b])

    def pour(b):
        to = choose_bucket()
        if to == b:
            # can't pour into yourself
            solver.prune()
        poured = min(buckets[b], sizes[to] - buckets[to])
        moves.append("pour %s from %s to %s" % (poured, sizes[b], sizes[to]))
        put(b, buckets[b] - poured)
        put(to, buckets[to] + poured)

    t = tuple(buckets)
    visited.add(t)
    while True:
        try:
            solver.choose((empty, fill, pour))(choose_bucket())
        except Success:
            break

        t = tuple(buckets)
        if t in visited:
            solver.prune()
        visited.add(t)

    return moves

if __name__ == '__main__':
    for moves in solve(diehardn, 4, 3, 5):
        print "\n".join(moves)
        print
        break
