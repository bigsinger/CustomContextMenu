#coding:utf-8
'''

'''

import os
import sys
import logging
import shutil
import traceback
import zipfile
import tempfile
from Constant import Constant
from PathManager import *
from star.AXMLPrinter import *
from star.ADBManager import ADBManager
from star.APK import APK
from xml.dom import minidom
import star

DEBUG = False

def main(params):
    '''
    :param params: 参数数组 oncommand.py command file [files]
    :return:
    '''
    paramCount = len(params)
    multiFiles = False
    if params is None or paramCount < 3:
        print u'参数不对，需要传至少 3 个参数'
        print params[0]
        print params[1]
        os.system('pause')
        return False
    CMD_STR = params[1]
    filesSelected = params[2]
    if paramCount > 3:
        multiFiles = True
    print str(paramCount) + ' '+ CMD_STR + ' ' + filesSelected
    if CMD_STR=='dex2jar':
        print u'dex2jar'
        dex2jar(filesSelected)
    elif CMD_STR == 'axml2txt':
        print u'axml2txt'
        axml2txt(filesSelected)
    elif CMD_STR == 'viewapk':
        print u'viewapk'
        viewapk(filesSelected)
    elif CMD_STR == 'viewsign':
        print u'viewsign'
        viewsign(filesSelected)
    elif CMD_STR == 'sign':
        print u'sign'
        sign(filesSelected)
    elif CMD_STR == 'installd':
        print u'installd'
        installd(filesSelected)
    elif CMD_STR == 'installr':
        print u'installr'
        installr(filesSelected)
    elif CMD_STR == 'uninstall':
        print u'uninstall'
        uninstall(filesSelected)
    elif CMD_STR == 'viewwrapper':
        print u'viewwrapper'
    elif CMD_STR == 'phone':
        print u'phone'
        viewphone(filesSelected)
    elif CMD_STR == 'photo':
        print u'photo'
        photo(filesSelected)
    elif CMD_STR == 'icon':
        print u'icon'
        extracticon(filesSelected)
    elif CMD_STR == 'zipalign':
        print u'zipalign'
    elif CMD_STR == 'baksmali':
        print u'baksmali'
        baksmali(filesSelected)
    elif CMD_STR == 'smali':
        print u'smali'
        smali(filesSelected)
    elif CMD_STR == 'plug1':
        print u'plug1'
        plug(filesSelected)
    elif CMD_STR == 'plug2':
        print u'plug2'
        plug(filesSelected)
    elif CMD_STR == 'plug3':
        print u'plug3'
        plug(filesSelected)
    elif CMD_STR == 'about':
        print u'右键工具2.0'
        os.system('pause')

    if sys.platform == 'win32':
        # win下命令行参数为gbk编码，转换为UNICODE
        filesSelected = filesSelected.decode('gbk', 'ignore')

def dex2jar(f):
    jarFile = os.path.splitext(f)[0] + '.jar'
    retcode, msg = Utils.runcmd([PathManager.get_dex2jar_path(), f, '-f', '-o', jarFile])
    if retcode==0:
        Utils.run_cmd_asyn([PathManager.get_jdgui_path(), jarFile])
        print 'dex2jar ok'

def axml2txt(f):
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
                Utils.runcmd([PathManager.get_axmlprinter_path(), axmlFile, '>', txtFile])
                break
    else:
        txtFile = f + '.txt'
        Utils.runcmd([PathManager.get_axmlprinter_path(), f, '>', txtFile])
        print 'axml2txt .xml'
    if os.path.exists(txtFile):
        Utils.run_cmd_asyn(['notepad', txtFile])

    print 'axml2txt ok'

def viewapk(f):
    infoFile = os.path.splitext(f)[0] + '_apkinfo.txt'
    retcode, msg = Utils.runcmd([PathManager.get_aapt_path(), 'dump', 'badging', f])
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
        if os.path.exists(infoFile):
            Utils.run_cmd_asyn(['notepad', infoFile])

def viewsign(f):
    infoFile = os.path.splitext(f)[0] + '_signinfo.txt'
    code, info = Utils.runcmd([PathManager.get_keytool_path(), '-printcert', '-jarfile', f])
    if code == 0:
        star.log(info, infoFile)
        if os.path.exists(infoFile):
            Utils.run_cmd_asyn(['notepad', infoFile])

def sign(f):
    Utils.runcmd([PathManager.get_signtool_path(), f])
    print u'签名完成'
    os.system('pause')

def installd(f):
    apk = APK(f)
    package = apk.get_package()
    adb = ADBManager()
    adb.uninstall(package)
    adb.install(f)

def installr(f):
    adb = ADBManager()
    adb.install(f, '-r')

def uninstall(f):
    apk = APK(f)
    package = apk.get_package()
    adb = ADBManager()
    adb.uninstall(package)

def viewphone(f):
    adb = ADBManager()
    retcode, model = adb.shell('getprop ro.product.model')
    retcode, name = adb.shell('getprop ro.product.name')
    retcode, release = adb.shell('getprop ro.build.version.release')
    retcode, sdk = adb.shell('getprop ro.build.version.sdk')
    retcode, cpu = adb.shell('getprop ro.product.cpu.abi')
    retcode, cpu2 = adb.shell('getprop ro.product.cpu.abi2')
    retcode, serialno = adb.shell('getprop ro.serialno')
    retcode, imei = adb.shell('getprop gsm.sim.imei')
    retcode, androidid = adb.shell('getprop net.hostname')
    retcode, description = adb.shell('getprop ro.build.description')

    retcode, mac = adb.shell('cat /sys/class/net/wlan0/address')
    retcode, size = adb.shell('wm size')
    if retcode==0:
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
        Utils.run_cmd_asyn(['notepad', infoFile])

def photo(f):
    imageFile = os.path.splitext(f)[0] + '.png'
    adb = ADBManager()
    adb.get_screenshot(imageFile)

def extracticon(f):
    dir = os.path.splitext(f)[0]
    retcode, msg = Utils.runcmd([PathManager.get_aapt_path(), 'dump', 'badging', f])
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

def baksmali(f):
    Utils.runcmd([PathManager.get_apktool_path(), 'd', '-f', f])
    print u'反编译完成'
    os.system('pause')


def smali(f):
    Utils.runcmd([PathManager.get_apktool_path(), 'b', f])
    print u'回编译完成'
    os.system('pause')

def plug(f):
    print u'等你来写。。。'
    os.system('pause')

def checkThirdParty():
    # try:
    #     from compiler.ast import flatten
    #     import base64
    #     import array
    # except Exception as e:
    #     print traceback.format_exc()
    pass

if __name__=='__main__':
    ret = False
    checkThirdParty()
    try:
        if DEBUG:
            ret = main([__file__, 'sign', 'C:/Users/hzzhuxingxing/Desktop/test.apk'])

        else:
            ret = main(sys.argv)
    except Exception as e:
        print e.message
        ret = False
    if not ret:
        sys.exit(-1)
