import numpy as np
import unittest
from pathlib import Path
import shutil
from texenv import TeXPreprocessor


class TestEmbeddedMacros(unittest.TestCase):
    def setUp(self) -> None:
        self.dir_ = Path(__file__).parent
        self.build_dir = self.dir_ / "build"

        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

    def tearDown(self) -> None:
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

    def test_macro_args(self):
        """
        Simple test with no python macro or pydefs.
        """
        dir_ = Path(__file__).parent

        filepath = dir_ / "self_import.tex"
        texpp = TeXPreprocessor(filepath)
        texpp.run()

        pp_filepath = dir_ / "build/self_import.tex"

        with open(pp_filepath) as pp_file:
            pp_text = pp_file.read()

        pp_filepath = dir_ / "self_import_truth.tex"

        with open(pp_filepath) as truth_file:
            truth_text = truth_file.read()

        # preprocessed file should be identical to truth data
        # print(pp_text)
        # print()
        # print(truth_text)
        self.assertEqual(pp_text, truth_text)


if __name__ == "__main__":
    unittest.main()
