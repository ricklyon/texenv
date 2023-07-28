
def ieeeformat(fontsize='10', mode='technote', top=0.6, bottom=0.4, left=0.7, right=0.7):

    # checks
    font_s = f'{fontsize}pt' if fontsize.isnumeric() else fontsize

    modes = ['conference', 'journal', 'technote', 'peerreview', 'peerreviewca']

    if mode not in modes:
        raise TypeError(f'invalid ieee mode: {mode}. Valid options are {modes}')

    s = r'\documentclass['+font_s+','+mode+']{IEEEtran}\n'

    packages = ['cite', 'amsmath', 'amssymb', 'amsfonts', 'algorithmic', 'graphicx', 'textcomp',
    'xcolor', 'base', 'stfloats']

    for p in packages:
        s += '\\usepackage{'+p+'}\n'

    s+='\\geometry{portrait,'
    s+= f'top={top}in, bottom={bottom}in, left={left}in, right={right}in,includefoot'+'}\n'

    s+='\\begin{document}\n\n'

    return s

def simple(arg1, arg2='default'):
    return str(arg1) + str(arg2)

def titleblock(title, subtitle=None, author=None, date=None):
    s = r'\title{'+title+'}\n'
    s+= r'\author{'

    if subtitle is not None:
        s+= subtitle
    if author is not None:
        nl = '' if subtitle is None else r' \\'
        s+= nl + author
    if date is not None:
        nl = '' if author is None and subtitle is None else r' \\'
        s+= nl + date
    else:
        s+= r' \\ \today'
    s += '}\maketitle'

    return s

def abstract(text, title=None):
    title = 'Abstract' if title is None else title
    s=r'\noindent\textbf{\textit{'+title+'}--- '
    s+= text.strip()+'}'
    return s

def figure(file=None, caption=None, width=None, twocolumn=False, placement='h', hspace=None):

    figure_s = 'figure*' if twocolumn else 'figure'

    s = r'\begin{'+figure_s+'}['+placement +']\n'
    s+= r'\centering'+'\n'

    if hspace is not None:
        s += r'\hspace*{'+hspace+'}\n'
    s+= r'\includegraphics'

    if width is not None:
        s+='[width='+ width+']'
    s+= '{'+file+'}\n'

    if caption is not None:
        s+= r'\caption{\small{'+caption+r'}\label{fig:'+file+r'}\nopagebreak}'+'\n'
    s+=r'\end{'+figure_s +'}\n'

    return s

def _check_table_header(row):
    return True if row[0].strip() == '-'*len(row[0].strip()) else False

def table(data, row='\n', column='|', placement='h', 
          caption=None, label=None, padding:int=1.4,
          header_color='gray!30!white', alignment=None
):
    s = r'\begin{table}['+placement+']\n\\begin{center}\n'

    if label and caption:
        s += r'\caption{\label{tab:'+label+r'}{\small '+caption+'}}\n'

    s += r'\renewcommand{\arraystretch}{'+str(padding)+'}\n'

    # escape any ampersands if the column delimeter is not an ampersand
    if column != '&':
        data.replace('&', '\\&')

    # split into rows
    rows = data.strip().split(row)
    # split into columns
    data_table = [r.split(column) for r in rows]
    
    table_s = ''
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
            if i < len(data_table) -1 and _check_table_header(data_table[i+1]):
                table_s += r'\rowcolor{'+header_color+'}\n'

            table_s += ' & '.join(c_trim) + r'\\\hline' + '\n'

    if alignment is None:
        s += r'\begin{tabular}{'+ ' '.join(['l']*max_col) + '}\n'
    else:
        s += r'\begin{tabular}{'+ alignment + '}\n'

    s += table_s

    s+='\end{tabular}\n\end{center}\n\end{table}\n'

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

    f = figure(file='img/test', caption='test', width='3in')
    print(f)
    # d = ieeeformat()
    
    # print(d)
