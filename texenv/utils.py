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
    curlisting = ''
    for k, v in pkg_listings.items():
        pkg_files[k] = {}
        pkg_files[k]['runfiles'] = []
        pkg_files[k]['binfiles'] = []
        pkg_files[k]['srcfiles'] = []
        for ln in v.split('\n'):
            if ln[:8] in ['runfiles', 'binfiles', 'srcfiles']:
                curlisting = ln[:8]
                continue
            elif not len(ln) or ln[0] != ' ':
                curlisting = ''
                continue

            if curlisting and len(ln):
                pkg_files[k][curlisting].append(ln.strip())

    return pkg_listings, pkg_files


