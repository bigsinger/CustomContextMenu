# coding:utf-8
import os
import re
import star
import subprocess
# from cStringIO import StringIO
import StringIO
from PIL import Image
from APK import APK

'''
负责ADB相关的操作
参考：https://github.com/vmalyi/adb_android
'''

ADB_COMMAND_PREFIX = 'adb'
ADB_COMMAND_SHELL = 'shell'
ADB_COMMAND_PULL = 'pull'
ADB_COMMAND_PUSH = 'push'
ADB_COMMAND_RM = 'rm -r'
ADB_COMMAND_CHMOD = 'chmod -R 777'
ADB_COMMAND_UNINSTALL = 'uninstall'
ADB_COMMAND_INSTALL = 'install'
ADB_COMMAND_UNINSTALL = 'uninstall'
ADB_COMMAND_FORWARD = 'forward'
ADB_COMMAND_DEVICES = 'devices'
ADB_COMMAND_GETSERIALNO = 'get-serialno'
ADB_COMMAND_WAITFORDEVICE = 'wait-for-device'
ADB_COMMAND_KILL_SERVER = 'kill-server'
ADB_COMMAND_START_SERVER = 'start-server'
ADB_COMMAND_GET_STATE = 'get-state'
ADB_COMMAND_SYNC = 'sync'
ADB_COMMAND_VERSION = 'version'
ADB_COMMAND_BUGREPORT = 'bugreport'

SCALE = 0.5


