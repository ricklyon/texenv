import numpy as np
import matplotlib.pyplot as plt
from texenv import Presentation, datatable
from pathlib import Path

dir_ = Path(__file__).parent

plt.style.use("ggplot")
plt.rc("font", size=7)

fig, ax = plt.subplots(1, 1)
x1 = np.linspace(-2 * np.pi, 2 * np.pi, 1000)
ax.plot(x1, np.cos(x1) * np.sin(x1) ** 2)

fig2, ax = plt.subplots(1, 1)
x1 = np.linspace(-2 * np.pi, 2 * np.pi, 1000)
ax.plot(x1, np.cos(3 * x1) * np.sin(x1) ** 2)

plt.close("all")
pres = Presentation(dir_ / "example_slides.pdf")

text = r"""
\item Bullet 1
\item[] Bullet 2
\item[--] Bullet 3 
"""

data = np.arange(16).reshape((4, 4))

table = datatable(
    data, header_row=[f"Header {i}" for i in range(4)], formatter="{:.2f}"
)

pres.add_slide(
    content=[[text, fig], [table, None]], title="Example TeX Slides", width_ratio=(1, 2)
)

pres.save()
