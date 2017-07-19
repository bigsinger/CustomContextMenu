#coding:utf-8

'''
说明：右键增强工具的菜单项处理代码。
测试时可以把【DEBUG】变量开关打开，直接调用on_command函数，测试通过后关闭【DEBUG】变量开关。
实时生效，无须重启explorer。

author: bigsing
'''
import os
import sys
import shutil
import zipfile
import logging
import tempfile
import traceback
try:
    import star
    from star.APK import APK
    from star.AXMLPrinter import *
    from star.ADBManager import ADBManager
    from PathManager import *
    from Constant import Constant
    from xml.dom import minidom
except Exception as e:
    print traceback.format_exc()
    os.system('pause')

DEBUG = False

'''
params: [0]oncommand.py [1]command  [2]filepath [files]
    |-->params[0]：this py file。
    |-->params[1]：command string。命令字符串，菜单项的tag标签，指示当前点击了哪个菜单命令。
    |-->params[2]：filepath。当前选择的文件（或文件夹）的全路径
    |-->params[3]：可选，标志位，如果有“files”开关则说明用户选择了多个文件，则参数3是一个文本文件，里面逐行记录了选择的文件全路径。
return: ret, msg
    |-->ret: 如果成功返回0, msg可以为空也可以为一些提示信息。失败返回非0值，此时msg为错误详情。
    |-->msg：错误详情信息。
'''
def on_command(params):
    ret = 0  # 默认返回成功
    msg = None

    paramCount = len(params)
    isMultiFiles = False
    if params is None or paramCount < 3:
        print params[0]
        print params[1]
        return -1, u'参数不对，需要传至少 3 个参数'
    CMD_STR = params[1]
    filesSelected = params[2]
    if paramCount > 3:
        isMultiFiles = True
    if sys.platform == 'win32':
        # win下命令行参数为gbk编码，转换为UNICODE
        filesSelected = filesSelected.decode('gbk', 'ignore')
    print str(paramCount) + ' ' + CMD_STR + ' ' + filesSelected

    if CMD_STR=='dex2jar':
        ret, msg = dex2jar(filesSelected)
    elif CMD_STR == 'axml2txt':
        ret, msg = axml2txt(filesSelected)
    elif CMD_STR == 'viewapk':
        ret, msg = viewapk(filesSelected)
    elif CMD_STR == 'viewsign':
        ret, msg = viewsign(filesSelected)
    elif CMD_STR == 'sign':
        ret, msg = sign(filesSelected)
    elif CMD_STR == 'installd':
        ret, msg = installd(filesSelected)
    elif CMD_STR == 'installr':
        ret, msg = installr(filesSelected)
    elif CMD_STR == 'uninstall':
        ret, msg = uninstall(filesSelected)
    elif CMD_STR == 'viewwrapper':
        # TODO
        return -1, u'未实现命令：' + CMD_STR + u' 等你来写……'
    elif CMD_STR == 'phone':
        ret, msg = viewphone(filesSelected)
    elif CMD_STR == 'photo':
        ret, msg = photo(filesSelected)
    elif CMD_STR == 'icon':
        ret, msg = extracticon(filesSelected)
    elif CMD_STR == 'zipalign':
        # TODO
        return -1, u'未实现命令：' + CMD_STR + u' 等你来写……'
    elif CMD_STR == 'baksmali':
        ret, msg = baksmali(filesSelected)
    elif CMD_STR == 'smali':
        print u'smali'
        ret, msg = smali(filesSelected)
    elif CMD_STR == 'md2html':
        ret, msg = md2html(filesSelected)
    elif CMD_STR == 'md2pdf':
        ret, msg = md2pdf(filesSelected)
    elif CMD_STR == 'plug3':
        ret, msg = plug(filesSelected)
    elif CMD_STR == 'about':
        print u'右键工具v3.0 by bising'
        os.system('pause')
        # star.runcmd2([PathManager.get_about_path()])
    elif CMD_STR == 'notepad':
        ret, msg = star.run_cmd_asyn(['notepad', star.unicode2gbk(filesSelected)])
    elif CMD_STR == 'hex':
        print u'open with hex tool'
        tool = PathManager.get_hextool_path()
        ret, msg = star.run_cmd_asyn([star.unicode2gbk(tool), star.unicode2gbk(filesSelected)])
    elif CMD_STR == 'lua':
        print u'open with Lua Editor'
        tool = PathManager.get_luaeditor_path()
        ret, msg = star.run_cmd_asyn([star.unicode2gbk(tool), star.unicode2gbk(filesSelected)])
    elif CMD_STR == 'luyten':
        print u'open with luyten'
        tool = PathManager.get_luyten_path()
        ret, msg = star.run_cmd_asyn([star.unicode2gbk(tool), star.unicode2gbk(filesSelected)])
    elif CMD_STR == 'jdgui':
        print u'open with jdgui'
        tool = PathManager.get_jdgui_path()
        ret, msg = star.run_cmd_asyn([star.unicode2gbk(tool), star.unicode2gbk(filesSelected)])
    else:
        return -1, u'未实现命令：' + CMD_STR + u' 等你来写……'
    return ret, msg

