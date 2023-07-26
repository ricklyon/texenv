# envtex

Compile LaTeX documents inside a virtual environment and call Python methods from LaTeX code.

## Installation

```bash
pip install envtex
```

## Usage

example.tex
```tex
\documentclass{article}

\import\envtex as \pym
\pydef\test true

\begin{document}
   
   \pym\simple[argument1, arg2=\test]
   
	Hello world!!\ \
\end{document}
```
envtex method:
```python
def simple(arg1, arg2='default'):
    return str(arg1) + str(arg2)
```

Compile on command line inside virtual environment:
```bash
envtex example.tex
```

## License

envtex is licensed under the MIT License.