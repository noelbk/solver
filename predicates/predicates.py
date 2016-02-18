#! /usr/bin/env python

class Predicate(object):
    STATE_UNSOLVED  = 'unsolved'
    STATE_SOLVING   = 'solving'
    STATE_SOLVED    = 'solved'
    STATE_STARTING  = 'starting'
    STATE_STARTED   = 'started'
    STATE_STOPPING  = 'stopping'
    
    @staticmethod
    def mkname(pred_name, args, kwargs):
        return (name, args, tuple(sorted(kwargs.items())))
        
    def __init__(self, sysvars, name, *args, **kwargs):
        vars(self)['vars'] = sysvars
        pred_name = self.mkname(name, args, kwargs)
        vars(self)['local_vars'] = sysvars.predicates[pred_name]
        self.name = pred_name
        self.args = args
        self.kwargs = kwargs
        self.state = self.STATE_UNSOLVED

    def __getattr__(self, key):
        return self.local_vars.get(key)

    def __setattr__(self, key, value):
        return self.local_vars.put(key, value)
        
    def require_byname(self, name, args, kwargs):
        pred_name = self.mkname(name, args, kwargs)
        pred = self.vars.predicates.get(pred_name)
        if pred:
            # circular dependency check
            assert pred.state is not self.STATE_SOLVING, \
                   "Circular dependency!  Hope the stack trace helps find where it is"
        else:
            klass = self.vars.pred_class.get(pred_name)
            assert klass, "undefined predicate name: %s" % pred_name
            pred = klass(self.vars, args, kwargs)
            self.vars.predicates[pred_name] = pred
            pred.solve()
        self.child_add(pred)
        return pred.ret

    @property
    def require(self):
        """So you can write self.require.pred_name(pred_args) instead
        of self.require_byname("pred_name", pred_args)"""
        return PredicateRequireHelper(self)
    
    def solve(self):
        self.state = self.STATE_SOLVING
        assert False, "unimplemented!"
        self.state = self.STATE_SOLVED
        

class PredicateRequireHelper(object):
    """handles self.require.pred_name"""
    def __init__(self, pred_caller):
        self.pred_caller = pred_caller

    def __getattr__(self, pred_name):
        return PredicateRequireArgsHelper(self.pred_caller, pred_name)


class PredicateRequireArgsHelper(object)
    """handles self.require.pred_name(*args, **kwargs)

    if pred_name(pred_args) is already defined, return it.  Otherwise, evaluate it and return the result"""
    def __init__(self, pred_caller, pred_name):
        self.pred_caller = pred_caller
        self.pred_name = pred_name

    def __call__(self, *args, *kwargs):
        return self.pred_caller.require_byname(pred_name, args, kwargs)
        

def predicate(fn):
    predicate_factories.add()
    class 

