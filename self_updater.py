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

FORMAT_PATTERN = '%(asctime)-15s.%(msecs)d [%(levelname)s] '+\
    '--- %(module)s(%(lineno)d) : %(message)s'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
SETTINGS_PATH = "./settings/settings.ini"
flogger = logging.getLogger("file_logger")
flogger.setLevel(logging.DEBUG)
fileHandler = logging.FileHandler('update.log', encoding='utf-8')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(logging.Formatter(FORMAT_PATTERN, TIME_FORMAT))
flogger.addHandler(fileHandler)

class Updater:
    def __init__(self):
        self.patch_meta = None
        self.state = None
        self.self_update_version = None
        self.settings = configparser.ConfigParser()
        self.settings.read(SETTINGS_PATH, encoding="UTF-8")
        self.qthz_path = reg_get_QTHZ_path()
        self.meta_file_path = self.qthz_path + self.settings['paths']['patch'] + self.settings['paths']['patchmeta']
        self.remote_manager_path = self.qthz_path + self.settings['paths']['manager_dir'] + self.settings['paths']['manager']
        self.read_patch_meta()
        self.new_manager_patch_path = self.qthz_path + self.settings['paths']['patch'] +"\\"+ self.self_update_version + self.settings['paths']['manager']

    def read_patch_meta(self):
        flogger.info("读取元文件信息")
        with open(self.meta_file_path, 'r') as meta_file:
            json_str = meta_file.read()
        self.patch_meta = jsonpickle.decode(json_str)
        self.state = self.patch_meta['state']
        self.self_update_version = self.patch_meta['self_update_version']

    def save_patch_meta(self):
        flogger.info("修改元文件状态")
        self.patch_meta['state'] = PatchCyclePhase.SELF_UPDATE_COMPLETE
        data_json_str = jsonpickle.encode(self.patch_meta)
        
        with open(self.meta_file_path, 'w') as meta_file:
            meta_file.write(data_json_str)

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
            
    def but_not_for_me(self):
        flogger.info("更替可执行文件")
        manager_name = self.settings['paths']['manager'].strip("\\")
        pids = self.get_pids_by_name(manager_name)
        while(len(pids)):
            time.sleep(1)
            pids = self.get_pids_by_name(manager_name)
            
        try:
            shutil.copy2(self.new_manager_patch_path, self.qthz_path + self.settings['paths']['manager_dir'])
        except:
            flogger.error(traceback.format_exc())
    
    def proceed_to_pull_the_gun_out(self):
        flogger.info("启动程序")
        try:
            proc = subprocess.Popen(
                [self.remote_manager_path], 
                shell=False, creationflags=subprocess.DETACHED_PROCESS)
        except:
            flogger.error(traceback.format_exc())

    def get_pids_by_name(self, process_name): 
        pids = []
        for proc in psutil.process_iter():
            if proc.name() == process_name:
                pids.append(proc.pid)
        return pids

def main():
    flogger.info("开始执行自更替")
    try:
        updater = Updater()
        updater.call_an_ambulance()
        updater.but_not_for_me()
        updater.save_patch_meta()
        updater.proceed_to_pull_the_gun_out()
    except:
        flogger.error(traceback.format_exc())
        os.system('pause')
    

main()