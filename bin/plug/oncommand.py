# coding:utf-8

'''
说明：右键增强工具的菜单项处理代码。
测试时可以把【DEBUG】变量开关打开，直接调用on_command函数，测试通过后关闭【DEBUG】变量开关。
实时生效，无须重启explorer。

author: bigsing
'''
import json
import os
import re
import sys
import shutil
import traceback
import zipfile
import ZipManager
from io import StringIO

plug_path = os.path.dirname(sys.argv[0])
sys.path.append(os.path.dirname(plug_path))

try:
    from third_part.lib_star import star
    from third_part.lib_star.APK import APK
    from third_part.lib_star.AXMLPrinter import *
    from third_part.lib_star.ADBManager import ADBManager
    from Constant import Constant
    from PathManager import PathManager
    from xml.dom import minidom
    from ApkDetect import ApkDetect
    import win32con
    import win32clipboard
    from PIL import Image
except Exception as e:
    # 执行3方库安装命令
    print(u"检测到所需的三方库未安装，已自动执行安装命令，如果仍然缺失某些三方库，请手动检查安装")
    print(traceback.format_exc())
    require_libs_path = PathManager.get_require_txt_path()
    cmd = ['pip', 'install', '-r', require_libs_path]
    star.runcmd2(cmd)
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
        print(params[0])
        print(params[1])
        return -1, u'参数不对，需要传至少 3 个参数'
    CMD_STR = params[1]
    filesSelected = params[2]
    if paramCount > 3:
        isMultiFiles = True
    if sys.platform == 'win32':
        # win下命令行参数为gbk编码，转换为UNICODE
        filesSelected = filesSelected.decode('gbk', 'ignore')
    print(str(paramCount) + ' ' + CMD_STR + ' ' + filesSelected)

    if CMD_STR == 'dex2jar':
        ret, msg = dex2jar(filesSelected)
    elif CMD_STR == 'axml2txt':
        ret, msg = axml2txt(filesSelected)
    elif CMD_STR == 'viewapk':
        ret, msg = viewapk(filesSelected)
    elif CMD_STR == 'viewsign':
        ret, msg = viewsign(filesSelected)
    elif CMD_STR == 'sign':
        ret, msg = sign(filesSelected)
    elif CMD_STR == 'sign_v1_v2':
        ret, msg = sign_v1_v2(filesSelected)
    elif CMD_STR == 'installd':
        ret, msg = installd(filesSelected)
    elif CMD_STR == 'installr':
        ret, msg = installr(filesSelected)
    elif CMD_STR == 'uninstall':
        ret, msg = uninstall(filesSelected)
    elif CMD_STR == 'viewwrapper':
        ret, msg = viewwrapper(filesSelected)
    elif CMD_STR == 'phone':
        ret, msg = viewphone(filesSelected)
        if ret == 0:
            os.system('pause')
    elif CMD_STR == 'photo':
        ret, msg = photo(filesSelected)
        os.system('pause')
    elif CMD_STR == 'icon':
        ret, msg = extracticon(filesSelected)
        os.system('pause')
    elif CMD_STR == 'zipalign':
        ret, msg = zipalign(filesSelected)
        os.system('pause')
    elif CMD_STR == 'baksmali':
        ret, msg = baksmali(filesSelected)
    elif CMD_STR == 'smali':
        ret, msg = smali(filesSelected)
    elif CMD_STR == 'plug_get_neprotect_ver':
        ret, msg = plug_get_neprotect_ver(filesSelected)
        os.system('pause')
    elif CMD_STR == 'md2html':
        ret, msg = md2html(filesSelected)
    elif CMD_STR == 'md2pdf':
        ret, msg = md2pdf(filesSelected)
    elif CMD_STR == 'plug3':
        ret, msg = plug(filesSelected)
    elif CMD_STR == 'about':
        print(u'右键工具v3.0 by bising')
        os.system('pause')
        # star.runcmd2([PathManager.get_about_path()])
    elif CMD_STR == 'notepad':
        ret, msg = star.run_cmd_asyn(['notepad', star.unicode2gbk(filesSelected)])
    elif CMD_STR == 'hex':
        print('open with hex tool')
        tool = PathManager.get_hextool_path()
        ret, msg = star.run_cmd_asyn([star.unicode2gbk(tool), star.unicode2gbk(filesSelected)])
    elif CMD_STR == 'lua':
        print('open with Lua Editor')
        tool = PathManager.get_luaeditor_path()
        ret, msg = star.run_cmd_asyn([star.unicode2gbk(tool), star.unicode2gbk(filesSelected)])
    elif CMD_STR == 'luyten':
        print('open with luyten')
        tool = PathManager.get_luyten_path()
        ret, msg = star.run_cmd_asyn([star.unicode2gbk(tool), star.unicode2gbk(filesSelected)])
        if ret != 0:  # 说明此时执行命令出错，暂停下让用户能够看到cmd窗口的出错信息
            os.system('pause')
    elif CMD_STR == 'jdgui':
        print('open with jdgui')
        tool = PathManager.get_jdgui_path()
        ret, msg = star.run_cmd_asyn([star.unicode2gbk(tool), star.unicode2gbk(filesSelected)])
    elif CMD_STR == 'md5':
        ret, msg = md5(filesSelected)
        os.system('pause')
    else:
        return -1, u'未实现命令：' + CMD_STR + u'请检查您输入的命令是否正确'
    return ret, msg


