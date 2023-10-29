from pathlib import Path
from time import time
import sys
import importlib
import os
import subprocess
import shutil
import click
import re
from typing import Callable, Union, List

class TeXPreprocessor(object):
    """ "
    Searches a .tex file for all macro calls that are defined in Python and replaces it with the
    returned string of the Python method.
    """

    EMPTY = ""
    COMMENT = "%"
    NEWLINE = "\n"
    BACKSLASH = "\\"

    def __init__(self, filepath: Path):
        """
        Parameters:
        -----------
        filepath: Path | str
            file path of .tex file to parse.
        """
        self._infile = Path(filepath).resolve()

        build_dir = Path(self._infile).parent / "build"

        if not build_dir.is_dir():
            os.mkdir(build_dir)

        self._outfile = build_dir / (self._infile.stem + ".tex")

        self.reset()

        # add current directory to path so processor can manually import modules
        sys.path.append(str(Path.cwd()).replace("\\", r"\\"))

    def reset(self):
        """
        Resets the stream to the beginning of the input file.
        """
        self._in_stream = open(self._infile, "rb")
        self._out_stream = open(self._outfile, "wb+")
        self._imported_modules = {}
        self._defined_macros = {}

        self._input_line_num = 1
        self._output_line_num = 1

    def advance(self):
        """Returns the next character in the input stream and advances the current position in the stream."""
        ch = self._in_stream.read(1).decode("utf-8")
        if ch == "\n":
            self._input_line_num += 1
        return ch

    def advance_if(self, condition: Callable):
        """
        Returns the next character in the input stream if condition returns True. Otherwise, returns None and
        does not advance the stream.
        """
        ch = self._in_stream.read(1).decode("utf-8")

        if condition(ch):
            # if condition is met, advance the line number if character was new line and return character
            if ch == "\n":
                self._input_line_num += 1
            return ch

        else:
            # if condition is not met, revert the stream back to the previous character. The only exception is if the
            # stream reached the end of the file, in which case the character will be the empty string
            if len(ch):
                self._in_stream.seek(-1, os.SEEK_CUR)
            return None

    def advance_until(self, condition: Callable):
        """
        Returns the next characters in the input stream up until the condition returns True.
        """

        ch = self._in_stream.read(1).decode("utf-8")
        read_str = ""
        while condition(ch):
            read_str += ch
            ch = self._in_stream.read(1).decode("utf-8")

        # the current character does not meet the condition, so rewind the stream so this character is the next one that is read.
        if len(ch):
            self._in_stream.seek(-1, os.SEEK_CUR)

        return read_str

    def peek(self, n: int = 1):
        """Returns the next n characters in the input stream without advancing the current position."""
        n_ch = self._in_stream.read(n).decode("utf-8")
        self._in_stream.seek(-n, os.SEEK_CUR)
        return n_ch

    def write(self, data: str):
        """Write decoded data to the working output file."""
        self._out_stream.write(data.encode())

    def syntax_error(self, msg: str):
        raise SyntaxError("Error on line {}. {}".format(self._input_line_num, msg))

    def skip_whitespace(self, allow_break=False):
        """
        Moves the input stream cursor to the first non-whitespace character.
        """

        if allow_break:
            condition = lambda x: x.isspace()
        else:
            condition = lambda x: x.isspace() and x != "\n"

        skipped_str = ""
        s_ch = self.advance_if(condition)

        while s_ch:
            skipped_str += skipped_str
            s_ch = self.advance_if(condition)

        return skipped_str

    def read_macro_name(self):
        """
        Reads the alpha-numeric characters after a backslash. Stream must be immediately after the backslash.
        """
        name = ""
        n_ch = self.advance_if(lambda x: x.isalnum() or x == "_")
        while n_ch:
            name += n_ch
            n_ch = self.advance_if(lambda x: x.isalnum() or x == "_")

        return name

    def call_pymacro(self, module_name: str, method_name: str):
        """
        Reads the arguments for a pymacro, and returns the replacement text. Input stream should be
        immediately after the method name (at the [ or { character before the arguments).
        """
        args = []
        kwargs = {}

        # look for arguments enclosed with {}
        while self.peek() == "{":
            # leave off the first character which will be "{"
            self.advance()
            args += self.parse_until("}")
            # the cursor here is pointing at the delimiter, advance cursor so the next one we read is the character after "}".
            self.advance()

        # look for kwargs enclosed with []
        if self.peek() == "[":
            # leave off the first character which will be "["
            self.advance()

            while delimiter != "]":
                # get string up until one of "]", "," or "="
                content = self.parse_until(delimiter=["]", ",", "="])

                # get the delimiter that stopped the parsing
                delimiter = self.advance()

                # if stopped by =, the previously read content is the key. Read the value after the = sign
                if delimiter == "=":
                    value = self.parse_until(delimiter=["]", ","])
                    kwargs[content] = value
                    delimiter = self.advance()
                # if stopped by a comma, save the content as a arg and continue to the next iteration
                if delimiter == ",":
                    args += content
                    
        module = self._imported_modules[module_name]

        lib = importlib.__import__(module)
        method = getattr(lib, method_name)

        return method(*args, **kwargs)
    
    def parse_until(self, delimiter: Union[str, List[str]]):
        """
        Returns the content up to any characters contained in delimiter, while allowing the delimiters to be escaped by
        enclosing the content in brackets.
        """

        delimiter = [delimiter] if isinstance(delimiter, str) else delimiter
        nested_bracket = 0
        arg_str = ''
        a_ch = ' '

        while len(a_ch):
            
            a_ch = self.peek()
            if a_ch == "{":
                nested_bracket += 1
            if a_ch == "}" and nested_bracket > 0:
                nested_bracket -= 1
    
            if a_ch in delimiter and nested_bracket == 0:
                break
            else:
                arg_str += self.advance()

        if nested_bracket:
            self.syntax_error("Missing closing bracket.")

        return arg_str
    
    def parse_pdflatex_error(self, output):
        lines = output.split("\n")

        error_msg = ""
        error_ln = int
        error_src = ""

        for ln in lines:
            if len(ln) and ln[0] == "!":
                error_msg = ln[1:].strip()

            m = re.match("^l.(\d+)", ln)

            if m:
                error_ln = int(m.group(1))
                error_src = ln[len(m.group(0)) :].strip()
                break

        return dict(msg=error_msg, line=error_ln, src=error_src)

    def run(self):
        self.reset()

        stime = time()
        g_ch = " "
        comment = False
        while len(g_ch):
            if g_ch == self.COMMENT:
                comment = True

            if g_ch == self.NEWLINE:
                comment = False

            if comment or g_ch != self.BACKSLASH:
                self.write(g_ch)
                g_ch = self.advance()
                continue

            # at this point, the current character is a backslash in a non-comment line.
            # get the name of the macro after the backslash
            mname = self.read_macro_name()

            if mname == "import":
                # expect another macro call immediately after the \import call, i.e. \import\example_pkg
                bkslash = self.advance_if(lambda x: x == self.BACKSLASH)

                if bkslash is None:
                    self.syntax_error("Expected module name after import statement.")

                module = self.read_macro_name()

                if module is None:
                    self.syntax_error("Expected module name after import statement.")

                # at this point we have read up to "\import\example_pkg". This may be the entire import statement
                # but we also allow the module name to be aliased with the syntax: "\import\example_pkg as \pkg"
                alias = module
                self.skip_whitespace()
                if self.peek(2) == "as":
                    self.skip_whitespace()
                    alias = self.read_macro_name()

                # save the imported module name under the alias name. If no alias was given, the key name is the
                # same as the module.
                self._imported_modules[alias] = module

            elif mname == "pydef":
                # expect another macro call immediately after the \pydef call, i.e. \pydef\test
                bkslash = self.advance_if(lambda x: x == self.BACKSLASH)

                if bkslash is None:
                    self.syntax_error("Expected variable name after pydef statement.")

                varname = self.read_macro_name()

                if varname is None:
                    self.syntax_error("Expected variable name after pydef statement.")

                # at this point we have read up to "\pydef\test". Now read the assignment string for this variable.
                # This string can be anything and is a direct replacement for every instance of "\pydef\test".
                self._defined_macros[varname] = self.advance_until(
                    lambda x: x != self.NEWLINE
                )

            elif mname in self._imported_modules.keys():
                # expect the method name immediately after the module or alias name, i.e. "\pkg\example_method"
                bkslash = self.advance_if(lambda x: x == self.BACKSLASH)

                if bkslash is None:
                    self.syntax_error(
                        "Expected method name after python module: {}.".format(mname)
                    )

                method_name = self.read_macro_name()

                if method_name is None:
                    self.syntax_error(
                        "Expected method name after python module: {}.".format(mname)
                    )

                # call the python method and get the replacement string
                output = self.call_pymacro(mname, method_name)
                self.write(output)

            elif mname in self._defined_macros.keys():
                # write the replacement text in place of the defined macro
                self.write(self._imported_modules[mname])

            else:
                # preprocessor does not recognize the macro name, so just pass through to the output stream.
                # include the backslash.
                self.write("\\" + mname)

        self._in_stream.close()
        self._out_stream.close()

        proc = subprocess.run(
            'pdflatex --synctex=1 --interaction=nonstopmode --halt-on-error --output-directory="{}" {}'.format(
                build_dir, outfile
            ),
            stdout=subprocess.PIPE,
        )

        if proc.returncode:
            err = self.parse_pdflatex_error(proc.stdout.decode("utf-8"))
            raise RuntimeError(
                "pdfTEX Error on line: {}. {} {}\n {}\n See full log at: {}".format(
                    err["line"],
                    err["msg"],
                    err["src"],
                    infile,
                    build_dir / (infile.stem + ".log"),
                )
            )

        else:
            gen_pdf = build_dir / (infile.stem + ".pdf")
            gen_syn = build_dir / (infile.stem + ".synctex.gz")

            out_pdf = infile.with_suffix(".pdf")
            out_syn = infile.with_suffix(".synctex.gz")

            shutil.copyfile(gen_pdf, out_pdf)
            shutil.copyfile(gen_syn, out_syn)

        print("Output PDF written to {}".format(out_pdf))
        return proc

    # out = subprocess.run("\"C:/Program Files/SumatraPDF/SumatraPDF-3.4.6-64.exe\" \"{}\" -inverse-search \"\"C:/ProgramData/Notepad++/notepad++.exe\" -n%l \"%f\"\"".format(out_pdf), shell=True)


@click.command()
@click.argument("filepath")
def cli(filepath):
    texpp = TeXPreprocessor()
    texpp.run(filepath)


if __name__ == "__main__":
    # cli()
    texpp = TeXPreprocessor()
    out = texpp.run(Path(__file__).parent / "../tests/test.tex")
