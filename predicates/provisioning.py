#! /usr/bin/env python
#
"""
Predicate Configuration Management

Current configuration management systems like Ansible, Puppet, and
Chef are procedural.  They apply a script to a system and hope that
correct system behaviour is a side effect of executing a script.
Monitoring and failure recovery is left to other subsystems like
pacemaker, systemd, etc.

We want a system to be flexible and resilient.  It should be able to
recover from system state changes like failures, upgrades, host
additions, etc.  To do that, you need a clear definition of what
correct system state is, and a flexible algorithm for provisioning a
system correctly given a changable set of resources.

This project uses a declarative paradigm for system configuration:
define correct system behaviour as a hierarchy of predicates and let
an automated solver find configuration solutions that satisfy those
predicates.  If system conditions change the solver will re-evaluate
affected predicates and attempt to find a new configuration that
continues to satisfy them.  This is rather like Prolog plus Make for
configuration management.

A predicate is a statement that must be true for the system to be
considered correct.  Predicates depend on system state variables and
other predicates.  System state variables include the set of available
hosts, and the processes running on those hosts.  If a variable
changes, the predicate is re-evaluated.  If the re-evalutation fails,
the parent predicates are re-evaluated and so on until the system
finds a new correct configuration or fails.

System configuration is applied in four steps: planning, execution,
monitoring, and recovery.  Planning to allocates a set of predicate
instances which satisfy predicate contraints.  Execution uses
predicate instances to configure and run services on hosts.
Monitoring tracks all services and reports service and host state back
by changing system variables.  When system variables change, the
planning process repeats.

Here's an example web app with web servers on all hosts and a 3-way
replicated database.

    myapp
    |
    |-httpd-everywhere
    | `-for all hosts  <-- changes when hosts are added/removed
    |   |-static content
    |   | |- allocate space
    |   | `- rsync content  <-- if content changes, will re-run rsync
    |   `-httpd
    |
    `-database
      `-mysql-replicated
        |-mysql-1
        | |-host 100   <-- changes when host 100 becomes unavailable
        | `-configure and run mysql
        |-mysql-2
        | |-host 101
        | `-configure and run mysql
        `-mysql-3
          |-host 102
          `-configure and run mysql

The "for all hosts" predicate depends on the "number of hosts"
variable.  If the number of hosts increases, the "for all hosts"
predicate will be re-evaluated and a new webserver will be spun up on
the new hosts.

The "host 100" predicate depends on that host being available.  If the
host becomes unavailable, the "host 100" ppredicate will fail.  That
will cause the "mysql-1" predicate to be re-evaluated.  It will choose
another available host and restart the new mysql replica with a new
predicate like "host 103".


Other Tricks

You can upgrade predicates.  If a predicate is redefined, the new
predicate is evaluated in the current system context.

"""


import collections
import copy


def pred_name(name, *args, **kwargs):
    return (name, args, tuple(sorted(kwargs.items())))


class Predicate(object):
    """unsolved -> checked -> failed -> starting -> started -> stopping -> stopped
    """
    def __init__(self, env, *args, *kwargs):
        self.env = env
        self.args = args
        self.kwargs = kwargs

        self.aliases = set() # set of other names I go by
        self.children = set() # set of predicate names that I depend on
        self.parents = set() # set of predicate names that depend on me
        self.depth = 0 # max(parents.depth) + 1

        self.failed = False
        self.solved = False
        self.ret = None

    def check(self, name, ):
        """Initialize myself from self.env.vars, assuming self.check() already passed"""
        raise UnimplementedError()

    def cleanup(self):
        """undo any changes check() made to self.vars"""
        raise UnimplementedError()

    def vars(self):
        """return the dict of system variables"""
        return self.env.vars

    def watch(self, var):
        """Recheck myself if var changes"""
        pass

    def require(self):
        """self.require.pred_name(pred_args)

        I require pred_name(pred_args) to be satisfied.  Add pred to
        self.children and add self to pred.parents

        1. If pred_name(pred_args) is already satisfied, return its value
        2. Instantiate a new predicate pred_name(pred_args) and call pred.check(pred_args)
        3. If pred aliases itself to another defined predicate, return that other one.
        4. call pred.check()

        add pred to self.parents, add self to pred.children, update depth

        """
        return RequireHelper(self)

    def require_pred(self, pred)
        """I require pred, which means pred must be deeper than me"""
        self.children.add(pred.name);
        pred.depth = max(self.depth+1, pred.depth)
        pred.parents.add(self.name)

    def parent_remove(self, pred):
        """Remove pred from self.parents"""
        self.parents.remove(pred.name)

    def unsolved(self):
        self.failed = False
        self.solved = False
        self.ret = None

    def check(self):
        if self.failed:
            env.prune()

        if self.solved:
            return self.ret

        # detach myself from my children.  I may not actually need
        # them any more.  If they end up as orphans, they'll get removed later
        for child_name in self.children:
            child = env.predicates[child_name]
            child.parent_remove(self, env):

        # call my function
        self.ret = env.pred_funcs[self.func_name](env, *self.args, **self.kwargs)
        self.solved = True
        return self.ret

