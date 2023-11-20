from pathlib import Path
from time import time
import sys
import importlib
import os
from typing import Callable, Union, List
from io import BytesIO
import numpy as np
import pickle

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
        self._syntex_map_path = build_dir / (self._infile.stem + ".syncmap")

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

        self._syntex_map = []

    def write(self, data: str):
        """Write decoded data to the working output file."""
        self._out_stream.write(data.encode())

        # map the preprocessed line number back to the corresponding line in the original file
        for i in range(data.count("\n")):
            # the input has already seen the new line and incremented the line num, so use the last number
            self._syntex_map.append(self._input_line_num - 1)

    def syntax_error(self, msg: str):
        raise SyntaxError("Error on line {}. {}".format(self._input_line_num, msg))
    
    def advance(self, stream=None):
        """Returns the next character in the input stream and advances the current position in the stream."""
        if stream is None:
            stream = self._in_stream

        ch = stream.read(1).decode("utf-8")
        if ch == "\n" and stream == self._in_stream:
            self._input_line_num += 1
        return ch

    def advance_if(self, condition: Callable, stream = None):
        """
        Returns the next character in the input stream if condition returns True. Otherwise, returns None and
        does not advance the stream.
        """
        if stream is None:
            stream = self._in_stream
        
        ch = stream.read(1).decode("utf-8")

        if condition(ch):
            # if condition is met, advance the line number if character was new line and return character
            if ch == "\n" and stream == self._in_stream:
                self._input_line_num += 1
            return ch

        else:
            # if condition is not met, revert the stream back to the previous character. The only exception is if the
            # stream reached the end of the file, in which case the character will be the empty string
            if len(ch):
                stream.seek(-1, os.SEEK_CUR)
            return None

    def advance_while(self, condition: Callable, stream = None):
        """
        Returns the next characters in the input stream up until the condition returns False.
        """

        if stream is None:
            stream = self._in_stream

        ch = stream.read(1).decode("utf-8")
        read_str = ""
        while condition(ch):
            if ch == "\n" and stream == self._in_stream:
                self._input_line_num += 1
            read_str += ch
            ch = stream.read(1).decode("utf-8")

        # the current character does not meet the condition, so rewind the stream so this character is the next one that is read.
        if len(ch):
            stream.seek(-1, os.SEEK_CUR)

        return read_str

    def peek(self, n: int = 1, stream=None):
        """Returns the next n characters in the input stream without advancing the current position."""
        if stream is None:
            stream = self._in_stream

        n_ch = stream.read(n).decode("utf-8")
        stream.seek(-n, os.SEEK_CUR)
        return n_ch

    def skip_whitespace(self, allow_break=False):
        """
        Moves the default input stream cursor to the first non-whitespace character.
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

    def read_macro_name(self, stream=None):
        """
        Reads the alpha-numeric characters after a backslash. Stream must be immediately after the backslash.
        """
        name = ""
        n_ch = self.advance_if(lambda x: x.isalnum() or x == "_", stream)
        while n_ch:
            name += n_ch
            n_ch = self.advance_if(lambda x: x.isalnum() or x == "_", stream)

        return name

    def call_pymacro(self, module_name: str, method_name: str, stream=None):
        """
        Reads the arguments for a pymacro, and returns the replacement text. Input stream should be
        immediately after the method name (at the [ or { character before the arguments).
        """
        args = []
        kwargs = {}

        # look for arguments enclosed with {}
        while self.peek(stream=stream) == "{":
            # leave off the first character which will be "{"
            self.advance(stream)
            args.append(self.parse_until("}", stream))
            # the cursor here is pointing at the delimiter, advance cursor so the next one we read is the character after "}".
            self.advance(stream)

        # look for kwargs enclosed with []
        if self.peek(stream=stream) == "[":
            # leave off the first character which will be "["
            self.advance(stream)

            delimiter = " "

            while len(delimiter) and delimiter != "]":
                # get string up until one of "]", "," or "="
                content = self.parse_until(delimiter=["]", ",", "="], stream=stream)

                # get the delimiter that stopped the parsing
                delimiter = self.advance(stream)

                # if stopped by =, the previously read content is the key. Read the value after the = sign
                if delimiter == "=":
                    value = self.parse_until(delimiter=["]", ","], stream=stream)
                    kwargs[content.strip()] = value.strip()
                    delimiter = self.advance(stream)
                # if stopped by a comma, save the content as an arg and continue to the next iteration
                elif delimiter in [",", "]"]:
                    args.append(content.strip())

        # search and replace macros in all arguments and kwarg values. Create a flat list of all arguments and kwarg values.
        value_list = list(args) + list(kwargs.values())
        # iterate through each one and make the macro replacments
        for i, value in enumerate(value_list):
            v_replaced = ""
            v_ch = " "
            arg_stream = BytesIO(value.encode('utf-8'))

            while len(v_ch):
                # step through value looking for backslashes
                v_ch = self.advance(arg_stream)

                if v_ch == self.BACKSLASH:
                    # get the name of the macro after the backslash
                    mname = self.read_macro_name(arg_stream)
                    # if we found a macro, get the replacement text. This will return the backslash with the macro name if the 
                    # macro is not recognized.
                    v_replaced += self.get_macro_replacement(mname, arg_stream)
                else:
                    v_replaced += v_ch

            # update kwarg with replaced text
            if i >= len(args):
                key = list(kwargs.keys())[i - len(args)]
                kwargs[key] = v_replaced
            # update arg with replaced text
            else:
                args[i] = v_replaced    

        # find the method pointer from the module and method name
        module = self._imported_modules[module_name]
        lib = importlib.__import__(module)
        method = getattr(lib, method_name)

        # call the method with the arguments and kwargs and return the result
        return method(*args, **kwargs)
    
    def parse_until(self, delimiter: Union[str, List[str]], stream=None):
        """
        Returns the content up to any characters contained in delimiter, while allowing the delimiters to be escaped by
        enclosing the content in brackets.
        """

        delimiter = [delimiter] if isinstance(delimiter, str) else delimiter
        nested_bracket = 0
        nested_sq_bracket = 0
        arg_str = ''
        a_ch = ' '

        while len(a_ch):
            a_ch = self.peek(stream=stream)
            if a_ch == "{":
                nested_bracket += 1
            elif a_ch == "}" and nested_bracket > 0:
                nested_bracket -= 1
            elif a_ch == "[":
                nested_sq_bracket += 1
            elif a_ch == "]" and nested_sq_bracket > 0:
                nested_sq_bracket -= 1

            elif a_ch in delimiter and (nested_bracket == 0 and nested_sq_bracket == 0):
                break

            arg_str += self.advance(stream)

        if nested_bracket or nested_sq_bracket:
            self.syntax_error("Missing closing bracket.")

        return arg_str

    def get_macro_replacement(self, mname, stream=None):
        """
        Returns the replacement text for the macro. Stream cursor must be immediately after the macro name.
        """

        if mname in self._imported_modules.keys():
            # expect the method name immediately after the module or alias name, i.e. "\pkg\example_method"
            bkslash = self.advance_if(lambda x: x == self.BACKSLASH, stream)

            if bkslash is None:
                self.syntax_error(
                    "Expected method name after python module: {}.".format(mname)
                )

            method_name = self.read_macro_name(stream)

            if method_name is None:
                self.syntax_error(
                    "Expected method name after python module: {}.".format(mname)
                )

            # call the python method and get the replacement string
            return self.call_pymacro(mname, method_name, stream)

        elif mname in self._defined_macros.keys():
            # get the replacement text in place of the defined macro
            return self._defined_macros[mname]

        else:
            # preprocessor does not recognize the macro name
            return "\\" + mname

    def run(self) -> Path:
        self.reset()

        g_ch = " "
        comment = False
        while len(g_ch):
            g_ch = self.advance()

            if g_ch == self.COMMENT:
                comment = True

            if g_ch == self.NEWLINE:
                comment = False

            if comment or g_ch != self.BACKSLASH:
                self.write(g_ch)
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
                    self.advance_while(lambda x: x != "\\")
                    # skip the backslash
                    self.advance()
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
                self._defined_macros[varname] = self.advance_while(
                    lambda x: x != self.NEWLINE
                ).strip()

            else:
                output = self.get_macro_replacement(mname)
                self.write(output)

        self._in_stream.close()
        self._out_stream.close()
        
        # add the last line to the mapping manually since there is no new line character on the last line to trigger the map write
        self._syntex_map.append(self._input_line_num)

        with open(self._syntex_map_path, "wb") as f:
            pickle.dump(self._syntex_map, f)
        # np.save(self._syntex_map_path, np.array(self._syntex_map))

        return self._outfile