def plug_get_neprotect_ver(apk_path):
    version = None
    try:
        import NEProtectVerManager
        version = NEProtectVerManager.get_version(apk_path, PathManager.get_aapt_path())
    except Exception as e:
        print(traceback.format_exc())
        os.system('pause')
        return None, None
    if version:
        print(u'当前apk使用的网易易盾加密的版本号为： ' + version)
        return version, None
    else:
        return None, None


def md5(apk_file):
    if not apk_file.endswith('.apk'):
        print(u"该文件不是apk文件，请选择一个apk文件")
        return None, None
    else:
        cmd = Constant.KEYTOOL_FILENAME + ' -printcert' + ' -jarfile ' + apk_file
        result = os.popen(cmd)
        for line in result.readlines():
            if "MD5" in line:
                print(line)
                return line, None
        return None, None


# 支持APK、DEX转换为Jar，
def dex2jar(f):
    # 如果操作的是apk，则将apk中全部的dex转换为jar文件输出到在apk同级目录下
    if f.endswith('.apk'):
        output_jar_prefix = os.path.splitext(f)[0] + '_'
        temp_dex_dir = PathManager.get_temp_dir_path()
        ZipManager.unzip_dexFile_to_dest(f, temp_dex_dir)
        filenames = os.listdir(temp_dex_dir)
        for dex_name in filenames:
            if dex_name.endswith('.dex'):
                dex_file_path = os.path.join(temp_dex_dir, dex_name)
                jar_file = output_jar_prefix + os.path.splitext(dex_name)[0] + '.jar'
                retcode, msg = star.runcmd2([PathManager.get_dex2jar_path(), dex_file_path, '-f', '-o', jar_file])
                if retcode == 0:
                    star.run_cmd_asyn([PathManager.get_jdgui_path(), jar_file])
                    print('dex2jar ok')
        shutil.rmtree(temp_dex_dir)
        return retcode, msg
    elif f.endswith('.dex'):
        jarFile = os.path.splitext(f)[0] + '.jar'
        retcode, msg = star.runcmd2([PathManager.get_dex2jar_path(), f, '-f', '-o', jarFile])
        if retcode == 0:
            star.run_cmd_asyn([PathManager.get_jdgui_path(), jarFile])
            print('dex2jar ok')
        return retcode, msg
    else:
        print(u'选择文件不合法，文件格式需要是apk或者dex格式')
        os.system("pause")
        return 0, None


