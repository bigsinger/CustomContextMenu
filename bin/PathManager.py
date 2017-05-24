#coding:utf-8

import os
import sys
import Utils
from Constant import Constant

class PathManager:

    @staticmethod
    def get_java_path():
        return "D:\\java\\jre7\\bin"

    @staticmethod
    def get_java_path():
        return "D:\\java\\jre7\\bin"

    @staticmethod
    def get_dex2jar_path():
        return os.path.join(Utils.getthispath(), 'tools\\dex2jar-2.0\\d2j-dex2jar.bat')

    @staticmethod
    def get_jdgui_path():
        return os.path.join(Utils.getthispath(), 'tools\\jdgui\\jd-gui.exe')

    @staticmethod
    def get_axmlprinter_path():
        return os.path.join(Utils.getthispath(), 'tools\\AXMLPrinter.bat')

    @staticmethod
    def get_aapt_path():
        return os.path.join(Utils.getthispath(), 'tools\\aapt.exe')

    @staticmethod
    def get_keytool_path():
        keytool = os.path.join(PathManager.get_java_path(), Constant.KEYTOOL_FILENAME)
        return keytool

    @staticmethod
    def get_apktool_path():
        apktool = os.path.join(Utils.getthispath(), 'tools\\apktool.bat')
        return apktool

    @staticmethod
    def get_signtool_path():
        signtool = os.path.join(Utils.getthispath(), 'tools\\sign\\sign.bat')
        return signtool