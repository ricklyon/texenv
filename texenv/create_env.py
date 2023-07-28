import subprocess
from pathlib import Path
import os
import re
import shutil
import utils

cwd = Path.cwd()
prompt = 'test'

# create python virtual environment
proc = subprocess.run(
    "python -m venv \"{}\.venv\" --prompt=\"{}\"".format(cwd, prompt), stdout=subprocess.PIPE
)
if proc.returncode:
    raise RuntimeError(proc.stdout.decode('utf-8'))

texpath = utils.get_texpath()

# copy tex binaries to venv folder
newtexpath = cwd / '.venv/tex'

# index packages in the database file that are required for texlive to run
install_pkgs = [
    '00texlive.config',
    '00texlive.installation',
    'amsfonts',
    'bibtex',
    'bibtex.windows',
    'cm',
    'collection-basic',
    'colorprofiles',
    'dehyph',
    'dvipdfmx',
    'dvipdfmx.windows',
    'dvips',
    'dvips.windows',
    'ec',
    'enctex',
    'etex',
    'etex-pkg',
    'glyphlist',
    'graphics-def',
    'hyph-utf8',
    'hyphen-base',
    'hyphenex',
    'ifplatform',
    'iftex',
    'knuth-lib',
    'knuth-local',
    'kpathsea',
    'kpathsea.windows',
    'lua-alt-getopt',
    'luahbtex',
    'luahbtex.windows',
    'luatex',
    'luatex.windows',
    'makeindex',
    'makeindex.windows',
    'metafont',
    'metafont.windows',
    'mflogo',
    'mfware',
    'mfware.windows',
    'modes',
    'pdftex',
    'pdftex.windows',
    'plain',
    'scheme-infraonly',
    'scheme-minimal',
    'tex',
    'tex-ini-files',
    'tex.windows',
    'texlive-common',
    'texlive-en',
    'texlive-msg-translations',
    'texlive-scripts',
    'texlive-scripts.windows',
    'texlive.infra',
    'texlive.infra.windows',
    'tlgs.windows',
    'tlperl.windows',
    'tlshell',
    'tlshell.windows',
    'unicode-data',
    'xdvi'
]

pdb_home = texpath / 'tlpkg/texlive.tlpdb'
pdb_dest = newtexpath / 'tlpkg/texlive.tlpdb'

pkg_listings, pkg_files = utils.tlpdb_parse(pdb_home)

for k,v in pkg_files.items():
    if k in install_pkgs:
        for v in v['runfile']:
            os.makedirs((newtexpath / v).parent, exist_ok=True)
            shutil.copy(texpath / v, newtexpath / v)
        for v in v['binfile']:
            os.makedirs((newtexpath / v).parent, exist_ok=True)
            shutil.copy(texpath / v, newtexpath / v)

with open(pdb_dest, 'w+') as f:
    for k, v in pkg_listings.items():
        if k in install_pkgs:
            f.write(f'name {k}\n'+ v + '\n')

pdb_path = texpath / 'tlpkg/texlive.tlpdb'

shutil.copy(texpath / 'texmf-dist/ls-R', newtexpath / 'texmf-dist/ls-R')

# modify activation scripts to add the new texpath to beginning of PATH so it's found before the base install
with open(cwd / '.venv/Scripts/activate.bat', 'a') as f:
    f.write('\nset PATH=%VIRTUAL_ENV%\\tex\\bin\\windows;%PATH%\n')

with open(cwd / '.venv/Scripts/activate', 'a') as f:
    f.write('\nPATH="$VIRTUAL_ENV/tex/bin/windows:$PATH"\nexport PATH')

# TODO: update powershell script