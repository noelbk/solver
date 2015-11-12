#! /usr/bin/env python

import collections

class Vars(dict):
    class DELETED(object): pass
    
    def __init__(self, parent=None):
        super(Vars, self).__init__()
        self.parent = parent

    def clone(self):
        return Vars(self)
        
    def __getattr__(self, name):
        if name in self:
            value = self[name]
            if value is DELETED:
                raise AttributeError(name)
            return value
        elif self.parent:
            return getattr(self.parent, name)
        else:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        self[name] = DELETED

class Env(object):
    def __init__(self, parent=None):
        if parent is None:
            parent = GlobalEnv
        self.parent = parent
        if parent:
            self.vars = parent.vars.clone()
        else:
            self.vars = Vars()
        
    def clone(self):
        return Env(self)
    
    def solve(self):
        def fn(solver):
            env = self.clone()
            env.solver = solver
            # TODO - resolve unsolved predicates
            return env
            
        for env in solver.solve(fn):
            yield env
            
    def choose(self, choices):
        return self.solver.choose(choices)
            
    def prune(self):
        self.solver.prune()

    def pred_func(self, fn, name=None):
        """define a new predicate in self.vars.predicates.  See
        @predicate for defining predicates in GlobalEnv"""
        if name is not None:
            name = fn.__name__
        self.pred_funcs[name] = fn
        # if there are any predicate instances defined from this func
        # already, mark them as unsolved
        for pred_inst in self.pred_inst_by_name(name):
            self.unsolved_add(pred_inst)
            
    def __getattr__(self, name):
        """default to returning a predicate, so you can call env.my_predicate(args)"""
        return self.pred_funcs[name]

    def pred_add(self, pred):
        """add a new predicate instance to my graph, usually a child of the root...?"""
        self.pred_stack[-1].depends(pred)
        self.unsolved_add(pred_inst)
        if self.mode == ModeSolving:
            self.pred_stack.append(pred)
            pred.check(self)
            self.pred_stack.pop()

    def cleanup(self, fn):
        """called withing a predicate to add a cleanup function when the predicate is removed"""
        self.pred_stack[-1].cleanup(fn)

    def solve(self, solver):
        env = self.clone()
        while env.unsolved:
            pred_inst = env.unsolved_pop(solver)
            if solver.if_any():
                pred_inst.check(solver)
            if solver.else_none():
                env.failed(pred_inst)
                for parent in pred_inst.parents:
                    env.unsolved_add(parent)
        return env


class PredFunc(PredFactory):
    def __call__(self, env, *args, **kwargs):
        # create a new PredicateInstance with args and kwargs
        pred = env.pred_get(env, self.name, args, kwargs)
        if not pred:
            pred = PredInst(self, env, args, kwargs)
        return env.pred_put(pred)
        
class PredInst(object):
    def __init__(self, pred_func, env, args, kwargs):
        self.pred_func = pred_func
        self.env = env
        self.args = args
        self.kwargs = kwargs
        self.children = [] # predicates that I depend on 
        self.parents = [] # predicates depend on me
        self.cleanups = []

    def depends(self, pred):
        self.children.add(pred);
        pred.parents.add(self)
        
    def cleanup(self, fn):
        self.cleanups.append(fn)
        
    def check(self, env):
        old_children = self.children
        for child in old_children:
            child.parents.remove(self):
        self.children = []
        self.ret = self.pred_func(env, *self.args, **self.kwargs)
        # clean up orphaned children
        for child in old_children:
            if not child.parents:
                env.remove(child)
      
GlobalEnv = Env()

def predicate(fn):
    return GlobalEnv.pred_func(fn)

@predicate
def choose_host(env):
    return env.choose(env.vars.hosts.keys())

@predicate
def host_require(env, host, ram=0, cpu=0, disk=0):
    host = env.vars.hosts[host]
    if host.ram < ram or host.cpu < cpu or host.disk < disk:
        env.prune()
        
    host.ram -= ram
    host.cpu -= cpu
    host.disk -= disk
    
    def cleanup(env):
        host.ram += ram
        host.cpu += cpu
        host.disk += disk
    env.cleanup(cleanup)
        
    
@predicate
def cluster(env, name, nodes):
    name = env.setname(("cluster", name))
    nodes = env.getvar(name + ("nodes",)), nodes)
    for i in range(nodes):
        env.cluster_node(name + ("nodes", i))
    
@predicate
def cluster_node(env, name):
    host = env.host_choose()
    env.qemu(host, name=name, ram=16, disks=(40, 80))
    
@predicate
def qemu(env, host, ram=2, disks=(,)):
    env.host_allocate(host, ram=ram)
    for disk in disks:
        env.host_allocate(host, disk=disk)
    env.host_service(host, "qemu -m %s" % ram)
    
@predicate
def host_service(env, host, cmd):
    print("service: %s: %s" % host, cmd)


#-----------
# example

        
env.changing()
env.hosts_add(100, ram=128, disks=(1000, 1000))
env.cluster("noel's cluster", 100)
for env2 in env.solve():
    env2.apply_parent()
    break


env.host_remove(host)
for env2 in env.solve():
    break
env.apply(env2)


