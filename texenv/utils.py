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
    try:
        img = Image.open(filepath)
        w_im, h_im = img.size

        if normalize:
            # normalize the width and height so the largest dimension is 1.
            w_im, h_im = normalize_dimensions(w_im, h_im)
        return w_im, h_im
    except Exception:
        return (1, 1)


def get_figure_size(fig, normalize=False):
    """
    Returns width and height of figure in inches.
    """
    w_im, h_im = fig.get_size_inches()

    if normalize:
        # normalize the width and height so the largest dimension is 1.
        w_im, h_im = normalize_dimensions(w_im, h_im)

    return w_im, h_im


def sync_from_file(filepath):

    with open(filepath, "r") as f:
        all_pkgs = f.read().split("\n")
        # filter out base packages if they somehow made it onto the file
        pkgs = [pkg.strip() for pkg in all_pkgs if pkg not in packages.install_pkgs]

    if "VIRTUAL_ENV" not in dict(os.environ).keys():
        raise RuntimeError(
            "This command must be run from a virtual environment. To create one use: python -m venv .venv"
        )

    texpath = get_env_texpath() / "tlmgr.bat"

    with subprocess.Popen(
        f"{texpath} install " + " ".join(pkgs),
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    ) as process:

        output = process.communicate()[0]

    return output


def texenv_init(prompt=".venv"):
    """
    Initializes the texenv environment and TeX installation.
    """
    # create python virtual environment if we aren't already in one
    if "VIRTUAL_ENV" not in dict(os.environ).keys():
        raise RuntimeError(
            "This command must be run from a virtual environment. To create one use: python -m venv .venv"
        )
    else:
        print(f"Found existing virtual environment at {os.environ['VIRTUAL_ENV']}")

    cwd = Path(os.environ["VIRTUAL_ENV"])

    texpath = get_base_texpath()

    # copy tex binaries to venv folderpip
    newtexpath = cwd / "tex"

    if newtexpath.exists():
        # prompt to overwrite existing venv Tex installation
        response = input(
            f"TeX installation already exists at {newtexpath}. Overwrite [y/n]?"
        )
        if response == "y":
            shutil.rmtree(newtexpath, ignore_errors=True)
        else:
            raise RuntimeError(f"TeX installation already exists at {newtexpath}")

    pdb_home = texpath / "tlpkg/texlive.tlpdb"
    pdb_dest = newtexpath / "tlpkg/texlive.tlpdb"

    print(f"Setting up TeX environment...")
    pkg_listings, pkg_files = tlpdb_parse(pdb_home)

    # install packages
    for k in packages.install_pkgs:
        if k not in pkg_files:
            raise RuntimeError(
                f'package {k} not found in base TeXLive installation. Ensure at least the "small" TeXLive scheme is installed on the system.'
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

    # update tlmgr inside the environment
    print(f"Updating TexLive package manager (tlmgr)...")
    subprocess.run(
        f"{newtexpath}\\bin\\windows\\tlmgr.bat update --self", stdout=subprocess.PIPE
    )

    print("Installing packages from pkg_files/slides.txt...")
    slide_file = Path(__file__).parent / "pkg_files/slides.txt"
    sync_from_file(slide_file)

    # changing PATH within python will not affect the parent session
    # subprocess.run(str(cwd / "Scripts/activate.bat"))


def parse_pdflatex_error(output):
    lines = output.split("\n")

    error_msg = ""
    error_ln = -1
    error_src = ""

    for ln in lines:
        if len(ln) and ln[0] == "!":
            error_msg += ln[1:].strip() + "\n"

        m = re.match(r"^l.(\d+)", ln)

        if m:
            error_ln = int(m.group(1))
            error_src = ln[len(m.group(0)) :].strip()
            break

    return dict(msg=error_msg, line=error_ln, src=error_src)


def get_base_texpath():
    """
    Returns the TeXLive installation directory on windows
    """
    path = os.environ["PATH"]

    texpath = [
        p for p in path.split(";") if re.match(r".*texlive\\\d+\\bin\\windows", p)
    ]

    if not len(texpath):
        raise RuntimeError("texlive installation not found!")
    else:
        texpath = (Path(texpath[0]) / "../../").resolve()

    return texpath


def get_env_texpath():
    return Path(os.environ["VIRTUAL_ENV"]) / r"tex/bin/windows"


def tlpdb_parse(pdb_path: Path):
    """
    Parses the TexLive Package Database file and returns the
    paths to the bin and run files associated with each package.
    """
    pkg_listings = {}

    with open(pdb_path, "r", encoding="utf-8") as f:
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
