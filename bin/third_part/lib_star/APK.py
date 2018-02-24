# coding: utf-8
# ref: https://github.com/tdoly/apk_parse

import os
import re
import star
import struct
import zipfile
import logging
import StringIO
import androconf
import subprocess
from ZipManager import *
from PathManager import *
from AXMLPrinter import *
from zlib import crc32
from xml.dom import minidom
from Constant import Constant
from dvm_permissions import DVM_PERMISSIONS


class APK:
    def __init__(self, filename):
        self._filename = filename
        self._axml = {}
        self._xml = {}
        self._package = None
        self._versionName = None
        self._versionCode = None
        self._permissions = []
        self._isvalidapk = False

        self._certtext = None
        self._certmd5 = None
        self._filemd5 = None
        self._filesize = None

        self.files = {}
        self.files_crc32 = {}

        self._data = star.read(filename)
        self._filesize = len(self._data)
        # self._filemd5 = star.md5(self._data)
        self._zip = zipfile.ZipFile(StringIO.StringIO(self._data), "r")
        for i in self._zip.namelist():
            if i == "AndroidManifest.xml":
                self._axml = AXMLPrinter(self._zip.read(i))
                try:
                    self._xml = minidom.parseString(self._axml.get_buff())
                except:
                    self._xml = None

                if self._xml != None:
                    self._package = self._xml.documentElement.getAttribute("package")
                    self._versionName = self._xml.documentElement.getAttributeNS(Constant.NS_ANDROID_URI, "versionName")
                    self._versionCode = self._xml.documentElement.getAttributeNS(Constant.NS_ANDROID_URI, "versionCode")
                    for item in self._xml.getElementsByTagName('uses-permission'):
                        self._permissions.append(str(item.getAttributeNS(Constant.NS_ANDROID_URI, "name")))

                    self.valid_apk = True
                break

                # re_cert = re.compile(r'meta-inf(/|\\).*\.(rsa|dsa)')
                # if re_cert.match(i.lower()):
                #     self.parse_cert(i)

        self.get_files_types()

    # def parse_cert(self, cert_fname):
    #     """
    #         parse the cert text and md5
    #     :param cert_fname:
    #     """
    #     input_bio = M2Crypto.BIO.MemoryBuffer(self.zip.read(cert_fname))
    #     p7 = M2Crypto.SMIME.PKCS7(M2Crypto.m2.pkcs7_read_bio_der(input_bio._ptr()), 1)
    #     sk3 = p7.get0_signers(M2Crypto.X509.X509_Stack())
    #     cert = sk3.pop()
    #     self.cert_text = cert.as_text()
    #     self.cert_md5 = star.md5(cert.as_der())
    #     pass

    '''
    调用keytool输出信息：
    签名者 #1:

    签名:

    所有者: CN=Android Debug, O=Android, C=US
    发布者: CN=Android Debug, O=Android, C=US
    序列号: 4fea8ec1
    有效期开始日期: Wed Jun 27 12:40:33 CST 2012, 截止日期: Fri Jun 20 12:40:33 CST 2042
    证书指纹:
         MD5: 9E:0F:03:05:37:03:8B:BF:14:93:40:2A:80:F4:72:39
         SHA1: 03:49:5B:57:29:E6:12:1B:EE:74:A5:7A:54:B2:F9:C7:ED:6B:CF:31
         SHA256: 52:FA:87:91:A4:42:0E:50:6B:10:35:AE:60:E5:F7:D4:58:70:99:71:F9:20:5D:F7:5D:16:88:A6:B6:42:A3:11
         签名算法名称: SHA1withRSA
         版本: 3
    '''

    def get_sign_info(self):
        keytool = os.path.join(PathManager.get_java_path(), Constant.KEYTOOL_FILENAME)
        code, result = star.runcmd([keytool, '-printcert', '-jarfile', self._filename])
        result = result.decode("gb2312", "ignore")
        if code == 0:
            pass
        return result

    def is_valid_APK(self):
        return self.valid_apk

    def get_filename(self):
        return self.filename

    def get_package(self):
        return self._package

    def get_version_code(self):
        return self._versionCode

    def get_version_name(self):
        return self._versionName

    def get_files(self):
        return self._zip.namelist()

    def get_files_types(self):
        """
            Return the files inside the APK with their associated types (by using python-magic)

            :rtype: a dictionnary
        """
        try:
            import magic
        except ImportError:
            # no lib magic !
            for i in self.get_files():
                buffer = self._zip.read(i)
                self.files_crc32[i] = crc32(buffer)
                self.files[i] = "Unknown"
            return self.files

        if self.files != {}:
            return self.files

        builtin_magic = 0
        try:
            getattr(magic, "MagicException")
        except AttributeError:
            builtin_magic = 1

        if builtin_magic:
            ms = magic.open(magic.MAGIC_NONE)
            ms.load()

            for i in self.get_files():
                buffer = self.zip.read(i)
                self.files[i] = ms.buffer(buffer)
                self.files[i] = self._patch_magic(buffer, self.files[i])
                self.files_crc32[i] = crc32(buffer)
        else:
            m = magic.Magic(magic_file=self.magic_file)
            for i in self.get_files():
                buffer = self.zip.read(i)
                self.files[i] = m.from_buffer(buffer)
                self.files[i] = self._patch_magic(buffer, self.files[i])
                self.files_crc32[i] = crc32(buffer)

        return self.files

    def _patch_magic(self, buffer, orig):
        if ("Zip" in orig) or ("DBase" in orig):
            val = androconf.is_android_raw(buffer)
            if val == "APK":
                if androconf.is_valid_android_raw(buffer):
                    return "Android application package file"
            elif val == "AXML":
                return "Android's binary XML"

        return orig

    def get_files_crc32(self):
        if self.files_crc32 == {}:
            self.get_files_types()

        return self.files_crc32

    def get_files_information(self):
        """
            Return the files inside the APK with their associated types and crc32

            :rtype: string, string, int
        """
        if self.files == {}:
            self.get_files_types()

        for i in self.get_files():
            try:
                yield i, self.files[i], self.files_crc32[i]
            except KeyError:
                yield i, "", ""

    def get_raw(self):
        """
            Return raw bytes of the APK

            :rtype: string
        """
        return self._data

    def get_file(self, filename):
        """
            Return the raw data of the specified filename

            :rtype: string
        """
        try:
            return self._zip.read(filename)
        except KeyError:
            return ""

    def get_dex(self):
        """
            Return the raw data of the classes dex file

            :rtype: string
        """
        return self.get_file("classes.dex")

    def get_elements(self, tag_name, attribute):
        """
            Return elements in xml files which match with the tag name and the specific attribute

            :param tag_name: a string which specify the tag name
            :param attribute: a string which specify the attribute
        """
        l = []
        for item in self._xml.getElementsByTagName(tag_name):
            value = item.getAttributeNS(Constant.NS_ANDROID_URI, attribute)
            value = self.format_value(value)

            l.append(str(value))
        return l

    def format_value(self, value):
        if len(value) > 0:
            if value[0] == ".":
                value = self._package + value
            else:
                v_dot = value.find(".")
                if v_dot == 0:
                    value = self._package + "." + value
                elif v_dot == -1:
                    value = self._package + "." + value
        return value

    def get_element(self, tag_name, attribute):
        """
            Return element in xml files which match with the tag name and the specific attribute

            :param tag_name: specify the tag name
            :type tag_name: string
            :param attribute: specify the attribute
            :type attribute: string

            :rtype: string
        """
        for item in self._xml.getElementsByTagName(tag_name):
            value = item.getAttributeNS(Constant.NS_ANDROID_URI, attribute)

            if len(value) > 0:
                return value
        return None

    # 获取启动activity，例如：com.example.crash.MainActivity
    def get_main_activity(self):
        """
            Return the name of the main activity

            :rtype: string
        """
        x = set()
        y = set()

        for item in self._xml.getElementsByTagName("activity"):
            for sitem in item.getElementsByTagName("action"):
                val = sitem.getAttributeNS(Constant.NS_ANDROID_URI, "name")
                if val == "android.intent.action.MAIN":
                    x.add(item.getAttributeNS(Constant.NS_ANDROID_URI, "name"))

            for sitem in item.getElementsByTagName("category"):
                val = sitem.getAttributeNS(Constant.NS_ANDROID_URI, "name")
                if val == "android.intent.category.LAUNCHER":
                    y.add(item.getAttributeNS(Constant.NS_ANDROID_URI, "name"))

        z = x.intersection(y)
        if len(z) > 0:
            return self.format_value(z.pop())
        return None

    def get_activities(self):
        """
            Return the android:name attribute of all activities

            :rtype: a list of string
        """
        return self.get_elements("activity", "name")

    def get_services(self):
        """
            Return the android:name attribute of all services

            :rtype: a list of string
        """
        return self.get_elements("service", "name")

    def get_receivers(self):
        """
            Return the android:name attribute of all receivers

            :rtype: a list of string
        """
        return self.get_elements("receiver", "name")

    def get_providers(self):
        """
            Return the android:name attribute of all providers

            :rtype: a list of string
        """
        return self.get_elements("provider", "name")

    def get_intent_filters(self, category, name):
        d = {}

        d["action"] = []
        d["category"] = []

        for item in self._xml.getElementsByTagName(category):
            if self.format_value(item.getAttributeNS(Constant.NS_ANDROID_URI, "name")) == name:
                for sitem in item.getElementsByTagName("intent-filter"):
                    for ssitem in sitem.getElementsByTagName("action"):
                        if ssitem.getAttributeNS(Constant.NS_ANDROID_URI, "name") not in d["action"]:
                            d["action"].append(ssitem.getAttributeNS(Constant.NS_ANDROID_URI, "name"))
                    for ssitem in sitem.getElementsByTagName("category"):
                        if ssitem.getAttributeNS(Constant.NS_ANDROID_URI, "name") not in d["category"]:
                            d["category"].append(ssitem.getAttributeNS(Constant.NS_ANDROID_URI, "name"))

        if not d["action"]:
            del d["action"]

        if not d["category"]:
            del d["category"]

        return d

    def get_permissions(self):
        """
            Return permissions

            :rtype: list of string
        """
        return self.permissions

    def get_details_permissions(self):
        """
            Return permissions with details

            :rtype: list of string
        """
        l = {}

        for i in self._permissions:
            perm = i
            pos = i.rfind(".")

            if pos != -1:
                perm = i[pos + 1:]

            try:
                l[i] = DVM_PERMISSIONS["MANIFEST_PERMISSION"][perm]
            except KeyError:
                l[i] = ["normal", "Unknown permission from android reference",
                        "Unknown permission from android reference"]

        return l

    def get_max_sdk_version(self):
        """
            Return the android:maxSdkVersion attribute

            :rtype: string
        """
        return self.get_element("uses-sdk", "maxSdkVersion")

    def get_min_sdk_version(self):
        """
            Return the android:minSdkVersion attribute

            :rtype: string
        """
        return self.get_element("uses-sdk", "minSdkVersion")

    def get_target_sdk_version(self):
        """
            Return the android:targetSdkVersion attribute

            :rtype: string
        """
        return self.get_element("uses-sdk", "targetSdkVersion")

    def get_libraries(self):
        """
            Return the android:name attributes for libraries

            :rtype: list
        """
        return self.get_elements("uses-library", "name")

    # 参数需要：META-INF/NETEASE.RSA，可以先调用get_signature_name获取。
    # 最后调用show_Certificate来打印信息
    def get_certificate(self, filename):
        """
            Return a certificate object by giving the name in the apk file
        """
        import chilkat

        cert = chilkat.CkCert()
        f = self.get_file(filename)
        data = chilkat.CkByteData()
        data.append2(f, len(f))
        success = cert.LoadFromBinary(data)
        return success, cert

    def new_zip(self, filename, deleted_files=None, new_files={}):
        """
            Create a new zip file

            :param filename: the output filename of the zip
            :param deleted_files: a regex pattern to remove specific file
            :param new_files: a dictionnary of new files

            :type filename: string
            :type deleted_files: None or a string
            :type new_files: a dictionnary (key:filename, value:content of the file)
        """
        if self.zipmodule == 2:
            from androguard.patch import zipfile

            zout = zipfile.ZipFile(filename, 'w')
        else:
            zout = zipfile.ZipFile(filename, 'w')

        for item in self.zip.infolist():
            if deleted_files != None:
                if re.match(deleted_files, item.filename) == None:
                    if item.filename in new_files:
                        zout.writestr(item, new_files[item.filename])
                    else:
                        buffer = self.zip.read(item.filename)
                        zout.writestr(item, buffer)
        zout.close()

    def get_android_manifest_axml(self):
        """
            Return the :class:`AXMLPrinter` object which corresponds to the AndroidManifest.xml file

            :rtype: :class:`AXMLPrinter`
        """
        try:
            return self.axml["AndroidManifest.xml"]
        except KeyError:
            return None

    def get_android_manifest_xml(self):
        """
            Return the xml object which corresponds to the AndroidManifest.xml file

            :rtype: object
        """
        try:
            return self._xml["AndroidManifest.xml"]
        except KeyError:
            return None

    def get_android_resources(self):
        """
            Return the :class:`ARSCParser` object which corresponds to the resources.arsc file

            :rtype: :class:`ARSCParser`
        """
        try:
            return self.arsc["resources.arsc"]
        except KeyError:
            try:
                self.arsc["resources.arsc"] = ARSCParser(self.zip.read("resources.arsc"))
                return self.arsc["resources.arsc"]
            except KeyError:
                return None

    # 输出类似：META-INF/NETEASE.RSA
    def get_signature_name(self):
        signature_expr = re.compile("^(META-INF/)(.*)(\.RSA|\.DSA)$")
        for i in self.get_files():
            if signature_expr.search(i):
                return i
        return None

    def get_signature(self):
        signature_expr = re.compile("^(META-INF/)(.*)(\.RSA|\.DSA)$")
        for i in self.get_files():
            if signature_expr.search(i):
                return self.get_file(i)
        return None

    def show(self):
        self.get_files_types()

        print("FILES: ")
        for i in self.get_files():
            try:
                print("\t", i, self.files[i], "%x" % self.files_crc32[i])
            except KeyError:
                print("\t", i, "%x" % self.files_crc32[i])

        print("PERMISSIONS: ")
        details_permissions = self.get_details_permissions()
        for i in details_permissions:
            print("\t", i, details_permissions[i])
        print("MAIN ACTIVITY: ", self.get_main_activity())

        print("ACTIVITIES: ")
        activities = self.get_activities()
        for i in activities:
            filters = self.get_intent_filters("activity", i)
            print("\t", i, filters or "")

        print("SERVICES: ")
        services = self.get_services()
        for i in services:
            filters = self.get_intent_filters("service", i)
            print("\t", i, filters or "")

        print("RECEIVERS: ")
        receivers = self.get_receivers()
        for i in receivers:
            filters = self.get_intent_filters("receiver", i)
            print("\t", i, filters or "")

        print("PROVIDERS: ", self.get_providers())

    def parse_icon(self, icon_path=None):
        """
        parse icon.
        :param icon_path: icon storage path
        """
        if not icon_path:
            icon_path = os.path.dirname(os.path.abspath(__file__))

        pkg_name_path = os.path.join(icon_path, self.package)
        if not os.path.exists(pkg_name_path):
            os.mkdir(pkg_name_path)

        aapt_line = "aapt dump badging %s | grep 'application-icon' | awk -F ':' '{print $2}'" % self.get_filename()
        parse_icon_rt = os.popen(aapt_line).read()
        icon_paths = [icon.replace("'", '') for icon in parse_icon_rt.split('\n') if icon]

        zfile = zipfile.ZipFile(StringIO.StringIO(self.__raw), mode='r')
        for icon in icon_paths:
            icon_name = icon.replace('/', '_')
            data = zfile.read(icon)
            with open(os.path.join(pkg_name_path, icon_name), 'w+b') as icon_file:
                icon_file.write(data)
        print("APK ICON in: %s" % pkg_name_path)

    def show_Certificate(self, cert):
        print("Issuer: C=%s, CN=%s, DN=%s, E=%s, L=%s, O=%s, OU=%s, S=%s" % (
            cert.issuerC(), cert.issuerCN(), cert.issuerDN(), cert.issuerE(), cert.issuerL(), cert.issuerO(),
            cert.issuerOU(),
            cert.issuerS()))
        print("Subject: C=%s, CN=%s, DN=%s, E=%s, L=%s, O=%s, OU=%s, S=%s" % (
            cert.subjectC(), cert.subjectCN(), cert.subjectDN(), cert.subjectE(), cert.subjectL(), cert.subjectO(),
            cert.subjectOU(), cert.subjectS()))
        print(cert.sha1Thumbprint())

    def get_arsc_info(arscobj):
        buff = ""
        for package in arscobj.get_packages_names():
            buff += package + ":\n"
            for locale in arscobj.get_locales(package):
                buff += "\t" + repr(locale) + ":\n"
                for ttype in arscobj.get_types(package, locale):
                    buff += "\t\t" + ttype + ":\n"
                    try:
                        tmp_buff = getattr(arscobj, "get_" + ttype + "_resources")(package, locale).decode("utf-8",
                                                                                                           'replace').split(
                            "\n")
                        for i in tmp_buff:
                            buff += "\t\t\t" + i + "\n"
                    except AttributeError:
                        pass
        return buff

    @staticmethod
    def isValidApk(apkPath):
        try:
            if not os.path.exists(apkPath):
                return False
            if not str(apkPath).lower().endswith(".apk"):
                return False

            contentManifest = ZipManager.extractFileContent(apkPath, "AndroidManifest.xml")
            contentDex = ZipManager.extractFileContent(apkPath, "classes.dex")
            if not contentDex or not contentManifest:
                return False
            if len(contentDex) <= 112 or len(contentManifest) <= 8:
                return False

            if APK.isValidDex(contentDex[0:4]) and APK.isValidManifest(contentManifest[0:4]):
                return True
        except Exception as e:
            logging.error(u"[isValidApk] 检测apk是否有效失败，原因：%s", e)
        return False

    @staticmethod
    def isWrapperAlready(apkPath):
        try:
            zipnamelist = ZipManager.getZipNameList(apkPath)
            if "assets/libsecexe.so" in zipnamelist or "assets/data.db" in zipnamelist:
                return True
        except Exception as e:
            logging.error(u"[isWrapperAlready] 检测apk是否加壳失败，原因:%s", e)
        return False

    @staticmethod
    def isValidManifest(magic):
        manifestMagic = struct.unpack('<L', magic)[0]
        # print hex(manifestMagic)
        if hex(manifestMagic) != "0x80003":
            return False
        return True

    @staticmethod
    def isValidDex(magic):
        if magic != "dex\n":
            return False
        return True