class ADBManager:
    def __init__(self):
        self._deviceSelected = None
        self._devices = None  # {[0].name = "", [0].info = "", }
        self.get_devices()
        self.is_no_devices = False
        if len(self._devices) == 1:
            self.select(0)
        elif len(self._devices) == 0:
            self.is_no_devices = True
            print "no devices"

    def get_version(self):
        """
        Returns ADB tool version
        adb version
        ex：1.0.36
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_VERSION]
        code, ret = star.runcmd(adb_full_cmd)
        try:
            pattern = re.compile(r"version\s(.*?)\s")
            version = pattern.search(ret).group(1)
        except Exception as e:
            print e
            version = None
        return version

    def get_devices(self):
        """
        Return a list containing all connected ADB-devices.
        """
        devices = {}
        out = subprocess.check_output([ADB_COMMAND_PREFIX, "devices", "-l"],
                                      universal_newlines=True)
        self.check_output(out)
        ADB_DEV_PATTERN = re.compile(r"(\S*?)\s*?device\s")
        for line in out.split('\n'):
            matched = ADB_DEV_PATTERN.search(line)
            if matched:
                name = matched.group(1)
                devices[name] = line
        self._devices = devices
        return devices

    def select(self, name_or_id):
        """
        Specify the device name to target
        example: set_target_device('emulator-5554')
        """
        if self._devices is None:
            self.get_devices()

        if name_or_id is None:
            self.__error = 'Must get device list first'
            print "[!] Device not found in device list"
            return False

        if isinstance(name_or_id, int):
            index = 0
            for name, info in self._devices.items():
                if index == name_or_id:
                    self._deviceSelected = name
                    break
                index = index + 1
        else:
            for name, info in self._devices.items():
                if info.find(name_or_id) >= 0:
                    self._deviceSelected = name
                    break
        print "Target device select: %s" % self.get_device_selected()
        return self._deviceSelected is not None

    def get_device_selected(self):
        """
        Returns the selected device to work with
        """
        if self._deviceSelected == None:
            print "[*] No device target set"

        return self._deviceSelected

    def get_model(self):
        """
        Get Model name from taget device
        """
        model = None
        if self._deviceSelected is None:
            print "No device target set"
        else:
            pattern = re.compile(r"model:(.+)\sdevice")
            matched = pattern.search(self._devices[self._deviceSelected])
            if matched:
                model = matched.group(1)
        return model

    def get_serialno(self):
        """
        Get serial number for all available target devices
        :return: result of star.runcmd() execution
        """
        cmds = [ADB_COMMAND_PREFIX]
        if len(self._devices) > 1 or not self._deviceSelected:
            cmds.append("-s")
            cmds.append(self._deviceSelected)
        cmds.append(ADB_COMMAND_GETSERIALNO)
        code, ret = star.runcmd(cmds)
        if code == 0:
            return ret
        else:
            return None

    def get_build_props(self):
        """
        Get contents of /system/build.prop as dict.
        Return dictionary like: Property => Value
        """
        build_props = {}
        cmds = [ADB_COMMAND_PREFIX]
        if len(self._devices) > 1 or not self._deviceSelected:
            cmds.append("-s")
            cmds.append(self._deviceSelected)
        cmds.append("shell")
        cmds.append("cat /system/build.prop")
        out = subprocess.check_output(cmds, universal_newlines=True)
        for line in out.split('\n'):
            if line == '':
                continue
            prop = line.split('=')
            if not prop[0].startswith('#'):
                build_props[prop[0]] = prop[1]
        return build_props

    def bugreport(self, dest_file="default.log"):
        """
        Prints dumpsys, dumpstate, and logcat data to the screen, for the purposes of bug reporting
        :return: result of star.runcmd() execution
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_BUGREPORT]
        try:
            dest_file_handler = open(dest_file, "w")
        except IOError:
            print "IOError: Failed to create a log file"

        # We have to check if device is available or not before executing this command
        # as adb bugreport will wait-for-device infinitely and does not come out of
        # loop
        # Execute only if device is available only
        if _isDeviceAvailable():
            result = star.runcmd_to_file(adb_full_cmd, dest_file_handler)
            return (result, "Success: Bug report saved to: " + dest_file)
        else:
            return (0, "Device Not Found")

    def push(self, src, dest):
        """
        Push object from host to target
        :param src: string path to source object on host
        :param dest: string destination path on target
        :return: result of star.runcmd() execution
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_PUSH, src, dest]
        return star.runcmd(adb_full_cmd)

    def pull(self, src, dest):
        """
        Pull object from target to host
        :param src: string path of object on target
        :param dest: string destination path on host
        :return: result of star.runcmd() execution
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_PULL, src, dest]
        return star.runcmd(adb_full_cmd)

    def shell(self, cmd):
        """
        Execute shell command on target
        :param cmd: string shell command to execute
        :return: result of star.runcmd() execution
        """
        cmds = [ADB_COMMAND_PREFIX]
        if len(self._devices) > 1 or not self._deviceSelected:
            cmds.append("-s")
            cmds.append(self._deviceSelected)
        cmds.append(ADB_COMMAND_SHELL)
        cmds.append(cmd)
        return star.runcmd(cmds)

    def install(self, apk, opts=None):
        """
        Install *.apk on target
        :param apk: string path to apk on host to install
        :param opts: list command options (e.g. "-r", "-a")
        :return: result of star.runcmd() execution
        """
        cmds = [ADB_COMMAND_PREFIX]
        if len(self._devices) > 1 or not self._deviceSelected:
            cmds.append("-s")
            cmds.append(self._deviceSelected)
        cmds.append(ADB_COMMAND_INSTALL)
        if opts is not None:
            cmds.append(opts)
        cmds.append(apk)
        return star.runcmd(cmds)

    def uninstall(self, app, opts=[]):
        """
        Uninstall app from target
        :param app: app name to uninstall from target (e.g. "com.example.android.valid")
        :param opts: list command options (e.g. ["-r", "-a"])
        :return: result of star.runcmd() execution
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_UNINSTALL, self._convert_opts(opts), app]
        return star.runcmd(adb_full_cmd)

    def wait_for_device(self):
        """
        Block execution until the device is online
        :return: result of star.runcmd() execution
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_WAITFORDEVICE]
        return star.runcmd(adb_full_cmd)

    def sync(self):
        """
        Copy host->device only if changed
        :return: result of star.runcmd() execution
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_SHELL, ADB_COMMAND_SYNC]
        return star.runcmd(adb_full_cmd)

    def start_server(self):
        """
        Startd adb server daemon on host
        :return: result of star.runcmd() execution
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_START_SERVER]
        return star.runcmd(adb_full_cmd)

    def kill_server(self):
        """
        Kill adb server daemon on host
        :return: result of star.runcmd() execution
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_KILL_SERVER]
        return star.runcmd(adb_full_cmd)

    def get_state(self):
        """
        Get state of device connected per adb
        :return: result of star.runcmd() execution
        """
        adb_full_cmd = [ADB_COMMAND_PREFIX, ADB_COMMAND_GET_STATE]
        return star.runcmd(adb_full_cmd)

    def _convert_opts(self, opts):
        """
        Convert list with command options to single string value
        with 'space' delimeter
        :param opts: list with space-delimeted values
        :return: string with space-delimeted values
        """
        return ' '.join(opts)

    def start(self, apkfile, force=True):
        '''
        运行一个APK，首先解析包名和activity，force为真时，如果未安装则强制安装，如果已经打开了则重新打开。
        :param apkfile: APK全路径
        :param force: 是否强制运行
        :return:
        '''
        apk = APK(apkfile)
        main_activity = apk.get_main_activity()
        package = apk.get_package()
        code, ret = self.runapp(package, main_activity)
        if force and ret:
            if ret.find("does not exist") >= 0:
                code, ret = self.install(apkfile)
                if code == 0:
                    code, ret = self.runapp(package, main_activity)
            elif ret.find("brought to the front") >= 0:
                self.stopapp(package)
                code, ret = self.runapp(package, main_activity)
        return (code, ret)

    def runapp(self, package, activity):
        return self.shell('am start -W -n ' + package + '/' + activity)

    def startapp(self, package, activity):
        return self.runapp(package, activity)

    def stopapp(self, package):
        return self.shell('am force-stop ' + package)

    def listpackages(self):
        return self.shell('pm list packages')

    def check_output(self, out):
        """
        Check if the response of a command is valid.
        """
        if out == "error: device not found":
            sys.exit("Error connecting to device!")

    def reboot(self, option):
        if option == "system":
            subprocess.call([ADB_COMMAND_PREFIX, "reboot"])
        elif option in ("recovery", "bootloader"):
            subprocess.call([ADB_COMMAND_PREFIX, "reboot", option])
        else:
            print("Invalid reboot-option!")

    def get_screenshot(self, filename, scale=0.5):
        retcode, data = self.shell("screencap -p")
        if retcode == 0:
            data = data.replace(b'\r\n', b'\n')
            data = data.replace(b'\r\n', b'\n')
            # star.write(filename, data)
            im = Image.open(StringIO.StringIO(data))
            w, h = im.size
            im_ss = im.resize((int(w * scale), int(h * scale)), Image.ANTIALIAS).convert('RGBA')
            im_ss.save(filename)


if __name__ == '__main__':
    adb = ADBManager()
    adb.get_version()
    adb.getserialno()
    adb.isDeviceAvailable()
    adb.devices()
    adb.push('/tmp/file.txt', '/data/media/0')
    adb.pull('/data/media/0/file.txt', '/tmp/')
    adb.shell('ls')
    adb.install('/usr/local/app.apk')
    adb.uninstall('com.example.android.valid')
    apk = APK('demo.apk')
    main_activity = apk.get_main_activity()
    package = apk.get_package()
    adb.startapp(package, main_activity)
