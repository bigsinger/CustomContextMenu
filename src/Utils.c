#include "stdafx.h"
#include "Const.h"
#include "Utils.h"

WCHAR g_modulePath[MAX_PATH];
WCHAR g_mainMenuName[128] = L"Custom Context Menu";
WCHAR g_defaultRunFile[MAX_PATH];
int g_isDebug = 0;

typedef INT GpStatus;
typedef struct GpBitmap GpBitmap;
typedef struct GpImage GpImage;
typedef struct GdiplusStartupInputC {
    UINT32 GdiplusVersion;
    void *DebugEventCallback;
    BOOL SuppressBackgroundThread;
    BOOL SuppressExternalCodecs;
} GdiplusStartupInputC;

GpStatus __stdcall GdiplusStartup(ULONG_PTR *token, const GdiplusStartupInputC *input, void *output);
void __stdcall GdiplusShutdown(ULONG_PTR token);
GpStatus __stdcall GdipCreateBitmapFromFile(const WCHAR *filename, GpBitmap **bitmap);
GpStatus __stdcall GdipCreateHBITMAPFromBitmap(GpBitmap *bitmap, HBITMAP *hbmReturn, DWORD background);
GpStatus __stdcall GdipDisposeImage(GpImage *image);

static INIT_ONCE g_gdiplusOnce = INIT_ONCE_STATIC_INIT;
static ULONG_PTR g_gdiplusToken = 0;
static BOOL g_gdiplusReady = FALSE;

typedef struct WideBuffer {
    LPWSTR data;
    size_t length;
    size_t capacity;
} WideBuffer;

static BOOL CALLBACK InitGdiplusOnce(PINIT_ONCE initOnce, PVOID parameter, PVOID *context)
{
    GdiplusStartupInputC input;

    UNREFERENCED_PARAMETER(initOnce);
    UNREFERENCED_PARAMETER(parameter);
    UNREFERENCED_PARAMETER(context);

    ZeroMemory(&input, sizeof(input));
    input.GdiplusVersion = 1;
    g_gdiplusReady = GdiplusStartup(&g_gdiplusToken, &input, NULL) == 0;
    return TRUE;
}

static BOOL EnsureGdiplus(void)
{
    InitOnceExecuteOnce(&g_gdiplusOnce, InitGdiplusOnce, NULL, NULL);
    return g_gdiplusReady;
}

void ShutdownImageLoader(void)
{
    if (g_gdiplusReady && g_gdiplusToken != 0) {
        GdiplusShutdown(g_gdiplusToken);
        g_gdiplusToken = 0;
        g_gdiplusReady = FALSE;
    }
}

static BOOL BufferReserve(WideBuffer *buffer, size_t extra)
{
    size_t needed;
    size_t capacity;
    LPWSTR next;

    if (!buffer) {
        return FALSE;
    }

    needed = buffer->length + extra + 1;
    if (needed <= buffer->capacity) {
        return TRUE;
    }

    capacity = buffer->capacity ? buffer->capacity : 64;
    while (capacity < needed) {
        if (capacity > ((size_t)-1) / 2) {
            return FALSE;
        }
        capacity *= 2;
    }

    next = (LPWSTR)realloc(buffer->data, capacity * sizeof(WCHAR));
    if (!next) {
        return FALSE;
    }

    buffer->data = next;
    buffer->capacity = capacity;
    return TRUE;
}

static BOOL BufferAppendN(WideBuffer *buffer, LPCWSTR text, size_t count)
{
    if (!text || count == 0) {
        return TRUE;
    }
    if (!BufferReserve(buffer, count)) {
        return FALSE;
    }
    memcpy(buffer->data + buffer->length, text, count * sizeof(WCHAR));
    buffer->length += count;
    buffer->data[buffer->length] = L'\0';
    return TRUE;
}

static BOOL BufferAppend(WideBuffer *buffer, LPCWSTR text)
{
    return BufferAppendN(buffer, text, text ? wcslen(text) : 0);
}

