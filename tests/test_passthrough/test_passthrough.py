import numpy as np
import unittest
from pathlib import Path
import shutil
from texenv import TeXPreprocessor

class TestPassThrough(unittest.TestCase):

    def setUp(self) -> None:
        self.dir_ = Path(__file__).parent
        self.build_dir = self.dir_ / "build"

        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

    def tearDown(self) -> None:
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
    
    def test_passthrough(self):
        """
        Simple test with no python macro or pydefs.
        """
        dir_ = Path(__file__).parent

        filepath = dir_ / "passthrough.tex"
        texpp = TeXPreprocessor(filepath)
        texpp.run()

        pp_filepath = dir_ / "build/passthrough.tex"

        with open(pp_filepath) as pp_file:
            pp_text = pp_file.read()

        with open(filepath) as in_file:
            in_text = in_file.read()

        # preprocessed file should be identical to orginal
        self.assertEqual(pp_text, in_text)

        # lines in the output should map 1:1 back to the input
        sync_pp = np.load(self.build_dir / "passthrough.syncmap.npy")
        np.testing.assert_array_equal(sync_pp, np.arange(1, 11))

if __name__ == '__main__':
    unittest.main()