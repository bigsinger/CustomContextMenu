#include "stdafx.h"
#include <time.h>
#include <strsafe.h>
#include <atlimage.h>
#include "Const.h"
#include "Utils.h"
//#include <Gdiplus.h>
//using namespace Gdiplus;
//#pragma comment(lib,"gdiplus") 


CString GetStartPath(HMODULE hModule/* = NULL*/) {
	TCHAR szTemp[MAX_PATH];
	GetModuleFileName(hModule, szTemp, sizeof(szTemp) / sizeof(TCHAR));
	_tcsrchr(szTemp, '\\')[1] = 0;
	return (CString)szTemp;
}

HBITMAP LoadImageFromFile(const wchar_t *szFileName) {
	if (::GetFileAttributes(szFileName) == -1) {
		return NULL;
	}

	HBITMAP hBitmap = NULL;
	//ULONG_PTR gdiplusToken;
	//Gdiplus::GdiplusStartupInput gdiplusStartupInput;
	//Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);

	Gdiplus::Bitmap *pBitmap = Gdiplus::Bitmap::FromFile(szFileName);
	if (pBitmap != NULL) {
		Gdiplus::Status result = pBitmap->GetLastStatus();
		if (result == Gdiplus::Ok) {
			pBitmap->GetHBITMAP(NULL, &hBitmap);
		}
		delete pBitmap;
	}
	//Gdiplus::GdiplusShutdown(gdiplusToken);
	return hBitmap;
}

// 如果debug打开，则显示运行三方App
BOOL Run(const CString& strCmdLine, LPCTSTR lpszCurrentDir, DWORD dwMilliseconds) {
	BOOL bSuccess = FALSE;
	if (!strCmdLine.IsEmpty()) {
		PROCESS_INFORMATION pi;
		STARTUPINFO si = { sizeof(si) };
		si.dwFlags = STARTF_USESHOWWINDOW;
		si.wShowWindow = SW_SHOW;
		//si.wShowWindow = g_isDebug ? SW_SHOW : SW_HIDE;

		bSuccess = ::CreateProcess(NULL, (LPTSTR)(LPCTSTR)strCmdLine, NULL, NULL, FALSE, 0, NULL, lpszCurrentDir, &si, &pi);
		if (dwMilliseconds!=0) {
			DWORD dwStatus = WaitForSingleObject(pi.hProcess, dwMilliseconds);
			if (dwStatus == WAIT_TIMEOUT) {
				// ...
			}
			
		}
		CloseHandle(pi.hThread);
		CloseHandle(pi.hProcess);
	}
	return bSuccess;
}

//void RunAsyn(const CString& strCmdLine, LPCTSTR lpszCurrentDir) {
//	std::thread t = std::thread([=]{
//		BOOL bSuccess = Run(strCmdLine, lpszCurrentDir, INFINITE);
//		if (!bSuccess) {
//			ShowTips(_T("执行失败!"));
//			MessageBox(NULL, _T("未能正常执行，请检查配置是否正确: \n\n") + strCmdLine, g_sMainMenuName, MB_OK);
//		} else {
//			ShowTips(_T("执行成功!"));
//		}
//	});
//	t.detach();
//}

//换行要用\r\n
BOOL CopyToClipboard(const CString&strText) {
	if (strText.IsEmpty() == true) {
		return FALSE;
	}

	CStringA strTextA;
	strTextA = strText;
	HGLOBAL hClip = GlobalAlloc(GHND | GMEM_SHARE, strTextA.GetLength() + 1);
	if (hClip == NULL) {
		return FALSE;
	}

	char *pBuff = (char*)GlobalLock(hClip);
	if (pBuff == NULL) {
		GlobalFree(hClip);
		return FALSE;
	}

	memcpy(pBuff, (LPCSTR)strTextA, strTextA.GetLength());
	pBuff[strTextA.GetLength()] = 0;
	GlobalUnlock(hClip);

	if (OpenClipboard(NULL)) {
		EmptyClipboard();
		SetClipboardData(CF_TEXT, hClip);
		CloseClipboard();
	}

	//注意：这里不能释放，否则会每隔一次设置不成功的。
	//GlobalFree(hClip);
	return TRUE;
}

