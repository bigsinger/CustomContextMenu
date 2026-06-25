#include "stdafx.h"
#include "resource.h"
#include "CustomContextMenuC_i.h"
#include "Utils.h"
#include "compreg.h"

HINSTANCE g_instance = NULL;
LONG g_objectCount = 0;
static LONG g_lockCount = 0;

typedef struct ClassFactory {
    IClassFactory iface;
    LONG refCount;
} ClassFactory;

static HRESULT STDMETHODCALLTYPE Factory_QueryInterface(IClassFactory *iface, REFIID riid, void **ppv)
{
    ClassFactory *factory = CONTAINING_RECORD(iface, ClassFactory, iface);

    if (!ppv) {
        return E_POINTER;
    }
    *ppv = NULL;

    if (IsEqualIID(riid, &IID_IUnknown) || IsEqualIID(riid, &IID_IClassFactory)) {
        *ppv = iface;
        InterlockedIncrement(&factory->refCount);
        return S_OK;
    }

    return E_NOINTERFACE;
}

static ULONG STDMETHODCALLTYPE Factory_AddRef(IClassFactory *iface)
{
    ClassFactory *factory = CONTAINING_RECORD(iface, ClassFactory, iface);
    return (ULONG)InterlockedIncrement(&factory->refCount);
}

static ULONG STDMETHODCALLTYPE Factory_Release(IClassFactory *iface)
{
    ClassFactory *factory = CONTAINING_RECORD(iface, ClassFactory, iface);
    LONG refs = InterlockedDecrement(&factory->refCount);

    if (refs == 0) {
        InterlockedDecrement(&g_objectCount);
        free(factory);
    }

    return (ULONG)refs;
}

static HRESULT STDMETHODCALLTYPE Factory_CreateInstance(IClassFactory *iface, IUnknown *outer, REFIID riid, void **ppv)
{
    UNREFERENCED_PARAMETER(iface);

    if (outer) {
        return CLASS_E_NOAGGREGATION;
    }

    return ShellMenuExt_CreateInstance(riid, ppv);
}

static HRESULT STDMETHODCALLTYPE Factory_LockServer(IClassFactory *iface, BOOL lock)
{
    UNREFERENCED_PARAMETER(iface);

    if (lock) {
        InterlockedIncrement(&g_lockCount);
    } else {
        InterlockedDecrement(&g_lockCount);
    }
    return S_OK;
}

static const IClassFactoryVtbl g_factoryVtbl = {
    Factory_QueryInterface,
    Factory_AddRef,
    Factory_Release,
    Factory_CreateInstance,
    Factory_LockServer
};

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID reserved)
{
    UNREFERENCED_PARAMETER(reserved);

    if (reason == DLL_PROCESS_ATTACH) {
        g_instance = instance;
        DisableThreadLibraryCalls(instance);
        GetModuleDirectory(instance, g_modulePath, ARRAYSIZE(g_modulePath));
    } else if (reason == DLL_PROCESS_DETACH) {
        ShutdownImageLoader();
    }

    return TRUE;
}

STDAPI DllCanUnloadNow(void)
{
    return (g_objectCount == 0 && g_lockCount == 0) ? S_OK : S_FALSE;
}

STDAPI DllGetClassObject(REFCLSID clsid, REFIID riid, LPVOID *ppv)
{
    ClassFactory *factory;
    HRESULT hr;

    if (!ppv) {
        return E_POINTER;
    }
    *ppv = NULL;

    if (!IsEqualCLSID(clsid, &CLSID_CompReg)) {
        return CLASS_E_CLASSNOTAVAILABLE;
    }

    factory = (ClassFactory *)calloc(1, sizeof(ClassFactory));
    if (!factory) {
        return E_OUTOFMEMORY;
    }

    factory->iface.lpVtbl = (IClassFactoryVtbl *)&g_factoryVtbl;
    factory->refCount = 1;
    InterlockedIncrement(&g_objectCount);

    hr = Factory_QueryInterface(&factory->iface, riid, (void **)ppv);
    Factory_Release(&factory->iface);
    return hr;
}

STDAPI DllRegisterServer(void)
{
    return RegisterShellExtension();
}

STDAPI DllUnregisterServer(void)
{
    return UnregisterShellExtension();
}

STDAPI DllInstall(BOOL install, LPCWSTR commandLine)
{
    UNREFERENCED_PARAMETER(commandLine);

    if (install) {
        HRESULT hr = DllRegisterServer();
        if (FAILED(hr)) {
            DllUnregisterServer();
        }
        return hr;
    }

    return DllUnregisterServer();
}
