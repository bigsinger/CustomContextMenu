#include "stdafx.h"
#include "resource.h"
#include "Const.h"
#include "Utils.h"
#include "compreg.h"

extern HINSTANCE g_instance;
extern LONG g_objectCount;

#define XML_MAX_BYTES (1024 * 1024)
typedef struct CommandWork {
    LPWSTR runFile;
    LPWSTR args;
    LPWSTR workDir;
    LPWSTR *files;
    UINT fileCount;
} CommandWork;

static HRESULT STDMETHODCALLTYPE ShellInit_QueryInterface(IShellExtInit *iface, REFIID riid, void **ppv);
static ULONG STDMETHODCALLTYPE ShellInit_AddRef(IShellExtInit *iface);
static ULONG STDMETHODCALLTYPE ShellInit_Release(IShellExtInit *iface);
static HRESULT STDMETHODCALLTYPE ShellInit_Initialize(IShellExtInit *iface, LPCITEMIDLIST pidlFolder, IDataObject *dataObject, HKEY progId);

static HRESULT STDMETHODCALLTYPE Context_QueryInterface(IContextMenu *iface, REFIID riid, void **ppv);
static ULONG STDMETHODCALLTYPE Context_AddRef(IContextMenu *iface);
static ULONG STDMETHODCALLTYPE Context_Release(IContextMenu *iface);
static HRESULT STDMETHODCALLTYPE Context_QueryContextMenu(IContextMenu *iface, HMENU menu, UINT indexMenu, UINT idCmdFirst, UINT idCmdLast, UINT flags);
static HRESULT STDMETHODCALLTYPE Context_InvokeCommand(IContextMenu *iface, LPCMINVOKECOMMANDINFO commandInfo);
static HRESULT STDMETHODCALLTYPE Context_GetCommandString(IContextMenu *iface, UINT_PTR idCmd, UINT type, UINT *reserved, LPSTR name, UINT cchMax);

static const IShellExtInitVtbl g_shellInitVtbl = {
    ShellInit_QueryInterface,
    ShellInit_AddRef,
    ShellInit_Release,
    ShellInit_Initialize
};

static const IContextMenuVtbl g_contextMenuVtbl = {
    Context_QueryInterface,
    Context_AddRef,
    Context_Release,
    Context_QueryContextMenu,
    Context_InvokeCommand,
    Context_GetCommandString
};

static ShellMenuExt *ObjectFromShellInit(IShellExtInit *iface)
{
    return CONTAINING_RECORD(iface, ShellMenuExt, shellInit);
}