void ShowTips(LPCTSTR szTips, LPCTSTR szTitle/* = NULL*/) {
	CString strTitle;
	if (szTitle == NULL) {
		strTitle = g_sMainMenuName;
	} else {
		strTitle = szTitle;
	}
	//MessageBox(NULL, szTips, NULL, 0);
	NOTIFYICONDATA m_NotifyIconData;
	m_NotifyIconData.cbSize = (DWORD)sizeof(NOTIFYICONDATA);
	m_NotifyIconData.hWnd = (HWND)GetModuleHandle(NULL);
	m_NotifyIconData.uID = NULL;
	m_NotifyIconData.uFlags = NIF_MESSAGE | NIF_TIP | NIF_INFO; // 设置托盘图标功能;
	m_NotifyIconData.uCallbackMessage = NULL; // 设置响应消息ID;
	m_NotifyIconData.hIcon = NULL;//LoadIcon(GetModuleHandle(NULL), MAKEINTRESOURCE(IDI_ICON1)); // 读取图标;
	Shell_NotifyIcon(NIM_ADD, &m_NotifyIconData);// 添加托盘图标;
	m_NotifyIconData.dwInfoFlags = NIIF_INFO;
	StringCchCopy(m_NotifyIconData.szInfoTitle, _countof(m_NotifyIconData.szInfoTitle), strTitle);
	StringCchCopy(m_NotifyIconData.szInfo, _countof(m_NotifyIconData.szInfo), szTips);
	m_NotifyIconData.uTimeout = 700; // 超时时间
	Shell_NotifyIcon(NIM_MODIFY, &m_NotifyIconData);
}

CString utf8s2ts(const char*lpszText, int nSize/* = -1*/) {
	CString strResult;
	CStringW strTextW;
	if (lpszText == NULL) {
		return strResult;
	}

	int len = MultiByteToWideChar(CP_UTF8, 0, lpszText, nSize, NULL, 0);
	WCHAR * wszUnicode = new WCHAR[len + 1]();
	MultiByteToWideChar(CP_UTF8, 0, lpszText, nSize, wszUnicode, len);
	strTextW = wszUnicode;
	delete[] wszUnicode;
#ifdef _UNICODE
	return strTextW;
#else
	strResult = strTextW;
	return strResult;
#endif
}

CStringA ts2utf8s(const CString&str) {
	CStringW strW;
	LPCWSTR lpwstrSrc = NULL;
	int cchWideChar = 0;
	CStringA strResultA;

#ifdef _UNICODE
	lpwstrSrc = str;
	cchWideChar = str.GetLength();
#else
	strW = str;
	lpwstrSrc = strW;
	cchWideChar = strW.GetLength();
#endif

	char *pBuff = NULL;
	int nLen = WideCharToMultiByte(CP_UTF8, 0, lpwstrSrc, cchWideChar, NULL, 0, NULL, NULL);
	if (nLen > 0) {
		pBuff = new char[nLen + 1]();
		if (pBuff != NULL) {
			WideCharToMultiByte(CP_UTF8, 0, lpwstrSrc, cchWideChar, pBuff, nLen, NULL, NULL);
			pBuff[nLen] = 0;
			strResultA = pBuff;
			delete[] pBuff;
		}
	}

	return strResultA;
}

bool writefile(IN const char*strFileName, IN const char* sData, size_t nSize) {
	FILE* fp = NULL;
	fopen_s(&fp, strFileName, "wb");
	if (fp != NULL) {
		fwrite(sData, sizeof(char), nSize, fp);
		fclose(fp);
		return true;
	}

	return false;
}

CString GetNowTimeStr(LPCSTR lpszFormat/* = NULL*/) {
	time_t t;
	time(&t);
	char tmp[64] = { 0 };
	struct tm tmTemp;
	localtime_s(&tmTemp, &t);
	if (lpszFormat) {
		strftime(tmp, sizeof(tmp), lpszFormat, &tmTemp);
	} else {
		strftime(tmp, sizeof(tmp), "%Y%m%d%H%M%S", &tmTemp);
	}
	return (CString)tmp;
}

CString GetFileName(const CString&strFilePath) {
	CString strFileName = strFilePath;
	strFileName.Replace('/', '\\');
	int nPos = strFileName.ReverseFind('\\');
	if (nPos != -1) {
		strFileName = strFileName.Mid(nPos + 1);
	}

	return strFileName;
}

