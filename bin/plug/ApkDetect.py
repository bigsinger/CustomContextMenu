# coding: utf-8

import os, re, platform
import zipfile
import sys
from zipmgr import zipmgr


class ApkDetect:
    def __init__(self, dit):
        self.apk_path = dit['apkPath']  # 下载后的APK地址   apkpath = unicode(apk_path , "utf-8")  #对路径进行utf-8编码
        self.aapt_path = dit['aaptPath']
        self.xmltree = ''  # 通过aapt获取的manifest.xml
        self.wrapperSdk = r'Failed'
        self.lastError = ''
        self.bugrptId = ''
        self.appdit = {'wrapperSdk': '', 'lastError': '', 'bugrptID': ''}
        self.zipnamelist = []
        self.apkInfo = ''
        self.iconName = ''
        self.rootpath = ''
        self.is_netease_protect = False
        self.netease_protect_ver = 0
        # 其中APKProtect加固是没有不判断application的
        self.applicationName = [
            r'com.secneo.apkwrapper|com.secneo.guard.ApplicationWrapper|com.secshell.secData.ApplicationWrapper',
            r'com.stub.StubApp',
            r'com.payegis.ProxyApplication', r'com.nqshield.NqApplication', r'com.tencent.StubShell.TxAppEntry',
            r'com.ijiami.residconfusion.ConfusionApplication|com.shell.SuperApplication|s.h.e.l.l.S',
            r'com.edog.AppWrapper|com.chaosvmp.AppWrapper',
            r'com.ali.mobisecenhance.StubApplication', r'com.baidu.protect.StubApplication',
            r'com.netease.nis.wrapper.MyApplication']
        self.soName = [r'libDexHelper\S*.so|libsecexe\S*.so|libSecShell\S*.so', r'libjiagu\S*.so|libprotectClass\S*.so',
                       r'libegis\S*.so|libegisboot\S*.so|libegismain\S*.so|libNSaferOnly\S*.so', r'libnqshield\S*.so',
                       r'libtxRes\S*.so|libshell\S*.so', r'ijiami\S*.dat|ijiami.ajm', r'lib\wdog.so',
                       r'libmobisec\w*.so|libaliutils\S*.so',
                       r'libbaiduprotect\S*.so', 'libnesec.so|data.db|clazz.jar', r'libAPKProtect\S*.so']
        self.protectflag_dict = {1: u"梆梆加固", 2: u"360加固", 3: u"通付盾加固",
                                 4: u"网秦加固", 5: u"腾讯加固", 6: u"爱加密加固",
                                 7: u"娜迦加固", 8: u"阿里加固", 9: u"百度加固", 10: u"网易易盾加密",
                                 11: u"APKProtect加固", 0: u"NO WRAPPER"}
        self.appName_regex = [re.compile(self.applicationName[0], re.I), re.compile(self.applicationName[1], re.I),
                              re.compile(self.applicationName[2], re.I), re.compile(self.applicationName[3], re.I),
                              re.compile(self.applicationName[4], re.I), re.compile(self.applicationName[5], re.I),
                              re.compile(self.applicationName[6], re.I), re.compile(self.applicationName[7], re.I),
                              re.compile(self.applicationName[8], re.I), re.compile(self.applicationName[9], re.I)]
        self.soName_regex = [re.compile(self.soName[0], re.I), re.compile(self.soName[1], re.I),
                             re.compile(self.soName[2], re.I),
                             re.compile(self.soName[3], re.I), re.compile(self.soName[4], re.I),
                             re.compile(self.soName[5], re.I),
                             re.compile(self.soName[6], re.I), re.compile(self.soName[7], re.I),
                             re.compile(self.soName[8], re.I),
                             re.compile(self.soName[9], re.I), re.compile(self.soName[10], re.I)]

        # self.bugrptID_regex = re.compile("A: android:name(0x01010003)="BUGRPT_APPID" (Raw: "BUGRPT_APPID")
        # A: android:value(0x01010024)="A007600419" (Raw: "A007600419")")

    # 读取APK文件名列表
    def getZipNameList(self, apk_path):
        self.lastError = ''
        if not os.path.isfile(apk_path):
            self.lastError = u'apk文件不存在'
            return False
        if not zipfile.is_zipfile(apk_path):
            self.lastError = u'非法的apk文件'
            return False
        try:
            zfobj = zipfile.ZipFile(apk_path)
            self.zipnamelist = zfobj.namelist()
            zfobj.close()
        except Exception as e:
            # print "%s" % e
            self.lastError = u'获取apk中文件列表异常'
            return False
        return True

    # 通过aapt获取的manifest.xml
    def getXmlInfo(self):
        xml_cmd = ''
        self.lastError = ''

        if 'Windows' in platform.system():
            xml_cmd = "%s d xmltree \"%s\" AndroidManifest.xml " % (self.aapt_path, self.apk_path)
            # xml_cmd = "%s%saapt.exe d xmltree \"%s\" AndroidManifest.xml "%(self.aapt_path,os.sep, self.apk_path)

        if 'Linux' in platform.system():
            xml_cmd = "%s%saapt d xmltree %s AndroidManifest.xml " % (self.aapt_path, os.sep, self.apk_path)

        try:
            strxml = os.popen(xml_cmd)
            self.xmltree = strxml.read()
        except Exception as e:
            # print "aapt Mainfestxml error"
            self.lastError = 'aapt get AndroidManifest.xml error'
            return False
        return True

    # 从xml中检测加壳信息
    def checkManifest(self):
        for key in range(len(self.applicationName)):
            result = self.appName_regex[key].search(self.xmltree)
            if result:
                return key + 1
            else:
                continue
        return 0

    # 通过aapt获取apk的信息
    def getApkInfo(self):
        apkinfo_cmd = ''
        aaptlines = []
        if 'Windows' in platform.system():
            apkinfo_cmd = "%s%saapt.exe  dump badging \"%s\" " % (self.aapt_path, os.sep, self.apk_path)

        if 'Linux' in platform.system():
            apkinfo_cmd = "%s%saapt  dump badging \"%s\" " % (self.aapt_path, os.sep, self.apk_path)

        try:
            linestr = os.popen(apkinfo_cmd)
            self.apkInfo = linestr.readlines()
        except Exception as e:
            return False

        for aaptline in self.apkInfo:
            # 从package中获取icon信息
            # print aaptline
            self.iconName = ''
            if aaptline.find('application: label=') > -1:
                pattern = r'icon=\'(\S*)\''
                m = re.search(pattern, aaptline)
                if m:
                    self.iconName = m.group(1)
                    # print self.iconName
                    break

        if self.iconName == '':
            return False
        return True

    def saveIcon(self):
        if not os.path.exists(self.apk_path):
            print(u'apk 路径不存在')
            return False
        result = self.getApkInfo()
        if not result:
            print(u'获取apk图标路径失败')
            return False
        self.rootpath, file = os.path.split(self.apk_path)

        result = zipmgr.unzip_allIocn_to_dir(self.apk_path, self.iconName, self.rootpath)
        if not result:
            print(u'解压apk图标失败')
            return False

        # icon_path = os.path.join(self.rootpath, filename)
        # print icon_path
        print(u'提取图标完成')
        return True

    # 获取APK的加壳SDK信息
    def getWrapperSdk(self):
        self.lastError = ''
        index = self.checkManifest()
        if index != 0:
            self.wrapperSdk = self.protectflag_dict[index]
            if index == 10:  # 如果是网易加固壳，则获取出加固的版本号
                self.is_netease_protect = True
            # print self.apk_path + ": Manifest: " + self.wrapperSdk
            # print "[WrapperSdk] ",self.wrapperSdk
            return True

        try:
            find = False
            for fileName in self.zipnamelist:
                if not find:
                    for key in range(len(self.soName)):
                        result = self.soName_regex[key].search(fileName)
                        print(result)
                        if result:
                            if key == 9:  # 如果是网易加固壳，则获取出加固的版本号
                                self.is_netease_protect = True
                            self.wrapperSdk = self.protectflag_dict[key + 1]
                            find = True
                            break
                else:
                    break
            if not find:
                self.wrapperSdk = self.protectflag_dict[0]
            # print self.apk_path + ": So: " + self.wrapperSdk
            # print "[WrapperSdk] ",self.wrapperSdk
            return True
        except Exception as e:
            # print "parser wrap sdk error: "
            # logging.error(e)
            self.lastError = 'parser wrap sdk error'
            return False

    def getBurptID(self):
        try:
            pattern = r'Raw: "BUGRPT_APPID"\)\s+A: android:value\S+ \(Raw: "(\S*)"'
            m = re.search(pattern, self.xmltree)
            if m:
                self.bugrptId = 'BUGRPT_APPID:' + str(m.group(1))
                return True
        except Exception as e:
            self.bugrptId = ''
        return False

    # 该函数最后调用，更新全局字典类型
    def getAppDit(self):
        self.appdit['lastError'] = self.lastError
        self.appdit['wrapperSdk'] = self.wrapperSdk
        self.appdit['bugrptID'] = self.bugrptId

    # 主函数，外部调用该函数
    def apkDetect(self):
        if not self.getXmlInfo():
            return

        if not self.getZipNameList(self.apk_path):
            return
        self.getWrapperSdk()
        self.getBurptID()

    def result(self):
        self.apkDetect()
        self.getAppDit()
        return self.appdit


if __name__ == "__main__":
    # 初始化地址
    if len(sys.argv) != 4:
        print(u"输入的参数不正常")
    else:
        dit = {'apkPath': '', 'aaptPath': ''}
        dit['apkPath'] = str(sys.argv[1], "gbk")
        dit['aaptPath'] = str(sys.argv[2], "gbk")
        flag = str(sys.argv[3], "gbk")

        ad = ApkDetect(dit)
        if flag == '1':  # 表示获取图标
            ad.saveIcon()
        else:  # 查壳
            dit_result = ad.result()

            if len(dit_result) != 3:
                print(u"解析加壳sdk失败")
            else:
                if dit_result['wrapperSdk'] == 'Failed':
                    print(dit_result['lastError'])
                else:
                    print(dit_result['wrapperSdk'])
                    if dit_result['bugrptID'] != '':
                        print(dit_result['bugrptID'])

                # gameDetect = GameApkDetect(dit['apkPath'])
                # dits = gameDetect.getResult()
                #
                # if dits['isu3d']:
                #     print u' U3d脚本已经加密' if dits['issafe'] else u' U3d脚本未加密'
                # else:
                print('')