static BOOL BufferAppendChar(WideBuffer *buffer, WCHAR ch)
{
    if (!BufferReserve(buffer, 1)) {
        return FALSE;
    }
    buffer->data[buffer->length++] = ch;
    buffer->data[buffer->length] = L'\0';
    return TRUE;
}

static LPWSTR BufferDetach(WideBuffer *buffer)
{
    LPWSTR result;

    if (!buffer->data) {
        return DupWide(L"");
    }
    result = buffer->data;
    buffer->data = NULL;
    buffer->length = 0;
    buffer->capacity = 0;
    return result;
}

LPWSTR DupWide(LPCWSTR text)
{
    size_t chars;
    LPWSTR copy;

    if (!text) {
        text = L"";
    }

    chars = wcslen(text) + 1;
    copy = (LPWSTR)malloc(chars * sizeof(WCHAR));
    if (!copy) {
        return NULL;
    }
    memcpy(copy, text, chars * sizeof(WCHAR));
    return copy;
}

LPWSTR DupUtf8AsWide(const char *text, int byteCount)
{
    int chars;
    LPWSTR wide;

    if (!text) {
        return DupWide(L"");
    }

    chars = MultiByteToWideChar(CP_UTF8, 0, text, byteCount, NULL, 0);
    if (chars <= 0) {
        return DupWide(L"");
    }

    wide = (LPWSTR)calloc((size_t)chars + 1, sizeof(WCHAR));
    if (!wide) {
        return NULL;
    }

    if (!MultiByteToWideChar(CP_UTF8, 0, text, byteCount, wide, chars)) {
        free(wide);
        return DupWide(L"");
    }

    wide[chars] = L'\0';
    return wide;
}

void FreeStringArray(LPWSTR *items, UINT count)
{
    UINT i;

    if (!items) {
        return;
    }

    for (i = 0; i < count; ++i) {
        free(items[i]);
    }
    free(items);
}

BOOL GetModuleDirectory(HMODULE module, LPWSTR buffer, DWORD cchBuffer)
{
    DWORD length;
    LPWSTR slash;

    if (!buffer || cchBuffer == 0) {
        return FALSE;
    }

    length = GetModuleFileNameW(module, buffer, cchBuffer);
    if (length == 0 || length >= cchBuffer) {
        buffer[0] = L'\0';
        return FALSE;
    }

    slash = wcsrchr(buffer, L'\\');
    if (!slash) {
        buffer[0] = L'\0';
        return FALSE;
    }

    slash[1] = L'\0';
    return TRUE;
}

static BOOL HasPathSeparator(LPCWSTR path)
{
    return path && (wcschr(path, L'\\') || wcschr(path, L'/'));
}

static BOOL IsAbsolutePath(LPCWSTR path)
{
    if (!path || !path[0]) {
        return FALSE;
    }
    if (path[0] == L'\\' || path[0] == L'/') {
        return TRUE;
    }
    return iswalpha(path[0]) && path[1] == L':';
}

LPWSTR JoinPath(LPCWSTR baseDir, LPCWSTR path)
{
    WideBuffer buffer = { 0 };

    if (!path) {
        return DupWide(L"");
    }

    if (IsAbsolutePath(path) || !HasPathSeparator(path)) {
        return DupWide(path);
    }

    if (!BufferAppend(&buffer, baseDir ? baseDir : L"") ||
        !BufferAppend(&buffer, path)) {
        free(buffer.data);
        return NULL;
    }

    return BufferDetach(&buffer);
}

LPWSTR NormalizePath(LPCWSTR path)
{
    DWORD needed;
    LPWSTR full;

    if (!path || !path[0]) {
        return DupWide(L"");
    }

    needed = GetFullPathNameW(path, 0, NULL, NULL);
    if (needed == 0) {
        return DupWide(path);
    }

    full = (LPWSTR)calloc(needed + 1, sizeof(WCHAR));
    if (!full) {
        return NULL;
    }

    if (!GetFullPathNameW(path, needed, full, NULL)) {
        free(full);
        return DupWide(path);
    }

    return full;
}

