#pragma once

#include "stdafx.h"

extern WCHAR g_modulePath[MAX_PATH];
extern WCHAR g_mainMenuName[128];
extern WCHAR g_defaultRunFile[MAX_PATH];
extern int g_isDebug;

LPWSTR DupWide(LPCWSTR text);
LPWSTR DupUtf8AsWide(const char *text, int byteCount);
void FreeStringArray(LPWSTR *items, UINT count);

BOOL GetModuleDirectory(HMODULE module, LPWSTR buffer, DWORD cchBuffer);
HBITMAP LoadMenuBitmap(LPCWSTR fileName);
void ShutdownImageLoader(void);
BOOL RunCommandLine(LPCWSTR commandLine, LPCWSTR currentDir, DWORD waitMs);
BOOL CopyToClipboardText(LPCWSTR text);
void ShowTips(LPCWSTR tips, LPCWSTR title);
void LogMessage(LPCWSTR format, ...);

LPWSTR JoinPath(LPCWSTR baseDir, LPCWSTR path);
LPWSTR NormalizePath(LPCWSTR path);
LPWSTR GetParentPathAlloc(LPCWSTR path);
LPWSTR GetFileNameAlloc(LPCWSTR path);
LPWSTR GetFileExtAlloc(LPCWSTR path);
LPWSTR GetFileNameWithoutExtAlloc(LPCWSTR path);
LPWSTR GetLaunchCommandAlloc(LPCWSTR runFile);
LPWSTR ExpandArgumentsAlloc(LPCWSTR args, LPCWSTR filePath);
