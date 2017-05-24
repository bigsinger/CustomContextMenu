set dir=%~dp0

%dir%RegAsm.exe /unregister %dir%bin/CustomContextMenu.dll /CodeBase

taskkill /f /im explorer.exe

explorer.exe