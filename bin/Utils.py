#coding:utf-8

import os
import sys
import tempfile
from subprocess import check_output, CalledProcessError
import subprocess

# 返回当前脚本的全路径，末尾不带\
def getthispath():
    path = sys.path[0]
    #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.split(path)[0]

def get_file_ext(path):
    print os.path.splitext(path)
    # return os.path.splitext(path)[1]

# 获取路径的父目录，末尾不带\
def getparent(filepath):
    if not filepath:
        return None
    lsPath = os.path.split(filepath)
    # print(lsPath)
    # print("lsPath[1] = %s" %lsPath[1])
    if lsPath[1]:
        return lsPath[0]
    lsPath = os.path.split(lsPath[0])
    return lsPath[0]