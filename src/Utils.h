#pragma once
#include <atlstr.h>

// dll当前所在的目录
extern CString	g_sModulePath;

// 主菜单的名称
extern CString	g_sMainMenuName;

// 是否需要调试
extern int		g_isDebug;

// 运行的三方App的类型
extern CString	g_sDefaultRunFile;


CString GetStartPath(HMODULE hModule = NULL);
HBITMAP LoadImageFromFile(const wchar_t *szFileName);

// 如果debug打开，则显示运行三方App，dwMilliseconds为0时不等待进程结束
BOOL Run(const CString& strCmdLine, LPCTSTR lpszCurrentDir, DWORD dwMilliseconds = 0);
//void RunAsyn(const CString& strCmdLine, LPCTSTR lpszCurrentDir);
BOOL CopyToClipboard(const CString&strText);
void ShowTips(LPCTSTR szTips, LPCTSTR szTitle = NULL);

// utf-8字符串转换为TCHAR字符串
CString utf8s2ts(const char*lpszText, int nSize = -1);

// TCHAR字符串转换为ANSI字符串
CStringA ts2utf8s(const CString&str);

bool writefile(IN const char*strFileName, IN const char* sData, size_t nSize);

// 返回当前日期时间的字符串，默认：2018-10-12_21:20:10
CString GetNowTimeStr(LPCSTR lpszFormat = NULL);

// 获取文件名，斜杠反斜杠后面的（包含扩展名）
CString GetFileName(const CString&strFilePath);

// 获取文件扩展名（包含点），不改变大小写
CString GetFileExt(const CString& strFilePath);

// 获取路径的父目录，最后带斜杠
CString GetParentPath(const CString& strFilePath);

// 获取文件名，斜杠反斜杠后面的（不包含扩展名）
CString GetFileNameWithoutExt(const CString& strFilePath);

// 获取文件对应的新的文件路径
CString GetNewFilePath(const CString& strFilePath, const CString& strAppendText);

//// 获取路径的全路径，例如获取相对路径的全路径
//CString getFullPath(LPCTSTR lpszPath);

// 标准化路径，例如：c:\1\2\..\ 返回c:\1
CString getStandardPath(LPCTSTR lpszPath);

// 获取待启动的三方App
CString get3rdAppCmd(CString strFilePath);

// 运行与tag同名的Python文件（如果有的话）的命令行
//CString getSameCommandPythonFileLaunchCmd(const CString&strCmdName, const CString& strFilePath, bool isMultiFiles);

void Log(LPCTSTR lpszFormat, ...);