class Env(object):
    def __init__(self, parent=None):
        if parent is None:
            parent = GlobalEnv
        self.parent = parent

        self.solver = None

        # these are copyable because they immutable
        self.pred_funcs = {} # map from func_name -> PredicateFactory

        # all these things should be json-serializable (names only, no
        # complex object references)
        self.vars = {}
        self.predicates = {} # map from pred.name -> predicate

        self.unsolved = set() # set of pred.name
        self.unsolved_sorted = True
        self.pred_stack = [] # stack[-1] is the current predicate

    def clone(self):
        """clone a copy of myself for solving"""
        return self.__class__(self)

    def choose(self, choices):
        return self.solver.choose(choices)

    def prune(self):
        self.solver.prune()

    def predicate_define(self, func_name, func):
        """define a new predicate in self.pred_funcs.  See
        @predicate for defining predicates in GlobalEnv"""
        self.pred_funcs[func_name] = func
        # if there are any predicate instances defined from this func
        # already, mark them as unsolved
        for pred in self.predicates:
            if pred.func_name == func_name:
                self.unsolved_add(pred)

    def predicate_instantiate(self, name, *args, **kwargs):
        # find or create a new instance of a Predicate with args and kwargs
        pred = self.predicates.get(pred_name(name, *args, **kwargs))
        if not pred:
            pred = Predicate(name, args, kwargs)
            self.predicates[pred.name] = pred

        # the current predicate now depends on the new instance
        self.predicates[self.pred_stack[-1]].depends(pred)

        if self.solver:
            # if I'm solving, call the predicate function.
            if not pred.solved:
                self.pred_stack.append(pred)
                pred.check(self)
                self.pred_stack.pop(pred)
        else:
            # otherwise, put it on the unsolved list
            self.unsolved_add(pred)

        return pred.ret

    def __getattr__(self, name):
        """env.mypred(*args, **kwargs) creates a new instance of a predicate named "mypred" with args"""
        return lambda(*args, **kwargs): self.predicate_instantiate(name, args, kwargs)

    def unsolved_add(self, pred):
        pred.unsolved()
        self.unsolved.add(pred.name)
        self.unsolved_sorted = False

    def unsolved_choose(self):
        # choose among all of the predicates at max depth
        if not self.unsolved_sorted:
            self.unsolved = sorted(self.unsolved, key=lambda pred_name: self.predicates[pred_name].depth)
            self.unsolved_sorted = True

        preds = []
        depth = None
        while self.unsolved:
            pred_name = self.unsolved.pop()
            pred = self.predicates[pred_name]
            if depth is None:
                depth = pred.depth
            if pred.depth != depth:
                self.unsolved.append(pred.name)
                break
            preds.append(pred)
        return self.solver.choose(preds)

    def solve(self):
        def solve_fn(solver):
            env = self.clone()
            env.solver = solver
            env._solve_me()
            return env

        for env in solver.solve(solve_fn):
            yield env

    def _solve_me(self):
        while self.unsolved:
            pred = self.unsolved_choose()
            if solver.if_any():
                pred.check(self)
            if solver.else_none():
                self.failed(pred)
                for parent_name in pred.parents:
                    self.unsolved_add(self.predicates[parent_name])

GlobalEnv = Env()

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

