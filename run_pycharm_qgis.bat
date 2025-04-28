@echo off
set OSGEO4W_ROOT=C:\Program Files\QGIS 3.40.5
call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
call "%OSGEO4W_ROOT%\bin\qt5_env.bat"
call "%OSGEO4W_ROOT%\bin\py3_env.bat"
set PATH=%OSGEO4W_ROOT%\apps\qgis-ltr\bin;%PATH%
set PYCHARM="C:\Program Files\JetBrains\PyCharm 2024.2.4\bin\pycharm64.exe"
start "" %PYCHARM%
