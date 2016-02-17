#! /usr/bin/env python

from setuptools import setup

setup(name='solver',
      version='0.1',
      description='A framework for nondeterministic programming',
      url='http://github.com/noelbk/solver',
      author='Noel Burton-Krahn',
      author_email='noel@burton-krahn.com',
      license='MIT',
      packages=['solver', 'predicates'],
      zip_safe=False,
      test_suite='tests',
      )
