import numpy as np
import unittest
from pathlib import Path
import shutil
from texenv import TeXPreprocessor


class TestPyDefs(unittest.TestCase):
    def setUp(self) -> None:
        self.dir_ = Path(__file__).parent
        self.build_dir = self.dir_ / "build"

        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

    def tearDown(self) -> None:
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

    def test_pydef(self):
        dir_ = Path(__file__).parent

        filepath = dir_ / "pydefs.tex"
        texpp = TeXPreprocessor(filepath)
        texpp.run()

        pp_filepath = dir_ / "build/pydefs.tex"

        with open(pp_filepath) as pp_file:
            pp_text = pp_file.read()

        with open(filepath) as in_file:
            in_text = in_file.read()

        desired_output = ""
        for ln in in_text.split("\n"):
            if "\pydef" not in ln:
                desired_output += ln + "\n"
            else:
                desired_output += "\n"

        desired_output = desired_output.replace(r"\SIMPLEDEF", "simpledef")
        desired_output = desired_output.replace(
            r"\DEF_WITH_UNDER_SCORE", "def with spaces and =]{}"
        )

        self.assertEqual(desired_output[:-1], pp_text)

        # pydefs can't have new lines, so lines should map one to one.
        np.testing.assert_array_equal(texpp._syntex_map, np.arange(1, 12))


if __name__ == "__main__":
    unittest.main()
