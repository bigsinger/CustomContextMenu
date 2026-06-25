# 开发文档

## 项目概览

CustomContextMenu 是 Windows Explorer 右键菜单 Shell 扩展。核心 DLL 注册为 COM Inproc Server，资源管理器在右键文件或目录时加载 DLL，DLL 根据 `menu.xml` 插入自定义菜单，并在用户点击菜单项后启动外部工具。

主要目录：

- `src/`：DLL 源码、IDL、资源文件和 Visual Studio 工程。
- `src/res/menu.xml`：内置菜单配置，外部 `menu.xml` 缺失时作为兜底。
- `bin/`：运行目录，包含 DLL、安装脚本、菜单配置、脚本和图标。
- `doc/refer/`：普通注册表右键菜单示例，不依赖 Shell 扩展 DLL。

## 构建环境

本机验证使用：

```bat
D:/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe CustomContextMenuC.sln /t:Rebuild /p:Configuration=Release /p:Platform=x64 /m:1 /v:minimal
```

用户指定的 Visual Studio 入口：

```bat
D:/Microsoft Visual Studio/18/Community/Common7/IDE/devenv.exe CustomContextMenuC.sln /Build "Release|x64"
```

工程保留 `Debug|Win32`、`Release|Win32`、`Debug|x64`、`Release|x64` 配置。实际安装脚本面向 64 位系统，发布时优先构建 `Release|x64`，产物输出到 `bin/CustomContextMenu.dll`。

工程配置要点：

- `CompileAsC`：所有核心源码按 C 编译。
- `/utf-8`：源码统一按 UTF-8 处理。
- 不使用预编译头。
- 不使用 ATL、STL、tinyxml2。
- 链接系统库：`ole32.lib`、`oleaut32.lib`、`uuid.lib`、`shell32.lib`、`user32.lib`、`advapi32.lib`、`gdiplus.lib`。

## 源码结构

`CustomContextMenuC.c` 负责 DLL 入口、COM 类工厂和导出函数：

- `DllMain`
- `DllCanUnloadNow`
- `DllGetClassObject`
- `DllRegisterServer`
- `DllUnregisterServer`
- `DllInstall`

`compreg.c` 负责 Shell 扩展对象：

- `IShellExtInit`：读取当前选中的文件列表。
- `IContextMenu`：插入菜单、响应点击。
- 菜单树、命令表和文件列表的动态内存管理。
- XML 菜单解析和注册表写入。

`Utils.c` 负责通用能力：

- UTF-8 到 UTF-16 转换。
- 路径解析和文件名拆分。
- 占位符替换。
- 命令行拼接和 `CreateProcessW` 启动。
- Unicode 剪贴板写入。
- GDI+ flat API 图标加载。
- 调试日志输出。

## 菜单加载流程

加载顺序：

1. 读取 DLL 同目录下的 `menu.xml`。
2. 失败时读取资源 `IDB_XML_MENU`，也就是 `src/res/menu.xml`。

XML 解析器只处理项目需要的菜单子集：

- 标签名：`menu`。
- 属性：`name`、`icon`、`run`、`arg`、`tag`、`debug`。
- 支持 XML 常见转义：`&amp;`、`&quot;`、`&apos;`、`&lt;`、`&gt;`。
- 支持 UTF-8 和 UTF-8 BOM。
- 最大读取 1 MB 的外部 XML，避免资源管理器被异常大配置拖慢。

根菜单的 `run` 是默认执行程序。子菜单未配置 `run` 时，会在点击时回退到根菜单 `run`；二级子菜单未配置 `run` 时，会先继承一级父菜单的 `run`。

## 命令执行流程

用户点击菜单项后：

1. Shell 传入菜单项相对编号。
2. DLL 从命令表取出对应 `run` 和 `arg`。
3. 相对路径按 DLL 所在目录解析。
4. `arg` 中的占位符按当前选中文件替换。
5. 后台线程逐个处理选中的文件。
6. 每个文件调用一次 `CreateProcessW`。

支持占位符：

- `{0}`：DLL 所在目录。
- `{1}`：当前文件完整路径。
- `{path}`：父目录。
- `{name}`：无扩展名文件名。
- `{ext}`：扩展名。

路径占位符在独立参数场景下会自动加引号，降低空格路径导致的执行失败和命令注入风险。涉及 `cmd /c`、重定向、管道等 shell 语法时，仍应优先把复杂逻辑放进脚本或 exe 中。

## 注册和卸载

`DllRegisterServer` 写入：

- COM CLSID 注册。
- 文件右键 Shell 扩展注册。
- 目录右键 Shell 扩展注册。

`DllUnregisterServer` 删除对应分支。

`doc/refer/add_menu.reg` 是普通注册表菜单示例，写入 `HKEY_CLASSES_ROOT\*\shell\...`。这种方式不加载 DLL，适合固定菜单；当前项目的 DLL 扩展方式适合由 XML 集中维护菜单。

## 安全和性能注意点

当前实现已经处理的点：

- 不再使用 ATL/C++/STL/tinyxml2，减少运行时和模板代码体积。
- 选中文件路径动态分配，不再被 `MAX_PATH * 2` 固定缓冲截断。
- 使用 `RegSetValueExW` 写入包含结尾 `NUL` 的注册表字符串。
- `InvokeCommand` 成功分派后返回 `S_OK`。
- 第一个菜单项不再被旧的内部复制路径逻辑吞掉。
- 剪贴板使用 `CF_UNICODETEXT`，避免中文路径丢失。
- 外部 XML 限制大小，避免异常配置拖慢资源管理器。
- 命令执行放在后台线程，避免阻塞右键菜单调用线程。

维护时需要注意：

- Shell 扩展运行在 `explorer.exe` 进程内，不能在菜单创建阶段做耗时操作。
- 不要在 `DllMain` 中做复杂初始化；图标加载在菜单配置加载阶段惰性初始化 GDI+。
- 不要把用户可控路径直接拼进复杂 `cmd /c` 命令。
- 新增依赖前先评估 DLL 体积和 Explorer 稳定性。
- 修改 CLSID 时，需要同步更新 `CustomContextMenuC.idl`、注册说明和安装验证。

## 验证清单

代码修改后至少执行：

```bat
D:/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe CustomContextMenuC.sln /t:Rebuild /p:Configuration=Release /p:Platform=x64 /m:1 /v:minimal
```

安装验证：

1. 管理员运行 `bin/install.bat`。
2. 重启资源管理器或重新登录。
3. 右键文件，确认主菜单出现。
4. 点击一个无副作用菜单项，例如复制路径或打开目录。
5. 管理员运行 `bin/uninstall.bat`，确认菜单消失。

