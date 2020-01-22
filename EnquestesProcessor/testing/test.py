import unittest
from ..core import core
 
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