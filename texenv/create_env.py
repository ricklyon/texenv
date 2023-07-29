import subprocess
from pathlib import Path
import os
import re
import shutil
import utils
import sys
import packages

cwd = Path.cwd()
prompt = sys.argv[1] if len(sys.argv) > 0 else '.venv'

# create python virtual environment
proc = subprocess.run(
    "python -m venv \"{}\.venv\" --prompt=\"{}\"".format(cwd, prompt), stdout=subprocess.PIPE
)
if proc.returncode:
    raise RuntimeError(proc.stdout.decode('utf-8'))

texpath = utils.get_texpath()

# copy tex binaries to venv folder
newtexpath = cwd / '.venv/tex'

pdb_home = texpath / 'tlpkg/texlive.tlpdb'
pdb_dest = newtexpath / 'tlpkg/texlive.tlpdb'

pkg_listings, pkg_files = utils.tlpdb_parse(pdb_home)

# install packages
for k in packages.install_pkgs:
    if k not in pkg_files:
        raise RuntimeError(f'package {k} not found in base TeXLive installation. Ensure the "basic" TeXLive scheme is installed.')
    
    for v in pkg_files[k]['runfiles']:
        os.makedirs((newtexpath / v).parent, exist_ok=True)
        shutil.copy(texpath / v, newtexpath / v)
    for v in pkg_files[k]['binfiles']:
        os.makedirs((newtexpath / v).parent, exist_ok=True)
        shutil.copy(texpath / v, newtexpath / v)

with open(pdb_dest, 'w+') as f:
    for k in packages.install_pkgs:
        f.write(f'name {k}\n'+ pkg_listings[k] + '\n')

shutil.copy(texpath / 'texmf-dist/ls-R', newtexpath / 'texmf-dist/ls-R')

shutil.copytree(texpath / 'texmf-var', newtexpath / 'texmf-var')

# modify activation scripts to add the new texpath to beginning of PATH so it's found before the base install
with open(cwd / '.venv/Scripts/activate.bat', 'a') as f:
    f.write('\nset PATH=%VIRTUAL_ENV%\\tex\\bin\\windows;%PATH%\n')

with open(cwd / '.venv/Scripts/activate', 'a') as f:
    f.write('\nPATH="$VIRTUAL_ENV/tex/bin/windows:$PATH"\nexport PATH')

# TODO: update powershell script