# coding:utf-8
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
    Constant.OK: u"成功",
    Constant.ERROR: u"失败",
}

Constant.FLASH = 'flash',  # flash 
Constant.UNITY3D = 'unity3d',  # unity3d引擎游戏
Constant.COCOS2DX = 'cocos2dx',  # cocos2dx引擎游戏
Constant.NEOX = 'neox',  # neox引擎游戏
