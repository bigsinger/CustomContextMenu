#coding:utf-8
import zipfile
import os

import logging

import Utils

#解压apk中所有的文件到某个目录
@staticmethod
def unzip_apk_file_to_dest(src_file,dest_file):
    try:
        if not zipfile.is_zipfile(src_file):
            return False

        if not os.path.exists(dest_file):
            Utils.create_dirs(dest_file)

        zfobj = zipfile.ZipFile(src_file)
        for name in zfobj.namelist():
            oriname = name
            if os.sep == '\\':
                name = name.replace('/', os.sep)
            if name.endswith(os.sep):
                Utils.create_dirs(os.path.join(dest_file, name))
                pass
            else:
                filepath = os.path.join(dest_file, name)
                dir = os.path.dirname(filepath)

                if not os.path.exists(dir):
                    Utils.create_dirs(dir)

                file = open(filepath, 'wb')
                file.write(zfobj.read(oriname))
                file.flush()
                file.close()
    except Exception as e:
        logging.error("[ZipManager.unpack] 解压%s到%s,失败，原因：%s", src_file, dest_file, e)
        return False
    return True

#解压apk中某种类型的文件到某个目录，如dex文件

def unzip_dexFile_to_dest(apk_path,dest_path):
    if not zipfile.is_zipfile(apk_path):
        return None
    if not os.path.exists(dest_path):
        os.mkdir(dest_path, 0o777)
    try :
        zipFile = zipfile.ZipFile(apk_path)
        for file in zipFile.namelist():
            if file.endswith('.dex'):
                zipFile.extract(file, dest_path)
        zipFile.close()

    except:
        #Utils.delete_file(filepath)
        return None

if __name__=='__main__':
    apk_path='C:\\Users\hzhuqi\Desktop\python\input.apk'
    filename='.dex'
    dest_path='C:\\Users\hzhuqi\Desktop\python\input'
    unzip_dexFile_to_dest(apk_path,dest_path)