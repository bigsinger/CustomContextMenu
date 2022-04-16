自定义系统右键菜单工具-使用说明

# 安装与卸载

- 安装：**以管理员身份运行**：install.bat

- 卸载：**以管理员身份运行**：uninstall.bat，由于是重启了explorer.exe，所以卸载后DLL文件可以直接删除。

# 设计模式

主要分为固定部分和可配置部分，固定部分主要是保持Windows Shell编程的透明，使用者无须关心右键的菜单如何创建、展示和响应的。

可配置部分主要是自定义菜单和菜单的响应事件。

![](./doc/design.png)

# 自定义菜单配置

## 菜单配置文件示例
在bin目录下修改menu.xml，默认给出了一个模板：
```xml
<?xml version="1.0"?>
<menu name="安卓右键工具" icon="icon\logo.png" run="..\..\APKInfo\APKInfo\bin\APKInfo.exe" debug="0">
  <menu name="复制路径" icon="icon\copypath.png" arg="{0} copypath"/>
  <menu name="DEX 》JAR" icon="icon\dex2jar.png" arg="{0} dex2jar"/>
  <menu name="Manifest 》TXT | AXML 》TXT" icon="icon\m2txt.png" arg="{0} axml2txt"/>
  <menu name="查看APK信息" icon="icon\apkinfo.png" arg="{0} viewapk"/>
  <menu name="查看签名信息" icon="icon\signinfo.png" arg="{0} viewsign"/>
  <menu name="签名" arg="{0} sign" icon="icon\sign.png"/>
  <menu/>
  <menu name="安装（卸载安装）" icon="icon\install.png" arg="{0} installd"/>
  <menu name="安装（替换安装）" icon="icon\installr.png" arg="{0} installr"/>
  <menu name="卸载" icon="icon\uninstall.png" arg="{0} uninstall"/>
  <menu name="查壳" icon="icon\detect.png" arg="{0} viewwrapper"/>
  <menu name="手机信息" icon="icon\phone.png" arg="{0} phone"/>
  <menu name="手机截图" icon="icon\photo.png" arg="{0} photo"/>
  <menu name="提取图标" icon="icon\extracticon.png" arg="{0} icon"/>
  <menu name="zipalign优化" icon="icon\align.png" arg="{0} zipalign"/>
  <menu name="反编译" icon="icon\decom.png" arg="{0} baksmali"/>
  <menu name="回编译" icon="icon\build.png" arg="{0} smali"/>
  <menu name="自定义插件" icon="icon\plug.png">
    <menu name="插件1" arg="{0} plug1"/>
    <menu name="插件2" arg="{0} plug2"/>
    <menu name="插件3" arg="{0} plug3"/>
  </menu>
  <menu name="关于" icon="icon\about.png" arg="{0} about"/>
</menu>
```
## 根菜单说明

- **name**：显示在系统右键菜单中的名称。

- **icon**：可选，显示在系统右键菜单中的图标。

- **debug**：可选，默认为"0"，调用三方应用时会以隐藏窗口模式运行，且不输出日志。设置为 "1" 时，调用三方应用以显式窗口模式运行，并可以通过**DebugView**查看日志输出，同时本目录下会生成名为 **log.txt** 的日志文件，方便排查：

  ```xml
  <menu name="安卓右键工具" icon="icon\logo.png" debug="1">
      ...
  </menu>
  ```

  

- **run**：可选，表示用户点击了子菜单命令后需要调用的三方应用，路径支持绝对路径和相对路径，使用相对路径时是以当前目录为准。该属性为有可继承属性，如果当前子节点未设置该属性，则使用父级节点的该属性值。目前支持以下几种扩展名路径：

  - exe：调用该exe程序：

    ```xml
    <menu name="安卓右键工具" icon="icon\logo.png" run="xxx.exe">
        ...
    </menu>
    ```

    调用的参数序列为：**xxx.exe arg [files]**

    

  - py：调用Python脚本：

    ```xml
    <menu name="安卓右键工具" icon="icon\logo.png" run="xxx.py">
        ...
    </menu>
    ```

    调用的参数序列为：**python xxx.py arg [files]**

    

  - jar：调用jar包：

    ```xml
    <menu name="安卓右键工具" icon="icon\logo.png" run="xxx.jar">
        ...
    </menu>
    ```

    调用的参数序列为：**java -jar xxx.jar arg [files]**

    
  
  - lua：调用本目录下名为 **runlua.exe** 的程序执行该lua脚本文件：
  
    ```xml
    <menu name="安卓右键工具" icon="icon\logo.png" run="xxx.lua">
        ...
    </menu>
    ```
  
    调用的参数序列为：**runlua.exe xxx.lua arg [files]**
  
    

## 子菜单说明

- 一个菜单项四个属性，分别为**name**，**icon**，**run**和**arg**。
- 如果name为空，则该菜单项为分隔条，例如配置分隔条可以这样配置：

```
<menu/>
```

- icon指示了菜单项的图标文件，以相对路径填写，相对于DLL的所在目录。例如：icon\logo.png，若不填写或者指示的图标文件不存在或者加载失败，则条菜单项前面不会出现图标，问题不大。为了加快菜单的加载速度，也可以全部不配置图标文件。
- run：可选，表示用户点击了子菜单命令后需要调用的三方应用，路径支持绝对路径和相对路径，使用相对路径时是以DLL的所在目录为准。该属性为有可继承属性，如果当前子节点未设置该属性，则使用父级节点的该属性值。见根菜单中对应run属性的说明。
- arg：如果该项菜单没有子菜单，也不是分隔条，那么就要响应事件，则arg指示了响应的事件名称，最终会被传递到三方程序中。以**{0}**表示待处理的文件名。
- 如果菜单含有子菜单项，则按示例menu.xml添加即可。最多支持二级菜单项，不支持更深层次的子菜单。

## 效果截图

![](./doc/screenshot1.png)

![](./doc/screenshot2.png)

## 如何响应事件

点击任意菜单项后，菜单的arg名称和选择的文件会被传递到三方App中，传递的参数形式为：

```
App arg [files]
```
arg属性中的**{0}**会替换为选中的文件路径。



如果用户只选择了一个文件，则参数形式为：

```
App arg
```
如果用户只选择了多个文件，则参数形式为：
```
App arg files
```
也即出现开关files，也可以认为多了一个参数标志。当出现这个标志时，file是一个纯文本的文件全路径，内容是用户选择的多个文件列表，逐行列出。



具体调用哪个App取决于菜单配置文件中的**run**值，可以参考前面的章节以及目录下的示例脚本。



## 注意

- menu.xml配置文件需要utf-8格式
- 选择多文件时生成的临时文件是utf-8格式的
- 日志文件是utf-8格式的



# 更新日志

#### 2022年4月16日

- 支持更灵活的外部调用，如exe程序、python脚本、jar包、lua脚本等，可以快速集成现成工具。

#### 2020年7月28日

- 在 **CustomContextMenu.dll** 同目录下如果出现与菜单中 arg 同名的 Python 文件，则也会调用。例如某子菜单项的 arg 为 decodeFile，且在同目录下存在 decodeFile.py，则右键的时候会调用本地安装的 Python 执行该文件，传递的参数就是右键选中的文件路径，多文件选中时规则同前面章节。

#### 2020年6月1日

- 增加 **debug** 调试开关，开关打开时有日志输出且三方调用不隐藏窗口，方便排错
- 增加 **apptype** 选项，使得响应事件的三方可以是exe、Lua脚本、Python脚本
