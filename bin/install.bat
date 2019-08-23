@echo off

set dir=%~dp0

rem 判断64位系统和32位系统
if /i %PROCESSOR_IDENTIFIER:~0,3%==x86 (
    echo 只支持Win64 不支持Win32
    pause
) else (
    regsvr32  %dir%CustomContextMenu.dll /CodeBase
)