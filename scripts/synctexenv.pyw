# main.py
import sys
from pathlib import Path
import pickle
import subprocess

# pythonw "C:\Users\rlyon\texenv\scripts\synctexenv.pyw" %f %l

if __name__ == "__main__":
    filepath, linenum = sys.argv[1:3]
    # print(filepath, linenum)

    filepath = Path(filepath)
    if filepath.with_suffix(".syncmap").exists():

        with open(filepath.with_suffix(".syncmap"), "rb") as f:
            syncmap = pickle.load(f)
        
        # get the line number of the file prior to preprocessing
        org_line_number = syncmap[int(linenum)] -1

        org_file_path = filepath.parent.parent / filepath.name
        # print(org_file_path, org_line_number)
        # input(r"C:\ProgramData\Notepad++\notepad++.exe -n%{} %{}".format(org_line_number, org_file_path))
        
        subprocess.Popen([r"C:\ProgramData\Notepad++\notepad++.exe", "-n{}".format(org_line_number), str(org_file_path)])

    