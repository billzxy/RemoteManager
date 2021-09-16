from misc.decorators import manager, with_lock
from utils.my_logger import logger
from misc.exceptions import UpdateIsNoGo
from misc.enumerators import FilePath, PatchCyclePhase, PatchStatus, ThreadLock
from pathlib import Path
from os import listdir
from os.path import isfile, join, exists, splitext
from gui.winrt_toaster import toast_notification
import shutil, traceback, time, sqlite3, threading, subprocess


@manager
@logger
class InstallManager:
    def __init__(self):
        pass

    def post_init(self):
        self.paths = self.settings_manager.get_paths()
        self.fnames = self.settings_manager.get_filenames()
        self.patch_manager.load_meta()
        self.__check_self_update_follow_up()
    
    def clear_download_cache(self):
        self.logger.info("清除下载缓存")
        patch_dir = self.settings_manager.get_patch_dir_path()
        try:
            shutil.rmtree(patch_dir)
        except:
            self.logger.debug("清除失败")
            toast_notification("证通智能精灵", "清除缓存", "本地下载缓存清除过程遇到问题, 请您稍后再试")
        else:
            self.logger.info("清除完毕")
            toast_notification("证通智能精灵", "清除缓存", "本地下载缓存已经清除")

    @with_lock(ThreadLock.INSTALL_UPDATE)
    @with_lock(ThreadLock.HEARTBEAT, blocking=True)
    def install_update(self):
        try:    
            result = self.installation_driver()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            result = 0
        finally:
            self.logger.debug("安装流程: %s", '完成' if result else '异常') 

    def installation_driver(self):
        self.patch_manager.load_meta()
        # extra try-catch block to ensure a lock-release when @with_lock decorator finishes execution
        try: 
            if(self.patch_manager.state <= PatchCyclePhase.DOWNLOAD 
                or self.patch_manager.state >= PatchCyclePhase.COMPLETE):
                toast_notification("证通智能精灵", "软件更新", "暂时没有需要安装的更新噢!")
                self.logger.info("暂无需要安装的更新")
                return 1
            self.pause_all_operations()
            self.logger.info("开始安装更新")
            toast_notification("证通智能精灵", "软件更新", "开始安装软件更新...")
            result = self.installation()
        
        except UpdateIsNoGo as nogo:
            toast_notification("证通智能精灵", "更新暂停", nogo.cause())
            self.logger.error(str(nogo))
            # decide if update should be triggered manually, or automatically timed
            # later on
            return 0
        except Exception:
            raise
        else:
            return result    
    
    def installation(self):
        if self.patch_manager.state == PatchCyclePhase.PENDING:
            result = self.create_backup()
        if self.patch_manager.state == PatchCyclePhase.BACKUP_CREATED:
            result = self.replace_files()
        if self.patch_manager.state == PatchCyclePhase.SELF_UPDATE_PENDING:
            result = self.commence_self_update()
        if self.patch_manager.state == PatchCyclePhase.ROLLEDBACK:
            # TODO: do something to mitigate the aftermath
            for index, _ in enumerate(self.patch_manager.patch_objs):
                patch_obj = self.patch_manager.patch_objs[index]
                patch_obj.status = PatchStatus.DOWNLOADED
            self.patch_manager.preserve_installation_state(PatchCyclePhase.PENDING)
            self.logger.info("可尝试再次安装")
            self.resume_all_operations()
        if self.patch_manager.state == PatchCyclePhase.FILES_UPDATED:
            result = self.post_installation_cleanup()
        if self.patch_manager.state == PatchCyclePhase.SELF_UPDATE_COMPLETE:
            result = self.__check_self_update_follow_up()
        
        return result

    def create_backup(self):
        try:
            self.logger.info("文件备份中")
            backup_dir = self.settings_manager.get_backup_dir_path()
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
            db_dir = self.settings_manager.get_sqlite_db_path()
            shutil.copytree(db_dir, backup_dir+"/data", dirs_exist_ok=True)
            jar_path = self.paths[FilePath.JAR]
            shutil.copy2(jar_path, backup_dir)
            conf_path = self.paths[FilePath.CONFIG]
            shutil.copy2(conf_path, backup_dir)
            yml_path = self.settings_manager.get_QTHZ_inst_path()+self.fnames[FilePath.APP_YML]
            shutil.copy2(yml_path, backup_dir)
            self.logger.info("文件备份完毕")    
        except Exception:
            self.logger.error(traceback.format_exc())
            raise
        else:
            self.patch_manager.preserve_installation_state(PatchCyclePhase.BACKUP_CREATED)
            return 1

    def revert_backup(self, patch_objs):
        for index, _ in enumerate(patch_objs):
            patch_obj = patch_objs[index]
            patch_obj.status = PatchStatus.REVERTED
            self.logger.debug("记录回滚版本: %s", patch_obj.version_num)
        self.revert_to_last()
        self.patch_manager.preserve_installation_state(PatchCyclePhase.ROLLEDBACK)
        toast_notification("证通智能精灵", "更新失败", "非常抱歉, 更新过程中遇到问题, 已经为您退回到之前的版本, 请您联系证通的技术人员")
        self.logger.info("回滚完成")

    def revert_to_last(self):
        backup_dir = self.settings_manager.get_backup_dir_path()
        db_dir = self.settings_manager.get_sqlite_db_path()
        shutil.rmtree(db_dir)
        shutil.copytree(backup_dir+"/data", db_dir, dirs_exist_ok=True)
        qthz_path = self.settings_manager.get_QTHZ_inst_path()
        shutil.copy2(backup_dir+ self.fnames[FilePath.JAR], qthz_path)
        shutil.copy2(backup_dir+"\\configuration.ini", qthz_path+"\\conf")
        shutil.copy2(backup_dir+ self.fnames[FilePath.APP_YML], qthz_path)
        self.config_manager.load_config()
        self.logger.info("文件回滚完毕")

    # 真正开始安装的流程
    def replace_files(self):
        self.logger.debug("开始文件更替")
        patch_objs = self.patch_manager.patch_objs
        for index, patch_obj in enumerate(patch_objs):
            if not patch_obj.status == PatchStatus.DOWNLOADED:
                continue
            try:
                self.replace_one_version(patch_objs[index])
            except Exception as e_outer: # any exception or error, will trigger a rollback
                self.logger.error("安装流程出现异常, 回滚中: %s", traceback.format_exc())
                try:
                    self.revert_backup(patch_objs)
                except Exception as e_inner:
                    self.logger.error("回滚失败 %s", traceback.format_exc())
                    raise e_inner
                else:
                    return 0
            
            else: # 
                # change patch_obj PatchStatus
                patch_objs[index].status = PatchStatus.INSTALLED
                self.logger.debug("完成一个版本的安装: %s", patch_obj.version_num)

        self.patch_manager.preserve_installation_state(PatchCyclePhase.FILES_UPDATED)
        
        if(self.patch_manager.self_update_version or not self.patch_manager.self_update_version==None):
            self.patch_manager.preserve_installation_state(PatchCyclePhase.SELF_UPDATE_PENDING)    
        
        self.logger.info("各个版本遍历安装完成")
        return 1

    def replace_one_version(self, patch_obj):
        arg_conf_map = patch_obj.argument_config_map
        version_num = patch_obj.version_num
        version_code = patch_obj.version_code
        patch_dir_path = "%s\\%s" %(self.settings_manager.get_patch_dir_path(),version_num)
        qthz_path = self.settings_manager.get_QTHZ_inst_path()
        
        self.logger.info("开始安装版本: %s", version_num)

        # TODO: execute sh commands 
        
        # exec sql script; or replace sqlite source file 
        self.update_sqlite_db(patch_dir_path, qthz_path, arg_conf_map)

        # TODO: replace JAR
        jar_patch = patch_dir_path + self.fnames[FilePath.JAR]
        if exists(jar_patch):
            shutil.copy2(jar_patch, qthz_path)
            self.logger.debug("更替JAR包完成")
        
        yml_path = patch_dir_path+self.fnames[FilePath.APP_YML]
        if exists(yml_path):
            shutil.copy2(yml_path, qthz_path)
            self.logger.debug("更替YAML配置文件完成")

        #self-update
        #start.exe
        start_exe_path = patch_dir_path+self.fnames[FilePath.STARTER]
        if exists(start_exe_path):
            try:
                shutil.copy2(start_exe_path, self.settings_manager.get_remote_manager_path())
            except:
                self.logger.error("失败: 更替主启动程序, 原因 %s", traceback.format_exc())
            self.logger.debug("更替主启动程序完成")

        #updater.exe
        updater_path = patch_dir_path+self.fnames[FilePath.UPDATER]
        if exists(updater_path):
            try:
                shutil.copy2(updater_path, self.settings_manager.get_remote_manager_path())
            except:
                self.logger.error("失败: 更替自更新程序, 原因 %s", traceback.format_exc())
            self.logger.debug("更替自更新程序完成")

        #settings.ini
        settings_file_path = patch_dir_path+"\\settings.ini"
        if exists(settings_file_path):
            try:
                new_configs = self.settings_manager.read_ini_into_config(settings_file_path)
                original_configs = self.settings_manager.read_ini_into_config("./settings/settings.ini")
                for section in new_configs:
                    for config in new_configs[section]:
                        try:
                            original_configs[section][config] = new_configs[section][config]
                        except KeyError:
                            original_configs.add_section(section)
                            original_configs[section][config] = new_configs[section][config]

                self.settings_manager.write_config_to_ini_file(original_configs, "./settings/settings.ini")
            except:
                self.logger.error("失败: 更替自更新程序, 原因 %s", traceback.format_exc())
            self.logger.debug("更替自更新程序完成")

        #entrypoint.exe
        entrypoint_path = patch_dir_path+self.fnames[FilePath.MANAGER]
        if exists(entrypoint_path):
            self.patch_manager.self_update_version = version_num
            self.patch_manager.dump_meta()

        # TODO: replace lua scripts
        
        # overwrite configuration.ini
        self.config_manager.update_remote_config(arg_conf_map, version_num, version_code)
    
    def update_sqlite_db(self, patch_dir_path, qthz_path, arg_conf_map):
        db_patch_dir = patch_dir_path+"\\data"
        db_dir = qthz_path+"\\data"
        sqlite_file = None
        sql_script = None
        dotdb_file = None
        # if the '/data' dir exists in patch_dir, theres a need to update data
        should_update_data = exists(db_patch_dir)
        if should_update_data:
            self.logger.debug("需要更新SQL数据")
            onlyfiles = [f for f in listdir(db_patch_dir) if isfile(join(db_patch_dir, f))]
            for file in onlyfiles:
                _, ext = splitext(file)
                if ext=="":
                    sqlite_file = file
                else:
                    if ext=='.sql' or ext=='sql':
                        sql_script = file
                    elif ext=='.db' or ext=='db':
                        dotdb_file = file
        
        # if there exists a sql script to be exec-ed, 
        if(sql_script):
            self.logger.debug("需要执行SQL命令")
            # call sql file execution
            with open(db_patch_dir+"\\"+sql_script, 'r', encoding='utf-8') as sql_file:
                sql_as_string = sql_file.read()
                self.logger.debug("已读取SQL脚本")
                try:
                    self.db_operator.execute_sql_file(sql_as_string)
                except Exception:
                    self.logger.error("SQL命令执行异常: %s", traceback.format_exc())
                    raise
                else:
                    self.logger.debug("SQL脚本执行完毕")

        # copy all files from patch dir to data dir
        if should_update_data:
            shutil.copytree(db_patch_dir, db_dir, dirs_exist_ok=True)

        # if theres a need to mount a new sqlite db source
        # save the filename to config.ini
        if(sqlite_file):
            self.logger.debug("需要修改挂载的SQLite数据库源文件")
            arg_conf_map['dbfileName'] = sqlite_file

        self.logger.debug("数据更新完成")

    def commence_self_update(self):
        self.logger.info("开始自更替")
        updater_path = self.settings_manager.get_paths()[FilePath.UPDATER]
        try:
            proc = subprocess.Popen([updater_path], creationflags=subprocess.DETACHED_PROCESS)
        except Exception:
            self.logger.error(traceback.format_exc())
            return 0
        else:
            self.logger.info("自更替脚本程序启动成功, pid: %s", proc.pid)
            return 1

    def __check_self_update_follow_up(self):
        if self.patch_manager.state == PatchCyclePhase.SELF_UPDATE_COMPLETE:
            return self.post_installation_cleanup()
        

    def post_installation_cleanup(self):
        # when all installation(including self-update) finished
        if(len(self.patch_manager.patch_objs)>0):
            patch_obj = self.patch_manager.patch_objs[-1]
            remark = patch_obj.remark
            version = patch_obj.version_num
            self.logger.info(f"{'当前最新版本: '+version if version else ''} {'更新内容: '+remark if remark else ''}")
            toast_notification("证通智能精灵", "更新成功", f"{'当前最新版本: '+version if version else ''} {'更新内容: '+remark if remark else ''}")
        self.config_manager.load_config()
        self.config_manager.save_fs_conf()
        self.patch_manager.preserve_installation_state(PatchCyclePhase.COMPLETE)
        self.logger.info("安装更新完成!")
        self.resume_all_operations()
        self.patch_manager.preserve_installation_state(PatchCyclePhase.READY)
        return 1

    def pause_all_operations(self):
        self.logger.debug("Halting all operations, triggering killswitch in...")

        # 请求任务暂停接口, 会阻塞重试, 之后抛 No Go 信号
        self.request_manager.post_pause_all_tasks()

        # 调取FS呼出状态, 会阻塞重试, 之后抛No Go 信号
        self.process_manager.freeswith_call_status()

        # 停止Java和FS服务, 同步
        self.process_manager.stop_freeswitch()
        self.process_manager.stop_java()
        # 异步
        # fs_stopper_thread = threading.Thread(target=self.process_manager.stopFreeswitch)
        # fs_stopper_thread.start() 
        # java_stopper_thread = threading.Thread(target=self.process_manager.stop_java)
        # java_stopper_thread.start()
        # countdown = 3
        # for i in range(countdown, 0, -1):
        #     self.logger.debug(i)
        #     time.sleep(1)
        # fs_stopper_thread.join()
        # java_stopper_thread.join()
        

    def resume_all_operations(self):
        self.logger.info("Resuming operations immediately!")
        starter_thread =  threading.Thread(target=self.process_manager.start_QTHZ)
        starter_thread.start()
        self.config_manager.load_config()
        starter_thread.join()
        try:
            self.request_manager.post_resume_all_tasks()
        except:
            self.logger.error("请求恢复任务失败, 原因: %s", traceback.format_exc())
    


