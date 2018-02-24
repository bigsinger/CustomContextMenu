# coding: utf-8
# ref: https://github.com/tdoly/apk_parse

import os
from . import star
import struct
from . import zipfile
import logging
import io
from . import androconf
import subprocess
from .ZipManager import *
from .PathManager import *
from .AXMLPrinter import *
from zlib import crc32
from xml.dom import minidom
from .Constant import Constant
from .dvm_permissions import DVM_PERMISSIONS

class ZIP:
    def __init__(self, filename):
        self._filename = filename

    @staticmethod
    def unzip(apk_path, dst_path):
        if not zipfile.is_zipfile(apk_path):
            return False

        if not os.path.exists(dst_path):
            os.mkdir(dst_path, 0o777)

        try:
            zfobj = zipfile.ZipFile(apk_path)
            for name in zfobj.namelist():
                oriname = name
                if os.sep == '\\':
                    name = name.replace('/', os.sep)
                if name.endswith(os.sep):
                    star.createdirs(os.path.join(dst_path, name))
                    pass
                else:
                    filepath = os.path.join(dst_path, name)
                    dir = os.path.dirname(filepath)

                    if not os.path.exists(dir):
                        star.createdirs(dir)

                    file = open(filepath, 'wb')
                    file.write(zfobj.read(oriname))
                    file.close()

            zfobj.close()
        except Exception as e:
            logging.error("解压%s失败，原因：%s", apk_path, e)
            return False
        return True

    #提取文件内容
    @staticmethod
    def extractFileContent(apk_path, filename):
        if not zipfile.is_zipfile(apk_path):
            return None

        try:
            zfobj = zipfile.ZipFile(apk_path)
            fileinfo = zfobj.getinfo(filename)
            if fileinfo.file_size > config.apk_maxsize:
                zfobj.close()
                return None
            content = zfobj.read(filename)
            zfobj.close()
            return content

        except Exception as e:
            logging.error("提取文件%s内容失败，原因：%s", filename, e)
            return None

    #读取APK文件名列表
    @staticmethod
    def getZipNameList(apk_path):
        zipnamelist = []
        if not zipfile.is_zipfile(apk_path):
            return []
        try:
            zfobj = zipfile.ZipFile(apk_path)
            zipnamelist = zfobj.namelist()
            zfobj.close()
        except Exception as e:
            logging.error("获取%s文件列表失败，原因：%s", apk_path, e)
        finally:
            return zipnamelist