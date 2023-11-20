# texenv

Compile LaTeX documents inside a virtual environment and call Python methods from LaTeX code.

## Installation

```bash
pip install texenv
```

## Usage

Contents of `example.tex`:
```tex
\documentclass{article}

\import\texenv as \pym
\pydef\test true

\begin{document}
   
   \pym\simple[argument1, arg2=\test]
   
\end{document}
```
Contents of `pymacros.py`, located in the same directory as `example.tex`:
```python
def simple(arg1: str, arg2: str = 'default') -> str:
    return str(arg1) + str(arg2)
```

Compile on command line inside virtual environment:
```bash
texenv example.tex
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
            "%DOC_EXT%"
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