import numpy as np
from texenv.macros import figure

def stem_plot(ax, xd, yd, color="teal", markersize=4, linestyle="solid", label=None):
    import matplotlib.pyplot as plt

    """Create customized stem plot on axes with data (xd, yd)"""
    markerline, stemlines, baseline = ax.stem(xd, yd, label=label)
    plt.setp(stemlines, color=color, linestyle=linestyle)
    plt.setp(markerline, markersize=markersize, color=color)


def dtft(xn: np.ndarray, omega: np.ndarray):
    """
    Compute the DTFT of the discrete time signal x[n] over omega
    """
    n = np.arange(len(xn))
    omega_mesh, n_mesh = np.meshgrid(omega, n)

    # broadcast input sequence across all omega
    x_b = np.broadcast_to(xn[..., None], (len(n), len(omega)))
    # sum across all non-zero n
    Xw = np.sum(x_b * np.exp(-1j * omega_mesh * n_mesh), axis=0)

    return Xw

def figA(clean=False, width="3in", **kwargs):
    
    if clean == "False":
        return figure(file="figA.pdf", width=width, **kwargs)
    
    import matplotlib.pyplot as plt
    import numpy as np
    from pathlib import Path

    plt.rc("xtick", labelsize='x-small')
    plt.rc("ytick", labelsize='x-small')

    Hr_half = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    Hr = np.concatenate([Hr_half, np.flip(Hr_half)[:-1]])
    N = 15
    k = np.arange(N)
    omega_k = 2 * np.pi * k / N

    Hphs = np.exp(-1j * omega_k * (N - 1) / 2)
    Hw = Hr * Hphs
    hn = np.fft.ifft(Hw, N)

    omega_dft = np.linspace(0, 2 * np.pi, 1001)
    Hw_dft = dtft(hn.real, omega_dft)

    fig, ax1 = plt.subplots(1, 1, figsize=(5, 3))
    ax1.plot(omega_dft, np.abs(Hw_dft))
    stem_plot(ax1, omega_k, np.abs(Hw), color="grey")

    ax1.set_xticks(np.arange(0, 2 * np.pi + 2 * np.pi / 15, 2 * np.pi / 15))
    ax1.xaxis.set_major_formatter(lambda x, pos: "{:.1f}$\pi$".format(x / np.pi))
    ax1.set_xlabel("$\omega$")

    dir_ = Path(__file__).parent
    plt.tight_layout()
    fig.savefig(dir_ / "figA.pdf")

    return figure(file="figA.pdf", width=width, **kwargs)
