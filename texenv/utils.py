import subprocess
from pathlib import Path
import os
import re

def get_texpath():
    """
    Returns the TeXLive installation directory on windows
    """
    path = os.environ['PATH']

    texpath = [p for p in path.split(';') if re.match(r'.*texlive\\\d+\\bin\\windows', p)]

    if not len(texpath):
        raise RuntimeError('texlive installation not found on PATH')
    else:
        texpath = (Path(texpath[0]) / '../../').resolve()

    return texpath


def tlpdb_parse(pdb_path):
    """
    Parses the TexLive Package Database file and returns the
    paths to the bin and run files associated with each package.
    """
    pkg_listings = {}

    with open(pdb_path, 'r') as f:
        ln = 1
        while ln:
            ln = f.readline()
            if ln[:4] == 'name' and ln[4:].strip():
                pkg_name = ln[4:].strip()
                pkg_listings[pkg_name] = ''

                ln = f.readline()
                while ln != '\n':
                    pkg_listings[pkg_name] += ln
                    ln = f.readline()

    pkg_files = {}
    runlisting = False
    binlisting = False
    for k, v in pkg_listings.items():
        pkg_files[k] = {}
        pkg_files[k]['runfile'] = []
        pkg_files[k]['binfile'] = []
        for ln in v.split('\n'):
            if ln[:7] == 'runfile':
                runlisting = True
                binlisting = False
                continue
            elif ln[:7] == 'binfile':
                binlisting = True
                runlisting = False
                continue
            elif len(ln) and ln[0] != ' ':
                runlisting = False
                binlisting = False
                continue

            if runlisting and len(ln):
                pkg_files[k]['runfile'].append(ln.strip())
            elif binlisting and len(ln):
                pkg_files[k]['binfile'].append(ln.strip())

    return pkg_listings, pkg_files

        




                