LPWSTR GetParentPathAlloc(LPCWSTR path)
{
    LPWSTR copy;
    LPWSTR slash;
    size_t length;

    copy = DupWide(path);
    if (!copy) {
        return NULL;
    }

    for (length = wcslen(copy); length > 0; --length) {
        if (copy[length - 1] == L'/') {
            copy[length - 1] = L'\\';
        }
    }

    length = wcslen(copy);
    while (length > 0 && copy[length - 1] == L'\\') {
        copy[--length] = L'\0';
    }

    slash = wcsrchr(copy, L'\\');
    if (!slash) {
        copy[0] = L'\0';
        return copy;
    }

    slash[1] = L'\0';
    return copy;
}

LPWSTR GetFileNameAlloc(LPCWSTR path)
{
    LPCWSTR slash1;
    LPCWSTR slash2;
    LPCWSTR name;

    if (!path) {
        return DupWide(L"");
    }

    slash1 = wcsrchr(path, L'\\');
    slash2 = wcsrchr(path, L'/');
    name = path;
    if (slash1 && slash1 + 1 > name) {
        name = slash1 + 1;
    }
    if (slash2 && slash2 + 1 > name) {
        name = slash2 + 1;
    }
    return DupWide(name);
}

LPWSTR GetFileExtAlloc(LPCWSTR path)
{
    LPWSTR name;
    LPWSTR dot;
    LPWSTR result;

    name = GetFileNameAlloc(path);
    if (!name) {
        return NULL;
    }
    dot = wcsrchr(name, L'.');
    result = DupWide(dot ? dot : L"");
    free(name);
    return result;
}

LPWSTR GetFileNameWithoutExtAlloc(LPCWSTR path)
{
    LPWSTR name;
    LPWSTR dot;

    name = GetFileNameAlloc(path);
    if (!name) {
        return NULL;
    }

    dot = wcsrchr(name, L'.');
    if (dot && dot != name) {
        *dot = L'\0';
    }
    return name;
}

static BOOL EndsWithNoCase(LPCWSTR text, LPCWSTR suffix)
{
    size_t textLen;
    size_t suffixLen;

    if (!text || !suffix) {
        return FALSE;
    }

    textLen = wcslen(text);
    suffixLen = wcslen(suffix);
    if (suffixLen > textLen) {
        return FALSE;
    }

    return _wcsicmp(text + textLen - suffixLen, suffix) == 0;
}

static BOOL AppendQuoted(WideBuffer *buffer, LPCWSTR text)
{
    return BufferAppendChar(buffer, L'"') &&
        BufferAppend(buffer, text ? text : L"") &&
        BufferAppendChar(buffer, L'"');
}

LPWSTR GetLaunchCommandAlloc(LPCWSTR runFile)
{
    WideBuffer buffer = { 0 };

    if (!runFile || !runFile[0]) {
        return DupWide(L"");
    }

    if (EndsWithNoCase(runFile, L".jar")) {
        if (!BufferAppend(&buffer, L"java -jar ") ||
            !AppendQuoted(&buffer, runFile)) {
            free(buffer.data);
            return NULL;
        }
        return BufferDetach(&buffer);
    }

    if (EndsWithNoCase(runFile, L".py")) {
        if (!BufferAppend(&buffer, L"python ") ||
            !AppendQuoted(&buffer, runFile)) {
            free(buffer.data);
            return NULL;
        }
        return BufferDetach(&buffer);
    }

    if (EndsWithNoCase(runFile, L".lua")) {
        WideBuffer runLuaPath = { 0 };
        if (!BufferAppend(&runLuaPath, g_modulePath) ||
            !BufferAppend(&runLuaPath, L"runLua.exe")) {
            free(runLuaPath.data);
            return NULL;
        }
        if (!AppendQuoted(&buffer, runLuaPath.data) ||
            !BufferAppendChar(&buffer, L' ') ||
            !AppendQuoted(&buffer, runFile)) {
            free(runLuaPath.data);
            free(buffer.data);
            return NULL;
        }
        free(runLuaPath.data);
        return BufferDetach(&buffer);
    }

    if (HasPathSeparator(runFile) || wcschr(runFile, L' ')) {
        if (!AppendQuoted(&buffer, runFile)) {
            free(buffer.data);
            return NULL;
        }
        return BufferDetach(&buffer);
    }

    return DupWide(runFile);
}

