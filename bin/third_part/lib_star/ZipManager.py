#coding:utf-8
import os
from . import star
from . import zipfile
import logging

'''
负责ZIP相关的操作，如：解压，打包，添加文件，删除文件等
'''

class ZipManager:
    @staticmethod
    def unpack(apk_path, dst_path):
        try:
            if not zipfile.is_zipfile(apk_path):
                return False

            if not os.path.exists(dst_path):
                star.createdirs(dst_path)

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
        except Exception as e:
            logging.error("[ZipManager.unpack] 解压%s到%s,失败，原因：%s", apk_path, dst_path, e)
            return False
        return True

    # 把目录folderPath压缩为zip（zip文件名为zipFilePath）
    @staticmethod
    def pack(dst_path, apk_path):
        return True

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

    #提取文件内容
    @staticmethod
    def extractFileContent(apk_path, filename):
        if not zipfile.is_zipfile(apk_path):
            return None

        try:
            zfobj = zipfile.ZipFile(apk_path)
            fileinfo = zfobj.getinfo(filename)
            if fileinfo.file_size > 700 * 1024 * 1024: #限制大小为700M
                zfobj.close()
                return None
            content = zfobj.read(filename)
            zfobj.close()
            return content

        except Exception as e:
            logging.error("提取文件%s内容失败，原因：%s", filename, e)
            return None

    #解压某个特定名称的文件, 解压一个dex, 如果dex大小超过700M， 认为是恶意apk, 将忽略
    @staticmethod
    def unzip_file(apk_path, filename, dst_path):
        if not zipfile.is_zipfile(apk_path):
            return None
        if not os.path.exists(dst_path):
            os.mkdir(dst_path, 0o777)
        filepath = ''
        try :
            zfobj = zipfile.ZipFile(apk_path)
            oriname = filename

            if os.sep == '\\':
                filename = filename.replace('/', os.sep)
            if filename.endswith(os.sep):
                star.createdirs(os.path.join(dst_path, filename))
                pass
            else:
                apkname = os.path.splitext(os.path.basename(apk_path))[0]
                filepath = os.path.join(dst_path,apkname+'_'+filename)
                dir = os.path.dirname(filepath)
                if not os.path.exists(dir):
                    star.createdirs(dir)
                fileinfo = zfobj.getinfo(oriname)
                if fileinfo.file_size > 700 * 1024 * 1024:
                    zfobj.close()
                    return None
                content = zfobj.read(oriname)
                zfobj.close()#即使在上面某些发生异常应该也没事，zfobj的析构函数会调用close
                with open(filepath, 'wb') as file:
                    file.write(content)
                return apkname+'_'+filename
        except:
            star.deletefile(filepath)
            return None

    @staticmethod
    def delFileFromZip(tool_path, apk_path, file2del):
        command = '\"%s%sApkUtil.exe\" -del \"%s\" \"%s\"' %(tool_path, os.sep, apk_path, file2del)
        result = star.runExe(command)
        if len(result) > 0:
            logging.error("[delFileFromZip] %s", result)
            return False
        else:
            return True

    @staticmethod
    def addFileToZip(tool_path, apk_path, file_path, file_name):
        command = '\"%s%sApkUtil.exe\" -add \"%s\" \"%s\" \"%s\"' %(tool_path, os.sep, apk_path, file_path, file_name)
        result = star.runExe(command)
        if len(result) > 0:
            logging.error("[addFileToZip] %s", result)
            logging.error("[addFileToZip] 向zip中添加文件错误 FileEntry:%s Path:%s", file_name, file_path)
            return False
        else:
            return True

    @staticmethod
    def addDirToZip(tool_path, apk_path, dir_name):
        command = '\"%s%sApkUtil.exe\" -adddir \"%s\" \"%s\"' %(tool_path, os.sep, apk_path, dir_name)
        result = star.runExe(command)
        if len(result) > 0:
            logging.error("[addDirToZip] 向%s中添加目录%s失败，输出%s", apk_path, dir_name, result)
            return False
        return True


    @staticmethod
    def createZipAndAddFile(zipPath, fileAdded, fileName, compressionFlag=zipfile.ZIP_STORED):
        zf = zipfile.ZipFile(zipPath, mode='w', compression=compressionFlag)
        try:
            zf.write(fileAdded, arcname=fileName)
        except Exception as e:
            logging.error("[createZipAndAddFile] 创建文件%s失败，原因：%s", zipPath, e)
            return False
        finally:
            zf.close()

        return True

    @staticmethod
    def createZip(zipPath, compressionFlag=zipfile.ZIP_STORED):
        try:
            zf = zipfile.ZipFile(zipPath, mode='w', compression=compressionFlag)
            zf.close()
        except Exception as e:
            logging.error("[createZip] 创建压缩文件%s失败，原因：%s", zipPath, e)
            return False

        if not os.path.exists(zipPath):
            logging.error("[createZip] 压缩文件%s不存在", zipPath)
            return False
        return True

if __name__ == '__main__':
    apkPath = 'E:\\client\\android\\wrapper\\bin\\temp\\641C232CE64AEE1A3E268A93428F0C6C_89\\student.apk'
    apkPath1 = 'E:\\client\\android\\wrapper\\bin\\temp\\641C232CE64AEE1A3E268A93428F0C6C_89\\student_tmp.apk'
    unzipPath = 'E:\\client\\android\\wrapper\\bin\\temp\\641C232CE64AEE1A3E268A93428F0C6C_89\\2'
    if not star.movefile(apkPath1, apkPath):
        print('fail')
    ZipManager.unpack(apkPath, unzipPath)
