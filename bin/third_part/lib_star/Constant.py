#coding:utf-8
class Constant:
    @staticmethod
    def test():
        pass

Constant.NS_ANDROID_URI = 'http://schemas.android.com/apk/res/android'
Constant.KEYTOOL_FILENAME = 'keytool.exe'
Constant.MANIFEST_FILENAME = 'AndroidManifest.xml'

Constant.dex2jar_FILEPATH = "tools\\dex2jar\\d2j-dex2jar.bat"
Constant.jdgui_FILEPATH = "tools\\jdgui\\jd-gui.exe"

Constant.ERROR = -1
Constant.FAILED = -1
Constant.OK = 0
Constant.SUCCESS = 0

Constant.ERROR_MSG = {
    Constant.OK:"成功",
    Constant.ERROR: "失败",
}