# AXML文件转换为纯文本，如果是APK包则自动抽取AndroidManifest.xml并转换。
def axml2txt(f):
    ret = 0
    msg = None
    ext = os.path.splitext(f)[1].lower()
    txtFile = None
    if ext == '.apk':
        print('axml2txt .apk')
        zfile = zipfile.ZipFile(f, 'r', compression=zipfile.ZIP_DEFLATED)
        for p in zfile.namelist():
            if p == "AndroidManifest.xml":
                axmlFile = os.path.join(Utils.getparent(f), 'AndroidManifest.xml')
                file(axmlFile, 'wb').write(zfile.read(p))
                txtFile = axmlFile + '.txt'
                star.runcmd2([PathManager.get_axmlprinter_path(), axmlFile, '>', txtFile])
                break
        os.remove(axmlFile)
    else:
        txtFile = f + '.txt'
        ret, msg = star.runcmd2([PathManager.get_axmlprinter_path(), f, '>', txtFile])
        print('axml2txt .xml')
    if os.path.exists(txtFile):
        star.run_cmd_asyn(['notepad', txtFile])

    print('axml2txt ok')
    return ret, msg


# 查看APK的信息，
def viewapk(apk_path):
    infoFile = os.path.splitext(apk_path)[0] + '_apkinfo.txt'
    retcode, msg = star.runcmd2([PathManager.get_aapt_path(), 'dump', 'badging', apk_path])
    if retcode == 0:
        package = star.find("package: name='(.*?)'", msg)
        versionCode = star.find("versionCode='(.*?)'", msg)
        versionName = star.find("versionName='(.*?)'", msg)
        appName = star.find("application-label:'(.*?)'", msg)
        activity = star.find("launchable-activity: name='(.*?)'", msg)
        print(package)
        print(versionCode)
        print(versionName)
        print(appName)
        print(activity)
        # APK类型探测
        app_type, is_game_app = detectApk(apk_path)
        if is_game_app:
            info = '软件名称: {0}\n软件包名: {1}\n软件版本: {2} ( {3} )\n启动Activity: {4}\n该apk为游戏类型app，使用的游戏引擎为: {5}\n'.format(
                appName, package, versionName, versionCode, activity, ''.join(app_type))
        else:
            info = '软件名称: {0}\n软件包名: {1}\n软件版本: {2} ( {3} )\n启动Activity: {4}\n'.format(appName, package, versionName,
                                                                                       versionCode, activity)
        star.log(info, infoFile)

        # 打开日志文件
        if os.path.exists(infoFile):
            star.run_cmd_asyn(['notepad', infoFile])
    return retcode, msg


def viewwrapper(file_path):
    dict = {'apkPath': file_path, 'aaptPath': PathManager.get_aapt_path()}
    apk_detect = ApkDetect(dict)
    apk_detect.getXmlInfo()
    apk_detect.getWrapperSdk()
    if apk_detect.is_netease_protect:  # 如果是网易加固，提示使用插件获取
        print(apk_detect.wrapperSdk)
        print(u'要查看网易加固版本号，您可使用插件“网易加固版本号”获取')
    else:
        print(apk_detect.wrapperSdk)
    return apk_detect.wrapperSdk, None


def zipalign(apk_path):
    output_apk_name = os.path.splitext(os.path.basename(apk_path))[0] + '_aligned.apk'
    retcode, msg = star.runcmd2(
        [PathManager.get_zipaligin_tool_path(), '-f', '4', apk_path,
         os.path.join(Utils.getparent(apk_path), output_apk_name)])
    if retcode == 0:
        print('zipalign successed')
    return retcode, msg


