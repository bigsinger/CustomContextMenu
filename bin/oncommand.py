import os
import sys
import traceback


DEBUG = False


def oncommand(cmdTag, fileName, isMultiFile):
    print('cmd name: ' + cmdTag + '\nfile: ' + fileName + '\nisMultiFiles: ' + str(isMultiFile))
    return True


def main(params):
    if len(params) < 3:
        print('invalid params')
        return False
    return oncommand(params[1], params[2], True if len(params) >= 4 else False)


if __name__ == '__main__':
    ret = False
    try:
        if DEBUG:
            ret = main([__file__, '', ''])  # 这里在调试状态下可以随意填参数，方便排查问题
        else:
            ret = main(sys.argv)
        if ret is False:
            print("failed")
    except:
        print(traceback.format_exc())
        os.system('pause')