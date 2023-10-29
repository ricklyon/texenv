import subprocess
from pathlib import Path
import os
import re
import shutil
import utils
import sys
import packages

cwd = Path.cwd()
prompt = sys.argv[1] if len(sys.argv) > 2 else ".venv"

# create python virtual environment if we aren't already in one
if "VIRTUAL_ENV" not in dict(os.environ).keys():
    print(f"Creating virtual environment... ({prompt})")
    proc = subprocess.run(
        'python -m venv "{}\.venv" --prompt="{}"'.format(cwd, prompt),
        stdout=subprocess.PIPE,
    )
    if proc.returncode:
        raise RuntimeError(proc.stdout.decode("utf-8"))

print(f"Setting up TeX installation...")
texpath = utils.get_texpath()

# copy tex binaries to venv folder
newtexpath = cwd / ".venv/tex"

if newtexpath.exists():
    raise RuntimeError(f"TeX installation already exists at {newtexpath}")

pdb_home = texpath / "tlpkg/texlive.tlpdb"
pdb_dest = newtexpath / "tlpkg/texlive.tlpdb"

pkg_listings, pkg_files = utils.tlpdb_parse(pdb_home)

# install packages
for k in packages.install_pkgs:
    if k not in pkg_files:
        raise RuntimeError(
            f'package {k} not found in base TeXLive installation. Ensure at least the "basic" TeXLive scheme is installed.'
        )

    for v in pkg_files[k]["runfiles"]:
        os.makedirs((newtexpath / v).parent, exist_ok=True)
        shutil.copy(texpath / v, newtexpath / v)
    for v in pkg_files[k]["binfiles"]:
        os.makedirs((newtexpath / v).parent, exist_ok=True)
        shutil.copy(texpath / v, newtexpath / v)

with open(pdb_dest, "w+") as f:
    for k in packages.install_pkgs:
        f.write(f"name {k}\n" + pkg_listings[k] + "\n")

shutil.copy(texpath / "texmf-dist/ls-R", newtexpath / "texmf-dist/ls-R")
shutil.copytree(texpath / "texmf-var", newtexpath / "texmf-var")

# modify activation scripts to add the new texpath to beginning of PATH so it's found before the base install
with open(cwd / ".venv/Scripts/activate.bat", "a") as f:
    f.write("\nset PATH=%VIRTUAL_ENV%\\tex\\bin\\windows;%PATH%\n")

with open(cwd / ".venv/Scripts/activate", "a") as f:
    f.write('\nPATH="$VIRTUAL_ENV/tex/bin/windows:$PATH"\nexport PATH')

# update powershell script, since we are modifiying it we need to remove the signature block first
script = ""
with open(cwd / ".venv/Scripts/Activate.ps1", "r") as f:
    ln = 1
    while ln:
        ln = f.readline()
        if ln.strip()[:7] == "# SIG #":
            break
        script += ln

with open(cwd / ".venv/Scripts/Activate.ps1", "w+") as f:
    f.write(script)
    f.write(
        '\n$path = Join-Path $VenvDir "\\tex\\bin\windows"\n$Env:PATH = "$path$([System.IO.Path]::PathSeparator)$Env:PATH"'
    )