# apk类型探测，判断是否是游戏apk，如果是则找出该apk使用的哪种游戏引擎
# 游戏引擎的判断首先通过特征文件名判断，如unity3d的libmono.so，neox的res.npk，
# 如果没有再用特征包名判断一次(因为so的名称万一修改过呢，此时使用特征包名判断)，如unity3d的com.unity3d.player
def detectApk(apk_path):
    app_type = ''
    is_game_app = False
    apk = zipfile.ZipFile(apk_path)
    # 先使用特征文件名判断
    u3d_regex = re.compile('libmono.so', re.I)
    flash_regex = re.compile('libCore.so', re.I)
    neox_regex = re.compile('res.npk', re.I)
    for entry in apk.namelist():
        find = u3d_regex.search(entry)
        if find:
            is_game_app = True
            app_type = Constant.UNITY3D
            break
        find = flash_regex.search(entry)
        if find:
            is_game_app = True
            app_type = Constant.FLASH
            break
        find = neox_regex.search(entry)
        if find:
            is_game_app = True
            app_type = Constant.NEOX
            break

    return app_type, is_game_app
    '''下面这种方式对于某些加固后的apk不可行，某些加固后的apk使用dex2jar会失败
    # 如果特征文件名未找到，使用特征包名再做一次查找
    if not is_game_app:
        temp_dir = PathManager.get_temp_dir_path()
        output_jar_path = os.path.join(temp_dir, 'temp.jar')
        apk.extract('classes.dex', temp_dir)
        dex_path = os.path.join(temp_dir, 'classes.dex')
        retcode, msg = star.runcmd2([PathManager.get_dex2jar_path(), dex_path, '-f', '-o', output_jar_path])
        if retcode == 0:
            jar = zipfile.ZipFile(output_jar_path)
            for entry in jar.namelist():
                if 'com.unity3d.player' in entry:
                    is_game_app = True
                    app_type = Constant.UNITY3D
                elif 'org.cocos2dx.lib' in entry:
                    is_game_app = True
                    app_type = Constant.COCOS2DX

                elif '' in entry:
                    is_game_app = True
                    app_type = Constant.NEOX
                # shutil.rmtree(temp_dir)
    '''


# 查看APK的签名信息
def viewsign(f):
    infoFile = os.path.splitext(f)[0] + '_signinfo.txt'
    check_v2sign_tool_path = PathManager.get_checkV2_sign_tool_path()
    code, info = star.runcmd2(['java', '-jar', check_v2sign_tool_path, f])
    if code == 0:
        msg_dic = json.loads(info)
        if msg_dic['isV1OK']:  # 如果使用了v1签名，不管是否使用了v2签名检测v1签名
            code, info = star.runcmd2([Constant.KEYTOOL_FILENAME, '-printcert', '-jarfile', f])
            if msg_dic['isV2']:
                info += u"该apk使用了V1+V2签名，其中V1签名信息如上所示"
            else:
                info += u"该apk仅仅用了V1签名，其签名信息如上所示"
        if msg_dic['isV2'] and not msg_dic['isV1OK']:  # 未使用v1签名，仅仅使用了v2签名
            info += u"该apk仅仅使用了v2签名，未使用v1签名，具体信息如上所示"
    if code == 0:
        star.log(info, infoFile)
        if os.path.exists(infoFile):
            star.run_cmd_asyn(['notepad', infoFile])

    return code, info


# 签名
def sign(f):
    return star.runcmd2([PathManager.get_signtool_path(), f])


# 签名V1+V2
def sign_v1_v2(f):
    print(u"使用v1+v2签名")
    return star.runcmd2([PathManager.get_v2_sign_tool_path(), f])


# 通过命令行输出检查是否成功，最常见的问题就是“忘记签名”
def checkIsInstalledSuccess(msg):
    if msg.find('Success') == -1:
        error = star.find('Failure \[(.*?)\]', msg)
        if error == 'INSTALL_PARSE_FAILED_NO_CERTIFICATES':
            print (u'没签名或者签名不对，请重新签名!\n错误详情：\n')
        elif error == 'INSTALL_FAILED_OLDER_SDK':
            print (u'INSTALL_FAILED_OLDER_SDK 错误是什么鬼？\n')
        print (msg)
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
    if len(adb.get_devices()) == 0:
        print(u"该功能需要连接手机或者模拟器，请确保手机或者模拟器已经启动")
        return 0, None
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
    if ret == 0:
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
    if size is not None:  # 获取分辨率如果失败size将会是None对象，此时不能使用+连接
        star.loga('分辨率：' + size, infoFile)

    if os.path.exists(infoFile):
        star.run_cmd_asyn(['notepad', infoFile])
    return 1, None