CString GetFileExt(const CString& strFilePath) {
	CString strExt;
	int nPos = strFilePath.ReverseFind('.');
	if (nPos != -1) {
		strExt = strFilePath.Mid(nPos);
	}

	return strExt;
}

CString GetParentPath(const CString& strFilePath) {
	CString strPath;
	strPath = strFilePath;
	strPath.Replace('/', '\\');

	if (strPath.Right(1) == "\\") {
		strPath = strPath.Left(strPath.GetLength() - 1);
	}

	int nPos = strPath.ReverseFind('\\');
	if (nPos != -1) {
		strPath = strPath.Left(nPos + 1);
	}

	return strPath;
}

CString GetFileNameWithoutExt(const CString& strFilePath) {
	CString strFileName = strFilePath;
	strFileName.Replace('/', '\\');

	int nPos = strFileName.ReverseFind('\\');
	int nPos2 = 0;

	if (nPos != -1) {
		if (GetFileAttributes(strFileName) & FILE_ATTRIBUTE_DIRECTORY) {
			nPos2 = strFileName.GetLength();
		} else {
			nPos2 = strFileName.ReverseFind('.');
			if (nPos2 == -1) {
				nPos2 = strFileName.GetLength();
			}
		}
		strFileName = strFileName.Mid(nPos + 1, nPos2 - nPos - 1);
	}

	return strFileName;
}

// 获取文件对应的新的文件路径
CString GetNewFilePath(const CString& strFilePath, const CString& strAppendText) {
	return GetParentPath(strFilePath) + GetFileNameWithoutExt(strFilePath) + strAppendText + GetFileExt(strFilePath);
}

//// 获取路径的全路径，例如获取相对路径的全路径
//CString getFullPath(LPCTSTR lpszPath) {
//	TCHAR path[MAX_PATH * 2] = { 0 };
//	GetFullPathName(lpszPath, MAX_PATH, path, NULL);
//	return path;
//}

// 标准化路径，例如：c:\1\2\..\ 返回c:\1
CString getStandardPath(LPCTSTR lpszPath) {
	TCHAR szPath[MAX_PATH] = { 0 };
	PathCanonicalize(szPath, lpszPath);
	return szPath;
}

// 获取待启动的三方App
CString get3rdAppCmd(CString strFilePath) {
	CString strCmd;
	CString strExt = GetFileExt(strFilePath).MakeLower();
	if (strExt.Compare(_T(".jar")) == 0) {
		strCmd.Format(_T("java -jar \"%s\""), (LPCTSTR)strFilePath);
	} else if (strExt.Compare(_T(".py")) == 0) {
		strCmd.Format(_T("python \"%s\""), (LPCTSTR)strFilePath);
	}else if (strExt.Compare(_T(".lua")) == 0) {
		strCmd.Format(_T("\"%srunlua.exe\" \"%s\""), (LPCTSTR)g_sModulePath, (LPCTSTR)strFilePath);
	} else {
		// default
		strCmd = strFilePath;
	}

	return strCmd;
}

// 运行与tag同名的Python文件（如果有的话）的命令行
//CString getSameCommandPythonFileLaunchCmd(const CString& strCmdName, const CString& strFilePath, bool isMultiFiles) {
//	CString strCmd;
//	CString strPythonFile = g_sModulePath + strCmdName + _T(".py");
//	if (::GetFileAttributes(strPythonFile) != -1) {
//		strCmd.Format(_T("python \"%s\" \"%s\""), (LPCTSTR)strPythonFile, (LPCTSTR)strFilePath);
//		if (isMultiFiles) {
//			strCmd.Append(_T(" files"));
//		}
//	}
//	return strCmd;
//}

void Log(LPCTSTR lpszFormat, ...) {
	if (g_isDebug) {
		CString strText;
		va_list args;
		va_start(args, lpszFormat);
		strText.FormatV(lpszFormat, args);
		va_end(args);
		strText += _T("\n");
		OutputDebugString(strText);

		CStringA strData = ts2utf8s(strText);
		FILE* fp = NULL;
		_tfopen_s(&fp, g_sModulePath + _T("log.txt"), _T("ab+"));	// 追加
		if (fp) {
			fwrite(strData, sizeof(BYTE), strData.GetLength(), fp);
			fclose(fp);
		}
	}
}