#! /usr/bin/env python
import collections

class Solver(object):
    """
A solver for nondeterministic programming [1].  A nondeterministic
function can at any time choose several different branches of
execution.  The solver will evaluate every branch.  Branches may be
pruned if they fail to solve the problem.  This solver explores all
possible choices breadth first.

For example, consider a maze solver.  At every node, the mouse chooses
to branch left, right, or forward.  If the branch ends in a wall or a
loop, that branch is pruned.  If the step reaches the end, it's
solved.

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

[1] https://en.wikipedia.org/wiki/Nondeterministic_programming

Apologies for the brute-force implementation.  An ideal implementation
would partially evaluate the function, save state, explore choices,
and backtrack, but saving the whole stack and execution context of a
function would require a language change.  (yield isn't sufficient.).
So, this restarts the function from scratch at every evaluation
    """

    def __init__(self):
        self.choice_stack = []
        self.choices_idx = -1
        self.if_any_stack = []
        self.choices = None

    def solve(self, fn, *args, **kwargs):
        """repeatedly call function , iterating over all possible outputs"""
        self.choice_stack = collections.deque()
        self.choice_stack.append([])
        while len(self.choice_stack) > 0:
            self.choices = self.choice_stack.popleft()
            self.choices_idx = -1
            self.if_any_stack = []
            try:
                yield fn(self, *args, **kwargs)
            except PruneException:
                pass
            except ChooseException:
                # could return partial solutions here
                pass

    def choose(self, choices):
        """branch myself to evaluate each choice in choices"""
        self.choices_idx += 1
        if self.choices_idx < len(self.choices):
            # return the next choice in my path, if there is one
            return choices[self.choices[self.choices_idx]]
        else:
            # push all possible next choices
            for i in range(1, len(choices)):
                self.choice_stack.append(self.choices + [i])

            # if I'm in under an if_any block, then count the number
            # of branches I must evaluate before concluding that they
            # *all* end in prune.
            if self.if_any_stack:
                if_any_inst = self.if_any_stack[-1]
                if_any_inst.branch_count += len(choices)-1

            # return the first choice
            choice = choices[0]
            self.choices.append(0)
            return choice

    def prune(self):
        """abort the current branch"""

        # if I'm in under an if_any block, then decrement my branch count
        if self.if_any_stack:
            if_any_inst = self.if_any_stack[-1]
            if_any_inst.branch_count -= 1
            if if_any_inst.branch_count == 0 and not if_any_inst.locked:
                # all my branches end in prune, so I must enable my else_none block
                if_any_inst.val = False
                # push a new choice path that ends in my if_any
                self.choice_stack.append(self.choices[:if_any_inst.choice_idx+1])

        raise PruneException()

    def if_any(self):
        """Evaluate all choosees of the first block and execute the
        second block only if all branches of the first block end in
        prune()

            if solver.if_any():
                do_stuff()
            if solver.else_none():
                other_stuff()

        do other_stuff() only if *all* branches of do_stuff() end in prune()

        Every if_any() must be followed by an else_none()
        """
        self.choices_idx += 1

        if self.choices_idx < len(self.choices):
            if_any_inst = self.choices[self.choices_idx]
        else:
            # create a new if_any instance that wil be shared by all
            # future choices
            if_any_inst = IfAny(self.choices_idx)
            self.choices.append(if_any_inst)
        self.if_any_stack.append(if_any_inst)

        # this will only be false after all branches have been
        # evaluated and all ended in prune
        return if_any_inst.val

    def else_none(self):
        if_any_inst = self.if_any_stack.pop()
        # if I reached here, either one branch never pruned, or all
        # branches pruned.  In either case, the if_any instance value
        # is now locked
        if_any_inst.locked = True
        return not if_any_inst.val

class ChooseException(Exception):
    pass

class PruneException(Exception):
    pass

class IfAny(object):
    def __init__(self, choice_idx):
        self.choice_idx = choice_idx
        self.val = True
        self.locked = False
        self.branch_count = 1

def solve(fn, *args, **kwargs):
    for r in Solver().solve(fn, *args, **kwargs):
        yield r
