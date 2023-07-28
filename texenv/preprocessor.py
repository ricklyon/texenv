from pathlib import Path
from time import time
import sys
import importlib
import os
import subprocess
import shutil
import click
import re

class TeXPreprocessor(object):
    """"
    Searches a .tex file for all macro calls that are defined in Python and replaces it with the 
    returned string of the Python method.
    """
    EMPTY = ''
    COMMENT= '%'
    NEWLINE= '\n'

    def __init__(self):
        self._in_stream  = None
        self._out_stream = None
        self._imported_modules = {}
        self._defined_macros = {}

    def advance(self, n:int=1):
        """Returns the next n characters in the input stream and advances the current position."""
        ch = self._in_stream.read(n).decode('utf-8')
        return ch
    
    def peek(self, n:int=1):
        """Returns the next n characters in the input stream without advancing the current position."""
        n_ch = self.advance(n)
        self.rewind(n)
        return n_ch

    def rewind(self, n:int=1):
        """Moves the current position of the input stream to the left by n characters."""
        self._in_stream.seek(-n, os.SEEK_CUR)

    def write(self, data):
        self._out_stream.write(data.encode())


    def parse_argument(self):

        argument = ''
        nested_bracket = 0
        arg_ch = ' '
        key = None

        while len(arg_ch):
            if arg_ch == '{':
                nested_bracket += 1
            elif arg_ch == '}':
                nested_bracket -= 1
            elif (arg_ch == ',' or arg_ch == ']') and nested_bracket <=0:
                self.rewind()
                break

            if arg_ch == '=':
                key = argument.strip()
                argument = ''

            mname = self.get_macro_name()
            
            if mname in self._imported_modules.keys():

                output = self.get_macro_content(mname)
                argument += output

            elif mname in self._defined_macros.keys():
                argument += self._defined_macros[mname]

            elif mname:
                argument += '\\' + mname

            elif arg_ch != '}' and arg_ch != '{' and arg_ch != '=':
                argument += arg_ch

            arg_ch = self.advance()

        return key, argument.strip()

    def parse_macro_args(self):
        """
        Returns the argument list and kwargs passed into a pytex method. Stream
        must be at the end of the pytex method name.
        """
        args = []
        kwargs = {}
        self.skip_whitespace(allow_break=True)

        m_ch = self.advance()

        # return if no enclosing bracket around arguments
        if m_ch != '[':
            return args, kwargs
        
        # get macro arguments
        key, arg = self.parse_argument()
        if key is None:
            args.append(arg)
        else:
            kwargs[key] = arg

        m_ch = self.advance()
        while m_ch == ',':

            key, arg = self.parse_argument()
            if key is None:
                args.append(arg)
            else:
                kwargs[key] = arg

            m_ch = self.advance()
        
        if m_ch != ']':
            raise ValueError('Unbalanced closing bracket around macro arguments.')

        return args, kwargs


    def skip_whitespace(self, allow_break=False, trim:bool=False):
        # read whitespace up to first non-whitespace character

        ch = self.advance()

        read_i = 1
        while ch.isspace():
            if ch == '\n' and not allow_break:
                break
            if not trim:
                self.write(ch)

            ch = self.advance()
            read_i += 1

        if len(ch):
            self.rewind()
        
    def get_macro_name(self, trim_whitespace=False):
        """
        Returns macro name. Stream must be at the first character of name (after backslash)
        """
        self.skip_whitespace(trim=trim_whitespace)
        n_ch = self.advance()

        if n_ch != '\\':
            if len(n_ch):
                self.rewind()
            return None

        name = ''
        n_ch = self.advance()
        while n_ch.isalpha():
            name += n_ch
            n_ch = self.advance()

        if len(n_ch):
            self.rewind()
        return name

    def get_def_value(self):
        """
        Returns the value assigned to a pytex variable
        """
        value = ''
        n_ch = self.advance()

        while n_ch != '\n' and len(n_ch):
            value += n_ch
            n_ch = self.advance()

        if len(n_ch):
            self.rewind()
        return value.strip()

    def get_macro_content(self, mname):
        module = self._imported_modules[mname]

        method_name = self.get_macro_name(trim_whitespace=True)
        if method_name is None:
            raise ValueError('expected method name after imported module')
        
        lib = importlib.__import__(module)
        method = getattr(lib, method_name)

        # get macro arguments
        args, kwargs = self.parse_macro_args()

        return method(*args, **kwargs)

    def parse_pdflatex_error(self, output):
        lines = output.split('\n')

        error_msg = ''
        error_ln = int
        error_src = ''

        for ln in lines:
            if len(ln) and ln[0] == '!':
                error_msg = ln[1:].strip()

            m = re.match('^l.(\d+)', ln) 

            if m:
                error_ln = int(m.group(1))
                error_src = ln[len(m.group(0)):].strip()
                break

        return dict(msg=error_msg, line=error_ln, src=error_src)

    def run(self, filepath):
        infile = Path(filepath).resolve()

        build_dir = Path(infile).parent / 'build'

        if not build_dir.is_dir():
            os.mkdir(build_dir)

        outfile = build_dir / (infile.stem + '.tex')

        self._in_stream  = open(infile, "rb")
        self._out_stream = open(outfile, "wb+")
        self._imported_modules = {}
        self._defined_macros = {}

        stime = time()
        g_ch = b' '
        comment = False
        while len(g_ch):

            if g_ch == self.COMMENT:
                comment = True

            if g_ch == self.NEWLINE:
                comment = False

            if comment:
                if g_ch != self.COMMENT:
                    self.write(g_ch)
                g_ch = self.advance()
                continue

            mname = self.get_macro_name(trim_whitespace=False)

            if mname is None:
                g_ch = self.advance()
                self.write(g_ch)
                
            elif mname == 'import':
                module = self.get_macro_name(trim_whitespace=True)

                if module is None:
                    raise ValueError('expected module name after import statement.')
                
                # check for alias
                self.skip_whitespace(trim=True)
                
                alias_as = self.advance(2)
                alias = module
                if alias_as == 'as':
                    alias = self.get_macro_name(trim_whitespace=True)
                else:
                    self.rewind(2)
                self._imported_modules[alias] = module

            elif mname == 'pydef':
                varname = self.get_macro_name(trim_whitespace=True)

                if varname is None:
                    raise ValueError('expected variable name after pydef statement.')
                
                self._defined_macros[varname] = self.get_def_value()

            elif mname in self._imported_modules.keys():

                output = self.get_macro_content(mname)
                self.write(output)

            elif mname in self._defined_macros:
                self.write(self._imported_modules[mname])

            else:
                self.write('\\' + mname)

        self._in_stream.close()
        self._out_stream.close()

        proc = subprocess.run(
            "pdflatex --synctex=1 --interaction=nonstopmode --halt-on-error --output-directory=\"{}\" {}".format(build_dir, outfile), stdout=subprocess.PIPE
        )
        
        if proc.returncode:
            err = self.parse_pdflatex_error(proc.stdout.decode('utf-8'))
            raise RuntimeError(
                "pdfTEX Error on line: {}. {} {}\n {}\n See full log at: {}".format(err['line'], err['msg'], err['src'], infile, build_dir / (infile.stem + '.log'))
            )
        
        else:
            gen_pdf = build_dir / (infile.stem + '.pdf')
            gen_syn = build_dir / (infile.stem + '.synctex.gz')

            out_pdf = infile.with_suffix('.pdf')
            out_syn = infile.with_suffix('.synctex.gz')

            shutil.copyfile(gen_pdf, out_pdf)
            shutil.copyfile(gen_syn, out_syn)

        print('Output PDF written to {}'.format(out_pdf))
        return proc

    # out = subprocess.run("\"C:/Program Files/SumatraPDF/SumatraPDF-3.4.6-64.exe\" \"{}\" -inverse-search \"\"C:/ProgramData/Notepad++/notepad++.exe\" -n%l \"%f\"\"".format(out_pdf), shell=True)

@click.command()
@click.argument('filepath')
def cli(filepath):
    texpp = TeXPreprocessor()
    texpp.run(filepath)

if __name__ == '__main__':
    
    # cli()
    texpp = TeXPreprocessor()
    out = texpp.run(Path(__file__).parent / '../tests/test.tex')

    


