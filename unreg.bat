@echo off

set dir=%~dp0

rem 判断64位系统和32位系统
if /i %PROCESSOR_IDENTIFIER:~0,3%==x86 (
    echo 32位操作系统
    %windir%\Microsoft.NET\Framework\v4.0.30319\RegAsm.exe /unregister %dir%bin/CustomContextMenu.dll /CodeBase
) else (
    echo 64位操作系统
    %windir%\Microsoft.NET\Framework64\v4.0.30319\RegAsm.exe /unregister %dir%bin/CustomContextMenu.dll /CodeBase
)

taskkill /f /im explorer.exe

explorer.exe