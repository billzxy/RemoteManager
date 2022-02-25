import logging
from misc.decorators import manager, with_countdown, with_lock
from utils.my_logger import logger
from patching.patch_obj import PatchObject
from misc.enumerators import PatchStatus, ThreadLock, UpgradeMark, PatchCyclePhase
from misc.exceptions import FileDownloadError, ICBRequestError, NoFileError
from pathlib import Path
from gui.winrt_toaster import toast_notification
import os, jsonpickle, shutil, hashlib, traceback, zipfile, threading, time

"""
更新状态的管理
不负责安装更新包

"""

@manager
@logger
class PatchManager:
    def __init__(self):
        jsonpickle.set_decoder_options('json', encoding='utf8')
        
    def post_init(self):
        self.reset_states()
        self.meta_file_path = self.settings_manager.get_patch_meta_path()
        self.patch_dir_path = self.settings_manager.get_patch_dir_path()
        
    # 检查更新的流程入口
    # @with_lock点缀器是用来给这个方法上锁的 
    # 下面两个锁就表示 在安装更新和心跳发送的时候, 不执行更新的检查
    @with_lock(ThreadLock.INSTALL_UPDATE)
    @with_lock(ThreadLock.HEARTBEAT, blocking=True)
    def check_update(self):
        try:  
            result = self.update_driver()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            result = 0
        finally:
            self.logger.debug("检查更新流程: %s", '完成' if result else '异常') 

    # 更新的流程
    # 流程分几个态(phase) 具体参考 PatchCyclePhase 枚举
    # 根据现在的更新状态(self.state)去决定执行对应的操作
    def update_driver(self):
        # 通过load_meta()再次获取下更新流程所处的状态
        status = -1
        self.load_meta()
        # if not self.state == PatchCyclePhase.READY:
        #     self.debug("Existing update sequence is in progress")
        #     return 0
        self.info("当前下载流程状态: %s", self.state.name)
        # 根据状态执行相应phase下应该执行的流程
        # 下面的流程会在结束后自动串入接下来的流程, 所以是 if-elif 判断
        if self.state == PatchCyclePhase.READY:
            status = self.check_for_update_phase()
        elif self.state == PatchCyclePhase.INCEPTION:
            status = self.file_download_phase(timed=True, max_wait=3, randomly=True)
        elif self.state == PatchCyclePhase.COMPLETE:
            status = self.check_for_update_phase()
        
        # 如果执行结果是失败, 拿到0作为返回值, 那就记一次重试
        if(status==0): # something went wrong
            self.count_retry_once()

        # 将现在的更新状态保存到本地
        self.dump_meta()  
        return status 

    # 如果是"准备完毕READY"态, 则为初始态, 暂时不知道是否有新的更新, 但是准备好开始新的更新流程了
    # 这一步就是先检查更新
    def check_for_update_phase(self):
        try:
            content = self.request_manager.get_version_check()
            self.logger.debug("查询版本回餐: %s",content)
            self.upgrade_mark = content['upgradeMark']
            # 无需更新则返回
            if self.upgrade_mark==0:
                self.logger.info("当前已是最新版本, 无需更新...")
                return 1
            upgrade_list = content['upgradeList']
        except Exception as err:
            self.logger.error("%s", traceback.format_exc())
            self.state = PatchCyclePhase.READY
            return 0

        # 有更新内容的话, 将远端返回回的需要更新的一个或多个版本信息
        # 包装成一个或多个PatchObject数据对象
        self.patch_objs = list(map(PatchObject, upgrade_list))
        # 更新流程状态改为"开始INCEPTION"
        self.state = PatchCyclePhase.INCEPTION
        # 进入下一步流程
        return self.file_download_phase(timed=True, max_wait=3, randomly=True)

    # 下载更新包的流程
    # @with_countdown是用来加个倒计时功能的
    @with_countdown
    def file_download_phase(self):
        # self.logger.debug("content: %s", content)
        # 状态改为"下载中DOWNLOAD"
        self.state = PatchCyclePhase.DOWNLOAD
        toast_notification("证通智能精灵", "软件更新", "发现可用的软件更新, 正在下载更新")
        try:
            # 遍历封装好的patch_obj, 去执行下载
            for index, patch_obj in enumerate(self.patch_objs):
                self.download_one(self.patch_objs[index])

        except FileDownloadError as err:
            self.logger.error("下载失败! 原因: %s", err)
            self.state = PatchCyclePhase.INCEPTION
            return 0
        self.debug("Download finished.")
        # 下载完成后, "等待安装PENDING"的状态会被保存到本地, 以防程序出错异常退出而丢失状态
        self.preserve_installation_state(PatchCyclePhase.PENDING)
        # 判断本次更新流程是否需要强制更新
        if(UpgradeMark(self.upgrade_mark)==UpgradeMark.MANDATORY):
            self.debug("Mandatory update")
            toast_notification("证通智能精灵", "重要更新", "需要立即应用重要的更新, 您的外呼任务将会被自动暂停")
            # update_thread = threading.Thread(target=self.install_manager.installation_driver, name="ForcedUpdateThread")
            # update_thread.start()
            time.sleep(1)
            # 是的话直接调用install_manager来开始安装流程
            self.install_manager.installation_driver()
        # 不强制, 仅提示
        elif(UpgradeMark(self.upgrade_mark)==UpgradeMark.OPTIONAL):
            self.debug("Optional update")
            toast_notification("证通智能精灵", "下载完成", "新的软件更新已经准备完毕, 请您及时更新!")
        
        self.reset_retry()
        return 1  

    # 下载一个子版本的安装包
    def download_one(self, patch_obj):
        # 判断该版本对应的patch_obj的状态是否为"DOWNLOADED已下载"
        if(patch_obj.status==PatchStatus.DOWNLOADED):
            return
        # 修改这个版本的patch_obj状态到"下载中DOWNLOADING"
        patch_obj.status = PatchStatus.DOWNLOADING
        
        # 保存文件到本地, 做完整性校验, 解压缩等操作
        # 解压出来的文件会被放在patch目录下的以子版本的version_num作为名称的目录内
        file_dir = f"{self.patch_dir_path}\\{patch_obj.version_num}"
        file_name = f"\\{patch_obj.version_code}.zip"
        full_path = file_dir + file_name
        Path(file_dir).mkdir(parents=True, exist_ok=True)
        self.progress = 0
        try:
            self.request_manager.get_file_download(
                patch_obj.version_code, full_path, self.check_dl_progress)
        except NoFileError:
            # 有可能有的版本只有下发参数而不带文件, 因此也记录为下载完成
            patch_obj.status = PatchStatus.DOWNLOADED
            return 
        md5 = self.gen_md5(full_path)
        self.debug("远程文件MD5值: %s", patch_obj.file_MD5)
        self.debug("本地文件MD5值: %s", md5)
        if not md5==patch_obj.file_MD5:
            raise FileDownloadError(f"文件完整性校验失败: {patch_obj.version_num}/{patch_obj.version_code}")
        
        with zipfile.ZipFile(full_path, 'r') as zip_ref:
            try:
                zip_ref.extractall(file_dir)
            except:
                self.logger.error("解压文件出错: %s, %s", 
                    full_path, traceback.format_exc())
                # 出错退回初始值"等待更新PENDING"
                patch_obj.status = PatchStatus.PENDING
            else:
                # 标记该版本为已下载完成
                patch_obj.status = PatchStatus.DOWNLOADED

    # 重置PatchManager存在内存里的更新状态
    def reset_states(self):
        self.state = PatchCyclePhase.READY
        self.retry = 5
        self.progress = 0
        self.patch_objs = []
        self.upgrade_mark = -1
        self.self_update_version = None

    def check_exists(self, dir_or_file):
        return os.path.exists(dir_or_file)

    # 将更新流程的状态, 在本地持久化保存
    def preserve_installation_state(self, new_state):
        self.state = new_state
        self.dump_meta()

    # 将更新流程的状态, 在本地持久化保存
    def dump_meta(self):
        meta_data = {
            'state': self.state.value,
            'list': list(map(PatchObject.to_dict, self.patch_objs)),
            'retries': self.retry,
            'mark': self.upgrade_mark,
            'self_update_version': self.self_update_version
        }
        data_json_str = jsonpickle.encode(meta_data)
        # if not os.path.isfile(self.meta_file_path):
        #     self.logger.debug('Creating new meta file')
        #     file_flag = 'x'
        
        Path(self.patch_dir_path).mkdir(parents=True, exist_ok=True)
        with open(self.meta_file_path, 'w') as meta_file:
            meta_file.write(data_json_str)
            self.debug('Update state is saved in meta file')

    # 读取本地持久化保存的更新流程的状态
    def load_meta(self):
        try:
            with open(self.meta_file_path, 'r') as meta_file:
                json_str = meta_file.read()
        except FileNotFoundError:
            self.warn("Could not find download meta file, previous states might not be preserved")
            self.reset_states()
            return 
        meta_data = jsonpickle.decode(json_str)
        self.state = PatchCyclePhase(int(meta_data['state']))
        self.patch_objs = list(map(PatchObject.from_dict, meta_data['list']))
        self.retry = meta_data['retries']
        self.upgrade_mark = meta_data['mark']
        self.self_update_version = meta_data['self_update_version']
        self.logger.debug('Loaded state from meta file')
        self.logger.debug('Current Patch Phase: %s', self.state.name)
        try:
            [self.logger.debug(f'Version {patch_obj.version_num}: {patch_obj.status.name}') 
                for patch_obj in self.patch_objs]
        except:
            pass

    # 记录一次更新流程的失败
    def count_retry_once(self):
        self.retry -= 1
        if(self.retry < 0):
            self.state = PatchCyclePhase.READY
            self.reset_retry()

    # 重置失败计数器
    def reset_retry(self):
        self.retry = 5

    def check_dl_progress(self, currIndex, totalIndex):
        progress = 100*currIndex/totalIndex
        self.progress = progress
        self.info("Download progress: %.0f percent, %s of %s completed..."%(progress, currIndex, totalIndex))

    def gen_md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    

    