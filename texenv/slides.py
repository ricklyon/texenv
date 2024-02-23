from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path
import shutil

import subprocess
import webbrowser

from . import utils

dir_ = Path(__file__).parent


def datatable(
    data: np.ndarray,
    header_row: list = None,
    header_column: list = None,
    formatter="{}",
    padding: int = 1.4,
    header_color: str = "gray!30!white",
    alignment: str = None,
    fontsize=(12, 14),
):
    r"""
    Returns LaTeX code for a simple table. The xcolor package must be imported into the template that calls
    this macro:
    \usepackage[table]{xcolor}

    Parameters:
    ----------
    data: np.ndarray
        1D or 2D array of data.
    header_row: list
        list of string values to place in first row of table. Length must match the number of data columns.
    header_column: list
        list of string values to place in the first column of table. Length must match the number of data rows.
    formatter: str
        string formatter used on each value in the data before placing into table.
    header_color: str
        xcolor string value, default is light gray.
    alignment: str
        tabular alignment string, i.e. c | p{1in} | c. Must match the number of columns.
    fontsize: tuple, optional:
        2-tuple of the text font size and the line spacing, default is (12pt, 14pt)

    Returns:
    --------
    str:
        LaTeX code for table.
    """

    data = np.atleast_2d(data)

    header_color_s = r" \cellcolor{" + header_color + "} "

    s = f"\\fontsize{{{fontsize[0]}}}{{{fontsize[1]:.1f}}}\\selectfont \n"
    s += r"\centering \renewcommand{\arraystretch}{" + str(padding) + "}\n"
    s += r"\setlength\arrayrulewidth{1.5pt}"

    column_num = data.shape[1]
    if header_column is not None:
        column_num += 1

    alignment_s = " ".join(["l|"] * column_num)[:-1] if alignment is None else alignment

    s += "\n" + "\\begin{tabular}{|" + alignment_s + "|} \\hline  \n"

    # place header row if provided
    if header_row is not None:
        # s += r"\rowcolor{" + header_color + r"} \hline" + "\n"
        s += (
            " & ".join(header_color_s + str(cell) for cell in header_row)
            + " \\\\ \\hline \n "
        )

    for i, r in enumerate(data):
        # insert column header at the first cell of each row
        if header_column is not None:
            s += r" \cellcolor{" + header_color + "} " + str(header_column[i]) + " & "

        s += " & ".join(formatter.format(cell) for cell in r) + " \\\\ \\hline \n "

    s += "\end{tabular}\n"

    return s


