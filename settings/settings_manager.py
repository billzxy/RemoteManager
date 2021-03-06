import configparser, os, logging, yaml, sys
from conf.reg import reg_get_QTHZ_path
from misc.enumerators import FilePath, SettingsCategories, SettingsItems
from settings.consts import DEFAULT_FILE_TEMPLATE
from misc.decorators import singleton

@singleton
class SettingsManager():
    def __init__(self):
        self.logger = logging.getLogger("box_helper_common_logger")
        self.logger.info("Starting the settings manager...")
        self.__settings_path = "./settings/settings.ini"
        self.read_settings(self.__settings_path)
        cond = (len(sys.argv)>1 and sys.argv[1]=='debug') or self.__settings.getboolean('general', 'debug_mode', fallback=False)
        self.dev_mode = cond
        self.read_QTHZ_inst_path()
        self.logger.info("Settings finished loading...")

    def get_paths(self):
        fnames = self.get_filenames()
        return {
            FilePath.CONFIG: self.qthz_inst_path+self.__settings[SettingsCategories.PATHS.value][SettingsItems.CONFIG.value],
            FilePath.FS: self.__settings[SettingsCategories.PATHS.value][SettingsItems.FS.value],
            FilePath.FS_CONF: self.__settings[SettingsCategories.PATHS.value][SettingsItems.FS.value]
                +self.__settings[SettingsCategories.PATHS.value][SettingsItems.FS_CONF.value],
            FilePath.JAVA: self.__settings[SettingsCategories.PATHS.value][SettingsItems.JAVA.value],
            FilePath.JAR: self.qthz_inst_path+fnames[FilePath.JAR],
            FilePath.JAVA_PID: self.qthz_inst_path+fnames[FilePath.JAVA_PID],
            FilePath.APP_YML: self.qthz_inst_path+fnames[FilePath.APP_YML],
            FilePath.PATH_BAT: self.qthz_inst_path+fnames[FilePath.PATH_BAT],
            FilePath.MANAGER: self.get_remote_manager_path() + fnames[FilePath.MANAGER],
            FilePath.UPDATER: self.get_remote_manager_path() + fnames[FilePath.UPDATER],
            FilePath.STARTER: self.get_remote_manager_path() + fnames[FilePath.STARTER]
        }

    def get_filenames(self):
        return {
            FilePath.JAR: self.__settings[SettingsCategories.PATHS.value][SettingsItems.JAR.value],
            FilePath.JAVA_PID: self.__settings[SettingsCategories.PATHS.value][SettingsItems.JAVA_PID.value],
            FilePath.APP_YML: self.__settings[SettingsCategories.PATHS.value][SettingsItems.APP_YML.value],
            FilePath.PATH_BAT: self.__settings[SettingsCategories.PATHS.value][SettingsItems.PATH_BAT.value],
            FilePath.MANAGER: self.__settings[SettingsCategories.PATHS.value][SettingsItems.MANAGER.value],
            FilePath.UPDATER: self.__settings[SettingsCategories.PATHS.value][SettingsItems.UPDATER.value],
            FilePath.STARTER: self.__settings[SettingsCategories.PATHS.value][SettingsItems.STARTER.value]
        }
    
    def get_host_addr(self):
        return self.__settings[SettingsCategories.GENERAL.value][SettingsItems.HOST_ADDR.value]

    def get_heartbeat_timer(self):
        return self.__settings[SettingsCategories.TIMER.value][SettingsItems.HB.value]

    def get_versioncheck_timer(self):
        return self.__settings[SettingsCategories.TIMER.value][SettingsItems.VC.value] 

    def get_env(self):
        return self.__settings[SettingsCategories.GENERAL.value][SettingsItems.ENV.value]

    def get_logging_level(self):
        return self.__settings[SettingsCategories.GENERAL.value][SettingsItems.LOGGING.value]

    def get_log_expiration(self):
        return self.__settings[SettingsCategories.GENERAL.value][SettingsItems.LOG_EXP.value]

    def get_QTHZ_inst_path(self):
        return self.qthz_inst_path

    def get_remote_manager_path(self):
        return self.qthz_inst_path + self.__settings[SettingsCategories.PATHS.value][SettingsItems.MANAGER_DIR.value]

    def get_sqlite_db_path(self):
        return self.qthz_inst_path+self.__settings[SettingsCategories.PATHS.value]['data']

    def get_backup_dir_path(self):
        return self.qthz_inst_path+self.__settings[SettingsCategories.PATHS.value]['backup']

    def get_patch_dir_path(self):
        return self.qthz_inst_path+self.__settings[SettingsCategories.PATHS.value][SettingsItems.PATCH.value]

    def get_patch_meta_path(self):
        return self.get_patch_dir_path()+self.__settings[SettingsCategories.PATHS.value][SettingsItems.PATCHMETA.value]

    def get_heartbeat_timer(self):
        return self.__settings[SettingsCategories.TIMER.value]['heartbeat']

    def get_version_check_timer(self):
        return self.__settings[SettingsCategories.TIMER.value]['versionCheck']


    def read_QTHZ_inst_path(self):
        self.qthz_inst_path = reg_get_QTHZ_path()

    def read_settings(self, path="./settings/settings.ini"):
        self.verify_settings_file_existence(path)
        self.__settings = self.read_ini_into_config(path)

    def verify_settings_file_existence(self, path):
        if not os.path.isfile(path):
            self.logger.warning(f"Settings file at {path} doesn't exist, creating default settings...")
            with open(path, "x") as settings_file:
                settings_file.write(DEFAULT_FILE_TEMPLATE)

    def read_ini_into_config(self, path):
        config = configparser.ConfigParser()
        config.read(path, encoding="UTF-8")
        return config
    
    def write_config_to_ini_file(self, config, filepath):
        with open(filepath, 'w') as configfile:
            config.write(configfile)
        self.logger.debug("??????????????????")

    def get_yaml_info(self, filepath):
        with open(filepath, mode = 'r', encoding='utf-8') as stream:
            data = yaml.safe_load(stream)
            return data 

    def write_yaml_info(self, filepath, data):
        with open(filepath, mode = 'w', encoding='utf-8') as stream:
            yaml.dump(data, stream, allow_unicode = True)
    

        