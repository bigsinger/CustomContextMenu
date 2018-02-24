#coding:utf-8
import os
import re
import logging
import hashlib
from . import zipfile
from pyasn1.codec.der import decoder, encoder
from pyasn1_modules import rfc2315
from .star.ZipManager import *


'''
负责签名相关的操作
需要安装pyasn1_modules，
https://pypi.python.org/pypi/pyasn1-modules下载Python对应版本的egg文件，
解压缩后复制文件夹到Python的lib目录下即可。
'''

class APKSigner:
    @staticmethod
    def sign(toolPath, workPath, apkPath, newApkPath):
        try:
            logging.info("[APKSigner.sign] 强制签名")
            if not APKSigner.deleteMetaInfoDirInZip(toolPath, apkPath):
                logging.error("[APKSigner.sign] 向zip中删除META-INF目录出错")

            signToolPath = os.path.join(toolPath, 'sign')
            signJarPath = os.path.join(signToolPath, 'signapk.jar')
            x509Path = os.path.join(signToolPath, 'testkey.x509.pem')
            pk8Path = os.path.join(signToolPath, 'testkey.pk8')
            if not APKSigner.checkPath(signJarPath) or not APKSigner.checkPath(x509Path) or \
                not APKSigner.checkPath(pk8Path):
                return False

            signedApkPath = os.path.join(workPath, 'signed.apk')

            command = 'java -jar \"%s\" \"%s\" \"%s\" \"%s\" \"%s\"' % (signJarPath, x509Path, pk8Path, apkPath, signedApkPath)
            result = star.runJar(command)
            logging.info("[APKSigner.sign] %s", result)
            if not os.path.exists(signedApkPath):
                logging.error("[APKSigner.sign] 对apk: %s签名失败", apkPath)
                return False

            if not star.movefile(signedApkPath, newApkPath):
                logging.error("[APKSigner.sign] 移动文件%s到%s失败", signedApkPath, newApkPath)
                return False

            logging.info("[APKSigner.sign] 强制签名结束")
        except Exception as e:
            logging.error("[APKSigner.sign] 强制签名失败，原因：%s", e)
            return False
        return True

    @staticmethod
    def checkPath(filePath):
        if not os.path.exists(filePath):
            logging.error("[checkPath] 签名工具%s不存在", filePath)
            return False
        return True

    @staticmethod
    def isCertFile(fileName):
        fileName = str(fileName).strip()
        if fileName.endswith(".MF") or fileName.endswith(".SF") or \
            fileName.endswith(".RSA") or fileName.endswith(".DSA"):
            return True

        return False

    @staticmethod
    def deleteMetaInfoDirInZip(toolPath, apkPath):
        try:
            sigFileList = []
            zfobj = zipfile.ZipFile(apkPath)
            for name in zfobj.namelist():
                if not str(name).startswith('META-INF'):
                    continue
                if APKSigner.isCertFile(name):
                    sigFileList.append(name)

            zfobj.close()
            # print sigFileList
            for sigFile in sigFileList:
                if not ZipManager.delFileFromZip(toolPath, apkPath, sigFile):
                    logging.error("[deleteMetaInfoDirInZip] 从%s删除%s文件失败", apkPath, sigFile)
                    return False

        except Exception as e:
            logging.error("[deleteMetaInfoDirInZip] 从%s中删除签名文件失败，原因：%s", apkPath, e)
            return False
        return True

    #从签名文件获取签名信息
    @staticmethod
    def getSignatureFromFile(filePath):
        signature = ''
        try:
            fileContent = ''
            with open(filePath, 'rb') as fp:
                fileContent = fp.read()

            content = decoder.decode(fileContent, asn1Spec=rfc2315.ContentInfo())[0]
            if content.getComponentByName('contentType') != rfc2315.signedData:
                logging.error("[genCertMd5FileFromRsa] 不支持的签名格式")
                return signature

            content = decoder.decode(content.getComponentByName('content'),
                                asn1Spec=rfc2315.SignedData())[0]
            try:
                certificates = content.getComponentByName('certificates')
            except Exception as e:
                logging.error("[genCertMd5FileFromRsa] Certificates 没有找到，原因：%s", e)
                return signature

            cert_encoded = encoder.encode(certificates)[4:]
            signature = hashlib.md5(cert_encoded).hexdigest()
        except Exception as e:
            logging.error("[getCertMd5FileFromRsa] 计算证书md5失败, 原因:%s ", e)
            return ''

        return signature

    #从apk获取签名信息
    @staticmethod
    def getSignatureFromApk(apkPath):
        signature = ''
        try:
            cert = None
            with zipfile.ZipFile(apkPath, 'r') as apk:
                certs = [n for n in apk.namelist() if APKSigner.cert_path_regex.match(n)]
                if len(certs) < 1:
                    logging.error("[getCertMd5FileFromApk] Found no signing certificates on %s" % apkPath)
                    return ''
                if len(certs) > 1:
                    logging.error("[getCertMd5FileFromApk] Found multiple signing certificates on %s" % apkPath)
                    return ''

                cert = apk.read(certs[0])

            content = decoder.decode(cert, asn1Spec=rfc2315.ContentInfo())[0]
            if content.getComponentByName('contentType') != rfc2315.signedData:
                logging.error("[genCertMd5FileFromRsa] 不支持的签名格式")
                return signature

            content = decoder.decode(content.getComponentByName('content'),
                                asn1Spec=rfc2315.SignedData())[0]
            try:
                certificates = content.getComponentByName('certificates')
            except Exception as e:
                logging.error("[genCertMd5FileFromRsa] Certificates 没有找到，原因：%s", e)
                return signature

            cert_encoded = encoder.encode(certificates)[4:]
            signature = hashlib.md5(cert_encoded).hexdigest()
        except Exception as e:
            logging.error("[getCertMd5FileFromApk] 计算证书md5失败, 原因:%s ", e)
            return ''

        return signature

    @staticmethod
    def getSignature(unzipPath):
        metainfPath = os.path.join(unzipPath, 'META-INF')
        if not os.path.exists(metainfPath):
            logging.error("[getSignature] 签名文件目录%s不存在", metainfPath)
            return ''
        filelist = star.getFileNameListFormDir(metainfPath, ['.rsa', '.dsa'])

        realRsaFile = ''
        if len(filelist) == 0:
            logging.error("[getSignature] 证书文件不存在")
            return ''
        elif len(filelist) == 1:
            realRsaFile = os.path.join(metainfPath, filelist[0])
        else:
            for item in filelist:  #todo 多个签名文件该如何处理，报错？
                if str(item) == 'CERT.RSA':
                    realRsaFile = os.path.join(metainfPath, item)
                    break

        if not os.path.exists(realRsaFile):
            logging.error("[getSignature] %s证书文件不存在", realRsaFile)
            return ''

        signature = APKSigner.getSignatureFromFile(realRsaFile)
        if signature == '':
            logging.error("[getSignature] 计算证书md5未成功")
            return ''

        logging.info("[getSignature] 计算证书md5完成,md5:%s", signature)
        return signature.upper()

APKSigner.cert_path_regex = re.compile(r'^META-INF/.*\.(DSA|EC|RSA)$')

if __name__ == '__main__':
    signer = APKSigner.getSignatureFromFile("E:\\test\\NETEASE.RSA")
    print(signer)