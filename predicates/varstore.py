#! /usr/bin/env python

ABSENT = object()


class VarStore(object):
    def __init__(self):
        self.root = {}
        self.watches = {}

    def top(self):
        return VarPath(self)

    def _traverse(self, path, mkdirs=False):
        if not path:
            return self.root, None

        last = path[-1]
        curpath = ()
        d = self.root
        for k in path[:-1]:
            assert k, "empty path in %s" % path
            if k not in d:
                if mkdirs:
                    d[k] = {}
                    self._check_watch(curpath)
            elif not isinstance(d[k], dict):
                raise KeyError()
            d = d[k]
            curpath = curpath + (k,)
        return d, last

    def clear(self, path):
        d, k = self._traverse(path)
        if k in d:
            del d[k]

    def rm(self, path):
        d, k = self._traverse(path)
        del d[k]
        self._check_watch(path)

    def mkdir(self, path):
        d, k = self._traverse(path, True)
        if k not in d:
            d[k] = {}
            self._check_watch(path)
        elif not isinstance(d[k], dict):
            raise KeyError("path %s already exists as %s" % (path, d[k]))

    def ls(self, path):
        if not path:
            return self.root.keys()
        d, k = self._traverse(path)
        return d[k].keys()

    def get(self, path):
        if not path:
            return self.root
        d, k = self._traverse(path)
        return d[k]

    def put(self, path, val):
        d, k = self._traverse(path, mkdirs=True)
        d[k] = val
        self._check_watch(path)

    def _check_watch(self, path):
        for watch in self.watches.get(path, []):
            watch.func(path)

    def watch(self, path, func):
        val = self.get(path)
        watch = VarWatch(path, func)
        if path not in self.watches:
            self.watches[path] = []
        self.watches[path].append(watch)
        return (val, watch)

    def unwatch(self, watch):
        self.watches.get(watch.path, {}).remove(watch)


class VarWatch(object):
    def __init__(self, path, func):
        self.path = path
        self.func = func


class VarPath(object):
    def __init__(self, keystore, path=None):
        vars(self)["keystore"] = keystore
        if path is None:
            path = ()
        else:
            if not isinstance(path, tuple):
                path = (path,)
        vars(self)["path"] = path

    def __getitem__(self, name):
        """allows path["name1"]["name2"]"""

    def __putitem__(self, name, val):
        """allows path["name"] = val"""
        return self.child(name).put(val)

    def __getattr__(self, name):
        """allows path.name1.name2"""
        return self.child(name)

    def __setattr__(self, name, val):
        """allows path.name = val"""
        return self.child(name).put(val)

    def child(self, name):
        return VarPath(self.keystore, self.path + (name,))

    def ls(self):
        for name in self.keystore.ls(self.path):
            yield self.child(name)

    def put(self, key, value=ABSENT):
        if value is ABSENT:
            return self.keystore.put(self.path, key)
        return self.child(key).put(value)

    def get(self, name=ABSENT, default=None):
        if name is not ABSENT:
            try:
                return self.child(name).get()
            except KeyError:
                return default
        return self.keystore.get(self.path)

    def name(self):
        return self.path[-1]

    def watch(self, func):
        return self.keystore.watch(self.path, func)

    def unwatch(self, watch):
        return self.keystore.unwatch(watch)
