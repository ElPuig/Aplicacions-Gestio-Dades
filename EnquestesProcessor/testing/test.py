import unittest
import os
import sys
import shutil

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

    def test_clean_files(self):        
        worker = Worker()

        #When done, the folders must exists but output and temp must be empty        
        if os.path.exists(worker.OUTPUT_FOLDER):
            shutil.rmtree(worker.OUTPUT_FOLDER)

        if os.path.exists(worker.TEMP_FOLDER):
            shutil.rmtree(worker.TEMP_FOLDER)
        
        #It will be called twice: the firs one to check if the folders has been created
        worker.clean_files()
        self.assertEqual(os.path.exists(worker.OUTPUT_FOLDER), True)
        self.assertEqual(os.path.exists(worker.TEMP_FOLDER), True)
        
        #It will be called twice: the second one to check if the folders are empty     
        #os.mknod(worker.REPORT_FILE_ADM) #not portable, only works on UNIX
        open(worker.REPORT_FILE_ADM, 'ab', 0).close()
        open(worker.REPORT_FILE_INF, 'ab', 0).close()
        open(worker.REPORT_FILE_CENTRE, 'ab', 0).close()
        open(worker.RESULT_FILE_ANSWERS, 'ab', 0).close()
        open(worker.RESULT_FILE_ERRORS, 'ab', 0).close()
        open(worker.RESULT_FILE_STATISTICS, 'ab', 0).close()
        open(worker.RESULT_FILE_STUDENTS_WITH_AVALUATED_MP, 'ab', 0).close()
        open(worker.TMP_ANONYMIZED_STUDENT_ANSWERS, 'ab', 0).close()
        open(worker.TMP_FILE_ANSWERS, 'ab', 0).close()
        open(worker.RECORD_FILE_ERRORS, 'ab', 0).close()
        open(worker.RECORD_FILE_ANSWERS, 'ab', 0).close()
        open(worker.SOURCE_FILE_STUDENTS_WITH_MP, 'ab', 0).close()
        open(worker.SOURCE_FILE_STUDENT_ANSWERS, 'ab', 0).close()

        worker.clean_files()
        path, dirs, files = next(os.walk(worker.OUTPUT_FOLDER))
        self.assertEqual(len(files), 0)

        path, dirs, files = next(os.walk(worker.TEMP_FOLDER))
        self.assertEqual(len(files), 0)

    def test_anonymize_answers(self):
        #TODO: this test must be executed for different input files   
        self.assertEqual(0, 0)     

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