class Presentation(object):
    def __init__(
        self, filepath: str, fontsize=tuple((18, 20)), template_path: Path = None
    ):
        """
        Creates a powerpoint PDF using LaTeX. Requires pdflatex to be installed on the system with the following
        packages:

        geometry
        graphicx
        fancyhdr
        xcolor

        Parameters:
        -----------
        filepath: Path | str
            filepath of output PDF
        fontsize: tuple, optional:
            2-tuple of the text font size and the line spacing, default is (18pt, 20pt)
        template_path: Path, optional
            path to a template .tex file
        """
        # width and height of the usuable content area of each slide, in inches
        self.width_in = 12
        self.height_in = 6.0

        # current slide index
        self.slide_counter = 0
        self.filepath = Path(filepath)
        self.fontsize = fontsize
        self.title_voffset = 0.2

        # temporary directory for build files
        self.build_dir = filepath.parent / (filepath.stem + "_build")
        self.build_dir.mkdir(parents=True, exist_ok=True)

        # template file
        if template_path is None:
            template_path = dir_ / "templates/default.tex"
        with open(template_path) as template:
            self.data = template.read()

        # copy template images to build folder
        template_dir = str(template_path.parent).replace("\\", "/")

        # insert the graphics path for the template img into the document data
        self.data = self.data.replace(
            r"\begin{document}",
            r"\graphicspath{{" + template_dir + "}}\n\n\\begin{document}",
        )

    def save(self, clean: bool = True):
        """
        Writes the slide data to a temporary .tex file and generates the PDF.

        Parameters:
        -----------
        clean: bool
            If true, remove the temporary build directory after a successful save.
            If save fails, the temporary directory is not removed, even if clean is True.
        """
        texfilepath = self.build_dir / (self.filepath.stem + ".tex")

        with open(texfilepath, "w+") as output:
            output.write(self.data + "\n\\end{document}")

        # generate PDF by running pdflatex
        proc = subprocess.run(
            'pdflatex --interaction=nonstopmode --halt-on-error --output-directory="{}" {}'.format(
                self.build_dir, texfilepath
            ),
            stdout=subprocess.PIPE,
        )

        if proc.returncode:
            raise RuntimeError(
                "pdflatex failed to compile document. Log file at {}".format(
                    self.build_dir / (self.filepath.stem + ".log")
                )
            )
        else:
            # copy the generated PDF from the build directory to the specified path
            shutil.copyfile(self.build_dir / self.filepath.name, self.filepath)
            print(f"Presentation saved to: {self.filepath}")
            if clean:
                # remove the temporary directory
                try:
                    shutil.rmtree(self.build_dir)
                except Exception:
                    pass

    def open(self):
        self.save()
        webbrowser.open(str(self.filepath))

    def open_vscode(self):
        self.save()
        subprocess.run("code " + str(self.filepath), shell=True)

    def format_content(self, text):
        """
        Formats text content so it appears as a bulleted list if \item is in the text.
        """
        if text.strip()[0:5] == r"\item":
            text = r"\begin{itemize} " + text + r" \end{itemize}"

        font_str = f"\\fontsize{{{self.fontsize[0]}}}{{{self.fontsize[1]:.1f}}}\\selectfont \\raggedright "

        return r"\vspace{0.2in}" + font_str + text

    def add_slide(
        self,
        content: np.ndarray,
        title: str = "",
        width_ratio: tuple = None,
        height_ratio: tuple = None,
    ) -> None:
        """
        Add a slide to the presentation.

        Parameters:
        -----------
        content: ArrayLike
            Matrix or list of content to place on slide, maximum number of dimensions must be 2.
            Supported content types are:
                1. pathlib.Path objects to a image file
                2. matplotlib Figure objects
                3. string of text. This is treated as direct LaTeX code, supports math mode, text formatting etc...
                   Make sure to use raw strings (or r-strings) when using LaTeX macros or escape backslashes
                   with another backslash, i.e. use r"\textbf{Bolded Text}" or "\\textbf{Bolded Text}".
            The place of the content in the matrix determines it's position on the slide. For example,
                fig1, ax = plt.subplots(...)
                ...
                content = [[fig1, fig2],
                           [fig3, fig4]]
            To create a cell that spans multiple rows, put None in the other row placeholder(s):
                content = [[fig1, fig2],
                           [None, fig4]]
            This would center fig1 in the first column, while fig2 and fig4 would split the second column.
            To not center fig1 in the column, provide an empty string instead of None in the other row:
                content = [[fig1, fig2],
                           ["",   fig4]]

        title: str, option
            slide title to place in header

        width_ratio: tuple, optional
            tuple of ratios to scale the columns widths by. For example, (2, 1, 1) would make the first column
            twice as wide as the last two columns. Default to equal column widths.

        height_ratio: tuple, optional
            tuple of ratios to scale the row heights by. Defaults to equal row heights.

        """
        content = np.atleast_2d(content).T
        # content is transposed so the shape is columns x rows
        n_col, n_row = content.shape

        if width_ratio is not None and len(width_ratio) != n_col:
            raise ValueError(
                f"Length of width_ratio must match the number of content columns ({n_col})."
            )

        if height_ratio is not None and len(height_ratio) != n_row:
            raise ValueError(
                f"Length of width_ratio must match the number of content columns ({n_row})."
            )

        # width of each column in inches
        width_columns = self.width_in / n_col
        # height of each row in inches
        height_rows = self.height_in / n_row

        # scale each column by the width ratio and normalize so the total width is the slide width
        if width_ratio is not None:
            width_columns = (self.width_in / n_col) * np.array(width_ratio)
            width_columns *= self.width_in / np.sum(width_columns)
        else:
            width_columns = np.ones(n_col) * (self.width_in / n_col)

        # scale each row by the height ratio and normalize so the total height is the slide height
        if height_ratio is not None:
            height_rows = (self.height_in / n_row) * np.array(height_ratio)
            height_rows *= self.height_in / np.sum(height_rows)
        else:
            height_rows = np.ones(n_row) * (self.height_in / n_row)

        slide_data = self._generate_slide_data(content, width_columns, height_rows)

        # add title in the header for the page
        title_data = (
            r"\chead{\Huge \vspace{"
            + f"{self.title_voffset:.2f}"
            + r"in} "
            + title
            + r"}"
        )
        # add slide data to the presentation
        self.data += title_data + "\n" + slide_data + "\n\n\\pagebreak\n\n"
        self.slide_counter += 1

    def _generate_slide_data(self, content, width_columns, height_rows):
        """
        Generate LaTeX data for a 2D grid of figure, images, and text
        """
        slide_data = ""
        fig_counter = 0
        slide_img_path = self.build_dir / f"slide{self.slide_counter}"
        slide_img_path.mkdir(parents=True, exist_ok=True)

        # get full height of all rows
        height_in = np.sum(height_rows)

        for i, col in enumerate(content):
            col_data = ""
            w_col = width_columns[i]
            # center content vertically in the column unless the content is text
            v_align = "t" if len(col) == 1 and isinstance(col[0], str) else "c"
            # create block for entire column (full height)
            # \begin{minipage}[b][height_in][v_align]{w_col}
            col_data += f"\n\\begin{{minipage}}[b][{height_in:.2f}in][{v_align}]{{{w_col:.2f}in}}"

            h_rows = np.array(height_rows)
            # if only the first row has data, set the other rows to 0 height so the first item is centered
            # in the column
            if len(col) > 1 and np.all(col[1:] == None):
                h_rows[0] = height_in
                h_rows[1:] = 0

            for j, item in enumerate(col):
                row_data = ""
                h_row = h_rows[j]
                # center content vertically in the column unless the content is text
                v_align = "t" if isinstance(item, str) else "c"

                # skip rows with 0 height
                if h_row <= 0:
                    continue

                # create block for row inside the column block (subdivided heights).
                # \begin{minipage}[b][h_row][v_align]{w_col}
                row_data += f"\n\t\\begin{{minipage}}[b][{h_row:.2f}in][{v_align}]{{{w_col:.2f}in}}"

                if isinstance(item, str):
                    # if item is str, treat it as direct LaTeX content
                    text = self.format_content(item)
                    row_data += "\n" + text
                else:
                    if item is None:
                        row_data += "\n\t\end{minipage} \\\\ "
                        col_data += row_data
                        continue

                    elif isinstance(item, Path):
                        # if item is a path to an image file, copy the image to the temporary build directory
                        # and insert into the doc with includegraphics macro. This macro sets the height or width,
                        shutil.copyfile(item, slide_img_path / item.name)

                        w_im, h_im = utils.get_image_size(item, normalize=True)
                        relative_path = f"slide{self.slide_counter}/" + item.stem
                    elif isinstance(item, plt.Figure):
                        # if item is a mpl Figure, get the fig size and save to the build folder
                        w_im, h_im = utils.get_figure_size(item, normalize=True)

                        try:
                            item.tight_layout()
                        except Exception:
                            pass

                        item.savefig(slide_img_path / f"fig{fig_counter}.pdf")
                        relative_path = (
                            f"slide{self.slide_counter}/fig{fig_counter}.pdf"
                        )
                        fig_counter += 1
                    else:
                        raise ValueError(f"Unrecognized content type: {type(item)}")

                    # get normalized values for the minipage size
                    w_col_n, h_row_n = utils.normalize_dimensions(w_col, h_row)

                    # get the width and heights normalized to the minipage sizes
                    w_im_n = w_im / w_col_n
                    h_im_n = h_im / h_row_n

                    # constrain the width if the normalized image width is larger than the height
                    im_dim_str = (
                        f"width={w_col:.2f}in"
                        if w_im_n > h_im_n
                        else f"height={h_row:.2f}in"
                    )

                    row_data += f"\n\t\centering \includegraphics[{im_dim_str}]{{{relative_path}}}"

                row_data += "\n\t\end{minipage}"

                if j < (len(col) - 1) and not np.all(col[j + 1 :] == None):
                    row_data += " \\\\ "

                col_data += row_data

            col_data += "\n\end{minipage}"
            slide_data += col_data

        return slide_data