def predicate(fn):
    return GlobalEnv.predicate_func(fn)


def host_avaiable(host, tags):
    return host.available.get() and (not tags or (tags in host.tags)):

@predicate
def host(self, name, tags=None, ram=0, cpu=0, disk=0):
    if self.locals.host.exists():
        host = self.vars.hosts[self.locals.host.get()]
        if not host_available(host, tags):
            self.prune()
    else:
        hosts = []
        for host in self.vars.hosts.children():
            if host_available(host, tags) \
               and host.cpu.get() >= cpu \
               and host.ram.get() >= ram \
               and host.disk.get() >= disk \
               hosts.append(host)
        host = self.choose(hosts)
        self.locals.host = host.name
        self.require.reserve(self.name, host.ram, ram)
        self.require.reserve(self.name, host.cpu, cpu)
        self.require.reserve(self.name, host.disk, disk)
        self.watch(host.available)
        self.watch(host.tags)
    return host.name


@predicate
def reserve(self, name, var, amount):
    if var.get() < self.amount:
        self.prune()

    var.put(var.get() - amount)
    self.locals.amount = amount
    self.locals.var_path = var.path

    def cleanup(self):
        if self.locals.amount.exists():
            var = self.vars[self.locals.var_path.get()]
            var.put(var.get() + self.locals.amount.get())
    self.cleanup(cleanup)


@predicate
def qcluster(self, name, build, net, nodes):
    net = self.locals.net.setdefault(net).watch().value()
    nodes = self.getvar("nodes", nodes)
    self.require.qcluster_grandpa(self.name, net)
    for i in range(nodes):
        self.require.qcluster_node(self.name + i, net)

@predicate
def qcluster_grandpa(self, name, build, net):
    ram = self.getvar("grandpa_ram", 4)
    cpu = self.getvar("grandpa_cpu", 2)
    disk = self.getvar("grandpa_disk", 20)
    host = self.require.host(cpu=cpu, ram=ram, disk=disk)
    disks = [
        self.require.qcluster_pentos_disk(host, build)
        self.require.qemu_disk(host, disk)
        ]
    ifaces = [
        self.require.qcluster_tuntap(host, "ipmi"),
        self.require.qcluster_tuntap(host, "data"),
        ]
    self.require.qemu(self.name, host=host, ram=ram, cpu=cpu, disks=disks, ifaces=ifaces)

@predicate
def qcluster_node(self, name, net):
    ram = self.getvar("node_ram", 16)
    cpu = self.getvar("node_cpu", 4)
    disks = self.getvar("node_disks", (40,80))
    host = self.require.host(cpu=cpu, ram=ram, disk=disk)
    self.require.qcluster_node_qemu(self.name, cpu=cpu, ram=ram, disks=disks)

@predicate
def qcluster_node_qemu(self, name, net):
    ipmi_iface = self.require.qcluster_veth(self.name, host, "ipmi")
    self.require.qcluster_node_dhcp(self.name, host=host, iface=ipmi_iface)
    self.require.qcluster_node_ipmisim(self.name, host=host)
    data_if = self.require.qcluster_tuntap(host, "data")
    self.require.qcluster_node_qemu(self.name, cpu=cpu, ram=ram, disks=disks, ifaces=data_if)

@predicate
def qcluster_tuntap(self, name, host, net):
    self.require.qcluster_bridge("ipmi", host=host)

@predicate
def qcluster_veth(self, name, host, net):
    self.require.qcluster_bridge(self.name + "ipmi", host=host)

@predicate
def qcluster_bridge(self, name, net):
    self.require.qcluster_bridge(self.name + "ipmi", host=host)

@predicate
def qemu(self, name, host, cpu, ram, disks, ifaces):
    return self.require.service(self.name, host=host,
                                package="qemu",
                                cmd=("qemu", "-m", ram, "-x", cpu)
                                check="")

@predicate
def host_service(self, host, cmd):
    print("service: %s: %s" % host, cmd)


#-----------
# example

self.hosts_add(100, ram=128, disks=(1000, 1000))

self.qcluster("noel's cluster", 1, 100)
for env2 in self.solve():
    env2.apply_parent()
    break


self.host_remove(host)
for env2 in self.solve():
    break
self.apply(env2)
