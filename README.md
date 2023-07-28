# texenv

Compile LaTeX documents inside a virtual environment and call Python methods from LaTeX code.

## Installation

```bash
pip install texenv
```

## Usage

example.tex
```tex
\documentclass{article}

\import\texenv as \pym
\pydef\test true

\begin{document}
   
   \pym\simple[argument1, arg2=\test]
   
	Hello world!!\ \
\end{document}
```
texenv method:
```python
def simple(arg1, arg2='default'):
    return str(arg1) + str(arg2)
```

Compile on command line inside virtual environment:
```bash
texenv example.tex
```

## License

texenv is licensed under the MIT License.