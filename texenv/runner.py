import subprocess
import shutil
import click
import gzip
import re
from pathlib import Path
import os

from texenv import TeXPreprocessor, utils


@click.command()
@click.argument("command")
@click.argument("filepath", required=False)
@click.option("--prompt", default=".venv")
def cli(command, filepath=None, prompt=None):

    if command == "init":
        utils.texenv_init(prompt)
        print('TeX environement setup complete. Please close this window and reactivate the environment for the changes to take effect.')
        return 
    
    elif command == "freeze":
        return 
    
    elif command == "sync":
        return 
    
    elif command == "run":
        filepath = Path(filepath).resolve()

        texpp = TeXPreprocessor(filepath)
        outfile = texpp.run()

        build_dir = outfile.parent

        proc = subprocess.run(
            'pdflatex --synctex=1 --interaction=nonstopmode --halt-on-error --output-directory="{}" {}'.format(
                build_dir, outfile
            ),
            stdout=subprocess.PIPE,
        )

        if proc.returncode:
            err = utils.parse_pdflatex_error(proc.stdout.decode("utf-8"))
            raise RuntimeError(
                "pdfTEX Error on line: {}. {} {}\n {}\n See full log at: {}".format(
                    err["line"],
                    err["msg"],
                    err["src"],
                    filepath,
                    build_dir / (filepath.stem + ".log"),
                )
            )

        else:
            gen_pdf = build_dir / (filepath.stem + ".pdf")
            gen_syn = build_dir / (filepath.stem + ".synctex.gz")

            out_pdf = filepath.with_suffix(".pdf")
            out_syn = filepath.with_suffix(".synctex.gz")

            # update the synctex file
            input_file_key = None
            updated_sync_data = ''
            with gzip.open(gen_syn, mode='rt') as f:
                for ln in f.readlines():
                    # look for the number that synctex assigned to the post-processed tex file.
                    if input_file_key is None:
                        m = re.match(r"^input:(\d+):"+str(outfile).replace('\\', '/').lower(), ln.lower())

                        if m is not None:
                            input_file_key = int(m.group(1))
                            ln = re.sub(f"build/{filepath.stem}", filepath.stem, ln)

                    else:
                        ptn = r"^.{},(\d+):".format(input_file_key)
                        m = re.match(ptn, ln)

                        if m is not None:
                            # line number of the postprocessed tex file
                            output_tex_lnum = int(m.group(1))
                            # line number of the input tex file before preprocessing
                            input_tex_lnum = texpp._syntex_map[output_tex_lnum-1]

                            sub_match = re.sub(f",{output_tex_lnum}", f",{input_tex_lnum}", m.group(0))

                            ln = sub_match + ln[m.span()[1]:]
                    
                    updated_sync_data += ln

            
            cmp_data = gzip.compress(updated_sync_data.encode('utf-8'))
            with open(out_syn, "wb+") as f:
                f.write(cmp_data)

            shutil.copyfile(gen_pdf, out_pdf)

    print("Output PDF written to {}".format(out_pdf))
    # out = subprocess.run("\"C:/Program Files/SumatraPDF/SumatraPDF-3.4.6-64.exe\" \"{}\" -inverse-search \"\"C:/ProgramData/Notepad++/notepad++.exe\" -n%l \"%f\"\"".format(out_pdf), shell=True)
