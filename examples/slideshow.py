import numpy as np
import matplotlib.pyplot as plt
from texenv import Presentation
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

pres = Presentation(dir_ / "example_slides.pdf")

text = r"""
\item Bullet 1
\item[] Bullet 2
\item[--] Bullet 3 
"""
text2 = r"""\[ \Delta t \le {1 \over  v_p \sqrt{ \Big({1 \over \Delta x} \Big)^2 + \Big({1 \over \Delta z}\Big)^2 }}\]
"""

pres.add_slide(
    content=[[text, fig], [text2, None]], title="Example TeX Slides", width_ratio=(1, 2)
)

pres.save(clean=False)
