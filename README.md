# texenv

Creates lightweight TeX virtual environments and call Python methods directly from TeX code. 

## Installation

`texenv` is currently only supported on Windows, and requires `texlive` to be installed on the system.  
https://tug.org/texlive/windows.html#install


Install `texenv` inside an existing Python virtual environment,

```bash
pip install texenv
```

To create a standalone TeX installation visible only to the current environment, 
```bash
texenv init
```
This installs a bare-bones version of LaTeX in `.venv/tex` and modifies the environment activation scripts so this TeX installation is used instead of the base installation. The console needs to be closed and re-opened for the changes to take effect.

## Usage

The TeX environment supports the standard `tlmgr` tool which can be used to install and update packages as normal.
```bash
tlmgr install <package name>
```

To write all currently installed TeX packages in the environment to a file (excluding core packages required for LaTeX to run),
```bash
texenv freeze > texrequirements.txt
```

To synchronize the TeX installation with the packages found in a requirements file,
```bash
texenv sync texrequirements.txt
```
### Compiling 

`.tex` files can be compiled in the environment using the standard tools (i.e `pdflatex`). `texenv` also supports a preprocessor that can be used to call Python methods directly from TeX code. The string returned by the Python method will be inserted into the document before compilation. 

Writing TeX macros in Python is much more straight forward and more versatile than writing them in TeX. 

Contents of `example.tex`:
```tex
\documentclass{article}

\import\pymacros_1 as \pym
\pydef\test true

\begin{document}
   
   \pym\simple[argument1, arg2=\test]
   
\end{document}
```
Contents of `pymacros_1.py`, located in the same directory as `example.tex`, or in a installed module named `pymacros_1`
```python
def simple(arg1: str, arg2: str = 'default') -> str:
    return str(arg1) + '|' + str(arg2)
```

Compile on command line inside virtual environment:
```bash
texenv run example.tex
```

The `run` command invokes the preprocessor, and then calls `pdflatex` on the post-processed `.tex` file. The synctex file is modified after running `pdflatex` so the intermediate file is transparent to synctex.

Contents of post-processed `example.tex` (located in `build` folder):
```tex
\documentclass{article}



\begin{document}
   
   argument1|true
   
\end{document}
```

## VSCode Setup

`texenv` is designed to work with the Latex Workshop extension in VSCode. Once the extension is installed, the following
settings should be added to the `settings.json` file:

```json
    "latex-workshop.latex.tools": [
        {
          "name": "texenv",
          "command": "texenv",
          "args": [
            "run", "%DOC_EXT%"
          ],
          "env": {
            "Path": "%WORKSPACE_FOLDER%/.venv/tex/bin/windows;%WORKSPACE_FOLDER%/.venv/Scripts;%PATH%"
          }
        },
    ],
    "latex-workshop.view.pdf.internal.synctex.keybinding": "double-click"
```

## License

texenv is licensed under the MIT License.