# 支持APK、DEX转换为Jar，TODO：APK里有多个DEX的时候都要转换，等你来写……
def dex2jar(f):
    jarFile = os.path.splitext(f)[0] + '.jar'
    retcode, msg = star.runcmd2([PathManager.get_dex2jar_path(), f, '-f', '-o', jarFile])
    if retcode==0:
        star.run_cmd_asyn([PathManager.get_jdgui_path(), jarFile])
        print 'dex2jar ok'
    return retcode, msg

# AXML文件转换为纯文本，如果是APK包则自动抽取AndroidManifest.xml并转换。
def axml2txt(f):
    ret = 0
    msg = None
    ext = os.path.splitext(f)[1].lower()
    txtFile = None
    if ext=='.apk':
        print 'axml2txt .apk'
        zfile = zipfile.ZipFile(f, 'r', compression=zipfile.ZIP_DEFLATED)
        for p in zfile.namelist():
            if p == "AndroidManifest.xml":
                axmlFile = os.path.join(Utils.getparent(f), 'AndroidManifest.xml')
                file(axmlFile, 'wb').write(zfile.read(p))
                txtFile = axmlFile + '.txt'
                star.runcmd2([PathManager.get_axmlprinter_path(), axmlFile, '>', txtFile])
                break
    else:
        txtFile = f + '.txt'
        ret, msg = star.runcmd2([PathManager.get_axmlprinter_path(), f, '>', txtFile])
        print 'axml2txt .xml'
    if os.path.exists(txtFile):
        star.run_cmd_asyn(['notepad', txtFile])

    print 'axml2txt ok'
    return ret, msg

# 查看APK的信息，TODO：最好能判断出是否是游戏，如果是游戏的话又是什么引擎的，等你来写……
def viewapk(f):
    infoFile = os.path.splitext(f)[0] + '_apkinfo.txt'
    retcode, msg = star.runcmd2([PathManager.get_aapt_path(), 'dump', 'badging', f])
    if retcode==0:
        package = star.find("package: name='(.*?)'", msg)
        versionCode = star.find("versionCode='(.*?)'", msg)
        versionName = star.find("versionName='(.*?)'", msg)
        appName = star.find("application-label:'(.*?)'", msg)
        activity = star.find("launchable-activity: name='(.*?)'", msg)
        print package
        print versionCode
        print versionName
        print appName
        print activity
        info = '软件名称: {0}\n软件包名: {1}\n软件版本: {2} ( {3} )\n启动Activity: {4}\n'.format(appName, package, versionName, versionCode, activity)
        star.log(info, infoFile)
        # APK类型探测
        detectApk(f)
        # 打开日志文件
        if os.path.exists(infoFile):
            star.run_cmd_asyn(['notepad', infoFile])
    return retcode, msg

# TODO
def detectApk(f):
    pass
    return 0, None

# 查看APK的签名信息
def viewsign(f):
    infoFile = os.path.splitext(f)[0] + '_signinfo.txt'
    code, info = star.runcmd2([PathManager.get_keytool_path(), '-printcert', '-jarfile', f])
    if code == 0:
        star.log(info, infoFile)
        if os.path.exists(infoFile):
            star.run_cmd_asyn(['notepad', infoFile])
    return code, info

# 签名
def sign(f):
    return star.runcmd2([PathManager.get_signtool_path(), f])

# 通过命令行输出检查是否成功，最常见的问题就是“忘记签名”
def checkIsInstalledSuccess(msg):
    if msg.find('Success')==-1:
        error = star.find('Failure \[(.*?)\]', msg)
        if error=='INSTALL_PARSE_FAILED_NO_CERTIFICATES':
            print u'没签名或者签名不对，请重新签名!\n错误详情：\n'
        elif error=='INSTALL_FAILED_OLDER_SDK':
            print u'INSTALL_FAILED_OLDER_SDK 错误是什么鬼？\n'
        print msg
        os.system('pause')

