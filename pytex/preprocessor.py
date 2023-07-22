from pathlib import Path
from time import time
import sys
import importlib
import os

infile = Path(__file__).parent / 'test.tex' #Path(sys.argv[1])
outfile = str(infile.parent) + '\\' + infile.stem + '_pp.tex'

EMPTY = b''
BACKSLASH =     '\\'.encode('utf-8')
LEFT_BRACKET =  '['.encode('utf-8')
RIGHT_BRACKET = ']'.encode('utf-8')
LEFT_BRACE =    '{'.encode('utf-8')
RIGHT_BRACE=    '}'.encode('utf-8')
COMMENT=        '%'.encode('utf-8')
NEWLINE=         '\n'.encode('utf-8')

def parse_argument(stream):

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
            stream.seek(-1, os.SEEK_CUR)
            break

        mname = get_macro_name(stream)
        if mname in imported_modules.keys():

            output = get_macro_content(stream, mname)
            arg_ch += output

        elif mname in defs:
            argument += defs[mname]

        elif arg_ch == '=':
            key = argument.strip()
            argument = ''

        elif arg_ch != '}' and arg_ch != '{':
            if mname:
                argument += (arg_ch + '\\' + mname).strip()
            else:
                argument += arg_ch
        
        arg_ch = stream.read(1).decode('utf-8')

    return key, argument.strip()

def parse_macro_args(stream):
    """
    Returns the argument list and kwargs passed into a pytex method. Stream
    must be at the end of the pytex method name.
    """
    args = []
    kwargs = {}
    skip_whitespace(stream, allow_break=True)

    m_ch = stream.read(1).decode('utf-8')

    # return if no enclosing bracket around arguments
    if m_ch != '[':
        return args, kwargs
    
    # get macro arguments
    key, arg = parse_argument(stream)
    if key is None:
        args.append(arg)
    else:
        kwargs[key] = arg

    m_ch = stream.read(1).decode('utf-8')
    while m_ch == ',':

        key, arg = parse_argument(stream)
        if key is None:
            args.append(arg)
        else:
            kwargs[key] = arg

        m_ch = stream.read(1).decode('utf-8')
    
    if m_ch != ']':
        raise ValueError('Unbalanced closing bracket around macro arguments.')

    return args, kwargs


def skip_whitespace(in_stream, out_stream=None, allow_break=False):
    # read whitespace up to first non-whitespace character

    ch = in_stream.read(1).decode('utf-8')  

    read_i = 1
    while ch.isspace():
        if ch == '\n' and not allow_break:
            break
        if out_stream is not None:
            out_stream.write(ch.encode())

        ch = in_stream.read(1).decode('utf-8')
        read_i += 1

    if len(ch):
        in_stream.seek(-1, os.SEEK_CUR)
    
def get_macro_name(in_stream, out_stream=None):
    """
    Returns macro name. Stream must be at the first character of name (after backslash)
    """
    skip_whitespace(in_stream, out_stream)
    n_ch = in_stream.read(1).decode('utf-8')

    if n_ch != '\\':
        if len(n_ch):
            in_stream.seek(-1, os.SEEK_CUR)
        return None

    name = ''
    n_ch = in_stream.read(1).decode('utf-8')
    while n_ch.isalpha():
        name += n_ch
        n_ch = in_stream.read(1).decode('utf-8')

    if len(n_ch):
        in_stream.seek(-1, os.SEEK_CUR)
    return name

def get_def_value(stream):
    """
    Returns the value assigned to a pytex variable
    """
    value = ''
    n_ch = stream.read(1).decode('utf-8')

    while n_ch != '\n' and len(n_ch):
        value += n_ch
        n_ch = stream.read(1).decode('utf-8')

    if len(n_ch):
        stream.seek(-1, os.SEEK_CUR)
    return value.strip()

def get_macro_content(stream, mname):
    module = imported_modules[mname]

    lib = importlib.__import__(module)

    method_name = get_macro_name(stream)
    if method_name is None:
        raise ValueError('expected method name after imported module')
    
    method = getattr(lib, method_name)

    # get macro arguments
    args, kwargs = parse_macro_args(stream)

    return method(*args, **kwargs)

in_stream = f = open(infile, "rb")
out_stream = open(outfile, "wb+")
imported_modules = {}
defs = {}

stime = time()
g_ch = b' '
comment = False
while len(g_ch):

    if g_ch == COMMENT:
        comment = True

    if g_ch == NEWLINE:
        comment = False

    if comment:
        if g_ch != COMMENT:
            out_stream.write(g_ch)
        g_ch = in_stream.read(1)
        continue

    mname = get_macro_name(in_stream, out_stream)

    if mname is None:
        g_ch = in_stream.read(1)
        out_stream.write(g_ch)
        
    elif mname == 'import':
        module = get_macro_name(in_stream)

        if module is None:
            raise ValueError('expected module name after import statement.')
        
        # check for alias
        skip_whitespace(in_stream)
        
        alias_as = in_stream.read(2).decode('utf-8')
        alias = module
        if alias_as == 'as':
            alias = get_macro_name(in_stream)
        else:
            in_stream.seek(-2, os.SEEK_CUR)
        imported_modules[alias] = module

    elif mname == 'pydef':
        varname = get_macro_name(in_stream)

        if varname is None:
            raise ValueError('expected variable name after pydef statement.')
        
        defs[varname] = get_def_value(in_stream)

    elif mname in imported_modules.keys():

        output = get_macro_content(in_stream, mname)
        out_stream.write(output.encode())

    elif mname in defs:
        out_stream.write(defs[mname].encode())

    else:
        out_stream.write('\\'.encode() + mname.encode())




print(time()-stime)

in_stream.close()
out_stream.close()




