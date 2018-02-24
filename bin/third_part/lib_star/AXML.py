#coding:utf-8
import os
from . import star
from .AXMLPrinter import *

class AXML:
    """
    把一个axml格式的文件转换为一个文本文件的xml，如果不设置xmlfile，则保存为同目录下的后缀为.txt的同名文件
    """
    @staticmethod
    def convert2xml(axmlfile, xmlfile = None):
        if os.path.isfile(axmlfile) is False:
            print("not found: " + axmlfile)
            return
        if xmlfile is None:
            (filename, fileext) = os.path.splitext(axmlfile)
            xmlfile = filename + ".txt"
        axml = AXMLPrinter(star.read(axmlfile))
        star.write(xmlfile, axml.get_xml())
