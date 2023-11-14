@echo off
echo Generating PDF...
cd /d %~dp1

call "C:\Users\rlyon\texenv\.venv\Scripts\activate.bat"

texenv %1

start "openPDF" "C:\ProgramData\SumatraPDF\SumatraPDF-3.3.3-64.exe" "%~n1.pdf" -inverse-search "pythonw "C:\Users\rlyon\texenv\scripts\synctexenv.pyw" "%%f" %%l" -reuse-instance

C:\ProgramData\Notepad++\notepad++.exe