static BOOL IsTokenQuoted(LPCWSTR source, size_t pos, size_t tokenLen)
{
    return pos > 0 && source[pos - 1] == L'"' && source[pos + tokenLen] == L'"';
}

static BOOL IsTokenSeparated(LPCWSTR source, size_t pos, size_t tokenLen)
{
    WCHAR before;
    WCHAR after;

    before = pos == 0 ? L'\0' : source[pos - 1];
    after = source[pos + tokenLen];

    return (before == L'\0' || iswspace(before) || before == L'"') &&
        (after == L'\0' || iswspace(after) || after == L'"');
}

static BOOL AppendPlaceholder(WideBuffer *buffer, LPCWSTR replacement, BOOL quote)
{
    if (quote) {
        return AppendQuoted(buffer, replacement ? replacement : L"");
    }
    return BufferAppend(buffer, replacement ? replacement : L"");
}

LPWSTR ExpandArgumentsAlloc(LPCWSTR args, LPCWSTR filePath)
{
    WideBuffer buffer = { 0 };
    LPWSTR parent = NULL;
    LPWSTR name = NULL;
    LPWSTR ext = NULL;
    size_t i;
    size_t len;
    BOOL ok = TRUE;

    if (!args) {
        return DupWide(L"");
    }

    parent = GetParentPathAlloc(filePath);
    name = GetFileNameWithoutExtAlloc(filePath);
    ext = GetFileExtAlloc(filePath);
    if (!parent || !name || !ext) {
        ok = FALSE;
        goto done;
    }

    len = wcslen(args);
    for (i = 0; i < len && ok; ) {
        if (wcsncmp(args + i, L"{0}", 3) == 0) {
            ok = AppendPlaceholder(&buffer, g_modulePath, !IsTokenQuoted(args, i, 3) && IsTokenSeparated(args, i, 3));
            i += 3;
        } else if (wcsncmp(args + i, L"{1}", 3) == 0) {
            ok = AppendPlaceholder(&buffer, filePath, !IsTokenQuoted(args, i, 3));
            i += 3;
        } else if (wcsncmp(args + i, L"{path}", 6) == 0) {
            ok = AppendPlaceholder(&buffer, parent, !IsTokenQuoted(args, i, 6) && IsTokenSeparated(args, i, 6));
            i += 6;
        } else if (wcsncmp(args + i, L"{name}", 6) == 0) {
            ok = BufferAppend(&buffer, name);
            i += 6;
        } else if (wcsncmp(args + i, L"{ext}", 5) == 0) {
            ok = BufferAppend(&buffer, ext);
            i += 5;
        } else {
            ok = BufferAppendChar(&buffer, args[i]);
            ++i;
        }
    }

done:
    free(parent);
    free(name);
    free(ext);

    if (!ok) {
        free(buffer.data);
        return NULL;
    }

    return BufferDetach(&buffer);
}

HBITMAP LoadMenuBitmap(LPCWSTR fileName)
{
    DWORD attr;
    HBITMAP bitmap;
    GpBitmap *gpBitmap = NULL;

    if (!fileName || !fileName[0]) {
        return NULL;
    }

    attr = GetFileAttributesW(fileName);
    if (attr == INVALID_FILE_ATTRIBUTES || (attr & FILE_ATTRIBUTE_DIRECTORY)) {
        return NULL;
    }

    bitmap = (HBITMAP)LoadImageW(NULL, fileName, IMAGE_BITMAP, 0, 0, LR_LOADFROMFILE | LR_CREATEDIBSECTION);
    if (bitmap) {
        return bitmap;
    }

    if (!EnsureGdiplus()) {
        return NULL;
    }

    if (GdipCreateBitmapFromFile(fileName, &gpBitmap) == 0 && gpBitmap) {
        GdipCreateHBITMAPFromBitmap(gpBitmap, &bitmap, 0x00FFFFFF);
        GdipDisposeImage((GpImage *)gpBitmap);
    }

    return bitmap;
}

