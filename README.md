# texenv

Create lightweight TeX virtual environments, and use Python methods directly from TeX code. 

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

`.tex` files can be compiled in the environment using the standard tools (i.e `pdflatex`). `texenv` also supports a preprocessor that can be used to call Python methods directly from TeX code. This is useful for generating figures and table data from python, or doing math that is difficult in LaTeX code. The example below shows a simple use case:

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

Compile on command line inside virtual environment:
```bash
texenv run example.tex
```

Full example:
[examples/macro_example/macro_example.tex](examples/macro_example/macro_example.tex)

The `run` command invokes the preprocessor, and then calls `pdflatex` on the post-processed `.tex` file. The synctex file is modified after running `pdflatex` so the intermediate file is transparent to synctex.

## Slideshows

`texenv` provides a simple way to generate PDF slideshow presentations directly from Python. Matplotlib figures, images, and LaTeX code (as strings in Python) can be assembled together into a slide using the `Presentation` class:

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

`texenv` is designed to work with the Latex Workshop extension in VSCode. Once the extension is installed, the following
settings should be added to the user `settings.json` file:

```json
    "latex-workshop.latex.recipes": [
        {
            "name": "texenv",
            "tools": [
                "texenv"
            ]
        }
    ],
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
    "latex-workshop.view.pdf.internal.synctex.keybinding": "double-click",
    "latex-workshop.latex.autoBuild.run": "onSave",
```

## License

texenv is licensed under the MIT License.