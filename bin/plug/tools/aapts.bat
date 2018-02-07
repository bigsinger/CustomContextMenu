@echo off
if "%PATH_BASE%" == "" set PATH_BASE=%PATH%
set PATH=%CD%;%PATH_BASE%;
"%~dp0\aapt.exe" %1 %2 %3 %4 %5 %6 %7 %8 %9
