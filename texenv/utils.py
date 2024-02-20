import subprocess
from pathlib import Path
import os
import re
import shutil
from PIL import Image
from . import packages


def normalize_dimensions(w, h):
    """normalize the width and height so the largest dimension is 1."""
    largest_dim = w if w > h else h
    w_n = w / largest_dim
    h_n = h / largest_dim

    return w_n, h_n


def get_image_size(filepath, normalize=False):
    """
    Return width and height of an image file.
    """
    img = Image.open(filepath)
    w_im, h_im = img.size

    if normalize:
        # normalize the width and height so the largest dimension is 1.
        w_im, h_im = normalize_dimensions(w_im, h_im)
    return w_im, h_im


def get_figure_size(fig, normalize=False):
    """
    Returns width and height of figure in inches.
    """
    w_im, h_im = fig.get_size_inches()

    if normalize:
        # normalize the width and height so the largest dimension is 1.
        w_im, h_im = normalize_dimensions(w_im, h_im)

    return w_im, h_im


def texenv_init(prompt=".venv"):
    """
    Initializes the texenv environment and TeX installation.
    """
    # create python virtual environment if we aren't already in one
    if "VIRTUAL_ENV" not in dict(os.environ).keys():
        print(f"Creating virtual environment... ({prompt})")
        cwd = Path.cwd()
        proc = subprocess.run(
            'python -m venv "{}\.venv" --prompt="{}"'.format(cwd, prompt),
            stdout=subprocess.PIPE,
        )
        if proc.returncode:
            raise RuntimeError(proc.stdout.decode("utf-8"))
    else:
        print(f"Found existing virtual environment at {os.environ['VIRTUAL_ENV']}")

    cwd = Path(os.environ["VIRTUAL_ENV"])

    texpath = get_texpath()

    # copy tex binaries to venv folder
    newtexpath = cwd / "tex"

    if newtexpath.exists():
        raise RuntimeError(f"TeX installation already exists at {newtexpath}")

    pdb_home = texpath / "tlpkg/texlive.tlpdb"
    pdb_dest = newtexpath / "tlpkg/texlive.tlpdb"

    print(f"Setting up TeX environment...")
    pkg_listings, pkg_files = tlpdb_parse(pdb_home)

    # install packages
    for k in packages.install_pkgs:
        if k not in pkg_files:
            raise RuntimeError(
                f'package {k} not found in base TeXLive installation. Ensure at least the "basic" TeXLive scheme is installed on the system.'
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

    os.makedirs(newtexpath / "tlpkg/backups", exist_ok=True)

    shutil.copy(texpath / "texmf-dist/ls-R", newtexpath / "texmf-dist/ls-R")
    shutil.copytree(texpath / "texmf-var", newtexpath / "texmf-var")

    # modify activation scripts to add the new texpath to beginning of PATH so it's found before the base install
    with open(cwd / "Scripts/activate.bat", "a") as f:
        f.write("\nset PATH=%VIRTUAL_ENV%\\tex\\bin\\windows;%PATH%\n")

    with open(cwd / "Scripts/activate", "a") as f:
        f.write('\nPATH="$VIRTUAL_ENV/tex/bin/windows:$PATH"\nexport PATH')

    # update powershell script, since we are modifiying it we need to remove the signature block first
    script = ""
    with open(cwd / "Scripts/Activate.ps1", "r") as f:
        ln = 1
        while ln:
            ln = f.readline()
            if ln.strip()[:7] == "# SIG #":
                break
            script += ln

    with open(cwd / "Scripts/Activate.ps1", "w+") as f:
        f.write(script)
        f.write(
            '\n$path = Join-Path $VenvDir "\\tex\\bin\windows"\n$Env:PATH = "$path$([System.IO.Path]::PathSeparator)$Env:PATH"'
        )

    # changing PATH within python will not affect the parent session
    # subprocess.run(str(cwd / "Scripts/activate.bat"))


def parse_pdflatex_error(output):
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


def get_texpath():
    """
    Returns the TeXLive installation directory on windows
    """
    path = os.environ["PATH"]

    texpath = [
        p for p in path.split(";") if re.match(r".*texlive\\\d+\\bin\\windows", p)
    ]

    if not len(texpath):
        raise RuntimeError("texlive installation not found on PATH")
    else:
        texpath = (Path(texpath[0]) / "../../").resolve()

    return texpath


def tlpdb_parse(pdb_path):
    """
    Parses the TexLive Package Database file and returns the
    paths to the bin and run files associated with each package.
    """
    pkg_listings = {}

    with open(pdb_path, "r") as f:
        ln = 1
        while ln:
            ln = f.readline()
            if ln[:4] == "name" and ln[4:].strip():
                pkg_name = ln[4:].strip()
                pkg_listings[pkg_name] = ""

                ln = f.readline()
                while ln != "\n":
                    pkg_listings[pkg_name] += ln
                    ln = f.readline()

    pkg_files = {}
    curlisting = ""
    for k, v in pkg_listings.items():
        pkg_files[k] = {}
        pkg_files[k]["runfiles"] = []
        pkg_files[k]["binfiles"] = []
        pkg_files[k]["srcfiles"] = []
        for ln in v.split("\n"):
            if ln[:8] in ["runfiles", "binfiles", "srcfiles"]:
                curlisting = ln[:8]
                continue
            elif not len(ln) or ln[0] != " ":
                curlisting = ""
                continue

            if curlisting and len(ln):
                pkg_files[k][curlisting].append(ln.strip())

    return pkg_listings, pkg_files