static ShellMenuExt *ObjectFromContext(IContextMenu *iface)
{
    return CONTAINING_RECORD(iface, ShellMenuExt, contextMenu);
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

static LPWSTR ResolveModuleFile(LPCWSTR path)
{
    size_t baseLen;
    size_t pathLen;
    LPWSTR joined;
    LPWSTR normalized;

    if (!path || !path[0]) {
        return DupWide(L"");
    }
    if (IsAbsolutePath(path)) {
        return NormalizePath(path);
    }

    baseLen = wcslen(g_modulePath);
    pathLen = wcslen(path);
    joined = (LPWSTR)calloc(baseLen + pathLen + 1, sizeof(WCHAR));
    if (!joined) {
        return NULL;
    }
    memcpy(joined, g_modulePath, baseLen * sizeof(WCHAR));
    memcpy(joined + baseLen, path, (pathLen + 1) * sizeof(WCHAR));

    normalized = NormalizePath(joined);
    free(joined);
    return normalized;
}

static LPWSTR ResolveRunFile(LPCWSTR runFile)
{
    if (!runFile || !runFile[0]) {
        return DupWide(L"");
    }
    if (IsAbsolutePath(runFile)) {
        return NormalizePath(runFile);
    }
    if (HasPathSeparator(runFile)) {
        return ResolveModuleFile(runFile);
    }
    return DupWide(runFile);
}

static void MenuItem_Init(MenuItem *item)
{
    if (item) {
        ZeroMemory(item, sizeof(*item));
    }
}

void ShellMenuExt_FreeMenu(MenuItem *item)
{
    UINT i;

    if (!item) {
        return;
    }

    for (i = 0; i < item->childCount; ++i) {
        ShellMenuExt_FreeMenu(&item->children[i]);
    }

    free(item->children);
    item->children = NULL;
    item->childCount = 0;
    item->childCapacity = 0;

    if (item->bitmap) {
        DeleteObject(item->bitmap);
        item->bitmap = NULL;
    }

    free(item->name);
    free(item->icon);
    free(item->run);
    free(item->arg);
    MenuItem_Init(item);
}

static MenuItem *MenuItem_AddChild(MenuItem *parent)
{
    MenuItem *next;
    UINT capacity;

    if (!parent) {
        return NULL;
    }

    if (parent->childCount == parent->childCapacity) {
        capacity = parent->childCapacity ? parent->childCapacity * 2 : 8;
        next = (MenuItem *)realloc(parent->children, capacity * sizeof(MenuItem));
        if (!next) {
            return NULL;
        }
        parent->children = next;
        parent->childCapacity = capacity;
    }

    next = &parent->children[parent->childCount++];
    MenuItem_Init(next);
    return next;
}

static void SetWideField(LPWSTR *field, LPWSTR value)
{
    if (!field) {
        free(value);
        return;
    }
    free(*field);
    *field = value;
}

static void LoadMenuItemBitmap(MenuItem *item)
{
    LPWSTR fullPath;

    if (!item || !item->icon || !item->icon[0]) {
        return;
    }

    fullPath = ResolveModuleFile(item->icon);
    if (!fullPath) {
        return;
    }

    item->bitmap = LoadMenuBitmap(fullPath);
    free(fullPath);
}

static char *XmlUnescape(const char *start, size_t length)
{
    char *text;
    size_t i;
    size_t out;

    text = (char *)malloc(length + 1);
    if (!text) {
        return NULL;
    }

    for (i = 0, out = 0; i < length; ++i) {
        if (start[i] == '&') {
            if (i + 5 <= length && memcmp(start + i, "&amp;", 5) == 0) {
                text[out++] = '&';
                i += 4;
            } else if (i + 6 <= length && memcmp(start + i, "&quot;", 6) == 0) {
                text[out++] = '"';
                i += 5;
            } else if (i + 6 <= length && memcmp(start + i, "&apos;", 6) == 0) {
                text[out++] = '\'';
                i += 5;
            } else if (i + 4 <= length && memcmp(start + i, "&lt;", 4) == 0) {
                text[out++] = '<';
                i += 3;
            } else if (i + 4 <= length && memcmp(start + i, "&gt;", 4) == 0) {
                text[out++] = '>';
                i += 3;
            } else {
                text[out++] = start[i];
            }
        } else {
            text[out++] = start[i];
        }
    }

    text[out] = '\0';
    return text;
}

static LPWSTR AttributeValueToWide(const char *start, size_t length)
{
    char *unescaped;
    LPWSTR wide;

    unescaped = XmlUnescape(start, length);
    if (!unescaped) {
        return NULL;
    }

    wide = DupUtf8AsWide(unescaped, -1);
    free(unescaped);
    return wide;
}

static int IsAttrName(const char *start, size_t length, const char *name)
{
    return strlen(name) == length && _strnicmp(start, name, length) == 0;
}

static void ParseMenuAttributes(MenuItem *item, const char *tagStart, const char *tagEnd, BOOL isRoot)
{
    const char *p;
    const char *nameStart;
    const char *valueStart;
    size_t nameLength;
    size_t valueLength;
    char quote;
    LPWSTR value;

    if (!item || !tagStart || !tagEnd || tagStart >= tagEnd) {
        return;
    }

    p = tagStart;
    while (p < tagEnd && *p != '<') {
        ++p;
    }
    if (p < tagEnd) {
        ++p;
    }
    while (p < tagEnd && !isspace((unsigned char)*p) && *p != '/' && *p != '>') {
        ++p;
    }

    while (p < tagEnd) {
        while (p < tagEnd && isspace((unsigned char)*p)) {
            ++p;
        }
        if (p >= tagEnd || *p == '/' || *p == '>') {
            break;
        }

        nameStart = p;
        while (p < tagEnd && (isalnum((unsigned char)*p) || *p == '_' || *p == '-' || *p == ':')) {
            ++p;
        }
        nameLength = (size_t)(p - nameStart);

        while (p < tagEnd && isspace((unsigned char)*p)) {
            ++p;
        }
        if (p >= tagEnd || *p != '=') {
            continue;
        }
        ++p;
        while (p < tagEnd && isspace((unsigned char)*p)) {
            ++p;
        }
        if (p >= tagEnd || (*p != '"' && *p != '\'')) {
            continue;
        }

        quote = *p++;
        valueStart = p;
        while (p < tagEnd && *p != quote) {
            ++p;
        }
        valueLength = (size_t)(p - valueStart);
        if (p < tagEnd) {
            ++p;
        }

        if (nameLength == 0) {
            continue;
        }

        if (isRoot && IsAttrName(nameStart, nameLength, "debug")) {
            char *debugText = XmlUnescape(valueStart, valueLength);
            g_isDebug = debugText ? atoi(debugText) : 0;
            free(debugText);
            continue;
        }

        value = AttributeValueToWide(valueStart, valueLength);
        if (!value) {
            continue;
        }

        if (IsAttrName(nameStart, nameLength, "name")) {
            SetWideField(&item->name, value);
        } else if (IsAttrName(nameStart, nameLength, "icon")) {
            SetWideField(&item->icon, value);
        } else if (IsAttrName(nameStart, nameLength, "run")) {
            SetWideField(&item->run, value);
            if (isRoot) {
                StringCchCopyW(g_defaultRunFile, ARRAYSIZE(g_defaultRunFile), value);
            }
        } else if (IsAttrName(nameStart, nameLength, "arg") || IsAttrName(nameStart, nameLength, "tag")) {
            SetWideField(&item->arg, value);
        } else {
            free(value);
        }
    }
}

static const char *FindTagEnd(const char *p)
{
    char quote = '\0';

    while (*p) {
        if (quote) {
            if (*p == quote) {
                quote = '\0';
            }
        } else if (*p == '"' || *p == '\'') {
            quote = *p;
        } else if (*p == '>') {
            return p;
        }
        ++p;
    }

    return NULL;
}

static BOOL IsMenuStartTag(const char *p)
{
    return p &&
        p[0] == '<' &&
        _strnicmp(p + 1, "menu", 4) == 0 &&
        (isspace((unsigned char)p[5]) || p[5] == '/' || p[5] == '>');
}

static BOOL IsClosingTag(const char *p)
{
    return p && p[0] == '<' && p[1] == '/';
}

static BOOL IsSelfClosingTag(const char *tagStart, const char *tagEnd)
{
    const char *p;

    if (!tagStart || !tagEnd || tagEnd <= tagStart) {
        return FALSE;
    }

    p = tagEnd - 1;
    while (p > tagStart && isspace((unsigned char)*p)) {
        --p;
    }
    return *p == '/';
}

static BOOL ParseMenuXmlBytes(ShellMenuExt *object, const char *bytes, DWORD byteCount)
{
    char *xml;
    const char *p;
    const char *tagEnd;
    int depth = 0;
    BOOL ok = TRUE;
    MenuItem *lastSecondLevel = NULL;

    if (!object || !bytes || byteCount == 0) {
        return FALSE;
    }

    xml = (char *)malloc((size_t)byteCount + 1);
    if (!xml) {
        return FALSE;
    }
    memcpy(xml, bytes, byteCount);
    xml[byteCount] = '\0';

    ShellMenuExt_FreeMenu(&object->rootMenu);
    MenuItem_Init(&object->rootMenu);
    g_isDebug = 0;
    g_defaultRunFile[0] = L'\0';

    p = xml;
    if ((unsigned char)p[0] == 0xEF && (unsigned char)p[1] == 0xBB && (unsigned char)p[2] == 0xBF) {
        p += 3;
    }

    while ((p = strchr(p, '<')) != NULL) {
        if (p[1] == '?' || strncmp(p, "<!--", 4) == 0) {
            const char *skipEnd = p[1] == '?' ? strstr(p, "?>") : strstr(p, "-->");
            if (!skipEnd) {
                break;
            }
            p = skipEnd + (p[1] == '?' ? 2 : 3);
            continue;
        }

        tagEnd = FindTagEnd(p);
        if (!tagEnd) {
            ok = FALSE;
            break;
        }

        if (IsClosingTag(p)) {
            if (depth > 0) {
                --depth;
            }
            p = tagEnd + 1;
            continue;
        }

        if (IsMenuStartTag(p)) {
            BOOL selfClosing = IsSelfClosingTag(p, tagEnd);
            if (depth == 0) {
                ParseMenuAttributes(&object->rootMenu, p, tagEnd, TRUE);
                LoadMenuItemBitmap(&object->rootMenu);
                if (!object->rootMenu.name || !object->rootMenu.name[0]) {
                    SetWideField(&object->rootMenu.name, DupWide(L"Custom Context Menu"));
                }
                if (!selfClosing) {
                    ++depth;
                }
            } else if (depth == 1) {
                MenuItem *child = MenuItem_AddChild(&object->rootMenu);
                if (!child) {
                    ok = FALSE;
                    break;
                }
                ParseMenuAttributes(child, p, tagEnd, FALSE);
                LoadMenuItemBitmap(child);
                lastSecondLevel = child;
                if (!selfClosing) {
                    ++depth;
                }
            } else if (depth == 2 && lastSecondLevel) {
                MenuItem *child = MenuItem_AddChild(lastSecondLevel);
                if (!child) {
                    ok = FALSE;
                    break;
                }
                ParseMenuAttributes(child, p, tagEnd, FALSE);
                if ((!child->run || !child->run[0]) && lastSecondLevel->run && lastSecondLevel->run[0]) {
                    SetWideField(&child->run, DupWide(lastSecondLevel->run));
                }
                LoadMenuItemBitmap(child);
                if (!selfClosing) {
                    ++depth;
                }
            } else if (!selfClosing) {
                ++depth;
            }
        } else if (!IsSelfClosingTag(p, tagEnd)) {
            ++depth;
        }

        p = tagEnd + 1;
    }

    free(xml);
    return ok && object->rootMenu.name != NULL;
}

static BOOL ReadWholeFile(LPCWSTR fileName, char **bytes, DWORD *byteCount)
{
    HANDLE file;
    LARGE_INTEGER size;
    DWORD readBytes;
    char *buffer;
    BOOL ok;

    if (!fileName || !bytes || !byteCount) {
        return FALSE;
    }

    *bytes = NULL;
    *byteCount = 0;

    file = CreateFileW(fileName, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        return FALSE;
    }

    if (!GetFileSizeEx(file, &size) || size.QuadPart <= 0 || size.QuadPart > XML_MAX_BYTES) {
        CloseHandle(file);
        return FALSE;
    }

    buffer = (char *)malloc((size_t)size.QuadPart);
    if (!buffer) {
        CloseHandle(file);
        return FALSE;
    }

    ok = ReadFile(file, buffer, (DWORD)size.QuadPart, &readBytes, NULL) && readBytes == (DWORD)size.QuadPart;
    CloseHandle(file);

    if (!ok) {
        free(buffer);
        return FALSE;
    }

    *bytes = buffer;
    *byteCount = readBytes;
    return TRUE;
}

static BOOL LoadMenuFromFile(ShellMenuExt *object, LPCWSTR fileName)
{
    char *bytes;
    DWORD byteCount;
    BOOL ok;

    if (!ReadWholeFile(fileName, &bytes, &byteCount)) {
        return FALSE;
    }

    ok = ParseMenuXmlBytes(object, bytes, byteCount);
    free(bytes);
    return ok;
}

static BOOL LoadMenuFromResource(ShellMenuExt *object)
{
    HRSRC resource;
    HGLOBAL data;
    LPVOID bytes;
    DWORD size;

    resource = FindResourceW(g_instance, MAKEINTRESOURCEW(IDB_XML_MENU), L"DAT");
    if (!resource) {
        return FALSE;
    }

    size = SizeofResource(g_instance, resource);
    data = LoadResource(g_instance, resource);
    if (!data || size == 0) {
        return FALSE;
    }

    bytes = LockResource(data);
    if (!bytes) {
        return FALSE;
    }

    return ParseMenuXmlBytes(object, (const char *)bytes, size);
}

static BOOL LoadCustomMenu(ShellMenuExt *object)
{
    WCHAR xmlPath[MAX_PATH];
    BOOL ok;

    if (FAILED(StringCchCopyW(xmlPath, ARRAYSIZE(xmlPath), g_modulePath)) ||
        FAILED(StringCchCatW(xmlPath, ARRAYSIZE(xmlPath), CCM_MENU_FILE_NAME))) {
        return FALSE;
    }

    ok = LoadMenuFromFile(object, xmlPath);
    if (!ok) {
        ok = LoadMenuFromResource(object);
    }
    if (ok && object->rootMenu.name && object->rootMenu.name[0]) {
        StringCchCopyW(g_mainMenuName, ARRAYSIZE(g_mainMenuName), object->rootMenu.name);
    }
    return ok;
}

static void ClearCommands(ShellMenuExt *object)
{
    UINT i;

    if (!object) {
        return;
    }

    for (i = 0; i < object->commandCount; ++i) {
        free(object->commands[i].run);
        free(object->commands[i].arg);
    }
    free(object->commands);
    object->commands = NULL;
    object->commandCount = 0;
    object->commandCapacity = 0;
}

static BOOL AddCommand(ShellMenuExt *object, const MenuItem *item)
{
    CommandEntry *next;
    UINT capacity;

    if (!object || !item) {
        return FALSE;
    }

    if (object->commandCount == object->commandCapacity) {
        capacity = object->commandCapacity ? object->commandCapacity * 2 : 16;
        next = (CommandEntry *)realloc(object->commands, capacity * sizeof(CommandEntry));
        if (!next) {
            return FALSE;
        }
        object->commands = next;
        object->commandCapacity = capacity;
    }

    object->commands[object->commandCount].run = DupWide(item->run ? item->run : L"");
    object->commands[object->commandCount].arg = DupWide(item->arg ? item->arg : L"");
    if (!object->commands[object->commandCount].run || !object->commands[object->commandCount].arg) {
        return FALSE;
    }
    ++object->commandCount;
    return TRUE;
}

static void InsertMenuText(HMENU menu, UINT index, UINT flags, UINT_PTR id, LPCWSTR text, HBITMAP bitmap)
{
    MENUITEMINFOW itemInfo;

    InsertMenuW(menu, index, MF_BYPOSITION | flags, id, text && text[0] ? text : L"");
    if (bitmap) {
        ZeroMemory(&itemInfo, sizeof(itemInfo));
        itemInfo.cbSize = sizeof(itemInfo);
        itemInfo.fMask = MIIM_BITMAP;
        itemInfo.hbmpItem = bitmap;
        SetMenuItemInfoW(menu, index, TRUE, &itemInfo);
    }
}

static UINT CreateMenuItems(ShellMenuExt *object, HMENU parentMenu, const MenuItem *items, UINT itemCount, UINT idCmdFirst, UINT idCmdLast, UINT nextCmd)
{
    UINT i;
    UINT menuIndex = 0;

    for (i = 0; i < itemCount; ++i) {
        const MenuItem *item = &items[i];

        if (!item->name || !item->name[0]) {
            InsertMenuW(parentMenu, menuIndex++, MF_BYPOSITION | MF_SEPARATOR, 0, NULL);
            continue;
        }

        if (item->childCount > 0) {
            HMENU subMenu = CreatePopupMenu();
            if (!subMenu) {
                continue;
            }
            nextCmd = CreateMenuItems(object, subMenu, item->children, item->childCount, idCmdFirst, idCmdLast, nextCmd);
            InsertMenuText(parentMenu, menuIndex++, MF_STRING | MF_POPUP, (UINT_PTR)subMenu, item->name, item->bitmap);
            continue;
        }

        if (idCmdFirst + nextCmd > idCmdLast) {
            break;
        }
        if (!AddCommand(object, item)) {
            break;
        }
        InsertMenuText(parentMenu, menuIndex++, MF_STRING, idCmdFirst + nextCmd, item->name, item->bitmap);
        ++nextCmd;
    }

    return nextCmd;
}

static UINT CreateRootMenu(ShellMenuExt *object, HMENU menu, UINT indexMenu, UINT idCmdFirst, UINT idCmdLast)
{
    HMENU popup;
    UINT nextCmd;

    ClearCommands(object);

    popup = CreatePopupMenu();
    if (!popup) {
        return 0;
    }

    nextCmd = CreateMenuItems(object, popup, object->rootMenu.children, object->rootMenu.childCount, idCmdFirst, idCmdLast, 0);
    if (nextCmd == 0 && object->rootMenu.childCount == 0) {
        DestroyMenu(popup);
        return 0;
    }

    InsertMenuW(menu, indexMenu++, MF_BYPOSITION | MF_SEPARATOR, 0, NULL);
    InsertMenuText(menu, indexMenu++, MF_STRING | MF_POPUP, (UINT_PTR)popup, object->rootMenu.name, object->rootMenu.bitmap);
    InsertMenuW(menu, indexMenu++, MF_BYPOSITION | MF_SEPARATOR, 0, NULL);
    return nextCmd;
}

static void FreeCommandWork(CommandWork *work)
{
    if (!work) {
        return;
    }
    free(work->runFile);
    free(work->args);
    free(work->workDir);
    FreeStringArray(work->files, work->fileCount);
    free(work);
}

static LPWSTR BuildCommandLine(LPCWSTR runFile, LPCWSTR args, LPCWSTR filePath)
{
    LPWSTR launcher;
    LPWSTR expanded;
    LPWSTR commandLine;
    size_t launcherLen;
    size_t expandedLen;

    launcher = GetLaunchCommandAlloc(runFile);
    expanded = ExpandArgumentsAlloc(args, filePath);
    if (!launcher || !expanded) {
        free(launcher);
        free(expanded);
        return NULL;
    }

    launcherLen = wcslen(launcher);
    expandedLen = wcslen(expanded);
    commandLine = (LPWSTR)calloc(launcherLen + expandedLen + 2, sizeof(WCHAR));
    if (!commandLine) {
        free(launcher);
        free(expanded);
        return NULL;
    }

    memcpy(commandLine, launcher, launcherLen * sizeof(WCHAR));
    if (expandedLen > 0) {
        commandLine[launcherLen] = L' ';
        memcpy(commandLine + launcherLen + 1, expanded, (expandedLen + 1) * sizeof(WCHAR));
    }

    free(launcher);
    free(expanded);
    return commandLine;
}

static DWORD WINAPI CommandThreadProc(LPVOID param)
{
    CommandWork *work = (CommandWork *)param;
    BOOL success = TRUE;
    UINT i;

    if (!work) {
        return 0;
    }

    for (i = 0; i < work->fileCount; ++i) {
        LPWSTR commandLine = BuildCommandLine(work->runFile, work->args, work->files[i]);
        DWORD waitMs = g_isDebug ? INFINITE : 0;

        if (!commandLine) {
            success = FALSE;
            break;
        }

        LogMessage(L"run: %s", commandLine);
        success = RunCommandLine(commandLine, work->workDir, waitMs);
        if (!success) {
            WCHAR message[2048];
            StringCchPrintfW(message, ARRAYSIZE(message), L"未能正常执行，请检查配置是否正确:\r\n\r\n%s", commandLine);
            ShowTips(L"执行失败", g_mainMenuName);
            MessageBoxW(NULL, message, g_mainMenuName, MB_OK | MB_ICONERROR);
            free(commandLine);
            break;
        }
        free(commandLine);
    }

    if (success) {
        ShowTips(L"执行完成", g_mainMenuName);
    }

    FreeCommandWork(work);
    return 0;
}

static BOOL CopySelectedPaths(ShellMenuExt *object)
{
    LPWSTR text = NULL;
    size_t total = 1;
    UINT i;
    BOOL copied;

    if (!object || object->selectedFileCount == 0) {
        return FALSE;
    }

    if (object->selectedFileCount == 1) {
        text = DupWide(object->selectedFiles[0]);
    } else {
        for (i = 0; i < object->selectedFileCount; ++i) {
            LPWSTR name = GetFileNameAlloc(object->selectedFiles[i]);
            total += name ? wcslen(name) + 2 : 2;
            free(name);
        }
        text = (LPWSTR)calloc(total, sizeof(WCHAR));
        if (text) {
            for (i = 0; i < object->selectedFileCount; ++i) {
                LPWSTR name = GetFileNameAlloc(object->selectedFiles[i]);
                if (name) {
                    StringCchCatW(text, total, name);
                    free(name);
                }
                StringCchCatW(text, total, L"\r\n");
            }
        }
    }

    if (!text) {
        return FALSE;
    }

    for (i = 0; text[i]; ++i) {
        if (text[i] == L'\\') {
            text[i] = L'/';
        }
    }

    copied = CopyToClipboardText(text);
    free(text);
    return copied;
}

static HRESULT StartCommand(ShellMenuExt *object, UINT commandIndex)
{
    const CommandEntry *entry;
    LPCWSTR runSource;
    CommandWork *work;
    HANDLE thread;
    UINT i;

    if (!object || commandIndex >= object->commandCount) {
        LogMessage(L"invalid command index: %u, command count: %u", commandIndex, object ? object->commandCount : 0);
        return E_INVALIDARG;
    }

    if (commandIndex == 0) {
        LogMessage(L"command 0: copy selected paths, file count: %u", object->selectedFileCount);
        return CopySelectedPaths(object) ? S_OK : E_FAIL;
    }

    entry = &object->commands[commandIndex];
    runSource = entry->run && entry->run[0] ? entry->run : g_defaultRunFile;
    LogMessage(
        L"command %u: run='%s' arg='%s' selected files=%u",
        commandIndex,
        runSource ? runSource : L"",
        entry->arg ? entry->arg : L"",
        object->selectedFileCount);

    if ((!runSource || !runSource[0]) && (!entry->arg || !entry->arg[0])) {
        LogMessage(L"command %u has no run and no arg, fallback to copy selected paths", commandIndex);
        return CopySelectedPaths(object) ? S_OK : E_FAIL;
    }

    if (!runSource || !runSource[0] || object->selectedFileCount == 0) {
        LogMessage(L"command %u skipped: run or selected files missing", commandIndex);
        return E_FAIL;
    }

    work = (CommandWork *)calloc(1, sizeof(CommandWork));
    if (!work) {
        return E_OUTOFMEMORY;
    }

    work->runFile = ResolveRunFile(runSource);
    work->args = DupWide(entry->arg ? entry->arg : L"");
    work->workDir = HasPathSeparator(work->runFile) || IsAbsolutePath(work->runFile) ? GetParentPathAlloc(work->runFile) : DupWide(L"");
    work->fileCount = object->selectedFileCount;
    work->files = (LPWSTR *)calloc(work->fileCount, sizeof(LPWSTR));

    if (!work->runFile || !work->args || !work->workDir || !work->files) {
        FreeCommandWork(work);
        return E_OUTOFMEMORY;
    }

    for (i = 0; i < work->fileCount; ++i) {
        work->files[i] = DupWide(object->selectedFiles[i]);
        if (!work->files[i]) {
            FreeCommandWork(work);
            return E_OUTOFMEMORY;
        }
    }

    thread = CreateThread(NULL, 0, CommandThreadProc, work, 0, NULL);
    if (!thread) {
        FreeCommandWork(work);
        return HRESULT_FROM_WIN32(GetLastError());
    }

    CloseHandle(thread);
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE ShellInit_QueryInterface(IShellExtInit *iface, REFIID riid, void **ppv)
{
    ShellMenuExt *object = ObjectFromShellInit(iface);

    if (!ppv) {
        return E_POINTER;
    }
    *ppv = NULL;

    if (IsEqualIID(riid, &IID_IUnknown) || IsEqualIID(riid, &IID_IShellExtInit)) {
        *ppv = &object->shellInit;
    } else if (IsEqualIID(riid, &IID_IContextMenu)) {
        *ppv = &object->contextMenu;
    } else {
        return E_NOINTERFACE;
    }

    ShellInit_AddRef(iface);
    return S_OK;
}

static ULONG STDMETHODCALLTYPE ShellInit_AddRef(IShellExtInit *iface)
{
    ShellMenuExt *object = ObjectFromShellInit(iface);
    return (ULONG)InterlockedIncrement(&object->refCount);
}

static ULONG STDMETHODCALLTYPE ShellInit_Release(IShellExtInit *iface)
{
    ShellMenuExt *object = ObjectFromShellInit(iface);
    LONG refs = InterlockedDecrement(&object->refCount);

    if (refs == 0) {
        ShellMenuExt_FreeMenu(&object->rootMenu);
        ClearCommands(object);
        FreeStringArray(object->selectedFiles, object->selectedFileCount);
        InterlockedDecrement(&g_objectCount);
        free(object);
    }

    return (ULONG)refs;
}

static HRESULT STDMETHODCALLTYPE ShellInit_Initialize(IShellExtInit *iface, LPCITEMIDLIST pidlFolder, IDataObject *dataObject, HKEY progId)
{
    ShellMenuExt *object = ObjectFromShellInit(iface);
    FORMATETC format = { CF_HDROP, NULL, DVASPECT_CONTENT, -1, TYMED_HGLOBAL };
    STGMEDIUM medium;
    HDROP drop;
    UINT count;
    UINT i;

    UNREFERENCED_PARAMETER(pidlFolder);
    UNREFERENCED_PARAMETER(progId);

    FreeStringArray(object->selectedFiles, object->selectedFileCount);
    object->selectedFiles = NULL;
    object->selectedFileCount = 0;

    if (!dataObject) {
        return S_OK;
    }

    ZeroMemory(&medium, sizeof(medium));
    if (FAILED(IDataObject_GetData(dataObject, &format, &medium))) {
        return S_OK;
    }

    drop = (HDROP)GlobalLock(medium.hGlobal);
    if (!drop) {
        ReleaseStgMedium(&medium);
        return S_OK;
    }

    count = DragQueryFileW(drop, 0xFFFFFFFF, NULL, 0);
    if (count > 0) {
        object->selectedFiles = (LPWSTR *)calloc(count, sizeof(LPWSTR));
        if (object->selectedFiles) {
            for (i = 0; i < count; ++i) {
                UINT chars = DragQueryFileW(drop, i, NULL, 0);
                object->selectedFiles[i] = (LPWSTR)calloc((size_t)chars + 1, sizeof(WCHAR));
                if (object->selectedFiles[i]) {
                    DragQueryFileW(drop, i, object->selectedFiles[i], chars + 1);
                    ++object->selectedFileCount;
                }
            }
        }
    }

    GlobalUnlock(medium.hGlobal);
    ReleaseStgMedium(&medium);
    return S_OK;
}

static HRESULT STDMETHODCALLTYPE Context_QueryInterface(IContextMenu *iface, REFIID riid, void **ppv)
{
    ShellMenuExt *object = ObjectFromContext(iface);
    return ShellInit_QueryInterface(&object->shellInit, riid, ppv);
}

static ULONG STDMETHODCALLTYPE Context_AddRef(IContextMenu *iface)
{
    ShellMenuExt *object = ObjectFromContext(iface);
    return ShellInit_AddRef(&object->shellInit);
}

static ULONG STDMETHODCALLTYPE Context_Release(IContextMenu *iface)
{
    ShellMenuExt *object = ObjectFromContext(iface);
    return ShellInit_Release(&object->shellInit);
}

static HRESULT STDMETHODCALLTYPE Context_QueryContextMenu(IContextMenu *iface, HMENU menu, UINT indexMenu, UINT idCmdFirst, UINT idCmdLast, UINT flags)
{
    ShellMenuExt *object = ObjectFromContext(iface);
    UINT used;

    if (flags & CMF_DEFAULTONLY) {
        return MAKE_HRESULT(SEVERITY_SUCCESS, FACILITY_NULL, 0);
    }

    LoadCustomMenu(object);
    LogMessage(L"QueryContextMenu: debug=%d defaultRun='%s' selected files=%u", g_isDebug, g_defaultRunFile, object->selectedFileCount);
    used = CreateRootMenu(object, menu, indexMenu, idCmdFirst, idCmdLast);
    return MAKE_HRESULT(SEVERITY_SUCCESS, FACILITY_NULL, used);
}

static HRESULT STDMETHODCALLTYPE Context_InvokeCommand(IContextMenu *iface, LPCMINVOKECOMMANDINFO commandInfo)
{
    ShellMenuExt *object = ObjectFromContext(iface);
    UINT commandIndex;

    if (!commandInfo) {
        return E_POINTER;
    }

    if (commandInfo->cbSize >= sizeof(CMINVOKECOMMANDINFOEX) &&
        (commandInfo->fMask & CMIC_MASK_UNICODE)) {
        LPCMINVOKECOMMANDINFOEX infoEx = (LPCMINVOKECOMMANDINFOEX)commandInfo;
        if (HIWORD(infoEx->lpVerbW)) {
            return E_INVALIDARG;
        }
        /* Explorer keeps ordinal verbs in lpVerb even for Unicode invokes. */
        commandIndex = LOWORD(commandInfo->lpVerb);
    } else {
        if (HIWORD(commandInfo->lpVerb)) {
            return E_INVALIDARG;
        }
        commandIndex = LOWORD(commandInfo->lpVerb);
    }

    LogMessage(L"InvokeCommand index: %u", commandIndex);
    return StartCommand(object, commandIndex);
}

static HRESULT STDMETHODCALLTYPE Context_GetCommandString(IContextMenu *iface, UINT_PTR idCmd, UINT type, UINT *reserved, LPSTR name, UINT cchMax)
{
    UNREFERENCED_PARAMETER(iface);
    UNREFERENCED_PARAMETER(idCmd);
    UNREFERENCED_PARAMETER(type);
    UNREFERENCED_PARAMETER(reserved);
    if (name && cchMax > 0) {
        name[0] = '\0';
    }
    return S_OK;
}

HRESULT ShellMenuExt_CreateInstance(REFIID riid, void **ppv)
{
    ShellMenuExt *object;
    HRESULT hr;

    if (!ppv) {
        return E_POINTER;
    }
    *ppv = NULL;

    object = (ShellMenuExt *)calloc(1, sizeof(ShellMenuExt));
    if (!object) {
        return E_OUTOFMEMORY;
    }

    object->shellInit.lpVtbl = (IShellExtInitVtbl *)&g_shellInitVtbl;
    object->contextMenu.lpVtbl = (IContextMenuVtbl *)&g_contextMenuVtbl;
    object->refCount = 1;
    MenuItem_Init(&object->rootMenu);
    InterlockedIncrement(&g_objectCount);

    if (!LoadCustomMenu(object)) {
        ShellInit_Release(&object->shellInit);
        return E_FAIL;
    }

    hr = ShellInit_QueryInterface(&object->shellInit, riid, ppv);
    ShellInit_Release(&object->shellInit);
    return hr;
}

static HRESULT SetRegistryString(HKEY root, LPCWSTR subKey, LPCWSTR valueName, LPCWSTR value)
{
    HKEY key;
    LSTATUS status;

    status = RegCreateKeyExW(root, subKey, 0, NULL, REG_OPTION_NON_VOLATILE, KEY_WRITE, NULL, &key, NULL);
    if (status != ERROR_SUCCESS) {
        return HRESULT_FROM_WIN32(status);
    }

    status = RegSetValueExW(
        key,
        valueName,
        0,
        REG_SZ,
        (const BYTE *)value,
        (DWORD)((wcslen(value) + 1) * sizeof(WCHAR)));
    RegCloseKey(key);

    return status == ERROR_SUCCESS ? S_OK : HRESULT_FROM_WIN32(status);
}

static HRESULT BuildClsidString(LPWSTR buffer, size_t cchBuffer)
{
    LPOLESTR clsidText = NULL;
    HRESULT hr;

    hr = StringFromCLSID(&CLSID_CompReg, &clsidText);
    if (FAILED(hr)) {
        return hr;
    }

    hr = StringCchCopyW(buffer, cchBuffer, clsidText);
    CoTaskMemFree(clsidText);
    return hr;
}

HRESULT RegisterShellExtension(void)
{
    WCHAR modulePath[MAX_PATH];
    WCHAR clsidText[64];
    WCHAR keyPath[256];
    HRESULT hr;

    if (!GetModuleFileNameW(g_instance, modulePath, ARRAYSIZE(modulePath))) {
        return HRESULT_FROM_WIN32(GetLastError());
    }

    hr = BuildClsidString(clsidText, ARRAYSIZE(clsidText));
    if (FAILED(hr)) {
        return hr;
    }

    hr = StringCchPrintfW(keyPath, ARRAYSIZE(keyPath), L"CLSID\\%s", clsidText);
    if (FAILED(hr)) {
        return hr;
    }
    hr = SetRegistryString(HKEY_CLASSES_ROOT, keyPath, NULL, L"CustomContextMenu Shell Extension");
    if (FAILED(hr)) {
        return hr;
    }

    hr = StringCchPrintfW(keyPath, ARRAYSIZE(keyPath), L"CLSID\\%s\\InprocServer32", clsidText);
    if (FAILED(hr)) {
        return hr;
    }
    hr = SetRegistryString(HKEY_CLASSES_ROOT, keyPath, NULL, modulePath);
    if (FAILED(hr)) {
        return hr;
    }
    hr = SetRegistryString(HKEY_CLASSES_ROOT, keyPath, L"ThreadingModel", L"Apartment");
    if (FAILED(hr)) {
        return hr;
    }

    hr = StringCchPrintfW(keyPath, ARRAYSIZE(keyPath), L"*\\shellex\\ContextMenuHandlers\\CustomContextMenu%s", clsidText);
    if (FAILED(hr)) {
        return hr;
    }
    hr = SetRegistryString(HKEY_CLASSES_ROOT, keyPath, NULL, clsidText);
    if (FAILED(hr)) {
        return hr;
    }

    hr = StringCchPrintfW(keyPath, ARRAYSIZE(keyPath), L"Directory\\shellex\\ContextMenuHandlers\\CustomContextMenu%s", clsidText);
    if (FAILED(hr)) {
        return hr;
    }
    return SetRegistryString(HKEY_CLASSES_ROOT, keyPath, NULL, clsidText);
}

HRESULT UnregisterShellExtension(void)
{
    WCHAR clsidText[64];
    WCHAR keyPath[256];
    HRESULT hr;

    hr = BuildClsidString(clsidText, ARRAYSIZE(clsidText));
    if (FAILED(hr)) {
        return hr;
    }

    if (SUCCEEDED(StringCchPrintfW(keyPath, ARRAYSIZE(keyPath), L"*\\shellex\\ContextMenuHandlers\\CustomContextMenu%s", clsidText))) {
        RegDeleteTreeW(HKEY_CLASSES_ROOT, keyPath);
    }

    if (SUCCEEDED(StringCchPrintfW(keyPath, ARRAYSIZE(keyPath), L"Directory\\shellex\\ContextMenuHandlers\\CustomContextMenu%s", clsidText))) {
        RegDeleteTreeW(HKEY_CLASSES_ROOT, keyPath);
    }

    if (SUCCEEDED(StringCchPrintfW(keyPath, ARRAYSIZE(keyPath), L"CLSID\\%s", clsidText))) {
        RegDeleteTreeW(HKEY_CLASSES_ROOT, keyPath);
    }

    return S_OK;
}
