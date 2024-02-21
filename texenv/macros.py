__all__ = ("figure", "table")


def figure(
    file: str = None,
    caption: str = None,
    width: str = None,
    twocolumn: str = False,
    placement: str = "h!",
    hspace: str = None,
):
    """
    Returns LaTeX code for a figure.

    Parameters:
    ----------
    """
    figure_s = "figure*" if twocolumn else "figure"

    s = r"\begin{" + figure_s + "}[" + placement + "]\n"
    s += r"\centering" + "\n"

    if hspace is not None:
        s += r"\hspace*{" + hspace + "}\n"
    s += r"\includegraphics"

    if width is not None:
        s += "[width=" + width + "]"
    s += "{" + file + "}\n"

    if caption is not None:
        s += (
            r"\caption{\small{"
            + caption
            + r"}\label{fig:"
            + file
            + r"}\nopagebreak}"
            + "\n"
        )
    s += r"\end{" + figure_s + "}\n"

    return s


def _check_table_header(row):
    return True if row[0].strip() == "-" * len(row[0].strip()) else False


def table(
    data: str,
    row: str = "\n",
    column: str = "|",
    caption: str = None,
    label: str = None,
    padding: int = 1.4,
    header_color: str = "gray!30!white",
    placement: str = "h",
    alignment: str = None,
    floating: bool = False,
):
    r"""
    Returns LaTeX code for a simple table. The xcolor package must be imported into any document that calls
    this macro:
    \usepackage[table]{xcolor}

    Parameters:
    ----------
    row: str
        delimiter for rows, default is the new line character '\n'
    column: str
        delimiter for columns, default is '|'
    caption: str
        caption placed below table content
    label: str
        label that references this table. 'tab:' will be appended to the label. For example,
        to reference a tabel with label='ex-table' use \ref{tab:ex-table}.
    padding: float
        padding around the cell contents, passed to the arraystretch macro
    header_color: str
        LaTeX color to use in the header. Defautls to grey. To turn off the shading, pass in 'white'.

    Examples:
    --------
    table(
    '''
        Setting         | Value
        ------------------------------
        Frequency Range | 20 MHz -- 3 GHz
        Sample points   | 1500
        IF Bandwidth    | 300 kHz
    '''
    )
    """
    if floating:
        s = r"\begin{table}[" + placement + "]\n\\begin{center}\n"
    else:
        s = "\n\\begin{center}\n"

    if label and caption:
        s += r"\caption{\label{tab:" + label + r"}{\small " + caption + "}}\n"

    s += r"\renewcommand{\arraystretch}{" + str(padding) + "}\n"

    s += r"\setlength\arrayrulewidth{1.5pt}"

    # escape any ampersands if the column delimeter is not an ampersand
    if column != "&":
        data.replace("&", "\\&")

    # split into rows
    rows = data.strip().split(row)
    # split into columns
    data_table = [r.split(column) for r in rows]

    table_s = ""
    max_col = 0
    # trim all cells and find maximum column count
    for i, r in enumerate(data_table):
        c_trim = [c.strip() for c in r]

        if len(c_trim) > max_col:
            max_col = len(c_trim)

        if _check_table_header(c_trim):
            pass

        elif len(c_trim) and len(c_trim[0]):
            # check for header
            if i < len(data_table) - 1 and _check_table_header(data_table[i + 1]):
                table_s += r"\rowcolor{" + header_color + r"} \hline" + "\n"

            table_s += " & ".join(c_trim) + r"\\\hline" + "\n"

    if alignment is None:
        s += r"\begin{tabular}{|" + " ".join(["l|"] * max_col) + "}\n"
    else:
        s += r"\begin{tabular}{" + alignment + +r"\\\hline" + "\n"

    s += table_s

    if floating:
        s += "\end{tabular}\n\end{center}\n\end{table}\n"
    else:
        s += "\end{tabular}\n\end{center}\n"

    return s.strip()


if __name__ == "__main__":
    d = table(
        """
            Setting         | Value 
            ------------------------------
            Frequency Range | 20 MHz -- 3 GHz
            Sample points   | 1500
            IF Bandwidth    | 300 kHz
        """
    )

    print(d)
