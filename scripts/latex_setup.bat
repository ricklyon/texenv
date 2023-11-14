echo off
cd /d %~dp0

set nppinstall=C:\ProgramData\Notepad++
set pdfinstall=C:\ProgramData\SumatraPDF

set npppluginconfig=C:\ProgramData\Notepad++\plugins\Config\npes_saved.txt

>%npppluginconfig% echo ::pdf2tex
>>%npppluginconfig% echo NPP_SAVE
>>%npppluginconfig% echo "%CD%/tex2pdf.bat" "$(FULL_CURRENT_PATH)"
>>%npppluginconfig% echo ::syncpdf
>>%npppluginconfig% echo NPP_CONSOLE -
>>%npppluginconfig% echo "%CD%/pdfsync.bat" "$(FULL_CURRENT_PATH)" "$(CURRENT_LINE)"

reg delete HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.tex /f >nul 2>&1
reg delete HKEY_CURRENT_USER\Software\Classes\texfile /f >nul 2>&1
reg add HKEY_CURRENT_USER\Software\Classes\.tex /d texfile /f
reg add HKEY_CURRENT_USER\Software\Classes\texfile\DefaultIcon /d "\"%CD%/resources/default.ico\"" /f
reg add HKEY_CURRENT_USER\Software\Classes\texfile\shell\open\command /d "miktex-texworks.exe \"%%1\"" /f
reg add HKEY_CURRENT_USER\Software\Classes\texfile\shell\pdfconversion /d "Convert To PDF" /f
reg add HKEY_CURRENT_USER\Software\Classes\texfile\shell\pdfconversion /v Icon /d "\"%CD%/resources/PDFFile_8.ico\",0" /f
reg add HKEY_CURRENT_USER\Software\Classes\texfile\shell\pdfconversion\command /d "\"%CD%/tex2pdf.bat\" \"%%1\"" /f

reg add HKEY_CURRENT_USER\Software\Classes\texfile\shell\editwnotepad /d "Edit With Notepad" /f
reg add HKEY_CURRENT_USER\Software\Classes\texfile\shell\editwnotepad /v Icon /d "\"%CD%/resources/default.ico\"" /f
reg add HKEY_CURRENT_USER\Software\Classes\texfile\shell\editwnotepad\command /d "\"C:\ProgramData\Notepad++\notepad++.exe\" \"%%1\"" /f

pause