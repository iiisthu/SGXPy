#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os, sys
import sh
import time
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import util

class TestSGXPython(unittest.TestCase):
    def setUp(self):
       self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print "%s: %.3fs" % (self.id(), t)

    def runtest(self, scriptname, exptected, comparefunc = unittest.TestCase.assertEqual, argv = []):
        scriptpath = path.join(util.ScriptDir, scriptname + ".py")
        print "testing script:", scriptpath
        output = util.runner(scriptpath, argv)
        comparefunc(self, output, exptected)

    def test_helloworld(self):
        scriptname = "helloworld"
        self.runtest(scriptname, "Hello, World.\n")

#     def test_tempfile(self):
#         scriptname = "tempfiletest"
#         self.runtest(scriptname, "Hello, World.\n")

#     def test_numpy(self):
#         scriptname = "numpytest"
#         arr = """[[ 0  1  2  3  4]
#  [ 5  6  7  8  9]
#  [10 11 12 13 14]]
# """
#         self.runtest(scriptname, arr, argv = ['-m', '1024M'])

#     def test_thread(self):
#         scriptname = "threadtest"

#         def assertfunc(obj, output, exptected):
#             obj.assertEqual(output.count("Current thread is: "), 8)
#             obj.assertEqual(output.count("main thread"), 2)

#         self.runtest(scriptname, None, assertfunc, ['-m', "1024M", '-t', 30])

#     def test_fork(self):
#         scriptname = "forktest"
#         output = """before the fork,my PID is 1
# Hello from the child. My PID is 2
# Hello from both of us.
# Hello from the parent. My PID is 1
# Hello from both of us.
# """
#         self.runtest(scriptname, output)

#     def test_execv(self):
#         scriptname = "execvtest"
#         output = sh.uname()
#         self.runtest(scriptname, output)

#     def test_popen(self):
#         scriptname = "popentest"
#         output = sh.uname('-p').stdout + "\n"
#         self.runtest(scriptname, output, argv = ['-u'])

#     def test_platform(self):
#         scriptname = "platformtest"
#         output = "x86_64\n"
#         self.runtest(scriptname, output, argv = ['-u'])

#     def test_reademptypipe(self):
#         scriptname = "reademptypipetest"
#         output = "text = \n"
#         self.runtest(scriptname, output)

#     def test_numpytestfile(self):
#         argv = ['-u', '--', '-m', 'numpy.core.tests.test_errstate', '-A', 'not slow', '--verbosity', 2]
#         print util.runner(None, argv)

#     def test_subproctest(self):
#         scriptname = "subproctest"
#         output = "Linux\n"
#         self.runtest(scriptname, output)

#     def test_zipfilesize(self):
#         scriptname = "zipfilesizetest"
#         output = "file size: 192\n"
#         self.runtest(scriptname, output)


if __name__ == '__main__':
    unittest.main()

