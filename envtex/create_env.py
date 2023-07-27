import subprocess
from pathlib import Path
import os
import re
import shutil

cwd = Path.cwd()
prompt = 'test'

# create python virtual environment
proc = subprocess.run(
    "python -m venv \"{}\.venv\" --prompt=\"{}\"".format(cwd, prompt), stdout=subprocess.PIPE
)
if proc.returncode:
    raise RuntimeError(proc.stdout.decode('utf-8'))

# get PATH and look for tex installation
path = os.environ['PATH']

texpath = [p for p in path.split(';') if re.match(r'.*texlive\\\d+\\bin\\windows', p)]

if not len(texpath):
    raise RuntimeError('texlive installation not found on PATH')
else:
    texpath = Path(texpath[0])

# copy tex binaries to venv folder
# def create_env()
dest = cwd / '.venv/tex'
shutil.copytree(texpath, dest / 'bin/windows')
shutil.copytree(texpath / '../../texmf-var', dest / 'texmf-var')
# copy bare bones latex packages and fonts from base install
core_pkgs = [
    'texmf-dist/fonts/type1',
    'texmf-dist/tex/latex/base',
    'texmf-dist/tex/latex/l3backend',
    'texmf-dist/tex/latex/l3kernel',
    'texmf-dist/web2c',
]

for p in core_pkgs:
    shutil.copytree(texpath / ('../../' + p), dest / p)

shutil.copy(texpath / ('../../texmf-dist/ls-R'), dest / 'texmf-dist/ls-R')

envpathtex = cwd / '.venv/tex/bin/windows'
# modify activation scripts to add the new texpath to beginning of PATH so it's found before the base install
with open(cwd / '.venv/Scripts/activate.bat', 'a') as f:
    f.write('\nset PATH=%VIRTUAL_ENV%\\tex\\bin\\windows;%PATH%\n')

with open(cwd / '.venv/Scripts/activate', 'a') as f:
    f.write('\nPATH="$VIRTUAL_ENV/tex/bin/windows:$PATH"\nexport PATH')

# with open(cwd / '.venv/Scripts/Activate.ps1', 'a') as f:
#     f.write('\nPATH="$VIRTUAL_ENV/tex/bin/windows:$PATH"\nexport PATH')