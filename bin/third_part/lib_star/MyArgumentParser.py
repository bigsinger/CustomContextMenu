# coding: utf-8

import argparse


'''
argparse.ArgumentParser在解析参数失败时不是抛出异常，而是直接错误退出。
这里重载掉error函数，抛出异常，使得外层可以捕获该异常并输出参数帮助。

from star.MyArgumentParser import MyArgumentParser
'''

class ArgumentParserError(Exception): pass


class MyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)
