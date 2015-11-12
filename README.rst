Solver
======

A Python library for solving for nondeterministic functions.  Those
are functions that can choose several different branches of execution.
The solver will evaluate every branch.  Branches may be pruned if they
fail to solve the problem.  This solver explores all possible choices
breadth first.


Installation
------------

::

    # (in a virtualenv)
    pip install -r requirements.txt
    python setup.py install  # (or develop)
    python setup.py test

    
Overview
--------
    
solver.solve(func, args) iterates over all possible solutions to
func::

    for solution in solver.solve(func, args)

func(solver, args) can call solver.choose() to evaluate different
values and solver.prune() to abort a choice::

    def func(solver, args):

        # will evaluate each choice
        choice = solver.branch(choices)

	# some time later
	if choice_was_no_good():
	    solver.prune()

	return val


Examples
--------
	
For example, consider a maze solver.  At every node, the mouse may
choose to branch left, right, or forward.  If the branch ends in a
wall or a loop, that branch is pruned.  If the step reaches the end,
it's solved::

    def mouse(solver, maze):
        route = []
        pos = maze.start
        while True:
            if maze.is_exit(pos):
                return route
            if not maze.is_valid(pos):
                solver.prune()
            maze.visited(pos):
            step = solver.choose((Left, Right, Forward))
            route.append(step)
            pos = pos.move(step)

    for route in solve(mouse, maze):
        print route

See also the `N queens problem`_ and the `diehard buckets`_ problem from `TLA+`_

.. _N queens problem: examples/queens.py
.. _diehard buckets: examples/buckets.py


See also
--------

The breadth-first solver is inspired by Leslie Lamport's excellent
`TLA+`_.  I've got an earlier `Elixir BFS solver`_ too.

.. _TLA+: http://research.microsoft.com/en-us/um/people/lamport/tla/tla.html
.. _Elixir BFS solver: https://github.com/noelbk/bfs


Author
------

Noel Burton-Krahn <noel@burton-krahn.com>
