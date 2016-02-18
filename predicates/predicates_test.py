import predicates

@predicates.predicate
def a(self):
    self.depends.b()

@predicates.predicate
def b(self):
    return True

@predicates.predicate
def c(self):
    self.depends.a()
    self.depends.b()

start = predicates.System()

start.depends.a()
start.depends.c()
solutions = list(start.solve())
