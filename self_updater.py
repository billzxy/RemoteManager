import os
import subprocess
import traceback
import psutil
import shutil
import jsonpickle
import configparser
import simplejson
import logging
import time
from misc.enumerators import PatchCyclePhase, PatchStatus
from conf.reg import reg_get_QTHZ_path

"""
本程序是用来辅助更替entrypoint.exe的, entrypoint.exe会启动本程序
然后本程序会终止entrypoint.exe的进程, 然后进行文件更替
更替完毕后, 修改相应更新态信息保存到文件, 然后再启动entrypoint.exe
entrypoint.exe会在初始化的时候读取相应状态, 继续未完成的流程

"""
FORMAT_PATTERN = '%(asctime)-15s.%(msecs)d [%(levelname)s] '+\
    '--- %(module)s(%(lineno)d) : %(message)s'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
SETTINGS_PATH = "./settings/settings.ini"
flogger = logging.getLogger("file_logger")
flogger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler('./logs/update.log', encoding='utf-8')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(logging.Formatter(FORMAT_PATTERN, TIME_FORMAT))
flogger.addHandler(fileHandler)

class PatchObject(object):
    def __init__(self, version_data):
        self.version_code = version_data['versionCode']
        self.version_num = version_data['versionNum']
        self.file_MD5 = version_data['fileMd5']
        self.remark = version_data['remark']
        try:
            self.argument_config_map = version_data['argumentConfigMap']
        except:
            self.argument_config_map = {}
        self.status = PatchStatus.PENDING

    def set_status(self, new_status):
        self.status = new_status
class Updater:
    def __init__(self):
        # 初始化路径和配置等信息
        self.patch_meta = None
        self.state = None
        self.self_update_version = None
        self.settings = configparser.ConfigParser()
        self.settings.read(SETTINGS_PATH, encoding="UTF-8")
        self.qthz_path = reg_get_QTHZ_path()
        self.meta_file_path = self.qthz_path + self.settings['paths']['patch'] + self.settings['paths']['patchmeta']
        self.remote_manager_path = self.qthz_path + self.settings['paths']['manager_dir'] + self.settings['paths']['manager']
        self.read_patch_meta()
        # 组装安装包的路径
        self.new_manager_patch_path = self.qthz_path + self.settings['paths']['patch'] +"\\"+ self.self_update_version + self.settings['paths']['manager']

    # 读取更新流程状态元文件, 获取更新流程态, 获取到自更新的版本
    def read_patch_meta(self):
        flogger.info("读取元文件信息")
        with open(self.meta_file_path, 'r') as meta_file:
            json_str = meta_file.read()
        self.patch_meta = jsonpickle.decode(json_str)
        self.state = PatchCyclePhase(int(self.patch_meta['state']))
        # 这个字段会在更替文件的步骤处, 用来定位安装包的位置
        self.self_update_version = self.patch_meta['self_update_version']

    # 更新完毕后, 修改元文件, 保存状态
    def save_patch_meta(self):
        flogger.info("修改元文件状态")
        self.patch_meta['state'] = PatchCyclePhase.SELF_UPDATE_COMPLETE.value
        data_json_str = jsonpickle.encode(self.patch_meta)
        
        with open(self.meta_file_path, 'w') as meta_file:
            meta_file.write(data_json_str)

    # 终止entrypoint.exe进程
    def call_an_ambulance(self):
        flogger.info("终止本体进程")
        manager_name = self.settings['paths']['manager'].strip("\\")
        pids = self.get_pids_by_name(manager_name)
        for pid in pids:
            p = psutil.Process(pid)
            try:
                p.terminate()
            except:
                flogger.error(traceback.format_exc())
            
    # 更替entrypoint.exe 
    def but_not_for_me(self):
        flogger.info("更替可执行文件")
        manager_name = self.settings['paths']['manager'].strip("\\")
        pids = self.get_pids_by_name(manager_name)
        # 循环 等待entrypoint.exe的退出
        while(len(pids)):
            time.sleep(1)
            pids = self.get_pids_by_name(manager_name)
        # 更替
        try:
            shutil.copy2(self.new_manager_patch_path, self.qthz_path + self.settings['paths']['manager_dir'])
        except:
            flogger.error(traceback.format_exc())
    
    # 启动entrypoint.exe
    def proceed_to_pull_the_gun_out(self):
        flogger.info("启动程序")
        try:
            proc = subprocess.Popen(
                [self.remote_manager_path], 
                shell=False, creationflags=subprocess.DETACHED_PROCESS)
        except:
            flogger.error(traceback.format_exc())

    # 根据名称获取到进程pid
    def get_pids_by_name(self, process_name): 
        pids = []
        for proc in psutil.process_iter():
            if proc.name() == process_name:
                pids.append(proc.pid)
        return pids

def main():
    flogger.info("开始执行自更替")
    try:
        # 自更新的辅助流程开始
        # 初始化patch.meta元文件路径和配置等信息
        updater = Updater()
        # 终止entrypoint.exe进程
        updater.call_an_ambulance()
        # 更替entrypoint.exe 
        updater.but_not_for_me()
        # 更新完毕后, 修改元文件, 保存状态
        updater.save_patch_meta()
        # 启动entrypoint.exe
        updater.proceed_to_pull_the_gun_out()
    except:
        flogger.error(traceback.format_exc())
        os.system('pause')
    

main()