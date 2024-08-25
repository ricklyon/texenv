# texenv

Create lightweight TeX virtual environments, and use Python methods in TeX code. 

## Installation

`texenv` is currently only supported on Windows, and requires `texlive` to be installed on the system.  
https://tug.org/texlive/windows.html#install  
Ensure at least the "basic" TeXLive scheme is selected during installation.

`texenv` requires an existing Python virtual environment, create one with the following command,
```bash
python -m venv .venv
```

Install `texenv` inside a Python virtual environment,

```bash
pip install texenv
```

To create a standalone TeX installation visible only to the current environment, 
```bash
texenv init
```
This installs a bare-bones version of LaTeX in `.venv/tex`.

## Usage

To install packages into the TeX environment,
```bash
texenv install <package name>
```

The package name refers to the TeXLive package name, which is often different than the package name in [CTAN](https://ctan.org/). To find the TeXLive package name, search for the package on CTAN and find the "Contained in" section. The package name will be listed next to "TeXLive as".   
For example,  
![ctan-example](https://raw.githubusercontent.com/ricklyon/texenv/main/docs/img/texlive_ctan.png)


To write all currently installed TeX packages in the environment to a file (excluding core packages required for LaTeX to run),
```bash
texenv freeze > texrequirements.txt
```

Or to print to the console:
```bash
texenv list
```

To synchronize the TeX installation with the packages found in a requirements file,
```bash
texenv sync texrequirements.txt
```

To compile a .tex file with pdflatex:
```bash
texenv run <.tex filepath>
```

`texenv` provides a preprocessor that can be used to call Python methods directly from TeX code. This is useful for generating figures and tables in python, or writing complicated macros that are difficult in LaTeX. The example below shows a simple use case:

Contents of `example.tex`:
```tex
\documentclass{article}

% required package for inserting figures
\usepackage{graphicx}

% import a python module either installed in the environment, or just a file in the same folder as the .tex file.
% In this case figures.py is in the same folder.
\import\figures

% preprocessor variables can be defined with \pydef followed by the variable name and value.
\pydef\cleanfig true

\begin{document}
  
  % call a python method. Supports arguments and kwargs, but all are passed in as string types. The return type of 
  % the method must be a string as it is inserted directly into the TeX code.
  \figures\figA[clean=\cleanfig, width=5in]
   
\end{document}
```
Contents of `figures.py`, located in the same directory as `example.tex`:
```python
from texenv.macros import figure
import matplotlib.pyplot as plt

def figA(clean="true", width="3in", **kwargs):
    
    if clean == "false":
        return figure(file="figA.pdf", width=width, **kwargs)

    fig, ax1 = plt.subplots(1, 1)
    ax1.plot(range(11, 17))

    fig.savefig("figA.pdf")

    return figure(file="figA.pdf", width=width, **kwargs)

```

The `run` command invokes the preprocessor, and then calls `pdflatex` on the post-processed `.tex` file. The synctex file is modified after running `pdflatex` so the intermediate file is transparent to synctex.

```bash
texenv run example.tex
```

Full example:
[examples/macro_example/macro_example.tex](examples/macro_example/macro_example.tex)

## Slideshows

`texenv` provides a simple way to generate PDF slideshow presentations directly from Python. Matplotlib figures, images, and LaTeX code can be assembled together into a slide using the `Presentation` class:

```python
from texenv import Presentation, datatable

... 

# text to place on slide. This is interpreted as an enumerate list if \item appears first in the string.
# Otherwise, the text is inserted directly as LaTeX code and supports math macros etc...
text = r"""
\item Bullet 1
\item Bullet 2
\[ \nabla \times \mathbf{E} = -\mu {\partial \mathbf{H} \over \partial t} \]
\[ \nabla \times \mathbf{H} = \varepsilon {\partial \mathbf{E} \over \partial t} \]
"""

# create a table with header names, and a format string applied to each cell
table = datatable(
    np.arange(16).reshape((4, 4)), header_row=[f"Header {i}" for i in range(4)], formatter="{:.2f}"
)

pres = Presentation("example_slides.pdf")

# add the content to the first slide. The layout will be a 2x2 grid, with the figure centered along both rows in the
# second column. The text and table will split the first column. 
pres.add_slide(
    content=[[text, fig], 
             [table, None]], 
    title="Example TeX Slides", 
    width_ratio=(1, 2) # make the second column twice as wide as the first column.
)

pres.save()
```

![example2](https://raw.githubusercontent.com/ricklyon/texenv/main/docs/img/example_slide.png)

Full example:
[examples/slideshow/slideshow.py](examples/slideshow/slideshow.py)


## VSCode Setup

`texenv` is designed to work with the Latex Workshop extension in VSCode. The following settings in `settings.json` should configure `texenv` on Unix platforms. Note that the "build on save" feature only works when VSCode is opened as a workspace.

```json
    "[latex]": {
        "editor.formatOnSave": false,
        "editor.wordWrap": "on"
    },
    "latex-workshop.latex.recipes": [
        {
        "name": "texenv",
        "tools": [
            "texenv"
        ]
        },
    ],
    "latex-workshop.latex.tools": [
        {
        "name": "texenv",
        "command": "texenv",
        "args": [
            "run",
            "%DOC_EXT%"
        ],
        "env": {
            "PATH": "%WORKSPACE_FOLDER%/.venv/tex/bin/x86_64-linux:%WORKSPACE_FOLDER%/.venv/bin:%PATH%",
            "VIRTUAL_ENV": "%WORKSPACE_FOLDER%/.venv"
        }
        }
    ],
    "latex-workshop.view.pdf.internal.synctex.keybinding": "double-click",
    "latex-workshop.latex.autoBuild.run": "onSave",
    "latex-workshop.latex.autoClean.run": "never",
```

If the Unix platform is not `x86_64-linux`, change the `PATH` to match the platform. 

On Windows, change `env` under `"latex-workshop.latex.tools"` to:
```json
"env": {
    "Path": "%WORKSPACE_FOLDER%/.venv/tex/bin/windows;%WORKSPACE_FOLDER%/.venv/Scripts;%PATH%",
    "VIRTUAL_ENV": "%WORKSPACE_FOLDER%/.venv"
}
```

## Troubleshooting

`texenv` installs lightweight version of LaTeX into the virtual environment (equivalent to the "basic" TeXLive distribution). Most packages and fonts will need to be installed after the environment is initialized. A couple of useful TeXLive packages that will solve a lot of missing package errors:

```bash
texenv install collection-latexrecommended
texenv install collection-fontsrecommended
```

`texenv` includes a parser for the rather verbose pdflatex log files, and attempts to show only the relevant error messages. For example, 
```
RuntimeError: pdfTEX Error on line: 9. LaTeX Error: File `hyphenat.sty' not found.
Emergency stop.
```

A link to the full log file is also included below the error message.

## License

`texenv` is licensed under the MIT License.