# 卸载安装
def installd(f):
    apk = APK(f)
    package = apk.get_package()
    adb = ADBManager()
    adb.uninstall(package)
    code, msg = adb.install(f)
    checkIsInstalledSuccess(msg)
    return 0, None

# 替换安装
def installr(f):
    adb = ADBManager()
    code, msg = adb.install(f, '-r')
    checkIsInstalledSuccess(msg)
    return 0, None

# 卸载应用
def uninstall(f):
    apk = APK(f)
    package = apk.get_package()
    adb = ADBManager()
    adb.uninstall(package)
    return 0, None

# 查看手机信息
def viewphone(f):
    adb = ADBManager()
    ret, model = adb.shell('getprop ro.product.model')
    ret, name = adb.shell('getprop ro.product.name')
    ret, release = adb.shell('getprop ro.build.version.release')
    ret, sdk = adb.shell('getprop ro.build.version.sdk')
    ret, cpu = adb.shell('getprop ro.product.cpu.abi')
    ret, cpu2 = adb.shell('getprop ro.product.cpu.abi2')
    ret, serialno = adb.shell('getprop ro.serialno')
    ret, imei = adb.shell('getprop gsm.sim.imei')
    ret, androidid = adb.shell('getprop net.hostname')
    ret, description = adb.shell('getprop ro.build.description')
    ret, mac = adb.shell('cat /sys/class/net/wlan0/address')
    ret, size = adb.shell('wm size')
    if ret==0:
        size = star.find('size: (.*?)\s', size)

    infoFile = os.path.splitext(f)[0] + '_phone.txt'
    star.log('手机类型：' + model, infoFile)
    star.loga('手机名称：' + name, infoFile)
    star.loga('系统版本：' + release, infoFile)
    star.loga('API版本：' + sdk, infoFile)
    star.loga('CPU：' + cpu, infoFile)
    star.loga('CPU2：' + cpu2, infoFile)
    star.loga('MAC：' + mac, infoFile)
    star.loga('序列号：' + serialno, infoFile)
    star.loga('IMEI：' + imei, infoFile)
    star.loga('AndroidId：' + androidid, infoFile)
    star.loga('描述信息：' + description, infoFile)
    star.loga('分辨率：' + size, infoFile)

    if os.path.exists(infoFile):
        star.run_cmd_asyn(['notepad', infoFile])
    return 0, None

# 手机截屏并保存位png图片，TODO：图片复制到剪贴板，等你来写……
# 截图太大感觉不爽？自己修改scale
def photo(f):
    scale = 0.4
    imageFile = os.path.splitext(f)[0] + '.png'
    adb = ADBManager()
    adb.get_screenshot(imageFile, scale)
    return 0, None

# 抽取APK的图标文件，TODO：不同分辨率的图标文件都抽取出来，等你来写……
def extracticon(f):
    dir = os.path.splitext(f)[0]
    retcode, msg = star.runcmd2([PathManager.get_aapt_path(), 'dump', 'badging', f])
    if retcode == 0:
        icons = star.findall("icon.*?'(.+?)'", msg)
        icons = list(set(icons))
        print icons
        zfile = zipfile.ZipFile(f, 'r', compression=zipfile.ZIP_DEFLATED)
        num = 0
        for icon in icons:
            num = num + 1
            iconFile = dir + '_' + str(num) + '.png'
            file(iconFile, 'wb').write(zfile.read(icon))
    return retcode, msg

# 反编译
def baksmali(f):
    print u'反编译完成'
    return star.runcmd2([PathManager.get_apktool_path(), 'd', '-f', f])


# 回编译
def smali(f):
    return star.runcmd2([PathManager.get_apktool_path(), 'b', f])

def md2html(f):
    return star.runcmd2([PathManager.get_mdconverter_path(), f])

def md2pdf(f):
    return star.runcmd2([PathManager.get_mdconverter_path(), f, 'pdf'])

def plug(f):
    print u'等你来写。。。'
    os.system('pause')
    return 0, None

def checkThirdParty():
    # try:
    #     from compiler.ast import flatten
    #     import base64
    #     import array
    # except Exception as e:
    #     print traceback.format_exc()
    pass

if __name__=='__main__':
    ret = 0
    msg = None
    checkThirdParty()
    try:
        if DEBUG:
            ret, msg = on_command([__file__, 'sign', 'C:/Users/hzzhuxingxing/Desktop/test.apk'])
        else:
            ret, msg = on_command(sys.argv)
        if ret!=0 and ret is not None:
            print msg
            os.system('pause')
    except Exception as e:
        print traceback.format_exc()
        os.system('pause')
    if not ret:
        sys.exit(-1)