#coding:utf-8
import os


'''
负责路径相关的操作
'''

class PathManager:

    @staticmethod
    def get_env(name, joinwhat = None):
        ret = None
        try:
            ret = os.environ[name]
        except:
            pass
        else:
            if joinwhat is not None:
                ret = os.path.join(ret, joinwhat)
        return ret

    @staticmethod
    def get_java_path(subpath = None):
        return PathManager.get_env('JAVA_HOME', 'bin')

    @staticmethod
    def get_android_sdk_path():
        return PathManager.get_env('ANDROID_SDK_ROOT')

    @staticmethod
    def get_ndk_path():
        return PathManager.get_env('NDK_ROOT')

if __name__ == '__main__':
    print(PathManager.get_android_sdk_path())
    print(PathManager.get_ndk_path())
    print(PathManager.get_java_path())