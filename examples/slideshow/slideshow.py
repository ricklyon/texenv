import numpy as np
import matplotlib.pyplot as plt
from texenv import Presentation, datatable
from pathlib import Path

dir_ = Path(__file__).parent

plt.style.use("ggplot")
plt.rc("font", size=7)

# create an example figure
fig, ax = plt.subplots(1, 1)
x1 = np.linspace(-2 * np.pi, 2 * np.pi, 1000)
ax.plot(x1, np.cos(x1) * np.sin(x1) ** 2)

fig2, ax = plt.subplots(1, 1)
x1 = np.linspace(-2 * np.pi, 2 * np.pi, 1000)
ax.plot(x1, np.cos(3 * x1) * np.sin(x1) ** 2)

pres = Presentation(dir_ / "example_slides.pdf")
# optionally provide a template path to a .tex file:
# pres = Presentation(dir_ / "example_slides.pdf", template_path=template.tex)

# text to place on slide. This is interpreted as an enumerate list if \item appears first in the string.
# Otherwise, the text is inserted directly as LaTeX code and supports math functions etc...
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

# add the content to the first slide. The layout will be a 2x2 grid, with the figure centered along both rows in the
# second column. The text and table will split the first column. 
pres.add_slide(
    content=[[text, fig], 
             [table, None]], 
    title="Example TeX Slides", 
    width_ratio=(1, 2) # make the second column twice as wide as the first column.
)

pres.save()