BOOL RunCommandLine(LPCWSTR commandLine, LPCWSTR currentDir, DWORD waitMs)
{
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    LPWSTR mutableCommand;
    BOOL success;

    if (!commandLine || !commandLine[0]) {
        return FALSE;
    }

    mutableCommand = DupWide(commandLine);
    if (!mutableCommand) {
        return FALSE;
    }

    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_SHOW;

    success = CreateProcessW(
        NULL,
        mutableCommand,
        NULL,
        NULL,
        FALSE,
        0,
        NULL,
        currentDir && currentDir[0] ? currentDir : NULL,
        &si,
        &pi);

    free(mutableCommand);

    if (!success) {
        return FALSE;
    }

    if (waitMs != 0) {
        WaitForSingleObject(pi.hProcess, waitMs);
    }

    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return TRUE;
}

BOOL CopyToClipboardText(LPCWSTR text)
{
    HGLOBAL memory;
    LPWSTR target;
    size_t bytes;

    if (!text || !text[0]) {
        return FALSE;
    }

    bytes = (wcslen(text) + 1) * sizeof(WCHAR);
    memory = GlobalAlloc(GMEM_MOVEABLE, bytes);
    if (!memory) {
        return FALSE;
    }

    target = (LPWSTR)GlobalLock(memory);
    if (!target) {
        GlobalFree(memory);
        return FALSE;
    }

    memcpy(target, text, bytes);
    GlobalUnlock(memory);

    if (!OpenClipboard(NULL)) {
        GlobalFree(memory);
        return FALSE;
    }

    EmptyClipboard();
    if (!SetClipboardData(CF_UNICODETEXT, memory)) {
        CloseClipboard();
        GlobalFree(memory);
        return FALSE;
    }

    CloseClipboard();
    return TRUE;
}

void ShowTips(LPCWSTR tips, LPCWSTR title)
{
    NOTIFYICONDATAW data;

    ZeroMemory(&data, sizeof(data));
    data.cbSize = sizeof(data);
    data.hWnd = GetActiveWindow();
    data.uID = 1;
    data.uFlags = NIF_INFO | NIF_TIP;
    data.dwInfoFlags = NIIF_INFO;
    data.uTimeout = 700;

    StringCchCopyW(data.szInfoTitle, ARRAYSIZE(data.szInfoTitle), title && title[0] ? title : g_mainMenuName);
    StringCchCopyW(data.szInfo, ARRAYSIZE(data.szInfo), tips ? tips : L"");

    Shell_NotifyIconW(NIM_ADD, &data);
    Shell_NotifyIconW(NIM_MODIFY, &data);
    Shell_NotifyIconW(NIM_DELETE, &data);
}

void LogMessage(LPCWSTR format, ...)
{
    WCHAR text[2048];
    WCHAR logPath[MAX_PATH];
    char utf8[4096];
    int bytes;
    FILE *file;
    va_list args;

    if (!g_isDebug || !format) {
        return;
    }

    va_start(args, format);
    StringCchVPrintfW(text, ARRAYSIZE(text), format, args);
    va_end(args);
    StringCchCatW(text, ARRAYSIZE(text), L"\r\n");

    OutputDebugStringW(text);

    bytes = WideCharToMultiByte(CP_UTF8, 0, text, -1, utf8, sizeof(utf8), NULL, NULL);
    if (bytes <= 0) {
        return;
    }

    if (FAILED(StringCchCopyW(logPath, ARRAYSIZE(logPath), g_modulePath)) ||
        FAILED(StringCchCatW(logPath, ARRAYSIZE(logPath), L"log.txt"))) {
        return;
    }

    if (_wfopen_s(&file, logPath, L"ab") == 0 && file) {
        fwrite(utf8, 1, (size_t)bytes - 1, file);
        fclose(file);
    }
}
