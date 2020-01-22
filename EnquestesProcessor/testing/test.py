import unittest
import os, sys

"""
The current project follows this structure, which I found logic and comfortable:
- EnquestesProcessor.py (main console app: runnable as a script)
    --core (core package)
        --terminal.py (console output system: not runnable as a script)
        --worker.py (main processor code: not runnable as a script)
    --testing (test package)
        --test.py (main processor testing code: runnable as a script)

The following line is needed in order to use the "core" package from here (I prefer to mantain this code isolated).
"""
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))  
from core.worker import *

class EnquestesProcessorTest(unittest.TestCase):

    def test_anonymize_answers(self):
        #TODO: this test must be executed for different input files
        worker = Worker()
        id_to_email_and_name_dict = worker.anonymize_answers()
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

if __name__ == '__main__':
    unittest.main(verbosity=2)