# 手机截屏并保存位png图片
# 从配置文件读取scale的值，如果配置文件中未设置scale则将其设置为0.5(默认值)
# 截屏之后图片自动保存至系统剪贴板，可直接粘贴使用
def photo(file_path):
    adb = ADBManager()
    if len(adb.get_devices()) == 0:
        print(u"该功能需要连接手机或者模拟器，请确保手机或者模拟器已经启动")
        return 0, None
    # 此处要注意从配置文件中读取出来的数值属于字符串类型，需要转换为数值类型
    scale = float(Utils.get_value_from_confing('ScaleSize', 'Scale'))
    if not scale:  # 如果配置文件未设置Scale字段
        scale = 0.5
    image_file = os.path.splitext(file_path)[0] + '.png'

    adb.get_screenshot(image_file, scale)
    # 将图片复制到剪贴板需要先将图片数据写到内存中
    image = Image.open(image_file)
    output = StringIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32con.CF_DIB, data)
    win32clipboard.CloseClipboard()
    print(u'图片已经复制到了剪贴板，您可直接粘贴使用')
    return 0, None


# 抽取APK的图标文件，
def extracticon(apk_path):
    apk_dir = os.path.splitext(apk_path)[0]
    retcode, msg = star.runcmd2([PathManager.get_aapt_path(), 'dump', 'badging', apk_path])
    if retcode == 0:
        icons = star.findall("icon.*?'(.+?)'", msg)
        icons = list(set(icons))
        # icons匹配出来的字符串可能不是图片格式，这里过滤删除下
        for i in range(len(icons) - 1, -1, -1):
            if not (icons[i].endswith('.png') or icons[i].endswith('.jpg')
                    or icons[i].endswith('.jpeg') or icons[i].endswith('.bmp')):
                icons.remove(icons[i])

        zfile = zipfile.ZipFile(apk_path, 'r', compression=zipfile.ZIP_DEFLATED)

        for icon in icons:
            icon_name = '_' + os.path.splitext(os.path.basename(icon))[0]
            icon_file = apk_dir + '_temp.png'
            file(icon_file, 'wb').write(zfile.read(icon))
            image = Image.open(icon_file)
            image_size = '_' + str(image.size[0])
            image.close()  # 一定要调用close否则下面的rename会出现异常
            new_icon_file = apk_dir + icon_name + image_size + '.png'
            if not os.path.exists(new_icon_file):
                os.rename(icon_file, new_icon_file)
            else:  # 如果当前目录下已存在提取后重新命名的文件，则删除临时文件而不是重命名
                os.remove(icon_file)
        print(u'不同分辨率的图标已经提取完成，路径位于和apk同级目录下')
    return retcode, msg


# 反编译
def baksmali(f):
    print(u'反编译完成')
    return star.runcmd2([PathManager.get_apktool_path(), 'd', '-f', f])


# 回编译
def smali(f):
    return star.runcmd2([PathManager.get_apktool_path(), 'b', f])


def md2html(f):
    return star.runcmd2([PathManager.get_mdconverter_path(), f])


def md2pdf(f):
    return star.runcmd2([PathManager.get_mdconverter_path(), f, 'pdf'])


def plug(f):
    os.system('pause')
    return 0, None


def check_and_installed_third_part():
    # try:
    #     import win32con
    #     import win32clipboard
    #     from PIL import Image
    # except Exception as e:
    #     # 执行安装命令
    #     os.system("pip install -r requirements.txt")
    #     print traceback.format_exc()
    # 放到最前面，因为发现后面要使用这些引入的module，放在这属于局部引入
    pass


if __name__ == '__main__':
    ret = 0
    msg = None
    check_and_installed_third_part()
    try:
        if DEBUG:
            ret, msg = on_command([__file__, 'installd', os.path.join(Utils.get_desktop_path(), 'nfcard.apk')])
        else:
            ret, msg = on_command(sys.argv)
        if ret != 0 and ret is not None:
            print(msg)
            os.system('pause')
    except Exception as e:
        print(traceback.format_exc())
        os.system('pause')
    if not ret:
        sys.exit(-1)
