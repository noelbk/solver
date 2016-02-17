#! /usr/bin/env python
import unittest

from predicates import varstore

class TestVarstore(unittest.TestCase):
    def test_varstore(self):
        v = varstore.VarStore()
        r = v.top()

        updates = []
        watch_updates = lambda path: updates.append(path)

        val, watch1 = r.watch(watch_updates)

        self.assertEqual([], updates)
        self.assertEqual([], list(r.ls()))

        d2 = r.d1.d2

        self.assertEqual([], updates)
        self.assertEqual([], list(r.ls()))

        d2.v1 = 1
        self.assertEqual(1, r.d1.d2.v1.get())
        self.assertEqual([("d1",)], [p.path for p in r.ls()])
        self.assertEqual([()], updates)
        updates = []

        r.d1.d2.v2 = 2
        self.assertEqual(2, d2.v2.get())
        self.assertEqual([], updates)
        updates = []

        val, watch2 = d2.v1.watch(watch_updates)
        d2.v1 = 2
        self.assertEqual(2, r.d1.d2.v1.get())
        self.assertEqual([("d1", "d2", "v1")], updates)
        updates = []

        d2.v1.unwatch(watch2)
        d2.v1 = 3
        self.assertEqual(3, r.d1.d2.v1.get())
        self.assertEqual([], updates)

        self.assertEqual(['v1', 'v2'], sorted([d.name() for d in d2.ls()]))

        # get(key) === .key.get()
        self.assertEqual(3, d2.get('v1'))

        # put(key, val) === .key.put(val)
        d2.put('v1', 4)
        self.assertEqual(4, d2.v1.get())

        # get(key) returns default
        self.assertEqual(None, d2.get('vx'))
        self.assertEqual(2, d2.get('vx', 2))

        # get() throws KeyError
        ex = None
        try:
            d2.vx.get()
        except KeyError as e:
            ex = e
        assert isinstance(ex, KeyError)
